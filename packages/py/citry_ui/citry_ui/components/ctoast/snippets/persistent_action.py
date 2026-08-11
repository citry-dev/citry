import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PersistentToastAction(Component):
    template = """
      <section class="toast-example" x-data="{items: [], result: 'No action yet'}">
        <c-CButton @click="items = [{
          id: 'offline', title: 'Working offline', actionLabel: 'Retry',
          closeOnAction: false, durationMs: 0, intent: 'warn'
        }]">Show persistent action</c-CButton>
        <output x-text="result"></output>
        <c-CToastRegion $c-props="{
          items,
          onAction: () => result = 'Retry requested',
          onDismiss: id => items = items.filter(item => item.id !== id),
        }" />
      </section>
    """
    css = ":where(.toast-example) { display:grid; gap:.75rem; min-block-size:16rem; padding:1rem; }"


preview = PersistentToastAction()
preview  # noqa: B018
