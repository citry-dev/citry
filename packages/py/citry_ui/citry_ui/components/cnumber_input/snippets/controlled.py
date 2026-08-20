from citry import Component


class ControlledNumberInput(Component):
    template = """
      <section x-data="{value:'2',last:'No request yet'}" class="number-input-example-stack">
        <c-CNumberInput
          c-input_attrs="{'aria-label':'Controlled quantity'}"
          $c-props="{
            value,
            onValueChange:(next,detail)=>{value=next;last=`${detail.source}: ${next}`},
          }"
        />
        <output x-text="`Canonical value: ${value}; ${last}`">Canonical value: 2</output>
      </section>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = ControlledNumberInput()
preview  # noqa: B018
