"""Tests for the dev server (live page rendering + 404s), via Starlette's TestClient."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from docs_site.config import DocsConfig
from docs_site.serve import create_app


def _client(tmp_path: Path) -> TestClient:
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("---\ntitle: Home\n---\n\nWelcome.\n", encoding="utf-8")
    (content / "guide").mkdir()
    (content / "guide" / "intro.md").write_text("# Intro\n\nThe intro.\n", encoding="utf-8")
    config = DocsConfig(content_dir=content, site_dir=tmp_path / "site", repo_root=tmp_path)
    return TestClient(create_app(config=config))


def test_serve_renders_index(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Welcome." in response.text


def test_serve_renders_clean_url_page(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/guide/intro/")
    assert response.status_code == 200
    assert "The intro." in response.text


def test_serve_404_for_unknown_page(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/nope/")
    assert response.status_code == 404
