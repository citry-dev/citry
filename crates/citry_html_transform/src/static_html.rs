//! Check that a finished piece of HTML keeps its own tree when the browser
//! parses it inside a page.
//!
//! Citry inserts HTML that Python hands over as one finished string (`<c-raw>`
//! contents, trusted `Markup` with tags) as one fixed block. When Vue builds
//! the page in the browser, it parses that string inside a `<template>`
//! element and inserts the resulting nodes (`insertStaticContent` in
//! `runtime-dom`). When the page hydrates, the server writes the string into
//! the page instead, and the browser parses it where it sits, inside the
//! elements around it. Vue then adopts a fixed number of nodes for the block
//! without looking at them (the `Static` case of `hydrateNode` in
//! `runtime-core`).
//!
//! Both only agree when the page's parse gives the block exactly the tree its
//! `<template>` parse gives it: a `<p>` inside an open `<p>`, table parts
//! outside a table, or a stray end tag would otherwise be repaired
//! differently, and nodes after the block could move. [`static_html_in_context`]
//! parses the block both ways with html5ever and compares the trees, so a
//! block the page would repair is left to the browser.
//!
//! The same check covers the Citry HTML the server writes inside an element
//! that Vue builds in the browser (a "shell"): that HTML is only shown until
//! the browser runtime empties the shell, but it must not move nodes around
//! the shell while the browser parses the page.

use crate::output_scanner::scan_output_html;
use html5ever::tendril::TendrilSink;
use html5ever::{namespace_url, ns, parse_fragment, LocalName, ParseOpts, QualName};
use markup5ever_rcdom::{Handle, NodeData, RcDom};

/// How the page uses a checked block, which decides what it may contain.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum StaticHtmlUse {
    /// Vue adopts the block's nodes while it hydrates. The server writes the
    /// block between Vue's `<!--[-->` and `<!--]-->` Fragment comments.
    Adopted,
    /// The block is the content of a shell, shown until the browser runtime
    /// empties the shell and Vue builds its children again.
    Replaced,
}

/// What the page's parse of a checked block creates.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct StaticHtmlFacts {
    /// Top-level nodes (elements, texts and comments), which is the node
    /// count Vue's static vnode must be given to hydrate the block.
    pub node_count: usize,
    /// Elements at any depth.
    pub element_count: usize,
}

/// The number of top-level nodes the browser creates when Vue inserts `html`
/// as a static vnode while it builds a page (`template.innerHTML = html`).
pub fn static_html_node_count(html: &str) -> usize {
    parse_children(html, "template").map_or(0, |(_, nodes)| nodes.len())
}

/// Parse `html` as the contents of a `context` element and return the
/// nodes the parser put directly inside it, with the document that owns
/// them. The caller keeps the document alive while it reads the nodes:
/// dropping it empties every node's children.
fn parse_children(html: &str, context: &str) -> Option<(RcDom, Vec<Handle>)> {
    let dom = parse_fragment(
        RcDom::default(),
        ParseOpts::default(),
        QualName::new(None, ns!(html), LocalName::from(context)),
        Vec::new(),
    )
    .one(html);
    // A fragment parse puts one `html` element under the document, and the
    // parsed nodes inside it.
    let roots = dom.document.children.borrow().clone();
    let [root] = roots.as_slice() else {
        return None;
    };
    let nodes = match &root.data {
        NodeData::Element { name, .. } if name.local.as_ref() == "html" => {
            root.children.borrow().clone()
        }
        _ => return None,
    };
    Some((dom, nodes))
}

/// Elements whose parsed form runs code or loads content again when the
/// browser runtime empties a shell and Vue builds the same element anew.
/// Shell content is shown only until then, so it must not hold them.
const REPLACED_UNSAFE_TAGS: [&str; 10] = [
    "iframe", "frame", "frameset", "object", "embed", "applet", "meta", "base", "link", "portal",
];

