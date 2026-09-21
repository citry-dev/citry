"""Private two-phase Vue document serialization."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from secrets import token_hex
from typing import TYPE_CHECKING, Any, cast

from citry._vue.capture import PreparedElementOpen
from citry.citry_render import CitryRender
from citry.ext.dependencies.scripts import has_component_asset
from citry.ext.dependencies.types import DependencyRecord, Script, Style
from citry.util.id import validate_render_id

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry._javascript_policy import _JavascriptPolicy
    from citry._serialization_security import _ScriptSecurityMaterializer
    from citry.citry_context import CitryContext
    from citry.ext.events.emission import EventInstanceEntry
    from citry.extension import OnSerializeContext
    from citry.settings import SecurityCspMode, SecurityJavascriptMode


_BODY_OPEN_RE = re.compile(r"<body(?:\s[^>]*)?>", re.IGNORECASE)
_BODY_CLOSE_RE = re.compile(r"</body\s*>", re.IGNORECASE)


class _HostValidator(HTMLParser):
    def __init__(self, host_id: str) -> None:
        super().__init__(convert_charrefs=False)
        self.host_id = host_id
        self.count = 0
        self.depth = 0
        self.empty = True
        self.valid_attrs = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if any(name == "id" and value == self.host_id for name, value in attrs):
            self.count += 1
            if tag != "div" or attrs != [("id", self.host_id)] or self.depth:
                self.valid_attrs = False
            else:
                self.depth = 1
            return
        if self.depth:
            self.empty = False
            self.depth += 1

    def handle_startendtag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if any(name == "id" and value == self.host_id for name, value in attrs):
            self.count += 1
            self.valid_attrs = False

    def handle_endtag(self, _tag: str) -> None:
        if self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth and data:
            self.empty = False

    # An entity, a character reference, and a comment each count as content for the
    # emptiness test, and the parser hands each of them a different string (a name
    # rather than text), so they delegate rather than alias: only presence matters.
    def handle_entityref(self, name: str) -> None:
        self.handle_data(name)

    def handle_charref(self, name: str) -> None:
        self.handle_data(name)

    def handle_comment(self, data: str) -> None:
        self.handle_data(data)


@dataclass(frozen=True, slots=True)
class VueSerializationPlan:
    """A prepared immutable app plus the exact host threaded through extension hooks."""

    shell_html: str
    host_id: str
    configuration: str
    scripts: tuple[Script, ...]
    styles: tuple[Style, ...]
    script_security: _ScriptSecurityMaterializer | None
    javascript_policy: _JavascriptPolicy | None
    render_context: CitryContext
    validate_metadata: Callable[[], None]
    deferred_to_dependency_manager: bool = False

    def finalize(self, hooked_html: str) -> str:
        """Validate the hook result and place the prepared assets in the document."""
        validator = _HostValidator(self.host_id)
        validator.feed(hooked_html)
        validator.close()
        canonical_host = f'<div id="{self.host_id}"></div>'
        if (
            validator.count != 1
            or validator.depth
            or not validator.empty
            or not validator.valid_attrs
            or hooked_html.count(canonical_host) != 1
        ):
            raise ValueError("Vue serialization hooks must preserve exactly one empty Citry mount host.")
        self.validate_metadata()
        if self.deferred_to_dependency_manager:
            return hooked_html
        scripts = list(self.scripts)
        from citry.ext.dependencies.emission import VUE_RUNTIME_EMITTED_KEY  # noqa: PLC0415

        if self.render_context.extra.get(VUE_RUNTIME_EMITTED_KEY):
            from citry.ext.dependencies.routes import runtime_url  # noqa: PLC0415

            runtime = scripts[0]
            plan_runtime_present = (
                f'src="{escape(runtime.url, quote=True)}"' in hooked_html
                if runtime.url is not None
                else "Citry interactive runtime" in hooked_html
            )
            component = self.render_context.component
            citry = component.citry if component is not None else None
            dependency_runtime_present = (
                citry is not None
                and citry.mounted_prefix is not None
                and f'src="{escape(runtime_url(citry), quote=True)}"' in hooked_html
            )
            if not plan_runtime_present and not dependency_runtime_present:
                raise ValueError("Vue serialization hooks removed the required Citry runtime asset.")
            scripts.pop(0)
        styles = list(self.styles)
        if self.javascript_policy is not None:
            scripts = self.javascript_policy.process_dependencies(scripts, position="Vue bootstrap")
            styles = self.javascript_policy.process_dependencies(styles, position="Vue extension stylesheet")
        rendered_styles = "".join(
            str(item.render()) if self.script_security is None else self.script_security.render_style(item)
            for item in styles
        )
        rendered = "".join(
            str(item.render()) if self.script_security is None else self.script_security.render(item)
            for item in scripts
        )
        # Keep the same default placement contract as the ordinary dependency
        # emitter.  Appending the assets after a complete document produces
        # technically invalid HTML and can make the browser execute the
        # bootstrap only after it has closed ``</html>``.  The helper also
        # preserves the established prepend/append fallback for fragments.
        from citry.ext.dependencies.emission import _insert_default  # noqa: PLC0415

        if rendered_styles:
            hooked_html = _insert_default(hooked_html, rendered_styles, kind="css")
        if rendered:
            hooked_html = _insert_default(hooked_html, rendered, kind="js")
        return hooked_html


@dataclass(frozen=True, slots=True)
class VueSerializationAnalysis:
    """Selected browser requirements shared by policy and Vue preparation."""

    runtime_requirements: frozenset[str]
    active_policy_requirements: frozenset[str]


def _component_tags_for_manifest(
    producer: Any, manifest: dict[str, Any], cached_tags: dict[str, str] | None
) -> dict[str, str]:
    tags = {} if cached_tags is None else cached_tags
    cached_type_keys = frozenset(tags)
    for item in manifest["occurrences"]:
        type_key = item["typeKey"]
        if type_key not in cached_type_keys:
            tags[type_key] = producer.component_tag(type_key)
    return tags


def _prepare_initial_result(
    producer: Any,
    render: CitryRender,
    citry: Any,
    app_id: str,
    *,
    include_extensions: bool = False,
    dependency_options: dict[str, object] | None = None,
) -> tuple[Any, ...]:
    from citry._vue.events import DirectVueEventsProducer  # noqa: PLC0415

    if (
        "prepare_from_render" not in vars(producer)
        and getattr(producer.prepare_from_render, "__func__", None) is DirectVueEventsProducer.prepare_from_render
    ):
        result = producer._prepare_from_render_result(
            render,
            citry=citry,
            app_id=app_id,
            revision=0,
            dependency_options=dependency_options,
        )
        base = (result.payload, result.tags, result.validate)
        return (*base, result.extensions) if include_extensions else base
    base = (producer.prepare_from_render(render, citry=citry, app_id=app_id, revision=0), None, lambda: None)
    return (*base, ()) if include_extensions else base


def _selected_renders(render: CitryRender) -> list[CitryRender]:
    selected: list[CitryRender] = []
    pending = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        selected.append(current)
        pending.extend(part for part in current.parts if isinstance(part, CitryRender))
    return selected


def _record_component_has_js(record: DependencyRecord, render: CitryRender) -> bool:
    """Whether the class behind one dependency record carries component JavaScript."""
    # The record normally keeps the exact class that produced it, so hot replacement
    # cannot pair an old body with a new class's assets.
    component_class = record.component_class
    if component_class is None:
        # Only a class id survived, so resolve it through the registry the render
        # belongs to. A render with no component cannot reach a registry at all.
        component = render.context.component
        if component is None:
            # Leaving the runtime out would break a component that does have JS,
            # while including it only costs payload, so assume it is needed.
            return True
        component_class = component.citry.get_component_by_class_id(record.class_id)
    return has_component_asset("js", component_class)


def analyze_vue_serialization(render: CitryRender) -> VueSerializationAnalysis:
    """Inspect selected typed metadata without invoking Assembly or the native compiler."""
    renders = _selected_renders(render)
    selected_ids = frozenset(
        current.frame.render_id
        for current in renders
        if current.frame.is_component_root and current.frame.render_id is not None
    )
    requirements: set[str] = set()
    active_policy: set[str] = set()
    if any(current.frame.is_component_root and current.context.js_data for current in renders):
        requirements.add("js_data")
        active_policy.add("js_data")
    if any(
        current.frame.is_component_root
        and current.frame.prepared_occurrence is not None
        and current.frame.prepared_occurrence.component_tag_client_bindings
        for current in renders
    ):
        requirements.add("vue_binding")
        active_policy.add("vue_binding")
    dependency_records = cast("dict[DependencyRecord, object]", render.context.extra.get("dependencies", {}))
    if any(
        record.component_id in selected_ids and _record_component_has_js(record, render)
        for record in dependency_records
    ):
        requirements.add("component_js")
    event_records = cast("dict[EventInstanceEntry, object]", render.context.extra.get("events", {}))
    if any(record.render_id in selected_ids for record in event_records):
        requirements.add("events")
    from citry._vue.leaf_program import PreparedLeafProgram  # noqa: PLC0415

    for current in renders:
        for part in current.parts:
            if isinstance(part, PreparedElementOpen):
                if (
                    part.event_bindings
                    or part.poll_bindings
                    or part.control_bindings
                    or part.runtime_event_bindings
                    or part.runtime_poll_bindings
                ):
                    requirements.add("events")
                    active_policy.add("events")
                elif part.runtime_events_candidate:
                    requirements.add("events")
                if part.browser_bindings:
                    requirements.add("vue_binding")
                    active_policy.add("vue_binding")
            if isinstance(part, PreparedLeafProgram):
                data = part.prepared_data
                if any(data.get(name) for name in ("eventBindings", "pollBindings", "controlBindings")):
                    requirements.add("events")
                    active_policy.add("events")
                requirements.update(part.fragment.browser_requirements)
    if any(
        isinstance(part, PreparedElementOpen)
        and any(attr.name.startswith(("@c-", ":c-", "v-", "@", ":", "#")) for attr in part.attrs)
        for current in renders
        for part in current.parts
    ):
        requirements.add("vue_binding")
    return VueSerializationAnalysis(frozenset(requirements), frozenset(active_policy))


def vue_serialization_requirements(render: CitryRender) -> frozenset[str]:
    return analyze_vue_serialization(render).runtime_requirements


def _reject_head_browser_activity(render: CitryRender, head_only_render_ids: frozenset[str]) -> None:
    """Reject browser behavior whose selected occurrence is excluded from the Vue body."""
    if not head_only_render_ids:
        return
    renders = _selected_renders(render)
    if any(current.frame.render_id in head_only_render_ids and current.context.js_data for current in renders):
        raise ValueError("Component js_data is unsupported in the physical document head.")
    component = render.context.component
    if component is None:
        raise ValueError("Interactive Vue document serialization requires a component-owned root.")
    dependency_records = cast("dict[DependencyRecord, object]", render.context.extra.get("dependencies", {}))
    if any(
        record.component_id in head_only_render_ids
        and has_component_asset(
            "js", record.component_class or component.citry.get_component_by_class_id(record.class_id)
        )
        for record in dependency_records
    ):
        raise ValueError("Component JavaScript is unsupported in the physical document head.")
    event_records = cast("dict[EventInstanceEntry, object]", render.context.extra.get("events", {}))
    if any(record.render_id in head_only_render_ids for record in event_records):
        raise ValueError("Events are unsupported in the physical document head.")


def _vue_shell(html: str, host: str) -> str:
    """Preserve a document's physical shell while replacing its logical body UI."""
    openings = list(_BODY_OPEN_RE.finditer(html))
    closings = list(_BODY_CLOSE_RE.finditer(html))
    document = bool(re.search(r"<!doctype\s|<html(?:\s|>)|<head(?:\s|>)|<body(?:\s|>)", html, re.IGNORECASE))
    if not document:
        return host
    if len(openings) != 1 or len(closings) != 1 or openings[0].end() > closings[0].start():
        raise ValueError("Interactive Vue document serialization requires exactly one well-ordered body element.")
    return html[: openings[0].end()] + host + html[closings[0].start() :]


