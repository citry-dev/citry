//! Browser-state-aware facts for settled HTML security validation.

use std::convert::Infallible;

use html5ever::tendril::StrTendril;
use html5ever::tokenizer::states::RawKind;
use html5ever::tokenizer::{Doctype, Tag, TagKind, Token, TokenSink, TokenSinkResult};
use html5ever::tree_builder::TreeBuilder;
use html5ever::{Attribute, LocalName, ParseOpts, QualName};
use html5gum::emitters::callback::{Callback, CallbackEmitter, CallbackEvent};
use html5gum::{Emitter, ForwardingEmitter, Span, State, Tokenizer};
use markup5ever_rcdom::{Handle, RcDom};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OutputAttribute {
    pub name: String,
    pub value: String,
    pub name_start: usize,
    pub name_end: usize,
    pub value_start: usize,
    pub value_end: usize,
    pub has_value: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OutputTag {
    pub name: String,
    pub start: usize,
    pub end: usize,
    pub name_start: usize,
    pub name_end: usize,
    pub element_end: usize,
    pub element_end_start: usize,
    pub attributes: Vec<OutputAttribute>,
}

struct ScannerCallback<'a, S> {
    sink: &'a mut S,
    facts: &'a mut Vec<OutputTag>,
    input: &'a [u8],
    current_tag: Option<Tag>,
    current_fact: Option<OutputTag>,
    next_state: Option<State>,
    raw_stack: Vec<(String, usize)>,
    boundary: Option<&'a mut BoundaryTracker>,
}

trait ScannerSink: TokenSink {
    fn has_unacknowledged_self_closing(&self) -> bool;
}

impl ScannerSink for TreeBuilder<Handle, RcDom> {
    fn has_unacknowledged_self_closing(&self) -> bool {
        // html5ever 0.29's TreeBuilder emits this exact diagnostic after it
        // processes a self-closing flag in the element's actual namespace.
        // The regression tests below deliberately pin that dependency contract.
        self.sink
            .errors
            .borrow()
            .iter()
            .any(|error| error.as_ref() == "Unacknowledged self-closing tag")
    }
}

#[derive(Default)]
struct BoundaryTracker {
    stack: Vec<String>,
    invalid: bool,
}

impl<S: ScannerSink> ScannerCallback<'_, S> {
    fn sink_token(&mut self, token: Token) {
        let result = self.sink.process_token(token, 1);
        self.next_state = match result {
            TokenSinkResult::Continue => None,
            TokenSinkResult::Script(_) => Some(State::Data),
            TokenSinkResult::Plaintext => Some(State::PlainText),
            TokenSinkResult::RawData(RawKind::Rcdata) => Some(State::RcData),
            TokenSinkResult::RawData(RawKind::Rawtext) => Some(State::RawText),
            TokenSinkResult::RawData(RawKind::ScriptData) => Some(State::ScriptData),
            TokenSinkResult::RawData(RawKind::ScriptDataEscaped(_)) => Some(State::ScriptData),
        };
    }
}

