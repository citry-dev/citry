"""Tests for versioned formatter requests and LSP edit construction."""

from __future__ import annotations

import json
from pathlib import Path

from lsprotocol import types

from citry_core.template_formatter import EmbeddedFormatResult
from citry_lsp.engine import DocumentState
from citry_lsp.formatting import (
    PreparedComponentAssets,
    finish_component_assets,
    format_templates,
    prepare_component_assets,
)
from citry_lsp.project import ProjectState
from citry_lsp.protocol import ProjectStatus
from citry_lsp.regions import standalone_region

REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_ROOT = REPO_ROOT / "crates" / "citry_template_formatter" / "tests" / "fixtures" / "v1"


def _project() -> ProjectState:
    return ProjectState(ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="syntax-only"))


def _document(source: str, *, language_id: str, version: int = 4) -> DocumentState:
    document = DocumentState(f"file:///template.{language_id}", language_id, source, version)
    document.update(source, version, _project())
    return document


def _new_text(result: dict[str, object]) -> str:
    edit = result["edit"]
    assert isinstance(edit, dict)
    document_changes = edit["documentChanges"]
    assert isinstance(document_changes, list)
    document_edit = document_changes[0]
    assert isinstance(document_edit, dict)
    edits = document_edit["edits"]
    assert isinstance(edits, list)
    text_edit = edits[0]
    assert isinstance(text_edit, dict)
    new_text = text_edit["newText"]
    assert isinstance(new_text, str)
    return new_text


def test_standalone_format_returns_one_versioned_whole_document_edit() -> None:
    source = '😀<div  title = "hello" ></div>'
    document = _document(source, language_id="citry-html")

    result = format_templates(document, requested_version=4, scope="document")

    assert result["kind"] == "edit"
    assert _new_text(result) == '😀<div title="hello"></div>'
    edit = result["edit"]
    assert isinstance(edit, dict)
    document_changes = edit["documentChanges"]
    assert isinstance(document_changes, list)
    document_edit = document_changes[0]
    assert isinstance(document_edit, dict)
    assert document_edit["textDocument"] == {"uri": document.uri, "version": 4}
    edits = document_edit["edits"]
    assert isinstance(edits, list)
    text_edit = edits[0]
    assert isinstance(text_edit, dict)
    assert text_edit["range"] == {
        "start": {"line": 0, "character": 0},
        "end": {"line": 0, "character": len(source.encode("utf-16-le")) // 2},
    }


def test_registry_owned_html_is_eligible_but_unrelated_html_is_not() -> None:
    source = '<div  title = "hello" ></div>'
    associated = _document(source, language_id="html")
    associated.regions = (standalone_region(source),)
    unrelated = _document(source, language_id="html")

    prepared = prepare_component_assets(associated, requested_version=4, scope="document")
    refused = prepare_component_assets(unrelated, requested_version=4, scope="document")

    assert isinstance(prepared, PreparedComponentAssets)
    assert refused["kind"] == "refused"
    assert refused["code"] == "citry.format.ineligible"


def test_standalone_lsp_consumes_the_shared_structural_corpus() -> None:
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

        document = _document(source, language_id="citry-html")
        result = format_templates(document, requested_version=4, scope="document")
        if source == expected:
            assert result == {"kind": "unchanged"}, case["id"]
        else:
            assert result["kind"] == "edit", case["id"]
            assert _new_text(result) == expected, case["id"]


def test_python_lsp_consumes_the_shared_host_corpus() -> None:
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))
    for case in index["python_hosts"]:
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")

        document = _document(source, language_id="python")
        result = format_templates(document, requested_version=4, scope="document")
        expected_error = case.get("expected_error")
        if expected_error is not None:
            assert result["kind"] == "refused", case["id"]
            assert result["code"] == expected_error["code"], case["id"]
            continue

        expected = case.get("expected_text")
        if expected is None:
            expected = (CORPUS_ROOT / case["expected"]).read_text(encoding="utf-8")
        if source == expected:
            assert result == {"kind": "unchanged"}, case["id"]
        else:
            assert result["kind"] == "edit", case["id"]
            assert _new_text(result) == expected, case["id"]


