//! Formatter-owned HTML display and whitespace-boundary contracts.
//!
//! This module is pure judgment about how browsers render, and it is the one
//! place in the crate the invariant checks cannot protect. Everything else is
//! verified by comparing the template against itself, but those comparisons use
//! the answers given here, so a wrong entry below is wrong on both sides and
//! passes every check while changing the rendered page.
//!
//! Treat the tables as a contract with the reader's browser rather than as
//! configuration, and pair any change with corpus coverage that would fail if
//! the judgment were reverted.

/// HTML elements whose default rendering provides a structural edge.
///
/// Keep this list sorted: lookup is ASCII case-insensitive without allocating.
/// Changing membership changes formatter output and requires corpus coverage.
pub(crate) const BLOCK_LIKE_HTML_TAGS: &[&str] = &[
    "address",
    "article",
    "aside",
    "blockquote",
    "body",
    "caption",
    "colgroup",
    "dd",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hgroup",
    "hr",
    "html",
    "li",
    "main",
    "menu",
    "nav",
    "ol",
    "p",
    "pre",
    "script",
    "search",
    "section",
    "style",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
];

const TRANSPARENT_CONTROL_TAGS: &[&str] = &["c-elif", "c-else", "c-empty", "c-for", "c-if"];
const HTML_VERBATIM_BODY_TAGS: &[&str] = &["pre", "script", "style", "textarea"];

/// The rendered edge a template item contributes to its parent.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum EdgeKind {
    BlockLike,
    Sensitive,
    Transparent,
}

/// How a tag body treats whitespace between its direct items.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ContainerKind {
    Root,
    Structural,
    Sensitive,
    Verbatim,
}

/// The preservation rule for one source gap.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum WhitespaceClass {
    Verbatim,
    Sensitive,
    Structural,
}

/// Facts needed to classify a gap independently of printing.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct GapContext {
    pub(crate) container: ContainerKind,
    pub(crate) left: Option<EdgeKind>,
    pub(crate) right: Option<EdgeKind>,
    pub(crate) authored_whitespace: bool,
    pub(crate) protected: bool,
}

#[cfg(test)]
pub(crate) fn edge_kind_for_tag(tag_name: &str) -> EdgeKind {
    edge_kind_for_tag_in_parent(tag_name, None)
}

pub(crate) fn edge_kind_for_tag_in_parent(
    tag_name: &str,
    parent_tag_name: Option<&str>,
) -> EdgeKind {
    if TRANSPARENT_CONTROL_TAGS.contains(&tag_name) {
        EdgeKind::Transparent
    } else if is_contextual_select_child(tag_name, parent_tag_name)
        || contains_ascii_case_insensitive(BLOCK_LIKE_HTML_TAGS, tag_name)
    {
        EdgeKind::BlockLike
    } else {
        EdgeKind::Sensitive
    }
}

pub(crate) fn container_kind_for_tag(tag_name: &str) -> ContainerKind {
    if tag_name == "c-raw" || contains_ascii_case_insensitive(HTML_VERBATIM_BODY_TAGS, tag_name) {
        ContainerKind::Verbatim
    } else if tag_name == "c-fill"
        || TRANSPARENT_CONTROL_TAGS.contains(&tag_name)
        || contains_ascii_case_insensitive(BLOCK_LIKE_HTML_TAGS, tag_name)
        || tag_name.eq_ignore_ascii_case("select")
        || tag_name.eq_ignore_ascii_case("optgroup")
    {
        ContainerKind::Structural
    } else {
        ContainerKind::Sensitive
    }
}

pub(crate) fn classify_gap(context: GapContext) -> WhitespaceClass {
    if context.protected || context.container == ContainerKind::Verbatim {
        return WhitespaceClass::Verbatim;
    }

    match context.container {
        ContainerKind::Sensitive => WhitespaceClass::Sensitive,
        ContainerKind::Structural => match (context.left, context.right) {
            (Some(EdgeKind::BlockLike), Some(EdgeKind::BlockLike))
            | (None, Some(EdgeKind::BlockLike))
            | (Some(EdgeKind::BlockLike), None) => WhitespaceClass::Structural,
            _ => WhitespaceClass::Sensitive,
        },
        ContainerKind::Root => classify_root_gap(context),
        ContainerKind::Verbatim => WhitespaceClass::Verbatim,
    }
}

