from citry import Component


class NumberInputWithoutControls(Component):
    template = """
      <c-CField>
        <c-fill name="label">Keyboard stepper</c-fill>
        <c-fill name="description">Use Arrow Up/Down; adjacent controls are hidden.</c-fill>
        <c-fill name="default">
          <c-CNumberInput value="5" min="0" max="10" c-show_controls="False" />
        </c-fill>
      </c-CField>
    """


preview = NumberInputWithoutControls()
preview  # noqa: B018
