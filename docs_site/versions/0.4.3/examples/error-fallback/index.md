---
title: Error boundary
url: https://citry.dev/v/0.4.3/examples/error-fallback/
description: "Show fallback content when one part of a page cannot render."
---
# Error boundary

A render error shows a fallback instead of breaking the page.



### Component

````citry
"""A widget that can fail on demand, used to demonstrate error boundaries."""

from typing import Any

from citry import Component


class FlakyWidget(Component):
    """Renders normal content, or raises during render when ``fail`` is true."""

    class Kwargs:
        label: str
        fail: bool = False

    class Slots:
        pass

    template = """
      <div class="flaky">
        <strong>{{ label }}</strong>
        <p class="flaky__ok">Loaded cleanly.</p>
      </div>
    """

    css = """
      .flaky {
        padding: 0.75rem 1rem;
        border: 1px solid #2da44e;
        border-radius: 8px;
        background: #effef1;
      }
      .flaky__ok {
        margin: 0.35rem 0 0;
        color: #1a7f37;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if kwargs.fail:
            # Raised during render so the surrounding <c-error-fallback> catches it.
            raise ValueError("FlakyWidget was told to fail")
        return {"label": kwargs.label}
````

### Page

````citry
"""Standalone page showing two error boundaries side by side."""

from citry import Component


class ErrorFallbackPage(Component):
    """Two FlakyWidgets, each in its own boundary: one healthy, one failing."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Error fallback example</title>
          <c-css />
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <h2 style="margin: 0 0 1rem;">Both boundaries rendered</h2>
          <div
            style="display: flex; gap: 1rem; align-items: flex-start;"
          >
            <c-error-fallback fallback="Could not load this widget.">
              <c-FlakyWidget label="Healthy widget" />
            </c-error-fallback>
            <c-error-fallback fallback="Could not load this widget.">
              <c-FlakyWidget
                label="Failing widget"
                c-fail="True"
              />
            </c-error-fallback>
          </div>
          <c-js />
        </body>
      </html>
    """
````

[Open the live result](/v/0.4.3/examples/error-fallback/demo/)

