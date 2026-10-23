//! Find what Citry's strict-CSP and JavaScript-policy checks report in
//! finished HTML.
//!
//! `citry.serialize()` checks the page it is about to return when
//! `security_csp` or `security_javascript` is set. This module runs the
//! rules of those checks over the page and returns only what they found:
//! the attributes and elements a rule reports, and every `script` and
//! `style` element, because Python remembers some of those between two
//! checks of one page. Python keeps the wording of each message, the
//! bookkeeping that drops repeated findings, and the decision to warn or
//! raise, so an ordinary tag never becomes a Python object.
//!
//! The rules copy the Python checks they replace exactly, including how
//! they decode character references (Python's `html.unescape`) and how
//! they compare letters in `javascript:` (Python's case-insensitive
//! regular expression). `packages/py/citry/tests/_output_policy_reference.py`
//! keeps the Python version, and a test compares the two on generated pages.

use std::borrow::Cow;
use std::collections::HashMap;
use std::collections::HashSet;

use html5ever::data::NAMED_ENTITIES;

use crate::output_scanner::{scan_output_html, scan_output_html_with, OutputTag};

/// Which of the two checks of one page runs.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PolicyPass {
    /// The page before the `on_serialize` extension hooks run. Only its
    /// `script` and `style` elements matter, so that the later check does
    /// not report one a second time.
    PreExtension,
    /// The page after every hook has run, which is what the browser gets.
    Settled,
}

/// The `security_javascript` mode whose rules run.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum JavascriptMode {
    Warn,
    Omit,
    Forbid,
}

/// What to check and which tags Citry itself wrote.
#[derive(Clone, Copy, Debug)]
pub struct OutputPolicyOptions<'a> {
    pub pass: PolicyPass,
    /// Run the strict-CSP attribute rules.
    pub csp: bool,
    /// Run the JavaScript-policy rules of this mode.
    pub javascript: Option<JavascriptMode>,
    /// A tag with an attribute whose name starts with this prefix is one
    /// Citry wrote. `None` trusts no tag by its attributes.
    pub marker_prefix: Option<&'a str>,
    /// Byte offsets of the start tags Citry wrote without a marker.
    pub trusted_tag_starts: &'a HashSet<usize>,
    /// The private attribute Citry puts on an element whose handler it left
    /// out in `omit` mode. The check removes it from the page.
    pub omit_handler_marker: Option<&'a str>,
}

/// A rule that reports one attribute or element.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Rule {
    CspNativeEvent,
    CspJavascriptUrl,
    JsBrowserAttribute,
    JsStaticFallback,
    JsNativeHandler,
    JsJavascriptUrl,
    JsEmbeddedDocument,
    JsHandlerOnlyControl,
}

impl Rule {
    /// The name Python uses to pick the message for this rule.
    pub fn code(self) -> &'static str {
        match self {
            Rule::CspNativeEvent => "csp-native-event",
            Rule::CspJavascriptUrl => "csp-javascript-url",
            Rule::JsBrowserAttribute => "js-browser-attribute",
            Rule::JsStaticFallback => "js-static-fallback",
            Rule::JsNativeHandler => "js-native-handler",
            Rule::JsJavascriptUrl => "js-javascript-url",
            Rule::JsEmbeddedDocument => "js-embedded-document",
            Rule::JsHandlerOnlyControl => "js-handler-only-control",
        }
    }
}

/// A `script` or `style` element, which Python checks against what it
/// remembers from the check before the hooks ran.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RawElement {
    /// `script` or `style`.
    pub tag: String,
    /// Byte offset of the start tag's `<`.
    pub token_start: usize,
    /// Byte span of the tag name in the start tag.
    pub name_start: usize,
    pub name_end: usize,
    /// Byte offset just past the element: its end tag, the end of the input
    /// when it never closes, or its start tag when nothing closes it.
    pub element_end: usize,
    /// Citry wrote this tag (see [`OutputPolicyOptions::marker_prefix`]).
    pub trusted: bool,
    /// The element is a `script` the browser would run.
    pub executable: bool,
    /// An attribute name starts with `data-citry`, which marks one of
    /// Citry's browser manifests.
    pub has_manager_attribute: bool,
    /// The suffixes of the element's `data-cid-*` attributes, in attribute
    /// order. Python names the first one it knows as the component.
    pub cids: Vec<String>,
}

/// One attribute or element a rule reports.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Finding {
    pub rule: Rule,
    /// The element's tag name.
    pub tag: String,
    /// The attribute name as the tokenizer read it, or `None` for a rule
    /// that reports the element.
    pub attribute: Option<String>,
    /// Byte span the message points at.
    pub start: usize,
    pub end: usize,
    /// Byte offset of the element's start tag.
    pub token_start: usize,
    /// As in [`RawElement::cids`].
    pub cids: Vec<String>,
}

/// One entry of a report, in the order the start tags appear.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PolicyEvent {
    RawElement(RawElement),
    Finding(Finding),
}

/// What [`check_output_html`] found.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct OutputPolicyReport {
    pub events: Vec<PolicyEvent>,
    /// The page with every omit marker removed, only when one was found.
    pub cleaned_html: Option<String>,
}

/// Run the rules the options select over `html`.
///
/// The scan follows the browser's parser state, so text inside
/// `<title>` or a comment is not read as tags. It never fails: malformed
/// HTML is read the way a browser recovers from it.
pub fn check_output_html(html: &str, options: &OutputPolicyOptions<'_>) -> OutputPolicyReport {
    let marker = options.omit_handler_marker.map(str::to_lowercase);
    let mut state = CheckState {
        options,
        source: html.as_bytes(),
        marker: marker.as_deref(),
        events: Vec::new(),
        pending_raw: Vec::new(),
        marker_spans: Vec::new(),
    };
    let raw_facts = scan_output_html_with(html, &mut |tag, raw_index| state.visit(tag, raw_index));
    // A raw element's end tag arrives after its start tag was reported, so
    // the element's end is filled in once the whole page has been read.
    for (event_index, fact_index) in std::mem::take(&mut state.pending_raw) {
        let fact = &raw_facts[fact_index];
        if let PolicyEvent::RawElement(element) = &mut state.events[event_index] {
            element.element_end = fact.end.max(fact.element_end);
        }
    }
    let cleaned_html = remove_spans(html, std::mem::take(&mut state.marker_spans));
    OutputPolicyReport {
        events: state.events,
        cleaned_html,
    }
}

