"""Standalone page that renders the recursion example (the live demo)."""

from typing import Any

from citry import Component


class RecursionPage(Component):
    """A full page showing a nested tree drawn by the self-rendering TreeNode."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Recursion example</title>
          <c-css />
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <c-TreeNode c-node="tree" />
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        # A small folder tree, three levels deep, passed in one piece.
        tree = {
            "label": "project",
            "children": [
                {
                    "label": "src",
                    "children": [
                        {"label": "app.py"},
                        {"label": "utils.py"},
                    ],
                },
                {
                    "label": "docs",
                    "children": [
                        {
                            "label": "guide",
                            "children": [
                                {"label": "intro.md"},
                                {"label": "advanced.md"},
                            ],
                        },
                    ],
                },
                {"label": "README.md"},
            ],
        }
        return {"tree": tree}
