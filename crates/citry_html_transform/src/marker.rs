//! Root-marking scan over serialized component frames.
//!
//! [`mark_html`] walks the HTML once, splices the given attributes onto
//! root-level (depth 0) tags, and splits the result around child placeholder
//! elements so the caller can join in each child's finished HTML without a
//! second scan. Bytes it does not touch are copied through verbatim: no
//! re-serialization, no normalization, no entity handling. It cannot fail;
//! markup it does not understand is treated as text.
//!
//! [`transform_html`](crate::transform_html) stays the right tool when every
//! element of the input must be rewritten (its `all_attributes` mode); this
//! scanner only touches root-level tags.

// The scanner follows these parts of the browser's rules for where HTML
// elements start and end. Each tag name is looked up once, in `classify`,
// and the open elements carry what the rules need, so a tag costs a few
// flag checks rather than a walk over name lists.

/// What a tag name means to the rules below. Names that need a rule of
/// their own get a `Kind`; the flags say which groups a name belongs to.
#[derive(Clone, Copy, PartialEq, Eq, Default)]
enum Kind {
    #[default]
    Other,
    P,
    Li,
    Dt,
    Dd,
    Option,
    Button,
    Td,
    Th,
    Caption,
    Tr,
    /// `<tbody>`, `<thead>` or `<tfoot>`.
    TableSection,
    Table,
    Ul,
    Ol,
    Dl,
    Address,
    Div,
    Template,
    Plaintext,
    Svg,
    Math,
    /// `<mglyph>` or `<malignmark>`, which stay MathML inside a MathML text
    /// element.
    MathMarkup,
}

/// The browser calls this element special: when it looks for the element
/// an end tag such as `</span>` names, it stops at any of these and ignores
/// the end tag.
const SPECIAL: u16 = 1;
/// The browser does not look past this element (its "scope" ends here) when
/// it looks for an open `<p>`, `<button>` or the element a block end tag
/// names.
const SCOPE: u16 = 1 << 1;
/// A block end tag, such as `</div>`: it closes its element and everything
/// inside it when the element is in scope.
const BLOCK_END: u16 = 1 << 2;
/// A start tag before which the browser ends an open `<p>`.
const CLOSES_P: u16 = 1 << 3;
/// A void element, which never has content. The list is html5ever's;
/// `image` is in it because the browser turns `<image>` into `<img>`.
const VOID: u16 = 1 << 4;
/// An element whose content the browser reads as text, so the scanner skips
/// to its end tag. `<noscript>` is not one here: with scripting off its
/// content is markup, and Citry's template grammar places child components
/// there.
const RAW_TEXT: u16 = 1 << 5;
/// `<h1>` to `<h6>`.
const HEADING: u16 = 1 << 6;

/// What the rules need to know about one tag name.
#[derive(Clone, Copy, Default)]
struct TagClass {
    kind: Kind,
    flags: u16,
}

impl TagClass {
    fn has(self, flag: u16) -> bool {
        self.flags & flag != 0
    }
}

