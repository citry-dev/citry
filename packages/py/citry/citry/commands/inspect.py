"""The runtime-only ``citry inspect [component] --json`` command."""

from __future__ import annotations

import sys
from typing import Any, NoReturn

from citry._component_introspection import _installed_citry_version
from citry.command import CommandArg
from citry.component_registry import NotRegistered
from citry.extension import ExtensionCommand
from citry.introspection import ComponentCatalog


class InspectCommand(ExtensionCommand):
    """Emit all components or one named component in a versioned runtime catalog."""

    name = "inspect"
    help = "Emit runtime component metadata as JSON."
    arguments = (
        CommandArg(
            "component",
            nargs="?",
            help="Optional registered component name or alias.",
        ),
        CommandArg(
            "--json",
            action="store_true",
            required=True,
            help="Emit compact ComponentCatalog JSON from the loaded runtime engine.",
        ),
    )

    def handle(self, **kwargs: Any) -> None:
        if self.citry is None:
            return
        component = kwargs.get("component")
        if component is None:
            catalog = self.citry.inspect_components()
        else:
            try:
                selected = self.citry.inspect_component(component)
            except NotRegistered as exc:
                _usage_error(str(exc))
            # Retain the established versioned envelope while using the true
            # singular inspection path, so unrelated component metadata is not
            # built just to discard it.
            catalog = ComponentCatalog(
                schema_version=1,
                citry_version=_installed_citry_version(),
                engine_id=self.citry.engine_id,
                extension_versions=(),
                components=(selected,),
            )
        print(catalog.to_json())


def _usage_error(message: str) -> NoReturn:
    """Report an invalid selector with argparse's usage-error exit status."""
    sys.stderr.write(f"citry inspect: error: {message}\n")
    raise SystemExit(2)


__all__ = ["InspectCommand"]
