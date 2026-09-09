"""Validated declarations and presentation values for component previews."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

from citry.component import Component

if TYPE_CHECKING:
    from citry.slots import Slot


class PreviewError(ValueError):
    """A preview declaration, selection, or rendering request is invalid."""


def _text(value: object, name: str, *, empty: bool = False) -> None:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise PreviewError(f"{name} must be {'a' if empty else 'a nonempty'} string.")


@dataclass(frozen=True)
class Viewport:
    """
    Browser dimensions and pixel scale used to capture one variant.

    Args:
        width: CSS width from 1 through 8192 pixels.
        height: CSS height from 1 through 8192 pixels.
        device_scale_factor: Finite pixel scale greater than zero, at most four.

    """

    width: int = 1280
    height: int = 800
    device_scale_factor: float = 1

    def __post_init__(self) -> None:
        for name in ("width", "height"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 8192:
                raise PreviewError(f"Viewport.{name} must be an integer from 1 through 8192.")
        scale = self.device_scale_factor
        if type(scale) not in (int, float) or not math.isfinite(scale) or not 0 < scale <= 4:
            raise PreviewError("Viewport.device_scale_factor must be finite, greater than zero, and at most four.")


@dataclass(frozen=True, kw_only=True)
class Variant:
    """
    One named example with display metadata and ordinary Python inputs.

    Args:
        slug: Stable lowercase name, using letters, digits, and single hyphens.
        label: Human-readable example label.
        description: Plain-text explanation of the example.
        params: Inputs for the component or variables for its preview template.
        viewport: Optional browser dimensions overriding component defaults.

    """

    slug: str
    label: str
    description: str = ""
    params: Mapping[str, Any] = field(default_factory=dict)
    viewport: Viewport | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.slug, str)
            or len(self.slug) > 80
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.slug)
        ):
            raise PreviewError("Variant.slug must contain 1 to 80 lowercase letters, digits, and single hyphens.")
        _text(self.label, "Variant.label")
        _text(self.description, "Variant.description", empty=True)
        if not isinstance(self.params, Mapping) or any(not isinstance(key, str) for key in self.params):
            raise PreviewError("Variant.params must be a string-keyed mapping.")
        if self.viewport is not None and not isinstance(self.viewport, Viewport):
            raise PreviewError("Variant.viewport must be a Viewport or None.")
        # Copy only the mapping: arbitrary Python values remain the author's inputs.
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))


def variant(
    *,
    slug: str,
    label: str,
    description: str = "",
    params: Mapping[str, Any] | None = None,
    viewport: Viewport | None = None,
) -> Variant:
    """Declare one preview variant with metadata and component or template params."""
    return Variant(
        slug=slug, label=label, description=description, params={} if params is None else params, viewport=viewport
    )


@dataclass(frozen=True, kw_only=True)
class Layout:
    """
    Wrap preview content with one template or component class.

    Exactly one source is required. The layout receives ``preview`` and a
    named ``content`` slot. Component classes must belong to the rendering app.

    Args:
        template: Trusted inline Citry template source.
        template_file: UTF-8 template path relative to the declaring class.
        component: Component class accepting preview metadata and content.

    """

    template: str | None = None
    template_file: str | Path | None = None
    component: type[Component] | None = None

    def __post_init__(self) -> None:
        if sum(value is not None for value in (self.template, self.template_file, self.component)) != 1:
            raise PreviewError("Layout requires exactly one of template, template_file, or component.")
        if self.template is not None:
            _text(self.template, "Layout.template")
        if self.template_file is not None and (
            not isinstance(self.template_file, (str, Path)) or not str(self.template_file).strip()
        ):
            raise PreviewError("Layout.template_file must be a nonempty string or Path.")
        if self.component is not None and (
            not isinstance(self.component, type) or not issubclass(self.component, Component)
        ):
            raise PreviewError("Layout.component must be a component class.")


@dataclass(frozen=True)
class PreviewComponent:
    """Display metadata for one component, without its live class or inputs."""

    id: str
    name: str
    group: str | None


@dataclass(frozen=True)
class PreviewVariant:
    """Display metadata for one variant, without its Python params."""

    slug: str
    label: str
    description: str
    viewport: Viewport
    url: str


@dataclass(frozen=True)
class PreviewMetadata:
    """Component and variant metadata supplied to an example or variant layout."""

    component: PreviewComponent
    variant: PreviewVariant


@dataclass(frozen=True)
class PreviewItem:
    """Variant metadata paired with lazily rendered content for a page layout."""

    variant: PreviewVariant
    content: Slot


@dataclass(frozen=True)
class PreviewGroup:
    """One component's metadata and ordered preview items."""

    component: PreviewComponent
    items: tuple[PreviewItem, ...]


@dataclass(frozen=True)
class PreviewPage:
    """Ordered component groups supplied to a single-preview or gallery layout."""

    selection: Literal["variant", "component", "all"]
    components: tuple[PreviewGroup, ...]