/// Attributes with the same problem: a handler would run once for the served
/// element and again for Vue's, focus would move to an element that is then
/// removed, media would start and restart.
/// `is` runs a customized built-in element's constructor again, and
/// `preload` fetches media a second time.
const REPLACED_UNSAFE_ATTRIBUTES: [&str; 6] = [
    "autofocus",
    "autoplay",
    "srcdoc",
    "http-equiv",
    "is",
    "preload",
];

/// Start tags the `<template>` parse drops but the page's parse applies to
/// the document itself: `<html>` and `<body>` copy their attributes (an
/// `onload` handler among them) onto the page's own elements, and the frame
/// tags change the document's structure. html5ever's fragment parse cannot
/// show that, so a block holding one is rejected by name.
const DOCUMENT_TAGS: [&str; 5] = ["html", "head", "body", "frameset", "frame"];

/// The attribute Vue reads to allow a hydration mismatch. The browser
/// runtime empties every element carrying it, so trusted HTML must not.
const ALLOW_MISMATCH_ATTRIBUTE: &str = "data-allow-mismatch";

/// Check how the browser parses `html` written inside the open elements
/// `open` (outermost first, all inside the Vue host `div`), and return what
/// it creates there, or `None` when the page's parse would differ from the
/// block's own `<template>` parse or the block holds something `usage`
/// does not allow.
///
/// The check holds for any page in which every node written before the
/// block was kept where it was written: the parser's state then depends only
/// on the names of the open elements (see `hydration_nesting`). It relies on
/// html5ever as the reference parser, so what html5ever does not model is
/// rejected instead of compared: declarative shadow roots, and `<html>`,
/// `<head>`, `<body>` and frame tags, whose attributes the page's parse
/// copies onto the document's own elements. It also
/// confirms that the parser is back in that state after the block (every
/// element the block opened is closed, and no formatting element is left to
/// be reopened), so the page's own check can treat the block as absent.
///
/// Every `usage` rejects a block that holds a `<script>` or `<noscript>`
/// element or a `data-allow-mismatch` attribute: the browser runs a served
/// script while it parses the page, while Vue inserts the same HTML without
/// running it, and parses `<noscript>` differently inside `<template>`.
/// [`StaticHtmlUse::Adopted`] also rejects a block whose first node is a
/// comment (Vue's static hydration only starts at an element or a text) or
/// that holds one of Vue's Fragment comments at its top level.
/// [`StaticHtmlUse::Replaced`] rejects elements and attributes that would run
/// or load twice ([`REPLACED_UNSAFE_TAGS`], [`REPLACED_UNSAFE_ATTRIBUTES`],
/// `on*` handlers, custom elements).
pub fn static_html_in_context(
    open: &[&str],
    html: &str,
    usage: StaticHtmlUse,
) -> Option<StaticHtmlFacts> {
    // Tokenizing the block costs a parse, so it runs only when one of the
    // names appears at all.
    let lowered = html.to_ascii_lowercase();
    if DOCUMENT_TAGS
        .iter()
        .any(|tag| lowered.contains(&format!("<{tag}")))
        && scan_output_html(html)
            .iter()
            .any(|tag| DOCUMENT_TAGS.contains(&tag.name.to_ascii_lowercase().as_str()))
    {
        return None;
    }
    let (_reference_dom, reference) = parse_children(html, "template")?;
    let mut element_count = 0;
    for node in &reference {
        if !allowed(node, usage, &mut element_count) {
            return None;
        }
    }
    if usage == StaticHtmlUse::Adopted {
        if reference.first().is_some_and(|node| {
            !matches!(node.data, NodeData::Element { .. } | NodeData::Text { .. })
        }) {
            return None;
        }
        // Vue finds the end of the block's Fragment by counting these
        // comments among its siblings.
        if reference.iter().any(|node| {
            matches!(&node.data, NodeData::Comment { contents } if matches!(&**contents, "[" | "]"))
        }) {
            return None;
        }
    }
    let parent = open.last().copied().unwrap_or("div");
    // The text after the block would take on any formatting element the
    // block left open to be reopened. The parser moves other text out of
    // table parts, so there the probe is a space.
    let probe = if matches!(
        parent,
        "table" | "thead" | "tbody" | "tfoot" | "tr" | "colgroup"
    ) {
        " "
    } else {
        "x"
    };
    let mut page = String::with_capacity(html.len() + open.len() * 16 + 32);
    for tag in open {
        page.push('<');
        page.push_str(tag);
        page.push('>');
    }
    // The comments keep the block's first and last text apart from the
    // text around it, as Vue's Fragment comments do in the page.
    page.push_str("<!--[-->");
    page.push_str(html);
    page.push_str("<!--]-->");
    page.push_str(probe);
    for tag in open.iter().rev() {
        page.push_str("</");
        page.push_str(tag);
        page.push('>');
    }
    let (_page_dom, mut children) = parse_children(&page, "div")?;
    for tag in open {
        // Each open element must hold only the next one: anything else
        // means the parser closed or moved something around the block.
        let [only] = children.as_slice() else {
            return None;
        };
        let inner = match &only.data {
            NodeData::Element { name, attrs, .. }
                if name.ns == ns!(html)
                    && name.local.as_ref() == *tag
                    && attrs.borrow().is_empty() =>
            {
                only.children.borrow().clone()
            }
            _ => return None,
        };
        children = inner;
    }
    let [start, block @ .., end, tail] = children.as_slice() else {
        return None;
    };
    let comment_is = |node: &Handle, data: &str| matches!(&node.data, NodeData::Comment { contents } if &**contents == data);
    let tail_is_probe =
        matches!(&tail.data, NodeData::Text { contents } if &**contents.borrow() == probe);
    if !comment_is(start, "[") || !comment_is(end, "]") || !tail_is_probe {
        return None;
    }
    if block.len() != reference.len()
        || !block
            .iter()
            .zip(&reference)
            .all(|(actual, expected)| same_tree(actual, expected))
    {
        return None;
    }
    Some(StaticHtmlFacts {
        node_count: reference.len(),
        element_count,
    })
}

