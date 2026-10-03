"""Preview command pages render real assets, isolated galleries, and PNG captures."""

import importlib
import json
import subprocess
import sys

import pytest

pytest.importorskip("pytest_playwright")
pytest.importorskip("uvicorn")

from citry.ext.preview.host import PreviewServer
from citry.ext.preview.rendering import PreviewRenderer
from citry.ext.preview.routes import preview_routes

pytestmark = pytest.mark.e2e

_FIXTURE = '''
from citry import Citry, Component
from citry.ext.preview import Layout, PreviewExtension, Viewport, variant

app = Citry(extensions=[PreviewExtension])

class Shell(Component):
    citry = app
    template = """
        <!doctype html>
        <html><head></head><body><c-slot name="content" /></body></html>
    """

class Counter(Component):
    citry = app

    class Kwargs:
        label: str = "First"

    class Preview:
        def variants(self):
            return [
                variant(slug="first", label="First", viewport=Viewport(420, 300)),
                variant(slug="second", label="Second", params={"label": "Second"}, viewport=Viewport(640, 320)),
            ]
        page_layout = Layout(component=Shell)

    template = """
        <div>
            <button class="counter" @click="count++">{{ label }}</button>
            <output v-text="count"></output>
            <span class="overlay">Overlay</span>
        </div>
    """
    js = """
        $component({
            data() { return { count: 0 }; },
            onServerRender({ component }) { component.$el.setAttribute('data-ready', 'true'); },
        });
    """
    css = """
        .counter { color: rgb(12, 34, 56); }
    """
'''


def test_gallery_and_capture_use_real_command_pages(page, browser_name, tmp_path, monkeypatch):
    if browser_name != "chromium":
        pytest.skip("The initial PNG command supports Chromium.")
    (tmp_path / "preview_browser_app.py").write_text(_FIXTURE)
    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("preview_browser_app")
    try:
        renderer = PreviewRenderer(module.app.extensions.get_extension("preview"))
        with PreviewServer(module.app, preview_routes(renderer)) as server:
            page.goto(server.base_url + "/ext/preview/gallery")
            page.locator("iframe").nth(1).wait_for()
            first = page.frame_locator("iframe").nth(0)
            second = page.frame_locator("iframe").nth(1)
            first.locator('[data-ready="true"]').wait_for()
            second.locator('[data-ready="true"]').wait_for()
            assert first.locator(".counter").evaluate("el => getComputedStyle(el).color") == "rgb(12, 34, 56)"
            assert first.locator("body").evaluate("() => innerWidth") == 420
            assert second.locator("body").evaluate("() => innerWidth") == 640
            first.locator(".counter").click()
            first.locator(".counter").focus()
            assert first.locator("output").inner_text() == "1"
            assert second.locator("output").inner_text() == "0"
            assert first.locator(".counter").evaluate("el => document.activeElement === el")
            # Native template compilation currently rejects the Teleport helper;
            # direct Vue.Teleport coverage remains in the i18n plugin browser
            # suite. Keep this assertion focused on preview iframe isolation.
            assert first.locator(".overlay").count() == 1
            assert second.locator(".overlay").count() == 1
            assert page.locator(".overlay").count() == 0

            # A separate CLI process owns its Playwright loop while pytest owns this page's loop.
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "citry",
                    "--app",
                    "preview_browser_app:app",
                    "ext",
                    "run",
                    "preview",
                    "render",
                    "--base-url",
                    server.base_url,
                    "--ready-selector",
                    '[data-ready="true"]',
                    "--outdir",
                    "captures",
                ],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            manifest = json.loads((tmp_path / "captures/manifest.json").read_text())
            assert len(manifest["captures"]) == 2
            for entry in manifest["captures"]:
                assert entry["success"]
                assert (tmp_path / "captures" / entry["output"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "citry",
                "--app",
                "preview_browser_app:app",
                "ext",
                "run",
                "preview",
                "render",
                "--variant",
                "first",
                "--ready-selector",
                '[data-ready="true"]',
                "--outdir",
                "owned",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(json.loads((tmp_path / "owned/manifest.json").read_text())["captures"]) == 1
    finally:
        sys.modules.pop("preview_browser_app", None)
