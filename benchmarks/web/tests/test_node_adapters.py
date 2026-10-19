"""Check Node adapter build preparation without running the toolchains."""

import hashlib
import importlib.util
import re
import shutil
from pathlib import Path

import pytest
import tomllib
from citry_bench.config import WEB, files

CANONICAL_BOARD_CSS_SHA256 = "6fe9d43e3f52df074d393a72308a19b0f686161408126fd54540ad85f1c5a983"


def _load_build_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load build module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("adapter", "update_payload", "timing_boundary"),
    [("next", "delta", "first-chunk"), ("nuxt", "json", "complete")],
)
def test_node_adapters_declare_hybrid_protocol_and_pinned_node(
    adapter: str, update_payload: str, timing_boundary: str
) -> None:
    declaration = tomllib.loads((WEB / "apps" / adapter / "adapter.toml").read_text(encoding="utf-8"))["app"]

    assert declaration["runtime"] == "node"
    assert declaration["node"] == ".toolchain/node-v22.22.0-darwin-arm64/bin/node"
    assert declaration["rendering"] == "hybrid"
    assert declaration["update_payload"] == update_payload
    assert declaration.get("timing_boundary", "complete") == timing_boundary
    assert declaration["health"] == "/health"


def test_cohort_profiles_include_node_adapters_at_both_scaling_points() -> None:
    for profile_name, expected_counts in (("cohort", [14, 140]), ("cohort-100x", [1400])):
        profile = tomllib.loads((WEB / "profiles" / f"{profile_name}.toml").read_text(encoding="utf-8"))
        assert {"next", "nuxt"} <= set(profile["apps"])
        assert profile["counts"] == expected_counts


def test_nuxt_csr_is_a_separate_browser_control_with_the_same_app_sources() -> None:
    source = WEB / "apps" / "nuxt"
    control = WEB / "apps" / "nuxt_csr"
    declaration = tomllib.loads((control / "adapter.toml").read_text(encoding="utf-8"))["app"]

    assert declaration["name"] == "nuxt_csr"
    assert declaration["runtime"] == "node"
    assert declaration["node"] == ".toolchain/node-v22.22.0-darwin-arm64/bin/node"
    assert declaration["rendering"] == "browser"
    assert "update_payload" not in declaration
    assert "ssr: false" in (control / "nuxt.config.ts").read_text(encoding="utf-8")
    assert "ssr: true" in (source / "nuxt.config.ts").read_text(encoding="utf-8")

    variants = {"README.md", "adapter.toml", "nuxt.config.ts", "pyproject.toml"}
    for path in files(source, tuple(declaration["source_exclude"])):
        relative = path.relative_to(source)
        if relative.name in variants:
            continue
        assert (control / relative).read_bytes() == path.read_bytes(), relative

    profile = tomllib.loads((WEB / "profiles" / "nuxt-csr.toml").read_text(encoding="utf-8"))
    assert profile["apps"] == ["nuxt_csr"]
    assert profile["counts"] == [14, 140]


@pytest.mark.parametrize("adapter", ["next", "nuxt", "nuxt_csr"])
def test_node_adapter_materializes_model_and_resolvable_data_import(tmp_path: Path, adapter: str) -> None:
    app = WEB / "apps" / adapter
    build = _load_build_module(f"{adapter}_build_for_test", app / "build.py")
    source = WEB / "scenarios/project_board"
    destination = tmp_path / adapter

    build.materialize_sources(destination, source)

    data = destination / "generated/data.mjs"
    model = destination / "scenario/node_model.mjs"
    assert data.is_file()
    assert model.is_file()
    assert model.read_bytes() == (source / "node_model.mjs").read_bytes()
    css = destination / "public/assets/board.css"
    assert css.read_bytes() == (source / "board.css").read_bytes()
    assert hashlib.sha256(css.read_bytes()).hexdigest() == CANONICAL_BOARD_CSS_SHA256
    if adapter == "next":
        assert 'href="/assets/board.css"' in (app / "app/layout.jsx").read_text(encoding="utf-8")
        assert "margin: 0" not in (app / "app/globals.css").read_text(encoding="utf-8")
    else:
        assert 'href: "/assets/board.css"' in (app / "nuxt.config.ts").read_text(encoding="utf-8")
        assert "margin: 0" not in (app / "app.vue").read_text(encoding="utf-8")
    match = re.search(r'import source from "([^"]+)";', model.read_text(encoding="utf-8"))
    assert match is not None
    assert (model.parent / match.group(1)).resolve() == data.resolve()


@pytest.mark.parametrize("adapter", ["next", "nuxt", "nuxt_csr"])
def test_node_adapter_uses_prepared_scenario_when_run_from_a_build_copy(tmp_path: Path, adapter: str) -> None:
    source_app = WEB / "apps" / adapter
    destination = tmp_path / adapter
    destination.mkdir()
    shutil.copyfile(source_app / "build.py", destination / "build.py")
    shutil.copyfile(source_app / "toolchain.json", destination / "toolchain.json")
    scenario = destination / "scenario"
    scenario.mkdir()
    for name in ("canonical_project.json", "node_model.mjs", "board.css"):
        shutil.copyfile(WEB / "scenarios/project_board" / name, scenario / name)

    build = _load_build_module(f"{adapter}_prepared_build_for_test", destination / "build.py")
    assert scenario == build.SCENARIO
    build.materialize_sources()
    assert (destination / "generated/data.mjs").is_file()
    assert (destination / "scenario/node_model.mjs").is_file()
    assert (destination / "public/assets/board.css").read_bytes() == (scenario / "board.css").read_bytes()
