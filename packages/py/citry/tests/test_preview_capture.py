"""Capture boundaries without requiring a browser installation."""

import copy
import importlib
import json
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

capture_module = importlib.import_module("citry.ext.preview.capture")


@pytest.fixture
def catalog():
    return {
        "service": "citry-preview",
        "version": 1,
        "components": [
            {
                "id": "Button_a1",
                "name": "Button",
                "group": None,
                "variants": [
                    {
                        "slug": slug,
                        "label": slug.title(),
                        "description": None,
                        "viewport": {"width": 800, "height": 600, "device_scale_factor": 2},
                        "url": f"/citry/ext/preview/render/Button_a1?variant={slug}",
                    }
                    for slug in ["default", "small"]
                ],
            }
        ],
    }


@pytest.fixture
def browser(monkeypatch, catalog):
    browser = MagicMock()
    page = browser.new_context.return_value.new_page.return_value
    page.goto.return_value = SimpleNamespace(ok=True, headers={"content-type": "text/html; charset=utf-8"})
    page.screenshot.return_value = b"\x89PNG\r\n\x1a\n"
    playwright = MagicMock()
    playwright.__enter__.return_value.chromium.launch.return_value = browser
    monkeypatch.setattr(capture_module, "_playwright", lambda: playwright)
    monkeypatch.setattr(capture_module, "fetch_catalog", lambda *_args: catalog)
    return browser


def test_capture_atomic_outputs_and_fresh_contexts(catalog, browser, tmp_path):
    result = capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    assert len(result["captures"]) == 2
    assert all(item["success"] for item in result["captures"])
    assert json.loads((tmp_path / "manifest.json").read_text()) == result
    assert (tmp_path / "Button_a1/default.png").read_bytes().startswith(b"\x89PNG")
    assert browser.new_context.call_count == 2
    assert browser.new_context.return_value.close.call_count == 2
    browser.close.assert_called_once()
    assert not list(tmp_path.rglob(".preview-*"))


def test_preflight_precedes_browser_and_preserves_existing(catalog, browser, tmp_path):
    (tmp_path / "manifest.json").write_text("untouched")
    with pytest.raises(FileExistsError):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    browser.new_context.assert_not_called()
    assert (tmp_path / "manifest.json").read_text() == "untouched"


def test_partial_failure_continues_and_closes(catalog, browser, tmp_path):
    page = browser.new_context.return_value.new_page.return_value
    page.screenshot.side_effect = [TimeoutError("Screenshot timed out"), b"PNG"]
    with pytest.raises(capture_module.CaptureError) as caught:
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    assert [item["success"] for item in caught.value.manifest["captures"]] == [False, True]
    assert not (tmp_path / "Button_a1/default.png").exists()
    assert (tmp_path / "Button_a1/small.png").exists()
    assert browser.new_context.return_value.close.call_count == 2
    browser.close.assert_called_once()


def test_interrupt_preserves_completed_manifest(catalog, browser, tmp_path):
    browser.new_context.return_value.new_page.return_value.screenshot.side_effect = [b"PNG", KeyboardInterrupt]
    with pytest.raises(KeyboardInterrupt):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    assert len(json.loads((tmp_path / "manifest.json").read_text())["captures"]) == 1
    assert browser.new_context.return_value.close.call_count == 2
    browser.close.assert_called_once()


def test_readiness_and_http_failure(catalog, browser, tmp_path):
    page = browser.new_context.return_value.new_page.return_value
    page.goto.return_value.ok = False
    with pytest.raises(capture_module.CaptureError):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path, ready_selector="#ready")
    page.screenshot.assert_not_called()


def test_ready_selector_and_assets_are_awaited(catalog, browser, tmp_path):
    capture_module.capture(catalog, "http://localhost/citry", tmp_path, ready_selector="#ready")
    page = browser.new_context.return_value.new_page.return_value
    assert page.locator.call_args.args == ("#ready",)
    assert page.locator.return_value.wait_for.call_args.kwargs["state"] == "visible"
    assert "document.fonts.ready" in page.evaluate.call_args.args[0]
    assert page.screenshot.call_args.kwargs["animations"] == "disabled"


