---
title: Tabs
description: Ship browser behavior with an accessible Tabs component.
---

# Tabs

Use this pattern when a component needs to react in the browser without
asking the server, such as switching tabs. The `Tabs` component brings
its own JavaScript, which tracks the open tab with Vue and supports the
arrow keys.

<c-example name="tabs" />

The lines to notice:

- `js_data()` sends the tab list and the starting tab from Python to the
  component's JavaScript.
- `@click` and `@keydown` in the template call into that JavaScript.
- The ID prefix uses `self.id`, so two Tabs on one page do not share
  element IDs.

To learn how a component's JavaScript works, see
[Component options](/vue/component-options/).
