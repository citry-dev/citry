"""Reports distinguish failed attempts, skipped work and measured payloads."""

import hashlib
import json

import pytest
from citry_bench.browser import server_prepare_kind, server_prepare_time, server_render_time
from citry_bench.config import CACHE
from citry_bench.results import append, report, representative_layout_phase, representative_phase
from playwright.sync_api import sync_playwright


def _run_manifest(run_id, *, kind=None, blocks=2, runner_hash="a" * 64):
    manifest = {
        "id": run_id,
        "status": "passed",
        "scenario_revision": "canonical-project-v1",
        "browser": {"version": "Chromium 1", "executable": f"/{run_id}/chromium"},
        "host": {"system": "Darwin", "machine": "arm64", "node": run_id},
        "inputs": {
            "inputs": {
                "profile": {
                    "name": run_id,
                    "mode": "native",
                    "apps": ["citry"],
                    "counts": [14],
                    "scenario": "canonical",
                    "browser": "chromium",
                    "blocks": blocks,
                    "sessions": 1,
                    "warmups": 0,
                    "cycles": 1,
                    "network": "loopback",
                },
                "runner": {"runner.py": runner_hash},
                "scenario": {"scenario.py": "b" * 64},
                "apps": {"citry": {"app.py": "c" * 64}},
                "runner_environment": {"python": "d" * 64},
                "local_wheels": {"citry": {"path": f"/{run_id}/citry.whl", "size": 10, "sha256": "e" * 64}},
            },
            "build_sources": {"citry": {"assets": {"type": "directory"}, "app.py": "f" * 64}},
            "artifacts": {"citry": {"site-packages/citry.py": "1" * 64}},
            "browser_artifacts": {"chromium": "2" * 64},
            "source_policy": "frozen sources",
        },
    }
    if kind:
        manifest["kind"] = kind
    return manifest


def test_summary_excludes_warmup_and_failed_sizes_and_separates_skips(tmp_path):
    common = {"app": "fixture", "count": 10, "action": "select", "warmup": False}
    for status, elapsed in (("ok", 10), ("error", None), ("not-run", None)):
        append(tmp_path / "samples.jsonl", {**common, "status": status, "elapsed_ms": elapsed})
    for warmup, status, value in ((False, "ok", 100), (True, "ok", 900), (False, "error", 800)):
        append(
            tmp_path / "sizes.jsonl",
            {
                **common,
                "warmup": warmup,
                "status": status,
                "final_html_bytes": value,
                "request_body_bytes": 0,
                "encoded_response_body_bytes": value * 2,
            },
        )
    summary = report(tmp_path)
    assert summary["rows"][0]["attempts"] == 2
    assert summary["rows"][0]["not_run"] == 1
    assert summary["sizes"][0]["final_html_bytes"] == 100
    assert summary["sizes"][0]["request_body_bytes"] == 0
    assert summary["sizes"][0]["encoded_response_body_bytes"] == 200
    assert summary["sizes"][0]["encoded_response_body_bytes_observations"] == 1


def test_colocated_composite_uses_separate_memory_samples(tmp_path):
    (tmp_path / "samples.jsonl").write_text("")
    (tmp_path / "sizes.jsonl").write_text("")
    append(
        tmp_path / "memory.jsonl",
        {"app": "django_rusty_templates", "count": 140, "action": "filter", "status": "invalid", "error": "failed"},
    )
    append(tmp_path / "memory-samples.jsonl", {"status": "not-run"})

    summary = report(tmp_path)

    assert summary["memory"]["not_run_observations"] == 1
    report_text = (tmp_path / "report.html").read_text()
    assert "Rusty + HTMX + Alpine" in report_text
    assert '"error": "failed"' in report_text


def test_offline_graphs_filter_observations_preserve_zero_and_escape_labels(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    hostile = "</script><script>window.injected=true</script>"
    for count in (10, 325):
        for action in ("initial", "select"):
            common = {"app": hostile, "count": count, "action": action, "warmup": False, "status": "ok"}
            append(tmp_path / "samples.jsonl", {**common, "elapsed_ms": count})
            append(
                tmp_path / "sizes.jsonl",
                {**common, "final_html_bytes": count, "request_body_bytes": 0, "encoded_response_body_bytes": count},
            )
    append(
        tmp_path / "samples.jsonl",
        {"app": "failed", "count": 10, "action": "select", "status": "error", "elapsed_ms": None},
    )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "id": "interrupted",
                "status": "incomplete",
                "inputs": {"inputs": {"profile": {"apps": [hostile, "failed", "unstarted"], "counts": [10, 325]}}},
            }
        )
    )
    report(tmp_path)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: external.append(request.url) if request.url.startswith("http") else None)
        page.goto((tmp_path / "report.html").as_uri())
        assert page.locator("table").count() == 0
        assert page.locator("#charts svg").count() == 7
        assert page.locator("a.download").count() == 7
        assert not page.evaluate("Boolean(window.injected)")
        assert "1 failed" in page.locator("#run-status").inner_text()
        initial_chart = page.locator(
            "#charts article", has=page.locator("h3", has_text="First-load time to interactive")
        ).locator("svg")
        assert "layout-endpoint-unavailable=1" in initial_chart.text_content()
        # Rows recorded without the layout endpoint keep their ready-only bars.
        assert "10.00 ms" in initial_chart.text_content()
        request_chart = page.locator(
            "#charts article", has=page.locator("h3", has_text="Action request size")
        ).locator("svg")
        assert "0 B" in request_chart.text_content()
        assert "No successful measurement" in request_chart.text_content()
        assert "No observations recorded" in request_chart.text_content()
        assert "unstarted: No observations recorded" in request_chart.locator("desc").text_content()
        page.select_option("#count", "325")
        latency_section = page.locator("#charts article", has=page.locator("h3", has_text="Server-action latency"))
        latency = latency_section.locator("svg")
        assert "325 rows, select" in latency.get_attribute("aria-label")
        assert "325.00 ms" in latency.text_content()
        assert "10.00 ms" not in latency.text_content()
        # Downloads contain the selected chart, not a stale prior selection.
        exported = latency_section.locator("a.download").evaluate("async a => (await fetch(a.href)).text()")
        assert "325 rows, select" in exported
        assert not errors
        assert not external
        browser.close()


