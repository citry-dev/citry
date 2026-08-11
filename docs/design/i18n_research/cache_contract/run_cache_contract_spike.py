from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType, MethodType
from typing import TYPE_CHECKING, Any, Literal, cast
from weakref import WeakSet

from citry import Citry, Component, Extension, InMemoryCache
from citry.cache import _normalize_ttl
from citry.constness import const_value
from citry.ext.cache.extension import CacheExtension, _CacheHit
from citry.ext.cache.keys import _build_component_cache_key, _build_fragment_cache_key, _validate_version
from citry.util.misc import to_dict

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.citry_context import CitryContext


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CACHE_EXTENSION = REPO / "packages/py/citry/citry/ext/cache/extension.py"
CACHE_KEYS = REPO / "packages/py/citry/citry/ext/cache/keys.py"
CACHE_DESIGN = REPO / "docs/design/caching.md"
I18N_DESIGN = REPO / "docs/design/i18n.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_always_on_checks() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    require(
        not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)],
        "the evidence harness must not use optimization-sensitive assert statements",
    )


@dataclass(frozen=True, slots=True)
class LocaleCacheContext:
    locale: str
    fallback_locales: tuple[str, ...]
    direction: Literal["ltr", "rtl"]
    time_zone: str | None
    tzdb_revision: str
    catalog_revision: str
    formats_revision: str


class I18nCacheToken:
    """One sealed token that only the active i18n extension can mint."""

    __slots__ = ("__weakref__", "_context", "_issuer")

    def __init__(self) -> None:
        raise TypeError("I18nCacheToken values are supplied by Citry Cache.")

    @classmethod
    def _mint(cls, issuer: Phase0I18nExtension, context: LocaleCacheContext) -> I18nCacheToken:
        token = object.__new__(cls)
        token._issuer = issuer
        token._context = context
        return token


class CacheTokenError(ValueError):
    pass


class Phase0I18nExtension(Extension):
    name = "i18n"
    render_cache_mode = "stateless"
    render_cache_version = 1

    def __init__(self) -> None:
        self._active: ContextVar[LocaleCacheContext | None] = ContextVar(
            "citry_i18n_phase0_cache_context",
            default=None,
        )
        self._issued: WeakSet[I18nCacheToken] = WeakSet()

    @contextmanager
    def bind(self, context: LocaleCacheContext) -> Iterator[None]:
        token = self._active.set(context)
        try:
            yield
        finally:
            self._active.reset(token)

    def current_context(self) -> LocaleCacheContext | None:
        return self._active.get()

    def current_token(self) -> I18nCacheToken | None:
        context = self.current_context()
        if context is None:
            return None
        token = I18nCacheToken._mint(self, context)
        self._issued.add(token)
        return token

    def encode_token(self, token: I18nCacheToken) -> tuple[object, ...]:
        context = self.current_context()
        if (
            type(token) is not I18nCacheToken
            or token not in self._issued
            or token._issuer is not self
            or token._context is not context
        ):
            raise CacheTokenError("an i18n cache token is forged, stale, or belongs to another engine")
        require(context is not None, "a current token existed without a current context")
        return (
            "citry-i18n-cache-token",
            1,
            context.locale,
            context.fallback_locales,
            context.direction,
            context.time_zone,
            context.tzdb_revision,
            context.catalog_revision,
            context.formats_revision,
        )


class RecordingCache(InMemoryCache):
    def __init__(self) -> None:
        super().__init__()
        self.gets: list[str] = []
        self.sets: list[str] = []

    def get(self, key: str) -> str | None:
        self.gets.append(key)
        return super().get(key)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.sets.append(key)
        super().set(key, value, ttl)


