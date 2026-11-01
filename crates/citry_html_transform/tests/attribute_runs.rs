//! A tag with a very long run of attributes is read on any stack.
//!
//! Upstream html5gum 0.8.4 nests a few calls for each `name="value"`
//! attribute in a row, so one tag with about 50,000 of them overflowed the
//! 8 MiB main-thread stack in a release build and killed the whole process
//! (about 3,000 on a 512 KiB thread, and far fewer in a debug build). The
//! patched copy in `third_party/rust/html5gum` returns to its main loop
//! after each attribute. These tests fail with a crash if that patch is
//! lost, for example when html5gum is upgraded.
//!
//! A stack overflow cannot be caught, so each case runs in a child process:
//! this test binary starts itself again with `--exact child` and an
//! environment variable that names the case, and the parent checks that the
//! child exited normally and printed the expected outcome.

use std::collections::HashSet;
use std::process::Command;

use citry_html_transform::hydration_structure::{
    browser_fragment_matches_nodes, ExpectedNodeEvent,
};
use citry_html_transform::output_policy::{
    check_output_html, JavascriptMode, OutputPolicyOptions, PolicyEvent, PolicyPass, Rule,
};
use citry_html_transform::output_scanner::{scan_output_html, validate_html_fragment_boundary};
use citry_html_transform::static_html::{
    static_html_in_context, static_html_node_count, StaticHtmlUse,
};

const CASE: &str = "CITRY_ATTRIBUTE_RUN_CASE";
const SHAPE: &str = "CITRY_ATTRIBUTE_RUN_SHAPE";
const COUNT: &str = "CITRY_ATTRIBUTE_RUN_COUNT";
const STACK_KIB: &str = "CITRY_ATTRIBUTE_RUN_STACK_KIB";

/// Twice what upstream html5gum read on an 8 MiB stack in a release build.
const MANY: usize = 100_000;

/// The smallest default thread stack Python code meets (musl Linux), and
/// the usual main-thread stack, which runs the work without a new segment.
const STACKS_KIB: [usize; 2] = [128, 8 * 1024];

/// One tag with `count` attributes written the way `shape` names.
///
/// The `stray_*` shapes put a `="` before the tag (as text, in a comment,
/// in a single-quoted value, or in a script) and end every value with `=`.
/// An independent review used them to show that a count of the attributes
/// made before the tokenizer runs can be thrown off; here they show the
/// tokenizer itself reads them on any stack.
fn page(shape: &str, count: usize) -> String {
    let value = if shape.starts_with("stray_") {
        "x="
    } else {
        "v"
    };
    let attributes: String = (0..count)
        .map(|i| match shape {
            "single" => format!(" a{i}='v'"),
            "unquoted" => format!(" a{i}=v"),
            "bare" => format!(" a{i}"),
            _ => format!(" a{i}=\"{value}\""),
        })
        .collect();
    let (before, open) = match shape {
        "double" | "single" | "unquoted" | "bare" => ("", "<p"),
        "stray_text" => ("=\"", "<p"),
        "stray_comment" => ("<!-- =\" -->", "<p"),
        "stray_single_quoted" => ("", "<p t='=\"'"),
        "stray_script" => ("<script>var s = '=\"';</script>", "<p"),
        _ => panic!("unknown shape {shape}"),
    };
    format!("{before}{open}{attributes}>x</p>")
}

/// What one entry point did with `html`, as one word or a short phrase.
fn outcome(case: &str, html: &str) -> String {
    match case {
        "scan" => format!("read {}", scan_output_html(html).len()),
        "check" => {
            let trusted = HashSet::new();
            let options = OutputPolicyOptions {
                pass: PolicyPass::Settled,
                csp: true,
                javascript: Some(JavascriptMode::Warn),
                marker_prefix: None,
                trusted_tag_starts: &trusted,
                omit_handler_marker: None,
            };
            format!("{} events", check_output_html(html, &options).events.len())
        }
        "srcdoc" => {
            // The attribute value is one small attribute for the page's own
            // scan; the document inside it is scanned again once decoded.
            let inner = html.replace('&', "&amp;").replace('"', "&quot;");
            let page = format!("<iframe srcdoc=\"{inner}\"></iframe>");
            let trusted = HashSet::new();
            let options = OutputPolicyOptions {
                pass: PolicyPass::Settled,
                csp: false,
                javascript: Some(JavascriptMode::Warn),
                marker_prefix: None,
                trusted_tag_starts: &trusted,
                omit_handler_marker: None,
            };
            let report = check_output_html(&page, &options);
            let embedded = report.events.iter().any(|event| {
                matches!(event, PolicyEvent::Finding(finding)
                    if finding.rule == Rule::JsEmbeddedDocument)
            });
            if embedded { "running code" } else { "inert" }.to_owned()
        }
        "validate" => match validate_html_fragment_boundary(html) {
            Ok(()) => "accepted".to_owned(),
            Err(message) => format!("refused: {message}"),
        },
        "nodes" => {
            let events = [
                ExpectedNodeEvent::Open {
                    tag: "p".to_owned(),
                    attributes: Vec::new(),
                },
                ExpectedNodeEvent::Close {
                    tag: "p".to_owned(),
                },
            ];
            // The attributes differ from the expected ones, so the answer
            // is a mismatch; what matters is that it returns.
            browser_fragment_matches_nodes(html, "div", &events).to_string()
        }
        "static_body" => {
            // The text `<body` makes the check read the block's tags. It is
            // in a single-quoted value, so the block has no document tag.
            let block = html.replacen("<p", "<p t='<body'", 1);
            match static_html_in_context(&["div"], &block, StaticHtmlUse::Replaced) {
                Some(_) => "accepted".to_owned(),
                None => "rejected".to_owned(),
            }
        }
        "count" => format!("{}", static_html_node_count(html)),
        _ => panic!("unknown case {case}"),
    }
}

