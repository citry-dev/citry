---
title: Inputs and validation
description: Declare component inputs and choose when Citry should validate their names, defaults, values, and returned data.
---

# Inputs and validation

Declare the inputs a component accepts, and Citry stops a misspelled name or
a missing value with an error before the component renders. The declaration
also fills in defaults and tells readers, editors, and type checkers how to
use the component.

Citry also checks that each value has the type its annotation names, so
`title: str` rejects a number. Add a validating model such as Pydantic to
check the items of a list or to turn a form's text into a number.

## `Kwargs` keyword inputs

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

## Find input errors

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

## Check value types { #typed-kwargs-checks }

When a component renders, Citry checks each input against its annotation
and raises `TypeError` for a value of the wrong type:

```python
button = Button(label=42)

# TypeError: Button.Kwargs.label expects str, got int (42).
# Pass a value of the expected type, or change the annotation
# to accept int.
str(button)
```

The message names the component, the input, the type the annotation
expects, and the value it got. When the component comes from a registered
component library, such as Citry UI, the message names the library and
asks you to change the value you pass, because its annotation is not yours
to edit. When the wrong value is one the component's own code computes,
such as its template data, the message names the library and asks you to
report the error to it, unless the value came from an input you passed. The check runs on every render, in
development and in production, so a value of the wrong type from a form,
an API, or a database fails here too.

