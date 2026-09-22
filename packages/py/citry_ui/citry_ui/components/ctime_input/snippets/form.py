import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimeInputForm(Component):
    template = """
      <form @submit.prevent="result=JSON.stringify(Object.fromEntries(new window.FormData($event.target)))">
        <c-CField required>
          <c-fill name="label">Delivery time</c-fill>
          <c-fill name="default"><c-CTimeInput name="delivery" value="14:30" /></c-fill>
        </c-CField>
        <c-CButton type="submit">Submit</c-CButton>
        <c-CButton type="reset" variant="outline">Reset</c-CButton>
        <output v-text="result">Submit to inspect FormData</output>
      </form>
    """
    js = """
      $component({
        data() {
          return {
            result:'Submit to inspect FormData'
          };
        },
      });
    """


preview = TimeInputForm()
preview  # noqa: B018
