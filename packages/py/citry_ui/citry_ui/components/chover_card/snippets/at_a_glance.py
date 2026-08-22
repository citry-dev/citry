import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardAtAGlance(Component):
    template = """
      <p>Meet
        <c-CHoverCard>
          <c-fill name="activator" data="{ activator_attrs }">
            <a href="#maya" c-bind="activator_attrs">Maya Chen</a>
          </c-fill>
          <c-fill name="default">
            <c-CCol gap="sm">
              <c-CAvatar>MC</c-CAvatar>
              <strong>Maya Chen</strong>
              <span>Field researcher · 18 shared observations</span>
            </c-CCol>
          </c-fill>
        </c-CHoverCard>
      </p>
    """


preview = HoverCardAtAGlance()
preview  # noqa: B018
