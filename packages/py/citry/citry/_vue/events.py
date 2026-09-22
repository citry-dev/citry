"""Private composition of direct prepared rendering with an Events occurrence."""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, cast
from weakref import WeakKeyDictionary, ref

from citry._vue.capture import render_prepared_direct, render_prepared_marker_replacement
from citry._vue.compiler import HELPER_CONTRACT, CompiledRender, NativeCompiler
from citry._vue.direct_capture import Assembly, assemble_typed_render
from citry._vue.protocol import DefinitionAsset, prepared_manifest, revision_envelope
from citry.citry import Citry
from citry.citry_element import CitryElement
from citry.component import Component, ComponentMeta
from citry.ext.dependencies.scripts import uses_component
from citry.ext.events.emission import EXTRA_KEY, EventInstanceEntry, build_events_manifest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

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


_BUNDLES: WeakKeyDictionary[Citry, OrderedDict[str, bytes]] = WeakKeyDictionary()
_STYLE_ASSETS: WeakKeyDictionary[Citry, OrderedDict[str, bytes]] = WeakKeyDictionary()
_PRODUCERS: WeakKeyDictionary[Citry, DirectVueEventsProducer] = WeakKeyDictionary()


class _DependencyOptions(TypedDict, total=False):
    script_security: _ScriptSecurityMaterializer
    security_csp: SecurityCspMode
    javascript_policy: _JavascriptPolicy
    security_javascript: SecurityJavascriptMode
    strategy: str


def _format_default_component_tag(type_key: str, component: type[Component]) -> str:
    words = re.sub(r"(?<!^)(?=[A-Z])", "-", component.__name__).lower()
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


def definition_bundle(citry: Citry, digest: str) -> bytes | None:
    """Return one engine-owned immutable compiled definition bundle."""
    bundles = _BUNDLES.get(citry)
    return None if bundles is None else bundles.get(digest)


def style_asset(citry: Citry, digest: str) -> bytes | None:
    """Return one engine-owned immutable prepared stylesheet."""
    styles = _STYLE_ASSETS.get(citry)
    return None if styles is None else styles.get(digest)


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
        bundles = _BUNDLES.setdefault(current(), OrderedDict())
        prior = bundles.get(digest)
        if prior is not None and prior != content:
            raise RuntimeError("Vue definition bundle digest collision.")
        bundles[digest] = content
        bundles.move_to_end(digest)
        while len(bundles) > 128:
            bundles.popitem(last=False)

    def publish_style(digest: str, content: bytes) -> None:
        assets = _STYLE_ASSETS.setdefault(current(), OrderedDict())
        prior = assets.get(digest)
        if prior is not None and prior != content:
            raise RuntimeError("Vue stylesheet asset digest collision.")
        assets[digest] = content
        assets.move_to_end(digest)
        while len(assets) > 128:
            assets.popitem(last=False)

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
    ) -> _PreparedResult:
        """Prepare initial or event output without rendering the selected tree again."""
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
            _BuiltInPreparationMetadata(citry, self._tag_for_type) if self._uses_builtin_metadata(citry) else None
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
        assembly = assemble_typed_render(
            render,
            revision=revision,
            tag_for_type=self._tag_for_type,
            component_metadata_for_type=(built_in_metadata.resolve if built_in_metadata is not None else None),
            root_occurrence_id=root_occurrence_id,
            template_context_names=template_context_names,
            expected_citry=citry,
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

        compiled_by_definition = self._compile_view(assembly)
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
            javascript_validator = (
                supplied_policy
                if supplied_policy is not None
                else _JavascriptPolicy(options.get("security_javascript", citry.settings.security_javascript))
            )
            csp_validator = _CspRenderValidator(options.get("security_csp", citry.settings.security_csp))
            component_classes = {
                type_key: (
                    built_in_metadata.classes[type_key].__name__
                    if built_in_metadata is not None and type_key in built_in_metadata.classes
                    else citry.get_component_by_class_id(type_key).__name__
                )
                for type_key in {item.type_key for item in view.definitions}
            }
            for html in opaque_records:
                javascript_validator.validate_settled_html(
                    html,
                    marker_prefix="data-cid-",
                    trusted_tag_starts=frozenset(),
                    component_classes=component_classes,
                )
                csp_validator.validate_settled_html(
                    html,
                    marker_prefix="data-cid-",
                    trusted_tag_starts=frozenset(),
                    component_classes=component_classes,
                )
            if supplied_policy is None:
                javascript_validator.report()
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
            before_manifest=[],
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
            dependency_ctx.before_manifest,
        )
        if dependency_ctx.before_manifest:
            raise RuntimeError(
                "Interactive dependency hooks must contribute Script and Style assets through their normal lists; "
                "before_manifest is unsupported by the prepared Vue transaction."
            )
        dependency_scripts = dependency_ctx.scripts
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
        return {
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

    return compile_view


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
