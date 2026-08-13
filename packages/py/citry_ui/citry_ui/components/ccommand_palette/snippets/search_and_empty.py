from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class SearchAndEmpty(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="theme",
                    label="Choose theme",
                    keywords=("appearance", "color mode"),
                ),
                CCommandPaletteCommand(
                    value="light-mode",
                    label="Use light appearance",
                    keywords=("theme", "color mode"),
                ),
                CCommandPaletteCommand(
                    value="dark-mode",
                    label="Use dark appearance",
                    keywords=("theme", "color mode"),
                ),
                CCommandPaletteCommand(
                    value="managed-theme",
                    label="Use managed appearance",
                    keywords=("theme",),
                    disabled=True,
                ),
            )
        }

    template = """
      <section
        class="command-palette-search"
        x-data="{open:true,query:'theme'}"
      >
        <h2>Exact substring search</h2>
        <div role="group" aria-label="Search examples">
          <button type="button" @click="query='appearance'">Search appearance</button>
          <button type="button" @click="query='zz'">Show no match</button>
          <button type="button" @click="query='managed'">Show a disabled match</button>
          <button type="button" @click="query=''">Clear search</button>
        </div>
        <c-CCommandPalette
          label="Appearance commands"
          c-entries="commands"
          empty_label="No appearance commands match"
          $c-props="{
            open,
            query,
            onOpenChange:(value)=>open=value,
            onQueryChange:(value)=>query=value,
          }"
        />
        <output>Owner query: <span x-text="query || 'empty'">theme</span></output>
      </section>
    """

    css = """
      :where(.command-palette-search) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-search h2) { margin: 0; }
      :where(.command-palette-search [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
    """


preview = SearchAndEmpty()

preview  # noqa: B018
