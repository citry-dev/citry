import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledHoverCard(Component):
    template = """
      <div >
        <c-CHoverCard :open="open" :onOpenChange="(next)=>open=next">
          <c-fill name="activator" data="{ activator_attrs }">
            <a href="#atlas" c-bind="activator_attrs">Atlas workspace</a>
          </c-fill>
          <c-fill name="default"><strong>Atlas</strong><p>12 collaborators · Active now</p></c-fill>
        </c-CHoverCard>
        <c-CButton variant="outline" @click="open=!open">Toggle preview</c-CButton>
      </div>
    """
    js = "$component({data(){return {open:false};}});"


preview = ControlledHoverCard()
preview  # noqa: B018
