---
title: Testing components
url: https://citry.dev/v/0.4.2/advanced/testing/
description: "Test rendered HTML, input contracts, server behavior, and browser interactions."
---
# Testing components

Test each behavior at the smallest useful layer. Python tests are quick and
good at checking component input and rendered HTML. A host framework's test
client checks HTTP integration. A browser test proves that Alpine, Citry's
client runtime, and real DOM events work together.

## Give each test its own Citry instance

A component registers when Python defines its class. If tests define temporary
components on the shared default engine, their names remain registered for
later tests and may collide.

Create a fresh [`Citry`](/v/0.4.2/reference/citry/#citry-citry) instance instead:


```citry
from citry import Citry, Component


def test_greeting():
    app = Citry(autodiscover=False)

    class Greeting(Component):
        class Kwargs:
            name: str

        citry = app

        template = """
          <p>Hello {{ name }}!</p>
        """

    html = str(Greeting(name="World"))

    assert "Hello World!" in html
```


Set `autodiscover=False` when the test defines every component it needs. This
keeps the test independent of project directories and imports.

For several tests, put the engine in a fixture and let each test define the
components it needs on that engine:


```python
import pytest
from citry import Citry


@pytest.fixture
def app():
    return Citry(autodiscover=False)
```


## Assert the result the reader can observe

Prefer focused checks for text, attributes, and ordering:


```python
html = str(Badge(label="Ready", tone="success"))

assert ">Ready<" in html
assert 'class="badge badge--success"' in html
```


Citry may add attributes needed by its browser runtime. Those attributes are
implementation details, so avoid exact comparisons against the entire HTML
string unless the exact serialization is the behavior under test.

An HTML parser can make structural assertions easier when whitespace and
attribute order do not matter:


```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
badge = soup.select_one(".badge")

assert badge is not None
assert badge.get_text(strip=True) == "Ready"
```


Use whichever parser your application already depends on. Citry does not
require Beautiful Soup for tests.

## Test inputs and slots

Render representative values, defaults, and boundary cases. Also check that
invalid calls fail in the way your public component contract promises:


```citry
import pytest
from citry import Citry, Component, SlotInput


def test_notice_requires_a_message():
    app = Citry(autodiscover=False)

    class Notice(Component):
        class Kwargs:
            message: str

        class Slots:
            actions: SlotInput | None = None

        citry = app

        template = """
          <aside>
            <p>{{ message }}</p>
            <c-slot name="actions" />
          </aside>
        """

    with pytest.raises(TypeError):
        str(Notice())
```


Test slot content through the public `slots` mapping:


```python
html = str(
    Notice(
        message="Saved",
        slots={"actions": "Undo"},
    )
)

assert "Saved" in html
assert "Undo" in html
```


## Test several components together

A component can render registered children only when they belong to the same
engine. Define the small component family on one test engine and render the
outer component:


```citry
from citry import Citry, Component


def test_profile_card_contains_the_avatar():
    app = Citry(autodiscover=False)

    class Avatar(Component):
        class Kwargs:
            name: str

        citry = app

        template = """
          <span class="avatar">{{ name[:1] }}</span>
        """

    class ProfileCard(Component):
        class Kwargs:
            name: str

        citry = app

        template = """
          <article>
            <c-avatar c-name="name" />
            <h2>{{ name }}</h2>
          </article>
        """

    html = str(ProfileCard(name="Ada"))

    assert 'class="avatar"' in html
    assert ">Ada</h2>" in html
```


This checks composition, input forwarding, template lookup, and final output
without depending on an HTTP server.

## Choose the right test for interactive behavior

Rendering in Python proves which HTML, bindings, and assets Citry produces. It
does not execute Alpine or Citry's browser runtime.

- Use a Python render test for component inputs and initial HTML.
- Use your framework's test client for mounted Citry routes, event requests,
  response status, and returned actions.
- Use a browser test for clicks, reactive state, focus, DOM updates, and event
  bubbling.

For server events, keep the handler's business logic in ordinary Python
functions when practical. Test those functions directly, then add a smaller
integration test for the Citry event boundary. See
[Events](/v/0.4.2/events/) and [Web frameworks](/v/0.4.2/web-frameworks/).

For browser behavior, exercise the page as a person would: click the visible
control and assert the visible result. Avoid reaching into Citry's internal DOM
attributes or JavaScript registries.

## Related reference

- [`Citry`](/v/0.4.2/reference/citry/#citry-citry)
- [`Component`](/v/0.4.2/reference/component/#citry-component)
- [`CitryElement`](/v/0.4.2/reference/rendering/#citry-citryelement)
- [Rendering](/v/0.4.2/concepts/rendering/)
- [Alpine in components](/v/0.4.2/syntax/alpine/)