def test_memory_report_separates_page_loads_and_suppresses_latency(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    (tmp_path / "samples.jsonl").write_text("")
    (tmp_path / "sizes.jsonl").write_text("")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "id": "memory-smoke",
                "kind": "memory",
                "status": "passed",
                "scenario_revision": "canonical-project-v1",
                "inputs": {"inputs": {"profile": {"apps": ["citry"], "counts": [14]}}},
            }
        )
    )
    mib = 1024 * 1024
    for load, rss in ((1, 100 * mib), (2, 80 * mib)):
        append(
            tmp_path / "memory.jsonl",
            {
                "app": "citry",
                "count": 14,
                "action": "initial",
                "page_load": load,
                "warmup": False,
                "status": "ok",
                "server": {"rss_bytes": rss, "rss_bytes_idle_server_delta": (-20 if load == 1 else -10) * mib},
                "browser": {"browser_rss_bytes": rss * 2, "heap_used_bytes": rss // 2, "nodes": 8},
                "server_sampled_peak_rss_bytes": rss + 10,
            },
        )
    append(
        tmp_path / "memory.jsonl",
        {
            "app": "citry",
            "count": 14,
            "action": "initial",
            "page_load": 1,
            "warmup": False,
            "status": "ok",
            "server": {"rss_bytes": 120 * mib, "rss_bytes_idle_server_delta": 0},
            "browser": {"browser_rss_bytes": 240 * mib, "heap_used_bytes": 60 * mib, "nodes": 9},
            "server_sampled_peak_rss_bytes": 130 * mib,
        },
    )
    append(
        tmp_path / "memory.jsonl",
        {
            "app": "citry",
            "count": 14,
            "action": "initial",
            "page_load": 1,
            "warmup": False,
            "status": "ok",
            "server": {"rss_bytes": 1000 * mib, "rss_bytes_idle_server_delta": -100 * mib},
            "browser": {"browser_rss_bytes": 2000 * mib, "heap_used_bytes": 500 * mib, "nodes": 10},
            "server_sampled_peak_rss_bytes": 1100 * mib,
        },
    )
    summary = report(tmp_path)
    assert summary["rows"] == []
    assert [(row["page_load"], row["server_rss_bytes"]) for row in summary["memory"]["rows"]] == [
        (1, 120 * mib),
        (2, 80 * mib),
    ]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        assert page.locator("#charts h3").all_text_contents() == [
            "Server RSS at readiness",
            "Server RSS growth from idle",
            "Server sampled peak RSS",
            "Browser RSS at readiness",
            "Browser RSS growth from blank",
            "JavaScript heap at readiness",
            "JavaScript heap growth from blank",
            "DOM nodes at readiness",
            "Event listeners at readiness",
        ]
        page.select_option("#page-load", "2")
        assert "80.00 MiB" in page.locator("#charts svg").nth(0).text_content()
        assert "N=1" in page.locator("#charts svg").nth(0).text_content()
        page.select_option("#page-load", "1")
        delta = page.locator("#charts svg").nth(1)
        assert "-20.00 MiB" in delta.text_content()
        range_text = page.locator("#charts svg").nth(0).text_content()
        assert "range 100.00 MiB" in range_text
        assert "1000.00 MiB" in range_text
        assert all(
            float(value) >= 0
            for value in delta.locator("rect").evaluate_all("nodes => nodes.map(n => n.getAttribute('width'))")
        )
        assert all(
            180 <= float(value) <= 540
            for value in page.locator("#charts svg")
            .nth(0)
            .locator("line[stroke-width='2']")
            .evaluate_all("nodes => nodes.flatMap(n => [n.getAttribute('x1'), n.getAttribute('x2')])")
        )
        assert page.locator("a.download").nth(0).get_attribute("download") == "server_rss_bytes-initial-14-load-1.svg"
        browser.close()


def test_memory_report_shows_heap_after_gc_only_where_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    (tmp_path / "samples.jsonl").write_text("")
    (tmp_path / "sizes.jsonl").write_text("")
    manifest = _run_manifest("memory-gc", kind="memory", blocks=1)
    manifest["inputs"]["inputs"]["profile"]["apps"] = ["citry", "older", "failed"]
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    mib = 1024 * 1024
    browsers = {
        # A current row carries the after-GC reading next to the existing heap.
        "citry": {
            "heap_used_bytes": 30 * mib,
            "heap_after_gc": {"status": "measured"},
            "heap_after_gc_used_bytes": 12 * mib,
        },
        # A row retained from a run made before the reading existed.
        "older": {"heap_used_bytes": 40 * mib},
        # A current row whose forced collection failed.
        "failed": {
            "heap_used_bytes": 50 * mib,
            "heap_after_gc": {"status": "unavailable"},
            "heap_after_gc_used_bytes": None,
        },
    }
    plain = {"heap_used_bytes": 30 * mib}
    rows_to_write = [(app, "initial", 0, browser_memory) for app, browser_memory in browsers.items()]
    # Only a page's last action reads the heap after GC; the earlier probe did not.
    rows_to_write += [
        ("citry", "select", 0, plain),
        ("citry", "probe", 0, plain),
        ("citry", "probe", 1, browsers["citry"]),
    ]
    for app, action, cycle, browser_memory in rows_to_write:
        append(
            tmp_path / "memory.jsonl",
            {
                "app": app,
                "count": 14,
                "action": action,
                "cycle": cycle,
                "page_load": 1,
                "warmup": False,
                "status": "ok",
                "server": {},
                "browser": browser_memory,
            },
        )
    summary = report(tmp_path)
    rows = {row["app"]: row for row in summary["memory"]["rows"] if row["action"] == "initial"}
    assert rows["citry"]["browser_heap_after_gc_used_bytes"] == 12 * mib
    assert rows["citry"]["browser_heap_used_bytes"] == 30 * mib
    assert rows["older"]["browser_heap_after_gc_used_bytes"] is None
    assert [rows[app]["browser_heap_after_gc_attempts"] for app in ("citry", "older", "failed")] == [1, 0, 1]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        titles = page.locator("#charts h3").all_text_contents()
        assert (
            titles.index("JavaScript heap after GC at readiness")
            == titles.index("JavaScript heap growth from blank") + 1
        )
        chart = page.locator("#charts article").nth(titles.index("JavaScript heap after GC at readiness"))
        text = chart.locator("svg").text_content()
        assert "12.00 MiB" in text
        assert "Not recorded for this app and action" in text
        assert "No successful measurement" in text
        description = chart.locator("desc").text_content()
        assert "unavailable=1; not recorded=0" in description
        assert "unavailable=0; not recorded=1" in description
        # No row of this action read the heap after GC, so the chart is absent.
        page.select_option("#action", "select")
        assert "JavaScript heap after GC, after action" not in page.locator("#charts h3").all_text_contents()
        page.select_option("#action", "probe")
        titles = page.locator("#charts h3").all_text_contents()
        assert "JavaScript heap after GC, after action" in titles
        probe = page.locator("#charts article").nth(titles.index("JavaScript heap after GC, after action"))
        assert "N=1; unavailable=0; not recorded=1" in probe.locator("desc").text_content()
        browser.close()


def test_combined_report_keeps_latency_and_memory_runs_separate(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    latency = tmp_path / "latency"
    memory = tmp_path / "memory"
    latency.mkdir()
    memory.mkdir()
    (latency / "manifest.json").write_text(json.dumps(_run_manifest("latency", blocks=20)))
    (memory / "manifest.json").write_text(json.dumps(_run_manifest("memory", kind="memory", blocks=1)))
    for path in (latency / "manifest.json", memory / "manifest.json"):
        manifest = json.loads(path.read_text())
        manifest["inputs"]["inputs"]["profile"]["counts"] = [14, 1400]
        path.write_text(json.dumps(manifest))
    append(
        latency / "samples.jsonl",
        {"app": "citry", "count": 14, "action": "initial", "status": "ok", "elapsed_ms": 3},
    )
    (latency / "sizes.jsonl").write_text("")
    append(
        memory / "memory.jsonl",
        {"app": "citry", "count": 14, "action": "initial", "status": "ok", "server": {"rss_bytes": 10}},
    )
    append(
        memory / "memory.jsonl",
        {"app": "citry", "count": 14, "action": "initial", "status": "error", "reason": "sample failed"},
    )
    append(
        memory / "memory.jsonl",
        {"app": "citry", "count": 14, "action": "initial", "status": "error", "warmup": True},
    )
    append(
        memory / "memory.jsonl",
        {"app": "failed-only", "count": 1400, "action": "select", "status": "error", "reason": "action failed"},
    )
    append(
        memory / "memory.jsonl",
        {"app": "failed-only", "count": 1400, "action": "initial", "page_load": 3, "status": "error"},
    )
    append(
        latency / "samples.jsonl",
        {"app": "citry", "count": 1400, "action": "initial", "status": "ok", "elapsed_ms": 30},
    )
    append(
        memory / "memory.jsonl",
        {"app": "citry", "count": 1400, "action": "initial", "status": "ok", "server": {"rss_bytes": 100}},
    )
    append(memory / "samples.jsonl", {"status": "not-run"})

    summary = report(latency, memory_directory=memory)

    assert summary["rows"][0]["median_ms"] == 3
    assert summary["memory"]["rows"][0]["server_rss_bytes"] == 10
    assert summary["memory"]["invalid_observations"] == 3
    assert summary["memory"]["not_run_observations"] == 1
    assert summary["memory"]["invalid_records"][0]["reason"] == "sample failed"
    report_text = (latency / "report.html").read_text()
    assert '"id": "latency"' in report_text
    assert '"id": "memory"' in report_text
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((latency / "report.html").as_uri())
        assert "Latency run latency" in page.locator("#run-status").inner_text()
        assert "memory run memory" in page.locator("#run-status").inner_text()
        memory_chart = page.locator("#charts article", has=page.locator("h3", has_text="Server RSS at readiness"))
        assert memory_chart.count() == 1
        assert "failed=1" in memory_chart.locator("svg").text_content()
        assert memory_chart.locator("circle").count() == 0
        assert page.locator("#charts h3", has_text="First-load time to interactive").count() == 1
        assert page.locator("#charts h3", has_text="Server RSS at readiness").count() == 1
        page.select_option("#count", "1400")
        assert "1400 outputs" in memory_chart.locator("svg").get_attribute("aria-label")
        assert "failed=0" in memory_chart.locator("svg").text_content()
        assert page.locator("#action option[value=select]").count() == 1
        assert page.locator("#page-load option[value='3']").count() == 1
        page.select_option("#action", "select")
        action_memory = page.locator("#charts article", has=page.locator("h3", has_text="Server RSS after action"))
        assert "failed-only" in action_memory.locator("svg").text_content()
        assert "failed=1" in action_memory.locator("svg").text_content()
        assert not errors
        browser.close()


def test_combined_report_rejects_identity_mismatch_before_rewriting(tmp_path):
    latency = tmp_path / "latency"
    memory = tmp_path / "memory"
    latency.mkdir()
    memory.mkdir()
    (latency / "manifest.json").write_text(json.dumps(_run_manifest("latency")))
    (memory / "manifest.json").write_text(json.dumps(_run_manifest("memory", kind="memory", runner_hash="3" * 64)))
    (latency / "samples.jsonl").write_text("")
    (latency / "sizes.jsonl").write_text("")
    (memory / "memory.jsonl").write_text("")
    (latency / "summary.json").write_text("preserve")

    with pytest.raises(ValueError, match="different frozen inputs"):
        report(latency, memory_directory=memory)

    assert (latency / "summary.json").read_text() == "preserve"


def test_combined_report_accepts_only_retained_derived_qualification_blocks(tmp_path):
    parent = tmp_path / "qualification"
    latency = tmp_path / "derived"
    memory = tmp_path / "memory"
    parent.mkdir()
    latency.mkdir()
    memory.mkdir()
    parent_manifest = _run_manifest("qualification")
    parent_manifest["qualification"] = True
    parent_bytes = json.dumps(parent_manifest).encode()
    (parent / "manifest.json").write_bytes(parent_bytes)
    latency_manifest = {
        **parent_manifest,
        "id": "derived",
        "kind": "derived-latency",
        "selected_blocks": [1, 2],
        "derived_from": {
            "id": "qualification",
            "path": str(parent),
            "manifest_sha256": hashlib.sha256(parent_bytes).hexdigest(),
            "qualification": True,
            "status": "passed",
        },
    }
    (latency / "manifest.json").write_text(json.dumps(latency_manifest))
    (memory / "manifest.json").write_text(json.dumps(_run_manifest("memory", kind="memory", blocks=1)))
    append(
        latency / "samples.jsonl",
        {"app": "citry", "count": 14, "action": "initial", "status": "ok", "elapsed_ms": 3, "block": 1},
    )
    append(
        latency / "samples.jsonl",
        {"app": "citry", "count": 14, "action": "initial", "status": "ok", "elapsed_ms": 4, "block": 2},
    )
    (latency / "sizes.jsonl").write_text("")
    (memory / "memory.jsonl").write_text("")

    assert report(latency, memory_directory=memory)["rows"][0]["median_ms"] == 3.5
    report_text = (latency / "report.html").read_text()
    assert '"selected_blocks": [1, 2]' in report_text
    assert "Timing reuses normal qualification blocks" in report_text

    latency_manifest["derived_from"]["manifest_sha256"] = "0" * 64
    (latency / "manifest.json").write_text(json.dumps(latency_manifest))
    with pytest.raises(ValueError, match="retained provenance"):
        report(latency, memory_directory=memory)


@pytest.mark.parametrize("missing_from", ["latency", "memory", "both"])
def test_combined_report_rejects_missing_artifact_identity(tmp_path, missing_from):
    latency = tmp_path / "latency"
    memory = tmp_path / "memory"
    latency.mkdir()
    memory.mkdir()
    latency_manifest = _run_manifest("latency")
    memory_manifest = _run_manifest("memory", kind="memory")
    if missing_from in {"latency", "both"}:
        latency_manifest["inputs"].pop("artifacts")
    if missing_from in {"memory", "both"}:
        memory_manifest["inputs"].pop("artifacts")
    (latency / "manifest.json").write_text(json.dumps(latency_manifest))
    (memory / "manifest.json").write_text(json.dumps(memory_manifest))
    (memory / "memory.jsonl").write_text("")

    with pytest.raises(ValueError, match="missing frozen source or artifact identity"):
        report(latency, memory_directory=memory)


@pytest.mark.parametrize(
    "malformation",
    [
        "null-runner",
        "null-app",
        "shallow-app",
        "bad-digest",
        "missing-wheel-path",
        "extra-wheel-field",
        "invalid-wheel-name",
        "missing-revision",
    ],
)
def test_combined_report_rejects_matching_malformed_identity(tmp_path, malformation):
    latency = tmp_path / "latency"
    memory = tmp_path / "memory"
    latency.mkdir()
    memory.mkdir()
    manifests = [_run_manifest("latency"), _run_manifest("memory", kind="memory")]
    for manifest in manifests:
        if malformation == "null-runner":
            manifest["inputs"]["inputs"]["runner"] = None
        elif malformation == "null-app":
            manifest["inputs"]["inputs"]["apps"] = {"citry": None}
        elif malformation == "shallow-app":
            manifest["inputs"]["inputs"]["apps"] = {"citry": "a" * 64}
        elif malformation == "bad-digest":
            manifest["inputs"]["inputs"]["runner"] = {"runner.py": "not-a-digest"}
        elif malformation == "missing-wheel-path":
            manifest["inputs"]["inputs"]["local_wheels"]["citry"].pop("path")
        elif malformation == "extra-wheel-field":
            manifest["inputs"]["inputs"]["local_wheels"]["citry"]["extra"] = True
        elif malformation == "invalid-wheel-name":
            manifest["inputs"]["inputs"]["local_wheels"][""] = manifest["inputs"]["inputs"]["local_wheels"].pop(
                "citry"
            )
        else:
            manifest.pop("scenario_revision")
    (latency / "manifest.json").write_text(json.dumps(manifests[0]))
    (memory / "manifest.json").write_text(json.dumps(manifests[1]))
    (memory / "memory.jsonl").write_text("")

    with pytest.raises(ValueError, match=r"malformed (?:frozen|local-wheel)|scenario revision"):
        report(latency, memory_directory=memory)


@pytest.mark.parametrize(("field", "value"), [("kind", "custom"), ("qualification", True)])
def test_combined_report_rejects_nonmeasurement_primary(tmp_path, field, value):
    latency = tmp_path / "latency"
    memory = tmp_path / "memory"
    latency.mkdir()
    memory.mkdir()
    latency_manifest = _run_manifest("latency")
    latency_manifest[field] = value
    (latency / "manifest.json").write_text(json.dumps(latency_manifest))
    (memory / "manifest.json").write_text(json.dumps(_run_manifest("memory", kind="memory")))
    (memory / "memory.jsonl").write_text("")

    with pytest.raises(ValueError, match="latency run as its primary"):
        report(latency, memory_directory=memory)


def test_canonical_scenario_revision_uses_output_scale_labels(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    for action in ("initial", "select"):
        append(
            tmp_path / "samples.jsonl",
            {"app": "citry", "count": 14, "action": action, "warmup": False, "status": "ok", "elapsed_ms": 1},
        )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "id": "canonical",
                "status": "passed",
                "scenario_revision": "canonical-project-v1",
                "inputs": {"inputs": {"profile": {"apps": ["citry"], "counts": [14]}}},
            }
        )
    )
    report(tmp_path)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        assert page.locator("#count-label").text_content() == "Canonical outputs"
        assert page.locator("#count option").text_content() == "14 outputs"
        action_ready = page.locator(
            "#charts article", has=page.locator("h3", has_text="Server-action latency")
        ).locator("svg")
        assert "14 outputs, select" in action_ready.get_attribute("aria-label")
        browser.close()


