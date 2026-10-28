//! How deeply a template may nest its tags, and how each tag counts.
//!
//! The parser, the compiler and the Python binding all walk a template's
//! tree, and the Python runtime walks what the compiler generates. Each of
//! those walks has a cost per level, so a template can nest at most
//! [`MAX_TAG_NESTING`] tags of any kind and at most [`MAX_LOGIC_NESTING`] of
//! Citry's logic tags. Both are fixed constants, not settings, so a template
//! that is valid in one process is valid in every process.
//!
//! A tag adds one total level for itself, and one more for each control-flow
//! shorthand attribute on it (`c-if=`, `c-elif=`, `c-else`, `c-for=`,
//! `c-empty`), because the compiler wraps the tag in one control-flow node
//! per shorthand. Logic levels are those wrappers, plus one for the tag itself
//! when it is a Citry tag other than `<c-raw>`: control flow, `<c-slot>`,
//! `<c-fill>`, and every component tag, `<c-component>` and `<c-element>`
//! included. The parser and the compiler count with [`tag_levels`], so they
//! agree exactly at the limit.

use crate::ast::{HtmlStartTag, Node, Template, TemplateElement, Token};
use crate::constants::{has_citry_component_prefix, CONTROL_FLOW_TAGS, C_RAW_TAG};

/// The most tags of any kind a template can nest.
///
/// Most of the Python runtime renders plain elements without a Python call
/// per level, so this limit mainly protects the Rust walks and other readers
/// of the tree. Blink's HTML parser also stops nesting at 512, so deeper
/// markup would not reach the browser as nested elements anyway.
pub const MAX_TAG_NESTING: usize = 512;

/// The most Citry logic tags and shorthand wrappers a template can nest.
///
/// The Python walkers over template bodies keep their own lists of what to
/// visit, so most of them use the same number of Python frames at any depth,
/// and a frame-budget test checks that a template at this depth renders well
/// within Python's default recursion limit. One exception is the code
/// generated to render a `simple='vue'` component, which still uses about
/// one Python frame per level. The limit is checked per template, so a
/// chain of components that pass slot content on to each other is not
/// bounded by it (both are #299). The limit must stay below
/// [`MAX_TAG_NESTING`], or it could never be reached.
pub const MAX_LOGIC_NESTING: usize = 256;

/// A nesting depth, in tags of any kind and in logic levels.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct NestingDepth {
    /// Tags of any kind, shorthand wrappers included.
    pub total: usize,
    /// Citry logic tags and shorthand wrappers.
    pub logic: usize,
}

impl NestingDepth {
    /// The depth after one more tag that adds `levels`.
    pub fn plus(self, levels: NestingDepth) -> NestingDepth {
        NestingDepth {
            total: self.total + levels.total,
            logic: self.logic + levels.logic,
        }
    }
}

/// Whether a tag counts as a logic level by itself, without its shorthands.
pub fn is_logic_tag(tag_name: &str) -> bool {
    has_citry_component_prefix(tag_name) && tag_name != C_RAW_TAG
}

/// How many levels a tag with this name and these attribute names adds.
pub fn tag_levels<'a>(tag_name: &str, attr_names: impl Iterator<Item = &'a str>) -> NestingDepth {
    // The compiler wraps a tag in one control-flow node for each attribute
    // named like a control-flow tag, so each of those is a level.
    let shorthands = attr_names
        .filter(|name| CONTROL_FLOW_TAGS.contains(name))
        .count();
    NestingDepth {
        total: 1 + shorthands,
        logic: usize::from(is_logic_tag(tag_name)) + shorthands,
    }
}

/// How many levels a parsed start tag adds.
pub fn start_tag_levels(start_tag: &HtmlStartTag) -> NestingDepth {
    tag_levels(
        &start_tag.name.content,
        start_tag.attrs.iter().map(|attr| attr.key.content.as_str()),
    )
}

/// The error message for a tag at `depth`, or `None` when it is within both
/// limits. The logic limit is checked first: a template that hits it has
/// usually not hit the total one, and the logic message names the cause.
pub fn too_deep_message(tag_name: &str, depth: NestingDepth) -> Option<String> {
    if depth.logic > MAX_LOGIC_NESTING {
        return Some(format!(
            "This <{tag_name}> is {} Citry logic levels deep. Every c- tag except \
             <c-raw> is one logic level, and so is each c-if=, c-elif=, c-else, \
             c-for= or c-empty attribute. A template can nest at most \
             {MAX_LOGIC_NESTING} logic levels and {MAX_TAG_NESTING} levels of any \
             kind. To go deeper, move the inner part into its own component.",
            depth.logic
        ));
    }
    if depth.total > MAX_TAG_NESTING {
        return Some(format!(
            "This <{tag_name}> is nested {} levels deep. Every tag is one level, \
             and so is each c-if=, c-elif=, c-else, c-for= or c-empty attribute. \
             A template can nest at most {MAX_TAG_NESTING} levels of any kind and \
             {MAX_LOGIC_NESTING} Citry logic levels. To go deeper, move the inner \
             part into its own component.",
            depth.total
        ));
    }
    None
}

/// Find the first tag in `template`, in source order, that nests past a
/// limit, with its message.
///
/// This walks the tree with a loop instead of recursion, so it can check a
/// tree of any depth, including one built by hand rather than by the parser,
/// before anything clones or walks it recursively.
pub fn first_too_deep_tag(template: &Template) -> Option<(&Token, String)> {
    // Each entry is a body partway through, and the depth of the tags around
    // it. A body is entered as soon as its tag is reached, so tags are checked
    // in source order and the first one past a limit is the one reported.
    let mut pending: Vec<(std::slice::Iter<'_, TemplateElement>, NestingDepth)> =
        vec![(template.elements.iter(), NestingDepth::default())];
    while let Some((elements, depth)) = pending.last_mut() {
        let depth = *depth;
        let Some(element) = elements.next() else {
            pending.pop();
            continue;
        };
        let TemplateElement::Node(node) = element else {
            continue;
        };
        let start_tag = node.start_tag();
        let here = depth.plus(start_tag_levels(start_tag));
        if let Some(message) = too_deep_message(&start_tag.name.content, here) {
            return Some((&start_tag.token, message));
        }
        if let Node::WithBody { body, .. } = node {
            pending.push((body.elements.iter(), here));
        }
    }
    None
}