class CacheGuard:
    """Research adapter that runs the proposed i18n proof before Cache reads its backend."""

    def __init__(self, cache: CacheExtension, i18n: Phase0I18nExtension) -> None:
        self.cache = cache
        self.i18n = i18n
        self.original_component = cache._lookup_component
        self.original_fragment = cache._lookup_fragment
        self.fragment_modes: dict[str, Literal["dependent", "independent"]] = {}

    def install(self) -> None:
        self.cache._lookup_component = MethodType(self._lookup_component, self.cache)
        self.cache._lookup_fragment = MethodType(self._lookup_fragment, self.cache)

    def _encode_variation(self, value: object, current: I18nCacheToken, state: dict[str, bool]) -> object:
        if isinstance(value, I18nCacheToken):
            encoded = self.i18n.encode_token(value)
            if value is current:
                state["found_current"] = True
            return encoded
        if type(value) is dict:
            return {key: self._encode_variation(item, current, state) for key, item in value.items()}
        if type(value) is list:
            return [self._encode_variation(item, current, state) for item in value]
        if type(value) is tuple:
            return tuple(self._encode_variation(item, current, state) for item in value)
        return value

    def _dependent_variation(self, value: object, token: I18nCacheToken) -> object | None:
        state = {"found_current": False}
        encoded = self._encode_variation(value, token, state)
        return encoded if state["found_current"] else None

    def _lookup_component(
        self,
        cache: CacheExtension,
        component: Component,
        context: CitryContext,
    ) -> object:
        if cache._is_fragment_boundary(component):
            return cache._lookup_fragment(component)
        mode = getattr(type(component), "phase0_i18n_cache", None)
        if mode != "dependent":
            return self.original_component(component, context)
        config = cast("Any", getattr(component, cache.name))
        if not config.enabled:
            return None
        token = self.i18n.current_token()
        if token is None:
            return None
        kwargs = MappingProxyType(dict(to_dict(component.kwargs)))
        slots = MappingProxyType(dict(to_dict(component.slots)))
        vary_method = getattr(config, "vary", None)
        if vary_method is None:
            return None
        variation = self._dependent_variation(vary_method(kwargs, slots, i18n=token), token)
        if variation is None:
            return None
        ttl = _normalize_ttl(config.ttl, source="component Cache ttl")
        if ttl == 0:
            return None
        key_context = cache._key_context()
        key = _build_component_cache_key(
            key_context,
            type(component).class_id,
            vary=variation,
            version=config.version,
        )
        decision = cache._lookup_physical_key(
            key,
            ttl=ttl,
            max_entry_bytes=cache._defaults.max_entry_bytes,
            revision=key_context.revision,
        )
        if not isinstance(decision, _CacheHit):
            cache._diagnose_lookup(decision, component=component)
        return decision

    def _lookup_fragment(self, cache: CacheExtension, component: Component) -> object:
        controls = dict(to_dict(component.kwargs))
        key = const_value(controls["key"])
        mode = self.fragment_modes.get(key)
        if mode != "dependent":
            return self.original_fragment(component)
        token = self.i18n.current_token()
        if token is None:
            return None
        ttl = _normalize_ttl(const_value(controls["ttl"]), source="<c-cache> ttl")
        enabled = const_value(controls["enabled"])
        version = const_value(controls["version"])
        _validate_version(version)
        if enabled is not True or ttl == 0:
            return None
        variation = self._dependent_variation(
            {"author": const_value(controls["vary"]), "i18n": token},
            token,
        )
        require(variation is not None, "the fragment adapter lost its injected token")
        key_context = cache._key_context()
        physical_key = _build_fragment_cache_key(
            key_context,
            cast("str", key),
            vary=variation,
            version=version,
        )
        decision = cache._lookup_physical_key(
            physical_key,
            ttl=ttl,
            max_entry_bytes=cache._defaults.max_entry_bytes,
            revision=key_context.revision,
            kind="fragment",
        )
        if not isinstance(decision, _CacheHit):
            cache._diagnose_lookup(decision, component=None)
        return decision


def context(
    locale: str,
    *,
    direction: Literal["ltr", "rtl"] = "ltr",
    time_zone: str | None = "UTC",
    fallback_locales: tuple[str, ...] | None = None,
    tzdb_revision: str = "tzdata-2026.3",
    catalog_revision: str = "catalog-1",
    formats_revision: str = "formats-1",
) -> LocaleCacheContext:
    return LocaleCacheContext(
        locale=locale,
        fallback_locales=fallback_locales or (locale.split("-")[0], "en-US"),
        direction=direction,
        time_zone=time_zone,
        tzdb_revision=tzdb_revision,
        catalog_revision=catalog_revision,
        formats_revision=formats_revision,
    )


