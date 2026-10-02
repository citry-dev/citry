---
title: Your first component
description: Build a reusable card, choose its border color, add some content, and render it with Python.
---

# Your first component

When the same piece of HTML appears in many places, you want to write it
once and reuse it. In Citry, that reusable piece is a **component**: a Python
class with an HTML template.

In this step you build a card with a colored top border. Each time you use
it, you choose a color and put different content inside. The card runs with
plain Python, so you do not need Django, FastAPI, or another web framework.
It helps to recognize basic HTML, and you can copy the CSS as it is.

<a href="/examples/card/demo/" target="_blank">See the finished result</a>
before you start.

## Create the card

Save this as `component.py`:

<c-live-code
  path="docs_site/examples/card/component.py"
  title="component.py"
  full_height
/>

The next sections go through it one piece at a time.

## Add a content slot

The [`template`][citry.Component.template] is ordinary HTML with one Citry
tag:

```citry-html
<article class="demo-card">
  <c-slot />
</article>
```

[`<c-slot />`](/reference/builtins/#c-slot) marks the place where the card's
content appears. When you write this:

```citry-html
<c-Card accent="#8250df">
  <p>Hello from inside the card.</p>
</c-Card>
```

Citry puts the paragraph where `<c-slot />` is. A place like this is called
a **slot**. This one has no name, so it is the **default slot**.

## Declare the inputs

The two short classes near the top of `Card` list what you can change each
time you use it:

- [`Kwargs`][citry.Component.Kwargs] lists the `name=value` options. This
  card has one option, `accent`, which sets the border color.
- [`Slots`][citry.Component.Slots] lists the places where text or HTML can
  go. This card has one, `default`, for everything written between `<c-Card>`
  and `</c-Card>`.

Neither `accent` nor `default` has a fallback value, so you must provide both
when you use the card.

## Style the card

The [`css`][citry.Component.css] block belongs to the card. Citry adds it to
any page that renders the card.

The [`css_data()`][citry.Component.css_data] method passes the chosen accent
to that CSS as the variable `--accent`, and `var(--accent)` in the border rule
reads it.

`.demo-card` is ordinary CSS: it styles every matching element on the page.
Give component classes distinctive names so they do not style something else
by accident.

## Use it in a template

Inside another component's template, the card looks like this:

```citry-html
<c-Card accent="#8250df">
  <h2 class="demo-card__title">Welcome</h2>
  <p class="demo-card__body">
    Choose the accent color, then add any content you like.
  </p>
</c-Card>
```

`accent` makes the top border purple. The heading and paragraph go inside the
card because they sit between its opening and closing tags.

## Use it in Python

You can also create the card directly in Python. Save this as `render.py`
next to `component.py`:

```python
from component import Card

card = Card(
    accent="#8250df",
    slots={"default": "Build something useful."},
)
print(card)
```

The `slots` dictionary fills the default slot from Python. Run the file:

```sh
python render.py
```

Citry prints the card's HTML and the styles it needs. Shortened, the result
looks like this:

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

The real HTML has a few extra attributes that Citry uses. You do not need to
write them.

## Give each card a color

Several cards on one page share the same CSS rules, but each card keeps the
color you gave it.

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

Run `python two_cards.py`. Both cards use the same HTML and CSS, but one is
blue and the other orange, each with its own text.

## Leave out an input

If you forget the color, Citry cannot render the card:

```python
str(Card(slots={"default": "Where is my color?"}))
# TypeError: Card.Kwargs.__init__() missing ... 'accent'
```

Add `accent` and the card renders:

```python
str(
    Card(
        accent="#8250df",
        slots={"default": "Now the card has everything it needs."},
    )
)
```

Leaving out the default slot fails the same way. The error appears when the
card turns into HTML, at `str()` or `print()`, not when Python first runs
`Card(...)`.

!!! note "Type annotations do not check values at runtime"

    `accent: str` helps your editor and type checker, but it does not
    reject `accent=123` while your program runs. If values come from a
    form, an API, or another source you do not control, read
    [Inputs and validation](/concepts/inputs-and-validation/) to add
    runtime checks.

## Next steps

You now have a card that:

- asks for an accent color;
- places text or HTML where `<c-slot />` appears;
- can have a different color each time you use it; and
- reports an error when required information is missing.

You can [open the Card recipe](/examples/card/) to compare the component,
complete page, and live result. To continue, [use Python data in
components](/getting-started/data-in-components/).
