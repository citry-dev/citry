"""Preserve raw observations and produce descriptive, nonpublication reports."""

import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from citry_bench.prepare import write_json

READY_PHASE_KEYS = (
    "browser_before",
    "server",
    "exchange_residual",
    "response_receive",
    "browser_after",
    "unclassified",
)
PHASE_KEYS = (*READY_PHASE_KEYS, "layout_wait")
SAMPLE_BUDGET_FIELDS = {"name", "blocks", "sessions", "warmups", "cycles", "publication"}
SHA256 = re.compile(r"[0-9a-f]{64}").fullmatch
LAYOUT_ENDPOINT = "second-rAF-layout-opportunity-v1"


def append(path: Path, value: dict) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")
        stream.flush()


def page_load(row: dict) -> int:
    """Map rows written before the page-load dimension to their original lane."""
    return row.get("page_load", 1)


def ready_elapsed(row: dict) -> float:
    """Return the original ready-only interval, including for archived rows."""
    value = row.get("ready_elapsed_ms")
    if isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
        return value
    return row["elapsed_ms"]


def layout_inclusive_elapsed(row: dict) -> float | None:
    """Accept only complete samples from the explicitly versioned endpoint."""
    if row.get("layout_endpoint") != LAYOUT_ENDPOINT:
        return None
    values = (row.get("layout_inclusive_elapsed_ms"), row.get("ready_elapsed_ms"), row.get("layout_extra_wait_ms"))
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        return None
    layout, ready, extra = values
    if layout < ready or not math.isclose(layout, ready + extra, abs_tol=1e-6):
        return None
    return layout


def layout_extra_wait(row: dict) -> float | None:
    return row.get("layout_extra_wait_ms") if layout_inclusive_elapsed(row) is not None else None


def paint_value(row: dict, name: str) -> float | None:
    """Return a measured FCP or LCP time; rows without paint fields yield None."""
    value = row.get(f"{name}_ms")
    if row.get(f"{name}_status") != "measured" or type(value) not in (int, float):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def paint_summary(observations: list[dict]) -> dict:
    """Summarize FCP and LCP of successful page loads, keeping why values are missing."""
    successful = [row for row in observations if row.get("status") == "ok"]
    result = {}
    for name in ("fcp", "lcp"):
        values = [value for row in successful if (value := paint_value(row, name)) is not None]
        # Rows from runs made before the runner recorded paint timing have no
        # status at all; they are
        # "not recorded", which is different from a browser that reported none.
        reasons = Counter(
            row.get(f"{name}_reason") or "unavailable"
            for row in successful
            if f"{name}_status" in row and paint_value(row, name) is None
        )
        result[f"{name}_median_ms"] = statistics.median(values) if values else None
        result[f"{name}_observations"] = len(values)
        result[f"{name}_not_recorded"] = sum(f"{name}_status" not in row for row in successful)
        result[f"{name}_unavailable_reasons"] = dict(sorted(reasons.items()))
    return result


def representative_phase(observations: list[dict]) -> dict | None:
    """Average ready-only phase segments for the observation(s) at median readiness."""
    successful = [
        row for row in observations if row.get("status") == "ok" and isinstance(row.get("elapsed_ms"), (int, float))
    ]
    if not successful:
        return None
    ordered = sorted(successful, key=ready_elapsed)
    middle = len(ordered) // 2
    selected = [ordered[middle]] if len(ordered) % 2 else ordered[middle - 1 : middle + 1]

    def normalized(row: dict) -> tuple[dict, str, str | None]:
        phase = row.get("latency_phase")
        if not isinstance(phase, dict) or not isinstance(phase.get("segments"), list):
            return {"unclassified": ready_elapsed(row)}, "unavailable", "phase evidence unavailable"
        try:
            segments = {}
            for segment in phase["segments"]:
                key, value = segment["key"], segment["ms"]
                if (
                    key not in READY_PHASE_KEYS
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < 0
                ):
                    raise ValueError
                segments[key] = segments.get(key, 0) + value
            if not math.isclose(sum(segments.values()), ready_elapsed(row), abs_tol=1e-6):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            return {"unclassified": ready_elapsed(row)}, "unavailable", "invalid retained phase evidence"
        status = "measured" if phase.get("status") == "measured" else "unavailable"
        return segments, status, phase.get("reason")

    normalized_rows = [normalized(row) for row in successful]
    vectors = [normalized(row)[0] for row in selected]
    segments = [
        {"key": key, "ms": sum(vector.get(key, 0) for vector in vectors) / len(vectors)}
        for key in READY_PHASE_KEYS
        if any(key in vector for vector in vectors)
    ]
    statuses = Counter(status for _, status, _ in normalized_rows)
    reasons = Counter(
        reason or "phase evidence unavailable" for _, status, reason in normalized_rows if status != "measured"
    )
    return {
        "total_ms": statistics.median(ready_elapsed(row) for row in successful),
        "segments": segments,
        "measured_observations": statuses["measured"],
        "unavailable_observations": len(successful) - statuses["measured"],
        "unavailable_reasons": dict(sorted(reasons.items())),
    }


