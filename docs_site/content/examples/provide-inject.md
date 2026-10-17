---
title: Provide and inject
description: Share a value with every component in a subtree.
---

# Provide and inject

Use this pattern when many components inside one part of the page need
the same value, such as a theme, and passing it through every component
in between would be tedious. `<c-provide>` makes the value available to
everything inside it, and each component reads it with `self.inject()`.

<c-example name="provide_inject" />

`ThemedButton` has no theme input. It calls `self.inject("theme")` and
reads `accent` and `label` from the result. The inner `<c-provide>` uses
the same key, so the button inside it gets the Forest theme, while the
buttons outside it get Ocean. A component always reads the nearest
value.

For defaults, errors, and providing values from Python, see
[Provide and inject](/concepts/provide-and-inject/).
