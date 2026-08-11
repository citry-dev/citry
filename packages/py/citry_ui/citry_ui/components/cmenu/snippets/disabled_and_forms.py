import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuDisabledAndForms(Component):
    template = """
      <section
        class="archive-disabled-demo"
        x-data="{locked: true, submits: 0}"
      >
        <c-CButton size="sm" @click="locked = !locked">
          Toggle archive seal
        </c-CButton>
        <form @submit.prevent="submits += 1">
          <fieldset :disabled="locked">
            <legend>Archive desk</legend>
            <c-CMenu>
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Desk commands</c-CButton>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="catalog">Catalog folio</c-CMenuItem>
                <c-CMenuItem value="sealed" disabled>Break royal seal</c-CMenuItem>
              </c-fill>
            </c-CMenu>
            <button type="submit">Submit native form</button>
          </fieldset>
        </form>
        <output x-text="`Form submits: ${submits}`">Form submits: 0</output>
      </section>
    """

    css = """
      :where(.archive-disabled-demo) {
        display: grid;
        gap: 0.75rem;
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-disabled-demo fieldset) {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }
    """


preview = MenuDisabledAndForms()

preview  # noqa: B018
