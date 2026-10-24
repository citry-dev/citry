//! Browser-state-aware facts for settled HTML security validation.

use std::borrow::Cow;
use std::cell::{Cell, RefCell};
use std::convert::Infallible;

use html5ever::tendril::StrTendril;
use html5ever::tokenizer::states::RawKind;
use html5ever::tokenizer::{Doctype, Tag, TagKind, Token, TokenSink, TokenSinkResult};
use html5ever::tree_builder::create_element;
use html5ever::tree_builder::{ElementFlags, NodeOrText, QuirksMode, TreeBuilder, TreeSink};
use html5ever::{namespace_url, ns, Attribute, ExpandedName, LocalName, ParseOpts, QualName};
use html5gum::emitters::callback::{Callback, CallbackEmitter, CallbackEvent};
use html5gum::{Emitter, Error, ForwardingEmitter, Span, State, Tokenizer};
use markup5ever_rcdom::{Handle, NodeData, RcDom};

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

/// Receives each start tag's facts as soon as the start tag ends at its `>`,
/// with the index the tag keeps in the returned facts when it is a `script`
/// or `style`, and where the browser put the element the tag made.
pub(crate) type StartTagObserver<'a> = dyn FnMut(&OutputTag, Option<usize>, &TagContext) + 'a;

/// Where the browser put the element a start tag made. It is read from the
/// tree the parser builds, so an implied end tag or a misnested tag moves
/// the element the way it moves in the browser.
#[derive(Default)]
pub(crate) struct TagContext {
    // The element this start tag inserted, or `None` when the parser did
    // not insert one (an ignored tag, or a scan that does not track this).
    element: Option<Handle>,
    // The parser tied the element to the form its form pointer names (the
    // last `<form>` not yet closed by `</form>`), even when the element
    // lands outside that form in the tree.
    parser_form_owner: bool,
}

impl TagContext {
    /// Whether a `<form>` owns the element, as the browser decides it for an
    /// element the parser creates, so a submit button or field can submit
    /// that form without JavaScript.
    ///
    /// The answer is read when the parser inserts the element. When the
    /// parser later moves an element it did not tie to a form, as it does
    /// for a misnested formatting end tag such as `</b>`, the browser
    /// recomputes the owner and this answer can be stale.
    pub(crate) fn has_form_owner(&self) -> bool {
        if self.parser_form_owner {
            return true;
        }
        let Some(element) = &self.element else {
            return false;
        };
        // Only an HTML element can belong to a form; a `<button>` inside
        // `<svg>` is an SVG element that does nothing on its own.
        if !matches!(&element.data, NodeData::Element { name, .. } if name.ns == ns!(html)) {
            return false;
        }
        // An element the parser did not tie to a form gets the nearest
        // `<form>` that contains it when it is inserted. This happens, for
        // example, after a `</form>` inside a still-open element clears the
        // form pointer.
        let mut node = parent_of(element);
        while let Some(current) = node {
            match &current.data {
                NodeData::Element { name, .. }
                    if name.ns == ns!(html) && name.local.as_ref() == "form" =>
                {
                    return true;
                }
                // A template's contents are a separate document, so a form
                // outside the template does not own what is inside it.
                NodeData::Document => return false,
                _ => {}
            }
            node = parent_of(&current);
        }
        false
    }

    /// The `data-cid-*` suffixes of the elements that contain this one,
    /// nearest element first, and one element's suffixes in attribute
    /// order. An element inside a `<template>` counts the template and what
    /// contains it. Like [`TagContext::has_form_owner`], this is read when the
    /// parser inserts the element, so a later move is not seen.
    pub(crate) fn ancestor_cids(&self) -> Vec<String> {
        let mut cids = Vec::new();
        let Some(element) = &self.element else {
            return cids;
        };
        let mut node = parent_of(element);
        while let Some(current) = node {
            if let NodeData::Element { attrs, .. } = &current.data {
                for attr in attrs.borrow().iter() {
                    let name = attr.name.local.as_ref();
                    if let Some(suffix) = ascii_lower(name).strip_prefix("data-cid-") {
                        cids.push(suffix.to_owned());
                    }
                }
            }
            node = parent_of(&current);
        }
        cids
    }
}

