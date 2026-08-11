import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledListbox(Component):
    template = """
      <div x-data>
        <c-CListbox
          label="Review status"
          value="draft"
          $c-props="{
            value: $store.listboxExample.value,
            onValueChange: (next) => $store.listboxExample.value = next,
          }"
        >
          <c-CListboxOption value="draft">Draft</c-CListboxOption>
          <c-CListboxOption value="review">Ready for review</c-CListboxOption>
          <c-CListboxOption value="approved">Approved</c-CListboxOption>
        </c-CListbox>
        <p>Current: <strong x-text="$store.listboxExample.value"></strong></p>
      </div>
    """
    js = """
      Alpine.store('listboxExample', {value: 'draft'});
    """


preview = ControlledListbox()
preview  # noqa: B018
