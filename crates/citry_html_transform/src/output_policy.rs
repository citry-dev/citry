//! Find what Citry's strict-CSP and JavaScript-policy checks report in
//! finished HTML.
//!
//! `citry.serialize()` checks the page it is about to return when
//! `security_csp` or `security_javascript` is set. This module runs the
//! rules of those checks over the page and returns only what they found:
//! the attributes and elements a rule reports, and the `script` and
//! `style` elements the selected rules look at (only scripts when only the
//! JavaScript policy runs), because Python remembers some of those between
//! two checks of one page. Python keeps the wording of each message, the
//! bookkeeping that drops repeated findings, and the decision to warn or
//! raise, so an ordinary tag never becomes a Python object.
//!
//! The rules copy the Python checks they replace exactly, including how
//! they decode character references in attribute values (the browser's
//! attribute-value rule) and how
//! they compare letters in `javascript:` (Python's case-insensitive
//! regular expression). `packages/py/citry/tests/_output_policy_reference.py`
//! keeps the Python version, and a test compares the two on generated pages.

use std::borrow::Cow;
use std::cell::{Cell, RefCell};
use std::collections::HashMap;
use std::collections::HashSet;
use std::rc::Rc;

use html5ever::data::NAMED_ENTITIES;

use crate::html_limits::{HtmlLimits, HtmlTooLarge};
use crate::output_scanner::{
    browser_rules_for, scan_output_html_under, scan_output_html_with, BrowserRules, EndTagRule,
    Mode, OutputAttribute, OutputTag, Placement, ScanResult, TagContext,
};

/// Which of the two checks of one page runs.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PolicyPass {
    /// The page before the `on_serialize` extension hooks run. Only its
    /// `script` and `style` elements matter: warn mode reports and
    /// remembers them here, so the later check does not report the same
    /// element again.
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
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum Rule {
    CspNativeEvent,
    CspJavascriptUrl,
    JsBrowserAttribute,
    JsStaticFallback,
    JsNativeHandler,
    JsJavascriptUrl,
    JsEmbeddedDocument,
    JsHandlerOnlyControl,
    JsPageEncoding,
    JsParserDifference,
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
            Rule::JsPageEncoding => "js-page-encoding",
            Rule::JsParserDifference => "js-parser-difference",
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
    /// Byte offset just past the element: past its end tag, or the end of
    /// the input when no end tag closes it.
    pub element_end: usize,
    /// Citry wrote this tag (see [`OutputPolicyOptions::marker_prefix`]).
    pub trusted: bool,
    /// The element is a `script` the browser would run.
    pub executable: bool,
    /// An attribute name starts with `data-citry`, which marks one of
    /// Citry's browser manifests (the data its browser manager reads).
    pub has_manager_attribute: bool,
    /// The suffixes of the raw element's own `data-cid-*` attributes, in
    /// attribute order, then those of the elements that contain it in the
    /// browser's tree, nearest first. Python names the first one it knows as the
    /// component, so a finding inside a component's outer tag names it.
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
    /// For `Rule::JsParserDifference`, a code naming which difference was
    /// found, such as `reopened-formatting` (see `DifferenceKind::code`),
    /// so Python can say what to change. `None` for every other rule.
    pub case: Option<&'static str>,
}

/// One entry of a report, in the order the start tags appear. The check
/// reads some pages more than once (see `for_each_reading`). Entries that
/// only a later reading found come after the earlier readings' entries.
/// Within each reading, the tags where browsers may build a different tree
/// from the check's (`Rule::JsParserDifference`) come after that reading's
/// other entries.
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
/// `<title>` or a comment is not read as tags. Malformed HTML is read the
/// way a browser recovers from it. The only page it refuses is one over a
/// limit in `html_limits` (too many attributes on one tag, too many `html`,
/// `head` or `body` start tags, elements nested too deep, too many
/// formatting elements reopened, or more work across all its readings than
/// `MAX_CHECK_WORK_PER_BYTE` allows): it returns [`HtmlTooLarge`] and
/// reports nothing, so the caller treats the page as one it could not
/// check.
pub fn check_output_html(
    html: &str,
    options: &OutputPolicyOptions<'_>,
) -> Result<OutputPolicyReport, HtmlTooLarge> {
    let marker = options.omit_handler_marker.map(str::to_lowercase);
    // Every reading of the page, and of the documents inside it, spends
    // from one budget, so the number of readings cannot multiply the cost
    // without bound.
    let work_left = HtmlLimits::check_work_for(html.len());
    // Every reading meets the same embedded documents, so each one's answer
    // is worked out once for the whole check.
    let documents = EmbeddedDocuments {
        work_left: Some(work_left.clone()),
        ..EmbeddedDocuments::default()
    };
    // Browsers differ on some tree-building rules, the check cannot know
    // the visitor's browser, and the page may be put into another page, so
    // it reports what any reading finds.
    let mut first_reading = None;
    let mut marker_spans = Vec::new();
    for_each_reading(html, PageKind::Page, |rules| {
        let report = run_rules(
            html,
            options,
            marker.as_deref(),
            rules,
            &documents,
            &work_left,
        )?;
        match &mut first_reading {
            Some(events) => add_new_events(events, report.events),
            None => first_reading = Some(report.events),
        }
        marker_spans.extend(report.marker_spans);
        Ok(report.needs)
    })?;
    let mut events = first_reading.unwrap_or_default();
    // This reads the page's bytes, not its tags, so the result does not
    // depend on the encoding the page declares or the response names. Only
    // the JavaScript policy runs it: a strict Content Security Policy makes
    // the browser block an inline script or handler this could hide.
    if options.pass == PolicyPass::Settled && options.javascript.is_some() {
        if let Some((start, end)) = encoding_dependent_span(html) {
            events.push(PolicyEvent::Finding(Finding {
                rule: Rule::JsPageEncoding,
                tag: String::new(),
                attribute: None,
                start,
                end,
                token_start: start,
                cids: Vec::new(),
                case: None,
            }));
        }
    }
    let cleaned_html = remove_spans(html, marker_spans);
    Ok(OutputPolicyReport {
        events,
        cleaned_html,
    })
}

/// What the browser does with a page the check reads, which decides the
/// readings it needs.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum PageKind {
    /// The HTML `serialize()` returns. A browser may load it as a document,
    /// Vue may build it inside a `<template>`, and an app may put it into
    /// the body of its own page.
    Page,
    /// The document of an `<iframe srcdoc>`. Chromium 156 picks its mode
    /// from its doctype as for a page it loads, so a document without a
    /// doctype is in quirks mode, and Firefox 157 always reads it in
    /// standards mode.
    Srcdoc,
    /// A document a `data:` URL opens, which takes its mode from its
    /// doctype like a page the browser loads.
    DataUrl,
}

/// What a reading found that can call for more readings.
#[derive(Clone, Copy, Debug, Default)]
struct ReadingNeeds {
    /// See [`ScanResult::end_tag_rule_matters`].
    end_tag_rule_matters: bool,
    /// See [`ScanResult::mode_matters`].
    mode_matters: bool,
    /// See [`ScanResult::quirks`].
    quirks: bool,
    /// See [`ScanResult::template_matters`].
    template_matters: bool,
}

impl ReadingNeeds {
    fn of(scan: &ScanResult) -> Self {
        Self {
            end_tag_rule_matters: scan.end_tag_rule_matters,
            mode_matters: scan.mode_matters,
            quirks: scan.quirks,
            template_matters: scan.template_matters,
        }
    }
}

/// Call `read` once for each reading of `html`: one scan of the page under
/// one set of [`BrowserRules`]. A reading follows the parsing rules of one
/// kind of browser, in one mode, with the markup in one place (see
/// [`Placement`]).
///
/// The first reading follows the standard's end-tag rules and html5ever's
/// `<select>` rule (see [`BrowserRules::keep_select_tags`]). It reads a page
/// or a `data:` document the way html5ever reads a page the browser loads,
/// and a `srcdoc` document in standards mode. More readings are added when
/// something in the page makes them differ:
///
/// - the text `<select` anywhere adds the same reading with the standard's
///   newer `<select>` rules;
/// - for a page, the text `<frameset` anywhere adds a reading of the markup
///   in the body of a page in standards mode. A whole document and the body
///   of another page build the same tree, apart from a `<frameset>` and the
///   mode;
/// - for a page, a `<noscript>` that may hold a tag adds a reading of the
///   markup inside a `<template>` with `<noscript>` contents read as
///   markup, as Chromium builds an opaque HTML block for Vue (see
///   [`BrowserRules::noscript_as_markup`] and [`noscript_may_hold_markup`]);
/// - after a reading, `read` says what it met. An end tag that
///   [`EndTagRule`] changes adds the readings of the two browsers that
///   differ from the standard. A `<table>` start tag inside an open `<p>`
///   adds the reading in the other mode: for a page, its markup in the body
///   of a page in that mode, and for a `srcdoc` document, the document in
///   the mode its doctype picks as Chromium reads it. A table part such as
///   `<tr>` that html5ever ignored adds, for a page, the reading of its
///   markup inside a `<template>`.
///
/// A page that holds none of these gets one reading.
fn for_each_reading<E>(
    html: &str,
    kind: PageKind,
    mut read: impl FnMut(BrowserRules) -> Result<ReadingNeeds, E>,
) -> Result<(), E> {
    let base = match kind {
        PageKind::Page | PageKind::DataUrl => BrowserRules::default(),
        PageKind::Srcdoc => BrowserRules {
            mode: Mode::Standards,
            ..BrowserRules::default()
        },
    };
    let mut readings = browser_rules_for(html, base);
    if kind == PageKind::Page && holds_text_ignoring_case(html, b"<frameset") {
        readings.extend(browser_rules_for(
            html,
            BrowserRules {
                placement: Placement::Body,
                mode: Mode::Standards,
                ..base
            },
        ));
    }
    if kind == PageKind::Page && noscript_may_hold_markup(html) {
        readings.extend(browser_rules_for(
            html,
            BrowserRules {
                placement: Placement::Template,
                mode: Mode::Standards,
                noscript_as_markup: true,
                ..base
            },
        ));
    }
    let mut index = 0;
    while let Some(&rules) = readings.get(index) {
        index += 1;
        let needs = read(rules)?;
        let mut more = Vec::new();
        if needs.end_tag_rule_matters && rules.end_tags == EndTagRule::Standard {
            for end_tags in [EndTagRule::Firefox, EndTagRule::Chromium] {
                more.push(BrowserRules { end_tags, ..rules });
            }
        }
        if needs.mode_matters {
            match kind {
                // A `data:` document takes its mode from its doctype as
                // html5ever does, apart from the doctypes the scan refuses a
                // `<table>` under, so the other mode adds nothing.
                PageKind::DataUrl => {}
                // Firefox reads a `srcdoc` document in standards mode, and
                // Chromium picks the mode from its doctype as for a page it
                // loads, so no doctype means quirks mode, as it does for
                // html5ever without `iframe_srcdoc`.
                PageKind::Srcdoc => more.push(BrowserRules {
                    mode: match rules.mode {
                        Mode::Standards => Mode::FromDoctype,
                        _ => Mode::Standards,
                    },
                    ..rules
                }),
                PageKind::Page => more.extend(rules.other_mode(needs.quirks)),
            }
        }
        if needs.template_matters
            && kind == PageKind::Page
            && rules.placement != Placement::Template
        {
            let mode = match rules.mode {
                Mode::FromDoctype if needs.quirks => Mode::Quirks,
                Mode::FromDoctype => Mode::Standards,
                mode => mode,
            };
            more.push(BrowserRules {
                placement: Placement::Template,
                mode,
                ..rules
            });
        }
        for rules in more {
            if !readings.contains(&rules) {
                readings.push(rules);
            }
        }
    }
    Ok(())
}

/// Whether a `<noscript>` in `html` may hold a tag, which only a reading
/// with `<noscript>` contents read as markup can find. A page reads
/// `<noscript>` contents as text up to the first `</noscript` that a space,
/// `/` or `>` follows, or to its end, so a `<` there may start a tag when the
/// contents are read as markup. Text without a `<` builds the same tree
/// either way. This reads the bytes, not the tags, so a `<noscript` that is
/// not a tag at all only adds a reading.
fn noscript_may_hold_markup(html: &str) -> bool {
    const START: &[u8] = b"<noscript";
    const END: &[u8] = b"</noscript";
    let bytes = html.as_bytes();
    let at = |index: usize, needle: &[u8]| {
        bytes
            .get(index..index + needle.len())
            .is_some_and(|window| window.eq_ignore_ascii_case(needle))
    };
    let mut index = 0;
    while index < bytes.len() {
        if !at(index, START) {
            index += 1;
            continue;
        }
        // The text after `<noscript`, start tag included, up to where the
        // contents end.
        let from = index + START.len();
        let mut end = from;
        while end < bytes.len()
            && !(at(end, END)
                && matches!(
                    bytes.get(end + END.len()),
                    Some(b' ' | b'\t' | b'\n' | b'\r' | b'\x0c' | b'/' | b'>')
                ))
        {
            end += 1;
        }
        if bytes[from..end].contains(&b'<') {
            return true;
        }
        index = end.max(from);
    }
    false
}

/// Whether `html` holds `needle`, which is lowercase, in any ASCII case.
fn holds_text_ignoring_case(html: &str, needle: &[u8]) -> bool {
    html.as_bytes()
        .windows(needle.len())
        .any(|window| window.eq_ignore_ascii_case(needle))
}