fn ascii_lower(value: &str) -> Cow<'_, str> {
    if value.bytes().any(|byte| byte.is_ascii_uppercase()) {
        Cow::Owned(value.to_ascii_lowercase())
    } else {
        Cow::Borrowed(value)
    }
}

/// The node's parent in the tree the parser built, if it has one.
fn parent_of(node: &Handle) -> Option<Handle> {
    // The parent is a weak pointer kept in a `Cell`, so take it out, upgrade
    // it, and put it back.
    let weak = node.parent.take()?;
    let parent = weak.upgrade();
    node.parent.set(Some(weak));
    parent
}

/// The DOM the output check builds, which also remembers the element each
/// start tag made, so the check can read where the browser put it.
#[derive(Default)]
pub(crate) struct TrackingSink {
    dom: RcDom,
    // The element the latest `create_element` made, cleared before each
    // start tag is processed.
    last_created: RefCell<Option<Handle>>,
    // Whether the parser tied that element to the form its form pointer
    // names.
    form_associated: Cell<bool>,
}

impl TreeSink for TrackingSink {
    type Handle = Handle;
    type Output = RcDom;
    type ElemName<'a> = ExpandedName<'a>;

    fn finish(self) -> RcDom {
        self.dom
    }

    fn parse_error(&self, msg: Cow<'static, str>) {
        self.dom.parse_error(msg);
    }

    fn get_document(&self) -> Handle {
        self.dom.get_document()
    }

    fn elem_name<'a>(&'a self, target: &'a Handle) -> ExpandedName<'a> {
        self.dom.elem_name(target)
    }

    fn create_element(&self, name: QualName, attrs: Vec<Attribute>, flags: ElementFlags) -> Handle {
        let template = flags.template;
        let element = self.dom.create_element(name, attrs, flags);
        if template {
            // The parser puts a template's children in a separate fragment
            // that has no parent. Pointing the fragment at its template lets
            // the walk up from an element inside a `<template>` reach the
            // component around it. html5ever and RcDom reach the fragment
            // only through `get_template_contents` and never read its
            // parent, and the tree is dropped after the scan.
            if let NodeData::Element {
                template_contents, ..
            } = &element.data
            {
                if let Some(contents) = template_contents.borrow().as_ref() {
                    contents.parent.set(Some(std::rc::Rc::downgrade(&element)));
                }
            }
        }
        *self.last_created.borrow_mut() = Some(element.clone());
        self.form_associated.set(false);
        element
    }

    fn create_comment(&self, text: StrTendril) -> Handle {
        self.dom.create_comment(text)
    }

    fn create_pi(&self, target: StrTendril, data: StrTendril) -> Handle {
        self.dom.create_pi(target, data)
    }

    fn append(&self, parent: &Handle, child: NodeOrText<Handle>) {
        self.dom.append(parent, child);
    }

    fn append_based_on_parent_node(
        &self,
        element: &Handle,
        prev_element: &Handle,
        child: NodeOrText<Handle>,
    ) {
        self.dom
            .append_based_on_parent_node(element, prev_element, child);
    }

    fn append_doctype_to_document(
        &self,
        name: StrTendril,
        public_id: StrTendril,
        system_id: StrTendril,
    ) {
        self.dom
            .append_doctype_to_document(name, public_id, system_id);
    }

    fn get_template_contents(&self, target: &Handle) -> Handle {
        self.dom.get_template_contents(target)
    }

    fn same_node(&self, x: &Handle, y: &Handle) -> bool {
        self.dom.same_node(x, y)
    }

    fn set_quirks_mode(&self, mode: QuirksMode) {
        self.dom.set_quirks_mode(mode);
    }

    fn append_before_sibling(&self, sibling: &Handle, new_node: NodeOrText<Handle>) {
        self.dom.append_before_sibling(sibling, new_node);
    }

    fn add_attrs_if_missing(&self, target: &Handle, attrs: Vec<Attribute>) {
        self.dom.add_attrs_if_missing(target, attrs);
    }

