"""Component configuration and selection for the command-owned preview host."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from weakref import WeakKeyDictionary

from citry.ext.preview.types import Layout, PreviewError, Variant, Viewport, _text, variant
from citry.extension import _SYNTHESIZED_CONFIG_ATTR, Extension, ExtensionConfig

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from citry.component import Component
    from citry.extension import OnComponentClassCreatedContext, OnExtensionCreatedContext
    from citry.introspection import ComponentInfo


_PRESENTATION = frozenset({"group", "viewport", "variant_layout", "page_layout"})
_FIELDS = _PRESENTATION | {"enabled", "template", "template_file", "variants"}


class PreviewConfig(ExtensionConfig):
    """Effective preview settings for one component, usable outside a render."""

    enabled: bool | None = None
    group: str | None = None
    template: str | None = None
    template_file: str | Path | None = None
    viewport = Viewport()
    variant_layout: Layout | None = None
    page_layout: Layout | None = None

    def variants(self) -> Sequence[Variant]:
        """Describe the default example when the component does not define variants."""
        info = self.component_class.citry.inspect_component(self.component_class)
        return (variant(slug="default", label=info.name),)


@dataclass(frozen=True)
class _Preview:
    component: type[Component]
    info: ComponentInfo
    config: PreviewConfig
    variants: tuple[Variant, ...]


@dataclass(frozen=True)
class Selection:
    """Command filters reused by catalog and HTML requests."""

    names: tuple[str, ...] = ()
    dirs: tuple[str, ...] = ()
    variants: tuple[str, ...] = ()
    cwd: Path = field(default_factory=Path.cwd)

    def __post_init__(self) -> None:
        for pattern in self.dirs:
            if not pattern or Path(pattern).is_absolute() or ".." in Path(pattern).parts:
                raise PreviewError("Preview directory filters must be nonempty relative paths without '..'.")


def _path_match(parts: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    if not pattern:
        return not parts
    if pattern[0] == "**":
        return _path_match(parts, pattern[1:]) or bool(parts and _path_match(parts[1:], pattern))
    return bool(parts and fnmatchcase(parts[0], pattern[0]) and _path_match(parts[1:], pattern[1:]))


def _matches_file(path: Path | None, selection: Selection) -> bool:
    if path is None:
        return False
    try:
        parts = path.resolve().relative_to(selection.cwd.resolve()).parts
    except ValueError:
        return False
    for pattern in selection.dirs:
        tokens = Path(pattern).parts
        if not any(char in pattern for char in "*?["):
            tokens = (*tokens, "**")
        if _path_match(parts, tokens):
            return True
    return False


class PreviewExtension(Extension):
    """
    Declare component previews and expose them only through CLI-owned servers.

    Install with ``Citry(extensions=[PreviewExtension])``. Components configure
    examples through a nested ``Preview`` class. Ordinary application adapters
    receive no routes from this extension.
    """

    name = "preview"
    class_name = "Preview"
    Config = PreviewConfig
    # Preview stores declarations, not state belonging to a rendered tree.
    render_cache_mode = "stateless"
    render_cache_version = 1

    def on_extension_created(self, _ctx: OnExtensionCreatedContext) -> None:
        self._cwd = Path.cwd()
        self._owners: WeakKeyDictionary[type[Component], dict[str, type]] = WeakKeyDictionary()

    def validate_config_fields(self, fields: Mapping[str, Any], *, component: type[Component] | None = None) -> None:
        allowed = _PRESENTATION if component is None else _FIELDS
        for name, value in fields.items():
            if name not in allowed:
                raise PreviewError(f"Unknown Preview field {name!r}; expected {', '.join(sorted(allowed))}.")
            if name == "enabled" and value is not None and type(value) is not bool:
                raise PreviewError("Preview.enabled must be True, False, or None.")
            if name in {"group", "template"} and value is not None:
                _text(value, f"Preview.{name}")
            if (
                name == "template_file"
                and value is not None
                and (not isinstance(value, (str, Path)) or not str(value).strip())
            ):
                raise PreviewError("Preview.template_file must be a nonempty string or Path.")
            if name == "viewport" and not isinstance(value, Viewport):
                raise PreviewError("Preview.viewport must be a Viewport.")
            if name in {"variant_layout", "page_layout"} and value is not None and not isinstance(value, Layout):
                raise PreviewError(f"Preview.{name} must be a Layout or None.")
            if name == "variants" and (
                not callable(value)
                or isinstance(value, (classmethod, staticmethod))
                or inspect.iscoroutinefunction(value)
            ):
                raise PreviewError("Preview.variants must be an instance method.")

    def on_component_class_created(self, ctx: OnComponentClassCreatedContext) -> None:
        owners: dict[str, type] = {}
        # Capture authored owners before the manager replaces the nested config.
        for declaration in ctx.nested_declarations("Preview"):
            if declaration.value is None:
                break
            if isinstance(declaration.value, type):
                for base in declaration.value.__mro__:
                    # Use the manager's own marker so defaults never count as authored content.
                    if base in self.Config.__mro__ or _SYNTHESIZED_CONFIG_ATTR in vars(base):
                        continue
                    for name in _FIELDS & vars(base).keys():
                        owners.setdefault(name, base)
        self._owners[ctx.component_class] = owners

    def file_path(self, component: type[Component] | None, field: str, path: str | Path) -> Path:
        """Resolve a file beside its declaration, retaining inherited provenance."""
        resolved = Path(path)
        if resolved.is_absolute():
            return resolved
        owner = self._owners.get(component, {}).get(field) if component is not None else None
        if owner is None:
            return self._cwd / resolved
        try:
            source = Path(inspect.getfile(owner))
        except (OSError, TypeError) as exc:
            raise PreviewError(f"Cannot locate the declaration of Preview.{field}; use an absolute path.") from exc
        if not source.is_file():
            raise PreviewError(f"Cannot locate the declaration of Preview.{field}; use an absolute path.")
        return source.resolve().parent / resolved

    def previews(self, selection: Selection | None = None) -> tuple[_Preview, ...]:
        """Resolve an ordered selection with fresh variant inputs on each call."""
        selection = selection or Selection()
        registrations = self.citry.components
        named: set[type[Component]] = set()
        for name in selection.names:
            matches = {cls for alias, cls in registrations.items() if alias.casefold() == name.casefold()}
            if not matches:
                raise PreviewError(f"Unknown preview component {name!r}.")
            named.update(matches)
        rows: list[_Preview] = []
        # Alias grouping prevents rendering one class more than once per catalog.
        for cls in dict.fromkeys(registrations.values()):
            if selection.names and cls not in named:
                continue
            info = self.citry.inspect_component(cls)
            if info.builtin:
                continue
            if selection.dirs and not _matches_file(info.python_file, selection):
                if cls in named:
                    raise PreviewError(f"Explicit component {info.name!r} is excluded by --dir.")
                continue
            config: PreviewConfig = cast("Any", cls).Preview(None)
            if config.template is not None and config.template_file is not None:
                raise PreviewError(f"{info.name}: Preview.template and template_file are mutually exclusive.")
            authored = (
                config.template is not None
                or config.template_file is not None
                or "variants" in self._owners.get(cls, {})
            )
            enabled = config.enabled if config.enabled is not None else authored
            if not enabled:
                if cls in named:
                    raise PreviewError(f"Component {info.name!r} has no enabled previews.")
                continue
            try:
                values = config.variants()
                if not isinstance(values, (list, tuple)) or any(not isinstance(item, Variant) for item in values):
                    raise PreviewError("variants() must return a list or tuple of Variant records.")
                slugs = [item.slug for item in values]
                if len(slugs) != len(set(slugs)):
                    raise PreviewError("variants() returned duplicate slugs.")
                if not values and cls in named:
                    raise PreviewError("No preview variants are available.")
                missing = set(selection.variants) - set(slugs)
                if missing:
                    raise PreviewError(f"Missing requested variants: {', '.join(sorted(missing))}.")
                selected = tuple(item for item in values if not selection.variants or item.slug in selection.variants)
                if selected:
                    rows.append(_Preview(cls, info, config, selected))
            except Exception as exc:
                raise PreviewError(f"{info.name}: {exc}") from exc
        if not rows and (selection.dirs or selection.names or selection.variants):
            raise PreviewError("No previews match the supplied selection.")
        return tuple(sorted(rows, key=lambda row: row.info.name))