/// Collapse the possible rendered edges of control-flow branches.
///
/// `None` is an empty possible branch. An empty branch, disagreement, or a
/// sensitive edge makes the group sensitive; only all-block possibilities are
/// block-like.
pub(crate) fn merge_branch_edges(edges: &[Option<EdgeKind>]) -> EdgeKind {
    if !edges.is_empty() && edges.iter().all(|edge| *edge == Some(EdgeKind::BlockLike)) {
        EdgeKind::BlockLike
    } else {
        EdgeKind::Sensitive
    }
}

fn classify_root_gap(context: GapContext) -> WhitespaceClass {
    match (context.left, context.right) {
        (Some(EdgeKind::BlockLike), Some(EdgeKind::BlockLike)) => WhitespaceClass::Structural,
        (None, Some(EdgeKind::BlockLike)) | (Some(EdgeKind::BlockLike), None)
            if context.authored_whitespace =>
        {
            WhitespaceClass::Structural
        }
        _ => WhitespaceClass::Sensitive,
    }
}

fn contains_ascii_case_insensitive(values: &[&str], candidate: &str) -> bool {
    values
        .iter()
        .any(|value| value.eq_ignore_ascii_case(candidate))
}

fn is_contextual_select_child(tag_name: &str, parent_tag_name: Option<&str>) -> bool {
    match parent_tag_name {
        Some(parent) if parent.eq_ignore_ascii_case("select") => {
            tag_name.eq_ignore_ascii_case("option") || tag_name.eq_ignore_ascii_case("optgroup")
        }
        Some(parent) if parent.eq_ignore_ascii_case("optgroup") => {
            tag_name.eq_ignore_ascii_case("option")
        }
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::{
        BLOCK_LIKE_HTML_TAGS, ContainerKind, EdgeKind, GapContext, WhitespaceClass, classify_gap,
        container_kind_for_tag, edge_kind_for_tag, edge_kind_for_tag_in_parent, merge_branch_edges,
    };

    #[test]
    fn block_like_table_is_sorted_and_unique() {
        assert!(
            BLOCK_LIKE_HTML_TAGS
                .windows(2)
                .all(|pair| pair[0] < pair[1]),
            "block-like tag table must stay sorted and duplicate-free"
        );
    }

    #[test]
    fn tag_lookup_is_ascii_case_insensitive_and_components_stay_sensitive() {
        assert_eq!(edge_kind_for_tag("DIV"), EdgeKind::BlockLike);
        assert_eq!(edge_kind_for_tag("c-if"), EdgeKind::Transparent);
        assert_eq!(edge_kind_for_tag("c-IF"), EdgeKind::Sensitive);
        assert_eq!(edge_kind_for_tag("span"), EdgeKind::Sensitive);
        assert_eq!(edge_kind_for_tag("x-panel"), EdgeKind::Sensitive);
        assert_eq!(edge_kind_for_tag("c-CButton"), EdgeKind::Sensitive);
    }

    #[test]
    fn select_is_a_structural_container_but_a_sensitive_outer_edge() {
        assert_eq!(container_kind_for_tag("select"), ContainerKind::Structural);
        assert_eq!(edge_kind_for_tag("select"), EdgeKind::Sensitive);
        assert_eq!(edge_kind_for_tag("option"), EdgeKind::Sensitive);
        assert_eq!(edge_kind_for_tag("optgroup"), EdgeKind::Sensitive);
        assert_eq!(
            edge_kind_for_tag_in_parent("option", Some("select")),
            EdgeKind::BlockLike
        );
        assert_eq!(
            edge_kind_for_tag_in_parent("optgroup", Some("SELECT")),
            EdgeKind::BlockLike
        );
        assert_eq!(
            edge_kind_for_tag_in_parent("option", Some("optgroup")),
            EdgeKind::BlockLike
        );
    }

    #[test]
    fn protected_body_tags_keep_distinct_outer_edges() {
        assert_eq!(container_kind_for_tag("c-raw"), ContainerKind::Verbatim);
        assert_eq!(edge_kind_for_tag("c-raw"), EdgeKind::Sensitive);
        assert_eq!(container_kind_for_tag("c-RAW"), ContainerKind::Sensitive);
        assert_eq!(container_kind_for_tag("c-fill"), ContainerKind::Structural);
        assert_eq!(edge_kind_for_tag("c-fill"), EdgeKind::Sensitive);
        assert_eq!(container_kind_for_tag("c-FILL"), ContainerKind::Sensitive);
        assert_eq!(container_kind_for_tag("textarea"), ContainerKind::Verbatim);
        assert_eq!(edge_kind_for_tag("textarea"), EdgeKind::Sensitive);
        assert_eq!(container_kind_for_tag("pre"), ContainerKind::Verbatim);
        assert_eq!(edge_kind_for_tag("pre"), EdgeKind::BlockLike);
    }

    #[test]
    fn protected_and_verbatim_gaps_are_never_structural() {
        let structural = GapContext {
            container: ContainerKind::Structural,
            left: Some(EdgeKind::BlockLike),
            right: Some(EdgeKind::BlockLike),
            authored_whitespace: true,
            protected: false,
        };
        assert_eq!(classify_gap(structural), WhitespaceClass::Structural);
        assert_eq!(
            classify_gap(GapContext {
                protected: true,
                ..structural
            }),
            WhitespaceClass::Verbatim
        );
        assert_eq!(
            classify_gap(GapContext {
                container: ContainerKind::Verbatim,
                ..structural
            }),
            WhitespaceClass::Verbatim
        );
    }

    #[test]
    fn block_container_requires_block_edges() {
        let facts = GapContext {
            container: ContainerKind::Structural,
            left: Some(EdgeKind::BlockLike),
            right: Some(EdgeKind::BlockLike),
            authored_whitespace: false,
            protected: false,
        };
        assert_eq!(classify_gap(facts), WhitespaceClass::Structural);
        assert_eq!(
            classify_gap(GapContext {
                right: Some(EdgeKind::Sensitive),
                ..facts
            }),
            WhitespaceClass::Sensitive
        );
        assert_eq!(
            classify_gap(GapContext {
                container: ContainerKind::Sensitive,
                ..facts
            }),
            WhitespaceClass::Sensitive
        );
    }

    #[test]
    fn structural_container_boundaries_count_as_block_edges() {
        let start = GapContext {
            container: ContainerKind::Structural,
            left: None,
            right: Some(EdgeKind::BlockLike),
            authored_whitespace: false,
            protected: false,
        };
        assert_eq!(classify_gap(start), WhitespaceClass::Structural);
        assert_eq!(
            classify_gap(GapContext {
                left: Some(EdgeKind::BlockLike),
                right: None,
                ..start
            }),
            WhitespaceClass::Structural
        );
        assert_eq!(
            classify_gap(GapContext {
                left: None,
                right: None,
                ..start
            }),
            WhitespaceClass::Sensitive
        );
    }

    #[test]
    fn root_margins_are_structural_only_when_authored() {
        let margin = GapContext {
            container: ContainerKind::Root,
            left: None,
            right: Some(EdgeKind::BlockLike),
            authored_whitespace: false,
            protected: false,
        };
        assert_eq!(classify_gap(margin), WhitespaceClass::Sensitive);
        assert_eq!(
            classify_gap(GapContext {
                authored_whitespace: true,
                ..margin
            }),
            WhitespaceClass::Structural
        );
    }

    #[test]
    fn transparent_branch_edges_are_block_like_only_when_every_branch_is() {
        assert_eq!(
            merge_branch_edges(&[Some(EdgeKind::BlockLike), Some(EdgeKind::BlockLike)]),
            EdgeKind::BlockLike
        );
        assert_eq!(
            merge_branch_edges(&[Some(EdgeKind::BlockLike), Some(EdgeKind::Sensitive)]),
            EdgeKind::Sensitive
        );
        assert_eq!(
            merge_branch_edges(&[Some(EdgeKind::BlockLike), None]),
            EdgeKind::Sensitive
        );
        assert_eq!(merge_branch_edges(&[]), EdgeKind::Sensitive);
    }
}
