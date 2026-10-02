---
title: Card
description: Build a reusable Card with an input, a slot, and component CSS.
---

# Card

Use this pattern for a piece of markup you repeat across pages, such as a
card, a panel, or a badge. The Card takes an `accent` color, wraps
whatever HTML you put inside `<c-Card>`, and brings its own CSS. It runs
with Citry alone; no web framework is needed.

<c-example name="card" />

The lines to notice:

- `accent` sets the top border color. `css_data()` passes it to the CSS
  as `var(--accent)`, so each Card on a page can have its own color.
- Everything between `<c-Card>` and `</c-Card>` appears where the
  template has `<c-slot />`.
- `<c-css />` in the page adds the Card's styles. Those styles apply to
  anything on the page with the `demo-card` class, so the example uses
  that specific name rather than a broad one such as `.card`.

If you leave out `accent` or the content, rendering the Card fails with
an error that names what is missing. The `accent: str` annotation helps
your editor and type checker, but Citry does not check at runtime that
the value is a string.

For a guided walkthrough, read
[Your first component](/getting-started/your-first-component/). For
details, see [component inputs][citry.Component.Kwargs],
[slots][citry.Component.Slots], [SlotInput][citry.SlotInput], and
[component CSS][citry.Component.css].
