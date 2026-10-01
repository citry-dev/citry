from citry import Component
from project_explorer.citry_app import citry_app
from project_explorer.data import Project


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
            <p class="eyebrow">Citry Django starter</p>
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

    css = """
      .hero {
        display: grid;
        max-width: 45rem;
        gap: 0.75rem;
        margin-bottom: 2rem;
      }

      .eyebrow {
        margin: 0 0 0.15rem;
        color: var(--color-muted);
      }

      h1 {
        margin: 0;
        color: var(--color-text);
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        line-height: 1.3;
      }

      .hero__intro {
        max-width: 43rem;
        margin: 0;
        color: var(--color-muted);
        font-size: 1.05rem;
      }

      @media (max-width: 35rem) {
        h1 {
          font-size: 2rem;
        }
      }
    """
