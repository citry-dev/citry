from app.citry_app import citry_app
from app.data import API_BASE, Owner, Project
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
          <div class="bord" title="Board">
            <p>Owner: {{ owner.name }}</p>
            <p>API: <span v-text="apiBase"></span></p>
            <div class="cards">
              <c-for each="project in projects">
                <c-Card
                  #c-key="project.slug"
                  c-title="project.title"
                  c-count="project.count"
                  :hiddenTitles="hiddenTitles"
                  @hide="hideCard"
                >
                  <c-fill name="footer">
                    <a c-href="'#' + project.slug">Open {{ project.title }}</a>
                  </c-fill>
                </c-Card>
              </c-for>
            </div>
            <c-Counter />
            <c-Details />
            <form role="search">
              <button type="submit">Search</button>
            </form>
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
      .board {
        color: rgb(0, 128, 0);
      }
    """

    messages = """
      board-title = Projects
    """
