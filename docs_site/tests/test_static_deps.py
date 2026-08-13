"""Tests for the static client-runtime export."""

from __future__ import annotations

import json
import re
from pathlib import Path

from citry import citry as default_citry
from docs_site._internal.static_deps import CITRY_MOUNT_PREFIX, export_runtime

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
