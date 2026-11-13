//! Browser-state-aware facts for settled HTML security validation.

use std::borrow::Cow;
use std::cell::{Cell, RefCell};
use std::collections::hash_map::Entry;
use std::collections::{HashMap, HashSet};
use std::convert::Infallible;
use std::ops::Range;
use std::rc::Rc;

use html5ever::tendril::StrTendril;
use html5ever::tokenizer::states::RawKind;
use html5ever::tokenizer::{Doctype, Tag, TagKind, Token, TokenSink, TokenSinkResult};
use html5ever::tree_builder::create_element;
use html5ever::tree_builder::{
    ElementFlags, NodeOrText, QuirksMode, Tracer, TreeBuilder, TreeSink,
};
use html5ever::{
    local_name, namespace_url, ns, Attribute, ExpandedName, LocalName, Namespace, ParseOpts,
    QualName,
};
use html5gum::emitters::callback::{Callback, CallbackEmitter, CallbackEvent};
use html5gum::{Emitter, Error, ForwardingEmitter, Span, State};
use markup5ever_rcdom::{Handle, NodeData, RcDom};

use crate::html_limits::{is_formatting_element, CountHandles, HtmlLimits, HtmlTooLarge};
use crate::output_policy::decode_html_attribute;
use crate::tokenizer::run_tokenizer;

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

/// The tree-building rules that browsers differ on, which a page scan can
/// follow. The tags a page holds depend on them: when a tag is dropped, the
/// bytes after it are read as ordinary markup, and when it is kept, they can
/// be the text of a `<style>`. The output check cannot know the visitor's
/// browser, so it scans some pages more than once, each time under one set
/// of these rules (one reading of the page), and reports what any reading
/// finds. Where browsers build a tree that no reading builds, the scan notes
/// a [`ParserDifference`] instead.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub(crate) struct BrowserRules {
    /// Keep every tag inside `<select>`, as Chromium 156, Firefox 157 and the
    /// HTML standard do today. Otherwise most of those tags, such as
    /// `<style>` and `<svg>`, are dropped, which is html5ever 0.29.0's rule
    /// and the rule an older browser may still follow.
    pub(crate) keep_select_tags: bool,
    /// How end tags that browsers disagree on behave inside SVG and MathML.
    pub(crate) end_tags: EndTagRule,
    /// Where the browser puts the page's markup: a document of its own, the
    /// body of another page, or a `<template>`.
    pub(crate) placement: Placement,
    /// Which mode the browser builds the tree in: the one the doctype
    /// picks, standards mode, or quirks mode.
    pub(crate) mode: Mode,
    /// Read the contents of `<noscript>` as markup, as a parser does when
    /// scripting is off. Chromium 156 parses `template.innerHTML` that way,
    /// so the elements inside a `<noscript>` are real elements there, and
    /// they load and run once Vue moves the template's nodes into the page.
    /// Everywhere else the check reads `<noscript>` contents as text, as a
    /// page with scripting on does.
    pub(crate) noscript_as_markup: bool,
}

/// Where the browser puts the markup a scan reads.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub(crate) enum Placement {
    /// The markup is a whole document, as when the browser loads the page.
    #[default]
    Document,
    /// The markup is inserted into the `<body>` of a page that is already
    /// open, as an app's own script does when it sets `innerHTML` on an
    /// element there, for example to insert a Vue fragment response.
    /// (Citry's browser runtime, through Vue, builds HTML inside a
    /// `<template>` instead, see [`Placement::Template`]. Vue's `v-html` sets
    /// `innerHTML` too, and the JavaScript check already reports it as
    /// needing JavaScript.)
    /// In this placement a `<frameset>`, `<html>`, `<head>` or `<body>` tag
    /// builds nothing, and a doctype is ignored, so the host page decides
    /// the mode.
    /// This reading assumes the target is an ordinary HTML element such as a
    /// `<div>`. Setting `innerHTML` on an element with special parsing rules,
    /// such as an SVG or MathML element, a `<table>` or table part
    /// (`<tbody>`, `<tr>`, `<td>`), a `<select>` or a `<form>`, builds the
    /// tree by that element's own rules, and no reading follows that.
    /// (A `<template>` builds markup the way [`Placement::Template`] reads
    /// it, and the check adds that reading when it would build a different
    /// tree.)
    Body,
    /// The markup is the contents of a `<template>`, as Citry's browser
    /// runtime (through Vue) builds an opaque HTML block in the browser
    /// (`template.innerHTML`, then the template's nodes move into the page).
    /// Read the same way otherwise, it differs from [`Placement::Body`] only
    /// at a table part such as `<tr>` that a body ignores, because a template
    /// can start the table rules there.
    /// Chromium also reads `<noscript>` contents there as markup (see
    /// [`BrowserRules::noscript_as_markup`]).
    Template,
}

/// Which mode the browser builds the tree in. Quirks mode changes one step
/// of tree building: a `<table>` start tag leaves an open `<p>` open, where
/// standards mode closes it first.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, PartialEq)]
pub(crate) enum Mode {
    /// The doctype decides, as html5ever 0.29.0 decides it for a page the
    /// browser loads. Chromium 156 decides the mode of an `<iframe srcdoc>`
    /// document this way too.
    #[default]
    FromDoctype,
    /// Standards mode whatever the doctype, as Firefox 157 reads every
    /// `<iframe srcdoc>` document and as a host page in standards mode
    /// reads markup put into its body.
    Standards,
    /// Quirks mode whatever the doctype, as a host page in quirks mode
    /// reads markup put into its body.
    Quirks,
}

impl BrowserRules {
    /// The rules of the same browser with the other mode, for a page
    /// `serialize()` returns where the mode matters (see
    /// [`ScanResult::mode_matters`]), or `None` when such a reading of the
    /// page cannot happen. `quirks` is the mode the scan under these rules
    /// ended in.
    ///
    /// A page the browser loads takes its mode from its doctype, and the
    /// check follows html5ever there. The other mode is the one the same
    /// markup gets in the body of a page in the other mode. Markup put into
    /// another page can meet a host page in either mode, so each leads to
    /// the other. (`for_each_reading` picks the other reading of an
    /// `<iframe srcdoc>` document itself.)
    pub(crate) fn other_mode(self, quirks: bool) -> Option<BrowserRules> {
        let mode = match (self.placement, self.mode) {
            (Placement::Document, Mode::FromDoctype) => {
                return Some(BrowserRules {
                    placement: Placement::Body,
                    mode: if quirks {
                        Mode::Standards
                    } else {
                        Mode::Quirks
                    },
                    ..self
                });
            }
            (_, Mode::Standards) => Mode::Quirks,
            (_, Mode::Quirks) => Mode::Standards,
            // Markup put into another page never takes its mode from its own
            // doctype, so no such reading exists.
            (Placement::Body | Placement::Template, Mode::FromDoctype) => return None,
        };
        Some(BrowserRules { mode, ..self })
    }

    /// The options html5ever builds a tree under for these rules.
    fn tree_builder_options(self) -> html5ever::tree_builder::TreeBuilderOpts {
        html5ever::tree_builder::TreeBuilderOpts {
            // html5ever's `iframe_srcdoc` keeps a document without a doctype
            // in standards mode, which is what a forced standards mode needs
            // when the page is a document. A doctype that would still pick
            // quirks mode is replaced as it is fed (see `feed`).
            iframe_srcdoc: self.placement == Placement::Document && self.mode == Mode::Standards,
            scripting_enabled: !self.noscript_as_markup,
            ..ParseOpts::default().tree_builder
        }
    }
}

/// The rule a browser follows for two kinds of end tag inside SVG or MathML.
/// The HTML standard's rule is the default, and a browser differs on one kind.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub(crate) enum EndTagRule {
    /// A stray `</p>` or `</br>` stays in an element that holds HTML, such as
    /// an SVG `<title>`, and an end tag such as `</clippath>` closes the HTML
    /// element of that name around an `<svg>`.
    #[default]
    Standard,
    /// A stray `</p>` or `</br>` leaves SVG and MathML altogether, as Firefox
    /// 157 does.
    Firefox,
    /// Inside SVG, an end tag named like an SVG element with capitals, such
    /// as `</clippath>`, closes no HTML element. Chromium 156 gives the tag
    /// those capitals, and then compares letters exactly, so the tag also
    /// misses an SVG `<clipPath>` from inside MathML.
    Chromium,
}

/// The readings of `input` to start with, before a scan has seen it: `base`,
/// and the same with [`BrowserRules::keep_select_tags`] when the page holds
/// the text `<select` anywhere, in any case. Only a `<select>` start tag can
/// make that rule matter, so a page without the text needs a single scan.
pub(crate) fn browser_rules_for(input: &str, base: BrowserRules) -> Vec<BrowserRules> {
    const NEEDLE: &[u8] = b"<select";
    let holds_select = input
        .as_bytes()
        .windows(NEEDLE.len())
        .any(|window| window.eq_ignore_ascii_case(NEEDLE));
    let mut rules = vec![base];
    if holds_select {
        rules.push(BrowserRules {
            keep_select_tags: true,
            ..base
        });
    }
    rules
}

/// What one scan under [`BrowserRules`] read.
pub(crate) struct ScanResult {
    pub(crate) tags: Vec<OutputTag>,
    /// The page has an end tag that [`EndTagRule`] changes, so a browser
    /// other than the one this scan followed may read what comes after it
    /// differently. A real page has no such tag, so this keeps ordinary pages
    /// to the scans they need.
    pub(crate) end_tag_rule_matters: bool,
    /// A `<table>` start tag came while a `<p>` was open in button scope
    /// (open, with no element such as `<button>`, `<table>` or an SVG
    /// `<desc>` between it and the newest open element, which is when a
    /// `<table>` would close it), so the page builds a different tree in
    /// the other mode (see [`Mode`]).
    pub(crate) mode_matters: bool,
    /// The scan ended in quirks mode.
    pub(crate) quirks: bool,
    /// html5ever ignored a table part such as `<tr>` or `<td>` outside any
    /// table, which a `<template>` builds (see [`Placement::Template`]).
    pub(crate) template_matters: bool,
    /// The tags where browsers may build a different tree, in page order.
    pub(crate) differences: Vec<ParserDifference>,
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

/// The DOM every scan here builds. It remembers the element each start tag
/// made, so the output check can read where the browser put it, and counts
/// the formatting elements the parser makes, so the scan can stop at the
/// limit on reopened ones (see `html_limits`).
#[derive(Default)]
pub(crate) struct TrackingSink {
    dom: RcDom,
    // What `create_element` has made of formatting elements, whatever made
    // them (a start tag, or the parser reopening or copying one): one for
    // each element and one for each of its attributes, which a reopened
    // element copies.
    formatting_made: Cell<usize>,
    // The element the latest `create_element` made, cleared before each
    // start tag is processed.
    last_created: RefCell<Option<Handle>>,
    // Whether the parser tied that element to the form its form pointer
    // names.
    form_associated: Cell<bool>,
    // Whether this scan is the output check's, which alone departs from what
    // html5ever does.
    follows_browsers: bool,
    // How that scan changes what html5ever does.
    rules: BrowserRules,
    // The tag html5ever is working on, and the names `elem_name` gives.
    feeding: Cell<FedTag>,
    names: VisibleNames,
    // See `ScanResult::end_tag_rule_matters`.
    end_tag_rule_matters: Cell<bool>,
    // The page made an SVG or MathML element, so the extra work on its tags
    // is worth doing.
    made_foreign: Cell<bool>,
    // An SVG or MathML element may still be open. Making one sets this, and a
    // read of the open elements that finds none clears it, because only a
    // new element can join them. While it is clear, an end tag needs no read.
    foreign_maybe_open: Cell<bool>,
    // What `held_elements` last read, kept while html5ever holds the same.
    held: RefCell<Option<Rc<Held>>>,
    // How many elements `create_element` has made.
    elements_made: Cell<usize>,
    // How many handles html5ever reported after the last token it got, or
    // `None` while it works on a token.
    handle_count: Cell<Option<usize>>,
    // Where the tag html5ever is working on starts and ends in the input.
    tag_span: Cell<(usize, usize)>,
    // The tags where browsers may build a different tree from this scan's
    // (see `ParserDifference`).
    differences: RefCell<Vec<ParserDifference>>,
    // An HTML `search` element may still be open, kept like
    // `foreign_maybe_open`.
    search_maybe_open: Cell<bool>,
    // The page made a `<thead>`.
    made_thead: Cell<bool>,
    // The page's doctype is one for which html5ever picks standards mode and
    // a browser picks quirks mode (see `quirks_list_differs`).
    quirks_list_differs: Cell<bool>,
    // The mode html5ever is in: html5ever reports it through
    // `set_quirks_mode`.
    quirks: Cell<bool>,
    // See `ScanResult::mode_matters` and `ScanResult::template_matters`.
    mode_matters: Cell<bool>,
    template_matters: Cell<bool>,
    // How many formatting elements with the same name and attributes have
    // been made, by a hash of both. The standard keeps at most three equal
    // copies on the list of formatting elements, so it takes an open one off
    // the list only when a fourth is made.
    formatting_copies: RefCell<HashMap<u64, usize>>,
    // Some name and attributes reached four copies (see `read_held`).
    copy_rule_possible: Cell<bool>,
    // A table from each handle to where `split_reports` first saw it, and a
    // buffer for the reports `read_held` collects, kept between reads so
    // their memory is reused.
    first_seen: RefCell<HashMap<usize, usize, BuildPointerHasher>>,
    spare_reports: RefCell<Vec<Handle>>,
}

/// A tag where browsers may build a different tree from the one the scan
/// builds, so the output check cannot tell what the page runs and counts it
/// as running code.
///
/// The scan follows html5ever 0.29.0, which skips or changes some steps of the
/// HTML standard, and reads `<select>` with html5ever's `applet` rules. For
/// these cases the check does not try to build the browser's tree. It notes
/// the tag where the trees differ, which pages rarely need.
///
/// Two terms come up below. The list of formatting elements is the
/// standard's list of the `<b>`, `<i>`, `<a>` and similar elements a page
/// opened, which a browser opens again at the next tag or text after an end
/// tag closed them early. A special element is one that stops the search
/// an end tag makes for the element to close, such as `<div>` or `<td>`.
/// The cases:
///
/// - an `<annotation-xml>` start tag whose `encoding` is `text/html` or
///   `application/xhtml+xml`, which makes the element hold HTML in browsers;
/// - an `<svg>` or `<math>` start tag while a formatting element such as
///   `<b>` has closed but is still on the list, because browsers open it
///   again around the new element and html5ever does not;
/// - a `</select>` or `</form>` end tag while a MathML `<annotation-xml>` is
///   open, because browsers stop looking for the element to close at it;
/// - an `<isindex>` start tag, which html5ever counts as special and
///   browsers do not;
/// - an end tag, or a `<li>`, `<dd>` or `<dt>` start tag, whose search for
///   what to close passes an open `search` element, where Firefox stops;
/// - a formatting end tag such as `</b>` that the scan ignores at an SVG or
///   MathML element holding HTML, while that tag's element is on the list,
///   because browsers first drop a closed element from the list;
/// - under [`BrowserRules::keep_select_tags`]: a `<select>` start tag while
///   the list holds a closed element, a tag that closes the `select` while
///   the list holds an element made inside it, a formatting start tag inside
///   it while the list holds one made before it, and an `<option>`,
///   `<optgroup>` or `<hr>` that the standard lets close a `<dd>`, `<li>`,
///   `<p>` or the like;
/// - a `<caption>`, `<col>`, `<colgroup>`, `<tbody>`, `<tfoot>` or `<thead>`
///   start tag, or a `</table>`, while a `<thead>` is open with no table
///   around it;
/// - a `<table>` start tag while a `<p>` is open in button scope, on a page
///   whose doctype makes a browser use quirks mode where html5ever does not
///   (see `quirks_list_differs`; for the HTML 4.01 doctypes only Chromium
///   does), because only quirks mode leaves that `<p>` open.
///
/// It also notes an end tag when it cannot tell html5ever's open elements
/// from its list of formatting elements (see [`read_held`]).
#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ParserDifference {
    /// The tag's name as the tokenizer read it.
    pub(crate) tag: String,
    /// Which of the cases above the tag is, so the message can say what to
    /// change.
    pub(crate) kind: DifferenceKind,
    /// Byte span of the tag, from its `<` to just past its `>`.
    pub(crate) start: usize,
    pub(crate) end: usize,
}

