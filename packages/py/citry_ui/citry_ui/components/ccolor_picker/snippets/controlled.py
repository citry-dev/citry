from citry import Component


class ControlledColorPicker(Component):
    template = """
      <section >
        <c-CColorPicker
          label="Controlled accent"
          :value="color"
          :open="open"
          :onValueChange="(next)=>color=next"
          :onOpenChange="(next)=>open=next"
        />
        <output v-text="color">#7f56d9</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            color:'#7f56d9',open:false
          };
        },
      });
    """


preview = ControlledColorPicker()
preview  # noqa: B018