def representative_layout_phase(observations: list[dict]) -> dict | None:
    """Compose the ready-only phase and same-sample layout wait for new endpoint rows."""
    successful = [
        row for row in observations if row.get("status") == "ok" and layout_inclusive_elapsed(row) is not None
    ]
    if not successful:
        return None
    ordered = sorted(successful, key=lambda row: layout_inclusive_elapsed(row))
    middle = len(ordered) // 2
    selected = [ordered[middle]] if len(ordered) % 2 else ordered[middle - 1 : middle + 1]

    def normalized(row: dict) -> tuple[dict, str, str | None]:
        ready = ready_elapsed(row)
        phase = row.get("latency_phase")
        try:
            if not isinstance(phase, dict) or not isinstance(phase.get("segments"), list):
                raise ValueError
            segments = {}
            for segment in phase["segments"]:
                key, value = segment["key"], segment["ms"]
                if (
                    key not in READY_PHASE_KEYS
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < 0
                ):
                    raise ValueError
                segments[key] = segments.get(key, 0) + value
            if not math.isclose(sum(segments.values()), ready, abs_tol=1e-6):
                raise ValueError
            status = "measured" if phase.get("status") == "measured" else "unavailable"
            reason = phase.get("reason")
        except (KeyError, TypeError, ValueError):
            segments = {"unclassified": ready}
            status = "unavailable"
            reason = "ready-only phase evidence unavailable"
        segments["layout_wait"] = row["layout_extra_wait_ms"]
        return segments, status, reason

    normalized_rows = [normalized(row) for row in successful]
    vectors = [normalized(row)[0] for row in selected]
    segments = [
        {"key": key, "ms": sum(vector.get(key, 0) for vector in vectors) / len(vectors)}
        for key in PHASE_KEYS
        if any(key in vector for vector in vectors)
    ]
    statuses = Counter(status for _, status, _ in normalized_rows)
    reasons = Counter(
        reason or "phase evidence unavailable" for _, status, reason in normalized_rows if status != "measured"
    )
    return {
        "total_ms": statistics.median(layout_inclusive_elapsed(row) for row in successful),
        "segments": segments,
        "measured_observations": statuses["measured"],
        "unavailable_observations": len(successful) - statuses["measured"],
        "unavailable_reasons": dict(sorted(reasons.items())),
    }


