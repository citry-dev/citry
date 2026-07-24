"""Tests for the Pagefind search-index build."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.pagefind import run_pagefind


def test_run_pagefind_builds_index(tmp_path: Path) -> None:
    # A minimal site with one indexable article.
    (tmp_path / "index.html").write_text(
        "<!DOCTYPE html><html><body><article data-pagefind-body>"
        "<h1>Hello</h1><p>some searchable content here</p></article></body></html>",
        encoding="utf-8",
    )

    outcome = run_pagefind(tmp_path)

    if not outcome.ok and "not found" in outcome.message:
        pytest.skip("pagefind binary not installed")
    assert outcome.ok, outcome.message
    assert (tmp_path / "pagefind" / "pagefind.js").is_file()


def test_run_pagefind_reports_missing_dir() -> None:
    outcome = run_pagefind(Path("/nonexistent/does/not/exist"))
    assert not outcome.ok
    assert "not found" in outcome.message
