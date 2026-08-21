# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDatePicker(Component):
    template = """
      <section x-data="{value:'2026-08-19',open:false,last:'No request yet'}">
        <p>Value: <strong x-text="value || 'empty'"></strong>; popup: <strong x-text="open ? 'open' : 'closed'"></strong></p>
        <c-CDatePicker
          value="2026-08-19"
          $c-props="{value,open,onValueChange:(next,detail)=>{last=`${detail.source}: ${next}`;value=next},onOpenChange:(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}}"
        />
        <div><button type="button" @click="value='2026-08-25'">Set August 25</button> <button type="button" @click="open=!open">Toggle popup</button></div>
        <output x-text="last">No request yet</output>
      </section>
    """
    css = ":where(section){display:grid;gap:.75rem;max-inline-size:28rem}:where(section p){margin:0}"


preview = ControlledDatePicker()
preview  # noqa: B018
