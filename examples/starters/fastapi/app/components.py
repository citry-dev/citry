from citry import Component, SlotInput

from .citry_app import citry_app
from .data import Project, find_projects


class PageShell(Component):
    citry = citry_app

    class Kwargs:
        title: str

    class Slots:
        header: SlotInput
        default: SlotInput

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"title": kwargs.title}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <meta name="description" content="Search a small project catalog with Citry" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <a class="skip-link" href="#main-content">Skip to content</a>
          <header class="site-header">
            <div class="site-header__inner">
              <a class="brand" href="/">
                <span class="brand__name">Citry</span>
              </a>
              <span class="site-title">Project Explorer</span>
              <span class="mode-label">FastAPI starter</span>
            </div>
          </header>
          <main id="main-content" class="page-frame">
            <c-slot name="header" />
            <c-slot />
          </main>
          <c-js />
        </body>
      </html>
    """

    css = """
      :root {
        color-scheme: light;
        --page-gutter: 1.5rem;
        --color-page: oklch(96.5% 0.005 250);
        --color-surface: oklch(94.5% 0.006 250);
        --color-input: oklch(99% 0.002 250);
        --color-text: oklch(25% 0.01 250);
        --color-muted: oklch(40% 0.01 250);
        --color-faint: oklch(50% 0.01 250);
        --color-border: oklch(88% 0.005 250);
        --color-border-subtle: oklch(92% 0.005 250);
        --color-input-border: oklch(65% 0.01 250);
        --color-accent: oklch(55% 0.13 195);
        --color-accent-hover: oklch(48% 0.13 195);
        --color-accent-ink: oklch(46% 0.13 195);
        --color-accent-soft: oklch(55% 0.13 195 / 10%);
        --color-link: oklch(52% 0.15 245);
        --color-link-hover: oklch(48% 0.15 245);
        --color-link-soft: oklch(55% 0.15 245 / 10%);
        --color-primary: oklch(48% 0.13 195);
        --color-primary-ink: #fff;
        --color-danger: oklch(50% 0.18 25);
        --color-focus: oklch(55% 0.13 195);
        color: var(--color-muted);
        background: var(--color-page);
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
        font-synthesis: none;
      }

      @media (min-width: 48rem) {
        :root { --page-gutter: 2rem; }
      }

      @media (min-width: 80rem) {
        :root { --page-gutter: 3rem; }
      }

      *, *::before, *::after { box-sizing: border-box; }

      html {
        min-width: 20rem;
        font-size: 90%;
        scroll-padding-top: 5rem;
      }

      [x-cloak] { display: none !important; }

      body {
        min-height: 100vh;
        margin: 0;
        color: var(--color-muted);
        background: var(--color-page);
        font-size: 1rem;
        line-height: 1.65;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }

      button, input { font: inherit; }

      button:focus-visible, input:focus-visible, a:focus-visible {
        outline: 2px solid var(--color-focus);
        outline-offset: 2px;
      }

      .skip-link {
        position: fixed;
        z-index: 30;
        top: 0.75rem;
        left: 0.75rem;
        padding: 0.45rem 0.7rem;
        border-radius: 0.375rem;
        color: var(--color-primary-ink);
        background: var(--color-primary);
        font-weight: 650;
        transform: translateY(-170%);
      }

      .skip-link:focus {
        transform: translateY(0);
      }

      .site-header {
        position: fixed;
        z-index: 20;
        top: 0;
        right: 0;
        left: 0;
        height: 4rem;
        border-bottom: 1px solid var(--color-border);
        background: var(--color-page);
      }

      .site-header__inner {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        width: min(80rem, 100%);
        height: 100%;
        margin-inline: auto;
        padding-inline: var(--page-gutter);
      }

      .brand {
        display: inline-flex;
        align-items: center;
        color: var(--color-text);
        text-decoration: none;
      }

      .brand__name {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
      }

      .site-title {
        margin-left: 0.3rem;
        padding-left: 0.9rem;
        border-left: 1px solid var(--color-border);
        color: var(--color-muted);
        font-size: 0.88rem;
      }

      .mode-label {
        margin-left: auto;
        color: var(--color-accent-ink);
        font-family: ui-monospace, "Cascadia Code", Menlo, monospace;
        font-size: 0.65rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .page-frame {
        width: min(68rem, calc(100% - (2 * var(--page-gutter))));
        margin-inline: auto;
        padding: 6.5rem 0 4rem;
      }

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
        .site-title { display: none; }

        .mode-label {
          max-width: 10rem;
          text-align: right;
        }

        .page-frame { padding-top: 6rem; }

        h1 { font-size: 2rem; }
      }
    """


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
        def refresh(self, state):
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
            <p class="eyebrow">Citry FastAPI starter</p>
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
