"""Tests for the dev server (live page rendering + 404s), via Starlette's TestClient."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from starlette.testclient import TestClient

from docs_site._internal.config import DocsConfig
from docs_site._internal.serve import create_app


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


def test_serve_pre_renders_a_fragment_variant_with_working_deps(tmp_path: Path) -> None:
    # The fragments demo page fetches /examples/<name>/<variant>/. The dev server
    # must serve that pre-rendered fragment (parity with the static build), and
    # the fragment's JS/CSS must resolve through the /citry mount.
    client = _client(tmp_path)
    frag = client.get("/examples/fragments/widget/")
    assert frag.status_code == 200
    assert "frag-widget" in frag.text  # the pre-rendered fragment HTML

    # The fragment manifest lists its JS/CSS as base64 dep descriptors that point
    # at /citry/cache/<class_id>.<ext>; the /citry mount must serve each one.
    manifest = json.loads(re.search(r"data-citry>(\{.*\})</script>", frag.text).group(1))
    dep_urls = [
        json.loads(base64.b64decode(enc))["attrs"].get("src") or json.loads(base64.b64decode(enc))["attrs"]["href"]
        for kind in ("js", "css")
        for enc in manifest["fetch"][kind]
    ]
    assert dep_urls  # the widget ships both JS and CSS
    for url in dep_urls:
        assert client.get(url).status_code == 200


def test_serve_404_for_unknown_fragment_variant(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.get("/examples/fragments/nope/").status_code == 404  # bad variant
    assert client.get("/examples/nope/widget/").status_code == 404  # bad example
