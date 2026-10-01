"""Private composition of direct prepared rendering with an Events occurrence."""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from threading import Lock
from typing import TYPE_CHECKING, TypedDict, cast
from weakref import WeakKeyDictionary, ref

from citry._vue.capture import render_prepared_direct, render_prepared_marker_replacement
from citry._vue.compiler import HELPER_CONTRACT, CompiledRender, NativeCompiler
from citry._vue.direct_capture import Assembly, assemble_typed_render
from citry._vue.protocol import DefinitionAsset, prepared_manifest, revision_envelope
from citry.cache import _forget_stored_key, _store_if_missing
from citry.citry import Citry
from citry.citry_element import CitryElement
from citry.component import Component, ComponentMeta
from citry.ext.dependencies.scripts import uses_component
from citry.ext.events.emission import EXTRA_KEY, EventInstanceEntry, build_events_manifest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

    from citry._javascript_policy import _JavascriptPolicy
    from citry._serialization_security import _ScriptSecurityMaterializer
    from citry._vue.prepared import PreparedViewMetadata
    from citry.browser_render import PreparedBrowserExtension
    from citry.citry_render import CitryRender
    from citry.ext.dependencies.types import Dependency, DependencyRecord
    from citry.ext.events.extension import EventsExtension
    from citry.ext.events.renderers import _VueMarkerTarget
    from citry.ext.events.results import RenderEncodingContext
    from citry.settings import SecurityCspMode, SecurityJavascriptMode


# A page links compiled definitions and stylesheets by digest, and the browser
# may ask for them long after the render. Each engine keeps them in this
# process in ``_LOCAL_ASSETS`` (see ``_LocalAssets``). When the engine was
# given a cache backend, that backend is where every worker sharing it finds
# them, and the local copies only save a round trip (see ``_store_asset``).
_LOCAL_ASSETS: WeakKeyDictionary[Citry, _LocalAssets] = WeakKeyDictionary()
# How many recent assets each process keeps in memory per engine when the
# engine has a cache backend, which holds the full set.
_LOCAL_ASSET_LIMIT = 128
# The asset name each kind uses in its collision error message.
_ASSET_LABELS = {"definition": "definition bundle", "style": "stylesheet asset"}
# Renders publish into these maps while route requests read and refill them,
# so one lock keeps an eviction from removing an entry mid-update.
_LOCAL_ASSETS_LOCK = Lock()
_PRODUCERS: WeakKeyDictionary[Citry, DirectVueEventsProducer] = WeakKeyDictionary()


class _DependencyOptions(TypedDict, total=False):
    script_security: _ScriptSecurityMaterializer
    security_csp: SecurityCspMode
    javascript_policy: _JavascriptPolicy
    security_javascript: SecurityJavascriptMode
    strategy: str


def _format_default_component_tag(type_key: str, component: type[Component]) -> str:
    words = re.sub(r"(?<!^)(?=[A-Z])", "-", component.__name__).lower()
    # A component class name may hold `_`, which the Vue tag check rejects,
    # so reduce the readable part to lowercase words joined by `-`.
    # The digest suffix keeps the tag unique, so the dropped characters are
    # only cosmetic.
    words = re.sub(r"[^a-z0-9]+", "-", words).strip("-") or "component"
    return f"citry-{words}-{hashlib.sha256(type_key.encode()).hexdigest()[:8]}"


class _BuiltInPreparationMetadata:
    """Resolve ordinary built-in component metadata once within one preparation."""

    def __init__(self, citry: Citry, fallback_tag: Callable[[str], str]) -> None:
        self.citry = citry
        self.fallback_tag = fallback_tag
        self.classes: dict[str, type[Component]] = {}
        self.tags: dict[str, str] = {}

    def resolve(self, type_key: str, rendered_class: type[object] | None) -> str:
        component = self.classes.get(type_key)
        if component is None:
            component = self.citry.get_component_by_class_id(type_key)
            if type(component) is not ComponentMeta:
                return self.fallback_tag(type_key)
            self.classes[type_key] = component
            self.tags[type_key] = _format_default_component_tag(type_key, component)
        if rendered_class is not None and rendered_class is not component:
            raise ValueError("prepared component class changed before Vue metadata preparation")
        return self.tags[type_key]

    def validate(self) -> None:
        for type_key, component in self.classes.items():
            current = self.citry.get_component_by_class_id(type_key)
            if current is not component or _format_default_component_tag(type_key, current) != self.tags[type_key]:
                raise ValueError("component registry metadata changed during Vue preparation")


@dataclass(frozen=True, slots=True)
class _PreparedResult:
    payload: dict[str, object]
    tags: dict[str, str] | None
    validate: Callable[[], None]
    extensions: tuple[PreparedBrowserExtension, ...] = ()


@dataclass(frozen=True, slots=True)
class EarlySelectedTreeCompilation:
    """Request-local compiler output prepared before HTML frame materialization."""

    selected_render: CitryRender
    citry: Citry
    revision: int
    root_occurrence_id: str | None
    producer_identity: tuple[object, object, object]
    assembly: Assembly | None
    compiled_by_definition: dict[str, CompiledRender] | None
    error: Exception | None = None
    error_stage: str | None = None
    metadata: _BuiltInPreparationMetadata | None = None


def _asset_cache_key(kind: str, digest: str) -> str:
    """The cache key for one Vue definition bundle or stylesheet, named by the sha256 of its bytes."""
    return f"citry:vue-{kind}:{digest}"


class _LocalAssets:
    """
    One engine's compiled Vue assets held in this process, dropping the ones used longest ago.

    Which limit applies depends on where else the assets live. When the
    engine has no configured cache, this map is the only place they are kept,
    so it holds up to ``CitrySettings.vue_asset_max_bytes`` bytes. When it has
    one, the backend holds every asset and this map keeps only the
    ``_LOCAL_ASSET_LIMIT`` most recent.

    An asset that a render still in progress has published is never dropped
    (see ``_hold_render_assets``), and the limit is applied only when an
    asset is added. So the total can exceed the limit by the files of the
    renders in progress and of the page rendered last.
    """

    def __init__(self) -> None:
        # (kind, digest) -> bytes. Order is recency: the front was used longest ago.
        self.entries: OrderedDict[tuple[str, str], bytes] = OrderedDict()
        self.total_bytes = 0
        # (kind, digest) -> how many in-progress renders published it.
        self.held: dict[tuple[str, str], int] = {}

    def __len__(self) -> int:
        return len(self.entries)

    def __contains__(self, key: object) -> bool:
        return key in self.entries


