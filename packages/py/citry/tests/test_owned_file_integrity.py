"""
Citry pins every file it serves, with no script security setting.

A `<base>` element that markup places before one of these tags moves its
root-relative URL to another site, so the tag itself must tell the browser
which bytes to accept. These tests render each route to the page and compare
the `integrity` value with the body the matching route answers with.
"""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import replace
from html import unescape
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component, Extension
from citry._owned_resource import _OwnedResource
from citry.ext.dependencies import Script, Style
from citry.util.routing import match_route

if TYPE_CHECKING:
    from pathlib import Path


TAG = re.compile(r"<(?:script|link)\b[^>]*>")
ATTR = re.compile(r'([\w:-]+)="([^"]*)"')


def _app(**kwargs: object) -> Citry:
    app = Citry(autodiscover=False, **kwargs)  # type: ignore[arg-type]
    app.set_mounted_prefix("/citry")
    return app


def _sri(body: bytes) -> str:
    return f"sha384-{base64.b64encode(hashlib.sha384(body).digest()).decode('ascii')}"


def _served(app: Citry, url: str) -> bytes:
    matched = match_route(app.urls, url.removeprefix("/citry/"))
    assert matched is not None, url
    response = matched.route.handler(None, **matched.params)
    assert response.status == 200, url
    return response.body


def _tags(html: str) -> dict[str, dict[str, str]]:
    """Return every tag that fetches a file from Citry's mount, by URL."""
    found: dict[str, dict[str, str]] = {}
    for tag in TAG.findall(html):
        attrs = {name: unescape(value) for name, value in ATTR.findall(tag)}
        url = attrs.get("src") or attrs.get("href") or ""
        if url.startswith("/citry/") and attrs.get("rel") != "preload":
            found[url] = attrs
    return found


def _assert_all_pinned(app: Citry, html: str, *expected: str) -> None:
    tags = _tags(html)
    for fragment in expected:
        assert any(fragment in url for url in tags), (fragment, sorted(tags))
    for url, attrs in tags.items():
        assert attrs.get("integrity") == _sri(_served(app, url)), url
        assert attrs.get("crossorigin") == "anonymous", url


def _served_files(tmp_path: Path) -> type:
    (tmp_path / "local.js").write_text("window.local = 1;\n", encoding="utf8")
    (tmp_path / "local.css").write_text("html { --local: 1; }\n", encoding="utf8")

    class Dependencies:
        local_files = "serve"
        js = [tmp_path / "local.js"]
        css = {"all": [tmp_path / "local.css"]}

    return Dependencies


class TestDocuments:
    def test_interactive_document_pins_the_runtime_and_its_preload(self):
        app = _app()

        class Page(Component):
            citry = app
            template = """
                <html>
                  <head><title>t</title></head>
                  <body><button @click="open = true">open</button></body>
                </html>
            """

        html = Page().render().serialize()
        _assert_all_pinned(app, html, "citry.js")
        # A hint with other values is not reused, so the browser would fetch the file twice.
        preload = next(tag for tag in TAG.findall(html) if 'rel="preload"' in tag and "citry.js" in tag)
        assert _tags(html)["/citry/citry.js"]["integrity"] in preload
        assert 'crossorigin="anonymous"' in preload

    def test_i18n_runtime_is_pinned(self):
        app = _app(extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}})

        class Page(Component):
            citry = app
            template = """
                <c-i18n c-client="True" tag="main">
                    <output v-text="$i18n.tr('client-title')"></output>
                </c-i18n>
            """
            messages = "client-title = Client title"

        _assert_all_pinned(app, Page().render().serialize(), "citry.js", "ext/i18n/runtime.js")

    @pytest.mark.parametrize("mode", ["allow", "omit"])
    def test_served_files_on_a_static_document_are_pinned(self, tmp_path: Path, mode: str):
        app = _app(security_javascript=mode)

        class Page(Component):
            citry = app
            template = "<main>static</main>"
            Dependencies = _served_files(tmp_path)

        html = Page().render().serialize()
        _assert_all_pinned(app, html, ".css", *([".js"] if mode == "allow" else []))

    def test_simple_strategy_pins_served_files(self, tmp_path: Path):
        app = _app()

        class Page(Component):
            citry = app
            template = "<main>static</main>"
            Dependencies = _served_files(tmp_path)

        _assert_all_pinned(app, Page().render().serialize(deps_strategy="simple"), ".js", ".css")

    def test_served_stylesheet_with_a_media_type_is_pinned(self, tmp_path: Path):
        app = _app()
        (tmp_path / "print.css").write_text("html { --print: 1; }\n", encoding="utf8")

        class Page(Component):
            citry = app
            template = "<main>static</main>"

            class Dependencies:
                local_files = "serve"
                css = {"print": [tmp_path / "print.css"]}

        html = Page().render().serialize()
        _assert_all_pinned(app, html, ".css")
        assert 'media="print"' in html

    @pytest.mark.parametrize("nonce", [None, "probe-nonce"])
    def test_served_files_on_an_interactive_document_are_pinned(self, tmp_path: Path, nonce: str | None):
        app = _app()

        class Page(Component):
            citry = app
            template = """
                <html>
                  <head><title>t</title></head>
                  <body><button @click="open = true">open</button></body>
                </html>
            """
            Dependencies = _served_files(tmp_path)

        html = Page().render().serialize(csp_nonce=nonce)
        # The script is listed in the page's data for the runtime to load, as
        # JSON that names the same two attributes.
        script_url = re.search(r"/citry/asset/[0-9a-f]+\.js", html)
        assert script_url is not None
        digest = _sri(_served(app, script_url.group()))
        assert f'"integrity":"{digest}"' in html.replace(" ", "")
        assert '"crossorigin":"anonymous"' in html.replace(" ", "")
        _assert_all_pinned(app, html, ".css")

    def test_cached_render_is_pinned_like_a_fresh_one(self):
        app = _app()
        renders: list[int] = []

        class Page(Component):
            citry = app
            template = """
                <html>
                  <head><title>t</title></head>
                  <body><button @click="open = true">open</button></body>
                </html>
            """

            class Cache:
                enabled = True

            def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
                renders.append(1)
                return {}

        Page().render().serialize()
        replayed = Page().render().serialize()
        # One render means the second page came from the cache.
        assert len(renders) == 1
        _assert_all_pinned(app, replayed, "citry.js")


