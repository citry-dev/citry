"""
Compiled Vue definitions and stylesheets resolve on every worker that shares a cache.

A rendered page links ``/ext/events/definitions/<digest>.js`` and
``/ext/events/assets/<digest>.css``. The browser may fetch those URLs from a
different worker than the one that rendered the page, so each test here plays
two workers with two ``Citry`` instances and checks which of them can answer.
"""

from __future__ import annotations

import re

import fastapi
import pytest
from fastapi.testclient import TestClient

from citry import Citry, Component
from citry._vue import events as vue_events
from citry.cache import InMemoryCache
from citry.contrib.caches import RedisCache
from citry.contrib.fastapi import mount

_ASSET_URL = re.compile(r"/citry/ext/events/(?:definitions/[0-9a-f]{64}\.js|assets/[0-9a-f]{64}\.css)")


class _FakeRedis:
    """The slice of redis-py's API ``RedisCache`` touches; stores bytes like the real client."""

    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}

    def get(self, name: str) -> bytes | None:
        return self.data.get(name)

    def set(self, name: str, value: str, ex: float | None = None) -> None:
        self.data[name] = value.encode()

    def delete(self, name: str) -> None:
        self.data.pop(name, None)

    def exists(self, name: str) -> int:
        return 1 if name in self.data else 0


def _worker(cache: object | None = None) -> tuple[Citry, type[Component], TestClient]:
    """One worker: an engine with the same component every worker registers, mounted in a web app."""
    engine = Citry(secret="vue-asset-sharing-secret", autodiscover=False, cache=cache)  # noqa: S106

    class Counter(Component):
        citry = engine
        template = """
          <button @click="count++" v-text="count"></button>
        """
        # A css_data variable makes the page link a stylesheet asset too.
        css = """
          button { color: var(--accent); }
        """

        def js_data(self, kwargs, slots):
            return {"count": 0}

        def css_data(self, kwargs, slots):
            return {"accent": "teal"}

    app = fastapi.FastAPI()
    mount(app, engine)
    return engine, Counter, TestClient(app)


def _linked_asset_urls(component: type[Component]) -> list[str]:
    urls = sorted(set(_ASSET_URL.findall(component().render().serialize())))
    # Both kinds must be present, or the test would silently cover only one route.
    assert any("/definitions/" in url for url in urls)
    assert any("/assets/" in url for url in urls)
    return urls


def _public_headers(response) -> tuple[str, str, str]:
    return (
        response.headers["content-type"],
        response.headers["cache-control"],
        response.headers["access-control-allow-origin"],
    )


def test_a_worker_sharing_the_cache_serves_assets_another_worker_rendered() -> None:
    shared = RedisCache(_FakeRedis())
    _engine_a, counter_a, client_a = _worker(shared)
    _engine_b, _counter_b, client_b = _worker(shared)

    for url in _linked_asset_urls(counter_a):
        from_a = client_a.get(url)
        from_b = client_b.get(url)
        assert from_a.status_code == 200
        assert from_b.status_code == 200
        assert from_b.content == from_a.content
        assert _public_headers(from_b) == _public_headers(from_a)
        assert _public_headers(from_b)[1:] == ("public, max-age=31536000, immutable", "*")


def test_a_restarted_worker_serves_assets_from_the_shared_cache() -> None:
    shared = RedisCache(_FakeRedis())
    engine_a, counter_a, client_a = _worker(shared)
    urls = _linked_asset_urls(counter_a)
    expected = {url: client_a.get(url).content for url in urls}

    # Forgetting the rendering process's own copies is what a restart or an
    # eviction from its bounded in-memory map looks like.
    vue_events._BUNDLES.pop(engine_a, None)
    vue_events._STYLE_ASSETS.pop(engine_a, None)
    _engine_c, _counter_c, client_c = _worker(shared)

    for url in urls:
        assert client_a.get(url).content == expected[url]
        assert client_c.get(url).content == expected[url]


def test_rendering_again_restores_assets_the_shared_backend_evicted() -> None:
    client = _FakeRedis()
    shared = RedisCache(client)
    _engine_a, counter_a, _client_a = _worker(shared)
    _engine_b, _counter_b, client_b = _worker(shared)
    urls = _linked_asset_urls(counter_a)

    client.data.clear()
    assert all(client_b.get(url).status_code == 404 for url in urls)

    # The rendering worker still holds the assets in memory, but it must
    # write them back so the page it just served works on other workers.
    _linked_asset_urls(counter_a)
    assert all(client_b.get(url).status_code == 200 for url in urls)


def test_workers_with_their_own_default_caches_do_not_share_assets() -> None:
    _engine_a, counter_a, client_a = _worker()
    _engine_b, _counter_b, client_b = _worker()

    for url in _linked_asset_urls(counter_a):
        assert client_a.get(url).status_code == 200
        assert client_b.get(url).status_code == 404


@pytest.mark.parametrize("route", ["definitions/{digest}.js", "assets/{digest}.css"])
def test_an_unpublished_digest_is_a_404(route: str) -> None:
    _engine, _counter, client = _worker(RedisCache(_FakeRedis()))
    response = client.get("/citry/ext/events/" + route.format(digest="0" * 64))
    assert response.status_code == 404


def test_cached_bytes_that_do_not_match_their_digest_are_a_404() -> None:
    fake = _FakeRedis()
    _engine_a, counter_a, _client_a = _worker(RedisCache(fake))
    engine_b, _counter_b, client_b = _worker(RedisCache(fake))
    urls = _linked_asset_urls(counter_a)
    # Sharing works before the tampering, so the 404s below come from the check.
    assert all(client_b.get(url).status_code == 200 for url in urls)
    # Worker B now holds its own copies; forget them so it reads the cache again.
    vue_events._BUNDLES.pop(engine_b, None)
    vue_events._STYLE_ASSETS.pop(engine_b, None)

    # A shared store can hold anything another process wrote under a key.
    for key in [key for key in fake.data if key.startswith("citry:vue-")]:
        fake.data[key] = b"globalThis.tampered = true;"
    assert all(client_b.get(url).status_code == 404 for url in urls)
    # Rejected entries are deleted, so rendering the page again repairs them.
    assert not any(key.startswith("citry:vue-") for key in fake.data)
    _linked_asset_urls(counter_a)
    assert all(client_b.get(url).status_code == 200 for url in urls)


def test_two_engines_sharing_one_in_memory_cache_share_assets() -> None:
    shared = InMemoryCache()
    _engine_a, counter_a, _client_a = _worker(shared)
    _engine_b, _counter_b, client_b = _worker(shared)

    assert all(client_b.get(url).status_code == 200 for url in _linked_asset_urls(counter_a))