def test_catalog_change_fails_before_capture(catalog, browser, tmp_path, monkeypatch):
    changed = copy.deepcopy(catalog)
    changed["components"][0]["variants"][0]["label"] = "Changed"
    monkeypatch.setattr(capture_module, "fetch_catalog", lambda *_args: changed)
    with pytest.raises(capture_module.CaptureError):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    browser.new_context.assert_not_called()


@pytest.mark.parametrize("value", ["../escape", "a/b", "a\\b", "CON", "x."])
def test_output_segments_reject_traversal(catalog, tmp_path, value):
    catalog["components"][0]["id"] = value
    with pytest.raises(ValueError, match="Unsafe"):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)


def test_symlink_cannot_escape(catalog, tmp_path):
    root = tmp_path / "output"
    root.mkdir()
    (root / "Button_a1").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes"):
        capture_module.capture(catalog, "http://localhost/citry", root)


@pytest.mark.parametrize("url", ["file:///tmp", "https://example.com/?x=1", "https://a/#x", "https://u:p@a"])
def test_base_url_validation(url):
    with pytest.raises(ValueError, match="HTTP"):
        capture_module.validate_base_url(url)


def test_remote_superset_and_origin(catalog):
    local = copy.deepcopy(catalog)
    local["components"][0]["variants"].pop()
    local["components"][0]["variants"][0].pop("url")
    selected = capture_module.validate_remote_catalog(local, catalog, "http://localhost/citry")
    assert len(selected["components"][0]["variants"]) == 1
    catalog["components"][0]["variants"][0]["url"] = "https://elsewhere/render"
    with pytest.raises(ValueError, match="origin"):
        capture_module.validate_remote_catalog(local, catalog, "http://localhost/citry")


def test_overwrite_preserves_unrelated_files(catalog, browser, tmp_path):
    capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    (tmp_path / "unrelated.png").write_bytes(b"keep")
    capture_module.capture(catalog, "http://localhost/citry", tmp_path, overwrite=True)
    assert (tmp_path / "unrelated.png").read_bytes() == b"keep"


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout(catalog, tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout"):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path, timeout=timeout)


def test_browser_error_fails_capture(catalog, browser, tmp_path):
    page = browser.new_context.return_value.new_page.return_value

    def navigation(*_args, **_kwargs):
        handlers = {call.args[0]: call.args[1] for call in page.on.call_args_list}
        handlers["pageerror"](RuntimeError("Component initialization failed"))
        return SimpleNamespace(ok=True, headers={"content-type": "text/html"})

    page.goto.side_effect = navigation
    with pytest.raises(capture_module.CaptureError) as caught:
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    assert "initialization failed" in caught.value.manifest["captures"][0]["diagnostic"]
    assert not (tmp_path / "Button_a1/default.png").exists()


def test_browser_launch_failure_does_not_claim_completed_captures(catalog, tmp_path, monkeypatch):
    playwright = MagicMock()
    playwright.__enter__.return_value.chromium.launch.side_effect = RuntimeError("No executable")
    monkeypatch.setattr(capture_module, "_playwright", lambda: playwright)
    with pytest.raises(capture_module.CaptureError, match="install chromium"):
        capture_module.capture(catalog, "http://localhost/citry", tmp_path)
    playwright.__exit__.assert_called_once()
    assert not (tmp_path / "manifest.json").exists()


def test_catalog_requires_service_marker(catalog):
    catalog["service"] = "application"
    with pytest.raises(ValueError, match="command service"):
        capture_module.validate_remote_catalog(catalog, catalog, "http://localhost/citry")


@pytest.mark.parametrize("resource_type", ["fetch", "xhr", "image", "stylesheet", "font", "script", "document"])
def test_failed_requests_only_fail_required_resources(catalog, browser, tmp_path, resource_type):
    page = browser.new_context.return_value.new_page.return_value

    def navigation(*_args, **_kwargs):
        handlers = {call.args[0]: call.args[1] for call in page.on.call_args_list}
        handlers["requestfailed"](SimpleNamespace(resource_type=resource_type, url="http://localhost/resource"))
        return SimpleNamespace(ok=True, headers={"content-type": "text/html"})

    page.goto.side_effect = navigation
    if resource_type in {"fetch", "xhr"}:
        result = capture_module.capture(catalog, "http://localhost/citry", tmp_path)
        assert all(item["success"] for item in result["captures"])
    else:
        with pytest.raises(capture_module.CaptureError, match="captures failed"):
            capture_module.capture(catalog, "http://localhost/citry", tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("width", 8193),
        ("height", 8193),
        ("device_scale_factor", 4.1),
        ("width", True),
        ("height", False),
        ("device_scale_factor", True),
    ],
)
def test_remote_viewports_reuse_local_bounds(catalog, field, value):
    remote = copy.deepcopy(catalog)
    remote["components"][0]["variants"][0]["viewport"][field] = value
    with pytest.raises(ValueError, match="Viewport"):
        capture_module.validate_remote_catalog(catalog, remote, "http://localhost/citry")


