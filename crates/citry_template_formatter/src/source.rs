//! The document model: everything the printer is allowed to touch.
//!
//! Walking the parsed template produces lists of spans rather than a tree to
//! render. Each list answers one question about the original text: which start
//! tags can be re-laid out, which gaps between elements may become line breaks,
//! which expressions have a canonical form, and which bytes are off limits.
//! Anything that does not end up in one of these lists is never edited, so the
//! decision about what is safe to change is made once, here, instead of being
//! rediscovered by the printer.
//!
//! The model also holds the fingerprints the formatter checks its own output
//! against, which is why it is built for the source and again for the result.

use citry_template_parser::{
    Comment, FillDataPattern, ForeignSpan, HtmlAttr, HtmlAttrKind, HtmlStartTag, Node,
    ParseOptions, Template, TemplateElement, Token, parse_template, parse_template_with_options,
};

use crate::PREFERRED_WIDTH;
use crate::comments::{CommentKind, CommentMap};
use crate::embedded::{EmbeddedLanguage, EmbeddedRegionKind};
use crate::error::FormatError;
use crate::html::{
    ContainerKind, EdgeKind, GapContext, WhitespaceClass, classify_gap, container_kind_for_tag,
};
use crate::layout::{ElementLayout, ItemEdges, analyze_elements};
use crate::newline::{detect_newline, normalize_to_lf};
use crate::python::{
    expression_is_provider_suppressed, for_clause_is_provider_suppressed, format_expression,
    format_for_clause,
};
use crate::suppression::{ProtectedRange, scan_body, scan_end_tag, scan_start_tag};

/// A byte range in the source. Every edit and every protected region is one.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct Span {
    pub(crate) start: usize,
    pub(crate) end: usize,
}

impl Span {
    pub(crate) fn from_token(token: &Token) -> Self {
        Self {
            start: token.start_index,
            end: token.end_index,
        }
    }

    /// Rebase a span onto the outer document.
    ///
    /// A nested template inside an attribute value is parsed on its own, so its
    /// spans start at zero. They have to be shifted by where that value sits
    /// before they mean anything to the printer.
    pub(crate) fn offset(self, base: usize) -> Self {
        Self {
            start: base + self.start,
            end: base + self.end,
        }
    }

    pub(crate) fn contains(self, other: Self) -> bool {
        self.start <= other.start && other.end <= self.end
    }
}

/// One attribute, split so the printer can tighten around its `=` without
/// disturbing the key or the value. `value` is absent for a bare attribute
/// such as `disabled`.
#[derive(Clone, Debug)]
pub(crate) struct AttrModel {
    pub(crate) span: Span,
    pub(crate) key: Span,
    pub(crate) value: Option<Span>,
}

/// Something occupying a slot inside a start tag. Comments count, because a
/// comment written between attributes has to keep its place when the tag wraps.
#[derive(Clone, Debug)]
pub(crate) enum TagItemModel {
    Attr(AttrModel),
    Comment(Span),
}

impl TagItemModel {
    pub(crate) fn span(&self) -> Span {
        match self {
            Self::Attr(attr) => attr.span,
            Self::Comment(span) => *span,
        }
    }
}

/// A start tag the printer may re-lay out.
///
/// `layout_column` is where the tag begins on its line, which fixes both the
/// indent of wrapped attributes and the width still available. `adjacent_end_tag`
/// is set when the end tag sits right beside it, as in `<div></div>`, so the
/// pair is measured as the one line it occupies.
#[derive(Clone, Debug)]
pub(crate) struct StartTagModel {
    pub(crate) span: Span,
    pub(crate) name: Span,
    pub(crate) delimiter: Span,
    pub(crate) items: Vec<TagItemModel>,
    pub(crate) adjacent_end_tag: Option<Span>,
    pub(crate) layout_column: usize,
}

/// Whitespace between two elements that was proven safe to replace with a line
/// break and indent. Gaps where whitespace is rendered never become one of
/// these, which is how inline and mixed content keeps its spacing.
#[derive(Clone, Debug)]
pub(crate) struct BodyGapModel {
    pub(crate) span: Span,
    pub(crate) indent: usize,
}

/// An expression region together with the text it should become. The canonical
/// form is computed while building the model, so the printer only substitutes.
#[derive(Clone, Debug)]
pub(crate) struct ExpressionModel {
    pub(crate) span: Span,
    pub(crate) canonical: String,
}

/// A `<script>` or `<style>` body, which this crate does not format itself.
///
/// `has_interpolation` matters because a body containing `{{ ... }}` is not
/// valid standalone JavaScript or CSS, so handing it to one of those formatters
/// would corrupt it.
#[derive(Clone, Debug)]
pub(crate) struct EmbeddedBodyModel {
    pub(crate) span: Span,
    pub(crate) language: Option<EmbeddedLanguage>,
    pub(crate) kind: EmbeddedRegionKind,
    pub(crate) tag_column: usize,
    pub(crate) has_interpolation: bool,
}

/// Everything one pass needs: the three editable lists, the bytes that are off
/// limits, and the fingerprints used to verify the result.
#[derive(Clone)]
pub(crate) struct SourceModel {
    pub(crate) tags: Vec<StartTagModel>,
    pub(crate) body_gaps: Vec<BodyGapModel>,
    pub(crate) expressions: Vec<ExpressionModel>,
    pub(crate) protected: Vec<ProtectedRange>,
    embedded_bodies: Vec<EmbeddedBodyModel>,
    verbatim_bodies: Vec<String>,
    comments: CommentMap,
}

