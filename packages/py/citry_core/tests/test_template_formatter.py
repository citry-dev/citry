"""Tests for the Rust-backed template formatter Python surface."""

from __future__ import annotations

import json
import pickle
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from citry_core import _rust
from citry_core.template_formatter import (
    EmbeddedFormatResult,
    EmbeddedLanguage,
    EmbeddedRegionKind,
    EmbeddedResultStatus,
    TemplateFormatError,
    finish_embedded_format,
    format_template,
    prepare_embedded_format,
    python_expression_provider,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_ROOT = REPO_ROOT / "crates" / "citry_template_formatter" / "tests" / "fixtures" / "v1"


def test_formats_authored_template_text() -> None:
    source = '<c-CButton  class = "primary"  disabled ></c-CButton>'
    expected = '<c-CButton class="primary" disabled></c-CButton>'

    assert _rust.template_formatter.format_template(source) == expected
    assert format_template(source) == expected
    assert format_template(expected) == expected


def test_python_binding_consumes_the_shared_structural_corpus() -> None:
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))
    for case in index["cases"]:
        if "expected_error" in case:
            continue
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")
        expected = case.get("expected_text")
        if expected is None:
            expected = (CORPUS_ROOT / case["expected"]).read_text(encoding="utf-8")

        assert _rust.template_formatter.format_template(source) == expected, case["id"]
        assert format_template(source) == expected, case["id"]


def test_python_binding_consumes_the_shared_embedded_corpus() -> None:
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))
    for case in index["embedded_cases"]:
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")
        plan = prepare_embedded_format(source)
        assert len(plan.requests) == len(case["requests"]), case["id"]
        for request, expected_request in zip(plan.requests, case["requests"], strict=True):
            assert request.language.value == expected_request["language"], case["id"]
            assert request.kind.value == expected_request["kind"], case["id"]
            assert request.source == expected_request["source"], case["id"]
            assert request.virtual_source == expected_request["virtual_source"], case["id"]
            assert request.base_indent == expected_request["base_indent"], case["id"]
            assert request.newline == expected_request["newline"], case["id"]
        assert [notice.code for notice in plan.notices] == [notice["code"] for notice in case["plan_notices"]], case[
            "id"
        ]
        results = _embedded_corpus_results(plan, case["results"])
        expected_error = case.get("expected_error")
        if expected_error is not None:
            with pytest.raises(TemplateFormatError) as raised:
                finish_embedded_format(plan, results)
            assert raised.value.code == expected_error["code"], case["id"]
            assert expected_error["contains"] in str(raised.value), case["id"]
            continue
        outcome = finish_embedded_format(plan, results)
        expected = case.get("expected_text")
        if expected is None:
            expected = (CORPUS_ROOT / case["expected"]).read_text(encoding="utf-8")
        assert outcome.source == expected, case["id"]
        assert [notice.code for notice in outcome.notices] == [notice["code"] for notice in case["outcome_notices"]], (
            case["id"]
        )
        assert outcome.providers == tuple(case["providers"]), case["id"]


def _embedded_corpus_results(plan, raw_results) -> list[EmbeddedFormatResult]:
    results: list[EmbeddedFormatResult] = []
    for raw in raw_results:
        request = plan.requests[raw["region"]]
        status = raw["status"]
        if status == "formatted":
            results.append(EmbeddedFormatResult.formatted(plan.id, request.id, raw["text"], raw["provider"]))
        elif status == "unchanged":
            results.append(EmbeddedFormatResult.unchanged(plan.id, request.id))
        elif status == "unavailable":
            results.append(EmbeddedFormatResult.unavailable(plan.id, request.id, raw["message"]))
        elif status == "error":
            results.append(EmbeddedFormatResult.error(plan.id, request.id, raw["message"]))
        elif status == "stale-plan":
            results.append(
                EmbeddedFormatResult.formatted(f"{plan.id}-stale", request.id, raw["text"], raw["provider"])
            )
        elif status == "duplicate":
            duplicate = EmbeddedFormatResult.formatted(plan.id, request.id, raw["text"], raw["provider"])
            results.extend((duplicate, duplicate))
        else:
            raise AssertionError(f"unknown embedded corpus status: {status}")
    return results


