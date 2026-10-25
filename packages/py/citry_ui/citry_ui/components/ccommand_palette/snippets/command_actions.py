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
      >
        <h2>Action transaction</h2>
        <div role="group" aria-label="Action behavior">
          <label><input type="checkbox" v-model="throwNext" /> Throw in next action</label>
          <label><input type="checkbox" v-model="moveFocus" /> Move owner focus</label>
        </div>
        <button
          ref="focusTarget"
          id="command-action-focus-target"
          type="button"
        >Owner focus target</button>
        <c-CCommandPalette
          label="Draft commands"
          c-entries="commands"
          :open="open"
          :onOpenChange="logOpenChange"
          :onQueryChange="(value,detail)=>events.push(`query:${value}:${detail.reason}`)"
          :onAction="runAction"
        />
        <output aria-live="polite" v-text="events.slice(-4).join(' | ') || 'No actions yet'">
          No actions yet
        </output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open:true,events:[],throwNext:false,moveFocus:false
          };
        },
        methods: {
          logOpenChange(value, detail) {
            this.events.push(`open:${value}:${detail.reason}`);
            this.open = value;
          },
          runAction(value, detail) {
            this.events.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);
            if (this.moveFocus) this.$refs.focusTarget.focus();
            // Throw once, so the next action shows the palette recovering.
            if (this.throwNext) {
              this.throwNext = false;
              throw new Error('Application action failed');
            }
          },
        },
      });
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
