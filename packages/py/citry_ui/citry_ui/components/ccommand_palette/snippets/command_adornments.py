from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class CommandAdornments(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="create-release",
                    label="Create release",
                    description="Prepare notes and artifacts",
                    keywords=("publish",),
                ),
                CCommandPaletteCommand(
                    value="open-preview",
                    label="Open preview",
                    description="Inspect the latest deployment",
                    keywords=("beta",),
                ),
            )
        }

    template = """
      <section class="command-palette-adornments" x-data="{open:true,last:'none'}">
        <h2>Release commands with decoration</h2>
        <c-CCommandPalette
          label="Release commands"
          c-entries="commands"
          $c-props="{
            open,
            onOpenChange:(value)=>open=value,
            onAction:(value)=>last=value,
          }"
        >
          <c-fill
            name="item_start"
            data="{ value, label, description, keywords, shortcut, disabled, close_on_action, intent }"
          >
            <span class="command-palette-adornments__icon">◆</span>
          </c-fill>
          <c-fill
            name="item_end"
            data="{ value, label, description, keywords, shortcut, disabled, close_on_action, intent }"
          >
            <span class="command-palette-adornments__badge">Beta</span>
          </c-fill>
        </c-CCommandPalette>
        <output aria-live="polite">Action: <span x-text="last">none</span></output>
      </section>
    """

    css = """
      :where(.command-palette-adornments) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-adornments h2) { margin: 0; }
      :where(.command-palette-adornments__badge) {
        padding: 0.125rem 0.375rem;
        border: 1px solid currentColor;
        border-radius: 999px;
        font-size: 0.6875rem;
      }
      :where(.command-palette-adornments__icon) { color: light-dark(#175cd3, #84adff); }
    """


preview = CommandAdornments()

preview  # noqa: B018
