import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DrawerForm(Component):
    template = """
      <section x-data="{result:'No chart selected'}">
        <c-CDrawer $c-props="{onOpenChange:(open, detail) => {
          if (!open && detail.returnValue) result = `Selected: ${detail.returnValue}`;
        }}">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Choose a chart</c-CButton>
          </c-fill>
          <c-fill name="title">Choose a chart</c-fill>
          <c-fill name="default">
            <form method="dialog" class="drawer-chart-form">
              <button type="submit" value="altitude">Altitude chart</button>
              <button type="submit" value="intensity">Intensity chart</button>
            </form>
          </c-fill>
        </c-CDrawer>
        <output x-text="result"></output>
      </section>
    """
    css = """
      :where(.drawer-chart-form) { display:grid; gap:.75rem; }
    """


preview = DrawerForm()
preview  # noqa: B018