/// The case a [`ParserDifference`] is, one for each fix a page author can
/// make. Python picks the message by [`DifferenceKind::code`].
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum DifferenceKind {
    /// An `<annotation-xml>` whose encoding makes it hold HTML.
    AnnotationXmlHoldsHtml,
    /// A `</select>` or `</form>` inside an open `<annotation-xml>`.
    EndTagInAnnotationXml,
    /// An `<svg>` or `<math>` start tag while a closed formatting element
    /// is still on the list.
    ReopenedFormatting,
    /// A formatting end tag such as `</b>` at an SVG or MathML element that
    /// holds HTML.
    FormattingEndTagInForeign,
    /// An end tag while an SVG or MathML element that holds HTML (such as
    /// `<desc>` or `<mi>`) or a `search` element is open, once the page has
    /// made four formatting elements with the same name and attributes. The
    /// check cannot then tell which formatting elements are still open (see
    /// [`read_held`]). A `<b>` start tag closes any other SVG or MathML
    /// element it is inside, so the case does not arise there on its own.
    /// The one other route, an `<svg>` start tag after a closed formatting
    /// element, is reported as [`DifferenceKind::ReopenedFormatting`], and
    /// end tags after it can report this case too.
    UnclearFormatting,
    /// An `<isindex>` start tag.
    Isindex,
    /// A tag whose search for what to close passes an open `search`.
    SearchElement,
    /// A formatting element open or reopened across the start or end of a
    /// `<select>`.
    FormattingAcrossSelect,
    /// An `<option>`, `<optgroup>` or `<hr>` inside a `<select>` that closes
    /// an element such as `<p>` or `<li>`.
    SelectClosesElement,
    /// A table part while a `<thead>` is open with no table around it.
    TheadOutsideTable,
    /// A `<table>` inside an open `<p>` on a page whose doctype makes a
    /// browser use quirks mode where html5ever does not.
    QuirksDoctypeTable,
}

impl DifferenceKind {
    /// The name Python uses to pick the message for this case.
    pub(crate) fn code(self) -> &'static str {
        match self {
            DifferenceKind::AnnotationXmlHoldsHtml => "annotation-xml-html",
            DifferenceKind::EndTagInAnnotationXml => "annotation-xml-end-tag",
            DifferenceKind::ReopenedFormatting => "reopened-formatting",
            DifferenceKind::FormattingEndTagInForeign => "formatting-end-tag-in-foreign",
            DifferenceKind::UnclearFormatting => "unclear-formatting",
            DifferenceKind::Isindex => "isindex",
            DifferenceKind::SearchElement => "search",
            DifferenceKind::FormattingAcrossSelect => "formatting-across-select",
            DifferenceKind::SelectClosesElement => "select-closes-element",
            DifferenceKind::TheadOutsideTable => "thead-outside-table",
            DifferenceKind::QuirksDoctypeTable => "quirks-doctype-table",
        }
    }
}

/// The names `elem_name` gives html5ever 0.29.0 in place of the real ones, which
/// is how a scan follows [`BrowserRules`] that html5ever does not have.
///
/// The standard's `<select>` now behaves in the tree builder like `<applet>`:
/// the start tag inserts an element in the current insertion mode, an end tag
/// closes it when it is in scope, and it ends the scope of `<p>`, `<div>` and
/// the other end tags. So under [`BrowserRules::keep_select_tags`] a `select`
/// tag reaches html5ever as an `applet` tag and takes html5ever's `applet`
/// rules. The element it makes is stored as `select`, and `elem_name` calls it
/// `applet` when html5ever asks. That keeps html5ever out of its own `select`
/// insertion modes, which it would also enter from `reset_insertion_mode` if
/// it saw the name.
///
/// A page can hold a real `<applet>` as well, so the two must not close each
/// other. `feeding` says which tag html5ever is working on, and `elem_name`
/// hides the other kind of element behind `marquee`, which has the same
/// rules and never matches this tag.
///
/// Under [`EndTagRule::Firefox`], html5ever already has the rule that leaves
/// SVG and MathML on `</p>`, but stops at an element that holds HTML. While it
/// works on such a tag, every foreign element is called `g`, which holds no
/// HTML, so it does not stop there.
///
/// Under [`EndTagRule::Chromium`], an element whose letters do not match the
/// tag exactly is called `g` while html5ever works on the tag.
///
/// In every reading, the HTML standard counts the SVG and MathML elements
/// that can hold HTML as special: they stop the search for what to close.
/// html5ever's list of special elements holds HTML names only. While it works
/// on a `<li>`, `<dd>` or `<dt>` start tag, which runs that search, such an
/// element is called `marquee`, which is special and ends the same scopes.
struct VisibleNames {
    html: Namespace,
    applet: LocalName,
    marquee: LocalName,
    g: LocalName,
}

impl Default for VisibleNames {
    fn default() -> Self {
        Self {
            html: ns!(html),
            applet: LocalName::from("applet"),
            marquee: LocalName::from("marquee"),
            g: LocalName::from("g"),
        }
    }
}

#[derive(Clone, Copy, Default, Eq, PartialEq)]
enum FedTag {
    /// A `select` tag, which html5ever sees as an `applet` tag.
    Select,
    /// A real `applet` tag.
    Applet,
    /// A `</p>` or `</br>` that leaves SVG and MathML entirely.
    LeavingForeignContent,
    /// An end tag Chromium compares exactly, with or without the capitals
    /// of an SVG name.
    ExactEndTag { capitals: bool },
    /// A `<li>`, `<dd>` or `<dt>` start tag.
    ListItem,
    #[default]
    Other,
}

impl VisibleNames {
    /// The name html5ever should see for an element with this name. In
    /// foreign content `</select>` must still close an SVG `<select>` and
    /// not an SVG `<applet>`, so those two names swap in any namespace. Away
    /// from a `select` tag, only the HTML element stands in for `applet`.
    fn visible_name(
        &self,
        rules: BrowserRules,
        feeding: FedTag,
        name: &ExpandedName<'_>,
        holds_html: bool,
    ) -> Option<&LocalName> {
        let html = *name.ns == ns!(html);
        match feeding {
            FedTag::LeavingForeignContent if !html => return Some(&self.g),
            FedTag::ExactEndTag { capitals } if !html => {
                let has_capitals = name.local.chars().any(|c| c.is_ascii_uppercase());
                return (has_capitals != capitals).then_some(&self.g);
            }
            FedTag::ListItem if holds_html => return Some(&self.marquee),
            _ => {}
        }
        if !rules.keep_select_tags {
            return None;
        }
        match (feeding, name.local.as_ref()) {
            (FedTag::Select, "select") => Some(&self.applet),
            (FedTag::Select, "applet") => Some(&self.marquee),
            (FedTag::Applet, "select") if html => Some(&self.marquee),
            (FedTag::Select | FedTag::Applet, _) => None,
            (_, "select") if html => Some(&self.applet),
            _ => None,
        }
    }
}

impl TrackingSink {
    /// A sink that builds into `dom`, which may already hold a context
    /// element for a fragment parse.
    fn new(dom: RcDom) -> Self {
        Self {
            dom,
            ..Self::default()
        }
    }

    /// The name `elem_name` gives while a rule changes names (see
    /// [`VisibleNames`]).
    #[inline(never)]
    fn renamed<'a>(&'a self, target: &'a Handle, name: ExpandedName<'a>) -> ExpandedName<'a> {
        let holds_html = self.feeding.get() == FedTag::ListItem
            && (self.dom.is_mathml_annotation_xml_integration_point(target)
                || (is_foreign_special(&name) && name.local.as_ref() != "annotation-xml"));
        let local = self
            .names
            .visible_name(self.rules, self.feeding.get(), &name, holds_html);
        match local {
            // The name stands for an HTML element, so the namespace must too.
            Some(local) if holds_html => ExpandedName {
                ns: &self.names.html,
                local,
            },
            Some(local) => ExpandedName { ns: name.ns, local },
            None => name,
        }
    }

    /// A sink for the output check's scan of a page under `rules`.
    fn for_rules(rules: BrowserRules) -> Self {
        Self {
            follows_browsers: true,
            rules,
            ..Self::default()
        }
    }
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

    #[inline]
    fn elem_name<'a>(&'a self, target: &'a Handle) -> ExpandedName<'a> {
        let name = self.dom.elem_name(target);
        // html5ever asks for names at every step of its searches, so the
        // common case, where at most an HTML `select` is renamed, returns at
        // once (the same answer as `visible_name`).
        if self.feeding.get() == FedTag::Other {
            if self.rules.keep_select_tags
                && *name.ns == ns!(html)
                && *name.local == local_name!("select")
            {
                return ExpandedName {
                    ns: name.ns,
                    local: &self.names.applet,
                };
            }
            return name;
        }
        self.renamed(target, name)
    }

    fn create_element(
        &self,
        mut name: QualName,
        attrs: Vec<Attribute>,
        flags: ElementFlags,
    ) -> Handle {
        // A `select` start tag reaches html5ever as `applet`, and this is
        // where the element gets its real name back.
        if self.feeding.get() == FedTag::Select && name.local.as_ref() == "applet" {
            name.local = LocalName::from("select");
        }
        if name.ns != ns!(html) {
            self.made_foreign.set(true);
            self.foreign_maybe_open.set(true);
        } else if name.local.as_ref() == "search" {
            self.search_maybe_open.set(true);
        } else if name.local.as_ref() == "thead" {
            self.made_thead.set(true);
        }
        self.elements_made.set(self.elements_made.get() + 1);
        let template = flags.template;
        // Counted by name in any namespace, so what a start tag's own element
        // adds matches what `HtmlLimits` counts for the tag, an SVG `<a>`
        // included.
        if is_formatting_element(name.local.as_bytes()) {
            self.formatting_made
                .set(self.formatting_made.get() + 1 + attrs.len());
            if name.ns == ns!(html) {
                self.count_copy(&name.local, &attrs);
            }
        }
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
        self.quirks.set(mode == QuirksMode::Quirks);
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
    // The size limits this run counts against (see `html_limits`).
    limits: &'a HtmlLimits,
}

trait ScannerSink: TokenSink<Handle = Handle> {
    /// Hand one token to the tree builder.
    fn feed(&self, token: Token) -> TokenSinkResult<Handle> {
        self.process_token(token, 1)
    }
    fn has_unacknowledged_self_closing(&self) -> bool;
    /// Count what the tree builder holds, and the formatting elements it has
    /// reopened, against the limits in `limits` (see `html_limits`).
    fn check_limits(&self, limits: &HtmlLimits);
    /// Forget the element the previous start tag made.
    fn begin_start_tag(&self) {}
    /// Where the browser put the element the start tag named `name` made,
    /// or an empty context when this scan does not track elements.
    fn tag_context(&self, _name: &str) -> TagContext {
        TagContext::default()
    }
    /// Remember where the next tag starts in the input, for a
    /// [`ParserDifference`] the output check notes at it.
    fn note_tag_start(&self, _start: usize) {}
    /// Remember where that tag ends.
    fn note_tag_end(&self, _end: usize) {}
}

fn has_unacknowledged_self_closing(dom: &RcDom) -> bool {
    // html5ever 0.29.0's TreeBuilder emits this exact diagnostic after it
    // processes a self-closing flag in the element's actual namespace.
    // The regression tests below deliberately pin that dependency contract.
    dom.errors
        .borrow()
        .iter()
        .any(|error| error.as_ref() == "Unacknowledged self-closing tag")
}

impl ScannerSink for TreeBuilder<Handle, TrackingSink> {
    fn feed(&self, token: Token) -> TokenSinkResult<Handle> {
        if !self.sink.follows_browsers {
            return self.process_token(token, 1);
        }
        let tag = match token {
            Token::TagToken(tag) => tag,
            Token::DoctypeToken(doctype) => return feed_doctype(self, doctype),
            token => return hand_over(self, token),
        };
        let is_start = tag.kind == TagKind::StartTag;
        let keep_select_tags = self.sink.rules.keep_select_tags;
        note_parser_difference(self, &tag);
        match tag.name.as_ref() {
            // The template this scan reads the page in is not the page's, so
            // a `</template>` must not close it. A real `template.innerHTML`
            // ignores this end tag, because its context element is not open.
            "template"
                if !is_start
                    && self.sink.rules.placement == Placement::Template
                    && open_templates(self) <= 1 =>
            {
                TokenSinkResult::Continue
            }
            "caption" | "col" | "colgroup" | "tbody" | "tfoot" | "thead" | "tr" | "td" | "th"
                if is_start
                    && self.sink.rules.placement != Placement::Template
                    && !self.sink.template_matters.get() =>
            {
                // In a body html5ever ignores a table part outside a table
                // and makes no element for it, while inside a `<template>`
                // the same tag can start the table rules. Only then can the
                // template reading differ (see `Placement::Template`). The
                // last element made tells: html5ever may make others first,
                // such as the `<tbody>` before a `<tr>`, or an implied
                // `<body>`.
                let name = tag.name.clone();
                let result = hand_over(self, Token::TagToken(tag));
                let made_its_element = self.sink.last_created.borrow().as_ref().is_some_and(
                    |element| matches!(&element.data, NodeData::Element { name: made, .. } if made.local == name),
                );
                if !made_its_element {
                    self.sink.template_matters.set(true);
                }
                result
            }
            "p" | "br" if !is_start => feed_stray_end_tag(self, tag),
            // The HTML standard has `</select>` close the `select` element
            // when it is in scope, and do nothing otherwise.
            "select" if keep_select_tags && !is_start => feed_as_select(self, tag),
            "select" if keep_select_tags => {
                // A second `<select>` closes the open one and makes no
                // element. Inside SVG or MathML this tag is a plain foreign
                // element, and at an element that holds HTML no `select` is
                // in scope, so neither closes anything.
                if !self.adjusted_current_node_present_but_not_in_html_namespace()
                    && close_select(self)
                {
                    return TokenSinkResult::Continue;
                }
                feed_as_select(self, tag)
            }
            "input" if keep_select_tags && is_start => {
                // `<input>` closes an open `select` too, unless a table's
                // own rules take it: they insert a hidden input where it
                // stands. html5ever logs a parse error for a hidden input
                // only in those rules, which is how this learns they ran.
                let in_foreign = self.adjusted_current_node_present_but_not_in_html_namespace();
                let hidden = tag.attrs.iter().any(|attr| {
                    attr.name.local.as_ref() == "type" && attr.value.eq_ignore_ascii_case("hidden")
                });
                let errors = self.sink.dom.errors.borrow().len();
                let result = hand_over(self, Token::TagToken(tag));
                let table_rule = hidden && self.sink.dom.errors.borrow().len() != errors;
                if !in_foreign && !table_rule {
                    close_select(self);
                }
                result
            }
            "applet" if keep_select_tags => {
                self.sink.feeding.set(FedTag::Applet);
                let result = hand_over(self, Token::TagToken(tag));
                self.sink.feeding.set(FedTag::Other);
                result
            }
            "li" | "dd" | "dt" if is_start && self.sink.made_foreign.get() => {
                self.sink.feeding.set(FedTag::ListItem);
                let result = hand_over(self, Token::TagToken(tag));
                self.sink.feeding.set(FedTag::Other);
                result
            }
            name if !is_start
                && (self.sink.foreign_maybe_open.get() || self.sink.search_maybe_open.get())
                && !closes_by_own_rule(name) =>
            {
                let result = if end_tag_is_ignored(self, name) {
                    TokenSinkResult::Continue
                } else {
                    hand_over(self, Token::TagToken(tag))
                };
                self.sink.feeding.set(FedTag::Other);
                result
            }
            _ => hand_over(self, Token::TagToken(tag)),
        }
    }

