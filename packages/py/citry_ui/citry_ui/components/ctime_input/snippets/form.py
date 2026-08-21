import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class TimeInputForm(Component):
    template = """
      <form x-data="{result:'Submit to inspect FormData'}" @submit.prevent="result=JSON.stringify(Object.fromEntries(new FormData($event.target)))">
        <c-CField required>
          <c-fill name="label">Delivery time</c-fill>
          <c-fill name="default"><c-CTimeInput name="delivery" value="14:30" /></c-fill>
        </c-CField>
        <c-CButton type="submit">Submit</c-CButton>
        <c-CButton type="reset" variant="outline">Reset</c-CButton>
        <output x-text="result">Submit to inspect FormData</output>
      </form>
    """


preview = TimeInputForm()
preview  # noqa: B018
