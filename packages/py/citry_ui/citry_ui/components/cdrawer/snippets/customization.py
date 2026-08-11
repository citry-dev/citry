import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedDrawer(Component):
    template = """
      <section class="polar-drawer-theme">
        <c-CDrawer class_="polar-drawer" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open polar archive</c-CButton>
          </c-fill>
          <c-fill name="title">Polar archive</c-fill>
          <c-fill name="description">A cool-toned field-research adaptation.</c-fill>
          <c-fill name="default">Ice-core and aurora records from the northern station.</c-fill>
          <c-fill name="close"><span aria-hidden="true">✦</span></c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.polar-drawer-theme) { color-scheme:light dark; padding:1.5rem; }
      :where(.polar-drawer) {
        --cui-drawer-background: light-dark(#eef8fb, #102a34);
        --cui-drawer-foreground: light-dark(#17343e, #e6f7fb);
        --cui-drawer-border-color: light-dark(#76b7c7, #5ea5b6);
        --cui-drawer-radius: 1.25rem;
      }
      :where(.polar-drawer [data-citry-ui-part="title"]) { letter-spacing:.04em; }
    """


preview = CustomizedDrawer()
preview  # noqa: B018
