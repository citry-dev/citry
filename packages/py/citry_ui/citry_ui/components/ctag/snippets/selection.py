import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagSelection(Component):
    template = """
      <div x-data="{chosen: ['quiet']}" class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Workspace qualities"
          selection_mode="multiple"
          $c-props="{value: chosen, onValueChange: (value) => chosen = value}"
        >
          <c-CTag value="quiet">Quiet</c-CTag>
          <c-CTag value="bright">Bright</c-CTag>
          <c-CTag value="central">Central</c-CTag>
        </c-CTagGroup>
        <output x-text="chosen.join(', ')"></output>
      </div>
    """


preview = TagSelection()
preview  # noqa: B018
