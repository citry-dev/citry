from app.citry_app import citry_app
from citry import Component


class AboutPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>About</title>
        </head>
        <body>
          <h1>About this board</h1>
        </body>
      </html>
    """
