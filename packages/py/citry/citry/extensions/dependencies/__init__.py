"""
The ``dependencies`` built-in extension: a component's secondary assets.

A component declares extra JS/CSS files in a nested ``Dependencies`` class::

    class Card(Component):
        class Dependencies:
            js = ["vendor/chart.js"]
            css = {"all": "theme.css", "print": "print.css"}
            extend = True   # inherit entries from base classes (the default)

This extension owns that whole concern:
- The nested class (through the extension system's per-component config mechanism,
  since the extension name ``dependencies`` derives the config class name ``Dependencies``),
- The normalization and path resolution of entries,
- The merge across the component's base classes.

The merged result is read through ``Card.get_dependencies()``,
which returns a :class:`CitryDependencies`.

Entries may also be :class:`Script`/:class:`Style` objects (see ``types.py``),
which say exactly what tag to emit and pass through resolution unchanged.

What the entries *mean* in the rendered output (inline the file content, emit
a ``<script src>`` tag, ...) is the emission half, which is in ``emission.py``.
This is citry's realization of django-components #1144 ("media becomes an extension"),
built as an extension from the start.

Design: docs/design/asset_loading.md section 7.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary

from citry.assets import HasHtml, dedupe, module_dir, resolve_asset_file
from citry.extension import (
    Extension,
    ExtensionConfig,
    OnComponentClassCreatedContext,
    OnComponentDataContext,
    OnFilesResetContext,
    OnRenderContextMergeContext,
    OnSerializeContext,
)
from citry.extensions.dependencies.emission import EXTRA_KEY, OnDependenciesContext, emit_dependencies
from citry.extensions.dependencies.scripts import (
    cache_component_css,
    cache_component_css_vars,
    cache_component_js,
    cache_component_js_vars,
    evict_component_scripts,
)
from citry.extensions.dependencies.types import Dependency, DependencyRecord, Script, Style
from citry.util.misc import is_glob

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.component import Component
    from citry.util.routing import URLRoute

__all__ = [
    "CitryDependencies",
    "DependenciesExtension",
    "Dependency",
    "DependencyRecord",
    "OnDependenciesContext",
    "Script",
    "Style",
    "get_dependencies",
]


@dataclass(frozen=True, slots=True)
class CitryDependencies:
    """
    A component's merged secondary assets (from the nested ``Dependencies``
    classes).

    Holds resolved entries:
    - a local file - resolved to ``Path``
    - URLs (plain strings) - unchanged
    - ``Script``/``Style`` objects - unchanged
    - Pre-rendered tags (`__html__`) - unchanged

    The entry's type is what tells the emission step what
    to do with it (inline the file content, emit a ``src``/``href`` tag, or
    output the tag verbatim; see ``emission.py``).

    Attributes:
        js: JS entries, base classes' entries first, then the class's own,
            de-duplicated.
        css: CSS entries per media type (``"all"``, ``"print"``, ...), same
            ordering per list.

    """

    js: tuple[Any, ...] = ()
    css: Mapping[str, tuple[Any, ...]] = field(default_factory=dict)

    def __add__(self, other: CitryDependencies) -> CitryDependencies:
        """Concatenate two sets (left first), keeping first-seen order and dropping duplicates."""
        if not isinstance(other, CitryDependencies):
            return NotImplemented  # type: ignore[unreachable]
        js = dedupe((*self.js, *other.js))
        css: dict[str, tuple[Any, ...]] = {}
        for media_type in dict.fromkeys((*self.css, *other.css)):
            css[media_type] = dedupe((*self.css.get(media_type, ()), *other.css.get(media_type, ())))
        return CitryDependencies(js=js, css=css)

    def __bool__(self) -> bool:
        return bool(self.js) or bool(self.css)


def get_dependencies(comp_cls: type[Component]) -> CitryDependencies:
    """
    The merged secondary assets of a component class.

    Routes through the class's Citry instance to its built-in ``dependencies``
    extension. Users reach this through ``Card.get_dependencies()``.
    """
    extension = comp_cls.citry.extensions.get_extension(DependenciesExtension.name)
    if not isinstance(extension, DependenciesExtension):  # defensive; the name is reserved
        msg = f"Extension {DependenciesExtension.name!r} is not the built-in DependenciesExtension"
        raise TypeError(msg)
    return extension.resolve(comp_cls)


class DependenciesExtension(Extension):
    """
    The built-in extension owning the ``Dependencies`` secondary-asset class.

    The loading half: captures each component class's raw ``Dependencies``
    declaration in ``on_component_class_created`` (before the extension
    manager's config rebuild replaces the nested class; see the design doc for
    why the raw declaration, not the rebuilt config, must feed the merge),
    resolves and merges declarations lazily in :meth:`resolve`, and drops a
    class's merged result when its files are reset (``on_files_reset``).

    The emission half (docs/design/dependencies.md): records each component
    render (``on_component_data``), bubbles the records up as nested renders
    are consumed (``on_render_context_merge``), and at serialize time turns them into
    ``<script>``/``<style>``/``<link>`` tags placed into the page
    (``on_serialize``, implemented in ``emission.py``).
    """

    name = "dependencies"

    class Config(ExtensionConfig):
        """Defaults for the per-component ``Dependencies`` config class."""

        js: Any = None
        css: Any = None
        extend: bool | list[type[Component]] = True
        local_files: str = "inline"
        """
        What a ``Dependencies`` entry that resolved to a local file becomes
        in the output:
        - ``"inline"`` embeds the file content in the page;
        - ``"serve"`` emits a fingerprinted URL on citry's routes
        (``asset/<content hash>.<ext>``), so the browser caches the file and
        the client-side manager de-duplicates it across pages and fragments.

        ``"serve"`` falls back to inlining when no web integration is
        mounted. Set per component here, or globally via
        ``extensions_defaults={"dependencies": {"local_files": "serve"}}``.

        See docs/design/dependencies.md section 9.4."""

    def __init__(self) -> None:
        # Raw per-class declarations, captured at class creation. A key is
        # present only when the class itself declared `Dependencies`; the
        # value is the user's class, or None for an explicit `Dependencies =
        # None` ("no entries, no inheritance"). Weak keys, so unregistered
        # component classes can be garbage-collected.
        self._declarations: WeakKeyDictionary[type, type | None] = WeakKeyDictionary()
        # Merged results, cached per class.
        self._merged: WeakKeyDictionary[type, CitryDependencies] = WeakKeyDictionary()

    def on_component_class_created(self, ctx: OnComponentClassCreatedContext) -> None:
        # This hook fires before the manager rebuilds the nested class into a
        # config class, so cls.__dict__ still holds exactly what the user
        # wrote (a class, None, or nothing).
        if "Dependencies" in ctx.component_class.__dict__:
            self._declarations[ctx.component_class] = ctx.component_class.__dict__["Dependencies"]

    def on_files_reset(self, ctx: OnFilesResetContext) -> None:
        # The captured declaration is class-definition data and stays; only
        # the merged result (which embeds resolved file paths) and the cached
        # processed scripts are dropped.
        self._merged.pop(ctx.component_class, None)
        evict_component_scripts(ctx.component_class)

    # ----- Collection during render (docs/design/dependencies.md section 6) -----

    def on_component_data(self, ctx: OnComponentDataContext) -> None:
        comp_cls = type(ctx.component)
        # Record only components that actually carry assets; <c-provide> and
        # plain markup-only components add nothing to emit. The accessors are
        # cached per class, so this costs a few attribute reads per render.
        if comp_cls.get_js() is None and comp_cls.get_css() is None and not comp_cls.get_dependencies():
            return
        # Keep the class's processed scripts cached, in case they were evicted
        # (also what the script-serving endpoint in routes.py reads).
        cache_component_js(comp_cls)
        cache_component_css(comp_cls)
        # Per-render variables: hash each data method's result and cache the
        # generated script/stylesheet under the hash, so identical data is
        # delivered to the browser once (docs/design/dependencies.md
        # section 5).
        js_vars_hash = cache_component_js_vars(comp_cls, ctx.js_data) if ctx.js_data else None
        css_vars_hash = cache_component_css_vars(comp_cls, ctx.css_data) if ctx.css_data else None
        if css_vars_hash is not None:
            # The instance's root elements get the matching marker attribute,
            # which the generated stylesheet scopes its custom properties to.
            ctx.context._add_root_markers([f"data-ccss-{css_vars_hash}"])
        records: list[DependencyRecord] = ctx.context.extra.setdefault(EXTRA_KEY, [])
        records.append(
            DependencyRecord(
                class_id=comp_cls.class_id,
                component_id=ctx.component.id,
                js_vars_hash=js_vars_hash,
                css_vars_hash=css_vars_hash,
            )
        )

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        # A nested render was consumed by an enclosing one: its records join
        # the enclosing list, preserving order (parent's own record was added
        # before its children rendered, so the list approximates document
        # order; emission dedupes).
        child_records = ctx.child_context.extra.get(EXTRA_KEY)
        if child_records:
            parent_records: list[DependencyRecord] = ctx.parent_context.extra.setdefault(EXTRA_KEY, [])
            parent_records.extend(child_records)

    # ----- Emission at serialize (docs/design/dependencies.md section 7) -----

    def on_serialize(self, ctx: OnSerializeContext) -> str | None:
        return emit_dependencies(ctx.citry, ctx)

    # ----- HTTP routes (docs/design/dependencies.md section 9) -----

    @property
    def urls(self) -> list[URLRoute]:
        # Imported here, not at module load: routes.py imports back into this
        # package, and routing is only needed when a web integration asks.
        from citry.extensions.dependencies.routes import dependency_routes  # noqa: PLC0415

        return dependency_routes(self.citry)

    # ----- Resolution and merge -----

    def resolve(self, comp_cls: type[Component]) -> CitryDependencies:
        """
        Resolve and merge ``comp_cls``'s secondary assets, cached per class.

        Merge order is **bases first, own entries last**: list order becomes
        document order at emission and CSS breaks equal-specificity ties by
        document order, so the more specialized class's styles must come later
        to win (docs/design/asset_loading.md section 7.3).

        ``Component.Dependencies.extend`` picks the bases:
        - ``True`` - inherit JS/CSS from `Component.Dependencies` of Component's base classes
        - ``False`` - no inheritance; only the class's own entries (if any)
        - a list - exactly those classes + their bases, in the order given

        An explicit ``Dependencies = None`` declaration means no own entries and no inheritance.
        """
        cached = self._merged.get(comp_cls)
        if cached is not None:
            return cached

        # Imported here, not at module load: this module is imported while the
        # default Citry instance is being constructed (the built-in extension
        # spec), which happens before component.py can be imported.
        from citry.component import Component  # noqa: PLC0415

        declared = comp_cls in self._declarations
        declaration = self._declarations.get(comp_cls)

        own = self._build_own(comp_cls, declaration)

        # `Dependencies = None` means: no inheritance either.
        if declared and declaration is None:
            bases: tuple[type, ...] = ()
        else:
            extend = getattr(declaration, "extend", True) if declaration is not None else True
            if extend is True:
                bases = comp_cls.__bases__
            elif extend is False:
                bases = ()
            else:
                bases = tuple(extend)

        merged = CitryDependencies()
        for base in bases:
            if not (isinstance(base, type) and issubclass(base, Component)) or base is Component:
                continue
            # Route through the base's own Citry instance (an `extend` list may
            # name classes bound to a different one).
            merged = merged + get_dependencies(base)
        merged = merged + own

        self._merged[comp_cls] = merged
        return merged

    def _build_own(self, comp_cls: type[Component], declaration: type | None) -> CitryDependencies:
        """Normalize and resolve the entries declared on this class's own ``Dependencies``."""
        if declaration is None:
            return CitryDependencies()

        js_entries, css_entries = _normalize_input(comp_cls, declaration)

        js = dedupe(entry for raw in js_entries for entry in _resolve_entry(raw, comp_cls))
        css = {
            media_type: dedupe(entry for raw in raw_entries for entry in _resolve_entry(raw, comp_cls))
            for media_type, raw_entries in css_entries.items()
        }
        return CitryDependencies(js=js, css=css)


