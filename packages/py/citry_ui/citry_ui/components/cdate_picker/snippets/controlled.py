# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDatePicker(Component):
    template = """
      <section >
        <p>Value: <strong v-text="value || 'empty'"></strong>; popup: <strong v-text="open ? 'open' : 'closed'"></strong></p>
        <c-CDatePicker
          value="2026-08-19"
          :value="value" :open="open" :onValueChange="(next,detail)=>{last=`${detail.source}: ${next}`;value=next}" :onOpenChange="(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}"
        />
        <div><button type="button" @click="value='2026-08-25'">Set August 25</button> <button type="button" @click="open=!open">Toggle popup</button></div>
        <output v-text="last">No request yet</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            value:'2026-08-19',open:false,last:'No request yet'
          };
        },
      });
    """
    css = ":where(section){display:grid;gap:.75rem;max-inline-size:28rem}:where(section p){margin:0}"


preview = ControlledDatePicker()
preview  # noqa: B018
