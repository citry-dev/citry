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

    # Strict Events protocol validation, per-handler loading/error state, and
    # atomic error rollback intentionally add a small amount of runtime code.
    # Keep a close regression guard around the resulting bundle; broader
    # optimization belongs to the dedicated benchmarking work.
    # Raised by 1 KB for the two-way binding value guard: a control that reads
    # back no value keeps its unsent draft instead of writing `undefined` into
    # the field, which costs a little code at both flush sites.
    # Raised by another 1 KB raw / 0.5 KB gzip for multi-select list reads,
    # exact list application, and post-morph preservation of pending lists.
    # Keyed virtual component ranges add strict graph-key validation, a
    # top-down logical correspondence planner, connected/portable recursive
    # physical paths, and correlated supplied-slot regions. The generated
    # Events bundle now also embeds the strict Events protocol runtime. The
    # maintainer approved that protocol-binding cost on 2026-08-04. Concurrent
    # graph work moved the core again during the bounded review. Nested split
    # Document/body ranges also need a lossless boundary-text alignment step;
    # keep narrow headroom over the resulting 646,821 raw / 134,997 gzip
    # moving baseline. Client-graph protocol validation then moved into its
    # generated browser helper and the Events bundle began sharing the same
    # ownership-comment parser. ComponentRange ignore then added detached
    # ignore-closure planning, transactional subset adoption, owner-filtered
    # dependencies, and persistent revision descriptors. Keep narrow headroom
    # over the resulting 702,253 raw / 146,749 gzip baseline. Connected
    # stationary ranges then added paired-sentinel traversal, pre-map key
    # filtering, fixed-point physical replanning, retained-boundary liveness,
    # and compositional connected handling through equivalent slot regions.
    # Keep the same narrow headroom over the resulting 710,453 raw baseline.
    # Direct element event listeners then replaced document delegation so
    # non-bubbling native/custom events follow browser propagation semantics;
    # listener reconciliation and same-document liveness checks move the raw
    # baseline to 713,520 while compressed size remains within its prior cap.
    # The complete input-type matrix adds strict compiled-spec decoding plus
    # one shared live classifier across effects, listeners, morph guards, and
    # delayed drafts. The measured baseline is 724,618 raw / 150,955 gzip.
    # Typed custom-element values then add upgrade-aware activation, strict
    # JSON uplink validation, raw-object identity, and pointed property
    # diagnostics. The measured baseline is 728,847 raw / 151,867 gzip.
    # These are deliberate validation and identity features, not incidental
    # bundle drift.
    assert len(payload) <= 731_000
    assert len(gzip.compress(payload, mtime=0)) <= 153_000


def test_325_instance_client_payload_budget():
    sizes = scenario.payload_sizes(scenario.build_client_scenario(325).document())

    assert sizes.graph_raw <= 660_000
    assert sizes.graph_gzip <= 38_000
    assert sizes.document_raw <= 1_425_000
    # Owner-aware fragment fetch entries and the ComponentRange client runtime
    # plus strict live input validation move the realistic document baseline
    # to 1,413,161 raw / 182,460 bytes compressed.
    assert sizes.document_gzip <= 183_000


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
