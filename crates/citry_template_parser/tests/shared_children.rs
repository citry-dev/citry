//! Copying a parsed template shares the tree below it instead of copying it.
//!
//! PyO3 copies a field each time Python reads it, so reading a node's `body`
//! or a template's `elements` from Python copies that value. The lists below
//! a template are shared between copies, so a read costs the same at any
//! depth (#384). These tests check the sharing directly: a copy holds the
//! same allocations as the original.

use citry_template_parser::ast::{Node, Shared, Template, TemplateElement};
use citry_template_parser::parser::parse_template;

/// A template whose root holds one deep chain of nodes.
fn deep_template() -> Template {
    let depth = 64;
    let source =
        "<c-if cond=\"flag\"><div>".repeat(depth) + "{{ x }}" + &"</div></c-if>".repeat(depth);
    parse_template(&source, None, None).unwrap()
}

/// The first node in `elements`, which every level of the chain has.
fn first_node(elements: &[TemplateElement]) -> &Node {
    match &elements[0] {
        TemplateElement::Node(node) => node,
        other => panic!("expected a node, found {other:?}"),
    }
}

#[test]
fn a_copied_template_shares_its_lists() {
    let template = deep_template();
    let copy = template.clone();
    assert!(Shared::ptr_eq(&template.elements, &copy.elements));
    assert!(Shared::ptr_eq(&template.comments, &copy.comments));
    assert!(Shared::ptr_eq(
        &template.used_variables,
        &copy.used_variables
    ));
    assert!(Shared::ptr_eq(&template.slots, &copy.slots));
    // Sharing changes nothing a reader can see.
    assert_eq!(template, copy);
}

#[test]
fn a_copied_node_shares_its_body_and_its_lists() {
    let template = deep_template();
    let node = first_node(&template.elements);
    // Python reads a node by copying it, as `TemplateElement._0` does.
    let copy = node.clone();
    let (
        Node::WithBody {
            body,
            used_variables,
            comments,
            ..
        },
        Node::WithBody {
            body: copy_body,
            used_variables: copy_used,
            comments: copy_comments,
            ..
        },
    ) = (node, &copy)
    else {
        panic!("expected nodes with bodies");
    };
    assert!(Shared::ptr_eq(&body.elements, &copy_body.elements));
    assert!(Shared::ptr_eq(used_variables, copy_used));
    assert!(Shared::ptr_eq(comments, copy_comments));
}