struct CheckState<'a, 'o> {
    options: &'o OutputPolicyOptions<'a>,
    source: &'o [u8],
    marker: Option<&'o str>,
    events: Vec<PolicyEvent>,
    // (index in `events`, index in the scanner's raw facts)
    pending_raw: Vec<(usize, usize)>,
    marker_spans: Vec<(usize, usize)>,
}

impl CheckState<'_, '_> {
    fn visit(&mut self, tag: &OutputTag, raw_index: Option<usize>) {
        let name = ascii_lower(&tag.name);
        let is_script = name == "script";
        let is_raw = is_script || name == "style";
        match self.options.pass {
            PolicyPass::PreExtension => {
                if let (true, Some(raw_index)) = (is_raw, raw_index) {
                    self.push_raw(tag, &name, raw_index, false, false);
                }
            }
            PolicyPass::Settled => self.visit_settled(tag, &name, is_script, is_raw, raw_index),
        }
    }

    fn visit_settled(
        &mut self,
        tag: &OutputTag,
        name: &str,
        is_script: bool,
        is_raw: bool,
        raw_index: Option<usize>,
    ) {
        let javascript = self.options.javascript;
        // Only the JavaScript policy removes omit markers and uses them.
        let has_managed_handler = match (javascript, self.marker) {
            (Some(_), Some(marker)) => self.collect_marker_spans(tag, marker),
            _ => false,
        };
        // The CSP check looks at every raw element, the JavaScript policy at
        // scripts only.
        if let (true, Some(raw_index)) = (
            is_raw && (self.options.csp || (javascript.is_some() && is_script)),
            raw_index,
        ) {
            let trusted = self.is_trusted(tag);
            let has_manager_attribute = tag
                .attributes
                .iter()
                .any(|attr| ascii_lower(&attr.name).starts_with("data-citry"));
            self.push_raw(tag, name, raw_index, trusted, has_manager_attribute);
        }

        // The decoded value of each attribute's first occurrence, which the
        // omit-mode rules read. It is built only when one of them runs.
        let mut first_values: Option<HashMap<Cow<'_, str>, Cow<'_, str>>> = None;
        let mut activation_attrs: Vec<Cow<'_, str>> = Vec::new();
        for attr in &tag.attributes {
            let attr_name = ascii_lower(&attr.name);
            let raw_value: &str = if attr.has_value { &attr.value } else { "" };
            // A value-less attribute points at the end of its name.
            let value_start = if attr.has_value {
                attr.value_start
            } else {
                attr.name_end
            };
            let value_end = value_start + raw_value.len();
            let mut decoded: Option<Cow<'_, str>> = None;
            let url_attribute = is_url_attribute(name, &attr_name);
            if self.options.csp {
                if is_native_event_attribute(&attr_name) {
                    self.push_finding(
                        Rule::CspNativeEvent,
                        tag,
                        name,
                        Some(&attr.name),
                        attr.name_start,
                        attr.name_end,
                    );
                }
                if url_attribute
                    && is_javascript_url(
                        decoded.get_or_insert_with(|| decode_html_attribute(raw_value)),
                    )
                {
                    self.push_finding(
                        Rule::CspJavascriptUrl,
                        tag,
                        name,
                        Some(&attr.name),
                        value_start,
                        value_end,
                    );
                }
            }
            let Some(mode) = javascript else {
                continue;
            };
            if is_activation_attribute(&attr_name) {
                activation_attrs.push(attr_name.clone());
                match mode {
                    JavascriptMode::Warn | JavascriptMode::Forbid => {
                        self.push_finding(
                            Rule::JsBrowserAttribute,
                            tag,
                            name,
                            Some(&attr.name),
                            attr.name_start,
                            attr.name_end,
                        );
                    }
                    JavascriptMode::Omit => {
                        let values =
                            first_values.get_or_insert_with(|| first_attribute_values(tag));
                        if is_omit_hazard(&attr_name, values) {
                            self.push_finding(
                                Rule::JsStaticFallback,
                                tag,
                                name,
                                Some(&attr.name),
                                attr.name_start,
                                attr.name_end,
                            );
                        }
                    }
                }
            }
            if is_native_event_attribute(&attr_name) {
                self.push_finding(
                    Rule::JsNativeHandler,
                    tag,
                    name,
                    Some(&attr.name),
                    attr.name_start,
                    attr.name_end,
                );
            }
            if url_attribute
                && is_javascript_url(
                    decoded.get_or_insert_with(|| decode_html_attribute(raw_value)),
                )
            {
                self.push_finding(
                    Rule::JsJavascriptUrl,
                    tag,
                    name,
                    Some(&attr.name),
                    value_start,
                    value_end,
                );
            }
            if may_embed_document(name, &attr_name)
                && embedded_document_requires_javascript(
                    name,
                    &attr_name,
                    decoded.get_or_insert_with(|| decode_html_attribute(raw_value)),
                )
            {
                self.push_finding(
                    Rule::JsEmbeddedDocument,
                    tag,
                    name,
                    Some(&attr.name),
                    value_start,
                    value_end,
                );
            }
        }
        if javascript == Some(JavascriptMode::Omit)
            && (!activation_attrs.is_empty() || has_managed_handler)
        {
            let values = first_values.get_or_insert_with(|| first_attribute_values(tag));
            if is_handler_only_control(name, values, &activation_attrs, has_managed_handler) {
                self.push_finding(
                    Rule::JsHandlerOnlyControl,
                    tag,
                    name,
                    None,
                    tag.name_start,
                    tag.name_end,
                );
            }
        }
    }

    fn is_trusted(&self, tag: &OutputTag) -> bool {
        self.options.trusted_tag_starts.contains(&tag.start)
            || self.options.marker_prefix.is_some_and(|prefix| {
                tag.attributes
                    .iter()
                    .any(|attr| ascii_lower(&attr.name).starts_with(prefix))
            })
    }

