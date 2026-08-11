import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectForm(Component):
    template = """
      <form x-data @submit.prevent="result = Array.from(new FormData($event.target).entries())">
        <c-CField required>
          <c-fill name="label">Review status</c-fill>
          <c-fill name="default">
            <c-CSelect c-options="options" placeholder="Choose a status" name="status" />
          </c-fill>
        </c-CField>
        <c-CButton type="submit">Save</c-CButton>
        <c-CButton type="reset" variant="ghost">Reset</c-CButton>
        <output x-text="JSON.stringify(result)"></output>
      </form>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("draft", "Draft"), CSelectOption("review", "Ready for review")]}


preview = SelectForm()
preview  # noqa: B018
