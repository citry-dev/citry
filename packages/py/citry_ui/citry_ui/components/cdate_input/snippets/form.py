from citry import Component

# ruff: noqa: E501 - template expression remains readable as authored HTML


class DateInputForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="date-input-demo-stack" x-data="{result:'Submit or reset the Form'}" @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))">
        <c-CField required>
          <c-fill name="label">Departure date</c-fill>
          <c-fill name="default"><c-CDateInput name="departure" value="2026-08-22" /></c-fill>
        </c-CField>
        <c-CRow><c-CButton type="submit">Submit</c-CButton><c-CButton type="reset" variant="outline">Reset</c-CButton></c-CRow>
        <output x-text="result">Submit or reset the Form</output>
      </form>
    """
    css = ":where(.date-input-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = DateInputForm()
preview  # noqa: B018
