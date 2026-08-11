import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagCustomization(Component):
    css = """
      :where(.forest-tags) {
        --cui-tag-selected-background: #176b4d;
        --cui-tag-selected-foreground: #fff;
        --cui-tag-radius: 0.45rem;
      }
    """
    template = """
      <c-CTagGroup label="Forest filters" class_="forest-tags" selection_mode="multiple" c-value="['fern']">
        <c-CTag value="fern">Fern</c-CTag>
        <c-CTag value="moss">Moss</c-CTag>
        <c-CTag value="river">River</c-CTag>
      </c-CTagGroup>
    """


preview = TagCustomization()
preview  # noqa: B018