def test_render_metric_keeps_missing_distinct_from_zero_and_browser_rendering():
    payload = {"server_timings": [{"header": "application;dur=3, render;dur=0"}]}
    assert server_render_time(payload, "server") == (0, "measured")
    assert server_render_time(payload, "browser") == (None, "not-applicable")
    assert server_render_time({"server_timings": [{"header": "application;dur=3"}]}, "server") == (None, "missing")
    payload["server_timings"].append({"header": "render;dur=1.25"})
    assert server_render_time(payload, "server") == (1.25, "measured")
    assert server_render_time(payload, "hybrid", initial=True) == (1.25, "measured")
    assert server_render_time(payload, "hybrid", initial=False) == (None, "not-applicable")


def test_server_output_kind_names_the_generated_payload():
    assert server_prepare_kind({"rendering": "server", "transport": "http"}) == "html"
    assert server_prepare_kind({"rendering": "browser", "transport": "http"}) == "json"
    assert server_prepare_kind({"rendering": "browser", "transport": "websocket"}) == "delta"
    assert server_prepare_kind({"rendering": "hybrid", "update_payload": "delta"}, initial=True) == "html"
    assert server_prepare_kind({"rendering": "hybrid", "update_payload": "delta"}, initial=False) == "delta"
    assert server_prepare_kind({"rendering": "hybrid", "update_payload": "json"}, initial=False) == "json"


