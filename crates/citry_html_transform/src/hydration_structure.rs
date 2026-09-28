//! Compare selected Vue-owned element boundaries with the browser's HTML tree.

use html5ever::{namespace_url, ns, Attribute};
use markup5ever_rcdom::{Handle, NodeData};
use std::collections::HashMap;

use crate::output_scanner::{parse_div_fragment_with_lexical_text, LexicalTextRun};

/// The attribute Vue reads to allow a hydration mismatch inside an element.
const ALLOW_MISMATCH_ATTRIBUTE: &str = "data-allow-mismatch";

/// The only comments Vue's server renderer writes as hydration anchors:
/// fragment start and end, an empty `v-if` branch, and an empty component.
const VUE_ANCHOR_COMMENTS: [&str; 4] = ["[", "]", "v-if", ""];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExpectedElementEvent {
    pub opening: bool,
    pub tag: String,
    pub attributes: Vec<(String, Option<String>)>,
}

/// One node boundary the caller expects the browser to construct, in
/// document order.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ExpectedNodeEvent {
    /// An element whose children follow as further events, then `Close`.
    Open {
        tag: String,
        attributes: Vec<(String, Option<String>)>,
    },
    /// The end of the most recent unclosed `Open` element.
    Close { tag: String },
    /// An element the server writes empty so Vue builds its contents in the
    /// browser. Its tag and attributes are compared, its attributes must carry
    /// `data-allow-mismatch="children"`, and the browser must build it with no
    /// child nodes. A `Close` does not follow it.
    Shell {
        tag: String,
        attributes: Vec<(String, Option<String>)>,
    },
    /// One of Vue's anchor comments (`[`, `]`, `v-if`, or empty).
    Comment { data: String },
    /// Whitespace-only text directly inside the fragment root.
    RootText { value: String },
}

/// Check one emitted HTML fragment in its actual insertion context.
///
/// This feeds one tokenizer into html5ever's tree builder, then compares both
/// element facts and the parent/position of decoded source text. The caller's
/// separate compiler/source proof still establishes which text Vue expects.
/// The first admission admits HTML-namespace elements under a `div` host.
///
/// This form accepts elements only: any comment or non-empty text at the
/// fragment root rejects the fragment. [`browser_fragment_matches_nodes`]
/// also accepts expected comments, root text, and shell elements.
pub fn browser_fragment_matches_elements(
    html: &str,
    context: &str,
    expected: &[ExpectedElementEvent],
) -> bool {
    let nodes = expected
        .iter()
        .map(|event| {
            if event.opening {
                ExpectedNodeEvent::Open {
                    tag: event.tag.clone(),
                    attributes: event.attributes.clone(),
                }
            } else if event.attributes.is_empty() {
                ExpectedNodeEvent::Close {
                    tag: event.tag.clone(),
                }
            } else {
                // A closing event never carries attributes. Keep the old
                // rejection by turning it into an event nothing can match.
                ExpectedNodeEvent::Comment {
                    data: "\u{0}".to_owned(),
                }
            }
        })
        .collect::<Vec<_>>();
    browser_fragment_matches_nodes(html, context, &nodes)
}

/// Check one emitted HTML fragment against expected elements, Vue anchor
/// comments, root whitespace, and shell elements.
///
/// Every comment and every root-level text node the browser constructs must
/// match the next expected event exactly; an unexpected one rejects the
/// fragment. Root text must be whitespace-only. A shell element must be
/// empty: Vue lets every mismatch under it pass silently, so content there
/// would never be checked by anyone.
pub fn browser_fragment_matches_nodes(
    html: &str,
    context: &str,
    expected: &[ExpectedNodeEvent],
) -> bool {
    if context != "div" || expected.is_empty() || !expected_events_are_well_formed(expected) {
        return false;
    }
    let Some((dom, lexical_text)) = parse_div_fragment_with_lexical_text(html) else {
        return false;
    };
    let roots = dom.document.children.borrow();
    if roots.len() != 1 {
        return false;
    }
    let mut walk = Walk {
        expected,
        position: 0,
        next_open_id: 1,
        text_runs: Vec::new(),
    };
    let accepted = match &roots[0].data {
        NodeData::Element { name, .. } if name.ns == ns!(html) && name.local.as_ref() == "html" => {
            walk.visit_children(&roots[0], 0, true)
        }
        _ => false,
    };
    accepted && walk.position == expected.len() && walk.text_runs == lexical_text
}

