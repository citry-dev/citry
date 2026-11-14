"""Tests for the cache backend (``citry/cache.py``) and its wiring on ``Citry``."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from citry import Citry, CitryCache, InMemoryCache
from citry.cache import _store_if_missing


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

    def test_an_unbounded_store_removes_expired_entries_nobody_reads(self, monkeypatch):
        # Server-stored State writes a fresh key per render and never reads
        # the old ones again, so expiry cannot wait for a read.
        now = [100.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        cache = InMemoryCache()
        for index in range(1000):
            cache.set(f"k{index}", "v", ttl=1)
        cache.set("forever", "v")
        now[0] = 102.0
        cache.set("trigger", "v", ttl=1)
        assert set(cache._data) == {"forever", "trigger"}

    def test_a_rewritten_key_keeps_its_newer_deadline(self, monkeypatch):
        now = [100.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        cache = InMemoryCache()
        cache.set("k", "old", ttl=1)
        cache.set("k", "new", ttl=10)
        now[0] = 105.0
        cache.set("trigger", "v")
        assert cache.get("k") == "new"
        cache.set("k", "kept")
        now[0] = 120.0
        cache.set("trigger", "v")
        # The key's last write had no TTL, so no earlier deadline removes it.
        assert cache.get("k") == "kept"

    def test_rewriting_one_key_does_not_grow_the_deadline_list(self, monkeypatch):
        now = [100.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        cache = InMemoryCache()
        for _ in range(10_000):
            cache.set("k", "v", ttl=3600)
        assert len(cache._deadlines) < 100

    def test_clear_also_forgets_deadlines(self):
        cache = InMemoryCache()
        cache.set("k", "v", ttl=60)
        cache.clear()
        assert cache._deadlines == []

    def test_state_entries_stay_within_their_byte_budget(self):
        cache = InMemoryCache(state_max_bytes=10_000)
        for index in range(100):
            cache.set(f"citry:state:k{index}", "x" * 500)
        assert cache._state_bytes <= 10_000
        # The newest entries are the ones kept.
        assert cache.get("citry:state:k99") == "x" * 500
        assert cache.get("citry:state:k0") is None

    def test_a_state_entry_read_recently_is_kept_longer(self):
        cache = InMemoryCache(state_max_bytes=3 * InMemoryCache._entry_bytes("citry:state:k0", "x" * 100))
        for index in range(3):
            cache.set(f"citry:state:k{index}", "x" * 100)
        cache.get("citry:state:k0")
        cache.set("citry:state:k3", "x" * 100)
        assert cache.get("citry:state:k0") is not None
        assert cache.get("citry:state:k1") is None

    def test_state_entries_never_push_out_other_entries(self):
        # A flood of State writes must not drop the assets open pages load.
        cache = InMemoryCache(max_entries=2, state_max_bytes=5_000)
        cache.set("citry:asset:a", "a")
        cache.set("citry:asset:b", "b")
        for index in range(1000):
            cache.set(f"citry:state:k{index}", "x" * 200)
        assert cache.get("citry:asset:a") == "a"
        assert cache.get("citry:asset:b") == "b"

    def test_state_entries_do_not_count_toward_max_entries(self):
        cache = InMemoryCache(max_entries=1)
        cache.set("citry:state:k", "s")
        cache.set("other", "o")
        assert cache.get("citry:state:k") == "s"
        assert cache.get("other") == "o"

    def test_a_state_entry_larger_than_the_budget_is_not_stored(self, caplog):
        cache = InMemoryCache(state_max_bytes=1_000)
        cache.set("citry:state:other", "kept")
        cache.set("citry:state:k", "small")
        with caplog.at_level("WARNING", logger="citry"):
            cache.set("citry:state:k", "x" * 2_000)
        # The old value is gone too, so a call with that token answers stale.
        assert cache.get("citry:state:k") is None
        # Refusing it must not first empty the store to make room.
        assert cache.get("citry:state:other") == "kept"
        assert any("larger than its whole state_max_bytes" in record.message for record in caplog.records)

    def test_non_ascii_state_counts_the_memory_it_really_takes(self):
        # One character above U+FFFF makes CPython store the whole string at
        # four bytes per character, so counting characters would undercount.
        ascii_size = InMemoryCache._entry_bytes("citry:state:k", "x" * 10_000)
        wide_size = InMemoryCache._entry_bytes("citry:state:k", "x" * 9_999 + "\U0001f600")
        assert wide_size > 3 * ascii_size - 1_000

    def test_the_state_byte_count_follows_rewrites_deletes_and_expiry(self, monkeypatch):
        now = [100.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        cache = InMemoryCache()
        cache.set("citry:state:a", "x" * 100)
        cache.set("citry:state:a", "x" * 50)
        cache.set("citry:state:b", "x" * 10, ttl=1)
        cache.set("citry:state:c", "x" * 10)
        cache.delete("citry:state:c")
        now[0] = 102.0
        cache.set("trigger", "v")
        assert set(cache._state) == {"citry:state:a"}
        assert cache._state_bytes == InMemoryCache._entry_bytes("citry:state:a", "x" * 50)
        cache.clear()
        assert cache._state_bytes == 0

    def test_the_default_state_budget_is_64_mib(self):
        assert InMemoryCache()._state_max_bytes == 64 * 1024 * 1024

    def test_no_state_budget_keeps_every_state_entry(self):
        cache = InMemoryCache(state_max_bytes=None)
        for index in range(1000):
            cache.set(f"citry:state:k{index}", "x" * 1000)
        assert len(cache._state) == 1000

    def test_state_max_bytes_must_be_positive(self):
        for value in (0, -1, True, 1.5, "1"):
            with pytest.raises(ValueError, match="state_max_bytes"):
                InMemoryCache(state_max_bytes=value)

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


class _Owner:
    """What a store call remembers its confirmed keys under (the engine, in a real render)."""


class _TwoArgumentCache:
    """A backend whose ``set`` has no ``ttl`` parameter, as one written before the parameter existed."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)

    def has(self, key: str) -> bool:
        return key in self.values


