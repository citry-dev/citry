import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagSelection(Component):
    template = """
      <div class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Workspace qualities"
          selection_mode="multiple"
          :value="chosen" :onValueChange="(value) => chosen = value"
        >
          <c-CTag value="quiet">Quiet</c-CTag>
          <c-CTag value="bright">Bright</c-CTag>
          <c-CTag value="central">Central</c-CTag>
        </c-CTagGroup>
        <output v-text="chosen.join(', ')"></output>
      </div>
    """
    js = """
      $component({
        data() {
          return {
            chosen: ['quiet']
          };
        },
      });
    """


preview = TagSelection()
preview  # noqa: B018
