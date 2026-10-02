---
title: Registration
description: Connect component tag names to Python classes and choose which Citry instance owns them.
---

# Registration

To render `<c-reading-list>`, Citry needs to know which Python class that tag
means. Citry records this when Python defines the class: there is no
decorator or list to maintain. This page shows which tag names a class
gets, and what to do when a tag is not found.

## Use a component's tag

A [`Component`][citry.Component] subclass is registered as soon as Python
runs its `class` statement:

```citry
from citry import Component, citry


class Greeting(Component):
    class Kwargs:
        name: str

    template = """
      <p>Hello, {{ name }}!</p>
    """


assert citry.get("greeting") is Greeting
```

Any template can now use `<c-greeting name="Ada" />`.

Citry builds the tag name from the class name. A class name made of several
words gets two names, and either works:

- `ReadingList` registers as `reading-list` and `readinglist`, so
  `<c-reading-list>` and `<c-readinglist>` both find it.
- `Greeting` registers only as `greeting`.

Case does not matter after the `c-` prefix, so `<c-ReadingList>` works too.
The `c-` prefix itself must be lowercase.

## Choose a different tag name

Set `name` when the tag should not follow the class name:

```citry
from citry import Component


class StatusBadge(Component):
    class Kwargs:
        text: str

    name = "result-badge"

    template = """
      <strong>{{ text }}</strong>
    """
```

The component is now used as `<c-result-badge>`.

## Import the module before using its tag

Because registration happens when Python runs the `class` statement, a
component in a module that has not been imported yet has no tag. Rendering
a template that uses the tag raises
[`NotRegistered`][citry.NotRegistered] with the message
`No component registered as 'reading-list'`.

In a small project, import the module where the app starts:

```python
from myproject.components.reading_list import ReadingList
```

The import is enough. You do not need to use `ReadingList` anywhere in that
file.

In a larger project, let Citry import whole directories of components at
startup. [Component discovery](/advanced/component-discovery/) shows how.

## Keep an app's components on one Citry instance

Each component belongs to one [`Citry`][citry.Citry] instance. A component
that does not set one belongs to the shared [`citry`][citry.citry]
instance.

An application usually creates its own instance, so its components,
settings, extensions, and routes stay together. Set it on each component
with `citry = ...`:

```citry
from citry import Citry, Component

app = Citry(autodiscover=False)


class ActionButton(Component):
    citry = app

    class Kwargs:
        label: str

    template = """
      <button type="button">{{ label }}</button>
    """


assert app.get("action-button") is ActionButton
```

A template looks up `<c-*>` tags on its own component's Citry instance. Two
components can use each other's tags only when they belong to the same
instance.

## Give a component a second name

Use [`register()`][citry.Citry.register] to add another tag name for a
component you already have:

```python
app.register(ActionButton, name="primary-button")

assert app.get("primary-button") is ActionButton
assert app.has("action-button")
```

Both names now work on `app`. To share components with other projects under
stable names, publish a
[component library](/advanced/component-libraries/) instead.

!!! note "Valid names and registration errors"

    A name must start with a letter, followed by letters, digits, hyphens,
    underscores, or dots. Any other name raises `ValueError`. Registering a
    name that another component already uses raises
    [`AlreadyRegistered`][citry.AlreadyRegistered], and so does a name that
    Citry reserves for its built-in tags, such as `slot`. Looking up a name
    that is not registered raises [`NotRegistered`][citry.NotRegistered].
