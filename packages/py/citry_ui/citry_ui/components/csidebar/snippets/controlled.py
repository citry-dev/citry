import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarControlled(Component):
    template = """
      <section x-data="{
        collapsed:false,
        last:'No request yet',
        change(next){this.last=`Requested ${next ? 'collapse' : 'expand'}`;this.collapsed=next},
      }">
        <p><output x-text="last">No request yet</output></p>
        <c-CSidebar
          label="Controlled navigation"
          $c-props="{collapsed,onCollapsedChange:change}"
        >
          <strong>Controlled Sidebar content</strong>
        </c-CSidebar>
      </section>
    """


preview = SidebarControlled()
preview  # noqa: B018