def _normalize_input(
    comp_cls: type[Component],
    declaration: type,
) -> tuple[list[Any], dict[str, list[Any]]]:
    """
    Normalize the ``Dependencies`` input shapes without mutating the user's class.

    ``js``:
    - single entry or list -> list.

    ``css``:
    - single entry or list -> ``{"all": [...]}``;
    - dict -> each value to a list.

    (django-components normalizes tot the same shapes, but rewrites the user's class in place;
    citry leaves the declaration as written.)
    """
    raw_js = getattr(declaration, "js", None)
    raw_css = getattr(declaration, "css", None)

    js_entries: list[Any] = []
    if raw_js is not None:
        if _is_single_entry(raw_js):
            js_entries = [raw_js]
        elif isinstance(raw_js, (list, tuple)):
            js_entries = list(raw_js)
        else:
            msg = (
                f"Dependencies.js must be a path, a list of paths, or a callable;"
                f" got {type(raw_js)} on {comp_cls.__name__}"
            )
            raise ValueError(msg)

    css_entries: dict[str, list[Any]] = {}
    if raw_css is not None:
        if _is_single_entry(raw_css):
            css_entries = {"all": [raw_css]}
        elif isinstance(raw_css, (list, tuple)):
            css_entries = {"all": list(raw_css)}
        elif isinstance(raw_css, dict):
            for media_type, value in raw_css.items():
                css_entries[media_type] = [value] if _is_single_entry(value) else list(value)
        else:
            msg = (
                f"Dependencies.css must be a path, a list, or a dict of media types;"
                f" got {type(raw_css)} on {comp_cls.__name__}"
            )
            raise ValueError(msg)

    return js_entries, css_entries


