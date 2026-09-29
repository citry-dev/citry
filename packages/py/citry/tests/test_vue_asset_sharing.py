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
from citry import cache as citry_cache
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
    app = fastapi.FastAPI()
    mount(app, engine)
    return engine, _counter(engine), TestClient(app)


def _counter(engine: Citry) -> type[Component]:
    """The component every worker registers; defining it again gives the same asset bytes."""

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

    return Counter


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
    vue_events._LOCAL_ASSETS.pop(engine_a, None)
    _engine_c, _counter_c, client_c = _worker(shared)

    for url in urls:
        assert client_a.get(url).content == expected[url]
        assert client_c.get(url).content == expected[url]


def test_rendering_again_restores_assets_the_shared_backend_evicted(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _FakeRedis()
    shared = RedisCache(client)
    _engine_a, counter_a, _client_a = _worker(shared)
    _engine_b, _counter_b, client_b = _worker(shared)
    urls = _linked_asset_urls(counter_a)

    client.data.clear()
    assert all(client_b.get(url).status_code == 404 for url in urls)

    # Worker A saw these assets stored moments ago, so within the recheck
    # interval it trusts that and does not ask the backend again.
    _linked_asset_urls(counter_a)
    assert all(client_b.get(url).status_code == 404 for url in urls)

    # Once the interval has passed, the next render asks again and writes
    # the assets back, so the page it just served works on other workers.
    monkeypatch.setattr(citry_cache, "_STORED_KEY_RECHECK_SECONDS", 0.0)
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


def test_cached_bytes_that_do_not_match_their_digest_are_a_404(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeRedis()
    _engine_a, counter_a, _client_a = _worker(RedisCache(fake))
    engine_b, _counter_b, client_b = _worker(RedisCache(fake))
    urls = _linked_asset_urls(counter_a)
    # Sharing works before the tampering, so the 404s below come from the check.
    assert all(client_b.get(url).status_code == 200 for url in urls)
    # Worker B now holds its own copies; forget them so it reads the cache again.
    vue_events._LOCAL_ASSETS.pop(engine_b, None)

    # A shared store can hold anything another process wrote under a key.
    for key in [key for key in fake.data if key.startswith("citry:vue-")]:
        fake.data[key] = b"globalThis.tampered = true;"
    assert all(client_b.get(url).status_code == 404 for url in urls)
    # Rejected entries are deleted, so rendering the page again repairs them
    # once the rendering worker re-checks the backend.
    assert not any(key.startswith("citry:vue-") for key in fake.data)
    monkeypatch.setattr(citry_cache, "_STORED_KEY_RECHECK_SECONDS", 0.0)
    _linked_asset_urls(counter_a)
    assert all(client_b.get(url).status_code == 200 for url in urls)


def test_the_worker_that_deleted_a_bad_entry_writes_it_again_on_its_next_render() -> None:
    fake = _FakeRedis()
    engine, counter, client = _worker(RedisCache(fake))
    urls = _linked_asset_urls(counter)
    vue_events._LOCAL_ASSETS.pop(engine, None)
    for key in [key for key in fake.data if key.startswith("citry:vue-")]:
        fake.data[key] = b"globalThis.tampered = true;"
    assert all(client.get(url).status_code == 404 for url in urls)

    # This worker deleted the entries itself, so it does not wait for the
    # recheck interval before writing them again.
    _linked_asset_urls(counter)
    vue_events._LOCAL_ASSETS.pop(engine, None)
    assert all(client.get(url).status_code == 200 for url in urls)


class _CountingCache(InMemoryCache):
    """An in-memory backend that counts how often Citry asks it about each key."""

    def __init__(self) -> None:
        super().__init__()
        self.has_calls: list[str] = []
        self.set_calls: list[str] = []

    def has(self, key: str) -> bool:
        self.has_calls.append(key)
        return super().has(key)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.set_calls.append(key)
        super().set(key, value, ttl)


def test_repeated_renders_check_the_shared_cache_once_per_asset() -> None:
    cache = _CountingCache()
    _engine, counter, _client = _worker(cache)
    for _ in range(5):
        _linked_asset_urls(counter)

    asset_has = [key for key in cache.has_calls if key.startswith("citry:vue-")]
    asset_set = [key for key in cache.set_calls if key.startswith("citry:vue-")]
    # Every asset was checked and written exactly once across five renders.
    assert asset_has
    assert sorted(asset_has) == sorted(set(asset_has))
    assert sorted(asset_set) == sorted(set(asset_has))


def test_clearing_the_engine_makes_the_next_render_store_its_assets_again() -> None:
    cache = _CountingCache()
    engine, counter, client = _worker(cache)
    urls = _linked_asset_urls(counter)

    # Citry.clear() empties the engine's in-memory backend. The engine must
    # not keep trusting that the backend still holds its assets.
    engine.clear()
    vue_events._LOCAL_ASSETS.pop(engine, None)
    assert all(client.get(url).status_code == 404 for url in urls)
    # clear() also unregisters components; the same definition links the
    # same assets, and this render must write them back at once.
    assert _linked_asset_urls(_counter(engine)) == urls
    vue_events._LOCAL_ASSETS.pop(engine, None)
    assert all(client.get(url).status_code == 200 for url in urls)


def test_two_engines_sharing_one_in_memory_cache_share_assets() -> None:
    shared = InMemoryCache()
    _engine_a, counter_a, _client_a = _worker(shared)
    _engine_b, _counter_b, client_b = _worker(shared)

    assert all(client_b.get(url).status_code == 200 for url in _linked_asset_urls(counter_a))
