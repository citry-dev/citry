//! Reads the `fmt:` comment directives and marks the bytes they protect.
//!
//! Three directives, matched on exact comment text: `fmt: off` and `fmt: on`
//! bracket a region, and `fmt: skip` exempts the one thing after it. Because
//! only comments the parser recognized as comments are examined, the same
//! characters inside an attribute value, a `<c-raw>` body, or a Python string
//! stay ordinary content.
//!
//! A directive's effect is inherited downward: a region turned off at one level
//! stays off inside the elements it contains, so each level does not have to
//! re-check its ancestors.

use citry_template_parser::{
    Comment, HtmlAttr, HtmlAttrKind, HtmlEndTag, HtmlStartTag, Template, TemplateElement,
};

use crate::error::FormatError;
use crate::source::{
    Span, direct_template_comments, element_span, is_html_space_text, nested_template_source,
};

/// Bytes the printer may not touch.
#[derive(Clone, Debug)]
pub(crate) struct ProtectedRange {
    pub(crate) span: Span,
    // `fmt: skip` protects its target bytes, not the following body gap.
    pub(crate) allow_insertion_at_end: bool,
}

impl ProtectedRange {
    /// Whether an insertion at `at` would land inside protected text.
    ///
    /// The end offset is the interesting case. For an `fmt: off` region the end
    /// is still protected, or the formatter could append at the boundary. For
    /// `fmt: skip` it is not, so the gap after the skipped item can still be
    /// re-indented.
    pub(crate) fn blocks_insertion(&self, at: usize) -> bool {
        self.span.start <= at
            && (at < self.span.end || (at == self.span.end && !self.allow_insertion_at_end))
    }
}

/// Per-element verdicts for one body, plus whether formatting is still on at
/// the end. The trailing flag is what carries an unclosed `fmt: off` outward.
pub(crate) struct BodySuppression {
    pub(crate) element_enabled: Vec<bool>,
    pub(crate) terminal_enabled: bool,
}