    fn has_unacknowledged_self_closing(&self) -> bool {
        has_unacknowledged_self_closing(&self.sink.dom)
    }

    fn check_limits(&self, limits: &HtmlLimits) {
        let count = limits.after_token(self.sink.formatting_made.get(), |tracer| {
            self.trace_handles(tracer);
        });
        self.sink.handle_count.set(count);
    }

    fn begin_start_tag(&self) {
        *self.sink.last_created.borrow_mut() = None;
        self.sink.form_associated.set(false);
    }

    fn note_tag_start(&self, start: usize) {
        self.sink.tag_span.set((start, start));
    }

    fn note_tag_end(&self, end: usize) {
        let (start, _) = self.sink.tag_span.get();
        self.sink.tag_span.set((start, end));
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

/// Hand a `</p>` or `</br>` to html5ever, and note when browsers can read
/// what follows differently (see [`ScanResult::end_tag_rule_matters`]).
fn feed_stray_end_tag(
    builder: &TreeBuilder<Handle, TrackingSink>,
    tag: Tag,
) -> TokenSinkResult<Handle> {
    let sink = &builder.sink;
    let in_foreign = builder.adjusted_current_node_present_but_not_in_html_namespace();
    if !in_foreign {
        return hand_over(builder, Token::TagToken(tag));
    }
    if sink.rules.end_tags == EndTagRule::Firefox {
        sink.feeding.set(FedTag::LeavingForeignContent);
    }
    let result = hand_over(builder, Token::TagToken(tag));
    sink.feeding.set(FedTag::Other);
    // Outside an element that holds HTML, html5ever leaves foreign content
    // here as every browser does, so only staying in it can differ.
    if builder.adjusted_current_node_present_but_not_in_html_namespace() {
        sink.end_tag_rule_matters.set(true);
    }
    result
}

/// A doctype that picks the scan's mode: `<!DOCTYPE html>` for standards
/// mode, or one marked to force quirks mode.
fn doctype_for(quirks: bool) -> Doctype {
    Doctype {
        name: Some(StrTendril::from_slice("html")),
        force_quirks: quirks,
        ..Doctype::default()
    }
}

/// Hand a doctype to html5ever under the scan's [`Mode`].
fn feed_doctype(
    builder: &TreeBuilder<Handle, TrackingSink>,
    doctype: Doctype,
) -> TokenSinkResult<Handle> {
    let sink = &builder.sink;
    let rules = sink.rules;
    // In a body or a template html5ever ignores a doctype, as browsers do,
    // so the host page's mode stands.
    if rules.placement != Placement::Document {
        return hand_over(builder, Token::DoctypeToken(doctype));
    }
    match rules.mode {
        Mode::FromDoctype => {
            // Only a doctype that comes before every element sets the mode;
            // html5ever ignores a later one.
            let sets_mode = sink.elements_made.get() == 0;
            let differs = sets_mode && quirks_list_differs(&doctype);
            let result = hand_over(builder, Token::DoctypeToken(doctype));
            // When html5ever picks quirks mode for it too, nothing differs.
            if differs && !sink.quirks.get() {
                sink.quirks_list_differs.set(true);
            }
            result
        }
        // The scan reads the page in one mode whatever its doctype says, so
        // the doctype is replaced with one that picks that mode.
        Mode::Standards => hand_over(builder, Token::DoctypeToken(doctype_for(false))),
        Mode::Quirks => hand_over(builder, Token::DoctypeToken(doctype_for(true))),
    }
}

/// Whether a browser picks quirks mode for this doctype where html5ever
/// 0.29.0 picks standards or limited-quirks mode. A matrix of every
/// identifier on html5ever's and the standard's lists, run in Chromium 156
/// and Firefox 157, found two such cases. Both browsers pick quirks mode for
/// a public identifier that starts with the Silmaril one, which html5ever's
/// list lacks. Chromium picks it for an HTML 4.01 Frameset or Transitional
/// public identifier with an empty system identifier, which html5ever counts
/// as present. Browsers compare identifiers without regard to ASCII case.
fn quirks_list_differs(doctype: &Doctype) -> bool {
    let Some(public) = doctype.public_id.as_deref() else {
        return false;
    };
    let starts_with = |prefix: &str| {
        public
            .as_bytes()
            .get(..prefix.len())
            .is_some_and(|start| start.eq_ignore_ascii_case(prefix.as_bytes()))
    };
    starts_with("+//silmaril//dtd html pro v0r11 19970101//")
        || ((starts_with("-//w3c//dtd html 4.01 frameset//")
            || starts_with("-//w3c//dtd html 4.01 transitional//"))
            && doctype.system_id.as_deref() == Some(""))
}

/// How many HTML `template` elements are open.
fn open_templates(builder: &TreeBuilder<Handle, TrackingSink>) -> usize {
    held_elements(builder)
        .open()
        .iter()
        .filter(|node| html_element_named(node, "template"))
        .count()
}

/// Whether a `<p>` is open in button scope, which is when a `<table>` start
/// tag closes it in standards mode and leaves it open in quirks mode. The
/// search from the newest open element stops at the elements that end
/// button scope. A `select` does not stop it here, although a scan that
/// keeps `<select>` contents reads it as an `applet`, which does; that can
/// only find a `<p>` more often.
fn p_in_button_scope(open: &[Handle]) -> bool {
    for node in open.iter().rev() {
        let NodeData::Element { name, .. } = &node.data else {
            continue;
        };
        if is_foreign_special(&name.expanded()) {
            return false;
        }
        if name.ns != ns!(html) {
            continue;
        }
        match name.local.as_ref() {
            "p" => return true,
            "applet" | "button" | "caption" | "html" | "marquee" | "object" | "table" | "td"
            | "template" | "th" => return false,
            _ => {}
        }
    }
    false
}

/// Start html5ever's tree builder for a scan under `rules`. For markup that
/// goes into another page (see [`Placement`]), html5ever first gets the tags
/// of an empty host page in the scan's mode, so the page's own tags arrive
/// inside its `<body>`, or inside a `<template>` there.
///
/// This reads the markup the way the browser's fragment parser does with a
/// `body` or `template` context element. An explicit `<body>` start tag
/// tells html5ever that a later `<frameset>` builds nothing, as in a
/// fragment, and the page's own doctype, `<html>`, `<head>` and `<body>` tags
/// arrive inside the body, where they build nothing either. html5ever keeps
/// its head pointer, which [`read_held`] relies on.
fn tree_builder_for(rules: BrowserRules) -> TreeBuilder<Handle, TrackingSink> {
    let builder = TreeBuilder::new(TrackingSink::for_rules(rules), rules.tree_builder_options());
    if rules.placement == Placement::Document {
        return builder;
    }
    let tag = |kind, name: &str| {
        Token::TagToken(Tag {
            kind,
            name: LocalName::from(name),
            self_closing: false,
            attrs: Vec::new(),
        })
    };
    // A host page without a doctype is in quirks mode.
    if rules.mode != Mode::Quirks {
        let _ = builder.process_token(Token::DoctypeToken(doctype_for(false)), 1);
    }
    let mut host = vec![
        tag(TagKind::StartTag, "html"),
        tag(TagKind::StartTag, "head"),
        tag(TagKind::EndTag, "head"),
        tag(TagKind::StartTag, "body"),
    ];
    if rules.placement == Placement::Template {
        host.push(tag(TagKind::StartTag, "template"));
    }
    for token in host {
        // None of these tags asks the tokenizer to change state.
        let _ = builder.process_token(token, 1);
    }
    builder
}

/// Whether an element is one the HTML standard counts as special although it
/// sits in SVG or MathML. These can hold HTML.
fn is_foreign_special(name: &ExpandedName<'_>) -> bool {
    match *name.ns {
        ns!(svg) => matches!(name.local.as_ref(), "foreignObject" | "desc" | "title"),
        ns!(mathml) => matches!(
            name.local.as_ref(),
            "mi" | "mo" | "mn" | "ms" | "mtext" | "annotation-xml"
        ),
        _ => false,
    }
}

/// Whether html5ever and the browsers handle this end tag without searching
/// for it through special elements, so [`end_tag_is_ignored`] does not apply.
fn closes_by_own_rule(name: &str) -> bool {
    matches!(
        name,
        "p" | "br"
            | "form"
            | "select"
            | "template"
            | "table"
            | "caption"
            | "col"
            | "colgroup"
            | "tbody"
            | "tfoot"
            | "thead"
            | "tr"
            | "td"
            | "th"
    )
}

/// Whether Chromium gives this lowercase SVG tag name capitals.
fn svg_name_has_capitals(name: &str) -> bool {
    matches!(
        name,
        "altglyph"
            | "altglyphdef"
            | "altglyphitem"
            | "animatecolor"
            | "animatemotion"
            | "animatetransform"
            | "clippath"
            | "feblend"
            | "fecolormatrix"
            | "fecomponenttransfer"
            | "fecomposite"
            | "feconvolvematrix"
            | "fediffuselighting"
            | "fedisplacementmap"
            | "fedistantlight"
            | "fedropshadow"
            | "feflood"
            | "fefunca"
            | "fefuncb"
            | "fefuncg"
            | "fefuncr"
            | "fegaussianblur"
            | "feimage"
            | "femerge"
            | "femergenode"
            | "femorphology"
            | "feoffset"
            | "fepointlight"
            | "fespecularlighting"
            | "fespotlight"
            | "fetile"
            | "feturbulence"
            | "foreignobject"
            | "glyphref"
            | "lineargradient"
            | "radialgradient"
            | "textpath"
    )
}

/// Hand a token to html5ever. Until the size limits count what it holds
/// afterwards, no earlier read of it (see [`held_elements`]) is reused.
fn hand_over(builder: &TreeBuilder<Handle, TrackingSink>, token: Token) -> TokenSinkResult<Handle> {
    builder.sink.handle_count.set(None);
    builder.process_token(token, 1)
}

impl TrackingSink {
    /// Count one more formatting element with this name and these
    /// attributes (see `formatting_copies`). The standard compares the
    /// attributes in any order, so their hashes are added up. Two different
    /// sets that collide only count more copies.
    fn count_copy(&self, local: &LocalName, attrs: &[Attribute]) {
        use std::hash::{DefaultHasher, Hash, Hasher};
        // Once the rule is possible, nothing more needs counting.
        if self.copy_rule_possible.get() {
            return;
        }
        let hash = |value: &dyn Fn(&mut DefaultHasher)| {
            let mut hasher = DefaultHasher::new();
            value(&mut hasher);
            hasher.finish()
        };
        let mut key = hash(&|hasher| local.hash(hasher));
        for attr in attrs {
            key = key.wrapping_add(hash(&|hasher| {
                attr.name.hash(hasher);
                attr.value.as_ref().hash(hasher);
            }));
        }
        let mut copies = self.formatting_copies.borrow_mut();
        let count = copies.entry(key).or_insert(0);
        *count += 1;
        if *count >= 4 {
            self.copy_rule_possible.set(true);
        }
    }

    /// Note the tag html5ever is about to get as a [`ParserDifference`].
    fn note_difference(&self, tag: &str, kind: DifferenceKind) {
        let (start, end) = self.tag_span.get();
        let mut differences = self.differences.borrow_mut();
        // Two rules can notice the same tag, which is reported once.
        if differences.last().is_some_and(|last| last.start == start) {
            return;
        }
        differences.push(ParserDifference {
            tag: tag.to_owned(),
            kind,
            start,
            end,
        });
    }
}

/// Note `tag` as a [`ParserDifference`] when it is one of the places where
/// html5ever 0.29.0, or the way this scan reads `<select>`, skips or adds a
/// step that browsers do not. Each check reads what html5ever holds only when
/// an earlier tag made the case possible, so an ordinary page skips the read.
fn note_parser_difference(builder: &TreeBuilder<Handle, TrackingSink>, tag: &Tag) {
    use DifferenceKind as Kind;
    let sink = &builder.sink;
    let keep_select_tags = sink.rules.keep_select_tags;
    let held = || held_elements(builder);
    let differs = match (tag.kind, tag.name.as_ref()) {
        (TagKind::StartTag, "annotation-xml") => {
            holds_html_encoding(tag).then_some(Kind::AnnotationXmlHoldsHtml)
        }
        // html5ever counts `<isindex>` as special, and browsers build an
        // ordinary element, so the search for what to close stops at it
        // only in the scan.
        (TagKind::StartTag, "isindex") => Some(Kind::Isindex),
        (TagKind::StartTag, "svg" | "math") => (sink.formatting_made.get() > 0
            && held().closed_formatting)
            .then_some(Kind::ReopenedFormatting),
        // A `<li>`, `<dd>` or `<dt>` closes the one before it unless the
        // search for it stops at a special element first, and Firefox counts
        // `search` as special while html5ever and Chromium do not.
        (TagKind::StartTag, name @ ("li" | "dd" | "dt")) if sink.search_maybe_open.get() => {
            list_item_search_passes_search(held().open(), name).then_some(Kind::SearchElement)
        }
        (TagKind::StartTag, "caption" | "col" | "colgroup" | "tbody" | "tfoot" | "thead")
        | (TagKind::EndTag, "table")
            if sink.made_thead.get() =>
        {
            thead_outside_table(held().open()).then_some(Kind::TheadOutsideTable)
        }
        // In quirks mode a `<table>` leaves an open `<p>` open, and in
        // standards mode it closes it. The scan follows one mode, so it
        // notes that the page needs a reading in the other one. For a few
        // doctypes html5ever picks a different mode from a browser (see
        // `quirks_list_differs`), and there the tag is refused. One such tag
        // settles both, so later ones are not looked at.
        (TagKind::StartTag, "table") if !sink.mode_matters.get() => {
            let in_p = p_in_button_scope(held().open());
            sink.mode_matters.set(sink.mode_matters.get() || in_p);
            (in_p && sink.quirks_list_differs.get()).then_some(Kind::QuirksDoctypeTable)
        }
        // The scan reads `<select>` as `<applet>`, which puts a marker on the
        // formatting list that the standard's `<select>` does not. Until it
        // closes, the marker keeps a closed formatting element from before
        // the `select` from being reopened, and hides the ones before it
        // from the count of copies a new `<a>` or a fourth `<b>` makes the
        // standard check (see `read_held`). Closing the `select` drops the
        // ones after the marker from the list.
        (TagKind::StartTag, "select") if keep_select_tags => {
            let held = held();
            (held.closed_formatting || listed_inside_select(&held).unwrap_or(false))
                .then_some(Kind::FormattingAcrossSelect)
        }
        (TagKind::EndTag, "select") | (TagKind::StartTag, "input") if keep_select_tags => {
            listed_inside_select(&held())
                .unwrap_or(false)
                .then_some(Kind::FormattingAcrossSelect)
        }
        (TagKind::StartTag, name) if keep_select_tags && is_formatting_element(name.as_bytes()) => {
            let held = held();
            innermost_select(held.open())
                .is_some_and(|select| held.listed().iter().any(|node| !is_inside(node, select)))
                .then_some(Kind::FormattingAcrossSelect)
        }
        // The standard closes `<dd>`, `<li>`, `<p>` and the like at an
        // `<option>`, `<optgroup>` or `<hr>` inside `select`. The scan's
        // `applet` rules close only an `<option>`.
        (TagKind::StartTag, name @ ("option" | "optgroup" | "hr")) if keep_select_tags => {
            let held = held();
            let open = held.open();
            (open.iter().any(|node| html_element_named(node, "select"))
                && select_closes_more(open, name))
            .then_some(Kind::SelectClosesElement)
        }
        _ => None,
    };
    if let Some(kind) = differs {
        sink.note_difference(tag.name.as_ref(), kind);
        return;
    }
    // A `</select>` or `</form>` closes the element only when no
    // `<annotation-xml>` stands in the way, which html5ever does not check.
    // This is checked apart from the `<select>` cases above, which the same
    // end tag can also meet.
    let crosses_annotation_xml = tag.kind == TagKind::EndTag
        && matches!(tag.name.as_ref(), "select" | "form")
        && sink.foreign_maybe_open.get()
        && held().open().iter().any(is_mathml_annotation_xml);
    if crosses_annotation_xml {
        sink.note_difference(tag.name.as_ref(), Kind::EndTagInAnnotationXml);
    }
}

/// The innermost open HTML `select` element.
fn innermost_select(open: &[Handle]) -> Option<&Handle> {
    open.iter()
        .rev()
        .find(|node| html_element_named(node, "select"))
}

/// Whether the node sits inside `ancestor` in the tree.
fn is_inside(node: &Handle, ancestor: &Handle) -> bool {
    let mut current = parent_of(node);
    while let Some(parent) = current {
        if Rc::ptr_eq(&parent, ancestor) {
            return true;
        }
        current = parent_of(&parent);
    }
    false
}

/// Whether the formatting list holds an element made inside the innermost
/// open `select`, or `None` when no `select` is open.
fn listed_inside_select(held: &Held) -> Option<bool> {
    let select = innermost_select(held.open())?;
    Some(held.listed().iter().any(|node| is_inside(node, select)))
}

fn html_element_named(node: &Handle, local: &str) -> bool {
    matches!(&node.data, NodeData::Element { name, .. }
        if name.ns == ns!(html) && name.local.as_ref() == local)
}

/// Whether the search a `<li>`, `<dd>` or `<dt>` start tag makes for the
/// item to close passes an open `search` element and then finds that item.
/// Firefox stops at the `search`, and html5ever closes the item.
fn list_item_search_passes_search(open: &[Handle], tag: &str) -> bool {
    let targets: &[&str] = if tag == "li" { &["li"] } else { &["dd", "dt"] };
    let mut passed_search = false;
    for node in open.iter().rev() {
        let NodeData::Element { name, .. } = &node.data else {
            continue;
        };
        if name.ns != ns!(html) {
            if is_foreign_special(&name.expanded()) {
                return false;
            }
            continue;
        }
        let local = name.local.as_ref();
        if targets.contains(&local) {
            return passed_search;
        }
        if local == "search" {
            passed_search = true;
        } else if is_html5ever_special(local) && !matches!(local, "address" | "div" | "p") {
            return false;
        }
    }
    false
}

/// Whether a `<thead>` is open with no `<table>`, `<tbody>` or `<tfoot>`
/// between it and the `<template>` or `<html>` it sits in. html5ever looks for
/// a `table`, `tbody` or `tfoot` there before it closes the table section,
/// where the standard looks for a `tbody`, `thead` or `tfoot`, so only the
/// standard closes such a `<thead>`.
fn thead_outside_table(open: &[Handle]) -> bool {
    let mut saw_thead = false;
    for node in open.iter().rev() {
        let NodeData::Element { name, .. } = &node.data else {
            continue;
        };
        if name.ns != ns!(html) {
            continue;
        }
        match name.local.as_ref() {
            "thead" => saw_thead = true,
            "table" | "tbody" | "tfoot" => return false,
            "template" | "html" => return saw_thead,
            _ => {}
        }
    }
    saw_thead
}

/// Whether the standard's `<option>`, `<optgroup>` or `<hr>` inside `select`
/// closes an element other than an `<option>` or `<optgroup>`. It closes the
/// run of elements at the top whose end tag the standard implies (`<option>`
/// stops at an `<optgroup>`), and html5ever closes at most an `<option>`.
fn select_closes_more(open: &[Handle], tag: &str) -> bool {
    for node in open.iter().rev() {
        let NodeData::Element { name, .. } = &node.data else {
            continue;
        };
        if name.ns != ns!(html) {
            return false;
        }
        match name.local.as_ref() {
            "option" => {}
            "optgroup" if tag != "option" => {}
            "dd" | "dt" | "li" | "p" | "rb" | "rp" | "rt" | "rtc" => return true,
            _ => return false,
        }
    }
    false
}

/// Whether an `<annotation-xml>` start tag names an encoding that makes the
/// element hold HTML in browsers. They compare the value with ASCII letters in
/// any case. This also accepts the value with ASCII whitespace around it, or
/// with its character references decoded, which can only count more tags.
fn holds_html_encoding(tag: &Tag) -> bool {
    tag.attrs
        .iter()
        .filter(|attr| attr.name.local.as_ref() == "encoding")
        .any(|attr| {
            let raw: &str = &attr.value;
            [Cow::Borrowed(raw), decode_html_attribute(raw)]
                .iter()
                .any(|value| {
                    let value =
                        value.trim_matches(|c| matches!(c, ' ' | '\t' | '\n' | '\r' | '\x0c'));
                    value.eq_ignore_ascii_case("text/html")
                        || value.eq_ignore_ascii_case("application/xhtml+xml")
                })
        })
}

fn is_mathml_annotation_xml(node: &Handle) -> bool {
    matches!(&node.data, NodeData::Element { name, .. }
        if name.ns == ns!(mathml) && name.local.as_ref() == "annotation-xml")
}

/// A [`Tracer`] that keeps what the tree builder reports.
#[derive(Default)]
struct CollectHandles(RefCell<Vec<Handle>>);

impl Tracer for CollectHandles {
    type Handle = Handle;

    fn trace_handle(&self, node: &Handle) {
        self.0.borrow_mut().push(node.clone());
    }
}

/// What html5ever holds at one moment (see [`held_elements`]).
#[derive(Default)]
pub(crate) struct Held {
    /// Every handle html5ever reported for this read, in its order. Holding
    /// them keeps those nodes alive, so no other node can take one of their
    /// addresses while this read is kept (see [`held_elements`]).
    reports: Vec<Handle>,
    /// Where the open elements (outermost first) sit in `reports`.
    open: Range<usize>,
    /// Where the elements on the list of formatting elements sit in
    /// `reports`.
    listed: Range<usize>,
    /// The elements made and the handles html5ever reported when this was
    /// last confirmed, or `None` when that happened while html5ever worked
    /// on a token.
    key: Cell<Option<(usize, usize)>>,
    /// The list of formatting elements holds an element that is no longer
    /// open. Browsers reopen such an element at the next start tag or text
    /// that asks for it.
    closed_formatting: bool,
    /// The read could not tell every open element from the list's (see
    /// [`read_held`]).
    unclear: bool,
    /// Whether four equal formatting elements had been made when this read
    /// was made (`TrackingSink::copy_rule_possible`). `unclear` depends on
    /// it, so a read made before it turned on is not reused after.
    copy_rule_possible: bool,
    /// What [`end_tag_is_ignored`] worked out for each end tag name.
    end_tag_answers: RefCell<HashMap<String, EndTagAnswer>>,
}

impl Held {
    /// The open elements, outermost first.
    fn open(&self) -> &[Handle] {
        &self.reports[self.open.clone()]
    }

    /// The elements on the list of formatting elements, oldest first.
    fn listed(&self) -> &[Handle] {
        &self.reports[self.listed.clone()]
    }
}

/// A [`Tracer`] that checks whether html5ever reports the same handles, in
/// the same order, as an earlier read.
struct SameReports<'a> {
    earlier: &'a [Handle],
    next: Cell<usize>,
    same: Cell<bool>,
}

impl Tracer for SameReports<'_> {
    type Handle = Handle;

