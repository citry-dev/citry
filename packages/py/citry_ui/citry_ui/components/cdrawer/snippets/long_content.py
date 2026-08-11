from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LongDrawer(Component):
    template = """
      <section>
        <c-CDrawer initial_focus="title" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Read expedition log</c-CButton>
          </c-fill>
          <c-fill name="title">Seven-night aurora expedition</c-fill>
          <c-fill name="default">
            <c-for each="night in nights">
              <h3>Night {{ night }}</h3>
              <p>Cloud cover shifted before a clear interval revealed green and violet arcs.</p>
            </c-for>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Finish reading</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, range]:  # noqa: ARG002
        return {"nights": range(1, 8)}


preview = LongDrawer()
preview  # noqa: B018
