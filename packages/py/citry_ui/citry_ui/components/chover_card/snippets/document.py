import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DocumentHoverCard(Component):
    template = """
      <c-CHoverCard placement="top-start">
        <c-fill name="activator" data="{ activator_attrs }">
          <a href="#survey" c-bind="activator_attrs">Northern reef survey</a>
        </c-fill>
        <c-fill name="default">
          <c-CCol gap="sm">
            <strong>Northern reef survey</strong>
            <span>Updated today · 42 observations</span>
            <c-CProgress c-value="68" label="Review progress" />
          </c-CCol>
        </c-fill>
      </c-CHoverCard>
    """


preview = DocumentHoverCard()
preview  # noqa: B018
