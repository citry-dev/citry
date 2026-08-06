"""The complete page shown in the Card example."""

# Importing Card registers the <c-Card> tag before CardPage renders.
from docs_site.examples.card.component import Card  # noqa: F401

from citry import Component


class CardPage(Component):
    """A full page showing the Card component on its own."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Card example</title>
          <c-css />
        </head>
        <body style="margin: 0; padding: 1.5rem; color-scheme: light dark;">
          <c-Card accent="#8250df">
            <h2 class="demo-card__title">Welcome</h2>
            <p class="demo-card__body">
              Choose the accent color, then add any content you like.
            </p>
          </c-Card>
        </body>
      </html>
    """
