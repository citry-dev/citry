import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarNavigation(Component):
    template = """
      <c-CSidebar tag="nav" label="Project navigation" c-collapsed="True">
        <c-fill name="header"><span data-citry-sidebar-expanded-only><strong>Atlas</strong></span></c-fill>
        <c-fill name="default">
          <c-CList>
            <c-CListItem href="#activity" c-current="True">
              <c-fill name="start"><c-CIcon name="clock" /></c-fill>
              <c-fill name="default">Activity</c-fill>
            </c-CListItem>
            <c-CListItem href="#members">
              <c-fill name="start"><c-CIcon name="user" /></c-fill>
              <c-fill name="default">Members</c-fill>
            </c-CListItem>
            <c-CListItem href="#settings">
              <c-fill name="start"><c-CIcon name="settings" /></c-fill>
              <c-fill name="default">Settings</c-fill>
            </c-CListItem>
          </c-CList>
        </c-fill>
      </c-CSidebar>
    """


preview = SidebarNavigation()
preview  # noqa: B018