    /// Record the byte span that removes each omit marker from this tag, and
    /// say whether the tag had one.
    fn collect_marker_spans(&mut self, tag: &OutputTag, marker: &str) -> bool {
        let raw = self.source;
        let mut found = false;
        for attr in &tag.attributes {
            if attr.name.to_lowercase() != marker {
                continue;
            }
            found = true;
            // Take the whitespace before the marker with it, so no gap is
            // left where it stood.
            let mut start = attr.name_start;
            while start > tag.start
                && matches!(raw[start - 1], b' ' | b'\t' | b'\r' | b'\n' | b'\x0c')
            {
                start -= 1;
            }
            let mut end = attr.name_end;
            if attr.has_value {
                end = attr.value_end;
                // A quoted value takes its closing quote with it.
                if attr.value_start > 0 && matches!(raw[attr.value_start - 1], b'"' | b'\'') {
                    let quote = raw[attr.value_start - 1];
                    if end < raw.len() && raw[end] == quote {
                        end += 1;
                    }
                }
            }
            if end < tag.end
                && !matches!(
                    raw[end],
                    b' ' | b'\t' | b'\r' | b'\n' | b'\x0c' | b'/' | b'>'
                )
            {
                // A hook may place another attribute immediately after this
                // one. Keep the leading separator so removing the marker
                // cannot merge that neighbor into the tag name or the
                // previous attribute.
                start = attr.name_start;
            }
            self.marker_spans.push((start, end));
        }
        found
    }

    fn push_raw(
        &mut self,
        tag: &OutputTag,
        name: &str,
        raw_index: usize,
        trusted: bool,
        has_manager_attribute: bool,
    ) {
        let executable = name == "script" && raw_script_is_executable(tag);
        self.pending_raw.push((self.events.len(), raw_index));
        self.events.push(PolicyEvent::RawElement(RawElement {
            tag: name.to_owned(),
            token_start: tag.start,
            name_start: tag.name_start,
            name_end: tag.name_end,
            element_end: tag.end,
            trusted,
            executable,
            has_manager_attribute,
            cids: component_ids(tag),
        }));
    }

    fn push_finding(
        &mut self,
        rule: Rule,
        tag: &OutputTag,
        name: &str,
        attribute: Option<&str>,
        start: usize,
        end: usize,
    ) {
        self.events.push(PolicyEvent::Finding(Finding {
            rule,
            tag: name.to_owned(),
            attribute: attribute.map(str::to_owned),
            start,
            end,
            token_start: tag.start,
            cids: component_ids(tag),
        }));
    }
}

/// The suffix of every `data-cid-*` attribute, in attribute order.
fn component_ids(tag: &OutputTag) -> Vec<String> {
    tag.attributes
        .iter()
        .filter_map(|attr| {
            ascii_lower(&attr.name)
                .strip_prefix("data-cid-")
                .map(str::to_owned)
        })
        .collect()
}

/// Each attribute name's decoded value, taken from its first occurrence.
fn first_attribute_values(tag: &OutputTag) -> HashMap<Cow<'_, str>, Cow<'_, str>> {
    let mut values = HashMap::new();
    for attr in &tag.attributes {
        values.entry(ascii_lower(&attr.name)).or_insert_with(|| {
            decode_html_attribute(if attr.has_value { &attr.value } else { "" })
        });
    }
    values
}

/// Remove the merged spans from `html`, or return `None` when there are none.
fn remove_spans(html: &str, mut spans: Vec<(usize, usize)>) -> Option<String> {
    if spans.is_empty() {
        return None;
    }
    spans.sort_unstable();
    let mut merged: Vec<(usize, usize)> = Vec::with_capacity(spans.len());
    for (start, end) in spans {
        match merged.last_mut() {
            Some(last) if start <= last.1 => last.1 = last.1.max(end),
            _ => merged.push((start, end)),
        }
    }
    let bytes = html.as_bytes();
    let mut cleaned = Vec::with_capacity(bytes.len());
    let mut cursor = 0;
    for (start, end) in merged {
        cleaned.extend_from_slice(&bytes[cursor..start]);
        cursor = end;
    }
    cleaned.extend_from_slice(&bytes[cursor..]);
    // Every span starts and ends next to an ASCII byte the tokenizer read
    // (whitespace, a quote, or a tag or attribute boundary), so the
    // remaining bytes are still valid UTF-8.
    Some(String::from_utf8_lossy(&cleaned).into_owned())
}

fn ascii_lower(value: &str) -> Cow<'_, str> {
    if value.bytes().any(|byte| byte.is_ascii_uppercase()) {
        Cow::Owned(value.to_ascii_lowercase())
    } else {
        Cow::Borrowed(value)
    }
}

fn is_html_space(value: char) -> bool {
    matches!(value, ' ' | '\t' | '\n' | '\r' | '\x0c')
}

// ---------------------------------------------------------------------------
// Predicates on attribute names and values
// ---------------------------------------------------------------------------

/// A native inline event attribute: any lowercased name longer than `on`
/// that starts with `on`, so event names browsers add later are caught too.
pub fn is_native_event_attribute(name: &str) -> bool {
    name.len() > 2 && name.starts_with("on")
}

/// An attribute whose value the browser loads or navigates to as a URL.
pub fn is_url_attribute(tag: &str, name: &str) -> bool {
    matches!(
        name,
        "action" | "formaction" | "href" | "src" | "xlink:href"
    ) || (tag == "object" && name == "data")
}

/// A Vue directive spelling, which needs the browser runtime to mean anything.
pub fn is_activation_attribute(name: &str) -> bool {
    name.starts_with("v-") || name.starts_with('@') || name.starts_with(':')
}