    fn associate_with_form(
        &self,
        target: &Handle,
        form: &Handle,
        nodes: (&Handle, Option<&Handle>),
    ) {
        // The parser calls this when it creates a control while its form
        // pointer (the last `<form>` not yet closed by `</form>`) is set,
        // which makes that form the control's owner even if the control
        // lands outside it. Only the element the current start tag made
        // counts, because the flag is read for that tag.
        if self
            .last_created
            .borrow()
            .as_ref()
            .is_some_and(|created| std::rc::Rc::ptr_eq(created, target))
        {
            self.form_associated.set(true);
        }
        self.dom.associate_with_form(target, form, nodes);
    }

    fn remove_from_parent(&self, target: &Handle) {
        self.dom.remove_from_parent(target);
    }

    fn reparent_children(&self, node: &Handle, new_parent: &Handle) {
        self.dom.reparent_children(node, new_parent);
    }

    fn is_mathml_annotation_xml_integration_point(&self, handle: &Handle) -> bool {
        self.dom.is_mathml_annotation_xml_integration_point(handle)
    }
}

struct ScannerCallback<'a, S> {
    sink: &'a mut S,
    facts: &'a mut Vec<OutputTag>,
    collect_facts: bool,
    // With an observer, only `script` and `style` facts are kept, because
    // their element end arrives later; the observer has seen every other tag.
    observer: Option<&'a mut StartTagObserver<'a>>,
    input: &'a [u8],
    current_tag: Option<Tag>,
    current_fact: Option<OutputTag>,
    next_state: Option<State>,
    raw_stack: Vec<(String, usize)>,
    boundary: Option<&'a mut BoundaryTracker>,
    lexical_text: Option<&'a mut LexicalTextTracker>,
}

trait ScannerSink: TokenSink {
    fn has_unacknowledged_self_closing(&self) -> bool;
    /// Forget the element the previous start tag made.
    fn begin_start_tag(&self) {}
    /// Where the browser put the element the start tag named `name` made,
    /// or an empty context when this scan does not track elements.
    fn tag_context(&self, _name: &str) -> TagContext {
        TagContext::default()
    }
}

fn has_unacknowledged_self_closing(dom: &RcDom) -> bool {
    // html5ever 0.29's TreeBuilder emits this exact diagnostic after it
    // processes a self-closing flag in the element's actual namespace.
    // The regression tests below deliberately pin that dependency contract.
    dom.errors
        .borrow()
        .iter()
        .any(|error| error.as_ref() == "Unacknowledged self-closing tag")
}

impl ScannerSink for TreeBuilder<Handle, RcDom> {
    fn has_unacknowledged_self_closing(&self) -> bool {
        has_unacknowledged_self_closing(&self.sink)
    }
}

impl ScannerSink for TreeBuilder<Handle, TrackingSink> {
    fn has_unacknowledged_self_closing(&self) -> bool {
        has_unacknowledged_self_closing(&self.sink.dom)
    }

    fn begin_start_tag(&self) {
        *self.sink.last_created.borrow_mut() = None;
        self.sink.form_associated.set(false);
    }

    fn tag_context(&self, name: &str) -> TagContext {
        // Only the element this tag made counts. The parser may have made
        // none (an ignored tag), it turns `<image>` into `<img>`, and inside
        // `<svg>` it gives some names capitals (`foreignObject`).
        let element = self.sink.last_created.borrow().clone().filter(|element| {
            matches!(&element.data, NodeData::Element { name: qual, .. }
                if qual.local.as_ref().eq_ignore_ascii_case(name)
                    || (name == "image" && qual.local.as_ref() == "img"))
        });
        TagContext {
            parser_form_owner: element.is_some() && self.sink.form_associated.get(),
            element,
        }
    }
}

#[derive(Default)]
struct BoundaryTracker {
    stack: Vec<String>,
    invalid: bool,
    // The first tokenizer error the fragment check refuses, by its name in
    // the HTML standard, so the caller can say what to fix.
    parse_error: Option<&'static str>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct LexicalTextRun {
    pub parent_open: usize,
    pub child_index: usize,
    pub value: String,
}

struct LexicalFrame {
    tag: String,
    open_id: usize,
    children: usize,
    last_was_text: bool,
}

struct LexicalTextTracker {
    frames: Vec<LexicalFrame>,
    next_open_id: usize,
    runs: Vec<LexicalTextRun>,
    valid: bool,
}