def render_checks() -> dict[str, Any]:
    backend = RecordingCache()
    app = Citry(cache=backend, extensions=[Phase0I18nExtension])
    i18n = cast("Phase0I18nExtension", app.extensions.get_extension("i18n"))
    cache = cast("CacheExtension", app.extensions.get_extension("cache"))
    guard = CacheGuard(cache, i18n)
    guard.fragment_modes.update({"localized-fragment": "dependent", "shared-fragment": "independent"})
    guard.install()

    localized_calls: list[str] = []

    class Localized(Component):
        citry = app
        phase0_i18n_cache = "dependent"

        class Cache:
            enabled = True

            def vary(self, kwargs: Any, _slots: Any, *, i18n: I18nCacheToken) -> dict[str, Any]:
                return {"i18n": i18n, "kwargs": dict(kwargs)}

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, str]:
            active = i18n.current_context()
            require(active is not None, "localized render lost its context")
            localized_calls.append(active.locale)
            return {"locale": active.locale}

        template = """
          <p class="localized">{{ locale }}</p>
        """

    en = context("en-US")
    ar = context("ar-EG", direction="rtl")
    with i18n.bind(en):
        en_first = str(Localized())
        en_second = str(Localized())
    with i18n.bind(ar):
        ar_first = str(Localized())
    with i18n.bind(context("en-US")):
        en_third = str(Localized())
    require(localized_calls == ["en-US", "ar-EG"], f"localized cache calls changed: {localized_calls!r}")
    require(all("en-US" in output for output in (en_first, en_second, en_third)), "English replay changed")
    require("ar-EG" in ar_first, "Arabic cache variation reused English")

    class MissingToken(Component):
        citry = app
        phase0_i18n_cache = "dependent"
        calls = 0

        class Cache:
            enabled = True

            def vary(self, kwargs: Any, slots: Any, *, i18n: I18nCacheToken) -> dict[str, Any]:  # noqa: ARG002
                return {"missing": True}

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            type(self).calls += 1
            return {}

        template = """
          missing
        """

    reads_before_missing = len(backend.gets)
    sets_before_missing = len(backend.sets)
    with i18n.bind(en):
        str(MissingToken())
        str(MissingToken())
    require(MissingToken.calls == 2, "a missing-token component unexpectedly replayed")
    require(len(backend.gets) == reads_before_missing, "a missing-token component read the backend")
    require(len(backend.sets) == sets_before_missing, "a missing-token component published an artifact")

    class UnboundDependent(Component):
        citry = app
        phase0_i18n_cache = "dependent"
        calls = 0

        class Cache:
            enabled = True

            def vary(self, _kwargs: Any, _slots: Any, *, i18n: I18nCacheToken) -> dict[str, Any]:
                return {"i18n": i18n}

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            type(self).calls += 1
            return {}

        template = """
          unbound
        """

    reads_before_unbound = len(backend.gets)
    str(UnboundDependent())
    require(UnboundDependent.calls == 1, "an unbound component did not render")
    require(len(backend.gets) == reads_before_unbound, "an unbound dependent component read the backend")

    independent_calls = 0

    class Independent(Component):
        citry = app
        phase0_i18n_cache = "independent"

        class Cache:
            enabled = True

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            nonlocal independent_calls
            independent_calls += 1
            return {}

        template = """
          neutral
        """

    with i18n.bind(en):
        str(Independent())
    with i18n.bind(ar):
        str(Independent())
    require(independent_calls == 1, "an explicit independent component did not share its entry")

    dormant_calls = 0

    class Dormant(Component):
        citry = app

        class Cache:
            enabled = True

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            nonlocal dormant_calls
            dormant_calls += 1
            return {}

        template = """
          dormant
        """

    str(Dormant())
    str(Dormant())
    require(dormant_calls == 1, "the dormant i18n extension disabled safe cache replay")

    stale: I18nCacheToken
    with i18n.bind(en):
        stale = cast("I18nCacheToken", i18n.current_token())

    class StaleToken(Component):
        citry = app
        phase0_i18n_cache = "dependent"

        class Cache:
            enabled = True

            def vary(self, kwargs: Any, slots: Any, *, i18n: I18nCacheToken) -> dict[str, Any]:  # noqa: ARG002
                return {"i18n": stale}

        template = """
          stale
        """

    reads_before_stale = len(backend.gets)
    stale_error = None
    try:
        with i18n.bind(context("en-US")):
            str(StaleToken())
    except CacheTokenError as error:
        stale_error = str(error)
    require(stale_error is not None, "a stale token was accepted")
    require(len(backend.gets) == reads_before_stale, "a stale token reached the backend")

    fragment_calls: list[str] = []

    class FragmentValue(Component):
        citry = app

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, str]:
            active = i18n.current_context()
            require(active is not None, "fragment render lost its context")
            fragment_calls.append(active.locale)
            return {"locale": active.locale}

        template = """
          <span>{{ locale }}</span>
        """

    class FragmentPage(Component):
        citry = app
        template = """
          <c-cache key="localized-fragment"><c-fragment-value /></c-cache>
        """

    with i18n.bind(en):
        en_fragment_first = str(FragmentPage())
        en_fragment_second = str(FragmentPage())
    with i18n.bind(ar):
        ar_fragment = str(FragmentPage())
    require(fragment_calls == ["en-US", "ar-EG"], f"fragment variation changed: {fragment_calls!r}")
    require(
        "en-US" in en_fragment_first and "en-US" in en_fragment_second and "ar-EG" in ar_fragment,
        "fragment replay crossed locale",
    )

    reads_before_unbound_fragment = len(backend.gets)
    try:
        str(FragmentPage())
    except RuntimeError as error:
        require("fragment render lost its context" in str(error), "the unbound fragment failed unexpectedly")
    require(len(backend.gets) == reads_before_unbound_fragment, "an unbound dependent fragment read the backend")

    return {
        "component_cache": {
            "distinct_locales_did_not_replay": True,
            "same_semantic_context_replayed": True,
        },
        "dormant_extension": {
            "cache_replayed": True,
            "render_cache_mode": i18n.render_cache_mode,
            "render_cache_version": i18n.render_cache_version,
        },
        "explicit_independence_shared": True,
        "fragment_cache": {
            "distinct_locales_did_not_replay": True,
            "same_locale_replayed": True,
            "unbound_backend_reads": 0,
        },
        "prelookup_failures": {
            "missing_token_backend_reads": 0,
            "missing_token_publications": 0,
            "stale_token_backend_reads": 0,
            "stale_token_rejected": True,
            "unbound_backend_reads": 0,
        },
        "recording_backend": {
            "gets": len(backend.gets),
            "sets": len(backend.sets),
            "unique_get_keys": len(set(backend.gets)),
            "unique_set_keys": len(set(backend.sets)),
        },
    }


