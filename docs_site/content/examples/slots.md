---
title: Slots
description: Give a component named content areas with useful fallbacks.
---

# Slots

Use this pattern when a component draws a fixed frame and each use fills
in different parts of it. `SlotPanel` has a header, a body, and a footer.
Each use fills them with `<c-fill>`, and the footer shows fallback text
when a use leaves it out.

<c-example name="slots" />

The `Slots` class makes `header` and the default slot required and the
footer optional (`SlotInput | None = None`). The content between
`<c-slot name="footer">` and `</c-slot>` is the fallback. The second
panel on the page does not fill the footer, so it shows "No actions
available".

For more about slots, see [Slots](/concepts/slots/).
