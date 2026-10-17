---
title: Error boundary
description: Show fallback content when one part of a page cannot render.
---

# Error boundary

Use this pattern when one part of a page, such as a widget that calls an
outside service, may fail to render and the rest of the page should still
appear. Wrap that part in `<c-error-fallback>`, and if it raises an error
while rendering, Citry shows the `fallback` text in its place.

<c-example name="error_fallback" />

Both widgets are the same component. The second one raises `ValueError`
in `template_data()`, so its boundary shows "Could not load this widget."
The first widget, in its own boundary, renders normally.

To use markup as the fallback, nest boundaries, or see what happens to
an error that no boundary catches, see
[Error boundaries](/concepts/error-boundaries/).
