---
title: Components
description: Turn part of a page into a reusable Python class with its own inputs, content, and markup.
---

# Components

When the same piece of UI appears on several pages, such as a card, a
button, or a page header, write it once as a component and reuse it. A Citry
component is a Python class based on [`Component`][citry.Component]. It
takes inputs, and its template turns them into HTML.

## Write a component

Set [`template`][citry.Component.template] to the markup the component
produces:

```citry
from citry import Component


class Welcome(Component):
    template = """
      <section class="welcome">
        <h1>Welcome!</h1>
      </section>
    """


welcome = Welcome()
html = str(welcome)
```

`str(...)` renders the component and returns the HTML as a string.

## Pass values in

List the keyword arguments a component accepts in a nested
[`Kwargs`][citry.Component.Kwargs] class. The template can read each one by
its name:

```citry
from citry import Component


class Welcome(Component):
    class Kwargs:
        name: str
        message_count: int = 0

    template = """
      <section class="welcome">
        <h1>Welcome, {{ name }}!</h1>
        <p>You have {{ message_count }} new messages.</p>
      </section>
    """


welcome = Welcome(name="Ada", message_count=3)
html = str(welcome)
```

`name` is required, and `message_count` defaults to `0`. Citry rejects a
missing required value or a name the class does not list.
[Inputs and validation](/concepts/inputs-and-validation/) covers defaults,
slots, and type checking.

A component without `Kwargs` also passes its keyword arguments to the
template, but accepts any name.

!!! note "`slots` is a reserved keyword argument"

    `Modal(slots={...})` passes content for the component's slots, not an
    input named `slots`. See [Slots](/concepts/slots/#fill-slots-from-python).

## Compute template values

When the template needs a value that is not an input as written, override
[`template_data()`][citry.Component.template_data] and return the values
the template should see. This component turns a list of messages into a
count:

```citry
from citry import Component


class InboxSummary(Component):
    class Kwargs:
        name: str
        messages: list[str]

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, object]:
        return {
            "name": kwargs.name,
            "message_count": len(kwargs.messages),
        }

    template = """
      <section class="inbox-summary">
        <h2>{{ name }}'s inbox</h2>
        <p>{{ message_count }} new messages</p>
      </section>
    """
```

Once you override `template_data()`, the template gets the values it returns
in place of the inputs. Here the template cannot read `messages`.

With a `Kwargs` class, read inputs as attributes, such as `kwargs.name`.
Without one, `kwargs` is a dictionary, so read `kwargs["name"]`.

## Nest components

Inside a template, a `<c-*>` tag renders another component. Write the class
name after `c-`, so `Welcome` is `<c-Welcome>`:

```citry
from citry import Component


class ProfilePage(Component):
    class Kwargs:
        user_name: str

    template = """
      <main>
        <c-Welcome c-name="user_name" />
      </main>
    """
```

A plain attribute such as `name="Ada"` passes a string. The `c-` prefix in
`c-name="user_name"` passes the value of a Python expression instead.

In a component tag, letter case does not matter after `c-`, and you can
also write a class name of several words with hyphens between the words.
`<c-TaskCard>`, `<c-taskcard>`, and `<c-task-card>` all render `TaskCard`.
[Registration](/concepts/registration/) explains how Citry finds the class
for a tag.

You can also build a component in Python and pass it in as a value. The
template inserts it with `{{ ... }}`:

```citry
from citry import Component


class PageFrame(Component):
    class Kwargs:
        body: object

    template = """
      <main>{{ body }}</main>
    """


welcome = Welcome(name="Ada")
page = PageFrame(body=welcome)
html = str(page)
```

To let the outer template supply markup that the component places in its
own layout, use [Slots](/concepts/slots/).

## Use a template file

An inline `template` suits short markup. For longer markup, set
[`template_file`][citry.Component.template_file] instead:

```citry
from citry import Component


class AccountPanel(Component):
    template_file = "account_panel.html"
```

A relative path is looked up first in the directory of the file that defines
the class, then in the template directories configured on the component's
[`Citry`][citry.Citry] instance. An absolute path is used as written.

Set `template` or `template_file`, not both. Setting both raises an error
when Python defines the class.

## Build now, render later

Calling a component class, as in `Welcome(name="Ada")`, does not render it.
It returns a [`CitryElement`][citry.CitryElement]: a description of what to
render, holding the class, its inputs, and its slot content. Rendering happens
when you call `str(...)`, or call `render()` and then `serialize()`:

```python
welcome = Welcome(name="Ada", message_count=3)

html = welcome.render().serialize()

assert str(welcome) == html
```

Because an element is only a description, you can build a whole page out of
elements first and render it once at the end. You can also render the same
element several times, or insert it in several places.
[Rendering](/concepts/rendering/) covers the steps in detail.

## Less common setups

### Leave out the template

A component does not need a template. Without one it renders nothing by
default. This suits a base class that other components extend, or a
component whose [`on_render()`][citry.Component.on_render] hook produces
the complete output.

### Render faster

For small display-only components that do not need hooks or their own
instance, [Simple components](/performance/simple-components/) render with
less overhead.
