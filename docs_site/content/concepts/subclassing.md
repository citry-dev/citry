---
title: Subclassing components
description: How a child component inherits or overrides its parent's template, JS, CSS, and dependencies, and how to opt out or reuse parent logic.
---

# Subclassing components

As a project grows, you often end up with several components that share the same
markup or behavior. Instead of repeating yourself, you can put the shared parts in
one base component and subclass it, so each variant only writes what makes it
different. A citry component is an ordinary Python class, so you subclass
[`Component`][citry.Component] the usual way. A few rules govern how the template,
JS, CSS, and dependency declarations are inherited, and this page covers them. If
components themselves are new to you, start with
[Components](/concepts/components/).

## Template, JS, and CSS inheritance

A component declares its markup and primary assets in three inline-or-file pairs:

- `template` / `template_file`
- `js` / `js_file`
- `css` / `css_file`

Each pair is inherited as a single unit. If a child class sets **either** member
of a pair, that value is used and the parent's whole pair is ignored. So a child
that sets only `template_file` replaces the parent's inline `template`. Each pair
is decided on its own, so you can override the template while still inheriting the
JS and CSS.

```citry
from citry import Component

class BaseCard(Component):
    class Kwargs:
        content: str = ""

    template = """
      <div class="card">
        <div class="card-content">{{ content }}</div>
      </div>
    """
    css = """
      .card {
        border: 1px solid gray;
      }
    """
    js = """
      console.log('Base card loaded');
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"content": kwargs.content}

# Overrides the template, inherits the CSS and JS
class SpecialCard(BaseCard):
    template = """
      <div class="card special">
        <div class="card-content">* {{ content }} *</div>
      </div>
    """

# Overrides the template (from a file) and the CSS, inherits the JS
class CustomCard(BaseCard):
    template_file = "custom_card.html"
    css = """
      .card {
        border: 2px solid gold;
      }
    """
```

`SpecialCard` renders its own markup, while `SpecialCard.get_css()` and
`SpecialCard.get_js()` return the base card's CSS and JS unchanged. `CustomCard`
loads its template from a file, which replaces the parent's inline `template`, and
defines its own CSS, but still inherits the base card's JS.

Everything else is normal Python inheritance: both children also inherit the
`Kwargs` class and the `template_data` method from `BaseCard`.

## Dependencies inheritance

A component's secondary JS and CSS files (the ones the page inlines or links to)
live in a nested `Dependencies` class. These are inherited too, but the rule is
different from the pairs above: by default a child's dependencies **add to** the
parent's rather than replacing them. The `extend` attribute controls this:

- `extend = True` (the default) inherits the JS and CSS from the base classes'
  `Dependencies` and adds the child's own entries on top.
- `extend = False` inherits nothing; only the child's own entries are used.
- `extend = [SomeComponent, ...]` inherits from exactly those classes (and their
  bases), in the order given.

```citry
from citry import Component

class BaseModal(Component):
    template = """
      <div>Modal content</div>
    """

    class Dependencies:
        css = ["base_modal.css"]
        js = ["base_modal.js"]

# Inherits base_modal, then adds fancy_modal (extend defaults to True)
class FancyModal(BaseModal):
    class Dependencies:
        css = ["fancy_modal.css"]
        js = ["fancy_modal.js"]

# Only simple_modal; the base's dependencies are not inherited
class SimpleModal(BaseModal):
    class Dependencies:
        extend = False
        css = ["simple_modal.css"]
        js = ["simple_modal.js"]
```

`FancyModal.get_dependencies().js` lists both `base_modal.js` and
`fancy_modal.js`, while `SimpleModal.get_dependencies().js` lists only
`simple_modal.js`. Inherited entries come first, so a more specific class's styles
land later in the page and win ties by document order.

For the full `Dependencies` class (media types, serving files versus inlining
them, and how the files reach the page), see
[JS and CSS dependencies](/advanced/js-and-css-dependencies/).

## Opt out with None

Sometimes a child should inherit nothing for a given pair, without setting a real
template, JS, or CSS in its place. Set the attribute to `None` to opt out. This
works for each pair, and for the `Dependencies` class:

- `template` / `template_file`
- `js` / `js_file`
- `css` / `css_file`
- the `Dependencies` class (write `Dependencies = None`)

```citry
from citry import Component

class BaseForm(Component):
    class Kwargs:
        content: str = ""

    template = """
      <form>
        {{ content }}
      </form>
    """
    css = """
      form {
        gap: 1rem;
      }
    """
    js = """
      console.log('form ready');
    """

    class Dependencies:
        js = ["form.js"]

    def template_data(self, kwargs: Kwargs, slots):
        return {"content": kwargs.content}

# Reuses the parent's template and CSS, but has no JS and no dependencies
class ContactForm(BaseForm):
    js = None
    Dependencies = None
```

`ContactForm` inherits the base form's `template` and `css`, but
`ContactForm.get_js()` returns `None` and `ContactForm.get_dependencies()` is
empty. Setting `js = None` is different from leaving `js` out: leaving it out
inherits the parent's JS, while `None` says "no JS here".

## Normal Python inheritance

Anything that is not one of the asset pairs or the `Dependencies` class follows
ordinary Python inheritance. You can call `super().template_data(...)` to build on
the parent's data instead of rewriting it, and you can override any helper method
the parent calls.

```citry
from citry import Component

class BaseForm(Component):
    template = """
      <form>
        <label>{{ label }}</label>
        <button type="submit">{{ submit_text }}</button>
      </form>
    """

    def template_data(self, kwargs, slots):
        return {
            "label": self.field_label(),
            "submit_text": "Submit",
        }

    def field_label(self):
        return "Your data"

class ContactForm(BaseForm):
    # Reuse the parent's data, then override one value
    def template_data(self, kwargs, slots):
        data = super().template_data(kwargs, slots)
        data["submit_text"] = "Send message"
        return data

    # Replace a helper the parent's template_data calls
    def field_label(self):
        return "Your email"
```

`ContactForm` renders the same form, but the button reads "Send message" and the
label reads "Your email". The label changes even though `ContactForm` never sets
`label` itself: the parent's `template_data` calls `self.field_label()`, and here
`self` is a `ContactForm`, so the overridden helper runs.
