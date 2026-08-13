from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand, CCommandPaletteGroup

citry.register_library(citry_ui)


class CommandPaletteEnvironment(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteGroup(
                    label="Localized workspace administration",
                    commands=(
                        CCommandPaletteCommand(
                            value="archive-workspace",
                            label="Archive this exceptionally long localized workspace name",
                            description="Keeps a recoverable copy for organization administrators",
                        ),
                        CCommandPaletteCommand(
                            value="delete-workspace",
                            label="Delete workspace permanently",
                            description="This command cannot be undone",
                            intent="danger",
                        ),
                        CCommandPaletteCommand(
                            value="managed-workspace",
                            label="Transfer managed workspace",
                            disabled=True,
                        ),
                    ),
                ),
            )
        }

    template = """
      <section
        class="command-palette-environment"
        x-data="{open:true,size:'md',dark:false,rtl:false}"
        :class="dark ? 'command-palette-environment--dark' : ''"
        :dir="rtl ? 'rtl' : 'ltr'"
      >
        <h2>Responsive command environment</h2>
        <div role="group" aria-label="Environment controls">
          <label>
            Size
            <select x-model="size">
              <option value="sm">Small</option>
              <option value="md">Medium</option>
              <option value="lg">Large</option>
            </select>
          </label>
          <label><input type="checkbox" x-model="dark" /> Dark scheme</label>
          <label><input type="checkbox" x-model="rtl" /> RTL</label>
        </div>
        <c-CCommandPalette
          label="Localized workspace commands"
          c-entries="commands"
          c-style="{
            '--cui-command-palette-inline-size':'min(42rem, calc(100dvi - 1rem))',
            '--cui-command-palette-row-min-block-size':'3rem',
          }"
          $c-props="{
            open,
            size,
            onOpenChange:(value)=>open=value,
          }"
        />
        <p>
          Inspect sm, md, and lg at 200% and 400% zoom, narrow and wide widths,
          coarse pointer, virtual keyboard, reduced motion, forced colors, and print.
        </p>
      </section>
    """

    css = """
      :where(.command-palette-environment) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        color-scheme: light;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-environment--dark) {
        color-scheme: dark;
        background: Canvas;
      }
      :where(.command-palette-environment h2, .command-palette-environment p) { margin: 0; }
      :where(.command-palette-environment [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      @media (forced-colors: active) {
        :where(.command-palette-environment) { border: 1px solid CanvasText; }
      }
      @media print {
        :where(.command-palette-environment [role="group"]) { display: none; }
      }
    """


preview = CommandPaletteEnvironment()

preview  # noqa: B018
