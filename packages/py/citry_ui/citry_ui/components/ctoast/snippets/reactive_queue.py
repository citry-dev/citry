import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ReactiveToastQueue(Component):
    template = """
      <section class="toast-example" x-data="{notices: [], next: 1}">
        <c-CButton @click="notices = [...notices, {
          id: `note-${next}`, title: `Observation ${next++} queued`, intent: 'info'
        }]">Add notification</c-CButton>
        <c-CToastRegion $c-props="{
          items: notices,
          onDismiss: id => notices = notices.filter(item => item.id !== id),
        }" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ReactiveToastQueue()
preview  # noqa: B018