/// Classify an HTML tag name, ignoring ASCII case. A name no rule knows,
/// such as a custom element, is `Kind::Other` with no flags.
fn classify(name: &[u8]) -> TagClass {
    // Every name the rules know fits in 16 bytes.
    let mut lower = [0u8; 16];
    if name.len() > lower.len() {
        return TagClass::default();
    }
    for (slot, byte) in lower.iter_mut().zip(name) {
        *slot = byte.to_ascii_lowercase();
    }
    let (kind, flags) = match &lower[..name.len()] {
        b"p" => (Kind::P, SPECIAL | BLOCK_END | CLOSES_P),
        b"li" => (Kind::Li, SPECIAL | BLOCK_END | CLOSES_P),
        b"dt" => (Kind::Dt, SPECIAL | BLOCK_END | CLOSES_P),
        b"dd" => (Kind::Dd, SPECIAL | BLOCK_END | CLOSES_P),
        b"option" => (Kind::Option, 0),
        b"button" => (Kind::Button, SPECIAL | BLOCK_END),
        b"td" => (Kind::Td, SPECIAL | SCOPE | BLOCK_END),
        b"th" => (Kind::Th, SPECIAL | SCOPE | BLOCK_END),
        b"caption" => (Kind::Caption, SPECIAL | SCOPE | BLOCK_END),
        b"tr" => (Kind::Tr, SPECIAL | BLOCK_END),
        b"tbody" | b"thead" | b"tfoot" => (Kind::TableSection, SPECIAL | BLOCK_END),
        b"table" => (Kind::Table, SPECIAL | SCOPE | BLOCK_END | CLOSES_P),
        b"ul" => (Kind::Ul, SPECIAL | BLOCK_END | CLOSES_P),
        b"ol" => (Kind::Ol, SPECIAL | BLOCK_END | CLOSES_P),
        b"dl" => (Kind::Dl, SPECIAL | BLOCK_END | CLOSES_P),
        b"address" => (Kind::Address, SPECIAL | BLOCK_END | CLOSES_P),
        b"div" => (Kind::Div, SPECIAL | BLOCK_END | CLOSES_P),
        b"template" => (Kind::Template, SPECIAL | SCOPE | BLOCK_END),
        b"plaintext" => (Kind::Plaintext, SPECIAL | CLOSES_P | RAW_TEXT),
        b"svg" => (Kind::Svg, 0),
        b"math" => (Kind::Math, 0),
        b"mglyph" | b"malignmark" => (Kind::MathMarkup, 0),
        b"h1" | b"h2" | b"h3" | b"h4" | b"h5" | b"h6" => {
            (Kind::Other, SPECIAL | CLOSES_P | HEADING)
        }
        b"article" | b"aside" | b"blockquote" | b"center" | b"details" | b"dialog" | b"dir"
        | b"fieldset" | b"figcaption" | b"figure" | b"footer" | b"form" | b"header" | b"hgroup"
        | b"listing" | b"main" | b"menu" | b"nav" | b"pre" | b"search" | b"section" => {
            (Kind::Other, SPECIAL | BLOCK_END | CLOSES_P)
        }
        b"summary" => (Kind::Other, SPECIAL | BLOCK_END),
        b"colgroup" | b"select" => (Kind::Other, SPECIAL | BLOCK_END),
        b"applet" | b"marquee" | b"object" => (Kind::Other, SPECIAL | SCOPE | BLOCK_END),
        b"hr" => (Kind::Other, SPECIAL | CLOSES_P | VOID),
        b"area" | b"base" | b"basefont" | b"bgsound" | b"br" | b"col" | b"embed" | b"frame"
        | b"img" | b"input" | b"keygen" | b"link" | b"meta" | b"param" | b"source" | b"track"
        | b"wbr" => (Kind::Other, SPECIAL | VOID),
        b"image" => (Kind::Other, VOID),
        b"script" | b"style" | b"textarea" | b"title" | b"xmp" | b"iframe" | b"noembed"
        | b"noframes" => (Kind::Other, SPECIAL | RAW_TEXT),
        b"html" => (Kind::Other, SPECIAL | SCOPE),
        b"body" | b"frameset" | b"head" | b"noscript" => (Kind::Other, SPECIAL),
        _ => (Kind::Other, 0),
    };
    TagClass { kind, flags }
}

/// The namespace an open element belongs to, which decides how the browser
/// reads the tags inside it.
#[derive(Clone, Copy, PartialEq, Eq)]
enum Namespace {
    Html,
    Svg,
    MathMl,
}

/// One element the scanner has seen open and not yet closed.
#[derive(Clone, Copy)]
struct OpenElement {
    /// Where the element's name sits in the input, so an end tag can find
    /// the element it closes.
    name_start: usize,
    name_end: usize,
    namespace: Namespace,
    /// For an HTML element, its class. An SVG or MathML element has the
    /// `SPECIAL` and `SCOPE` flags only when the browser reads its children
    /// as HTML, and no kind.
    class: TagClass,
    /// Whether the browser reads this element's children as HTML: every
    /// HTML element, SVG's `<foreignObject>`, `<desc>` and `<title>`, and
    /// MathML's `<mi>`, `<mo>`, `<mn>`, `<ms>` and `<mtext>`. MathML's
    /// `<annotation-xml encoding="text/html">` does too, but the scanner
    /// does not read attributes, so it treats that element as MathML.
    children_are_html: bool,
}

