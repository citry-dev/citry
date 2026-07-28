"""
Implementation of the ``dependencies`` extension: the extension class, and the
resolution and merge of a component's declared entries.

The package ``__init__`` re-exports the public names; this module holds the
loading half (capture each class's ``Dependencies`` declaration, resolve
entries to files or URLs, merge across base classes). The serialize-time half
(turning collected render records into tags) is in ``emission.py``.

Design: docs/design/asset_loading.md section 7.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry._nested_declarations import _get_nested_class_declarations
from citry.assets import HasHtml, dedupe, module_dir, resolve_asset_file
from citry.ext.dependencies.emission import EXTRA_KEY, emit_dependencies
from citry.ext.dependencies.scripts import (
    _cache_component_css_vars_capture,
    _cache_component_js_vars_capture,
    _css_vars_capture,
    _js_vars_capture,
    _VariablesScriptCapture,
    cache_component_css,
    cache_component_js,
    evict_component_script_keys,
    evict_component_scripts,
    gen_cache_key,
    has_component_asset,
    uses_component,
)
from citry.ext.dependencies.types import Dependency, DependencyRecord
from citry.extension import (
    Extension,
    ExtensionConfig,
    OnComponentDataContext,
    OnComponentUnregisteredContext,
    OnFilesResetContext,
    OnRenderCacheExportContext,
    OnRenderCacheStageContext,
    OnRenderContextMergeContext,
    OnSerializeContext,
    RenderCacheWrite,
    StagedRenderCacheContribution,
)
from citry.util.misc import is_glob

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.component import Component
    from citry.util.routing import URLRoute


@dataclass(frozen=True, slots=True)
class CitryDependencies:
    """
    A component's merged secondary assets (from the nested ``Dependencies``
    classes).

    Holds resolved entries:

    - a local file (declared with ``PathLike`` or a resolvable string) - resolved to ``Path``
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


@dataclass(frozen=True, slots=True)
class _DependencyCacheCapture:
    """Detached-value inputs needed to rebuild one dependency record."""

    js: _VariablesScriptCapture | None = None
    css: _VariablesScriptCapture | None = None


_DEPENDENCIES_CACHE_ATTR = "_citry_dependencies_cache"


def _cached_dependencies(component_class: type) -> CitryDependencies | None:
    """Return a merged result stored directly on one concrete component class."""
    value = vars(component_class).get(_DEPENDENCIES_CACHE_ATTR)
    return value if isinstance(value, CitryDependencies) else None


