import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagGlance(Component):
    template = """
      <c-CStack gap="lg">
        <c-CTagGroup label="Topics">
          <c-CTag value="css">CSS</c-CTag>
          <c-CTag value="html">HTML</c-CTag>
          <c-CTag value="accessibility">Accessibility</c-CTag>
        </c-CTagGroup>
        <c-CTagGroup label="Amenities" selection_mode="multiple" c-value="['wifi']">
          <c-CTag value="wifi">Wi-Fi</c-CTag>
          <c-CTag value="parking">Parking</c-CTag>
          <c-CTag value="pool">Pool</c-CTag>
        </c-CTagGroup>
      </c-CStack>
    """


preview = TagGlance()
preview  # noqa: B018