def test_python_expression_provider_identity_is_pinned() -> None:
    assert python_expression_provider() == "ruff@0.16.2+5b48a04097"


def test_format_error_preserves_structured_syntax_details() -> None:
    with pytest.raises(TemplateFormatError) as raised:
        format_template("<c-raw>unterminated")

    error = raised.value
    assert isinstance(error, ValueError)
    assert error.code == "citry.format.syntax"
    assert error.message == str(error)
    assert error.range is not None
    assert error.diagnostic is not None
    assert error.diagnostic.code == "citry.parse.syntax"


def test_suppression_error_has_no_parser_diagnostic() -> None:
    with pytest.raises(TemplateFormatError) as raised:
        format_template("{# fmt: on #}<div></div>")

    error = raised.value
    assert error.code == "citry.format.suppression"
    assert error.range == (0, 13)
    assert error.diagnostic is None


def test_error_has_the_public_importable_module_identity() -> None:
    assert TemplateFormatError.__module__ == "citry_core.template_formatter"

    error = TemplateFormatError("failure")
    restored = pickle.loads(pickle.dumps(error))  # noqa: S301 - trusted local round-trip

    assert type(restored) is TemplateFormatError
    assert str(restored) == "failure"


def test_non_string_input_remains_a_type_error() -> None:
    with pytest.raises(TypeError):
        format_template(42)  # type: ignore[arg-type]


def test_embedded_plan_and_outcome_are_typed_and_immutable() -> None:
    plan = prepare_embedded_format("<main><script>const  answer=41+1;</script><style>.card{color:red}</style></main>")

    assert plan.formatted_source.startswith("<main>\n")
    assert [request.language for request in plan.requests] == [
        EmbeddedLanguage.JAVASCRIPT,
        EmbeddedLanguage.CSS,
    ]
    assert [request.kind for request in plan.requests] == [
        EmbeddedRegionKind.SCRIPT_BODY,
        EmbeddedRegionKind.STYLE_BODY,
    ]
    assert plan.requests[0].virtual_source == "const  answer=41+1;"
    assert plan.requests[0].source == (plan.formatted_source[slice(*plan.requests[0].byte_range)])
    with pytest.raises(FrozenInstanceError):
        plan.id = "replacement"  # type: ignore[misc]

    outcome = finish_embedded_format(
        plan,
        [
            EmbeddedFormatResult.formatted(
                plan.id,
                plan.requests[0].id,
                "const answer = 41 + 1;\n",
                "fake-javascript@1",
            ),
            EmbeddedFormatResult.formatted(
                plan.id,
                plan.requests[1].id,
                ".card {\n  color: red;\n}\n",
                "fake-css@1",
            ),
        ],
    )

    assert "const answer = 41 + 1;" in outcome.source
    assert "  color: red;" in outcome.source
    assert outcome.providers == ("fake-css@1", "fake-javascript@1")
    assert outcome.notices == ()


def test_embedded_plan_reports_regions_that_cannot_be_delegated() -> None:
    plan = prepare_embedded_format(
        '<script>const answer = {{ answer }};</script><style type="text/less">.card{color:red}</style>'
    )

    assert plan.requests == ()
    assert [notice.code for notice in plan.notices] == [
        "citry.format.embedded-interpolation-unsupported",
        "citry.format.embedded-language-unsupported",
    ]
    assert plan.notices[0].language is EmbeddedLanguage.JAVASCRIPT
    assert plan.notices[1].language is None
    assert finish_embedded_format(plan, []).source == plan.formatted_source

    for source in [
        "<script>{# note #}const x=1;</script>",
        "<style>{# note #}a{color:red}</style>",
    ]:
        comment_plan = prepare_embedded_format(source)
        assert comment_plan.requests == ()
        assert comment_plan.notices[0].code == "citry.format.embedded-interpolation-unsupported"