def _comparable_run_identity(manifest: dict) -> dict:
    """Select frozen inputs while allowing only the documented sampling differences."""
    evidence = manifest.get("inputs")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("inputs"), dict):
        raise ValueError("Run manifest is missing retained input identity")
    identity = json.loads(json.dumps(evidence))
    frozen_inputs = identity["inputs"]
    required_inputs = {"profile", "runner", "scenario", "apps", "runner_environment", "local_wheels"}
    required_evidence = {"build_sources", "artifacts", "browser_artifacts"}
    if not required_inputs <= frozen_inputs.keys() or not required_evidence <= identity.keys():
        raise ValueError("Run manifest is missing frozen source or artifact identity")

    def valid_hash_map(value: object) -> bool:
        return (
            isinstance(value, dict)
            and bool(value)
            and all(
                isinstance(path, str) and path and isinstance(digest, str) and SHA256(digest)
                for path, digest in value.items()
            )
        )

    def valid_generated_map(value: object) -> bool:
        if not isinstance(value, dict) or not value:
            return False
        for path, item in value.items():
            if not isinstance(path, str) or not path:
                return False
            if isinstance(item, str) and SHA256(item):
                continue
            if not isinstance(item, dict) or item.get("type") not in {"directory", "symlink"}:
                return False
            expected = {"type"} if item["type"] == "directory" else {"type", "target"}
            invalid_target = "target" in item and (not isinstance(item["target"], str) or not item["target"])
            if set(item) != expected or invalid_target:
                return False
        return True

    profile = frozen_inputs.get("profile")
    if not isinstance(profile, dict) or not isinstance(profile.get("apps"), list):
        raise ValueError("Run manifest is missing retained profile identity")
    apps = profile["apps"]
    nested_maps = (frozen_inputs["apps"], identity["build_sources"], identity["artifacts"])
    if (
        not all(
            valid_hash_map(value)
            for value in (
                frozen_inputs["runner"],
                frozen_inputs["scenario"],
                frozen_inputs["runner_environment"],
                identity["browser_artifacts"],
            )
        )
        or any(not isinstance(value, dict) or set(value) != set(apps) for value in nested_maps)
        or any(not valid_hash_map(paths) for paths in frozen_inputs["apps"].values())
        or any(not valid_generated_map(paths) for paths in identity["build_sources"].values())
        or any(not valid_hash_map(paths) for paths in identity["artifacts"].values())
    ):
        raise ValueError("Run manifest has malformed frozen source or artifact identity")
    wheels = frozen_inputs["local_wheels"]
    if (
        not isinstance(wheels, dict)
        or not set(wheels) <= {"citry", "citry-core"}
        or any(
            not isinstance(wheel, dict)
            or set(wheel) != {"path", "size", "sha256"}
            or not isinstance(wheel.get("path"), str)
            or not wheel["path"]
            or type(wheel.get("size")) is not int
            or wheel["size"] < 0
            or not isinstance(wheel.get("sha256"), str)
            or not SHA256(wheel["sha256"])
            for wheel in wheels.values()
        )
    ):
        raise ValueError("Run manifest has malformed local-wheel identity")
    identity["inputs"]["profile"] = {key: value for key, value in profile.items() if key not in SAMPLE_BUDGET_FIELDS}
    profile_wheels = identity["inputs"]["profile"].get("local_wheels")
    if isinstance(profile_wheels, dict):
        identity["inputs"]["profile"]["local_wheels"] = sorted(profile_wheels)
    # Wheel locations may move, but the retained size and digest identify their bytes.
    for wheel in identity["inputs"].get("local_wheels", {}).values():
        if isinstance(wheel, dict):
            wheel.pop("path", None)
    scenario_revision = manifest.get("scenario_revision")
    if not isinstance(scenario_revision, str) or not scenario_revision:
        raise ValueError("Run manifest is missing scenario revision identity")
    browser = manifest.get("browser")
    if not isinstance(browser, dict) or not isinstance(browser.get("version"), str) or not browser["version"]:
        raise ValueError("Run manifest is missing browser runtime identity")
    host = manifest.get("host")
    if not isinstance(host, dict) or not all(
        isinstance(host.get(key), str) and host[key] for key in ("system", "machine")
    ):
        raise ValueError("Run manifest is missing host OS or architecture identity")
    return {
        "scenario_revision": scenario_revision,
        "evidence": identity,
        "browser_version": browser["version"],
        "host": {key: host[key] for key in ("system", "machine")},
    }