impl<S: ScannerSink> Callback<Infallible, usize> for ScannerCallback<'_, S> {
    fn handle_event(&mut self, event: CallbackEvent<'_>, span: Span<usize>) -> Option<Infallible> {
        match event {
            CallbackEvent::OpenStartTag { name } => {
                let decoded = String::from_utf8_lossy(name).into_owned();
                self.current_tag = Some(Tag {
                    kind: TagKind::StartTag,
                    name: LocalName::from(decoded.as_str()),
                    self_closing: false,
                    attrs: Vec::new(),
                });
                self.current_fact = Some(OutputTag {
                    name: decoded,
                    start: span.start,
                    end: span.end,
                    name_start: span.start + 1,
                    name_end: source_tag_name_end(self.input, span.start),
                    element_end: span.end,
                    element_end_start: span.end,
                    attributes: Vec::new(),
                });
            }
            CallbackEvent::AttributeName { name } => {
                let decoded = String::from_utf8_lossy(name).into_owned();
                if let Some(tag) = self.current_tag.as_mut() {
                    tag.attrs.push(Attribute {
                        name: QualName::new(
                            None,
                            Default::default(),
                            LocalName::from(decoded.as_str()),
                        ),
                        value: StrTendril::new(),
                    });
                }
                if let Some(fact) = self.current_fact.as_mut() {
                    fact.attributes.push(OutputAttribute {
                        name: decoded,
                        value: String::new(),
                        name_start: span.start,
                        name_end: span.end,
                        value_start: span.end,
                        value_end: span.end,
                        has_value: false,
                    });
                }
            }
            CallbackEvent::AttributeValue { value } => {
                if let Some(attr) = self
                    .current_tag
                    .as_mut()
                    .and_then(|tag| tag.attrs.last_mut())
                {
                    attr.value.push_slice(&String::from_utf8_lossy(value));
                }
                if let Some(attr) = self
                    .current_fact
                    .as_mut()
                    .and_then(|tag| tag.attributes.last_mut())
                {
                    attr.value = String::from_utf8_lossy(value).into_owned();
                    attr.value_start = span.start;
                    attr.value_end = span.end;
                }
            }
            CallbackEvent::CloseStartTag { self_closing } => {
                if let (Some(tag), Some(boundary)) =
                    (self.current_tag.as_ref(), self.boundary.as_deref_mut())
                {
                    let name = tag.name.as_ref();
                    let void = crate::transformer::is_void_element(name.as_bytes());
                    if !void && !self_closing {
                        boundary.stack.push(name.to_owned());
                    }
                }
                if let Some(mut tag) = self.current_tag.take() {
                    tag.self_closing = self_closing;
                    self.sink_token(Token::TagToken(tag));
                }
                if let Some(mut fact) = self.current_fact.take() {
                    fact.end = span.end;
                    repair_attribute_value_spans(self.input, &mut fact);
                    self.facts.push(fact);
                    let index = self.facts.len() - 1;
                    let name = &self.facts[index].name;
                    if matches!(name.as_str(), "script" | "style") {
                        self.raw_stack.push((name.clone(), index));
                    }
                }
            }
            CallbackEvent::EndTag { name } => {
                let decoded = String::from_utf8_lossy(name).into_owned();
                if let Some(boundary) = self.boundary.as_deref_mut() {
                    if crate::transformer::is_void_element(decoded.as_bytes())
                        || boundary.stack.pop().as_deref() != Some(decoded.as_str())
                    {
                        boundary.invalid = true;
                    }
                }
                if let Some(position) = self
                    .raw_stack
                    .iter()
                    .rposition(|(value, _)| *value == decoded)
                {
                    let (_, index) = self.raw_stack.remove(position);
                    self.facts[index].element_end = span.end;
                    self.facts[index].element_end_start = span.start;
                }
                self.sink_token(Token::TagToken(Tag {
                    kind: TagKind::EndTag,
                    name: LocalName::from(decoded.as_str()),
                    self_closing: false,
                    attrs: Vec::new(),
                }));
            }
            CallbackEvent::String { value } => {
                let mut first = true;
                for part in value.split(|byte| *byte == 0) {
                    if !first {
                        self.sink_token(Token::NullCharacterToken);
                    }
                    first = false;
                    self.sink_token(Token::CharacterTokens(StrTendril::from_slice(
                        &String::from_utf8_lossy(part),
                    )));
                }
            }
            CallbackEvent::Comment { value } => self.sink_token(Token::CommentToken(
                StrTendril::from_slice(&String::from_utf8_lossy(value)),
            )),
            CallbackEvent::Doctype {
                name,
                public_identifier,
                system_identifier,
                force_quirks,
            } => self.sink_token(Token::DoctypeToken(Doctype {
                name: Some(name)
                    .filter(|value| !value.is_empty())
                    .map(|value| StrTendril::from_slice(&String::from_utf8_lossy(value))),
                public_id: public_identifier
                    .map(|value| StrTendril::from_slice(&String::from_utf8_lossy(value))),
                system_id: system_identifier
                    .map(|value| StrTendril::from_slice(&String::from_utf8_lossy(value))),
                force_quirks,
            })),
            CallbackEvent::Error(error) => {
                if let Some(boundary) = self.boundary.as_deref_mut() {
                    boundary.invalid = true;
                }
                self.sink_token(Token::ParseError(error.as_str().into()));
            }
        }
        None
    }
}

struct ScannerEmitter<'a, S: ScannerSink> {
    inner: CallbackEmitter<ScannerCallback<'a, S>, Infallible, usize>,
}

