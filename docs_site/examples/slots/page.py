"""Standalone page that renders the SlotPanel example."""

from citry import Component


class SlotsPage(Component):
    """A full page showing named slots and footer fallback content."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Slots example</title>
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
          <main style="display: grid; gap: 1.5rem;">
            <c-SlotPanel>
              <c-fill name="header">
                Project settings
              </c-fill>
              <c-fill name="default">
                Configure how your project builds and deploys. Every
                region of this panel is a named slot filled by the
                caller.
              </c-fill>
              <c-fill name="footer">
                <button class="slot-panel__button">Cancel</button>
                <button class="slot-panel__button">Save</button>
              </c-fill>
            </c-SlotPanel>

            <c-SlotPanel>
              <c-fill name="header">
                Read-only notice
              </c-fill>
              <c-fill name="default">
                This panel omits the footer slot, so its footer shows
                the component's own fallback content instead.
              </c-fill>
            </c-SlotPanel>
          </main>
          <c-js />
        </body>
      </html>
    """
