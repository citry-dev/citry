from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class FormSafePalette(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(value="focus-name", label="Focus display name"),
                CCommandPaletteCommand(value="submit-profile", label="Submit profile explicitly"),
                CCommandPaletteCommand(value="managed-setting", label="Managed setting", disabled=True),
            )
        }

    template = """
      <form
        id="command-palette-profile-form"
        class="command-palette-form"
        x-data="{open:false,submits:0,actions:0,query:''}"
        @submit.prevent="submits++"
      >
        <h2>Profile Form</h2>
        <label>Display name <input id="command-profile-name" name="display_name" value="Ada" /></label>
        <c-CCommandPalette
          label="Profile commands"
          c-entries="commands"
          $c-props="{
            open,
            query,
            onOpenChange:(value)=>open=value,
            onQueryChange:(value)=>query=value,
            onAction:(value)=>{
              actions++;
              if (value==='focus-name') document.getElementById('command-profile-name').focus();
              if (value==='submit-profile') {
                document.getElementById('command-palette-profile-form').requestSubmit();
              }
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton
              type="button"
              c-disabled="activator_disabled"
              c-attrs="activator_attrs"
            >Open profile commands</c-CButton>
          </c-fill>
        </c-CCommandPalette>
        <button type="submit">Save profile</button>
        <output aria-live="polite">
          Native submits: <span x-text="submits">0</span>;
          palette actions: <span x-text="actions">0</span>
        </output>
        <p>
          IME fixture: composition Enter and Escape remain native; ordinary
          palette Enter never submits this Form unless the action callback asks.
        </p>
      </form>
    """

    css = """
      :where(.command-palette-form) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-form h2, .command-palette-form p) { margin: 0; }
      :where(.command-palette-form label) { display: grid; gap: 0.25rem; }
    """


preview = FormSafePalette()

preview  # noqa: B018
