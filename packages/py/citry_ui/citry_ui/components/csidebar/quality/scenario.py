"""Shared Sidebar scenario used by repository quality tools."""

from citry import Citry, Component


def sidebar_states_component(app: Citry) -> type[Component]:
    class CitryUiSidebarStates(Component):
        citry = app
        template = """
          <section
            class="citry-ui-quality-stack sidebar-quality"
            data-quality-sidebar-ready
            x-data="{collapsed:false,last:'No request'}"
          >
            <h1>Sidebar states</h1>
            <div class="sidebar-quality__grid">
              <c-CSidebar
                id="quality-sidebar"
                tag="nav"
                label="Quality navigation"
                variant="floating"
                c-sticky="True"
                c-attrs="primary_attrs"
                $c-props="{collapsed,onCollapsedChange:(next)=>{collapsed=next;last=`Collapsed ${next}`}}"
              >
                <c-fill name="header"><strong data-citry-sidebar-expanded-only>Northstar</strong></c-fill>
                <c-fill name="default">
                  <c-CList>
                    <c-CListItem href="#home" c-current="True">
                      <c-fill name="start"><c-CIcon name="home" /></c-fill>
                      <c-fill name="default">Home</c-fill>
                    </c-CListItem>
                    <c-CListItem href="#reports">
                      <c-fill name="start"><c-CIcon name="file" /></c-fill>
                      <c-fill name="default">Reports with long wrapping content</c-fill>
                    </c-CListItem>
                  </c-CList>
                </c-fill>
                <c-fill name="footer"><small>ada@example.com</small></c-fill>
              </c-CSidebar>
              <c-CSidebar
                label="Offcanvas tools"
                collapsible="offcanvas"
                c-collapsed="True"
                side="inline-end"
                size="sm"
                c-attrs="{'data-quality-states':'offcanvas inline-end touch'}"
              >
                Hidden panel starts collapsed.
              </c-CSidebar>
              <div dir="rtl" style="color-scheme:dark">
                <c-CSidebar
                  tag="nav"
                  label="RTL navigation"
                  side="inline-end"
                  collapsible="none"
                  size="lg"
                  c-attrs="{'data-quality-states':'rtl nested-dark permanent'}"
                >
                  التنقل الرئيسي
                </c-CSidebar>
              </div>
            </div>
            <output x-text="last">No request</output>
          </section>
        """
        css = """
          :where(.sidebar-quality__grid){display:flex;align-items:flex-start;gap:1rem;min-block-size:24rem}
          :where(.sidebar-quality [dir="rtl"]){background:#172033;color:#f8fafc}
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "primary_attrs": {
                    "data-quality-states": (
                        "aside nav expanded collapsed controlled uncontrolled rail plain floating sm md lg sticky "
                        "header content footer localized keyboard focus long-content"
                    )
                }
            }

    return CitryUiSidebarStates


__all__ = ["sidebar_states_component"]
