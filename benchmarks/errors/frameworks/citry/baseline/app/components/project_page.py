from app.citry_app import citry_app
from citry import Component


class ProjectPage(Component):
    citry = citry_app

    class Kwargs:
        project_id: int

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"project_id": kwargs.project_id}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Project</title>
        </head>
        <body>
          <h1>Project {{ project_id }}</h1>
        </body>
      </html>
    """
