import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class ControlledTimePicker(Component):
    template = """
      <section x-data="{value:'09:30',open:false,last:'No request yet'}" style="display:grid;gap:.75rem;max-width:24rem">
        <c-CTimePicker min="09:00" max="11:00" $c-props="{value,open,onValueChange:(next,detail)=>{last=`${detail.source}: ${next}`;value=next},onOpenChange:(next)=>open=next}" />
        <output x-text="last">No request yet</output>
      </section>
    """


preview = ControlledTimePicker()
preview  # noqa: B018
