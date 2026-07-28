---
title: Card
description: Build a reusable Card with an input, a slot, and component CSS.
---

# Card

Make a card with a colored top border. Choose the color with `accent`, then put
a heading, text, or any other HTML inside `<c-Card>`. You can run this example
with Citry alone; no web framework is needed.

<c-example name="card" />

The Card works in both light and dark themes. The lines to notice are simple:
`accent` chooses the border color, and everything between `<c-Card>` and
`</c-Card>` appears inside it. Each Card keeps its own color, so several Cards
on one page do not have to match.

The styles in `Card.css` are added automatically. They can affect anything on
the page named `.demo-card`, which is why the example uses a specific class
name rather than a broad name such as `.card`.

Try the same code in your project with another accent color. If you leave out
the color or the content, Citry tells you what is missing when it renders the
Card. The `accent: str` annotation helps your editor and type checker, but it
does not check the value while your program runs.

For a guided walkthrough, read
[Your first component](/getting-started/your-first-component/). When you want
more detail, read about [component inputs][citry.Component.Kwargs],
[component slots][citry.Component.Slots], [SlotInput][citry.SlotInput], and
[component CSS][citry.Component.css].
