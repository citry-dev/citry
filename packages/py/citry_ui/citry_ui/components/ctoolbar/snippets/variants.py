import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarVariants(Component):
    template = """
      <c-CCol gap="md">
        <c-CToolbar
          #c-key="f'{variant}-{size}'"
          c-for="variant, size in [('plain', 'sm'), ('soft', 'md'), ('outline', 'lg')]"
          c-label="variant + ' ' + size + ' tools'"
          c-variant="variant"
          c-size="size"
        >
          <c-CButton #c-key="f'{variant}-{size}-cut'">Cut</c-CButton>
          <c-CButton #c-key="f'{variant}-{size}-copy'">Copy</c-CButton>
          <c-CButton #c-key="f'{variant}-{size}-paste'">Paste</c-CButton>
        </c-CToolbar>
      </c-CCol>
    """


preview = ToolbarVariants()

preview  # noqa: B018
