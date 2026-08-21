import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarAtAGlance(Component):
    template = """
      <div class="sidebar-layout">
        <c-CSidebar id="workspace" tag="nav" label="Workspace navigation">
          <c-fill name="header"><strong>Northstar</strong></c-fill>
          <c-fill name="default">
            <c-CList variant="surface">
              <c-CListItem href="#overview" c-current="True">
                <c-fill name="start"><c-CIcon name="home" /></c-fill>
                <c-fill name="default">Overview</c-fill>
              </c-CListItem>
              <c-CListItem href="#projects">
                <c-fill name="start"><c-CIcon name="folder" /></c-fill>
                <c-fill name="default">Projects</c-fill>
              </c-CListItem>
              <c-CListItem href="#reports">
                <c-fill name="start"><c-CIcon name="file" /></c-fill>
                <c-fill name="default">Reports</c-fill>
              </c-CListItem>
            </c-CList>
          </c-fill>
          <c-fill name="footer"><small>ada@example.com</small></c-fill>
        </c-CSidebar>
        <main><h2 id="overview">Overview</h2><p>The primary page remains ordinary application layout.</p></main>
      </div>
    """
    css = """
      :where(.sidebar-layout) {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 1.5rem;
        min-block-size: 24rem;
      }
      :where(.sidebar-layout main) { padding: 1rem; }
    """


preview = SidebarAtAGlance()
preview  # noqa: B018
