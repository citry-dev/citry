"""Command Palette component family."""

from .ccommand_palette import (
    CCommandPalette,
    CCommandPaletteActionDetail,
    CCommandPaletteActionSource,
    CCommandPaletteCommand,
    CCommandPaletteEntry,
    CCommandPaletteGroup,
    CCommandPaletteIntent,
    CCommandPaletteItemSlotData,
    CCommandPaletteOpenChangeDetail,
    CCommandPaletteOpenReason,
    CCommandPaletteQueryChangeDetail,
    CCommandPaletteQueryReason,
    CCommandPaletteSeparator,
    CCommandPaletteSize,
)

__all__ = [  # noqa: RUF022 - ratified public order
    "CCommandPalette",
    "CCommandPaletteCommand",
    "CCommandPaletteGroup",
    "CCommandPaletteSeparator",
    "CCommandPaletteEntry",
    "CCommandPaletteIntent",
    "CCommandPaletteSize",
    "CCommandPaletteActionSource",
    "CCommandPaletteActionDetail",
    "CCommandPaletteOpenReason",
    "CCommandPaletteOpenChangeDetail",
    "CCommandPaletteQueryReason",
    "CCommandPaletteQueryChangeDetail",
    "CCommandPaletteItemSlotData",
]