impl<S: ScannerSink> ForwardingEmitter for ScannerEmitter<'_, S> {
    type Token = Infallible;

    fn inner(&mut self) -> &mut impl Emitter<Token = Self::Token> {
        &mut self.inner
    }

    fn emit_eof(&mut self) {
        self.inner.emit_eof();
        let input_end = self.inner.callback_mut().input.len();
        let open_raw = std::mem::take(&mut self.inner.callback_mut().raw_stack);
        for (_, index) in open_raw {
            self.inner.callback_mut().facts[index].element_end_start = input_end;
            self.inner.callback_mut().facts[index].element_end = input_end;
        }
        let unacknowledged_self_closing = {
            let sink = &mut self.inner.callback_mut().sink;
            let _ = sink.process_token(Token::EOFToken, 1);
            let found = sink.has_unacknowledged_self_closing();
            sink.end();
            found
        };
        if unacknowledged_self_closing {
            if let Some(boundary) = self.inner.callback_mut().boundary.as_deref_mut() {
                boundary.invalid = true;
            }
        }
    }

    fn emit_current_tag(&mut self) -> Option<State> {
        let emitted = self.inner.emit_current_tag();
        debug_assert!(emitted.is_none());
        self.inner.callback_mut().next_state.take()
    }

    fn adjusted_current_node_present_but_not_in_html_namespace(&mut self) -> bool {
        self.inner
            .callback_mut()
            .sink
            .adjusted_current_node_present_but_not_in_html_namespace()
    }
}

pub fn scan_output_html(input: &str) -> Vec<OutputTag> {
    let dom = RcDom::default();
    let mut builder = TreeBuilder::new(dom, ParseOpts::default().tree_builder);
    let mut facts = Vec::new();
    let emitter = ScannerEmitter {
        inner: CallbackEmitter::new(ScannerCallback {
            sink: &mut builder,
            facts: &mut facts,
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: None,
        }),
    };
    Tokenizer::new_with_emitter(input, emitter)
        .finish()
        .expect("string input is infallible");
    facts
}

/// Validate one strict, independently parseable HTML fragment boundary.
///
/// The accepted subset requires explicit, correctly nested tags and rejects
/// tokenizer errors. It also uses html5ever's processed-token diagnostic to
/// reject non-void HTML self-closing syntax while retaining SVG/MathML
/// self-closing elements in their foreign-content namespaces. Other browser
/// recovery behavior is not promised by this validator.
pub fn validate_html_fragment_boundary(input: &str) -> Result<(), &'static str> {
    let dom = RcDom::default();
    let mut builder = TreeBuilder::new(dom, ParseOpts::default().tree_builder);
    let mut facts = Vec::new();
    let mut boundary = BoundaryTracker::default();
    let emitter = ScannerEmitter {
        inner: CallbackEmitter::new(ScannerCallback {
            sink: &mut builder,
            facts: &mut facts,
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: Some(&mut boundary),
        }),
    };
    Tokenizer::new_with_emitter(input, emitter)
        .finish()
        .expect("string input is infallible");
    if boundary.invalid || !boundary.stack.is_empty() {
        Err("opaque HTML must be a self-contained strict fragment")
    } else {
        Ok(())
    }
}

fn repair_attribute_value_spans(input: &[u8], fact: &mut OutputTag) {
    let name_starts = fact
        .attributes
        .iter()
        .map(|attribute| attribute.name_start)
        .collect::<Vec<_>>();
    for (index, attr) in fact.attributes.iter_mut().enumerate() {
        let limit = name_starts
            .get(index + 1)
            .copied()
            .unwrap_or_else(|| fact.end.saturating_sub(1));
        let mut cursor = attr.name_end;
        while cursor < limit && is_html_space(input[cursor]) {
            cursor += 1;
        }
        if cursor >= limit || input[cursor] != b'=' {
            attr.value_start = attr.name_end;
            attr.value_end = attr.name_end;
            continue;
        }
        attr.has_value = true;
        cursor += 1;
        while cursor < limit && is_html_space(input[cursor]) {
            cursor += 1;
        }
        if cursor < limit && matches!(input[cursor], b'\'' | b'"') {
            let quote = input[cursor];
            attr.value_start = cursor + 1;
            attr.value_end = input[attr.value_start..limit]
                .iter()
                .position(|value| *value == quote)
                .map_or(limit, |offset| attr.value_start + offset);
        } else {
            attr.value_start = cursor;
            attr.value_end = input[cursor..limit]
                .iter()
                .position(|value| is_html_space(*value) || *value == b'>')
                .map_or(limit, |offset| cursor + offset);
        }
        attr.value = String::from_utf8_lossy(&input[attr.value_start..attr.value_end]).into_owned();
    }
}

fn source_tag_name_end(input: &[u8], start: usize) -> usize {
    let mut end = start + 1;
    while end < input.len() && !is_html_space(input[end]) && !matches!(input[end], b'/' | b'>') {
        end += 1;
    }
    end
}

fn is_html_space(value: u8) -> bool {
    matches!(value, b' ' | b'\t' | b'\n' | b'\r' | b'\x0c')
}

#[cfg(test)]
mod tests {
    use super::{scan_output_html, validate_html_fragment_boundary};

