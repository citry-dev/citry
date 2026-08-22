import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagVariants(Component):
    template = """
      <c-CCol gap="lg">
        <c-CTagGroup
          c-for="variant in ['soft', 'solid', 'outline']"
          c-label="variant"
          c-variant="variant"
          selection_mode="single"
          value="one"
        >
          <c-CTag value="one">Selected</c-CTag><c-CTag value="two">Available</c-CTag>
        </c-CTagGroup>
        <c-CTagGroup c-for="size in ['sm', 'md', 'lg']" c-label="size" c-size="size">
          <c-CTag value="sample">Sample</c-CTag>
        </c-CTagGroup>
      </c-CCol>
    """


preview = TagVariants()
preview  # noqa: B018