def test_html_output_preparation_uses_valid_render_span_when_no_narrower_metric_exists():
    missing = {
        "server_prepare_ms": None,
        "server_prepare_status": "missing",
        "server_prepare_reason": "prepare timing is missing",
    }
    assert server_prepare_time(missing, "server", 1.25) == (1.25, "measured", None)
    assert server_prepare_time(missing, "browser", None) == (None, "missing", "prepare timing is missing")
    invalid = {**missing, "server_prepare_status": "invalid"}
    assert server_prepare_time(invalid, "server", 1.25) == (None, "invalid", "prepare timing is missing")
    assert server_prepare_time(missing, "hybrid", 1.25, initial=True) == (1.25, "measured", None)
    assert server_prepare_time(missing, "hybrid", None, initial=False) == (
        None,
        "missing",
        "prepare timing is missing",
    )


@pytest.mark.parametrize("header", ["render;dur=NaN", "render;dur=inf", "render;dur=-1", "render;dur=1,render;dur=2"])
def test_render_metric_rejects_invalid_measurements(header):
    with pytest.raises(ValueError, match=r"[Rr]ender timing"):
        server_render_time({"server_timings": [{"header": header}]}, "server")


def test_phase_representative_averages_the_two_observations_that_define_the_median():
    rows = [
        {
            "status": "ok",
            "elapsed_ms": 10,
            "latency_phase": {
                "status": "measured",
                "reason": None,
                "segments": [
                    {"key": "browser_before", "ms": 1},
                    {"key": "server", "ms": 2},
                    {"key": "browser_after", "ms": 7},
                ],
            },
        },
        {
            "status": "ok",
            "elapsed_ms": 20,
            "latency_phase": {
                "status": "unavailable",
                "reason": "ambiguous exchange",
                "segments": [{"key": "unclassified", "ms": 20}],
            },
        },
    ]
    result = representative_phase(rows)
    assert result == {
        "total_ms": 15,
        "segments": [
            {"key": "browser_before", "ms": 0.5},
            {"key": "server", "ms": 1},
            {"key": "browser_after", "ms": 3.5},
            {"key": "unclassified", "ms": 10},
        ],
        "measured_observations": 1,
        "unavailable_observations": 1,
        "unavailable_reasons": {"ambiguous exchange": 1},
    }
    assert sum(segment["ms"] for segment in result["segments"]) == result["total_ms"]


