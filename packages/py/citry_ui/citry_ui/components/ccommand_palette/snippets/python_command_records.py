from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import (
    CCommandPalette,
    CCommandPaletteCommand,
    CCommandPaletteGroup,
    CCommandPaletteSeparator,
)

citry.register_library(citry_ui)


class PythonCommandRecords(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        entries = (
            CCommandPaletteGroup(
                label="Project navigation",
                commands=(
                    CCommandPaletteCommand(value="project-overview", label="Open project overview"),
                    CCommandPaletteCommand(value="project-files", label="Browse project files"),
                ),
            ),
            CCommandPaletteSeparator(),
            CCommandPaletteGroup(
                label="Draft actions",
                commands=(
                    CCommandPaletteCommand(value="save-draft", label="Save draft", shortcut="Ctrl S"),
                    CCommandPaletteCommand(
                        value="delete-draft",
                        label="Delete draft",
                        description="Moves this draft to Trash",
                        intent="danger",
                    ),
                ),
            ),
        )
        return {
            "python_palette": CCommandPalette(
                label="Project commands",
                entries=entries,
                open=True,
            )
        }

    template = """
      <section class="command-palette-records">
        <h2>Frozen Python records</h2>
        <p>The rendered palette preserves group, separator, and command order.</p>
        {{ python_palette }}
      </section>
    """

    css = """
      :where(.command-palette-records) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-records h2, .command-palette-records p) { margin: 0; }
    """


preview = PythonCommandRecords()

preview  # noqa: B018
