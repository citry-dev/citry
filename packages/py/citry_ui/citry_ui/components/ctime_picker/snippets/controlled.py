import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class ControlledTimePicker(Component):
    template = """
      <section style="display:grid;gap:.75rem;max-width:24rem">
        <c-CTimePicker min="09:00" max="11:00" :value="value" :open="open" :onValueChange="(next,detail)=>{last=`${detail.source}: ${next}`;value=next}" :onOpenChange="(next)=>open=next" />
        <output v-text="last">No request yet</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            value:'09:30',open:false,last:'No request yet'
          };
        },
      });
    """


preview = ControlledTimePicker()
preview  # noqa: B018