impl SourceModel {
    pub(crate) fn build(source: &str, template: &Template) -> Result<Self, FormatError> {
        Self::build_with_options(source, template, &ParseOptions::default())
    }

    pub(crate) fn build_with_options(
        source: &str,
        template: &Template,
        options: &ParseOptions,
    ) -> Result<Self, FormatError> {
        let mut model = Self {
            tags: Vec::new(),
            body_gaps: Vec::new(),
            expressions: Vec::new(),
            protected: Vec::new(),
            embedded_bodies: Vec::new(),
            verbatim_bodies: Vec::new(),
            comments: CommentMap::new(source, &template.comments)?,
        };
        visit_template(
            &VisitContext {
                root_source: source,
                local_source: source,
                document_comments: &template.comments,
                foreign_spans: &options.foreign_spans,
                base: 0,
                editable: true,
                provider_editable: true,
                root_layout_column: None,
                root_closing_column: None,
            },
            template,
            Span {
                start: 0,
                end: source.len(),
            },
            None,
            true,
            &mut model,
        )?;
        // Every comment must have been claimed by something. An unclaimed one
        // means the walk missed a region, and formatting a template the model
        // does not fully describe is how comments get lost.
        model.comments.validate_complete()?;
        // Nested templates are visited inside their parent, so the lists come
        // back out of source order. The printer needs them sorted, and
        // overlapping protected ranges are merged so containment tests are a
        // simple scan.
        model.tags.sort_by_key(|tag| tag.span.start);
        model.body_gaps.sort_by_key(|gap| gap.span.start);
        model
            .expressions
            .sort_by_key(|expression| expression.span.start);
        normalize_protected_ranges(&mut model.protected);
        Ok(model)
    }

    pub(crate) fn markup_comment_fingerprint(&self) -> Vec<(CommentKind, String)> {
        self.comments.markup_fingerprint()
    }

    /// The text of every protected range, in order.
    ///
    /// Compared as content rather than spans, because formatting legitimately
    /// moves protected text around on the page. What must not change is what it
    /// says.
    pub(crate) fn protected_fingerprint(&self, source: &str) -> Result<Vec<String>, FormatError> {
        self.protected
            .iter()
            .map(|range| {
                source
                    .get(range.span.start..range.span.end)
                    .map(str::to_string)
                    .ok_or_else(|| {
                        FormatError::invalid_span(
                            "protected formatter range is not valid UTF-8 source",
                            range.span.start..range.span.end,
                        )
                    })
            })
            .collect()
    }

    pub(crate) fn verbatim_fingerprint(&self) -> &[String] {
        &self.verbatim_bodies
    }

    pub(crate) fn embedded_bodies(&self) -> &[EmbeddedBodyModel] {
        &self.embedded_bodies
    }
}

/// What the walk needs to know at each level.
///
/// The two source fields differ only inside a nested template: `local_source` is
/// the attribute value being parsed on its own, `root_source` the whole
/// document, and `base` converts between them. `editable` and `provider_editable`
/// are inherited, so an `fmt: off` on an ancestor keeps everything below it from
/// being edited without each level having to re-check.
struct VisitContext<'a> {
    root_source: &'a str,
    local_source: &'a str,
    document_comments: &'a [Comment],
    foreign_spans: &'a [ForeignSpan],
    base: usize,
    editable: bool,
    provider_editable: bool,
    root_layout_column: Option<usize>,
    root_closing_column: Option<usize>,
}

#[derive(Clone, Copy)]
struct ParentLayout<'a> {
    name: &'a str,
    column: usize,
}

#[derive(Clone, Copy)]
struct NodeLayout {
    column: usize,
    body_editable: bool,
}