impl Default for LexicalTextTracker {
    fn default() -> Self {
        Self {
            frames: vec![LexicalFrame {
                tag: String::new(),
                open_id: 0,
                children: 0,
                last_was_text: false,
            }],
            next_open_id: 1,
            runs: Vec::new(),
            valid: true,
        }
    }
}

impl LexicalTextTracker {
    fn open(&mut self, tag: &str, self_closing: bool) {
        let parent = self.frames.last_mut().expect("fragment frame exists");
        parent.children += 1;
        parent.last_was_text = false;
        let is_void = crate::transformer::is_void_element(tag.as_bytes());
        if self_closing && !is_void {
            self.valid = false;
        }
        if !is_void && !self_closing {
            let open_id = self.next_open_id;
            self.next_open_id += 1;
            self.frames.push(LexicalFrame {
                tag: tag.to_owned(),
                open_id,
                children: 0,
                last_was_text: false,
            });
        } else {
            self.next_open_id += 1;
        }
    }

    fn close(&mut self, tag: &str) {
        if self.frames.len() <= 1 || self.frames.last().is_none_or(|frame| frame.tag != tag) {
            self.valid = false;
            return;
        }
        self.frames.pop();
        self.frames
            .last_mut()
            .expect("fragment frame exists")
            .last_was_text = false;
    }

    fn text(&mut self, value: &[u8]) {
        if value.is_empty() {
            return;
        }
        let value = String::from_utf8_lossy(value);
        let frame = self.frames.last_mut().expect("fragment frame exists");
        if frame.last_was_text {
            self.runs
                .last_mut()
                .expect("adjacent text exists")
                .value
                .push_str(&value);
        } else {
            self.runs.push(LexicalTextRun {
                parent_open: frame.open_id,
                child_index: frame.children,
                value: value.into_owned(),
            });
            frame.children += 1;
            frame.last_was_text = true;
        }
    }

