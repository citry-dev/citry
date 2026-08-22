---
title: Card
url: https://citry.dev/v/0.4.3/examples/card/
description: "Build a reusable Card with an input, a slot, and component CSS."
---
# Card

Make a card with a colored top border. Choose the color with `accent`, then put
a heading, text, or any other HTML inside `<c-Card>`. You can run this example
with Citry alone; no web framework is needed.



### Component

````citry
from citry import Component, SlotInput


class Card(Component):
    class Kwargs:
        accent: str

    class Slots:
        default: SlotInput

    def css_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:
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
        border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
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
        </head>
        <body style="margin: 0; padding: 1.5rem; color-scheme: light dark;">
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

[Open the live result](/v/0.4.3/examples/card/demo/)



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
[Your first component](/v/0.4.3/getting-started/your-first-component/). When you want
more detail, read about [component inputs](/v/0.4.3/reference/component/#citry-component-kwargs),
[component slots](/v/0.4.3/reference/component/#citry-component-slots), [SlotInput](/v/0.4.3/reference/slots/#citry-slotinput), and
[component CSS](/v/0.4.3/reference/component/#citry-component-css).