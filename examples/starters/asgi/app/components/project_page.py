from app.citry_app import citry_app
from app.data import Project
from citry import Component


class ProjectPage(Component):
    citry = citry_app

    class Kwargs:
        projects: tuple[Project, ...]
        query: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"projects": kwargs.projects, "query": kwargs.query}

    template = """
      <c-PageShell c-title="'Project Explorer · Citry'">
        <c-fill name="header">
          <section class="hero">
            <p class="eyebrow">Citry bare ASGI starter</p>
            <h1>Search project records with Citry.</h1>
            <p class="hero__intro">
              Python passes each project to a typed component. The help panel
              opens in the browser, while search sends the query back to
              Python through a Citry Event.
            </p>
          </section>
        </c-fill>
        <c-fill name="default">
          <c-ProjectExplorer c-projects="projects" c-query="query" />
        </c-fill>
      </c-PageShell>
    """
