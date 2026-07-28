"""Deterministic A10 payload budgets for the realistic client graph workload."""

from __future__ import annotations

import gzip
import importlib.util
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[4]


def _load_scenario(module_name: str = "citry_client_benchmark_scenario") -> Any:
    path = _ROOT / "benchmarks" / "client_scenario.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


scenario = _load_scenario()


def test_client_runtime_bundle_budget():
    paths = [
        _ROOT / "packages/py/citry/citry/ext/dependencies/client/citry.js",
        _ROOT / "packages/py/citry/citry/ext/events/client/citry-events.js",
    ]
    payload = b"".join(path.read_bytes() for path in paths)

    # Strict Events protocol validation intentionally adds a small amount of
    # runtime code. Keep a close regression guard around the resulting bundle;
    # broader optimization belongs to the dedicated benchmarking work.
    assert len(payload) <= 565_000
    assert len(gzip.compress(payload, mtime=0)) <= 122_000


def test_325_instance_client_payload_budget():
    sizes = scenario.payload_sizes(scenario.build_client_scenario(325).document())

    assert sizes.graph_raw <= 660_000
    assert sizes.graph_gzip <= 38_000
    assert sizes.document_raw <= 1_415_000
    assert sizes.document_gzip <= 170_000


def test_450_instance_large_graph_regression_budget():
    sizes = scenario.payload_sizes(scenario.build_client_scenario(450).document())

    assert sizes.graph_raw <= 900_000


def test_payload_measurement_is_byte_for_byte_repeatable():
    first = scenario.payload_sizes(scenario.build_client_scenario(25).document())
    separately_loaded = _load_scenario("citry_client_benchmark_scenario_repeat")
    second = separately_loaded.payload_sizes(separately_loaded.build_client_scenario(25).document())

    assert (
        first.graph_raw,
        first.graph_gzip,
        first.document_raw,
        first.document_gzip,
    ) == (
        second.graph_raw,
        second.graph_gzip,
        second.document_raw,
        second.document_gzip,
    )
