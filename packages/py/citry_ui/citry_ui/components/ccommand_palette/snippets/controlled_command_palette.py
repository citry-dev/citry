from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class ControlledCommandPalette(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(value="workspace-alpha", label="Switch to Alpha workspace"),
                CCommandPaletteCommand(value="workspace-bravo", label="Switch to Bravo workspace"),
                CCommandPaletteCommand(value="workspace-charlie", label="Switch to Charlie workspace"),
            )
        }

    template = """
      <section
        class="command-palette-controlled"
      >
        <h2>Switch workspace</h2>
        <div role="group" aria-label="Controlled palette settings">
          <label><input type="checkbox" v-model="acceptClose" /> Accept close</label>
          <label><input type="checkbox" v-model="acceptQuery" /> Accept query edits</label>
          <button type="button" @click="controlOpen=false">Release open control</button>
          <button type="button" @click="controlQuery=false">Release query control</button>
          <button type="button" @click="controlOpen=true;open=true">Open from owner</button>
        </div>
        <c-CCommandPalette
          label="Switch workspace"
          c-entries="commands"
          :open="controlOpen ? open : null" :query="controlQuery ? query : null" :onOpenChange="(value,detail)=>{
              requests.push(`open:${value}:${detail.reason}`);
              if (!controlOpen || value || acceptClose) open=value;
            }" :onQueryChange="(value,detail)=>{
              requests.push(`query:${value}:${detail.reason}`);
              if (!controlQuery || acceptQuery || detail.reason==='close') query=value;
            }"
        />
        <output aria-live="polite">
          Owner: <span v-text="open ? 'open' : 'closed'">open</span>;
          query: <span v-text="query || 'empty'">work</span>;
          requests: <span v-text="requests.slice(-3).join(' | ') || 'none'">none</span>
        </output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open:true,
            query:'work',
            controlOpen:true,
            controlQuery:true,
            acceptClose:false,
            acceptQuery:false,
            requests:[],
          };
        },
      });
    """

    css = """
      :where(.command-palette-controlled) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-controlled h2) { margin: 0; }
      :where(.command-palette-controlled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        align-items: center;
      }
    """


preview = ControlledCommandPalette()

preview  # noqa: B018
