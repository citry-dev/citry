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
                    "body": "Each Tabs instance keeps the open tab in its own browser state.",
                },
                {
                    "label": "Details",
                    "body": "Clicking a tab, or moving to it with the arrow keys, opens its panel.",
                },
                {
                    "label": "Notes",
                    "body": "The component's CSS styles the open tab through its aria-selected attribute.",
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
