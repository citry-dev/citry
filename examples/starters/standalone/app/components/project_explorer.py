from app.citry_app import citry_app
from app.data import Project
from citry import Component


class ProjectExplorer(Component):
    citry = citry_app

    class Kwargs:
        projects: tuple[Project, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "projects": kwargs.projects,
            "result_count": len(kwargs.projects),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"tipsOpen": False}

    template = """
      <section class="explorer" aria-labelledby="project-list-heading">
        <div class="explorer__toolbar">
          <div>
            <h2 id="project-list-heading">Current projects</h2>
            <p>{{ result_count }} projects rendered from Python</p>
          </div>
          <button
            class="help-button"
            type="button"
            @click="tipsOpen = !tipsOpen"
            :aria-expanded="tipsOpen.toString()"
            aria-controls="explorer-help"
          >
            <span aria-hidden="true">?</span>
            <span x-text="tipsOpen ? 'Hide explanation' : 'How this page works'">
              How this page works
            </span>
          </button>
        </div>

        <aside id="explorer-help" class="explorer__help" x-cloak x-show="tipsOpen">
          <strong>Opening this panel does not call Python.</strong>
          Alpine stores whether the panel is open in your browser, so the page
          stays interactive after Python finishes rendering it.
        </aside>

        <div class="project-grid">
          <c-for each="project in projects">
            <c-ProjectCard c-project="project" />
          </c-for>
        </div>
      </section>
    """

    css = """
      .explorer {
        display: grid;
        gap: 1.25rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--color-border-subtle);
      }

      .explorer__toolbar {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
      }

      .explorer__toolbar h2 {
        margin: 0 0 0.25rem;
        color: var(--color-text);
        font-size: 1.5rem;
        font-weight: 700;
      }

      .explorer__toolbar p {
        margin: 0;
        color: var(--color-faint);
      }

      .help-button {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        min-height: 2.6rem;
        padding: 0.45rem 0.7rem;
        border: 1px solid var(--color-border);
        border-radius: 0.375rem;
        color: var(--color-link);
        background: transparent;
        font-weight: 650;
        cursor: pointer;
      }

      .help-button:hover {
        border-color: var(--color-link);
        color: var(--color-link-hover);
        background: var(--color-link-soft);
      }

      .help-button > span:first-child {
        display: grid;
        width: 1.45rem;
        height: 1.45rem;
        place-items: center;
        border-radius: 50%;
        color: var(--color-primary-ink);
        background: var(--color-link);
        font-weight: 800;
      }

      .explorer__help {
        padding: 1rem 1.15rem;
        border: 1px solid var(--color-border);
        border-left: 0.25rem solid var(--color-link);
        border-radius: 0.5rem;
        color: var(--color-muted);
        background: var(--color-link-soft);
        line-height: 1.55;
      }

      .explorer__help strong { color: var(--color-text); }

      .project-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
      }

      @media (max-width: 42rem) {
        .explorer__toolbar { align-items: stretch; flex-direction: column; }
        .help-button { align-self: flex-start; }
      }
    """