impl OpenElement {
    fn name<'a>(&self, bytes: &'a [u8]) -> &'a [u8] {
        &bytes[self.name_start..self.name_end]
    }

    fn is_html(&self, kind: Kind) -> bool {
        self.namespace == Namespace::Html && self.class.kind == kind
    }
}

/// The open elements, innermost last, with a count of the open elements of
/// each kind, so a rule can skip its search when nothing it closes is open.
#[derive(Default)]
struct OpenStack {
    elements: Vec<OpenElement>,
    counts: [u32; 8],
}

/// The kinds `OpenStack` counts, by slot.
fn counted_slot(element: &OpenElement) -> Option<usize> {
    if element.namespace != Namespace::Html {
        return None;
    }
    Some(match element.class.kind {
        Kind::P => 0,
        Kind::Li => 1,
        Kind::Dt | Kind::Dd => 2,
        Kind::Button => 3,
        Kind::Td | Kind::Th | Kind::Caption => 4,
        Kind::Tr => 5,
        Kind::TableSection => 6,
        _ if element.class.has(HEADING) => 7,
        _ => return None,
    })
}

impl OpenStack {
    fn push(&mut self, element: OpenElement) {
        if let Some(slot) = counted_slot(&element) {
            self.counts[slot] += 1;
        }
        self.elements.push(element);
    }

    /// Close the element at `index` and every element opened inside it.
    fn truncate(&mut self, index: usize) {
        while self.elements.len() > index {
            let element = self.elements.pop().expect("length checked");
            if let Some(slot) = counted_slot(&element) {
                self.counts[slot] -= 1;
            }
        }
    }

    fn last(&self) -> Option<&OpenElement> {
        self.elements.last()
    }

    fn is_empty(&self) -> bool {
        self.elements.is_empty()
    }

    fn open_count(&self, slot: usize) -> u32 {
        self.counts[slot]
    }

    /// The index of the innermost open HTML element that `matches`, unless
    /// an element with the `SCOPE` flag (or one of `extra_boundaries`) comes
    /// first.
    fn find_in_scope(
        &self,
        matches: impl Fn(&OpenElement) -> bool,
        extra_boundaries: &[Kind],
    ) -> Option<usize> {
        for index in (0..self.elements.len()).rev() {
            let element = &self.elements[index];
            if element.namespace == Namespace::Html && matches(element) {
                return Some(index);
            }
            if element.class.has(SCOPE)
                || (element.namespace == Namespace::Html
                    && extra_boundaries.contains(&element.class.kind))
            {
                return None;
            }
        }
        None
    }
}

/// The namespace a start tag lands in, inside the innermost open element.
fn child_namespace(open: &OpenStack, class: TagClass) -> Namespace {
    let parent = match open.last() {
        None => Namespace::Html,
        Some(parent) if !parent.children_are_html => return parent.namespace,
        // In a MathML text element, `<mglyph>` and `<malignmark>` stay MathML.
        Some(parent) if parent.namespace == Namespace::MathMl && class.kind == Kind::MathMarkup => {
            return Namespace::MathMl;
        }
        Some(_) => Namespace::Html,
    };
    match class.kind {
        Kind::Svg => Namespace::Svg,
        Kind::Math => Namespace::MathMl,
        // The browser also ends SVG or MathML content early when it meets
        // some HTML tags (`<p>`, `<div>`, `<img>` and others) inside it;
        // this scanner keeps those inside the SVG or MathML element.
        _ => parent,
    }
}

/// Whether the browser reads the children of this SVG or MathML element as
/// HTML.
fn foreign_children_are_html(namespace: Namespace, name: &[u8]) -> bool {
    let names: &[&[u8]] = match namespace {
        Namespace::Html => return true,
        Namespace::Svg => &[b"foreignObject", b"desc", b"title"],
        Namespace::MathMl => &[b"mi", b"mo", b"mn", b"ms", b"mtext"],
    };
    names
        .iter()
        .any(|candidate| candidate.eq_ignore_ascii_case(name))
}

