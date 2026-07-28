"""Tests for the dev server (live page rendering + 404s), via Starlette's TestClient."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from starlette.testclient import TestClient

from docs_site._internal.config import DocsConfig
from docs_site._internal.serve import create_app


def _client(tmp_path: Path) -> TestClient:
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("---\ntitle: Home\n---\n\nWelcome.\n", encoding="utf-8")
    (content / "guide").mkdir()
    (content / "guide" / "intro.md").write_text("# Intro\n\nThe intro.\n", encoding="utf-8")
    (content / "examples").mkdir()
    (content / "examples" / "card.md").write_text(
        "# Card recipe\n\nRecipe marker.\n",
        encoding="utf-8",
    )
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


def test_release_index_404s_without_a_changelog(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/releases/")
    assert response.status_code == 404


def test_recipe_and_standalone_demo_use_distinct_routes(tmp_path: Path) -> None:
    client = _client(tmp_path)

    recipe = client.get("/examples/card/")
    demo = client.get("/examples/card/demo/")

    assert recipe.status_code == 200
    assert "Recipe marker." in recipe.text
    assert "citry docs builder" in recipe.text
    assert demo.status_code == 200
    assert 'class="demo-card"' in demo.text
    assert "Recipe marker." not in demo.text


def test_serve_pre_renders_a_fragment_variant_with_working_deps(tmp_path: Path) -> None:
    # The dev server must serve the demo's pre-rendered fragment (parity with
    # the static build), and its JS/CSS must resolve through the /citry mount.
    client = _client(tmp_path)
    frag = client.get("/examples/fragments/demo/widget/")
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
    assert client.get("/examples/fragments/demo/nope/").status_code == 404
    assert client.get("/examples/nope/demo/widget/").status_code == 404


def test_serve_blog_uses_stable_routes_and_previews_atom_feed(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Blog\n    source: blog\n    scope: site\n    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    blog = content / "blog"
    blog.mkdir()
    (blog / "index.md").write_text(
        "---\ntitle: Blog\ndescription: News.\n---\n\n<c-blog-list />\n",
        encoding="utf-8",
    )
    (blog / "2026-07-27-first-post.md").write_text(
        "---\n"
        "title: First post\n"
        "description: A dated post.\n"
        "date: 2026-07-27T09:00:00+02:00\n"
        "author: Citry maintainers\n"
        "tags: news\n"
        "---\n\n"
        "Opening.\n\n## Details\n\nMore.\n",
        encoding="utf-8",
    )
    config = DocsConfig(
        content_dir=content,
        site_dir=tmp_path / "site",
        repo_root=tmp_path,
        base_path="/preview",
    )
    client = TestClient(create_app(config=config))

    index = client.get("/blog/")
    post = client.get("/blog/first-post/")
    feed = client.get("/blog/feed.xml")

    assert index.status_code == 200
    assert "First post" in index.text
    assert post.status_code == 200
    assert "A dated post." in post.text
    assert 'href="/blog/feed.xml"' in post.text
    assert client.get("/blog/2026-07-27-first-post/").status_code == 404
    assert client.get("/blog/index/").status_code == 404
    assert client.get("/blog/missing/").status_code == 404
    assert feed.status_code == 200
    assert feed.headers["content-type"].startswith("application/atom+xml")
    root = ET.fromstring(feed.content)  # noqa: S314 - parses our serializer output
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    link = root.find("atom:entry/atom:link", ns)
    assert link is not None
    assert link.attrib["href"] == "http://testserver/preview/blog/first-post/"
