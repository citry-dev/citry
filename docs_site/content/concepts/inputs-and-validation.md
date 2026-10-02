---
title: Inputs and validation
description: Declare component inputs and choose when Citry should validate their names, defaults, values, and returned data.
---

# Inputs and validation

Declare the inputs a component accepts, and Citry stops a misspelled name or
a missing value with an error before the component renders. The declaration
also fills in defaults and tells readers, editors, and type checkers how to
use the component.

Plain nested classes check input names. Add a validating model such as
Pydantic when the values themselves must be checked too.

## Declare keyword inputs

Add a nested [`Kwargs`][citry.Component.Kwargs] class to a
[`Component`][citry.Component] and list each accepted name:

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
```

`label` is required because it has no default. `variant` is optional and is
`"primary"` when a template or Python code leaves it out. The template can read both by
name.

Without a `Kwargs` class, a component accepts any keyword name. To accept no
inputs at all, declare an empty class:

```citry
from citry import Component


class Divider(Component):
    class Kwargs:
        pass

    template = """
      <hr class="divider" />
    """
```

## See where a wrong input is reported

A mistake in a `<c-*>` tag written in a template raises `SyntaxError` the
first time that template renders. This covers a misspelled name and a
missing required input:

```citry-html
<!-- Wrong: "lable" is not a Button input. -->
<c-button lable="Save" />

<!-- Right: this matches Button.Kwargs. -->
<c-button label="Save" />
```

Citry can check the tag this early only if the child component is already
registered, which means its module has been imported. See
[Registration](/concepts/registration/).

Inputs passed from Python are checked when the component renders, not when
you call the class:

```python
# Calling the class only records the inputs.
button = Button(lable="Save")

# Rendering checks them and raises TypeError.
button.render()
```

Inputs added with a `c-bind` spread are also checked when the child renders,
because their names are known only then.

## Check the values, not only the names

A plain `Kwargs` class checks that required names are present and unknown
names are absent. Its type annotations are not checked when the page runs:

```python
# The name is valid, so a plain Kwargs class accepts 42.
html = str(Button(label=42))
```

The annotations still help readers, editors, and type checkers. Do not rely
on them to check data from a form, request, database, or other untrusted
source.

To check values, base `Kwargs` on a validating model such as
[Pydantic](https://docs.pydantic.dev/){: target="_blank" rel="noopener"}:

```citry
from citry import Component
from pydantic import BaseModel, ConfigDict


class AgeBadge(Component):
    class Kwargs(BaseModel):
        model_config = ConfigDict(extra="forbid")

        age: int

    template = """
      <span class="age-badge">Age {{ age }}</span>
    """
```

Now `AgeBadge(age="unknown").render()` raises Pydantic's validation error.
The model's own settings decide which values pass. Here,
`extra="forbid"` also makes Pydantic reject unknown names passed from
Python.

You can also use a `@dataclass` or a `NamedTuple` as `Kwargs`. Like a plain
class, these check names but not value types.

## Give list and dict defaults a fresh value per render

A list, dictionary, or set written directly as a default would be shared by
every render, so Citry rejects it when Python defines the class:

```citry
from citry import Component


class TodoList(Component):
    class Kwargs:
        items: list[str] = []  # Error: one shared list.
```

Use
[`field()`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field){: target="_blank" rel="noopener"}
to create a new value for each render:

```citry
from dataclasses import field

from citry import Component


class TodoList(Component):
    class Kwargs:
        items: list[str] = field(default_factory=list)

    template = """
      <p>{{ len(items) }} tasks</p>
    """
```

A default applies only when the input is left out. Passing `None` gives the
component `None`, not the default.

## Declare the slots a component accepts

A slot is a place in the component's template where each use of the component can insert
its own content. List the accepted slots in a nested
[`Slots`][citry.Component.Slots] class, and annotate each one with
[`SlotInput`][citry.SlotInput]:

```citry
from citry import Component, SlotInput


class Panel(Component):
    class Slots:
        default: SlotInput
        actions: SlotInput | None = None

    template = """
      <section class="panel">
        <div class="panel__body"><c-slot /></div>
        <footer><c-slot name="actions" /></footer>
      </section>
    """
```

The `default` slot is required. `actions` is optional because it defaults to
`None`. A missing required slot or an unknown slot name is reported at the
same points as a wrong keyword input. A slot can also pass data to its
fill with `SlotInput[...]`; see
[Slots](/concepts/slots/#pass-data-from-the-component-to-the-fill).

## Check the data a component returns

Input schemas check what goes into a component. Three more nested classes
check what its data methods return:

- [`TemplateData`][citry.Component.TemplateData] checks
  [`template_data()`][citry.Component.template_data];
- [`JsData`][citry.Component.JsData] checks
  [`js_data()`][citry.Component.js_data]; and
- [`CssData`][citry.Component.CssData] checks
  [`css_data()`][citry.Component.css_data].

```citry
from citry import Component


class Counter(Component):
    class Kwargs:
        initial_count: int = 0

    class JsData:
        initial_count: int

    def js_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> JsData:
        return self.JsData(initial_count=kwargs.initial_count)
```

A missing or unexpected field raises an error during the render. As with
`Kwargs`, a plain class checks names and a validating model also checks
values. Citry passes the checked result on, with defaults filled in and any
conversions the model made.

[Client interactivity](/concepts/client-interactivity/#seed-browser-data-from-python)
shows how the browser reads `js_data()`.

## Extend inputs in a subclass

A plain `Kwargs` class in a subclass adds its fields to the ones it
inherits:

```citry
from citry import Component


class Button(Component):
    class Kwargs:
        label: str

    template = """
      <button>{{ label }}</button>
    """


class IconButton(Button):
    class Kwargs:
        icon: str

    template = """
      <button>{{ icon }} {{ label }}</button>
    """
```

`IconButton` accepts both `label` and `icon`. With several parent
components, Citry combines them in Python's usual method resolution order.
`Slots`, `TemplateData`, `JsData`, and `CssData` combine the same way.

To stop a subclass from inheriting a schema, set it to `None`:

```python
class FreeFormButton(Button):
    Kwargs = None
```

`FreeFormButton` accepts any keyword name.
[Subclassing](/advanced/subclassing/) covers how templates, JavaScript, and
CSS combine across a component hierarchy.