/// Whether a node of the block's `<template>` parse may be written for
/// `usage`, counting its elements.
fn allowed(node: &Handle, usage: StaticHtmlUse, element_count: &mut usize) -> bool {
    match &node.data {
        NodeData::Text { .. } | NodeData::Comment { .. } => true,
        NodeData::Element {
            name,
            attrs,
            template_contents,
            ..
        } => {
            *element_count += 1;
            let tag = name.local.as_ref();
            if tag == "script" || tag == "noscript" {
                return false;
            }
            let attrs = attrs.borrow();
            if attrs
                .iter()
                .any(|attr| attr.name.local.as_ref() == ALLOW_MISMATCH_ATTRIBUTE)
            {
                return false;
            }
            // html5ever does not model declarative shadow roots: the page's
            // parse attaches one to the parent element instead of keeping the
            // `<template>`, so the node count and the parent's children differ.
            if tag == "template"
                && attrs
                    .iter()
                    .any(|attr| matches!(attr.name.local.as_ref(), "shadowrootmode" | "shadowroot"))
            {
                return false;
            }
            if usage == StaticHtmlUse::Replaced
                && ((name.ns == ns!(html)
                    && (REPLACED_UNSAFE_TAGS.contains(&tag) || tag.contains('-')))
                    || attrs.iter().any(|attr| {
                        let attr = attr.name.local.as_ref();
                        attr.get(..2)
                            .is_some_and(|start| start.eq_ignore_ascii_case("on"))
                            || REPLACED_UNSAFE_ATTRIBUTES.contains(&attr)
                    }))
            {
                return false;
            }
            let contents = template_contents.borrow();
            let children = match contents.as_ref() {
                Some(fragment) => fragment.children.borrow().clone(),
                None => Vec::new(),
            };
            children
                .iter()
                .chain(node.children.borrow().iter())
                .all(|child| allowed(child, usage, element_count))
        }
        _ => false,
    }
}