/// Whether a URL value, with its character references already decoded,
/// starts with `javascript:`.
///
/// Leading U+0000 to U+0020 are skipped and a tab, line feed, or carriage
/// return may sit between any two letters, as browsers allow. Letters
/// compare the way Python's case-insensitive regular expression compares
/// them, so `ſ` (U+017F) counts as `s`, and `ı` (U+0131) and `İ` (U+0130)
/// count as `i`.
pub fn is_javascript_url(value: &str) -> bool {
    let mut chars = value
        .trim_start_matches(|c: char| c <= '\u{20}')
        .chars()
        .peekable();
    for (index, letter) in "javascript".chars().enumerate() {
        if index > 0 {
            while chars.next_if(|c| matches!(c, '\t' | '\n' | '\r')).is_some() {}
        }
        match chars.next() {
            Some(c) if letter_matches(letter, c) => {}
            _ => return false,
        }
    }
    while chars.next_if(|c| matches!(c, '\t' | '\n' | '\r')).is_some() {}
    chars.next() == Some(':')
}

fn letter_matches(letter: char, c: char) -> bool {
    c.to_ascii_lowercase() == letter && c.is_ascii()
        || match letter {
            's' => c == '\u{17f}',
            'i' => matches!(c, '\u{130}' | '\u{131}'),
            _ => false,
        }
}

/// The MIME types that make a `<script>` a classic script the browser runs.
pub const JAVASCRIPT_MIME_TYPES: [&str; 16] = [
    "text/javascript",
    "application/javascript",
    "application/ecmascript",
    "application/x-ecmascript",
    "application/x-javascript",
    "text/ecmascript",
    "text/javascript1.0",
    "text/javascript1.1",
    "text/javascript1.2",
    "text/javascript1.3",
    "text/javascript1.4",
    "text/javascript1.5",
    "text/jscript",
    "text/livescript",
    "text/x-ecmascript",
    "text/x-javascript",
];

/// Whether a `<script>` whose `type` attribute holds `value` runs in the
/// browser, judged by the type's MIME essence (the part before `;`).
pub fn script_type_is_executable(value: &str) -> bool {
    let normalized = value.trim_matches(is_html_space).to_ascii_lowercase();
    let essence = normalized
        .split(';')
        .next()
        .unwrap_or("")
        .trim_end_matches(is_html_space);
    if matches!(essence, "module" | "importmap" | "speculationrules") {
        // A parameter makes these types unknown to the browser.
        return !normalized.contains(';');
    }
    essence.is_empty() || JAVASCRIPT_MIME_TYPES.contains(&essence)
}

/// Whether a `<script>` start tag makes a script the browser runs: no
/// `type`, a repeated `type`, a `type` without a value, or a value that
/// [`script_type_is_executable`] accepts.
fn raw_script_is_executable(tag: &OutputTag) -> bool {
    let mut types = tag
        .attributes
        .iter()
        .filter(|attr| ascii_lower(&attr.name) == "type");
    let Some(first) = types.next() else {
        return true;
    };
    if types.next().is_some() || !first.has_value {
        return true;
    }
    script_type_is_executable(&decode_html_attribute(&first.value))
}

/// Whether a Vue directive leaves an unusable page once Citry leaves out
/// the JavaScript that would apply it (`omit` mode).
fn is_omit_hazard(name: &str, values: &HashMap<Cow<'_, str>, Cow<'_, str>>) -> bool {
    let base = name.split('.').next().unwrap_or(name);
    if matches!(base, "v-for" | "v-if" | "v-show" | "v-text" | "v-html") {
        return true;
    }
    let bound = match base.strip_prefix(':') {
        Some(rest) => rest,
        None => base.strip_prefix("v-bind:").unwrap_or(base),
    };
    match bound {
        "hidden" => values.contains_key("hidden"),
        "href" | "action" | "formaction" | "src" | "value" => {
            values.get(bound).is_none_or(|value| value.is_empty())
        }
        _ => false,
    }
}