def _uses_own_store(citry: Citry) -> bool:
    """
    Whether this engine keeps Vue assets only in this process.

    With no configured cache, the engine's default in-memory cache is private
    to this process anyway, so writing assets there would only keep a second,
    unbounded copy. A configured backend (even an ``InMemoryCache`` shared
    by several engines) is where other engines and workers look, so it keeps
    receiving every asset.
    """
    return citry.settings.cache is None


# The assets published by the render in progress in this context (thread or
# async task), with the engine that owns each. ``None`` outside a render.
_RENDER_PUBLISHES: ContextVar[list[tuple[Citry, tuple[str, str]]] | None] = ContextVar(
    "citry_vue_render_publishes", default=None
)


@contextmanager
def _hold_render_assets() -> Iterator[None]:
    """
    Keep every asset a render publishes until the render has finished preparing its page.

    One page links several assets. Without this, a small limit or several
    concurrent renders could drop an asset the page links before the page is
    even sent, and the browser's first request for it would get a 404.

    Finishing only releases the hold; it drops nothing. The page is sent
    after this point and the browser asks for its files right away, so the
    limit is applied again only when a later render publishes something.
    """
    if _RENDER_PUBLISHES.get() is not None:
        # A nested preparation: the outermost render holds everything.
        yield
        return
    published: list[tuple[Citry, tuple[str, str]]] = []
    token = _RENDER_PUBLISHES.set(published)
    try:
        yield
    finally:
        _RENDER_PUBLISHES.reset(token)
        with _LOCAL_ASSETS_LOCK:
            for citry, key in published:
                local = _LOCAL_ASSETS.get(citry)
                if local is None:
                    continue
                remaining = local.held.get(key, 0) - 1
                if remaining > 0:
                    local.held[key] = remaining
                else:
                    local.held.pop(key, None)


def _enforce_limit(citry: Citry, local: _LocalAssets, *, newest: tuple[str, str]) -> None:
    """Drop the assets used longest ago until ``local`` fits its limit; the caller holds the lock."""
    own_store = _uses_own_store(citry)
    byte_limit = citry.settings.vue_asset_max_bytes if own_store else None
    entry_limit = None if own_store else _LOCAL_ASSET_LIMIT

    def over_limit() -> bool:
        return (entry_limit is not None and len(local.entries) > entry_limit) or (
            byte_limit is not None and local.total_bytes > byte_limit
        )

    for key in list(local.entries):
        if not over_limit():
            return
        # The newest asset stays even when it alone exceeds the limit, and so
        # does anything a render in progress links: those pages need them now.
        if key == newest or local.held.get(key):
            continue
        local.total_bytes -= len(local.entries.pop(key))


def _remember_locally(citry: Citry, kind: str, digest: str, content: bytes) -> None:
    """Keep one asset in this process, rejecting a digest reused for other bytes, then apply the limit."""
    key = (kind, digest)
    published = _RENDER_PUBLISHES.get()
    with _LOCAL_ASSETS_LOCK:
        local = _LOCAL_ASSETS.setdefault(citry, _LocalAssets())
        prior = local.entries.get(key)
        if prior is not None and prior != content:
            raise RuntimeError(f"Vue {_ASSET_LABELS[kind]} digest collision.")
        if prior is None:
            local.total_bytes += len(content)
        local.entries[key] = content
        local.entries.move_to_end(key)
        # A render holds each asset it publishes once, however often it
        # publishes it, so the release at its end balances exactly.
        if published is not None and (citry, key) not in published:
            published.append((citry, key))
            local.held[key] = local.held.get(key, 0) + 1
        _enforce_limit(citry, local, newest=key)


def _local_asset(citry: Citry, kind: str, digest: str) -> bytes | None:
    """This process's copy of one asset, marking it as recently used."""
    with _LOCAL_ASSETS_LOCK:
        local = _LOCAL_ASSETS.get(citry)
        if local is None:
            return None
        content = local.entries.get((kind, digest))
        if content is not None:
            local.entries.move_to_end((kind, digest))
        return content


def _store_asset(citry: Citry, kind: str, digest: str, content: bytes) -> None:
    """
    Publish one asset before the page that links it is sent, so a later request for its URL finds it.

    Without a configured cache, the asset stays in this process only, within
    ``CitrySettings.vue_asset_max_bytes``. Assets of a render in progress and
    of the page rendered last are never dropped; once the limit drops an
    older asset, an open page that asks for it gets a 404.

    With a configured cache, the asset is also written there, without a TTL,
    so any worker sharing the backend can serve it and an open page can load
    it at any later time. The backend's own capacity and eviction decide how
    long it stays. To avoid a round trip per asset per render, this process
    asks the backend whether it holds the asset at most once per
    ``citry.cache._STORED_KEY_RECHECK_SECONDS``. The cost of that saving: if
    the backend drops an asset, a process that already saw it stored writes
    it back only on its first render after that interval, and other workers
    answer 404 for it until then.

    An error from the cache backend (a lost connection, a full store) is not
    caught: it fails the render that is about to link the asset. Rendering the
    page anyway would send a link that other workers answer with 404, so a
    loud failure is the safer outcome, as it is for ``Dependencies`` files.
    """
    _remember_locally(citry, kind, digest, content)
    if _uses_own_store(citry):
        return
    _store_if_missing(citry, citry.cache, _asset_cache_key(kind, digest), content.decode)


