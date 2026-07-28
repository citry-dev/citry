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
from typing import TYPE_CHECKING, Any, TypeAlias

from citry.assets import HasHtml
from citry.ext.dependencies.routes import runtime_url, script_url
from citry.ext.dependencies.scripts import (
    cache_asset,
    cache_component_css,
    cache_component_js,
    get_component_script,
    get_script,
    has_component_asset,
    uses_component,
)
from citry.ext.dependencies.types import Dependency, Script, Style
from citry.ownership_manifest import EXTRA_KEY as OWNERSHIP_MANIFEST_KEY
from citry.ownership_manifest import OwnershipManifestArtifact
from citry.util.html import SafeString

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.component import Component
    from citry.ext.dependencies.types import DependencyRecord
    from citry.extension import OnSerializeContext

# One "run this instance's $component callback" entry for the client-side
# manager: (class_id, component_id, js_vars_hash or None).
_ComponentCall: TypeAlias = tuple[str, str, "str | None"]

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


@dataclass(eq=False)
class _PrerenderedTag(Dependency):
    """
    A ``Dependencies`` entry that was a pre-rendered tag (an object with
    ``__html__``): emitted verbatim. ``content`` holds the full tag text.
    """

    def render(self) -> SafeString:
        return SafeString(self.content or "")


def emit_dependencies(citry: Citry, ctx: OnSerializeContext) -> str:
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

    # "ignore": no tags inserted; the internal placeholders are still removed,
    # they are render artifacts, not user content.
    if ctx.deps_strategy == "ignore":
        return _blank(ctx.html, all_placeholder_texts)

    # Collected as an insertion-ordered set (a dict) so the bubble-up merge
    # dedupes on insert instead of accumulating one copy per ancestor.
    records: list[DependencyRecord] = list(ctx.context.extra.get(EXTRA_KEY, {}))

    # "fragment": nothing is inlined; the output carries a pre-loader plus a
    # manifest of URLs for the client-side manager to fetch (section 8).
    if ctx.deps_strategy == "fragment":
        return _emit_fragment(citry, ctx, records, all_placeholder_texts)

    # "document" includes the client-side manager and everything that needs
    # it (the JS-variables scripts, the per-instance component calls, the
    # manifest). "simple" is the no-JS-runtime mode: component and
    # Dependencies tags only, so per-instance JS does not run there.
    # CSS variables are pure CSS (a stylesheet plus a root-element marker)
    # and work under both.
    with_client_js = ctx.deps_strategy == "document"
    resolved = _resolve_records(citry, records, with_client_js=with_client_js)
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
    )
    citry.extensions.emit("on_dependencies", hook_ctx)
    scripts, styles, before_manifest = hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest
    ownership = ctx.context.extra.get(OWNERSHIP_MANIFEST_KEY)
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
        )
        core_scripts = [_runtime_script(citry), *before_manifest, manifest]

    js_html = "".join(str(script.render()) for script in [*core_scripts, *scripts])
    css_html = "".join(str(style.render()) for style in styles)

    if ctx.deps_position in ("prepend", "append"):
        html = _blank(ctx.html, all_placeholder_texts)
        if ctx.deps_position == "prepend":
            return js_html + css_html + html
        return html + js_html + css_html

    # "smart": placeholders first, default locations as the fallback.
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
    # no $component callback. Nothing else registers such an instance with
    # the client-side manager, so the manifest declares it present and the
    # manager can count the class's live instances for the Component.css
    # cleanup (docs/design/dependencies.md 8.4).
    css_instances: list[tuple[str, str]]


