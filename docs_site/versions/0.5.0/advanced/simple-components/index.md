---
title: Simple components
url: https://citry.dev/v/0.5.0/advanced/simple-components/
description: "Render presentation components without creating an independent component instance."
---
# Simple components

A label, icon or wrapper may only turn inputs into HTML. Declare
[`simple = True`](/v/0.5.0/reference/component/#citry-component-simple) when that component does not need
its own instance, lifecycle hooks or browser identity. Citry renders its
template under the surrounding component's ownership and skips that setup.


```citry
from citry import Component


class StatusLabel(Component):
    simple = True

    class Kwargs:
        text: str

    template = """
      <span class="status">{{ text }}</span>
    """
```


Use it through a component tag, insert `StatusLabel(text="Ready")` from a
Python expression, or render it directly. Inputs are current on every call.
The flag does not cache output or promise that the template is pure.

## Calculate data without an instance

The default data method exposes the keyword arguments to the template.
When data needs preparation, use a synchronous static method with both
`kwargs` and `slots` parameters:


```citry
from citry import Component


class UpperLabel(Component):
    simple = True

    class Kwargs:
        text: str

    @staticmethod
    def template_data(kwargs, slots):
        return {"text": kwargs.text.upper()}

    template = """
      <span>{{ text }}</span>
    """
```


Citry calls this method on every invocation. With a `Kwargs` or `Slots`
schema, it receives a fresh schema instance; without one, it receives a
mapping. Ordinary schema construction and returned-data validation still
apply. Async methods, generators and arbitrary callable objects are rejected.
Authored helper methods must also be static; custom instance methods,
class methods and properties are unsupported.

An ordinary instance method is a common migration mistake:


```python
# Invalid in a class with simple = True: there is no instance.
def template_data(self, kwargs, slots):
    return {"text": kwargs.text.upper()}


# Use a static method with the two input parameters.
@staticmethod
def template_data(kwargs, slots):
    return {"text": kwargs.text.upper()}
```


## Accept optional default content

A simple template can have an empty default outlet:


```citry
from citry import Component, Slot


class Inset(Component):
    simple = True

    class Slots:
        default: Slot | None = None

    template = """
      <section class="inset"><c-slot /></section>
    """
```


Supply content as the tag's body:


```citry-html
<c-Inset><strong>{{ user_name }}</strong></c-Inset>
```


`user_name` belongs to the caller. The simple component's own data does not
replace the variables used by supplied content. From Python, use
`Inset(slots={"default": "Ready"})`. A data callback receives supplied
content as a lazy `Slot`, so it can consume it or return it as template data.

The outlet must be plain `<c-slot />`: no name, fallback body, slot data or
required-content declaration. Explicit `<c-fill>` wrappers at the simple
call are rejected, including an explicit default fill. If declared, `Slots`
must be a plain schema with only a `default` field defaulting to `None`; custom
constructors, factories and additional fields are unsupported.

Simple templates can call ordinary child components and supply named fills
to those children. Those children keep their own instances and hooks.

## Understand the ownership change

A simple invocation gets no separate Python component instance, render ID,
component hooks, slot hooks of its own, or automatic Alpine isolation boundary.
HTML it produces belongs to its surrounding ordinary component. Component
tags authored inside its template use that ordinary component as their
parent; supplied content retains its caller's scope.

Ordinary HTML attributes, `c-bind` spreads, expressions, branches, loops and
Alpine attributes remain available in the template. The simple class cannot
declare its own JavaScript, CSS or translation messages. Its ordinary child
components can still bring those features.

Direct tags execute their data callbacks at the normal deferred stage.
Python values execute when their expression inserts them. A direct root
render uses a framework owner, so rendering one simple component as an
entire page still has root setup cost. `<c-component>` can select a simple
class, but the selector keeps its own instance and hooks.

## Let invalid opt-ins fail early

Citry raises an error rather than silently rendering an incompatible class
as an ordinary component:

| Checked when | Unsupported examples |
| --- | --- |
| Class definition | A non-boolean `simple` value; instance data methods or lifecycle hooks; JS, CSS or messages; instance configurations such as State, Events, Cache, Dependencies or I18n; `transparent = True` |
| Template preparation | Named or fallback outlets; `$c-tr` translation bindings; unsupported custom or foreign-template nodes, including in inactive branches |
| Each invocation | Explicit fills; component-level client bindings or `#c-key`/`#c-ignore` on the simple call; unsupported Python slot names; invalid inputs or returned data; `$c-tr` keys arriving through an attribute spread |

An empty asset string still declares an asset. The restrictions also apply
to inherited declarations and to targets chosen by a dynamic selector.
A caller's active translation catalog does not enable `$c-tr` inside a
simple template.

## Keep the checked class definition stable

`simple` defaults to `False`, accepts only `True` or `False`, and inherits
to subclasses. Each simple subclass is validated independently. The flag
and a simple class's checked declarations cannot be reassigned after class
creation; define a new subclass for a changed definition. Supported template
file reset APIs reload and recheck the template.

A subclass can explicitly declare `simple = False` to use the ordinary
component contract. [`LibraryComponent`](/v/0.5.0/reference/component-libraries/#citry-librarycomponent) also accepts
the flag; Citry checks the class when the library is materialized.

## Choose between simple rendering and reuse

`simple = True` removes independent component setup. It does not require
equal inputs between calls, and the data callback stays live.
[`pure = True`](/v/0.5.0/reference/component/#citry-component-pure) separately promises deterministic,
side-effect-free template behavior and can reuse equal bodies within one
root render. You can declare both when both contracts apply. A simple body
with a default outlet remains live even with `pure = True`.

Measure your own repeated-render workload before opting in. The benefit
depends on how much instance setup the component would otherwise do, and
how much time it spends producing its HTML.

## Related pages

- [Performance](/v/0.5.0/advanced/performance/) compares simple rendering,
  `Const` and pure bodies.
- [Component hooks](/v/0.5.0/advanced/hooks/) covers ordinary instance behavior.
- [Benchmarks](/v/0.5.0/about/benchmarks/) describes the measured workloads.