def test_layout_phase_averages_ready_phases_and_wait_from_the_same_observations():
    rows = [
        {"status": "ok", "elapsed_ms": 7},
        {
            "status": "ok",
            "elapsed_ms": 10,
            "ready_elapsed_ms": 10,
            "layout_extra_wait_ms": 5,
            "layout_inclusive_elapsed_ms": 15,
            "layout_endpoint": "second-rAF-layout-opportunity-v1",
            "latency_phase": {"status": "measured", "segments": [{"key": "server", "ms": 10}]},
        },
        {
            "status": "ok",
            "elapsed_ms": 20,
            "ready_elapsed_ms": 20,
            "layout_extra_wait_ms": 10,
            "layout_inclusive_elapsed_ms": 30,
            "layout_endpoint": "second-rAF-layout-opportunity-v1",
            "latency_phase": {"status": "measured", "segments": [{"key": "server", "ms": 20}]},
        },
    ]

    result = representative_layout_phase(rows)

    assert result["total_ms"] == 22.5
    assert result["segments"] == [
        {"key": "server", "ms": 15},
        {"key": "layout_wait", "ms": 7.5},
    ]
    assert sum(segment["ms"] for segment in result["segments"]) == result["total_ms"]


def test_mixed_legacy_and_layout_samples_keep_endpoints_separate_in_summary_and_report(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    common = {"app": "citry", "count": 14, "action": "initial", "status": "ok", "warmup": False}
    append(tmp_path / "samples.jsonl", {**common, "elapsed_ms": 7})
    for ready, extra in ((10, 5), (20, 10)):
        append(
            tmp_path / "samples.jsonl",
            {
                **common,
                "elapsed_ms": ready,
                "ready_elapsed_ms": ready,
                "layout_extra_wait_ms": extra,
                "layout_inclusive_elapsed_ms": ready + extra,
                "layout_endpoint": "second-rAF-layout-opportunity-v1",
                "latency_phase": {"status": "measured", "segments": [{"key": "server", "ms": ready}]},
            },
        )

    summary = report(tmp_path)
    result = summary["rows"][0]

    assert result["median_ms"] == 10
    assert result["ready_only_median_ms"] == 10
    assert result["layout_inclusive_median_ms"] == 22.5
    assert result["layout_inclusive_observations"] == 2
    assert result["layout_endpoint_status"] == "partially-measured"
    assert result["layout_extra_wait_median_ms"] == 7.5
    assert result["latency_phase"]["total_ms"] == 10
    assert result["layout_latency_phase"]["total_ms"] == 22.5
    assert sum(part["ms"] for part in result["layout_latency_phase"]["segments"]) == 22.5

    report_html = (tmp_path / "report.html").read_text()
    payload = report_html.split('<script id="report-data" type="application/json">', 1)[1].split("</script>", 1)[0]
    graph_rows = json.loads(payload)["samples"]
    assert graph_rows[0]["layout_inclusive_elapsed_ms"] is None
    assert graph_rows[0]["layout_endpoint"] is None
    assert [row["layout_inclusive_elapsed_ms"] for row in graph_rows[1:]] == [15, 30]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        phase = page.locator(
            "#charts article", has=page.locator("h3", has_text="First-load time to interactive")
        ).locator("svg")
        # One legacy row lacks the layout endpoint, so the chart keeps every row on the ready-only endpoint
        # and reports the additional wait as unavailable instead of mixing the two endpoints in one bar.
        assert "N=3; phases=2 measured/1 unavailable; layout-endpoint-unavailable=1" in phase.text_content()
        assert "additional wait unavailable=1" in phase.text_content()
        assert phase.locator('rect[aria-label="Main document server: 10.00 ms"]').count() == 1
        assert phase.locator('rect[aria-label^="Additional ready-to-layout wait"]').count() == 0
        assert "representative segments sum to median 10.00 ms" in phase.locator("desc").text_content()
        assert "rendering opportunity, not physical paint" in page.locator("details").text_content()
        browser.close()


@pytest.mark.parametrize(
    "phase",
    [
        None,
        {"status": "measured", "segments": [{"key": "server", "ms": -1}]},
        {"status": "measured", "segments": [{"key": "unknown", "ms": 10}]},
    ],
)
def test_missing_or_malformed_phase_is_wholly_unclassified(phase):
    result = representative_phase([{"status": "ok", "elapsed_ms": 10, "latency_phase": phase}])
    assert result["segments"] == [{"key": "unclassified", "ms": 10}]
    assert result["measured_observations"] == 0
    assert result["unavailable_observations"] == 1


def test_output_preparation_stays_in_summary_without_a_chart(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    for app, value, kind in (("citry", 0, "html"), ("python_vue", 1.25, "json")):
        for action in ("initial", "select"):
            append(
                tmp_path / "samples.jsonl",
                {
                    "app": app,
                    "count": 1000,
                    "action": action,
                    "status": "ok",
                    "elapsed_ms": 10,
                    "server_prepare_ms": value,
                    "server_prepare_status": "measured",
                    "server_prepare_kind": kind,
                    "latency_phase": {
                        "status": "measured",
                        "reason": None,
                        "segments": [
                            {"key": "browser_before", "ms": 1},
                            {"key": "server", "ms": 2},
                            {"key": "exchange_residual", "ms": 3},
                            {"key": "response_receive", "ms": 1},
                            {"key": "browser_after", "ms": 3},
                        ],
                    },
                },
            )
    summary = report(tmp_path)
    # The summary keeps the preparation span for analysis, including a true zero.
    assert [(row["app"], row["server_prepare_median_ms"], row["server_prepare_kinds"]) for row in summary["rows"]][
        :2
    ] == [("citry", 0, ["html"]), ("citry", 0, ["html"])]
    assert {row["server_prepare_median_ms"] for row in summary["rows"] if row["app"] == "python_vue"} == {1.25}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        # The page charts the server's work only as the load and action server segments.
        assert not [title for title in page.locator("#charts h3").all_text_contents() if "preparation" in title]
        phase = page.locator(
            "#charts article", has=page.locator("h3", has_text="First-load time to interactive")
        ).locator("svg")
        # Rows without the layout endpoint keep ready-only bars; the row tooltip and the description both say so.
        assert phase.text_content().count("N=1; phases=1 measured/0 unavailable; layout-endpoint-unavailable=1") == 4
        assert phase.locator('rect[aria-label="Main document server: 2.00 ms"]').count() == 2
        browser.close()


def test_report_separates_first_and_second_page_loads_and_keeps_legacy_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    for page_load, elapsed, size, prepare in ((1, 20, 100, 2), (2, 10, 80, 1)):
        common = {
            "app": "citry",
            "count": 14,
            "action": "initial",
            "page_load": page_load,
            "warmup": False,
            "status": "ok",
        }
        append(
            tmp_path / "samples.jsonl",
            {
                **common,
                "elapsed_ms": elapsed,
                "server_prepare_ms": prepare,
                "server_prepare_status": "measured",
                "server_prepare_kind": "html",
                "latency_phase": {
                    "status": "measured",
                    "reason": None,
                    "segments": [{"key": "browser_after", "ms": elapsed}],
                },
            },
        )
        append(
            tmp_path / "sizes.jsonl",
            {
                **common,
                "final_html_bytes": size,
                "request_body_bytes": 0,
                "encoded_response_body_bytes": size * 2,
            },
        )
    # Historical rows predate the page-load dimension and retain their original first-page provenance.
    action = {"app": "citry", "count": 14, "action": "select", "warmup": False, "status": "ok"}
    append(tmp_path / "samples.jsonl", {**action, "elapsed_ms": 5})
    append(
        tmp_path / "sizes.jsonl",
        {**action, "final_html_bytes": 81, "request_body_bytes": 1, "encoded_response_body_bytes": 2},
    )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "id": "second-load",
                "status": "passed",
                "scenario_revision": "canonical-project-v1",
                "inputs": {"inputs": {"profile": {"apps": ["citry"], "counts": [14]}}},
            }
        )
    )

    summary = report(tmp_path)
    initial = [row for row in summary["rows"] if row["action"] == "initial"]
    assert [(row["page_load"], row["median_ms"]) for row in initial] == [(1, 20), (2, 10)]
    assert next(row for row in summary["rows"] if row["action"] == "select")["page_load"] == 1
    assert [(row["page_load"], row["final_html_bytes"]) for row in summary["sizes"] if row["action"] == "initial"] == [
        (1, 100),
        (2, 80),
    ]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        assert page.locator("#charts svg").count() == 8
        assert page.locator("#charts h3").all_text_contents()[:3] == [
            "First-load time to interactive",
            "Second-load time to interactive",
            "Server-action latency",
        ]
        assert "layout-endpoint-unavailable=1" in page.locator("#charts svg").nth(0).text_content()
        assert "20.00 ms" in page.locator("#charts svg").nth(0).text_content()
        assert "10.00 ms" in page.locator("#charts svg").nth(1).text_content()
        assert page.locator("#page-load option").all_text_contents() == ["First load", "Second load"]
        html_size_chart = page.locator(
            "#charts article", has=page.locator("h3", has_text="Initial final HTML size")
        ).locator("svg")
        assert "100 B" in html_size_chart.text_content()
        page.select_option("#page-load", "2")
        assert "80 B" in html_size_chart.text_content()
        browser.close()


