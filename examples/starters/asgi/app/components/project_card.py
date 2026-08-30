from app.citry_app import citry_app
from app.data import Project
from citry import Component


class ProjectCard(Component):
    citry = citry_app

    class Kwargs:
        project: Project

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        project = kwargs.project
        return {
            "name": project.name,
            "summary": project.summary,
            "status": project.status,
            "language": project.language,
            "initial": project.name[0],
        }

    template = """
      <article class="project-card">
        <div class="project-card__topline">
          <span class="project-card__initial" aria-hidden="true">{{ initial }}</span>
          <span class="project-card__status">{{ status }}</span>
        </div>
        <div>
          <h3>{{ name }}</h3>
          <p>{{ summary }}</p>
        </div>
        <footer><span class="language-dot" aria-hidden="true"></span>{{ language }}</footer>
      </article>
    """

    css = """
      .project-card {
        display: grid;
        min-height: 13rem;
        gap: 1.25rem;
        align-content: space-between;
        padding: 1.2rem;
        border: 1px solid var(--color-border);
        border-radius: 0.5rem;
        background: var(--color-surface);
      }

      .project-card__topline, .project-card footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
      }
      .project-card__initial {
        display: grid;
        width: 2.4rem;
        height: 2.4rem;
        place-items: center;
        border-radius: 0.375rem;
        color: var(--color-primary-ink);
        background: var(--color-primary);
        font-weight: 750;
      }

      .project-card__status {
        padding: 0.22rem 0.5rem;
        border-radius: 999px;
        color: var(--color-accent-ink);
        background: var(--color-accent-soft);
        font-size: 0.75rem;
        font-weight: 650;
      }

      .project-card h3 {
        margin: 0 0 0.55rem;
        color: var(--color-text);
        font-size: 1.2rem;
        font-weight: 700;
      }

      .project-card p {
        margin: 0;
        color: var(--color-muted);
        line-height: 1.55;
      }

      .project-card footer {
        justify-content: flex-start;
        color: var(--color-faint);
        font-size: 0.82rem;
      }

      .language-dot {
        width: 0.55rem;
        height: 0.55rem;
        border-radius: 50%;
        background: var(--color-link);
      }
    """
