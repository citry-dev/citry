# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PersistentToastAction(Component):
    template = """
      <section class="toast-example" >
        <c-CButton @click="items = [{
          id: 'offline', title: 'Working offline', actionLabel: 'Retry',
          closeOnAction: false, durationMs: 0, intent: 'warn'
        }]">Show persistent action</c-CButton>
        <output v-text="result"></output>
        <c-CToastRegion :items="items" :onAction="() => result = 'Retry requested'" :onDismiss="id => items = items.filter(item => item.id !== id)" />
      </section>
    """
    js = """
      $component({
        data() {
          return {
            items: [], result: 'No action yet'
          };
        },
      });
    """
    css = ":where(.toast-example) { display:grid; gap:.75rem; min-block-size:16rem; padding:1rem; }"


preview = PersistentToastAction()
preview  # noqa: B018
