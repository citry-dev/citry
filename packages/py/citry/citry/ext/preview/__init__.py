"""Component examples, galleries, and PNG capture served only by preview commands."""

from citry.ext.preview.commands import RenderCommand, ServeCommand
from citry.ext.preview.extension import PreviewExtension
from citry.ext.preview.types import (
    Layout,
    PreviewComponent,
    PreviewError,
    PreviewGroup,
    PreviewItem,
    PreviewMetadata,
    PreviewPage,
    PreviewVariant,
    Variant,
    Viewport,
    variant,
)

PreviewExtension.commands = [ServeCommand, RenderCommand]

__all__ = [
    "Layout",
    "PreviewComponent",
    "PreviewError",
    "PreviewExtension",
    "PreviewGroup",
    "PreviewItem",
    "PreviewMetadata",
    "PreviewPage",
    "PreviewVariant",
    "Variant",
    "Viewport",
    "variant",
]
