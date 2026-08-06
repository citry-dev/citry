"""Tests for the cache backend (``citry/cache.py``) and its wiring on ``Citry``."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from citry import Citry, CitryCache, InMemoryCache


class TestInMemoryCache:
    def test_get_set_has_delete(self):
        cache = InMemoryCache()
        assert cache.get("k") is None
        assert not cache.has("k")

        cache.set("k", "v")
        assert cache.get("k") == "v"
        assert cache.has("k")

        cache.delete("k")
        assert cache.get("k") is None
        assert not cache.has("k")

    def test_delete_missing_key_is_a_noop(self):
        cache = InMemoryCache()
        cache.delete("never-set")

    def test_set_overwrites(self):
        cache = InMemoryCache()
        cache.set("k", "v1")
        cache.set("k", "v2")
        assert cache.get("k") == "v2"

    def test_positive_ttl_expires_at_its_monotonic_deadline(self, monkeypatch):
        now = [10.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        cache = InMemoryCache()

        cache.set("k", "v", ttl=2.5)
        now[0] = 12.49
        assert cache.get("k") == "v"

        now[0] = 12.5
        assert cache.get("k") is None
        assert not cache.has("k")

    @pytest.mark.parametrize("ttl", [None, 0, 1, 0.25])
    def test_valid_ttl_values(self, ttl):
        cache = InMemoryCache()
        cache.set("k", "v", ttl=ttl)
        assert cache.get("k") == (None if ttl == 0 else "v")

    @pytest.mark.parametrize(
        "ttl",
        [True, False, -1, -0.25, float("nan"), float("inf"), float("-inf"), "1", Decimal(1)],
    )
    def test_invalid_ttl_values(self, ttl):
        cache = InMemoryCache()
        with pytest.raises(ValueError, match="ttl"):
            cache.set("k", "v", ttl=ttl)

    def test_zero_ttl_removes_an_existing_value(self):
        cache = InMemoryCache()
        cache.set("k", "old")
        cache.set("k", "new", ttl=0)
        assert cache.get("k") is None

    def test_no_ttl_keeps_entry(self):
        cache = InMemoryCache()
        cache.set("k", "v", ttl=None)
        assert cache.get("k") == "v"

    def test_max_entries_drops_least_recently_used(self):
        cache = InMemoryCache(max_entries=2)
        cache.set("a", "1")
        cache.set("b", "2")
        # Reading "a" makes "b" the stalest entry.
        assert cache.get("a") == "1"
        cache.set("c", "3")
        assert cache.get("b") is None
        assert cache.get("a") == "1"
        assert cache.get("c") == "3"

    def test_has_refreshes_lru_recency(self):
        cache = InMemoryCache(max_entries=2)
        cache.set("a", "1")
        cache.set("b", "2")
        assert cache.has("a")
        cache.set("c", "3")
        assert cache.get("a") == "1"
        assert cache.get("b") is None

    def test_expired_entries_do_not_evict_live_entries(self, monkeypatch):
        now = [10.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        cache = InMemoryCache(max_entries=2)
        cache.set("live", "1")
        cache.set("expired", "2", ttl=1)
        now[0] = 12.0

        cache.set("new", "3")

        assert cache.get("live") == "1"
        assert cache.get("expired") is None
        assert cache.get("new") == "3"

    def test_max_entries_must_be_positive(self):
        for value in (0, -1, True, 1.5):
            with pytest.raises(ValueError, match="max_entries"):
                InMemoryCache(max_entries=value)

    def test_clear(self):
        cache = InMemoryCache()
        cache.set("k", "v")
        cache.clear()
        assert cache.get("k") is None

    def test_concurrent_operations_are_race_safe(self):
        cache = InMemoryCache(max_entries=17)

        def exercise(worker: int) -> None:
            for index in range(500):
                key = f"{worker}:{index % 23}"
                cache.set(key, str(index), ttl=None if index % 5 else 0.01)
                cache.get(key)
                cache.has(key)
                if index % 7 == 0:
                    cache.delete(key)
                if index % 113 == 0:
                    cache.clear()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(exercise, worker) for worker in range(8)]
            for future in futures:
                future.result()

        assert len(cache._data) <= 17

    def test_satisfies_the_protocol(self):
        assert isinstance(InMemoryCache(), CitryCache)


class TestCitryCacheWiring:
    def test_default_is_a_fresh_in_memory_cache(self):
        c1 = Citry()
        c2 = Citry()
        assert isinstance(c1.cache, InMemoryCache)
        assert c1.cache is not c2.cache

    def test_backend_object_is_used_as_is(self):
        backend = InMemoryCache()
        c = Citry(cache=backend)
        assert c.cache is backend

    def test_import_string_naming_a_class_is_instantiated(self):
        c = Citry(cache="citry.cache.InMemoryCache")
        assert isinstance(c.cache, InMemoryCache)

    def test_invalid_backend_raises(self):
        with pytest.raises(TypeError, match="get/set/delete/has"):
            Citry(cache=object())  # type: ignore[arg-type]

    def test_settings_keep_the_spec(self):
        c = Citry(cache="citry.cache.InMemoryCache")
        assert c.settings.cache == "citry.cache.InMemoryCache"

    def test_clear_clears_the_cache(self):
        c = Citry()
        c.cache.set("k", "v")
        c.clear()
        assert c.cache.get("k") is None
