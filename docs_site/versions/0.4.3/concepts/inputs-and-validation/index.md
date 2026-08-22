---
title: Inputs and validation
url: https://citry.dev/v/0.4.3/concepts/inputs-and-validation/
description: "Declare component inputs and choose when Citry should validate their names, defaults, values, and returned data."
---
# Inputs and validation

A component becomes easier to use when it says what people may pass to it.
Citry can check keyword arguments and slot names, fill in defaults, and reject
missing or unexpected values before the component body renders.

Start with plain nested classes for a clear component interface. Add a
validating model when values also cross an untrusted boundary or must obey
runtime type rules.

## Declare keyword inputs

Add [`Kwargs`](/v/0.4.3/reference/component/#citry-component-kwargs) to a
[`Component`](/v/0.4.3/reference/component/#citry-component) and list each accepted name:


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


`label` is required because it has no default. `variant` is optional and uses
`"primary"` when the template or Python code leaves it out. The default
[`template_data()`](/v/0.4.3/reference/component/#citry-component-template-data) exposes both fields to
the template, so this component does not need its own data method.

Leaving `Kwargs` off means the component accepts any keyword name. Use an
empty declaration when accepting no inputs is part of the contract:


```citry
from citry import Component


class Divider(Component):
    class Kwargs:
        pass

    template = """
      <hr class="divider" />
    """
```


## Know when Citry checks the inputs

Citry checks a statically written component tag when its parent template is
first compiled. The child must already be registered so Citry knows its
contract. A misspelled name or missing required input then raises a
`SyntaxError` during that first render:


```citry-html
<!-- Wrong: "lable" is not a Button input. -->
<c-button lable="Save" />

<!-- Right: this matches Button.Kwargs. -->
<c-button label="Save" />
```


Inputs passed from Python are checked when the element renders, not when you
call the class. Calling `Button(...)` only composes a
[`CitryElement`](/v/0.4.3/reference/rendering/#citry-citryelement):


```python
button = Button(lable="Save")

# Rendering finalizes the inputs and raises TypeError.
button.render()
```


Values added through a dynamic spread such as `c-bind` cannot all be known
when the parent template is compiled. Citry checks the completed child inputs
when that child renders.

This difference matters when you handle errors: a static template mistake
belongs to the parent's compile step, while a direct Python or dynamic input
mistake belongs to the child render.

## Choose name checks or value checks

A plain nested `Kwargs` class becomes a slotted dataclass. It checks required,
default, and unexpected field names, but its annotations do not validate
runtime value types:


```python
# The name is valid, so a plain schema accepts this value.
button = Button(label=42)
html = str(button)
```


Use annotations to help readers, editors, and type checkers. Do not rely on a
plain annotation to validate data from a form, request, database, or another
untrusted source.

For runtime value validation, inherit from a supported validating model such
as [Pydantic](https://docs.pydantic.dev/){: target="_blank" rel="noopener"}.
This example also asks Pydantic to reject unexpected fields from direct
Python calls:


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
Citry delegates value rules to the model, so its coercion and strictness
settings decide which values pass.

You may also use an explicitly decorated dataclass or a `NamedTuple` when you
want its construction model. Like Citry's plain dataclass form, these do not
turn annotations into runtime value validators by themselves.

## Give each render a fresh mutable default

A list, dictionary, or set written directly as a default would be shared by
every instance. The generated dataclass rejects that declaration when Citry
defines the component:


```citry
from citry import Component


class TodoList(Component):
    class Kwargs:
        items: list[str] = []  # Error: one shared list.
```


Use
[`field()`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field){: target="_blank" rel="noopener"}
to make a fresh value for each render:


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


A default applies only when the input is absent. Passing `None` keeps `None`;
it does not select the default factory.

## Declare the content a component accepts

Use [`Slots`](/v/0.4.3/reference/component/#citry-component-slots) for places where someone can insert
content. Annotate each field with [`SlotInput`](/v/0.4.3/reference/slots/#citry-slotinput):


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


The default slot is required by this declaration. `actions` is optional
because it permits and defaults to `None`. A missing required slot or an
unexpected slot name follows the same compile-time and render-time checks as
keyword inputs.

Use `SlotInput[SomeData]` when a slot exposes named values to its fill. The
complete rules, including fallback content and the separate `required`
attribute on `<c-slot>`, are in [Slots](/v/0.4.3/concepts/slots/).

## Check data returned by component methods

Input schemas check what enters a component. Data schemas can check the shape
of what its methods return:

- [`TemplateData`](/v/0.4.3/reference/component/#citry-component-templatedata) checks
  `template_data()`;
- [`JsData`](/v/0.4.3/reference/component/#citry-component-jsdata) checks
  [`js_data()`](/v/0.4.3/reference/component/#citry-component-js-data); and
- [`CssData`](/v/0.4.3/reference/component/#citry-component-cssdata) checks
  [`css_data()`](/v/0.4.3/reference/component/#citry-component-css-data).

These declarations catch a missing or unexpected returned field during the
render. Plain schemas still check field names, not the runtime type of each
value. Citry uses the constructed schema instance as the normalized result, so
declared defaults are filled and validating schema libraries such as Pydantic
can coerce values before templates and extensions receive them.

When you use `JsData`, the returned names and values become a strict-JSON
payload for that rendered component. Citry seeds its top-level keys into the
component's Alpine scope and also passes a fresh instance-local graph to the
component's [`$component()`](/v/0.4.3/reference/browser-apis/#component) callback when one exists. A component
with Alpine expressions does not need `$component()` only to copy data into
scope. When a render has neither Alpine expressions nor `$component()`, Citry
does not send the payload.


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

    template = """
      <button class="counter" x-text="initial_count">Count</button>
    """

    js = """
      $component(({ data }) => {
        const initialCount = data.initial_count;
        console.log(initialCount);
      });
    """
```


Python writes the payload key `initial_count`, and the Alpine expression reads
that exact key directly. Component JavaScript can still assign it to a
`camelCase` local when useful. See
[Component JavaScript and CSS](/v/0.4.3/advanced/js-and-css-dependencies/) for delivery
and CSS custom properties.

## Extend a plain schema in a subclass

A plain nested declaration adds its fields to declarations inherited from
parent components:


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


`IconButton.Kwargs` contains both `label` and `icon`. With multiple component
bases, Citry follows their normal Python method resolution order.

The same composition rule applies to plain `Slots`, `TemplateData`, `JsData`,
and `CssData` declarations. Assign a schema attribute to `None` when a
subclass should stop inheriting that schema:


```python
class FreeFormButton(Button):
    Kwargs = None
```


`FreeFormButton` now accepts keyword names without a `Kwargs` schema. See
[Subclassing](/v/0.4.3/advanced/subclassing/) for how schemas, templates, JavaScript,
and CSS interact across a component hierarchy.