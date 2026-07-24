"""
Tests for external Sphinx inventory parsing and the offline-safe fetch cache.

These never touch the network: the parser is fed synthetic in-memory
inventories, and the download path is exercised with a monkeypatched
``urlopen`` so a build (and this suite) works with no outbound access.
"""

from __future__ import annotations

import zlib

from docs_site._internal import inventory
from docs_site._internal.inventory import external_inventory, parse_objects_inv

BASE = "https://docs.python.org/3.13/"


def _make_inventory(lines: list[str], *, first_line: bytes = b"# Sphinx inventory version 2") -> bytes:
    """Build a minimal but valid Sphinx v2 ``objects.inv`` from payload lines."""
    header = (
        b"\n".join(
            [
                first_line,
                b"# Project: Test",
                b"# Version: 1.0",
                b"# The remainder of this file is compressed using zlib.",
            ],
        )
        + b"\n"
    )
    payload = zlib.compress(("\n".join(lines) + "\n").encode("utf-8"), 9)
    return header + payload


def test_parse_maps_names_to_urls_and_expands_dollar() -> None:
    data = _make_inventory(
        [
            "os.path py:module 0 library/os.path.html#module-os.path -",
            # The "$" in the URI is shorthand for the object's own name.
            "collections.abc.Mapping py:class 1 library/collections.abc.html#$ Mapping",
            "typing.Any py:data 1 library/typing.html#$ typing.Any",
        ],
    )
    assert parse_objects_inv(data, BASE) == {
        "os.path": "https://docs.python.org/3.13/library/os.path.html#module-os.path",
        "collections.abc.Mapping": "https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping",
        "typing.Any": "https://docs.python.org/3.13/library/typing.html#typing.Any",
    }


def test_parse_trailing_slash_on_base_is_normalized() -> None:
    # A base without the trailing slash must still join cleanly (no doubled/missing "/").
    data = _make_inventory(["os.path py:module 0 library/os.path.html -"])
    assert parse_objects_inv(data, "https://docs.python.org/3.13") == {
        "os.path": "https://docs.python.org/3.13/library/os.path.html",
    }


def test_parse_empty_bytes_yields_empty_map() -> None:
    assert parse_objects_inv(b"", BASE) == {}


def test_parse_wrong_header_yields_empty_map() -> None:
    assert parse_objects_inv(b"not a sphinx inventory at all", BASE) == {}
    assert parse_objects_inv(_make_inventory(["x py:obj 0 x -"], first_line=b"# nope"), BASE) == {}


def test_parse_corrupt_zlib_payload_yields_empty_map() -> None:
    # Valid four-line header, but the compressed section is garbage, not zlib data.
    corrupt = (
        b"# Sphinx inventory version 2\n"
        b"# Project: Test\n"
        b"# Version: 1.0\n"
        b"# The remainder of this file is compressed using zlib.\n"
        b"\x00\x01\x02 not zlib"
    )
    assert parse_objects_inv(corrupt, BASE) == {}


class _FakeResponse:
    """Stand-in for the object ``urllib.request.urlopen`` returns as a context manager."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def test_load_one_fetches_parses_then_caches(monkeypatch, tmp_path) -> None:
    # Isolate the on-disk cache so we never read a real prior download.
    monkeypatch.setattr(inventory, "_cache_dir", lambda: tmp_path)
    inv_bytes = _make_inventory(["os.path py:module 0 library/os.path.html#module-os.path -"])
    calls: list[str] = []

    def fake_urlopen(url, timeout):
        # The fetch is bounded so an unreachable host can never hang the build.
        assert timeout == 15
        calls.append(url)
        return _FakeResponse(inv_bytes)

    monkeypatch.setattr(inventory.urllib.request, "urlopen", fake_urlopen)

    url = BASE + "objects.inv"
    expected = {"os.path": "https://docs.python.org/3.13/library/os.path.html#module-os.path"}

    assert inventory._load_one(url, BASE) == expected
    assert calls == [url]  # fetched exactly once

    # The second call is served from the on-disk cache, with no further fetch.
    assert inventory._load_one(url, BASE) == expected
    assert calls == [url]


def test_load_one_returns_empty_map_on_fetch_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(inventory, "_cache_dir", lambda: tmp_path)

    def boom(*_args, **_kwargs):
        raise OSError("no network")

    monkeypatch.setattr(inventory.urllib.request, "urlopen", boom)
    assert inventory._load_one(BASE + "objects.inv", BASE) == {}


def test_external_inventory_merges_fetched_names(monkeypatch, tmp_path) -> None:
    external_inventory.cache_clear()
    monkeypatch.setattr(inventory, "_cache_dir", lambda: tmp_path)
    inv_bytes = _make_inventory(
        [
            "os.path py:module 0 library/os.path.html#module-os.path -",
            "typing.Any py:data 1 library/typing.html#$ typing.Any",
        ],
    )
    monkeypatch.setattr(inventory.urllib.request, "urlopen", lambda *_a, **_k: _FakeResponse(inv_bytes))
    try:
        result = external_inventory()
        assert result["os.path"] == "https://docs.python.org/3.13/library/os.path.html#module-os.path"
        assert result["typing.Any"] == "https://docs.python.org/3.13/library/typing.html#typing.Any"
    finally:
        external_inventory.cache_clear()
