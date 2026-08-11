import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimedToast(Component):
    template = """
      <section class="toast-example" x-data="{items: []}">
        <c-CButton @click="items = [{id: crypto.randomUUID(), title: 'Hover or focus to pause'}]">
          Start timed Toast
        </c-CButton>
        <c-CToastRegion c-duration_ms="4000" $c-props="{
          items,
          onDismiss: id => items = items.filter(item => item.id !== id),
        }" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = TimedToast()
preview  # noqa: B018
