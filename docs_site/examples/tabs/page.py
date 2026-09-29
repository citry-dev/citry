"""Standalone page that renders the Tabs example (the live demo)."""

from typing import Any

from citry import Component


class TabsPage(Component):
    """A full page showing the Tabs component switching panels on click."""

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {
            "tabs": [
                {
                    "label": "Overview",
                    "body": "Each Tabs keeps its open tab in browser state.",
                },
                {
                    "label": "Details",
                    "body": "Click a tab or use the arrow keys to open a panel.",
                },
                {
                    "label": "Notes",
                    "body": "CSS styles the open tab by its aria-selected value.",
                },
            ]
        }

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
