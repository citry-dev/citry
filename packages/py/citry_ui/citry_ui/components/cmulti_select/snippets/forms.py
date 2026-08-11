import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectForm(Component):
    template = """
      <form x-data @submit.prevent="result = Array.from(new FormData($event.target).entries())">
        <c-CField required>
          <c-fill name="label">Reviewers</c-fill>
          <c-fill name="default">
            <c-CMultiSelect c-options="options" placeholder="Choose reviewers" name="reviewer" />
          </c-fill>
        </c-CField>
        <c-CButton type="submit">Save</c-CButton>
        <c-CButton type="reset" variant="ghost">Reset</c-CButton>
        <output x-text="JSON.stringify(result)"></output>
      </form>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("maya", "Maya Chen"),
                CMultiSelectOption("noah", "Noah Williams"),
                CMultiSelectOption("ines", "Inês Silva"),
            ]
        }


preview = MultiSelectForm()
preview  # noqa: B018
