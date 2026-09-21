import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledListbox(Component):
    template = """
      <div >
        <c-CListbox
          label="Review status"
          value="draft"
          :value="value" :onValueChange="(next) => value = next"
        >
          <c-CListboxOption value="draft">Draft</c-CListboxOption>
          <c-CListboxOption value="review">Ready for review</c-CListboxOption>
          <c-CListboxOption value="approved">Approved</c-CListboxOption>
        </c-CListbox>
        <p>Current: <strong v-text="value"></strong></p>
      </div>
    """
    js = """
      $component({data(){return {value:'draft'};}});
    """


preview = ControlledListbox()
preview  # noqa: B018
