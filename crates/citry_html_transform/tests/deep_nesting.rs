//! The checks that read a parsed HTML tree handle deep trees on a small
//! thread.
//!
//! Comparing the browser's parse with the expected nodes and checking a raw
//! HTML block call themselves once per level of the parsed tree. These tests
//! run both on HTML nested 2,000 elements deep on threads with 128 KiB and
//! 384 KiB stacks. A crash aborts this test binary, which fails the test
//! run.

use citry_html_transform::hydration_structure::{
    browser_fragment_matches_nodes, ExpectedNodeEvent,
};
use citry_html_transform::static_html::{static_html_in_context, StaticHtmlUse};

const DEPTH: usize = 2_000;

fn on_small_stacks(work: fn() -> bool) {
    for stack_size in [128 * 1024, 384 * 1024] {
        let accepted = std::thread::Builder::new()
            .stack_size(stack_size)
            .spawn(work)
            .unwrap()
            .join()
            .unwrap_or_else(|_| panic!("failed on a {stack_size}-byte stack"));
        assert!(accepted, "rejected on a {stack_size}-byte stack");
    }
}

fn nested_divs() -> String {
    format!("{}x{}", "<div>".repeat(DEPTH), "</div>".repeat(DEPTH))
}

#[test]
fn the_parse_comparison_walks_a_deep_tree() {
    on_small_stacks(|| {
        let mut events = Vec::new();
        for _ in 0..DEPTH {
            events.push(ExpectedNodeEvent::Open {
                tag: "div".to_owned(),
                attributes: Vec::new(),
            });
        }
        for _ in 0..DEPTH {
            events.push(ExpectedNodeEvent::Close {
                tag: "div".to_owned(),
            });
        }
        browser_fragment_matches_nodes(&nested_divs(), "div", &events)
    });
}

#[test]
fn the_raw_block_check_walks_a_deep_tree() {
    on_small_stacks(|| {
        static_html_in_context(&["div"], &nested_divs(), StaticHtmlUse::Adopted).is_some()
    });
}