/// Walk one template body, collecting everything editable inside it.
///
/// Returns whether formatting is still enabled on the way out, so an `fmt: off`
/// that a body opened carries on into the elements that follow it.
fn visit_template(
    context: &VisitContext<'_>,
    template: &Template,
    body_span: Span,
    parent: Option<ParentLayout<'_>>,
    initial_formatting_enabled: bool,
    model: &mut SourceModel,
) -> Result<bool, FormatError> {
    // Check the parser's spans against this source before trusting them. A bad
    // offset here would become a bad edit later, where it is much harder to
    // attribute.
    validate_local_span(
        context.local_source,
        body_span,
        context.base,
        "template body",
    )?;
    for element in &template.elements {
        validate_local_span(
            context.local_source,
            element_span(element),
            context.base,
            "template element",
        )?;
    }
    // Suppression is resolved before anything is collected, so a directive can
    // take a region out of play before the walk offers it to the printer.
    let suppression = scan_body(
        template,
        context.document_comments,
        body_span,
        context.base,
        initial_formatting_enabled,
        &mut model.protected,
    )?;
    model.comments.associate_body(
        context.root_source,
        template,
        context.document_comments,
        body_span,
        context.base,
    )?;

    let node_layouts = collect_body_layout(context, template, body_span, parent, model)?;

    for (index, element) in template.elements.iter().enumerate() {
        match element {
            TemplateElement::Node(node) => {
                visit_node(
                    context,
                    node,
                    node_layouts[index],
                    suppression.element_enabled[index],
                    model,
                )?;
            }
            TemplateElement::Expr(expr) => {
                validate_token(
                    context.root_source,
                    context.local_source,
                    &expr.token,
                    context.base,
                    "expression",
                )?;
                validate_token(
                    context.root_source,
                    context.local_source,
                    &expr.value,
                    context.base,
                    "expression value",
                )?;
                let span = Span::from_token(&expr.token).offset(context.base);
                if context.provider_editable
                    && !is_protected(span, &model.protected)
                    && !expression_is_provider_suppressed(&expr.value.content)
                {
                    let source_column = source_column(context.root_source, span.start)?;
                    let column = parent
                        .filter(|_| span.start == context.base + body_span.start)
                        .map_or(source_column, |layout| layout.column);
                    let suffix_width = same_line_suffix_width(context.root_source, span.end)?;
                    let formatted = format_expression(
                        &expr.value.content,
                        PREFERRED_WIDTH.saturating_sub(column + 6 + suffix_width),
                        detect_newline(context.root_source),
                    )?;
                    model.expressions.push(ExpressionModel {
                        span,
                        canonical: format_template_expression(
                            &formatted,
                            column,
                            detect_newline(context.root_source),
                            expr.token.content.contains(['\n', '\r']),
                        ),
                    });
                }
            }
            TemplateElement::Text(text) => validate_token(
                context.root_source,
                context.local_source,
                &text.token,
                context.base,
                "text",
            )?,
            TemplateElement::Foreign(part) => {
                validate_token(
                    context.root_source,
                    context.local_source,
                    &part.token,
                    context.base,
                    "foreign source",
                )?;
                model.protected.push(ProtectedRange {
                    span: Span::from_token(&part.token).offset(context.base),
                    allow_insertion_at_end: false,
                });
            }
        }
    }
    Ok(suppression.terminal_enabled)
}

fn visit_node(
    context: &VisitContext<'_>,
    node: &Node,
    layout: NodeLayout,
    initial_formatting_enabled: bool,
    model: &mut SourceModel,
) -> Result<(), FormatError> {
    let start_tag = node.start_tag();
    protect_start_tag_foreign_parts(context, start_tag, &mut model.protected)?;
    // A raw contribution between attributes may emit spacing or several
    // attributes. Preserve the complete authored start tag because Citry
    // cannot safely normalize layout around output it does not understand.
    let mut start_tag_model = if start_tag.foreign_parts.is_empty() {
        Some(build_start_tag(
            context.root_source,
            context.local_source,
            start_tag,
            context.base,
        )?)
    } else {
        validate_token(
            context.root_source,
            context.local_source,
            &start_tag.token,
            context.base,
            "start tag",
        )?;
        validate_token(
            context.root_source,
            context.local_source,
            &start_tag.name,
            context.base,
            "start tag name",
        )?;
        None
    };
    if let Some(start_tag_model) = &mut start_tag_model {
        if let Node::WithBody {
            start_tag, end_tag, ..
        } = node
            && start_tag.token.end_index == end_tag.token.start_index
        {
            start_tag_model.adjacent_end_tag =
                Some(Span::from_token(&end_tag.token).offset(context.base));
        }
        start_tag_model.layout_column = layout.column;
    }
    let start_tag_suppression = scan_start_tag(
        start_tag,
        context.base,
        initial_formatting_enabled,
        &mut model.protected,
    )?;
    model
        .comments
        .associate_start_tag(context.root_source, start_tag, context.base)?;
    if context.editable
        && let Some(start_tag_model) = start_tag_model
    {
        model.tags.push(start_tag_model);
    }

    if context.provider_editable {
        collect_attribute_provider_edits(
            context,
            start_tag,
            layout.column,
            &model.protected,
            &mut model.expressions,
        )?;
    }

    for (attr_index, attr) in start_tag.attrs.iter().enumerate() {
        if attr.kind != HtmlAttrKind::Template {
            continue;
        }
        let Some(inner_value) = &attr.inner_value else {
            continue;
        };
        if !attr.foreign_parts.is_empty() {
            continue;
        }
        let (prefix_len, nested_source, is_fragment) = nested_template_source(&inner_value.content);
        let nested_base = context.base + inner_value.start_index + prefix_len;
        let nested_options =
            options_for_nested_source(context.foreign_spans, nested_base, nested_source.len())?;
        let nested = parse_with_options(nested_source, &nested_options).map_err(|error| {
            FormatError::invariant(format!(
                "nested template parsed in the outer document but not in the formatter: {error}"
            ))
        })?;
        visit_template(
            &VisitContext {
                root_source: context.root_source,
                local_source: nested_source,
                document_comments: &nested.comments,
                foreign_spans: context.foreign_spans,
                base: nested_base,
                editable: context.editable,
                provider_editable: context.provider_editable,
                root_layout_column: Some(layout.column + 2 + if is_fragment { 2 } else { 0 }),
                root_closing_column: is_fragment.then_some(layout.column + 2),
            },
            &nested,
            Span {
                start: 0,
                end: nested_source.len(),
            },
            None,
            start_tag_suppression.attribute_enabled[attr_index],
            model,
        )?;
    }

    if let Node::WithBody {
        start_tag,
        end_tag,
        body,
        ..
    } = node
    {
        validate_token(
            context.root_source,
            context.local_source,
            &end_tag.token,
            context.base,
            "end tag",
        )?;
        validate_token(
            context.root_source,
            context.local_source,
            &end_tag.name,
            context.base,
            "end tag name",
        )?;
        model.comments.associate_end_tag(end_tag, context.base)?;
        if let Some((kind, language)) = embedded_body_kind(start_tag, node.tag_name()) {
            model.embedded_bodies.push(EmbeddedBodyModel {
                span: Span {
                    start: context.base + start_tag.token.end_index,
                    end: context.base + end_tag.token.start_index,
                },
                language,
                kind,
                tag_column: layout.column,
                has_interpolation: body
                    .elements
                    .iter()
                    .any(|element| matches!(element, TemplateElement::Expr(_))),
            });
        }
        if container_kind_for_tag(node.tag_name()) == ContainerKind::Verbatim {
            let body_start = context.base + start_tag.token.end_index;
            let body_end = context.base + end_tag.token.start_index;
            model.verbatim_bodies.push(
                context
                    .root_source
                    .get(body_start..body_end)
                    .ok_or_else(|| {
                        FormatError::invalid_span(
                            "verbatim body is not valid UTF-8 source",
                            body_start..body_end,
                        )
                    })?
                    .to_string(),
            );
        }
        let body_editable = context.editable
            && layout.body_editable
            && container_kind_for_tag(node.tag_name()) != ContainerKind::Verbatim;
        let body_terminal_formatting_enabled = visit_template(
            &VisitContext {
                root_source: context.root_source,
                local_source: context.local_source,
                document_comments: context.document_comments,
                foreign_spans: context.foreign_spans,
                base: context.base,
                editable: body_editable,
                provider_editable: context.provider_editable
                    && container_kind_for_tag(node.tag_name()) != ContainerKind::Verbatim,
                root_layout_column: None,
                root_closing_column: None,
            },
            body,
            Span {
                start: start_tag.token.end_index,
                end: end_tag.token.start_index,
            },
            Some(ParentLayout {
                name: node.tag_name(),
                column: layout.column,
            }),
            initial_formatting_enabled,
            model,
        )?;
        scan_end_tag(
            end_tag,
            context.base,
            body_terminal_formatting_enabled,
            &mut model.protected,
        )?;
    }
    Ok(())
}

