"""
Asset loading: resolving and reading a component's template, messages, JS, and CSS.

A component declares its primary assets as class fields, in four inline/file
pairs (``template``/``template_file``, ``messages``/``messages_file``,
``js``/``js_file``, ``css``/``css_file``).
The fields are declarations and are never rewritten; the loaded values are read
through matching classmethods on ``Component``.

Resolution is lazy and cached once per class (in the class's own ``__dict__``).
File paths resolve relative to the directory of the class that declared the
file value first, then relative to each entry of the requesting component's
``Citry.settings.dirs``. Content loading fires its matching extension hook, and every resolved file
is registered in the requesting Citry instance's file-to-component index that
hot reload queries.

Secondary assets (the nested ``Dependencies`` class) are owned by the built-in
``dependencies`` extension (``citry/ext/dependencies/``), which reuses
this module's path-resolution helpers.

The full design, including what diverges from django-components and why, is in
``docs/design/asset_loading.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from citry._class_introspection import _safe_class_text, _static_class_dict, _static_class_mro
from citry._inline_assets import normalize_inline_asset
from citry.citry_template import CitryTemplate
from citry.util.logger import logger
from citry.util.misc import get_module_info

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from citry.component import Component


@runtime_checkable
class HasHtml(Protocol):
    """An object carrying a pre-rendered HTML tag (e.g. ``markupsafe.Markup``)."""

    def __html__(self) -> str: ...  # pragma: no cover - protocol


def dedupe(items: Iterable[Any]) -> tuple[Any, ...]:
    """De-duplicate by equality while preserving each first-seen object."""
    result: list[Any] = []
    seen_hashable: set[Any] = set()
    unhashable: list[Any] = []
    for item in items:
        try:
            already_seen = item in seen_hashable or item in unhashable
        except TypeError:
            # Pre-rendered dependency objects only promise ``__html__``; they
            # need not be hashable, so compare those against every prior item.
            if item in result:
                continue
            unhashable.append(item)
        else:
            if already_seen:
                continue
            seen_hashable.add(item)
        result.append(item)
    return tuple(result)


################################################
# DECLARATION LOOKUP (the inline/file pairs)
################################################

ASSET_PAIRS: tuple[tuple[str, str], ...] = (
    ("template", "template_file"),
    ("messages", "messages_file"),
    ("js", "js_file"),
    ("css", "css_file"),
)

# Class-level cache attributes. Presence in the class's own __dict__ means
# "already resolved"; the cached value may be None (a valid result). The
# template cache holds the CitryTemplate, which also carries the compiled
# form once first rendered (one object, one invalidation).
_TEMPLATE_CACHE = "_citry_template"
_MESSAGES_CACHE = "_resolved_messages"
_JS_CACHE = "_resolved_js"
_CSS_CACHE = "_resolved_css"


def validate_asset_pairs(class_name: str, attrs: Mapping[str, Any]) -> None:
    """
    Reject a class that sets both members of an inline/file pair.

    Called by ``ComponentMeta.__new__`` with the class's own attributes, so the
    error surfaces at class definition. Both members set to ``None`` is fine
    (it means "explicitly no asset").
    """
    for inline_attr, file_attr in ASSET_PAIRS:
        if attrs.get(inline_attr) is not None and attrs.get(file_attr) is not None:
            msg = (
                f"Component {class_name} received non-empty values for both {inline_attr!r}"
                f" and {file_attr!r}. Only one of the two may be set."
            )
            raise ValueError(msg)


def _find_pair_declaration(
    comp_cls: type[Component],
    inline_attr: str,
    file_attr: str,
) -> tuple[type, Any, Any]:
    """
    Find the class in the MRO that owns this asset pair.

    The pair is one inheritance unit: the first class whose own ``__dict__``
    declares *either* member wins for both, so a child that sets only
    ``template_file`` fully shadows a parent's inline ``template``. An explicit
    ``None`` declaration stops the walk too ("no asset"); a class that does not
    mention the pair is skipped. The base ``Component`` class declares both
    members as ``None``, terminating the walk with the empty case.

    Returns ``(owner, inline_value, file_value)``.
    """
    for klass in _static_class_mro(comp_cls):
        attrs = _static_class_dict(klass)
        if inline_attr in attrs or file_attr in attrs:
            inline_val = attrs.get(inline_attr)
            file_val = attrs.get(file_attr)
            if inline_val is not None and file_val is not None:
                class_name = _safe_class_text(klass, "__name__") or "Component"
                msg = (
                    f"Component {class_name} has non-empty values for both {inline_attr!r}"
                    f" and {file_attr!r}. Only one of the two may be set."
                )
                raise ValueError(msg)
            return klass, inline_val, file_val
    return comp_cls, None, None


################################################
# FILE RESOLUTION
################################################


@dataclass(frozen=True, slots=True)
class _AssetPathInspection:
    """The filesystem state observed for one asset path search."""

    resolution: Literal["resolved", "missing", "unavailable"]
    resolved_path: Path | None
    searched_paths: tuple[Path, ...]


def _inspect_asset_path(
    filepath: str | Path,
    *,
    owner_dir: Path | None,
    search_dirs: tuple[Path, ...],
) -> _AssetPathInspection:
    """Check asset candidates without reading content or changing runtime state."""
    path = Path(filepath)
    if path.is_absolute():
        candidates = (path,)
    else:
        candidates = (
            *((owner_dir / path,) if owner_dir is not None else ()),
            *(base_dir / path for base_dir in search_dirs),
        )

    if not candidates:
        return _AssetPathInspection(resolution="unavailable", resolved_path=None, searched_paths=())

    searched: list[Path] = []
    for candidate in candidates:
        if candidate.exists():
            # Preserve the loader's existing absolute-path behavior. Relative
            # winners are resolved because their search roots may contain a
            # symlink or ``..`` segment.
            resolved = candidate if path.is_absolute() else candidate.resolve()
            searched.append(resolved)
            return _AssetPathInspection(
                resolution="resolved",
                resolved_path=resolved,
                searched_paths=tuple(searched),
            )
        searched.append(candidate)
    return _AssetPathInspection(resolution="missing", resolved_path=None, searched_paths=tuple(searched))


def module_dir(comp_cls: type[Component]) -> Path | None:
    """The directory of the ``.py`` file where the class is defined, if any."""
    _module, _module_name, module_file = get_module_info(comp_cls)
    if module_file is None:
        return None
    return Path(module_file).parent


def resolve_asset_file(
    filepath: str | Path,
    comp_cls: type[Component],
    *,
    search_dirs: tuple[Path, ...] | None = None,
) -> Path:
    """
    Resolve an asset file path to an absolute ``Path``.

    Lookup order (docs/design/asset_loading.md section 5.2):

    1. An absolute path is used as-is (and must exist).
    2. Relative to the directory of ``comp_cls``'s ``.py`` file. For an
       inherited declaration, callers pass the class that declared the value.
    3. Relative to each entry of ``search_dirs`` when supplied, or
       ``comp_cls.citry.settings.dirs`` otherwise, in order.

    Raises ``FileNotFoundError`` naming every location searched.
    """
    roots = comp_cls.citry.settings.dirs if search_dirs is None else search_dirs
    inspection = _inspect_asset_path(filepath, owner_dir=module_dir(comp_cls), search_dirs=roots)
    if inspection.resolved_path is not None:
        return inspection.resolved_path

    locations = (
        ", ".join(str(location) for location in inspection.searched_paths)
        if inspection.searched_paths
        else "(no searchable locations)"
    )
    msg = (
        f"Could not find file {str(filepath)!r} for component {comp_cls.__name__}."
        f" Searched: {locations}. Set the file next to the component's .py file,"
        f" under one of Citry(dirs=...), or pass an absolute path."
    )
    raise FileNotFoundError(msg)


def _load_pair(
    comp_cls: type[Component],
    inline_attr: str,
    file_attr: str,
) -> tuple[str | None, Path | None]:
    """
    Resolve an asset pair to ``(content, filepath)``.

    Inline content has its common indentation removed and is returned with
    ``filepath=None``. A file declaration is resolved (section 5.2 chain), read with explicit utf8 encoding
    (django-components #1074), and registered in the Citry file index for hot
    reload. ``(None, None)`` when the pair declares no asset.
    """
    owner, inline_val, file_val = _find_pair_declaration(comp_cls, inline_attr, file_attr)

    if inline_val is not None:
        return normalize_inline_asset(inline_val), None

    if file_val is not None:
        path = resolve_asset_file(file_val, owner, search_dirs=comp_cls.citry.settings.dirs)
        comp_cls.citry._register_component_file(path, comp_cls)
        content = path.read_text(encoding="utf8")
        logger.debug("Loaded %s for component %s from %s", file_attr, comp_cls.__name__, path)
        return content, path

    return None, None


################################################
# PRIMARY ASSET LOADERS
################################################


def load_template(comp_cls: type[Component]) -> CitryTemplate | None:
    """
    The component's loaded template, or ``None`` for a template-less component.

    Resolves ``template`` / ``template_file`` once per class (cached on the
    class), fires ``on_template_loaded`` with the content (inline or file), and
    wraps the post-hook source in a ``CitryTemplate`` carrying its origin. The
    render pipeline later fills the struct's compiled form in place; this
    loader never does.

    Users reach this through ``Card.get_template()``.
    """
    with comp_cls.citry._template_source_lock:
        if _TEMPLATE_CACHE in comp_cls.__dict__:
            return comp_cls.__dict__[_TEMPLATE_CACHE]  # type: ignore[no-any-return]

        content, path = _load_pair(comp_cls, "template", "template_file")

        result: CitryTemplate | None
        if content is None:
            result = None
        else:
            origin = str(path) if path is not None else _inline_origin(comp_cls)
            result = CitryTemplate(source=content, origin=origin, filepath=path)
            result.source = comp_cls.citry.extensions.on_template_loaded(
                comp_cls,
                content,
                template_id=result.template_id,
                origin=origin,
                template_kind=result.kind,
            )

        setattr(comp_cls, _TEMPLATE_CACHE, result)
        return result


def load_js(comp_cls: type[Component]) -> str | None:
    """
    The component's primary JS content, or ``None``.

    Resolves ``js`` / ``js_file`` once per class (cached on the class) and
    fires ``on_js_loaded`` with the content (inline or file). Users reach this
    through ``Card.get_js()``.
    """
    return _load_asset_content(comp_cls, "js", "js_file", _JS_CACHE)


def load_messages(comp_cls: type[Component]) -> str | None:
    """The component's loaded source-locale Fluent messages, or ``None``."""
    declaration_owner, _inline_value, _file_value = _find_pair_declaration(
        comp_cls,
        "messages",
        "messages_file",
    )
    with comp_cls.citry._messages_source_lock:
        cached_source = comp_cls.citry._messages_source_cache.get(declaration_owner)
        if cached_source is not None:
            cached_content, _origin = cached_source
            if _file_value is not None:
                cached_path = resolve_asset_file(
                    _file_value,
                    declaration_owner,
                    search_dirs=comp_cls.citry.settings.dirs,
                )
                comp_cls.citry._register_component_file(cached_path, comp_cls)
            setattr(comp_cls, _MESSAGES_CACHE, cached_content)
            return cached_content

        if declaration_owner in comp_cls.citry._messages_sources_loading:
            msg = (
                f"Re-entrant messages loading for source unit {declaration_owner.__module__}::"
                f"{declaration_owner.__qualname__}."
            )
            raise RuntimeError(msg)
        comp_cls.citry._messages_sources_loading.add(declaration_owner)
        try:
            try:
                content, path = _load_pair(comp_cls, "messages", "messages_file")
                origin: str | None = None
                if content is not None:
                    origin = str(path) if path is not None else f"{_inline_origin(declaration_owner)}.messages"
                    content = comp_cls.citry.extensions.on_messages_loaded(
                        declaration_owner,
                        declaration_owner,
                        content,
                        origin,
                    )
            except Exception:
                previous = comp_cls.citry._messages_reload_fallbacks.pop(
                    declaration_owner,
                    None,
                )
                if previous is not None:
                    comp_cls.citry._messages_source_cache[declaration_owner] = previous
                    setattr(comp_cls, _MESSAGES_CACHE, previous[0])
                raise

            comp_cls.citry._messages_reload_fallbacks.pop(declaration_owner, None)
            comp_cls.citry._messages_source_cache[declaration_owner] = (content, origin)
            setattr(comp_cls, _MESSAGES_CACHE, content)
            return content
        finally:
            comp_cls.citry._messages_sources_loading.discard(declaration_owner)


def messages_declaration_owner(comp_cls: type[Component]) -> type:
    """Return the class that owns ``comp_cls``'s inherited messages pair."""
    owner, _inline_value, _file_value = _find_pair_declaration(comp_cls, "messages", "messages_file")
    return owner


def loaded_messages_source(comp_cls: type[Component]) -> tuple[type, str, str] | None:
    """Describe an already loaded messages source without running hooks again."""
    owner, _inline_value, _file_value = _find_pair_declaration(comp_cls, "messages", "messages_file")
    with comp_cls.citry._messages_source_lock:
        shared = comp_cls.citry._messages_source_cache.get(owner)
        if shared is None:
            return None
        content, origin = shared
        if content is None or origin is None:
            return None
        return owner, content, origin


def load_css(comp_cls: type[Component]) -> str | None:
    """
    The component's primary CSS content, or ``None``.

    Resolves ``css`` / ``css_file`` once per class (cached on the class) and
    fires ``on_css_loaded`` with the content (inline or file). Users reach this
    through ``Card.get_css()``.
    """
    return _load_asset_content(comp_cls, "css", "css_file", _CSS_CACHE)


def _load_asset_content(
    comp_cls: type[Component],
    inline_attr: str,
    file_attr: str,
    cache_attr: str,
) -> str | None:
    if cache_attr in comp_cls.__dict__:
        return comp_cls.__dict__[cache_attr]  # type: ignore[no-any-return]

    content, _path = _load_pair(comp_cls, inline_attr, file_attr)
    if content is not None:
        extensions = comp_cls.citry.extensions
        if inline_attr == "js":
            content = extensions.on_js_loaded(comp_cls, content)
        else:
            content = extensions.on_css_loaded(comp_cls, content)

    setattr(comp_cls, cache_attr, content)
    return content


def _inline_origin(comp_cls: type[Component]) -> str:
    """Origin string for an inline template: ``<module file>::<ClassName>``."""
    _module, module_name, module_file = get_module_info(comp_cls)
    prefix = module_file or module_name or "<unknown module>"
    return f"{prefix}::{comp_cls.__name__}"


################################################
# HOT RELOAD: RESETS
################################################


def reset_template(comp_cls: type[Component]) -> None:
    """
    Clear the class's loaded template so the next render re-reads it.

    Drops the cached ``CitryTemplate`` (one object carrying the source and the
    compiled form) and the class's cached ``Const`` optimization results
    (template work that was pre-computed for inputs marked constant; see
    citry/constness.py). The next access re-resolves the file, re-fires
    ``on_template_loaded``, and re-compiles.

    Users reach this through ``Card.reset_template()``.

    Note: a subclass that *inherits* this class's template caches its own copy;
    clear it too (file-driven invalidation via
    ``Citry.get_components_for_file`` reaches all of them).
    """
    with comp_cls.citry.extensions._render_cache_invalidation():
        with comp_cls.citry._template_source_lock:
            if _TEMPLATE_CACHE in comp_cls.__dict__:
                delattr(comp_cls, _TEMPLATE_CACHE)
            comp_cls.citry._evict_component_cache(comp_cls)
            comp_cls.citry.extensions.on_template_reset(comp_cls)


def reset_files(comp_cls: type[Component]) -> None:
    """
    Clear the class's loaded messages, JS, and CSS so the next access re-reads them.

    Fires the ``on_files_reset`` hook so extensions evict their own per-class
    state too: the built-in ``dependencies`` extension drops its merged
    ``CitryDependencies`` for this class there. Users reach this through
    ``Card.reset_files()``.
    """
    with comp_cls.citry.extensions._render_cache_invalidation():
        with comp_cls.citry._messages_source_lock:
            owner = messages_declaration_owner(comp_cls)
            previous = comp_cls.citry._messages_source_cache.pop(owner, None)
            if previous is not None:
                comp_cls.citry._messages_reload_fallbacks[owner] = previous
            for attr in (_MESSAGES_CACHE, _JS_CACHE, _CSS_CACHE):
                if attr in comp_cls.__dict__:
                    delattr(comp_cls, attr)
            # Keep source invalidation and extension state invalidation atomic
            # with respect to a concurrent first reload of this source unit.
            comp_cls.citry.extensions.on_files_reset(comp_cls)
