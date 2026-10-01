from citry import Component

# ruff: noqa: E501 - Vue expression stays readable in public source


class ControlledPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack" >
        <c-CPinInput
          label="Controlled four-digit code"
          value="12"
          c-length="4"
          :value="code" :onValueChange="(next,detail)=>{code=next;last=`${detail.source}: ${next}`}" :onComplete="(next)=>last=`Complete: ${next}`"
        />
        <output v-text="last">No request yet</output>
        <c-CButton type="button" @click="code=''">Clear</c-CButton>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            code:'12',last:'No request yet'
          };
        },
      });
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledPinInput()
preview  # noqa: B018