def _load_asset(citry: Citry, kind: str, digest: str) -> bytes | None:
    """Find one asset in this process first, then in the cache another worker may have written."""
    content = _local_asset(citry, kind, digest)
    if content is not None:
        return content
    # Without a configured cache nothing else holds the asset: a miss here
    # is the route's 404.
    if _uses_own_store(citry):
        return None
    key = _asset_cache_key(kind, digest)
    cached = citry.cache.get(key)
    if cached is None:
        return None
    content = cached.encode()
    # A shared backend is outside this process's control. Serve only bytes
    # that still match the digest in the URL; anything else is a miss (404),
    # and the browser's integrity check would reject those bytes anyway.
    # Deleting the entry lets the next render that links it write it again;
    # this process forgets it saw the key stored so its own next render does.
    if hashlib.sha256(content).hexdigest() != digest:
        citry.cache.delete(key)
        _forget_stored_key(citry, key)
        return None
    _remember_locally(citry, kind, digest, content)
    return content


def definition_bundle(citry: Citry, digest: str) -> bytes | None:
    """
    Return one engine-owned immutable compiled definition bundle.

    Returns ``None`` when neither this process nor the cache holds it.
    """
    return _load_asset(citry, "definition", digest)


def style_asset(citry: Citry, digest: str) -> bytes | None:
    """
    Return one engine-owned immutable prepared stylesheet.

    Returns ``None`` when neither this process nor the cache holds it.
    """
    return _load_asset(citry, "style", digest)


def default_events_producer(citry: Citry) -> DirectVueEventsProducer:
    """Create the engine's graph-free Vue Events producer without retaining the engine."""
    cached = _PRODUCERS.get(citry)
    if cached is not None:
        return cached
    engine = ref(citry)

    def current() -> Citry:
        value = engine()
        if value is None:
            raise RuntimeError("The Citry engine owning this Vue producer was collected.")
        return value

    def tag_for_type(type_key: str) -> str:
        component = current().get_component_by_class_id(type_key)
        return _format_default_component_tag(type_key, component)

    def request_scope(
        _renderable: CitryElement | CitryRender, context: RenderEncodingContext
    ) -> tuple[str, int, int, str]:
        headers = {key.lower(): value for key, value in context.headers.items()}
        app_id = headers.get("x-citry-vue-app", "")
        occurrence_id = headers.get("x-citry-vue-occurrence", "")
        raw_revision = headers.get("x-citry-vue-revision", "")
        if not app_id or not occurrence_id or not raw_revision.isdigit():
            raise ValueError("Vue Events requires current app, occurrence, and revision headers.")
        base_revision = int(raw_revision)
        return app_id, base_revision + 1, base_revision, occurrence_id

    def publish_bundle(digest: str, content: bytes) -> None:
        _store_asset(current(), "definition", digest, content)

    def publish_style(digest: str, content: bytes) -> None:
        _store_asset(current(), "style", digest, content)

    producer = DirectVueEventsProducer(
        tag_for_type=tag_for_type,
        compile_view=native_compile_view(NativeCompiler()),
        request_scope=request_scope,
        publish_bundle=publish_bundle,
        publish_style=publish_style,
        asset_url=lambda digest: (
            current().build_url(f"ext/events/definitions/{digest}.js")
            if current().mounted_prefix is not None
            else f"/definitions/{digest}.js"
        ),
        style_asset_url=lambda digest: (
            current().build_url(f"ext/events/assets/{digest}.css")
            if current().mounted_prefix is not None
            else f"/assets/{digest}.css"
        ),
        _builtin_citry_ref=engine,
        _builtin_tag_callback=tag_for_type,
    )
    _PRODUCERS[citry] = producer
    return producer


def precompile_selected_tree_for_serialization(
    render: CitryRender,
    citry: Citry,
) -> EarlySelectedTreeCompilation | None:
    """Compile the pure selected tree early when no browser hook can run."""
    browser_hooks = set(citry.extensions._extensions_with_hook("browser_plugin")) | set(
        citry.extensions._extensions_with_hook("prepare_browser_render")
    )
    if browser_hooks:
        from citry.ext.i18n.extension import I18nExtension  # noqa: PLC0415

        # The stock, unconfigured i18n extension contributes nothing to the
        # browser tree. Permit that exact inert instance while leaving every
        # configured, replaced, or user-defined callback on the late path.
        inert_i18n_only = all(
            type(extension) is I18nExtension
            and not extension.configured
            and "browser_plugin" not in vars(extension)
            and "prepare_browser_render" not in vars(extension)
            for extension in browser_hooks
        )
        if not inert_i18n_only:
            return None
    producer = default_events_producer(citry)
    if type(producer) is not DirectVueEventsProducer or not producer._uses_builtin_metadata(citry):
        return None
    metadata = _BuiltInPreparationMetadata(citry, producer._tag_for_type)
    producer_identity = (
        producer._builtin_citry_ref,
        producer._builtin_tag_callback,
        producer._tag_for_type,
    )
    try:
        assembly = assemble_typed_render(
            render,
            revision=0,
            tag_for_type=producer._tag_for_type,
            component_metadata_for_type=metadata.resolve,
            expected_citry=citry,
        )
    except Exception as error:  # noqa: BLE001 -- defer to the established post-validation boundary
        return EarlySelectedTreeCompilation(
            render, citry, 0, None, producer_identity, None, None, error, "assembly", metadata
        )
    try:
        compiled = producer._compile_view(assembly)
        if set(compiled) != {item.id for item in assembly.view.definitions}:
            raise ValueError("direct compiler output must exactly cover the prepared definitions")
    except Exception as error:  # noqa: BLE001 -- preserve compiler errors after pre-extension validation
        return EarlySelectedTreeCompilation(
            render, citry, 0, None, producer_identity, assembly, None, error, "compile", metadata
        )
    return EarlySelectedTreeCompilation(
        render, citry, 0, None, producer_identity, assembly, compiled, metadata=metadata
    )


