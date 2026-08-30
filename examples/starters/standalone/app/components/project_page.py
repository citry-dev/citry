from app.citry_app import citry_app
from app.data import Project
from citry import Component


class ProjectPage(Component):
    citry = citry_app

    class Kwargs:
        projects: tuple[Project, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"projects": kwargs.projects}

    template = """
      <c-PageShell c-title="'Project Explorer · Citry'">
        <c-fill name="header">
          <section class="hero">
            <p class="eyebrow">Citry standalone starter</p>
            <h1>Render an interactive page without a web server.</h1>
            <p class="hero__intro">
              Python renders the project cards and bundles the page's CSS and
              JavaScript. Alpine opens the help panel after you open the file.
            </p>
          </section>
        </c-fill>
        <c-fill name="default">
          <c-ProjectExplorer c-projects="projects" />
        </c-fill>
      </c-PageShell>
    """