/// Close what the browser closes before an HTML start tag of `class`
/// inserts its element:
/// - a new `<li>`, `<dt>` or `<dd>` ends an open one, unless a list or
///   another special element starts in between;
/// - a new `<option>` ends an open `<option>` that is the innermost element;
/// - a new `<button>` ends an open `<button>` in scope;
/// - a new `<td>`, `<th>`, `<tr>`, `<tbody>`, `<thead>` or `<tfoot>` ends the
///   open cell, row or section it replaces;
/// - a block start such as `<div>` ends an open `<p>` in scope;
/// - a heading ends an open heading that is the innermost element.
fn close_implied(open: &mut OpenStack, class: TagClass) {
    match class.kind {
        Kind::Li if open.open_count(1) > 0 => close_item(open, &[Kind::Li]),
        Kind::Dt | Kind::Dd if open.open_count(2) > 0 => close_item(open, &[Kind::Dt, Kind::Dd]),
        Kind::Option => {
            if open
                .last()
                .is_some_and(|element| element.is_html(Kind::Option))
            {
                open.truncate(open.elements.len() - 1);
            }
        }
        Kind::Button if open.open_count(3) > 0 => {
            if let Some(index) =
                open.find_in_scope(|element| element.class.kind == Kind::Button, &[])
            {
                open.truncate(index);
            }
        }
        Kind::Td | Kind::Th if open.open_count(4) > 0 => {
            close_in_table(open, &[Kind::Td, Kind::Th], &[Kind::Tr]);
        }
        Kind::Tr if open.open_count(5) > 0 => {
            close_in_table(open, &[Kind::Tr], &[Kind::TableSection]);
        }
        Kind::TableSection if open.open_count(6) > 0 => {
            close_in_table(open, &[Kind::TableSection], &[]);
        }
        _ => {}
    }
    if class.has(CLOSES_P) && open.open_count(0) > 0 {
        if let Some(index) =
            open.find_in_scope(|element| element.class.kind == Kind::P, &[Kind::Button])
        {
            open.truncate(index);
        }
    }
    if class.has(HEADING)
        && open.last().is_some_and(|element| {
            element.namespace == Namespace::Html && element.class.has(HEADING)
        })
    {
        open.truncate(open.elements.len() - 1);
    }
}

/// End an open list item of one of `items` before a new item starts,
/// unless an element the browser calls special, other than `<address>`,
/// `<div>` or `<p>`, comes first (such as a nested list).
fn close_item(open: &mut OpenStack, items: &[Kind]) {
    for index in (0..open.elements.len()).rev() {
        let element = &open.elements[index];
        if element.namespace != Namespace::Html {
            return;
        }
        if items.contains(&element.class.kind) {
            open.truncate(index);
            return;
        }
        if element.class.has(SPECIAL)
            && !matches!(element.class.kind, Kind::Address | Kind::Div | Kind::P)
        {
            return;
        }
    }
}

/// End the innermost open element of one of `kinds` inside the current
/// table, stopping at `<table>`, `<template>` or one of `stops`.
fn close_in_table(open: &mut OpenStack, kinds: &[Kind], stops: &[Kind]) {
    for index in (0..open.elements.len()).rev() {
        let element = &open.elements[index];
        if element.namespace != Namespace::Html {
            return;
        }
        let kind = element.class.kind;
        if kinds.contains(&kind) {
            open.truncate(index);
            return;
        }
        if matches!(kind, Kind::Table | Kind::Template) || stops.contains(&kind) {
            return;
        }
    }
}

