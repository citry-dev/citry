"""
How an engine without a configured cache keeps compiled Vue assets in memory.

Such an engine keeps its definition bundles and stylesheets only in this
process, up to ``vue_asset_max_bytes``, and drops the ones used longest ago
beyond that. An engine given a cache backend is covered by
``test_vue_asset_sharing.py``.
"""

from __future__ import annotations

import hashlib
import re
import threading

import pytest

from citry import Citry, CitrySettings, Component
from citry._vue import events as vue_events
from citry._vue.events import default_events_producer
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
