---
title: Registration
url: https://citry.dev/v/0.4.1/concepts/registration/
description: "Connect component tag names to Python classes and choose which Citry instance owns them."
---
# Registration

Before Citry can render `<c-reading-list>`, it needs to know which Python
class that name means. Defining a component creates that connection. Once the
class's module has been imported, every component on the same
[`Citry`](/v/0.4.1/reference/citry/#citry-citry) instance can use its tag.

If importing every component module by hand becomes unwieldy, read
[Component discovery](/v/0.4.1/advanced/component-discovery/) after this page.

## Register a component when its class is defined

A concrete [`Component`](/v/0.4.1/reference/component/#citry-component) registers as soon as Python defines
the class. There is no decorator or separate registration list:


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


Citry derives two case-insensitive names from a multiword class name:

- `ReadingList` registers as `readinglist` and `reading-list`;
- either `<c-readinglist>` or `<c-reading-list>` finds the same class.

A one-word name such as `Greeting` produces only `greeting`.

The `c-` prefix itself is always lowercase. The component-name suffix is
case-insensitive, so `<c-ReadingList>` is valid, while `<C-ReadingList>` is
not Citry component syntax.

Set `name` when the public tag should use a different name:


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


The component is now available as `<c-result-badge>`.

## Keep related components on one Citry instance

Every component belongs to one [`Citry`](/v/0.4.1/reference/citry/#citry-citry) instance. Components
without an explicit owner use the shared [`citry`](/v/0.4.1/reference/citry/#citry-citry-2) instance.

Applications often create their own instance so their components, settings,
extensions, and routes stay together:


```citry
from citry import Citry, Component

app = Citry(autodiscover=False)


class ActionButton(Component):
    class Kwargs:
        label: str

    citry = app

    template = """
      <button type="button">{{ label }}</button>
    """


assert app.get("action-button") is ActionButton
```


A template resolves `<c-*>` tags through its own component's Citry instance.
Two components can use each other's tags only when they belong to the same
instance.

## Add an alias when one class needs another name

Use [`register()`](/v/0.4.1/reference/citry/#citry-citry-register) to give an existing component another
name on its own Citry instance:


```python
app.register(ActionButton, name="primary-button")

assert app.get("primary-button") is ActionButton
assert app.has("action-button")
```


Aliases are useful when one application needs a local spelling. A reusable
component package should publish a
[component library](/v/0.4.1/advanced/component-libraries/) with deliberate public
names.

Names must begin with a letter. The remaining characters may be letters,
digits, hyphens, underscores, or dots. An invalid name raises `ValueError`.

If another component already owns the requested name, Citry raises
[`AlreadyRegistered`](/v/0.4.1/reference/citry/#citry-alreadyregistered). Built-in and structural tag
names are reserved and produce the same error. Looking up a name that does not
exist raises [`NotRegistered`](/v/0.4.1/reference/citry/#citry-notregistered).

## Import the module before using its tag

Registration happens while Python executes the class statement. A class in a
module that has never been imported does not exist yet, so its tag cannot be
found.

For a small project, an ordinary import is enough:


```python
from myproject.components.reading_list import ReadingList
```


The imported name does not need to appear elsewhere in that file. Running the
module defines `ReadingList`, which registers its tag.

For a larger project, configure directories that Citry can import and prepare
them during application startup.
[Component discovery](/v/0.4.1/advanced/component-discovery/) shows the directory
layout, explicit startup call, and recovery behavior.