/// Per-attribute verdicts for one start tag, so a directive written between
/// attributes governs only the attributes after it.
pub(crate) struct StartTagSuppression {
    pub(crate) attribute_enabled: Vec<bool>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Directive {
    Off,
    On,
    Skip,
}

enum BodyEvent<'a> {
    Comment(&'a Comment),
    Element(usize, &'a TemplateElement),
}

impl BodyEvent<'_> {
    fn span(&self) -> Span {
        match self {
            Self::Comment(comment) => Span::from_token(&comment.token),
            Self::Element(_, element) => element_span(element),
        }
    }
}

enum StartTagEvent<'a> {
    Comment(&'a Comment),
    Attribute(usize, &'a HtmlAttr),
}

impl StartTagEvent<'_> {
    fn span(&self) -> Span {
        match self {
            Self::Comment(comment) => Span::from_token(&comment.token),
            Self::Attribute(_, attr) => Span::from_token(&attr.token),
        }
    }
}

/// Walk one body in source order, tracking whether formatting is on.
///
/// Directives take effect from where they are written, so comments and elements
/// have to be merged into one ordered sequence. The parser keeps them in
/// separate lists, which is why they are interleaved here rather than read off
/// the tree directly.
pub(crate) fn scan_body(
    template: &Template,
    document_comments: &[Comment],
    body_span: Span,
    base: usize,
    initial_enabled: bool,
    protected: &mut Vec<ProtectedRange>,
) -> Result<BodySuppression, FormatError> {
    let comments = direct_template_comments(template, document_comments, body_span);
    let mut events = template
        .elements
        .iter()
        .enumerate()
        .map(|(index, element)| BodyEvent::Element(index, element))
        .chain(comments.iter().map(|comment| BodyEvent::Comment(comment)))
        .collect::<Vec<_>>();
    events.sort_by_key(|event| {
        let span = event.span();
        (span.start, span.end)
    });

    // `cursor` trails the walk so the whitespace between two events can be
    // protected too. Without it, a disabled region would keep its elements but
    // lose the spacing between them.
    let mut state = initial_enabled;
    let mut cursor = body_span.start;
    let mut element_enabled = vec![initial_enabled; template.elements.len()];
    for event in events {
        let span = event.span();
        protect_when_disabled(cursor, span.start, base, state, protected);
        match event {
            BodyEvent::Comment(comment) => {
                match directive(comment) {
                    Some(Directive::Off | Directive::On) => {
                        state = transition_state(comment, base, state)?;
                    }
                    Some(Directive::Skip) => {
                        let target = skip_body_target(template, &comments, comment, base)?;
                        protected.push(ProtectedRange {
                            span: target,
                            allow_insertion_at_end: true,
                        });
                    }
                    None => protect_when_disabled(span.start, span.end, base, state, protected),
                }
                cursor = span.end;
            }
            BodyEvent::Element(index, element) => {
                element_enabled[index] = state;
                // A node's own bytes are not blanket-protected here, because the
                // walk descends into it and decides tag by tag. Anything else
                // (text, an expression) has no inside to visit, so it is
                // protected whole.
                if !matches!(element, TemplateElement::Node(_)) {
                    protect_when_disabled(span.start, span.end, base, state, protected);
                }
                cursor = span.end;
            }
        }
    }
    // The tail after the last event, so a trailing `fmt: off` covers the rest of
    // the body rather than stopping at the final element.
    protect_when_disabled(cursor, body_span.end, base, state, protected);

    Ok(BodySuppression {
        element_enabled,
        terminal_enabled: state,
    })
}

/// The same walk for the inside of one start tag.
///
/// A directive between attributes governs the attributes after it, so the tag
/// needs its own ordered pass rather than a single verdict for the whole tag.
pub(crate) fn scan_start_tag(
    tag: &HtmlStartTag,
    base: usize,
    initial_enabled: bool,
    protected: &mut Vec<ProtectedRange>,
) -> Result<StartTagSuppression, FormatError> {
    let mut events = tag
        .attrs
        .iter()
        .enumerate()
        .map(|(index, attr)| StartTagEvent::Attribute(index, attr))
        .chain(tag.comments.iter().map(StartTagEvent::Comment))
        .collect::<Vec<_>>();
    events.sort_by_key(|event| {
        let span = event.span();
        (span.start, span.end)
    });

    // Where the closing `>` or `/>` begins. The scan stops here so the
    // delimiter itself is never swept into a protected range.
    let delimiter_start = tag.token.end_index
        - if tag.is_self_closing {
            "/>".len()
        } else {
            ">".len()
        };
    // Start after the tag name: the name is never editable, so protecting it
    // would only add a range nothing consults.
    let mut state = initial_enabled;
    let mut cursor = tag.name.end_index;
    let mut attribute_enabled = vec![initial_enabled; tag.attrs.len()];
    for (event_index, event) in events.iter().enumerate() {
        let span = event.span();
        protect_when_disabled(cursor, span.start, base, state, protected);
        match event {
            StartTagEvent::Comment(comment) => {
                match directive(comment) {
                    Some(Directive::Off | Directive::On) => {
                        state = transition_state(comment, base, state)?;
                    }
                    Some(Directive::Skip) => {
                        let target = events[event_index + 1..]
                            .iter()
                            .find_map(|event| match event {
                                StartTagEvent::Attribute(_, attr) => {
                                    Some(Span::from_token(&attr.token).offset(base))
                                }
                                StartTagEvent::Comment(_) => None,
                            })
                            .ok_or_else(|| {
                                suppression_error(
                                    comment,
                                    base,
                                    "'fmt: skip' inside a start tag must be followed by an attribute",
                                )
                            })?;
                        protected.push(ProtectedRange {
                            span: target,
                            allow_insertion_at_end: true,
                        });
                    }
                    None => protect_when_disabled(span.start, span.end, base, state, protected),
                }
                cursor = span.end;
            }
            StartTagEvent::Attribute(index, attr) => {
                attribute_enabled[*index] = state;
                if !state {
                    protect_attribute_shell(attr, base, protected);
                }
                cursor = span.end;
            }
        }
    }
    protect_when_disabled(cursor, delimiter_start, base, state, protected);

    Ok(StartTagSuppression { attribute_enabled })
}

pub(crate) fn scan_end_tag(
    tag: &HtmlEndTag,
    base: usize,
    initial_enabled: bool,
    protected: &mut Vec<ProtectedRange>,
) -> Result<(), FormatError> {
    let mut comments = tag.comments.iter().collect::<Vec<_>>();
    comments.sort_by_key(|comment| comment.token.start_index);

    let delimiter_start = tag.token.end_index - ">".len();
    let mut state = initial_enabled;
    let mut cursor = tag.name.end_index;
    for comment in comments {
        let span = Span::from_token(&comment.token);
        protect_when_disabled(cursor, span.start, base, state, protected);
        match directive(comment) {
            Some(Directive::Off | Directive::On) => {
                state = transition_state(comment, base, state)?;
            }
            Some(Directive::Skip) => {
                return Err(suppression_error(
                    comment,
                    base,
                    "'fmt: skip' inside an end tag has no formatting target",
                ));
            }
            None => {
                protect_when_disabled(span.start, span.end, base, state, protected);
            }
        }
        cursor = span.end;
    }
    protect_when_disabled(cursor, delimiter_start, base, state, protected);
    Ok(())
}

/// Apply an `fmt: off` / `fmt: on` and reject a pairing that makes no sense.
///
/// Both mistakes are errors rather than no-ops on purpose. A second `fmt: off`
/// reads as if it opened a scope that a later `fmt: on` would close, when the
/// `on` would in fact re-enable everything; and an `fmt: on` with nothing to
/// resume is usually a directive written in the wrong place. Failing loudly
/// tells the author, where ignoring it would quietly format what they meant to
/// protect.
fn transition_state(comment: &Comment, base: usize, enabled: bool) -> Result<bool, FormatError> {
    match directive(comment) {
        Some(Directive::Off) if !enabled => Err(suppression_error(
            comment,
            base,
            "nested 'fmt: off' directives are not allowed in an inherited disabled scope",
        )),
        Some(Directive::Off) => Ok(false),
        Some(Directive::On) if enabled => Err(suppression_error(
            comment,
            base,
            "'fmt: on' has no matching or inherited 'fmt: off' in this formatter scope",
        )),
        Some(Directive::On) => Ok(true),
        Some(Directive::Skip) | None => Ok(enabled),
    }
}

fn protect_attribute_shell(attr: &HtmlAttr, base: usize, protected: &mut Vec<ProtectedRange>) {
    let attr_span = Span::from_token(&attr.token);
    let Some(inner_value) = attr
        .inner_value
        .as_ref()
        .filter(|_| attr.kind == HtmlAttrKind::Template)
    else {
        protect_local(attr_span, base, false, protected);
        return;
    };
    let (prefix_len, nested_source, _) = nested_template_source(&inner_value.content);
    let nested_span = Span {
        start: inner_value.start_index + prefix_len,
        end: inner_value.start_index + prefix_len + nested_source.len(),
    };
    protect_local(
        Span {
            start: attr_span.start,
            end: nested_span.start,
        },
        base,
        false,
        protected,
    );
    protect_local(
        Span {
            start: nested_span.end,
            end: attr_span.end,
        },
        base,
        false,
        protected,
    );
}

fn protect_when_disabled(
    start: usize,
    end: usize,
    base: usize,
    enabled: bool,
    protected: &mut Vec<ProtectedRange>,
) {
    if !enabled {
        protect_local(Span { start, end }, base, false, protected);
    }
}

fn protect_local(
    span: Span,
    base: usize,
    allow_insertion_at_end: bool,
    protected: &mut Vec<ProtectedRange>,
) {
    protected.push(ProtectedRange {
        span: span.offset(base),
        allow_insertion_at_end,
    });
}

/// Find what an `fmt: skip` applies to: the next thing after it.
///
/// Whitespace between the directive and its target is skipped over, so a
/// directive on its own line still reaches the element below it. A directive
/// with nothing after it is an error, since silently applying to nothing would
/// leave the author believing something is protected.
fn skip_body_target(
    template: &Template,
    comments: &[&Comment],
    directive_comment: &Comment,
    base: usize,
) -> Result<Span, FormatError> {
    enum Event<'a> {
        Comment,
        Element(&'a TemplateElement),
    }

    let mut events = template
        .elements
        .iter()
        .map(|element| (element_span(element).start, Event::Element(element)))
        .chain(
            comments
                .iter()
                .map(|comment| (comment.token.start_index, Event::Comment)),
        )
        .collect::<Vec<_>>();
    events.sort_by_key(|event| event.0);

    for (_, event) in events
        .into_iter()
        .skip_while(|(start, _)| *start <= directive_comment.token.start_index)
    {
        match event {
            Event::Comment => {}
            Event::Element(TemplateElement::Text(text))
                if is_html_space_text(&text.token.content) => {}
            Event::Element(element) => return Ok(element_span(element).offset(base)),
        }
    }

    Err(suppression_error(
        directive_comment,
        base,
        "'fmt: skip' must be followed by a node, expression, or rendered text",
    ))
}

fn directive(comment: &Comment) -> Option<Directive> {
    match comment.value.content.trim() {
        "fmt: off" => Some(Directive::Off),
        "fmt: on" => Some(Directive::On),
        "fmt: skip" => Some(Directive::Skip),
        _ => None,
    }
}

fn suppression_error(comment: &Comment, base: usize, message: &str) -> FormatError {
    FormatError::suppression(
        message,
        base + comment.token.start_index..base + comment.token.end_index,
    )
}