    fn comment(&mut self) {
        // A comment is one child node. The structure check decides whether
        // this particular comment was expected; here it only separates the
        // text on either side into distinct sibling positions.
        let frame = self.frames.last_mut().expect("fragment frame exists");
        frame.children += 1;
        frame.last_was_text = false;
    }
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
                self.current_fact = self.collect_facts.then_some(OutputTag {
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
                if let (Some(tag), Some(tracker)) =
                    (self.current_tag.as_ref(), self.lexical_text.as_deref_mut())
                {
                    tracker.open(tag.name.as_ref(), self_closing);
                }
                if let (Some(tag), Some(boundary)) =
                    (self.current_tag.as_ref(), self.boundary.as_deref_mut())
                {
                    let name = tag.name.as_ref();
                    let void = crate::transformer::is_void_element(name.as_bytes());
                    if !void && !self_closing {
                        boundary.stack.push(name.to_owned());
                    }
                }
                let mut context = TagContext::default();
                if let Some(mut tag) = self.current_tag.take() {
                    tag.self_closing = self_closing;
                    let name = tag.name.as_ref().to_owned();
                    self.sink.begin_start_tag();
                    self.sink_token(Token::TagToken(tag));
                    // Only the observer reads the context, so a scan without
                    // one skips the lookup.
                    if self.observer.is_some() {
                        context = self.sink.tag_context(&name);
                    }
                    // The tree builder asks the tokenizer to change state
                    // after a start tag only when it will read that
                    // element's contents as text (`<iframe>`, `<textarea>`,
                    // `<script>` and the like). The browser ignores the `/`
                    // on such a tag and reads the rest of the input as its
                    // text, so the fragment does not end where it seems to.
                    // html5ever logs no unacknowledged self-closing error
                    // here, because it returns before it checks the flag.
                    if self_closing && self.next_state.is_some() {
                        if let Some(boundary) = self.boundary.as_deref_mut() {
                            boundary.invalid = true;
                        }
                    }
                }
                if let Some(mut fact) = self.current_fact.take() {
                    fact.end = span.end;
                    repair_attribute_value_spans(self.input, &mut fact);
                    let raw = matches!(fact.name.as_str(), "script" | "style");
                    let keep = raw || self.observer.is_none();
                    if let Some(observer) = self.observer.as_deref_mut() {
                        observer(&fact, raw.then_some(self.facts.len()), &context);
                    }
                    if keep {
                        self.facts.push(fact);
                        let index = self.facts.len() - 1;
                        if raw {
                            self.raw_stack.push((self.facts[index].name.clone(), index));
                        }
                    }
                }
            }
            CallbackEvent::EndTag { name } => {
                let decoded = String::from_utf8_lossy(name).into_owned();
                if let Some(tracker) = self.lexical_text.as_deref_mut() {
                    tracker.close(&decoded);
                }
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
                if let Some(tracker) = self.lexical_text.as_deref_mut() {
                    tracker.text(value);
                }
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
            CallbackEvent::Comment { value } => {
                if let Some(tracker) = self.lexical_text.as_deref_mut() {
                    tracker.comment();
                }
                self.sink_token(Token::CommentToken(StrTendril::from_slice(
                    &String::from_utf8_lossy(value),
                )));
            }
            CallbackEvent::Doctype {
                name,
                public_identifier,
                system_identifier,
                force_quirks,
            } => {
                if let Some(tracker) = self.lexical_text.as_deref_mut() {
                    tracker.valid = false;
                }
                self.sink_token(Token::DoctypeToken(Doctype {
                    name: Some(name)
                        .filter(|value| !value.is_empty())
                        .map(|value| StrTendril::from_slice(&String::from_utf8_lossy(value))),
                    public_id: public_identifier
                        .map(|value| StrTendril::from_slice(&String::from_utf8_lossy(value))),
                    system_id: system_identifier
                        .map(|value| StrTendril::from_slice(&String::from_utf8_lossy(value))),
                    force_quirks,
                }));
            }
            CallbackEvent::Error(error) => {
                // These two errors leave the browser's tree exactly as
                // written, so they do not fail the parse; every other error
                // still fails the page parse.
                if !error_keeps_input_as_written(error) {
                    if let Some(tracker) = self.lexical_text.as_deref_mut() {
                        tracker.valid = false;
                    }
                }
                // A fragment check also lets a character reference error
                // pass: the reference decodes to text, so it cannot open or
                // close an element.
                if !error_keeps_input_as_written(error) && !is_character_reference_error(error) {
                    if let Some(boundary) = self.boundary.as_deref_mut() {
                        boundary.invalid = true;
                        boundary.parse_error.get_or_insert(error.as_str());
                    }
                }
                // Tokenizer errors stop here, as in the browser, whose tree
                // builder never sees them. html5ever's tree builder would
                // count an error as the token after `<pre>`, `<listing>` or
                // `<textarea>`, and html5gum reports a character's error
                // before the text holding it, so forwarding the error would
                // keep the newline after those tags that the browser drops.
            }
        }
        None
    }
}

/// Whether the browser keeps the input exactly as written despite this
/// tokenizer error, so the full page parse
/// ([`parse_div_fragment_with_lexical_text`]) and
/// [`validate_html_fragment_boundary`] let it pass.
///
/// The HTML standard reports a control character (other than ASCII
/// whitespace and NUL) and a Unicode noncharacter in the input as parse
/// errors, but parses those characters "as-is": they reach the DOM
/// unchanged wherever they appear (text, attribute value, comment or name),
/// and the tree is the same as without the error. They are also the only
/// errors the server's escaped text and attribute values can hold, because
/// the server writes these characters as they are and rejects NUL and
/// carriage returns. Every other error fails the page parse; the fragment
/// check also lets a character reference error pass (see
/// `is_character_reference_error`). Both accept only explicit, correctly
/// nested markup; some of the errors they refuse also change what the
/// browser builds (a NUL is dropped, a tag left open at the end is lost). html5gum never reports `surrogate-in-input-stream`
/// for a Rust string.
fn error_keeps_input_as_written(error: Error) -> bool {
    matches!(
        error,
        Error::ControlCharacterInInputStream | Error::NoncharacterInInputStream
    )
}