    fn trace_handle(&self, node: &Handle) {
        let index = self.next.get();
        self.next.set(index + 1);
        if self.same.get() {
            self.same.set(
                self.earlier
                    .get(index)
                    .is_some_and(|earlier| Rc::ptr_eq(earlier, node)),
            );
        }
    }
}

/// Hashes a node's address for [`split_reports`]'s table. The allocator
/// picks addresses, so a page has no direct control over them.
#[derive(Default)]
pub(crate) struct PointerHasher(u64);

impl std::hash::Hasher for PointerHasher {
    fn finish(&self) -> u64 {
        self.0
    }

    fn write(&mut self, bytes: &[u8]) {
        for byte in bytes {
            self.0 = (self.0 ^ u64::from(*byte)).wrapping_mul(0x0100_0000_01b3);
        }
    }

    fn write_usize(&mut self, value: usize) {
        // Nodes are at least 16 bytes apart, so the low bits carry nothing.
        self.0 = ((value as u64) >> 4).wrapping_mul(0x9e37_79b9_7f4a_7c15);
    }
}

type BuildPointerHasher = std::hash::BuildHasherDefault<PointerHasher>;

/// What html5ever holds now.
///
/// A read is reused while html5ever holds the same, so a run of tags that
/// change nothing costs one read. Two checks tell that nothing changed:
///
/// - Only a new element can join the open elements or the formatting list:
///   html5ever puts nothing else on either, apart from the `<head>` it puts
///   back for one token and takes off again. Every other change takes a
///   handle away. So while no element has been made and html5ever reports
///   as many handles, both lists are as they were.
/// - Otherwise html5ever's report is compared with the one the read came
///   from, handle by handle. The read holds those handles, so the nodes are
///   alive and an equal address is the same node. An element that came and
///   went, such as an `<svg/>`, leaves the report as it was. This costs one
///   pass over the report, which the scan also makes after every token for
///   the size limits (`HtmlLimits::after_token`), where a full read also
///   sorts out the two lists.
///
/// Neither check applies once four equal formatting elements have been
/// made since the read (`copy_rule_possible`): the same handles can then
/// be an unclear answer where the read said a clear one, so the lists are
/// read again. That happens at most once per scan.
fn held_elements(builder: &TreeBuilder<Handle, TrackingSink>) -> Rc<Held> {
    let sink = &builder.sink;
    let key = sink
        .handle_count
        .get()
        .map(|count| (sink.elements_made.get(), count));
    if let Some(held) = sink
        .held
        .borrow()
        .as_ref()
        .filter(|held| held.copy_rule_possible == sink.copy_rule_possible.get())
    {
        if key.is_some() && held.key.get() == key {
            #[cfg(debug_assertions)]
            check_against_full_read(builder, held, "a read kept for the same count");
            return held.clone();
        }
        // A different number of handles cannot be the same report.
        let count_differs =
            matches!((key, held.key.get()), (Some((_, now)), Some((_, then))) if now != then);
        let same = SameReports {
            earlier: &held.reports,
            next: Cell::new(0),
            same: Cell::new(true),
        };
        if !count_differs {
            builder.trace_handles(&same);
            if same.same.get() && same.next.get() == held.reports.len() {
                #[cfg(debug_assertions)]
                check_against_full_read(builder, held, "a read kept for the same handles");
                held.key.set(key);
                return held.clone();
            }
        }
    }
    let earlier = sink.held.borrow_mut().take();
    let held = read_held(builder, earlier.as_deref());
    // The last read's buffer is reused when nothing else holds the read.
    if let Some(mut old) = earlier.and_then(|old| Rc::try_unwrap(old).ok()) {
        old.reports.clear();
        *sink.spare_reports.borrow_mut() = old.reports;
    }
    held.key.set(key);
    let held = Rc::new(held);
    // A read can tell that no SVG, MathML or `search` element is open any
    // more, so later tags skip the work they need. Each flag is looked at
    // only while it is set.
    if sink.foreign_maybe_open.get()
        && !held.open().iter().any(
            |node| matches!(&node.data, NodeData::Element { name, .. } if name.ns != ns!(html)),
        )
    {
        sink.foreign_maybe_open.set(false);
    }
    if sink.search_maybe_open.get()
        && !held
            .open()
            .iter()
            .any(|node| html_element_named(node, "search"))
    {
        sink.search_maybe_open.set(false);
    }
    *sink.held.borrow_mut() = Some(held.clone());
    held
}

