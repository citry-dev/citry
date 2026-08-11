import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagActions(Component):
    template = """
      <div x-data="{last: 'None'}" class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Open view"
          actionable
          $c-props="{onAction: (value) => last = value}"
        >
          <c-CTag value="overview">Overview</c-CTag>
          <c-CTag value="activity">Activity</c-CTag>
          <c-CTag value="settings">Settings</c-CTag>
        </c-CTagGroup>
        <output x-text="`Last action: ${last}`"></output>
      </div>
    """


preview = TagActions()
preview  # noqa: B018
