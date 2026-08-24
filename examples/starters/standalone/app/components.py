from citry import Component, SlotInput

from .citry_app import citry_app
from .data import Project


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
          <meta
            name="description"
            content="A standalone Project Explorer built with Citry"
          />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <header class="site-header">
            <a class="brand" href="#main-content" aria-label="Project Explorer home">
              <span class="brand__mark" aria-hidden="true">C</span>
              <span>Project Explorer</span>
            </a>
            <span class="mode-pill">Standalone document</span>
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
        font-family:
          Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
          "Segoe UI", sans-serif;
        color: #16231d;
        background: #f4f1e8;
        font-synthesis: none;
      }

      * { box-sizing: border-box; }

      [x-cloak] { display: none !important; }

      body {
        min-width: 20rem;
        min-height: 100vh;
        margin: 0;
        background:
          radial-gradient(circle at 10% 0%, rgb(255 255 255 / 0.9), transparent 28rem),
          #f4f1e8;
      }

      button, input { font: inherit; }

      button:focus-visible, input:focus-visible, a:focus-visible {
        outline: 3px solid #cf5c36;
        outline-offset: 3px;
      }

      .site-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        min-height: 4.5rem;
        padding: 0.85rem clamp(1rem, 5vw, 4rem);
        color: #f7f4ec;
        background: #163c32;
      }

      .brand {
        display: inline-flex;
        align-items: center;
        gap: 0.7rem;
        color: inherit;
        font-weight: 750;
        letter-spacing: -0.02em;
        text-decoration: none;
      }

      .brand__mark {
        display: grid;
        width: 2.1rem;
        height: 2.1rem;
        place-items: center;
        border: 1px solid rgb(255 255 255 / 0.35);
        border-radius: 0.65rem;
        color: #163c32;
        background: #f1bb69;
      }

      .mode-pill {
        padding: 0.38rem 0.7rem;
        border: 1px solid rgb(255 255 255 / 0.25);
        border-radius: 999px;
        font-size: 0.78rem;
      }

      .page-frame {
        width: min(72rem, calc(100% - 2rem));
        margin: 0 auto;
        padding: clamp(2.5rem, 7vw, 6rem) 0;
      }

      .hero {
        display: grid;
        max-width: 50rem;
        gap: 1rem;
        margin-bottom: 2.2rem;
      }

      .eyebrow {
        margin: 0;
        color: #a04426;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      h1 {
        max-width: 13ch;
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(2.8rem, 8vw, 5.7rem);
        font-weight: 500;
        letter-spacing: -0.055em;
        line-height: 0.94;
      }

      .hero__intro {
        max-width: 43rem;
        margin: 0;
        color: #526159;
        font-size: clamp(1rem, 2vw, 1.2rem);
        line-height: 1.65;
      }

      @media (max-width: 35rem) {
        .site-header { align-items: flex-start; }
        .mode-pill { display: none; }
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
          <h2>{{ name }}</h2>
          <p>{{ summary }}</p>
        </div>
        <footer>
          <span class="language-dot" aria-hidden="true"></span>
          {{ language }}
        </footer>
      </article>
    """

    css = """
      .project-card {
        display: grid;
        min-height: 16rem;
        gap: 1.7rem;
        align-content: space-between;
        padding: 1.35rem;
        border: 1px solid #d9d4c8;
        border-radius: 1rem;
        background: rgb(255 255 255 / 0.76);
        box-shadow: 0 0.7rem 2rem rgb(34 49 42 / 0.06);
      }

      .project-card__topline, .project-card footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
      }

      .project-card__initial {
        display: grid;
        width: 2.7rem;
        height: 2.7rem;
        place-items: center;
        border-radius: 0.75rem;
        color: #f9f6ed;
        background: #1f5948;
        font-weight: 800;
      }

      .project-card__status {
        padding: 0.3rem 0.6rem;
        border-radius: 999px;
        color: #81401f;
        background: #f6dfbd;
        font-size: 0.75rem;
        font-weight: 750;
      }

      .project-card h2 {
        margin: 0 0 0.55rem;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.7rem;
        font-weight: 500;
      }

      .project-card p {
        margin: 0;
        color: #5c685f;
        line-height: 1.55;
      }

      .project-card footer {
        justify-content: flex-start;
        color: #69766d;
        font-size: 0.82rem;
      }

      .language-dot {
        width: 0.55rem;
        height: 0.55rem;
        border-radius: 50%;
        background: #cf5c36;
      }
    """


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
            <p>{{ result_count }} projects supplied by Python</p>
          </div>
          <button
            class="help-button"
            type="button"
            @click="tipsOpen = !tipsOpen"
            :aria-expanded="tipsOpen.toString()"
            aria-controls="explorer-help"
          >
            <span aria-hidden="true">?</span>
            <span x-text="tipsOpen ? 'Hide how it works' : 'Show how it works'">
              Show how it works
            </span>
          </button>
        </div>

        <aside id="explorer-help" class="explorer__help" x-cloak x-show="tipsOpen">
          <strong>This toggle stays in the browser.</strong>
          Alpine owns <code>tipsOpen</code>, so showing this panel does not
          rerun Python or require a web server.
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
      }

      .explorer__toolbar {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #d4cec0;
      }

      .explorer__toolbar h2 {
        margin: 0 0 0.25rem;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(1.6rem, 4vw, 2.2rem);
        font-weight: 500;
      }

      .explorer__toolbar p { margin: 0; color: #647168; }

      .help-button {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        min-height: 2.7rem;
        padding: 0.55rem 0.8rem;
        border: 1px solid #b9b3a6;
        border-radius: 0.7rem;
        color: #263b31;
        background: transparent;
        cursor: pointer;
      }

      .help-button > span:first-child {
        display: grid;
        width: 1.45rem;
        height: 1.45rem;
        place-items: center;
        border-radius: 50%;
        color: #fff;
        background: #cf5c36;
        font-weight: 800;
      }

      .explorer__help {
        padding: 1rem 1.15rem;
        border-left: 0.3rem solid #cf5c36;
        color: #4d5a52;
        background: #fffbf2;
        line-height: 1.55;
      }

      .explorer__help strong { color: #263b31; }

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
            <h1>Useful pages start with ordinary Python data.</h1>
            <p class="hero__intro">
              This self-contained document passes rich records through a
              component tree, collects CSS and JavaScript once, and adds local
              Alpine behavior without a web framework.
            </p>
          </section>
        </c-fill>
        <c-fill name="default">
          <c-ProjectExplorer c-projects="projects" />
        </c-fill>
      </c-PageShell>
    """
