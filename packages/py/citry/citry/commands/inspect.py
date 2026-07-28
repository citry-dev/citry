"""The runtime-only ``citry inspect --json`` command."""

from __future__ import annotations

from typing import Any

from citry.command import CommandArg
from citry.extension import ExtensionCommand


class InspectCommand(ExtensionCommand):
    """Emit the selected engine's versioned runtime component catalog."""

    name = "inspect"
    help = "Emit the runtime component catalog as JSON."
    arguments = (
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
        print(self.citry.inspect_components().to_json())


__all__ = ["InspectCommand"]