/// Whether this tokenizer error is about a character reference.
///
/// The HTML standard reports a reference it can still decode as a parse
/// error: a legacy name without `;` (`&copy 2026`), an unknown name
/// (`&foo;`, kept as written), a numeric reference to a control character,
/// a noncharacter, NUL, a surrogate or a value past U+10FFFF (decoded, the
/// last three to U+FFFD, and most of U+0080 to U+009F mapped as
/// Windows-1252), and
/// `&#` with no digits (kept as written). In every case the reference
/// becomes text, so it cannot open or close an element, and a fragment
/// that holds one keeps the shape it is written with.
fn is_character_reference_error(error: Error) -> bool {
    matches!(
        error,
        Error::MissingSemicolonAfterCharacterReference
            | Error::UnknownNamedCharacterReference
            | Error::ControlCharacterReference
            | Error::NoncharacterCharacterReference
            | Error::NullCharacterReference
            | Error::SurrogateCharacterReference
            | Error::CharacterReferenceOutsideUnicodeRange
            | Error::AbsenceOfDigitsInNumericCharacterReference
    )
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
            if let Some(tracker) = self.inner.callback_mut().lexical_text.as_deref_mut() {
                tracker.valid = false;
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
            collect_facts: true,
            observer: None,
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: None,
            lexical_text: None,
        }),
    };
    Tokenizer::new_with_emitter(input, emitter)
        .finish()
        .expect("string input is infallible");
    facts
}

/// Scan `input` like [`scan_output_html`], but hand each start tag to
/// `observer` when it ends at its `>`, instead of keeping it.
///
/// The result holds only the `script` and `style` tags, in document order,
/// with their element ends filled in. The observer receives each of those
/// tags with its index in the result, and every other tag with `None`.
pub(crate) fn scan_output_html_with(
    input: &str,
    observer: &mut StartTagObserver<'_>,
) -> Vec<OutputTag> {
    let mut builder = TreeBuilder::new(TrackingSink::default(), ParseOpts::default().tree_builder);
    let mut facts = Vec::new();
    let emitter = ScannerEmitter {
        inner: CallbackEmitter::new(ScannerCallback {
            sink: &mut builder,
            facts: &mut facts,
            collect_facts: true,
            observer: Some(observer),
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: None,
            lexical_text: None,
        }),
    };
    Tokenizer::new_with_emitter(input, emitter)
        .finish()
        .expect("string input is infallible");
    facts
}

/// Parse a `div` fragment while retaining decoded source text in lexical
/// element occurrences. The DOM and source facts come from one tokenizer pass.
pub(crate) fn parse_div_fragment_with_lexical_text(
    input: &str,
) -> Option<(RcDom, Vec<LexicalTextRun>)> {
    let dom = RcDom::default();
    let context = create_element(
        &dom,
        QualName::new(None, ns!(html), LocalName::from("div")),
        Vec::new(),
    );
    let mut builder =
        TreeBuilder::new_for_fragment(dom, context, None, ParseOpts::default().tree_builder);
    let mut facts = Vec::new();
    let mut tracker = LexicalTextTracker::default();
    let emitter = ScannerEmitter {
        inner: CallbackEmitter::new(ScannerCallback {
            sink: &mut builder,
            facts: &mut facts,
            collect_facts: false,
            observer: None,
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: None,
            lexical_text: Some(&mut tracker),
        }),
    };
    Tokenizer::new_with_emitter(input, emitter)
        .finish()
        .expect("string input is infallible");
    if !tracker.valid || tracker.frames.len() != 1 {
        return None;
    }
    Some((builder.sink, tracker.runs))
}

