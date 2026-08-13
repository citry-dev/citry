from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class BasicCommandPalette(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="open-settings",
                    label="Open settings",
                    keywords=("preferences",),
                    shortcut="Ctrl ,",
                ),
                CCommandPaletteCommand(value="create-project", label="Create project"),
                CCommandPaletteCommand(value="invite-teammate", label="Invite teammate"),
            )
        }

    template = """
      <section
        class="command-palette-basic"
        x-data="{lastAction:'none',lastQuery:'',lastOpen:'closed'}"
      >
        <h2>Workspace commands</h2>
        <p>Search a small set of actions without leaving the current task.</p>
        <c-CCommandPalette
          label="Workspace commands"
          c-entries="commands"
          $c-props="{
            onAction:(value)=>lastAction=value,
            onQueryChange:(value)=>lastQuery=value,
            onOpenChange:(value)=>lastOpen=value ? 'open' : 'closed',
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton
              variant="solid"
              c-disabled="activator_disabled"
              c-attrs="activator_attrs"
            >
              Open command palette
            </c-CButton>
          </c-fill>
        </c-CCommandPalette>
        <output aria-live="polite">
          State: <span x-text="lastOpen">closed</span>;
          query: <span x-text="lastQuery || 'empty'">empty</span>;
          action: <span x-text="lastAction">none</span>
        </output>
      </section>
    """

    css = """
      :where(.command-palette-basic) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-basic h2, .command-palette-basic p) { margin: 0; }
    """


preview = BasicCommandPalette()

preview  # noqa: B018
