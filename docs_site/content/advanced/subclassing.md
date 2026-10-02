---
title: Subclassing components
description: Reuse a component contract while changing its template, browser code, styles, dependencies, or Python behavior.
---

# Subclassing components

Sometimes you need several versions of one component: a card and a linked
card, a dialog and a confirm dialog. They take the same inputs and behave
the same way, and differ only in one part, such as the template or the
styles.

Subclass the component for this. Put the shared parts on a base class, and
let each child change only what makes it different.

When the two pieces should change independently of each other, use one
inside the other's template instead. A subclass also inherits every future
change to its parent.

## Reuse inputs and behavior

A child inherits its parent's inputs, methods, template, JavaScript, and
CSS. Override only the method that differs:

```citry
from citry import Component


class Message(Component):
    class Kwargs:
        text: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, str]:
        return {"message": self.format_message(kwargs.text)}

    def format_message(self, text: str) -> str:
        return text

    template = """
      <p>{{ message }}</p>
    """


class LoudMessage(Message):
    def format_message(self, text: str) -> str:
        return text.upper()
```

`LoudMessage(text="Saved")` renders `<p>SAVED</p>`. The inherited
`template_data()` calls the child's `format_message()`.

## Add inputs in a child

Declare a nested `Kwargs` on the child with only the new fields. Citry
combines them with the parent's fields, so `SignedMessage` takes both
`text` and `author`:

```citry
class SignedMessage(Message):
    class Kwargs:
        author: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, str]:
        data = super().template_data(kwargs, slots)
        data["message"] += f" ({kwargs.author})"
        return data
```

The child calls `super().template_data()` and adjusts the result.

Citry combines these nested declarations the same way:

- [`Kwargs`][citry.Component.Kwargs] and [`Slots`][citry.Component.Slots],
  which describe the inputs;
- [`TemplateData`][citry.Component.TemplateData],
  [`JsData`][citry.Component.JsData], and
  [`CssData`][citry.Component.CssData], which describe the data methods
  return;
- [`State`][citry.Component.State] and [`Events`][citry.Component.Events],
  from [server events](/events/).

To start a child without the parent's declaration, set it to `None`:

```citry
class FreeformMessage(Message):
    Kwargs = None
```

`FreeformMessage` declares no `Kwargs`, so it accepts any inputs.

## Replace the template, JavaScript, or CSS

A component's template, JavaScript, and CSS can each be written inline or
loaded from a file:

- [`template`][citry.Component.template] or `template_file`;
- [`js`][citry.Component.js] or `js_file`;
- [`css`][citry.Component.css] or `css_file`.

Each line is one pair. A child that sets neither member of a pair inherits
the parent's. A child that sets either member replaces the whole pair, and
still inherits the other two pairs:

```citry
from citry import Component


class BaseCard(Component):
    class Kwargs:
        title: str

    template = """
      <article class="card" ref="root">
        <h2>{{ title }}</h2>
      </article>
    """
    js = """
      $component(({ component }) => {
        const root = component.$refs.root;
        if (root instanceof HTMLElement) {
          root.dataset.ready = "true";
        }
      });
    """
    css = """
      .card {
        border: 1px solid currentColor;
      }
    """


class LinkedCard(BaseCard):
    template_file = "linked_card.html"
```

`LinkedCard` uses its own template file in place of `BaseCard`'s inline
`template`, and keeps `BaseCard`'s JavaScript and CSS.

To drop one of them in a child, set it to `None`:

```citry
class StaticCard(BaseCard):
    js = None
```

`StaticCard` has no JavaScript. Leaving `js` out would inherit it.

## Add scripts and stylesheets in a child

The nested `Dependencies` class lists extra script and stylesheet files a
component needs. A child's `Dependencies` adds to its parents' lists rather
than replacing them. Parent entries come first, so a child's stylesheet
loads later and wins when two CSS rules are equally specific:

```citry
from citry import Component, SlotInput


class BaseDialog(Component):
    class Slots:
        default: SlotInput

    class Dependencies:
        js = ["/static/dialog.js"]
        css = ["/static/dialog.css"]

    template = """
      <dialog>
        <c-slot />
      </dialog>
    """


class ConfirmDialog(BaseDialog):
    class Dependencies:
        css = ["/static/confirm-dialog.css"]
```

`ConfirmDialog` loads `dialog.js`, `dialog.css`, and then
`confirm-dialog.css`.

Set `extend` on `Dependencies` to choose which parents contribute:

- `extend = True`, the default, includes the parent classes;
- `extend = False` includes only this class's own entries;
- `extend = [CompactTheme, BrandTheme]` includes exactly those classes and
  their own parents, in the order written.

`Dependencies = None` gives the child no extra files, not even its
parents'.

[Dependency files](/advanced/dependency-files/) covers the forms an entry
can take, local files, URLs, and how the files are served.

## Rules for duplicates and conflicts

### Mixing schema styles across a family

Plain classes, dataclasses, named tuples, Pydantic models, and the other
supported schema styles do not all combine the same way. Citry raises an
error when the child class is defined if the parent's and child's styles
cannot be combined. See
[Inputs and validation](/concepts/inputs-and-validation/) before mixing
them.

### Setting both members of a pair

Setting both `template` and `template_file` to non-empty values on the
same class raises `ValueError` when the class is defined. The same applies
to `js` and `js_file`, and `css` and `css_file`.

### Listing the same dependency twice

A dependency listed more than once is loaded once, at its first position.
For a script, the first entry's tag attributes are used, and a later
duplicate cannot add more. The same holds for a stylesheet listed again
under the same `media` key. Listing one stylesheet under two different
`media` keys raises `ValueError` when the page is rendered to HTML.