def prepare_vue_serialization(
    ctx: OnSerializeContext,
    script_security: _ScriptSecurityMaterializer | None,
    _security_csp: SecurityCspMode,
    javascript_policy: _JavascriptPolicy | None,
    security_javascript: SecurityJavascriptMode,
    analysis: VueSerializationAnalysis | None = None,
) -> VueSerializationPlan | None:
    """Prepare a browser app only when selected typed metadata requires Vue."""
    requirements = (analysis or analyze_vue_serialization(ctx.selected_render)).runtime_requirements
    if ctx.selected_render.render_target != "prepared" or not requirements:
        return None
    if ctx.deps_strategy in {"simple", "ignore"}:
        # These public strategies deliberately do not install a client
        # runtime. Keep the settled server fallback and let the call-local
        # JavaScript policy inspect that exact output.
        return None
    if ctx.deps_strategy not in {"document", "fragment"}:
        if requirements == {"component_js"}:
            return None
        raise ValueError("Interactive Vue serialization requires deps_strategy='document' or 'fragment'.")
    if security_javascript in {"omit", "forbid"}:
        return None

    from citry._vue.events import default_events_producer, definition_bundle  # noqa: PLC0415
    from citry.ext.events.routes import EVENTS_RUNTIME_SRC, RUNTIME_PATH, _runtime_resource  # noqa: PLC0415

    if "_vue_app_id" in ctx.context.extra:
        app_id = ctx.context.extra["_vue_app_id"]
        if type(app_id) is not str:
            raise TypeError("Vue render-local app ID metadata must be a string.")
    elif ctx.citry.id_generator is None:
        app_id = token_hex(16)
        ctx.context.extra["_vue_app_id"] = app_id
    else:
        # Reuse the same validation as component render IDs.  The explicit
        # generator is a deterministic test/snapshot hook; hash its validated
        # value so the app protocol keeps its existing fixed 32-hex shape.
        generated = validate_render_id(ctx.citry.id_generator())
        app_id = hashlib.sha256(generated.encode("utf-8")).hexdigest()[:32]
        ctx.context.extra["_vue_app_id"] = app_id
    ctx.context.extra["_vue_style_app_id"] = app_id
    producer = default_events_producer(ctx.citry)
    from citry._vue.document import typed_document_shell  # noqa: PLC0415

    typed_shell = typed_document_shell(ctx.selected_render, f'<div id="citry-vue-{app_id}"></div>')
    if typed_shell is not None:
        _reject_head_browser_activity(ctx.selected_render, typed_shell.head_only_render_ids)
    manifest, tags, validate_metadata, prepared_extensions = _prepare_initial_result(
        producer,
        ctx.selected_render,
        ctx.citry,
        app_id,
        include_extensions=True,
        dependency_options={
            "script_security": script_security,
            "security_csp": _security_csp,
            "javascript_policy": javascript_policy,
            "security_javascript": security_javascript,
            "strategy": ctx.deps_strategy,
        },
    )
    browser_plugins = {item.name: item.plugin for item in prepared_extensions}
    if any(plugin is None for plugin in browser_plugins.values()):
        raise TypeError("A prepared browser extension has no registered plugin descriptor.")
    has_events = any("eventContext" in item for item in manifest["occurrences"])
    if has_events and (
        security_javascript != ctx.citry.settings.security_javascript
        or _security_csp != ctx.citry.settings.security_csp
    ):
        raise ValueError(
            "Call-local JavaScript/CSP overrides are unsupported for revisable Events apps; "
            "configure the same policy on Citry settings so later revisions retain it."
        )
    mounted = ctx.citry.mounted_prefix is not None
    if has_events and not mounted:
        raise ValueError("Components with Events require a mounted web integration for Vue serialization.")
    tags = _component_tags_for_manifest(producer, manifest, tags)
    dependency_hooks = ctx.citry.extensions._extensions_with_hook("on_dependencies")
    from citry.ext.i18n.extension import I18nExtension  # noqa: PLC0415

    def permits_owned_late_assets(extension: Any) -> bool:
        if plugin_policies.get(extension.name) is True:
            return True
        return (
            type(extension) is I18nExtension
            and not extension.configured
            and "on_dependencies" not in vars(extension)
            and getattr(extension.on_dependencies, "__func__", None) is I18nExtension.on_dependencies
        )

    plugin_policies = {
        name: cast("Any", plugin).allows_late_component_assets for name, plugin in browser_plugins.items()
    }
    allow_lazy_type_assets = security_javascript == "allow" and all(
        permits_owned_late_assets(hook) for hook in dependency_hooks
    )
    host_id = f"citry-vue-{app_id}"
    configuration = {
        "manifest": manifest,
        "host": f"#{host_id}",
        "tags": tags,
        "allowLazyTypeAssets": allow_lazy_type_assets,
        # Mounted applications fetch the content-addressed dependency URLs.
        # Standalone serialization emits those exact assets into the document
        # below and asks the runtime to adopt them instead.
        "loadInitialAssets": mounted,
    }
    if script_security is not None and script_security.csp_nonce is not None:
        configuration["nonce"] = script_security.csp_nonce
    if mounted:
        configuration["endpoint"] = ctx.citry.build_url("ext/events/call")
        configuration["eventBaseUrl"] = ctx.citry.build_url("ext/events/e/")
    serialized = json.dumps(configuration, allow_nan=False, separators=(",", ":"), sort_keys=True).replace(
        "<", "\\u003c"
    )
    scripts: list[Script] = []
    if mounted:
        runtime = Script(kind="core", url=ctx.citry.build_url(RUNTIME_PATH))
        runtime._owned_resource = _runtime_resource(ctx.citry)
        scripts.append(runtime)
    else:
        scripts.append(Script(kind="core", content=EVENTS_RUNTIME_SRC.read_text()))
        for digest in dict.fromkeys(item["sha256"] for item in manifest["definitions"]):
            bundle = definition_bundle(ctx.citry, digest)
            if bundle is None:
                raise RuntimeError("A prepared Vue definition bundle was not published.")
            scripts.append(Script(kind="core", content=bundle.decode()))
        from citry._vue.events import style_asset  # noqa: PLC0415

        # Standalone HTML has no asset routes. Materialize every prepared
        # dependency before startPrepared while retaining the descriptor URL
        # as the runtime's ownership identity.
        emitted_script_sources: set[str] = set()
        for asset in manifest["scripts"]:
            source = asset["source"]
            source_identity = json.dumps(source, allow_nan=False, separators=(",", ":"), sort_keys=True)
            if source_identity in emitted_script_sources:
                continue
            emitted_script_sources.add(source_identity)
            attrs = dict(source.get("attrs", {}))
            if source["kind"] == "owned":
                body = definition_bundle(ctx.citry, source["sha256"])
                if body is None:
                    raise RuntimeError("A prepared Vue script asset was not retained for standalone serialization.")
                scripts.append(Script(kind="core", content=body.decode(), attrs=attrs))
            else:
                scripts.append(Script(kind="core", url=source["url"], attrs=attrs))
    scripts.extend(cast("Any", plugin).script for plugin in browser_plugins.values())
    standalone_styles: list[Style] = []
    if not mounted:
        emitted_style_sources: set[str] = set()
        for asset in manifest["styles"]:
            source = asset["source"]
            source_identity = json.dumps(source, allow_nan=False, separators=(",", ":"), sort_keys=True)
            if source_identity in emitted_style_sources:
                continue
            emitted_style_sources.add(source_identity)
            attrs = dict(source.get("attrs", {}))
            attrs["data-citry-css-url"] = source["url"]
            attrs["data-citry-vue-style-app"] = app_id
            if source["kind"] == "owned":
                body = style_asset(ctx.citry, source["sha256"])
                if body is None:
                    raise RuntimeError("A prepared Vue stylesheet was not retained for standalone serialization.")
                standalone_styles.append(Style(kind="core", content=body.decode(), attrs=attrs))
            else:
                standalone_styles.append(Style(kind="core", url=source["url"], attrs=attrs))
    # Browser contribution assets are already represented exactly once in the
    # validated manifest. Mounted apps load them; standalone apps materialize
    # them above. Only the plugin registration scripts remain direct.
    styles = () if mounted else tuple(standalone_styles)
    scripts.append(
        Script(
            kind="core",
            content=(
                f"CitryStable.startPrepared({serialized}).catch(error => queueMicrotask(() => {{ throw error; }}));"
            ),
        )
    )
    validate_metadata()
    deferred = ctx.deps_strategy == "fragment"
    if deferred:
        from citry.ext.dependencies.emission import (  # noqa: PLC0415
            VUE_FRAGMENT_MOUNT_KEY,
        )

        ctx.context.extra[VUE_FRAGMENT_MOUNT_KEY] = {
            "protocol": "citry-vue-fragment/1",
            "appId": app_id,
            "host": f"#{host_id}",
            "prepared": json.loads(serialized),
        }
    else:
        from citry.ext.dependencies.emission import VUE_RUNTIME_REQUIRED_KEY  # noqa: PLC0415

        ctx.context.extra[VUE_RUNTIME_REQUIRED_KEY] = True
    return VueSerializationPlan(
        shell_html=_vue_shell(ctx.html, f'<div id="{host_id}"></div>'),
        host_id=host_id,
        configuration=serialized,
        scripts=tuple(scripts),
        styles=styles,
        script_security=script_security,
        javascript_policy=javascript_policy,
        render_context=ctx.context,
        validate_metadata=validate_metadata,
        deferred_to_dependency_manager=deferred,
    )