class DirectVueEventsProducer:
    """
    Produce a prepared revision from an already selected render tree.

    Event contexts use the tokens captured during that same render and never mint credentials.
    Definition JavaScript is published through ``publish_bundle`` before its
    content-addressed URL is put on the wire.
    """

    def __init__(
        self,
        *,
        tag_for_type: Callable[[str], str],
        compile_view: Callable[[Assembly], dict[str, CompiledRender]],
        request_scope: Callable[[CitryElement | CitryRender, RenderEncodingContext], tuple[str, int, int, str]],
        publish_bundle: Callable[[str, bytes], None],
        asset_url: Callable[[str], str] = lambda digest: f"/definitions/{digest}.js",
        publish_style: Callable[[str, bytes], None] | None = None,
        style_asset_url: Callable[[str], str] = lambda digest: f"/assets/{digest}.css",
        _builtin_citry_ref: ref[Citry] | None = None,
        _builtin_tag_callback: Callable[[str], str] | None = None,
    ) -> None:
        self._tag_for_type = tag_for_type
        self._compile_view = compile_view
        self._request_scope = request_scope
        self._publish_bundle = publish_bundle
        self._asset_url = asset_url
        self._publish_style = publish_bundle if publish_style is None else publish_style
        self._style_asset_url = style_asset_url
        self._builtin_citry_ref = _builtin_citry_ref
        self._builtin_tag_callback = _builtin_tag_callback

    def component_tag(self, type_key: str) -> str:
        """Return the engine-specific registered Vue tag for one stable type."""
        return self._tag_for_type(type_key)

    def _uses_builtin_metadata(self, citry: Citry) -> bool:
        return bool(
            self._builtin_citry_ref is not None
            and self._builtin_citry_ref() is citry
            and self._tag_for_type is self._builtin_tag_callback
            and "get_component_by_class_id" not in vars(citry)
            and getattr(citry.get_component_by_class_id, "__func__", None) is Citry.get_component_by_class_id
            and "component_tag" not in vars(self)
            and getattr(self.component_tag, "__func__", None) is DirectVueEventsProducer.component_tag
            and "prepare_from_render" not in vars(self)
            and getattr(self.prepare_from_render, "__func__", None) is DirectVueEventsProducer.prepare_from_render
        )

    def __call__(self, renderable: CitryElement | CitryRender, context: RenderEncodingContext) -> dict[str, object]:
        app_id, revision, base_revision, root_occurrence_id = self._request_scope(renderable, context)
        render = render_prepared_direct(renderable) if isinstance(renderable, CitryElement) else renderable
        if render.render_target != "prepared":
            raise TypeError("vue-prepared/1 requires a typed prepared CitryRender.")
        return self.prepare_from_render(
            render,
            citry=context.citry,
            app_id=app_id,
            revision=revision,
            base_revision=base_revision,
            root_occurrence_id=root_occurrence_id,
        )

    def prepare_marker(
        self,
        renderable: CitryElement | CitryRender,
        context: RenderEncodingContext,
        target: _VueMarkerTarget,
    ) -> dict[str, object]:
        """Prepare a private Mark wrapper without rerendering its payload."""
        app_id, revision, base_revision, _root_occurrence_id = self._request_scope(renderable, context)
        render = render_prepared_marker_replacement(renderable, citry=context.citry, name=target.name)
        return self.prepare_from_render(
            render,
            citry=context.citry,
            app_id=app_id,
            revision=revision,
            base_revision=base_revision,
            root_occurrence_id=None,
        )

    def prepare_from_render(
        self,
        render: CitryRender,
        *,
        citry: Citry,
        app_id: str,
        revision: int,
        base_revision: int | None = None,
        root_occurrence_id: str | None = None,
    ) -> dict[str, object]:
        """Prepare initial or event output without rendering the selected tree again."""
        return self._prepare_from_render_result(
            render,
            citry=citry,
            app_id=app_id,
            revision=revision,
            base_revision=base_revision,
            root_occurrence_id=root_occurrence_id,
        ).payload

    def _prepare_from_render_result(
        self,
        render: CitryRender,
        *,
        citry: Citry,
        app_id: str,
        revision: int,
        base_revision: int | None = None,
        root_occurrence_id: str | None = None,
        dependency_options: _DependencyOptions | None = None,
        _early_selected_tree: EarlySelectedTreeCompilation | None = None,
    ) -> _PreparedResult:
        """Prepare initial or event output without rendering the selected tree again."""
        # Every asset this preparation publishes stays in memory until it is
        # done, so the page never links an asset the limit already dropped.
        with _hold_render_assets():
            return self._prepare_holding_assets(
                render,
                citry=citry,
                app_id=app_id,
                revision=revision,
                base_revision=base_revision,
                root_occurrence_id=root_occurrence_id,
                dependency_options=dependency_options,
                _early_selected_tree=_early_selected_tree,
            )

    def _prepare_holding_assets(
        self,
        render: CitryRender,
        *,
        citry: Citry,
        app_id: str,
        revision: int,
        base_revision: int | None = None,
        root_occurrence_id: str | None = None,
        dependency_options: _DependencyOptions | None = None,
        _early_selected_tree: EarlySelectedTreeCompilation | None = None,
    ) -> _PreparedResult:
        """The body of ``_prepare_from_render_result``, run while its published assets are held."""
        root_component = render.context.component
        if root_component is not None:
            root_class = type(root_component)
            if citry.get_component_by_class_id(root_component._citry_class_id) is not root_class:
                raise ValueError("component class changed before Vue metadata preparation")
        built_in_identity = (
            self._builtin_citry_ref,
            self._builtin_tag_callback,
            self._tag_for_type,
        )
        built_in_metadata = (
            _early_selected_tree.metadata
            if _early_selected_tree is not None and _early_selected_tree.metadata is not None
            else (
                _BuiltInPreparationMetadata(citry, self._tag_for_type) if self._uses_builtin_metadata(citry) else None
            )
        )
        from citry.browser_render import (  # noqa: PLC0415
            collect_browser_plugin_descriptors,
            prepare_browser_extensions,
            validate_browser_plugin_registrations,
        )

        browser_plugin_registrations = collect_browser_plugin_descriptors(citry)
        template_context_names = tuple(
            sorted(
                name
                for registration in browser_plugin_registrations
                if registration.plugin is not None
                for name in registration.plugin.template_context_names
            )
        )
        if _early_selected_tree is not None and (
            _early_selected_tree.selected_render is not render
            or _early_selected_tree.citry is not citry
            or _early_selected_tree.revision != revision
            or _early_selected_tree.root_occurrence_id != root_occurrence_id
            or _early_selected_tree.producer_identity[0] is not built_in_identity[0]
            or _early_selected_tree.producer_identity[1] is not built_in_identity[1]
            or _early_selected_tree.producer_identity[2] is not built_in_identity[2]
        ):
            raise ValueError("early selected-tree compilation does not match the current render preparation")
        if _early_selected_tree is not None and _early_selected_tree.error_stage == "assembly":
            if _early_selected_tree.error is None:
                raise AssertionError("early selected-tree assembly error is missing")
            raise _early_selected_tree.error
        assembly = (
            _early_selected_tree.assembly
            if _early_selected_tree is not None and _early_selected_tree.assembly is not None
            else assemble_typed_render(
                render,
                revision=revision,
                tag_for_type=self._tag_for_type,
                component_metadata_for_type=(built_in_metadata.resolve if built_in_metadata is not None else None),
                root_occurrence_id=root_occurrence_id,
                template_context_names=template_context_names,
                expected_citry=citry,
            )
        )
        if dependency_options is None:
            from citry._csp_validation import _CspRenderValidator  # noqa: PLC0415
            from citry._javascript_policy import _JavascriptPolicy  # noqa: PLC0415

            opaque_html_values = [
                record["html"]
                for occurrence in assembly.view.occurrences
                for record in cast(
                    "dict[str, dict[str, object]]", occurrence.prepared_data.get("opaqueHtml", {})
                ).values()
            ]
            if any(type(html) is not str for html in opaque_html_values):
                raise AssertionError("prepared opaque HTML record changed type")
            opaque_html = cast("list[str]", opaque_html_values)
            component_classes: dict[str, str] = {}
            if citry.settings.security_javascript != "allow":
                pre_extension_policy = _JavascriptPolicy(citry.settings.security_javascript)
                for html in opaque_html:
                    pre_extension_policy.validate_pre_extension_html(html, component_classes=component_classes)
                pre_extension_policy.report()
            if citry.settings.security_csp != "off":
                csp = _CspRenderValidator(citry.settings.security_csp)
                for html in opaque_html:
                    csp.validate_pre_extension_html(html, component_classes=component_classes)
                csp.report()
        view = assembly.view
        occurrence_for_render = dict(assembly.render_to_occurrence)
        render_for_occurrence = dict(assembly.occurrence_to_render)
        selected_ids = frozenset(occurrence_for_render)
        browser_extensions = prepare_browser_extensions(
            citry=citry,
            context=render.context,
            selected_render=render,
            view=view,
            render_to_occurrence=occurrence_for_render,
            app_id=app_id,
            revision=revision,
            base_revision=base_revision,
            registrations=browser_plugin_registrations,
        )
        entries = [
            entry
            for entry in cast("dict[EventInstanceEntry, None]", render.context.extra.get(EXTRA_KEY, {}))
            if entry.render_id in selected_ids
        ]

        if _early_selected_tree is not None and _early_selected_tree.error_stage == "compile":
            if _early_selected_tree.error is None:
                raise AssertionError("early selected-tree compiler error is missing")
            raise _early_selected_tree.error
        compiled_by_definition = (
            _early_selected_tree.compiled_by_definition
            if _early_selected_tree is not None and _early_selected_tree.compiled_by_definition is not None
            else self._compile_view(assembly)
        )
        if set(compiled_by_definition) != {item.id for item in view.definitions}:
            raise ValueError("direct compiler output must exactly cover the prepared definitions")
        definition_ids = {logical_id: compiled.id for logical_id, compiled in compiled_by_definition.items()}

        # One shared bundle is intentional: every definition points to the same
        # content-addressed, same-origin script and the browser loads that URL once.
        unique_compiled = {item.id: item for item in compiled_by_definition.values()}
        bundle = "\n".join(item.javascript for item in unique_compiled.values()).encode()
        bundle_digest = hashlib.sha256(bundle).hexdigest()
        assets = tuple(
            DefinitionAsset(
                item.id,
                self._asset_url(bundle_digest),
                bundle_digest,
                item.target,
                HELPER_CONTRACT,
                tuple(
                    {"siteId": value.site_id, "name": value.name, "arg": value.arg, "modifiers": list(value.modifiers)}
                    for value in item.directive_signature
                ),
                item.replacement_sites,
                item.dynamic_elements,
                item.local_call_runs,
                item.local_calls,
                item.opaque_html_sites,
                item.runtime_event_sites,
            )
            for item in unique_compiled.values()
        )
        payload = (
            prepared_manifest(app_id=app_id, view=view, assets=assets, definition_ids=definition_ids)
            if base_revision is None
            else revision_envelope(
                app_id=app_id,
                base_revision=base_revision,
                view=view,
                assets=assets,
                updated_ids=tuple(item.id for item in view.occurrences),
                definition_ids=definition_ids,
            )
        )
        payload_occurrences = cast("list[dict[str, object]]", payload["occurrences"])
        opaque_record_values: list[object] = []
        for occurrence in payload_occurrences:
            prepared_data = cast("dict[str, object]", occurrence["preparedData"])
            opaque_data = cast("dict[str, dict[str, object]]", prepared_data.get("opaqueHtml", {}))
            opaque_record_values.extend(record["html"] for record in opaque_data.values())
        if any(type(html) is not str for html in opaque_record_values):
            raise AssertionError("prepared opaque HTML payload changed type")
        opaque_records = cast("list[str]", opaque_record_values)
        if opaque_records:
            from citry._csp_validation import _CspRenderValidator  # noqa: PLC0415
            from citry._javascript_policy import _JavascriptPolicy  # noqa: PLC0415

            options = dependency_options or {}
            supplied_policy = options.get("javascript_policy")
            javascript_mode = options.get("security_javascript", citry.settings.security_javascript)
            javascript_validator = supplied_policy
            if javascript_validator is None and javascript_mode != "allow":
                javascript_validator = _JavascriptPolicy(javascript_mode)
            csp_mode = options.get("security_csp", citry.settings.security_csp)
            csp_validator = None if csp_mode == "off" else _CspRenderValidator(csp_mode)
            if javascript_validator is not None or csp_validator is not None:
                component_classes = {
                    type_key: (
                        built_in_metadata.classes[type_key].__name__
                        if built_in_metadata is not None and type_key in built_in_metadata.classes
                        else citry.get_component_by_class_id(type_key).__name__
                    )
                    for type_key in {item.type_key for item in view.definitions}
                }
                for html in opaque_records:
                    if javascript_validator is not None:
                        javascript_validator.validate_settled_html(
                            html,
                            marker_prefix="data-cid-",
                            trusted_tag_starts=frozenset(),
                            component_classes=component_classes,
                        )
                    if csp_validator is not None:
                        csp_validator.validate_settled_html(
                            html,
                            marker_prefix="data-cid-",
                            trusted_tag_starts=frozenset(),
                            component_classes=component_classes,
                        )
            if supplied_policy is None and javascript_validator is not None:
                javascript_validator.report()
            if csp_validator is not None:
                csp_validator.report()
        type_policies: list[dict[str, object]] = []
        selected_type_keys = dict.fromkeys(item.type_key for item in view.definitions)
        for type_key in selected_type_keys:
            component = (
                built_in_metadata.classes[type_key]
                if built_in_metadata is not None and type_key in built_in_metadata.classes
                else citry.get_component_by_class_id(type_key)
            )
            lazy_allowed = (
                getattr(component.on_dependencies, "__func__", None)
                is getattr(Component.on_dependencies, "__func__", None)
                and not component.get_dependencies()
            )
            type_policies.append({"typeKey": type_key, "lazyAllowed": lazy_allowed})
        dependency_records = cast("dict[DependencyRecord, object]", render.context.extra.get("dependencies", {}))
        for record in dependency_records:
            if record.component_id not in selected_ids or record.component_class is None:
                continue
            if citry.get_component_by_class_id(record.class_id) is not record.component_class:
                raise ValueError("component class changed before Vue metadata preparation")
        # Resolve the public Dependencies surface through the same ordered
        # component hooks used by static serialization. This final list is
        # authoritative for native Vue too: a hook may remove or replace a
        # class asset before it becomes a browser-loader descriptor.
        from dataclasses import replace  # noqa: PLC0415

        from citry._serialization_security import _browser_loader_descriptor  # noqa: PLC0415
        from citry.ext.dependencies.emission import (  # noqa: PLC0415
            OnDependenciesContext,
            _resolve_records,
            _validate_hook_nonces,
        )

        options = dependency_options or {}
        script_security = options.get("script_security")
        javascript_policy = options.get("javascript_policy")
        resolved = _resolve_records(
            citry,
            [record for record in dependency_records if record.component_id in selected_ids],
            with_client_js=True,
            prepared_vue=True,
            script_security=script_security,
        )
        dependency_ctx = OnDependenciesContext(
            citry=citry,
            scripts=resolved.scripts,
            styles=resolved.styles,
            context=render.context,
            selected_render=render,
            strategy=options.get("strategy", "fragment" if base_revision is not None else "document"),
            early_scripts=[],
            _security_csp=options.get("security_csp", "off"),
            _security_javascript=options.get("security_javascript", "allow"),
        )
        citry.extensions.emit("on_dependencies", dependency_ctx)
        if dependency_options is not None:
            from citry.ext.dependencies.emission import VUE_DEPENDENCIES_PREPARED_KEY  # noqa: PLC0415

            render.context.extra[VUE_DEPENDENCIES_PREPARED_KEY] = True
        _validate_hook_nonces(
            script_security,
            dependency_ctx.scripts,
            dependency_ctx.styles,
            dependency_ctx.early_scripts,
        )
        # An interactive page has no static manifest to write tags ahead of.
        # The Vue app loads its scripts in list order, so loading these
        # entries first, in the order the hooks added them, keeps what static
        # output promises: they run before every other dependency script.
        # They are then ordinary scripts and follow the same loading rules.
        dependency_scripts = [*dependency_ctx.early_scripts, *dependency_ctx.scripts]
        dependency_styles = dependency_ctx.styles
        if javascript_policy is not None:
            dependency_scripts = javascript_policy.process_dependencies(
                dependency_scripts, position="prepared Vue dependency"
            )
            dependency_styles = javascript_policy.process_dependencies(
                dependency_styles, position="prepared Vue stylesheet"
            )
        scripts: list[dict[str, object]] = []
        styles: list[dict[str, object]] = []

        configured_nonce = getattr(script_security, "csp_nonce", None)

        def deferred_dependency(dependency: Dependency) -> Dependency:
            if configured_nonce is None:
                return dependency
            attrs = dict(dependency.attrs)
            for key in tuple(attrs):
                if key.lower() == "nonce":
                    attrs.pop(key)
            return replace(dependency, attrs=attrs)

        occurrence_types = {item.id: item.type_key for item in view.occurrences}

        def component_owners(dependency: Dependency, *, style: bool) -> list[dict[str, object]]:
            owners = (resolved.style_owners if style else resolved.script_owners).get(id(dependency), set())
            by_type: dict[str, list[str]] = {}
            for render_id in owners:
                occurrence_id = occurrence_for_render.get(render_id)
                if occurrence_id is None:
                    continue
                by_type.setdefault(occurrence_types[occurrence_id], []).append(occurrence_id)
            if not by_type:
                root = view.occurrences[0]
                by_type[root.type_key] = [root.id]
            return [
                {
                    "kind": "component",
                    "typeKey": type_key,
                    **({"occurrenceIds": sorted(set(ids))} if style else {}),
                }
                for type_key, ids in sorted(by_type.items())
            ]

        for values, target in ((dependency_scripts, scripts), (dependency_styles, styles)):
            is_style = target is styles
            for dependency in values:
                prepared_dependency = deferred_dependency(dependency)
                source = _browser_loader_descriptor(prepared_dependency)
                if source["kind"] == "inline":
                    content = cast("str", source.pop("content")).encode()
                    digest = hashlib.sha256(content).hexdigest()
                    if is_style:
                        self._publish_style(digest, content)
                    else:
                        self._publish_bundle(digest, content)
                    source = {
                        "kind": "owned",
                        "url": self._style_asset_url(digest) if is_style else self._asset_url(digest),
                        "sha256": digest,
                        "attrs": source["attrs"],
                    }
                if is_style:
                    cast("dict[str, object]", source["attrs"])["rel"] = "stylesheet"
                for owner in component_owners(dependency, style=is_style):
                    type_key = cast("str", owner["typeKey"])
                    policy = next(item for item in type_policies if item["typeKey"] == type_key)
                    target.append(
                        {
                            "owner": owner,
                            "source": source,
                            "lazyAllowed": policy["lazyAllowed"],
                            **(
                                {
                                    "registersOptions": dependency.kind == "component"
                                    and uses_component(citry.get_component_by_class_id(type_key))
                                }
                                if not is_style
                                else {}
                            ),
                        }
                    )

        def append_extension_assets(
            extension_asset: PreparedBrowserExtension,
            extension_sources: Sequence[Dependency],
            target: list[dict[str, object]],
        ) -> None:
            for dependency in extension_sources:
                source = _browser_loader_descriptor(dependency)
                if source["kind"] == "inline":
                    content = cast("str", source.pop("content")).encode()
                    digest = hashlib.sha256(content).hexdigest()
                    if target is styles:
                        self._publish_style(digest, content)
                    else:
                        self._publish_bundle(digest, content)
                    source = {
                        "kind": "owned",
                        "url": self._style_asset_url(digest) if target is styles else self._asset_url(digest),
                        "sha256": digest,
                        "attrs": source["attrs"],
                    }
                if target is styles:
                    cast("dict[str, object]", source["attrs"])["rel"] = "stylesheet"
                    dependency.attrs["data-citry-css-url"] = cast("str", source["url"])
                    dependency.attrs["data-citry-vue-style-app"] = app_id
                target.append(
                    {
                        "owner": {"kind": "extension", "extensionName": extension_asset.name},
                        "source": source,
                        "lazyAllowed": True,
                        **({"registersOptions": False} if target is scripts else {}),
                    }
                )

        for extension_asset in browser_extensions:
            append_extension_assets(extension_asset, extension_asset.scripts, scripts)
            append_extension_assets(extension_asset, extension_asset.styles, styles)
        payload["scripts"] = scripts
        _validate_script_assets(scripts)
        _validate_style_assets(styles, view)
        payload["styles"] = styles
        payload["typePolicies"] = type_policies
        payload["extensions"] = {
            item.name: {
                "schemaVersion": item.schema_version,
                "payload": item.payload,
                "templateContextNames": list(item.plugin.template_context_names),
            }
            for item in browser_extensions
        }

        extension = cast("EventsExtension", citry.extensions.get_extension("events"))
        events_manifest = build_events_manifest(extension, citry, entries)
        instances: dict[str, dict[str, object]] = {}
        for item in cast("list[dict[str, object]]", events_manifest["componentInstances"]):
            render_id = cast("str", item["renderId"])
            occurrence_id = occurrence_for_render[render_id]
            if occurrence_id in instances:
                raise ValueError("multiple Events instances matched one prepared occurrence")
            instances[occurrence_id] = item
        descriptors = {
            cast("str", item["componentClassId"]): item
            for item in cast("list[dict[str, object]]", events_manifest["componentClasses"])
        }
        occurrences = cast("list[dict[str, object]]", payload["occurrences"])
        for occurrence in occurrences:
            occurrence_id = cast("str", occurrence["id"])
            render_id = render_for_occurrence[occurrence_id]
            occurrence["renderId"] = render_id
            instance = instances.get(occurrence_id)
            if instance is None:
                continue
            class_id = cast("str", instance["componentClassId"])
            if instance["renderId"] != render_id:
                raise ValueError("Events instance does not match its canonical prepared occurrence render ID")
            if class_id != occurrence["typeKey"]:
                raise ValueError("Events instance class does not match its prepared occurrence type")
            component_class = citry.get_component_by_class_id(class_id)
            events_info = extension.resolve(component_class)
            if component_class.transparent or events_info.events_cls is None:
                raise ValueError("Events instance matched a component type without an Events declaration")
            if class_id not in descriptors:
                raise ValueError("Events instance has no matching component descriptor")
            occurrence["eventContext"] = {
                "serverRenderId": instance["renderId"],
                "stateToken": instance["stateToken"],
                "publicState": instance["publicState"],
                "componentClassId": class_id,
                "descriptor": descriptors[class_id],
            }
        self._publish_bundle(bundle_digest, bundle)

        def validate_metadata() -> None:
            validate_browser_plugin_registrations(citry, browser_plugin_registrations)
            for browser_extension in browser_extensions:
                browser_extension.validate()
            if built_in_metadata is None:
                return
            if (
                self._builtin_citry_ref is not built_in_identity[0]
                or self._builtin_tag_callback is not built_in_identity[1]
                or self._tag_for_type is not built_in_identity[2]
                or not self._uses_builtin_metadata(citry)
            ):
                raise ValueError("built-in Vue metadata configuration changed during preparation")
            built_in_metadata.validate()

        validate_metadata()
        cached_tags = (
            {
                type_key: built_in_metadata.tags[type_key]
                for type_key in dict.fromkeys(item.type_key for item in view.occurrences)
                if type_key in built_in_metadata.tags
            }
            if built_in_metadata is not None
            else None
        )
        return _PreparedResult(payload, cached_tags, validate_metadata, browser_extensions)


