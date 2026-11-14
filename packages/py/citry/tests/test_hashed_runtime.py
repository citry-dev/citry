"""
Tests for the browser runtimes that pages link by a URL carrying their hash.

A page links ``citry.<sha256>.js`` and ``ext/i18n/runtime.<sha256>.js``, where
``<sha256>`` is the SHA-256 of the file. These tests cover what the handlers
answer for a hash, how the bytes reach other workers through the shared cache
(``CitrySettings.cache``), and the public ``Citry.runtime_url()``. The headers
on the wire, the stable aliases through the adapters, and the start script
live in ``test_asset_cors.py`` and ``test_vue_document_configuration.py``.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

import citry as citry_package
from citry import Citry, Component
from citry import cache as citry_cache
from citry._hashed_runtime import RUNTIME_CACHE_TTL_SECONDS, HashedRuntime, is_content_digest
from citry._owned_resource import IMMUTABLE_CACHE_CONTROL
from citry.ext.dependencies.routes import SHARED_RUNTIME
from citry.ext.i18n.emission import I18N_RUNTIME
from citry.util.routing import RouteRequest, RouteResponse, match_route

PACKAGE = Path(citry_package.__file__).parent
THIRTY_DAYS = 30 * 24 * 60 * 60
# A page on another origin (a sandboxed frame, or one that loads the runtime from a CDN)
# loads it with `crossorigin`. Without this header its console shows a CORS error that
# hides the 404. No browser or CDN may store a miss.
MISS_HEADERS = (("Access-Control-Allow-Origin", "*"), ("Cache-Control", "no-store"))

# Each runtime with the files it is read from, the stable URL that serves the
# same bytes, and the shared-cache key prefix other versions agree on.
RUNTIMES = {
    "shared": (SHARED_RUNTIME, PACKAGE / "_vue" / "runtime.js", "citry.js", "citry:runtime"),
    "i18n": (
        I18N_RUNTIME,
        PACKAGE / "ext" / "i18n" / "client" / "vue-plugin.source.js",
        "ext/i18n/runtime.js",
        "citry:i18n-runtime",
    ),
}


class _RecordingCache:
    """A cache backend that remembers each ``ttl`` it was given, and every key it was asked for or lost."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, float | None] = {}
        self.sets: list[str] = []
        self.gets: list[str] = []
        self.deleted: list[str] = []

    def get(self, key: str) -> str | None:
        self.gets.append(key)
        return self.values.get(key)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.sets.append(key)
        self.values[key] = value
        self.ttls[key] = ttl

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.values.pop(key, None)
        self.ttls.pop(key, None)

    def has(self, key: str) -> bool:
        return key in self.values


@pytest.fixture(params=sorted(RUNTIMES))
def kind(request: pytest.FixtureRequest) -> str:
    """Run a test once for the shared runtime and once for the i18n runtime."""
    return request.param


