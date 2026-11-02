"""Focused tests for the browser playground's Citry analysis adapter."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

_ADAPTER = Path(__file__).parents[1] / "static" / "playground" / "analysis_adapter.py"
_PORTABLE_IDE = Path(__file__).parents[1] / "static" / "playground" / "portable_ide.py"


def _catalog_snapshot() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "registries": [
            {
                "engineId": "playground",
                "components": [
                    {
                        "definitionId": "profile-card",
                        "name": "ProfileCard",
                        "aliases": ["profile-card"],
                        "className": "ProfileCard",
                        "importPath": "__playground__.ProfileCard",
                        "description": "Show one member profile.",
                        "builtin": False,
                        "kwargs": [
                            {
                                "name": "title",
                                "required": True,
                                "typeDisplay": "str",
                                "description": "Visible heading.",
                            }
                        ],
                        "slots": [],
                    }
                ],
            }
        ],
    }


@pytest.fixture(scope="module")
def adapter() -> Iterator[ModuleType]:
    # The adapter imports the generated `portable_ide.py`, as in the Worker,
    # so every test here runs that copy rather than its source.
    portable_spec = importlib.util.spec_from_file_location("citry_portable_ide", _PORTABLE_IDE)
    assert portable_spec is not None
    assert portable_spec.loader is not None
    portable = importlib.util.module_from_spec(portable_spec)
    sys.modules["citry_portable_ide"] = portable
    try:
        portable_spec.loader.exec_module(portable)
        spec = importlib.util.spec_from_file_location("citry_playground_analysis_adapter", _ADAPTER)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("citry_portable_ide", None)


def test_analysis_reports_and_clears_real_parser_diagnostics(adapter: ModuleType) -> None:
    invalid = json.loads(adapter.analyze_regions_json(json.dumps([{"id": "card", "source": "<c-if>"}])))
    valid = json.loads(
        adapter.analyze_regions_json(
            json.dumps([{"id": "card", "source": '<c-if cond="ready">ok</c-if>'}]),
        ),
    )

    assert len(invalid["diagnostics"]) == 1
    finding = invalid["diagnostics"][0]
    assert finding["regionId"] == "card"
    assert finding["severity"] == "error"
    assert finding["code"].startswith("citry.parse")
    assert finding["range"]["start"] == {"line": 0, "character": 0}
    assert "Unclosed tag" in finding["message"]
    assert valid == {"diagnostics": []}


def test_analysis_keeps_legacy_parser_failures_actionable(adapter: ModuleType) -> None:
    error = SyntaxError("Parse error:  --> 2:3\n  |\n2 | <bad\n  |   ^")

    finding = adapter._parser_error("first\n<bad", error)

    assert finding["code"] == "citry.parse"
    assert finding["range"] == {
        "start": {"line": 1, "character": 2},
        "end": {"line": 1, "character": 3},
    }


def test_analysis_completes_parser_owned_structural_tags(adapter: ModuleType) -> None:
    source = "😀<c-i"

    result = json.loads(
        adapter.complete_region_json(source, json.dumps({"line": 0, "character": 6})),
    )

    assert result["range"] == {
        "start": {"line": 0, "character": 3},
        "end": {"line": 0, "character": 6},
    }
    assert [item["label"] for item in result["items"]] == ["c-if"]
    assert (
        json.loads(
            adapter.complete_region_json('<div title="<c-i', json.dumps({"line": 0, "character": 16})),
        )
        is None
    )


def test_analysis_hovers_only_parser_proven_structural_tags(adapter: ModuleType) -> None:
    source = '<c-if cond="ready">ok</c-if>'

    result = json.loads(
        adapter.hover_region_json(source, json.dumps({"line": 0, "character": 3})),
    )
    comment = json.loads(
        adapter.hover_region_json("<!-- <c-if> -->", json.dumps({"line": 0, "character": 8})),
    )

    assert result["label"] == "c-if"
    assert result["range"] == {
        "start": {"line": 0, "character": 1},
        "end": {"line": 0, "character": 5},
    }
    assert result["documentationUrl"].startswith("https://citry.dev/")
    assert comment is None


def test_analysis_rejects_unknown_wire_fields(adapter: ModuleType) -> None:
    with pytest.raises(ValueError, match="exactly"):
        adapter.analyze_regions_json(json.dumps([{"id": "card", "source": "<p/>", "extra": True}]))


def test_runtime_catalog_adds_component_completion_hover_and_diagnostics(adapter: ModuleType) -> None:
    adapter.update_catalog_json(json.dumps(_catalog_snapshot()))
    try:
        completion = json.loads(
            adapter.complete_region_json("<c-Pro", json.dumps({"line": 0, "character": 6})),
        )
        hover = json.loads(
            adapter.hover_region_json("<c-ProfileCard />", json.dumps({"line": 0, "character": 4})),
        )
        nested_source = '<div c-body="<><c-ProfileCard /></>"></div>'
        nested_hover = json.loads(
            adapter.hover_region_json(
                nested_source,
                json.dumps({"line": 0, "character": nested_source.index("ProfileCard") + 2}),
            ),
        )
        unknown = json.loads(
            adapter.analyze_regions_json(
                json.dumps([{"id": "card", "source": '<div c-body="<><c-Missing /></>"></div>'}]),
            )
        )
        known = json.loads(adapter.analyze_regions_json(json.dumps([{"id": "card", "source": "<c-ProfileCard />"}])))
    finally:
        adapter.update_catalog_json("null")

    assert "c-ProfileCard" in {item["label"] for item in completion["items"]}
    assert hover["detail"] == "__playground__.ProfileCard"
    assert nested_hover["detail"] == "__playground__.ProfileCard"
    assert "Inputs: title." in hover["documentation"]
    assert [(item["code"], item["message"]) for item in unknown["diagnostics"]] == [
        ("citry.template.unknown-component", "Component <c-Missing> is not registered.")
    ]
    assert known == {"diagnostics": []}


def test_runtime_catalog_rejects_partial_records_without_replacing_current_facts(adapter: ModuleType) -> None:
    adapter.update_catalog_json(json.dumps(_catalog_snapshot()))
    broken = _catalog_snapshot()
    del broken["registries"][0]["components"][0]["kwargs"]  # type: ignore[index]

    try:
        with pytest.raises(ValueError, match="exactly"):
            adapter.update_catalog_json(json.dumps(broken))
        result = json.loads(
            adapter.complete_region_json("<c-Pro", json.dumps({"line": 0, "character": 6})),
        )
    finally:
        adapter.update_catalog_json("null")

    assert "c-ProfileCard" in {item["label"] for item in result["items"]}


def test_runtime_catalog_withholds_ambiguous_component_help(adapter: ModuleType) -> None:
    snapshot = _catalog_snapshot()
    second = _catalog_snapshot()["registries"][0]
    second["engineId"] = "other"  # type: ignore[index]
    second["components"][0]["definitionId"] = "other-profile-card"  # type: ignore[index]
    snapshot["registries"].append(second)  # type: ignore[union-attr]

    adapter.update_catalog_json(json.dumps(snapshot))
    try:
        completion = json.loads(
            adapter.complete_region_json("<c-Pro", json.dumps({"line": 0, "character": 6})),
        )
        hover = json.loads(
            adapter.hover_region_json("<c-ProfileCard />", json.dumps({"line": 0, "character": 4})),
        )
    finally:
        adapter.update_catalog_json("null")

    assert "c-ProfileCard" not in {item["label"] for item in completion["items"]}
    assert hover is None


def test_runtime_catalog_requires_an_exact_integer_schema(adapter: ModuleType) -> None:
    snapshot = _catalog_snapshot()
    snapshot["schemaVersion"] = True

    with pytest.raises(ValueError, match="unsupported"):
        adapter.update_catalog_json(json.dumps(snapshot))


# Loads the generated `portable_ide.py` the way `analysis_worker.js` does: as the
# top-level module `citry_portable_ide`, with `citry-core` installed and the
# `citry` package absent, then runs the adapter beside it.
_WORKER_LOAD = """
import importlib.util, json, sys
sys.modules["citry"] = None  # the playground Worker installs only citry-core
portable_path, adapter_path = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("citry_portable_ide", portable_path)
portable = importlib.util.module_from_spec(spec)
sys.modules["citry_portable_ide"] = portable
spec.loader.exec_module(portable)
from citry_core.template_parser import parse_template
uses = portable.template_tag_uses(parse_template('<c-if cond="x"><div><c-card /></div></c-if>'))
print(json.dumps([use.tag for use in uses]))
adapter = {"__name__": "citry_playground_analysis_adapter"}
exec(compile(open(adapter_path).read(), adapter_path, "exec"), adapter)
print(adapter["analyze_regions_json"](json.dumps([{"id": "card", "source": "<c-if>"}])))
"""


def test_generated_portable_rules_load_without_the_citry_package() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _WORKER_LOAD, str(_PORTABLE_IDE), str(_ADAPTER)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    tags, analysis = result.stdout.splitlines()
    # Opening and closing tags, in source order.
    assert json.loads(tags) == ["c-if", "div", "c-card", "div", "c-if"]
    assert json.loads(analysis)["diagnostics"][0]["code"].startswith("citry.parse")