/// Reject event lists whose shape no fragment could satisfy, so the walk
/// below can rely on them.
fn expected_events_are_well_formed(expected: &[ExpectedNodeEvent]) -> bool {
    let mut open: Vec<&str> = Vec::new();
    for event in expected {
        match event {
            ExpectedNodeEvent::Open { tag, attributes } => {
                // A marker on an element whose children are compared would
                // tell Vue to ignore mismatches inside checked content.
                if has_allow_mismatch(attributes) {
                    return false;
                }
                open.push(tag);
            }
            ExpectedNodeEvent::Close { tag } => {
                if open.pop() != Some(tag.as_str()) {
                    return false;
                }
            }
            ExpectedNodeEvent::Shell { attributes, .. } => {
                let markers = attributes
                    .iter()
                    .filter(|(name, _)| name == ALLOW_MISMATCH_ATTRIBUTE)
                    .collect::<Vec<_>>();
                if markers.len() != 1 || markers[0].1.as_deref() != Some("children") {
                    return false;
                }
            }
            ExpectedNodeEvent::Comment { data } => {
                if !VUE_ANCHOR_COMMENTS.contains(&data.as_str()) {
                    return false;
                }
            }
            ExpectedNodeEvent::RootText { value } => {
                if !open.is_empty() || value.is_empty() || !value.chars().all(is_html_whitespace) {
                    return false;
                }
            }
        }
    }
    open.is_empty()
}

fn has_allow_mismatch(attributes: &[(String, Option<String>)]) -> bool {
    attributes
        .iter()
        .any(|(name, _)| name == ALLOW_MISMATCH_ATTRIBUTE)
}

fn is_html_whitespace(value: char) -> bool {
    matches!(value, ' ' | '\t' | '\n' | '\u{c}')
}

struct Walk<'a> {
    expected: &'a [ExpectedNodeEvent],
    position: usize,
    next_open_id: usize,
    text_runs: Vec<LexicalTextRun>,
}

impl Walk<'_> {
    fn visit_children(
        &mut self,
        parent: &Handle,
        parent_open: usize,
        at_fragment_root: bool,
    ) -> bool {
        let children = parent.children.borrow();
        let mut child_index = 0;
        let mut last_was_text = false;
        for child in children.iter() {
            match &child.data {
                NodeData::Element { name, attrs, .. } => {
                    let open_id = self.next_open_id;
                    self.next_open_id += 1;
                    child_index += 1;
                    last_was_text = false;
                    if name.ns != ns!(html) || name.local.as_ref() == "template" {
                        return false;
                    }
                    let (shell, attributes) = match self.expected.get(self.position) {
                        Some(ExpectedNodeEvent::Open { tag, attributes })
                            if tag == name.local.as_ref() =>
                        {
                            (false, attributes)
                        }
                        Some(ExpectedNodeEvent::Shell { tag, attributes })
                            if tag == name.local.as_ref() =>
                        {
                            (true, attributes)
                        }
                        _ => return false,
                    };
                    if !attributes_match(&attrs.borrow(), attributes) {
                        return false;
                    }
                    self.position += 1;
                    if shell {
                        // Vue builds a shell's contents in the browser and
                        // hides any mismatch under it, so the written shell
                        // must be empty for nothing to escape this check.
                        if !child.children.borrow().is_empty() {
                            return false;
                        }
                        continue;
                    }
                    if !self.visit_children(child, open_id, false) {
                        return false;
                    }
                    match self.expected.get(self.position) {
                        Some(ExpectedNodeEvent::Close { tag }) if tag == name.local.as_ref() => {}
                        _ => return false,
                    }
                    self.position += 1;
                }
                NodeData::Text { contents } => {
                    let value = contents.borrow();
                    if value.is_empty() {
                        continue;
                    }
                    if at_fragment_root {
                        // Text directly in the host must be expected exactly,
                        // or Vue would meet a text node where it wants a vnode.
                        match self.expected.get(self.position) {
                            Some(ExpectedNodeEvent::RootText { value: expected })
                                if !last_was_text && expected.as_str() == &**value => {}
                            _ => return false,
                        }
                        self.position += 1;
                    }
                    if last_was_text {
                        self.text_runs
                            .last_mut()
                            .expect("adjacent text exists")
                            .value
                            .push_str(&value);
                    } else {
                        self.text_runs.push(LexicalTextRun {
                            parent_open,
                            child_index,
                            value: value.to_string(),
                        });
                        child_index += 1;
                        last_was_text = true;
                    }
                }
                NodeData::Comment { contents } => {
                    match self.expected.get(self.position) {
                        Some(ExpectedNodeEvent::Comment { data })
                            if data.as_str() == &**contents => {}
                        _ => return false,
                    }
                    self.position += 1;
                    // The tokenizer counts a comment as one child, so text on
                    // either side keeps its own sibling position.
                    child_index += 1;
                    last_was_text = false;
                }
                _ => return false,
            }
        }
        true
    }
}

