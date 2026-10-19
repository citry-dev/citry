---
title: Provide and inject
url: https://citry.dev/v/0.6.0/examples/provide-inject/
description: "Share a value with every component in a subtree."
---
# Provide and inject

Use this pattern when many components inside one part of the page need
the same value, such as a theme, and passing it through every component
in between would be tedious. `<c-provide>` makes the value available to
everything inside it, and each component reads it with `self.inject()`.



### Component

````citry
"""A button that reads its look from a provided theme."""

from typing import Any

from citry import Component


class ThemedButton(Component):
    """A button with no theme prop.

    It injects the nearest provided theme instead.
    """

    class Kwargs:
        text: str

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        theme = self.inject("theme")
        return {
            "text": kwargs.text,
            "label": theme.label,
            "style": f"background: {theme.accent};",
        }

    template = """
      <button class="themed-btn" c-style="style">
        {{ label }}: {{ text }}
      </button>
    """

    css = """
      .themed-btn {
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-family: system-ui, sans-serif;
        font-size: 0.95rem;
        cursor: pointer;
      }
    """
````

### Page

````citry
"""Standalone page showing buttons styled by an ancestor theme."""

from citry import Component


class ProvideInjectPage(Component):
    """A full page wrapping ThemedButtons in provided themes.

    The buttons inject their theme and never receive it as a prop.
    """

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Provide / inject example</title>
          <c-css />
          <style>
            body {
              margin: 0;
              padding: 1.5rem;
              font-family: system-ui, sans-serif;
            }
          </style>
        </head>
        <body>
          <c-provide
            key="theme"
            accent="#2563eb"
            label="Ocean"
          >
            <p style="margin: 0 0 0.5rem; color: #57606a;">
              These buttons read the outer theme:
            </p>
            <c-ThemedButton text="Save" />
            <c-ThemedButton text="Share" />

            <c-provide
              key="theme"
              accent="#16a34a"
              label="Forest"
            >
              <p style="margin: 1rem 0 0.5rem; color: #57606a;">
                Nested provide wins for buttons inside it:
              </p>
              <c-ThemedButton text="Publish" />
            </c-provide>
          </c-provide>
          <c-js />
        </body>
      </html>
    """
````

[Open the live result](/v/0.6.0/examples/provide-inject/demo/)



`ThemedButton` has no theme input. It calls `self.inject("theme")` and
reads `accent` and `label` from the result. The inner `<c-provide>` uses
the same key, so the button inside it gets the Forest theme, while the
buttons outside it get Ocean. A component always reads the nearest
value.

For defaults, errors, and providing values from Python, see
[Provide and inject](/v/0.6.0/concepts/provide-and-inject/).