def test_unavailable_embedded_provider_preserves_source_and_adds_notice() -> None:
    plan = prepare_embedded_format("<style>.card{color:red}</style>")
    request = plan.requests[0]

    outcome = finish_embedded_format(
        plan,
        [
            EmbeddedFormatResult.unavailable(
                plan.id,
                request.id,
                "no compatible CSS formatter is configured",
            )
        ],
    )

    assert outcome.source == plan.formatted_source
    assert outcome.providers == ()
    assert len(outcome.notices) == 1
    assert outcome.notices[0].code == "citry.format.provider-unavailable"
    assert outcome.notices[0].region_id == request.id
    assert outcome.notices[0].language is EmbeddedLanguage.CSS


@pytest.mark.parametrize(
    "make_results",
    [
        lambda _plan, _request: [],
        lambda _plan, request: [EmbeddedFormatResult.unchanged("stale-plan", request.id)],
        lambda plan, _request: [EmbeddedFormatResult.unchanged(plan.id, "unknown-region")],
        lambda plan, request: [
            EmbeddedFormatResult.unchanged(plan.id, request.id),
            EmbeddedFormatResult.unchanged(plan.id, request.id),
        ],
    ],
)
def test_malformed_embedded_results_raise_structured_provider_error(make_results) -> None:
    plan = prepare_embedded_format("<script>let  value=1</script>")
    request = plan.requests[0]

    with pytest.raises(TemplateFormatError) as raised:
        finish_embedded_format(plan, make_results(plan, request))

    assert raised.value.code == "citry.format.provider-invalid"
    assert raised.value.range is None
    assert raised.value.diagnostic is None


@pytest.mark.parametrize(
    "result",
    [
        EmbeddedFormatResult(
            EmbeddedResultStatus.FORMATTED,
            "unused",
            "unused",
            text="let value = 1;",
            message="contradiction",
        ),
        EmbeddedFormatResult(
            EmbeddedResultStatus.UNCHANGED,
            "unused",
            "unused",
            text="unexpected",
        ),
        EmbeddedFormatResult(
            EmbeddedResultStatus.ERROR,
            "unused",
            "unused",
            text="unexpected",
            message="failed",
        ),
    ],
)
def test_embedded_result_status_rejects_contradictory_fields(result: EmbeddedFormatResult) -> None:
    plan = prepare_embedded_format("<script>let value=1</script>")
    request = plan.requests[0]
    contradictory = EmbeddedFormatResult(
        result.status,
        plan.id,
        request.id,
        text=result.text,
        provider=result.provider,
        message=result.message,
    )

    with pytest.raises(TemplateFormatError) as raised:
        finish_embedded_format(plan, [contradictory])

    assert raised.value.code == "citry.format.provider-invalid"


def test_provider_output_delimiter_conflict_rejects_the_complete_plan() -> None:
    plan = prepare_embedded_format("<script>let  value=1</script>")
    request = plan.requests[0]

    with pytest.raises(TemplateFormatError) as raised:
        finish_embedded_format(
            plan,
            [
                EmbeddedFormatResult.formatted(
                    plan.id,
                    request.id,
                    "const value = '</script>';\n",
                    "fake@1",
                )
            ],
        )

    assert raised.value.code == "citry.format.provider-invalid"
    assert raised.value.range == request.byte_range

    for text in ["if (x) {{ foo }}", "if (x) {# fmt: off #}"]:
        with pytest.raises(TemplateFormatError) as host_delimiter:
            finish_embedded_format(
                plan,
                [EmbeddedFormatResult.formatted(plan.id, request.id, text, "fake@1")],
            )
        assert host_delimiter.value.code == "citry.format.provider-invalid"
