---
title: Tabs
url: https://citry.dev/v/0.6.0/examples/tabs/
description: "Ship browser behavior with an accessible Tabs component."
---
# Tabs

Use this pattern when a component needs to react in the browser without
asking the server, such as switching tabs. The `Tabs` component brings
its own JavaScript, which tracks the open tab with Vue and supports the
arrow keys.



### Component

````citry
"""A client-side tabbed panel, used as a live example in the docs."""

from typing import Any, TypedDict

from citry import Component


class Tab(TypedDict):
    label: str
    body: str


class Tabs(Component):
    """A tab bar plus panels; Vue state tracks the open tab."""

    class Kwargs:
        tabs: list[Tab]

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {
            "tabs": kwargs.tabs,
            "activeIndex": 0,
            # The instance ID keeps element IDs unique when a page
            # shows several Tabs, so each tab still names its own
            # panel.
            "idPrefix": f"demo-tabs-{self.id}",
        }

    template = """
      <div class="demo-tabs">
        <div
          class="demo-tabs__bar"
          role="tablist"
          aria-label="Example sections"
        >
          <button
            v-for="(tab, index) in tabs"
            :ref="(el) => keepTabButton(index, el)"
            :id="idPrefix + '-tab-' + index"
            type="button"
            class="demo-tabs__tab"
            role="tab"
            :aria-controls="idPrefix + '-panel-' + index"
            :aria-selected="index === activeIndex"
            :tabindex="index === activeIndex ? 0 : -1"
            @click="activeIndex = index"
            @keydown="moveWithKeys($event, index)"
            v-text="tab.label"
          ></button>
        </div>
        <div
          v-for="(tab, index) in tabs"
          v-show="index === activeIndex"
          :id="idPrefix + '-panel-' + index"
          class="demo-tabs__panel"
          role="tabpanel"
          tabindex="0"
          :aria-labelledby="idPrefix + '-tab-' + index"
          v-text="tab.body"
        ></div>
      </div>
    """

    js = """
      $component({
        created() {
          // Vue does not promise that refs collected inside v-for
          // keep the list order, so each button is stored under its
          // index. A plain Map, set up here rather than in data(),
          // keeps Vue from tracking the elements as state.
          this.tabButtons = new Map();
        },
        methods: {
          keepTabButton(index, el) {
            // Vue calls this with null when the button unmounts, so
            // the Map drops it instead of holding a detached element.
            if (el) {
              this.tabButtons.set(index, el);
            } else {
              this.tabButtons.delete(index);
            }
          },
          moveWithKeys(event, index) {
            // The arrow keys wrap around, and Home and End jump to
            // the ends, as the WAI-ARIA tabs pattern expects.
            const count = this.tabs.length;
            const nextIndex = {
              ArrowRight: (index + 1) % count,
              ArrowLeft: (index - 1 + count) % count,
              Home: 0,
              End: count - 1,
            }[event.key];
            // Other keys, such as Tab, keep their usual meaning.
            if (nextIndex === undefined) return;
            event.preventDefault();
            this.activeIndex = nextIndex;
            // Only the open tab is in the Tab order, so focus
            // follows it.
            this.tabButtons.get(nextIndex)?.focus();
          },
        },
      });
    """

    css = """
      .demo-tabs {
        max-width: 30rem;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        overflow: hidden;
        font-family: system-ui, sans-serif;
      }
      .demo-tabs__bar {
        display: flex;
        background: #f6f8fa;
        border-bottom: 1px solid #d0d7de;
      }
      .demo-tabs__tab {
        flex: 1;
        padding: 0.6rem 1rem;
        border: none;
        background: transparent;
        font: inherit;
        color: #57606a;
        cursor: pointer;
        border-bottom: 2px solid transparent;
      }
      .demo-tabs__tab:hover {
        background: #eef1f4;
      }
      .demo-tabs__tab[aria-selected="true"] {
        color: #0969da;
        font-weight: 600;
        border-bottom-color: #0969da;
      }
      .demo-tabs__panel {
        padding: 1rem 1.25rem;
        color: #24292f;
        line-height: 1.5;
      }
    """
````

### Page

````citry
"""Standalone page that renders the Tabs example (the live demo)."""

from typing import Any

from citry import Component

# Every render shows the same three tabs, so the list is defined once.
TABS = [
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


class TabsPage(Component):
    """A full page showing the Tabs component switching panels."""

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {"tabs": TABS}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Tabs example</title>
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
          <c-Tabs c-tabs="tabs" />
          <c-js />
        </body>
      </html>
    """
````

[Open the live result](/v/0.6.0/examples/tabs/demo/)



The lines to notice:

- `js_data()` sends the tab list and the starting tab from Python to the
  component's JavaScript.
- `@click` and `@keydown` in the template call into that JavaScript.
- The ID prefix uses `self.id`, so two Tabs on one page do not share
  element IDs.

To learn how a component's JavaScript works, see
[Component options](/v/0.6.0/vue/component-options/).