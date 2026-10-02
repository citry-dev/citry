---
title: Testing components
description: Test rendered HTML, input contracts, server behavior, and browser interactions.
---

# Testing components

Most component tests render the component in Python and check the HTML.
These tests are fast and need no server or browser. Reach for slower tests
only for what Python rendering cannot show:

- a plain Python test checks inputs, slots, and the rendered HTML;
- your web framework's test client checks Citry routes and server events
  over HTTP: the request, the status code, and the actions a handler
  returns;
- a browser test checks clicks, reactive state, focus, and page updates.

## Isolate each test

Defining a component registers it with a [`Citry`][citry.Citry] instance.
If a test defines a component on the shared default instance, the second
run of that code, such as the next case of a parametrized test, raises
`AlreadyRegistered`.

Create a new `Citry` instance in each test instead:

```citry
from citry import Citry, Component


def test_greeting():
    app = Citry(autodiscover=False)

    class Greeting(Component):
        citry = app

        class Kwargs:
            name: str

        template = """
          <p>Hello {{ name }}!</p>
        """

    greeting = Greeting(name="World")
    html = str(greeting)

    assert "Hello World!" in html
```

`autodiscover=False` stops Citry from importing your project's component
files, so the test uses only the components it defines.

To share the setup across tests, put the instance in a fixture:

```python
import pytest
from citry import Citry


@pytest.fixture
def app():
    return Citry(autodiscover=False)
```

## Check what users see

Check the text, attributes, and order that matter:

```python
badge = Badge(label="Ready", tone="success")
html = str(badge)

assert ">Ready<" in html
assert 'class="badge badge--success"' in html
```

Avoid comparing the whole HTML string. Citry adds attributes for its
browser code, and those can change between versions. Compare the full
string only when the exact output is what you are testing.

An HTML parser helps when whitespace and attribute order should not
matter:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
badge = soup.select_one(".badge")

assert badge is not None
assert badge.get_text(strip=True) == "Ready"
```

Any parser works. Citry does not need Beautiful Soup.

## Test inputs and slots

Render typical values, defaults, and edge values. Also check that a wrong
call fails the way you expect. Here a missing required input raises
`TypeError`:

```citry
import pytest
from citry import Citry, Component, SlotInput


def test_notice_requires_a_message():
    app = Citry(autodiscover=False)

    class Notice(Component):
        citry = app

        class Kwargs:
            message: str

        class Slots:
            actions: SlotInput | None = None

        template = """
          <aside>
            <p>{{ message }}</p>
            <c-slot name="actions" />
          </aside>
        """

    notice = Notice()
    with pytest.raises(TypeError):
        str(notice)
```

Fill slots with the `slots` mapping:

```python
notice = Notice(
    message="Saved",
    slots={"actions": "Undo"},
)
html = str(notice)

assert "Saved" in html
assert "Undo" in html
```

## Test nested components

A component's template can use only components registered with the same
`Citry` instance. Define the parent and its children on one test instance,
then render the parent:

```citry
from citry import Citry, Component


def test_profile_card_contains_the_avatar():
    app = Citry(autodiscover=False)

    class Avatar(Component):
        citry = app

        class Kwargs:
            name: str

        template = """
          <span class="avatar">{{ name[:1] }}</span>
        """

    class ProfileCard(Component):
        citry = app

        class Kwargs:
            name: str

        template = """
          <article>
            <c-avatar c-name="name" />
            <h2>{{ name }}</h2>
          </article>
        """

    card = ProfileCard(name="Ada")
    html = str(card)

    assert 'class="avatar"' in html
    assert ">Ada</h2>" in html
```

This checks that `ProfileCard` finds `Avatar`, passes it the name, and
renders both, all without an HTTP server.

## Test browser behavior

A Python render shows the HTML, bindings, and assets Citry sends to the
browser. It does not run Vue or Citry's browser code, so it cannot show
what happens after a click. Use the test client and browser tests listed
at the top of this page for that.

For [server events](/events/), keep the business logic in ordinary Python
functions and test those directly. Then add one smaller test that calls
the event over HTTP. [Web frameworks](/web-frameworks/) shows how Citry
routes are added to each framework.

In a browser test, act as a person would: click the visible control, then
check the visible result. Do not depend on Citry's own DOM attributes or
JavaScript objects, which can change between versions.

## Related reference

- [`Citry`][citry.Citry]
- [`Component`][citry.Component]
- [`CitryElement`][citry.CitryElement]
- [Rendering](/concepts/rendering/)
- [Vue in templates](/syntax/vue/)