fn protect_start_tag_foreign_parts(
    context: &VisitContext<'_>,
    start_tag: &HtmlStartTag,
    protected: &mut Vec<ProtectedRange>,
) -> Result<(), FormatError> {
    for part in start_tag.foreign_parts.iter().chain(
        start_tag
            .attrs
            .iter()
            .flat_map(|attr| attr.foreign_parts.iter()),
    ) {
        validate_token(
            context.root_source,
            context.local_source,
            &part.token,
            context.base,
            "foreign start-tag source",
        )?;
        protected.push(ProtectedRange {
            span: Span::from_token(&part.token).offset(context.base),
            allow_insertion_at_end: false,
        });
    }
    Ok(())
}

fn parse_with_options(
    source: &str,
    options: &ParseOptions,
) -> Result<Template, Box<citry_template_parser::ParseError>> {
    if options == &ParseOptions::default() {
        parse_template(source, None, None)
    } else {
        parse_template_with_options(source, None, None, options)
    }
    .map_err(Box::new)
}

fn options_for_nested_source(
    foreign_spans: &[ForeignSpan],
    nested_base: usize,
    nested_len: usize,
) -> Result<ParseOptions, FormatError> {
    let nested_end = nested_base
        .checked_add(nested_len)
        .ok_or_else(|| FormatError::invariant("nested template range overflows source offsets"))?;
    let mut projected = Vec::new();
    for span in foreign_spans {
        let intersects = span.start_byte < nested_end && nested_base < span.end_byte;
        if !intersects {
            continue;
        }
        if span.start_byte < nested_base || span.end_byte > nested_end {
            return Err(FormatError::invalid_span(
                "foreign span crosses a nested template boundary",
                span.start_byte..span.end_byte,
            ));
        }
        projected.push(ForeignSpan::from_parts(
            span.start_byte - nested_base,
            span.end_byte - nested_base,
            span.provider.clone(),
            span.ordinal,
            span.may_control_body,
        ));
    }
    Ok(ParseOptions::with_foreign_spans(projected))
}

fn embedded_body_kind(
    start_tag: &HtmlStartTag,
    tag_name: &str,
) -> Option<(EmbeddedRegionKind, Option<EmbeddedLanguage>)> {
    let (kind, default_language) = if tag_name.eq_ignore_ascii_case("script") {
        (EmbeddedRegionKind::ScriptBody, EmbeddedLanguage::JavaScript)
    } else if tag_name.eq_ignore_ascii_case("style") {
        (EmbeddedRegionKind::StyleBody, EmbeddedLanguage::Css)
    } else {
        return None;
    };

    let type_attrs = start_tag
        .attrs
        .iter()
        .filter(|attr| attr.key.content.eq_ignore_ascii_case("type"))
        .collect::<Vec<_>>();
    if type_attrs.is_empty() {
        return Some((kind, Some(default_language)));
    }
    if type_attrs.len() != 1 {
        return Some((kind, None));
    }
    let attr = type_attrs[0];
    if attr.kind != HtmlAttrKind::Static {
        return Some((kind, None));
    }
    let value = attr
        .inner_value
        .as_ref()
        .map_or("", |token| trim_html_ascii_whitespace(&token.content));
    let recognized = match kind {
        EmbeddedRegionKind::ScriptBody => script_type_is_javascript(value),
        EmbeddedRegionKind::StyleBody => value.is_empty() || value.eq_ignore_ascii_case("text/css"),
    };
    Some((kind, recognized.then_some(default_language)))
}