/// Whether two parsed nodes are the same tree: names, attributes in order,
/// texts, comments, and `<template>` contents.
fn same_tree(actual: &Handle, expected: &Handle) -> bool {
    let same_children = |a: &Handle, b: &Handle| {
        let a = a.children.borrow();
        let b = b.children.borrow();
        a.len() == b.len() && a.iter().zip(b.iter()).all(|(a, b)| same_tree(a, b))
    };
    match (&actual.data, &expected.data) {
        (NodeData::Text { contents: a }, NodeData::Text { contents: b }) => {
            *a.borrow() == *b.borrow()
        }
        (NodeData::Comment { contents: a }, NodeData::Comment { contents: b }) => a == b,
        (
            NodeData::Element {
                name: a_name,
                attrs: a_attrs,
                template_contents: a_template,
                mathml_annotation_xml_integration_point: a_point,
            },
            NodeData::Element {
                name: b_name,
                attrs: b_attrs,
                template_contents: b_template,
                mathml_annotation_xml_integration_point: b_point,
            },
        ) => {
            let same_template = match (&*a_template.borrow(), &*b_template.borrow()) {
                (None, None) => true,
                (Some(a), Some(b)) => same_children(a, b),
                _ => false,
            };
            a_name == b_name
                && a_point == b_point
                && *a_attrs.borrow() == *b_attrs.borrow()
                && same_template
                && same_children(actual, expected)
        }
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::{static_html_in_context, static_html_node_count, StaticHtmlFacts, StaticHtmlUse};

    fn adopted(open: &[&str], html: &str) -> Option<StaticHtmlFacts> {
        static_html_in_context(open, html, StaticHtmlUse::Adopted)
    }

    fn facts(node_count: usize, element_count: usize) -> Option<StaticHtmlFacts> {
        Some(StaticHtmlFacts {
            node_count,
            element_count,
        })
    }

    #[test]
    fn counts_top_level_texts_comments_and_elements() {
        assert_eq!(static_html_node_count(""), 0);
        assert_eq!(static_html_node_count("   "), 1);
        assert_eq!(static_html_node_count("a &amp; b"), 1);
        assert_eq!(static_html_node_count("<b>x</b>"), 1);
        assert_eq!(static_html_node_count("lead <b>x</b> tail"), 3);
        assert_eq!(static_html_node_count("<b>x</b><!-- c --><i>y</i>"), 3);
        // Table parts stay where the `<template>` parse puts them.
        assert_eq!(static_html_node_count("<tr><td>1</td></tr><tr></tr>"), 2);
    }

    #[test]
    fn a_block_the_page_keeps_reports_its_nodes() {
        assert_eq!(adopted(&["main", "p"], "lead <b>x</b> tail"), facts(3, 1));
        assert_eq!(adopted(&["div"], "<b>x</b><!-- note -->"), facts(2, 1));
        assert_eq!(adopted(&["div"], "   "), facts(1, 0));
        assert_eq!(adopted(&["div"], "a &amp; b &lt;c&gt;"), facts(1, 0));
        assert_eq!(adopted(&["span"], "<em>a<b>b</b></em>"), facts(1, 2));
        assert_eq!(adopted(&[], "<section>x</section>"), facts(1, 1));
        assert_eq!(
            adopted(&["div"], r#"<svg viewBox="0 0 1 1"><path d="M0 0"/></svg>"#),
            facts(1, 2)
        );
        assert_eq!(adopted(&["div"], "<pre>\nkept</pre>"), facts(1, 1));
        assert_eq!(
            adopted(&["table", "tbody"], "<tr><td>1</td></tr>"),
            facts(1, 2)
        );
        assert_eq!(
            adopted(&["select"], "<option>a</option><option>b</option>"),
            facts(2, 2)
        );
        assert_eq!(adopted(&["div"], ""), facts(0, 0));
    }

    #[test]
    fn a_block_the_page_would_repair_is_rejected() {
        // A paragraph inside an open paragraph closes it.
        assert_eq!(adopted(&["p"], "<p>inner</p>"), None);
        assert_eq!(adopted(&["p", "span"], "<div>x</div>"), None);
        // A row outside a table, and text inside a table, move.
        assert_eq!(adopted(&["div"], "<tr><td>1</td></tr>"), None);
        assert_eq!(adopted(&["table"], "text"), None);
        // A nested link or form is closed or dropped.
        assert_eq!(adopted(&["a"], "<a href=\"/x\">x</a>"), None);
        // An unclosed formatting element would be reopened after the block.
        assert_eq!(adopted(&["div"], "<b>open"), None);
        // A stray end tag closes the element around the block.
        assert_eq!(adopted(&["div", "span"], "x</span>y"), None);
    }

    #[test]
    fn blocks_vue_or_the_page_cannot_use_are_rejected() {
        assert_eq!(adopted(&["div"], "<!-- first -->x"), None);
        assert_eq!(adopted(&["div"], "x<!--[-->y"), None);
        assert_eq!(adopted(&["div"], "<b>x</b><script>run()</script>"), None);
        assert_eq!(adopted(&["div"], "<noscript><b>x</b></noscript>"), None);
        assert_eq!(adopted(&["div"], "<i data-allow-mismatch>x</i>"), None);
        // An inner Fragment comment is not among the block's siblings.
        assert_eq!(adopted(&["div"], "<b><!--[-->x</b>"), facts(1, 1));
    }

    #[test]
    fn what_the_reference_parser_cannot_model_is_rejected() {
        // A declarative shadow root attaches to the parent in the page.
        assert_eq!(
            adopted(
                &["div"],
                r#"<template shadowrootmode="open"><b>x</b></template>tail"#
            ),
            None
        );
        // `<body>` and `<html>` copy their attributes onto the page's own
        // elements, which neither parse compared here shows.
        assert_eq!(
            adopted(&["div"], r#"<body onload="f()"><p>x</p></body>"#),
            None
        );
        assert_eq!(adopted(&["div"], r#"<html lang="fr"><p>x</p>"#), None);
        assert_eq!(adopted(&["div"], "<head></head><p>x</p>"), None);
        // An ordinary template is kept.
        assert_eq!(
            adopted(&["div"], "<template><b>x</b></template>"),
            facts(1, 2)
        );
    }

    #[test]
    fn shell_content_rejects_what_would_run_or_load_twice() {
        let replaced = |html| static_html_in_context(&["div"], html, StaticHtmlUse::Replaced);
        assert_eq!(replaced("<!-- c --><b>x</b>"), facts(2, 1));
        assert_eq!(replaced(r#"<img src="/a.png" onerror="f()">"#), None);
        assert_eq!(replaced(r#"<input autofocus>"#), None);
        assert_eq!(replaced(r#"<video autoplay src="/v.mp4"></video>"#), None);
        assert_eq!(replaced(r#"<iframe src="/f"></iframe>"#), None);
        assert_eq!(replaced(r#"<my-widget></my-widget>"#), None);
        assert_eq!(replaced(r#"<svg onload="f()"></svg>"#), None);
        assert_eq!(replaced(r#"<button is="fancy-button">x</button>"#), None);
        assert_eq!(
            replaced(r#"<video preload="auto" src="/v.mp4"></video>"#),
            None
        );
        // The same attributes are fine where Vue adopts the served element.
        assert_eq!(
            adopted(&["div"], r#"<img src="/a.png" onerror="f()">"#),
            facts(1, 1)
        );
    }
}
