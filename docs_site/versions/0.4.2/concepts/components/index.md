---
title: Components
url: https://citry.dev/v/0.4.2/concepts/components/
description: "Turn part of a page into a reusable Python class with its own inputs, content, and markup."
---
# Components

Components let you name and reuse parts of a page. A component can accept
values, leave places for other content, and decide what HTML to render. Use
one when a piece of UI appears more than once or deserves a clear interface
of its own.

A Citry component is a Python class based on
[`Component`](/v/0.4.2/reference/component/#citry-component). Most components bring together:

- inputs and slots that describe what people can change;
- a template that turns those values into HTML; and
- data methods when the template needs a calculated value.

## Render the smallest component

Set [`template`](/v/0.4.2/reference/component/#citry-component-template) to the markup you want the
component to produce:


```citry
from citry import Component


class Welcome(Component):
    template = """
      <section class="welcome">
        <h1>Welcome!</h1>
      </section>
    """


html = str(Welcome())
```


Calling `Welcome()` describes one use of the component. `str(...)` renders
that use and turns the result into HTML.

## Pass values straight to the template

Declare accepted keyword arguments with
[`Kwargs`](/v/0.4.2/reference/component/#citry-component-kwargs). By default, Citry makes those values
available to template expressions with the same names:


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


html = str(Welcome(name="Ada", message_count=3))
```


You do not need a data method just to repeat an input in the template. The
default [`template_data()`](/v/0.4.2/reference/component/#citry-component-template-data) returns the
component's keyword arguments.

A component without a `Kwargs` declaration also exposes its keyword
arguments this way, but accepts any name. Declaring the inputs gives Citry a
contract it can check. See
[Inputs and validation](/v/0.4.2/concepts/inputs-and-validation/) for required
values, defaults, slots, and runtime type validation.

## Calculate a value for the template

Override `template_data()` when the template needs a value that is not an
input as written. For example, this component turns a list of messages into a
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


With a `Kwargs` class, read inputs as attributes such as `kwargs.name`.
Without one, `kwargs` is a dictionary, so you would read
`kwargs["name"]`.

The method may return a dictionary or a supported data object. Returning
`None` gives the template no component data. You can declare
[`TemplateData`](/v/0.4.2/reference/component/#citry-component-templatedata) when you also want Citry to
check the returned fields.

## Keep the template beside the class or in a file

An inline `template` is useful when the markup is small and belongs with the
Python code. Set [`template_file`](/v/0.4.2/reference/component/#citry-component-template-file) when you
want the markup in its own file:


```citry
from citry import Component


class AccountPanel(Component):
    template_file = "account_panel.html"
```


Relative paths start from the directory that contains the class declaration,
then use the directories configured on the owning Citry instance. An absolute
path is used as written.

Set either `template` or `template_file`, not both. If both contain a value,
Citry raises an error when the class is defined.

Most visible components have a template, but Citry does not require one. A
component with no template renders no body by default. This is useful for a
base class or for a component whose
[`on_render()`](/v/0.4.2/reference/component/#citry-component-on-render) hook supplies its complete output.

## Compose first, render when you need HTML

Calling a component class returns a
[`CitryElement`](/v/0.4.2/reference/rendering/#citry-citryelement), not a live `Component` instance and not
an HTML string. The element remembers which class to use, along with its
inputs and slot content:


```python
welcome = Welcome(name="Ada", message_count=3)

rendered = welcome.render()
html = rendered.serialize()

assert str(welcome) == html
```


Keeping composition separate from rendering lets you build a page out of
elements before doing any rendering work. It also lets you render the same
element again as a fresh occurrence.

The name `slots` is reserved when you call a component. A `slots=` mapping
fills its content areas instead of becoming a regular keyword argument. See
[Slots](/v/0.4.2/concepts/slots/) for template and Python examples.

## Put one component inside another

Inside a template, a `<c-*>` tag composes another registered component:


```citry
from citry import Component


class ProfilePage(Component):
    class Kwargs:
        user_name: str

    template = """
      <main>
        <c-welcome c-name="user_name" />
      </main>
    """
```


You can also pass an element through Python and insert it from an expression:


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


When an expression inserts a `CitryElement`, Citry renders it in that place.
The same element can appear in more than one place because each use creates a
fresh rendered occurrence. [Rendering](/v/0.4.2/concepts/rendering/) explains when to
keep an element and when to keep its rendered result.