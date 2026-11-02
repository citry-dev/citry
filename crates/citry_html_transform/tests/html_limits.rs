//! Every entry point refuses HTML over the size limits in
//! `src/html_limits.rs`, accepts HTML at them, and finishes quickly on the
//! inputs that took seconds to minutes before the limits.
//!
//! Most slow inputs below took far longer than the time this file allows
//! them when html5ever read them whole (in a debug build, which runs these
//! tests), so a lost limit fails the time check. The two inputs that
//! reopen formatting elements finish within it either way, so only their
//! assertions that the page is refused guard those limits.

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
use citry_html_transform::{
    HtmlTooLarge, MAX_ATTRIBUTES_PER_TAG, MAX_DOCUMENT_TAGS, MAX_OPEN_ELEMENTS,
    MAX_REOPENED_FORMATTING_ELEMENTS,
};

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
/// assertion covers all of them. The last entry point compares the page
/// with a lone `<p>`.
fn outcomes(html: &str) -> Vec<(&'static str, String)> {
    let expected = [
        ExpectedNodeEvent::Open {
            tag: "p".to_owned(),
            attributes: Vec::new(),
        },
        ExpectedNodeEvent::Close {
            tag: "p".to_owned(),
        },
    ];
    outcomes_expecting(html, &expected)
}