/// Close what the browser closes for an end tag named `name`, or nothing
/// when it ignores the end tag.
fn close_for_end_tag(open: &mut OpenStack, bytes: &[u8], name: &[u8]) {
    let Some(current) = open.last() else {
        return;
    };
    if current.namespace != Namespace::Html {
        // Inside SVG or MathML, an end tag closes the innermost element with
        // its name, looking up to the first HTML element.
        for index in (0..open.elements.len()).rev() {
            let element = &open.elements[index];
            if element.namespace == Namespace::Html {
                break;
            }
            if element.name(bytes).eq_ignore_ascii_case(name) {
                open.truncate(index);
                return;
            }
        }
    }
    let class = classify(name);
    if class.has(HEADING) {
        // Any heading end tag closes the innermost open heading.
        if open.open_count(7) > 0 {
            if let Some(index) = open.find_in_scope(|element| element.class.has(HEADING), &[]) {
                open.truncate(index);
            }
        }
        return;
    }
    if matches!(class.kind, Kind::Table | Kind::TableSection | Kind::Tr) {
        // A table-level end tag first closes any open cell or caption.
        for index in (0..open.elements.len()).rev() {
            let element = &open.elements[index];
            if element.namespace == Namespace::Html
                && element.name(bytes).eq_ignore_ascii_case(name)
            {
                open.truncate(index);
                return;
            }
            let in_cell = element.namespace == Namespace::Html
                && matches!(element.class.kind, Kind::Td | Kind::Th | Kind::Caption);
            if !in_cell && element.class.has(SCOPE) {
                return;
            }
        }
        return;
    }
    if class.has(BLOCK_END) {
        if let Some(index) = open.find_in_scope(
            |element| element.name(bytes).eq_ignore_ascii_case(name),
            &[],
        ) {
            open.truncate(index);
        }
        return;
    }
    // Any other end tag closes the innermost element with its name, unless
    // an element the browser calls special comes first.
    for index in (0..open.elements.len()).rev() {
        let element = &open.elements[index];
        if element.namespace == Namespace::Html && element.name(bytes).eq_ignore_ascii_case(name) {
            open.truncate(index);
            return;
        }
        if element.class.has(SPECIAL) {
            return;
        }
    }
}

/// One placeholder element found by [`mark_html`].
pub struct MarkedPlaceholder {
    /// The value of the placeholder attribute (the child's render id).
    pub id: String,
    /// The placeholder element's text, including any spliced attributes.
    /// Callers that do not recognize `id` emit this verbatim.
    pub html: String,
    /// The attributes spliced into this placeholder (a subset of
    /// `root_attributes`; non-empty only when the placeholder sat at depth 0).
    pub added_attributes: Vec<String>,
}

/// The result of [`mark_html`].
///
/// The marked frame is `segments[0] + placeholders[0].html + segments[1] +
/// ... + segments[n]`; there is always exactly one more segment than
/// placeholders.
pub struct MarkedHtml {
    pub segments: Vec<String>,
    pub placeholders: Vec<MarkedPlaceholder>,
}

