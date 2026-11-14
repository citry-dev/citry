"""
Serve Citry's browser runtimes at URLs that carry a hash of their bytes.

A page links the shared runtime as ``<prefix>/citry.<sha256>.js`` and the
i18n runtime as ``<prefix>/ext/i18n/runtime.<sha256>.js``, where
``<sha256>`` is the SHA-256 of the file as 64 lowercase hex characters. The
URL changes whenever the file does, so the browser may keep the file for a
year, and a page always loads the runtime it was rendered for. Each runtime
also keeps a stable URL (``citry.js``, ``ext/i18n/runtime.js``) that serves the
current bytes with ``no-store``, for pages rendered by older versions and for
apps that link the runtime by hand.

During a rolling deploy, a worker can be asked for a hash that another
version rendered. When the app sets ``CitrySettings.cache``, every process
that links a hashed URL writes the bytes to that shared cache for 30 days, so
any worker can answer. Design: ``docs/design/runtime_hashed_urls.md``.
"""

from __future__ import annotations

import re
from functools import cached_property
from hashlib import sha256
from typing import TYPE_CHECKING

from citry._owned_resource import JAVASCRIPT_CONTENT_TYPE, PUBLIC_ASSET_CORS_HEADERS, _OwnedResource
from citry.cache import _forget_stored_key, _store_if_missing
from citry.util.routing import RouteResponse

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.citry import Citry

_CONTENT_DIGEST_RE = re.compile(r"[0-9a-f]{64}")

RUNTIME_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
"""
How long the shared cache keeps a runtime version after a process writes it.

The 30 days count from the write, not from the last time a page linked the
runtime. A process that still links the same hash writes it again on its
first render after the entry expires, once the recheck interval
(``_STORED_KEY_RECHECK_SECONDS``) has passed. So a version stays in the cache
while some worker links it, apart from short gaps after each expiry. The
value is fixed in code, so the cache never receives an invalid expiry.
"""

# A miss may succeed on another worker or after a deploy, so neither the
# browser nor a CDN may keep it.
NO_STORE_HEADERS: tuple[tuple[str, str], ...] = (("Cache-Control", "no-store"),)


def is_content_digest(value: object) -> bool:
    """Return whether ``value`` is a SHA-256 digest in the form Citry puts in URLs: 64 lowercase hex characters."""
    return type(value) is str and _CONTENT_DIGEST_RE.fullmatch(value) is not None


def not_found() -> RouteResponse:
    """Answer a request for a file this worker does not hold, with an empty body nobody may store."""
    # A page that loads the runtime with `crossorigin` (Citry adds it next to
    # `integrity`) would see a 404 without this header as a CORS failure in
    # the browser console, which hides the real cause. The body is empty and depends only on the URL, so the
    # header exposes nothing a visitor cannot already see.
    return RouteResponse(
        "",
        status=404,
        content_type="text/plain",
        headers=(*PUBLIC_ASSET_CORS_HEADERS, *NO_STORE_HEADERS),
    )


class HashedRuntime:
    """
    One browser runtime file, served at a stable URL and at a URL named by its hash.

    The bytes and their digest are read once per process, so the stable URL,
    the hashed URL, and every page this process renders name the same file.
    """

    def __init__(self, *, stable_path: str, hashed_stem: str, cache_namespace: str, load: Callable[[], str]) -> None:
        # `hashed_stem` is the stable path without its `.js`, so both URLs sit side by side.
        self.stable_path = stable_path
        self.hashed_stem = hashed_stem
        self.cache_namespace = cache_namespace
        self._load = load

    @cached_property
    def content(self) -> str:
        """Return the runtime's source, read once per process."""
        return self._load()

    @cached_property
    def digest(self) -> str:
        """Return the SHA-256 of the bytes the routes send, as 64 lowercase hex characters."""
        return sha256(self.content.encode()).hexdigest()

    @property
    def route_path(self) -> str:
        """Return the route pattern of the hashed URL, such as ``citry.{digest}.js``."""
        return f"{self.hashed_stem}.{{digest}}.js"

    @property
    def hashed_path(self) -> str:
        """Return this process's hashed route path, such as ``citry.<sha256>.js``."""
        return f"{self.hashed_stem}.{self.digest}.js"

    def cache_key(self, digest: str) -> str:
        """Return the shared-cache key that holds the runtime whose SHA-256 is ``digest``."""
        return f"{self.cache_namespace}:{digest}"

    def url(self, citry: Citry) -> str:
        """
        Return the hashed URL a page links, and make sure other workers can serve it.

        Raises ``RuntimeError`` when no web integration is mounted, as
        ``Citry.build_url`` does.
        """
        url = citry.build_url(self.hashed_path)
        # The page that links this URL may reach another worker, perhaps one
        # on another version. Writing the bytes before the page is sent lets
        # that worker answer from the shared cache. Without a configured
        # cache, nothing else could read the entry, so nothing is written.
        if citry.settings.cache is not None:
            _store_if_missing(
                citry,
                citry.cache,
                self.cache_key(self.digest),
                lambda: self.content,
                ttl=RUNTIME_CACHE_TTL_SECONDS,
            )
        return url

    def resource(self, citry: Citry) -> _OwnedResource:
        """
        Return the runtime as a page links it.

        A mounted engine links the hashed URL. Without a mount the page
        inlines the runtime, and the relative stable path only names the
        resource for the output checks.
        """
        url = self.url(citry) if citry.mounted_prefix is not None else self.stable_path
        return _OwnedResource(url=url, content=self.content, content_type=JAVASCRIPT_CONTENT_TYPE)

    def serve_stable(self) -> RouteResponse:
        """Answer the stable URL with the current bytes, which nobody may store."""
        # The stable URL keeps its address across upgrades. A copy reused on
        # back/forward navigation could pair a page with the wrong runtime
        # and fail its integrity check, so the browser must fetch it each time.
        return _OwnedResource(
            url="",
            content=self.content,
            content_type=JAVASCRIPT_CONTENT_TYPE,
            headers=NO_STORE_HEADERS,
        ).response()

    def serve_hashed(self, citry: Citry, digest: str) -> RouteResponse:
        """Answer the hashed URL: this process's bytes, a copy another worker stored, or ``404``."""
        # Check the shape before building a cache key from request data.
        if not is_content_digest(digest):
            return not_found()
        if digest == self.digest:
            content = self.content
        else:
            stored = self._stored(citry, digest)
            if stored is None:
                return not_found()
            content = stored
        # The URL names these exact bytes, so the browser may keep them for a year.
        return _OwnedResource(url="", content=content, content_type=JAVASCRIPT_CONTENT_TYPE).immutable_response()

    def _stored(self, citry: Citry, digest: str) -> str | None:
        """Return a runtime another worker wrote to the shared cache, only when its bytes match ``digest``."""
        if citry.settings.cache is None:
            return None
        key = self.cache_key(digest)
        content = citry.cache.get(key)
        if content is None:
            return None
        # The shared backend is outside this process's control. Serving bytes
        # under a hash they do not match would run unknown code wherever the
        # page has no integrity check, so a mismatch is a miss. Deleting the
        # entry lets the next process that links this hash write it again.
        if sha256(content.encode()).hexdigest() != digest:
            citry.cache.delete(key)
            _forget_stored_key(citry, key)
            return None
        return content


__all__ = [
    "NO_STORE_HEADERS",
    "RUNTIME_CACHE_TTL_SECONDS",
    "HashedRuntime",
    "is_content_digest",
    "not_found",
]
