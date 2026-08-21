"""Helpers for assertions against readable Citry UI asset sources."""

from __future__ import annotations

from pathlib import Path

_COMPONENT_ROOT = Path(__file__).parents[1] / "components"


def read_component_source_css(package: str) -> str:
    """Return every readable CSS source owned by one component package."""
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((_COMPONENT_ROOT / package).glob("*.source.css"))
    )