class _TtlRecordingCache(_TwoArgumentCache):
    def __init__(self) -> None:
        super().__init__()
        self.ttls: list[float | None] = []

    def set(self, key: str, value: str, ttl: float | None = None) -> None:  # type: ignore[override]
        self.ttls.append(ttl)
        super().set(key, value)


class _KeywordTtlCache(_TwoArgumentCache):
    def __init__(self) -> None:
        super().__init__()
        self.ttls: list[float | None] = []

    def set(self, key: str, value: str, *, ttl: float | None = None) -> None:  # type: ignore[override]
        self.ttls.append(ttl)
        super().set(key, value)


class TestStoreIfMissing:
    def test_a_ttl_reaches_a_backend_that_takes_it_only_by_keyword(self):
        """The ttl is passed by keyword, as every other Citry caller passes it."""
        cache = _KeywordTtlCache()
        _store_if_missing(_Owner(), cache, "expiring", lambda: "v", ttl=60)
        assert cache.ttls == [60]

    def test_a_write_without_a_ttl_calls_set_with_two_arguments(self):
        owner = _Owner()
        cache = _TwoArgumentCache()
        # A backend that leaves out the optional `ttl` keeps working for the entries that never expire.
        _store_if_missing(owner, cache, "k", lambda: "v")
        assert cache.values == {"k": "v"}

    def test_a_ttl_reaches_the_backend(self):
        owner = _Owner()
        cache = _TtlRecordingCache()
        _store_if_missing(owner, cache, "kept", lambda: "v")
        _store_if_missing(owner, cache, "expiring", lambda: "v", ttl=60)
        assert cache.ttls == [None, 60]

    def test_an_entry_the_backend_holds_is_not_written_again(self):
        owner = _Owner()
        cache = _TtlRecordingCache()
        cache.values["k"] = "already there"
        calls: list[int] = []
        _store_if_missing(owner, cache, "k", lambda: calls.append(1) or "v", ttl=60)
        # The value is built only when the entry must be written.
        assert calls == []
        assert cache.ttls == []
