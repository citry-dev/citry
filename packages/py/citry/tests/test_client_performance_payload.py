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
    # Automatic instance-local JsData parsing, Alpine scope seeding, explicit
    # init/seed calls, and rerender key ownership move the measured raw
    # baseline to 734,546 raw / 153,229 gzip bytes.
    # The final seed lifecycle and ownership-manifest integration move that
    # baseline to 737,241 raw / 154,025 gzip bytes.
    # Alpine and morph 3.16.1 move the generated standard runtime baseline to
    # 740,041 raw / 154,683 gzip bytes.
    # Document-nonce capture, descriptor propagation, and atomic nonce-conflict
    # preflight move the combined baseline to 742,471 raw / 155,224 gzip bytes.
    # Phase 8 adds explicit standard/CSP runtime identity plus manifest preflight
    # before dependency adoption. The measured baseline is 744,463 raw / 155,660
    # gzip bytes.
    # I18n phase 5 adds the shared async framework-manifest transaction around
    # fragment adoption, including rollback after failed current-locale staging.
    # The measured baseline is 754,238 raw / 157,891 gzip bytes.
    # These are deliberate validation and identity features, not incidental
    # bundle drift.
    assert len(payload) <= 755_500
    assert len(gzip.compress(payload, mtime=0)) <= 158_500


def test_csp_events_runtime_bundle_budget():
    """Keep the alternative CSP Events runtime close to its measured build."""
    path = _ROOT / "packages/py/citry/citry/ext/events/client/citry-events-csp.js"
    payload = path.read_bytes()

    # The CSP parser replaces dynamic evaluation but the rest of the Events,
    # ownership, and morph runtime is identical to the standard build. The
    # phase-7 baseline was 387,046 raw / 77,715 gzip bytes. I18n phase 5's
    # fragment transaction moves it to 390,324 raw / 78,515 gzip bytes.
    assert len(payload) <= 391_000
    assert len(gzip.compress(payload, mtime=0)) <= 79_000


def test_i18n_runtime_bundle_budget():
    """Keep the opt-in i18n runtime inside its release payload budget."""
    path = _ROOT / "packages/py/citry/citry/ext/i18n/client/citry-i18n.js"
    payload = path.read_bytes()

    # The production bundle contains the Fluent runtime, locale switching,
    # every current formatter, strict number and percent parsing, and wire
    # validation. Checked declarative/imperative bindings, transactional
    # switching, and current-locale fragment preparation move the phase-5
    # baseline to 109,446 raw / 23,730 gzip bytes.
    # Keep only narrow headroom so new browser work has to account for its cost.
    assert len(payload) <= 110_500
    assert len(gzip.compress(payload, mtime=0)) <= 24_000


def test_325_instance_client_payload_budget():
    sizes = scenario.payload_sizes(scenario.build_client_scenario(325).document())

    assert sizes.graph_raw <= 660_000
    assert sizes.graph_gzip <= 38_000
    # Owner-aware fragment fetch entries and the ComponentRange client runtime
    # plus strict live input validation move the realistic document baseline
    # to 1,413,161 raw / 182,460 bytes compressed. Automatic JsData scope
    # seeding then moves the compressed 325-instance document to 183,637.
    # Alpine and morph 3.16.1 move it to 1,426,955 raw / 184,972 gzip bytes.
    # Phase 5 nonce propagation moves it to 1,429,385 raw / 185,489 gzip.
    # Phase 8 runtime identity and preflight move it to 1,431,406 raw / 185,931
    # gzip bytes. I18n phase 5's framework-manifest transaction moves the
    # measured document to 1,441,181 raw / 187,232 gzip bytes.
    assert sizes.document_raw <= 1_442_500
    assert sizes.document_gzip <= 188_000


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