def native_compile_view(
    compiler: NativeCompiler,
) -> Callable[[Assembly], dict[str, CompiledRender]]:
    """Bind the direct prepared compiler input adapter to one persistent compiler."""

    def compile_view(assembly: Assembly) -> dict[str, CompiledRender]:
        definitions = {item.id: item for item in assembly.view.definitions}
        compiled = {
            definition_id: compiler.compile(
                value.template,
                type_key=definitions[definition_id].type_key,
                dynamic_elements=value.dynamic_elements,
                template_context_names=value.template_context_names,
                directive_signature=definitions[definition_id].directive_signature,
                local_calls=value.local_calls,
                element_bindings=value.element_bindings,
                local_call_runs=value.local_call_runs,
                opaque_html_sites=value.opaque_html_sites,
                runtime_event_sites=value.runtime_event_sites,
            )
            for definition_id, value in assembly.compile_inputs.items()
        }
        check_directive_roots(assembly, compiled)
        return compiled

    return compile_view


_UNSHOWABLE_ROOTS = {
    "fragment": "its template has several top-level nodes, or a 'v-for', '<c-for>', or '<c-slot>' at the top level",
    "text": "its template renders only text",
    "opaque-html": "its template renders HTML from Python (such as '<c-raw>' or trusted markup) at the top level",
}