fn trim_html_ascii_whitespace(value: &str) -> &str {
    value.trim_matches(is_html_ascii_whitespace)
}

fn script_type_is_javascript(value: &str) -> bool {
    matches!(
        value.to_ascii_lowercase().as_str(),
        "" | "module"
            | "application/ecmascript"
            | "application/javascript"
            | "application/x-ecmascript"
            | "application/x-javascript"
            | "text/ecmascript"
            | "text/javascript"
            | "text/javascript1.0"
            | "text/javascript1.1"
            | "text/javascript1.2"
            | "text/javascript1.3"
            | "text/javascript1.4"
            | "text/javascript1.5"
            | "text/jscript"
            | "text/livescript"
            | "text/x-ecmascript"
            | "text/x-javascript"
    )
}

fn collect_attribute_provider_edits(
    context: &VisitContext<'_>,
    tag: &HtmlStartTag,
    layout_column: usize,
    protected: &[ProtectedRange],
    edits: &mut Vec<ExpressionModel>,
) -> Result<(), FormatError> {
    for attr in &tag.attrs {
        let Some(inner_value) = &attr.inner_value else {
            continue;
        };
        let span = Span::from_token(inner_value).offset(context.base);
        if is_protected(span, protected) {
            continue;
        }

        let key = attr.key.content.to_ascii_lowercase();
        let tag_name = tag.name.content.to_ascii_lowercase();
        let available_width = PREFERRED_WIDTH
            .saturating_sub(layout_column + 2 + attr.key.content.chars().count() + 3);
        let formatted = if key == "c-for" || (tag_name == "c-for" && key == "each") {
            if for_clause_is_provider_suppressed(
                &inner_value.content,
                detect_newline(context.root_source),
            ) {
                None
            } else {
                Some(format_for_clause(
                    &inner_value.content,
                    available_width,
                    detect_newline(context.root_source),
                )?)
            }
        } else if tag_name == "c-fill" && key == "data" {
            attr.fill_data_pattern
                .as_ref()
                .map(|pattern| format_fill_data_pattern(pattern, available_width))
        } else if attr.kind == HtmlAttrKind::Expression || key == "#c-key" {
            if expression_is_provider_suppressed(&inner_value.content) {
                None
            } else {
                Some(format_expression(
                    &inner_value.content,
                    available_width,
                    detect_newline(context.root_source),
                )?)
            }
        } else {
            None
        };
        let Some(formatted) = formatted else {
            continue;
        };
        if !attribute_value_is_representable(attr, &formatted) {
            continue;
        }
        edits.push(ExpressionModel {
            span,
            canonical: indent_attribute_value(
                &formatted,
                layout_column + 2,
                detect_newline(context.root_source),
            ),
        });
    }
    Ok(())
}

fn format_template_expression(
    formatted: &str,
    column: usize,
    newline: &str,
    preserve_multiline: bool,
) -> String {
    if !preserve_multiline && !formatted.contains(['\n', '\r']) {
        return format!("{{{{ {} }}}}", formatted.trim());
    }
    let content_indent = " ".repeat(column + 2);
    let closing_indent = " ".repeat(column);
    let normalized = normalize_to_lf(formatted);
    let content = normalized
        .lines()
        .map(|line| format!("{content_indent}{line}"))
        .collect::<Vec<_>>()
        .join(newline);
    format!("{{{{{newline}{content}{newline}{closing_indent}}}}}")
}

fn indent_attribute_value(formatted: &str, attribute_column: usize, newline: &str) -> String {
    let normalized = normalize_to_lf(formatted);
    let mut lines = normalized.lines();
    let Some(first) = lines.next() else {
        return String::new();
    };
    let continuation = " ".repeat(attribute_column);
    let mut result = first.to_string();
    for line in lines {
        result.push_str(newline);
        result.push_str(&continuation);
        result.push_str(line);
    }
    result
}

fn format_fill_data_pattern(pattern: &FillDataPattern, available_width: usize) -> String {
    if let Some(whole) = &pattern.whole {
        return whole.content.clone();
    }
    let mut items = pattern
        .fields
        .iter()
        .map(|field| {
            if field.source.content == field.target.content {
                field.source.content.clone()
            } else {
                format!("{} as {}", field.source.content, field.target.content)
            }
        })
        .collect::<Vec<_>>();
    if let Some(rest) = &pattern.rest {
        items.push(format!("**{}", rest.content));
    }
    let compact = format!("{{{}}}", items.join(", "));
    if compact.chars().count() <= available_width {
        return compact;
    }
    format!("{{\n  {},\n}}", items.join(",\n  "))
}

fn attribute_value_is_representable(attr: &HtmlAttr, formatted: &str) -> bool {
    match attr.quote_char {
        Some(quote) => !contains_unescaped_quote(formatted, quote),
        None => !formatted
            .chars()
            .any(|character| character.is_whitespace() || matches!(character, '>' | '/' | '=')),
    }
}

fn contains_unescaped_quote(source: &str, quote: char) -> bool {
    let mut backslashes = 0;
    for character in source.chars() {
        if character == '\\' {
            backslashes += 1;
        } else {
            if character == quote && backslashes % 2 == 0 {
                return true;
            }
            backslashes = 0;
        }
    }
    false
}