/// Validate one strict, independently parseable HTML fragment boundary.
///
/// The accepted subset requires explicit, correctly nested tags and rejects
/// every tokenizer error except a control character (other than NUL and
/// whitespace) or a noncharacter in the input, which the browser keeps as
/// written, and a character reference error such as `&copy` without `;`,
/// which the browser reads as text (see `is_character_reference_error`).
/// It rejects a self-closed non-void HTML element such as `<div/>` or
/// `<iframe/>`, because the browser ignores the `/` there.
/// html5ever logs most of these as an unacknowledged self-closing tag; it
/// logs nothing for a tag whose contents the parser reads as text, so the
/// validator also checks for that state change. Self-closed SVG and MathML
/// elements are allowed. Other browser recovery behavior is not promised by
/// this validator. When it refuses a tokenizer error, the message names the
/// first one by its name in the HTML standard.
pub fn validate_html_fragment_boundary(input: &str) -> Result<(), String> {
    let dom = RcDom::default();
    let mut builder = TreeBuilder::new(dom, ParseOpts::default().tree_builder);
    let mut facts = Vec::new();
    let mut boundary = BoundaryTracker::default();
    let emitter = ScannerEmitter {
        inner: CallbackEmitter::new(ScannerCallback {
            sink: &mut builder,
            facts: &mut facts,
            collect_facts: true,
            observer: None,
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: Some(&mut boundary),
            lexical_text: None,
        }),
    };
    Tokenizer::new_with_emitter(input, emitter)
        .finish()
        .expect("string input is infallible");
    if let Some(name) = boundary.parse_error {
        Err(format!("opaque HTML has the HTML parse error {name}"))
    } else if boundary.invalid || !boundary.stack.is_empty() {
        Err("opaque HTML must be a self-contained strict fragment".to_owned())
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
            // In SVG and MathML, a self-closed `style` or `script` is an
            // empty element.
            "<svg><style/><script/></svg>",
            "<math><style/></math>",
            // The browser keeps control characters and noncharacters as
            // written, so the tokenizer's report of them does not count.
            "<b>a\u{7f}b</b>",
            "<b title='a\u{1}b'>a\u{80}b</b>",
            "<b>a\u{fdd0}b\u{10ffff}</b>",
            "<!--a\u{7f}b--><b>x</b>",
        ] {
            assert_eq!(
                validate_html_fragment_boundary(source),
                Ok(()),
                "{source:?}"
            );
        }
    }

    /// The text html5gum decodes from `input`, joined across its string tokens.
    fn decoded_text(input: &str) -> String {
        html5gum::Tokenizer::new(input)
            .flatten()
            .filter_map(|token| match token {
                html5gum::Token::String(value) => {
                    Some(String::from_utf8_lossy(&value).into_owned())
                }
                _ => None,
            })
            .collect()
    }

    #[test]
    fn strict_fragment_boundary_accepts_character_references_the_browser_decodes() {
        // The HTML standard calls each of these a parse error, but the
        // reference becomes text, so it cannot change where an element
        // ends. The decoded text is what the browser reads (parse5 7.3.0).
        for (source, text) in [
            ("<p>&copy 2026</p>", "\u{a9} 2026"),
            ("<p>&nbsp</p>", "\u{a0}"),
            ("<p>a&foo;b</p>", "a&foo;b"),
            ("<b>a&#127;b</b>", "a\u{7f}b"),
            ("<b>a&#xfdd0;b</b>", "a\u{fdd0}b"),
            ("<b>a&#x80;b</b>", "a\u{20ac}b"),
            ("<p>&#0;</p>", "\u{fffd}"),
            ("<p>&#xd800;</p>", "\u{fffd}"),
            ("<p>&#x110000;</p>", "\u{fffd}"),
            ("<p>&#;</p>", "&#;"),
            ("<a title='&copy 2026'>x</a>", "x"),
        ] {
            assert_eq!(
                validate_html_fragment_boundary(source),
                Ok(()),
                "{source:?}"
            );
            assert_eq!(decoded_text(source), text, "{source:?}");
        }
    }

    #[test]
    fn strict_fragment_boundary_names_the_parse_error_it_refuses() {
        assert_eq!(
            validate_html_fragment_boundary("<p a='1'b='2'>x</p>"),
            Err(
                "opaque HTML has the HTML parse error missing-whitespace-between-attributes"
                    .to_owned()
            )
        );
        assert_eq!(
            validate_html_fragment_boundary("<div>"),
            Err("opaque HTML must be a self-contained strict fragment".to_owned())
        );
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
            // The parser ignores the `/` on these and reads the rest of the
            // input as their text.
            "<iframe/><p>x</p>",
            "<textarea/>a",
            "<title/>",
            "<xmp/>",
            "<noscript/>",
            "<noembed/>",
            "<noframes/>",
            "<style/>",
            "<script/>",
            "<plaintext/>",
            "<p>x</p><iframe/>",
            // The browser drops a NUL from text, so that error still counts.
            "<b>a\u{0}b</b>",
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
