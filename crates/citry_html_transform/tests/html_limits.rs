//! Every entry point refuses HTML over the size limits in
//! `src/html_limits.rs`, accepts HTML at them, and finishes quickly on the
//! inputs that took seconds to minutes before the limits.
//!
//! Each slow input below took far longer than the time this file allows it
//! when html5ever read it whole (in a debug build, which runs these tests),
//! so a lost limit fails the time check.

use std::collections::HashSet;
use std::time::{Duration, Instant};

use citry_html_transform::hydration_structure::{
    browser_fragment_matches_nodes, ExpectedNodeEvent,
};
use citry_html_transform::output_policy::{
    check_output_html, JavascriptMode, OutputPolicyOptions, PolicyPass,
};
use citry_html_transform::output_scanner::{scan_output_html, validate_html_fragment_boundary};
use citry_html_transform::static_html::{
    static_html_in_context, static_html_node_count, StaticHtmlUse,
};
use citry_html_transform::{HtmlTooLarge, MAX_ATTRIBUTES_PER_TAG, MAX_DOCUMENT_TAGS};

/// The time one slow input may take. Generous for a debug build on a busy
/// machine, and still far below what the inputs took without the limits.
const QUICK: Duration = Duration::from_secs(10);

/// A `<p>` with `count` distinct bare attributes, the cheapest way to write
/// many of them.
fn tag_with(count: usize) -> String {
    let attributes: String = (0..count).map(|i| format!(" a{i}")).collect();
    format!("<p{attributes}>x</p>")
}

/// What each entry point did with `html`, in a fixed order, so one
/// assertion covers all of them.
fn outcomes(html: &str) -> Vec<(&'static str, String)> {
    let trusted = HashSet::new();
    let options = OutputPolicyOptions {
        pass: PolicyPass::Settled,
        csp: true,
        javascript: Some(JavascriptMode::Warn),
        marker_prefix: None,
        trusted_tag_starts: &trusted,
        omit_handler_marker: None,
    };
    let expected = [
        ExpectedNodeEvent::Open {
            tag: "p".to_owned(),
            attributes: Vec::new(),
        },
        ExpectedNodeEvent::Close {
            tag: "p".to_owned(),
        },
    ];
    vec![
        (
            "scan",
            match scan_output_html(html) {
                Ok(tags) => format!("read {}", tags.len()),
                Err(error) => error.to_string(),
            },
        ),
        (
            "check",
            match check_output_html(html, &options) {
                Ok(_) => "checked".to_owned(),
                Err(error) => error.to_string(),
            },
        ),
        (
            "validate",
            match validate_html_fragment_boundary(html) {
                Ok(()) => "accepted".to_owned(),
                Err(message) => message,
            },
        ),
        (
            "count",
            match static_html_node_count(html) {
                Ok(count) => format!("{count} nodes"),
                Err(error) => error.to_string(),
            },
        ),
        (
            "static",
            match static_html_in_context(&["div"], html, StaticHtmlUse::Adopted) {
                Some(_) => "accepted".to_owned(),
                None => "rejected".to_owned(),
            },
        ),
        (
            "nodes",
            browser_fragment_matches_nodes(html, "div", &expected).to_string(),
        ),
    ]
}

#[test]
fn a_tag_at_the_attribute_limit_is_read_and_one_more_is_refused() {
    let at_limit = outcomes(&tag_with(MAX_ATTRIBUTES_PER_TAG));
    assert_eq!(
        at_limit,
        [
            ("scan", "read 1".to_owned()),
            ("check", "checked".to_owned()),
            ("validate", "accepted".to_owned()),
            ("count", "1 nodes".to_owned()),
            ("static", "accepted".to_owned()),
            // The expected events carry no attributes, so the comparison
            // read the tag and found a difference.
            ("nodes", "false".to_owned()),
        ]
    );
    let over = outcomes(&tag_with(MAX_ATTRIBUTES_PER_TAG + 1));
    let message = HtmlTooLarge::Attributes.to_string();
    assert_eq!(
        over,
        [
            ("scan", message.clone()),
            ("check", message.clone()),
            ("validate", format!("opaque {message}")),
            ("count", message),
            ("static", "rejected".to_owned()),
            ("nodes", "false".to_owned()),
        ]
    );
}

#[test]
fn many_tags_at_the_limit_are_read() {
    // The limit is per tag: a page of many full tags is read.
    let page = tag_with(MAX_ATTRIBUTES_PER_TAG).repeat(20);
    assert_eq!(scan_output_html(&page).map(|tags| tags.len()), Ok(20));
    assert_eq!(static_html_node_count(&page), Ok(20));
}

#[test]
fn an_end_tag_does_not_add_to_the_start_tag_count() {
    // html5gum reports an end tag's attributes, which the browser drops.
    let attributes: String = (0..MAX_ATTRIBUTES_PER_TAG)
        .map(|i| format!(" b{i}"))
        .collect();
    let page = format!("{}</p{attributes}>", tag_with(MAX_ATTRIBUTES_PER_TAG));
    assert!(scan_output_html(&page).is_ok());
}