fn is_protected(span: Span, protected: &[ProtectedRange]) -> bool {
    protected
        .iter()
        .any(|range| span.start < range.span.end && range.span.start < span.end)
}

fn insertion_is_protected(at: usize, protected: &[ProtectedRange]) -> bool {
    protected.iter().any(|range| range.blocks_insertion(at))
}

fn same_line_suffix_width(source: &str, at: usize) -> Result<usize, FormatError> {
    let suffix = source.get(at..).ok_or_else(|| {
        FormatError::invalid_span("expression suffix is not valid UTF-8 source", at..at)
    })?;
    Ok(suffix
        .chars()
        .take_while(|character| !matches!(character, '\r' | '\n'))
        .count())
}

fn normalize_protected_ranges(ranges: &mut Vec<ProtectedRange>) {
    ranges.sort_by_key(|range| (range.span.start, range.span.end));
    let mut merged: Vec<ProtectedRange> = Vec::with_capacity(ranges.len());
    for range in ranges.drain(..) {
        if let Some(previous) = merged.last_mut()
            && range.span.start <= previous.span.end
        {
            if range.span.end > previous.span.end {
                previous.span.end = range.span.end;
                previous.allow_insertion_at_end = range.allow_insertion_at_end;
            } else if range.span.end == previous.span.end {
                previous.allow_insertion_at_end &= range.allow_insertion_at_end;
            }
        } else {
            merged.push(range);
        }
    }
    *ranges = merged;
}

fn build_start_tag(
    root_source: &str,
    local_source: &str,
    tag: &HtmlStartTag,
    base: usize,
) -> Result<StartTagModel, FormatError> {
    validate_token(root_source, local_source, &tag.token, base, "start tag")?;
    validate_token(root_source, local_source, &tag.name, base, "start tag name")?;
    let tag_span = Span::from_token(&tag.token).offset(base);
    let name_span = Span::from_token(&tag.name).offset(base);
    let delimiter_text = if tag.is_self_closing { "/>" } else { ">" };
    let delimiter_start = tag_span
        .end
        .checked_sub(delimiter_text.len())
        .ok_or_else(|| {
            FormatError::invalid_span(
                "start tag is shorter than its delimiter",
                tag_span.start..tag_span.end,
            )
        })?;
    let delimiter = Span {
        start: delimiter_start,
        end: tag_span.end,
    };
    if root_source.get(delimiter.start..delimiter.end) != Some(delimiter_text) {
        return Err(FormatError::invalid_span(
            "start tag delimiter does not match its parser flag",
            delimiter.start..delimiter.end,
        ));
    }

    let mut items = Vec::new();
    for attr in &tag.attrs {
        validate_token(root_source, local_source, &attr.token, base, "attribute")?;
        validate_token(root_source, local_source, &attr.key, base, "attribute key")?;
        if let Some(value) = &attr.value {
            validate_token(root_source, local_source, value, base, "attribute value")?;
        }
        if let Some(inner_value) = &attr.inner_value {
            validate_token(
                root_source,
                local_source,
                inner_value,
                base,
                "attribute inner value",
            )?;
        }
        items.push(TagItemModel::Attr(AttrModel {
            span: Span::from_token(&attr.token).offset(base),
            key: Span::from_token(&attr.key).offset(base),
            value: attr
                .value
                .as_ref()
                .map(|value| Span::from_token(value).offset(base)),
        }));
    }
    let mut seen_comments = std::collections::HashSet::new();
    for comment in &tag.comments {
        validate_token(
            root_source,
            local_source,
            &comment.token,
            base,
            "start tag comment",
        )?;
        let span = Span::from_token(&comment.token).offset(base);
        if seen_comments.insert((span.start, span.end)) {
            items.push(TagItemModel::Comment(span));
        }
    }
    items.sort_by_key(|item| item.span().start);
    validate_tag_items(root_source, tag_span, name_span, delimiter, &items)?;

    Ok(StartTagModel {
        span: tag_span,
        name: name_span,
        delimiter,
        items,
        adjacent_end_tag: None,
        layout_column: 0,
    })
}

#[derive(Clone, Copy)]
struct BodyLayoutItem {
    span: Span,
    edges: Option<ItemEdges>,
    element_index: Option<usize>,
}

