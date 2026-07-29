---
title: Your first component
description: Build a reusable card, choose its border color, add some content, and render it with Python.
---

# Your first component

Let's build something you can see and reuse: a card with a colored top border.
Each time you use it, you can choose a new color and put different content
inside.

The finished card runs with plain Python. You do not need to set up Django,
FastAPI, or another web framework.

<a href="/examples/card/demo/" target="_blank">See the finished result</a>
before you start.

## Before you start

It helps to recognize basic HTML, but you can copy
the CSS as-is even if styling is new to you.

## Create the card

A component is a reusable piece of HTML. You define it once, then use it
wherever you need the same structure.

Save this as `component.py`:

<c-live-code
  path="docs_site/examples/card/component.py"
  title="component.py"
  full_height
/>

It may look like a lot for a first component, so we'll unpack it one piece at
a time.

## Start with the HTML

The [`template`][citry.Component.template] is ordinary HTML with one Citry tag:

```html
<article class="demo-card">
  <c-slot />
</article>
```

[`<c-slot />`](/reference/builtins/#c-slot) marks the place where the card's
content will appear. When you
write this:

```html
<c-Card accent="#8250df">
  <p>Hello from inside the card.</p>
</c-Card>
```

Citry puts the paragraph where `<c-slot />` appears. This unnamed space is
called the **default slot**.

## Choose what can change

The two short classes near the top of `Card` describe the parts you can
change each time you use it:

- [`Kwargs`][citry.Component.Kwargs] lists the `name=value` options you can
  choose when you use the Card.
  This card has one option, `accent`, which chooses the border color.
- [`Slots`][citry.Component.Slots] lists places where text or HTML can go. This
  card has one place, `default`, for everything written between `<c-Card>` and
  `</c-Card>`.

The [`css_data()`][citry.Component.css_data] method sends the chosen accent to
CSS as `--accent`.

Neither `accent` nor `default` has a fallback value, so you need to provide
both when you use the card.

## Add the styles

The [`css`][citry.Component.css] block travels with the Card. Citry adds it to
any page that renders the component, and `var(--accent)` picks up the color you
chose.

The `.demo-card` selector behaves like ordinary CSS: it styles every matching
element on the page. Give component classes distinctive names so they do not
accidentally style something else.

## Use the card in a template

Here is the important part of the complete example page:

```html
<c-Card accent="#8250df">
  <h2 class="demo-card__title">Welcome</h2>
  <p class="demo-card__body">
    Choose the accent color, then add any content you like.
  </p>
</c-Card>
```

The `accent` option makes the top border purple. The heading and paragraph go
inside the card because they sit between its opening and closing tags.

## Render it from Python

You can create the same Card directly from Python. Save this as `render.py`
next to `component.py`:

```python
from component import Card

card = Card(
    accent="#8250df",
    slots={"default": "Build something useful."},
)
print(card)
```

The `slots` dictionary is the Python way to fill the same default slot. Run
the file:

```sh
python render.py
```

Citry prints the card's HTML and the styles it needs. The result looks like this (shortened):

```html
<style>
  /* Citry adds --accent: #8250df for this card. */
  .demo-card {
    border-top: 0.25rem solid var(--accent);
  }
</style>
<article class="demo-card">
  Build something useful.
</article>
```

The real HTML contains a few extra attributes that Citry uses. You do not need
to write or remember them.

## Use a different color for each card

The rules in `Card.css` are shared by every Card on the page. The value from
`css_data()` stays with the Card it came from, so one Card can be blue while
another is orange.

Save this as `two_cards.py` next to `component.py`:

```citry
from citry import Component

from component import Card

class CardList(Component):
    template = """
      <c-Card accent="#0969da">
        <p>Blue card: Prepare the first draft.</p>
      </c-Card>
      <c-Card accent="#bc4c00">
        <p>Orange card: Review the final copy.</p>
      </c-Card>
    """

print(CardList())
```

Run `python two_cards.py`. Both cards use the same HTML and CSS, but each card
keeps the color and text given to it.

This is useful whenever several copies of a component should share the same
layout but keep their own colors, sizes, or other CSS values.

## If you leave something out

Both the accent color and the content are required. If you forget the color,
Citry cannot finish the Card:

```python
str(Card(slots={"default": "Where is my color?"}))
# TypeError: Card.Kwargs.__init__() missing ... 'accent'
```

Add `accent` and the Card renders:

```python
str(
    Card(
        accent="#8250df",
        slots={"default": "Now the card has everything it needs."},
    )
)
```

The same thing happens if you leave out the default slot. Citry checks these
values when it turns the Card into HTML, so the error appears at `str()` or
`print()`, not when Python first reaches `Card(...)`.

!!! note

    `accent: str` helps your editor and type checker, but it
    does not reject `accent=123` while your program runs. If values come from a
    form, an API, or another source you do not control, read
    [Inputs and validation](/concepts/inputs-and-validation/) to add runtime
    checks.

## What to try next

You now have a Card that:

- asks for an accent color;
- places text or HTML where `<c-slot />` appears;
- lets several Cards use different colors; and
- reports an error when required information is missing.

You can [open the Card recipe](/examples/card/) to compare the component,
complete page, and live result. To continue the guided journey, [use Python
data in components](/getting-started/data-in-components/).