/// Read html5ever's open elements and its list of formatting elements.
///
/// html5ever 0.29.0 shows neither list. Its `trace_handles` reports, in this
/// order, the document, the open elements (outermost first), the elements on
/// the formatting list, the `<head>` its head pointer names, the `<form>` its
/// form pointer names, and a fragment's context element. Nothing marks where
/// one part ends, so the parts are worked out:
///
/// - The head pointer is set before any element but `<html>` is open, and
///   the form pointer only later, so the reports end with that `<head>`, or
///   with it and a `<form>`. The output check never parses a fragment: it
///   reads markup meant for another page's body inside an empty host page
///   (see [`tree_builder_for`]).
/// - The formatting list (the standard's list of open `<b>`, `<i>`, `<a>`
///   and similar elements, which a browser reopens at the next tag or text
///   even after an end tag closed them) holds only HTML formatting
///   elements, so the open elements run at least to the last other element.
/// - After it, an element reported twice is open and on the list: its first
///   report is open, its second on the list. An element reported once is
///   either on the list and closed, or open and off the list. Only one rule
///   takes an open element off the list: the standard keeps at most three
///   copies of a formatting element with the same name and attributes on
///   the list, so a fourth copy pushes the oldest one off. The open
///   elements end before the first element reported for the second time,
///   and after the last one reported for the first time.
///
/// What lies between those two points is reported once. It is all closed
/// unless that copy rule has taken an element off the list. The rule needs
/// four elements with the same name and attributes, so while the page has
/// made no four such elements the answer is exact. Once it has, the read
/// cannot tell, so it counts that part as closed and says the answer is
/// unclear.
fn read_held(builder: &TreeBuilder<Handle, TrackingSink>, earlier: Option<&Held>) -> Held {
    debug_assert!(!builder.is_fragment());
    let collected = CollectHandles(RefCell::new(std::mem::take(
        &mut *builder.sink.spare_reports.borrow_mut(),
    )));
    builder.trace_handles(&collected);
    let reports = collected.0.into_inner();
    // Most tags change only the newest open elements, so the last read can
    // often be brought up to date without sorting out the two lists again.
    if let Some(earlier) = earlier.filter(|_| !builder.sink.copy_rule_possible.get()) {
        if let Some(held) = update_held(earlier, reports.as_slice()) {
            let held = Held { reports, ..held };
            // Tests and debug builds check the shortcut against a full read.
            #[cfg(debug_assertions)]
            check_against_full_read(builder, &held, "a read brought up to date");
            return held;
        }
    }
    split_reports(builder, reports)
}

/// Panic when a read that [`held_elements`] or [`read_held`] reuses or
/// brings up to date differs from a full read of what html5ever holds now.
/// Debug builds run it at every such shortcut, so the tests and any random
/// comparison run in a debug build check all three of them.
#[cfg(debug_assertions)]
fn check_against_full_read(
    builder: &TreeBuilder<Handle, TrackingSink>,
    held: &Held,
    shortcut: &str,
) {
    let collected = CollectHandles(RefCell::new(Vec::new()));
    builder.trace_handles(&collected);
    let full = split_reports(builder, collected.0.into_inner());
    // Equal addresses are the same nodes, because both reads hold them.
    let same = |a: &[Handle], b: &[Handle]| {
        a.len() == b.len() && a.iter().zip(b).all(|(a, b)| Rc::ptr_eq(a, b))
    };
    assert!(
        same(full.open(), held.open())
            && same(full.listed(), held.listed())
            && (
                full.closed_formatting,
                full.unclear,
                full.copy_rule_possible
            ) == (
                held.closed_formatting,
                held.unclear,
                held.copy_rule_possible
            ),
        "{shortcut} differs from a full read: full open {}, listed {}, closed {}, unclear {}, \
         copy rule possible {}; kept open {}, listed {}, closed {}, unclear {}, \
         copy rule possible {}",
        full.open().len(),
        full.listed().len(),
        full.closed_formatting,
        full.unclear,
        full.copy_rule_possible,
        held.open().len(),
        held.listed().len(),
        held.closed_formatting,
        held.unclear,
        held.copy_rule_possible,
    );
}

/// Sort html5ever's `reports` into the open elements and the formatting
/// list, as [`read_held`] describes.
fn split_reports(builder: &TreeBuilder<Handle, TrackingSink>, reports: Vec<Handle>) -> Held {
    let end = pointers_start(&reports);
    // The document comes first and is no element.
    let begin = end.min(1);
    let parts = &reports[begin..end];
    let formatting = |node: &Handle| {
        matches!(&node.data, NodeData::Element { name, .. }
            if name.ns == ns!(html) && is_formatting_element(name.local.as_bytes()))
    };
    let tail_start = parts
        .iter()
        .rposition(|node| !formatting(node))
        .map_or(0, |index| index + 1);
    if tail_start == parts.len() {
        return Held {
            open: begin..end,
            listed: end..end,
            copy_rule_possible: builder.sink.copy_rule_possible.get(),
            reports,
            ..Held::default()
        };
    }
    let tail = &parts[tail_start..];
    // For each element after `tail_start`: whether it was reported before,
    // and whether it is reported again later.
    let mut earlier = vec![false; tail.len()];
    let mut later = vec![false; tail.len()];
    {
        let mut first_seen = builder.sink.first_seen.borrow_mut();
        first_seen.clear();
        for (index, node) in tail.iter().enumerate() {
            match first_seen.entry(Rc::as_ptr(node) as usize) {
                Entry::Occupied(first) => {
                    earlier[index] = true;
                    later[*first.get()] = true;
                }
                Entry::Vacant(slot) => {
                    slot.insert(index);
                }
            }
        }
        // An element on the list whose open report comes before `tail_start`.
        for node in parts[..tail_start].iter().filter(|node| formatting(node)) {
            if let Some(&index) = first_seen.get(&(Rc::as_ptr(node) as usize)) {
                earlier[index] = true;
            }
        }
    }
    let first_listed = earlier.iter().position(|&seen| seen).unwrap_or(tail.len());
    let open_end = later[..first_listed]
        .iter()
        .rposition(|&again| again)
        .map_or(0, |index| index + 1);
    let undecided = open_end < first_listed;
    let closed_formatting = undecided || earlier[first_listed..].iter().any(|&seen| !seen);
    let copy_rule_possible = builder.sink.copy_rule_possible.get();
    let unclear = undecided && copy_rule_possible;
    let split = begin + tail_start + open_end;
    Held {
        open: begin..split,
        listed: split..end,
        closed_formatting,
        unclear,
        copy_rule_possible,
        reports,
        ..Held::default()
    }
}

/// Where the `<head>` and `<form>` pointers start at the end of html5ever's
/// `reports` (see [`read_held`]).
fn pointers_start(reports: &[Handle]) -> usize {
    let html_named = |node: &Handle, local: &str| {
        matches!(&node.data, NodeData::Element { name, .. }
            if name.ns == ns!(html) && name.local.as_ref() == local)
    };
    let end = reports.len();
    if end >= 3 && html_named(&reports[end - 1], "form") && html_named(&reports[end - 2], "head") {
        end - 2
    } else if end >= 2 && html_named(&reports[end - 1], "head") {
        end - 1
    } else {
        end
    }
}

/// Bring an earlier read up to date with html5ever's new `reports`, or say
/// `None` when the two lists have to be sorted out again. The answer has
/// empty `reports`, for the caller to fill in.
///
/// This holds when the reports end with the same elements on the
/// formatting list and the same `<head>` and `<form>` pointers, and the
/// open elements that left or joined since are none of them formatting
/// elements. Then the list is the same: an element joins it only when it
/// is made, and every made one joined the open elements instead, and an
/// open element leaves it only through the copy rule (see [`read_held`]),
/// which the caller rules out. Every element that left the open elements
/// comes after the part the two reports share, so each listed element is
/// open exactly when it was, and so is every closed one.
fn update_held(earlier: &Held, reports: &[Handle]) -> Option<Held> {
    let old = earlier.reports.as_slice();
    let same = |new: &[Handle], old: &[Handle]| {
        new.len() == old.len() && new.iter().zip(old).all(|(new, old)| Rc::ptr_eq(new, old))
    };
    // The `<head>` and `<form>` pointers, which may have been set since,
    // and then the elements on the list.
    let end = pointers_start(reports);
    let listed_start = end.checked_sub(earlier.listed.len())?;
    if listed_start < earlier.open.start
        || !same(&reports[end..], &old[earlier.listed.end..])
        || !same(&reports[listed_start..end], earlier.listed())
    {
        return None;
    }
    let limit = earlier.open.end.min(listed_start);
    let shared = (0..limit)
        .find(|&index| !Rc::ptr_eq(&reports[index], &old[index]))
        .unwrap_or(limit);
    // The document must be the same, and so must the first open element.
    if shared <= earlier.open.start.min(1) {
        return None;
    }
    let formatting = |node: &Handle| {
        matches!(&node.data, NodeData::Element { name, .. }
            if name.ns == ns!(html) && is_formatting_element(name.local.as_bytes()))
    };
    if old[shared..earlier.open.end].iter().any(formatting)
        || reports[shared..listed_start].iter().any(formatting)
    {
        return None;
    }
    Some(Held {
        open: earlier.open.start..listed_start,
        listed: listed_start..end,
        closed_formatting: earlier.closed_formatting,
        unclear: earlier.unclear,
        copy_rule_possible: earlier.copy_rule_possible,
        ..Held::default()
    })
}

/// Whether browsers ignore an end tag that html5ever would act on, because the
/// search for what to close stops at an SVG or MathML element that holds HTML,
/// or under [`EndTagRule::Chromium`]. An end tag that this rule changes in
/// another way sets `feeding` for the call that hands the tag to html5ever.
///
/// It also notes the end tag as a [`ParserDifference`] when browsers may
/// close something else for a reason this scan does not follow.
fn end_tag_is_ignored(builder: &TreeBuilder<Handle, TrackingSink>, tag: &str) -> bool {
    let sink = &builder.sink;
    let chromium = sink.rules.end_tags == EndTagRule::Chromium;
    let held = held_elements(builder);
    if held.unclear {
        sink.note_difference(tag, DifferenceKind::UnclearFormatting);
    }
    // A run of the same stray end tag, which html5ever ignores, keeps the
    // same read, so the answer is worked out once for it.
    let answer = *held
        .end_tag_answers
        .borrow_mut()
        .entry(tag.to_owned())
        .or_insert_with(|| end_tag_answer(&held, tag, chromium));
    if answer.rule_matters {
        sink.end_tag_rule_matters.set(true);
    }
    if let Some(capitals) = answer.exact_capitals {
        sink.feeding.set(FedTag::ExactEndTag { capitals });
    }
    if let Some(kind) = answer.differs {
        sink.note_difference(tag, kind);
    }
    answer.ignored
}

/// What [`end_tag_is_ignored`] does for one end tag, given what html5ever
/// holds.
#[derive(Clone, Copy, Default)]
struct EndTagAnswer {
    ignored: bool,
    /// Another browser can read what follows differently (see
    /// [`ScanResult::end_tag_rule_matters`]).
    rule_matters: bool,
    /// html5ever gets the tag as one Chromium compares exactly, with or
    /// without the capitals of an SVG name.
    exact_capitals: Option<bool>,
    /// Browsers may close something else (see [`ParserDifference`]).
    differs: Option<DifferenceKind>,
}

fn end_tag_answer(held: &Held, tag: &str, chromium: bool) -> EndTagAnswer {
    let mut answer = EndTagAnswer::default();
    let names = || {
        held.open()
            .iter()
            .rev()
            .filter_map(|node| match &node.data {
                NodeData::Element { name, .. } => Some(name),
                _ => None,
            })
    };
    let inside_svg = names().next().is_some_and(|name| name.ns == ns!(svg));
    // Chromium gives the tag the capitals of an SVG name only inside SVG.
    let capitals = inside_svg && svg_name_has_capitals(tag);
    // In SVG or MathML, the tag first closes a matching foreign element, as
    // long as no HTML element comes between them.
    for name in names() {
        if name.ns == ns!(html) {
            break;
        }
        if name.local.as_ref().eq_ignore_ascii_case(tag) {
            let has_capitals = name.local.chars().any(|c| c.is_ascii_uppercase());
            if has_capitals == capitals {
                return answer;
            }
            answer.rule_matters = true;
            if !chromium {
                return answer;
            }
            answer.exact_capitals = Some(capitals);
        }
    }
    // Then it looks for an HTML element with its name.
    let mut passed_search = false;
    for name in names() {
        if name.ns == ns!(html) {
            let local = name.local.as_ref();
            if local == tag {
                // Firefox stops at a `search` element, and html5ever and
                // Chromium pass it.
                answer.differs = passed_search.then_some(DifferenceKind::SearchElement);
                if capitals {
                    answer.rule_matters = true;
                    answer.ignored = chromium;
                }
                return answer;
            }
            passed_search |= local == "search";
            // html5ever stops at its own special elements too, and the
            // elements that end a scope are among them, so what lies past
            // one cannot change what it does.
            if is_html5ever_special(local) {
                return answer;
            }
            continue;
        }
        if is_foreign_special(&name.expanded()) {
            answer.ignored = true;
            // For a formatting tag such as `</b>`, browsers first look on the
            // list of formatting elements, and drop a closed element they
            // find there, which html5ever would reopen later.
            answer.differs = (is_formatting_element(tag.as_bytes())
                && held
                    .listed()
                    .iter()
                    .any(|node| html_element_named(node, tag)))
            .then_some(DifferenceKind::FormattingEndTagInForeign);
            return answer;
        }
    }
    answer
}

/// Whether html5ever 0.29.0 counts this HTML element as special: the search
/// for what an end tag closes stops at it (its `special_tag` list).
fn is_html5ever_special(name: &str) -> bool {
    matches!(
        name,
        "address"
            | "applet"
            | "area"
            | "article"
            | "aside"
            | "base"
            | "basefont"
            | "bgsound"
            | "blockquote"
            | "body"
            | "br"
            | "button"
            | "caption"
            | "center"
            | "col"
            | "colgroup"
            | "dd"
            | "details"
            | "dir"
            | "div"
            | "dl"
            | "dt"
            | "embed"
            | "fieldset"
            | "figcaption"
            | "figure"
            | "footer"
            | "form"
            | "frame"
            | "frameset"
            | "h1"
            | "h2"
            | "h3"
            | "h4"
            | "h5"
            | "h6"
            | "head"
            | "header"
            | "hgroup"
            | "hr"
            | "html"
            | "iframe"
            | "img"
            | "input"
            | "isindex"
            | "li"
            | "link"
            | "listing"
            | "main"
            | "marquee"
            | "menu"
            | "meta"
            | "nav"
            | "noembed"
            | "noframes"
            | "noscript"
            | "object"
            | "ol"
            | "p"
            | "param"
            | "plaintext"
            | "pre"
            | "script"
            | "section"
            | "select"
            | "source"
            | "style"
            | "summary"
            | "table"
            | "tbody"
            | "td"
            | "template"
            | "textarea"
            | "tfoot"
            | "th"
            | "thead"
            | "title"
            | "tr"
            | "track"
            | "ul"
            | "wbr"
            | "xmp"
    )
}

/// Hand a `select` tag to html5ever under the name of an `applet` tag (see
/// [`VisibleNames`]).
fn feed_as_select(
    builder: &TreeBuilder<Handle, TrackingSink>,
    tag: Tag,
) -> TokenSinkResult<Handle> {
    let sink = &builder.sink;
    sink.feeding.set(FedTag::Select);
    let result = hand_over(
        builder,
        Token::TagToken(Tag {
            name: sink.names.applet.clone(),
            ..tag
        }),
    );
    sink.feeding.set(FedTag::Other);
    result
}

