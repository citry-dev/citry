---
title: Components
url: https://citry.dev/v/0.3.0/concepts/components/
description: "How a citry component pairs a template with the data it needs, and how you construct, render, and reuse one."
---
# Components

A component is a Python class that pairs a template with the data it needs. You
subclass [`Component`](/v/0.3.0/reference/component/#citry-component), give it a template, and describe how the
values you pass in become the variables the template reads. That is the whole
mental model: markup on one side, the data that fills it on the other, held
together by one class.

## The template

Every component needs a template. The common way is an inline `template` string:


```citry
from citry import Component

class Welcome(Component):
    template = """
      <div class="card">
        <h1>{{ title }}</h1>
        <p>You have {{ count }} new messages.</p>
      </div>
    """
```


Write `template` as a multiline triple-quoted string with the HTML on its own
lines. The `{{ title }}` and `{{ count }}` are template expressions; see
[Expressions](/v/0.3.0/syntax/expressions/) for what you can put inside them.

If you would rather keep the markup in its own `.html` file, use `template_file`
with a path instead of `template`. The two are mutually exclusive: setting both
on one class raises an error when the class is defined.

## Giving the template its data

A template can only read variables you hand it. That is the job of
`template_data`: override it to map the component's inputs to a dictionary of
template variables. Return a dict (its keys become the variables the template
sees) or `None` when there are no variables.


```citry
from citry import Component

class Welcome(Component):
    template = """
      <div class="card">
        <h1>{{ title }}</h1>
        <p>You have {{ count }} new messages.</p>
      </div>
    """

    def template_data(self, kwargs, slots):
        return {
            "title": kwargs["title"],
            "count": len(kwargs["messages"]),
        }
```


Here `kwargs` holds the inputs you passed when constructing the component. In
this example there is no `Kwargs` class declared, so `kwargs` is a plain dict and
you read it with subscript access: `kwargs["title"]`.

### Reading inputs when you declare a `Kwargs` class

If you add an inner `Kwargs` class to declare typed inputs, the metaclass turns
it into a dataclass, and then `kwargs` inside `template_data` is an instance of
it. Read it with attribute access instead of subscript:


```citry
from citry import Component

class Welcome(Component):
    class Kwargs:
        title: str
        messages: list[str]

    def template_data(self, kwargs, slots):
        return {
            "title": kwargs.title,
            "messages": kwargs.messages,
        }

    template = """
      <div class="card">
        <h1>{{ title }}</h1>
        <p>You have {{ len(messages[:20]) }} new messages.</p>
      </div>
    """
```


So the access style follows one rule: with a `Kwargs` class use `kwargs.title`
(attribute), without one use `kwargs["title"]` (subscript). See
[Typing and validation](/v/0.3.0/concepts/typing-and-validation/) for what the `Kwargs`
class buys you.

## Constructing and rendering

You construct a component by calling the class with your inputs:


```python
component = Welcome(title="Welcome back", messages=["a", "b", "c"])
html = str(component)
```


There is one thing to know here that surprises people. Calling the class does
**not** return a `Component` instance. It returns a [`CitryElement`](/v/0.3.0/reference/rendering/#citry-citryelement),
a lightweight record of "this class, with these inputs". Nothing has rendered
yet.

To get HTML, render the element. The shortest path is `str(component)`, which
runs the full pipeline with default options. If you need to pass rendering
options, call `render()` then `serialize()` yourself:


```python
component = Welcome(title="Welcome back", messages=["a", "b", "c"])

html = str(component)                        # render + serialize, defaults
same_html = component.render().serialize()   # the explicit form
```


`render()` returns a [`CitryRender`](/v/0.3.0/reference/rendering/#citry-citryrender) (an object, not a
string), and `serialize()` turns that into the final HTML. This split is what
lets you reuse a rendered subtree, and it is where options like a fragment render
live. For the full picture see [Rendering](/v/0.3.0/concepts/rendering/).

One input name is reserved: `slots`. Passing `slots=` fills slot content rather
than becoming a regular input, so a component cannot take a keyword argument
named `slots`. See [Slots](/v/0.3.0/concepts/slots/).

## Composing and reusing an element

Because calling a component gives you a `CitryElement`, you can render it on its
own or pass it into another component as an input. The same element can be used
in more than one place.


```citry
class Layout(Component):
    template = """
      <main>
        {{ body }}
      </main>
    """

    def template_data(self, kwargs, slots):
        return {"body": kwargs["body"]}

card = Card(title="Welcome")   # a CitryElement, not yet rendered

standalone = str(card)         # render the card on its own
page = Layout(body=card)       # or pass the same element into another component
html = str(page)
```


When an element lands in a `{{ }}` expression (like `{{ body }}` above), it is
rendered in place. Each time you render an element it mints a fresh render, so
using `card` in two places gives each spot its own independent render.

For building whole component trees from within a template with `<c-*>` tags,
rather than passing elements as inputs, see
[Build a page from components](/v/0.3.0/getting-started/build-page/).