/// Decide which gaps between the children of one body may become line breaks.
///
/// This is where indentation is actually won or lost. A gap only becomes a
/// `BodyGapModel` if the classification proves nothing rendered depends on it,
/// so the default is to leave whitespace exactly as the author wrote it.
fn collect_body_layout(
    context: &VisitContext<'_>,
    template: &Template,
    body_span: Span,
    parent: Option<ParentLayout<'_>>,
    model: &mut SourceModel,
) -> Result<Vec<NodeLayout>, FormatError> {
    let global_body = body_span.offset(context.base);
    let element_layouts = analyze_elements(template, parent.map(|layout| layout.name));
    let mut items = Vec::new();
    for (index, element) in template.elements.iter().enumerate() {
        let local_span = element_span(element);
        let global_span = local_span.offset(context.base);
        match element {
            // Whitespace-only text is the gap, not an item beside it. Keeping it
            // in the list would leave no gap to rewrite between its neighbours.
            TemplateElement::Text(text) if is_html_space_text(&text.token.content) => {}
            _ => items.push(BodyLayoutItem {
                span: global_span,
                edges: element_layouts[index].edges,
                element_index: Some(index),
            }),
        }
    }
    // Comments are items too, so a gap is never measured straight through one.
    // They carry no rendered edges, hence `edges: None`.
    for comment in direct_template_comments(template, context.document_comments, body_span) {
        items.push(BodyLayoutItem {
            span: Span::from_token(&comment.token).offset(context.base),
            edges: None,
            element_index: None,
        });
    }
    items.sort_by_key(|item| (item.span.start, item.span.end));
    validate_body_items(context.root_source, global_body, &items)?;

    let container = parent.map_or(ContainerKind::Root, |layout| {
        container_kind_for_tag(layout.name)
    });
    // Two reasons to treat a whole body as untouchable rather than judging each
    // gap on its own. A control-flow element that may or may not render leaves
    // the surrounding whitespace unknowable unless both its edges are block-like;
    // and one item with a sensitive edge makes the spacing around its siblings
    // load-bearing too.
    let optional_physical_control = element_layouts.iter().any(|layout| {
        layout.physical_control
            && !layout.edges.is_some_and(|edges| {
                edges.first == EdgeKind::BlockLike && edges.last == EdgeKind::BlockLike
            })
    });
    let has_sensitive_rendered_item = element_layouts.iter().any(|layout| {
        layout.edges.is_some_and(|edges| {
            edges.first == EdgeKind::Sensitive || edges.last == EdgeKind::Sensitive
        })
    });
    let has_rendered_item = items.iter().any(|item| item.edges.is_some());
    let has_unprotected_rendered_item = items.iter().any(|item| {
        item.edges.is_some()
            && !model
                .protected
                .iter()
                .any(|range| range.span.contains(item.span))
    });
    let all_rendered_items_are_protected = has_rendered_item && !has_unprotected_rendered_item;
    let protected_outer_boundaries_are_editable = !all_rendered_items_are_protected
        || (!insertion_is_protected(global_body.start, &model.protected)
            && !insertion_is_protected(global_body.end, &model.protected));
    let root_column = context
        .root_layout_column
        .or_else(|| {
            items
                .first()
                .and_then(|item| source_column(context.root_source, item.span.start).ok())
        })
        .unwrap_or(0);
    let child_indent = parent.map_or(root_column, |layout| layout.column + 2);
    let closing_indent = parent.map_or(
        context.root_closing_column.unwrap_or(root_column),
        |layout| layout.column,
    );
    let normalize_body_gaps = context.editable
        && !optional_physical_control
        && !has_sensitive_rendered_item
        && protected_outer_boundaries_are_editable;

    let mut gap_classes = Vec::with_capacity(items.len() + 1);
    let mut cursor = global_body.start;
    for index in 0..=items.len() {
        let end = items
            .get(index)
            .map_or(global_body.end, |item| item.span.start);
        let span = Span { start: cursor, end };
        let content = context
            .root_source
            .get(span.start..span.end)
            .ok_or_else(|| {
                FormatError::invalid_span(
                    "structural body gap is not valid UTF-8 source",
                    span.start..span.end,
                )
            })?;
        if !is_html_space_text(content) {
            return Err(FormatError::invalid_span(
                "body gap contains non-whitespace source",
                span.start..span.end,
            ));
        }
        let left = items[..index]
            .iter()
            .rev()
            .find_map(|item| item.edges.map(|edges| edges.last));
        let right = items[index..]
            .iter()
            .find_map(|item| item.edges.map(|edges| edges.first));
        let class = classify_gap(GapContext {
            container,
            left,
            right,
            authored_whitespace: !content.is_empty(),
            protected: false,
        });
        if normalize_body_gaps
            && class == WhitespaceClass::Structural
            && (!all_rendered_items_are_protected || index == 0 || index == items.len())
        {
            model.body_gaps.push(BodyGapModel {
                span,
                indent: if index == items.len() {
                    closing_indent
                } else {
                    child_indent
                },
            });
        }
        gap_classes.push(class);
        if let Some(item) = items.get(index) {
            cursor = item.span.end;
        }
    }

    let mut nodes = template
        .elements
        .iter()
        .map(|element| NodeLayout {
            column: source_column(
                context.root_source,
                element_span(element).offset(context.base).start,
            )
            .ok()
            .unwrap_or(child_indent),
            body_editable: true,
        })
        .collect::<Vec<_>>();
    for (item_index, item) in items.iter().enumerate() {
        let Some(element_index) = item.element_index else {
            continue;
        };
        if (normalize_body_gaps
            && gap_classes[item_index] == WhitespaceClass::Structural
            && (!all_rendered_items_are_protected || item_index == 0))
            || (parent.is_none() && context.root_layout_column.is_some())
        {
            nodes[element_index].column = child_indent;
        }
        let ElementLayout {
            edges,
            physical_control,
            ..
        } = element_layouts[element_index];
        if physical_control
            && !edges.is_some_and(|edges| {
                edges.first == EdgeKind::BlockLike && edges.last == EdgeKind::BlockLike
            })
        {
            nodes[element_index].body_editable = false;
        }
    }
    Ok(nodes)
}

