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

import base64
import json
import re
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from citry._owned_resource import _OwnedResource
from citry.assets import HasHtml
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
from citry.ownership_manifest import EXTRA_KEY as OWNERSHIP_MANIFEST_KEY
from citry.ownership_manifest import OwnershipManifestArtifact
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

# One per-instance client call: initialize `$component` after seeding, or only
# seed the instance's Alpine scope. The explicit mode keeps script arrival
# order from changing semantics.
_CallMode: TypeAlias = Literal["init", "seed"]
_ComponentCall: TypeAlias = tuple[str, str, "str | None", _CallMode]

# The key under which the extension keeps its records in CitryContext.extra.
EXTRA_KEY = "dependencies"

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
    strategy: str
    """The ``serialize(deps_strategy=...)`` value this emission runs under
    (``"document"``, ``"simple"``, or ``"fragment"``)."""
    before_manifest: list[Dependency]
    """Entries rendered as tags immediately before the ``data-citry`` page
    manifest tag (mutable). For anything that must already be in the DOM when
    the client-side manager processes the manifest, e.g. the events
    extension's own manifest tag. Only the strategies that emit the page
    manifest render these (``"document"`` and ``"fragment"``); under
    ``"simple"`` they are not emitted."""
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
    ownership_artifact: OwnershipManifestArtifact | None = None,
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
    records: list[DependencyRecord] = list(ctx.context.extra.get(EXTRA_KEY, {}))
    ownership = ownership_artifact or ctx.context.extra.get(OWNERSHIP_MANIFEST_KEY)
    scope_seed_instances = ownership.scope_seed_instances if isinstance(ownership, OwnershipManifestArtifact) else ()

    # "ignore": no tags inserted and no dependency hooks invoked. The policy
    # still inventories reached declarations because ignore cannot hide a
    # JavaScript requirement from forbid.
    if ctx.deps_strategy == "ignore":
        if javascript_policy is not None:
            _inspect_ignored_records(citry, records, scope_seed_instances, javascript_policy)
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
            scope_seed_instances=scope_seed_instances,
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
        script_security=script_security,
        scope_seed_instances=scope_seed_instances,
    )
    scripts, styles, calls = resolved.scripts, resolved.styles, resolved.calls

    # The extension-owned custom hook: other extensions adjust the lists in
    # place (docs/design/extensions.md section 9.2). The hook sees the
    # component-derived entries (possibly none); the runtime and the manifest
    # are appended after it, so URLs an extension adds here are still marked
    # as loaded.
    hook_ctx = OnDependenciesContext(
        citry=citry,
        scripts=scripts,
        styles=styles,
        context=ctx.context,
        strategy=ctx.deps_strategy,
        before_manifest=[],
        _security_csp=security_csp,
        _security_javascript=security_javascript,
    )
    citry.extensions.emit("on_dependencies", hook_ctx)
    scripts, styles, before_manifest = hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest
    _validate_hook_nonces(script_security, scripts, styles, before_manifest)
    graph_revision: str | None = None
    if isinstance(ownership, OwnershipManifestArtifact):
        graph_revision = ownership.revision
        before_manifest.insert(
            0,
            Script(
                kind="core",
                content=ownership.json(),
                attrs={"type": "application/json", "data-citry-graph": True},
            ),
        )

    # The client runtime and the page manifest ride along when the page either
    # runs per-instance JS (a component registered a `$component` callback,
    # so `calls` is non-empty) OR carries mounted component assets a later
    # fragment must dedup against (the `mark_*_urls`, only filled when mounted)
    # OR an extension contributed tags that must precede the manifest (the
    # events manifest tag). The manifest's `markLoaded` tells the client which
    # cache URLs this page already has, so a fragment inserted later does not
    # fetch them again. A page with none of the three stays as lean as
    # "simple". The `before_manifest` entries sit between the runtime and the
    # manifest tag, so they are already parsed when the manager processes the
    # manifest (the events boot-order rule, docs/design/events.md 5.2).
    core_scripts: list[Dependency] = []
    if with_client_js and (calls or resolved.mark_js_urls or resolved.mark_css_urls or before_manifest):
        mark_js = [*(script.url for script in scripts if script.url), *resolved.mark_js_urls]
        mark_css = [*(style.url for style in styles if style.url), *resolved.mark_css_urls]
        manifest = _build_manifest(
            mark_js=mark_js,
            mark_css=mark_css,
            fetch_js=[],
            fetch_css=[],
            calls=calls,
            css_instances=resolved.css_instances,
            graph_revision=graph_revision,
            alpine_runtime="csp" if security_csp == "strict" else "standard",
        )
        core_scripts = [
            _runtime_script(citry, alpine_runtime="csp" if security_csp == "strict" else "standard"),
            *before_manifest,
            manifest,
        ]

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
    scope_seed_instances: tuple[tuple[str, str], ...],
    javascript_policy: _JavascriptPolicy,
) -> None:
    """Inventory reached declarations without invoking ignored dependency hooks."""
    scope_seed_ids = {render_id for _class_id, render_id in scope_seed_instances}
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
        if record.js_vars_hash is not None and (uses_component(comp_cls) or record.component_id in scope_seed_ids):
            javascript_policy.add_requirement(
                "active js_data() scope seeding requires the Citry browser manager",
                component=comp_cls.__name__,
                key=("js-data", record.component_id, record.js_vars_hash),
            )


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
    scope_seed_instances: tuple[tuple[str, str], ...],
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
        scope_seed_instances=scope_seed_instances,
    )
    hook_ctx = OnDependenciesContext(
        citry=citry,
        scripts=resolved.scripts,
        styles=resolved.styles,
        context=ctx.context,
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
    if ctx.deps_position in ("prepend", "append"):
        html = _blank(ctx.html, all_placeholder_texts)
        if ctx.deps_position == "prepend":
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
    calls: list[_ComponentCall]
    # Cache URLs of the inlined component/variables scripts (only filled when
    # a web integration is mounted): a document page marks these as loaded so
    # a fragment inserted later does not fetch them again.
    mark_js_urls: list[str]
    mark_css_urls: list[str]
    # (class_id, component_id) of instances whose class has Component.css but
    # no component call. Nothing else registers such an instance with the
    # client-side manager, so the manifest declares it present and the manager
    # can count the class's live instances for Component.css cleanup
    # (docs/design/dependencies.md 8.4).
    css_instances: list[tuple[str, str]]
    # Fragment fetch descriptors are deduplicated across component instances,
    # but adoption still needs to know which incoming branches requested one.
    # Identity keys distinguish a hook-created equal descriptor from the
    # component-owned object it happens to duplicate.
    script_owners: dict[int, set[str]]
    style_owners: dict[int, set[str]]


def _resolve_records(
    citry: Citry,
    records: list[DependencyRecord],
    *,
    with_client_js: bool,
    as_urls: bool = False,
    attach_owned_resources: bool = False,
    script_security: _ScriptSecurityMaterializer | None = None,
    scope_seed_instances: tuple[tuple[str, str], ...] = (),
) -> _Resolved:
    """
    Turn the collected records into the ``scripts`` / ``styles`` lists plus
    the per-instance component calls for the client-side manager.

    Per record: the class's ``Dependencies`` entries, its own
    ``Component.js``/``css`` (read through the cache), and the variables
    script/stylesheet for the instance's hashed ``js_data()``/``css_data()``.
    ``Component.on_dependencies`` may adjust each record's lists. The final
    order is: core entries first, then all ``Dependencies`` entries, then all
    component scripts (a vendored lib from a ``Dependencies`` class loads
    before the component code that uses it), de-duplicated keeping the first
    occurrence.

    With ``with_client_js`` off (the "simple" strategy), the JS variables
    scripts and the component calls are skipped: both need the client-side
    manager, which only the "document" strategy includes.

    With ``as_urls`` on (the "fragment" strategy), component and variables
    scripts become url-based entries pointing at the cache endpoints instead
    of carrying their content, so the client-side manager fetches each once
    per page no matter how many fragments use it. ``attach_owned_resources``
    also binds each JavaScript URL to the exact currently cached response bytes
    for integrity-mode serialization.
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
    calls: list[_ComponentCall] = []
    called_ids: set[str] = set()
    scope_seed_by_id = {render_id: class_id for class_id, render_id in scope_seed_instances}
    mark_js_urls: list[str] = []
    mark_css_urls: list[str] = []
    css_instances: list[tuple[str, str]] = []
    script_owner_groups: dict[Dependency, set[str]] = {}
    style_owner_groups: dict[Dependency, set[str]] = {}

    # The class-level entries (a class's Dependencies plus its own JS/CSS) are
    # identical for every instance of the class, so resolve them once per class
    # and reuse them: a page commonly renders many instances of the same
    # component. Only the per-instance variables scripts and the client-side
    # call below differ between instances. Cached as (scripts, styles,
    # mark_js_url, mark_css_url, uses_component, css_only_presence).
    class_deps: dict[
        type[Component], tuple[list[Dependency], list[Dependency], str | None, str | None, bool, bool]
    ] = {}

    for record in records:
        # A render can be serialized after hot replacement installed a new
        # class with the same deterministic ID. Prefer the exact class that
        # rendered this record; the fallback keeps manually constructed and
        # older records compatible.
        comp_cls = record.component_class or citry.get_component_by_class_id(record.class_id)
        expected_seed_class = scope_seed_by_id.get(record.component_id)
        if expected_seed_class is not None and expected_seed_class != record.class_id:
            msg = f"Scope-seed instance {record.component_id!r} changed component class during serialization."
            raise RuntimeError(msg)

        cached = class_deps.get(comp_cls)
        if cached is None:
            scripts: list[Dependency] = []
            styles: list[Dependency] = []
            mark_js: str | None = None
            mark_css: str | None = None

            deps = comp_cls.get_dependencies()
            for entry in deps.js:
                scripts.append(_entry_to_script(entry, comp_cls, fragment=as_urls))
            for media_type, entries in deps.css.items():
                for entry in entries:
                    styles.append(_entry_to_style(entry, media_type, comp_cls, fragment=as_urls))

            # The class's own JS/CSS: inlined content for a page, a cache URL for
            # a fragment (the endpoint serves what the cache write here stores).
            # Either way the Component.css sheet is tagged with its class id
            # (data-citry-css-class), which is how the client-side manager's
            # cleanup finds the sheet when the class's last instance leaves the
            # page (docs/design/dependencies.md 8.4).
            css_class_attr: dict[str, str | bool] = {"data-citry-css-class": comp_cls.class_id}
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
                    if mounted:
                        mark_js = script_url(comp_cls, "js")
                comp_css = get_component_script("css", comp_cls)
                if comp_css is not None:
                    if mounted:
                        # A document inlines this sheet but tells the runtime
                        # that its fragment URL is loaded. Store the URL on the
                        # style so the runtime can clear both when it removes
                        # the sheet.
                        mark_css = script_url(comp_cls, "css")
                        css_class_attr["data-citry-css-url"] = mark_css
                    styles.append(replace(comp_css, attrs={**comp_css.attrs, **css_class_attr}))

            cached = (
                scripts,
                styles,
                mark_js,
                mark_css,
                with_client_js and uses_component(comp_cls),
                # An instance of a class with Component.css but no $component
                # callback appears in the manifest's presence record; see
                # _Resolved.css_instances.
                with_client_js and has_component_asset("css", comp_cls) and not uses_component(comp_cls),
            )
            class_deps[comp_cls] = cached

        cls_scripts, cls_styles, cls_mark_js, cls_mark_css, cls_uses_oncomp, cls_css_presence = cached
        call_mode: _CallMode | None = None
        if cls_uses_oncomp:
            call_mode = "init"
        elif with_client_js and record.component_id in scope_seed_by_id:
            call_mode = "seed"
        # Copy the class lists so the per-instance scripts below (and any
        # on_dependencies edit) never mutate the cached entry.
        instance_scripts: list[Dependency] = list(cls_scripts)
        instance_styles: list[Dependency] = list(cls_styles)
        if cls_mark_js is not None:
            mark_js_urls.append(cls_mark_js)
        if cls_mark_css is not None:
            mark_css_urls.append(cls_mark_css)

        # The variables scripts generated for this instance's data hashes.
        # Unlike class scripts these cannot be rebuilt on a cache miss (the
        # data existed only during the render). Legacy fragment output retains
        # its URL on a miss; integrity mode fails because it cannot prove bytes.
        # A shared cache backend prevents the miss across processes.
        if call_mode is not None and record.js_vars_hash is not None:
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
                    if mounted:
                        mark_js_urls.append(script_url(comp_cls, "js", record.js_vars_hash))
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
                    instance_styles.append(vars_css)
                    if mounted:
                        mark_css_urls.append(script_url(comp_cls, "css", record.css_vars_hash))

        if call_mode is not None:
            calls.append((record.class_id, record.component_id, record.js_vars_hash, call_mode))
            called_ids.add(record.component_id)
        if cls_css_presence and call_mode is None:
            css_instances.append((record.class_id, record.component_id))

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

    # A component with direct Alpine expressions needs a lifecycle and an
    # empty seed call even when it declares no assets and returns no JsData.
    # Such an instance has no dependency record, so add it from the settled
    # ownership artifact after record-backed calls have claimed their hashes.
    if with_client_js:
        for class_id, component_id in scope_seed_instances:
            if component_id in called_ids:
                continue
            calls.append((class_id, component_id, None, "seed"))
            called_ids.add(component_id)

    deduped_scripts = list(dict.fromkeys([*core_js, *extra_js, *component_js]))
    deduped_styles = list(dict.fromkeys([*core_css, *extra_css, *component_css]))

    return _Resolved(
        scripts=deduped_scripts,
        styles=deduped_styles,
        calls=calls,
        mark_js_urls=list(dict.fromkeys(mark_js_urls)),
        mark_css_urls=list(dict.fromkeys(mark_css_urls)),
        css_instances=css_instances,
        script_owners={id(dependency): set(script_owner_groups[dependency]) for dependency in deduped_scripts},
        style_owners={id(dependency): set(style_owner_groups[dependency]) for dependency in deduped_styles},
    )


# ----- The client runtime and the page manifest -----


@cache
def _runtime_js() -> str:
    """The client-side dependency manager's source (shipped as package data)."""
    return (Path(__file__).parent / "client" / "citry.js").read_text(encoding="utf8")


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


def _runtime_script(citry: Citry, *, alpine_runtime: Literal["standard", "csp"] = "standard") -> Script:
    # A mounted web integration serves the runtime at a URL (cacheable by the
    # browser); without one, the runtime is inlined so the zero-configuration
    # document flow still works end to end. wrap=False: the runtime is
    # already a self-contained immediately-invoked function.
    attrs: dict[str, str | bool] | None = {"data-citry-alpine-runtime": "csp"} if alpine_runtime == "csp" else None
    if citry.mounted_prefix is not None:
        return _owned_script(_runtime_resource(citry), kind="core", attrs=attrs)
    return Script(kind="core", content=_runtime_js(), wrap=False, attrs={} if attrs is None else attrs)


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
        "if (!globalThis.Citry || !globalThis.Citry.manager) {\n"
        '  var s = document.createElement("script");\n'
        f"  s.src = {url_literal};\n"
        f"{integrity_line}"
        f"{nonce_line}"
        "  document.head.appendChild(s);\n"
        "}\n"
        "if (document.currentScript) document.currentScript.remove();"
    )
    return Script(kind="core", content=content, wrap=True)


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _build_manifest(
    *,
    mark_js: list[str],
    mark_css: list[str],
    fetch_js: list[Dependency],
    fetch_css: list[Dependency],
    calls: list[_ComponentCall],
    css_instances: list[tuple[str, str]],
    graph_revision: str | None = None,
    fetch_js_owners: dict[int, set[str]] | None = None,
    fetch_css_owners: dict[int, set[str]] | None = None,
    before_manifest: list[Dependency] | None = None,
    transactional: bool = False,
    script_security: _ScriptSecurityMaterializer | None = None,
    alpine_runtime: Literal["standard", "csp"] = "standard",
) -> Script:
    """
    The page manifest: a ``<script type="application/json" data-citry>`` tag
    the client runtime watches for and processes.

    Carries which URLs are already on this page (so a fragment inserted later
    does not fetch them again), which tags to fetch (filled by fragments,
    empty for a document), which component instances to call, and which
    instances are present for CSS only (a ``Component.css`` instance with no
    ``$component`` callback, counted live for the per-class CSS cleanup).
    String fields ride as base64, so no value can break out of the script tag.
    """

    def encode_fetch(
        dependencies: list[Dependency],
        owners_by_identity: dict[int, set[str]] | None,
        *,
        kind: Literal["js", "css"],
    ) -> list[str] | list[list[str | list[str] | None]]:
        if not transactional:
            return [_b64(json.dumps(_dependency_descriptor(dep, script_security, kind=kind))) for dep in dependencies]

        # A global hook can append an object equal to a component dependency.
        # Keep the first descriptor position, union component owners, and let
        # one truly global occurrence make the deduplicated entry global.
        grouped: dict[Dependency, tuple[Dependency, set[str], bool]] = {}
        for dependency in dependencies:
            owners = None if owners_by_identity is None else owners_by_identity.get(id(dependency))
            current = grouped.get(dependency)
            if current is None:
                grouped[dependency] = (dependency, set(owners or ()), owners is None)
                continue
            current[1].update(owners or ())
            if owners is None and not current[2]:
                grouped[dependency] = (current[0], current[1], True)

        encoded: list[list[str | list[str] | None]] = []
        for dependency, owners, global_dependency in grouped.values():
            encoded_owners = None if global_dependency else [_b64(owner) for owner in sorted(owners)]
            descriptor = _dependency_descriptor(dependency, script_security, kind=kind)
            encoded.append([_b64(json.dumps(descriptor)), encoded_owners])
        return encoded

    manifest = {
        "markLoaded": {
            "js": [_b64(url) for url in dict.fromkeys(mark_js)],
            "css": [_b64(url) for url in dict.fromkeys(mark_css)],
        },
        "fetch": {
            "js": encode_fetch(fetch_js, fetch_js_owners, kind="js"),
            "css": encode_fetch(fetch_css, fetch_css_owners, kind="css"),
        },
        "calls": [
            [_b64(class_id), _b64(component_id), None if vars_hash is None else _b64(vars_hash), mode]
            for class_id, component_id, vars_hash, mode in calls
        ],
        "cssInstances": [[_b64(class_id), _b64(component_id)] for class_id, component_id in css_instances],
        "graph": graph_revision,
        "alpineRuntime": alpine_runtime,
    }
    if transactional:
        manifest["beforeManifest"] = [
            _b64(json.dumps(_dependency_descriptor(dependency, script_security, kind="before")))
            for dependency in before_manifest or []
        ]
    return Script(kind="core", content=json.dumps(manifest), attrs={"type": "application/json", "data-citry": True})


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
    The "fragment" strategy: content followed by the pre-loader and a
    fetch-manifest, nothing inlined.

    The fragment references its scripts by URL (the cache endpoints), so the
    client-side manager fetches each dependency once per page however many
    fragments need it; local-file ``Dependencies`` entries, which have no
    URL, ride as inline tag descriptors. Requires a mounted web integration
    (the URLs must point somewhere), and, with multiple worker processes, a
    shared cache backend (docs/design/dependencies.md section 8.3).
    """
    fragment_needs_mount_msg = (
        "serialize(deps_strategy='fragment') needs a mounted web integration:"
        " the fragment references its JS/CSS by URL. Mount one (e.g."
        " citry.contrib.fastapi.mount(app, citry_instance)), or use"
        " set_mounted_prefix() in processes that only render."
    )
    ownership = ctx.context.extra.get(OWNERSHIP_MANIFEST_KEY)
    scope_seed_instances = ownership.scope_seed_instances if isinstance(ownership, OwnershipManifestArtifact) else ()
    if records or scope_seed_instances:
        if citry.mounted_prefix is None:
            raise RuntimeError(fragment_needs_mount_msg)
        resolved = _resolve_records(
            citry,
            records,
            with_client_js=True,
            as_urls=True,
            attach_owned_resources=script_security is not None and script_security.integrity_enabled,
            script_security=script_security,
            scope_seed_instances=scope_seed_instances,
        )
    else:
        resolved = _Resolved(
            scripts=[],
            styles=[],
            calls=[],
            mark_js_urls=[],
            mark_css_urls=[],
            css_instances=[],
            script_owners={},
            style_owners={},
        )
    scripts, styles = resolved.scripts, resolved.styles

    hook_ctx = OnDependenciesContext(
        citry=citry,
        scripts=scripts,
        styles=styles,
        context=ctx.context,
        strategy="fragment",
        before_manifest=[],
        _security_csp=security_csp,
        _security_javascript=security_javascript,
    )
    citry.extensions.emit("on_dependencies", hook_ctx)
    scripts, styles, before_manifest = hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest
    _validate_hook_nonces(script_security, scripts, styles, before_manifest)
    graph_revision: str | None = None
    ownership_tag: Dependency | None = None
    if isinstance(ownership, OwnershipManifestArtifact):
        graph_revision = ownership.revision
        ownership_tag = Script(
            kind="core",
            content=ownership.json(),
            attrs={"type": "application/json", "data-citry-graph": True},
        )

    framework_manifests: list[Dependency] = []
    staged_before_manifest: list[Dependency] = []
    for dependency in before_manifest:
        if (
            graph_revision is not None
            and isinstance(dependency, Script)
            and dependency.attrs.get("type") == "application/json"
            and (dependency.attrs.get("data-citry-events") is True or dependency.attrs.get("data-citry-i18n") is True)
        ):
            framework_manifests.append(dependency)
        elif graph_revision is not None:
            staged_before_manifest.append(dependency)
        else:
            framework_manifests.append(dependency)
    if ownership_tag is not None:
        framework_manifests.insert(0, ownership_tag)

    if javascript_policy is not None:
        scripts = javascript_policy.process_dependencies(scripts, position="fragment fetch")
        styles = javascript_policy.process_dependencies(styles, position="fragment stylesheet")
        framework_manifests = javascript_policy.process_dependencies(
            framework_manifests,
            position="fragment framework",
        )
        staged_before_manifest = javascript_policy.process_dependencies(
            staged_before_manifest,
            position="fragment before-manifest",
        )

    # A fragment that carries nothing at all has nothing to load, so it needs
    # no pre-loader or manifest (and no mounted integration).
    if not scripts and not styles and not resolved.calls and not resolved.css_instances and not before_manifest:
        return _blank(ctx.html, placeholder_texts)
    if citry.mounted_prefix is None:
        raise RuntimeError(fragment_needs_mount_msg)

    html = _blank(ctx.html, placeholder_texts)
    # Ownership and Events manifests stay inert top-level JSON. Every other
    # graph-backed hook entry is a descriptor inside the dependency manifest,
    # so an ignored incoming branch cannot execute it during fragment parsing.
    if script_security is None:
        manifest = _build_manifest(
            mark_js=[],
            mark_css=[],
            fetch_js=scripts,
            fetch_css=styles,
            calls=resolved.calls,
            css_instances=resolved.css_instances,
            graph_revision=graph_revision,
            fetch_js_owners=resolved.script_owners,
            fetch_css_owners=resolved.style_owners,
            before_manifest=staged_before_manifest,
            transactional=graph_revision is not None,
            alpine_runtime="standard",
        )
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
    manifest = _build_manifest(
        mark_js=[],
        mark_css=[],
        fetch_js=scripts,
        fetch_css=styles,
        calls=resolved.calls,
        css_instances=resolved.css_instances,
        graph_revision=graph_revision,
        fetch_js_owners=resolved.script_owners,
        fetch_css_owners=resolved.style_owners,
        before_manifest=staged_before_manifest,
        transactional=graph_revision is not None,
        script_security=script_security,
        alpine_runtime="csp" if security_csp == "strict" else "standard",
    )
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


def _dependency_descriptor(
    dependency: Dependency,
    script_security: _ScriptSecurityMaterializer | None,
    *,
    kind: Literal["js", "css", "before"],
) -> dict[str, str | dict[str, str | bool]]:
    if script_security is not None and kind == "js":
        return script_security.descriptor(dependency)
    if script_security is not None and kind == "css":
        return script_security.style_descriptor(dependency)
    if script_security is not None and isinstance(dependency, Script):
        return script_security.descriptor(dependency)
    if script_security is not None and isinstance(dependency, Style):
        return script_security.style_descriptor(dependency)
    descriptor = dependency.render_json()
    rejects_opaque = descriptor.get("tag") == "script" or (
        descriptor.get("tag") == "style" and script_security is not None and script_security.csp_nonce is not None
    )
    if script_security is not None and rejects_opaque:
        msg = "Executable before-manifest dependency descriptors must use structured Script or Style objects."
        raise TypeError(msg)
    return descriptor


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
