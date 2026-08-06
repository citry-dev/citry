//! Validation for the shared byte-oriented formatter corpus.

use std::collections::HashSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use citry_template_parser::parse_template;
use serde::Deserialize;

use crate::projection::{ProjectionCapability, verify_contract_projection};
use crate::{
    EmbeddedFormatPlan, EmbeddedFormatResult, EmbeddedLanguage, EmbeddedRegionKind,
    PYTHON_EXPRESSION_PROVIDER, finish_embedded_format, format_template, prepare_embedded_format,
};

const CORPUS_ROOT: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/v1");

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct CorpusIndex {
    schema_version: u32,
    python_expression_provider: String,
    cases: Vec<CorpusCase>,
    embedded_cases: Vec<EmbeddedCase>,
    python_hosts: Vec<PythonHostCase>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct EmbeddedCase {
    id: String,
    category: String,
    input: Option<String>,
    input_text: Option<String>,
    requests: Vec<ExpectedEmbeddedRequest>,
    plan_notices: Vec<ExpectedNotice>,
    results: Vec<FakeProviderResult>,
    expected: Option<String>,
    expected_text: Option<String>,
    expected_error: Option<ExpectedError>,
    outcome_notices: Vec<ExpectedNotice>,
    providers: Option<Vec<String>>,
    features: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExpectedEmbeddedRequest {
    language: ExpectedEmbeddedLanguage,
    kind: ExpectedEmbeddedRegionKind,
    source: String,
    virtual_source: String,
    base_indent: usize,
    newline: String,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
enum ExpectedEmbeddedLanguage {
    Javascript,
    Css,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
enum ExpectedEmbeddedRegionKind {
    ScriptBody,
    StyleBody,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExpectedNotice {
    code: String,
    contains: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(tag = "status", rename_all = "kebab-case", deny_unknown_fields)]
enum FakeProviderResult {
    Formatted {
        region: usize,
        text: String,
        provider: String,
    },
    Unchanged {
        region: usize,
        #[serde(rename = "provider")]
        _provider: String,
    },
    Unavailable {
        region: usize,
        #[serde(rename = "provider")]
        _provider: String,
        message: String,
    },
    Error {
        region: usize,
        #[serde(rename = "provider")]
        _provider: String,
        message: String,
    },
    StalePlan {
        region: usize,
        text: String,
        provider: String,
    },
    Duplicate {
        region: usize,
        text: String,
        provider: String,
    },
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct CorpusCase {
    id: String,
    capability: CorpusCapability,
    category: String,
    input: Option<String>,
    input_text: Option<String>,
    expected: Option<String>,
    expected_text: Option<String>,
    expected_error: Option<ExpectedError>,
    features: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExpectedError {
    phase: ErrorPhase,
    code: String,
    contains: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PythonHostCase {
    id: String,
    category: String,
    input: Option<String>,
    input_text: Option<String>,
    expected: Option<String>,
    expected_text: Option<String>,
    expected_error: Option<PythonHostExpectedError>,
    features: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PythonHostExpectedError {
    code: String,
    contains: Option<String>,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
enum ErrorPhase {
    Parse,
    Format,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
enum CorpusCapability {
    OpeningTags,
    StructuralLayout,
    PythonExpressions,
}

impl CorpusCapability {
    fn projection(self) -> Option<ProjectionCapability> {
        match self {
            Self::OpeningTags | Self::StructuralLayout | Self::PythonExpressions => {
                Some(ProjectionCapability::PythonExpressions)
            }
        }
    }
}

#[test]
fn corpus_index_and_contract_pairs_are_valid() {
    let root = Path::new(CORPUS_ROOT);
    let index_source = fs::read_to_string(root.join("index.json")).expect("read corpus index");
    let index: CorpusIndex = serde_json::from_str(&index_source).expect("parse corpus index");
    assert_eq!(
        index.schema_version, 1,
        "unsupported formatter corpus version"
    );
    assert_eq!(
        index.python_expression_provider, PYTHON_EXPRESSION_PROVIDER,
        "formatter corpus provider pin"
    );
    assert!(
        !index.cases.is_empty(),
        "formatter corpus must not be empty"
    );

    let mut ids = HashSet::new();
    let mut features = HashSet::new();
    let mut referenced_files = HashSet::new();
    for case in index.cases {
        assert!(
            ids.insert(case.id.clone()),
            "duplicate corpus id: {}",
            case.id
        );
        assert!(
            !case.category.trim().is_empty(),
            "{} has no category",
            case.id
        );
        assert!(
            !case.features.is_empty(),
            "{} has no feature labels",
            case.id
        );
        assert!(
            case.features
                .iter()
                .all(|feature| !feature.trim().is_empty()),
            "{} has an empty feature label",
            case.id
        );
        features.extend(case.features.iter().cloned());

        let input = read_case_source(
            root,
            case.input.as_deref(),
            case.input_text.as_deref(),
            &case.id,
            "input",
            &mut referenced_files,
        );
        let has_expected = case.expected.is_some() || case.expected_text.is_some();
        match (has_expected, &case.expected_error) {
            (true, None) => {
                let expected = read_case_source(
                    root,
                    case.expected.as_deref(),
                    case.expected_text.as_deref(),
                    &case.id,
                    "expected output",
                    &mut referenced_files,
                );
                parse_template(&input, None, None)
                    .unwrap_or_else(|error| panic!("{} input does not parse: {error}", case.id));
                parse_template(&expected, None, None).unwrap_or_else(|error| {
                    panic!("{} expected output does not parse: {error}", case.id)
                });
                verify_contract_projection(
                    &input,
                    &expected,
                    case.capability
                        .projection()
                        .expect("all capabilities project"),
                )
                .unwrap_or_else(|error| {
                    panic!("{} violates its formatter contract: {error}", case.id)
                });

                let stable_expected = format_template(&expected).unwrap_or_else(|error| {
                    panic!(
                        "{} expected output is not formatter-stable: {error}",
                        case.id
                    )
                });
                assert_eq!(
                    stable_expected, expected,
                    "{} expected output is not formatter-stable",
                    case.id,
                );

                let actual = format_template(&input)
                    .unwrap_or_else(|error| panic!("{} did not format: {error}", case.id));
                assert_eq!(actual, expected, "{} formatter output", case.id);
                assert_eq!(
                    format_template(&actual)
                        .unwrap_or_else(|error| panic!("{} did not reformat: {error}", case.id)),
                    actual,
                    "{} formatter output is not idempotent",
                    case.id,
                );
            }
            (false, Some(expected_error)) => {
                assert!(
                    expected_error.code.starts_with("citry."),
                    "{} has a non-Citry error code: {}",
                    case.id,
                    expected_error.code,
                );
                assert!(
                    expected_error
                        .contains
                        .as_ref()
                        .is_none_or(|needle| !needle.trim().is_empty()),
                    "{} has an empty expected error substring",
                    case.id
                );
                validate_expected_error(&case.id, &input, expected_error);
            }
            _ => panic!(
                "{} must define exactly one expected output or error",
                case.id
            ),
        }
    }

    for case in index.embedded_cases {
        assert!(
            ids.insert(case.id.clone()),
            "duplicate corpus id: {}",
            case.id
        );
        assert!(
            !case.category.trim().is_empty(),
            "{} has no category",
            case.id
        );
        assert!(
            !case.features.is_empty(),
            "{} has no feature labels",
            case.id
        );
        assert!(
            case.features
                .iter()
                .all(|feature| !feature.trim().is_empty()),
            "{} has an empty feature label",
            case.id
        );
        features.extend(case.features.iter().cloned());

        let input = read_case_source(
            root,
            case.input.as_deref(),
            case.input_text.as_deref(),
            &case.id,
            "input",
            &mut referenced_files,
        );
        let plan = prepare_embedded_format(&input)
            .unwrap_or_else(|error| panic!("{} did not prepare: {error}", case.id));
        validate_embedded_plan(&case, &input, &plan);
        let results = fake_provider_results(&case, &plan);

        let has_expected = case.expected.is_some() || case.expected_text.is_some();
        match (has_expected, &case.expected_error) {
            (true, None) => {
                let expected = read_case_source(
                    root,
                    case.expected.as_deref(),
                    case.expected_text.as_deref(),
                    &case.id,
                    "expected output",
                    &mut referenced_files,
                );
                let outcome = finish_embedded_format(&plan, &results)
                    .unwrap_or_else(|error| panic!("{} did not finish: {error}", case.id));
                assert_eq!(outcome.source(), expected, "{} formatter output", case.id);
                validate_notices(&case.id, outcome.notices(), &case.outcome_notices);
                if let Some(expected_providers) = &case.providers {
                    assert_eq!(
                        outcome.providers(),
                        expected_providers,
                        "{} provider identities",
                        case.id
                    );
                }

                let repeated_plan = prepare_embedded_format(outcome.source())
                    .unwrap_or_else(|error| panic!("{} did not reprepare: {error}", case.id));
                let repeated_results = fake_provider_results(&case, &repeated_plan);
                let repeated = finish_embedded_format(&repeated_plan, &repeated_results)
                    .unwrap_or_else(|error| panic!("{} did not refinish: {error}", case.id));
                assert_eq!(
                    repeated.source(),
                    outcome.source(),
                    "{} embedded formatting is not idempotent",
                    case.id
                );
            }
            (false, Some(expected_error)) => {
                assert_eq!(
                    expected_error.phase,
                    ErrorPhase::Format,
                    "{} embedded provider failures belong to the format phase",
                    case.id
                );
                let error = finish_embedded_format(&plan, &results)
                    .expect_err("invalid embedded results unexpectedly finished");
                assert_eq!(error.code(), expected_error.code, "{} error code", case.id);
                if let Some(needle) = &expected_error.contains {
                    assert!(
                        error.to_string().contains(needle),
                        "{} expected error containing {needle:?}, got {error:?}",
                        case.id
                    );
                }
            }
            _ => panic!(
                "{} must define exactly one expected output or error",
                case.id
            ),
        }
    }

    for case in index.python_hosts {
        assert!(
            ids.insert(case.id.clone()),
            "duplicate corpus id: {}",
            case.id
        );
        assert!(
            !case.category.trim().is_empty(),
            "{} has no category",
            case.id
        );
        assert!(
            !case.features.is_empty(),
            "{} has no feature labels",
            case.id
        );
        assert!(
            case.features
                .iter()
                .all(|feature| !feature.trim().is_empty()),
            "{} has an empty feature label",
            case.id
        );
        features.extend(case.features.iter().cloned());

        let _input = read_case_source(
            root,
            case.input.as_deref(),
            case.input_text.as_deref(),
            &case.id,
            "input",
            &mut referenced_files,
        );
        let has_expected = case.expected.is_some() || case.expected_text.is_some();
        match (has_expected, &case.expected_error) {
            (true, None) => {
                let _expected = read_case_source(
                    root,
                    case.expected.as_deref(),
                    case.expected_text.as_deref(),
                    &case.id,
                    "expected output",
                    &mut referenced_files,
                );
            }
            (false, Some(expected_error)) => {
                assert!(
                    expected_error.code.starts_with("citry.format."),
                    "{} has a non-formatter error code: {}",
                    case.id,
                    expected_error.code,
                );
                assert!(
                    expected_error
                        .contains
                        .as_ref()
                        .is_none_or(|needle| !needle.trim().is_empty()),
                    "{} has an empty expected error substring",
                    case.id,
                );
            }
            _ => panic!(
                "{} must define exactly one expected output or error",
                case.id
            ),
        }
    }

    let actual_files = collect_case_files(root);
    assert_eq!(
        actual_files, referenced_files,
        "every formatter input/expected file must be indexed exactly once"
    );

    for required in REQUIRED_FEATURES {
        assert!(
            features.contains(*required),
            "formatter corpus is missing required feature label {required:?}"
        );
    }
}

const REQUIRED_FEATURES: &[&str] = &[
    "attribute-kinds",
    "block-container",
    "comment-only-body",
    "comment-only-tag",
    "component",
    "contextual-option",
    "control-exhaustive",
    "control-optional",
    "doctype",
    "embedded-delimiter-conflict",
    "embedded-idempotence",
    "embedded-provider-error",
    "embedded-provider-unavailable",
    "embedded-result-duplicate",
    "embedded-result-missing",
    "embedded-result-stale",
    "embedded-virtual-mapping",
    "delimiter-spacing",
    "crlf",
    "end-tag-directive",
    "end-tag-comment",
    "expression-byte-exact",
    "fragment",
    "html-comment",
    "invalid-citry",
    "invalid-python-host",
    "invalid-suppression",
    "lowercase-component",
    "mixed-content",
    "missing-final-newline",
    "multiline-attribute",
    "nested-template",
    "python-host-framing",
    "python-host-crlf",
    "python-host-reverse-rewrite",
    "python-literal-concatenation",
    "python-literal-escape",
    "python-comment",
    "protected-attribute",
    "protected-expression",
    "protected-node",
    "raw-body",
    "rendered-unicode-space",
    "script-body",
    "select",
    "slot-data",
    "source-column",
    "suppression",
    "style-body",
    "template-comment",
    "textarea-body",
    "unicode",
    "unbreakable-token",
];

fn validate_embedded_plan(case: &EmbeddedCase, input: &str, plan: &EmbeddedFormatPlan) {
    let repeated = prepare_embedded_format(input).expect("repeat embedded preparation");
    assert_eq!(
        plan.id(),
        repeated.id(),
        "{} unstable plan identity",
        case.id
    );
    assert_eq!(
        plan.requests().len(),
        case.requests.len(),
        "{} request count",
        case.id
    );

    let prepared = format_template(input).expect("M2 preparation formats valid input");
    for (request, expected) in plan.requests().iter().zip(&case.requests) {
        assert!(
            repeated
                .requests()
                .iter()
                .any(|other| other.id() == request.id()),
            "{} has an unstable region identity",
            case.id
        );
        assert_eq!(
            request.source(),
            expected.source,
            "{} request source",
            case.id
        );
        assert_eq!(
            request.virtual_source(),
            expected.virtual_source,
            "{} virtual source",
            case.id
        );
        assert_eq!(
            request.base_indent(),
            expected.base_indent,
            "{} base indentation",
            case.id
        );
        assert_eq!(request.newline(), expected.newline, "{} newline", case.id);
        assert_eq!(
            &prepared[request.byte_range()],
            request.source(),
            "{} byte range does not map to the prepared source",
            case.id
        );
        match (request.language(), expected.language) {
            (EmbeddedLanguage::JavaScript, ExpectedEmbeddedLanguage::Javascript)
            | (EmbeddedLanguage::Css, ExpectedEmbeddedLanguage::Css) => {}
            (actual, expected) => {
                panic!("{} language mismatch: {actual:?} != {expected:?}", case.id)
            }
        }
        match (request.kind(), expected.kind) {
            (EmbeddedRegionKind::ScriptBody, ExpectedEmbeddedRegionKind::ScriptBody)
            | (EmbeddedRegionKind::StyleBody, ExpectedEmbeddedRegionKind::StyleBody) => {}
            (actual, expected) => panic!(
                "{} region kind mismatch: {actual:?} != {expected:?}",
                case.id
            ),
        }
    }
    validate_notices(&case.id, plan.notices(), &case.plan_notices);
}

fn validate_notices(
    case_id: &str,
    actual: &[crate::EmbeddedFormatNotice],
    expected: &[ExpectedNotice],
) {
    assert_eq!(actual.len(), expected.len(), "{case_id} notice count");
    for (actual, expected) in actual.iter().zip(expected) {
        assert_eq!(actual.code(), expected.code, "{case_id} notice code");
        assert!(
            actual.message().contains(&expected.contains),
            "{case_id} expected notice containing {:?}, got {:?}",
            expected.contains,
            actual.message()
        );
    }
}

fn fake_provider_results(
    case: &EmbeddedCase,
    plan: &EmbeddedFormatPlan,
) -> Vec<EmbeddedFormatResult> {
    let mut results = Vec::new();
    for fake in &case.results {
        let region = match fake {
            FakeProviderResult::Formatted { region, .. }
            | FakeProviderResult::Unchanged { region, .. }
            | FakeProviderResult::Unavailable { region, .. }
            | FakeProviderResult::Error { region, .. }
            | FakeProviderResult::StalePlan { region, .. }
            | FakeProviderResult::Duplicate { region, .. } => *region,
        };
        let region_id = plan
            .requests()
            .get(region)
            .unwrap_or_else(|| panic!("{} invalid fixture region {region}", case.id))
            .id()
            .to_string();
        let plan_id = plan.id().to_string();
        match fake {
            FakeProviderResult::Formatted { text, provider, .. } => {
                results.push(EmbeddedFormatResult::Formatted {
                    plan_id,
                    region_id,
                    text: text.clone(),
                    provider: Some(provider.clone()),
                });
            }
            FakeProviderResult::Unchanged { .. } => {
                results.push(EmbeddedFormatResult::Unchanged { plan_id, region_id });
            }
            FakeProviderResult::Unavailable { message, .. } => {
                results.push(EmbeddedFormatResult::Unavailable {
                    plan_id,
                    region_id,
                    message: message.clone(),
                });
            }
            FakeProviderResult::Error { message, .. } => {
                results.push(EmbeddedFormatResult::Error {
                    plan_id,
                    region_id,
                    message: message.clone(),
                });
            }
            FakeProviderResult::StalePlan { text, provider, .. } => {
                results.push(EmbeddedFormatResult::Formatted {
                    plan_id: format!("{plan_id}-stale"),
                    region_id,
                    text: text.clone(),
                    provider: Some(provider.clone()),
                });
            }
            FakeProviderResult::Duplicate { text, provider, .. } => {
                let result = EmbeddedFormatResult::Formatted {
                    plan_id,
                    region_id,
                    text: text.clone(),
                    provider: Some(provider.clone()),
                };
                results.push(result.clone());
                results.push(result);
            }
        }
    }
    results
}

fn validate_expected_error(case_id: &str, input: &str, expected: &ExpectedError) {
    let format_error = format_template(input).expect_err("error corpus input formatted");
    assert_eq!(format_error.code(), expected.code, "{case_id} error code");
    if let Some(needle) = &expected.contains {
        assert!(
            format_error.to_string().contains(needle),
            "{case_id} formatter error did not contain {needle:?}: {format_error}"
        );
    }

    match expected.phase {
        ErrorPhase::Parse => {
            assert_eq!(
                expected.code, "citry.format.syntax",
                "{case_id} parse errors use the public formatter syntax code"
            );
            let error = parse_template(input, None, None)
                .expect_err("parse-error corpus input unexpectedly parsed")
                .to_string();
            if let Some(needle) = &expected.contains {
                assert!(
                    error.contains(needle),
                    "{case_id} expected error containing {needle:?}, got {error:?}"
                );
            }
        }
        ErrorPhase::Format => {
            assert!(
                expected.code.starts_with("citry.format."),
                "{case_id} formatter errors use the citry.format.* namespace"
            );
            parse_template(input, None, None)
                .unwrap_or_else(|error| panic!("{case_id} format-error input must parse: {error}"));
            assert!(
                format_error.range().is_some(),
                "{case_id} formatter errors carry a source range"
            );
        }
    }
}

fn corpus_path(root: &Path, relative: &str, case_id: &str) -> PathBuf {
    let relative = Path::new(relative);
    assert!(
        !relative.is_absolute()
            && relative
                .components()
                .all(|component| matches!(component, Component::Normal(_))),
        "{case_id} has a non-local corpus path: {}",
        relative.display()
    );
    let path = root.join(relative);
    assert!(
        path.is_file(),
        "{case_id} corpus file is missing: {}",
        path.display()
    );
    path
}

fn read_case_source(
    root: &Path,
    file: Option<&str>,
    inline: Option<&str>,
    case_id: &str,
    label: &str,
    referenced_files: &mut HashSet<PathBuf>,
) -> String {
    match (file, inline) {
        (Some(relative), None) => {
            let path = corpus_path(root, relative, case_id);
            referenced_files.insert(path.clone());
            read_utf8(&path, case_id)
        }
        (None, Some(content)) => content.to_string(),
        _ => panic!("{case_id} must define exactly one file or inline {label}"),
    }
}

fn read_utf8(path: &Path, case_id: &str) -> String {
    String::from_utf8(
        fs::read(path).unwrap_or_else(|error| {
            panic!("failed to read {} for {case_id}: {error}", path.display())
        }),
    )
    .unwrap_or_else(|error| panic!("{} for {case_id} is not UTF-8: {error}", path.display()))
}

fn collect_case_files(root: &Path) -> HashSet<PathBuf> {
    let mut pending = vec![root.to_path_buf()];
    let mut files = HashSet::new();
    while let Some(directory) = pending.pop() {
        for entry in fs::read_dir(&directory)
            .unwrap_or_else(|error| panic!("failed to read {}: {error}", directory.display()))
        {
            let path = entry.expect("read corpus directory entry").path();
            if path.is_dir() {
                pending.push(path);
            } else if path
                .file_name()
                .and_then(|name| name.to_str())
                .is_some_and(|name| {
                    name.ends_with(".input.citry-html")
                        || name.ends_with(".expected.citry-html")
                        || name.ends_with(".input.py")
                        || name.ends_with(".expected.py")
                })
            {
                files.insert(path);
            }
        }
    }
    files
}