fn validate_body_items(
    source: &str,
    body: Span,
    items: &[BodyLayoutItem],
) -> Result<(), FormatError> {
    let mut cursor = body.start;
    for item in items {
        if item.span.start < cursor || item.span.end > body.end {
            return Err(FormatError::invalid_span(
                "body items overlap or lie outside their body",
                item.span.start..item.span.end,
            ));
        }
        source.get(item.span.start..item.span.end).ok_or_else(|| {
            FormatError::invalid_span(
                "body item is not valid UTF-8 source",
                item.span.start..item.span.end,
            )
        })?;
        cursor = item.span.end;
    }
    Ok(())
}

fn validate_tag_items(
    source: &str,
    tag: Span,
    name: Span,
    delimiter: Span,
    items: &[TagItemModel],
) -> Result<(), FormatError> {
    if !tag.contains(name) || !tag.contains(delimiter) || name.end > delimiter.start {
        return Err(FormatError::invalid_span(
            "start tag child span lies outside its tag",
            tag.start..tag.end,
        ));
    }
    let mut cursor = name.end;
    for item in items {
        let span = item.span();
        if span.start < cursor || span.end > delimiter.start {
            return Err(FormatError::invalid_span(
                "start tag items overlap or are out of order",
                span.start..span.end,
            ));
        }
        if !is_html_space_text(&source[cursor..span.start]) {
            return Err(FormatError::invalid_span(
                "start tag item gap contains non-whitespace source",
                cursor..span.start,
            ));
        }
        cursor = span.end;
    }
    if !is_html_space_text(&source[cursor..delimiter.start]) {
        return Err(FormatError::invalid_span(
            "start tag delimiter gap contains non-whitespace source",
            cursor..delimiter.start,
        ));
    }
    Ok(())
}

fn validate_token(
    root_source: &str,
    local_source: &str,
    token: &Token,
    base: usize,
    label: &str,
) -> Result<(), FormatError> {
    let local = token.start_index..token.end_index;
    let global = base + token.start_index..base + token.end_index;
    if local_source.get(local) == Some(token.content.as_str())
        && root_source.get(global.clone()) == Some(token.content.as_str())
    {
        Ok(())
    } else {
        Err(FormatError::invalid_span(
            format!("{label} span does not match its source content"),
            global,
        ))
    }
}

fn validate_local_span(
    local_source: &str,
    span: Span,
    base: usize,
    label: &str,
) -> Result<(), FormatError> {
    if local_source.get(span.start..span.end).is_some() {
        Ok(())
    } else {
        Err(FormatError::invalid_span(
            format!("{label} span is not valid UTF-8 source"),
            base + span.start..base + span.end,
        ))
    }
}

fn source_column(source: &str, at: usize) -> Result<usize, FormatError> {
    let before = source.get(..at).ok_or_else(|| {
        FormatError::invalid_span("layout position is not valid UTF-8 source", at..at)
    })?;
    let line_start = before
        .char_indices()
        .rev()
        .find_map(|(index, character)| {
            matches!(character, '\n' | '\r').then_some(index + character.len_utf8())
        })
        .unwrap_or(0);
    Ok(source[line_start..at].chars().count())
}

pub(crate) fn nested_template_source(content: &str) -> (usize, &str, bool) {
    let without_leading = content.trim_start_matches(is_html_ascii_whitespace);
    let leading = content.len() - without_leading.len();
    let trimmed = without_leading.trim_end_matches(is_html_ascii_whitespace);
    let trailing = without_leading.len() - trimmed.len();
    let trimmed_end = content.len() - trailing;
    let trimmed = &content[leading..trimmed_end];
    if let Some(inner_with_close) = trimmed.strip_prefix("<>")
        && let Some(inner) = inner_with_close.strip_suffix("</>")
    {
        return (leading + 2, inner, true);
    }
    (0, content, false)
}

const fn is_html_ascii_whitespace(character: char) -> bool {
    matches!(character, '\t' | '\n' | '\u{000C}' | '\r' | ' ')
}

pub(crate) fn direct_template_comments<'a>(
    template: &Template,
    document_comments: &'a [Comment],
    body_span: Span,
) -> Vec<&'a Comment> {
    let element_spans = template
        .elements
        .iter()
        .map(element_span)
        .collect::<Vec<_>>();
    let mut seen = std::collections::HashSet::new();
    let mut comments = document_comments
        .iter()
        .filter(|comment| comment.token.content.starts_with("{#"))
        .filter(|comment| {
            let span = Span::from_token(&comment.token);
            body_span.contains(span)
                && !element_spans
                    .iter()
                    .any(|element_span| element_span.contains(span))
                && seen.insert((span.start, span.end))
        })
        .collect::<Vec<_>>();
    comments.sort_by_key(|comment| comment.token.start_index);
    comments
}

pub(crate) fn element_span(element: &TemplateElement) -> Span {
    match element {
        TemplateElement::Node(Node::SelfClosing { start_tag, .. }) => {
            Span::from_token(&start_tag.token)
        }
        TemplateElement::Node(Node::WithBody {
            start_tag, end_tag, ..
        }) => Span {
            start: start_tag.token.start_index,
            end: end_tag.token.end_index,
        },
        TemplateElement::Expr(expr) => Span::from_token(&expr.token),
        TemplateElement::Text(text) => Span::from_token(&text.token),
        TemplateElement::Foreign(part) => Span::from_token(&part.token),
    }
}

pub(crate) fn is_html_space_text(content: &str) -> bool {
    content.chars().all(|character| {
        matches!(
            character,
            '\u{0009}' | '\u{000a}' | '\u{000c}' | '\u{000d}' | ' '
        )
    })
}