/// Whether a control has a browser handler but nothing the browser does
/// without JavaScript, such as following a link or submitting a form.
///
/// Whether the control sits inside a `<form>` is not known here, so a
/// control without a `form` attribute counts as outside one.
fn is_handler_only_control(
    tag: &str,
    values: &HashMap<Cow<'_, str>, Cow<'_, str>>,
    activation_attrs: &[Cow<'_, str>],
    has_managed_handler: bool,
) -> bool {
    // A Citry-managed handler is marked on the element by the omit marker,
    // while an authored Vue handler, including the object form
    // `v-on="..."`, appears as its own activation attribute.
    let has_handler = has_managed_handler
        || activation_attrs
            .iter()
            .any(|name| name == "v-on" || name.starts_with('@') || name.starts_with("v-on:"));
    if !has_handler {
        return false;
    }
    let present = |key: &str| values.get(key).is_some_and(|value| !value.is_empty());
    match tag {
        "a" => !present("href"),
        "button" => {
            let button_type = values
                .get("type")
                .map_or(Cow::Borrowed("submit"), |value| ascii_lower(value));
            button_type == "button" || (button_type == "submit" && !present("form"))
        }
        "input" => {
            let input_type = values
                .get("type")
                .map_or(Cow::Borrowed("text"), |value| ascii_lower(value));
            matches!(input_type.as_ref(), "button" | "reset") || !present("form")
        }
        "select" | "textarea" => !present("form"),
        _ => matches!(tag, "div" | "span" | "section"),
    }
}

// ---------------------------------------------------------------------------
// Embedded documents
// ---------------------------------------------------------------------------

/// The attributes that can hold a whole HTML document.
fn may_embed_document(tag: &str, name: &str) -> bool {
    matches!(
        (tag, name),
        ("iframe", "srcdoc") | ("iframe", "src") | ("object", "data") | ("embed", "src")
    )
}

/// Whether an attribute value holds an HTML document with code the browser
/// would run: an `iframe srcdoc`, or a `data:text/html` URL in `iframe src`,
/// `object data`, or `embed src`.
fn embedded_document_requires_javascript(tag: &str, name: &str, value: &str) -> bool {
    if tag == "iframe" && name == "srcdoc" {
        return html_document_requires_javascript(value, 0);
    }
    may_embed_document(tag, name)
        && decode_html_data_url(value)
            .is_some_and(|document| html_document_requires_javascript(&document, 0))
}

// Four nested documents is deeper than any real page goes, so a deeper one
// counts as running code instead of being read further.
const MAX_EMBEDDED_DEPTH: usize = 4;

fn html_document_requires_javascript(html: &str, depth: usize) -> bool {
    if depth >= MAX_EMBEDDED_DEPTH {
        return true;
    }
    for tag in scan_output_html(html) {
        let name = ascii_lower(&tag.name);
        if name == "script" && raw_script_is_executable(&tag) {
            return true;
        }
        for attr in &tag.attributes {
            let attr_name = ascii_lower(&attr.name);
            let value = decode_html_attribute(if attr.has_value { &attr.value } else { "" });
            if is_native_event_attribute(&attr_name)
                || (is_url_attribute(&name, &attr_name) && is_javascript_url(&value))
            {
                return true;
            }
            if name == "iframe"
                && attr_name == "srcdoc"
                && html_document_requires_javascript(&value, depth + 1)
            {
                return true;
            }
            if matches!(
                (name.as_ref(), attr_name.as_ref()),
                ("iframe", "src") | ("object", "data") | ("embed", "src")
            ) && decode_html_data_url(&value)
                .is_some_and(|document| html_document_requires_javascript(&document, depth + 1))
            {
                return true;
            }
        }
    }
    false
}

/// Decode a `data:text/html` URL to its document, or return `None` for any
/// other URL.
///
/// The payload is percent-decoded, then base64-decoded when the header
/// holds `;base64`. A payload that is not valid base64 decodes to
/// `<script>`, so a document the check cannot read counts as running code.
fn decode_html_data_url(value: &str) -> Option<String> {
    let value = value.trim_start_matches(|c: char| c <= '\u{20}');
    let (header, payload) = value.split_once(',')?;
    let folded = ascii_lower(header);
    let media_type = folded
        .strip_prefix("data:")?
        .split(';')
        .next()
        .unwrap_or("")
        .trim_matches(is_html_space);
    if media_type != "text/html" {
        return None;
    }
    let bytes = percent_decode(payload.as_bytes());
    let body = if folded.contains(";base64") {
        match decode_strict_base64(&bytes) {
            Some(body) => body,
            None => return Some("<script>".to_owned()),
        }
    } else {
        bytes
    };
    Some(String::from_utf8_lossy(&body).into_owned())
}

/// Replace each `%` followed by two hex digits with the byte they name, and
/// keep any other `%` as it is.
fn percent_decode(input: &[u8]) -> Vec<u8> {
    let mut output = Vec::with_capacity(input.len());
    let mut index = 0;
    while index < input.len() {
        if input[index] == b'%' && index + 2 < input.len() {
            if let (Some(high), Some(low)) =
                (hex_value(input[index + 1]), hex_value(input[index + 2]))
            {
                output.push(high << 4 | low);
                index += 3;
                continue;
            }
        }
        output.push(input[index]);
        index += 1;
    }
    output
}

fn hex_value(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        b'A'..=b'F' => Some(byte - b'A' + 10),
        _ => None,
    }
}

/// Decode base64 that uses only the standard alphabet and exactly the
/// padding its length needs, or return `None`.
///
/// Python 3.12 and later accept exactly these inputs with
/// `base64.b64decode(validate=True)`. Bits left over in the last character
/// are ignored, as Python does.
fn decode_strict_base64(input: &[u8]) -> Option<Vec<u8>> {
    if !input.len().is_multiple_of(4) {
        return None;
    }
    let padding = input.iter().rev().take_while(|byte| **byte == b'=').count();
    if padding > 2 {
        return None;
    }
    let data = &input[..input.len() - padding];
    let mut output = Vec::with_capacity(data.len() / 4 * 3 + 2);
    let mut buffer: u32 = 0;
    let mut bits = 0;
    for &byte in data {
        let value = match byte {
            b'A'..=b'Z' => byte - b'A',
            b'a'..=b'z' => byte - b'a' + 26,
            b'0'..=b'9' => byte - b'0' + 52,
            b'+' => 62,
            b'/' => 63,
            _ => return None,
        };
        buffer = buffer << 6 | u32::from(value);
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            output.push((buffer >> bits) as u8);
            buffer &= (1 << bits) - 1;
        }
    }
    Some(output)
}

// ---------------------------------------------------------------------------
// Character references in attribute values
// ---------------------------------------------------------------------------

/// Decode the character references in an attribute value, so the rules see
/// roughly what the browser sees.
///
/// This copies Citry's Python decoder: each reference that matches
/// `&(#[xX]hex+|#digits+|letter alnum+);?` is decoded by the rules of
/// Python's `html.unescape`, and a reference it does not know stays
/// literal. Those rules differ from the browser's in places: a legacy name
/// without `;` decodes by its longest known prefix (`&ampx` becomes `&x`),
/// only the first 32 characters of a name are looked up, `&#128;` to
/// `&#159;` map to Windows-1252, and some control and noncharacter code
/// points are removed.
pub fn decode_html_attribute(source: &str) -> Cow<'_, str> {
    let Some(first) = source.find('&') else {
        return Cow::Borrowed(source);
    };
    let bytes = source.as_bytes();
    let mut decoded = String::with_capacity(source.len());
    decoded.push_str(&source[..first]);
    let mut position = first;
    while position < bytes.len() {
        if bytes[position] != b'&' {
            let next = source[position..]
                .find('&')
                .map_or(source.len(), |offset| position + offset);
            decoded.push_str(&source[position..next]);
            position = next;
            continue;
        }
        if let Some(length) = reference_length(&bytes[position..]) {
            let raw = &source[position..position + length];
            let value = unescape_reference(raw);
            // An unknown reference such as `&bogus;` stays literal, so step
            // past only its `&` and keep reading the rest as text.
            if value != raw {
                decoded.push_str(&value);
                position += length;
                continue;
            }
        }
        decoded.push('&');
        position += 1;
    }
    Cow::Owned(decoded)
}

