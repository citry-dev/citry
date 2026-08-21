# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDateRange(Component):
    template = """
      <section x-data="{value:{start:'2026-08-19',end:'2026-08-23'},open:false,last:'No request yet'}">
        <p>Range: <strong x-text="value ? `${value.start} through ${value.end}` : 'empty'"></strong>; popup: <strong x-text="open ? 'open' : 'closed'"></strong></p>
        <c-CDateRange start="2026-08-19" end="2026-08-23" $c-props="{value,open,onValueChange:(next,detail)=>{last=`${detail.source}: ${JSON.stringify(next)}`;value=next},onOpenChange:(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}}" />
        <div><button type="button" @click="value={start:'2026-08-25',end:'2026-08-29'}">Set August 25 through 29</button> <button type="button" @click="open=!open">Toggle popup</button></div>
        <output x-text="last">No request yet</output>
      </section>
    """
    css = ":where(section){display:grid;gap:.75rem;max-inline-size:32rem}:where(section p){margin:0}"


preview = ControlledDateRange()
preview  # noqa: B018