/// What the selected rules found in one reading of a page.
struct ReadingReport {
    events: Vec<PolicyEvent>,
    /// The spans of the omit markers.
    marker_spans: Vec<(usize, usize)>,
    /// What calls for more readings (see [`for_each_reading`]).
    needs: ReadingNeeds,
}

/// The answers [`html_document_requires_javascript`] has worked out during
/// one check, by document, depth and kind. Each reading of the outer page
/// meets the same `srcdoc` and `data:` documents, so without this a
/// document nested a few levels deep would be read once for every
/// combination of the readings around it.
#[derive(Default)]
struct EmbeddedDocuments {
    answers: RefCell<HashMap<(String, usize, bool), bool>>,
    /// The budget the outer page's readings spend from, which these
    /// readings share. `None` in tests that read a document alone.
    work_left: Option<Rc<Cell<usize>>>,
}

/// Run the selected rules over one reading of `html`.
fn run_rules(
    html: &str,
    options: &OutputPolicyOptions<'_>,
    marker: Option<&str>,
    rules: BrowserRules,
    documents: &EmbeddedDocuments,
    work_left: &Rc<Cell<usize>>,
) -> Result<ReadingReport, HtmlTooLarge> {
    let mut state = CheckState {
        options,
        documents,
        source: html.as_bytes(),
        marker,
        events: Vec::new(),
        pending_raw: Vec::new(),
        marker_spans: Vec::new(),
        tag_cids: None,
    };
    let scan = scan_output_html_with(
        html,
        rules,
        &mut |tag, raw_index, context| state.visit(tag, raw_index, context),
        Some(work_left.clone()),
    )?;
    // A raw element's end tag arrives after its start tag was reported, so
    // the element's end is filled in once the whole page has been read.
    for (event_index, fact_index) in std::mem::take(&mut state.pending_raw) {
        let fact = &scan.tags[fact_index];
        if let PolicyEvent::RawElement(element) = &mut state.events[event_index] {
            element.element_end = fact.end.max(fact.element_end);
        }
    }
    // Where browsers may build a different tree from the scan's, the check
    // cannot tell what the page runs, so only the JavaScript policy reports
    // it, as it reports text whose tags depend on the encoding.
    if options.pass == PolicyPass::Settled && options.javascript.is_some() {
        for difference in &scan.differences {
            state.events.push(PolicyEvent::Finding(Finding {
                rule: Rule::JsParserDifference,
                tag: difference.tag.clone(),
                // This rule reports a tag, not an attribute.
                attribute: None,
                start: difference.start,
                end: difference.end,
                token_start: difference.start,
                cids: Vec::new(),
                case: Some(difference.kind.code()),
            }));
        }
    }
    Ok(ReadingReport {
        events: state.events,
        marker_spans: state.marker_spans,
        needs: ReadingNeeds::of(&scan),
    })
}

/// Add what a later reading found and the earlier ones did not, so an entry
/// that more than one reading found is reported once.
fn add_new_events(events: &mut Vec<PolicyEvent>, later: Vec<PolicyEvent>) {
    type Key<'e> = (usize, &'e str, Option<Rule>, Option<&'e str>, usize);
    fn key(event: &PolicyEvent) -> Key<'_> {
        match event {
            PolicyEvent::RawElement(element) => (element.token_start, &element.tag, None, None, 0),
            // The key leaves out `case`: two readings can find one tag where
            // browsers differ under two cases, and the tag is still one place
            // for the page author to fix, so the first reading's case is kept.
            PolicyEvent::Finding(finding) => (
                finding.token_start,
                &finding.tag,
                Some(finding.rule),
                finding.attribute.as_deref(),
                finding.start,
            ),
        }
    }
    let new: Vec<PolicyEvent> = {
        let seen: HashSet<Key<'_>> = events.iter().map(key).collect();
        later
            .into_iter()
            .filter(|event| {
                // Only the first reading reports a control without a
                // fallback. That rule is about a missing fallback, not about
                // code that runs, and a later reading can tie a control to a
                // form differently: it hands html5ever a `select` tag under
                // another name, which html5ever does not tie to a form.
                let about_fallback = matches!(
                    event,
                    PolicyEvent::Finding(finding) if finding.rule == Rule::JsHandlerOnlyControl
                );
                !about_fallback && !seen.contains(&key(event))
            })
            .collect()
    };
    events.extend(new);
}

struct CheckState<'a, 'o> {
    options: &'o OutputPolicyOptions<'a>,
    documents: &'o EmbeddedDocuments,
    source: &'o [u8],
    marker: Option<&'o str>,
    events: Vec<PolicyEvent>,
    // (index in `events`, index in the scanner's raw facts)
    pending_raw: Vec<(usize, usize)>,
    marker_spans: Vec<(usize, usize)>,
    // The current tag's own `data-cid-*` suffixes followed by those of the
    // elements around it, worked out the first time an event needs them.
    tag_cids: Option<Vec<String>>,
}

impl CheckState<'_, '_> {
    fn visit(&mut self, tag: &OutputTag, raw_index: Option<usize>, context: &TagContext) {
        let name = ascii_lower(&tag.name);
        let is_script = name == "script";
        let is_raw = is_script || name == "style";
        self.tag_cids = None;
        match self.options.pass {
            PolicyPass::PreExtension => {
                if let (true, Some(raw_index)) = (is_raw, raw_index) {
                    self.push_raw(tag, context, &name, raw_index, false, false);
                }
            }
            PolicyPass::Settled => {
                self.visit_settled(tag, context, &name, is_script, is_raw, raw_index);
            }
        }
    }

    /// The `cids` an event on this tag carries: its own `data-cid-*`
    /// suffixes, then those of the elements the browser put around it,
    /// nearest first, so Python names the innermost known component.
    fn cids(&mut self, tag: &OutputTag, context: &TagContext) -> Vec<String> {
        self.tag_cids
            .get_or_insert_with(|| {
                let mut cids = component_ids(tag);
                cids.extend(context.ancestor_cids());
                cids
            })
            .clone()
    }

    fn visit_settled(
        &mut self,
        tag: &OutputTag,
        context: &TagContext,
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
            self.push_raw(
                tag,
                context,
                name,
                raw_index,
                trusted,
                has_manager_attribute,
            );
        }

