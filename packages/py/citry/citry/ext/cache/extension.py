"""Component and named-fragment render caching with local invalidation."""

from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, cast

from citry._nested_declarations import _compose_nested_declaration_class
from citry.cache import _normalize_ttl
from citry.constness import const_value
from citry.extension import Extension
from citry.util.misc import to_dict

from ._introspection import inspect_cache
from .config import (
    CacheConfig,
    _build_engine_defaults,
    _effective_scope,
    _validate_component_fields,
    _validate_engine_fields,
)
from .keys import (
    _build_component_cache_key,
    _build_fragment_cache_key,
    _CacheKeyContext,
    _ExtensionCacheCompatibility,
    _validate_version,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.citry_render import CitryRender
    from citry.component import Component
    from citry.extension import (
        ComponentIntrospectionContext,
        OnComponentClassCreatedContext,
        OnExtensionCreatedContext,
    )

    from .artifact import CachedRenderArtifact


logger = logging.getLogger("citry")

_CacheLookupOutcome = Literal["miss", "corrupt-entry", "incompatible-entry", "oversized-entry"]
_CacheKind = Literal["component", "fragment"]


@dataclass(frozen=True, slots=True)
class _CacheMissPlan:
    """Render-local publication data captured by one cache lookup."""

    key: str
    ttl: float | None
    max_entry_bytes: int | None
    revision: int
    kind: _CacheKind = "component"
    lookup_outcome: _CacheLookupOutcome = "miss"
    artifact_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class _CacheHit:
    """One decoded candidate plus the miss plan used if replay rejects it."""

    artifact: CachedRenderArtifact
    miss: _CacheMissPlan
    artifact_bytes: int


@dataclass(frozen=True, slots=True)
class OnComponentCacheHitContext:
    """
    Notify an observer after one cached component subtree was replayed.

    ``component`` is the live boundary from the current call, never an
    archived object. ``key_digest`` is exactly 64 lowercase hexadecimal
    characters without a backend-key prefix. ``artifact_bytes`` is the
    stored value's validated UTF-8 size, and ``frame_count`` includes the
    boundary frame. ``kind`` distinguishes a ``Component.Cache`` hit from a
    transparent ``<c-cache>`` fragment hit. For a fragment, ``component`` is
    the live built-in Cache boundary from the current call. Return values and
    observer failures do not alter the committed hit.

    The dataclass is shallowly frozen. Observers should copy the scalar fields
    they need instead of retaining the live component through this context.
    """

    citry: Citry
    component: Component
    kind: Literal["component", "fragment"]
    key_digest: str
    artifact_bytes: int
    frame_count: int


class CacheExtension(Extension):
    """Own component and fragment output caching, defaults, and invalidation."""

    name = "cache"
    introspection_version = 1
    render_cache_mode = "stateless"
    render_cache_version = 1
    Config = CacheConfig

    def __init__(self) -> None:
        self._revision = 0
        self._revision_lock = RLock()
        self._defaults = _build_engine_defaults({})

    def validate_config_fields(
        self,
        fields: Mapping[str, Any],
        *,
        component: type[Component] | None = None,
    ) -> None:
        if component is not None:
            _validate_component_fields(fields)
        else:
            _validate_engine_fields(fields)

    def _component_config_defaults(self, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        """Expose only the engine TTL default through ``Component.Cache``."""
        return {"ttl": fields["ttl"]} if "ttl" in fields else {}

    def on_extension_created(self, ctx: OnExtensionCreatedContext) -> None:
        self._defaults = _build_engine_defaults(ctx.citry.settings.extensions_defaults.get("cache", {}))

    def on_component_class_created(self, ctx: OnComponentClassCreatedContext) -> None:
        declaration = _compose_nested_declaration_class(ctx.component_class, self.class_name)
        if ctx.component_class.transparent and getattr(declaration, "enabled", False) is True:
            msg = (
                f"Component {ctx.component_class.__name__}: Component.Cache cannot be enabled on a transparent "
                "component. Transparent fragment caching is provided by <c-cache>."
            )
            raise ValueError(msg)

    def inspect_component(self, ctx: ComponentIntrospectionContext) -> dict[str, object] | None:
        """
        Return public, JSON-safe Cache policy metadata for component introspection.

        This reports the effective component configuration without running a
        variation method, Slot factory, render, or asset load. The transparent
        ``<c-cache>`` built-in returns ``None`` because its fragment controls are
        already described by the core Kwargs schema and are unrelated to
        ``Component.Cache.enabled``.

        Args:
            ctx: The component-introspection request.

        Returns:
            Versioned component Cache policy metadata, or ``None`` for the
            transparent fragment-cache built-in.

        """
        return inspect_cache(ctx.component_class, ctx.info)

    def _revision_snapshot(self) -> int:
        """Read the current local invalidation revision atomically."""
        with self._revision_lock:
            return self._revision

    def _advance_revision(self) -> int:
        """Increment and return the local invalidation revision atomically."""
        with self._revision_lock:
            self._revision += 1
            return self._revision

    @contextmanager
    def _invalidation(self) -> Iterator[None]:
        """Block key snapshots until one invalidation commits a new revision."""
        with self._revision_lock:
            try:
                yield
            finally:
                self._revision += 1

    @contextmanager
    def _stable_revision(self, expected: int | None) -> Iterator[None]:
        """Keep one replay apply atomic with respect to local invalidation."""
        from .errors import _CacheRevisionChanged  # noqa: PLC0415

        with self._revision_lock:
            if expected is not None and self._revision != expected:
                raise _CacheRevisionChanged
            yield
            if expected is not None and self._revision != expected:
                raise _CacheRevisionChanged

    def _key_context(self) -> _CacheKeyContext:
        """Snapshot all engine-owned inputs to physical key construction."""
        scope = _effective_scope(self.citry, self._defaults)
        compatibility = tuple(
            _ExtensionCacheCompatibility(
                name=extension.name,
                mode=extension.render_cache_mode,
                version=extension.render_cache_version,
            )
            for extension in self.citry.extensions._extensions
        )
        return _CacheKeyContext(
            scope_kind=scope.kind,
            namespace=scope.namespace,
            generation=scope.generation,
            engine_id=scope.engine_id,
            revision=self._revision_snapshot(),
            extensions=compatibility,
        )

    def _lookup_component(
        self,
        component: Component,
        context: CitryContext,  # noqa: ARG002 - the boundary context is consumed by replay
    ) -> _CacheHit | _CacheMissPlan | None:
        """Build the effective component key and fetch one replay candidate."""
        if self._is_fragment_boundary(component):
            return self._lookup_fragment(component)
        config = cast("CacheConfig", getattr(component, self.name))
        if not config.enabled:
            return None

        bypass_reason = self._extension_bypass_reason()
        if bypass_reason is not None:
            self._diagnose_component("bypass", component, reason=bypass_reason)
            return None

        ttl = _normalize_ttl(config.ttl, source="component Cache ttl")
        if ttl == 0:
            self._diagnose_component("bypass", component, reason="ttl-zero")
            return None

        kwargs = MappingProxyType(dict(to_dict(component.kwargs)))
        slots = MappingProxyType(dict(to_dict(component.slots)))
        vary_method = getattr(config, "vary", None)
        if vary_method is None:
            effective_slots = sorted(name for name, value in slots.items() if value is not None)
            if effective_slots:
                names = ", ".join(repr(name) for name in effective_slots)
                from .errors import CacheKeyError  # noqa: PLC0415

                raise CacheKeyError(
                    f"slots[{effective_slots[0]!r}]",
                    f"component {type(component).__name__} has effective Slot content from {names}",
                )
            vary: object = dict(kwargs)
        else:
            vary = vary_method(kwargs, slots)

        key_context = self._key_context()
        key = _build_component_cache_key(
            key_context,
            type(component).class_id,
            vary=vary,
            version=config.version,
        )
        decision = self._lookup_physical_key(
            key,
            ttl=ttl,
            max_entry_bytes=self._defaults.max_entry_bytes,
            revision=key_context.revision,
        )
        if isinstance(decision, _CacheHit):
            return decision
        self._diagnose_lookup(decision, component=component)
        return decision

    def _is_fragment_boundary(self, component: Component) -> bool:
        """Whether this is this engine's exact transparent ``<c-cache>`` built-in."""
        component_class = type(component)
        return self.citry._is_builtin_component(component_class) and component_class.name == "cache"

    def _lookup_fragment(self, component: Component) -> _CacheHit | _CacheMissPlan | None:
        """Validate one fragment boundary and fetch its detached artifact."""
        controls = dict(to_dict(component.kwargs))
        key = const_value(controls["key"])
        vary = const_value(controls["vary"])
        ttl_value = const_value(controls["ttl"])
        version = const_value(controls["version"])
        enabled = const_value(controls["enabled"])

        if type(key) is not str or not key:
            msg = f"<c-cache> key must be an exact non-empty string; got {key!r}."
            raise ValueError(msg)
        ttl = _normalize_ttl(ttl_value, source="<c-cache> ttl")
        _validate_version(version)
        if type(enabled) is not bool:
            msg = f"<c-cache> enabled must be an exact bool; got {enabled!r}."
            raise ValueError(msg)
        if not enabled:
            return None
        bypass_reason = self._extension_bypass_reason()
        if bypass_reason is not None:
            self._diagnose("bypass", kind="fragment", reason=bypass_reason)
            return None
        if ttl == 0:
            self._diagnose("bypass", kind="fragment", reason="ttl-zero")
            return None

        key_context = self._key_context()
        physical_key = _build_fragment_cache_key(
            key_context,
            key,
            vary=vary,
            version=version,
        )
        decision = self._lookup_physical_key(
            physical_key,
            ttl=ttl,
            max_entry_bytes=self._defaults.max_entry_bytes,
            revision=key_context.revision,
            kind="fragment",
        )
        if isinstance(decision, _CacheHit):
            return decision
        self._diagnose_lookup(decision, component=None)
        return decision

    def _extension_bypass_reason(self) -> str | None:
        """Ask every extension through the same public cache-lookup hook."""
        for extension in self.citry.extensions._extensions:
            reason = extension.render_cache_bypass_reason()
            if reason is not None:
                if type(reason) is not str or not reason:
                    raise TypeError(
                        f"Extension {extension.name!r} render_cache_bypass_reason() must return "
                        "None or an exact non-empty string."
                    )
                return reason
        return None

    def _lookup_physical_key(
        self,
        key: str,
        *,
        ttl: float | None,
        max_entry_bytes: int | None,
        revision: int | None = None,
        kind: _CacheKind = "component",
    ) -> _CacheHit | _CacheMissPlan:
        """Fetch and decode one key against a stable local revision snapshot."""
        from .artifact import _decode_artifact_with_size  # noqa: PLC0415
        from .errors import (  # noqa: PLC0415
            CacheArtifactError,
            _CacheArtifactCompatibilityError,
            _CacheArtifactOversizedError,
            _CacheRevisionChanged,
        )

        if revision is None:
            revision = self._revision_snapshot()
        elif self._revision_snapshot() != revision:
            raise _CacheRevisionChanged
        value = self.citry.cache.get(key)
        if self._revision_snapshot() != revision:
            # The physical key may include the revision. Let the caller rebuild
            # the whole lookup decision instead of pairing an old key with a
            # new revision.
            raise _CacheRevisionChanged
        miss = _CacheMissPlan(
            key=key,
            ttl=ttl,
            max_entry_bytes=max_entry_bytes,
            revision=revision,
            kind=kind,
        )
        if value is None:
            return miss
        try:
            artifact, artifact_bytes = _decode_artifact_with_size(value)
        except _CacheArtifactOversizedError as error:
            return _CacheMissPlan(
                key=key,
                ttl=ttl,
                max_entry_bytes=max_entry_bytes,
                revision=revision,
                kind=kind,
                lookup_outcome="oversized-entry",
                artifact_bytes=error.size,
            )
        except CacheArtifactError as error:
            outcome: _CacheLookupOutcome = (
                "incompatible-entry" if isinstance(error, _CacheArtifactCompatibilityError) else "corrupt-entry"
            )
            return _CacheMissPlan(
                key=key,
                ttl=ttl,
                max_entry_bytes=max_entry_bytes,
                revision=revision,
                kind=kind,
                lookup_outcome=outcome,
                artifact_bytes=None,
            )
        return _CacheHit(artifact=artifact, miss=miss, artifact_bytes=artifact_bytes)

    def _diagnose_lookup(self, decision: _CacheMissPlan, *, component: Component | None) -> None:
        """Record one miss or rejected backend value without exposing fragment inputs."""
        self._diagnose(
            decision.lookup_outcome,
            kind=decision.kind,
            component=component if decision.kind == "component" else None,
            key=decision.key,
            artifact_bytes=decision.artifact_bytes,
            reason=(
                "format-version"
                if decision.lookup_outcome == "incompatible-entry"
                else "absolute-limit"
                if decision.lookup_outcome == "oversized-entry"
                else "decode-rejected"
                if decision.lookup_outcome == "corrupt-entry"
                else None
            ),
        )

    def _record_replay_rejection(
        self,
        hit: _CacheHit,
        component: Component,
        error: Exception,  # noqa: ARG002 - diagnostic details are deliberately not logged
    ) -> None:
        """Record a validated artifact that cannot bind to the current runtime."""
        self._diagnose(
            "incompatible-entry",
            kind=hit.miss.kind,
            component=component if hit.miss.kind == "component" else None,
            key=hit.miss.key,
            artifact_bytes=hit.artifact_bytes,
            frame_count=len(hit.artifact.frames),
            reason="replay-rejected",
        )

    def _notify_component_hit(self, hit: _CacheHit, component: Component) -> None:
        """Record and isolate notify-only observers after ownership settles."""
        observers = self.citry.extensions._extensions_with_hook("on_component_cache_hit")
        debug_enabled = logger.isEnabledFor(logging.DEBUG)
        if not observers and not debug_enabled:
            return
        frame_count = len(hit.artifact.frames)
        if debug_enabled:
            self._diagnose(
                "hit",
                kind=hit.miss.kind,
                component=component if hit.miss.kind == "component" else None,
                key=hit.miss.key,
                artifact_bytes=hit.artifact_bytes,
                frame_count=frame_count,
            )
        if not observers:
            return
        ctx = OnComponentCacheHitContext(
            citry=self.citry,
            component=component,
            kind=hit.miss.kind,
            key_digest=_key_digest(hit.miss.key),
            artifact_bytes=hit.artifact_bytes,
            frame_count=frame_count,
        )
        for observer in observers:
            try:
                cast("Any", observer).on_component_cache_hit(ctx)
            except Exception as error:  # noqa: BLE001 - notify-only observers are isolated
                logger.log(
                    logging.ERROR,
                    "Render cache hit observer failed extension=%s exception=%s",
                    observer.name,
                    type(error).__name__,
                )

    def _publish_component(self, plan: _CacheMissPlan, render: CitryRender) -> bool:
        """Publish one settled, clean subtree when its revision is still current."""
        from .artifact import _encode_artifact  # noqa: PLC0415
        from .errors import (  # noqa: PLC0415
            CacheArtifactError,
            _CacheArtifactOversizedError,
            _CacheRevisionChanged,
            _CacheUncacheableError,
        )
        from .replay import _export_component_artifact, _export_fragment_artifact  # noqa: PLC0415

        component = render.context.component
        if component is None:
            raise RuntimeError("A render-cache publication has no live boundary component.")
        if render.context._error_tainted:
            self._diagnose_plan("store-skipped", plan, component, reason="error-tainted")
            return False
        if self._revision_snapshot() != plan.revision:
            self._diagnose_plan("store-skipped", plan, component, reason="revision-changed")
            return False
        try:
            artifact = (
                _export_fragment_artifact(render) if plan.kind == "fragment" else _export_component_artifact(render)
            )
            value = _encode_artifact(artifact)
        except _CacheArtifactOversizedError as error:
            self._diagnose_plan(
                "oversized-entry",
                plan,
                component,
                artifact_bytes=error.size,
                limit_bytes=error.limit,
                reason="entry-limit",
            )
            return False
        except _CacheUncacheableError as error:
            self._diagnose_plan(
                "store-skipped",
                plan,
                component,
                reason="extension-denied",
                extension_name=error.extension_name,
            )
            return False
        except CacheArtifactError:
            self._diagnose_plan("store-skipped", plan, component, reason="artifact-rejected")
            return False
        artifact_bytes = len(value.encode("utf-8"))
        if plan.max_entry_bytes is not None and artifact_bytes > plan.max_entry_bytes:
            self._diagnose_plan(
                "oversized-entry",
                plan,
                component,
                artifact_bytes=artifact_bytes,
                frame_count=len(artifact.frames),
                limit_bytes=plan.max_entry_bytes,
                reason="entry-limit",
            )
            return False
        try:
            stored = False
            with self._stable_revision(plan.revision):
                self.citry.cache.set(plan.key, value, ttl=plan.ttl)
                stored = True
        except _CacheRevisionChanged:
            if stored:
                self.citry.cache.delete(plan.key)
            self._diagnose_plan("store-skipped", plan, component, reason="revision-changed")
            return False
        except Exception:
            self._diagnose_plan("store-error", plan, component, reason="backend-set-failed")
            raise
        self._diagnose_plan(
            "store",
            plan,
            component,
            artifact_bytes=artifact_bytes,
            frame_count=len(artifact.frames),
        )
        return True

    def _diagnose_plan(
        self,
        outcome: str,
        plan: _CacheMissPlan,
        component: Component,
        **fields: Any,
    ) -> None:
        """Record one publication outcome using the plan's cache kind."""
        self._diagnose(
            outcome,
            kind=plan.kind,
            component=component if plan.kind == "component" else None,
            key=plan.key,
            **fields,
        )

    def _diagnose_component(
        self,
        outcome: str,
        component: Component,
        *,
        key: str | None = None,
        artifact_bytes: int | None = None,
        frame_count: int | None = None,
        limit_bytes: int | None = None,
        reason: str | None = None,
        extension_name: str | None = None,
    ) -> None:
        """Emit one safe structured component-cache DEBUG record."""
        self._diagnose(
            outcome,
            kind="component",
            component=component,
            key=key,
            artifact_bytes=artifact_bytes,
            frame_count=frame_count,
            limit_bytes=limit_bytes,
            reason=reason,
            extension_name=extension_name,
        )

    def _diagnose(
        self,
        outcome: str,
        *,
        kind: _CacheKind,
        component: Component | None = None,
        key: str | None = None,
        artifact_bytes: int | None = None,
        frame_count: int | None = None,
        limit_bytes: int | None = None,
        reason: str | None = None,
        extension_name: str | None = None,
    ) -> None:
        """Emit one safe structured DEBUG record for cache observability."""
        if not logger.isEnabledFor(logging.DEBUG):
            return
        key_digest = _key_digest(key) if key is not None else None
        component_name = type(component).__name__ if component is not None else None
        component_class = type(component) if component is not None else None
        fields = {
            "citry_cache_outcome": outcome,
            "citry_cache_kind": kind,
            "citry_cache_component": component_name,
            "citry_cache_class_id": component_class.class_id if component_class is not None else None,
            "citry_cache_definition_id": component_class.definition_id if component_class is not None else None,
            "citry_cache_engine_id": self.citry.engine_id,
            "citry_cache_key_digest": key_digest,
            "citry_cache_artifact_bytes": artifact_bytes,
            "citry_cache_frame_count": frame_count,
            "citry_cache_limit_bytes": limit_bytes,
            "citry_cache_reason": reason,
            "citry_cache_extension": extension_name,
        }
        logger.debug(
            "Render cache %s kind=%s component=%s class_id=%s key_digest=%s bytes=%s frames=%s reason=%s",
            outcome,
            kind,
            component_name,
            component_class.class_id if component_class is not None else None,
            key_digest,
            artifact_bytes,
            frame_count,
            reason,
            extra=fields,
        )


def _key_digest(key: str) -> str:
    """Return only the opaque digest portion of one physical render key."""
    suffix = key.rsplit(":", 1)[-1]
    if re.fullmatch(r"[0-9a-f]{64}", suffix) is not None:
        return suffix
    return sha256(key.encode("utf-8")).hexdigest()