/// Splice `root_attributes` (as `attr=""`) onto every root-level (depth 0)
/// tag of `html`, and split the output around placeholder elements.
///
/// A placeholder is a `<template>` element (any ASCII case) that carries
/// `placeholder_attr` and whose body is only whitespace, e.g.
/// `<template c-render-id="cAb3d9"></template>`. A placeholder inside an
/// element whose content is text, such as `<xmp>`, is still split out, so
/// the child's HTML is not lost; it gets no attributes.
///
/// Root-level void and self-closing tags are marked too. Structure follows
/// the browser in these ways:
/// - comments, doctype, CDATA, processing instructions and quoted attribute
///   values containing `>` are skipped;
/// - the content of `<script>`, `<xmp>` and the other elements the browser
///   reads as text is skipped;
/// - a block end tag such as `</div>` closes its element and everything
///   inside it when the element is in scope; a table end tag first closes an
///   open cell or caption; any other end tag closes the innermost element
///   with its name unless an element the browser calls special comes first;
///   an end tag the browser ignores closes nothing;
/// - a new `<li>`, `<dt>`, `<dd>`, `<option>`, `<button>`, cell, row, table
///   section or heading ends an open one where the browser does, and a block
///   start such as `<div>` ends an open `<p>`;
/// - a self-closed HTML element that is not void, such as `<div/>` or
///   `<textarea/>`, stays open, while an SVG or MathML element closes at its
///   `/>`.
///
/// It sees one component's HTML at a time, so an element left open at the
/// end of that HTML, such as `<plaintext>`, does not affect what follows it
/// in the page.
pub fn mark_html(html: &str, root_attributes: &[String], placeholder_attr: &str) -> MarkedHtml {
    let bytes = html.as_bytes();
    let len = bytes.len();
    let splice: String = root_attributes
        .iter()
        .map(|attr| format!(" {attr}=\"\""))
        .collect();

    let mut segments: Vec<String> = Vec::new();
    let mut placeholders: Vec<MarkedPlaceholder> = Vec::new();
    let mut seg = String::with_capacity(len + splice.len());
    // The open elements; the scanner is at the root when it is empty.
    let mut open = OpenStack::default();
    let mut pos = 0;

    while pos < len {
        // Copy text verbatim up to the next '<'.
        let Some(lt) = find_byte(bytes, pos, b'<') else {
            seg.push_str(&html[pos..]);
            break;
        };
        seg.push_str(&html[pos..lt]);
        pos = lt;

        if starts_with_at(bytes, pos, b"<!--") {
            // Comment: copy through `-->` (or to EOF when unterminated).
            let end = find_seq(bytes, pos + 4, b"-->").map_or(len, |i| i + 3);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if starts_with_at(bytes, pos, b"<![CDATA[") {
            let end = find_seq(bytes, pos + 9, b"]]>").map_or(len, |i| i + 3);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if starts_with_at(bytes, pos, b"<!") || starts_with_at(bytes, pos, b"<?") {
            // Doctype or processing instruction: copy through the next '>'.
            let end = find_byte(bytes, pos, b'>').map_or(len, |i| i + 1);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if starts_with_at(bytes, pos, b"</") {
            // End tag: close what the browser closes for it.
            let name_start = pos + 2;
            let mut i = name_start;
            while i < len && !is_ws(bytes[i]) && bytes[i] != b'>' && bytes[i] != b'/' {
                i += 1;
            }
            let name = &bytes[name_start..i];
            let end = find_byte(bytes, pos, b'>').map_or(len, |i| i + 1);
            close_for_end_tag(&mut open, bytes, name);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if pos + 1 < len && bytes[pos + 1].is_ascii_alphabetic() {
            // Start tag.
            let tag = lex_start_tag(bytes, pos, placeholder_attr);
            let name = &bytes[tag.name_start..tag.name_end];
            let class = classify(name);
            let namespace = child_namespace(&open, class);
            if namespace == Namespace::Html {
                close_implied(&mut open, class);
            }
            let at_root = open.is_empty();
            let added: &str = if at_root { &splice } else { "" };

            // A placeholder: a `<template placeholder_attr=...>` whose body is
            // only whitespace up to its own `</template>`.
            let placeholder_end = if !tag.self_closing && class.kind == Kind::Template {
                tag.placeholder_value
                    .and_then(|_| placeholder_close_end(bytes, tag.end))
            } else {
                None
            };

            if let Some(ph_end) = placeholder_end {
                let (val_start, val_end) = tag.placeholder_value.expect("checked above");
                let mut ph_html = String::with_capacity(ph_end - pos + added.len());
                ph_html.push_str(&html[pos..tag.insert_pos]);
                ph_html.push_str(added);
                ph_html.push_str(&html[tag.insert_pos..ph_end]);
                placeholders.push(MarkedPlaceholder {
                    id: html[val_start..val_end].to_string(),
                    html: ph_html,
                    added_attributes: if at_root {
                        root_attributes.to_vec()
                    } else {
                        Vec::new()
                    },
                });
                segments.push(std::mem::take(&mut seg));
                pos = ph_end;
                // The whole element was consumed, so nothing stays open.
                continue;
            }

            seg.push_str(&html[pos..tag.insert_pos]);
            seg.push_str(added);
            seg.push_str(&html[tag.insert_pos..tag.end]);
            pos = tag.end;

            // The browser ignores the `/` of `<div/>` and keeps the element
            // open; only an SVG or MathML element ends at its `/>`.
            let closes_itself = tag.self_closing && namespace != Namespace::Html;
            let is_html_void = namespace == Namespace::Html && class.has(VOID);
            if closes_itself || is_html_void {
                continue;
            }
            let raw_text_end = if namespace == Namespace::Html && class.has(RAW_TEXT) {
                Some(raw_text_content_end(
                    bytes,
                    pos,
                    name,
                    class.kind == Kind::Plaintext,
                ))
            } else {
                None
            };
            if let Some(content_end) = raw_text_end {
                // Text content: copy it and the closing tag through, still
                // splitting out any placeholder so the child's HTML is kept.
                split_placeholders(
                    html,
                    pos,
                    content_end,
                    placeholder_attr,
                    &mut seg,
                    &mut segments,
                    &mut placeholders,
                );
                pos = content_end;
            } else {
                let children_are_html = foreign_children_are_html(namespace, name);
                let element_class = match namespace {
                    Namespace::Html => class,
                    // An SVG or MathML element whose children are HTML ends
                    // the browser's searches the way a special scope
                    // boundary does.
                    _ if children_are_html => TagClass {
                        kind: Kind::Other,
                        flags: SPECIAL | SCOPE,
                    },
                    _ => TagClass::default(),
                };
                open.push(OpenElement {
                    name_start: tag.name_start,
                    name_end: tag.name_end,
                    namespace,
                    class: element_class,
                    children_are_html,
                });
            }
        } else {
            // A bare '<' that opens no construct: plain text.
            seg.push('<');
            pos += 1;
        }
    }

    segments.push(seg);
    MarkedHtml {
        segments,
        placeholders,
    }
}

/// Copy `html[from..to]` into the output, splitting out each placeholder
/// element inside it with no attributes added.
fn split_placeholders(
    html: &str,
    from: usize,
    to: usize,
    placeholder_attr: &str,
    seg: &mut String,
    segments: &mut Vec<String>,
    placeholders: &mut Vec<MarkedPlaceholder>,
) {
    let bytes = html.as_bytes();
    let mut pos = from;
    while let Some(lt) = find_byte(&bytes[..to], pos, b'<') {
        if lt + 1 < to && bytes[lt + 1].is_ascii_alphabetic() {
            let tag = lex_start_tag(&bytes[..to], lt, placeholder_attr);
            let name = &bytes[tag.name_start..tag.name_end];
            let placeholder = if !tag.self_closing && name.eq_ignore_ascii_case(b"template") {
                tag.placeholder_value.and_then(|value| {
                    placeholder_close_end(&bytes[..to], tag.end).map(|ph_end| (value, ph_end))
                })
            } else {
                None
            };
            if let Some(((val_start, val_end), ph_end)) = placeholder {
                seg.push_str(&html[pos..lt]);
                placeholders.push(MarkedPlaceholder {
                    id: html[val_start..val_end].to_string(),
                    html: html[lt..ph_end].to_string(),
                    added_attributes: Vec::new(),
                });
                segments.push(std::mem::take(seg));
                pos = ph_end;
                continue;
            }
        }
        seg.push_str(&html[pos..=lt]);
        pos = lt + 1;
    }
    seg.push_str(&html[pos..to]);
}

/// A lexed start tag. All positions are byte offsets into the scanned input,
/// and all sit on ASCII bytes, so they are valid `str` slice boundaries.
struct StartTag {
    name_start: usize,
    name_end: usize,
    /// Where spliced attributes go: right after the last attribute (or the
    /// tag name), before any trailing whitespace and the `>` / `/>`.
    insert_pos: usize,
    /// One past the closing `>`.
    end: usize,
    self_closing: bool,
    /// Span of the placeholder attribute's value, when the tag carries it.
    placeholder_value: Option<(usize, usize)>,
}

/// Lex one start tag beginning at `start` (which holds `<`). Quoted attribute
/// values may contain `>`. Never fails; at EOF the tag just ends there.
fn lex_start_tag(bytes: &[u8], start: usize, placeholder_attr: &str) -> StartTag {
    let len = bytes.len();
    let name_start = start + 1;
    let mut i = name_start;
    while i < len && !is_ws(bytes[i]) && bytes[i] != b'/' && bytes[i] != b'>' {
        i += 1;
    }
    let name_end = i;
    let mut insert_pos = i;
    let mut placeholder_value: Option<(usize, usize)> = None;

    macro_rules! tag {
        ($end:expr, $self_closing:expr) => {
            StartTag {
                name_start,
                name_end,
                insert_pos,
                end: $end,
                self_closing: $self_closing,
                placeholder_value,
            }
        };
    }

    loop {
        while i < len && is_ws(bytes[i]) {
            i += 1;
        }
        if i >= len {
            return tag!(len, false);
        }
        match bytes[i] {
            b'>' => return tag!(i + 1, false),
            b'/' if i + 1 < len && bytes[i + 1] == b'>' => return tag!(i + 2, true),
            b'/' => i += 1, // stray slash inside the tag, skip it
            _ => {
                // Attribute name.
                let attr_start = i;
                while i < len
                    && !is_ws(bytes[i])
                    && bytes[i] != b'='
                    && bytes[i] != b'>'
                    && bytes[i] != b'/'
                {
                    i += 1;
                }
                let attr_end = i;
                let mut j = i;
                while j < len && is_ws(bytes[j]) {
                    j += 1;
                }
                let value = if j < len && bytes[j] == b'=' {
                    j += 1;
                    while j < len && is_ws(bytes[j]) {
                        j += 1;
                    }
                    if j < len && (bytes[j] == b'"' || bytes[j] == b'\'') {
                        let quote = bytes[j];
                        j += 1;
                        let val_start = j;
                        while j < len && bytes[j] != quote {
                            j += 1;
                        }
                        let val_end = j;
                        if j < len {
                            j += 1; // the closing quote
                        }
                        i = j;
                        Some((val_start, val_end))
                    } else {
                        // Unquoted value (may contain '/', per HTML5).
                        let val_start = j;
                        while j < len && !is_ws(bytes[j]) && bytes[j] != b'>' {
                            j += 1;
                        }
                        i = j;
                        Some((val_start, j))
                    }
                } else {
                    // Boolean attribute; do not consume the lookahead whitespace.
                    Some((attr_end, attr_end))
                };
                if bytes[attr_start..attr_end].eq_ignore_ascii_case(placeholder_attr.as_bytes()) {
                    placeholder_value = value;
                }
                insert_pos = i;
            }
        }
    }
}

/// When the bytes at `from` are only whitespace followed by a `</template>`
/// end tag, return one past that end tag's `>`; otherwise `None`.
fn placeholder_close_end(bytes: &[u8], from: usize) -> Option<usize> {
    let len = bytes.len();
    let mut i = from;
    while i < len && is_ws(bytes[i]) {
        i += 1;
    }
    if !starts_with_at(bytes, i, b"</") {
        return None;
    }
    let name_end = i + 2 + "template".len();
    if name_end > len || !bytes[i + 2..name_end].eq_ignore_ascii_case(b"template") {
        return None;
    }
    let mut j = name_end;
    while j < len && is_ws(bytes[j]) {
        j += 1;
    }
    if j < len && bytes[j] == b'>' {
        Some(j + 1)
    } else {
        None
    }
}

/// For an element named `name` whose content is text, return one past the
/// `>` of its matching closing tag (searching from `from`, the end of the
/// start tag), or the input length when the closing tag is missing.
fn raw_text_content_end(bytes: &[u8], from: usize, name: &[u8], is_plaintext: bool) -> usize {
    let len = bytes.len();
    // No end tag closes `<plaintext>`: the rest of the input is its text.
    if is_plaintext {
        return len;
    }
    let mut i = from;
    while i + 2 + name.len() <= len {
        if bytes[i] == b'<'
            && bytes[i + 1] == b'/'
            && bytes[i + 2..i + 2 + name.len()].eq_ignore_ascii_case(name)
        {
            // HTML5: the name must be followed by whitespace, '/', or '>'.
            let after = i + 2 + name.len();
            if after >= len || is_ws(bytes[after]) || bytes[after] == b'/' || bytes[after] == b'>' {
                return find_byte(bytes, after, b'>').map_or(len, |k| k + 1);
            }
        }
        i += 1;
    }
    len
}

fn is_ws(b: u8) -> bool {
    matches!(b, b' ' | b'\t' | b'\n' | b'\r' | b'\x0C')
}

fn find_byte(bytes: &[u8], from: usize, needle: u8) -> Option<usize> {
    bytes[from..]
        .iter()
        .position(|&b| b == needle)
        .map(|i| from + i)
}

fn starts_with_at(bytes: &[u8], at: usize, prefix: &[u8]) -> bool {
    bytes.len() >= at + prefix.len() && &bytes[at..at + prefix.len()] == prefix
}

fn find_seq(bytes: &[u8], from: usize, needle: &[u8]) -> Option<usize> {
    if from >= bytes.len() {
        return None;
    }
    bytes[from..]
        .windows(needle.len())
        .position(|w| w == needle)
        .map(|i| from + i)
}
