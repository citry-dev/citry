//! A tag with a very long run of attributes is refused instead of aborting
//! the process.
//!
//! html5gum nests several calls for each `name="value"` attribute in a row, so
//! one tag with about 20,000 of them overflowed the stack and killed the
//! whole process (about 3,000 on a 512 KiB thread). A stack overflow cannot
//! be caught, so each case runs in a child process: this test binary starts
//! itself again with `--exact child` and an environment variable that names
//! the case, and the parent checks that the child exited normally and
//! printed the expected outcome.

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
use citry_html_transform::MAX_ATTRIBUTE_RUN;

const CASE: &str = "CITRY_ATTRIBUTE_LIMIT_CASE";
const SHAPE: &str = "CITRY_ATTRIBUTE_LIMIT_SHAPE";
const COUNT: &str = "CITRY_ATTRIBUTE_LIMIT_COUNT";
const STACK_KIB: &str = "CITRY_ATTRIBUTE_LIMIT_STACK_KIB";

/// One tag with `count` attributes written the way `shape` names.
fn tag(shape: &str, count: usize) -> String {
    let attributes: String = (0..count)
        .map(|i| match shape {
            "double" => format!(" a{i}=\"v\""),
            "single" => format!(" a{i}='v'"),
            "unquoted" => format!(" a{i}=v"),
            "bare" => format!(" a{i}"),
            _ => panic!("unknown shape {shape}"),
        })
        .collect();
    format!("<p{attributes}>x</p>")
}

/// What one entry point did with `html`, as one word.
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
                Ok(_) => "read".to_owned(),
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
            let report =
                check_output_html(&page, &options).expect("the page itself has one attribute");
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
            // The attributes differ from the expected ones, so a page the
            // scan reads is a mismatch too; what matters is that it returns.
            browser_fragment_matches_nodes(html, "div", &events).to_string()
        }
        "static_body" => {
            // The text `<body` makes the check read the block's tags. It is
            // in a single-quoted value, so the block has no document tag
            // and the attributes after it are the only run.
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
    let html = tag(&shape, count.parse().unwrap());
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

const ENTRY_POINTS: [&str; 5] = ["scan", "check", "validate", "nodes", "static_body"];

#[test]
fn a_tag_with_20000_attributes_is_refused_on_every_entry_point() {
    for stack_kib in [128, 512, 8 * 1024] {
        for case in ENTRY_POINTS {
            let result = run(case, "double", 20_000, stack_kib);
            let refused = match case {
                "nodes" => result == "false",
                "static_body" => result == "rejected",
                _ => result.starts_with("refused"),
            };
            assert!(refused, "{case} on {stack_kib} KiB: {result}");
        }
    }
}

#[test]
fn a_document_in_an_attribute_with_20000_attributes_counts_as_running_code() {
    // A short document is inert, so the answer below comes from the limit.
    assert_eq!(run("srcdoc", "double", 10, 512), "inert");
    for stack_kib in [128, 512] {
        let result = run("srcdoc", "double", 20_000, stack_kib);
        assert_eq!(result, "running code", "{stack_kib} KiB");
    }
}

#[test]
fn a_run_at_the_limit_is_read_even_on_a_small_stack() {
    // In a debug build the nested calls need about 6 MiB for this many
    // attributes, so this also shows the tokenizer moves to a larger stack
    // when the thread has too little.
    for stack_kib in [128, 512] {
        for case in ["scan", "check", "validate"] {
            let result = run(case, "double", MAX_ATTRIBUTE_RUN, stack_kib);
            assert!(!result.starts_with("refused"), "{case}: {result}");
        }
        let result = run("nodes", "double", MAX_ATTRIBUTE_RUN, stack_kib);
        assert_eq!(result, "false", "the attributes differ from the expected");
        let result = run("static_body", "double", MAX_ATTRIBUTE_RUN, stack_kib);
        assert_eq!(result, "accepted", "{stack_kib} KiB");
    }
}

#[test]
fn one_attribute_over_the_limit_is_refused() {
    let result = run("scan", "double", MAX_ATTRIBUTE_RUN + 1, 512);
    assert_eq!(result, "refused");
    let result = run("validate", "double", MAX_ATTRIBUTE_RUN + 1, 512);
    assert!(
        result.starts_with("refused: opaque HTML has a tag with more than"),
        "{result}"
    );
}

#[test]
fn attributes_that_do_not_nest_are_read_without_a_limit() {
    // None of these keep html5gum inside one call, so a very long tag is
    // read as it always was, even on a thread with a small stack.
    for shape in ["single", "unquoted", "bare"] {
        for case in ["scan", "validate"] {
            let result = run(case, shape, 100_000, 128);
            assert!(!result.starts_with("refused"), "{case} {shape}: {result}");
        }
    }
}

#[test]
fn the_html5ever_parse_of_a_long_tag_does_not_nest() {
    // `static_html_node_count` parses with html5ever's own tokenizer, which
    // reads attributes in a loop.
    let result = run("count", "double", 20_000, 128);
    assert_eq!(result, "1");
}