def test_lsp_consumes_the_shared_embedded_corpus() -> None:
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))
    for case in index["embedded_cases"]:
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")
        document = _document(source, language_id="citry-html")
        prepared = prepare_component_assets(document, requested_version=4, scope="document")
        assert isinstance(prepared, PreparedComponentAssets), case["id"]
        assert len(prepared.requests) == len(case["requests"]), case["id"]
        for request, expected_request in zip(prepared.requests, case["requests"], strict=True):
            assert request.language == expected_request["language"], case["id"]
            assert request.kind == expected_request["kind"], case["id"]
            assert request.source == expected_request["source"], case["id"]
            assert request.virtual_source == expected_request["virtual_source"], case["id"]
        results = _embedded_corpus_results(prepared, case["results"])
        result = finish_component_assets(document, prepared, results)
        expected_error = case.get("expected_error")
        if expected_error is not None:
            assert result["kind"] == "refused", case["id"]
            assert result["code"] == expected_error["code"], case["id"]
            assert expected_error["contains"] in str(result["message"]), case["id"]
            continue
        expected = case.get("expected_text")
        if expected is None:
            expected = (CORPUS_ROOT / case["expected"]).read_text(encoding="utf-8")
        if expected == source:
            assert result["kind"] == "unchanged", case["id"]
        else:
            assert result["kind"] == "edit", case["id"]
            assert _new_text(result) == expected, case["id"]
        assert [notice["code"] for notice in result["notices"]] == [
            notice["code"] for notice in case["outcome_notices"]
        ], case["id"]
        assert result["providers"] == case["providers"], case["id"]


def _embedded_corpus_results(
    prepared: PreparedComponentAssets,
    raw_results: list[dict[str, object]],
) -> list[EmbeddedFormatResult]:
    results: list[EmbeddedFormatResult] = []
    for raw in raw_results:
        region = raw["region"]
        assert type(region) is int
        request = prepared.requests[region]
        status = raw["status"]
        if status == "formatted":
            results.append(
                EmbeddedFormatResult.formatted(
                    prepared.id,
                    request.id,
                    str(raw["text"]),
                    str(raw["provider"]),
                )
            )
        elif status == "unchanged":
            results.append(EmbeddedFormatResult.unchanged(prepared.id, request.id))
        elif status == "unavailable":
            results.append(EmbeddedFormatResult.unavailable(prepared.id, request.id, str(raw["message"])))
        elif status == "error":
            results.append(EmbeddedFormatResult.error(prepared.id, request.id, str(raw["message"])))
        elif status == "stale-plan":
            results.append(
                EmbeddedFormatResult.formatted(
                    f"{prepared.id}-stale",
                    request.id,
                    str(raw["text"]),
                    str(raw["provider"]),
                )
            )
        elif status == "duplicate":
            duplicate = EmbeddedFormatResult.formatted(
                prepared.id,
                request.id,
                str(raw["text"]),
                str(raw["provider"]),
            )
            results.extend((duplicate, duplicate))
        else:
            raise AssertionError(f"unknown embedded corpus status: {status}")
    return results


def test_standalone_unchanged_and_structured_refusal() -> None:
    unchanged = _document("<div></div>", language_id="citry-html")
    invalid = _document("😀<div>", language_id="citry-html")

    assert format_templates(unchanged, requested_version=4, scope="document") == {"kind": "unchanged"}
    refused = format_templates(invalid, requested_version=4, scope="document")

    assert refused["kind"] == "refused"
    assert refused["code"] == "citry.format.syntax"
    assert "Unclosed tag" in str(refused["message"])
    assert refused["range"] is not None


def test_python_document_and_position_scopes_share_host_formatter() -> None:
    source = (
        "from citry import Component\n"
        "class First(Component):\n"
        '    template = """<div  id = "first" ></div>"""\n'
        "class Second(Component):\n"
        '    template = """<span  id = "second" ></span>"""\n'
    )
    document = _document(source, language_id="python")
    cursor = source.index("<div") + 2
    position = types.Position(2, cursor - source.rfind("\n", 0, cursor) - 1)

    selected = format_templates(
        document,
        requested_version=4,
        scope="position",
        position=position,
    )
    complete = format_templates(document, requested_version=4, scope="document")

    assert '<div id="first"></div>' in _new_text(selected)
    assert '<span  id = "second" ></span>' in _new_text(selected)
    assert '<div id="first"></div>' in _new_text(complete)
    assert '<span id="second"></span>' in _new_text(complete)


def test_position_scope_outside_template_is_a_structured_refusal() -> None:
    source = 'from citry import Component\nclass Card(Component):\n    template = """<div></div>"""\n'
    document = _document(source, language_id="python")

    result = format_templates(
        document,
        requested_version=4,
        scope="position",
        position=types.Position(0, 0),
    )

    assert result["kind"] == "refused"
    assert result["code"] == "citry.format.ineligible"
    assert "does not contain a definite Citry template" in str(result["message"])