def _validate_derived_latency(directory: Path, manifest: dict) -> None:
    derived = manifest.get("derived_from")
    selected = manifest.get("selected_blocks")
    if (
        manifest.get("status") != "passed"
        or manifest.get("qualification") is not True
        or not isinstance(derived, dict)
        or not isinstance(selected, list)
        or not selected
        or any(type(block) is not int or block < 1 for block in selected)
        or 0 in selected
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("Derived latency run has malformed qualification provenance")
    parent_path = Path(derived.get("path", ""))
    parent_manifest_path = parent_path / "manifest.json"
    if not parent_manifest_path.is_file():
        raise ValueError("Derived latency parent qualification manifest is missing")
    parent_bytes = parent_manifest_path.read_bytes()
    parent = json.loads(parent_bytes)
    if (
        derived.get("manifest_sha256") != hashlib.sha256(parent_bytes).hexdigest()
        or derived.get("id") != parent.get("id")
        or derived.get("qualification") is not True
        or derived.get("status") != "passed"
        or parent.get("qualification") is not True
        or parent.get("status") != "passed"
        or _comparable_run_identity(manifest) != _comparable_run_identity(parent)
    ):
        raise ValueError("Derived latency parent qualification does not match its retained provenance")
    rows = [json.loads(line) for line in (directory / "samples.jsonl").read_text().splitlines()]
    if not rows or {row.get("block") for row in rows} != set(selected):
        raise ValueError("Derived latency samples do not match the selected qualification blocks")


def _associated_memory_manifest(directory: Path, memory_directory: Path) -> dict:
    manifest_path = memory_directory / "manifest.json"
    if not manifest_path.is_file() or not (memory_directory / "memory.jsonl").is_file():
        raise ValueError(f"Memory run is missing its manifest or observations: {memory_directory}")
    memory_manifest = json.loads(manifest_path.read_text())
    if memory_manifest.get("kind") != "memory":
        raise ValueError("Associated run is not a memory run")
    latency_manifest_path = directory / "manifest.json"
    if not latency_manifest_path.is_file():
        raise ValueError("Latency run is missing its manifest")
    latency_manifest = json.loads(latency_manifest_path.read_text())
    if latency_manifest.get("kind") == "derived-latency":
        _validate_derived_latency(directory, latency_manifest)
    elif latency_manifest.get("kind") is not None or latency_manifest.get("qualification") is True:
        raise ValueError("A combined report requires a latency run as its primary run")
    if _comparable_run_identity(latency_manifest) != _comparable_run_identity(memory_manifest):
        raise ValueError("Latency and memory runs have different frozen inputs or execution conditions")
    return memory_manifest


def report(directory: Path, *, memory_directory: Path | None = None) -> dict:
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    memory_manifest = _associated_memory_manifest(directory, memory_directory) if memory_directory else None
    memory_only = manifest.get("kind") == "memory"
    records = [json.loads(line) for line in (directory / "samples.jsonl").read_text().splitlines()]
    groups = defaultdict(list)
    for row in records:
        if not row.get("warmup"):
            groups[(row["app"], row["count"], row["action"], page_load(row))].append(row)
    rows = []
    for (app, count, action, load), observations in sorted(groups.items()):
        timings = [r["elapsed_ms"] for r in observations if r["status"] == "ok"]
        ready_timings = [ready_elapsed(r) for r in observations if r["status"] == "ok"]
        layout_timings = [
            elapsed
            for r in observations
            if r["status"] == "ok"
            if (elapsed := layout_inclusive_elapsed(r)) is not None
        ]
        layout_wait_timings = [
            wait for r in observations if r["status"] == "ok" if (wait := layout_extra_wait(r)) is not None
        ]
        layout_status = (
            "measured"
            if layout_timings and len(layout_timings) == len(timings)
            else "partially-measured"
            if layout_timings
            else "unavailable-legacy-endpoint"
            if timings
            else "no-successful-observations"
        )
        render_timings = [
            r["server_render_ms"]
            for r in observations
            if r["status"] == "ok" and r.get("server_render_ms") is not None
        ]
        observer_timings = [
            r["observer_ms"] for r in observations if r["status"] == "ok" and r.get("observer_ms") is not None
        ]
        semantic_observer_timings = [
            r["semantic_observer_ms"]
            for r in observations
            if r["status"] == "ok" and r.get("semantic_observer_ms") is not None
        ]
        prepare_timings = [
            r["server_prepare_ms"]
            for r in observations
            if r["status"] == "ok"
            and r.get("server_prepare_status") == "measured"
            and r.get("server_prepare_ms") is not None
        ]
        prepare_statuses = Counter(
            r.get("server_prepare_status", "missing") for r in observations if r["status"] == "ok"
        )
        prepare_reasons = Counter(
            r.get("server_prepare_reason") or "output preparation timing unavailable"
            for r in observations
            if r["status"] == "ok" and r.get("server_prepare_status") != "measured"
        )
        rows.append(
            {
                "app": app,
                "count": count,
                "action": action,
                "page_load": load,
                "attempts": sum(r["status"] != "not-run" for r in observations),
                "not_run": sum(r["status"] == "not-run" for r in observations),
                "successes": len(timings),
                "median_ms": statistics.median(timings) if timings else None,
                "min_ms": min(timings) if timings else None,
                "max_ms": max(timings) if timings else None,
                "layout_inclusive_median_ms": statistics.median(layout_timings) if layout_timings else None,
                "layout_inclusive_observations": len(layout_timings),
                "layout_endpoint_status": layout_status,
                "ready_only_median_ms": statistics.median(ready_timings) if ready_timings else None,
                "ready_only_observations": len(ready_timings),
                "layout_extra_wait_median_ms": statistics.median(layout_wait_timings) if layout_wait_timings else None,
                "layout_extra_wait_observations": len(layout_wait_timings),
                "server_render_median_ms": statistics.median(render_timings) if render_timings else None,
                "server_render_observations": len(render_timings),
                "observer_median_ms": statistics.median(observer_timings) if observer_timings else None,
                "observer_observations": len(observer_timings),
                "semantic_observer_median_ms": statistics.median(semantic_observer_timings)
                if semantic_observer_timings
                else None,
                "semantic_observer_observations": len(semantic_observer_timings),
                "server_prepare_median_ms": statistics.median(prepare_timings) if prepare_timings else None,
                "server_prepare_observations": len(prepare_timings),
                "server_prepare_statuses": dict(sorted(prepare_statuses.items())),
                "server_prepare_reasons": dict(sorted(prepare_reasons.items())),
                "server_prepare_kinds": sorted(
                    {r["server_prepare_kind"] for r in observations if r.get("server_prepare_kind")}
                ),
                "server_prepare_boundaries": sorted(
                    {r.get("server_timing_boundary", "complete") for r in observations}
                ),
                "latency_phase": representative_phase(observations),
                "layout_latency_phase": representative_layout_phase(observations),
                # Paint timing belongs to page loads only, and a group from an
                # earlier run keeps its original summary keys.
                **(
                    paint_summary(observations)
                    if action == "initial" and any("fcp_status" in r or "lcp_status" in r for r in observations)
                    else {}
                ),
            }
        )
    size_groups = defaultdict(list)
    size_path = directory / "sizes.jsonl"
    if size_path.exists():
        for line in size_path.read_text().splitlines():
            row = json.loads(line)
            if not row.get("warmup"):
                size_groups[(row["app"], row["count"], row["action"], page_load(row))].append(row)
    size_fields = ("final_html_bytes", "request_body_bytes", "encoded_response_body_bytes")
    size_rows = []
    for (app, count, action, load), observations in sorted(size_groups.items()):
        # Failed or incomplete measurements must not become zero-byte successes.
        valid = [row for row in observations if row["status"] == "ok"]
        entry = {"app": app, "count": count, "action": action, "page_load": load, "successes": len(valid)}
        for field in size_fields:
            values = [row[field] for row in valid if row.get(field) is not None]
            entry[field] = statistics.median(values) if values else None
            entry[field + "_observations"] = len(values)
        size_rows.append(entry)
    summary = {
        "schema": 1,
        "publication": False,
        "description": "Local diagnostic observations; no ranking or precise tail estimates",
        "rows": [] if memory_only else rows,
        "sizes": size_rows,
    }
    memory_path = (memory_directory or directory) / "memory.jsonl"
    if memory_path.exists():
        memory_records = [json.loads(line) for line in memory_path.read_text().splitlines()]
        retained_memory_records = [row for row in memory_records if not row.get("warmup")]
        memory_groups = defaultdict(list)
        for row in retained_memory_records:
            if row.get("status") == "ok":
                memory_groups[(row["app"], row["count"], row.get("action", "initial"), page_load(row))].append(row)
        memory_rows = []
        for (app, count, action, load), observations in sorted(memory_groups.items()):
            entry = {
                "app": app,
                "count": count,
                "action": action,
                "page_load": load,
                "successes": len(observations),
            }
            paths = {
                "server_rss_bytes": ("server", "rss_bytes"),
                "server_rss_idle_delta": ("server", "rss_bytes_idle_server_delta"),
                "server_uss_bytes": ("server", "uss_bytes"),
                "server_sampled_peak_rss_bytes": (None, "server_sampled_peak_rss_bytes"),
                "browser_heap_used_bytes": ("browser", "heap_used_bytes"),
                "browser_heap_blank_delta": ("browser", "heap_used_bytes_blank_browser_delta"),
                # Read after forced GC at a page's last observation only.
                "browser_heap_after_gc_used_bytes": ("browser", "heap_after_gc_used_bytes"),
                "browser_rss_bytes": ("browser", "browser_rss_bytes"),
                "browser_rss_blank_delta": ("browser", "browser_rss_bytes_blank_browser_delta"),
                "dom_nodes": ("browser", "nodes"),
                "dom_listeners": ("browser", "listeners"),
            }
            for output_key, (section, key) in paths.items():
                values = []
                for row in observations:
                    value = row.get(key) if section is None else row.get(section, {}).get(key)
                    if isinstance(value, (int, float)):
                        values.append(value)
                entry[output_key] = statistics.median(values) if values else None
                entry[output_key + "_observations"] = len(values)
                entry[output_key + "_min"] = min(values) if values else None
                entry[output_key + "_max"] = max(values) if values else None
            # Separate rows that never requested the after-GC reading (an older
            # run, or not the page's last observation) from rows whose attempt
            # failed, so the report can say which.
            entry["browser_heap_after_gc_attempts"] = sum(
                "heap_after_gc" in (row.get("browser") or {}) for row in observations
            )
            memory_rows.append(entry)
        summary["memory"] = {
            "rows": memory_rows,
            "invalid_observations": sum(row.get("status") != "ok" for row in retained_memory_records),
            "invalid_records": [row for row in retained_memory_records if row.get("status") != "ok"],
        }
        memory_root = memory_directory or directory
        memory_samples_path = memory_root / (
            "memory-samples.jsonl" if (memory_root / "memory-samples.jsonl").exists() else "samples.jsonl"
        )
        memory_samples = (
            [json.loads(line) for line in memory_samples_path.read_text().splitlines()]
            if memory_samples_path.exists()
            else []
        )
        summary["memory"]["not_run_observations"] = sum(
            row.get("status") == "not-run" for row in memory_samples if not row.get("warmup")
        )
    write_json(directory / "summary.json", summary)
    sample_fields = (
        "app",
        "count",
        "action",
        "page_load",
        "status",
        "elapsed_ms",
        "ready_elapsed_ms",
        "layout_inclusive_elapsed_ms",
        "layout_extra_wait_ms",
        "layout_endpoint",
        "server_render_ms",
        "server_render_status",
        "observer_ms",
        "semantic_observer_ms",
        "server_prepare_ms",
        "server_prepare_status",
        "server_prepare_reason",
        "server_prepare_kind",
        "server_timing_boundary",
        "latency_phase",
        "fcp_ms",
        "fcp_status",
        "fcp_reason",
        "lcp_ms",
        "lcp_status",
        "lcp_reason",
    )

    def graph_sample_value(row: dict, key: str) -> object:
        if key == "ready_elapsed_ms":
            return ready_elapsed(row)
        if key == "layout_inclusive_elapsed_ms":
            return layout_inclusive_elapsed(row)
        if key == "layout_extra_wait_ms":
            return layout_extra_wait(row)
        if key == "layout_endpoint":
            return LAYOUT_ENDPOINT if layout_inclusive_elapsed(row) is not None else None
        if key in ("fcp_ms", "lcp_ms"):
            return paint_value(row, key.removesuffix("_ms"))
        return row.get(key)

    graph_data = {
        "run": {
            key: manifest.get(key)
            for key in ("id", "status", "scenario_revision", "kind", "selected_blocks", "derived_from")
        },
        "memory_run": (
            {key: memory_manifest.get(key) for key in ("id", "status", "scenario_revision", "kind")}
            if memory_manifest
            else None
        ),
        "profile": manifest.get("inputs", {}).get("inputs", {}).get("profile", {}),
        "samples": [
            {key: page_load(row) if key == "page_load" else graph_sample_value(row, key) for key in sample_fields}
            for row in records
            if not memory_only
            if not row.get("warmup")
        ],
        "sizes": [
            {
                key: page_load(row) if key == "page_load" else row.get(key)
                for key in ("app", "count", "action", "page_load", "status", *size_fields)
            }
            for observations in size_groups.values()
            for row in observations
        ],
        "memory": summary.get("memory", {}).get("rows", []),
        "memory_invalid_observations": summary.get("memory", {}).get("invalid_observations", 0),
        "memory_not_run_observations": summary.get("memory", {}).get("not_run_observations", 0),
        "memory_invalid_records": [
            {
                key: page_load(row) if key == "page_load" else row.get(key)
                for key in ("app", "count", "action", "page_load", "status", "reason", "error")
            }
            for row in summary.get("memory", {}).get("invalid_records", [])
            if not row.get("warmup")
        ],
    }
    # Escape markup delimiters so application labels cannot terminate the data script.
    payload = json.dumps(graph_data).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    assets = Path(__file__).parent
    document = (assets / "report.html").read_text().replace("__BENCH_SCRIPT__", (assets / "report.js").read_text())
    (directory / "report.html").write_text(document.replace("__BENCH_DATA__", payload))
    return summary