    #[test]
    fn strict_fragment_boundary_accepts_balanced_html_and_foreign_self_closing() {
        for source in [
            "",
            "text<!-- comment --><br>",
            "<table><tbody><tr><td>x</td></tr></tbody></table>",
            "<svg><path d='x'/><g><circle/></g></svg>",
            "<math><mi>x</mi><mspace/></math>",
        ] {
            assert_eq!(validate_html_fragment_boundary(source), Ok(()), "{source}");
        }
    }

    #[test]
    fn strict_fragment_boundary_rejects_recovery_and_cross_boundary_forms() {
        for source in [
            "<div>",
            "</div>",
            "<div/>",
            "<svg><foreignObject><div/></foreignObject></svg>",
            "<svg><g><div/></g></svg>",
            "<math><mtext><div/></mtext></math>",
            "<li>a<li>b",
            "<!-- unfinished",
            "<script>unfinished",
            "<div><span></div></span>",
        ] {
            assert!(validate_html_fragment_boundary(source).is_err(), "{source}");
        }
    }

    #[test]
    fn tree_builder_feedback_distinguishes_html_and_svg_title() {
        let html = scan_output_html("<title><script>x</script></title>");
        assert_eq!(
            html.iter().map(|tag| tag.name.as_str()).collect::<Vec<_>>(),
            ["title"]
        );

        let svg = scan_output_html("<svg><title><script>x</script></title></svg>");
        assert_eq!(
            svg.iter().map(|tag| tag.name.as_str()).collect::<Vec<_>>(),
            ["svg", "title", "script"]
        );
    }

    #[test]
    fn spans_slice_exact_utf8_source_bytes() {
        let source = "<p title='žluťoučký' onclick=go()>x</p>";
        let tag = &scan_output_html(source)[0];
        assert_eq!(
            &source.as_bytes()[tag.start..tag.end],
            b"<p title='\xc5\xbelu\xc5\xa5ou\xc4\x8dk\xc3\xbd' onclick=go()>"
        );
        assert_eq!(&source.as_bytes()[tag.name_start..tag.name_end], b"p");
        assert_eq!(
            &source.as_bytes()[tag.attributes[1].name_start..tag.attributes[1].name_end],
            b"onclick"
        );
        assert_eq!(
            &source.as_bytes()[tag.attributes[1].value_start..tag.attributes[1].value_end],
            b"go()"
        );
    }

    #[test]
    fn tree_builder_drives_foreign_breakout_and_scripting_noscript_states() {
        let cases = [
            (
                "<select><script>x</script></select>",
                vec!["select", "script"],
            ),
            ("<table><script>x</script></table>", vec!["table", "script"]),
            ("<noscript><script>x</script></noscript>", vec!["noscript"]),
            (
                "<svg><g><p><script>x</script></p></g></svg>",
                vec!["svg", "g", "p", "script"],
            ),
            ("<div/><script>x</script>", vec!["div", "script"]),
            ("<script><!--<script>still data</script>", vec!["script"]),
        ];
        for (source, expected) in cases {
            assert_eq!(
                scan_output_html(source)
                    .iter()
                    .map(|tag| tag.name.as_str())
                    .collect::<Vec<_>>(),
                expected
            );
        }
    }

    #[test]
    fn duplicate_attributes_keep_every_authored_source_range() {
        let source = "<button onclick='first()' onclick=second()>x</button>";
        let tag = &scan_output_html(source)[0];
        assert_eq!(tag.attributes.len(), 2);
        assert_eq!(tag.attributes[0].value, "first()");
        assert_eq!(tag.attributes[1].value, "second()");
        for attr in &tag.attributes {
            assert_eq!(
                &source.as_bytes()[attr.name_start..attr.name_end],
                b"onclick"
            );
        }
    }

    #[test]
    fn facts_keep_raw_entities_null_name_span_and_unclosed_raw_extent() {
        let source = "<a\0b href='java&#x73;cript:x'><script>open";
        let tags = scan_output_html(source);
        assert_eq!(
            &source.as_bytes()[tags[0].name_start..tags[0].name_end],
            b"a\0b"
        );
        assert_eq!(tags[0].attributes[0].value, "java&#x73;cript:x");
        assert_eq!(tags[1].element_end_start, source.len());
        assert_eq!(tags[1].element_end, source.len());
    }

    #[test]
    fn vertical_tab_does_not_become_html_attribute_whitespace() {
        let source = "<a href=\x0b'javascript:x'>";
        let attr = &scan_output_html(source)[0].attributes[0];
        assert_eq!(
            &source.as_bytes()[attr.value_start..attr.value_end],
            b"\x0b'javascript:x'"
        );
    }
}
