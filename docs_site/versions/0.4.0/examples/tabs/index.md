---
title: Tabs
url: https://citry.dev/v/0.4.0/examples/tabs/
description: "Ship browser behavior with an accessible Tabs component."
---
# Tabs

A component that ships its own JavaScript, switching panels on click.



### Component

````citry
"""A client-side tabbed panel, used as a live example in the docs."""

from typing import Any, TypedDict

from citry import Component


class Tab(TypedDict):
    label: str
    body: str


class Tabs(Component):
    """A tab bar plus panels; clicking a tab shows its panel, driven by per-component JS."""

    class Kwargs:
        tabs: list[Tab]

    class Slots:
        pass

    template = """
      <div class="demo-tabs">
        <div
          class="demo-tabs__bar"
          role="tablist"
          aria-label="Example sections"
        >
          <button
            c-for="tab in tabs"
            c-id="tab['tab_id']"
            type="button"
            class="demo-tabs__tab"
            role="tab"
            c-aria-controls="tab['panel_id']"
            c-aria-selected="tab['active']"
            c-tabindex="tab['tabindex']"
            c-data-active="tab['active']"
            c-data-index="tab['index']"
          >
            {{ tab['label'] }}
          </button>
        </div>
        <div class="demo-tabs__panels">
          <div
            c-for="tab in tabs"
            c-id="tab['panel_id']"
            class="demo-tabs__panel"
            role="tabpanel"
            tabindex="0"
            c-aria-labelledby="tab['tab_id']"
            c-data-index="tab['index']"
            c-hidden="tab['active'] == 'false'"
          >
            {{ tab['body'] }}
          </div>
        </div>
      </div>
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
      .demo-tabs__tab[data-active="true"] {
        color: #0969da;
        font-weight: 600;
        border-bottom-color: #0969da;
      }
      .demo-tabs__panel {
        padding: 1rem 1.25rem;
        color: #24292f;
        line-height: 1.5;
      }
      .demo-tabs__panel[hidden] {
        display: none;
      }
    """

    js = """
      $component(({ els }) => {
        const root = els[0];
        const tabs = root.querySelectorAll(".demo-tabs__tab");
        const panels = root.querySelectorAll(".demo-tabs__panel");

        const activate = (nextTab, moveFocus = false) => {
          const nextIndex = nextTab.getAttribute("data-index");
          tabs.forEach((tab) => {
            const selected = tab === nextTab;
            tab.setAttribute("aria-selected", selected ? "true" : "false");
            tab.setAttribute("data-active", selected ? "true" : "false");
            tab.tabIndex = selected ? 0 : -1;
          });
          panels.forEach((panel) => {
            if (panel.getAttribute("data-index") === nextIndex) {
              panel.removeAttribute("hidden");
            } else {
              panel.setAttribute("hidden", "");
            }
          });
          if (moveFocus) {
            nextTab.focus();
          }
        };

        tabs.forEach((tab, index) => {
          tab.addEventListener("click", () => activate(tab));
          tab.addEventListener("keydown", (event) => {
            let nextIndex;
            if (event.key === "ArrowRight") {
              nextIndex = (index + 1) % tabs.length;
            } else if (event.key === "ArrowLeft") {
              nextIndex = (index - 1 + tabs.length) % tabs.length;
            } else if (event.key === "Home") {
              nextIndex = 0;
            } else if (event.key === "End") {
              nextIndex = tabs.length - 1;
            } else {
              return;
            }
            event.preventDefault();
            activate(tabs[nextIndex], true);
          });
        });
      });
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        # Precompute a per-tab index and active flag as strings. Expressions in the
        # template can't call builtins like enumerate/str, and a bare True boolean
        # would render as a valueless attribute, breaking the [data-active="true"]
        # CSS selector, so the string values are built here.
        prepared: list[dict[str, str]] = []
        id_prefix = f"demo-tabs-{self.id}"
        for i, tab in enumerate(kwargs.tabs):
            tab_id = f"{id_prefix}-tab-{i}"
            panel_id = f"{id_prefix}-panel-{i}"
            prepared.append(
                {
                    "label": tab["label"],
                    "body": tab["body"],
                    "tab_id": tab_id,
                    "panel_id": panel_id,
                    "index": str(i),
                    "active": "true" if i == 0 else "false",
                    "tabindex": "0" if i == 0 else "-1",
                }
            )
        return {"tabs": prepared}
````

### Page

````citry
"""Standalone page that renders the Tabs example (the live demo)."""

from typing import Any

from citry import Component


class TabsPage(Component):
    """A full page showing the Tabs component switching panels on click."""

    class Kwargs:
        pass

    class Slots:
        pass

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

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {
            "tabs": [
                {
                    "label": "Overview",
                    "body": "Citry ships a tiny bit of JS with each component. No framework, no CDN.",
                },
                {
                    "label": "Details",
                    "body": "Clicking a tab toggles the hidden attribute on its panel, all client-side.",
                },
                {
                    "label": "Notes",
                    "body": "The active tab is styled with the component's own CSS via a data attribute.",
                },
            ]
        }
````

[Open the live result](/v/0.4.0/examples/tabs/demo/)

