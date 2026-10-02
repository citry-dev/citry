---
title: Simple components
description: Render presentation components without creating an independent component instance.
---

# Simple components

A label, icon or wrapper may only turn inputs into HTML. Declare
[`simple = True`][citry.Component.simple] when that component does not need
its own instance, lifecycle hooks or browser identity. Citry renders its
template as part of the surrounding component and skips that setup.

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

## Choose the component's browser identity

The default `simple = False` keeps an ordinary Python component and its Vue
instance. `simple = True` keeps its existing caller-owned HTML behavior and
has no separate Vue identity. `simple = "vue"` skips the Python component
instance but creates an independent Vue instance with its own identity and
authored assets:

```citry
from citry import Component


class Toggle(Component):
    simple = "vue"

    class Kwargs:
        label: str

    @staticmethod
    def template_data(kwargs, slots):
        return {"label": kwargs.label}

    template = """
      <button
        :aria-expanded="open"
        @click="open = !open"
      >
        {{ label }}
      </button>
    """

    js = """
      $component({
        data() {
          return { open: false };
        },
      });
    """
```

This mode accepts registered components whose templates contain no slots
and do not declare `transparent = True`. Its template may use text, `c-if`,
`c-for`, fixed `c-*` attributes, safe `c-bind` objects, authored Vue
bindings, and calls to child components, described below. Authored
component JS/CSS and static `js_data`/`css_data` callbacks are supported.
Slots, provide/inject, instance hooks, `Events`, `Cache`, `I18n`, and `State`
configuration, component messages, and any `js` or `css` entry in
`Dependencies` are unsupported. Evaluated
template values must be JSON-like values such as strings, numbers, booleans,
lists and dictionaries. Citry calls the callback once per call. An unsupported
class shape fails before it runs. An unsafe returned value raises an error;
Citry does not switch to ordinary rendering for it.

The Python component instance is omitted; the browser Vue instance still owns
`open` and updates `aria-expanded` on each click. Incompatible declarations and
values raise a named error. `simple = False` restores ordinary component
behavior; `simple = True` remains unchanged.

Some app-wide settings need the component instance: i18n settings passed to
`Citry`, messages declared on any other registered component, an extension
that handles component data or lifecycle hooks, or an extension that changes
element attributes (`on_attrs_resolved`) used by this template. While one of
them applies, Citry renders the `simple = "vue"` component as an ordinary
component instead. The page shows the same HTML and the data callback still
runs once per call, but that component renders at ordinary speed.

## Call child components from a `simple = "vue"` template

A `simple = "vue"` template can call other components. Each child
renders the way its own class says, whatever mode its caller uses: an
ordinary child still gets its Python instance, hooks, data callbacks and
assets, and a `simple = "vue"` child still skips its instance.

```citry
from citry import Component


class Row(Component):
    simple = "vue"

    class Kwargs:
        row: dict

    template = """
      <li>
        <button @click="open = !open">{{ row['title'] }}</button>
        <div v-show="open">
          <c-Details c-row="row" />
        </div>
      </li>
    """

    js = """
      $component({
        data() {
          return { open: false };
        },
      });
    """
```

`Details` can be an ordinary component or another `simple = "vue"`
component; the page shows the same HTML either way, and the same HTML
as it would if `Row` were an ordinary component.

A call from a `simple = "vue"` template passes its inputs as attributes
and nothing else:

- Each input is a static attribute or a `c-*` expression that the rest
  of the template could also use.
- `#c-key` is allowed, and is required when `c-for` repeats a call.
- The call cannot pass content (a tag body or `<c-fill>`), a `c-bind`
  spread, or Vue bindings and events on the component tag (`@click`,
  `:prop`, `v-show`). Put those on an element inside the child, or use an
  ordinary parent.

Calls outside `c-if` and `c-for` are the cheapest: Citry compiles the
browser template once and reuses it for every row, unless the parent
sets `css_data`. A call inside `c-if` or `c-for` works too, but Citry
builds each row's browser template from that row's values, as it does
for an ordinary component, so serializing it costs more.

