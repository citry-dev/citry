# ruff: noqa: I001, S101
"""Static and render-contract tests for the component-field research proof."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path

import pytest

from components import (
    COORDINATE_SCALE,
    SUPPORTED_COUNTS,
    build_descriptors,
    build_scenario,
    component_asset_paths,
    component_fixture_sha256,
    descriptor_sha256,
    parse_canvas_descriptors,
)

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def test_descriptor_geometry_is_exact_ordered_and_bounded() -> None:
    for count in SUPPORTED_COUNTS:
        descriptors, columns, rows = build_descriptors(count)

        assert len(descriptors) == count
        assert [descriptor.cell_id for descriptor in descriptors] == list(range(count))
        assert columns * rows >= count
        assert columns * (rows - 1) < count
        assert len(descriptor_sha256(descriptors)) == 64
        assert all(0 <= descriptor.x_ppm <= COORDINATE_SCALE for descriptor in descriptors)
        assert all(0 <= descriptor.y_ppm <= COORDINATE_SCALE for descriptor in descriptors)
        assert all(0 <= descriptor.phase_ms <= 1600 for descriptor in descriptors)
        assert all(0 <= descriptor.palette < 4 for descriptor in descriptors)


def test_descriptor_builder_rejects_unmeasured_count() -> None:
    with pytest.raises(ValueError, match="cell count must be one of"):
        build_descriptors(1000)


def test_literal_page_renders_one_inert_element_per_component() -> None:
    scenario = build_scenario("dom", 256)
    html, cell_renders = scenario.render()

    assert cell_renders == 256
    assert html.count('class="component-field__cell"') == 256
    assert html.count("data-cell-id=") == 256
    assert f'data-descriptor-sha256="{scenario.descriptor_sha256}"' in html
    assert "will-change" not in html


def test_canvas_page_renders_components_into_one_valid_descriptor_block() -> None:
    scenario = build_scenario("canvas", 256)
    html, cell_renders = scenario.render()
    parsed = parse_canvas_descriptors(html)
    canonical = [list(descriptor.compact()) for descriptor in scenario.descriptors]

    assert cell_renders == 256
    assert parsed == canonical
    assert html.count('<script type="application/json" data-field-descriptors>') == 1
    assert "data-field-cell" not in html
    assert "c-render-id" not in html
    digest = hashlib.sha256(json.dumps(parsed, separators=(",", ":")).encode()).hexdigest()
    assert digest == scenario.descriptor_sha256


def test_baseline_keeps_the_same_complete_shell_without_cells() -> None:
    scenario = build_scenario("baseline", 256)
    html, cell_renders = scenario.render()

    assert cell_renders == 0
    assert "Build the frontend in Python." in html
    assert "One component, a complete UI path" in html
    assert "data-field-cell" not in html
    assert "data-field-descriptors" not in html


def test_render_output_sizes_are_repeatable_across_fresh_scenarios() -> None:
    for renderer in ("baseline", "dom", "canvas"):
        first, _ = build_scenario(renderer, 256).render()
        second, _ = build_scenario(renderer, 256).render()

        assert first == second
        assert gzip.compress(first.encode(), mtime=0) == gzip.compress(second.encode(), mtime=0)


def test_research_assets_follow_repository_prose_rules() -> None:
    forbidden_jargon = re.compile(r"\bseam\b", re.IGNORECASE)
    for path in component_asset_paths():
        source = path.read_text(encoding="utf-8")
        assert "\N{EM DASH}" not in source, path
        assert forbidden_jargon.search(source) is None, path


def test_reviewed_artifacts_match_the_current_fixture_and_decision() -> None:
    scale = json.loads((RESULTS_DIR / "reference-2026-07-28-practical.json").read_text())
    target = json.loads((RESULTS_DIR / "reference-2026-07-28-target-1024.json").read_text())
    fixture_digest = component_fixture_sha256()

    for artifact in (scale, target):
        assert artifact["metadata"]["fixture_sha256"] == fixture_digest
        assert (
            artifact["metadata"]["harness_sha256"]
            == hashlib.sha256((Path(__file__).resolve().parent / "browser_probe.py").read_bytes()).hexdigest()
        )
        assert artifact["metadata"]["release_build_attested"] is True
        assert all(artifact["correctness_gates"]["canvas"].values())
        assert all(artifact["correctness_gates"]["dom"].values())

    assert scale["metadata"]["rounds"] == 5
    assert scale["summary"]["feasible_frontier"] == {"canvas": 2048, "dom": 256}
    for browser in ("firefox", "webkit"):
        for renderer in ("dom", "canvas"):
            result = scale["cross_browser"][browser]["renderers"][renderer]
            assert result["errors"] == []
            assert result["snapshot"]["cellCount"] == 1024

    assert target["metadata"]["rounds"] == 12
    assert not [sample for sample in target["samples"] if not sample["valid"]]
    assert not [sample for sample in target["retained_state"] if not sample["valid"]]
    for profile in ("desktop", "mobile"):
        result = target["summary"]["profiles"][profile]["1024"]
        assert result["canvas"]["passes"] is True
        assert result["dom"]["passes"] is False
