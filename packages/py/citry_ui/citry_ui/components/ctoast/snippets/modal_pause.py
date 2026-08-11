import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastModalPause(Component):
    template = """
      <section class="toast-example" x-data="{items: [{id:'global', title:'Global queue waits', durationMs:0}]}">
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open modal task</c-CButton>
          </c-fill>
          <c-fill name="title">Modal-local feedback</c-fill>
          <c-fill name="default">
            <c-CAlert intent="info">Use Alert for immediate feedback inside this task.</c-CAlert>
          </c-fill>
        </c-CDialog>
        <c-CToastRegion $c-props="{items}" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastModalPause()
preview  # noqa: B018