def test_preflight_without_urls_checks_browser_without_launching(catalog, tmp_path, monkeypatch):
    for variant in catalog["components"][0]["variants"]:
        variant.pop("url")
    executable = tmp_path / "chromium"
    executable.write_bytes(b"browser")
    playwright = MagicMock()
    chromium = playwright.__enter__.return_value.chromium
    chromium.executable_path = str(executable)
    monkeypatch.setattr(capture_module, "_playwright", lambda: playwright)
    capture_module.preflight(catalog, tmp_path / "out")
    chromium.launch.assert_not_called()
    playwright.__enter__.return_value.request.new_context.return_value.dispose.assert_called_once()
    playwright.__exit__.assert_called_once()
    assert not (tmp_path / "out").exists()


def test_preflight_missing_browser(catalog, tmp_path, monkeypatch):
    playwright = MagicMock()
    playwright.__enter__.return_value.chromium.executable_path = str(tmp_path / "missing")
    monkeypatch.setattr(capture_module, "_playwright", lambda: playwright)
    with pytest.raises(capture_module.CaptureError, match="install chromium"):
        capture_module.preflight(catalog, tmp_path)
    playwright.__exit__.assert_called_once()


def test_preflight_collision_precedes_optional_browser_dependency(catalog, tmp_path, monkeypatch):
    dependency = MagicMock(side_effect=ImportError("Not installed"))
    monkeypatch.setattr(capture_module, "_playwright", dependency)
    (tmp_path / "manifest.json").write_text("existing")
    with pytest.raises(FileExistsError):
        capture_module.preflight(catalog, tmp_path)
    dependency.assert_not_called()


def test_empty_preflight_needs_no_browser(catalog, tmp_path, monkeypatch):
    dependency = MagicMock(side_effect=ImportError("Not installed"))
    monkeypatch.setattr(capture_module, "_playwright", dependency)
    catalog["components"] = []
    capture_module.preflight(catalog, tmp_path)
    dependency.assert_not_called()


def test_preflight_missing_playwright_is_actionable(catalog, tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    with pytest.raises(capture_module.CaptureError, match=r"Install citry\[ext-preview\]"):
        capture_module.preflight(catalog, tmp_path)


def test_real_preflight_driver_shutdown_has_no_pending_tasks(tmp_path):
    pytest.importorskip("playwright.sync_api")
    # A subprocess exposes shutdown warnings that fake drivers cannot reproduce.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from pathlib import Path
from citry.ext.preview.capture import CaptureError, preflight
catalog = {"service": "citry-preview", "version": 1, "components": [{
    "id": "Button", "variants": [{"slug": "default", "label": "Default",
    "viewport": {"width": 800, "height": 600, "device_scale_factor": 1}}]}]}
try:
    preflight(catalog, Path(sys.argv[1]))
except CaptureError:
    pass  # Browser binaries are optional; driver shutdown must still be clean.
""",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