fn attributes_match(actual: &[Attribute], expected: &[(String, Option<String>)]) -> bool {
    let mut expected_attrs = HashMap::with_capacity(expected.len());
    // A duplicate expected name has no single browser value to compare.
    if expected.iter().any(|(key, value)| {
        expected_attrs
            .insert(key.as_str(), value.as_deref().unwrap_or(""))
            .is_some()
    }) {
        return false;
    }
    actual.len() == expected_attrs.len()
        && actual.iter().all(|attr| {
            attr.name.ns == ns!()
                && expected_attrs.get(attr.name.local.as_ref()).copied()
                    == Some(attr.value.as_ref())
        })
}

#[cfg(test)]
mod tests {
    use super::{
        browser_fragment_matches_elements, browser_fragment_matches_nodes, ExpectedElementEvent,
        ExpectedNodeEvent,
    };

    fn event(opening: bool, tag: &str) -> ExpectedElementEvent {
        ExpectedElementEvent {
            opening,
            tag: tag.to_owned(),
            attributes: Vec::new(),
        }
    }

    #[test]
    fn compares_constructed_tree_not_source_tag_stack() {
        let normal = [
            event(true, "main"),
            event(true, "p"),
            event(false, "p"),
            event(false, "main"),
        ];
        assert!(browser_fragment_matches_elements(
            "<main><p>A</p></main>",
            "div",
            &normal
        ));
        let repaired = [
            event(true, "p"),
            event(true, "div"),
            event(false, "div"),
            event(false, "p"),
        ];
        assert!(!browser_fragment_matches_elements(
            "<p><div>A</div></p>",
            "div",
            &repaired
        ));
        let table = [
            event(true, "table"),
            event(true, "tr"),
            event(false, "tr"),
            event(false, "table"),
        ];
        assert!(!browser_fragment_matches_elements(
            "<table><tr></tr></table>",
            "div",
            &table
        ));
    }

    #[test]
    fn rejects_duplicate_expected_attributes_and_template_contents() {
        let duplicates = [
            ExpectedElementEvent {
                opening: true,
                tag: "main".to_owned(),
                attributes: vec![
                    ("id".to_owned(), Some("x".to_owned())),
                    ("id".to_owned(), Some("x".to_owned())),
                ],
            },
            event(false, "main"),
        ];
        assert!(!browser_fragment_matches_elements(
            "<main id=x class=y></main>",
            "div",
            &duplicates
        ));
        let template = [event(true, "template"), event(false, "template")];
        assert!(!browser_fragment_matches_elements(
            "<template><p>hidden</p></template>",
            "div",
            &template
        ));
    }