/// The length of the reference at the start of `input` (which starts with
/// `&`), matching `&(?:#[xX][0-9A-Fa-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);?`.
fn reference_length(input: &[u8]) -> Option<usize> {
    let run = |from: usize, accept: fn(&u8) -> bool| {
        input[from.min(input.len())..]
            .iter()
            .take_while(|byte| accept(byte))
            .count()
    };
    let body = match input.get(1) {
        Some(b'#')
            if matches!(input.get(2), Some(b'x' | b'X'))
                && input.get(3).is_some_and(u8::is_ascii_hexdigit) =>
        {
            3 + run(3, u8::is_ascii_hexdigit)
        }
        Some(b'#') if input.get(2).is_some_and(u8::is_ascii_digit) => {
            2 + run(2, u8::is_ascii_digit)
        }
        Some(byte)
            if byte.is_ascii_alphabetic()
                && input.get(2).is_some_and(u8::is_ascii_alphanumeric) =>
        {
            2 + run(2, u8::is_ascii_alphanumeric)
        }
        _ => return None,
    };
    Some(body + usize::from(input.get(body) == Some(&b';')))
}

/// Decode one reference the way Python's `html.unescape` decodes it.
fn unescape_reference(raw: &str) -> Cow<'_, str> {
    let body = &raw[1..];
    if let Some(number) = body.strip_prefix('#') {
        let number = number.strip_suffix(';').unwrap_or(number);
        let code_point = match number.strip_prefix(['x', 'X']) {
            Some(hex) => parse_code_point(hex, 16),
            None => parse_code_point(number, 10),
        };
        return Cow::Owned(numeric_reference(code_point));
    }
    // Python reads at most 32 characters of a name, and `;` belongs to the
    // reference only when it follows within them.
    const MAX_NAME: usize = 32;
    let name_length = body.strip_suffix(';').unwrap_or(body).len();
    let (looked_up, rest) = if name_length <= MAX_NAME {
        (body, "")
    } else {
        body.split_at(MAX_NAME)
    };
    let mut value = match named_reference(looked_up) {
        Some(value) => value,
        None => return Cow::Borrowed(raw),
    };
    value.push_str(rest);
    Cow::Owned(value)
}

/// The code point a run of digits names, or `0x110000` for any number past
/// U+10FFFF. Leading zeros do not change it.
fn parse_code_point(digits: &str, radix: u32) -> u32 {
    let mut value: u32 = 0;
    for digit in digits.chars() {
        value = value * radix + digit.to_digit(radix).unwrap_or(0);
        if value > 0x10FFFF {
            return 0x110000;
        }
    }
    value
}

// Python's `html._invalid_charrefs` for U+0080 to U+009F: Windows-1252,
// except five code points that keep their own value.
const C1_CODE_POINTS: [u32; 32] = [
    0x20AC, 0x81, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039,
    0x0152, 0x8D, 0x017D, 0x8F, 0x90, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014,
    0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x9D, 0x017E, 0x0178,
];

fn numeric_reference(code_point: u32) -> String {
    match code_point {
        0x00 => "\u{FFFD}".to_owned(),
        0x0D => "\r".to_owned(),
        0x80..=0x9F => char::from_u32(C1_CODE_POINTS[(code_point - 0x80) as usize])
            .map_or_else(String::new, String::from),
        0xD800..=0xDFFF | 0x110000.. => "\u{FFFD}".to_owned(),
        // Python's `html._invalid_codepoints`: these decode to nothing.
        0x01..=0x08 | 0x0B | 0x0E..=0x1F | 0x7F | 0xFDD0..=0xFDEF => String::new(),
        _ if code_point & 0xFFFE == 0xFFFE => String::new(),
        _ => char::from_u32(code_point).map_or_else(String::new, String::from),
    }
}

/// Decode a named reference (without its `&`), falling back to the longest
/// known prefix as Python does, or return `None` when nothing matches.
fn named_reference(name: &str) -> Option<String> {
    if let Some(value) = entity(name) {
        return Some(value);
    }
    // Python tries every prefix from one character shorter down to two.
    (2..name.len()).rev().find_map(|length| {
        entity(&name[..length]).map(|mut value| {
            value.push_str(&name[length..]);
            value
        })
    })
}

