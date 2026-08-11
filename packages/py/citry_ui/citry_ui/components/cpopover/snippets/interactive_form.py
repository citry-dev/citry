import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InteractivePopover(Component):
    template = """
      <section class="orbit-editor">
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Adjust orbit note
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Orbit note
          </c-fill>
          <c-fill name="description">
            Changes stay in the native Form after closing.
          </c-fill>
          <c-fill name="default">
            <form id="orbit-form">
              <label for="orbit-label">Label</label>
              <input id="orbit-label" name="label" value="Perijove pass" />
              <label for="orbit-detail">Detail</label>
              <textarea id="orbit-detail" name="detail">Closest approach before sunrise.</textarea>
            </form>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="ghost" c-attrs="close_attrs">
              Cancel
            </c-CButton>
            <c-CButton c-attrs="close_attrs">
              Keep note
            </c-CButton>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.orbit-editor) {
        min-block-size: 15rem;
        padding-block: 3rem;
      }

      :where(#orbit-form) {
        display: grid;
        gap: 0.5rem;
      }

      :where(#orbit-form input, #orbit-form textarea) {
        box-sizing: border-box;
        inline-size: 100%;
        padding: 0.5rem 0.625rem;
        border: 1px solid color-mix(in srgb, CanvasText 25%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }
    """


preview = InteractivePopover()

preview  # noqa: B018