def _resolve_records(
    citry: Citry,
    records: list[DependencyRecord],
    *,
    with_client_js: bool,
    as_urls: bool = False,
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
    per page no matter how many fragments use it.
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
    mark_js_urls: list[str] = []
    mark_css_urls: list[str] = []
    css_instances: list[tuple[str, str]] = []

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
                    scripts.append(
                        Script(url=script_url(comp_cls, "js"), kind="component", origin_class_id=comp_cls.class_id)
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
                    styles.append(replace(comp_css, attrs={**comp_css.attrs, **css_class_attr}))
                    if mounted:
                        mark_css = script_url(comp_cls, "css")

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
        # data existed only during the render), so a missing entry is
        # skipped; a shared cache backend prevents this across processes.
        if with_client_js and record.js_vars_hash is not None:
            if as_urls:
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

        if cls_uses_oncomp:
            calls.append((record.class_id, record.component_id, record.js_vars_hash))
        if cls_css_presence:
            css_instances.append((record.class_id, record.component_id))

        # Per-component hook: adjust this instance's lists before they join
        # the page-wide ones.
        result = comp_cls.on_dependencies(instance_scripts, instance_styles)
        if result is not None:
            instance_scripts, instance_styles = result

        for script in instance_scripts:
            _bucket(script, core_js, extra_js, component_js)
        for style in instance_styles:
            _bucket(style, core_css, extra_css, component_css)

    return _Resolved(
        scripts=list(dict.fromkeys([*core_js, *extra_js, *component_js])),
        styles=list(dict.fromkeys([*core_css, *extra_css, *component_css])),
        calls=calls,
        mark_js_urls=list(dict.fromkeys(mark_js_urls)),
        mark_css_urls=list(dict.fromkeys(mark_css_urls)),
        css_instances=css_instances,
    )


# ----- The client runtime and the page manifest -----


@cache
def _runtime_js() -> str:
    """The client-side dependency manager's source (shipped as package data)."""
    return (Path(__file__).parent / "client" / "citry.js").read_text(encoding="utf8")


def _runtime_script(citry: Citry) -> Script:
    # A mounted web integration serves the runtime at a URL (cacheable by the
    # browser); without one, the runtime is inlined so the zero-configuration
    # document flow still works end to end. wrap=False: the runtime is
    # already a self-contained immediately-invoked function.
    if citry.mounted_prefix is not None:
        return Script(kind="core", url=runtime_url(citry))
    return Script(kind="core", content=_runtime_js(), wrap=False)


def _preloader_script(citry: Citry) -> Script:
    """
    The fragment pre-loader: loads the client runtime if the page does not
    have it yet, so fragments work even on pages that were not rendered with
    the "document" strategy. Removes its own tag afterward.
    """
    url = runtime_url(citry)
    if '"' in url:
        msg = f"The runtime URL cannot contain quotes, got {url!r}"
        raise ValueError(msg)
    content = (
        "if (!globalThis.Citry || !globalThis.Citry.manager) {\n"
        '  var s = document.createElement("script");\n'
        f'  s.src = "{url}";\n'
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
    manifest = {
        "markLoaded": {
            "js": [_b64(url) for url in dict.fromkeys(mark_js)],
            "css": [_b64(url) for url in dict.fromkeys(mark_css)],
        },
        "fetch": {
            "js": [_b64(json.dumps(dep.render_json())) for dep in fetch_js],
            "css": [_b64(json.dumps(dep.render_json())) for dep in fetch_css],
        },
        "calls": [
            [_b64(class_id), _b64(component_id), None if vars_hash is None else _b64(vars_hash)]
            for class_id, component_id, vars_hash in calls
        ],
        "cssInstances": [[_b64(class_id), _b64(component_id)] for class_id, component_id in css_instances],
        "graph": graph_revision,
    }
    return Script(kind="core", content=json.dumps(manifest), attrs={"type": "application/json", "data-citry": True})


def _emit_fragment(
    citry: Citry,
    ctx: OnSerializeContext,
    records: list[DependencyRecord],
    placeholder_texts: list[str],
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
    if records:
        if citry.mounted_prefix is None:
            raise RuntimeError(fragment_needs_mount_msg)
        resolved = _resolve_records(citry, records, with_client_js=True, as_urls=True)
    else:
        resolved = _Resolved(scripts=[], styles=[], calls=[], mark_js_urls=[], mark_css_urls=[], css_instances=[])
    scripts, styles = resolved.scripts, resolved.styles

    hook_ctx = OnDependenciesContext(
        citry=citry,
        scripts=scripts,
        styles=styles,
        context=ctx.context,
        strategy="fragment",
        before_manifest=[],
    )
    citry.extensions.emit("on_dependencies", hook_ctx)
    scripts, styles, before_manifest = hook_ctx.scripts, hook_ctx.styles, hook_ctx.before_manifest
    ownership = ctx.context.extra.get(OWNERSHIP_MANIFEST_KEY)
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

    # A fragment that carries nothing at all has nothing to load, so it needs
    # no pre-loader or manifest (and no mounted integration).
    if not scripts and not styles and not resolved.calls and not resolved.css_instances and not before_manifest:
        return _blank(ctx.html, placeholder_texts)
    if citry.mounted_prefix is None:
        raise RuntimeError(fragment_needs_mount_msg)

    manifest = _build_manifest(
        mark_js=[],
        mark_css=[],
        fetch_js=scripts,
        fetch_css=styles,
        calls=resolved.calls,
        css_instances=resolved.css_instances,
        graph_revision=graph_revision,
    )
    html = _blank(ctx.html, placeholder_texts)
    # The `before_manifest` entries render as real tags (not fetch
    # descriptors) directly before the manifest tag, so they are already in
    # the DOM when the client-side manager processes the manifest.
    before_html = "".join(str(dep.render()) for dep in before_manifest)
    return html + str(_preloader_script(citry).render()) + before_html + str(manifest.render())


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
        url = _maybe_serve_local_file(entry, comp_cls)
        if url is not None:
            return Script(url=url, kind="extra", origin_class_id=comp_cls.class_id)
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
        url = _maybe_serve_local_file(entry, comp_cls)
        if url is not None:
            return Style(url=url, attrs=media_attrs, kind="extra", origin_class_id=comp_cls.class_id)
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


def _maybe_serve_local_file(path: Path, comp_cls: type[Component]) -> str | None:
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
    file_name = cache_asset(citry, _read_asset(path), path.suffix.lstrip("."))
    return citry.build_url(f"asset/{file_name}")


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
