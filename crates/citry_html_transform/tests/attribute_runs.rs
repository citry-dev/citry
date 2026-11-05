//! A tag with a very long run of attributes is read to its end on any
//! stack, and refused.
//!
//! An html5gum release that nests a few calls for each `name="value"`
//! attribute in a row overflows the stack on a long tag and kills the whole
//! process. Version 0.8.4 did so at about 50,000 attributes on the 8 MiB
//! main-thread stack in a release build (about 3,000 on a 512 KiB thread,
//! and far fewer in a debug build). Version 0.9.1 returns to its main loop
//! after each attribute (untitaker/html5gum pull request 158). These tests
//! fail with a crash if a later release nests again, so run them when you
//! upgrade html5gum.
//!
//! Every entry point refuses a tag with more than 1,024 attributes (see
//! `src/html_limits.rs`), but html5gum still reads the rest of the input
//! after the limit, so a tag of 100,000 still exercises the tokenizer.
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

/// Twice what html5gum 0.8.4 read on an 8 MiB stack in a release build.
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
        "scan" => match scan_output_html(html) {
            Ok(tags) => format!("read {}", tags.len()),
            Err(_) => "refused".to_owned(),
        },
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
            match check_output_html(html, &options) {
                Ok(report) => format!("{} events", report.events.len()),
                Err(_) => "refused".to_owned(),
            }
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
            let report = check_output_html(&page, &options).expect("the page has one attribute");
            let embedded = report.events.iter().any(|event| {
                matches!(event, PolicyEvent::Finding(finding)
                    if finding.rule == Rule::JsEmbeddedDocument)
            });
            if embedded { "running code" } else { "inert" }.to_owned()
        }
        "validate" => match validate_html_fragment_boundary(html) {
            Ok(()) => "accepted".to_owned(),
            Err(message) if message.contains("more than 1024 attributes") => "refused".to_owned(),
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
        "count" => match static_html_node_count(html) {
            Ok(count) => format!("{count}"),
            Err(_) => "refused".to_owned(),
        },
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
fn every_entry_point_refuses_a_tag_with_many_attributes() {
    // A tag with three attributes gets each entry point's ordinary answer,
    // and the long tag gets its refusal, after html5gum has read all of it.
    // A refused embedded document counts as running code, and the two
    // comparisons answer that the block does not match.
    for stack_kib in STACKS_KIB {
        for (case, small, large) in [
            ("scan", "read 1", "refused"),
            ("check", "0 events", "refused"),
            ("validate", "accepted", "refused"),
            ("nodes", "false", "false"),
            ("srcdoc", "inert", "running code"),
            ("static_body", "accepted", "rejected"),
            ("count", "1", "refused"),
        ] {
            assert_eq!(run(case, "double", 3, stack_kib), small, "{case}, 3");
            assert_eq!(
                run(case, "double", MANY, stack_kib),
                large,
                "{case} with {MANY} on {stack_kib} KiB"
            );
        }
    }
}

#[test]
fn a_stray_quote_before_the_tag_changes_nothing() {
    // The count comes from the tokenizer itself, so a `="` before the tag
    // cannot hide the tag's attributes from it.
    for stack_kib in STACKS_KIB {
        for shape in [
            "stray_text",
            "stray_comment",
            "stray_single_quoted",
            "stray_script",
        ] {
            for case in ["scan", "validate"] {
                let result = run(case, shape, MANY, stack_kib);
                assert_eq!(result, "refused", "{case} {shape} on {stack_kib} KiB");
            }
        }
    }
}

#[test]
fn attributes_written_other_ways_are_refused_too() {
    for shape in ["single", "unquoted", "bare"] {
        for case in ["scan", "validate"] {
            let result = run(case, shape, MANY, 128);
            assert_eq!(result, "refused", "{case} {shape}");
        }
    }
}
