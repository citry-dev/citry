"""Tests for the cache backend (``citry/cache.py``) and its wiring on ``Citry``."""

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

    def test_ttl_expires(self):
        cache = InMemoryCache()
        # ttl=0 means the deadline is "now", so by the time get() runs the
        # entry is expired. Deterministic (monotonic clocks never go back).
        cache.set("k", "v", ttl=0)
        assert cache.get("k") is None
        assert not cache.has("k")

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

    def test_max_entries_must_be_positive(self):
        with pytest.raises(ValueError, match="max_entries"):
            InMemoryCache(max_entries=0)

    def test_clear(self):
        cache = InMemoryCache()
        cache.set("k", "v")
        cache.clear()
        assert cache.get("k") is None

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