/// The child half: runs one case on a thread with the requested stack and
/// prints its outcome. Without the environment variables it does nothing.
#[test]
fn child() {
    let (Ok(case), Ok(shape), Ok(count), Ok(stack_kib)) = (
        std::env::var(CASE),
        std::env::var(SHAPE),
        std::env::var(COUNT),
        std::env::var(STACK_KIB),
    ) else {
        return;
    };
    let html = page(&shape, count.parse().unwrap());
    let result = std::thread::Builder::new()
        .stack_size(stack_kib.parse::<usize>().unwrap() * 1024)
        .spawn(move || outcome(&case, &html))
        .unwrap()
        .join()
        .expect("the case panicked");
    println!("OUTCOME: {result}");
}

/// Run one case in a child process. Returns the outcome it printed, or
/// panics with how the child died.
fn run(case: &str, shape: &str, count: usize, stack_kib: usize) -> String {
    let output = Command::new(std::env::current_exe().unwrap())
        .args(["--exact", "child", "--nocapture", "--test-threads=1"])
        .env(CASE, case)
        .env(SHAPE, shape)
        .env(COUNT, count.to_string())
        .env(STACK_KIB, stack_kib.to_string())
        .output()
        .unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    let printed = stdout
        .lines()
        // The test harness prints `test child ... ` on the same line first.
        .find_map(|line| line.split_once("OUTCOME: "))
        .map(|(_, outcome)| outcome.to_owned());
    printed.unwrap_or_else(|| {
        panic!(
            "{case} with {count} {shape} attributes on a {stack_kib} KiB stack died: {:?}",
            output.status
        )
    })
}

#[test]
fn every_entry_point_reads_a_tag_with_many_attributes() {
    // The answers are the ones a tag with three attributes gets, so each
    // entry point read the whole tag rather than giving up on it.
    // `static_body` also parses the block with html5ever, whose time grows
    // with the square of the attribute count, so it gets a smaller tag that
    // still overflowed upstream html5gum on the segment `run_tokenizer`
    // moves to. `count` parses only with html5ever, so the control is
    // enough for it.
    for stack_kib in STACKS_KIB {
        for (case, expected, count) in [
            ("scan", "read 1", MANY),
            ("check", "0 events", MANY),
            ("validate", "accepted", MANY),
            ("nodes", "false", MANY),
            ("srcdoc", "inert", MANY),
            ("static_body", "accepted", 20_000),
            ("count", "1", 3),
        ] {
            assert_eq!(run(case, "double", 3, stack_kib), expected, "{case}, 3");
            assert_eq!(
                run(case, "double", count, stack_kib),
                expected,
                "{case} with {count} on {stack_kib} KiB"
            );
        }
    }
}

#[test]
fn a_stray_quote_before_the_tag_changes_nothing() {
    for stack_kib in STACKS_KIB {
        for shape in [
            "stray_text",
            "stray_comment",
            "stray_single_quoted",
            "stray_script",
        ] {
            let scan = run("scan", shape, MANY, stack_kib);
            let tags = if shape == "stray_script" { 2 } else { 1 };
            assert_eq!(scan, format!("read {tags}"), "{shape} on {stack_kib} KiB");
            let validate = run("validate", shape, MANY, stack_kib);
            assert_eq!(validate, "accepted", "{shape} on {stack_kib} KiB");
        }
    }
}

#[test]
fn attributes_written_other_ways_are_read_too() {
    for shape in ["single", "unquoted", "bare"] {
        for case in ["scan", "validate"] {
            let result = run(case, shape, MANY, 128);
            assert!(!result.starts_with("refused"), "{case} {shape}: {result}");
        }
    }
}