    #[test]
    fn compares_decoded_text_parent_and_sibling_position() {
        let simple = [
            event(true, "main"),
            event(true, "span"),
            event(false, "span"),
            event(true, "em"),
            event(false, "em"),
            event(false, "main"),
        ];
        assert!(browser_fragment_matches_elements(
            "<main><span>A &amp; B</span><em>C</em>tail</main>",
            "div",
            &simple,
        ));
        let table = [
            event(true, "main"),
            event(true, "table"),
            event(true, "tbody"),
            event(true, "tr"),
            event(true, "td"),
            event(false, "td"),
            event(false, "tr"),
            event(false, "tbody"),
            event(false, "table"),
            event(false, "main"),
        ];
        assert!(browser_fragment_matches_elements(
            "<main><table><tbody><tr><td>x</td></tr></tbody></table></main>",
            "div",
            &table,
        ));
        assert!(!browser_fragment_matches_elements(
            "<main><table>moved<tbody><tr><td>x</td></tr></tbody></table></main>",
            "div",
            &table,
        ));
    }

    fn open(tag: &str) -> ExpectedNodeEvent {
        ExpectedNodeEvent::Open {
            tag: tag.to_owned(),
            attributes: Vec::new(),
        }
    }

    fn close(tag: &str) -> ExpectedNodeEvent {
        ExpectedNodeEvent::Close {
            tag: tag.to_owned(),
        }
    }

    fn comment(data: &str) -> ExpectedNodeEvent {
        ExpectedNodeEvent::Comment {
            data: data.to_owned(),
        }
    }

    fn shell(tag: &str) -> ExpectedNodeEvent {
        ExpectedNodeEvent::Shell {
            tag: tag.to_owned(),
            attributes: vec![(
                "data-allow-mismatch".to_owned(),
                Some("children".to_owned()),
            )],
        }
    }

    #[test]
    fn accepts_vue_anchor_comments_only_in_expected_order() {
        let html = "<main><!--[--><p>a</p><!--v-if--><!----><!--]--></main>";
        let events = [
            open("main"),
            comment("["),
            open("p"),
            close("p"),
            comment("v-if"),
            comment(""),
            comment("]"),
            close("main"),
        ];
        assert!(browser_fragment_matches_nodes(html, "div", &events));

        // The same comments in a different order are a different Vue tree.
        let swapped = [
            open("main"),
            comment("["),
            open("p"),
            close("p"),
            comment(""),
            comment("v-if"),
            comment("]"),
            close("main"),
        ];
        assert!(!browser_fragment_matches_nodes(html, "div", &swapped));

        // A comment the browser builds but the caller did not expect.
        let missing = [
            open("main"),
            comment("["),
            open("p"),
            close("p"),
            comment("]"),
            close("main"),
        ];
        assert!(!browser_fragment_matches_nodes(html, "div", &missing));

        // An expected comment the HTML does not contain.
        let extra = [
            open("main"),
            comment("["),
            open("p"),
            close("p"),
            comment("v-if"),
            comment(""),
            comment("]"),
            comment("v-if"),
            close("main"),
        ];
        assert!(!browser_fragment_matches_nodes(html, "div", &extra));

        // Only Vue's own anchors are admissible comments.
        let other = [open("main"), comment("note"), close("main")];
        assert!(!browser_fragment_matches_nodes(
            "<main><!--note--></main>",
            "div",
            &other
        ));
    }

    #[test]
    fn comments_split_text_positions_like_the_tokenizer() {
        let events = [open("p"), comment("v-if"), close("p")];
        assert!(browser_fragment_matches_nodes(
            "<p>a<!--v-if-->b</p>",
            "div",
            &events
        ));
        // The element-only form keeps rejecting every comment.
        let elements = [
            ExpectedElementEvent {
                opening: true,
                tag: "p".to_owned(),
                attributes: Vec::new(),
            },
            ExpectedElementEvent {
                opening: false,
                tag: "p".to_owned(),
                attributes: Vec::new(),
            },
        ];
        assert!(!browser_fragment_matches_elements(
            "<p>a<!--v-if-->b</p>",
            "div",
            &elements
        ));
    }

