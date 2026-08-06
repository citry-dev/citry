//! Shared rendered-edge analysis for structural whitespace decisions.

use citry_template_parser::{Node, Template, TemplateElement};

use crate::html::{EdgeKind, edge_kind_for_tag_in_parent, merge_branch_edges};
use crate::source::is_html_space_text;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct ItemEdges {
    pub(crate) first: EdgeKind,
    pub(crate) last: EdgeKind,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ControlBranch {
    If,
    Elif,
    Else,
    For,
    Empty,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct ElementLayout {
    pub(crate) edges: Option<ItemEdges>,
    pub(crate) control: Option<ControlBranch>,
    pub(crate) physical_control: bool,
}

pub(crate) fn analyze_elements(
    template: &Template,
    parent_tag_name: Option<&str>,
) -> Vec<ElementLayout> {
    let mut layouts = template
        .elements
        .iter()
        .map(|element| analyze_element(element, parent_tag_name))
        .collect::<Vec<_>>();
    apply_control_group_edges(&mut layouts);
    layouts
}

pub(crate) fn body_edges(template: &Template, parent_tag_name: Option<&str>) -> Option<ItemEdges> {
    let layouts = analyze_elements(template, parent_tag_name);
    Some(ItemEdges {
        first: layouts
            .iter()
            .find_map(|layout| layout.edges.map(|edges| edges.first))?,
        last: layouts
            .iter()
            .rev()
            .find_map(|layout| layout.edges.map(|edges| edges.last))?,
    })
}

fn analyze_element(element: &TemplateElement, parent_tag_name: Option<&str>) -> ElementLayout {
    match element {
        TemplateElement::Node(node) => analyze_node(node, parent_tag_name),
        TemplateElement::Expr(_) => sensitive_layout(),
        TemplateElement::Text(text) if is_html_space_text(&text.token.content) => ElementLayout {
            edges: None,
            control: None,
            physical_control: false,
        },
        TemplateElement::Text(text) if is_non_rendered_html_comment(&text.token.content) => {
            ElementLayout {
                edges: None,
                control: None,
                physical_control: false,
            }
        }
        TemplateElement::Text(text)
            if parent_tag_name.is_none() && is_structural_root_pseudo_item(&text.token.content) =>
        {
            block_layout()
        }
        TemplateElement::Text(_) => sensitive_layout(),
    }
}

fn analyze_node(node: &Node, parent_tag_name: Option<&str>) -> ElementLayout {
    let tag_name = node.tag_name();
    let physical_control = control_branch(tag_name);
    let control = physical_control.or_else(|| shorthand_control_branch(node));
    let raw_edges = match edge_kind_for_tag_in_parent(tag_name, parent_tag_name) {
        EdgeKind::Transparent => match node {
            Node::WithBody { body, .. } => body_edges(body, Some(tag_name)),
            Node::SelfClosing { .. } => None,
        },
        edge => Some(ItemEdges {
            first: edge,
            last: edge,
        }),
    };
    let edges = suppress_edge_for_inner_control(node, control, raw_edges);
    ElementLayout {
        edges,
        control,
        physical_control: physical_control.is_some(),
    }
}

fn sensitive_layout() -> ElementLayout {
    ElementLayout {
        edges: Some(ItemEdges {
            first: EdgeKind::Sensitive,
            last: EdgeKind::Sensitive,
        }),
        control: None,
        physical_control: false,
    }
}

fn block_layout() -> ElementLayout {
    ElementLayout {
        edges: Some(ItemEdges {
            first: EdgeKind::BlockLike,
            last: EdgeKind::BlockLike,
        }),
        control: None,
        physical_control: false,
    }
}

fn apply_control_group_edges(layouts: &mut [ElementLayout]) {
    let significant = layouts
        .iter()
        .enumerate()
        .filter_map(|(index, layout)| {
            (layout.control.is_some() || layout.edges.is_some()).then_some(index)
        })
        .collect::<Vec<_>>();
    let mut cursor = 0;

    while cursor < significant.len() {
        let start_index = significant[cursor];
        let Some(start_branch) = layouts[start_index].control else {
            cursor += 1;
            continue;
        };
        let family = match start_branch {
            ControlBranch::If => ControlBranch::If,
            ControlBranch::For => ControlBranch::For,
            _ => {
                cursor += 1;
                continue;
            }
        };

        let mut end = cursor + 1;
        while end < significant.len() {
            let branch = layouts[significant[end]].control;
            let belongs = match family {
                ControlBranch::If => {
                    matches!(branch, Some(ControlBranch::Elif | ControlBranch::Else))
                }
                ControlBranch::For => matches!(branch, Some(ControlBranch::Empty)),
                _ => false,
            };
            if !belongs {
                break;
            }
            end += 1;
            if branch == Some(ControlBranch::Else) || branch == Some(ControlBranch::Empty) {
                break;
            }
        }

        let branch_indexes = &significant[cursor..end];
        let mut first_edges = branch_indexes
            .iter()
            .map(|index| layouts[*index].edges.map(|edges| edges.first))
            .collect::<Vec<_>>();
        let mut last_edges = branch_indexes
            .iter()
            .map(|index| layouts[*index].edges.map(|edges| edges.last))
            .collect::<Vec<_>>();
        let exhaustive = match family {
            ControlBranch::If => branch_indexes
                .last()
                .is_some_and(|index| layouts[*index].control == Some(ControlBranch::Else)),
            ControlBranch::For => branch_indexes
                .last()
                .is_some_and(|index| layouts[*index].control == Some(ControlBranch::Empty)),
            _ => false,
        };
        if !exhaustive {
            first_edges.push(None);
            last_edges.push(None);
        }
        let merged = ItemEdges {
            first: merge_branch_edges(&first_edges),
            last: merge_branch_edges(&last_edges),
        };
        for index in branch_indexes {
            layouts[*index].edges = Some(merged);
        }
        cursor = end;
    }
}

fn control_branch(tag_name: &str) -> Option<ControlBranch> {
    match tag_name {
        "c-if" => Some(ControlBranch::If),
        "c-elif" => Some(ControlBranch::Elif),
        "c-else" => Some(ControlBranch::Else),
        "c-for" => Some(ControlBranch::For),
        "c-empty" => Some(ControlBranch::Empty),
        _ => None,
    }
}

fn shorthand_control_branch(node: &Node) -> Option<ControlBranch> {
    for names in [&["c-if", "c-elif", "c-else"][..], &["c-for", "c-empty"][..]] {
        if let Some(branch) = node.attrs().iter().find_map(|attr| {
            names.contains(&attr.key.content.as_str()).then(|| {
                control_branch(&attr.key.content)
                    .expect("control attribute names share control tag spellings")
            })
        }) {
            return Some(branch);
        }
    }
    None
}

fn suppress_edge_for_inner_control(
    node: &Node,
    outer_control: Option<ControlBranch>,
    edges: Option<ItemEdges>,
) -> Option<ItemEdges> {
    if matches!(
        outer_control,
        Some(ControlBranch::If | ControlBranch::Elif | ControlBranch::Else)
    ) && node
        .attrs()
        .iter()
        .any(|attr| matches!(attr.key.content.as_str(), "c-for" | "c-empty"))
    {
        None
    } else {
        edges
    }
}

fn is_non_rendered_html_comment(content: &str) -> bool {
    content.starts_with("<!--") && content.ends_with("-->")
}

fn is_structural_root_pseudo_item(content: &str) -> bool {
    (content.starts_with("<!") || content.starts_with("<?")) && content.ends_with('>')
}