def test_report_groups_frameworks_sections_and_shares_select_state(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    # One app from each framework group plus one the report does not know,
    # recorded out of display order to prove the report orders them itself.
    apps = ["python_vue", "zz_custom", "next", "django_components", "fasthtml", "citry_vue", "django_rusty_templates"]
    for app in apps:
        for count in (140, 1400):
            for action in ("initial", "select"):
                ready = count / 10
                append(
                    tmp_path / "samples.jsonl",
                    {
                        "app": app,
                        "count": count,
                        "action": action,
                        "page_load": 1,
                        "status": "ok",
                        "warmup": False,
                        "elapsed_ms": ready,
                        "ready_elapsed_ms": ready,
                        "latency_phase": {"status": "measured", "segments": [{"key": "server", "ms": ready}]},
                    },
                )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "id": "layout",
                "status": "passed",
                "scenario_revision": "canonical-project-v1",
                "inputs": {"inputs": {"profile": {"apps": apps, "counts": [140, 1400]}}},
            }
        )
    )
    report(tmp_path)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((tmp_path / "report.html").as_uri())
        assert page.locator("#charts h2").all_text_contents() == ["Timings", "Sizes"]
        assert page.locator("#charts article").count() == page.locator("#charts h3").count() == 7
        first = page.locator("#charts article").first
        svg = first.locator("svg")
        # The Citry group sits right under the legend and carries no heading,
        # which leaves more room between the legend and the first row.
        assert svg.locator("text.group-heading").all_text_contents() == [
            "Django libraries",
            "Other Python libraries",
            "JavaScript SSR",
            "Server API + CSR",
            "Other",
        ]
        # Headings end where the app names end.
        headings = svg.locator("text.group-heading")
        assert set(headings.evaluate_all("n => n.map(t => t.getAttribute('text-anchor'))")) == {"end"}
        heading_x = headings.evaluate_all("n => n.map(t => t.getAttribute('x'))")
        name_x = svg.locator("text[text-anchor='end']:not(.group-heading)").first.get_attribute("x")
        assert set(heading_x) == {name_x}
        labels = svg.locator("text[text-anchor='end']:not(.group-heading)").all_text_contents()
        assert labels == [
            "Citry (Vue)",
            "Rusty + HTMX + Alpine",
            "django-components",
            "FastHTML",
            "Next.js",
            "Python API + Vue",
            "zz_custom",
        ]
        # Totals are bold; the legend uses three columns (x = 12, 241, 470).
        assert svg.locator("text[font-weight='700']", has_text="14.00 ms").count() == len(apps)
        legend_x = {
            float(x) for x in svg.locator("rect[width='11']").evaluate_all("n => n.map(r => r.getAttribute('x'))")
        }
        assert legend_x == {12, 241, 470}
        # The canonical-output labels carry no scale suffix anywhere.
        assert "(10x)" not in page.locator("select").evaluate_all("s => s.map(e => e.textContent).join()")
        # A chart shows only the selects that change it.
        assert first.locator("select").evaluate_all("s => s.map(e => e.dataset.control)") == ["count"]
        latency = page.locator("#charts article", has=page.locator("h3", has_text="Server-action latency"))
        assert latency.locator("select").evaluate_all("s => s.map(e => e.dataset.control)") == ["count", "action"]
        # Changing one chart's select updates the page select, every chart and every other inline select.
        latency.locator("select[data-control=count]").select_option("1400")
        assert page.locator("#count").input_value() == "1400"
        assert set(page.locator("select[data-control=count]").evaluate_all("s => s.map(e => e.value)")) == {"1400"}
        assert "140.00 ms" in page.locator("#charts article").first.locator("svg").text_content()
        # Focus returns to the redrawn copy of the select that was changed.
        assert page.evaluate(
            "[document.activeElement.dataset.control, document.activeElement.closest('article').dataset.title]"
        ) == ["count", "Server-action latency"]
        # Charts and sections collapse, and stay collapsed after a redraw.
        page.locator("#charts h3 button", has_text="Server-action latency").click()
        assert latency.locator(".chart-body").is_hidden()
        page.select_option("#count", "140")
        assert (
            page.locator("#charts article", has=page.locator("h3", has_text="Server-action latency"))
            .locator(".chart-body")
            .is_hidden()
        )
        page.locator("#charts h2 button", has_text="Sizes").click()
        sizes = page.locator("#charts section.chart-group", has=page.locator("h2", has_text="Sizes"))
        assert sizes.locator(".group-body").is_hidden()
        assert sizes.locator("h2 button").get_attribute("aria-expanded") == "false"
        assert not errors
        browser.close()
