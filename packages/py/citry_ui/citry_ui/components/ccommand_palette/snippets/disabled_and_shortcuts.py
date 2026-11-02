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
                    shortcut="Alt Shift D",
                    disabled=True,
                ),
                CCommandPaletteCommand(value="view-logs", label="View logs", shortcut="Alt Shift V"),
                CCommandPaletteCommand(
                    value="delete-environment",
                    label="Delete environment",
                    shortcut="Alt Shift X",
                    intent="danger",
                ),
            )
        }

    template = """
      <section
        class="command-palette-disabled"
        dir="rtl"
      >
        <h2>Deployment commands</h2>
        <div role="group" aria-label="Palette settings">
          <label><input type="checkbox" v-model="disabled" /> Disable palette</label>
          <label><input type="checkbox" v-model="loop" /> Loop navigation</label>
        </div>
        <c-CCommandPalette
          label="Deployment commands"
          c-entries="commands"
          size="lg"
          :open="open"
          :disabled="disabled"
          :loop="loop"
          :onOpenChange="(value)=>open=value"
          :onAction="(value)=>last=value"
        />
        <output aria-live="polite">Action: <span v-text="last">none</span></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open:true,disabled:false,loop:true,last:'none',
            // Alt+Shift+D is left out on purpose: "Deploy production" is
            // disabled, so its hint must not run anything.
            shortcuts:{V:'view-logs',X:'delete-environment'}
          };
        },
        methods: {
          // The palette shows the hints but never listens for the keys,
          // so the page handles them and records the same action as
          // choosing each command. Few browsers use Alt+Shift+letter.
          // On macOS, Option+Shift types a character such as Ø, so the
          // code falls back to the key's position. In the search box
          // this also stops macOS Option+Shift from typing that
          // character, so an application should pick keys its users do
          // not need to type there.
          handleShortcut(event) {
            const target = event.target;
            const letter = /^[a-z]$/i.test(event.key)
              ? event.key.toUpperCase()
              : event.code.replace(/^Key/, '');
            const value = this.shortcuts[letter];
            // Leave text fields alone (input, textarea, select and
            // contenteditable), except a combobox such as the palette's
            // search box, which has focus whenever the hints are on
            // screen. A checkbox takes no typing and keeps focus after a
            // click, so the keys still work while one is focused.
            const typing = target.matches(
              'textarea, select, input:not([type=checkbox])'
            ) || target.isContentEditable;
            if (
              !value
              // A disabled palette's commands are unavailable, so their
              // keys do nothing too.
              || this.disabled
              || !event.altKey || !event.shiftKey
              || event.ctrlKey || event.metaKey
              || event.isComposing
              || (typing && target.getAttribute('role') !== 'combobox')
            ) return;
            event.preventDefault();
            this.last = value;
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
