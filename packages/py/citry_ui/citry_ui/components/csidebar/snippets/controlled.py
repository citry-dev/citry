import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarControlled(Component):
    template = """
      <section>
        <p><output v-text="last">No request yet</output></p>
        <c-CSidebar
          label="Controlled navigation"
          :collapsed="collapsed"
          :on-collapsed-change="change"
        >
          <strong>Controlled Sidebar content</strong>
        </c-CSidebar>
      </section>
    """
    js = """$component({data(){return {collapsed:false,last:'No request yet'}},methods:{
      change(next){this.last=`Requested ${next ? 'collapse' : 'expand'}`;this.collapsed=next},
    }})"""


preview = SidebarControlled()
preview  # noqa: B018