Citry checks only the outer type. `tags: list[str]` rejects a tuple or a
string, but it does not look at the items, so a list of numbers passes.
To check the contents of data you do not control, use Pydantic
([below](#check-more-with-pydantic)).

The same check applies to `TemplateData`, `JsData`, and `CssData` (see
[below](#templatedata-jsdata-cssdata)), and to the Events
[`State`][citry.Component.State] a component builds when the page renders.
State sent back with an event call is not checked again.

### Accept more values

Widen the annotation when a field should take more than one type:

```citry
from citry import Component


class Price(Component):
    class Kwargs:
        # Wrong: an int amount from the database fails.
        # amount: str

        # Right: the annotation names every type the field takes.
        amount: str | int

    template = """
      <span class="price">{{ amount }}</span>
    """
```

In a template, a plain attribute such as `amount="18"` always passes text.
Write `c-amount="18"` to pass the number instead.

### Turn the check off

To turn the check off for one component and its subclasses, set
`check_input_types = False` in its nested
[`Lint`][citry.Component.Lint] class:

```citry
from citry import Component


class LegacyCard(Component):
    class Kwargs:
        title: str

    class Lint:
        check_input_types = False

    template = """
      <div class="legacy-card">{{ title }}</div>
    """
```

To turn it off for a whole application, pass `check_input_types=False`
to [`LintSettings`][citry.LintSettings]. The setting sits with the lint
settings, but it acts when a component renders; `citry check` ignores
it:

```python
from citry import Citry, LintSettings

app = Citry(
    lint=LintSettings(check_input_types=False),
)
```

A component can still turn the check on for itself with
`check_input_types = True` in its `Lint` class.

### What each type accepts

Each annotation accepts about what a type checker would accept, with a
few allowances:

- `int` accepts `bool` and other integer types, such as numpy integers.
- `float` accepts `int`, `Fraction`, and numpy floats. It rejects
  `Decimal`, as type checkers do; write `float | Decimal` to accept it.
- `str` accepts subclasses such as [`Markup`][citry.Markup], and Django's
  lazy translation strings from `gettext_lazy()`.
- `X | None` and `Optional[X]` accept `None`. So does a field whose
  default is `None`, such as `title: str = None`.
- A field's own default value always passes, so `tags: list[str] = ()`
  works when the input is left out. A non-empty tuple such as `("a",)`
  still fails, and so does a wrong value from a `default_factory`.
- `Literal["a", "b"]` accepts those values, and also a value of a `str` or
  `int` subclass that equals one, such as a `StrEnum` member or
  `Markup("a")`. A `bool` never matches an `int` member: `True` does not
  pass for `Literal[1]`, and `1` does not pass for `Literal[True]`.
- `type[Row]` accepts the class `Row` or a subclass.

Citry skips an annotation it cannot test while the page runs: `Any`,
`object`, a type variable, a `Protocol` without `@runtime_checkable`, and a
name Python cannot find while the page runs. That last case covers a name
imported only under `if TYPE_CHECKING:`, and a class defined inside a
function in a module that uses `from __future__ import annotations`. A
union with one such member, such as `Row | None` where `Row` is imported
only for type checkers, is not checked at all. Import a type normally when
you want its inputs checked.

A `Mock` from `unittest.mock` fails the check unless it is created with
`spec=`, which makes it pass for that class.

### Check more with Pydantic

To check the items of a list, or to convert values, base `Kwargs` on a
validating model such as
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

Now `AgeBadge(age="unknown").render()` raises Pydantic's validation error,
while `AgeBadge(age="42")` passes because Pydantic turns the text into a
number. The model's own settings decide which values pass, so Citry does
not check a Pydantic model's fields again. Here, `extra="forbid"` also
makes Pydantic reject unknown names passed from Python.

You can also use a `@dataclass` or a `NamedTuple` as `Kwargs`. Citry
checks their names and value types like a plain class. A dataclass that
writes its own `__init__` controls its own values, so Citry skips the type
check for it.

### Share one schema base { #model-base }

Citry turns each schema class on this page (`Kwargs`, `TemplateData`, and
the others below) that lists plain annotated fields into a class it
generates, a dataclass by default.
To make all of them Pydantic models with the same settings, without
writing `BaseModel` on each one, set `model_base` on `Citry`:

```citry
from citry import Citry, Component
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


app = Citry(model_base=Model)


class AgeBadge(Component):
    citry = app  # use app's settings

    class Kwargs:
        age: int

    template = """
      <span class="age-badge">Age {{ age }}</span>
    """
```

`AgeBadge.Kwargs` is now a `Model`, so Pydantic checks its values with
`extra="forbid"` and `strict=True`. With `strict=True`, `"42"` fails for
`age: int`, as it does under Citry's own check; without it, Pydantic turns
the text into a number. Pydantic ignores an unknown name unless the
base's `model_config` sets `extra="forbid"`, so without it a misspelled
input passed from Python is dropped silently.

The setting applies to the plain declarations of `Kwargs`,
`TemplateData`, `JsData`, `CssData`, `State`, and Events `data` classes
(see [Pydantic State](/events/state/#pydantic-state)). A
class that is, or inherits, a dataclass or a model keeps that type, so a
child component's `class Kwargs(Parent.Kwargs):` keeps its parent's.
`Slots`, Citry's own components, and the components of a library you
install with `register_library()` keep the classes their authors wrote.

`model_base` takes one of these values:

| Value | What Citry generates |
|---|---|
| `None` (the default) | dataclasses |
| a Pydantic v2 model class, such as `BaseModel` | Pydantic v2 models that subclass it |
| a Pydantic v1 model class, such as `pydantic.v1.BaseModel` | Pydantic v1 models that subclass it |
| a dataclass, such as `@dataclass(frozen=True) class Model: ...` | dataclasses that subclass it and copy its options |
| `typing.NamedTuple` | named tuples |

You can also pass an import string, such as `"pydantic.BaseModel"`, so a
settings module does not import the class itself. Citry imports it when
`Citry(...)` is built, and raises `ImportError` there if the import fails,
or `TypeError` if the class is not one of the kinds above (or the string
has no module part).

A generated model or named tuple does not inherit the class you wrote, so
a few things work differently:

- Its ordinary methods and properties are copied. A method that calls
  `super()` fails when the component class is defined; call the parent
  method directly, such as `Base.label(self)` when `Kwargs` subclasses
  `Base`, or decorate `Kwargs` with `@dataclass` to keep it a dataclass.
- `isinstance()` checks against the class you wrote, or its plain base
  classes, return `False`. The component's own `Kwargs` is the generated
  class.
- Read the fields as attributes, such as `kwargs.age`. Code that calls
  `dataclasses.fields()` on a schema only works for dataclasses.
- A Pydantic model never calls `__post_init__`; write
  `model_post_init(self, context)` instead, or decorate `Kwargs` with
  `@dataclass`.
- Under Pydantic v2, a class constant whose name starts with `_`, such as
  `_cache = {}`, becomes a private attribute that each instance copies.

These fail when the component class is defined, with a message that names
the component:

- A field type Pydantic cannot check. The message names the field.
- Under Pydantic, a field whose name starts with `_` (Pydantic keeps it as
  a private attribute), and a field with `field(init=False)`.
- Under `typing.NamedTuple`, a field without a default after one with a
  default, a field with `field(default_factory=...)`, and a list,
  dictionary, or set written as a default. A child
  `Kwargs` cannot add fields to its parent's named tuple either.
- `State` under a frozen dataclass base, a frozen model base, or
  `typing.NamedTuple`, because handlers change `State`.
- An Events `data` class under `typing.NamedTuple` or a Pydantic v1 base,
  because Events validation reads dataclasses and Pydantic v2 models.

A name imported only under `if TYPE_CHECKING:`, which Citry's own check
skips, cannot be read when the class is defined. Under a Pydantic v2 base
it fails at the first render with Pydantic's "not fully defined" error.
Under a v1 base it fails once a value is passed for that field, and so
does a field that names a class defined later in the module; call
`Kwargs.update_forward_refs()` after that class is defined. Import the
type normally where you can.

`Citry(...)` raises `TypeError` when `model_base` is a named tuple class
with fields (pass `typing.NamedTuple` instead), a dataclass with its own
`__init__` (use `__post_init__`), a Pydantic dataclass, or a root model.

Under Pydantic, string values from a browser form or a query string reach
an Events `data` class as text, and `strict=True` rejects text for a
number field. A field whose type is a plain class, such as
`lines: list[Line]`, fails under Pydantic when the component class is
defined; make `Line` a Pydantic model or a dataclass.

With a dataclass base, Python 3.11 does not record `kw_only=True` or
`match_args`, so those options have no effect there.

## `field()` defaults

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

## `Slots` and `SlotInput`

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

## `TemplateData`, `JsData`, `CssData`

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

A missing or unexpected field, or a value of the wrong type, raises an
error during the render. As with `Kwargs`, a validating model such as
Pydantic checks values by its own rules instead. Citry passes the checked
result on, with defaults filled in and any conversions the model made.

[Component options](/vue/component-options/#seed-browser-data-from-python)
shows how the browser reads `js_data()`.

## `Kwargs` in subclasses

A subclass uses its parent's `Kwargs` until it declares its own. To add
inputs, name the parent's class as a base, so the subclass keeps the
parent's fields and defaults:

```citry
from citry import Component


class Button(Component):
    class Kwargs:
        label: str

    template = """
      <button>{{ label }}</button>
    """


class IconButton(Button):
    class Kwargs(Button.Kwargs):
        icon: str

    template = """
      <button>{{ icon }} {{ label }}</button>
    """
```

`IconButton` accepts both `label` and `icon`. A plain `class Kwargs:` in
the subclass would replace the parent's fields instead, like any nested
Python class, and Citry warns when that leaves out a parent field.
`Slots`, `TemplateData`, `JsData`, and `CssData` follow the same rule.

To stop a subclass from checking inputs, set its `Kwargs` to `None`:

```python
class FreeFormButton(Button):
    Kwargs = None
```

`FreeFormButton` accepts any keyword name.
[Subclass components](/advanced/subclassing/) covers replacing inputs,
combining two parents, and how templates, JavaScript, and CSS carry over
to a subclass.