A `simple = "vue"` parent has no Python instance, so an ordinary child's
`self.parent` is the nearest ordinary component above it, and the child
receives the values provided above that parent. Error messages still name
the whole path, for example `Page > Row > Details`.

A child whose HTML must become part of its caller's own template cannot
be called this way: a `simple = True` component, a transparent component,
or a `<c-component>` that picks its target with `c-is`. Rendering the
parent raises an error that names the child:

```citry-html
<!-- Fails when Row is simple = "vue" and Label is simple = True -->
<c-Label c-text="row['title']" />
```

Make `Label` an ordinary or `simple = "vue"` component, or call it from
an ordinary component.

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

With `simple = True`, a template can have an empty default outlet:

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

## Know what a `simple = True` component shares with its caller

With `simple = True`, an invocation gets no separate Python or Vue component
instance, render ID, component hooks, or slot hooks of its own. Its HTML is
rendered into the surrounding ordinary component instance. Component tags
authored inside its template use that ordinary component as their parent;
supplied content keeps the caller's Vue scope.

Ordinary HTML attributes, `c-bind` spreads, expressions, branches, loops and
native Vue bindings remain available to `simple = True`. Those Vue expressions
run in the surrounding ordinary component's instance scope. The class cannot
declare its own JavaScript, `js_data`, CSS or translation messages. Its ordinary
child components can still bring those features.

Direct tags execute their `template_data` callbacks at the normal deferred stage.
Python values execute when their expression inserts them. A direct root
render uses a framework owner, so rendering one simple component as an
entire page still has root setup cost. `<c-component>` can select a simple
class, but the selector keeps its own instance and hooks.

## Let invalid opt-ins fail early

Citry raises an error rather than silently rendering an incompatible class
as an ordinary component:

| Checked when | Unsupported examples |
| --- | --- |
| Class definition | A `simple` value other than `False`, `True`, or `"vue"`; instance data methods or lifecycle hooks. With `simple = True`, JS, CSS, messages, and instance configurations such as State, Events, Cache, Dependencies or I18n are also unsupported. |
| Template preparation | With `simple = True`, named or fallback outlets and unsupported custom or foreign-template nodes, including in inactive branches. With `simple = "vue"`, a child call that passes content, a `c-bind` spread, Vue bindings, or `#c-ignore`. Both simple modes reject `$c-tr` translation bindings. |
| Each invocation | With `simple = True`, explicit fills, component-level client bindings or `#c-key`/`#c-ignore` on the call, and unsupported Python slot names. With `simple = "vue"`, a template call to a `simple = True`, transparent or dynamic component. Both modes reject invalid inputs, returned data, and `$c-tr` keys arriving through an attribute spread. |

An empty asset string still declares an asset. The restrictions also apply
to inherited declarations and to targets chosen by a dynamic selector.
A caller's active translation catalog does not enable `$c-tr` inside a
simple template.

## Keep the checked class definition stable

`simple` defaults to `False`, accepts exactly `False`, `True`, or `"vue"`, and
inherits to subclasses. Each simple subclass is validated independently. The
flag and nested schema declarations cannot be rebound after class creation.
`simple = True` also freezes its checked class declarations; `simple = "vue"`
checks compatible declarations on use. Supported template file reset APIs
reload and recheck the template.

A subclass can explicitly declare `simple = False` to use the ordinary
component contract. [`LibraryComponent`][citry.LibraryComponent] also accepts
the flag; Citry checks the class when the library is materialized.

## Choose between simple rendering and reuse

`simple = True` removes independent component setup. It does not require
equal inputs between calls, and the data callback stays live.
[`pure = True`][citry.Component.pure] separately promises deterministic,
side-effect-free template behavior and can reuse equal bodies within one
root render. You can declare both when both contracts apply. A simple body
with a default outlet remains live even with `pure = True`.

Measure your own repeated-render workload before opting in. The benefit
depends on how much instance setup the component would otherwise do, and
how much time it spends producing its HTML.

## Related pages

- [Performance overview](/performance/) compares simple rendering,
  `Const`, pure bodies, and rendered output caching.
- [Component hooks](/advanced/hooks/) covers ordinary instance behavior.
- [Benchmarks](/about/benchmarks/) describes the measured workloads.
