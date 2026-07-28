---
title: Testing components
description: Test citry components in isolation by giving each test its own Citry instance, then rendering and asserting on the HTML.
---

# Testing components

Testing a citry component is mostly rendering it and checking the HTML. Calling
a component returns a [`CitryElement`][citry.CitryElement], and `str()` on it
produces the final HTML (see [Rendering](/concepts/rendering/)), so a test can
render and assert in a couple of lines. If the component is one you have already
defined and imported, that is the whole story: import it, render it, assert on
the output.

Isolation matters when a test defines its own components. A component registers
itself (see [Registration](/concepts/registration/)) with a
[`Citry`][citry.Citry] instance when the class is defined, and by default that
is the shared default instance ([`citry`][citry.citry]). Define throwaway
components on that shared instance across many tests and they pile up: a name
from one test is still registered in the next, and two tests that both define a
`Card` clash with an [`AlreadyRegistered`][citry.AlreadyRegistered] error. Give
each test its own [`Citry`][citry.Citry] instance and the problem goes away.

## Give each test its own Citry instance

Construct a fresh [`Citry`][citry.Citry] inside the test and point the component
at it with the `citry` class attribute. Define the component inside the test
function too, so it registers with that test's instance and is gone once the
test returns.

```citry
from citry import Citry, Component

def test_greeting():
    app = Citry()

    class Greeting(Component):
        citry = app
        template = """
          <p>Hello {{ name }}!</p>
        """

        class Kwargs:
            name: str

        def template_data(self, kwargs: Kwargs, slots):
            return {"name": kwargs.name}

    assert "Hello World!" in str(Greeting(name="World"))
```

`Greeting(name="World")` composes the component into a
[`CitryElement`][citry.CitryElement]; `str()` renders it and serializes the
result to HTML. Because `app` is brand new, no component from another test is
registered on it, and the `Greeting` class disappears when the test returns.

## Assert on the HTML you care about

You might reach for an exact match:

```python
assert str(Greeting(name="World")) == "<p>Hello World!</p>"   # fails
```

This fails, because the rendered HTML carries two things your literal string
does not. First, it keeps the whitespace from your `template`, the newlines and
indentation you wrote. Second, citry adds a `data-cid-<id>` marker to each
component's root element, to record which component produced which part of the
page:

```html
<p data-cid-cbgnc0d00="">Hello World!</p>
```

The id in that marker changes on every render, so no fixed string will match it.
The robust approach is to assert on the content you care about with `in`:

```python
html = str(Greeting(name="World"))
assert "Hello World!" in html
```

## Use a pytest fixture

Writing `app = Citry()` at the top of every test gets repetitive. A pytest
fixture hands each test a fresh instance, and because pytest calls the fixture
again for every test, the isolation is automatic.

```citry
import pytest
from citry import Citry, Component

@pytest.fixture
def app():
    return Citry()

def test_button_label(app):
    class Button(Component):
        citry = app
        template = """
          <button>{{ label }}</button>
        """

        class Kwargs:
            label: str

        def template_data(self, kwargs: Kwargs, slots):
            return {"label": kwargs.label}

    assert "Save" in str(Button(label="Save"))

def test_registrations_do_not_leak(app):
    # This test's app is fresh, so a Button registered on
    # another test's instance was never added here.
    assert not app.has("button")
```

The `app.has("button")` call asks that instance's registry whether a component
is registered under the name. On a fresh instance it is `False` until a
component is registered under that name.

## Match the whole string with a stable id

When you do want to compare the entire output, make the marker predictable by
passing an `id_generator` to [`Citry`][citry.Citry], and strip the template's
surrounding whitespace. The `id_generator` is any callable that returns a
unique string made from lowercase ASCII letters, digits, hyphens, and
underscores; a counter hands out `c1`, `c2`, and so on in render order. The
lowercase restriction matters because Citry embeds the value in an HTML
attribute name, and HTML attribute names are case-insensitive.

```citry
import itertools
from citry import Citry, Component

def test_card_html():
    ids = itertools.count(1)
    app = Citry(id_generator=lambda: f"c{next(ids)}")

    class Card(Component):
        citry = app
        template = """
          <div class="card">{{ title }}</div>
        """

        class Kwargs:
            title: str

        def template_data(self, kwargs: Kwargs, slots):
            return {"title": kwargs.title}

    html = str(Card(title="Hi")).strip()
    assert html == '<div class="card" data-cid-c1="">Hi</div>'
```

Prefer the `in` check unless you specifically need the whole string. It does not
tie your test to the marker or to your template's indentation.

## Testing slots and typed inputs

Slot fills pass through the reserved `slots` argument, so a test can hand a slot
its content and assert on the result the same way. The component below renders
its `body` slot with the built-in `<c-slot>` tag.

```citry
def test_layout_slot(app):
    class Layout(Component):
        citry = app
        template = """
          <section>
            <c-slot name="body" />
          </section>
        """

    html = str(Layout(slots={"body": "Page content"}))
    assert "Page content" in html
```

A component with a `Kwargs` class checks its inputs when it renders (see
[Typing and validation](/concepts/typing-and-validation/)), so asserting that a
bad call is rejected is a good test of the contract. Composing the element does
not validate; rendering does, so render inside the `pytest.raises` block.

```citry
def test_missing_required_kwarg(app):
    class Greeting(Component):
        citry = app
        template = """
          <p>Hello {{ name }}!</p>
        """

        class Kwargs:
            name: str

        def template_data(self, kwargs: Kwargs, slots):
            return {"name": kwargs.name}

    with pytest.raises(TypeError):
        str(Greeting())   # no name passed
```

## Isolation without a test decorator

The pattern on this page is deliberately plain Python: a fresh
[`Citry`][citry.Citry] per test, directly or through a fixture. A single
decorator that wraps a test in its own instance, so you would not write the
fixture yourself, is a natural convenience and a good candidate for a future
release. Until then, the fixture above is the recommended way to keep tests
isolated, and [contributions](/community/contributing/) toward the helper are
welcome.
