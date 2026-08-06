import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureDialog(Component):
    template = """
      <section
        class="dialog-config"
        x-data="{
          size: 'md',
          scroll: 'body',
          dismissible: true,
          close_on_escape: true,
          close_on_outside: true,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <p>Observation archive</p>
        <h2>Configure the Dialog</h2>
        <c-CDialog
          $c-props="{
            size,
            scroll,
            dismissible,
            closeOnEscape: close_on_escape,
            closeOnOutside: close_on_outside,
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Preview configuration
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Observation archive
          </c-fill>
          <c-fill name="description">
            Test size, scrolling, and passive dismissal.
          </c-fill>
          <c-fill name="default">
            <p>The archive currently holds 384 lunar observations.</p>
            <p>Try Escape, the backdrop, and the explicit action.</p>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Finish preview
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.dialog-config) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 52rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-config h2, .dialog-config p) {
        margin: 0;
      }

      :where(.dialog-config > p) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large"), ("full", "Full")),
    },
    {
        "name": "scroll",
        "label": "Scroll",
        "type": "select",
        "default": "body",
        "options": (("body", "Body only"), ("dialog", "Complete Dialog")),
    },
    {
        "name": "dismissible",
        "label": "Allow passive dismissal",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "close_on_escape",
        "label": "Close on Escape",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "close_on_outside",
        "label": "Close on backdrop press",
        "type": "checkbox",
        "default": True,
    },
)

preview = ConfigureDialog()

preview  # noqa: B018