def test_stale_version_and_unsupported_scope_never_return_an_edit() -> None:
    python = _document("answer = 42\n", language_id="python")
    standalone = _document('<div  id = "x" ></div>', language_id="citry-html")

    stale = format_templates(python, requested_version=3, scope="document")
    unsupported = format_templates(
        standalone,
        requested_version=4,
        scope="position",
        position=types.Position(0, 2),
    )

    assert stale["kind"] == "refused"
    assert stale["code"] == "citry.format.stale-document"
    assert unsupported["kind"] == "refused"
    assert unsupported["code"] == "citry.format.ineligible"


def test_python_component_assets_use_one_atomic_two_pass_plan() -> None:
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """<main><script>const  nested=1;</script></main>"""\n'
        '    js = """const  direct=1;"""\n'
        '    css = """.card{color:red}"""\n'
    )
    document = _document(source, language_id="python")

    prepared = prepare_component_assets(document, requested_version=4, scope="document")

    assert isinstance(prepared, PreparedComponentAssets)
    assert [request.kind for request in prepared.requests] == [
        "script-body",
        "component-js",
        "component-css",
    ]
    results = [
        EmbeddedFormatResult.formatted(prepared.id, prepared.requests[0].id, "const nested = 1;\n"),
        EmbeddedFormatResult.formatted(prepared.id, prepared.requests[1].id, "const direct = 1;\n"),
        EmbeddedFormatResult.formatted(prepared.id, prepared.requests[2].id, ".card {\n  color: red;\n}\n"),
    ]
    result = finish_component_assets(document, prepared, results)

    assert result["kind"] == "edit"
    formatted = _new_text(result)
    assert "const nested = 1;" in formatted
    assert 'js = """const direct = 1;\n"""' in formatted
    assert 'css = """.card {\n  color: red;\n}\n"""' in formatted
    assert result["providers"] == []
    assert result["notices"] == []


def test_component_asset_position_scope_selects_direct_js() -> None:
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """<main  ></main>"""\n'
        '    js = """const  direct=1;"""\n'
    )
    document = _document(source, language_id="python")
    cursor = source.index("const")
    position = types.Position(3, cursor - source.rfind("\n", 0, cursor) - 1)

    prepared = prepare_component_assets(
        document,
        requested_version=4,
        scope="position",
        position=position,
    )

    assert isinstance(prepared, PreparedComponentAssets)
    assert len(prepared.requests) == 1
    assert prepared.requests[0].kind == "component-js"
    result = finish_component_assets(
        document,
        prepared,
        [EmbeddedFormatResult.formatted(prepared.id, prepared.requests[0].id, "const direct = 1;\n")],
    )
    assert "<main  ></main>" in _new_text(result)
    assert "const direct = 1;" in _new_text(result)


def test_component_asset_position_scope_does_not_follow_files_or_select_methods() -> None:
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template_file = "card.html"\n'
        '    css_file = "card.css"\n'
        "    def template_data(self):\n"
        "        return {}\n"
    )
    document = _document(source, language_id="python")

    for marker in ("card.html", "card.css", "template_data"):
        cursor = source.index(marker) + 1
        line_start = source.rfind("\n", 0, cursor) + 1
        result = prepare_component_assets(
            document,
            requested_version=4,
            scope="position",
            position=types.Position(source.count("\n", 0, cursor), cursor - line_start),
        )

        assert not isinstance(result, PreparedComponentAssets), marker
        assert result["kind"] == "refused", marker
        assert result["code"] == "citry.format.ineligible", marker


def test_component_asset_plan_rejects_document_changes_before_composition() -> None:
    source = "<script>const  value=1;</script>"
    document = _document(source, language_id="citry-html")
    prepared = prepare_component_assets(document, requested_version=4, scope="document")
    assert isinstance(prepared, PreparedComponentAssets)
    assert prepared.requests[0].forbidden_substrings == ("</script", "{{", "{#")
    document.source = "<script>const changed=2;</script>"
    document.version = 5

    result = finish_component_assets(document, prepared, [])

    assert result["kind"] == "refused"
    assert result["code"] == "citry.format.stale-document"


def test_unavailable_component_asset_provider_keeps_region_and_reports_notice() -> None:
    source = "<main><style>.card{color:red}</style></main>"
    document = _document(source, language_id="citry-html")
    prepared = prepare_component_assets(document, requested_version=4, scope="document")
    assert isinstance(prepared, PreparedComponentAssets)
    request = prepared.requests[0]

    result = finish_component_assets(
        document,
        prepared,
        [EmbeddedFormatResult.unavailable(prepared.id, request.id, "no CSS provider")],
    )

    assert result["kind"] == "edit"
    assert ".card{color:red}" in _new_text(result)
    assert result["notices"] == [
        {
            "code": "citry.format.provider-unavailable",
            "message": "no CSS provider",
            "regionId": request.id,
            "language": "css",
        }
    ]
