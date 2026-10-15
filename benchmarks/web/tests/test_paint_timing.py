"""FCP and LCP come from the browser, and a missing value keeps its reason."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest
from citry_bench.browser import SCRIPT, paint_fields, read_paint_timing
from citry_bench.config import CACHE
from citry_bench.results import append, report
from playwright.sync_api import sync_playwright

MEASURED = {
    "time_origin": "navigation-start",
    "supported": {"paint": True, "largest-contentful-paint": True},
    "errors": [],
    "fcp_ms": 40.5,
    "lcp": {"start_ms": 90.25, "render_ms": 90.25, "load_ms": 0, "size": 5000, "element": {"tag": "h1"}},
    "lcp_candidates": 2,
    "first_input": None,
    "finalized_ms": 300.0,
    "request_start_ms": 2.0,
}

TEXT = "Canonical project board output. " * 40
# A server-rendered page paints its content from the document, while its
# framework reports readiness later.
STATIC = f"""<!doctype html><html><body><h1 style="font-size:40px">Project board</h1><p>{TEXT}</p>
<script>setTimeout(() => {{ window.__ready = performance.now(); }}, 300);</script></body></html>"""
# A browser-rendered page has no content until its script builds it.
RENDER = f"""document.getElementById('app').innerHTML = '<h1 style="font-size:40px">Project board</h1><p>{TEXT}</p>';
window.__ready = performance.now();"""
EMPTY_SHELL = f"""<!doctype html><html><body><div id="app"></div>
<script>setTimeout(() => {{ {RENDER} }}, 300);</script></body></html>"""
LOADING_SHELL = f"""<!doctype html><html><body><header>Loading</header><div id="app"></div>
<script>setTimeout(() => {{ {RENDER} }}, 300);</script></body></html>"""
PAGES = {"/static": STATIC, "/empty-shell": EMPTY_SHELL, "/loading-shell": LOADING_SHELL}


def test_measured_paint_times_keep_the_navigation_start_zero():
    fields = paint_fields(MEASURED)
    assert (fields["fcp_ms"], fields["fcp_status"], fields["fcp_reason"]) == (40.5, "measured", None)
    assert (fields["lcp_ms"], fields["lcp_status"], fields["lcp_reason"]) == (90.25, "measured", None)
    assert fields["paint_timing"]["time_origin"] == "navigation-start"
    assert fields["paint_timing"]["request_start_ms"] == 2.0
    assert fields["paint_timing"]["lcp_element"] == {"tag": "h1"}


@pytest.mark.parametrize(
    ("change", "fcp_reason", "lcp_reason"),
    [
        ({"fcp_ms": None, "lcp": None}, "no first-contentful-paint", "no largest-contentful-paint candidate"),
        ({"supported": {"paint": True}}, None, "browser does not support largest-contentful-paint"),
        ({"errors": ["paint: TypeError"]}, "paint observer failed", None),
        ({"finalized_ms": None}, "not finalized", "not finalized"),
        ({"fcp_ms": -1, "lcp": {"start_ms": float("nan")}}, "not a finite nonnegative", "not a finite nonnegative"),
        ({"fcp_ms": 301}, "later than finalization", None),
        ({"first_input": {"type": "pointerdown", "at": 50}}, None, "pointerdown before finalization stopped LCP"),
    ],
)
def test_missing_or_untrustworthy_paint_values_stay_unavailable_with_a_reason(change, fcp_reason, lcp_reason):
    fields = paint_fields({**MEASURED, **change})
    for name, reason in (("fcp", fcp_reason), ("lcp", lcp_reason)):
        if reason is None:
            assert fields[f"{name}_status"] == "measured"
        else:
            assert fields[f"{name}_ms"] is None
            assert fields[f"{name}_status"] == "unavailable"
            assert reason in fields[f"{name}_reason"]


@pytest.mark.parametrize("raw", [None, {}, {**MEASURED, "time_origin": "request-start"}])
def test_malformed_record_or_failed_read_is_unavailable(raw):
    assert paint_fields(raw)["fcp_reason"] == "paint timing record is missing or malformed"
    failed = paint_fields(MEASURED, read_error="Target closed")
    assert failed["lcp_reason"] == "paint timing read failed: Target closed"
    assert failed["paint_timing"] is None


def _initial(page_load, **fields):
    return {
        "app": "citry",
        "count": 14,
        "action": "initial",
        "page_load": page_load,
        "warmup": False,
        "status": "ok",
        "elapsed_ms": 50,
        **fields,
    }


def test_summary_medians_count_unavailable_and_unrecorded_paint_separately(tmp_path):
    for fcp, lcp in ((10, 30), (20, 50)):
        append(
            tmp_path / "samples.jsonl",
            _initial(1, **paint_fields({**MEASURED, "fcp_ms": fcp, "lcp": {"start_ms": lcp}})),
        )
    append(tmp_path / "samples.jsonl", _initial(1, **paint_fields({**MEASURED, "lcp": None})))
    # A row from a run before paint timing has no paint fields at all.
    append(tmp_path / "samples.jsonl", _initial(1))
    # Failed loads and actions never contribute paint values.
    append(tmp_path / "samples.jsonl", {**_initial(1, fcp_ms=1, fcp_status="measured"), "status": "error"})
    append(tmp_path / "samples.jsonl", {**_initial(1), "action": "select"})

    rows = {row["action"]: row for row in report(tmp_path)["rows"]}
    initial = rows["initial"]
    assert (initial["fcp_median_ms"], initial["fcp_observations"], initial["fcp_not_recorded"]) == (20, 3, 1)
    assert (initial["lcp_median_ms"], initial["lcp_observations"], initial["lcp_not_recorded"]) == (40, 2, 1)
    assert initial["lcp_unavailable_reasons"] == {"no largest-contentful-paint candidate before finalization": 1}
    assert "fcp_median_ms" not in rows["select"]

    payload = (tmp_path / "report.html").read_text().split('type="application/json">', 1)[1].split("</script>")[0]
    samples = json.loads(payload)["samples"]
    assert [row["lcp_ms"] for row in samples if row["action"] == "initial"] == [30, 50, None, None, None]
    assert samples[2]["lcp_reason"] == "no largest-contentful-paint candidate before finalization"


def test_report_marks_paint_on_initial_stacks_and_keeps_older_runs_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
    phase = {"status": "measured", "segments": [{"key": "browser_after", "ms": 50}]}
    append(tmp_path / "samples.jsonl", _initial(1, latency_phase=phase, **paint_fields(MEASURED)))
    append(tmp_path / "samples.jsonl", _initial(2, latency_phase=phase, **paint_fields({**MEASURED, "lcp": None})))
    # A second app retained from a run before paint timing shares the chart.
    append(tmp_path / "samples.jsonl", {**_initial(1, latency_phase=phase), "app": "next"})
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "id": "paint",
                "status": "passed",
                "scenario_revision": "canonical-project-v1",
                "inputs": {"inputs": {"profile": {"apps": ["citry", "next"], "counts": [14]}}},
            }
        )
    )
    report(tmp_path)
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    append(legacy / "samples.jsonl", _initial(1, latency_phase=phase))
    # A run before paint timing keeps its original summary keys.
    assert "fcp_median_ms" not in report(legacy)["rows"][0]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((tmp_path / "report.html").as_uri())
        first, second = page.locator("#charts article").nth(0), page.locator("#charts article").nth(1)
        assert first.locator('path[aria-label="Citry: FCP median 40.50 ms (N=1)"]').count() == 1
        assert first.locator('path[aria-label="Citry: LCP median 90.25 ms (N=1)"]').count() == 1
        # LCP (90 ms) is later than readiness (50 ms); the axis stretches so
        # its marker stays inside the 360-unit plot that starts at x=180.
        lcp_path = first.locator('path[aria-label^="Citry: LCP"]').get_attribute("d")
        assert float(lcp_path[1:].split(" ")[0]) + 5.5 <= 180 + 360
        assert "LCP median 90.25 ms" in first.locator("desc").text_content()
        # The markers carry the paint times; the chart has no separate table.
        assert first.locator("table").count() == 0
        assert "Next.js: representative segments" in first.locator("desc").text_content()
        assert "FCP not recorded; LCP not recorded" in first.locator("desc").text_content()
        assert first.locator("path[aria-label^='Next.js']").count() == 0
        assert second.locator("path[aria-label*='LCP median']").count() == 0
        assert (
            "LCP unavailable: no largest-contentful-paint candidate before finalization"
            in second.locator("desc").text_content()
        )
        assert "Triangles mark median" in first.locator(".description").text_content()
        assert "largest-contentful-paint" in page.locator("details").text_content()

        page.goto((legacy / "report.html").as_uri())
        assert page.locator("#charts table").count() == 0
        assert "FCP" not in page.locator("#charts article").nth(0).text_content()
        browser.close()


@pytest.fixture(scope="module")
def server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = PAGES[self.path].encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{instance.server_port}"
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join()


@pytest.fixture(scope="module")
def browser():
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
        with sync_playwright() as playwright:
            instance = playwright.chromium.launch()
            try:
                yield instance
            finally:
                instance.close()


def _load(browser, url, *, click_before_read=False):
    # The same viewport and init script as the measured sessions.
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    context.add_init_script(SCRIPT)
    try:
        page = context.new_page()
        page.goto(url)
        page.wait_for_function("() => window.__ready !== undefined")
        if click_before_read:
            page.mouse.click(5, 5)
        ready = page.evaluate("window.__ready")
        fields = read_paint_timing(page)
        # After finalization, larger content no longer changes the record.
        page.evaluate("""() => { const big = document.createElement('div');
          big.style.cssText = 'font-size:120px'; big.textContent = 'Much larger later content';
          document.body.prepend(big); }""")
        page.wait_for_timeout(100)
        again = read_paint_timing(page)
        return ready, fields, again
    finally:
        context.close()


def test_server_html_paints_before_its_later_readiness(browser, server):
    ready, fields, again = _load(browser, server + "/static")
    assert fields["fcp_status"] == fields["lcp_status"] == "measured"
    assert 0 < fields["fcp_ms"] <= fields["lcp_ms"] < ready
    assert fields["paint_timing"]["request_start_ms"] < fields["fcp_ms"]
    assert again == fields


def test_browser_rendered_content_sets_lcp_after_the_render(browser, server):
    ready, fields, _ = _load(browser, server + "/empty-shell")
    # Nothing contentful exists before the script, so both paints follow it
    # (allowing one 4 ms step of Chromium's paint-time rounding).
    assert ready - 4 <= fields["fcp_ms"] <= fields["lcp_ms"]

    ready, fields, _ = _load(browser, server + "/loading-shell")
    # A shell with text paints first; the rendered board becomes the LCP.
    assert fields["fcp_ms"] < ready - 4 <= fields["lcp_ms"]
    assert fields["paint_timing"]["lcp_candidates"] >= 2


def test_input_before_the_read_marks_lcp_unavailable(browser, server):
    _, fields, _ = _load(browser, server + "/static", click_before_read=True)
    assert fields["fcp_status"] == "measured"
    assert fields["lcp_status"] == "unavailable"
    assert "before finalization stopped LCP" in fields["lcp_reason"]


def test_instrumentation_adds_no_event_listeners(browser, server):
    # The memory report shows the page's listener count, so detecting early
    # input must not add DOM listeners of its own.
    counts = []
    # The same script without its paint section (paintTimings is never called).
    before, rest = SCRIPT.split("  // Paint timing.")
    without_paint = before + "  window.__citryBench = {" + rest.split("  window.__citryBench = {")[1]
    for script in (SCRIPT, without_paint):
        context = browser.new_context()
        context.add_init_script(script)
        page = context.new_page()
        page.goto(server + "/static")
        session = context.new_cdp_session(page)
        counts.append(session.send("Memory.getDOMCounters")["jsEventListeners"])
        context.close()
    assert counts[0] == counts[1]
