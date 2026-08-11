# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledHoverCard(Component):
    template = """
      <div x-data>
        <c-CHoverCard $c-props="{open:$store.hoverExample.open,onOpenChange:(next)=>$store.hoverExample.open=next}">
          <c-fill name="activator" data="{ activator_attrs }">
            <a href="#atlas" c-bind="activator_attrs">Atlas workspace</a>
          </c-fill>
          <c-fill name="default"><strong>Atlas</strong><p>12 collaborators · Active now</p></c-fill>
        </c-CHoverCard>
        <c-CButton variant="outline" @click="$store.hoverExample.open=!$store.hoverExample.open">Toggle preview</c-CButton>
      </div>
    """
    js = "Alpine.store('hoverExample',{open:false});"


preview = ControlledHoverCard()
preview  # noqa: B018