/// Close the `select` element in scope, and say whether there was one.
fn close_select(builder: &TreeBuilder<Handle, TrackingSink>) -> bool {
    // html5ever does not say whether an end tag closed anything, but closing
    // an element changes how many elements it holds.
    let held = || {
        let count = CountHandles::default();
        builder.trace_handles(&count);
        count.0.get()
    };
    let before = held();
    // An end tag never asks the tokenizer to change state.
    let _ = feed_as_select(
        builder,
        Tag {
            kind: TagKind::EndTag,
            name: LocalName::from("select"),
            self_closing: false,
            attrs: Vec::new(),
        },
    );
    held() != before
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
        // One event can hold several tokens (text split at NULs). Once a
        // token has put the tree over a limit, the rest are not handed on.
        if self.limits.exceeded().is_some() {
            return;
        }
        let result = self.sink.feed(token);
        // Any token can make the tree builder reopen formatting elements,
        // so every token is followed by a check of what it holds.
        self.sink.check_limits(self.limits);
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
        // Once the page is over a limit, the caller refuses it, so nothing
        // more reaches the tree builder, whose cost the limits bound.
        // html5gum still reads the rest of the input, in linear time.
        if self.limits.exceeded().is_some() {
            return None;
        }
        match event {
            CallbackEvent::OpenStartTag { name } => {
                self.limits.start_tag(name);
                if self.limits.exceeded().is_some() {
                    return None;
                }
                self.sink.note_tag_start(span.start);
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
                // Only a start tag's attributes reach the tree builder; the
                // ones html5gum reports for an end tag are dropped below.
                if self.current_tag.is_some() {
                    self.limits.attribute();
                    if self.limits.exceeded().is_some() {
                        return None;
                    }
                }
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
                    // The browser keeps the first of two attributes with the
                    // same name, as html5ever's own tokenizer does; html5gum
                    // reports both. A set keeps this linear in the count.
                    if tag.attrs.len() > 1 {
                        let mut seen = HashSet::with_capacity(tag.attrs.len());
                        tag.attrs
                            .retain(|attr| seen.insert(attr.name.local.clone()));
                    }
                    let name = tag.name.as_ref().to_owned();
                    self.sink.begin_start_tag();
                    self.sink.note_tag_end(span.end);
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
                self.sink.note_tag_start(span.start);
                self.sink.note_tag_end(span.end);
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
                // still fails the page parse. A reference to a control
                // character passes too: Citry writes ESC as `&#27;`, and a
                // reference decodes to text, so it cannot change the tree.
                if !error_keeps_input_as_written(error)
                    && !matches!(error, Error::ControlCharacterReference)
                {
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
/// and the tree is the same as without the error. The server's escaped text
/// and attribute values can hold these two errors, because the server writes
/// these characters as they are and rejects NUL and carriage returns, and a
/// control character reference, because it writes ESC as `&#27;`. Every other
/// error fails the page parse; the fragment check also lets a character
/// reference error pass (see `is_character_reference_error`). Both accept only explicit, correctly
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

/// Read `input` the way the browser's parser does and return the facts of
/// each start tag.
///
/// Returns [`HtmlTooLarge`] when `input` is over one of the limits in
/// `html_limits` (too many attributes on one tag, too many `html`, `head` or
/// `body` start tags, elements nested too deep, or too many formatting
/// elements reopened).
pub fn scan_output_html(input: &str) -> Result<Vec<OutputTag>, HtmlTooLarge> {
    let builder = TreeBuilder::new(TrackingSink::default(), ParseOpts::default().tree_builder);
    Ok(scan_with_builder(input, builder, None, None)?.tags)
}

/// Scan `input` like [`scan_output_html`], under `rules`, for the output
/// check.
pub(crate) fn scan_output_html_under(
    input: &str,
    rules: BrowserRules,
    work_left: Option<Rc<Cell<usize>>>,
) -> Result<ScanResult, HtmlTooLarge> {
    scan_with_builder(input, tree_builder_for(rules), None, work_left)
}

/// Scan `input` like [`scan_output_html`], but hand each start tag to
/// `observer` when it ends at its `>`, instead of keeping it.
///
/// The result holds only the `script` and `style` tags, in document order,
/// with their element ends filled in. The observer receives each of those
/// tags with its index in the result, and every other tag with `None`.
///
/// Refuses the input like [`scan_output_html`] does, and when the scan
/// spends more than `work_left` holds (see `MAX_CHECK_WORK_PER_BYTE`). The
/// observer may have seen the tags before the limit was reached.
pub(crate) fn scan_output_html_with(
    input: &str,
    rules: BrowserRules,
    observer: &mut StartTagObserver<'_>,
    work_left: Option<Rc<Cell<usize>>>,
) -> Result<ScanResult, HtmlTooLarge> {
    scan_with_builder(input, tree_builder_for(rules), Some(observer), work_left)
}

fn scan_with_builder(
    input: &str,
    mut builder: TreeBuilder<Handle, TrackingSink>,
    observer: Option<&mut StartTagObserver<'_>>,
    work_left: Option<Rc<Cell<usize>>>,
) -> Result<ScanResult, HtmlTooLarge> {
    let limits = HtmlLimits::spending(work_left);
    let mut facts = Vec::new();
    let emitter = ScannerEmitter {
        inner: CallbackEmitter::new(ScannerCallback {
            sink: &mut builder,
            facts: &mut facts,
            collect_facts: true,
            observer: observer.map(|observer| observer as &mut StartTagObserver<'_>),
            input: input.as_bytes(),
            current_tag: None,
            current_fact: None,
            next_state: None,
            raw_stack: Vec::new(),
            boundary: None,
            lexical_text: None,
            limits: &limits,
        }),
    };
    run_tokenizer(input, emitter, &limits)?;
    let sink = &builder.sink;
    Ok(ScanResult {
        tags: facts,
        end_tag_rule_matters: sink.end_tag_rule_matters.get(),
        mode_matters: sink.mode_matters.get(),
        quirks: sink.quirks.get(),
        template_matters: sink.template_matters.get(),
        differences: sink.differences.take(),
    })
}

/// Parse a `div` fragment while retaining decoded source text in lexical
/// element occurrences. The DOM and source facts come from one tokenizer pass.
///
/// Returns `None` when the fragment cannot be read as one, including when it
/// is over one of the limits in `html_limits`.
pub(crate) fn parse_div_fragment_with_lexical_text(
    input: &str,
) -> Option<(RcDom, Vec<LexicalTextRun>)> {
    let limits = HtmlLimits::default();
    let dom = RcDom::default();
    let context = create_element(
        &dom,
        QualName::new(None, ns!(html), LocalName::from("div")),
        Vec::new(),
    );
    let mut builder = TreeBuilder::new_for_fragment(
        TrackingSink::new(dom),
        context,
        None,
        ParseOpts::default().tree_builder,
    );
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
            limits: &limits,
        }),
    };
    // The page cannot be compared with what was expected when it is not read.
    run_tokenizer(input, emitter, &limits).ok()?;
    if !tracker.valid || tracker.frames.len() != 1 {
        return None;
    }
    Some((builder.sink.finish(), tracker.runs))
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
/// first one by its name in the HTML standard. It also refuses a fragment
/// over one of the limits in `html_limits`, with that limit's message
/// (see [`HtmlTooLarge`]) after the word `opaque`.
pub fn validate_html_fragment_boundary(input: &str) -> Result<(), String> {
    let limits = HtmlLimits::default();
    let mut builder = TreeBuilder::new(TrackingSink::default(), ParseOpts::default().tree_builder);
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
            limits: &limits,
        }),
    };
    // Vue parses the block inside a `<template>`, where some tags read as
    // raw text in a document (such as `<style>` after `<col>`) are ignored
    // and the tags after them are read. Checking both contexts lets the
    // caller name the limit, rather than the later count failing.
    if let Err(too_large) = run_tokenizer(input, emitter, &limits)
        .and_then(|()| parse_fragment_in(input, "template").map(drop))
    {
        return Err(format!("opaque {too_large}"));
    }
    if let Some(name) = boundary.parse_error {
        Err(format!("opaque HTML has the HTML parse error {name}"))
    } else if boundary.invalid || !boundary.stack.is_empty() {
        Err("opaque HTML must be a self-contained strict fragment".to_owned())
    } else {
        Ok(())
    }
}

