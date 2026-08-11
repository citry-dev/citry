import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarVariants(Component):
    template = """
      <c-CStack gap="md">
        <c-CToolbar
          c-for="variant, size in [('plain', 'sm'), ('soft', 'md'), ('outline', 'lg')]"
          c-label="variant + ' ' + size + ' tools'"
          c-variant="variant"
          c-size="size"
        >
          <c-CButton>Cut</c-CButton>
          <c-CButton>Copy</c-CButton>
          <c-CButton>Paste</c-CButton>
        </c-CToolbar>
      </c-CStack>
    """


preview = ToolbarVariants()

preview  # noqa: B018
