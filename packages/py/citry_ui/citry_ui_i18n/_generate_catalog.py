"""Generate Citry UI's distributable catalog from component-owned messages."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from citry.ext.i18n.packages import compile_catalog_package
from citry_ui.components import COMPONENTS

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry import LibraryComponent

_GENERATED_CATALOG = "locales/en-US/citry-ui.ftl"


def render_component_catalog(components: Iterable[type[LibraryComponent]]) -> str:
    """Collect direct ``Component.messages`` declarations in catalog order."""
    blocks = ["### Generated from Citry UI Component.messages declarations; do not edit by hand."]
    for component in components:
        source = component.__dict__.get("messages")
        if source is None:
            continue
        if type(source) is not str:
            raise TypeError(f"{component.__qualname__}.messages must be an exact string or None.")
        normalized = dedent(source).strip()
        if not normalized:
            raise ValueError(f"{component.__qualname__}.messages must not be empty.")
        blocks.append(f"### {component.__module__}.{component.__qualname__}\n{normalized}")
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    root = Path(__file__).parent
    catalog_path = root / _GENERATED_CATALOG
    catalog_path.write_text(render_component_catalog(COMPONENTS), encoding="utf-8")
    compile_catalog_package("citry_ui_i18n")


if __name__ == "__main__":
    main()
