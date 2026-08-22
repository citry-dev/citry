from citry import Component

# ruff: noqa: E501 - template expression stays readable in public source


class PinInputForms(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="pin-input-demo-stack" x-data="{result:'Submit or reset the Form'}" @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))">
        <c-CField required>
          <c-fill name="label">One-time code</c-fill>
          <c-fill name="default"><c-CPinInput name="code" value="01" /></c-fill>
        </c-CField>
        <c-CPinInput name="issued" label="Issued code" value="246810" readonly />
        <c-CRow><c-CButton type="submit">Submit</c-CButton><c-CButton type="reset" variant="outline">Reset</c-CButton></c-CRow>
        <output x-text="result">Submit or reset the Form</output>
      </form>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = PinInputForms()
preview  # noqa: B018