def _engine(*, cache: object = None) -> Citry:
    """An engine with the web integration mounted and i18n on, so both hashed routes exist."""
    engine = Citry(
        autodiscover=False,
        cache=cache,  # type: ignore[arg-type]
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    engine.set_mounted_prefix("/citry")
    return engine


def _page(engine: Citry) -> type[Component]:
    """A page with an event button and a client i18n root, so it links both runtimes."""

    class Page(Component):
        citry = engine
        template = """
            <c-i18n c-client="True" tag="main">
                <output v-text="$i18n.tr('client-title')"></output>
                <button @click="count += 1">add</button>
            </c-i18n>
        """
        messages = "client-title = Client title"

    return Page


def _get(engine: Citry, path: str) -> RouteResponse:
    """Run the route handler for ``path`` the way an adapter does."""
    matched = match_route(engine.urls, path)
    assert matched is not None, path
    return matched.route.handler(RouteRequest(path=path), **matched.params)


def _header_values(response: RouteResponse, name: str) -> list[str]:
    return [value for key, value in response.headers if key.lower() == name.lower()]


class TestHashedUrl:
    def test_the_hash_is_the_sha256_of_the_file(self, kind: str) -> None:
        runtime, source, _stable, _prefix = RUNTIMES[kind]
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert runtime.digest == digest
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        assert runtime.hashed_path == f"{runtime.hashed_stem}.{digest}.js"

    def test_the_hashed_route_serves_the_file_for_a_year(self, kind: str) -> None:
        runtime, source, _stable, _prefix = RUNTIMES[kind]
        response = _get(_engine(), runtime.hashed_path)
        assert response.status == 200
        assert response.body == source.read_bytes()
        assert response.content_type == "text/javascript; charset=utf-8"
        # One Cache-Control line, so a proxy never has two policies to choose between.
        assert _header_values(response, "Cache-Control") == ["public, max-age=31536000, immutable"]
        assert IMMUTABLE_CACHE_CONTROL == "public, max-age=31536000, immutable"
        # The browser needs this to check `integrity` in a frame with no origin.
        assert _header_values(response, "Access-Control-Allow-Origin") == ["*"]

    def test_the_stable_url_serves_the_same_bytes_uncached(self, kind: str) -> None:
        runtime, source, stable, _prefix = RUNTIMES[kind]
        response = _get(_engine(), stable)
        assert response.status == 200
        assert response.body == source.read_bytes() == _get(_engine(), runtime.hashed_path).body
        assert _header_values(response, "Cache-Control") == ["no-store"]
        assert _header_values(response, "Access-Control-Allow-Origin") == ["*"]

    def test_the_events_alias_serves_the_shared_runtime(self) -> None:
        response = _get(_engine(), "ext/events/runtime.js")
        assert response.status == 200
        assert response.body == _get(_engine(), SHARED_RUNTIME.hashed_path).body
        assert _header_values(response, "Cache-Control") == ["no-store"]

    @pytest.mark.parametrize(
        "digest",
        [
            "A" * 64,
            ("0123456789ABCDEF" * 4),
            "a" * 63,
            "a" * 65,
            "g" * 64,
            "a" * 63 + "-",
            "",
        ],
        ids=["upper", "mixed-upper", "short", "long", "non-hex", "dash", "empty"],
    )
    def test_a_malformed_digest_gets_an_empty_404_that_nothing_keeps(self, kind: str, digest: str) -> None:
        runtime, _source, _stable, _prefix = RUNTIMES[kind]
        engine = _engine(cache=_RecordingCache())
        response = runtime.serve_hashed(engine, digest)
        assert response.status == 404
        assert response.body == b""
        assert response.headers == MISS_HEADERS
        # The shape is checked before a cache key is built from request data.
        assert engine.cache.gets == []  # type: ignore[attr-defined]

    def test_a_malformed_digest_through_the_route_is_a_404_that_nothing_keeps(self, kind: str) -> None:
        runtime, _source, _stable, _prefix = RUNTIMES[kind]
        engine = _engine()
        for digest in ("A" * 64, "a" * 63, "a" * 65, "g" * 64):
            response = _get(engine, f"{runtime.hashed_stem}.{digest}.js")
            assert response.status == 404, digest
            assert response.body == b"", digest
            assert response.headers == MISS_HEADERS, digest

    @pytest.mark.parametrize("suffix", [".x", ".js", "/x", ".a.b"])
    def test_a_path_with_an_extra_dot_matches_no_route(self, kind: str, suffix: str) -> None:
        runtime, _source, _stable, _prefix = RUNTIMES[kind]
        assert match_route(_engine().urls, f"{runtime.hashed_stem}.{'a' * 64}{suffix}.js") is None

    def test_an_unknown_well_formed_digest_is_a_404_that_nothing_keeps(self, kind: str) -> None:
        runtime, _source, _stable, _prefix = RUNTIMES[kind]
        response = _get(_engine(), f"{runtime.hashed_stem}.{'0' * 64}.js")
        assert response.status == 404
        assert response.body == b""
        assert response.headers == MISS_HEADERS

    def test_a_digest_shape_check_accepts_only_64_lowercase_hex_characters(self) -> None:
        assert is_content_digest("0123456789abcdef" * 4)
        for value in ("A" * 64, "a" * 63, "a" * 65, "g" * 64, "", " " + "a" * 63, "a" * 64 + "\n", None, 5, b"a" * 64):
            assert not is_content_digest(value), value

    def test_a_runtime_is_read_once_per_process_and_not_before_it_is_needed(self) -> None:
        reads: list[int] = []

        def load() -> str:
            reads.append(1)
            return "console.log('x');"

        runtime = HashedRuntime(stable_path="x.js", hashed_stem="x", cache_namespace="citry:x", load=load)
        # The route table is built when the engine starts, so the file is read when a URL first needs its hash.
        assert reads == []
        assert runtime.digest == hashlib.sha256(b"console.log('x');").hexdigest()
        assert runtime.hashed_path == f"x.{runtime.digest}.js"
        assert runtime.route_path == "x.{digest}.js"
        assert runtime.content == "console.log('x');"
        assert reads == [1]


class TestSharedCache:
    def test_a_mounted_page_writes_each_runtime_for_30_days(self) -> None:
        cache = _RecordingCache()
        engine = _engine(cache=cache)
        _page(engine)().render().serialize()
        assert RUNTIME_CACHE_TTL_SECONDS == THIRTY_DAYS
        for kind_name, (runtime, _source, _stable, prefix) in RUNTIMES.items():
            key = f"{prefix}:{runtime.digest}"
            assert cache.values[key] == runtime.content, kind_name
            assert cache.ttls[key] == THIRTY_DAYS, kind_name

    def test_runtime_url_writes_the_runtime_for_a_page_written_by_hand(self) -> None:
        cache = _RecordingCache()
        engine = _engine(cache=cache)
        assert engine.runtime_url() == f"/citry/{SHARED_RUNTIME.hashed_path}"
        assert cache.ttls == {f"citry:runtime:{SHARED_RUNTIME.digest}": THIRTY_DAYS}

    def test_a_second_render_does_not_send_the_runtime_again(self) -> None:
        cache = _RecordingCache()
        engine = _engine(cache=cache)
        page = _page(engine)
        page().render().serialize()
        first = [key for key in cache.sets if "runtime" in key]
        page().render().serialize()
        # The engine remembers what it stored, so a busy page does not ask the backend on every render.
        assert [key for key in cache.sets if "runtime" in key] == first
        assert len(first) == 2

    def test_a_runtime_the_backend_dropped_is_written_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(citry_cache, "_STORED_KEY_RECHECK_SECONDS", 0.0)
        cache = _RecordingCache()
        engine = _engine(cache=cache)
        key = f"citry:runtime:{SHARED_RUNTIME.digest}"
        engine.runtime_url()
        cache.delete(key)
        engine.runtime_url()
        assert cache.ttls[key] == THIRTY_DAYS
        assert cache.sets.count(key) == 2

    def test_nothing_is_written_without_a_configured_cache(self) -> None:
        engine = _engine()
        assert engine.settings.cache is None
        _page(engine)().render().serialize()
        # The engine's own in-memory cache holds no entry that no other worker could read.
        for runtime, _source, _stable, prefix in RUNTIMES.values():
            assert not engine.cache.has(f"{prefix}:{runtime.digest}")
        # With no shared copy, a hash this process lacks is a miss.
        assert _get(engine, f"citry.{'0' * 64}.js").status == 404

    def test_another_worker_serves_a_version_it_does_not_hold(self, kind: str) -> None:
        runtime, _source, _stable, prefix = RUNTIMES[kind]
        cache = _RecordingCache()
        previous_version = "console.log('the runtime another version rendered');\n"
        digest = hashlib.sha256(previous_version.encode()).hexdigest()
        assert digest != runtime.digest
        # The worker that rendered the page wrote this entry before it sent the page.
        cache.set(f"{prefix}:{digest}", previous_version, THIRTY_DAYS)

        response = _get(_engine(cache=cache), f"{runtime.hashed_stem}.{digest}.js")

        assert response.status == 200
        assert response.content == previous_version
        assert _header_values(response, "Cache-Control") == ["public, max-age=31536000, immutable"]
        assert _header_values(response, "Access-Control-Allow-Origin") == ["*"]

    def test_a_stored_copy_whose_bytes_do_not_match_its_hash_is_a_miss_and_is_removed(self, kind: str) -> None:
        runtime, _source, _stable, prefix = RUNTIMES[kind]
        cache = _RecordingCache()
        digest = hashlib.sha256(b"what the URL names").hexdigest()
        key = f"{prefix}:{digest}"
        cache.set(key, "console.log('something else');", THIRTY_DAYS)

        response = _get(_engine(cache=cache), f"{runtime.hashed_stem}.{digest}.js")

        # Serving these bytes would run unknown code under a hash that promises other bytes.
        assert response.status == 404
        assert response.body == b""
        assert response.headers == MISS_HEADERS
        assert cache.deleted == [key]
        assert not cache.has(key)

    def test_a_copy_under_the_other_runtimes_key_is_not_served(self) -> None:
        cache = _RecordingCache()
        text = "console.log('shared runtime of another version');\n"
        digest = hashlib.sha256(text.encode()).hexdigest()
        cache.set(f"citry:runtime:{digest}", text, THIRTY_DAYS)
        engine = _engine(cache=cache)
        assert _get(engine, f"citry.{digest}.js").status == 200
        # Each runtime reads only its own key prefix.
        assert _get(engine, f"ext/i18n/runtime.{digest}.js").status == 404

    def test_a_lookup_that_finds_nothing_is_a_404(self, kind: str) -> None:
        runtime, _source, _stable, prefix = RUNTIMES[kind]
        digest = "1" * 64
        cache = _RecordingCache()
        response = _get(_engine(cache=cache), f"{runtime.hashed_stem}.{digest}.js")
        assert response.status == 404
        assert cache.gets == [f"{prefix}:{digest}"]
        assert cache.deleted == []


class TestRuntimeUrl:
    def test_it_is_the_url_a_mounted_document_links(self) -> None:
        engine = _engine()
        html = _page(engine)().render().serialize()
        linked = re.findall(r'src="(/citry/citry\.[^"]*)"', html)
        assert linked == [engine.runtime_url()]
        assert engine.runtime_url() == f"/citry/{SHARED_RUNTIME.hashed_path}"

    def test_it_follows_the_mount_prefix(self) -> None:
        engine = Citry(autodiscover=False)
        engine.set_mounted_prefix("/static/c")
        assert engine.runtime_url() == f"/static/c/{SHARED_RUNTIME.hashed_path}"

    def test_it_raises_when_no_web_integration_is_mounted(self) -> None:
        with pytest.raises(RuntimeError, match="no web integration is mounted"):
            Citry(autodiscover=False).runtime_url()

    def test_the_url_it_returns_is_served(self) -> None:
        engine = _engine()
        response = _get(engine, engine.runtime_url().removeprefix("/citry/"))
        assert response.status == 200
        assert response.body == SHARED_RUNTIME.content.encode()
