"""
How an engine without a configured cache keeps page files in memory.

Such an engine keeps its compiled Vue definition bundles and stylesheets,
and the stylesheets that ``css_data()`` produces, only in this process, up
to ``vue_asset_max_bytes``, and drops the ones used longest ago beyond that.
An engine given a cache backend is covered by ``test_vue_asset_sharing.py``.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading

import pytest

from citry import Citry, CitrySettings, Component, Extension, InMemoryCache
from citry._vue import events as vue_events
from citry._vue.capture import render_prepared_direct
from citry._vue.events import default_events_producer
from citry.ext.dependencies.scripts import gen_cache_key, get_script
from citry.settings import DEFAULT_VUE_ASSET_MAX_BYTES


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_default_engine_keeps_assets_out_of_its_cache() -> None:
    app = Citry(autodiscover=False)
    producer = default_events_producer(app)
    content = b"globalThis.definition = 1;"
    producer._publish_bundle(_digest(content), content)

    # The asset is served from this process, and the engine's private
    # in-memory cache holds no second copy of it.
    assert vue_events.definition_bundle(app, _digest(content)) == content
    assert not app.cache.has(vue_events._asset_cache_key("definition", _digest(content)))


def test_default_engine_drops_the_least_recently_used_assets_past_its_byte_limit() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=100)
    producer = default_events_producer(app)
    first, second, third = (bytes([ord("a") + index]) * 40 for index in range(3))
    producer._publish_bundle(_digest(first), first)
    producer._publish_style(_digest(second), second)
    # Reading the first asset makes it the most recently used ...
    assert vue_events.definition_bundle(app, _digest(first)) == first
    producer._publish_bundle(_digest(third), third)

    # ... so the third asset pushes the total past 100 bytes and drops the
    # second one, whichever kind it is. An open page asking for it gets a 404.
    assert vue_events.style_asset(app, _digest(second)) is None
    assert vue_events.definition_bundle(app, _digest(first)) == first
    assert vue_events.definition_bundle(app, _digest(third)) == third
    assert vue_events._LOCAL_ASSETS[app].total_bytes == 80


def test_an_asset_larger_than_the_limit_is_still_kept_while_it_is_the_newest() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=10)
    producer = default_events_producer(app)
    small, large = b"x" * 5, b"y" * 50
    producer._publish_bundle(_digest(small), small)
    producer._publish_bundle(_digest(large), large)

    # The page being rendered links the large asset right now, so it stays.
    assert vue_events.definition_bundle(app, _digest(large)) == large
    assert vue_events.definition_bundle(app, _digest(small)) is None


def test_no_limit_keeps_every_asset() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=None)
    producer = default_events_producer(app)
    contents = [f"asset-{index}".encode() * 100 for index in range(vue_events._LOCAL_ASSET_LIMIT + 5)]
    for content in contents:
        producer._publish_bundle(_digest(content), content)
    assert all(vue_events.definition_bundle(app, _digest(content)) == content for content in contents)


def test_vue_asset_max_bytes_defaults_to_64_mib() -> None:
    assert DEFAULT_VUE_ASSET_MAX_BYTES == 64 * 1024 * 1024
    assert Citry().settings.vue_asset_max_bytes == DEFAULT_VUE_ASSET_MAX_BYTES
    assert CitrySettings().vue_asset_max_bytes == DEFAULT_VUE_ASSET_MAX_BYTES
    assert Citry(vue_asset_max_bytes=None).settings.vue_asset_max_bytes is None


@pytest.mark.parametrize(
    ("value", "error"),
    [(0, ValueError), (-1, ValueError), (True, TypeError), (1.5, TypeError), ("64MB", TypeError)],
)
def test_invalid_vue_asset_max_bytes_is_rejected(value: object, error: type[Exception]) -> None:
    with pytest.raises(error, match="vue_asset_max_bytes"):
        Citry(vue_asset_max_bytes=value)  # type: ignore[arg-type]
    with pytest.raises(error, match="vue_asset_max_bytes"):
        CitrySettings(vue_asset_max_bytes=value)  # type: ignore[arg-type]


def test_a_page_whose_files_exceed_the_limit_still_finds_every_file_it_links() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=3000)
    app.set_mounted_prefix("/citry")
    rule = "".join(f".row-{index} {{ color: var(--accent); }}\n" for index in range(40))
    script = "".join(f"globalThis.value{index} = {index};\n" for index in range(60))

    class Panel(Component):
        citry = app
        template = """
          <button @click="count++" v-text="count"></button>
        """
        css = rule
        js = script

        def js_data(self, kwargs, slots):
            return {"count": 0}

        def css_data(self, kwargs, slots):
            return {"accent": "teal"}

    html = Panel().render().serialize()
    digests = set(re.findall(r"/citry/ext/events/definitions/([0-9a-f]{64})\.js", html))
    styles = set(re.findall(r"/citry/ext/events/assets/([0-9a-f]{64})\.css", html))
    assert len(digests) >= 2
    # Every file the page links is still there for the browser's first
    # request, although together they exceed the 3000-byte limit.
    scripts = [vue_events.definition_bundle(app, digest) for digest in digests]
    sheets = [vue_events.style_asset(app, digest) for digest in styles]
    assert all(content is not None for content in [*scripts, *sheets])
    assert sum(len(content or b"") for content in [*scripts, *sheets]) > 3000


def test_a_render_in_progress_keeps_its_files_while_another_render_publishes() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=100)
    producer = default_events_producer(app)
    held = b"h" * 60
    other = [bytes([ord("a") + index]) * 60 for index in range(3)]
    done = threading.Event()

    def other_render() -> None:
        # A second render on another thread publishes past the limit.
        with vue_events._hold_render_assets():
            for content in other:
                producer._publish_bundle(_digest(content), content)
        done.set()

    with vue_events._hold_render_assets():
        producer._publish_bundle(_digest(held), held)
        worker = threading.Thread(target=other_render)
        worker.start()
        worker.join()
        assert done.is_set()
        # The first render has not finished, so its file is still there.
        assert vue_events.definition_bundle(app, _digest(held)) == held

    # Finishing releases the hold without dropping anything, because that
    # page is about to be sent; the next publish applies the limit again.
    local = vue_events._LOCAL_ASSETS[app]
    assert not local.held
    assert vue_events.definition_bundle(app, _digest(held)) == held
    latest = b"z" * 60
    producer._publish_bundle(_digest(latest), latest)
    assert vue_events.definition_bundle(app, _digest(held)) is None
    assert local.total_bytes == 60


def _swatch(app: Citry) -> type[Component]:
    """A component whose ``css_data()`` makes one stylesheet per ``accent`` value."""

    class Swatch(Component):
        citry = app
        template = """
          <span class="swatch">x</span>
        """
        css = """
          .swatch { color: var(--accent); }
        """

        def css_data(self, kwargs, slots):
            return {"accent": kwargs["accent"]}

    return Swatch


def _css_data_hashes(html: str) -> list[str]:
    return re.findall(r'data-ccss-([0-9a-f]+)=""', html)


def test_css_data_stylesheets_stay_within_the_byte_limit() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=2000)
    swatch = _swatch(app)
    hashes = [_css_data_hashes(swatch(accent=f"#{index:06x}").render().serialize())[0] for index in range(200)]

    # Each value made its own stylesheet, but the store kept only as many as
    # fit in 2000 bytes, and the default cache holds none of them.
    local = vue_events._LOCAL_ASSETS[app]
    kept = [key for key in local.entries if key[0] == "css-data"]
    assert 1 < len(kept) < 20
    assert local.total_bytes <= 2000
    assert not any(app.cache.has(gen_cache_key(swatch.class_id, "css", digest)) for digest in hashes)
    # The oldest was dropped, so its URL now answers 404; the newest is kept.
    assert get_script("css", swatch, hashes[0]) is None
    assert get_script("css", swatch, hashes[-1]) is not None


def test_a_page_keeps_its_css_data_stylesheets_while_other_renders_publish() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=1)
    app.set_mounted_prefix("/citry")
    swatch = _swatch(app)

    class Page(Component):
        citry = app
        template = """
          <html><head></head><body>
            <c-swatch accent="teal" />
            <c-swatch accent="navy" />
          </body></html>
        """

    page = Page().render()
    fragment = swatch(accent="olive").render()
    # Renders that finish between this page's render and its serialization
    # fill the 1-byte store with their own stylesheets.
    for index in range(5):
        swatch(accent=f"#{index:06x}").render().serialize()

    # The page still inlines both of its stylesheets ...
    html = page.serialize()
    assert "--accent: teal;" in html
    assert "--accent: navy;" in html
    # ... and a fragment's linked stylesheet is there for the browser's
    # first request, although the limit is far smaller than one stylesheet.
    linked = fragment.serialize(deps_strategy="fragment")
    digest = _css_data_hashes(linked)[0]
    assert f"/citry/cache/{swatch.class_id}.{digest}.css" in linked
    served = get_script("css", swatch, digest)
    assert served is not None
    assert "--accent: olive;" in (served.content or "")


def test_a_configured_cache_receives_every_css_data_stylesheet() -> None:
    backend = InMemoryCache()
    app = Citry(autodiscover=False, cache=backend, vue_asset_max_bytes=1)
    swatch = _swatch(app)
    hashes = [_css_data_hashes(swatch(accent=f"#{index:06x}").render().serialize())[0] for index in range(20)]

    # The backend's own capacity applies, so vue_asset_max_bytes drops none.
    assert all(backend.has(gen_cache_key(swatch.class_id, "css", digest)) for digest in hashes)
    assert all(get_script("css", swatch, digest) is not None for digest in hashes)
    # The backend is the only copy; this process keeps none.
    local = vue_events._LOCAL_ASSETS.get(app)
    assert local is None or not any(key[0] == "css-data" for key in local.entries)


def _panel(app: Citry, *, cached: bool = False, calls: list[str] | None = None) -> type[Component]:
    """An interactive component whose ``css_data()`` makes one stylesheet per ``accent`` value."""

    class Panel(Component):
        citry = app

        class Cache:
            enabled = cached

        template = """
          <button @click="count++" v-text="count"></button>
        """
        css = """
          button { color: var(--accent); }
        """

        def js_data(self, kwargs, slots):
            return {"count": 0}

        def css_data(self, kwargs, slots):
            if calls is not None:
                calls.append(kwargs["accent"])
            return {"accent": kwargs["accent"]}

    return Panel


def _linked_css_data(panel: type[Component], text: str) -> list[str]:
    """The ``css_data()`` stylesheet hashes ``text`` links, each checked to be served now."""
    hashes = re.findall(rf"/citry/cache/{panel.class_id}\.([0-9a-f]{{32}})\.css", text)
    assert hashes
    assert all(get_script("css", panel, digest) is not None for digest in hashes)
    return hashes


def test_a_vue_page_links_every_css_data_stylesheet_under_a_tiny_limit() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=1)
    app.set_mounted_prefix("/citry")
    panel = _panel(app)

    class Page(Component):
        citry = app
        template = """
          <main>
            <c-panel accent="teal" />
            <c-panel accent="navy" />
          </main>
        """

    # Each stylesheet alone exceeds the limit, yet both stay linked and
    # served, because the page holds them while it is written.
    assert len(set(_linked_css_data(panel, Page().render().serialize()))) == 2


def test_a_vue_page_keeps_its_css_data_stylesheets_while_other_renders_publish() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=1)
    app.set_mounted_prefix("/citry")
    panel = _panel(app)
    page = panel(accent="teal").render()
    for index in range(3):
        panel(accent=f"#{index:06x}").render().serialize()

    # The Vue preparation reads the stylesheet before the dependencies
    # step runs, so the page publishes it before either one runs.
    html = page.serialize()
    (digest,) = set(_linked_css_data(panel, html))
    served = get_script("css", panel, digest)
    assert served is not None
    assert "--accent: teal;" in (served.content or "")


def test_an_event_response_publishes_its_css_data_stylesheets() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=1)
    app.set_mounted_prefix("/citry")
    panel = _panel(app)
    render = render_prepared_direct(panel(accent="teal"))
    for index in range(3):
        panel(accent=f"#{index:06x}").render().serialize()

    # An event response is prepared without serializing a page.
    payload = default_events_producer(app).prepare_from_render(render, citry=app, app_id="a" * 32, revision=0)
    _linked_css_data(panel, json.dumps(payload))


def test_a_replayed_vue_page_still_links_its_css_data_stylesheet() -> None:
    app = Citry(autodiscover=False, vue_asset_max_bytes=1)
    app.set_mounted_prefix("/citry")
    calls: list[str] = []
    panel = _panel(app, cached=True, calls=calls)
    (first,) = set(_linked_css_data(panel, panel(accent="teal").render().serialize()))
    for index in range(3):
        panel(accent=f"#{index:06x}").render().serialize()
    assert get_script("css", panel, first) is None

    # The replay renders nothing, so its stylesheet comes from the stored
    # render and is published again when the replayed page is written.
    assert set(_linked_css_data(panel, panel(accent="teal").render().serialize())) == {first}
    assert calls.count("teal") == 1


def test_a_page_serialized_inside_another_page_publishes_its_css_data_stylesheets() -> None:
    holder: dict[str, type[Component]] = {}

    class AppendSwatch(Extension):
        name = "append_swatch"

        def on_serialize(self, ctx):
            swatch = holder["swatch"]
            if type(ctx.selected_render.context.component) is swatch:
                return None
            # A render serialized inside the outer page's serialization.
            return ctx.html + swatch(accent="olive").render().serialize()

    app = Citry(autodiscover=False, extensions=[AppendSwatch])
    holder["swatch"] = _swatch(app)

    class Page(Component):
        citry = app
        template = """
          <html><head></head><body><c-swatch accent="teal" /></body></html>
        """

    html = Page().render().serialize()
    assert "--accent: teal;" in html
    assert "--accent: olive;" in html
