---
title: Slots
url: https://citry.dev/v/0.4.6/examples/slots/
description: "Give a component named content areas with useful fallbacks."
---
# Slots

Named areas that show fallback content when you leave them empty.



### Component

````citry
"""A panel with named slots and footer fallback, used as a live docs example."""

from citry import Component, SlotInput


class SlotPanel(Component):
    """A styled panel with a header slot, a default body slot, and a footer slot.

    The footer slot ships fallback content, so a caller that omits the footer
    still gets a sensible default rendering.
    """

    class Kwargs:
        pass

    class Slots:
        header: SlotInput
        default: SlotInput
        footer: SlotInput | None = None

    template = """
      <section class="slot-panel">
        <header class="slot-panel__header">
          <c-slot name="header" />
        </header>
        <div class="slot-panel__body">
          <c-slot />
        </div>
        <footer class="slot-panel__footer">
          <c-slot name="footer">
            <span class="slot-panel__fallback">No actions available</span>
          </c-slot>
        </footer>
      </section>
    """

    css = """
      .slot-panel {
        max-width: 26rem;
        border: 1px solid #d0d7de;
        border-radius: 10px;
        overflow: hidden;
        font-family: system-ui, sans-serif;
        box-shadow: 0 1px 3px rgba(27, 31, 36, 0.12);
      }
      .slot-panel__header {
        padding: 0.75rem 1.25rem;
        background: #0969da;
        color: #ffffff;
        font-weight: 600;
      }
      .slot-panel__body {
        padding: 1.25rem;
        color: #24292f;
        line-height: 1.5;
      }
      .slot-panel__footer {
        padding: 0.75rem 1.25rem;
        background: #f6f8fa;
        border-top: 1px solid #d0d7de;
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
      }
      .slot-panel__fallback {
        color: #6e7781;
        font-style: italic;
        font-size: 0.9rem;
      }
      .slot-panel__button {
        padding: 0.35rem 0.85rem;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        background: #ffffff;
        color: #0969da;
        font: inherit;
        cursor: pointer;
      }
    """
````

### Page

````citry
"""Standalone page that renders the SlotPanel example (the live demo)."""

from citry import Component


class SlotsPage(Component):
    """A full page showing named slots with footer fallback content."""

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
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif; display: grid; gap: 1.5rem;"
        >
          <c-SlotPanel>
            <c-fill name="header">
              Project settings
            </c-fill>
            <c-fill name="default">
              Configure how your project builds and deploys. Every region of
              this panel is a named slot filled by the caller.
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
              This panel omits the footer slot, so its footer shows the
              component's own fallback content instead.
            </c-fill>
          </c-SlotPanel>
          <c-js />
        </body>
      </html>
    """
````

[Open the live result](/v/0.4.6/examples/slots/demo/)