        // The decoded value of each attribute's first occurrence, which the
        // omit-mode rules read. It is built only when one of them runs.
        let mut first_values: Option<HashMap<Cow<'_, str>, Cow<'_, str>>> = None;
        let mut activation_attrs: Vec<Cow<'_, str>> = Vec::new();
        // Whether this tag is an SVG animation that writes a link's `href`,
        // which makes its `to`, `from`, `by` and `values` URL attributes.
        // It is worked out once per tag, so a tag with many attributes is
        // not scanned again for each one.
        let animates_href = (self.options.csp || javascript.is_some())
            && animation_sets_href(name, &tag.attributes);
        // Whether this tag is a `<meta http-equiv="refresh">`, which opens
        // the URL in its `content`; only the JavaScript policy reads it.
        let facts = DocumentFacts {
            animates_href,
            refreshes: javascript.is_some() && meta_refreshes(name, &tag.attributes),
        };
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
            let url_attribute = is_url_value(name, &attr_name, animates_href);
            if self.options.csp {
                if is_native_event_attribute(&attr_name) {
                    self.push_finding_in(
                        context,
                        Rule::CspNativeEvent,
                        tag,
                        name,
                        Some(&attr.name),
                        attr.name_start,
                        attr.name_end,
                    );
                }
                if url_attribute
                    && is_javascript_url_value(
                        &attr_name,
                        decoded.get_or_insert_with(|| decode_html_attribute(raw_value)),
                    )
                {
                    self.push_finding_in(
                        context,
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
                        self.push_finding_in(
                            context,
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
                            self.push_finding_in(
                                context,
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
                self.push_finding_in(
                    context,
                    Rule::JsNativeHandler,
                    tag,
                    name,
                    Some(&attr.name),
                    attr.name_start,
                    attr.name_end,
                );
            }
            if url_attribute
                && is_javascript_url_value(
                    &attr_name,
                    decoded.get_or_insert_with(|| decode_html_attribute(raw_value)),
                )
            {
                self.push_finding_in(
                    context,
                    Rule::JsJavascriptUrl,
                    tag,
                    name,
                    Some(&attr.name),
                    value_start,
                    value_end,
                );
            }
            if may_hold_document(name, &attr_name, facts)
                && attribute_document_requires_javascript(
                    name,
                    &attr_name,
                    decoded.get_or_insert_with(|| decode_html_attribute(raw_value)),
                    facts,
                    0,
                    self.documents,
                )
            {
                self.push_finding_in(
                    context,
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
            if is_handler_only_control(
                name,
                values,
                &activation_attrs,
                has_managed_handler,
                context.has_form_owner(),
            ) {
                self.push_finding_in(
                    context,
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
        context: &TagContext,
        name: &str,
        raw_index: usize,
        trusted: bool,
        has_manager_attribute: bool,
    ) {
        let executable = name == "script" && raw_script_is_executable(tag);
        let cids = self.cids(tag, context);
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
            cids,
        }));
    }

    fn push_finding_in(
        &mut self,
        context: &TagContext,
        rule: Rule,
        tag: &OutputTag,
        name: &str,
        attribute: Option<&str>,
        start: usize,
        end: usize,
    ) {
        let cids = self.cids(tag, context);
        self.events.push(PolicyEvent::Finding(Finding {
            rule,
            tag: name.to_owned(),
            attribute: attribute.map(str::to_owned),
            start,
            end,
            token_start: tag.start,
            cids,
            case: None,
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

/// Whether a browser might skip `value` where it reads a `<script type>`
/// or a `<meta http-equiv="refresh">` value: any character other than a
/// printable ASCII character (U+0021 to U+007E).
///
/// Browsers do not agree here. In a type and around a refresh delay,
/// Firefox 157 skipped only ASCII whitespace when this was written, while
/// Chromium 156 also skipped U+000B and the Unicode spaces U+1680, U+2000
/// to U+200A, U+2028, U+205F, and U+3000.
/// The names the check compares against are all printable ASCII, so
/// counting every other character as one a browser may skip can only make
/// the check report more, never less. A `data:` document can spell these
/// characters in another encoding, so [`payload_may_hide_markup`] counts
/// any document that is not plain ASCII.
fn may_be_skipped_by_browser(value: char) -> bool {
    !value.is_ascii_graphic()
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

/// Whether an SVG `<animate>` or `<set>` writes the `href` (or
/// `xlink:href`) of the element it animates.
///
/// Such an element carries the new link in its `to`, `from`, `by` or
/// `values` attribute, so those attributes are URLs, as `href` is. The
/// browser reads the first `attributeName` when there are two and compares
/// it exactly. When this was written, Chromium 156 and Firefox 157 ran an
/// animation named `href`. They did not run `xlink:href`, `HREF`, or a name
/// with spaces around it, but this check reports those too, in case another
/// browser reads the name more loosely. The same two browsers did not run
/// `attributeName=href` on `<animateTransform>` or `<animateMotion>`, and
/// this check leaves those alone. It reads the tag by name, so an
/// `<animate>` outside `<svg>`, which the browser ignores, counts as well.
/// `tag` is the tag name in lowercase.
pub fn animation_sets_href(tag: &str, attributes: &[OutputAttribute]) -> bool {
    if !matches!(tag, "animate" | "set") {
        return false;
    }
    let Some(attribute_name) = attributes
        .iter()
        .find(|attr| attr.name.eq_ignore_ascii_case("attributeName"))
    else {
        return false;
    };
    let value = decode_html_attribute(if attribute_name.has_value {
        &attribute_name.value
    } else {
        ""
    });
    let value = value.trim_matches(is_html_space);
    value.eq_ignore_ascii_case("href") || value.eq_ignore_ascii_case("xlink:href")
}

/// The attributes of an animation that hold the value it sets.
fn is_animation_value_attribute(name: &str) -> bool {
    matches!(name, "to" | "from" | "by" | "values")
}

/// Whether the browser may use an attribute's value as a URL: a URL
/// attribute, or the value of an animation that sets `href`
/// (`animates_href` comes from [`animation_sets_href`]).
pub fn is_url_value(tag: &str, name: &str, animates_href: bool) -> bool {
    is_url_attribute(tag, name) || (animates_href && is_animation_value_attribute(name))
}

/// Whether a URL attribute's value, with its character references already
/// decoded, starts with `javascript:`, or for `values`, whether any
/// `;`-separated item does. The page check and the
/// embedded-document check both call this, so they cannot disagree.
///
/// `values` is a list that the browser's SVG animation code (SMIL) splits on
/// `;`, and an item can be any of the values the animation passes through,
/// so any item counts. Any other attribute is one URL.
pub fn is_javascript_url_value(name: &str, value: &str) -> bool {
    if name == "values" {
        value.split(';').any(is_javascript_url)
    } else {
        is_javascript_url(value)
    }
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

/// What a strict Content Security Policy would block in one attribute.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CspAttributeProblem {
    /// A native inline event handler such as `onclick="..."`.
    NativeEvent,
    /// A `javascript:` URL in an attribute the browser loads or follows.
    JavascriptUrl,
}

impl CspAttributeProblem {
    /// The name Python uses for this problem.
    pub fn code(self) -> &'static str {
        match self {
            CspAttributeProblem::NativeEvent => "native-event",
            CspAttributeProblem::JavascriptUrl => "javascript-url",
        }
    }
}

/// Judge one attribute written literally in a template, by the same rules
/// [`check_output_html`] applies to a finished page under strict CSP.
///
/// `raw_value` is the value as written, before character references are
/// decoded, or `None` for an attribute written without a value. ASCII
/// letters in the tag and attribute names are compared without regard to
/// case, as the browser reads them. This lets `citry check` and the editor
/// report what the render-time check would report for the same attribute,
/// with no second copy of the rules to keep in step. The caller decides
/// which attributes the browser reads as attributes at all: inside
/// `<noscript>` or `<xmp>`, for example, the page check reads none.
pub fn csp_attribute_problem(
    tag: &str,
    name: &str,
    raw_value: Option<&str>,
) -> Option<CspAttributeProblem> {
    let tag = ascii_lower(tag);
    let name = ascii_lower(name);
    // No URL attribute starts with `on` (a test checks this), so at most one
    // rule can match, and the cheaper name check goes first.
    if is_native_event_attribute(&name) {
        return Some(CspAttributeProblem::NativeEvent);
    }
    // The page check reads a value-less attribute as an empty value, which
    // is never a `javascript:` URL.
    let raw_value = raw_value?;
    if is_url_attribute(&tag, &name) && is_javascript_url(&decode_html_attribute(raw_value)) {
        return Some(CspAttributeProblem::JavascriptUrl);
    }
    None
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
///
/// After ASCII whitespace is trimmed, a value that still holds a character
/// a browser may skip ([`may_be_skipped_by_browser`]), other than ASCII
/// whitespace between words, counts as running. Chromium drops some of
/// those characters from the ends of a type before it compares, so
/// `"\u{b}text/javascript"` runs there, and no real data block needs one.
pub fn script_type_is_executable(value: &str) -> bool {
    let trimmed = value.trim_matches(is_html_space);
    // Count it as running rather than copy one browser's list of the
    // characters it trims, which differs between browsers and can change.
    if trimmed
        .chars()
        .any(|c| may_be_skipped_by_browser(c) && !is_html_space(c))
    {
        return true;
    }
    let normalized = trimmed.to_ascii_lowercase();
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
/// `inside_form` says a `<form>` owns the control, as the browser decides
/// it. A submit button, an input not of type `button` or `reset`, a
/// `select`, or a `textarea` then has the form as its fallback. A non-empty
/// `form` attribute counts as a fallback too; the check does not look up
/// the form it names.
fn is_handler_only_control(
    tag: &str,
    values: &HashMap<Cow<'_, str>, Cow<'_, str>>,
    activation_attrs: &[Cow<'_, str>],
    has_managed_handler: bool,
    inside_form: bool,
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
            button_type == "button" || (button_type == "submit" && !inside_form && !present("form"))
        }
        "input" => {
            let input_type = values
                .get("type")
                .map_or(Cow::Borrowed("text"), |value| ascii_lower(value));
            matches!(input_type.as_ref(), "button" | "reset") || (!inside_form && !present("form"))
        }
        "select" | "textarea" => !inside_form && !present("form"),
        _ => matches!(tag, "div" | "span" | "section"),
    }
}

// ---------------------------------------------------------------------------
// Embedded documents
// ---------------------------------------------------------------------------

/// What a tag's other attributes say about how its URLs are opened,
/// worked out once per tag so a tag with many attributes is not rescanned.
#[derive(Clone, Copy, Default)]
struct DocumentFacts {
    /// The tag is an SVG animation that writes a link's `href`
    /// ([`animation_sets_href`]).
    animates_href: bool,
    /// The tag is a `<meta http-equiv="refresh">`, whose `content` names a
    /// URL the browser opens ([`meta_refreshes`]).
    refreshes: bool,
}

impl DocumentFacts {
    fn of(tag: &str, attributes: &[OutputAttribute]) -> Self {
        Self {
            animates_href: animation_sets_href(tag, attributes),
            refreshes: meta_refreshes(tag, attributes),
        }
    }
}

/// Whether a tag is a `<meta>` whose first `http-equiv` is `refresh`, so
/// the browser opens the URL in its `content` after the given delay.
fn meta_refreshes(tag: &str, attributes: &[OutputAttribute]) -> bool {
    tag == "meta"
        && attributes
            .iter()
            .find(|attr| attr.name.eq_ignore_ascii_case("http-equiv"))
            .is_some_and(|attr| {
                let value = decode_html_attribute(if attr.has_value { &attr.value } else { "" });
                value
                    .trim_matches(is_html_space)
                    .eq_ignore_ascii_case("refresh")
            })
}

/// The attributes whose URL the browser loads as a document in a frame.
fn loads_document_url(tag: &str, name: &str) -> bool {
    matches!(
        (tag, name),
        ("iframe", "src") | ("frame", "src") | ("object", "data") | ("embed", "src")
    )
}

/// Whether the browser may open an attribute's URL as a document, in a
/// frame or in a window: the frame attributes of [`loads_document_url`], a
/// link (`href` on `<a>` or `<area>`, `xlink:href` on an SVG `<a>`), a form
/// (`action`, `formaction`), or the value of an SVG animation that sets a
/// link. A link or form opens a `data:` document only in a frame, but any
/// link can be sent to one by its `target` or by `<base target>`, so every
/// link counts.
fn opens_document_url(tag: &str, name: &str, facts: DocumentFacts) -> bool {
    loads_document_url(tag, name)
        || matches!(
            (tag, name),
            ("a" | "area", "href")
                | ("a", "xlink:href")
                | ("form", "action")
                | ("button" | "input", "formaction")
        )
        || (facts.animates_href && is_animation_value_attribute(name))
}

/// Whether an attribute can hold or open a whole document, so its value
/// must go through [`attribute_document_requires_javascript`].
fn may_hold_document(tag: &str, name: &str, facts: DocumentFacts) -> bool {
    (tag == "iframe" && name == "srcdoc")
        || (facts.refreshes && name == "content")
        || opens_document_url(tag, name, facts)
}

/// The `data:` URL a `<meta http-equiv="refresh">` opens, read from its
/// `content` the way the HTML standard reads a refresh: a delay of digits
/// and `.`, spaces, `;` or `,`, spaces, an optional `url` and `=`, an
/// optional quote, then the URL. It is `None` when that URL does not start
/// with `data:`.
///
/// The delay is optional here although the browser needs one, and the text
/// after the URL's closing quote is kept, so the check can only read more
/// than the browser opens. For the same reason every gap skips each
/// character that [`may_be_skipped_by_browser`] accepts, although a browser
/// skips fewer. Chromium skips U+000B and Unicode spaces around the delay
/// and before the URL.
fn refresh_data_url(content: &str) -> Option<String> {
    // The browser drops tabs and line breaks from a URL, so `da\tta:`
    // still starts one.
    let content = content.replace(['\t', '\n', '\r'], "");
    let rest = content
        .trim_start_matches(may_be_skipped_by_browser)
        .trim_start_matches(|c: char| c.is_ascii_digit() || c == '.')
        .trim_start_matches(may_be_skipped_by_browser);
    let rest = rest.strip_prefix([';', ',']).unwrap_or(rest);
    let rest = rest.trim_start_matches(may_be_skipped_by_browser);
    // After `url` the browser expects `=`; without one, both readings are
    // tried, so neither can hide a `data:` URL.
    let mut candidates = vec![rest];
    if rest
        .get(..3)
        .is_some_and(|word| word.eq_ignore_ascii_case("url"))
    {
        let after = rest[3..].trim_start_matches(may_be_skipped_by_browser);
        candidates.push(after.strip_prefix('=').unwrap_or(after));
    }
    candidates.into_iter().find_map(|candidate| {
        let candidate = candidate.trim_start_matches(may_be_skipped_by_browser);
        let candidate = candidate.strip_prefix(['"', '\'']).unwrap_or(candidate);
        // The URL parser drops leading control characters and spaces, and
        // Chromium also drops the Unicode spaces it trims elsewhere.
        let url = candidate.trim_start_matches(may_be_skipped_by_browser);
        url.get(..5)
            .is_some_and(|scheme| scheme.eq_ignore_ascii_case("data:"))
            .then(|| url.to_owned())
    })
}

/// Whether an attribute value holds or opens a document with code the
/// browser would run: an `iframe srcdoc`, or a `data:` URL that
/// [`data_url_requires_javascript`] reports, in a frame, a link, a form, an
/// SVG animation of a link, or a `<meta http-equiv="refresh">`.
fn attribute_document_requires_javascript(
    tag: &str,
    name: &str,
    value: &str,
    facts: DocumentFacts,
    depth: usize,
    documents: &EmbeddedDocuments,
) -> bool {
    if tag == "iframe" && name == "srcdoc" {
        return html_document_requires_javascript(value, depth, PageKind::Srcdoc, documents);
    }
    if facts.refreshes && name == "content" {
        return refresh_data_url(value)
            .is_some_and(|url| data_url_requires_javascript(&url, depth, documents));
    }
    if !opens_document_url(tag, name, facts) {
        return false;
    }
    // An animation's `values` is a list the browser splits on `;`, and the
    // link takes each item in turn.
    if facts.animates_href && name == "values" {
        return value
            .split(';')
            .any(|item| data_url_requires_javascript(item, depth, documents));
    }
    data_url_requires_javascript(value, depth, documents)
}

/// Whether a `data:` URL loads a document with code the browser would run.
///
/// A `text/html` document is read like any other page. A type the browser
/// shows as text, an image, media, or a download runs nothing. Every other
/// type counts as running code without being read. That covers SVG, XHTML,
/// and the other XML types, whose scripts the browser runs and which the
/// HTML scanner would read wrongly (an XML document can declare entities
/// that expand into a `<script>`, and XHTML builds elements inside
/// `<title>`). It also covers types a browser reads as HTML on its own, such
/// as `*/*` in Firefox, and spellings no browser was tested with.
fn data_url_requires_javascript(value: &str, depth: usize, documents: &EmbeddedDocuments) -> bool {
    match decode_data_url_document(value) {
        Some(DataUrlDocument::Html(document)) => {
            html_document_requires_javascript(&document, depth, PageKind::DataUrl, documents)
        }
        Some(DataUrlDocument::Unread) => true,
        None => false,
    }
}

// Four nested documents is deeper than any real page goes, so a deeper one
// counts as running code instead of being read further.
const MAX_EMBEDDED_DEPTH: usize = 4;

/// Whether a document holds code the browser would run. `kind` says whether
/// it is the document of an `<iframe srcdoc>` or of a `data:` URL, which
/// browsers read in different modes (see [`PageKind`]).
fn html_document_requires_javascript(
    html: &str,
    depth: usize,
    kind: PageKind,
    documents: &EmbeddedDocuments,
) -> bool {
    if depth >= MAX_EMBEDDED_DEPTH {
        return true;
    }
    let key = (html.to_owned(), depth, kind == PageKind::Srcdoc);
    if let Some(&known) = documents.answers.borrow().get(&key) {
        return known;
    }
    let requires_javascript = read_document_requires_javascript(html, depth, kind, documents);
    documents
        .answers
        .borrow_mut()
        .insert(key, requires_javascript);
    requires_javascript
}

/// Read a document for [`html_document_requires_javascript`].
fn read_document_requires_javascript(
    html: &str,
    depth: usize,
    kind: PageKind,
    documents: &EmbeddedDocuments,
) -> bool {
    // A browser decodes a `srcdoc` value with the outer page, so raw bytes in
    // it depend on that page's encoding. A value written as `&#27;` reaches
    // the document after decoding, but the check reads the value with its
    // references decoded and cannot tell the two apart, so either counts as
    // running code.
    if encoding_dependent_span(html).is_some() {
        return true;
    }
    // Browsers differ on some tree-building rules, and code that any reading
    // finds counts.
    let mut requires_javascript = false;
    let finished = for_each_reading(html, kind, |rules| -> Result<ReadingNeeds, HtmlTooLarge> {
        let scan = scan_output_html_under(html, rules, documents.work_left.clone())?;
        // A tag where browsers may build a different tree counts as code,
        // the same as on the page itself.
        requires_javascript |=
            !scan.differences.is_empty() || tags_require_javascript(&scan.tags, depth, documents);
        Ok(ReadingNeeds::of(&scan))
    });
    // A document the scan refuses cannot be shown to hold no script, so it
    // counts as running code, the same as one nested too deep.
    requires_javascript || finished.is_err()
}

/// Whether one reading of a document holds code the browser would run.
fn tags_require_javascript(
    tags: &[OutputTag],
    depth: usize,
    documents: &EmbeddedDocuments,
) -> bool {
    for tag in tags {
        let name = ascii_lower(&tag.name);
        if name == "script" && raw_script_is_executable(tag) {
            return true;
        }
        let facts = DocumentFacts::of(&name, &tag.attributes);
        for attr in &tag.attributes {
            let attr_name = ascii_lower(&attr.name);
            let value = decode_html_attribute(if attr.has_value { &attr.value } else { "" });
            if is_native_event_attribute(&attr_name)
                || (is_url_value(&name, &attr_name, facts.animates_href)
                    && is_javascript_url_value(&attr_name, &value))
            {
                return true;
            }
            if may_hold_document(&name, &attr_name, facts)
                && attribute_document_requires_javascript(
                    &name,
                    &attr_name,
                    &value,
                    facts,
                    depth + 1,
                    documents,
                )
            {
                return true;
            }
        }
    }
    false
}

/// The document a `data:` URL loads in a frame, as far as the check needs.
enum DataUrlDocument {
    /// A `text/html` document, decoded.
    Html(String),
    /// A document the check does not read, which counts as running code.
    Unread,
}

/// Whether a media type, already lowercased, is one the browser shows as
/// text, an image, audio, video, a font, or a download, so a document of
/// this type runs no script.
///
/// An empty type is `text/plain` in a `data:` URL. An image, audio, video,
/// or font type counts unless its subtype ends in `+xml`, the mark of an
/// XML document such as `image/svg+xml`. Chromium 151 and Firefox 153 ran no
/// script from any of these with an HTML or SVG body.
fn is_inert_media_type(media_type: &str) -> bool {
    if matches!(
        media_type,
        "" | "text/plain"
            | "text/css"
            | "text/csv"
            | "application/json"
            | "application/pdf"
            | "application/octet-stream"
    ) {
        return true;
    }
    media_type.split_once('/').is_some_and(|(kind, subtype)| {
        matches!(kind, "image" | "audio" | "video" | "font")
            && !subtype.is_empty()
            && !subtype.ends_with("+xml")
    })
}

/// Whether a `data:` URL header (after `data:`, lowercased) marks the
/// payload as base64.
///
/// The Fetch standard's rule is a header that ends in `;`, any spaces, and
/// `base64`, so `; base64` counts. A `;base64` anywhere else also counts,
/// so a header the browser reads either way is decoded as base64; a raw
/// HTML payload with a tag in it is never valid base64, so it then counts
/// as running code.
fn data_url_is_base64(header: &str) -> bool {
    let trimmed = header.trim_matches(is_html_space);
    let ends_in_base64 = trimmed
        .strip_suffix("base64")
        .is_some_and(|rest| rest.trim_end_matches(' ').ends_with(';'));
    ends_in_base64 || header.contains(";base64")
}

/// The byte span of the first text in `html` whose tags depend on the
/// encoding the browser reads the page in, or `None` when there is none.
///
/// The check reads the page as text and cannot know the encoding: a page
/// can declare one in a `<meta charset>` or its response can name one, and
/// the check sees neither reliably. Three things change the tags a browser
/// finds, and this looks for them directly, whichever encoding is in use:
///
/// - An ISO-2022-JP escape: ESC `$` or ESC `(`. Citry writes ESC in an
///   escaped value as `&#27;`, so this finds text Citry did not escape:
///   `Markup`, inline `Script` or `Style` content, and the template's own
///   text. Chromium 156 and Firefox 157
///   act on five such sequences. ESC `$` `@`, ESC `$` `B` and ESC `(` `I`
///   make the browser read later ASCII bytes as parts of other characters,
///   so a quote or a `>` disappears. ESC `(` `B` and ESC `(` `J` are removed
///   from the text, so the bytes on either side join up. Terminal colors use
///   ESC `[`, which neither does.
/// - Non-ASCII text in a CDATA section. In Shift_JIS, Big5, GBK and GB18030
///   the last byte of a UTF-8 character can start a character that takes the
///   next `]` with it, so `]]>` does not end the section there, and what the
///   check reads as a comment after it can be live.
///
/// - A `<` followed by a NUL byte. A response header that names UTF-16 makes the
///   browser read two bytes as one character, so ASCII text spelled with a
///   NUL byte after or before each character is markup there. Any tag in
///   such text starts with `<` and then a NUL byte, in both byte orders.
///   Citry escapes `<` in a value, so this finds text Citry did not escape.
///
/// We found no other case. A probe decoded each character followed by each
/// ASCII byte in every encoding browsers support, apart from UTF-16 and the
/// `replacement` encodings: outside ISO-2022-JP a non-ASCII character took
/// only a following byte of 0x40 or above with it and never made ASCII. The
/// bytes that shape tags are below 0x40. When such a character takes a letter
/// of a name, the character stays in the name, so the check and the browser
/// both read a name that is not ASCII.
fn encoding_dependent_span(html: &str) -> Option<(usize, usize)> {
    let bytes = html.as_bytes();
    for (index, _) in bytes.iter().enumerate().filter(|(_, byte)| **byte == 0x1b) {
        if let [b'$' | b'(', ..] = &bytes[index + 1..] {
            return Some((index, index + 2));
        }
    }
    if let Some(index) = bytes.windows(2).position(|pair| pair == b"<\0") {
        return Some((index, index + 2));
    }
    let mut cursor = 0;
    while let Some(offset) = html[cursor..].find("<![CDATA[") {
        let start = cursor + offset;
        // An unended section runs to the end of the page in the browser too.
        let end = html[start..]
            .find("]]>")
            .map_or(html.len(), |end| start + end);
        if !html[start..end].is_ascii() {
            return Some((start, end));
        }
        cursor = end;
    }
    None
}

/// Whether a browser may read a decoded payload differently from the check,
/// because the browser may decode it in another encoding.
///
/// The browser follows a `charset` parameter, a byte order mark, a
/// `<meta charset>`, or its own guess, and the check reads none of them.
/// Every encoding browsers support reads ASCII bytes as the same ASCII text,
/// apart from UTF-16 and four bytes: zero, 0x0E, 0x0F, and the escape byte.
/// UTF-16 spells every ASCII character with a zero byte, so a payload
/// without one holds no ASCII markup there, and ISO-2022-JP changes the
/// other three. Any byte above 0x7F counts too, because its meaning
/// depends on the encoding. In Shift_JIS the bytes 0x81 0x40 spell U+3000,
/// which Chromium skips in a refresh, and which the check could not see.
/// Counting these payloads means the check need not know each encoding.
fn payload_may_hide_markup(body: &[u8]) -> bool {
    body.iter()
        .any(|&byte| !byte.is_ascii() || matches!(byte, 0x00 | 0x0e | 0x0f | 0x1b))
}

/// Read the document a `data:` URL loads, or return `None` for a URL that
/// is not a `data:` URL or whose type runs no script.
///
/// The browser drops tabs and line breaks anywhere in a URL, so they are
/// removed first. An HTML payload is percent-decoded, then base64-decoded
/// when [`data_url_is_base64`] says so. A payload that is not valid base64,
/// or that [`payload_may_hide_markup`], is [`DataUrlDocument::Unread`], so
/// a document the check cannot read counts as running code.
fn decode_data_url_document(value: &str) -> Option<DataUrlDocument> {
    let value = value.trim_start_matches(|c: char| c <= '\u{20}');
    let value: Cow<str> = if value.contains(['\t', '\n', '\r']) {
        Cow::Owned(value.replace(['\t', '\n', '\r'], ""))
    } else {
        Cow::Borrowed(value)
    };
    let (header, payload) = value.split_once(',')?;
    let folded = ascii_lower(header);
    let header = folded.strip_prefix("data:")?;
    let media_type = header
        .split(';')
        .next()
        .unwrap_or("")
        .trim_matches(is_html_space);
    if media_type != "text/html" {
        return (!is_inert_media_type(media_type)).then_some(DataUrlDocument::Unread);
    }
    let bytes = percent_decode(payload.as_bytes());
    let body = if data_url_is_base64(header) {
        match decode_strict_base64(&bytes) {
            Some(body) => body,
            None => return Some(DataUrlDocument::Unread),
        }
    } else {
        bytes
    };
    if payload_may_hide_markup(&body) {
        return Some(DataUrlDocument::Unread);
    }
    // The check above accepted only ASCII, so this always succeeds; if it
    // ever fails, the document counts as unread.
    String::from_utf8(body)
        .ok()
        .map(DataUrlDocument::Html)
        .or(Some(DataUrlDocument::Unread))
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

/// Decode the character references in an attribute value the way the
/// browser does when it reads the value from an attribute.
///
/// Each reference that matches `&(#[xX]hex+|#digits+|letter alnum+);?` is
/// decoded. A numeric reference decodes by the HTML standard: `&#0;`, a
/// surrogate and a value past U+10FFFF become U+FFFD, `&#128;` to `&#159;`
/// map to Windows-1252, and every other code point is kept, control
/// characters and noncharacters included. A named
/// reference decodes when it ends with `;` and names an entity. A legacy
/// name without `;` (such as `&copy`) decodes only when the next source
/// character is not `=` or an ASCII letter or digit; otherwise the browser
/// keeps it as typed, so `?a=1&copy=2` stays a URL. A reference the browser
/// does not know stays literal.
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
            // The browser's attribute rule looks at the character right
            // after the reference to decide a legacy name without `;`.
            let next = source[position + length..].chars().next();
            let value = unescape_reference(raw, next);
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

/// Decode one reference, with `next` the source character right after it.
///
/// Returns `raw` unchanged to mean "the browser keeps this literal".
fn unescape_reference(raw: &str, next: Option<char>) -> Cow<'_, str> {
    let body = &raw[1..];
    if let Some(number) = body.strip_prefix('#') {
        let number = number.strip_suffix(';').unwrap_or(number);
        let code_point = match number.strip_prefix(['x', 'X']) {
            Some(hex) => parse_code_point(hex, 16),
            None => parse_code_point(number, 10),
        };
        return Cow::Owned(numeric_reference(code_point));
    }
    // A reference that ends with `;` and names an entity decodes in full.
    if body.ends_with(';') {
        if let Some(value) = entity(body) {
            return Cow::Owned(value);
        }
    }
    // A legacy name without `;`. The browser decodes it only when the next
    // source character does not continue a name or begin an assignment.
    let name = body.strip_suffix(';').unwrap_or(body);
    if let Some(value) = entity(name) {
        if next.is_some_and(|c| c == '=' || c.is_ascii_alphanumeric()) {
            return Cow::Borrowed(raw);
        }
        return Cow::Owned(value);
    }
    // The name is not an entity. Any known prefix of it is followed by
    // another name character, so in an attribute value the browser keeps the
    // whole reference as typed.
    Cow::Borrowed(raw)
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

// The HTML standard's table for U+0080 to U+009F: Windows-1252, except five
// code points that Windows-1252 leaves undefined and that keep their own value.
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
        // The browser keeps every other code point, so a control character
        // stays in the value: `&#27;` in a `data:` URL stays an escape byte
        // that `payload_may_hide_markup` must see.
        _ => char::from_u32(code_point).map_or_else(String::new, String::from),
    }
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
        .expect("the test pages are far below the limits")
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
            case: None,
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

    // The expected values are what a browser reads from a quoted attribute
    // value. `packages/py/citry/tests/_output_policy_reference.py` keeps the
    // Python copy of this decoder, and the differential test compares them.
    #[test]
    fn attribute_values_decode_the_way_a_browser_reads_them() {
        let cases = [
            ("plain", "plain"),
            ("&amp;", "&"),
            // A legacy name at the end of the value decodes.
            ("&amp", "&"),
            // A legacy name the next character continues stays literal.
            ("&ampx;", "&ampx;"),
            ("&AMP;x", "&x"),
            ("&notit;", "&notit;"),
            ("&notin;", "\u{2209}"),
            ("&bogus;", "&bogus;"),
            // A legacy name followed by `=` or an ASCII letter or digit stays
            // literal, so a query string is not rewritten.
            ("?a=1&copy=2", "?a=1&copy=2"),
            ("&copya", "&copya"),
            ("&copy9", "&copy9"),
            // A legacy name followed by any other character decodes.
            ("&copy.", "\u{a9}."),
            ("&copy", "\u{a9}"),
            ("&lta b", "&lta b"),
            ("&lt;", "<"),
            ("&lt", "<"),
            ("&#128;", "\u{20ac}"),
            ("&#129;", "\u{81}"),
            ("&#xD800;", "\u{fffd}"),
            ("&#1;", "\u{1}"),
            ("&#27;", "\u{1b}"),
            ("&#11;", "\u{b}"),
            ("&#xFDD0;", "\u{fdd0}"),
            ("&#0;", "\u{fffd}"),
            ("&#13;", "\u{d}"),
            ("&#x110000;", "\u{fffd}"),
            ("&#xFFFE;", "\u{fffe}"),
            ("&#x1FFFF;", "\u{1ffff}"),
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
                "&ampxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;",
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

    // Chromium 156 dropped each of these from either end of a JavaScript
    // type and ran `<script type="\u{b}text/javascript">`. Firefox 157 did
    // not. Neither dropped them around `module`, which the check counts
    // anyway.
    const CHROMIUM_TYPE_SPACES: [char; 16] = [
        '\u{b}', '\u{1680}', '\u{2000}', '\u{2001}', '\u{2002}', '\u{2003}', '\u{2004}',
        '\u{2005}', '\u{2006}', '\u{2007}', '\u{2008}', '\u{2009}', '\u{200a}', '\u{2028}',
        '\u{205f}', '\u{3000}',
    ];

    #[test]
    fn a_script_type_with_a_character_a_browser_may_skip_counts_as_running() {
        for space in CHROMIUM_TYPE_SPACES {
            for value in [
                format!("{space}text/javascript"),
                format!("text/javascript{space}"),
                format!("{space}module"),
            ] {
                assert!(script_type_is_executable(&value), "{value:?}");
            }
        }
        // No browser tested skips these, but the check does not track
        // which characters each browser skips, so any of them counts.
        for value in [
            "\u{a0}application/json",
            "application/json\u{85}",
            "\u{feff}text/plain",
            "text/x-template\u{0}",
            "text/javascript\u{3000};x=1",
            "text/java\u{200b}script",
            "text/javascr\u{130}pt",
        ] {
            assert!(script_type_is_executable(value), "{value:?}");
        }
        // ASCII whitespace inside a data type is still a data type.
        assert!(!script_type_is_executable(" application/json ; x=1 "));
    }

    #[test]
    fn a_raw_script_type_with_a_character_a_browser_may_skip_is_reported() {
        // At the top level, inside an embedded document, typed raw or as a
        // reference, and raw U+000B, which the browser and this check both
        // read from `&#11;`.
        for space in CHROMIUM_TYPE_SPACES {
            let reference = format!("&amp;#x{:x};", u32::from(space));
            for html in [
                format!("<iframe srcdoc=\"&lt;script type={space}text/javascript&gt;x()&lt;/script&gt;\"></iframe>"),
                format!("<iframe srcdoc=\"&lt;script type='{reference}text/javascript'&gt;x()&lt;/script&gt;\"></iframe>"),
            ] {
                assert!(embedded_document_reported(&html), "{html:?}");
            }
            let html = format!("<script type=\"text/javascript{space}\">x()</script>");
            let report = check(
                &html,
                PolicyPass::Settled,
                false,
                Some(JavascriptMode::Forbid),
                None,
                &[],
                None,
            );
            assert!(
                report.events.iter().any(|event| matches!(
                    event,
                    PolicyEvent::RawElement(raw) if raw.executable
                )),
                "{html:?}"
            );
        }
    }

    /// The rule codes the JavaScript policy reports for `html`.
    fn javascript_rules(html: &str) -> Vec<&'static str> {
        check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Forbid),
            None,
            &[],
            None,
        )
        .events
        .iter()
        .filter_map(|event| match event {
            PolicyEvent::Finding(finding) => Some(finding.rule.code()),
            _ => None,
        })
        .collect()
    }

    #[test]
    fn text_whose_tags_depend_on_the_encoding_is_reported() {
        for (html, span) in [
            // Each ISO-2022-JP escape Chromium 156 and Firefox 157 act on.
            // The first three take later bytes, and the last two are removed.
            ("<p title='\u{1b}$B'>x</p>", (10, 12)),
            ("<p title='\u{1b}$@'>x</p>", (10, 12)),
            ("<p title='\u{1b}(I'>x</p>", (10, 12)),
            ("<scr\u{1b}(Bipt>x()</script>", (4, 6)),
            ("<scr\u{1b}(Jipt>x()</script>", (4, 6)),
            // Non-ASCII text in a CDATA section, which Shift_JIS, Big5, GBK
            // and GB18030 can read as a longer section.
            ("<svg><![CDATA[\u{3041}]]></svg>", (5, 17)),
            ("<svg><![CDATA[a]]><![CDATA[\u{e9}]]></svg>", (18, 29)),
            ("<svg><![CDATA[\u{e9}", (5, 16)),
        ] {
            assert!(
                javascript_rules(html).contains(&"js-page-encoding"),
                "{html:?}"
            );
            assert_eq!(encoding_dependent_span(html), Some(span), "{html:?}");
        }
        for html in [
            "<p>plain</p>",
            // Terminal colors, and an escape at the end of the page.
            "<pre>\u{1b}[31mred\u{1b}[0m\u{1b}</pre>\u{1b}",
            // ASCII in a section, and non-ASCII outside one.
            "<svg><![CDATA[a]]></svg><p>\u{3041}]]></p>",
            "<p>[caf\u{e9}]</p>",
        ] {
            assert_eq!(encoding_dependent_span(html), None, "{html:?}");
        }
    }

    #[test]
    fn a_tag_spelled_with_nul_bytes_is_reported() {
        for page in [
            "<\0s\0c\0r\0i\0p\0t\0>\0",
            "\0<\0s\0c\0r\0i\0p\0t\0>",
            "<p>abc</p><\0b\0>\0",
        ] {
            assert_eq!(javascript_rules(page), ["js-page-encoding"], "{page:?}");
        }
        for page in [
            "<p>\0</p>",
            "<p title=\"\0\">x</p>",
            "a\0b",
            "<p>&lt;\0</p>",
        ] {
            assert_eq!(javascript_rules(page), Vec::<&str>::new(), "{page:?}");
        }
    }

    #[test]
    fn code_only_one_reading_of_a_select_finds_is_reported() {
        for page in [
            "<select><style><!-- </style><img onerror=x><!-- --></select>",
            "<select><svg><![CDATA[><!-- ]]><img onerror=x><!-- --></select>",
            // The tags of the first `<select>` decide what the second reads.
            "<select><button></button><svg></select><select><style><!-- </style><img onerror=x>",
        ] {
            assert_eq!(javascript_rules(page), ["js-native-handler"], "{page:?}");
            let srcdoc = format!("<iframe srcdoc='{page}'></iframe>");
            assert!(embedded_document_reported(&srcdoc), "{srcdoc}");
        }
    }

    #[test]
    fn code_only_chromium_finds_after_an_end_tag_with_an_svg_name_is_reported() {
        let page = "<clippath><svg></clippath><style><img onerror=x></style>";
        assert_eq!(javascript_rules(page), ["js-native-handler"]);
        let srcdoc = format!("<iframe srcdoc='{page}'></iframe>");
        assert!(embedded_document_reported(&srcdoc), "{srcdoc}");
    }

    #[test]
    fn code_past_an_svg_or_mathml_element_that_holds_html_is_reported() {
        for page in [
            "<span><math><mtext></span><![CDATA[><!-- ]]><img onerror=x><!-- -->",
            "<li><svg><desc><li></li><![CDATA[><!-- ]]><img onerror=x><!-- -->",
        ] {
            assert_eq!(javascript_rules(page), ["js-native-handler"], "{page:?}");
        }
    }

    #[test]
    fn code_only_firefox_finds_after_a_stray_end_tag_is_reported() {
        for page in [
            "<svg><a><title></p></a><style><!-- </style><img onerror=x><!-- -->",
            "<svg><a><desc></br></a><style><!-- </style><img onerror=x><!-- -->",
            // The select and end tag rules can each hide the code on its own.
            "<select><svg><a><title></p></a><style><!-- </style><img onerror=x><!-- -->",
        ] {
            assert_eq!(javascript_rules(page), ["js-native-handler"], "{page:?}");
            let srcdoc = format!("<iframe srcdoc='{page}'></iframe>");
            assert!(embedded_document_reported(&srcdoc), "{srcdoc}");
        }
    }

    #[test]
    fn a_select_both_readings_agree_on_reports_a_tag_once() {
        assert_eq!(
            javascript_rules("<select onchange=x><option onclick=y></select>"),
            ["js-native-handler", "js-native-handler"]
        );
    }

    /// The findings on a page under `forbid`, as (rule, case or attribute).
    fn javascript_findings(html: &str) -> Vec<(&'static str, Option<String>)> {
        check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Forbid),
            None,
            &[],
            None,
        )
        .events
        .into_iter()
        .filter_map(|event| match event {
            PolicyEvent::Finding(finding) => Some((
                finding.rule.code(),
                finding.case.map(str::to_owned).or(finding.attribute),
            )),
            _ => None,
        })
        .collect()
    }

    /// Every page here runs its `<img onerror>` in Chromium 156, Firefox
    /// 157, or both, while html5ever 0.29.0 alone hides it, as checked in
    /// those browsers. The check refuses the tag where the trees differ,
    /// with the case that names the fix, on the page and in `srcdoc` and
    /// `data:` documents.
    #[test]
    fn pages_browsers_read_another_way_are_refused() {
        const IMG: &str = "<img src=x onerror=\"document.title=1\">";
        let cdata = format!("<![CDATA[><!-- ]]>{IMG}<!-- -->");
        let style = format!("<style><!--</style>{IMG}<!-- -->");
        let pages = [
            (format!("<math><annotation-xml encoding=text/html></br>{cdata}"), "annotation-xml-html"),
            (format!("<math><annotation-xml encoding=text/html></p>{cdata}"), "annotation-xml-html"),
            (
                format!("<foreignObject><a></foreignobject><math></a><noscript><!-- </noscript>{IMG}"),
                "reopened-formatting",
            ),
            (format!("<p><b></p><svg></b>{style}"), "reopened-formatting"),
            (format!("<p><math><annotation-xml encoding=text/html><div></p></div>{cdata}"), "annotation-xml-html"),
            (format!("<select><math><annotation-xml encoding=text/html></select>{cdata}"), "annotation-xml-html"),
            (format!("<select></b><math><annotation-xml></select></noscript>{cdata}"), "annotation-xml-end-tag"),
            (format!("<math><annotation-xml encoding=text/html><svg><br>{cdata}"), "annotation-xml-html"),
            (format!("<math><annotation-xml encoding=text/html><svg><p></p>{cdata}"), "annotation-xml-html"),
            (format!("<svg><desc><span><isindex></span>{cdata}"), "isindex"),
            (format!("<svg><desc><b><isindex></b>{cdata}"), "isindex"),
            (format!("<svg><desc><span><search></span></desc>{style}"), "search"),
            (format!("<svg><desc><b><search></b></desc>{style}"), "search"),
            (format!("<svg><desc><li><search><li></li></desc>{style}"), "search"),
            (format!("<select><option><dd><option><svg><g></dd>{cdata}"), "select-closes-element"),
            (format!("<select><option><dd><hr><svg><g></dd>{cdata}"), "select-closes-element"),
            (format!("<select><optgroup><dd><optgroup><svg><g></dd>{cdata}"), "select-closes-element"),
            (format!("<select><b></select>x<svg></b>{style}"), "formatting-across-select"),
            (
                format!(
                    "<div><template shadowrootmode=\"open\"><thead><caption><svg><g></caption>{style}</template></div>"
                ),
                "thead-outside-table",
            ),
            (
                format!(
                    "<!DOCTYPE html PUBLIC \"+//Silmaril//dtd html Pro v0r11 19970101//\"><span><p><table></table><svg><g></span>{cdata}"
                ),
                "quirks-doctype-table",
            ),
            (
                format!(
                    "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"\"><span><p><table></table><svg><g></span>{cdata}"
                ),
                "quirks-doctype-table",
            ),
            (format!("<svg><desc><p><b></p></b></desc></svg>x<svg><g></b>{cdata}"), "formatting-end-tag-in-foreign"),
        ];
        for (page, case) in &pages {
            let findings = javascript_findings(page);
            assert!(
                findings.contains(&("js-parser-difference", Some((*case).to_owned()))),
                "{page}: {findings:?}"
            );
            let attribute = page.replace('&', "&amp;").replace('"', "&quot;");
            assert!(
                embedded_document_reported(&format!("<iframe srcdoc=\"{attribute}\"></iframe>")),
                "{page}"
            );
            let encoded: String = page.bytes().map(|byte| format!("%{byte:02X}")).collect();
            assert!(
                embedded_document_reported(&format!(
                    "<iframe src=\"data:text/html,{encoded}\"></iframe>"
                )),
                "{page}"
            );
        }
        // `warn` mode reports the same tags.
        let warned = check(
            "<p><b></p><svg></svg>",
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Warn),
            None,
            &[],
            None,
        );
        assert_eq!(
            warned.events,
            [PolicyEvent::Finding(Finding {
                rule: Rule::JsParserDifference,
                tag: "svg".to_owned(),
                attribute: None,
                start: 10,
                end: 15,
                token_start: 10,
                cids: Vec::new(),
                case: Some("reopened-formatting"),
            })]
        );
        // The CSP check alone does not.
        let csp_only = check(
            "<p><b></p><svg></svg>",
            PolicyPass::Settled,
            true,
            None,
            None,
            &[],
            None,
        );
        assert_eq!(csp_only.events, []);
    }

    /// Two readings of each page find one tag under two cases. The tag is
    /// one place to fix, so it is reported once, under the case of the first
    /// reading that found it.
    #[test]
    fn a_tag_two_readings_find_is_reported_once() {
        for (page, tag, start, case) in [
            (
                "<thead><select><i><i><th><i><i></i><i><math><form><annotation-xml encoding=text/html></select></x><table><tr></p><svg>",
                "select",
                85,
                "formatting-across-select",
            ),
            (
                "<colgroup><b><button></b><b><select><col><em id=x><b></b><a></td><math><a><annotation-xml encoding=text/html></b>",
                "b",
                109,
                "formatting-end-tag-in-foreign",
            ),
            (
                "<tr><i><i><select><caption><i><i></i><b><svg><caption><desc><foreignObject></b><form></p>",
                "b",
                75,
                "formatting-end-tag-in-foreign",
            ),
        ] {
            let report = check(
                page,
                PolicyPass::Settled,
                false,
                Some(JavascriptMode::Warn),
                None,
                &[],
                None,
            );
            let cases: Vec<_> = report
                .events
                .iter()
                .filter_map(|event| match event {
                    PolicyEvent::Finding(finding)
                        if finding.rule == Rule::JsParserDifference
                            && finding.tag == tag
                            && finding.start == start =>
                    {
                        finding.case
                    }
                    _ => None,
                })
                .collect();
            assert_eq!(cases, [case], "{page}");
        }
    }

    /// In these pages html5ever 0.29.0 alone could misread the open
    /// `<form>` or the closed `<b>`, and the check reads them as browsers do,
    /// so it reports the `<img onerror>` itself.
    #[test]
    fn an_open_form_or_a_closed_formatting_element_does_not_hide_a_script() {
        const IMG: &str = "<img src=x onerror=\"document.title=1\">";
        let cdata = format!("<![CDATA[><!-- ]]>{IMG}<!-- -->");
        for page in [
            format!("<math><mtext><form></form>{cdata}"),
            format!("<svg><desc><p><b></p></desc><style>{IMG}</style>"),
        ] {
            assert!(
                javascript_rules(&page).contains(&"js-native-handler"),
                "{page}"
            );
        }
    }

    /// The same markup can build a different tree where the browser puts it, so
    /// the check also reads a page as markup inside another page's body (as
    /// an app's own `innerHTML` puts it there) in either mode, and inside a
    /// `<template>` as Chromium parses it for Vue. Each page here hides its
    /// script from a reading of the whole document and runs it in Chromium
    /// 156, Firefox 157, or both, when put into a body or a template.
    #[test]
    fn a_script_hidden_only_in_a_whole_document_is_reported() {
        const IMG: &str = "<img src=x onerror=\"document.title=1\">";
        for page in [
            // A `<frameset>` builds nothing inside a body, so the
            // `<textarea>` holds only the comment start.
            format!("<frameset><textarea><!-- </textarea>{IMG}<!-- -->"),
            format!("<FRAMESET><noframes></noframes><textarea><!-- </textarea>{IMG}<!-- -->"),
            // Without a doctype a document is in quirks mode, where the
            // `<table>` leaves the `<p>` open; a host page in standards mode
            // closes it.
            format!("<span><p><table></table><svg><g></span><style><!--</style>{IMG}<!-- -->"),
            // With a doctype it is the other way round, for a host page in
            // quirks mode.
            format!("<!DOCTYPE html><span><p><table></table><svg><g></span><style><!--</style>{IMG}<!-- -->"),
            // Chromium parses `template.innerHTML`, which Vue uses for an
            // opaque HTML block, with scripting off, so `<noscript>` holds
            // real elements there.
            format!("<noscript>{IMG}</noscript>"),
            format!("<NOSCRIPT><p title=\"</noscript>\">{IMG}</NOSCRIPT>"),
        ] {
            assert!(
                javascript_rules(&page).contains(&"js-native-handler"),
                "{page}"
            );
        }
        // Ordinary pages with the same tags get no finding.
        for page in [
            "<!DOCTYPE html><html><head><title>t</title></head><body><p>Text<table><tr><td>1</td></tr></table></body></html>",
            "<p>Text<table><tr><td>1</td></tr></table>",
            "<frameset><frame src=a></frameset>",
            "<html><head></head><body><p>x</p></body></html>",
            "<noscript><p>Turn on JavaScript.</p><img src=pixel.gif alt=\"\"></noscript>",
        ] {
            assert_eq!(javascript_rules(page), Vec::<&str>::new(), "{page}");
        }
    }

    /// Only a `<noscript>` whose contents may hold a `<` asks for the reading
    /// that reads `<noscript>` contents as markup.
    #[test]
    fn only_a_noscript_that_may_hold_a_tag_asks_for_its_reading() {
        for html in [
            "<noscript><img src=pixel.gif></noscript>",
            "<NOSCRIPT>a <b>b</b></NOSCRIPT>",
            "<noscript>a</noscriptx><img></noscript>",
            "<noscript>a<b>",
            "<noscript title='<'>a</noscript>",
            "<p>x</p><noscript>Turn it on</noscript><noscript>a<i>b</i></noscript>",
        ] {
            assert!(noscript_may_hold_markup(html), "{html}");
        }
        for html in [
            "<p>noscript</p>",
            "<noscript>Turn on JavaScript.</noscript><p>x</p>",
            "<noscript>a &amp; b</noscript >",
            "<noscript>a</NOSCRIPT/>",
        ] {
            assert!(!noscript_may_hold_markup(html), "{html}");
        }
    }

    /// Every reading of a page spends from one budget, so a page that
    /// holds every kind of markup that calls for another reading cannot
    /// make the check read a deep page dozens of times. The same deep page
    /// needs one reading and passes.
    #[test]
    fn a_page_that_needs_every_reading_while_deep_is_refused() {
        let deep: String = (0..450).map(|index| format!("<b id={index}>")).collect();
        let triggers = "<select></select><!-- <frameset <noscript --><svg><title></p></title></svg><p><table></table><tr>";
        let body = "<img>".repeat(6_000);
        let check = |html: &str| {
            let trusted = HashSet::new();
            check_output_html(
                html,
                &OutputPolicyOptions {
                    pass: PolicyPass::Settled,
                    csp: false,
                    javascript: Some(JavascriptMode::Forbid),
                    marker_prefix: None,
                    trusted_tag_starts: &trusted,
                    omit_handler_marker: None,
                },
            )
        };
        assert_eq!(
            check(&format!("{triggers}{deep}{body}")).map(|report| report.events.len()),
            Err(HtmlTooLarge::CheckWork)
        );
        assert!(check(&format!("{deep}{body}")).is_ok());
        // The security page quotes the start of this message, and the Python
        // test `test_a_page_over_the_work_budget_gets_the_message_the_security_docs_quote`
        // pins it from the other side.
        assert!(HtmlTooLarge::CheckWork
            .to_string()
            .starts_with("HTML would take too long to check"));
    }

    /// Chromium 156 picks the mode of an `<iframe srcdoc>` document from its
    /// doctype, with no doctype meaning quirks mode, and Firefox 157 always
    /// reads it in standards mode, so the check reads it both ways. Each of
    /// these ran its script in one of the two browsers.
    #[test]
    fn a_srcdoc_document_is_read_in_both_modes() {
        let quirks_only = "<span><p><table></table><svg><g></span><![CDATA[><!-- ]]><img src=x onerror=\"parent.document.title=1\"><!-- -->";
        let standards_only = "<span><p><table></table><svg><g></span><style><!--</style><img src=x onerror=\"parent.document.title=1\"><!-- -->";
        for document in [
            // Chromium: no doctype, or an odd one, so quirks mode.
            quirks_only.to_owned(),
            format!("<!DOCTYPE foo>{quirks_only}"),
            // Firefox: standards mode whatever the doctype.
            standards_only.to_owned(),
            format!("<!DOCTYPE foo>{standards_only}"),
            format!("<!DOCTYPE>{standards_only}"),
            format!("<!DOCTYPE html PUBLIC \"-//IETF//DTD HTML//EN\">{standards_only}"),
        ] {
            let attribute = document.replace('&', "&amp;").replace('"', "&quot;");
            assert!(
                embedded_document_reported(&format!("<iframe srcdoc=\"{attribute}\"></iframe>")),
                "{document}"
            );
        }
        assert!(!embedded_document_reported(
            "<iframe srcdoc=\"&lt;p&gt;Text&lt;table&gt;&lt;tr&gt;&lt;td&gt;1&lt;/table&gt;\"></iframe>"
        ));
        // With `<!DOCTYPE html>` both browsers use standards mode, where the
        // `<table>` closes the `<p>` and the CDATA section hides the image.
        let standards = format!("<!DOCTYPE html>{quirks_only}")
            .replace('&', "&amp;")
            .replace('"', "&quot;");
        assert!(!embedded_document_reported(&format!(
            "<iframe srcdoc=\"{standards}\"></iframe>"
        )));
    }

    #[test]
    fn a_srcdoc_whose_tags_depend_on_the_encoding_counts_as_running() {
        assert!(embedded_document_reported(
            "<iframe srcdoc=\"&lt;svg&gt;&lt;![CDATA[\u{3041}]]&gt;&lt;/svg&gt;\"></iframe>"
        ));
        assert!(!embedded_document_reported(
            "<iframe srcdoc=\"&lt;svg&gt;&lt;![CDATA[a]]&gt;&lt;/svg&gt;\"></iframe>"
        ));
    }

    #[test]
    fn the_encoding_rule_belongs_to_the_javascript_policy_on_the_settled_page() {
        let html = "<p title='\u{1b}$B'>x</p>";
        for (pass, javascript) in [
            (PolicyPass::PreExtension, Some(JavascriptMode::Forbid)),
            (PolicyPass::Settled, None),
        ] {
            let report = check(html, pass, true, javascript, None, &[], None);
            assert!(report.events.is_empty(), "{pass:?} {javascript:?}");
        }
    }

    #[test]
    fn a_data_document_that_is_not_plain_ascii_counts_as_running() {
        // U+3000 in Shift_JIS, Big5, GBK, and EUC-JP, and U+2028 in GB18030.
        // Chromium 156 decoded the Shift_JIS and Big5 spellings, skipped the
        // U+3000, and opened the URL, when the document named its encoding
        // by a `charset` parameter or a `<meta charset>`.
        for (charset, space) in [
            ("shift_jis", "%81%40"),
            ("big5", "%A1%40"),
            ("gbk", "%A1%A1"),
            ("euc-jp", "%A1%A1"),
            ("gb18030", "%816%A65"),
        ] {
            let target = "data:text/xml,x";
            for content in [
                format!("{space}0;url={target}"),
                format!("0{space};url={target}"),
                format!("0;url={space}{target}"),
                format!("0;url='{space}{target}'"),
                format!("0;{space}{target}"),
            ] {
                let document = format!("%3Cmeta http-equiv=refresh content=%22{content}%22%3E");
                for html in [
                    format!("<iframe src=\"data:text/html;charset={charset},{document}\"></iframe>"),
                    format!("<iframe src=\"data:text/html,%3Cmeta charset={charset}%3E{document}\"></iframe>"),
                ] {
                    assert!(embedded_document_reported(&html), "{html:?}");
                }
            }
        }
        for html in [
            // Base64 reaches the same rule. This is `<p>\x81@</p>`.
            "<iframe src=\"data:text/html;base64,PHA+gUA8L3A+\"></iframe>",
            // Text that is valid UTF-8 can still be read in another encoding.
            "<iframe src=\"data:text/html,%3Cp%3E%C3%A9%3C/p%3E\"></iframe>",
            "<iframe src=\"data:text/html,<p>\u{e9}</p>\"></iframe>",
            // ISO-2022-JP reads these two bytes as U+FFFD.
            "<iframe src=\"data:text/html,%3Cp%3E%0E%3C/p%3E\"></iframe>",
            "<iframe src=\"data:text/html,%3Cp%3E%0F%3C/p%3E\"></iframe>",
        ] {
            assert!(embedded_document_reported(html), "{html:?}");
        }
        // Non-ASCII text written as a reference stays ASCII, so it is read.
        assert!(!embedded_document_reported(
            "<iframe src=\"data:text/html,%3Cp%3E%26%23233;%3C/p%3E\"></iframe>"
        ));
    }

    #[test]
    fn a_refresh_with_a_character_a_browser_may_skip_is_reported() {
        let url = "data:text/html,%3Cscript%3Ex()%3C/script%3E";
        for space in CHROMIUM_TYPE_SPACES {
            // Chromium 156 skipped each of these around the delay and before
            // the URL, quoted or not. The last two are gaps only the check
            // reads past.
            for content in [
                format!("{space}0;url={url}"),
                format!("0{space};url={url}"),
                format!("0;url={space}{url}"),
                format!("0;url='{space}{url}'"),
                format!("0;{space}url={url}"),
                format!("0;url{space}={url}"),
            ] {
                assert!(refresh_data_url(&content).is_some(), "{content:?}");
                for html in [
                    format!("<meta http-equiv=refresh content=\"{content}\">"),
                    format!(
                        "<iframe srcdoc=\"&lt;meta http-equiv=refresh content=&quot;{content}&quot;&gt;\"></iframe>"
                    ),
                ] {
                    assert!(embedded_document_reported(&html), "{html:?}");
                }
            }
        }
        // A reference in an embedded document decodes to the same character.
        assert!(embedded_document_reported(
            "<iframe srcdoc=\"&lt;meta http-equiv=refresh content='0&amp;#x3000;;url=data:text/xml,x'&gt;\"></iframe>"
        ));
        // A refresh to a URL that runs nothing is still not reported.
        assert!(!embedded_document_reported(
            "<meta http-equiv=refresh content=\"0\u{3000};url=data:image/png,x\">"
        ));
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
                // The `<a>` sits inside the `<p>`, so it carries the `<p>`'s
                // component id after its own (it has none).
                finding(
                    Rule::CspJavascriptUrl,
                    "a",
                    Some("href"),
                    (51, 68),
                    42,
                    &["q"]
                ),
                finding(
                    Rule::JsJavascriptUrl,
                    "a",
                    Some("href"),
                    (51, 68),
                    42,
                    &["q"]
                ),
                finding(
                    Rule::CspJavascriptUrl,
                    "a",
                    Some("href"),
                    (75, 87),
                    42,
                    &["q"]
                ),
                finding(
                    Rule::JsJavascriptUrl,
                    "a",
                    Some("href"),
                    (75, 87),
                    42,
                    &["q"]
                ),
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

    /// Whether the check reports an embedded document in `html`.
    fn embedded_document_reported(html: &str) -> bool {
        let report = check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Forbid),
            None,
            &[],
            None,
        );
        report.events.iter().any(|event| {
            matches!(event, PolicyEvent::Finding(finding) if finding.rule == Rule::JsEmbeddedDocument)
        })
    }

    #[test]
    fn embedded_documents_are_read_like_the_browser_would_load_them() {
        let html = concat!(
            // An inert nested document.
            "<iframe srcdoc=\"&lt;iframe srcdoc=&quot;&amp;lt;b&amp;gt;&quot;&gt;\"></iframe>",
            // Padding after a complete group is not valid base64.
            "<iframe src=\"data:text/html;base64,PHA+aGk8L3A+=\"></iframe>",
            // ASCII text that holds no script.
            "<object data='data:text/html,%3Cp%3Ehi%3C/p%3E'></object>",
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
                    (206, 249),
                    194,
                    &[]
                ),
            ]
        );
    }

    #[test]
    fn embedded_documents_with_a_script_are_reported() {
        // A document with no script is not reported.
        assert!(!embedded_document_reported(
            "<iframe srcdoc=\"&lt;p&gt;hi&lt;/p&gt;\"></iframe>"
        ));
        assert!(!embedded_document_reported(
            "<iframe src=\"data:text/html,%3Cp%3Ehi%3C/p%3E\"></iframe>"
        ));
        // A script in the document is reported, through srcdoc and a data URL.
        for html in [
            "<iframe srcdoc=\"&lt;script&gt;run()&lt;/script&gt;\"></iframe>",
            "<iframe src=\"data:text/html,%3Cscript%3Erun()%3C/script%3E\"></iframe>",
            "<object data=\"data:text/html;base64,PHNjcmlwdD54PC9zY3JpcHQ+\"></object>",
            "<embed src=\"data:text/html,%3Cbody onload=x%3E\">",
        ] {
            assert!(embedded_document_reported(html), "{html}");
        }
    }

    #[test]
    fn a_data_url_of_a_type_other_than_html_or_an_inert_one_counts_as_running_code() {
        // The browser runs the scripts of an SVG, XHTML, or other XML
        // document, and Firefox reads some unknown types as HTML. The check
        // reads only HTML, so every such document is reported, even one
        // with no script in it.
        for html in [
            "<iframe src=\"data:image/svg+xml,%3Csvg/%3E\"></iframe>",
            "<object data=\"data:image/svg+xml,%3Csvg/%3E\"></object>",
            "<embed src=\"data:image/svg+xml,%3Csvg/%3E\">",
            "<frameset><frame src=\"data:image/svg+xml,%3Csvg/%3E\"></frameset>",
            "<iframe src=\"data:application/xhtml+xml,x\"></iframe>",
            "<iframe src=\"data:text/xml,x\"></iframe>",
            "<iframe src=\"data:application/xml,x\"></iframe>",
            "<iframe src=\"data:text/xsl,x\"></iframe>",
            "<iframe src=\"data:application/rss+xml,x\"></iframe>",
            "<iframe src=\"data:x/+xml,x\"></iframe>",
            "<iframe src=\"data:audio/x+xml,x\"></iframe>",
            "<iframe src=\"data:font/,x\"></iframe>",
            "<iframe src=\"data:/svg+xml,x\"></iframe>",
            "<iframe src=\"data:+xml,x\"></iframe>",
            "<iframe src=\"data:*/*,x\"></iframe>",
            "<iframe src=\"data:application/x-unknown-content-type,x\"></iframe>",
            "<iframe src=\"data:foo,x\"></iframe>",
            "<iframe src=\" DATA:Image/SVG+XML ;charset=utf-8,x\"></iframe>",
            "<iframe src=\"data:\timage/svg+xml\x0c;x,x\"></iframe>",
            // The browser drops tabs and line breaks anywhere in a URL.
            "<iframe src=\"da&#9;ta:image/svg+xml,x\"></iframe>",
            "<iframe src=\"data:image/svg+x&#10;ml,x\"></iframe>",
            "<iframe src=\"data:image/svg+xml;base64,!\"></iframe>",
            // The same URLs inside an `iframe srcdoc` document.
            "<iframe srcdoc=\"&lt;iframe src='data:image/svg+xml,x'&gt;\"></iframe>",
            "<iframe srcdoc=\"&lt;frame src='data:text/xml,x'&gt;\"></iframe>",
        ] {
            assert!(embedded_document_reported(html), "{html}");
        }
        // Text, images, media, fonts, and downloads run no script.
        for html in [
            "<iframe src=\"data:image/svg,x\"></iframe>",
            "<iframe src=\"data:image/svg+xmlx,x\"></iframe>",
            "<iframe src=\"data:IMAGE/PNG;x,%3Cscript%3Ex()%3C/script%3E\"></iframe>",
            "<iframe src=\"data:text/plain,%3Csvg onload=x%3E\"></iframe>",
            "<iframe src=\"data:,%3Cscript%3Ex()%3C/script%3E\"></iframe>",
            "<object data=\"data:application/pdf,x\"></object>",
            "<embed src=\"data:video/mp4,x\">",
            "<embed src=\"data:audio/mpeg,%3Cscript%3Ex()%3C/script%3E\">",
            "<iframe src=\"data:font/woff,%3Cscript%3Ex()%3C/script%3E\"></iframe>",
            "<iframe src=\"data:application/json;charset=utf-8,%3Cscript%3E\"></iframe>",
            // No comma, so the browser loads nothing.
            "<iframe src=\"data:image/svg+xml\"></iframe>",
            "<img src=\"data:image/svg+xml,%3Csvg onload=x%3E\">",
        ] {
            assert!(!embedded_document_reported(html), "{html}");
        }
    }

    #[test]
    fn a_link_form_or_refresh_that_opens_a_running_data_document_is_reported() {
        // A link or form opens a `data:` document in a frame, and a meta
        // refresh opens one in the page's own frame, so each counts like a
        // frame's URL.
        for html in [
            "<a href=\"data:text/html,%3Cscript%3Ex()%3C/script%3E\">x</a>",
            "<a target=f href=\"data:image/svg+xml,x\">x</a>",
            "<map><area href=\"data:image/svg+xml,x\"></map>",
            "<svg><a xlink:href=\"data:image/svg+xml,x\"></a></svg>",
            "<svg><a href=\"data:text/xml,x\"></a></svg>",
            "<form action=\"data:text/xml,x\"></form>",
            "<button formaction=\"data:text/xml,x\">x</button>",
            "<input type=submit formaction=\"data:text/xml,x\">",
            // An SVG animation that sets a link's `href`.
            "<svg><a><set attributeName=href to=\"data:image/svg+xml,x\"></a></svg>",
            "<svg><a><animate attributeName=href values=\"#a;data:text/xml,x\"></a></svg>",
            // A meta refresh, with the spellings the browser accepts.
            "<meta http-equiv=\"refresh\" content=\"0;url=data:image/svg+xml,x\">",
            "<meta http-equiv=\" Refresh \" content=\"0; URL='data:text/html,%3Cscript%3Ex()%3C/script%3E'\">",
            "<meta http-equiv=refresh content=\"1,da&#9;ta:text/xml,x\">",
            "<meta http-equiv=refresh content=\"0;url=DATA:text/xml,x\">",
            "<meta http-equiv=refresh content=\" .5 ; url = &quot;data:text/xml,x\">",
            "<meta http-equiv=refresh content=\"0;&#1;data:text/xml,x\">",
            // Inside an embedded HTML document.
            "<iframe srcdoc=\"&lt;meta http-equiv=refresh content='0;url=data:text/xml,x'&gt;\"></iframe>",
            "<iframe srcdoc=\"&lt;a target=f href='data:text/xml,x'&gt;x&lt;/a&gt;\"></iframe>",
        ] {
            assert!(embedded_document_reported(html), "{html}");
        }
        for html in [
            "<a href=\"data:image/png,x\">x</a>",
            "<a href=\"data:text/html,%3Cp%3Ehi%3C/p%3E\">x</a>",
            "<a href=\"/data:text/xml,x\">x</a>",
            "<form action=\"/submit\"></form>",
            // A stylesheet, an icon, or an SVG reference is not opened as a page.
            "<link rel=stylesheet href=\"data:text/css,x\">",
            "<link rel=icon href=\"data:image/svg+xml,x\">",
            "<svg><use href=\"data:image/svg+xml,x\"></use></svg>",
            "<div href=\"data:text/xml,x\"></div>",
            // Not a refresh, or a refresh to a URL that runs nothing.
            "<meta http-equiv=refresh content=\"0;url=/next\">",
            "<meta http-equiv=refresh content=\"0;url=https://example.com/?next=data:text/xml,x\">",
            "<meta http-equiv=refresh content=\"0;url=data:image/png,x\">",
            "<meta name=refresh content=\"0;url=data:text/xml,x\">",
            "<meta http-equiv=refreshx content=\"0;url=data:text/xml,x\">",
            "<svg><a><set attributeName=fill to=\"data:text/xml,x\"></a></svg>",
        ] {
            assert!(!embedded_document_reported(html), "{html}");
        }
    }

    #[test]
    fn an_html_data_url_is_read_as_the_browser_reads_it() {
        for html in [
            // Tabs and line breaks are dropped, also inside the payload.
            "<iframe src=\"data:text/ht&#9;ml,%3Cscript%3Ex()%3C/script%3E\"></iframe>",
            "<iframe src=\"data:text/html,&lt;scr&#9;ipt&gt;x()&lt;/script&gt;\"></iframe>",
            // `;` and spaces before `base64` still mark base64.
            "<iframe src=\"data:text/html; base64,PHNjcmlwdD54PC9zY3JpcHQ+\"></iframe>",
            "<iframe src=\"data:text/html;  BASE64 ,PHNjcmlwdD54PC9zY3JpcHQ+\"></iframe>",
            "<iframe src=\"data:text/html;&#9;base64,PHNjcmlwdD54PC9zY3JpcHQ+\"></iframe>",
            // An encoding that is not ASCII compatible, by charset or byte
            // order mark, or an ISO-2022-JP escape inside a tag name.
            "<iframe src=\"data:text/html;charset=utf-16le,%3C%00p%00%3E%00\"></iframe>",
            "<iframe src=\"data:text/html,%FF%FE%3C%00p%00%3E%00\"></iframe>",
            "<iframe src=\"data:text/html,%3Cscr%1B(Bipt%3Ex()%3C/script%3E\"></iframe>",
        ] {
            assert!(embedded_document_reported(html), "{html}");
        }
        for html in [
            "<iframe src=\"data:text/html;charset=utf-16le,%3Cp%3Ehi%3C/p%3E\"></iframe>",
            "<iframe src=\"data:text/html;base64,PHA+aGk8L3A+\"></iframe>",
            "<iframe src=\"data:text/html; base64,PHA+aGk8L3A+\"></iframe>",
        ] {
            assert!(!embedded_document_reported(html), "{html}");
        }
    }

    #[test]
    fn a_legacy_reference_followed_by_a_letter_stays_literal_in_a_document() {
        // The browser keeps `&lta` as typed, so the document is the text
        // `&lta` followed by a `<script>` element, and the check must report
        // it.
        for html in [
            "<iframe srcdoc=\"&lta&lt;script&gt;run()&lt;/script&gt;\"></iframe>",
            "<iframe src=\"data:text/html,&lta%3Cscript%3Erun()%3C/script%3E\"></iframe>",
            "<object data=\"data:text/html,&lta%3Cscript%3Erun()%3C/script%3E\"></object>",
            "<embed src=\"data:text/html,&lta%3Cscript%3Erun()%3C/script%3E\">",
        ] {
            assert!(embedded_document_reported(html), "{html}");
        }
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
            let requires = attribute_document_requires_javascript(
                "iframe",
                "srcdoc",
                &decode_html_attribute(&document[16..document.len() - 11]),
                DocumentFacts::default(),
                0,
                &EmbeddedDocuments::default(),
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

    fn warn_findings(html: &str) -> Vec<(Rule, Vec<String>)> {
        check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Warn),
            None,
            &[],
            None,
        )
        .events
        .into_iter()
        .filter_map(|event| match event {
            PolicyEvent::Finding(finding) => Some((finding.rule, finding.cids)),
            PolicyEvent::RawElement(_) => None,
        })
        .collect()
    }

    fn handler_only_controls(html: &str) -> Vec<String> {
        check(
            html,
            PolicyPass::Settled,
            false,
            Some(JavascriptMode::Omit),
            None,
            &[],
            None,
        )
        .events
        .into_iter()
        .filter_map(|event| match event {
            PolicyEvent::Finding(finding) if finding.rule == Rule::JsHandlerOnlyControl => {
                Some(finding.tag)
            }
            _ => None,
        })
        .collect()
    }

    #[test]
    fn a_finding_carries_the_component_ids_of_the_elements_the_browser_put_around_it() {
        let cases: [(&str, &[&str]); 10] = [
            // Nested components: the innermost one comes first.
            (
                "<div data-cid-outer><section data-cid-inner><a onclick=x>a</a></section></div>",
                &["inner", "outer"],
            ),
            // An element inside `<svg>` keeps the HTML elements around it.
            ("<div data-cid-x><svg><a onclick=x></a></svg></div>", &["x"]),
            // Inside `<svg>` the parser spells some names with capitals.
            (
                "<div data-cid-x><svg><foreignObject onclick=x></foreignObject></svg></div>",
                &["x"],
            ),
            // The parser keeps a template's children apart from the page,
            // but they still belong to the component around the template.
            (
                "<div data-cid-x><template><a onclick=x>a</a></template></div>",
                &["x"],
            ),
            (
                "<div data-cid-x><template data-cid-t><template><a onclick=x>a</a></template></template></div>",
                &["t", "x"],
            ),
            // A `<div>` closes the open `<p>`, so the link is not inside it.
            ("<p data-cid-x>text<div><a onclick=x>a</a></div>", &[]),
            // A second `<li>` closes the first.
            ("<ul><li data-cid-x>a<li><a onclick=x>b</a></ul>", &[]),
            // A closed component does not own what follows it.
            ("<div data-cid-x></div><a onclick=x>after</a>", &[]),
            // The parser moves a link written inside a table out before it.
            (
                "<table data-cid-t><a onclick=x>x</a><tr><td>c</td></tr></table>",
                &[],
            ),
            // A misnested `</b>` leaves the link outside the `<b>`.
            ("<b data-cid-x><p>a</b><a onclick=x>b</a>", &[]),
        ];
        for (html, expected) in cases {
            let expected: Vec<String> = expected.iter().map(|cid| (*cid).to_owned()).collect();
            assert_eq!(
                warn_findings(html),
                [(Rule::JsNativeHandler, expected)],
                "{html}"
            );
        }
    }

    #[test]
    fn a_control_the_parser_puts_in_an_open_form_has_a_fallback() {
        // The form submits without JavaScript, so these are not reported.
        for html in [
            "<form action=/s><button @click=go>Save</button></form>",
            "<form><div><button @click=go>Save</button></div></form>",
            "<form><input @click=go name=q></form>",
            "<form><select @change=go></select><textarea @input=go></textarea></form>",
            // Inside a table, the form is closed at once but still owns the
            // controls the parser inserts until `</form>`.
            "<table><form><tr><td><button @click=go>Save</button></td></tr></form></table>",
            // A `form` attribute names the form that owns the button.
            "<form id=other></form><form><button form=other @click=go>x</button></form>",
            // `</form>` inside the `<div>` clears the parser's form pointer,
            // but the `<div>` stays in the form. The browser gives a control
            // that the parser did not tie to a form the nearest form that
            // contains it.
            "<form><div></form><button @click=go>x</button></div>",
            // The `</div>` closes the form element but leaves the parser's
            // form pointer set, so the pointer ties the button to the form
            // although the button lands after it.
            "<div><form></div><button @click=go>x</button>",
            // A form inside a template owns the controls inside it.
            "<template><form><button @click=go>x</button></form></template>",
            // Known limit: the `</b>` later moves the `<div>` out of the
            // form, which leaves the button without an owner in the
            // browser, but the check reads the owner when the parser
            // inserts the button.
            "<b><form><div></form><button @click=go>x</button></b>",
        ] {
            assert_eq!(handler_only_controls(html), Vec::<String>::new(), "{html}");
        }
        // These still have no fallback.
        for html in [
            "<button @click=go>Save</button>",
            // The form was closed before the button.
            "<form action=/s></form><button @click=go>Save</button>",
            // A `type=button` button never submits.
            "<form><button type=button @click=go>x</button></form>",
            // A template's contents are a separate document, so the form
            // around the template does not own the button.
            "<form><template><button @click=go>x</button></template></form>",
            // A `<button>` inside `<svg>` is an SVG element, not a control.
            "<form><svg><button @click=go>x</button></svg></form>",
        ] {
            assert_eq!(handler_only_controls(html), ["button"], "{html}");
        }
    }

    const EVENT: Option<CspAttributeProblem> = Some(CspAttributeProblem::NativeEvent);
    const URL: Option<CspAttributeProblem> = Some(CspAttributeProblem::JavascriptUrl);

    // Attributes an author might write, with the problem each one has. The
    // decode cases are where a separate reading of the value would most
    // likely differ from the page check: references, a tab inside the
    // scheme, and uppercase.
    const ATTRIBUTE_CASES: [(&str, &str, Option<&str>, Option<CspAttributeProblem>); 23] = [
        ("button", "onclick", Some("go()"), EVENT),
        ("button", "ONCLICK", Some("go()"), EVENT),
        ("button", "onclick", None, EVENT),
        // Any name longer than `on` that starts with it, so custom names too.
        ("div", "online", Some("yes"), EVENT),
        ("div", "on", Some("x"), None),
        ("div", "data-onclick", Some("x"), None),
        ("a", "href", Some("javascript:go()"), URL),
        ("a", "HREF", Some("JavaScript:go()"), URL),
        ("a", "href", Some("java&#115;cript:go()"), URL),
        ("a", "href", Some("java&#x09;script:go()"), URL),
        ("a", "href", Some("javascript&colon;go()"), URL),
        ("a", "href", Some(" \tjavascript:go()"), URL),
        ("form", "action", Some("javascript:go()"), URL),
        ("button", "formaction", Some("javascript:go()"), URL),
        ("img", "src", Some("javascript:go()"), URL),
        ("use", "xlink:href", Some("javascript:go()"), URL),
        ("object", "data", Some("javascript:go()"), URL),
        // The tag matters only here, so this checks it is read without case.
        ("OBJECT", "DATA", Some("javascript:go()"), URL),
        // `data` is a URL only on `<object>`.
        ("div", "data", Some("javascript:go()"), None),
        ("a", "title", Some("javascript:go()"), None),
        ("a", "href", Some("/javascript:go()"), None),
        ("a", "href", Some("https://example.com"), None),
        ("a", "href", None, None),
    ];

    #[test]
    fn literal_attributes_get_the_problem_the_rules_give() {
        for (tag, name, value, expected) in ATTRIBUTE_CASES {
            assert_eq!(
                csp_attribute_problem(tag, name, value),
                expected,
                "<{tag} {name}={value:?}>"
            );
        }
    }

    #[test]
    fn a_literal_attribute_gets_the_problem_the_page_check_reports() {
        // The static check and the render-time check must agree, so each
        // case is also written into a page and run through the page check.
        for (tag, name, value, _) in ATTRIBUTE_CASES {
            let html = match value {
                Some(value) => format!("<{tag} {name}=\"{value}\"></{tag}>"),
                None => format!("<{tag} {name}></{tag}>"),
            };
            let report = check(&html, PolicyPass::Settled, true, None, None, &[], None);
            let from_page: Vec<CspAttributeProblem> = report
                .events
                .iter()
                .filter_map(|event| match event {
                    PolicyEvent::Finding(Finding {
                        rule: Rule::CspNativeEvent,
                        ..
                    }) => Some(CspAttributeProblem::NativeEvent),
                    PolicyEvent::Finding(Finding {
                        rule: Rule::CspJavascriptUrl,
                        ..
                    }) => Some(CspAttributeProblem::JavascriptUrl),
                    _ => None,
                })
                .collect();
            let alone: Vec<CspAttributeProblem> = csp_attribute_problem(tag, name, value)
                .into_iter()
                .collect();
            assert_eq!(alone, from_page, "{html}");
        }
    }

    #[test]
    fn no_url_attribute_is_also_an_event_attribute() {
        // `csp_attribute_problem` reports one problem per attribute, which
        // is right only while no URL attribute name starts with `on`.
        for name in ["action", "formaction", "href", "src", "xlink:href", "data"] {
            assert!(is_url_attribute("object", name), "{name}");
            assert!(!is_native_event_attribute(name), "{name}");
        }
    }

    #[test]
    fn each_problem_has_the_name_python_uses() {
        assert_eq!(CspAttributeProblem::NativeEvent.code(), "native-event");
        assert_eq!(CspAttributeProblem::JavascriptUrl.code(), "javascript-url");
    }

    /// The attributes that carry a `javascript:` URL finding, in order, for
    /// each of the two rules that report one.
    fn url_findings(html: &str) -> (Vec<String>, Vec<String>) {
        let names = |csp: bool, javascript: Option<JavascriptMode>, rule: Rule| -> Vec<String> {
            check(html, PolicyPass::Settled, csp, javascript, None, &[], None)
                .events
                .into_iter()
                .filter_map(|event| match event {
                    PolicyEvent::Finding(finding) if finding.rule == rule => finding.attribute,
                    _ => None,
                })
                .collect()
        };
        (
            names(true, None, Rule::CspJavascriptUrl),
            names(false, Some(JavascriptMode::Warn), Rule::JsJavascriptUrl),
        )
    }

    #[test]
    fn an_animation_that_sets_href_to_a_javascript_url_is_reported_like_href() {
        // (page, the attribute that holds the URL)
        let reported: [(&str, &[&str]); 16] = [
            (
                "<svg><a><animate attributeName=href values='javascript:x' dur=1s></a></svg>",
                &["values"],
            ),
            (
                "<svg><a><animate attributeName=href to='javascript:x' dur=1s></a></svg>",
                &["to"],
            ),
            (
                "<svg><a><animate attributeName=href from='javascript:x' to='#a'></a></svg>",
                &["from"],
            ),
            (
                "<svg><a><animate attributeName=href by='javascript:x'></a></svg>",
                &["by"],
            ),
            (
                "<svg><a><set attributeName=href to='javascript:x'></a></svg>",
                &["to"],
            ),
            (
                "<svg><a><set attributeName=xlink:href to='javascript:x'></a></svg>",
                &["to"],
            ),
            // The animation may name its target with its own `href`, which
            // is not the value that is set.
            (
                "<svg><a id=a></a><set href='#a' attributeName=href to='javascript:x'></svg>",
                &["to"],
            ),
            // `values` is a list split on `;`, so each item is read alone.
            (
                "<svg><a><animate attributeName=href values='#a; #b ;javascript:x;#c'></a></svg>",
                &["values"],
            ),
            (
                "<svg><a><animate attributeName=href values='javascript:x;#b'></a></svg>",
                &["values"],
            ),
            // Character references in both the name and the value.
            (
                "<svg><a><set attributeName='hr&#101;f' to='java&#115;cript&colon;x'></a></svg>",
                &["to"],
            ),
            (
                "<svg><a><set attributeName=href to='java&#9;script:x'></a></svg>",
                &["to"],
            ),
            (
                "<svg><a><set attributeName=href to='  &#1;JavaScript:x'></a></svg>",
                &["to"],
            ),
            // Chromium and Firefox did not run these spellings, but the
            // check reports them in case another browser does.
            (
                "<svg><a><set attributeName=HREF to='javascript:x'></a></svg>",
                &["to"],
            ),
            (
                "<svg><a><set attributeName=' XLINK:Href\t' to='javascript:x'></a></svg>",
                &["to"],
            ),
            // Every value attribute that holds a URL is reported.
            (
                "<svg><a><set attributeName=href to='javascript:x' from='javascript:y'></a></svg>",
                &["to", "from"],
            ),
            // Uppercase tag and attribute names are read as the browser reads them
            // (the tokenizer lowercases attribute names).
            (
                "<SVG><A><SET ATTRIBUTENAME=href TO='javascript:x'></A></SVG>",
                &["to"],
            ),
        ];
        for (html, attributes) in reported {
            let (csp, javascript) = url_findings(html);
            assert_eq!(csp, attributes, "csp: {html}");
            assert_eq!(javascript, attributes, "javascript: {html}");
        }
    }

    #[test]
    fn an_animation_that_sets_no_javascript_url_is_not_reported() {
        for html in [
            "<svg><a><set attributeName=href to='#x'></a></svg>",
            "<svg><a><animate attributeName=href values='#a;#b'></a></svg>",
            // Only `href` and `xlink:href` set a link.
            "<svg><rect><set attributeName=fill to='javascript:x'></rect></svg>",
            "<svg><a><set attributeName=hrefx to='javascript:x'></a></svg>",
            "<svg><a><set attributeName=svg:href to='javascript:x'></a></svg>",
            "<svg><a><set to='javascript:x'></a></svg>",
            "<svg><a><set attributeName to='javascript:x'></a></svg>",
            // The browser keeps the first of two same-named attributes.
            "<svg><a><set attributeName=x attributeName=href to='javascript:x'></a></svg>",
            // Not a scheme: a control character inside it, a missing colon,
            // or text before it.
            "<svg><a><set attributeName=href to='java\u{1}script:x'></a></svg>",
            "<svg><a><set attributeName=href to='javascript'></a></svg>",
            "<svg><a><set attributeName=href to='/javascript:x'></a></svg>",
            // `animateTransform` does not set a link in the browsers tested.
            "<svg><rect><animateTransform attributeName=href to='javascript:x'></rect></svg>",
            "<div attributeName=href to='javascript:x'></div>",
            // An attribute that is not a value the animation sets.
            "<svg><a><set attributeName=href title='javascript:x' begin='javascript:x'></a></svg>",
            // A `;` is a list separator only in `values`.
            "<svg><a><set attributeName=href to='#a;javascript:x'></a></svg>",
        ] {
            assert_eq!(url_findings(html), (Vec::new(), Vec::new()), "{html}");
        }
    }

    #[test]
    fn an_animation_in_an_embedded_document_makes_it_run_code() {
        let document = "<svg><a><set attributeName=href to='javascript:x'></a></svg>";
        let documents = EmbeddedDocuments::default();
        assert!(html_document_requires_javascript(
            document,
            0,
            PageKind::DataUrl,
            &documents
        ));
        assert!(!html_document_requires_javascript(
            "<svg><a><set attributeName=href to='#x'></a></svg>",
            0,
            PageKind::DataUrl,
            &documents
        ));
        assert!(embedded_document_reported(&format!(
            "<iframe srcdoc=\"{}\"></iframe>",
            document
                .replace('\'', "&#39;")
                .replace('<', "&lt;")
                .replace('>', "&gt;")
        )));
    }
}
