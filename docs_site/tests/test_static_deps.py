"""Tests for the static client-runtime export."""

from __future__ import annotations

from pathlib import Path

from citry import citry as default_citry
from docs_site._internal.static_deps import CITRY_MOUNT_PREFIX, export_runtime


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