def check_directive_roots(assembly: Assembly, compiled: Mapping[str, CompiledRender]) -> None:
    """
    Reject a caller's ``v-show`` or custom directive that Vue would skip without an error.

    Vue applies these directives on a component tag to the element the child
    renders at its root. For a child whose compiled render returns several
    roots, only text, or HTML from Python, Vue does nothing, so the page would
    keep showing content the author meant to hide, or miss the directive's
    behavior. A child whose root is another component, or whose shape the
    reader cannot tell, is left to the browser runtime check.

    Raises:
        RuntimeError: When such a child's selected render cannot carry the
            directive.

    """
    occurrences = {item.id: item for item in assembly.view.occurrences}
    for occurrence_id, (class_name, tag, directive) in assembly.root_directive_occurrences.items():
        shape = compiled[occurrences[occurrence_id].definition_id].root_shape
        reason = _UNSHOWABLE_ROOTS.get(shape)
        if reason is not None:
            msg = (
                f"{directive!r} on <{tag}> needs component {class_name!r} to render one root element, but "
                f"{reason}. Vue would ignore {directive!r} there. Wrap the child's template in one element, or put "
                f"{directive!r} on an element around <{tag}>."
            )
            raise RuntimeError(msg)


def _validate_style_assets(styles: list[dict[str, object]], view: PreparedViewMetadata) -> None:
    occurrences = {item.id: item.type_key for item in view.occurrences}
    urls: dict[str, dict[str, object]] = {}
    expected_keys = {"owner", "source", "lazyAllowed"}
    for style in styles:
        if type(style) is not dict or set(style) != expected_keys:
            raise ValueError("prepared style asset has an invalid shape")
        owner, source = style["owner"], style["source"]
        if type(owner) is not dict or type(source) is not dict:
            raise ValueError("prepared style asset metadata is invalid")
        url, digest = source.get("url"), source.get("sha256")
        component = owner.get("kind") == "component"
        type_key, ids = owner.get("typeKey"), owner.get("occurrenceIds")
        if (
            type(url) is not str
            or (source.get("kind") == "owned" and (not url.startswith("/") or "//" in url))
            or (url in urls and urls[url] != source)
            or type(style["lazyAllowed"]) is not bool
            or (
                source.get("kind") == "owned"
                and (type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None)
            )
            or (source.get("kind") == "external" and set(source) != {"kind", "url", "attrs"})
            or (
                source.get("kind") == "owned"
                and set(source) not in ({"kind", "url", "sha256"}, {"kind", "url", "sha256", "attrs"})
            )
            or source.get("kind") not in {"owned", "external"}
            or type(source.get("attrs")) is not dict
            or cast("dict[str, object]", source["attrs"]).get("rel") != "stylesheet"
            or (
                component
                and (
                    set(owner) != {"kind", "typeKey", "occurrenceIds"}
                    or type(type_key) is not str
                    or type(ids) is not list
                    or not ids
                    or ids != sorted(set(ids))
                    or any(type(item) is not str or occurrences.get(item) != type_key for item in ids)
                )
            )
            or (
                not component
                and (
                    owner.get("kind") != "extension"
                    or set(owner) != {"kind", "extensionName"}
                    or type(owner.get("extensionName")) is not str
                )
            )
        ):
            raise ValueError("prepared style asset metadata is invalid")
        urls[url] = source


