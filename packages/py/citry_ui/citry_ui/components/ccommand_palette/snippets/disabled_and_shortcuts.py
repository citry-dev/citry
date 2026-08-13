from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class DisabledAndShortcuts(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="deploy-production",
                    label="Deploy production",
                    description="Unavailable until checks pass",
                    shortcut="Ctrl D",
                    disabled=True,
                ),
                CCommandPaletteCommand(value="view-logs", label="View logs", shortcut="Ctrl L"),
                CCommandPaletteCommand(
                    value="delete-environment",
                    label="Delete environment",
                    shortcut="Shift Delete",
                    intent="danger",
                ),
            )
        }

    template = """
      <section
        class="command-palette-disabled"
        dir="rtl"
        x-data="{open:true,disabled:false,loop:true,last:'none'}"
      >
        <h2>Deployment commands</h2>
        <div role="group" aria-label="Palette settings">
          <label><input type="checkbox" x-model="disabled" /> Disable palette</label>
          <label><input type="checkbox" x-model="loop" /> Loop navigation</label>
        </div>
        <c-CCommandPalette
          label="Deployment commands"
          c-entries="commands"
          size="lg"
          $c-props="{
            open,
            disabled,
            loop,
            onOpenChange:(value)=>open=value,
            onAction:(value)=>last=value,
          }"
        />
        <output aria-live="polite">Action: <span x-text="last">none</span></output>
      </section>
    """

    css = """
      :where(.command-palette-disabled) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-disabled h2) { margin: 0; }
      :where(.command-palette-disabled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      @media (forced-colors: active) {
        :where(.command-palette-disabled output) { border: 1px solid CanvasText; }
      }
    """


preview = DisabledAndShortcuts()

preview  # noqa: B018
