---
title: Card
url: https://citry.dev/v/0.6.0/examples/card/
description: "Build a reusable Card with an input, a slot, and component CSS."
---
# Card

Use this pattern for a piece of markup you repeat across pages, such as a
card, a panel, or a badge. The Card takes an `accent` color, wraps
whatever HTML you put inside `<c-Card>`, and brings its own CSS. It runs
with Citry alone; no web framework is needed.



### Component

````citry
from citry import Component, SlotInput


class Card(Component):
    class Kwargs:
        accent: str

    class Slots:
        default: SlotInput

    def css_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, str]:
        return {"accent": kwargs.accent}

    template = """
      <article class="demo-card">
        <c-slot />
      </article>
    """

    css = """
      .demo-card {
        max-width: 24rem;
        padding: 1rem 1.25rem;
        border: 1px solid
          color-mix(in srgb, currentColor 20%, transparent);
        border-top: 0.25rem solid var(--accent);
        border-radius: 8px;
        background: Canvas;
        color: CanvasText;
        font-family: system-ui, sans-serif;
      }

      .demo-card__title {
        margin: 0 0 0.25rem;
        font-size: 1.1rem;
      }

      .demo-card__body {
        margin: 0;
      }
    """
````

### Page

````citry
"""The complete page shown in the Card example."""

# Importing Card registers the <c-Card> tag before CardPage renders.
from docs_site.examples.card.component import Card  # noqa: F401

from citry import Component


class CardPage(Component):
    """A full page showing the Card component on its own."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Card example</title>
          <c-css />
          <style>
            body {
              margin: 0;
              padding: 1.5rem;
              color-scheme: light dark;
            }
          </style>
        </head>
        <body>
          <c-Card accent="#8250df">
            <h2 class="demo-card__title">Welcome</h2>
            <p class="demo-card__body">
              Choose the accent color, then add any content you like.
            </p>
          </c-Card>
        </body>
      </html>
    """
````

[Open the live result](/v/0.6.0/examples/card/demo/)



The lines to notice:

- `accent` sets the top border color. `css_data()` passes it to the CSS
  as `var(--accent)`, so each Card on a page can have its own color.
- Everything between `<c-Card>` and `</c-Card>` appears where the
  template has `<c-slot />`.
- Citry adds the Card's styles to the page; `<c-css />` marks where.
  Those styles apply to anything on the page with the `demo-card` class, so the example uses
  that specific name rather than a broad one such as `.card`.

If a template leaves out `accent` or the content, Citry raises an error
that names what is missing as soon as it compiles that template. The `accent: str` annotation helps
your editor and type checker, but Citry does not check at runtime that
the value is a string.

For a guided walkthrough, read
[Your first component](/v/0.6.0/getting-started/your-first-component/). For
details, see [component inputs](/v/0.6.0/reference/component/#citry-component-kwargs),
[slots](/v/0.6.0/reference/component/#citry-component-slots), [SlotInput](/v/0.6.0/reference/slots/#citry-slotinput), and
[component CSS](/v/0.6.0/reference/component/#citry-component-css).