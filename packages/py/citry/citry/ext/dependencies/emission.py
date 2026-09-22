"""
Turning collected dependency records into JS/CSS tags in the final HTML.

This is the serialize-time half of the dependencies extension. The render
collected one :class:`DependencyRecord` per component instance (bubbled up to
the root context); this module resolves those records into ``Script``/``Style``
objects, lets components and extensions adjust the lists, renders the tags,
and places them into the page:

- into the ``<c-js>`` / ``<c-css>`` placeholders when the template has them
  (the first one in document order gets the tags, later ones are removed),
- otherwise CSS goes before the first ``</head>`` and JS before the last
  ``</body>``,
- and when neither exists, CSS is prepended and JS appended to the output.

Design: docs/design/dependencies.md section 7.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from citry._owned_resource import _OwnedResource
from citry.assets import HasHtml
from citry.citry_render import CitryRender, selected_render_ids
from citry.ext.dependencies.routes import RUNTIME_PATH, runtime_url, script_url
from citry.ext.dependencies.scripts import (
    cache_asset,
    cache_component_css,
    cache_component_js,
    gen_asset_cache_key,
    get_component_script,
    get_script,
    has_component_asset,
    uses_component,
)
from citry.ext.dependencies.types import Dependency, Script, Style
from citry.util.html import Markup

if TYPE_CHECKING:
    from citry._javascript_policy import _JavascriptPolicy
    from citry._serialization_security import _ScriptSecurityMaterializer
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.component import Component
    from citry.ext.dependencies.types import DependencyRecord
    from citry.extension import OnSerializeContext
    from citry.settings import SecurityCspMode, SecurityJavascriptMode

# The key under which the extension keeps its records in CitryContext.extra.
EXTRA_KEY = "dependencies"
VUE_RUNTIME_EMITTED_KEY = "vue_runtime_emitted"
VUE_RUNTIME_REQUIRED_KEY = "vue_runtime_required"
VUE_FRAGMENT_MOUNT_KEY = "vue_fragment_mount"
VUE_DEPENDENCIES_PREPARED_KEY = "vue_dependencies_prepared"

# The Placeholder keys the <c-js> / <c-css> built-ins render. The serializer
# makes each occurrence unique by appending a counter and private
# per-serialization identity ("deps:js:1:<identity>", ...).
JS_PLACEHOLDER_KEY = "deps:js"
CSS_PLACEHOLDER_KEY = "deps:css"


@dataclass(frozen=True, slots=True)
class OnDependenciesContext:
    """
    Context for the ``on_dependencies`` hook, owned by the dependencies
    extension (not a "core" hook: any extension that defines an
    ``on_dependencies`` method receives it, via the manager's ``emit``).

    Fires at serialize time with the final, deduplicated tag lists (possibly
    empty), just before they are rendered into the page. Mutate the lists in
    place to add, remove, or reorder entries.
    """

    citry: Citry
    """The ``Citry`` instance the render belongs to."""
    scripts: list[Dependency]
    """The ``<script>`` entries about to be emitted, in document order (mutable)."""
    styles: list[Dependency]
    """The stylesheet entries about to be emitted, in document order (mutable)."""
    context: CitryContext
    """The root render's ``CitryContext``. Its ``extra`` carries everything
    that bubbled up during the render, so an extension can read back what its
    render-time hooks collected."""
    selected_render: CitryRender
    """The exact render selected for serialization and asset filtering."""
    strategy: str
    """The ``serialize(deps_strategy=...)`` value this emission runs under
    (``"document"``, ``"simple"``, or ``"fragment"``)."""
    before_manifest: list[Dependency]
    """Entries rendered immediately before the native Vue fragment descriptor,
    or before dependency scripts for static output (mutable). Under ``simple``
    they are emitted with the other direct dependency tags."""
    _security_csp: SecurityCspMode = "off"
    """The effective call-local CSP mode used by built-in dependency producers."""
    _security_javascript: SecurityJavascriptMode = "allow"
    """The effective call-local JavaScript delivery mode."""


@dataclass(eq=False)
class _PrerenderedTag(Dependency):
    """
    A ``Dependencies`` entry that was a pre-rendered tag (an object with
    ``__html__``): emitted verbatim. ``content`` holds the full tag text.
    """

    def render(self) -> Markup:
        return Markup(self.content or "")  # noqa: S704 - __html__ declared this entry trusted


def emit_dependencies(
    citry: Citry,
    ctx: OnSerializeContext,
    *,
    script_security: _ScriptSecurityMaterializer | None = None,
    security_csp: SecurityCspMode = "off",
    javascript_policy: _JavascriptPolicy | None = None,
    security_javascript: SecurityJavascriptMode = "allow",
) -> str:
    """
    The extension's ``on_serialize`` implementation: place the collected
    JS/CSS into ``ctx.html`` per the strategy and position (module docstring).
    """
    # Locate the <c-js>/<c-css> placeholders in the joined HTML, in document
    # order. Each placeholder's exact text is unique (the serializer numbers
    # them), so plain string search and replace is unambiguous.
    js_placeholders = _locate_placeholders(ctx.html, ctx.placeholders, JS_PLACEHOLDER_KEY)
    css_placeholders = _locate_placeholders(ctx.html, ctx.placeholders, CSS_PLACEHOLDER_KEY)
    all_placeholder_texts = [text for _, text in js_placeholders] + [text for _, text in css_placeholders]

    # Collected as an insertion-ordered set (a dict) so the bubble-up merge
    # dedupes on insert instead of accumulating one copy per ancestor.
    selected_ids = selected_render_ids(ctx.selected_render)
    records: list[DependencyRecord] = [
        record for record in ctx.context.extra.get(EXTRA_KEY, {}) if record.component_id in selected_ids
    ]

    # "ignore": no tags inserted and no dependency hooks invoked. The policy
    # still inventories reached declarations because ignore cannot hide a
    # JavaScript requirement from forbid.
    if ctx.deps_strategy == "ignore":
        if javascript_policy is not None:
            _inspect_ignored_records(citry, records, javascript_policy)
        return _blank(ctx.html, all_placeholder_texts)

    if security_javascript in {"omit", "forbid"}:
        if javascript_policy is None:
            raise RuntimeError("A restrictive JavaScript mode has no call-local policy authority.")
        return _emit_without_javascript(
            citry,
            ctx,
            records,
            all_placeholder_texts,
            js_placeholders,
            css_placeholders,
            script_security=script_security,
            security_csp=security_csp,
            javascript_policy=javascript_policy,
            security_javascript=security_javascript,
        )

    # "fragment": nothing is inlined; the output carries a pre-loader plus a
    # manifest of URLs for the client-side manager to fetch (section 8).
    if ctx.deps_strategy == "fragment":
        return _emit_fragment(
            citry,
            ctx,
            records,
            all_placeholder_texts,
            script_security=script_security,
            security_csp=security_csp,
            javascript_policy=javascript_policy,
            security_javascript=security_javascript,
        )

    # "document" includes the client-side manager and everything that needs
    # it (the JS-variables scripts, the per-instance component calls, the
    # manifest). "simple" is the no-JS-runtime mode: component and
    # Dependencies tags only, so per-instance JS does not run there.
    # CSS variables are pure CSS (a stylesheet plus a root-element marker)
    # and work under both.
    with_client_js = ctx.deps_strategy == "document"
    resolved = _resolve_records(
        citry,
        records,
        with_client_js=with_client_js,
        prepared_vue=ctx.context.extra.get(VUE_DEPENDENCIES_PREPARED_KEY) is True,
        script_security=script_security,
    )
    scripts, styles = resolved.scripts, resolved.styles

    # Prepared Vue tracks only stylesheet elements emitted for this app. The
    # URL alone is not ownership: authored markup may intentionally use the
    # same href, so give each engine-emitted initial sheet an app-local marker.
    vue_style_app_id = ctx.context.extra.get("_vue_style_app_id")
    if isinstance(vue_style_app_id, str):
        for style in styles:
            if "data-citry-css-url" in style.attrs:
                style.attrs["data-citry-vue-style-app"] = vue_style_app_id

    # The extension-owned custom hook: other extensions adjust the lists in
    # place (docs/design/extensions.md section 9.2). The hook sees the
    # component-derived entries (possibly none); the runtime and the manifest
    # are appended after it, so URLs an extension adds here are still marked
    # as loaded.
    if ctx.context.extra.get(VUE_DEPENDENCIES_PREPARED_KEY) is True:
        scripts, styles, before_manifest = [], [], []
    else:
        hook_ctx = OnDependenciesContext(
            citry=citry,
            scripts=scripts,
            styles=styles,
            context=ctx.context,
            selected_render=ctx.selected_render,
            strategy=ctx.deps_strategy,
            before_manifest=[],
            _security_csp=security_csp,
            _security_javascript=security_javascript,
        )
        citry.extensions.emit("on_dependencies", hook_ctx)
        scripts, styles, before_manifest = hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest
        _validate_hook_nonces(script_security, scripts, styles, before_manifest)

    # An actual Vue serialization plan requests its runtime here so it appears
    # before component Options. Static dependency hooks remain direct tags and
    # need no client-side ownership manifest.
    core_scripts: list[Dependency] = []
    vue_runtime_required = with_client_js and ctx.context.extra.get(VUE_RUNTIME_REQUIRED_KEY) is True
    if vue_runtime_required:
        core_scripts.append(_runtime_script(citry))
        ctx.context.extra[VUE_RUNTIME_EMITTED_KEY] = True
    elif resolved.has_component_calls:
        raise RuntimeError("Component JavaScript calls require a native Vue serialization plan.")
    core_scripts.extend(before_manifest)

    if javascript_policy is not None:
        core_scripts = javascript_policy.process_dependencies(core_scripts, position="managed runtime")
        scripts = javascript_policy.process_dependencies(scripts, position="page")
        styles = javascript_policy.process_dependencies(styles, position="stylesheet")

    js_html = "".join(
        str(script.render()) if script_security is None else script_security.render(script)
        for script in [*core_scripts, *scripts]
    )
    css_html = "".join(
        str(style.render()) if script_security is None else script_security.render_style(style) for style in styles
    )

    return _place_dependency_html(
        ctx,
        js_placeholders,
        css_placeholders,
        all_placeholder_texts,
        js_html=js_html,
        css_html=css_html,
    )


def _inspect_ignored_records(
    citry: Citry,
    records: list[DependencyRecord],
    javascript_policy: _JavascriptPolicy,
) -> None:
    """Inventory reached declarations without invoking ignored dependency hooks."""
    seen_classes: set[type[Component]] = set()
    for record in dict.fromkeys(records):
        comp_cls = record.component_class or citry.get_component_by_class_id(record.class_id)
        if comp_cls not in seen_classes:
            seen_classes.add(comp_cls)
            if has_component_asset("js", comp_cls):
                javascript_policy.add_requirement(
                    "Component.js is declared on a reached component",
                    component=comp_cls.__name__,
                    key=("component-js", comp_cls.class_id),
                )
            if comp_cls.get_dependencies().js:
                javascript_policy.add_requirement(
                    "JavaScript Dependencies are declared on a reached component",
                    component=comp_cls.__name__,
                    key=("dependencies-js", comp_cls.class_id),
                )
            _inspect_ignored_css(comp_cls, javascript_policy)


def _inspect_ignored_css(comp_cls: type[Component], javascript_policy: _JavascriptPolicy) -> None:
    """Inspect CSS declarations without rendering files or invoking dependency hooks."""
    structured: list[Dependency] = []
    for media_type, entries in comp_cls.get_dependencies().css.items():
        media_attrs: dict[str, str | bool] = {} if media_type == "all" else {"media": media_type}
        for entry in entries:
            if isinstance(entry, Dependency):
                structured.append(entry)
            elif isinstance(entry, Path):
                continue
            elif isinstance(entry, str) and not isinstance(entry, HasHtml):
                structured.append(Style(url=entry, attrs=media_attrs, kind="extra", origin_class_id=comp_cls.class_id))
            else:
                javascript_policy.add_requirement(
                    "an opaque Dependencies.css entry cannot be proven JavaScript-free while dependencies are ignored",
                    component=comp_cls.__name__,
                    rule="opaque-dependency",
                    key=("dependencies-css-opaque", comp_cls.class_id, id(entry)),
                )
    javascript_policy.process_dependencies(structured, position="ignored CSS")


def _emit_without_javascript(
    citry: Citry,
    ctx: OnSerializeContext,
    records: list[DependencyRecord],
    placeholder_texts: list[str],
    js_placeholders: list[tuple[int, str]],
    css_placeholders: list[tuple[int, str]],
    *,
    script_security: _ScriptSecurityMaterializer | None,
    security_csp: SecurityCspMode,
    javascript_policy: _JavascriptPolicy,
    security_javascript: SecurityJavascriptMode,
) -> str:
    """Emit server HTML, CSS, and safe inert data scripts without a manager."""
    resolved = _resolve_records(
        citry,
        records,
        with_client_js=True,
        as_urls=False,
        script_security=script_security,
    )
    hook_ctx = OnDependenciesContext(
        citry=citry,
        scripts=resolved.scripts,
        styles=resolved.styles,
        context=ctx.context,
        selected_render=ctx.selected_render,
        strategy=ctx.deps_strategy,
        before_manifest=[],
        _security_csp=security_csp,
        _security_javascript=security_javascript,
    )
    citry.extensions.emit("on_dependencies", hook_ctx)
    _validate_hook_nonces(script_security, hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest)
    scripts = javascript_policy.process_dependencies(hook_ctx.scripts, position="page")
    before_manifest = javascript_policy.process_dependencies(
        hook_ctx.before_manifest,
        position="before-manifest",
    )
    styles = javascript_policy.process_dependencies(hook_ctx.styles, position="stylesheet")

    retained = [*before_manifest, *scripts]
    js_html = "".join(_render_dependency(dep, script_security) for dep in retained)
    css_html = "".join(_render_dependency(dep, script_security) for dep in styles)
    return _place_dependency_html(
        ctx,
        js_placeholders,
        css_placeholders,
        placeholder_texts,
        js_html=js_html,
        css_html=css_html,
    )


def _render_dependency(
    dependency: Dependency,
    script_security: _ScriptSecurityMaterializer | None,
) -> str:
    if script_security is None:
        return str(dependency.render())
    if isinstance(dependency, Style):
        return script_security.render_style(dependency)
    return script_security.render(dependency)


def _place_dependency_html(
    ctx: OnSerializeContext,
    js_placeholders: list[tuple[int, str]],
    css_placeholders: list[tuple[int, str]],
    all_placeholder_texts: list[str],
    *,
    js_html: str,
    css_html: str,
) -> str:
    """Place already-rendered dependency tags using the established strategy."""
    # A native Vue plan has already moved the logical mount point into the
    # document shell, and its runtime must execute while that document is
    # still open.  Keep ordinary dependency calls' explicit prepend/append
    # contract, but place this Vue-owned batch with the normal head/body
    # rules.  Otherwise ``deps_position='append'`` would put the runtime
    # after ``</html>`` before VueSerializationPlan.finalize adds its own
    # definitions and bootstrap.
    position = ctx.deps_position
    if position in ("prepend", "append") and ctx.context.extra.get(VUE_RUNTIME_REQUIRED_KEY) is True:
        position = "smart"
    if position in ("prepend", "append"):
        html = _blank(ctx.html, all_placeholder_texts)
        if position == "prepend":
            return js_html + css_html + html
        return html + js_html + css_html

    html = ctx.html
    html = _fill_placeholders(html, css_placeholders, css_html)
    html = _fill_placeholders(html, js_placeholders, js_html)
    if not css_placeholders and css_html:
        html = _insert_default(html, css_html, kind="css")
    if not js_placeholders and js_html:
        html = _insert_default(html, js_html, kind="js")
    return html


# ----- Record resolution -----


@dataclass(slots=True)
class _Resolved:
    """The outcome of resolving the collected records."""

    scripts: list[Dependency]
    styles: list[Dependency]
    has_component_calls: bool
    script_owners: dict[int, set[str]]
    style_owners: dict[int, set[str]]


def _resolve_records(
    citry: Citry,
    records: list[DependencyRecord],
    *,
    with_client_js: bool,
    prepared_vue: bool = False,
    as_urls: bool = False,
    attach_owned_resources: bool = False,
    script_security: _ScriptSecurityMaterializer | None = None,
    allow_prerendered: bool = False,
) -> _Resolved:
    """
    Turn the collected records into the ``scripts`` / ``styles`` lists and
    report whether a native component callback requires a Vue plan.

    Per record: the class's ``Dependencies`` entries, its own
    ``Component.js``/``css`` (read through the cache), and the variables
    script/stylesheet for the instance's hashed ``js_data()``/``css_data()``.
    ``Component.on_dependencies`` may adjust each record's lists. The final
    order is: core entries first, then all ``Dependencies`` entries, then all
    component scripts (a vendored lib from a ``Dependencies`` class loads
    before the component code that uses it), de-duplicated keeping the first
    occurrence.

    With ``with_client_js`` off (the "simple" strategy), JavaScript variables
    are skipped because they require the native Vue app.

    With ``as_urls`` on, component and variables assets become URL entries.
    ``attach_owned_resources`` binds JavaScript URLs to exact cached response
    bytes for integrity-mode serialization.
    """
    mounted = citry.mounted_prefix is not None

    # A record bubbles up through every ancestor as nested renders merge, so the
    # same instance's record can arrive many times (deeply nested pages see a
    # large multiple). Each duplicate resolves to identical scripts, so collapse
    # them first, keeping first-seen (document) order; without this the
    # per-record work below is quadratic in the tree depth.
    records = list(dict.fromkeys(records))

    core_js: list[Dependency] = []
    core_css: list[Dependency] = []
    extra_js: list[Dependency] = []
    extra_css: list[Dependency] = []
    component_js: list[Dependency] = []
    component_css: list[Dependency] = []
    has_component_calls = False
    script_owner_groups: dict[Dependency, set[str]] = {}
    style_owner_groups: dict[Dependency, set[str]] = {}

    # The class-level entries (a class's Dependencies plus its own JS/CSS) are
    # identical for every instance of the class, so resolve them once per class
    # and reuse them: a page commonly renders many instances of the same
    # component. Only the per-instance variables scripts and the client-side
    # call below differ between instances.
    class_deps: dict[type[Component], tuple[list[Dependency], list[Dependency], bool]] = {}

    for record in records:
        # A render can be serialized after hot replacement installed a new
        # class with the same deterministic ID. Prefer the exact class that
        # rendered this record; the fallback keeps manually constructed and
        # older records compatible.
        comp_cls = record.component_class or citry.get_component_by_class_id(record.class_id)
        cached = class_deps.get(comp_cls)
        if cached is None:
            scripts: list[Dependency] = []
            styles: list[Dependency] = []

            deps = comp_cls.get_dependencies()
            for entry in deps.js:
                scripts.append(_entry_to_script(entry, comp_cls, fragment=as_urls and not allow_prerendered))
            for media_type, entries in deps.css.items():
                for entry in entries:
                    styles.append(
                        _entry_to_style(entry, media_type, comp_cls, fragment=as_urls and not allow_prerendered)
                    )

            # The class's own JS/CSS: inlined content for a page, a cache URL for
            # a fragment (the endpoint serves what the cache write here stores).
            # Either way the Component.css sheet is tagged with its class id
            # (data-citry-css-class), which is how the client-side manager's
            # cleanup finds the sheet when the class's last instance leaves the
            # page (docs/design/dependencies.md 8.4).
            # The legacy document emitter uses these attributes to find and
            # retire component-owned sheets. Prepared Vue assets carry their
            # ownership in the manifest's occurrence IDs instead. Omitting
            # the legacy class marker there lets related components share one
            # byte-identical sheet (for example CSlider/CRangeSlider) without
            # creating conflicting attributes on the same prepared asset.
            css_class_attr: dict[str, str | bool] = {} if prepared_vue else {"data-citry-css-class": comp_cls.class_id}
            if as_urls:
                if has_component_asset("js", comp_cls):
                    cache_component_js(comp_cls)
                    if attach_owned_resources:
                        resource = _cached_js_resource(comp_cls)
                        if resource is None:
                            msg = f"Cannot prove the response bytes for Component.js of {comp_cls.class_id!r}."
                            raise RuntimeError(msg)
                        scripts.append(_owned_script(resource, kind="component", origin_class_id=comp_cls.class_id))
                    else:
                        scripts.append(
                            Script(
                                url=script_url(comp_cls, "js"),
                                kind="component",
                                origin_class_id=comp_cls.class_id,
                            )
                        )
                if has_component_asset("css", comp_cls):
                    cache_component_css(comp_cls)
                    styles.append(
                        Style(
                            url=script_url(comp_cls, "css"),
                            attrs=css_class_attr,
                            kind="component",
                            origin_class_id=comp_cls.class_id,
                        )
                    )
            else:
                comp_js = get_component_script("js", comp_cls)
                if comp_js is not None:
                    scripts.append(comp_js)
                comp_css = get_component_script("css", comp_cls)
                if comp_css is not None:
                    if mounted and not prepared_vue:
                        # A document inlines this sheet but tells the runtime
                        # that its fragment URL is loaded. Store the URL on the
                        # style so the runtime can clear both when it removes
                        # the sheet.
                        css_class_attr["data-citry-css-url"] = script_url(comp_cls, "css")
                    styles.append(replace(comp_css, attrs={**comp_css.attrs, **css_class_attr}))

            cached = (
                scripts,
                styles,
                with_client_js and uses_component(comp_cls),
            )
            class_deps[comp_cls] = cached

        cls_scripts, cls_styles, cls_uses_oncomp = cached
        has_component_calls = has_component_calls or cls_uses_oncomp
        # Copy the class lists so the per-instance scripts below (and any
        # on_dependencies edit) never mutate the cached entry.
        instance_scripts: list[Dependency] = list(cls_scripts)
        instance_styles: list[Dependency] = list(cls_styles)

        # The variables scripts generated for this instance's data hashes.
        # Unlike class scripts these cannot be rebuilt on a cache miss (the
        # data existed only during the render). Legacy fragment output retains
        # its URL on a miss; integrity mode fails because it cannot prove bytes.
        # A shared cache backend prevents the miss across processes.
        if cls_uses_oncomp and record.js_vars_hash is not None:
            if as_urls:
                if attach_owned_resources:
                    resource = _cached_js_resource(comp_cls, record.js_vars_hash)
                    if resource is None:
                        msg = (
                            f"Cannot prove the response bytes for JavaScript data {record.js_vars_hash!r} "
                            f"of {comp_cls.class_id!r}."
                        )
                        raise RuntimeError(msg)
                    instance_scripts.append(
                        _owned_script(resource, kind="variables", origin_class_id=comp_cls.class_id)
                    )
                else:
                    instance_scripts.append(
                        Script(
                            url=script_url(comp_cls, "js", record.js_vars_hash),
                            kind="variables",
                            origin_class_id=comp_cls.class_id,
                        )
                    )
            else:
                vars_js = get_script("js", comp_cls, record.js_vars_hash)
                if vars_js is not None:
                    instance_scripts.append(vars_js)
        if record.css_vars_hash is not None:
            if as_urls:
                instance_styles.append(
                    Style(
                        url=script_url(comp_cls, "css", record.css_vars_hash),
                        kind="variables",
                        origin_class_id=comp_cls.class_id,
                    )
                )
            else:
                vars_css = get_script("css", comp_cls, record.css_vars_hash)
                if vars_css is not None:
                    if mounted:
                        variables_url = script_url(comp_cls, "css", record.css_vars_hash)
                        vars_css = replace(
                            vars_css,
                            attrs={**vars_css.attrs, "data-citry-css-url": variables_url},
                        )
                    instance_styles.append(vars_css)

        # Per-component hook: adjust this instance's lists before they join
        # the page-wide ones.
        result = comp_cls.on_dependencies(instance_scripts, instance_styles)
        if result is not None:
            instance_scripts, instance_styles = result

        for script in instance_scripts:
            if script_security is not None:
                script_security.validate_declared_nonce(script)
            _bucket(script, core_js, extra_js, component_js)
            script_owner_groups.setdefault(script, set()).add(record.component_id)
        for style in instance_styles:
            if script_security is not None:
                script_security.validate_declared_nonce(style)
            _bucket(style, core_css, extra_css, component_css)
            style_owner_groups.setdefault(style, set()).add(record.component_id)

    all_styles = [*core_css, *extra_css, *component_css]
    style_attrs: dict[Dependency, dict[str, str | bool]] = {}
    for style in all_styles:
        prior_attrs = style_attrs.get(style)
        if prior_attrs is not None and prior_attrs != style.attrs:
            identity = style.url if style.url is not None else "inline stylesheet content"
            raise ValueError(
                f"The same stylesheet {identity!r} was declared with conflicting attributes; "
                "use distinct stylesheet URLs until attribute-specific stylesheet ownership is supported."
            )
        style_attrs[style] = dict(style.attrs)

    deduped_scripts = list(dict.fromkeys([*core_js, *extra_js, *component_js]))
    deduped_styles = list(dict.fromkeys(all_styles))

    return _Resolved(
        scripts=deduped_scripts,
        styles=deduped_styles,
        has_component_calls=has_component_calls,
        script_owners={id(item): set(script_owner_groups[item]) for item in deduped_scripts},
        style_owners={id(item): set(style_owner_groups[item]) for item in deduped_styles},
    )


# ----- The client runtime and the page manifest -----


@cache
def _runtime_js() -> str:
    """The generated Vue interactive runtime shipped to browsers."""
    return (Path(__file__).parents[2] / "_vue" / "runtime.js").read_text(encoding="utf8")


def _runtime_resource(citry: Citry) -> _OwnedResource:
    url = runtime_url(citry) if citry.mounted_prefix is not None else RUNTIME_PATH
    return _OwnedResource(url=url, content=_runtime_js(), content_type="text/javascript")


def _owned_script(
    resource: _OwnedResource,
    *,
    kind: Literal["core", "component", "variables", "extra"],
    origin_class_id: str | None = None,
    attrs: dict[str, str | bool] | None = None,
) -> Script:
    script = Script(
        kind=kind,
        url=resource.url,
        attrs={} if attrs is None else attrs,
        origin_class_id=origin_class_id,
    )
    script._owned_resource = resource
    return script


def _cached_js_resource(comp_cls: type[Component], variables_hash: str | None = None) -> _OwnedResource | None:
    dependency = (
        get_component_script("js", comp_cls) if variables_hash is None else get_script("js", comp_cls, variables_hash)
    )
    if dependency is None:
        return None
    if not isinstance(dependency, Script) or dependency.content is None:
        msg = f"Cached JavaScript for component {comp_cls.class_id!r} is not an inline Script."
        raise TypeError(msg)
    return _OwnedResource(
        url=script_url(comp_cls, "js", variables_hash),
        content=dependency.content,
        content_type="text/javascript",
    )


def _runtime_script(citry: Citry) -> Script:
    # A mounted web integration serves the runtime at a URL (cacheable by the
    # browser); without one, the runtime is inlined so the zero-configuration
    # document flow still works end to end. wrap=False: the runtime is
    # already a self-contained immediately-invoked function.
    if citry.mounted_prefix is not None:
        return _owned_script(_runtime_resource(citry), kind="core")
    return Script(kind="core", content=_runtime_js(), wrap=False)


def _preloader_script(
    citry: Citry,
    script_security: _ScriptSecurityMaterializer | None = None,
) -> Script:
    """
    The fragment pre-loader: loads the client runtime if the page does not
    have it yet, so fragments work even on pages that were not rendered with
    the "document" strategy. Removes its own tag afterward.
    """
    resource = _runtime_resource(citry)
    url_literal = json.dumps(resource.url).replace("<", "\\u003c")
    integrity_line = ""
    if script_security is not None and script_security.integrity_enabled:
        integrity = script_security.owned_integrity(resource)
        integrity_line = f"  s.integrity = {json.dumps(integrity)};\n"
    nonce_line = ""
    if script_security is not None and script_security.csp_nonce is not None:
        nonce_line = f"  s.nonce = {json.dumps(script_security.csp_nonce)};\n"
    content = (
        "if (!globalThis.Citry || !globalThis.Citry.fragments) {\n"
        '  var s = document.createElement("script");\n'
        f"  s.src = {url_literal};\n"
        f"{integrity_line}"
        f"{nonce_line}"
        "  document.head.appendChild(s);\n"
        "}\n"
        "if (document.currentScript) document.currentScript.remove();"
    )
    return Script(kind="core", content=content, wrap=True)


def _vue_fragment_manifest(vue_mount: dict[str, object]) -> Script:
    return Script(
        kind="core",
        content=json.dumps({"vue": vue_mount}),
        attrs={"type": "application/json", "data-citry-vue-fragment": True},
    )


def _emit_fragment(
    citry: Citry,
    ctx: OnSerializeContext,
    records: list[DependencyRecord],
    placeholder_texts: list[str],
    *,
    script_security: _ScriptSecurityMaterializer | None,
    security_csp: SecurityCspMode,
    javascript_policy: _JavascriptPolicy | None,
    security_javascript: SecurityJavascriptMode,
) -> str:
    """
    Emit direct dependency tags for static fragments, or a native Vue loader
    and one structured descriptor for interactive fragments.
    """
    fragment_needs_mount_msg = (
        "serialize(deps_strategy='fragment') needs a mounted web integration:"
        " the fragment references its JS/CSS by URL. Mount one (e.g."
        " citry.contrib.fastapi.mount(app, citry_instance)), or use"
        " set_mounted_prefix() in processes that only render."
    )
    vue_mount = ctx.context.extra.pop(VUE_FRAGMENT_MOUNT_KEY, None)
    if vue_mount is not None:
        records = []
    if records:
        if citry.mounted_prefix is None:
            raise RuntimeError(fragment_needs_mount_msg)
        resolved = _resolve_records(
            citry,
            records,
            with_client_js=True,
            as_urls=True,
            attach_owned_resources=script_security is not None and script_security.integrity_enabled,
            script_security=script_security,
            allow_prerendered=vue_mount is None,
        )
    else:
        resolved = _Resolved(
            scripts=[],
            styles=[],
            has_component_calls=False,
            script_owners={},
            style_owners={},
        )
    scripts, styles = resolved.scripts, resolved.styles

    if ctx.context.extra.get(VUE_DEPENDENCIES_PREPARED_KEY) is True:
        scripts, styles, before_manifest = [], [], []
    else:
        hook_ctx = OnDependenciesContext(
            citry=citry,
            scripts=scripts,
            styles=styles,
            context=ctx.context,
            selected_render=ctx.selected_render,
            strategy="fragment",
            before_manifest=[],
            _security_csp=security_csp,
            _security_javascript=security_javascript,
        )
        citry.extensions.emit("on_dependencies", hook_ctx)
        scripts, styles, before_manifest = hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest
        _validate_hook_nonces(script_security, scripts, styles, before_manifest)
    if vue_mount is not None and before_manifest:
        raise RuntimeError(
            "Interactive fragment dependency hooks must contribute through the prepared browser extension API."
        )
    framework_manifests = before_manifest

    if javascript_policy is not None:
        scripts = javascript_policy.process_dependencies(scripts, position="fragment fetch")
        styles = javascript_policy.process_dependencies(styles, position="fragment stylesheet")
        framework_manifests = javascript_policy.process_dependencies(
            framework_manifests,
            position="fragment framework",
        )

    # Static fragments have no Vue application or client-side ownership graph.
    # Emit their already-resolved dependencies as ordinary tags: stylesheets
    # remain useful after insertion, and an integrating fragment library keeps
    # its normal script execution semantics.  Do not emit the former legacy
    # data-citry manifest, which the native Vue runtime intentionally ignores.
    if vue_mount is None:
        if resolved.has_component_calls:
            raise RuntimeError("A static fragment cannot carry component runtime state.")

        def render_dependency(dependency: Dependency, *, style: bool = False) -> str:
            if script_security is None:
                return str(dependency.render())
            return script_security.render_style(dependency) if style else script_security.render(dependency)

        html = _blank(ctx.html, placeholder_texts)
        css_html = "".join(render_dependency(dependency, style=True) for dependency in styles)
        before_html = "".join(render_dependency(dependency) for dependency in framework_manifests)
        script_html = "".join(render_dependency(dependency) for dependency in scripts)
        return html + css_html + before_html + script_html

    # A fragment that carries nothing at all has nothing to load, so it needs
    # no pre-loader or manifest (and no mounted integration).
    if not scripts and not styles and not resolved.has_component_calls and not before_manifest and vue_mount is None:
        return _blank(ctx.html, placeholder_texts)
    if citry.mounted_prefix is None:
        raise RuntimeError(fragment_needs_mount_msg)

    html = _blank(ctx.html, placeholder_texts)
    # Ownership and Events manifests stay inert top-level JSON. Every other
    # graph-backed hook entry is a descriptor inside the dependency manifest,
    # so an ignored incoming branch cannot execute it during fragment parsing.
    if script_security is None:
        manifest = _vue_fragment_manifest(vue_mount)
        before_html = "".join(str(dep.render()) for dep in framework_manifests)
        return html + str(_preloader_script(citry, None).render()) + before_html + str(manifest.render())
    if security_csp == "strict":
        preloader_html = ""
    else:
        runtime_resource = _runtime_resource(citry)
        preloader = _preloader_script(citry, script_security)
        if javascript_policy is not None:
            retained_preloader = javascript_policy.process_dependencies(
                [preloader],
                position="fragment preloader",
            )
            if not retained_preloader or not isinstance(retained_preloader[0], Script):
                raise RuntimeError("The JavaScript inventory unexpectedly removed the warning-mode preloader.")
            preloader = retained_preloader[0]
        preloader_html = script_security.render(preloader)
        if script_security.integrity_enabled:
            script_security.record_owned_dynamic(runtime_resource)
    before_html = "".join(script_security.render(dep) for dep in framework_manifests)
    manifest = _vue_fragment_manifest(vue_mount)
    if javascript_policy is not None:
        retained_manifest = javascript_policy.process_dependencies(
            [manifest],
            position="fragment manifest",
        )
        if not retained_manifest:
            return html + preloader_html + before_html
        if not isinstance(retained_manifest[0], Script):
            raise RuntimeError("The JavaScript inventory changed the structured fragment manifest type.")
        manifest = retained_manifest[0]
    return html + preloader_html + before_html + script_security.render(manifest)


def _validate_hook_nonces(
    script_security: _ScriptSecurityMaterializer | None,
    scripts: list[Dependency],
    styles: list[Dependency],
    before_manifest: list[Dependency],
) -> None:
    """Check every global-hook contribution before later equality deduplication."""
    if script_security is None or script_security.csp_nonce is None:
        return
    for dependency in [*scripts, *styles, *before_manifest]:
        script_security.validate_declared_nonce(dependency)


def _bucket(dep: Dependency, core: list[Dependency], extra: list[Dependency], component: list[Dependency]) -> None:
    if dep.kind == "core":
        core.append(dep)
    elif dep.kind in ("component", "variables"):
        component.append(dep)
    else:
        extra.append(dep)


def _prerendered(entry: Any, comp_cls: type[Component], *, fragment: bool) -> _PrerenderedTag:
    # A fragment delivers its dependencies as {tag, attrs, content}
    # descriptors, and an opaque pre-rendered tag string cannot be decomposed
    # into one. Fail loudly rather than dropping it.
    if fragment:
        msg = (
            f"A pre-rendered Dependencies entry of {comp_cls.__name__} cannot be delivered"
            " in a fragment; declare it as a Script/Style object or a URL instead."
        )
        raise TypeError(msg)
    return _PrerenderedTag(content=str(entry.__html__()), kind="extra", origin_class_id=comp_cls.class_id)


def _entry_to_script(entry: Any, comp_cls: type[Component], *, fragment: bool = False) -> Dependency:
    """
    Convert one resolved ``Dependencies.js`` entry into an emittable object.

    Entries arrive from the loading half already resolved: a ``Script``
    object passes through; a ``Path`` is a local file, read and inlined
    (unwrapped, so a vendored lib's top-level ``var`` declarations stay
    global); a string is a URL; a pre-rendered tag is emitted verbatim
    (documents only).
    """
    if isinstance(entry, Style):
        msg = f"Dependencies.js of {comp_cls.__name__} contains a Style entry; use Script for JS"
        raise TypeError(msg)
    if isinstance(entry, Dependency):
        return entry
    if isinstance(entry, Path):
        resource = _maybe_serve_local_file(entry, comp_cls)
        if resource is not None:
            return _owned_script(resource, kind="extra", origin_class_id=comp_cls.class_id)
        return Script(content=_read_asset(entry), wrap=False, kind="extra", origin_class_id=comp_cls.class_id)
    if isinstance(entry, HasHtml) and not isinstance(entry, str):
        return _prerendered(entry, comp_cls, fragment=fragment)
    if isinstance(entry, str):
        if isinstance(entry, HasHtml):
            return _prerendered(entry, comp_cls, fragment=fragment)
        return Script(url=entry, kind="extra", origin_class_id=comp_cls.class_id)
    msg = f"Cannot emit Dependencies.js entry {entry!r} of {comp_cls.__name__}"
    raise TypeError(msg)


def _entry_to_style(entry: Any, media_type: str, comp_cls: type[Component], *, fragment: bool = False) -> Dependency:
    """
    The CSS counterpart of :func:`_entry_to_script`. The ``Dependencies.css``
    media type ("print", ...) becomes the tag's ``media`` attribute ("all",
    the default, is omitted, matching what browsers assume).
    """
    if isinstance(entry, Script):
        msg = f"Dependencies.css of {comp_cls.__name__} contains a Script entry; use Style for CSS"
        raise TypeError(msg)
    media_attrs: dict[str, str | bool] = {} if media_type == "all" else {"media": media_type}
    if isinstance(entry, Style):
        # Stamp the media type onto a user Style that does not set one itself.
        if media_attrs and "media" not in entry.attrs:
            return replace(entry, attrs={**entry.attrs, **media_attrs})
        return entry
    if isinstance(entry, Dependency):
        return entry
    if isinstance(entry, Path):
        resource = _maybe_serve_local_file(entry, comp_cls)
        if resource is not None:
            return Style(url=resource.url, attrs=media_attrs, kind="extra", origin_class_id=comp_cls.class_id)
        return Style(content=_read_asset(entry), attrs=media_attrs, kind="extra", origin_class_id=comp_cls.class_id)
    if isinstance(entry, HasHtml) and not isinstance(entry, str):
        return _prerendered(entry, comp_cls, fragment=fragment)
    if isinstance(entry, str):
        if isinstance(entry, HasHtml):
            return _prerendered(entry, comp_cls, fragment=fragment)
        return Style(url=entry, attrs=media_attrs, kind="extra", origin_class_id=comp_cls.class_id)
    msg = f"Cannot emit Dependencies.css entry {entry!r} of {comp_cls.__name__}"
    raise TypeError(msg)


def _read_asset(path: Path) -> str:
    # Read on every serialize; with local_files="serve" the content is cached
    # under its hash instead (see _maybe_serve_local_file).
    return path.read_text(encoding="utf8")


def _maybe_serve_local_file(path: Path, comp_cls: type[Component]) -> _OwnedResource | None:
    """
    The URL a local-file entry is served at, or ``None`` to inline it.

    Honors the component's ``local_files`` setting (the ``Dependencies``
    config, docs/design/dependencies.md section 9.4). ``"serve"`` caches the
    content under its hash and emits a fingerprinted URL on the asset
    endpoint; with no web integration mounted it falls back to inlining,
    which is always correct.
    """
    config = getattr(comp_cls, "Dependencies", None)
    mode = getattr(config, "local_files", "inline")
    if mode == "inline":
        return None
    if mode != "serve":
        msg = f"local_files of {comp_cls.__name__} must be 'inline' or 'serve', got {mode!r}"
        raise ValueError(msg)
    citry = comp_cls.citry
    if citry.mounted_prefix is None:
        return None
    content = _read_asset(path)
    extension = path.suffix.lstrip(".")
    file_name = cache_asset(citry, content, extension)
    served_content = citry.cache.get(gen_asset_cache_key(file_name))
    if not isinstance(served_content, (str, bytes)):
        msg = f"Cached dependency asset {file_name!r} has no text or byte content."
        raise TypeError(msg)
    content_type = (
        "text/javascript" if extension == "js" else "text/css" if extension == "css" else "application/octet-stream"
    )
    return _OwnedResource(
        url=citry.build_url(f"asset/{file_name}"),
        content=served_content,
        content_type=content_type,
    )


# ----- Placement -----


def _locate_placeholders(html: str, placeholders: dict[str, str], key: str) -> list[tuple[int, str]]:
    """
    The placeholders of one kind, as ``(position in html, exact text)``,
    sorted by position. A placeholder no longer present in the HTML (its
    parent was replaced by a hook after serialization built it) is skipped.
    """
    prefix = key + ":"
    located: list[tuple[int, str]] = []
    for placeholder_id, text in placeholders.items():
        if not placeholder_id.startswith(prefix):
            continue
        position = html.find(text)
        if position != -1:
            located.append((position, text))
    located.sort()
    return located


def _blank(html: str, placeholder_texts: list[str]) -> str:
    for text in placeholder_texts:
        html = html.replace(text, "", 1)
    return html


def _fill_placeholders(html: str, placeholders: list[tuple[int, str]], content: str) -> str:
    """Put ``content`` into the first placeholder (document order); remove the rest."""
    for i, (_, text) in enumerate(placeholders):
        html = html.replace(text, content if i == 0 else "", 1)
    return html


_HEAD_OR_BODY_END_RE = re.compile(r"</(?:head|body)\s*>")


def _insert_default(html: str, content: str, kind: str) -> str:
    """
    Insert ``content`` at its default location: CSS before the first
    ``</head>``, JS before the last ``</body>``. When the target tag does not
    exist, CSS is prepended and JS appended, so the tags are never silently
    dropped (django-components dropped them here; flagged divergence,
    docs/design/dependencies.md section 7.3).
    """
    target = None
    for match in _HEAD_OR_BODY_END_RE.finditer(html):
        is_head = match[0][2:6] == "head"
        if kind == "css" and is_head:
            target = match.start()
            break
        if kind == "js" and not is_head:
            target = match.start()  # keep the last </body>
    if target is not None:
        return html[:target] + content + html[target:]
    return content + html if kind == "css" else html + content
