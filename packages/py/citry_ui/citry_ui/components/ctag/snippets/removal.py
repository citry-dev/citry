import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagRemoval(Component):
    template = """
      <div x-data="{last: 'None'}" class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Project topics"
          removable
          $c-props="{onRemove: (values) => last = values.join(', ')}"
        >
          <c-CTag value="Design">Design</c-CTag>
          <c-CTag value="Research">Research</c-CTag>
          <c-CTag value="Delivery">Delivery</c-CTag>
        </c-CTagGroup>
        <output x-text="`Requested removal: ${last}`"></output>
      </div>
    """


preview = TagRemoval()
preview  # noqa: B018