def _clear_cached_dependencies(component_class: type) -> None:
    """Drop one class-owned merged result without invoking its metaclass."""
    if _DEPENDENCIES_CACHE_ATTR in vars(component_class):
        type.__delattr__(component_class, _DEPENDENCIES_CACHE_ATTR)


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

    The loading half reads each component or reusable definition base's
    preserved ``Dependencies`` declaration, resolves and merges declarations
    lazily in :meth:`resolve`, and drops a class's derived state when its files
    are reset or its final registry alias is removed.

    The emission half (docs/design/dependencies.md): records each component
    render (``on_component_data``), bubbles the records up as nested renders
    are consumed (``on_render_context_merge``), and at serialize time turns them into
    ``<script>``/``<style>``/``<link>`` tags placed into the page
    (``on_serialize``, implemented in ``emission.py``).
    """

    name = "dependencies"
    render_cache_mode = "payload"
    render_cache_version = 1

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

    def on_component_unregistered(self, ctx: OnComponentUnregisteredContext) -> None:
        # A PascalCase class may retain another registry alias. Keep its
        # derived assets until the class's final name is removed.
        if ctx.citry._has_component_class(ctx.component_class):
            return
        _clear_cached_dependencies(ctx.component_class)
        evict_component_script_keys(ctx.citry, ctx.component_class.class_id)

    def on_files_reset(self, ctx: OnFilesResetContext) -> None:
        # The captured declaration is class-definition data and stays; only
        # the merged result (which embeds resolved file paths) and the cached
        # processed scripts are dropped.
        _clear_cached_dependencies(ctx.component_class)
        evict_component_scripts(ctx.component_class)

    # ----- Collection during render (docs/design/dependencies.md section 6) -----

    def on_component_data(self, ctx: OnComponentDataContext) -> None:
        comp_cls = type(ctx.component)
        # Record only components that actually carry assets; <c-provide> and
        # plain markup-only components add nothing to emit. The accessors are
        # cached per class, so this costs a few attribute reads per render.
        if (
            not has_component_asset("js", comp_cls)
            and not has_component_asset("css", comp_cls)
            and not comp_cls.get_dependencies()
        ):
            return
        # Keep the class's processed scripts cached, in case they were evicted
        # (also what the script-serving endpoint in routes.py reads).
        cache_component_js(comp_cls)
        cache_component_css(comp_cls)
        # Per-render variables: hash each data method's result and cache the
        # generated script/stylesheet under the hash, so identical data is
        # delivered to the browser once (docs/design/dependencies.md
        # section 5).
        js_capture = _cache_component_js_vars_capture(comp_cls, ctx.js_data) if ctx.js_data else None
        css_capture = _cache_component_css_vars_capture(comp_cls, ctx.css_data) if ctx.css_data else None
        js_vars_hash = None if js_capture is None else js_capture.variables_hash
        css_vars_hash = None if css_capture is None else css_capture.variables_hash
        if css_vars_hash is not None:
            # The instance's root elements get the matching marker attribute,
            # which the generated stylesheet scopes its custom properties to.
            ctx.context._add_root_markers([f"data-ccss-{css_vars_hash}"])
        # Records are held as an insertion-ordered set (dict keyed by the
        # record, value unused): a record bubbles up through every ancestor, so
        # without dedup-on-insert a deep page accumulates one copy of each
        # record per ancestor level (the merge below would be O(n*depth)).
        records: dict[DependencyRecord, _DependencyCacheCapture] = ctx.context.extra.setdefault(EXTRA_KEY, {})
        records[
            DependencyRecord(
                class_id=comp_cls.class_id,
                component_id=ctx.component.id,
                js_vars_hash=js_vars_hash,
                css_vars_hash=css_vars_hash,
                component_class=comp_cls,
            )
        ] = _DependencyCacheCapture(js=js_capture, css=css_capture)

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        # A nested render was consumed by an enclosing one: its records join the
        # enclosing set, preserving first-seen order (the parent's own record
        # was added before its children rendered, so the order approximates
        # document order). The set makes the merge idempotent, so a render
        # consumed by several enclosing renders never multiplies its records.
        child_records = ctx.child_context.extra.get(EXTRA_KEY)
        if child_records:
            parent_records: dict[DependencyRecord, _DependencyCacheCapture] = ctx.parent_context.extra.setdefault(
                EXTRA_KEY, {}
            )
            parent_records.update(child_records)

    def export_render_cache(self, ctx: OnRenderCacheExportContext) -> dict[str, object]:
        """Detach selected dependency records and exact variable-script values."""
        local_by_id = {instance.render_id: instance.index for instance in ctx.instances}
        records: dict[DependencyRecord, _DependencyCacheCapture] = ctx.root_context.extra.get(EXTRA_KEY, {})
        return {
            "records": [
                {
                    "class_id": record.class_id,
                    "css": _capture_to_wire(capture.css),
                    "instance": local_by_id[record.component_id],
                    "js": _capture_to_wire(capture.js),
                }
                for record, capture in records.items()
                if record.component_id in ctx.selected_render_ids
            ]
        }

    def stage_render_cache(self, ctx: OnRenderCacheStageContext) -> StagedRenderCacheContribution:
        """Validate dependency payloads and prepare exact cache repairs."""
        if set(ctx.payload) != {"records"} or type(ctx.payload["records"]) is not list:
            from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

            raise CacheArtifactError("Dependencies render-cache payload has an invalid field set.")
        from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

        records: dict[DependencyRecord, _DependencyCacheCapture] = {}
        writes: list[RenderCacheWrite] = []
        markers: list[tuple[int, tuple[str, ...]]] = []
        seen_instances: set[int] = set()
        for index, raw in enumerate(ctx.payload["records"]):
            path = f"dependencies.records[{index}]"
            if type(raw) is not dict or set(raw) != {"class_id", "css", "instance", "js"}:
                raise CacheArtifactError(f"{path} has an invalid field set.")
            item = raw
            instance = item["instance"]
            if type(instance) is not int or not 0 <= instance < len(ctx.instance_ids):
                raise CacheArtifactError(f"{path}.instance refers to a missing artifact instance.")
            if instance in seen_instances:
                raise CacheArtifactError(f"{path}.instance is duplicated.")
            seen_instances.add(instance)
            class_id = item["class_id"]
            if type(class_id) is not str or not class_id or class_id != ctx.instance_class_ids[instance]:
                raise CacheArtifactError(f"{path}.class_id does not match its artifact instance.")
            try:
                component_class = ctx.citry.get_component_by_class_id(class_id)
            except KeyError as err:
                raise CacheArtifactError(f"{path}.class_id has no current registered component.") from err
            js_capture = _capture_from_wire(item["js"], path=f"{path}.js", class_id=class_id, kind="js")
            css_capture = _capture_from_wire(item["css"], path=f"{path}.css", class_id=class_id, kind="css")
            if js_capture is not None and not uses_component(component_class):
                raise CacheArtifactError(f"{path}.js is incompatible with the current component JS.")
            if css_capture is not None and not has_component_asset("css", component_class):
                raise CacheArtifactError(f"{path}.css is incompatible with the current component CSS.")
            if js_capture is not None:
                writes.append(
                    RenderCacheWrite(
                        key=gen_cache_key(class_id, "js", js_capture.variables_hash),
                        value=js_capture.cache_value,
                    )
                )
            if css_capture is not None:
                writes.append(
                    RenderCacheWrite(
                        key=gen_cache_key(class_id, "css", css_capture.variables_hash),
                        value=css_capture.cache_value,
                    )
                )
                markers.append((instance, (f"data-ccss-{css_capture.variables_hash}",)))
            record = DependencyRecord(
                class_id=class_id,
                component_id=ctx.instance_ids[instance],
                js_vars_hash=None if js_capture is None else js_capture.variables_hash,
                css_vars_hash=None if css_capture is None else css_capture.variables_hash,
                component_class=component_class,
            )
            records[record] = _DependencyCacheCapture(js=js_capture, css=css_capture)
        return StagedRenderCacheContribution(
            extra_items=((EXTRA_KEY, records),) if records else (),
            cache_writes=tuple(writes),
            frame_markers=tuple(markers),
        )

    # ----- Emission at serialize (docs/design/dependencies.md section 7) -----

    def on_serialize(self, ctx: OnSerializeContext) -> str | None:
        return emit_dependencies(ctx.citry, ctx)

    # ----- HTTP routes (docs/design/dependencies.md section 9) -----

    @property
    def urls(self) -> list[URLRoute]:
        # Imported here, not at module load: routes.py imports back into this
        # package, and routing is only needed when a web integration asks.
        from citry.ext.dependencies.routes import dependency_routes  # noqa: PLC0415

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
        cached = _cached_dependencies(comp_cls)
        if cached is not None:
            return cached

        merged = self._resolve_branch(comp_cls, comp_cls, set())
        type.__setattr__(comp_cls, _DEPENDENCIES_CACHE_ATTR, merged)
        return merged

    def _resolve_branch(
        self,
        branch: type,
        bound_component: type[Component],
        visiting: set[type],
    ) -> CitryDependencies:
        """Resolve one component or plain definition branch for a bound component."""
        # Imported here, not at module load: this module is imported while the
        # default Citry instance is being constructed (the built-in extension
        # spec), which happens before component.py can be imported.
        from citry.component import Component  # noqa: PLC0415

        if branch in visiting:
            msg = f"Component {bound_component.__name__}: cyclic Dependencies.extend graph at {branch.__name__}."
            raise ValueError(msg)

        if branch is not bound_component and isinstance(branch, type) and issubclass(branch, Component):
            if branch is Component:
                return CitryDependencies()
            if branch.citry is not self.citry:
                return get_dependencies(branch)
            cached = _cached_dependencies(branch)
            if cached is not None:
                return cached
            return self._resolve_branch(branch, branch, visiting)

        record = next(
            (
                item
                for item in _get_nested_class_declarations(branch, "Dependencies")
                if item.declaring_class is branch
            ),
            None,
        )
        declared = record is not None
        declaration = None if record is None else record.value
        if declaration is not None and not isinstance(declaration, type):
            msg = (
                f"Component {bound_component.__name__}: 'Dependencies' must be a class"
                f" (or None to reset inherited dependencies); got {declaration!r}."
            )
            raise ValueError(msg)

        own = self._build_own(bound_component, branch, declaration)

        # `Dependencies = None` means: no inheritance either.
        if declared and declaration is None:
            bases: tuple[type, ...] = ()
        else:
            extend = getattr(declaration, "extend", True) if declaration is not None else True
            if extend is True:
                bases = branch.__bases__
            elif extend is False:
                bases = ()
            else:
                bases = tuple(extend)

        visiting.add(branch)
        try:
            merged = CitryDependencies()
            for base in bases:
                if not isinstance(base, type) or base is object:
                    continue
                merged = merged + self._resolve_branch(base, bound_component, visiting)
            merged = merged + own
        finally:
            visiting.remove(branch)

        if isinstance(branch, type) and issubclass(branch, Component) and branch is not Component:
            type.__setattr__(branch, _DEPENDENCIES_CACHE_ATTR, merged)
        return merged

    def _build_own(
        self,
        comp_cls: type[Component],
        source_class: type,
        declaration: type | None,
    ) -> CitryDependencies:
        """Normalize and resolve the entries declared on this class's own ``Dependencies``."""
        if declaration is None:
            return CitryDependencies()

        js_entries, css_entries = _normalize_input(comp_cls, declaration)

        js = dedupe(entry for raw in js_entries for entry in _resolve_entry(raw, comp_cls, source_class))
        css = {
            media_type: dedupe(entry for raw in raw_entries for entry in _resolve_entry(raw, comp_cls, source_class))
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
                if _is_single_entry(value):
                    css_entries[media_type] = [value]
                elif isinstance(value, (list, tuple)):
                    css_entries[media_type] = list(value)
                else:
                    msg = (
                        f"Dependencies.css[{media_type!r}] must be a path, a list of paths, or a callable;"
                        f" got {type(value)} on {comp_cls.__name__}"
                    )
                    raise ValueError(msg)
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
    # bytes is one (invalid) entry, not a sequence: without this, a bytes
    # value in a dict would be expanded into integer bytes and the error
    # would name a meaningless int instead of the offending value. Kept
    # single so _resolve_entry rejects it naming the component and entry.
    return isinstance(value, (str, bytes, bytearray, Path, os.PathLike))


def _resolve_entry(entry: Any, comp_cls: type[Component], source_class: type) -> list[Any]:
    """
    Resolve one ``Dependencies`` entry to zero or more output entries.

    - Callables are invoked (lazily, here, not at class definition).
    - ``Script``/``Style`` objects pass through unchanged: they already say
      exactly what tag to emit (docs/design/dependencies.md section 3).
    - Pre-rendered tags (objects with ``__html__``) pass through unchanged.
    - URL strings pass through unchanged.
    - Globs expand (sorted, for deterministic output) relative to the module
      dir, then relative to the Citry dirs. Absolute ``PathLike`` globs expand
      from their absolute location.
    - Plain paths resolve through the standard chain to an absolute ``Path``
      and are registered in the file index. ``PathLike`` always means local
      filesystem input and raises when unresolved. An unresolvable string is
      kept as-is because it may be a server static route.
    """
    if callable(entry):
        entry = entry()

    if isinstance(entry, Dependency):
        return [entry]

    if isinstance(entry, HasHtml) and not isinstance(entry, (str, Path)):
        return [entry]

    filesystem_entry = Path(entry) if isinstance(entry, (Path, os.PathLike)) else None
    if filesystem_entry is not None:
        entry_text = filesystem_entry.as_posix()
    elif isinstance(entry, str):
        entry_text = entry
    else:
        msg = (
            f"Unknown Dependencies entry {entry!r} of type {type(entry)} on {comp_cls.__name__}."
            f" Must be a str, Path, pre-rendered tag (object with __html__),"
            f" or a callable returning one of those."
        )
        raise TypeError(msg)

    # Pre-rendered markup that is also a str subclass (e.g. markupsafe.Markup).
    if isinstance(entry, HasHtml):
        return [entry]

    # Only strings can denote URLs. A PathLike value always means filesystem
    # input, including an absolute path whose POSIX form starts with a slash.
    if filesystem_entry is None and entry_text.startswith(("http://", "https://", "://", "/")):
        return [entry_text]

    citry_instance = comp_cls.citry

    # Resolve globs relative to the module dir, then relative to the Citry dirs.
    if is_glob(entry_text):
        if filesystem_entry is not None and filesystem_entry.is_absolute():
            glob_root = Path(filesystem_entry.anchor)
            pattern = filesystem_entry.relative_to(glob_root).as_posix()
            matches = sorted(glob_root.glob(pattern))
            resolved = [match.resolve() for match in matches if match.is_file()]
            if resolved:
                for resolved_path in resolved:
                    citry_instance._register_component_file(resolved_path, comp_cls)
                return list(resolved)
        else:
            search_dirs: list[Path] = []
            comp_module_dir = module_dir(cast("type[Component]", source_class))
            if comp_module_dir is not None:
                search_dirs.append(comp_module_dir)
            search_dirs.extend(citry_instance.settings.dirs)
            for base_dir in search_dirs:
                matches = sorted(base_dir.glob(entry_text))
                if matches:
                    resolved = [match.resolve() for match in matches if match.is_file()]
                    if resolved:
                        for resolved_path in resolved:
                            citry_instance._register_component_file(resolved_path, comp_cls)
                        return list(resolved)
            if filesystem_entry is None:
                return [entry_text]

    try:
        path = resolve_asset_file(
            filesystem_entry if filesystem_entry is not None else entry_text,
            cast("type[Component]", source_class),
            search_dirs=comp_cls.citry.settings.dirs,
        )
    except FileNotFoundError:
        if filesystem_entry is not None:
            raise
        return [entry_text]
    citry_instance._register_component_file(path, comp_cls)
    return [path]


def _capture_to_wire(capture: _VariablesScriptCapture | None) -> dict[str, str] | None:
    if capture is None:
        return None
    return {
        "hash": capture.variables_hash,
        "source": capture.source_json,
        "value": capture.cache_value,
    }


def _capture_from_wire(
    value: object,
    *,
    path: str,
    class_id: str,
    kind: str,
) -> _VariablesScriptCapture | None:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if value is None:
        return None
    if type(value) is not dict or set(value) != {"hash", "source", "value"}:
        raise CacheArtifactError(f"{path} has an invalid field set.")
    raw = cast("dict[str, object]", value)
    if any(type(raw[field]) is not str for field in ("hash", "source", "value")):
        raise CacheArtifactError(f"{path} fields must be exact strings.")
    source = cast("str", raw["source"])
    try:
        rebuilt = _js_vars_capture(class_id, source) if kind == "js" else _css_vars_capture(class_id, source)
    except (TypeError, ValueError) as err:
        raise CacheArtifactError(f"{path}.source is invalid: {err}") from err
    if rebuilt.variables_hash != raw["hash"] or rebuilt.cache_value != raw["value"]:
        raise CacheArtifactError(f"{path} does not match its canonical source value.")
    return rebuilt