def _validate_script_assets(scripts: list[dict[str, object]]) -> None:
    urls: dict[str, dict[str, object]] = {}
    for script in scripts:
        if type(script) is not dict or set(script) != {"owner", "source", "lazyAllowed", "registersOptions"}:
            raise ValueError("prepared script asset has an invalid shape")
        owner, source = script["owner"], script["source"]
        if type(owner) is not dict or type(source) is not dict or type(script["lazyAllowed"]) is not bool:
            raise ValueError("prepared script asset metadata is invalid")
        component = owner.get("kind") == "component"
        if (
            type(script["registersOptions"]) is not bool
            or (component and (set(owner) != {"kind", "typeKey"} or type(owner.get("typeKey")) is not str))
            or (
                not component
                and (
                    owner.get("kind") != "extension"
                    or set(owner) != {"kind", "extensionName"}
                    or type(owner.get("extensionName")) is not str
                    or script["registersOptions"]
                )
            )
            or type(source.get("url")) is not str
            or source.get("kind") not in {"owned", "external"}
            or (
                source.get("kind") == "owned"
                and (
                    type(source.get("sha256")) is not str
                    or re.fullmatch(r"[0-9a-f]{64}", cast("str", source.get("sha256"))) is None
                )
            )
            or (source.get("kind") == "external" and set(source) != {"kind", "url", "attrs"})
            or (
                source.get("kind") == "owned"
                and set(source) not in ({"kind", "url", "sha256"}, {"kind", "url", "sha256", "attrs"})
            )
            or (source["url"] in urls and urls[source["url"]] != source)
        ):
            raise ValueError("prepared script asset metadata is invalid")
        urls[cast("str", source["url"])] = source
