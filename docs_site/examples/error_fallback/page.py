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