#[test]
fn each_document_tag_is_read_up_to_the_limit_and_refused_after() {
    for name in ["html", "head", "body"] {
        let at_limit = format!("<{name}>").repeat(MAX_DOCUMENT_TAGS);
        let over = format!("<{name}>").repeat(MAX_DOCUMENT_TAGS + 1);
        let message = HtmlTooLarge::DocumentTags(name).to_string();
        assert!(scan_output_html(&at_limit).is_ok(), "{name}");
        assert!(static_html_node_count(&at_limit).is_ok(), "{name}");
        assert_eq!(
            scan_output_html(&over).map(|_| ()),
            Err(HtmlTooLarge::DocumentTags(name))
        );
        assert_eq!(
            static_html_node_count(&over),
            Err(HtmlTooLarge::DocumentTags(name))
        );
        assert_eq!(
            validate_html_fragment_boundary(&over),
            Err(format!("opaque {message}"))
        );
        assert!(static_html_in_context(&["div"], &over, StaticHtmlUse::Replaced).is_none());
    }
    // The three names count apart, so a full set of each is still read.
    let all = ["<html>", "<head>", "<body>"].map(|tag| tag.repeat(MAX_DOCUMENT_TAGS));
    assert!(scan_output_html(&all.concat()).is_ok());
}

#[test]
fn text_the_browser_does_not_read_as_tags_is_not_counted() {
    // Inside a script, a title, a textarea and a comment, `<body>` is text.
    // The scan follows the browser here, so none of it counts.
    let many = "<body a b c>".repeat(MAX_DOCUMENT_TAGS * 4);
    let attributes: String = (0..MAX_ATTRIBUTES_PER_TAG * 2)
        .map(|i| format!(" a{i}"))
        .collect();
    let wide = format!("<p{attributes}>");
    for (open, close) in [
        ("<script>", "</script>"),
        ("<title>", "</title>"),
        ("<textarea>", "</textarea>"),
        ("<!--", "-->"),
    ] {
        let page = format!("{open}{many}{wide}{close}");
        assert!(scan_output_html(&page).is_ok(), "{open}");
        assert!(static_html_node_count(&page).is_ok(), "{open}");
    }
}

#[test]
fn a_tag_the_browser_reads_after_raw_text_is_counted() {
    // A `<!--` inside a title is text, so the `<p>` after `</title>` is a
    // real tag, and a reading that ignored the title would hide it.
    let page = format!(
        "<title><!--</title>{}-->",
        tag_with(MAX_ATTRIBUTES_PER_TAG + 1)
    );
    assert_eq!(
        scan_output_html(&page).map(|_| ()),
        Err(HtmlTooLarge::Attributes)
    );
    assert_eq!(static_html_node_count(&page), Err(HtmlTooLarge::Attributes));
}

/// Run `work` and check that it finished within [`QUICK`].
fn quickly<T>(what: &str, work: impl FnOnce() -> T) -> T {
    let start = Instant::now();
    let result = work();
    let took = start.elapsed();
    assert!(took < QUICK, "{what} took {took:?}");
    result
}

#[test]
fn a_tag_with_40000_attributes_is_refused_quickly() {
    // html5ever's tokenizer compared each name with every earlier one.
    let page = tag_with(40_000);
    quickly("count", || {
        assert_eq!(static_html_node_count(&page), Err(HtmlTooLarge::Attributes));
    });
    quickly("static", || {
        assert!(static_html_in_context(&["div"], &page, StaticHtmlUse::Adopted).is_none());
    });
}

#[test]
fn many_repeated_body_tags_are_refused_quickly() {
    // The tree builder copied each `<body>` tag's new attributes onto the
    // first one, and read all of them again for the next tag.
    let page: String = (0..3_000)
        .map(|i| {
            let attributes: String = (0..64).map(|j| format!(" b{i}_{j}")).collect();
            format!("<body{attributes}>")
        })
        .collect();
    let refused = HtmlTooLarge::DocumentTags("body");
    quickly("scan", || {
        assert_eq!(scan_output_html(&page).map(|_| ()), Err(refused))
    });
    quickly("count", || {
        assert_eq!(static_html_node_count(&page), Err(refused))
    });
    quickly("validate", || {
        assert!(validate_html_fragment_boundary(&page).is_err())
    });
    quickly("nodes", || {
        assert!(!browser_fragment_matches_nodes(&page, "div", &[]));
    });
}

#[test]
fn a_tag_raw_text_hides_in_a_document_is_counted_where_vue_parses_it() {
    // Inside `<template>`, a `<col>` puts the parser where `<style>` and
    // `<plaintext>` are ignored, so the wide tag after them is a real tag
    // there, though a document parse reads it as text.
    let wide = tag_with(MAX_ATTRIBUTES_PER_TAG + 1);
    for block in [
        format!("<col><style>{wide}</style>"),
        format!("<col><plaintext>{wide}"),
    ] {
        assert_eq!(
            static_html_node_count(&block),
            Err(HtmlTooLarge::Attributes),
            "{block:.20}"
        );
        assert_eq!(
            validate_html_fragment_boundary(&block),
            Err(format!("opaque {}", HtmlTooLarge::Attributes)),
            "{block:.20}"
        );
        assert!(static_html_in_context(&["div"], &block, StaticHtmlUse::Adopted).is_none());
    }
}

#[test]
fn a_tag_raw_text_hides_is_counted_inside_every_open_element() {
    // The page parse puts the block inside the open elements. In `<select>`
    // a `<style>` or `<title>` is ignored, and `</textarea>` or `</title>`
    // closes the element the block sits in, so the wide tag is read.
    let wide = tag_with(40_000);
    for (open, block) in [
        (&["select"][..], format!("<style>{wide}</style>")),
        (&["select", "option"][..], format!("<title>{wide}</title>")),
        (
            &["textarea"][..],
            format!("<style></textarea>{wide}</style>"),
        ),
        (&["title"][..], format!("<style></title>{wide}</style>")),
    ] {
        quickly("static", || {
            assert!(
                static_html_in_context(open, &block, StaticHtmlUse::Adopted).is_none(),
                "{open:?}"
            );
        });
    }
}
