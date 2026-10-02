---
title: Rendering
description: Turn a component and everything inside it into HTML, add values for the whole page, and choose where JavaScript and CSS go.
---

# Rendering

Rendering turns a component, and every component inside it, into an HTML
string you can send to the browser. For most pages, `str(MyPage(...))` is
all you need.

Split rendering into its steps when you need more control: to give every
component in the page a value such as the current user, to choose where the
page's JavaScript and CSS go, or to keep a rendered result and use it later.

## Render a component to HTML

```citry
from citry import Component


class Greeting(Component):
    class Kwargs:
        name: str

    template = """
      <p>Hello, {{ name }}!</p>
    """


html = str(Greeting(name="Ada"))
```

`str(...)` runs all the rendering steps below with their default options.

## Run the rendering steps yourself

`str(...)` does three things, which you can also do one at a time:

```python
element = Greeting(name="Ada")
rendered = element.render()
html = rendered.serialize()
```

1. Calling the class creates a [`CitryElement`][citry.CitryElement]. It
   records which component to render, with its inputs and slot content,
   but renders nothing yet.
2. [`render()`][citry.CitryElement.render] renders the component and
   everything inside it. It returns a [`CitryRender`][citry.CitryRender],
   which holds the result together with the JavaScript and CSS those
   components need.
3. [`serialize()`][citry.CitryRender.serialize] turns that result into the
   final HTML string and inserts the JavaScript and CSS.

## Add values for one whole render

Pass `template_globals` to `render()` to give every template in the page
the same values. This suits values that belong to the request, such as the
current user's name, the locale, or a request ID:

```citry
from citry import Component


class PageFooter(Component):
    template = """
      <footer>{{ site_name }}</footer>
    """


class AccountPage(Component):
    template = """
      <main>Account</main>
      <c-page-footer />
    """


rendered = AccountPage().render(
    template_globals={"site_name": "Citry"},
)
html = rendered.serialize()
```

Both `AccountPage` and `PageFooter` can read `site_name`, and so can slot
content and any other component inside this render. Later renders do not
see it.

To set a value for every render, pass `template_globals` to your
[`Citry`][citry.Citry] instance instead. When the same name is set in more
than one place, the later entry in this list wins:

1. the Citry instance's `template_globals`;
2. the `template_globals` passed to this `render()` call;
3. the value the component's own `template_data()` returns.

A component's own data therefore always wins over a global value with the
same name.

## Pass data to child components

A child component does not see the variables its parent's
[`template_data()`][citry.Component.template_data] returns. Each component
builds its own template variables from its own inputs, so a component
behaves the same wherever you place it.

Pass the value to the child as an input:

```citry-html
<main>
  <h1>{{ account_name }}</h1>
  <c-account-summary c-name="account_name" />
</main>
```

Choose by how widely the value is needed:

- one child needs it: pass it as an input, as above;
- many components deep in the page need it: use
  [provide and inject](/concepts/provide-and-inject/);
- the parent supplies markup for the child to place: use
  [slots](/concepts/slots/);
- every template in the page needs it: use `template_globals`.

## Share a Python object with the whole page

Pass `provides` to `render()` when the page and the components inside it
need the same Python object, such as the request, but it should not become
a template variable:

```python
rendered = AccountPage().render(
    provides={"request": request},
)
```

Any component in this render can read it with
[`inject()`][citry.Component.inject].
[Provide and inject](/concepts/provide-and-inject/) explains the details.

## Choose where JavaScript and CSS go

`str(...)` places the page's JavaScript and CSS in the default way. When
the HTML goes somewhere else, call `serialize()` yourself and choose a
`deps_strategy`:

```python
rendered = Greeting(name="Ada").render()

html = rendered.serialize(deps_strategy="ignore")
```

[Asset placement](/advanced/asset-placement/) explains the `document`,
`simple`, and `ignore` options, and
[HTML fragments](/advanced/html-fragments/) covers `fragment`, for HTML
that you insert into a page that is already open.

To return the HTML from a web route, see the
[Web frameworks guide](/web-frameworks/).

## Render the same component more than once

A `CitryElement` only describes what to render, so you can render it as
many times as you like. Each `render()` call starts fresh:

```python
greeting = Greeting(name="Ada")

first = greeting.render()
second = greeting.render()

assert first is not second
```

You can also insert the same element in two places in a template. Citry
renders it separately in each place.

A `CitryRender` is one finished result. You can serialize it as often as you
like, and you get the same HTML each time:

```python
rendered = Greeting(name="Ada").render()

assert rendered.serialize() == rendered.serialize()
```

!!! warning "Insert a rendered result in only one place"

    Inserting the same `CitryRender` in two places in a page raises
    `RuntimeError` when the page is serialized. To show a component twice,
    keep the `CitryElement` and insert that instead.
