---
title: Provide and inject
url: https://citry.dev/v/0.4.6/examples/provide-inject/
description: "Share a value with every component in a subtree."
---
# Provide and inject

Pass a value to a whole subtree with `<c-provide>`, and read it with `inject()`.



### Component

````citry
"""A button that reads its look from a provided theme, used as a live docs example."""

from typing import Any

from citry import Component


class ThemedButton(Component):
    """A button with no theme prop: it injects the nearest provided theme instead."""

    class Kwargs:
        text: str

    class Slots:
        pass

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

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        theme = self.inject("theme")
        return {
            "text": kwargs.text,
            "label": theme.label,
            "style": "background: " + theme.accent + ";",
        }
````

### Page

````citry
"""Standalone page showing provide/inject: buttons styled by an ancestor theme."""

from citry import Component


class ProvideInjectPage(Component):
    """A full page wrapping ThemedButtons in themes they inject, never receive as props."""

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
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
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

[Open the live result](/v/0.4.6/examples/provide-inject/demo/)

