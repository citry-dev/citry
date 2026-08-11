import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableForm(Component):
    template = """
      <form x-data @submit.prevent="result = Object.fromEntries(new FormData($event.target))">
        <c-CField required>
          <c-fill name="label">Workspace title</c-fill>
          <c-fill name="default">
            <c-CEditable value="Field notes" name="title" />
          </c-fill>
        </c-CField>
        <c-CButton type="submit">Save form</c-CButton>
        <c-CButton type="reset" variant="ghost">Reset</c-CButton>
        <output x-text="JSON.stringify(result)"></output>
      </form>
    """


preview = EditableForm()
preview  # noqa: B018
