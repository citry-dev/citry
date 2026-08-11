import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagContent(Component):
    template = """
      <div style="max-inline-size: 22rem">
        <c-CTagGroup label="People">
          <c-CTag value="ava">
            <c-fill name="start"><c-CAvatar alt="Ava" size="sm">A</c-CAvatar></c-fill>
            <c-fill name="default">Ava, accessibility research</c-fill>
          </c-CTag>
          <c-CTag value="leo">
            <c-fill name="start"><c-CAvatar alt="Leo" size="sm">L</c-CAvatar></c-fill>
            <c-fill name="default">Leo, design systems</c-fill>
          </c-CTag>
        </c-CTagGroup>
      </div>
    """


preview = TagContent()
preview  # noqa: B018