    #[test]
    fn root_text_must_be_expected_and_whitespace_only() {
        let root_text = |value: &str| ExpectedNodeEvent::RootText {
            value: value.to_owned(),
        };
        let events = [
            comment("["),
            open("p"),
            close("p"),
            root_text("\n  "),
            open("p"),
            close("p"),
            comment("]"),
        ];
        assert!(browser_fragment_matches_nodes(
            "<!--[--><p></p>\n  <p></p><!--]-->",
            "div",
            &events
        ));
        // Unexpected root whitespace is a text node Vue does not expect.
        let without_text = [
            comment("["),
            open("p"),
            close("p"),
            open("p"),
            close("p"),
            comment("]"),
        ];
        assert!(!browser_fragment_matches_nodes(
            "<!--[--><p></p>\n  <p></p><!--]-->",
            "div",
            &without_text
        ));
        // Non-whitespace root text is never admissible.
        let words = [open("p"), close("p"), root_text("x")];
        assert!(!browser_fragment_matches_nodes("<p></p>x", "div", &words));
        // Root text is only a root-level event.
        let nested = [open("p"), root_text(" "), close("p")];
        assert!(!browser_fragment_matches_nodes("<p> </p>", "div", &nested));
    }

    #[test]
    fn shells_must_be_empty_and_keep_their_own_opening() {
        let events = [
            open("main"),
            shell("aside"),
            open("section"),
            close("section"),
            close("main"),
        ];
        assert!(browser_fragment_matches_nodes(
            "<main><aside data-allow-mismatch=\"children\"></aside><section>x</section></main>",
            "div",
            &events
        ));
        // Written content under a shell would never be checked by Vue.
        assert!(!browser_fragment_matches_nodes(
            "<main><aside data-allow-mismatch=\"children\"><p title=\"wrong\">zz</p></aside><section>x</section></main>",
            "div",
            &events
        ));
        assert!(!browser_fragment_matches_nodes(
            "<main><aside data-allow-mismatch=\"children\"><!--[--></aside><section>x</section></main>",
            "div",
            &events
        ));
        // The shell's own attributes are still compared exactly.
        assert!(!browser_fragment_matches_nodes(
            "<main><aside data-allow-mismatch=\"children\" id=x></aside><section>x</section></main>",
            "div",
            &events
        ));
        // Unproven contents that the parser moves out of the shell show up
        // as siblings the caller did not expect.
        let paragraph = [open("main"), shell("p"), close("main")];
        assert!(!browser_fragment_matches_nodes(
            "<main><p data-allow-mismatch=\"children\"><div>moved</div></p></main>",
            "div",
            &paragraph
        ));
    }

    #[test]
    fn allow_mismatch_marker_is_only_valid_on_shells() {
        let marker = (
            "data-allow-mismatch".to_owned(),
            Some("children".to_owned()),
        );
        // A marked element whose children are compared would hide their
        // mismatches from Vue, so the event list itself is rejected.
        let container = [
            ExpectedNodeEvent::Open {
                tag: "main".to_owned(),
                attributes: vec![marker.clone()],
            },
            open("p"),
            close("p"),
            close("main"),
        ];
        assert!(!browser_fragment_matches_nodes(
            "<main data-allow-mismatch=\"children\"><p></p></main>",
            "div",
            &container
        ));
        // A shell without the marker, or with another mismatch kind, is not
        // a shell Vue will fill without reporting a mismatch.
        let unmarked = [ExpectedNodeEvent::Shell {
            tag: "main".to_owned(),
            attributes: Vec::new(),
        }];
        assert!(!browser_fragment_matches_nodes(
            "<main></main>",
            "div",
            &unmarked
        ));
        let wrong_kind = [ExpectedNodeEvent::Shell {
            tag: "main".to_owned(),
            attributes: vec![("data-allow-mismatch".to_owned(), Some("text".to_owned()))],
        }];
        assert!(!browser_fragment_matches_nodes(
            "<main data-allow-mismatch=\"text\"></main>",
            "div",
            &wrong_kind
        ));
        // A shell is a complete element, so a close after it is unbalanced.
        let closed_shell = [shell("main"), close("main")];
        assert!(!browser_fragment_matches_nodes(
            "<main data-allow-mismatch=\"children\"></main>",
            "div",
            &closed_shell
        ));
    }
}
