# ruff: noqa: E501 - Alpine expression remains readable in the public example

from citry import Component


class ControlledColorPicker(Component):
    template = """
      <section x-data="{color:'#7f56d9',open:false}">
        <c-CColorPicker label="Controlled accent" $c-props="{value:color,open,onValueChange:(next)=>color=next,onOpenChange:(next)=>open=next}" />
        <output x-text="color">#7f56d9</output>
      </section>
    """


preview = ControlledColorPicker()
preview  # noqa: B018
