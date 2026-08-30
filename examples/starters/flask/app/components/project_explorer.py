from app.citry_app import citry_app
from app.data import Project, find_projects
from citry import Component


class ProjectExplorer(Component):
    citry = citry_app

    class Kwargs:
        projects: tuple[Project, ...]
        query: str = ""

    class Slots:
        pass

    class State:
        query: str = ""

    class Events:
        def refresh(self, state: "ProjectExplorer.State"):
            # State came from the browser, so use it only to select trusted server records.
            return ProjectExplorer(
                projects=find_projects(state.query),
                query=state.query,
            )

    def template_data(self, kwargs: Kwargs, slots: Slots):
        result_count = len(kwargs.projects)
        return {
            "projects": kwargs.projects,
            "query": kwargs.query,
            "result_count": result_count,
            "project_label": "project" if result_count == 1 else "projects",
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"tipsOpen": False}

    template = """
      <section class="explorer" aria-labelledby="project-list-heading">
        <div class="explorer__toolbar">
          <label class="search-field">
            <span>Filter projects</span>
            <input
              type="search"
              placeholder="Try Python, active, or incident"
              autocomplete="off"
              :c-query.debounce.300ms="refresh"
            />
          </label>
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
          <strong>The help button and search take different paths.</strong>
          This panel opens entirely in your browser. After you pause typing, a
          Citry Event sends the query to Python and updates the project list.
        </aside>

        <div class="result-summary" aria-live="polite" aria-atomic="true">
          <h2 id="project-list-heading">Current projects</h2>
          <span x-cloak x-show="$loading('refresh')">Searching…</span>
          <span x-show="!$loading('refresh')">
            {{ result_count }} matching {{ project_label }}
          </span>
        </div>
        <p
          class="event-error"
          role="alert"
          x-show="$error('refresh')"
          x-text="$error('refresh')?.message || ''"
        ></p>

        <c-if cond="projects">
          <div class="project-grid">
            <c-for each="project in projects">
              <c-ProjectCard c-project="project" />
            </c-for>
          </div>
        </c-if>
        <c-else>
          <div class="empty-state">
            <strong>No projects match “{{ query }}”.</strong>
            Try a project name, status, language, or description.
          </div>
        </c-else>
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
      .search-field {
        display: grid;
        width: min(100%, 34rem);
        gap: 0.35rem;
        color: var(--color-text);
        font-size: 0.82rem;
        font-weight: 650;
      }

      .search-field input {
        min-height: 2.6rem;
        padding: 0.45rem 0.65rem;
        border: 1px solid var(--color-input-border);
        border-radius: 0.375rem;
        color: var(--color-text);
        background: var(--color-input);
        font-size: 1rem;
        font-weight: 400;
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

      .result-summary {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--color-border-subtle);
        color: var(--color-faint);
      }

      .result-summary h2 {
        margin: 0;
        color: var(--color-text);
        font-size: 1.5rem;
        font-weight: 700;
      }

      .event-error {
        min-height: 1.2rem;
        margin: 0;
        color: var(--color-danger);
      }

      .project-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
      }
      .empty-state {
        display: grid;
        gap: 0.4rem;
        padding: 2rem;
        border: 1px dashed var(--color-input-border);
        border-radius: 0.5rem;
        color: var(--color-muted);
        text-align: center;
      }

      .empty-state strong { color: var(--color-text); }

      @media (max-width: 42rem) {
        .explorer__toolbar {
          align-items: stretch;
          flex-direction: column;
        }

        .help-button { align-self: flex-start; }

        .result-summary {
          align-items: flex-start;
          flex-direction: column;
        }
      }
    """
