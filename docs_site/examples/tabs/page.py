"""Standalone page that renders the Tabs example (the live demo)."""

from typing import Any

from citry import Component


class TabsPage(Component):
    """A full page showing the Tabs component switching panels on click."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Tabs example</title>
          <c-css />
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <c-Tabs c-tabs="tabs" />
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {
            "tabs": [
                {
                    "label": "Overview",
                    "body": "Citry ships a tiny bit of JS with each component. No framework, no CDN.",
                },
                {
                    "label": "Details",
                    "body": "Clicking a tab toggles the hidden attribute on its panel, all client-side.",
                },
                {
                    "label": "Notes",
                    "body": "The active tab is styled with the component's own CSS via a data attribute.",
                },
            ]
        }