def token_field_checks() -> dict[str, Any]:
    app = Citry(extensions=[Phase0I18nExtension])
    i18n = cast("Phase0I18nExtension", app.extensions.get_extension("i18n"))
    variants = [
        context("en-US"),
        context("en-US", direction="rtl"),
        context("en-US", time_zone="Europe/Prague"),
        context("en-US", fallback_locales=("en", "cs-CZ", "en-US")),
        context("en-US", tzdb_revision="tzdata-2026.4"),
        context("en-US", catalog_revision="catalog-2"),
        context("en-US", formats_revision="formats-2"),
    ]
    encoded: list[tuple[object, ...]] = []
    for value in variants:
        with i18n.bind(value):
            token = i18n.current_token()
            require(token is not None, "the extension did not mint a token")
            encoded.append(i18n.encode_token(token))
    require(len(set(encoded)) == len(variants), "one output-affecting context field did not vary the token")

    other_app = Citry(extensions=[Phase0I18nExtension])
    other = cast("Phase0I18nExtension", other_app.extensions.get_extension("i18n"))
    with other.bind(variants[0]):
        cross_engine = other.current_token()
    cross_engine_rejected = False
    try:
        with i18n.bind(variants[0]):
            i18n.encode_token(cast("I18nCacheToken", cross_engine))
    except CacheTokenError:
        cross_engine_rejected = True
    require(cross_engine_rejected, "a cross-engine token was accepted")
    forged_rejected = False
    with i18n.bind(variants[0]):
        forged = object.__new__(I18nCacheToken)
        forged._issuer = i18n
        forged._context = variants[0]
        try:
            i18n.encode_token(forged)
        except CacheTokenError:
            forged_rejected = True
    require(forged_rejected, "a token copied outside the issuer was accepted")
    return {
        "cross_engine_rejected": True,
        "forged_token_rejected": True,
        "output_affecting_fields_produced_distinct_encodings": True,
        "schema_version": 1,
        "variant_count": len(variants),
    }


def build_evidence() -> dict[str, Any]:
    ensure_always_on_checks()
    return {
        "artifacts": {
            "cache_design": sha256(CACHE_DESIGN),
            "cache_extension": sha256(CACHE_EXTENSION),
            "cache_keys": sha256(CACHE_KEYS),
            "harness": sha256(Path(__file__)),
            "i18n_design": sha256(I18N_DESIGN),
            "uv_lock": sha256(REPO / "uv.lock"),
        },
        "environment": {
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "render_checks": render_checks(),
        "result": "PASS_BOUNDED",
        "token_checks": token_field_checks(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "evidence.json")
    arguments = parser.parse_args()
    evidence = build_evidence()
    arguments.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"PASS_BOUNDED\nevidence={arguments.output}\n")


if __name__ == "__main__":
    main()
