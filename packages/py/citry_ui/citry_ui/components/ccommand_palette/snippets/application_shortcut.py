from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class ApplicationShortcut(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "help_commands": (
                CCommandPaletteCommand(value="help-docs", label="Open documentation"),
                CCommandPaletteCommand(value="help-support", label="Contact support"),
            ),
            "workspace_commands": (
                CCommandPaletteCommand(value="workspace-settings", label="Open workspace settings"),
                CCommandPaletteCommand(value="workspace-members", label="Manage workspace members"),
            ),
        }

    template = """
      <section
        class="command-palette-shortcut"
      >
        <h2>Application-owned Mod+K</h2>
        <p>Focus the app shell and press Mod+K. Editable targets stay native.</p>
        <label><input type="checkbox" v-model="enabled" /> Enable app shortcut</label>
        <label>
          Shortcut target
          <select v-model="target">
            <option value="workspace">Workspace palette</option>
            <option value="help">Help palette</option>
          </select>
        </label>
        <label>Unrelated input <input type="text" value="Mod+K stays editable here" /></label>
        <div contenteditable="true" role="textbox" aria-label="Editable application note">
          Contenteditable shortcut exclusion
        </div>

        <c-CCommandPalette
          label="Workspace commands"
          c-entries="workspace_commands"
          :open="workspaceOpen" :onOpenChange="(value)=>workspaceOpen=value"
        />
        <c-CCommandPalette
          label="Help commands"
          c-entries="help_commands"
          :open="helpOpen" :onOpenChange="(value)=>helpOpen=value"
        />
        <output>Handled app shortcuts: <span v-text="opens">0</span></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            workspaceOpen:false,helpOpen:false,enabled:true,target:'workspace',opens:0
          };
        },
        methods: {
          handleShortcut(event) {
            if (
              !this.enabled
              || (!event.metaKey && !event.ctrlKey)
              || event.key.toLowerCase() !== 'k'
              || event.isComposing
              || ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)
              || event.target.isContentEditable
            ) return;
            event.preventDefault();
            this.opens++;
            if (this.target === 'workspace') this.workspaceOpen = true;
            else this.helpOpen = true;
          },
        },
        mounted() {
          window.addEventListener("keydown", this.handleShortcut);
        },
        beforeUnmount() {
          window.removeEventListener("keydown", this.handleShortcut);
        },
      });
    """

    css = """
      :where(.command-palette-shortcut) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-shortcut h2, .command-palette-shortcut p) { margin: 0; }
      :where(.command-palette-shortcut [contenteditable]) {
        min-block-size: 2.75rem;
        padding: 0.625rem;
        border: 1px solid currentColor;
      }
    """


preview = ApplicationShortcut()

preview  # noqa: B018
