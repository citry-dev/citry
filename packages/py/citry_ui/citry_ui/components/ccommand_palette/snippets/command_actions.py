from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class CommandActions(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="copy-id",
                    label="Copy ID",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(
                    value="toggle-sidebar",
                    label="Toggle sidebar",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(
                    value="delete-draft",
                    label="Delete draft",
                    intent="danger",
                ),
            )
        }

    template = """
      <section
        class="command-palette-actions"
        x-data="{open:true,events:[],throwNext:false,moveFocus:false}"
      >
        <h2>Action transaction</h2>
        <div role="group" aria-label="Action behavior">
          <label><input type="checkbox" x-model="throwNext" /> Throw in next action</label>
          <label><input type="checkbox" x-model="moveFocus" /> Move owner focus</label>
        </div>
        <button id="command-action-focus-target" type="button">Owner focus target</button>
        <c-CCommandPalette
          label="Draft commands"
          c-entries="commands"
          $c-props="{
            open,
            onOpenChange:(value,detail)=>{
              events.push(`open:${value}:${detail.reason}`);
              open=value;
            },
            onQueryChange:(value,detail)=>events.push(`query:${value}:${detail.reason}`),
            onAction:(value,detail)=>{
              events.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);
              if (moveFocus) document.getElementById('command-action-focus-target').focus();
              if (throwNext) { throwNext=false; throw new Error('Application action failed'); }
            },
          }"
        />
        <output aria-live="polite" x-text="events.slice(-4).join(' | ') || 'No actions yet'">
          No actions yet
        </output>
      </section>
    """

    css = """
      :where(.command-palette-actions) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-actions h2) { margin: 0; }
      :where(.command-palette-actions [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = CommandActions()

preview  # noqa: B018
