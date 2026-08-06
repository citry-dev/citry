"""The ``citry list`` command: list the registered components."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from citry.command import format_as_ascii_table
from citry.component_registry import _pascal_to_kebab
from citry.extension import ExtensionCommand

if TYPE_CHECKING:
    from citry.introspection import ComponentInfo


def _source_path(file: Path | None) -> str:
    """The file defining the class, relative to the working directory when inside it."""
    if file is None:
        return ""
    # Try the path as imported first, so a file reached through a symlinked
    # directory inside the project keeps its friendly project-relative
    # spelling; fall back to the physical location, then to absolute.
    for candidate in (file, file.resolve()):
        try:
            return str(candidate.relative_to(Path.cwd()))
        except ValueError:
            continue
    return str(file.resolve())


def _registered_names(info: ComponentInfo) -> str:
    """Project canonical names into the legacy table's common alias order."""
    names = [info.name, *info.aliases]
    if info.class_name is not None:
        lowered_class_name = info.class_name.lower()
        derived_kebab_name = _pascal_to_kebab(info.class_name)
        if info.name == derived_kebab_name and lowered_class_name in names:
            names.remove(lowered_class_name)
            names.insert(0, lowered_class_name)
    return ", ".join(names)


class ListCommand(ExtensionCommand):
    """List the components registered on the engine."""

    name = "list"
    help = "List the registered components."

    def handle(self, **kwargs: Any) -> None:
        # Bound by the runner; absent only if invoked outside the CLI.
        if self.citry is None:
            return
        # Catalog construction completes autodiscovery, groups aliases, and
        # includes built-ins so this remains a projection of the complete
        # registry that the legacy command displayed.
        catalog = self.citry.inspect_components(include_builtins=True)
        rows = [
            {
                "name": _registered_names(info),
                "class": info.class_name or "",
                "path": _source_path(info.python_file),
            }
            for info in catalog.components
        ]
        print(format_as_ascii_table(rows, ("name", "class", "path")))