def _is_single_entry(value: Any) -> bool:
    """Whether a ``Dependencies`` value is one entry (vs a list of entries)."""
    if callable(value):
        return True
    if isinstance(value, HasHtml):
        return True
    return isinstance(value, (str, Path, os.PathLike))


def _resolve_entry(entry: Any, comp_cls: type[Component]) -> list[Any]:
    """
    Resolve one ``Dependencies`` entry to zero or more output entries.

    - Callables are invoked (lazily, here, not at class definition).
    - ``Script``/``Style`` objects pass through unchanged: they already say
      exactly what tag to emit (docs/design/dependencies.md section 3).
    - Pre-rendered tags (objects with ``__html__``) pass through unchanged.
    - URLs pass through unchanged.
    - Globs expand (sorted, for deterministic output) relative to the module
      dir, then relative to the Citry dirs; no match keeps the entry as-is.
    - Plain paths resolve through the standard chain to an absolute ``Path``
      and are registered in the file index. The ``Path`` type is what marks
      "local file" for the emission step (URL-like strings such as
      ``/static/x.css`` stay strings). An unresolvable path is kept as-is
      (it may be meaningful to the consumer, e.g. a server static route).
    """
    if callable(entry):
        entry = entry()

    if isinstance(entry, Dependency):
        return [entry]

    if isinstance(entry, HasHtml) and not isinstance(entry, (str, Path)):
        return [entry]

    if isinstance(entry, (Path, os.PathLike)):
        entry = Path(entry).as_posix()

    if not isinstance(entry, str):
        msg = (
            f"Unknown Dependencies entry {entry!r} of type {type(entry)} on {comp_cls.__name__}."
            f" Must be a str, Path, pre-rendered tag (object with __html__),"
            f" or a callable returning one of those."
        )
        raise TypeError(msg)

    # Pre-rendered markup that is also a str subclass (e.g. markupsafe.Markup).
    if isinstance(entry, HasHtml):
        return [entry]

    # URL prefixes, matching django-components' Media.absolute_path() rule.
    if entry.startswith(("http://", "https://", "://", "/")):
        return [entry]

    citry_instance = comp_cls.citry

    # Resolve globs relative to the module dir, then relative to the Citry dirs.
    if is_glob(entry):
        search_dirs: list[Path] = []
        comp_module_dir = module_dir(comp_cls)
        if comp_module_dir is not None:
            search_dirs.append(comp_module_dir)
        search_dirs.extend(citry_instance.settings.dirs)
        for base_dir in search_dirs:
            matches = sorted(base_dir.glob(entry))
            if matches:
                resolved = [match.resolve() for match in matches if match.is_file()]
                for resolved_path in resolved:
                    citry_instance._register_component_file(resolved_path, comp_cls)
                return list(resolved)
        return [entry]

    try:
        path = resolve_asset_file(entry, comp_cls)
    except FileNotFoundError:
        return [entry]
    citry_instance._register_component_file(path, comp_cls)
    return [path]
