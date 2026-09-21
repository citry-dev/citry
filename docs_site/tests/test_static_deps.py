"""Tests for the static client-runtime export."""

from __future__ import annotations

import json
import re
from pathlib import Path

from citry import Component
from citry import citry as default_citry
from docs_site._internal.static_deps import (
    CITRY_MOUNT_PREFIX,
    export_prepared_page_assets,
    export_runtime,
    validate_prepared_assets,
)

DOCS_SITE_DIR = Path(__file__).resolve().parents[1]


def test_playground_transport_uses_protocol_v1_everywhere() -> None:
    bridge = (DOCS_SITE_DIR / "_internal/frontend/src/preview_bridge.js").read_text(encoding="utf-8")
    preview = (DOCS_SITE_DIR / "static/playground/preview.html").read_text(encoding="utf-8")
    worker = (DOCS_SITE_DIR / "static/playground/worker.js").read_text(encoding="utf-8")
    runtime = json.loads((DOCS_SITE_DIR / "static/playground/runtime.json").read_text(encoding="utf-8"))

    bridge_version = re.search(r"const PROTOCOL_VERSION = (\d+);", bridge)
    preview_version = re.search(r"const VERSION = (\d+);", preview)
    worker_version = re.search(r"runtime\.protocol_version !== (\d+)", worker)

    assert bridge_version is not None
    assert preview_version is not None
    assert worker_version is not None
    assert {
        bridge_version.group(1),
        preview_version.group(1),
        worker_version.group(1),
        str(runtime["protocol_version"]),
    } == {"1"}


def test_playground_analysis_transport_uses_schema_v1() -> None:
    browser_ide = (DOCS_SITE_DIR / "_internal/frontend/src/browser_ide.js").read_text(encoding="utf-8")
    worker = (DOCS_SITE_DIR / "_internal/frontend/src/analysis_worker.js").read_text(encoding="utf-8")

    browser_version = re.search(r"const SCHEMA_VERSION = (\d+);", browser_ide)
    worker_version = re.search(r"const SCHEMA_VERSION = (\d+);", worker)

    assert browser_version is not None
    assert worker_version is not None
    assert {browser_version.group(1), worker_version.group(1)} == {"1"}


def test_export_runtime_writes_under_mount_prefix(tmp_path: Path) -> None:
    default_citry.set_mounted_prefix(CITRY_MOUNT_PREFIX)

    dest = export_runtime(tmp_path, default_citry)

    # Written where the pages reference it: <prefix>/citry.js.
    assert dest == tmp_path / "citry" / "citry.js"
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8").strip()  # non-empty runtime source

    events_runtime = tmp_path / "citry" / "ext" / "events" / "runtime.js"
    assert events_runtime.is_file()
    assert events_runtime.read_text(encoding="utf-8").strip()


def test_export_prepared_page_assets_uses_only_the_generated_manifest(tmp_path: Path, monkeypatch: object) -> None:
    from citry._vue import events

    js_digest = "a" * 64
    css_digest = "b" * 64
    fake_digest = "c" * 64
    payload = {
        "manifest": {
            "protocol": "citry-vue-prepared/1",
            "definitions": [],
            "scripts": [
                {
                    "source": {
                        "kind": "owned",
                        "sha256": js_digest,
                        "url": f"/citry/ext/events/definitions/{js_digest}.js",
                    }
                }
            ],
            "styles": [
                {
                    "source": {
                        "kind": "owned",
                        "sha256": css_digest,
                        "url": f"/citry/ext/events/assets/{css_digest}.css",
                    }
                }
            ],
        }
    }
    html = (
        f"<p>/citry/ext/events/definitions/{fake_digest}.js</p>"
        f"<script>(function() {{\nCitryStable.startPrepared({json.dumps(payload)})"
        ".catch(error => queueMicrotask(() => { throw error; }));\n})();</script>"
    )
    monkeypatch.setattr(events, "definition_bundle", lambda _citry, digest: b"js" if digest == js_digest else None)
    monkeypatch.setattr(events, "style_asset", lambda _citry, digest: b"css" if digest == css_digest else None)

    written = export_prepared_page_assets(html, tmp_path, default_citry)

    assert {path.read_bytes() for path in written} == {b"js", b"css"}
    assert not any(fake_digest in path.name for path in written)
    (tmp_path / "index.html").write_text(html, encoding="utf-8")
    validate_prepared_assets(tmp_path, default_citry)


def test_landing_prepared_assets_export_at_their_manifest_urls(tmp_path: Path) -> None:
    from docs_site._internal.pipeline import render_page

    default_citry.set_mounted_prefix(CITRY_MOUNT_PREFIX)
    source = (DOCS_SITE_DIR / "content/index.md").read_text(encoding="utf-8")
    html = render_page(source, current_path="").html

    written = export_prepared_page_assets(html, tmp_path, default_citry)

    assert any(path.suffix == ".js" for path in written)
    assert any(path.suffix == ".css" for path in written)
    assert all(path.is_relative_to(tmp_path / "citry/ext/events") for path in written)


def test_prepared_fragment_exports_its_manifest_assets(tmp_path: Path) -> None:
    class FragmentAsset(Component):
        template = "<button>Fragment</button>"
        js = "export default {}"
        css = "button { color: red; }"

    default_citry.set_mounted_prefix(CITRY_MOUNT_PREFIX)
    html = FragmentAsset().render().serialize(deps_strategy="fragment")

    written = export_prepared_page_assets(html, tmp_path, default_citry)

    assert any(path.suffix == ".js" for path in written)
    assert any(path.suffix == ".css" for path in written)
