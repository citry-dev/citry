---
title: Error boundary
url: https://citry.dev/v/0.6.0/examples/error-fallback/
description: "Show fallback content when one part of a page cannot render."
---
# Error boundary

Use this pattern when one part of a page, such as a widget that calls an
outside service, may fail to render and the rest of the page should still
appear. Wrap that part in `<c-error-fallback>`, and if it raises an error
while rendering, Citry shows the `fallback` text in its place.



### Component

````citry
"""A widget that fails on demand, to demonstrate error boundaries."""

from typing import Any

from citry import Component


class FlakyWidget(Component):
    """Renders normal content, or raises when ``fail`` is true."""

    class Kwargs:
        label: str
        fail: bool = False

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        if kwargs.fail:
            # Raised during render, so the surrounding
            # <c-error-fallback> catches it.
            raise ValueError("FlakyWidget was told to fail")
        return {"label": kwargs.label}

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
````

### Page

````citry
"""Standalone page showing two error boundaries side by side."""

from citry import Component


class ErrorFallbackPage(Component):
    """Two FlakyWidgets, each in its own boundary.

    One widget renders cleanly and the other fails.
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
          <title>Error fallback example</title>
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

[Open the live result](/v/0.6.0/examples/error-fallback/demo/)



Both widgets are the same component. The second one raises `ValueError`
in `template_data()`, so its boundary shows "Could not load this widget."
The first widget, in its own boundary, renders normally.

To use markup as the fallback, nest boundaries, or see what happens to
an error that no boundary catches, see
[Error boundaries](/v/0.6.0/concepts/error-boundaries/).