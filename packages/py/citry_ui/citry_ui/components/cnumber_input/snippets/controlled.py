from citry import Component


class ControlledNumberInput(Component):
    template = """
      <section class="number-input-example-stack">
        <c-CNumberInput
          c-input_attrs="{'aria-label':'Controlled quantity'}"
          :value="value" :onValueChange="(next,detail)=>{value=next;last=`${detail.source}: ${next}`}"
        />
        <output v-text="`Canonical value: ${value}; ${last}`">Canonical value: 2</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            value:'2',last:'No request yet'
          };
        },
      });
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = ControlledNumberInput()
preview  # noqa: B018
