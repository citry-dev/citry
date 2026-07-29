---
title: Typing and validation
url: https://citry.dev/v/0.3.1/concepts/typing-and-validation/
description: "Declare component inputs with class Kwargs and class Slots so typos and missing or unknown props are caught early rather than in production."
---
# Typing and validation

When you pass a prop to a component, a small typo is easy to make and hard to
catch. Without any declaration, `<c-button lable="Save" />` looks fine until a
user hits the page and the label is blank. Citry lets you declare what a
component accepts, so that mistake can be caught rather than becoming a silent
bug in production.

You declare inputs with two nested classes on your component: `class Kwargs:`
for the attributes it accepts, and `class Slots:` for the slots it fills.
Together they form the component's contract.

## Declare the props a component accepts

Add a `class Kwargs:` to your [Component](/v/0.3.1/reference/component/#citry-component) and list each prop
with its type. This is the set of attributes the component knows about.


```citry
from citry import Component


class Button(Component):
    class Kwargs:
        label: str
        variant: str = "primary"

    template = """
      <button c-class="'btn btn-' + variant">
        {{ label }}
      </button>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "label": kwargs.label,
            "variant": kwargs.variant,
        }
```


`label` has no default, so it is required. `variant` has a default, so it is
optional. Anything not listed here is not part of the contract.

## The wrong attempt and the fix

Say you reach for the component and mistype an attribute name:


```html
<c-button lable="Save" />
```


Here `lable` is not the declared name, and the required `label` prop is never
supplied, so the component does not receive the value it needs.

The fix is to use the declared name:


```html
<c-button label="Save" />
```


The value of declaring inputs shows up here: the mismatch is visible against
the component's declared contract instead of surfacing only as a blank button
for a visitor later.

## Default values for lists and dicts

A default like `variant: str = "primary"` above is a plain value, and that is
all you need for a string, a number, or a boolean. A list or dict default takes
one more step. Behind the scenes Citry turns `class Kwargs` into a dataclass,
and a dataclass rejects a mutable value (a list, dict, or set) written directly
as a default:


```citry
from citry import Component


class TodoList(Component):
    class Kwargs:
        items: list[str] = []  # error when the class is defined
```


Defining this component raises the error `mutable default ... is not allowed: use default_factory`.
The reason is that a single list written here would be shared by every render of
the component, so an item added in one place would appear in all of them. Citry
catches this at definition time instead of letting it become a confusing bug.

Give the field a factory that builds a fresh value each time, with
`dataclasses.field`:


```citry
from dataclasses import field

from citry import Component


class TodoList(Component):
    template = """
      <ul>
        {{ shown }}
      </ul>
    """

    class Kwargs:
        items: list[str] = field(default_factory=list)

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "shown": ", ".join(kwargs.items),
        }
```


`field(default_factory=...)` runs the factory for every render, so each render
gets its own list. Pass `list` or `dict` for an empty default, or a small
function for a preset, such as `field(default_factory=lambda: ["first"])`.

A default only fills in when the attribute is left out. Passing `None` on purpose
keeps `None` as the value; it does not fall back to the default. So
`TodoList(items=None)` sets `items` to `None`, not to an empty list. If an
omitted value and an explicit `None` should behave the same, handle `None` in
your data method.

## Declare the slots a component fills

Slots work the same way. Add a `class Slots:` listing each slot the component
renders.


```citry
from citry import Component


class Card(Component):
    class Slots:
        header: str
        body: str

    template = """
      <div class="card">
        <div class="card-header">
          <c-slot name="header" />
        </div>
        <div class="card-body">
          <c-slot name="body" />
        </div>
      </div>
    """
```


Declaring slots documents which slots the component fills, so a misspelled or
unexpected slot name stands out against the contract the same way a prop does.
See [Slots](/v/0.3.1/concepts/slots/) for how to fill and default slot content.

## Why declare inputs at all

Declaring `class Kwargs` and `class Slots` writes down the component's
contract, so common mistakes have something to check against:

- A **typo in a prop or slot name** no longer matches a declared input.
- A **missing required prop** (one with no default) is visible against the
  declaration.
- An **unexpected prop** stands out against the set the component declares.

The trade is small: a few lines of declaration up front. For how components
fit together more broadly, see [Components](/v/0.3.1/concepts/components/) and
[Use data in components](/v/0.3.1/getting-started/data-in-components/).

## Type the data your methods return

Declaring inputs is the common case, and it is where most of the value is. You
can go further and type the data a component hands on: the variables its template
reads, and the values passed to its JavaScript and CSS.

`template_data` returns the variables the template sees. Declare a matching
`class TemplateData` and Citry checks the returned data against it on every
render, so a missing or misspelled key fails the render instead of showing up as
a blank value on the page.


```citry
from citry import Component


class Price(Component):
    template = """
      <p class="price">{{ formatted }}</p>
    """

    class Kwargs:
        amount: float
        currency: str = "USD"

    class TemplateData:
        formatted: str

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "formatted": f"{kwargs.amount:.2f} {kwargs.currency}",
        }
```


The template reads only `formatted`, and `TemplateData` says so. You can return
the plain dict as above, or build the type and return it directly with
`Price.TemplateData(formatted=...)`.

The data for a component's JavaScript and CSS is typed the same way, with
`class JsData` for `js_data` and `class CssData` for `css_data`:


```citry
from citry import Component


class LikeButton(Component):
    template = """
      <button class="like">Like</button>
    """

    js = """
      console.log("like button ready")
    """

    class JsData:
        count: int

    def js_data(self, kwargs, slots):
        return {
            "count": 0,
        }
```


See [JS and CSS dependencies](/v/0.3.1/advanced/js-and-css-dependencies/) for how a component
uses that data in the browser.

## Choose how a type is stored

When you write `class Kwargs` as a plain annotated class, Citry turns it into a
dataclass with `slots=True` for you. You can choose a different backing type by
having the class inherit one: a `NamedTuple`, a dataclass you decorate
yourself, or a validating model such as a Pydantic model. An explicitly
decorated dataclass keeps the options you chose. Citry uses whichever you
provide, for any of the typed classes.

The choice decides how strict the check is. A plain class, a dataclass, or a
`NamedTuple` checks only that the declared fields are present, so a number given
where a string is expected still passes. A Pydantic model also checks each
value's type and rejects a wrong one. Reach for a model when you want the values
validated, not just named.


```citry
from typing import NamedTuple

from citry import Component


class Tag(Component):
    template = """
      <span class="tag">{{ label }}</span>
    """

    class Kwargs(NamedTuple):
        label: str
        rounded: bool = False

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "label": kwargs.label,
        }
```


## Declare a component that takes no inputs

A component that accepts no props can put that in its contract. Give it a
`Kwargs` class with an empty body:


```citry
from citry import Component


class Divider(Component):
    template = """
      <hr class="divider" />
    """

    class Kwargs:
        pass
```


Now passing any attribute to `<c-divider>` is caught as an error, because the
component declares no props. Leaving `Kwargs` off entirely does the opposite: the
component then accepts any attribute without checking. Use the empty class when
"no inputs" is part of what the component promises. An empty `class Slots` works
the same way for a component that fills no slots.

## Reuse types when subclassing

Each type is a normal class attribute, so a subclass keeps the ones it does not
touch and overrides only the ones it does. A child component can inherit its
parent's `Kwargs`, `Slots`, and data methods, and change just what it needs.


```citry
from citry import Component


class Button(Component):
    template = """
      <button class="btn">{{ label }}</button>
    """

    class Kwargs:
        label: str

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "label": kwargs.label,
        }


class LoudButton(Button):
    def template_data(self, kwargs: "Button.Kwargs", slots):
        data = super().template_data(kwargs, slots)
        data["label"] = data["label"].upper()
        return data
```


`LoudButton` reuses `Button`'s template and `Kwargs`, and changes only the data
method, calling `super().template_data(...)` to build on the parent's result. One
detail lives in the type hint: when a method uses a type it inherited, rather than
one defined in its own body, write the hint as the full name in quotes,
`"Button.Kwargs"`. A subclass that declares its own `Kwargs` can use the bare
name. See [Subclassing](/v/0.3.1/concepts/subclassing/) for more on extending components.