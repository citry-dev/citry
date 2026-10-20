from app.citry_app import citry_app
from app.data import ACCENT, API_BASE, Owner, Project
from citry import Component


class BoardPage(Component):
    citry = citry_app

    class I18n:
        messages_locale = "en-US"

    class Kwargs:
        owner: Owner
        projects: tuple[Project, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"owner": kwargs.owner, "projects": kwargs.projects}

    def js_data(self, kwargs: Kwargs, slots: Slots):
        # Only the public API base goes to the browser.
        return {"apiBase": API_BASE, "hiddenTitles": []}

    def css_data(self, kwargs: Kwargs, slots: Slots):
        # The server picks the heading color; the stylesheet reads it as --accent.
        return {"accent": ACCENT}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Projects</title>
          <c-css />
        </head>
        <body>
          <h1>{{ tr("board-title") }}</h1>
          <p>{{ tr("board-subtitle", name=owner.name) }}</p>
          <div class="board" title="Board">
            <img
              src="/static/avatar.svg"
              c-alt="owner.name"
              width="32"
              height="32"
            />
            <p>Owner: {{ owner.name }}</p>
            <p>API: <span v-text="apiBase"></span></p>
            <div class="cards">
              <c-for each="project in projects">
                <c-Card
                  #c-key="project.slug"
                  c-title="project.title"
                  c-count="project.count"
                  c-tone="'accent' if project.featured else 'plain'"
                  :hiddenTitles="hiddenTitles"
                  @hide="hideCard"
                >
                  <c-fill name="footer" data="card">
                    <a c-href="'#' + project.slug">Open {{ card.title }} ({{ card.count }})</a>
                  </c-fill>
                </c-Card>
              </c-for>
            </div>
            <c-Counter />
            <c-Details />
            <c-Search />
            <nav>
              <a href="/about">About</a>
              <a href="/projects/1">Project 1</a>
            </nav>
          </div>
          <c-js />
        </body>
      </html>
    """

    js = """
      $component({
        methods: {
          hideCard(title) {
            this.hiddenTitles.push(title);
          },
        },
      });
    """

    css = """
      h1 {
        color: var(--accent);
      }

      .board {
        color: rgb(0, 128, 0);
      }
    """

    messages = """
      board-title = Projects

      # @param {str} $name - The board owner's name.
      board-subtitle = Owned by { $name }
    """
