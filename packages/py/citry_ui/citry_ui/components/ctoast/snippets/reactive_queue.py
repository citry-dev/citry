import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ReactiveToastQueue(Component):
    template = """
      <section class="toast-example" >
        <c-CButton @click="notices = [...notices, {
          id: `note-${next}`, title: `Observation ${next++} queued`, intent: 'info'
        }]">Add notification</c-CButton>
        <c-CToastRegion :items="notices" :onDismiss="id => notices = notices.filter(item => item.id !== id)" />
      </section>
    """
    js = """
      $component({
        data() {
          return {
            notices: [], next: 1
          };
        },
      });
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ReactiveToastQueue()
preview  # noqa: B018