/// [`outcomes`], with the last entry point comparing the page with
/// `expected` instead.
fn outcomes_expecting(html: &str, expected: &[ExpectedNodeEvent]) -> Vec<(&'static str, String)> {
    let trusted = HashSet::new();
    let options = OutputPolicyOptions {
        pass: PolicyPass::Settled,
        csp: true,
        javascript: Some(JavascriptMode::Warn),
        marker_prefix: None,
        trusted_tag_starts: &trusted,
        omit_handler_marker: None,
    };
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
            browser_fragment_matches_nodes(html, "div", expected).to_string(),
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

/// `count` elements named `tag`, each inside the one before, all closed.
fn nested(tag: &str, count: usize) -> String {
    format!(
        "{}{}",
        format!("<{tag}>").repeat(count),
        format!("</{tag}>").repeat(count)
    )
}

/// The events a page of `nested("div", count)` is expected to give.
fn nested_div_events(count: usize) -> Vec<ExpectedNodeEvent> {
    let open = |_| ExpectedNodeEvent::Open {
        tag: "div".to_owned(),
        attributes: Vec::new(),
    };
    let close = |_| ExpectedNodeEvent::Close {
        tag: "div".to_owned(),
    };
    (0..count).map(open).chain((0..count).map(close)).collect()
}

#[test]
fn elements_nested_just_under_the_limit_are_read_and_just_over_are_refused() {
    let under = MAX_OPEN_ELEMENTS - 12;
    assert_eq!(
        outcomes_expecting(&nested("div", under), &nested_div_events(under)),
        [
            ("scan", format!("read {under}")),
            ("check", "checked".to_owned()),
            ("validate", "accepted".to_owned()),
            ("count", "1 nodes".to_owned()),
            ("static", "accepted".to_owned()),
            ("nodes", "true".to_owned()),
        ]
    );
    let over = MAX_OPEN_ELEMENTS + 8;
    let message = HtmlTooLarge::OpenElements.to_string();
    assert_eq!(
        outcomes_expecting(&nested("div", over), &nested_div_events(over)),
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
fn the_open_element_limit_is_exact_for_the_elements_the_parser_holds() {
    // A page scan holds the `<html>`, `<body>` and `<head>` elements besides
    // the page's own, so 509 nested elements are 512 in all. A fragment
    // parsed for `<template>` holds the root `<html>` and the context
    // element, so it fits 510.
    for tag in ["div", "b"] {
        assert!(scan_output_html(&nested(tag, 509)).is_ok(), "{tag}");
        assert_eq!(
            scan_output_html(&nested(tag, 510)).map(|_| ()),
            Err(HtmlTooLarge::OpenElements),
            "{tag}"
        );
        assert_eq!(static_html_node_count(&nested(tag, 510)), Ok(1), "{tag}");
        assert_eq!(
            static_html_node_count(&nested(tag, 511)),
            Err(HtmlTooLarge::OpenElements),
            "{tag}"
        );
    }
}

/// `count` nested `<b>` elements that each have their own attribute value.
/// The parser keeps at most three equal formatting elements on its list, so
/// these differ to keep every one of them there.
fn nested_distinct_b(count: usize) -> String {
    let open: String = (0..count).map(|i| format!("<b a=\"{i}\">")).collect();
    format!("{open}{}", "</b>".repeat(count))
}

#[test]
fn an_element_that_is_open_and_on_the_formatting_list_counts_once() {
    // An open `<b>` is in the parser's stack of open elements and on its
    // list of formatting elements, so the parser reports it twice. 300 of
    // them are 300 elements, not 600, and they nest as far as `<div>` does.
    assert!(scan_output_html(&nested_distinct_b(300)).is_ok());
    assert_eq!(
        scan_output_html(&nested_distinct_b(509)).map(|tags| tags.len()),
        Ok(509)
    );
    assert_eq!(
        scan_output_html(&nested_distinct_b(510)).map(|_| ()),
        Err(HtmlTooLarge::OpenElements)
    );
    // Two groups after each other hold 300 elements at a time, not 600.
    let group = nested_distinct_b(300);
    assert!(scan_output_html(&format!("{group}{group}")).is_ok());
}

#[test]
fn tags_without_end_tags_are_not_nested_elements() {
    // The parser closes an open `<li>` or `<p>` when the next one starts,
    // so the limit counts what is open, not how many start tags there are.
    let items = "<li>x".repeat(50_000);
    assert_eq!(scan_output_html(&items).map(|tags| tags.len()), Ok(50_000));
    assert!(static_html_node_count(&items).is_ok());
    let paragraphs = "<p>x".repeat(50_000);
    assert_eq!(
        scan_output_html(&paragraphs).map(|tags| tags.len()),
        Ok(50_000)
    );
    assert!(static_html_node_count(&paragraphs).is_ok());
}

#[test]
fn deeply_nested_elements_are_refused_quickly() {
    // The parser looked down its whole stack of open elements for each
    // `<div>`: 40,000 of them (200 KB) took 23 seconds in a debug build.
    let page = "<div>".repeat(40_000);
    let refused = HtmlTooLarge::OpenElements;
    quickly("scan", || {
        assert_eq!(scan_output_html(&page).map(|_| ()), Err(refused));
    });
    quickly("count", || {
        assert_eq!(static_html_node_count(&page), Err(refused));
    });
    quickly("validate", || {
        assert_eq!(
            validate_html_fragment_boundary(&page),
            Err(format!("opaque {refused}"))
        );
    });
    quickly("static", || {
        assert!(static_html_in_context(&["div"], &page, StaticHtmlUse::Adopted).is_none());
    });
    quickly("nodes", || {
        assert!(!browser_fragment_matches_nodes(&page, "div", &[]));
    });
}

/// `WAITING` formatting elements waiting on the parser's list, then `tail`
/// pieces of `<div>x</div>`. Each piece reopens all of them (see
/// [`MAX_REOPENED_FORMATTING_ELEMENTS`]). The waiting elements come from
/// `<div><b a="i"></div>`: the `</div>` closes the `<b>` without removing it
/// from the list, and the next `<b>` reopens it. Each `<b>` has its own
/// attribute value, because the list keeps at most three equal ones.
fn reopening(tail: usize) -> String {
    let waiting: String = (0..WAITING)
        .map(|i| format!("<div><b a=\"{i}\"></div>"))
        .collect();
    format!("{waiting}{}", "<div>x</div>".repeat(tail))
}

/// How many elements wait on the list in [`reopening`].
const WAITING: usize = 25;

/// The `tail` at which [`reopening`] copies exactly as much as the limit
/// allows. A reopened `<b a="i">` counts as 2, the element and its
/// attribute. Building the waiting elements reopens the earlier ones each
/// time, 0 + 1 + ... + 24 of them in all, and each piece after that
/// reopens all 25.
fn tail_at_the_reopen_limit() -> usize {
    let building = 2 * WAITING * (WAITING - 1) / 2;
    let per_piece = 2 * WAITING;
    let room = MAX_REOPENED_FORMATTING_ELEMENTS - building;
    // The limit is met exactly, so the page after it is one piece over.
    assert_eq!(room % per_piece, 0);
    room / per_piece
}

#[test]
fn formatting_elements_reopened_up_to_the_limit_are_read_and_one_more_is_refused() {
    let tail = tail_at_the_reopen_limit();
    // The strict fragment check refuses this page for its misnesting,
    // which is not a limit, so its answer is the same as for any such page.
    let strict = "opaque HTML must be a self-contained strict fragment".to_owned();
    assert_eq!(
        outcomes(&reopening(tail)),
        [
            // A `<div>` and a `<b>` for each waiting element, then a `<div>`
            // for each piece.
            ("scan", format!("read {}", 2 * WAITING + tail)),
            ("check", "checked".to_owned()),
            ("validate", strict),
            ("count", format!("{} nodes", WAITING + tail)),
            ("static", "rejected".to_owned()),
            ("nodes", "false".to_owned()),
        ]
    );
    let message = HtmlTooLarge::ReopenedFormatting.to_string();
    assert_eq!(
        outcomes(&reopening(tail + 1)),
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
fn a_page_that_reopens_far_more_than_the_limit_is_refused_quickly() {
    let page = reopening(20_000);
    let refused = HtmlTooLarge::ReopenedFormatting;
    quickly("scan", || {
        assert_eq!(scan_output_html(&page).map(|_| ()), Err(refused));
    });
    quickly("count", || {
        assert_eq!(static_html_node_count(&page), Err(refused));
    });
    quickly("validate", || {
        assert_eq!(
            validate_html_fragment_boundary(&page),
            Err(format!("opaque {refused}"))
        );
    });
}

#[test]
fn tags_that_account_for_more_than_the_parser_makes_do_not_hide_reopening() {
    // A `<b>` that repeats one attribute name 1,024 times makes an element
    // with one attribute from 1,025 counted ones: the scan drops the
    // repeats. Three of them are no credit for what the page reopens later.
    let repeats = " a".repeat(MAX_ATTRIBUTES_PER_TAG);
    let credit = format!("<b{repeats}></b>").repeat(3);
    let tail = tail_at_the_reopen_limit();
    assert!(scan_output_html(&format!("{credit}{}", reopening(tail))).is_ok());
    assert_eq!(
        scan_output_html(&format!("{credit}{}", reopening(tail + 1))).map(|_| ()),
        Err(HtmlTooLarge::ReopenedFormatting)
    );
}

#[test]
fn a_reopened_element_counts_its_attributes() {
    // Each reopened element copies its attributes. 50 waiting `<b>`
    // elements with 1,024 attributes each are reopened 1,225 times while the
    // page builds them, which is 1.2 million attributes copied (about 50 MB)
    // from a page of 500 KB. That is over the limit once each attribute
    // counts, though only 1,225 elements are reopened.
    let waiting: String = (0..50)
        .map(|i| {
            let attributes: String = (0..MAX_ATTRIBUTES_PER_TAG)
                .map(|j| format!(" a{j}=\"{i}\""))
                .collect();
            format!("<div><b{attributes}></div>")
        })
        .collect();
    let page = format!("{waiting}{}", "<div>x</div>".repeat(100));
    let refused = HtmlTooLarge::ReopenedFormatting;
    quickly("scan", || {
        assert_eq!(scan_output_html(&page).map(|_| ()), Err(refused));
    });
    quickly("count", || {
        assert_eq!(static_html_node_count(&page), Err(refused));
    });
}

#[test]
fn pages_that_misnest_many_formatting_tags_are_read() {
    // A `<b>` left open in each paragraph is reopened in the next one, up to
    // three copies at a time. 20,000 such paragraphs reopen about 60,000
    // elements, a fraction of the limit.
    let page = "<p><b>one</p>".repeat(20_000);
    assert_eq!(scan_output_html(&page).map(|tags| tags.len()), Ok(40_000));
    assert!(static_html_node_count(&page).is_ok());
    let swapped = "<b><i>x</b>y</i>".repeat(10_000);
    assert_eq!(
        scan_output_html(&swapped).map(|tags| tags.len()),
        Ok(20_000)
    );
}

#[test]
fn formatting_elements_closed_in_order_reopen_nothing() {
    // Each `<b>` makes the element its own start tag asks for, and no more,
    // however many there are. The unit tests in `src/html_limits.rs` pin the
    // counting of one tag; this checks that real tags add up to nothing.
    let plain = "<b>x</b>".repeat(130_000);
    assert_eq!(scan_output_html(&plain).map(|tags| tags.len()), Ok(130_000));
    let with_attributes = "<b a=1 b=2 c=3>x</b>".repeat(70_000);
    assert_eq!(
        scan_output_html(&with_attributes).map(|tags| tags.len()),
        Ok(70_000)
    );
    assert!(static_html_node_count(&with_attributes).is_ok());
}