/// Parse `input` as the contents of a `context` element, the way the
/// browser's fragment parser does (`template.innerHTML = input` for
/// `"template"`), and return the document that holds the nodes.
///
/// html5gum reads the input and html5ever's tree builder builds the tree,
/// like every other scan here, so the size limits in `html_limits` apply
/// in the same parser context as the tree: a tag the tree builder reads is
/// counted, whatever raw text the context makes of the tags before it.
/// Returns [`HtmlTooLarge`] when the input is over a limit.
///
/// html5gum starts in its data state, which is right only for a context
/// whose contents the browser reads as markup, such as `template` or `div`
/// (not `title`, `textarea`, `script` or the like).
pub(crate) fn parse_fragment_in(input: &str, context: &str) -> Result<RcDom, HtmlTooLarge> {
    debug_assert!(
        matches!(context, "template" | "div"),
        "html5gum would start in the wrong state for <{context}>"
    );
    let limits = HtmlLimits::default();
    let dom = RcDom::default();
    let context = create_element(
        &dom,
        QualName::new(None, ns!(html), LocalName::from(context)),
        Vec::new(),
    );
    let mut builder = TreeBuilder::new_for_fragment(
        TrackingSink::new(dom),
        context,
        None,
        ParseOpts::default().tree_builder,
    );
    let mut facts = Vec::new();
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
            lexical_text: None,
            limits: &limits,
        }),
    };
    run_tokenizer(input, emitter, &limits)?;
    Ok(builder.sink.finish())
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
    use super::{
        browser_rules_for, scan_output_html, scan_output_html_under, tree_builder_for,
        validate_html_fragment_boundary, BrowserRules, EndTagRule, Handle, HtmlLimits, Mode,
        NodeData, Placement, ScannerCallback, ScannerEmitter,
    };
    use html5gum::emitters::callback::CallbackEmitter;

    use crate::tokenizer::run_tokenizer;

    /// The tree a scan under `rule` builds, with its text, in the form the
    /// browser probe prints: `(tag children)`, SVG tags as `svg:tag`.
    fn tree_under(input: &str, rules: BrowserRules) -> String {
        let limits = HtmlLimits::default();
        let mut builder = tree_builder_for(rules);
        let mut facts = Vec::new();
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
                lexical_text: None,
                limits: &limits,
            }),
        };
        run_tokenizer(input, emitter, &limits).expect("the input is small");

        fn write(node: &Handle, out: &mut String) {
            for child in node.children.borrow().iter() {
                match &child.data {
                    NodeData::Element {
                        name,
                        template_contents,
                        ..
                    } => {
                        out.push('(');
                        match name.ns.as_ref() {
                            "http://www.w3.org/2000/svg" => out.push_str("svg:"),
                            "http://www.w3.org/1998/Math/MathML" => out.push_str("math:"),
                            _ => {}
                        }
                        out.push_str(name.local.as_ref());
                        write(child, out);
                        if let Some(contents) = template_contents.borrow().as_ref() {
                            write(contents, out);
                        }
                        out.push(')');
                    }
                    NodeData::Text { contents } => {
                        out.push_str(&format!("{:?}", contents.borrow().to_string()));
                    }
                    _ => {}
                }
            }
        }
        // `<html>` holds `<head>` and `<body>`, or `<frameset>`; the last
        // one is the part of the page these shapes change.
        let document = builder.sink.dom.document.clone();
        let html = document.children.borrow().last().cloned().expect("html");
        let body = html.children.borrow().last().cloned().expect("body");
        let mut out = String::new();
        write(&body, &mut out);
        out
    }

    /// These trees come from Chromium 156 and Firefox 157, which built the
    /// same tree for every shape here. The Rust side never sees a browser,
    /// so this pins the [`super::VisibleNames`] rules to what the browsers do.
    #[test]
    fn keeping_select_contents_builds_the_tree_browsers_build() {
        for (input, expected) in [
            ("<select><select><b>x", r#"(select)(b"x")"#),
            // The scan closes `select` just after `<input>`, because only then
            // does it know which rule took a hidden input, so the input lands
            // inside `select`, where browsers put it just after. The input is
            // void, so what follows is read the same.
            ("<select><input><b>x", r#"(select(input))(b"x")"#),
            (
                "<select><input type=hidden><b>x",
                r#"(select(input))(b"x")"#,
            ),
            ("<select><keygen><b>x", r#"(select(keygen)(b"x"))"#),
            (
                "<select><textarea></textarea><b>x",
                r#"(select(textarea)(b"x"))"#,
            ),
            ("<select><hr><b>x", r#"(select(hr)(b"x"))"#),
            ("<select><option><select><b>x", r#"(select(option))(b"x")"#),
            ("<p><select><p>x", r#"(p(select(p"x")))"#),
            ("<p><select></p><b>x", r#"(p(select(p)(b"x")))"#),
            ("<div><select></div><b>x", r#"(div(select(b"x")))"#),
            ("<span><select></span><b>x", r#"(span(select(b"x")))"#),
            ("<select><div></select><b>x", r#"(select(div))(b"x")"#),
            ("<select><svg></select><b>x", r#"(select(svg:svg))(b"x")"#),
            (
                "<select><svg><desc></select><b>x",
                r#"(select(svg:svg(svg:desc(b"x"))))"#,
            ),
            ("<button><select></button><b>x", r#"(button(select(b"x")))"#),
            ("<select><button></select><b>x", r#"(select(button))(b"x")"#),
            (
                "<table><select><input type=hidden><b>x",
                r#"(select(input)(b"x"))(table)"#,
            ),
            (
                "<table><select><input><b>x",
                r#"(select(input))(b"x")(table)"#,
            ),
            (
                "<table><select><tr><td>x",
                r#"(select)(table(tbody(tr(td"x"))))"#,
            ),
            (
                "<table><td><select><td>y",
                r#"(table(tbody(tr(td(select))(td"y"))))"#,
            ),
            (
                "<table><td><select></td><td>y",
                r#"(table(tbody(tr(td(select))(td"y"))))"#,
            ),
            (
                "<table><caption><select></caption>x",
                r#""x"(table(caption(select)))"#,
            ),
            ("<select><table></table><b>x", r#"(select(table)(b"x"))"#),
            ("<select><table></select><b>x", r#"(select(b"x")(table))"#),
            (
                "<select><template></select></template><b>x",
                r#"(select(template)(b"x"))"#,
            ),
            ("<select></select><frameset>", "(select)"),
            ("<select><frameset>", "(select)"),
            ("<select><option><p></select>x", r#"(select(option(p)))"x""#),
            ("<a><select><a>x", r#"(a(select(a"x")))"#),
            ("<b><select></b>x", r#"(b(select"x"))"#),
            ("<select><plaintext>x", r#"(select(plaintext"x"))"#),
            (
                "<select><script>1</script><b>x",
                r#"(select(script"1")(b"x"))"#,
            ),
            (
                "<svg><select><select><b>x</select>y",
                r#"(svg:svg(svg:select(svg:select)))(b"xy")"#,
            ),
            (
                "<math><mtext><select><b>x",
                r#"(math:math(math:mtext(select(b"x"))))"#,
            ),
            (
                "<select><svg><select><b>x",
                r#"(select(svg:svg(svg:select))(b"x"))"#,
            ),
            (
                "<select><svg><input>x",
                r#"(select(svg:svg(svg:input"x")))"#,
            ),
            (
                "<select><option><option>x",
                r#"(select(option)(option"x"))"#,
            ),
            // Browsers end the first `<optgroup>` here, and html5ever's own
            // `optgroup` rule does not. Both are ordinary elements inside
            // `select`, so no tag after them reads differently.
            (
                "<select><optgroup><option><optgroup>x",
                r#"(select(optgroup(option)(optgroup"x")))"#,
            ),
            ("<select><option></select>x", r#"(select(option))"x""#),
            ("<select></option>x", r#"(select"x")"#),
            ("<select><li><li>x", r#"(select(li)(li"x"))"#),
            ("<select><dd><dt>x", r#"(select(dd)(dt"x"))"#),
            ("<select><h1><h2>x", r#"(select(h1)(h2"x"))"#),
            ("<select><p><div>x", r#"(select(p)(div"x"))"#),
            ("<select><form><form>x", r#"(select(form"x"))"#),
            ("<form><select></form>x", r#"(form(select"x"))"#),
            // `select` keeps its scope while html5ever works on other tags.
            (
                "<svg></svg><p><select><li>x",
                r#"(svg:svg)(p(select(li"x")))"#,
            ),
            (
                "<svg></svg><p><select></p>x",
                r#"(svg:svg)(p(select(p)"x"))"#,
            ),
            (
                "<svg><title></title></svg><p><select><dd><svg></select>x",
                r#"(svg:svg(svg:title))(p(select(dd(svg:svg)))"x")"#,
            ),
            (
                "<svg></svg><p><select><svg><title></p>x",
                r#"(svg:svg)(p(select(svg:svg(svg:title(p)"x"))))"#,
            ),
            (
                "<clippath><select><svg></clippath>x",
                r#"(clippath(select(svg:svg"x")))"#,
            ),
            (
                "<svg></svg><b><select><span></b>x",
                r#"(svg:svg)(b(select(span"x")))"#,
            ),
            (
                "<svg></svg><span><select></span>x",
                r#"(svg:svg)(span(select"x"))"#,
            ),
            // A real `<applet>` and `<select>` must not close each other.
            ("<applet><select></applet><b>x", r#"(applet(select(b"x")))"#),
            ("<select><applet></select><b>x", r#"(select(applet(b"x")))"#),
            ("<select></applet><b>x", r#"(select(b"x"))"#),
        ] {
            let rules = BrowserRules {
                keep_select_tags: true,
                ..BrowserRules::default()
            };
            assert_eq!(tree_under(input, rules), expected, "{input}");
        }
    }

    /// These trees come from Firefox 157. Chromium 156 and the first reading
    /// keep the `<p>` or `<br>` inside the SVG or MathML element.
    #[test]
    fn a_stray_end_tag_can_leave_foreign_content_as_firefox_does() {
        let firefox = BrowserRules {
            end_tags: EndTagRule::Firefox,
            ..BrowserRules::default()
        };
        for (input, expected) in [
            ("<svg><title></p>x", r#"(svg:svg(svg:title))(p)"x""#),
            ("<svg><title></br>x", r#"(svg:svg(svg:title))(br)"x""#),
            ("<svg><desc></p>x", r#"(svg:svg(svg:desc))(p)"x""#),
            (
                "<svg><foreignObject></p>x",
                r#"(svg:svg(svg:foreignObject))(p)"x""#,
            ),
            ("<math><mtext></p>x", r#"(math:math(math:mtext))(p)"x""#),
            ("<math><mi></br>x", r#"(math:math(math:mi))(br)"x""#),
            (
                "<math><annotation-xml encoding=text/html></p>x",
                r#"(math:math(math:annotation-xml))(p)"x""#,
            ),
            (
                "<svg><desc><math><mi></p>x",
                r#"(svg:svg(svg:desc(math:math(math:mi))))(p)"x""#,
            ),
            (
                "<div><svg><desc><svg><title></p>x",
                r#"(div(svg:svg(svg:desc(svg:svg(svg:title))))(p)"x")"#,
            ),
            (
                "<table><td><svg><title></p>x",
                r#"(table(tbody(tr(td(svg:svg(svg:title))(p)"x"))))"#,
            ),
            // Every other end tag behaves the same in every browser.
            ("<svg><title></div>x", r#"(svg:svg(svg:title"x"))"#),
            ("<svg><title></svg>x", r#"(svg:svg(svg:title))"x""#),
        ] {
            assert_eq!(tree_under(input, firefox), expected, "{input}");
        }
    }

    /// These trees come from Chromium 156. Firefox 157 and the first reading
    /// close the outer HTML element instead.
    #[test]
    fn an_end_tag_with_an_svg_name_stays_inside_svg_as_chromium_does() {
        let chromium = BrowserRules {
            end_tags: EndTagRule::Chromium,
            ..BrowserRules::default()
        };
        for (input, expected) in [
            (
                "<foreignobject><svg></foreignobject>x",
                r#"(foreignobject(svg:svg"x"))"#,
            ),
            (
                "<clippath><svg><g></clippath>x",
                r#"(clippath(svg:svg(svg:g"x")))"#,
            ),
            (
                "<lineargradient><svg></lineargradient>x",
                r#"(lineargradient(svg:svg"x"))"#,
            ),
            // Inside MathML the tag keeps its letters.
            (
                "<foreignobject><math></foreignobject>x",
                r#"(foreignobject(math:math))"x""#,
            ),
            // So it misses an SVG element with capitals, and with capitals
            // it misses a MathML element without them.
            (
                "<svg><foreignObject><math></foreignObject>x",
                r#"(svg:svg(svg:foreignObject(math:math"x")))"#,
            ),
            (
                "<svg><clipPath><desc><math></clipPath>x",
                r#"(svg:svg(svg:clipPath(svg:desc(math:math"x"))))"#,
            ),
            (
                "<math><clippath><mi><svg></clippath>x",
                r#"(math:math(math:clippath(math:mi(svg:svg"x"))))"#,
            ),
            (
                "<foreignobject><svg><foreignObject><math></foreignobject>x",
                r#"(foreignobject(svg:svg(svg:foreignObject(math:math"x"))))"#,
            ),
        ] {
            assert_eq!(tree_under(input, chromium), expected, "{input}");
        }
    }

    /// These trees come from Chromium 156 and Firefox 157, which agree, and
    /// html5ever does not: its list of special elements leaves these out.
    #[test]
    fn an_svg_or_mathml_element_that_holds_html_stops_the_search_for_what_to_close() {
        for (input, expected) in [
            (
                "<span><math><mtext></span>x",
                r#"(span(math:math(math:mtext"x")))"#,
            ),
            (
                "<span><math><annotation-xml></span>x",
                r#"(span(math:math(math:annotation-xml"x")))"#,
            ),
            (
                "<span><svg><title><b></span>x",
                r#"(span(svg:svg(svg:title(b"x"))))"#,
            ),
            ("<x><svg><title></x>x", r#"(x(svg:svg(svg:title"x")))"#),
            (
                "<g><svg><g><desc><b><math><mtext></g>x",
                r#"(g(svg:svg(svg:g(svg:desc(b(math:math(math:mtext"x")))))))"#,
            ),
            ("<li><svg><desc><li>x", r#"(li(svg:svg(svg:desc(li"x"))))"#),
            ("<dd><math><mi><dt>x", r#"(dd(math:math(math:mi(dt"x"))))"#),
            (
                "<li><svg><foreignObject><div><li>x",
                r#"(li(svg:svg(svg:foreignObject(div(li"x")))))"#,
            ),
            (
                "<li><math><annotation-xml encoding=text/html><li>x",
                r#"(li(math:math(math:annotation-xml(li"x"))))"#,
            ),
            // These have no such element in the way.
            ("<span><svg></span>x", r#"(span(svg:svg))"x""#),
            ("<svg><title></svg>x", r#"(svg:svg(svg:title))"x""#),
            (
                "<li><math><annotation-xml><mrow><li>x",
                r#"(li(math:math(math:annotation-xml(math:mrow))))(li"x")"#,
            ),
            ("<template><svg><title></template>x", r#""x""#),
            (
                "<table><svg><title></table>x",
                r#"(svg:svg(svg:title))(table)"x""#,
            ),
        ] {
            assert_eq!(
                tree_under(input, BrowserRules::default()),
                expected,
                "{input}"
            );
        }
    }

    /// These trees come from Chromium 156 and Firefox 157, which agree. The
    /// end tags here need the open elements, and html5ever reports them
    /// mixed with its formatting list and its `<head>` and `<form>`.
    #[test]
    fn the_open_elements_are_told_from_the_formatting_list() {
        for (input, expected) in [
            // A `<form>` on top of the open elements, and in the form
            // pointer.
            (
                "<math><mtext><form></form>x",
                r#"(math:math(math:mtext(form)"x"))"#,
            ),
            (
                "<svg><desc><form></form>x",
                r#"(svg:svg(svg:desc(form)"x"))"#,
            ),
            (
                "<math><mi><form></form></mi>x",
                r#"(math:math(math:mi(form))"x")"#,
            ),
            (
                "<svg><foreignObject><form><b></form>x",
                r#"(svg:svg(svg:foreignObject(form(b"x"))))"#,
            ),
            (
                "<math><mtext><form><div></form>x",
                r#"(math:math(math:mtext(form(div"x"))))"#,
            ),
            (
                "<form><svg><desc></form>x",
                r#"(form(svg:svg(svg:desc"x")))"#,
            ),
            // A formatting element that `</p>` or `</div>` closed stays on
            // the list, after every open element.
            (
                "<svg><desc><p><b></p></desc>x",
                r#"(svg:svg(svg:desc(p(b)))"x")"#,
            ),
            (
                "<svg><title><p><i></p></title>x",
                r#"(svg:svg(svg:title(p(i)))"x")"#,
            ),
            (
                "<math><mi><div><b></div></mi>x",
                r#"(math:math(math:mi(div(b)))"x")"#,
            ),
            (
                "<svg><desc><p><b><i></p></desc>x",
                r#"(svg:svg(svg:desc(p(b(i))))"x")"#,
            ),
            (
                "<svg><desc><form><p><b></p></form></desc>x",
                r#"(svg:svg(svg:desc(form(p(b))))"x")"#,
            ),
            (
                "<math><mtext><p><a></p></mtext>x",
                r#"(math:math(math:mtext(p(a)))"x")"#,
            ),
            (
                "<svg><desc><div><b></div></desc><g>x",
                r#"(svg:svg(svg:desc(div(b)))(svg:g"x"))"#,
            ),
        ] {
            assert_eq!(
                tree_under(input, BrowserRules::default()),
                expected,
                "{input}"
            );
        }
    }

    fn noted(input: &str, rules: BrowserRules) -> Vec<(String, usize, usize)> {
        scan_output_html_under(input, rules, None)
            .unwrap()
            .differences
            .into_iter()
            .map(|difference| (difference.tag, difference.start, difference.end))
            .collect()
    }

    /// The case of each noted tag.
    fn noted_cases(input: &str, rules: BrowserRules) -> Vec<&'static str> {
        scan_output_html_under(input, rules, None)
            .unwrap()
            .differences
            .into_iter()
            .map(|difference| difference.kind.code())
            .collect()
    }

    /// Each page here hides a script from html5ever 0.29.0 that Chromium 156,
    /// Firefox 157, or both, run, as checked in those browsers, at the tag the
    /// scan notes.
    #[test]
    fn a_tag_browsers_read_another_way_is_noted() {
        let keep_select = BrowserRules {
            keep_select_tags: true,
            ..BrowserRules::default()
        };
        let default = BrowserRules::default();
        for (input, rules, tag) in [
            // An `<annotation-xml>` that holds HTML.
            (
                "<math><annotation-xml encoding=text/html></br>",
                default,
                "annotation-xml",
            ),
            (
                "<math><annotation-xml encoding=TEXT/HTML>",
                default,
                "annotation-xml",
            ),
            (
                "<math><annotation-xml encoding=' application/xhtml+xml'>",
                default,
                "annotation-xml",
            ),
            (
                "<math><annotation-xml encoding='text&#47;html'>",
                default,
                "annotation-xml",
            ),
            (
                "<annotation-xml encoding=text/html>",
                default,
                "annotation-xml",
            ),
            // An end tag that would cross an `<annotation-xml>` of any kind.
            (
                "<select><math><annotation-xml></select>",
                keep_select,
                "select",
            ),
            ("<form><math><annotation-xml></form>", default, "form"),
            // A formatting element browsers reopen around `<svg>` or `<math>`.
            ("<p><b></p><svg>", default, "svg"),
            ("<foreignObject><a></foreignobject><math>", default, "math"),
            // `<isindex>` and `search`.
            ("<svg><desc><span><isindex>", default, "isindex"),
            ("<svg><desc><span><search></span>", default, "span"),
            ("<svg><desc><b><search></b>", default, "b"),
            ("<svg><desc><li><search><li>", default, "li"),
            ("<span><search></span>", default, "span"),
            // A formatting end tag browsers match on the formatting list.
            ("<svg><desc><p><b></p></b>", default, "b"),
            // The standard's `<select>`.
            ("<select><option><dd><option>", keep_select, "option"),
            ("<select><option><dd><hr>", keep_select, "hr"),
            ("<select><optgroup><dd><optgroup>", keep_select, "optgroup"),
            ("<select><b></select>", keep_select, "select"),
            ("<p><b></p><select>", keep_select, "select"),
            ("<b><select><i>", keep_select, "i"),
            // Both rules meet a `</select>` inside SVG or MathML.
            ("<select><svg></svg><b></select>", keep_select, "select"),
            (
                "<select><math><annotation-xml></select>",
                keep_select,
                "select",
            ),
            // A `<thead>` with no table around it.
            ("<template><thead><caption>", default, "caption"),
            // A legacy doctype, where a `<table>` may leave a `<p>` open.
            (
                "<!DOCTYPE html PUBLIC \"+//Silmaril//dtd html Pro v0r11 19970101//\"><p><table>",
                default,
                "table",
            ),
        ] {
            let found = noted(input, rules);
            assert_eq!(found.len(), 1, "{input}: {found:?}");
            let (name, start, end) = &found[0];
            assert_eq!(name, tag, "{input}");
            assert!(
                input[*start..*end].to_ascii_lowercase().contains(tag),
                "{input}"
            );
        }
    }

    /// Ordinary markup with the same tags as the noted pages builds the same
    /// tree in browsers and in the scan, so nothing is noted.
    #[test]
    fn ordinary_markup_like_the_noted_pages_is_not_noted() {
        let keep_select = BrowserRules {
            keep_select_tags: true,
            ..BrowserRules::default()
        };
        for input in [
            "<math><semantics><mi>x</mi><annotation-xml encoding=\"MathML-Content\"><ci>x</ci></annotation-xml></semantics></math>",
            "<math><annotation-xml encoding=text/htmlx></annotation-xml></math>",
            "<form><math><annotation-xml></annotation-xml></math></form>",
            "<p><b>x</b></p><svg></svg><math></math>",
            "<p><b>x</p> <svg></svg>",
            "<b><svg></svg></b><i>x</i>",
            "<search><form><input><button><svg><path/></svg></button></form></search>",
            "<ul><li><search>x</search><li>y</ul>",
            "<table><thead><tr><th>a</thead><tbody><tr><td>b</tbody><caption>c</caption></table>",
            "<!DOCTYPE html><p><table></table>",
            "<p><table></table>",
            "<svg><desc><b>x</b></desc></svg>",
            "<div><svg><title>x</title></svg></div>",
        ] {
            for rules in [BrowserRules::default(), keep_select] {
                assert_eq!(noted(input, rules), [], "{input}");
            }
        }
        for input in [
            "<select><option>a<option>b</select>",
            "<select><optgroup label=a><option>a<optgroup label=b><option>b</select>",
            "<select><option><b>x</b></option></select><svg></svg>",
            "<b><select><option>x</select></b>",
            "<select><button><selectedcontent></selectedcontent></button><option><svg></svg>a</select>",
            "<select><hr><option>a</select>",
        ] {
            assert_eq!(noted(input, keep_select), [], "{input}");
        }
    }

    /// Only the doctypes `quirks_list_differs` names make html5ever and a
    /// browser pick different modes, and only a `<table>` that meets a `<p>`
    /// in button scope builds a different tree there. A page with no
    /// doctype is in quirks mode in both, so it is not noted.
    #[test]
    fn a_table_in_a_paragraph_is_noted_only_where_html5ever_picks_another_mode() {
        let default = BrowserRules::default();
        for doctype in [
            "<!DOCTYPE html PUBLIC \"+//Silmaril//dtd html Pro v0r11 19970101//\">",
            "<!DOCTYPE html PUBLIC \"+//SILMARIL//DTD HTML PRO V0R11 19970101//EN\" \"x\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Frameset//EN\" \"\">",
        ] {
            let page = format!("{doctype}<p>Text<table></table>");
            assert_eq!(
                noted_cases(&page, default),
                ["quirks-doctype-table"],
                "{page}"
            );
            // A `<button>` ends button scope, so the `<p>` stays open in
            // both modes.
            let page = format!("{doctype}<p><button><table></table>");
            assert_eq!(noted_cases(&page, default), Vec::<&str>::new(), "{page}");
        }
        for doctype in [
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">",
            "<!DOCTYPE html SYSTEM \"about:legacy-compat\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01//EN\" \"http://www.w3.org/TR/html4/strict.dtd\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">",
            "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">",
            "<!DOCTYPE html>",
            "",
            // A doctype after the first element sets no mode.
            "<p></p><!DOCTYPE html PUBLIC \"+//Silmaril//dtd html Pro v0r11 19970101//\">",
        ] {
            let page = format!("{doctype}<p>Text<table></table>");
            assert_eq!(noted_cases(&page, default), Vec::<&str>::new(), "{page}");
        }
    }

    #[test]
    fn noted_tags_carry_the_case_that_names_the_fix() {
        let keep_select = BrowserRules {
            keep_select_tags: true,
            ..BrowserRules::default()
        };
        let default = BrowserRules::default();
        for (input, rules, case) in [
            (
                "<math><annotation-xml encoding=text/html>",
                default,
                "annotation-xml-html",
            ),
            (
                "<form><math><annotation-xml></form>",
                default,
                "annotation-xml-end-tag",
            ),
            ("<p><b></p><svg>", default, "reopened-formatting"),
            (
                "<svg><desc><p><b></p></b>",
                default,
                "formatting-end-tag-in-foreign",
            ),
            ("<svg><desc><span><isindex>", default, "isindex"),
            ("<svg><desc><span><search></span>", default, "search"),
            ("<svg><desc><li><search><li>", default, "search"),
            (
                "<select><b></select>",
                keep_select,
                "formatting-across-select",
            ),
            (
                "<select><option><dd><option>",
                keep_select,
                "select-closes-element",
            ),
            ("<template><thead><caption>", default, "thead-outside-table"),
            // A fourth `<b>` with the same attributes takes the first one off
            // the formatting list while it stays open. Once three end tags
            // close the others, the read cannot tell that `<b>` is open.
            (
                "<svg><desc><b><b><b><b></b></b></b></x>",
                default,
                "unclear-formatting",
            ),
        ] {
            assert_eq!(noted_cases(input, rules), [case], "{input}");
        }
        // With other attributes on each copy, no copy leaves the list, so
        // the read is exact.
        assert_eq!(
            noted_cases(
                "<svg><desc><b id=1><b id=2><b id=3><b id=4></b></b></b></x>",
                default
            ),
            Vec::<&str>::new()
        );
    }

    /// Debug builds check every read that `held_elements` keeps and every
    /// read that `update_held` brings up to date against a full read (see
    /// `check_against_full_read`). These pages, made from tags that open,
    /// close and misnest formatting elements around special and foreign
    /// elements, give that check many shapes to fail on.
    #[test]
    fn a_kept_or_updated_read_matches_a_full_read() {
        const PIECES: &[&str] = &[
            "<b>",
            "</b>",
            "<i>",
            "</i>",
            "<a>",
            "</a>",
            "<b id=1>",
            "<p>",
            "</p>",
            "<div>",
            "</div>",
            "<svg>",
            "</svg>",
            "<svg/>",
            "<math>",
            "<desc>",
            "</desc>",
            "<mtext>",
            "<g>",
            "</x>",
            "<table>",
            "<td>",
            "<tr>",
            "</table>",
            "<select>",
            "</select>",
            "<option>",
            "<form>",
            "</form>",
            "<span>",
            "</span>",
            "<li>",
            "<search>",
            "<template>",
            "</template>",
            "<head>",
            "<body>",
            "<frameset>",
            "<!DOCTYPE html>",
            "x",
            "<foreignObject>",
            "<br>",
        ];
        let mut state: u64 = 0x2545_f491_4f6c_dd1d;
        let mut next = || {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            state
        };
        let placements = [
            BrowserRules::default(),
            BrowserRules {
                keep_select_tags: true,
                end_tags: EndTagRule::Firefox,
                ..BrowserRules::default()
            },
            BrowserRules {
                placement: Placement::Body,
                mode: Mode::Quirks,
                end_tags: EndTagRule::Chromium,
                ..BrowserRules::default()
            },
            BrowserRules {
                placement: Placement::Template,
                mode: Mode::Standards,
                ..BrowserRules::default()
            },
        ];
        for _ in 0..4000 {
            let length = 4 + next() % 40;
            let page: String = (0..length)
                .map(|_| PIECES[(next() % PIECES.len() as u64) as usize])
                .collect();
            for rules in placements {
                // A page over a limit is refused, which is not what this
                // checks; the debug assertion panics on a mismatch.
                let _ = scan_output_html_under(&page, rules, None);
            }
        }
    }

    /// The nesting limit counts every element html5ever holds. A page read
    /// as a whole document or in another page's body holds `<html>`,
    /// `<body>` and the `<head>` pointer, so 509 nested elements fit; read
    /// inside a `<template>` it also holds the `<template>`, so 508 fit.
    #[test]
    fn each_placement_fits_the_nesting_its_host_elements_leave() {
        for (placement, mode, fits) in [
            (Placement::Document, Mode::FromDoctype, 509),
            (Placement::Body, Mode::Standards, 509),
            (Placement::Template, Mode::Standards, 508),
        ] {
            let rules = BrowserRules {
                placement,
                mode,
                ..BrowserRules::default()
            };
            assert!(
                scan_output_html_under(&"<div>".repeat(fits), rules, None).is_ok(),
                "{placement:?}"
            );
            assert_eq!(
                scan_output_html_under(&"<div>".repeat(fits + 1), rules, None).map(|_| ()),
                Err(crate::html_limits::HtmlTooLarge::OpenElements),
                "{placement:?}"
            );
        }
    }

    /// Each page makes a fourth equal formatting element and then reaches a
    /// tag where html5ever reports the same handles as the read before it.
    /// A read kept for the same handles would then say the lists are clear
    /// where a full read says they are unclear. Debug builds compare each
    /// kept read with a full one (see `check_against_full_read`), which
    /// panics on such a read.
    #[test]
    fn a_kept_read_is_dropped_once_four_equal_copies_are_made() {
        for input in [
            "<tr><i><i><select><caption><i><i></i><b>",
            "<table><i><i><select class=b><colgroup><i><i></i><hr>",
            "<thead><select><i><i><th><i><i></i><i>",
        ] {
            for end_tags in [
                EndTagRule::Standard,
                EndTagRule::Firefox,
                EndTagRule::Chromium,
            ] {
                for placement in [Placement::Document, Placement::Body, Placement::Template] {
                    let rules = BrowserRules {
                        keep_select_tags: true,
                        end_tags,
                        placement,
                        ..BrowserRules::default()
                    };
                    scan_output_html_under(input, rules, None).unwrap();
                }
            }
        }
        // The second page with more tags: the `</svg>` end tag must be
        // noted as unclear, which a kept read missed.
        let rules = BrowserRules {
            keep_select_tags: true,
            ..BrowserRules::default()
        };
        assert_eq!(
            noted_cases(
                "<table><i><i><select class=b><colgroup><i><i></i><hr><math></p></svg>",
                rules
            ),
            ["reopened-formatting", "unclear-formatting"]
        );
    }

    /// A body ignores a `<frameset>`, and a `<template>` builds the table
    /// part a body ignores.
    #[test]
    fn markup_put_into_another_page_builds_the_tree_it_builds_there() {
        let body = BrowserRules {
            placement: Placement::Body,
            mode: Mode::Standards,
            ..BrowserRules::default()
        };
        let template = BrowserRules {
            placement: Placement::Template,
            ..body
        };
        for (input, rules, expected) in [
            (
                "<frameset><textarea>x</textarea>",
                BrowserRules::default(),
                "",
            ),
            ("<frameset><textarea>x</textarea>", body, r#"(textarea"x")"#),
            (
                "<!DOCTYPE html><html><head><title>t</title></head><body><p>x</p></body></html>",
                body,
                r#"(title"t")(p"x")"#,
            ),
            ("<tr><td>x</td></tr>", body, r#""x""#),
            ("<tr><td>x</td></tr>", template, r#"(template(tr(td"x")))"#),
            // Chromium reads `template.innerHTML` with scripting off.
            (
                "<noscript><b>x</b></noscript>",
                BrowserRules {
                    noscript_as_markup: true,
                    ..template
                },
                r#"(template(noscript(b"x")))"#,
            ),
            (
                "<noscript><b>x</b></noscript>",
                template,
                r#"(template(noscript"<b>x</b>"))"#,
            ),
            // A `</template>` in the page cannot close the template it is
            // read in.
            ("</template><b>x</b>", template, r#"(template(b"x"))"#),
            ("<p><table></table>", body, "(p)(table)"),
            (
                "<p><table></table>",
                BrowserRules {
                    mode: Mode::Quirks,
                    ..body
                },
                "(p(table))",
            ),
        ] {
            assert_eq!(tree_under(input, rules), expected, "{input} {rules:?}");
        }
    }

    #[test]
    fn a_table_in_a_paragraph_or_a_table_part_alone_asks_for_more_readings() {
        let scan = |input| scan_output_html_under(input, BrowserRules::default(), None).unwrap();
        for input in [
            "<p><table>",
            "<p>a<span><table>",
            "<svg><p></svg><p><table>",
        ] {
            assert!(scan(input).mode_matters, "{input}");
        }
        for input in [
            "<p></p><table>",
            "<p><button><table>",
            "<table><tr><td><p>x</td></tr></table>",
        ] {
            assert!(!scan(input).mode_matters, "{input}");
        }
        for input in ["<tr>", "<p><td>", "<select><td>"] {
            assert!(scan(input).template_matters, "{input}");
        }
        for input in [
            "<table><tr><td>x</table>",
            "<template><tr></template>",
            "<svg><tr>",
        ] {
            assert!(!scan(input).template_matters, "{input}");
        }
        assert!(scan("").quirks && !scan("<!DOCTYPE html>").quirks);
    }

    #[test]
    fn only_an_end_tag_browsers_disagree_on_asks_for_more_readings() {
        let rule_matters = |input| {
            scan_output_html_under(input, BrowserRules::default(), None)
                .unwrap()
                .end_tag_rule_matters
        };
        for input in [
            "<svg><title></p>",
            "<math><mi></br>",
            "<svg><title><svg><g></p>",
        ] {
            assert!(rule_matters(input), "{input}");
        }
        for input in [
            "<p>a</p>",
            "<svg><g></p>",
            "<svg><title><p>a</p></title></svg><p>b</p>",
            "<svg><foreignObject><p>a</p></foreignObject></svg>",
            "<svg><clipPath></clipPath><linearGradient></linearGradient></svg>",
            "<clippath><math></clippath>",
        ] {
            assert!(!rule_matters(input), "{input}");
        }
    }

    #[test]
    fn a_page_needs_the_second_reading_only_with_the_text_select() {
        for (input, readings) in [
            ("<p>select</p>", 1),
            ("</select>", 1),
            ("<select>", 2),
            ("<SeLeCt id=a>", 2),
            // The text is enough, wherever it stands.
            ("<!-- <select -->", 2),
            ("<selectedcontent>", 2),
        ] {
            assert_eq!(
                browser_rules_for(input, BrowserRules::default()).len(),
                readings,
                "{input}"
            );
        }
    }

    #[test]
    fn the_two_select_rules_find_different_tags() {
        let names = |input, keep_select_tags| -> Vec<String> {
            let rules = BrowserRules {
                keep_select_tags,
                ..BrowserRules::default()
            };
            scan_output_html_under(input, rules, None)
                .unwrap()
                .tags
                .into_iter()
                .map(|tag| tag.name)
                .collect()
        };
        let input = "<select><style><!-- </style><script></script><!-- --></select>";
        assert_eq!(names(input, false), ["select", "style"]);
        assert_eq!(names(input, true), ["select", "style", "script"]);
        // `scan_output_html` is the reading other callers rely on.
        assert_eq!(scan_output_html(input).unwrap().len(), 2);
    }

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
        let html = scan_output_html("<title><script>x</script></title>").unwrap();
        assert_eq!(
            html.iter().map(|tag| tag.name.as_str()).collect::<Vec<_>>(),
            ["title"]
        );

        let svg = scan_output_html("<svg><title><script>x</script></title></svg>").unwrap();
        assert_eq!(
            svg.iter().map(|tag| tag.name.as_str()).collect::<Vec<_>>(),
            ["svg", "title", "script"]
        );
    }

    #[test]
    fn spans_slice_exact_utf8_source_bytes() {
        let source = "<p title='žluťoučký' onclick=go()>x</p>";
        let tag = &scan_output_html(source).unwrap()[0];
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
                    .unwrap()
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
        let tag = &scan_output_html(source).unwrap()[0];
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
        let tags = scan_output_html(source).unwrap();
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
        let attr = &scan_output_html(source).unwrap()[0].attributes[0];
        assert_eq!(
            &source.as_bytes()[attr.value_start..attr.value_end],
            b"\x0b'javascript:x'"
        );
    }
}