fn entity(name: &str) -> Option<String> {
    // The table also lists every prefix of a name with the value (0, 0),
    // which the browser's tokenizer uses while it reads; that is no entity.
    let &(first, second) = NAMED_ENTITIES.get(name)?;
    if (first, second) == (0, 0) {
        return None;
    }
    let mut value = String::new();
    value.extend(char::from_u32(first));
    if second != 0 {
        value.extend(char::from_u32(second));
    }
    Some(value)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn check(
        html: &str,
        pass: PolicyPass,
        csp: bool,
        javascript: Option<JavascriptMode>,
        marker_prefix: Option<&str>,
        trusted: &[usize],
        omit_handler_marker: Option<&str>,
    ) -> OutputPolicyReport {
        let trusted_tag_starts: HashSet<usize> = trusted.iter().copied().collect();
        check_output_html(
            html,
            &OutputPolicyOptions {
                pass,
                csp,
                javascript,
                marker_prefix,
                trusted_tag_starts: &trusted_tag_starts,
                omit_handler_marker,
            },
        )
    }

    fn finding(
        rule: Rule,
        tag: &str,
        attribute: Option<&str>,
        span: (usize, usize),
        token_start: usize,
        cids: &[&str],
    ) -> PolicyEvent {
        PolicyEvent::Finding(Finding {
            rule,
            tag: tag.to_owned(),
            attribute: attribute.map(str::to_owned),
            start: span.0,
            end: span.1,
            token_start,
            cids: cids.iter().map(|cid| (*cid).to_owned()).collect(),
        })
    }

    fn raw(
        tag: &str,
        token_start: usize,
        element_end: usize,
        trusted: bool,
        executable: bool,
        has_manager_attribute: bool,
    ) -> PolicyEvent {
        PolicyEvent::RawElement(RawElement {
            tag: tag.to_owned(),
            token_start,
            name_start: token_start + 1,
            name_end: token_start + 1 + tag.len(),
            element_end,
            trusted,
            executable,
            has_manager_attribute,
            cids: Vec::new(),
        })
    }

    // The expected values below are what Citry's Python decoder returned
    // for the same inputs (`_decode_html_attribute` before the rules moved).
    #[test]
    fn attribute_values_decode_like_python_html_unescape() {
        let cases = [
            ("plain", "plain"),
            ("&amp;", "&"),
            ("&amp", "&"),
            ("&ampx;", "&x;"),
            ("&AMP;x", "&x"),
            ("&notit;", "\u{ac}it;"),
            ("&notin;", "\u{2209}"),
            ("&bogus;", "&bogus;"),
            ("&#128;", "\u{20ac}"),
            ("&#129;", "\u{81}"),
            ("&#xD800;", "\u{fffd}"),
            ("&#1;", ""),
            ("&#0;", "\u{fffd}"),
            ("&#13;", "\u{d}"),
            ("&#x110000;", "\u{fffd}"),
            ("&#xFFFE;", ""),
            ("&#x1FFFF;", ""),
            ("&#;", "&#;"),
            ("&#x;", "&#x;"),
            ("&#xg", "&#xg"),
            ("&#12a", "\u{c}a"),
            ("&Tab;", "\u{9}"),
            ("&NotEqualTilde;", "\u{2242}\u{338}"),
            (
                "&bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb;",
                "&bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb;",
            ),
            (
                "&ampxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;",
                "&xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;",
            ),
            ("&#00000000000000000000106;", "j"),
            ("&#x0000006A;", "j"),
            ("a&&amp;b", "a&&b"),
            ("&#106avascript", "javascript"),
            ("&CounterClockwiseContourIntegral;", "\u{2233}"),
            ("\u{17f}&#115;", "\u{17f}s"),
        ];
        for (source, expected) in cases {
            assert_eq!(decode_html_attribute(source), expected, "{source}");
        }
    }

    #[test]
    fn decimal_references_of_any_length_name_their_code_point() {
        let zeros = "0".repeat(5000);
        assert_eq!(decode_html_attribute(&format!("&#{zeros}106;")), "j");
        assert_eq!(
            decode_html_attribute(&format!("&#{};", "9".repeat(5000))),
            "\u{fffd}"
        );
        assert_eq!(decode_html_attribute(&format!("&#x{zeros}6a")), "j");
    }

    #[test]
    fn javascript_urls_match_python_case_insensitive_letters() {
        let cases = [
            ("javascript:x", true),
            (" \u{0}JaVaScRiPt:x", true),
            ("java\u{9}script:x", true),
            ("java\u{17f}cript:x", true),
            ("javascr\u{131}pt:x", true),
            ("javascr\u{130}pt:x", true),
            ("javascript\u{9}:x", true),
            ("\u{a0}javascript:x", false),
            ("javascript", false),
            ("java script:x", false),
            ("\u{b}javascript:x", true),
            // U+212A KELVIN SIGN matches `k`, which `javascript` lacks.
            ("javascript\u{212a}:x", false),
        ];
        for (value, expected) in cases {
            assert_eq!(is_javascript_url(value), expected, "{value:?}");
        }
    }

    #[test]
    fn script_types_follow_the_mime_essence() {
        let cases = [
            ("", true),
            ("module", true),
            (" Module ", true),
            ("module;x", false),
            ("importmap", true),
            ("speculationrules;a", false),
            ("text/javascript", true),
            ("TEXT/JAVASCRIPT ; charset=utf-8", true),
            ("application/json", false),
            ("text/plain", false),
            ("\u{9}text/x-javascript\u{a}", true),
            ("javascript", false),
        ];
        for (value, expected) in cases {
            assert_eq!(script_type_is_executable(value), expected, "{value:?}");
        }
    }

    #[test]
    fn settled_rules_report_attributes_in_source_order_with_utf8_offsets() {
        let html = "<p title='žluť' onclick=go() data-cid-q><a href=\"java&#x73;cript:x\" HREF=javascript:y>x</a>";
        let report = check(
            html,
            PolicyPass::Settled,
            true,
            Some(JavascriptMode::Warn),
            None,
            &[],
            None,
        );
        assert_eq!(
            report.events,
            [
                finding(
                    Rule::CspNativeEvent,
                    "p",
                    Some("onclick"),
                    (18, 25),
                    0,
                    &["q"]
                ),
                finding(
                    Rule::JsNativeHandler,
                    "p",
                    Some("onclick"),
                    (18, 25),
                    0,
                    &["q"]
                ),
                finding(Rule::CspJavascriptUrl, "a", Some("href"), (51, 68), 42, &[]),
                finding(Rule::JsJavascriptUrl, "a", Some("href"), (51, 68), 42, &[]),
                finding(Rule::CspJavascriptUrl, "a", Some("href"), (75, 87), 42, &[]),
                finding(Rule::JsJavascriptUrl, "a", Some("href"), (75, 87), 42, &[]),
            ]
        );
        assert_eq!(&html.as_bytes()[18..25], b"onclick");
        assert_eq!(report.cleaned_html, None);
    }

    #[test]
    fn trust_comes_from_a_marker_prefix_or_a_listed_start() {
        // An empty prefix trusts every tag that has an attribute.
        let html = "<style media=print>a{}</style><style>b{}</style><script data-x>1</script>";
        let report = check(html, PolicyPass::Settled, true, None, Some(""), &[], None);
        assert_eq!(
            report.events,
            [
                raw("style", 0, 30, true, false, false),
                raw("style", 30, 48, false, false, false),
                raw("script", 48, 73, true, true, false),
            ]
        );
        // No prefix trusts no tag by its attributes.
        let report = check(html, PolicyPass::Settled, true, None, None, &[30], None);
        let trusted = report
            .events
            .iter()
            .map(|event| matches!(event, PolicyEvent::RawElement(element) if element.trusted))
            .collect::<Vec<_>>();
        assert_eq!(trusted, [false, true, false]);
    }

    #[test]
    fn the_javascript_policy_looks_at_scripts_only() {
        let html = "<style media=print>a{}</style><script data-m-1 src=x></script><script type=application/json data-citry>{}</script>";
        let report = check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Forbid),
            Some("data-m"),
            &[],
            None,
        );
        assert_eq!(
            report.events,
            [
                raw("script", 30, 62, true, true, false),
                raw("script", 62, 114, false, false, true)
            ]
        );
    }

    #[test]
    fn raw_elements_end_where_the_scanner_closes_them() {
        // A self-closed SVG script stays open to the scanner, so the next
        // end tag closes the newer script and the SVG one runs to the end.
        let html = "<svg><script/></svg><script>x</script><script>open";
        let report = check(html, PolicyPass::PreExtension, false, None, None, &[], None);
        assert_eq!(
            report.events,
            [
                raw("script", 5, 50, false, true, false),
                raw("script", 20, 38, false, true, false),
                raw("script", 38, 50, false, true, false),
            ]
        );
    }

    #[test]
    fn omit_markers_are_removed_and_mark_handler_only_controls() {
        let html = concat!(
            "<button data-citry-omit-handler-ab @click=x>a</button>",
            "<a DATA-CITRY-OMIT-HANDLER-AB=\"1\"x=y>b</a>",
            "<div\tdata-citry-omit-handler-ab='v' :hidden=h hidden>c</div>",
            "<input data-citry-omit-handler-ab type=submit form=f>",
        );
        let report = check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Omit),
            Some("p"),
            &[],
            Some("data-citry-omit-handler-AB"),
        );
        assert_eq!(
            report.events,
            [
                finding(Rule::JsHandlerOnlyControl, "button", None, (1, 7), 0, &[]),
                finding(Rule::JsHandlerOnlyControl, "a", None, (55, 56), 54, &[]),
                finding(
                    Rule::JsStaticFallback,
                    "div",
                    Some(":hidden"),
                    (132, 139),
                    96,
                    &[]
                ),
                finding(Rule::JsHandlerOnlyControl, "div", None, (97, 100), 96, &[]),
            ]
        );
        // The marker that touches its neighbor keeps the space before it.
        assert_eq!(
            report.cleaned_html.as_deref(),
            Some("<button @click=x>a</button><a x=y>b</a><div :hidden=h hidden>c</div><input type=submit form=f>")
        );
    }

    #[test]
    fn omit_mode_reports_fallbacks_that_need_javascript() {
        let html = "<a @click=go v-if=x :href=u href=''>a</a><button @click.prevent=x type=BUTTON>b</button><span v-on=h :title=t>c</span>";
        let report = check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Omit),
            None,
            &[],
            None,
        );
        assert_eq!(
            report.events,
            [
                finding(Rule::JsStaticFallback, "a", Some("v-if"), (13, 17), 0, &[]),
                finding(Rule::JsStaticFallback, "a", Some(":href"), (20, 25), 0, &[]),
                finding(Rule::JsHandlerOnlyControl, "a", None, (1, 2), 0, &[]),
                finding(
                    Rule::JsHandlerOnlyControl,
                    "button",
                    None,
                    (42, 48),
                    41,
                    &[]
                ),
                finding(Rule::JsHandlerOnlyControl, "span", None, (89, 93), 88, &[]),
            ]
        );
    }

    #[test]
    fn embedded_documents_are_read_like_the_browser_would_load_them() {
        let html = concat!(
            // An inert nested document.
            "<iframe srcdoc=\"&lt;iframe srcdoc=&quot;&amp;lt;b&amp;gt;&quot;&gt;\"></iframe>",
            // Padding after a complete group is not valid base64.
            "<iframe src=\"data:text/html;base64,PHA+aGk8L3A+=\"></iframe>",
            // A byte that is not UTF-8 becomes U+FFFD, so this is no <script>.
            "<object data='data:text/html,%3Cscr%ffipt%3Ex()%3C/script%3E'></object>",
            "<embed src=' DATA:Text/HTML;charset=x,%3Cb onclick=1%3E'>",
        );
        let report = check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Warn),
            None,
            &[],
            None,
        );
        assert_eq!(
            report.events,
            [
                finding(
                    Rule::JsEmbeddedDocument,
                    "iframe",
                    Some("src"),
                    (91, 126),
                    78,
                    &[]
                ),
                finding(
                    Rule::JsEmbeddedDocument,
                    "embed",
                    Some("src"),
                    (220, 263),
                    208,
                    &[]
                ),
            ]
        );
    }

    #[test]
    fn documents_nested_more_than_four_deep_count_as_running_code() {
        // `depth` counts the iframes around the inert paragraph; the check
        // reads the outermost one's srcdoc, which nests one fewer.
        let mut document = String::from("<p>inert</p>");
        for depth in 1..=6 {
            document = format!(
                "<iframe srcdoc=\"{}\"></iframe>",
                document
                    .replace('&', "&amp;")
                    .replace('"', "&quot;")
                    .replace('<', "&lt;")
            );
            let requires = embedded_document_requires_javascript(
                "iframe",
                "srcdoc",
                &decode_html_attribute(&document[16..document.len() - 11]),
            );
            assert_eq!(requires, depth >= 5, "depth {depth}");
        }
    }

    #[test]
    fn strict_base64_accepts_only_canonical_padding() {
        assert_eq!(decode_strict_base64(b"").as_deref(), Some(&b""[..]));
        assert_eq!(decode_strict_base64(b"QUJD").as_deref(), Some(&b"ABC"[..]));
        assert_eq!(decode_strict_base64(b"QUI=").as_deref(), Some(&b"AB"[..]));
        assert_eq!(decode_strict_base64(b"QQ==").as_deref(), Some(&b"A"[..]));
        // Leftover bits in the last character are ignored, as Python does.
        assert_eq!(decode_strict_base64(b"QR==").as_deref(), Some(&b"A"[..]));
        for invalid in [
            &b"QUJD="[..],
            b"QQ",
            b"QQ=",
            b"Q===",
            b"=",
            b"==",
            b"QU!D",
            b"QQ==QQ==",
            b"Q=Q=",
        ] {
            assert_eq!(decode_strict_base64(invalid), None, "{invalid:?}");
        }
    }

    #[test]
    fn percent_escapes_need_two_hex_digits() {
        assert_eq!(percent_decode(b"%41%4%zz%%41%"), b"A%4%zz%A%");
    }

    #[test]
    fn malformed_input_is_read_without_failing() {
        for html in [
            "<a href='x",
            "<!-- open",
            "<script>open",
            "<a\0b c=d>",
            "</p></div>",
            "<<<>>>",
        ] {
            check(
                html,
                PolicyPass::Settled,
                true,
                Some(JavascriptMode::Omit),
                Some(""),
                &[0],
                Some("m"),
            );
        }
    }
}