class TestFragments:
    def test_interactive_fragment_loader_pins_the_runtime(self):
        app = _app()

        class Widget(Component):
            citry = app
            template = '<button @click="open = true">open</button>'

        html = Widget().render().serialize(deps_strategy="fragment")
        assert f's.integrity = "{_sri(_served(app, "/citry/citry.js"))}"' in html
        assert 's.crossOrigin = "anonymous"' in html

    def test_static_fragment_pins_component_variables_and_served_files(self, tmp_path: Path):
        app = _app()

        class Card(Component):
            citry = app
            template = "<div>card</div>"
            css = """
                div { color: var(--tone); }
            """
            Dependencies = _served_files(tmp_path)

            def css_data(self, kwargs: object, slots: object) -> dict[str, str]:
                return {"tone": "red"}

        html = Card().render().serialize(deps_strategy="fragment")
        _assert_all_pinned(app, html, "/cache/", "/asset/", ".js")
        assert len([url for url in _tags(html) if url.endswith(".css")]) == 3

    def test_stylesheet_the_store_dropped_keeps_its_hash(self):
        app = _app()

        class Card(Component):
            citry = app
            template = "<div>card</div>"
            css = """
                div { color: var(--tone); }
            """

            def css_data(self, kwargs: object, slots: object) -> dict[str, str]:
                return {"tone": "red"}

        rendered = Card().render()
        # The store drops entries it needs room for, possibly between the two steps.
        app.cache.clear()
        html = rendered.serialize(deps_strategy="fragment")
        links = [tag for tag in TAG.findall(html) if "rel=" in tag]
        assert len(links) == 2
        assert all('integrity="sha384-' in link for link in links)


class TestHooks:
    def _page(self, app: Citry, tmp_path: Path) -> type[Component]:
        class Page(Component):
            citry = app
            template = "<main>static</main>"
            Dependencies = _served_files(tmp_path)

        return Page

    def test_hook_that_moves_a_file_leaves_the_attributes_off(self, tmp_path: Path):
        class Move(Extension):
            name = "move"

            def on_dependencies(self, ctx: object) -> None:
                for script in ctx.scripts:  # type: ignore[attr-defined]
                    script.url = "https://cdn.example.test/moved.js"

        app = _app(extensions=[Move])
        html = self._page(app, tmp_path)().render().serialize()
        moved = next(tag for tag in TAG.findall(html) if "cdn.example.test" in tag)
        assert "integrity" not in moved
        assert "crossorigin" not in moved

    def test_hook_values_stay_as_written(self, tmp_path: Path):
        class Edit(Extension):
            name = "edit"

            def on_dependencies(self, ctx: object) -> None:
                for dependency in [*ctx.scripts, *ctx.styles]:  # type: ignore[attr-defined]
                    dependency.attrs["CrossOrigin"] = "use-credentials"

        app = _app(extensions=[Edit])
        html = self._page(app, tmp_path)().render().serialize()
        assert 'crossorigin="anonymous"' not in html
        assert html.count('CrossOrigin="use-credentials"') == 2
        assert html.count('integrity="sha384-') == 2

    def test_hook_that_rebuilds_a_tag_keeps_the_hash(self, tmp_path: Path):
        class Rebuild(Extension):
            name = "rebuild"

            def on_dependencies(self, ctx: object) -> None:
                for values in (ctx.scripts, ctx.styles):  # type: ignore[attr-defined]
                    values[:] = [replace(dependency, attrs={"data-rebuilt": "1"}) for dependency in values]

        app = _app(extensions=[Rebuild])
        html = self._page(app, tmp_path)().render().serialize()
        assert html.count('data-rebuilt="1"') == 2
        _assert_all_pinned(app, html, ".js", ".css")


class TestDependencyObjects:
    def _resource(self, url: str = "/citry/x.css") -> _OwnedResource:
        return _OwnedResource(url=url, content="a {}", content_type="text/css; charset=utf-8")

    def test_author_urls_are_left_alone(self):
        assert "integrity" not in Script(url="/static/app.js").render()
        assert "crossorigin" not in Style(url="/static/app.css").render()

    def test_replace_keeps_the_file(self):
        style = Style(url="/citry/x.css")
        style._owned_resource = self._resource()
        rebuilt = str(replace(style, attrs={"media": "print"}).render())
        assert 'media="print"' in rebuilt
        assert "integrity" in rebuilt
        assert "integrity" not in replace(style, url="/elsewhere.css").render()

    def test_a_declared_value_is_kept(self):
        style = Style(url="/citry/x.css", attrs={"Integrity": "sha256-kept"})
        style._owned_resource = self._resource()
        html = str(style.render())
        assert 'Integrity="sha256-kept"' in html
        assert 'integrity="' not in html

    def test_a_tag_at_another_url_is_not_pinned(self):
        style = Style(url="/elsewhere.css")
        style._owned_resource = self._resource()
        assert "integrity" not in style.render()
