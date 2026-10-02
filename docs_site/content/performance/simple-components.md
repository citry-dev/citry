---
title: Simple components
description: Render small display components faster by skipping the setup Citry does for each ordinary component.
---

# Simple components

A page made of many small components, such as a status label in every
table row, can spend more time setting up each component than producing
its HTML. For every ordinary component, Citry creates a Python object for
it (the component instance that `self` refers to), runs its lifecycle
hooks, and creates a separate Vue component for it in the browser.

Declare [`simple = True`][citry.Component.simple] on a component that only
turns its inputs into HTML. Citry then renders its template as part of
the component around it and skips that setup. The component gives up the
features that need an instance, such as hooks and its own JavaScript.

## Set `simple = True`

Set the flag on the class:

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

Use it like any other component: as a `<c-StatusLabel>` tag, as a
`StatusLabel(text="Ready")` value inserted from Python, or rendered on its
own. Its inputs are validated and read again on every call.

`simple = True` does not store output. Each call renders the template
again. To reuse output, see [Pure components](/performance/pure/) and
[Cache rendered output](/performance/caching/).

A `simple = True` component cannot have:

- lifecycle hooks or instance methods;
- `transparent = True`;
- its own `js`, `css`, `js_data`, `css_data`, or translation messages;
- nested configuration such as `State`, `Events`, `Cache`,
  `Dependencies`, or `I18n`;
- named slots or slot fallback content.

Citry raises an error when the class uses one of these, so a
`simple = True` component never silently renders the slow way. The component's template can still
use other components, and those keep all their features.

## Use a static method

By default the template receives the component's inputs. To compute
other values, write `template_data` as a static method that takes
`kwargs` and `slots`:

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

Citry runs it each time the component renders. With a `Kwargs` or `Slots` class it receives
a new instance of that class; without one, it receives a plain mapping.
Citry validates the inputs and the returned data as it does for an
ordinary component.

When you convert an existing component, the usual mistake is to keep an
instance method. A simple component has no instance, so there is no
`self` to pass:

```python
# Fails with simple = True: the method expects self.
def template_data(self, kwargs, slots):
    return {"text": kwargs.text.upper()}


# Works: a static method with the two input parameters.
@staticmethod
def template_data(kwargs, slots):
    return {"text": kwargs.text.upper()}
```

The method must be a plain synchronous function. Async methods,
generators, and other callable objects are rejected. Any other helper
method on the class must be static too; instance methods, class methods,
and properties are not supported.

## Accept slot content

A `simple = True` template can show content the caller passes in, through
one plain `<c-slot />`:

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

The caller passes the content as the tag's body:

```citry-html
<c-Inset><strong>{{ user_name }}</strong></c-Inset>
```

`user_name` comes from the caller's data, as it would with an ordinary
component. From Python, pass `Inset(slots={"default": "Ready"})`. A
`template_data` method receives the content as a `Slot` that has not
rendered yet, so it can render it or pass it to the template.

The slot rules are strict:

- The template can contain only `<c-slot />`: no name, fallback content,
  slot data, or `required` flag.
- The caller cannot use `<c-fill>`, not even for the default slot.
- A `Slots` class, if you declare one, can contain only
  `default`, with a default of `None`, and no custom constructor or
  factory.

## Uses the caller's scope

A `simple = True` call has no component instance, Vue component, or
hooks of its own, and no render ID (the value that identifies a
component in the browser). Its HTML becomes
part of the nearest ordinary component above it. That has three effects:

- Vue bindings in its template run in that ordinary component's scope.
- Component tags in its template get that ordinary component as their
  parent.
- Content passed into its slot keeps the caller's Vue scope.

Its template can still use HTML attributes, `c-bind` spreads,
expressions, `c-if`, `c-for`, and Vue bindings.

## Add Vue state { #give-a-simple-component-its-own-vue-state }

`simple = True` gives the component no browser state of its own. Any Vue
binding in its template, such as `@click`, runs in the scope of the
ordinary component around it.

Use `simple = "vue"` when the component needs its own Vue state and
JavaScript but still no Python instance. Citry skips the Python setup and
creates a separate Vue component in the browser:

```citry
from citry import Component


class Toggle(Component):
    simple = "vue"

    class Kwargs:
        label: str

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

Each `Toggle` on the page keeps its own `open` value and updates
`aria-expanded` on each click.

A `simple = "vue"` component can use:

- text, `c-if`, `c-for`, fixed `c-*` attributes, and `c-bind` objects;
- Vue bindings written in the template;
- its own `js` and `css`, and static `js_data` and `css_data` methods;
- calls to other components, as described in the next section.

It cannot use:

- slots, `transparent = True`, or `pure = True`;
- [provide and inject](/concepts/provide-and-inject/), lifecycle hooks,
  or translation messages;
- nested configuration such as `State`, `Events`, `Cache`, or `I18n`, or
  `js` and `css` entries in `Dependencies`.

Values that its template expressions produce must be JSON-like: strings,
numbers, booleans, lists, and dictionaries. The class must stay
registered with its `Citry` instance. Citry raises an error for an
unsupported class or value instead of rendering the component the
ordinary way.

Some app-wide features need a component instance. While any of them
applies, Citry renders `simple = "vue"` components the ordinary way:

- translation (i18n) settings passed to `Citry`;
- translation messages declared on any other registered component;
- an extension that handles component data or lifecycle hooks;
- an extension that changes element attributes through the
  `on_attrs_resolved` hook, used by this template.

The page shows the same HTML and the data method still runs once per
call; the component only loses its speed advantage.

## Call other components

A `simple = "vue"` template can call other components. Each child renders
the way its own class says: an ordinary child still gets its instance,
hooks, and assets, and a `simple = "vue"` child still skips its instance.

```citry
from citry import Component


class Row(Component):
    simple = "vue"

    class Kwargs:
        row: dict

    template = """
      <li>
        <button @click="open = !open">
          {{ row['title'] }}
        </button>
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

The page shows the same HTML whether `Details` is ordinary or
`simple = "vue"`, and the same HTML as if `Row` were ordinary.

A call from a `simple = "vue"` template passes only inputs:

- Each input is a static attribute or a `c-*` expression.
- `#c-key` is allowed, and required when `c-for` repeats the call.
- The call cannot pass content (a tag body or `<c-fill>`), a `c-bind`
  spread, or Vue bindings and events on the component tag (`@click`,
  `:prop`, `v-show`). Put those on an element inside the child, or call
  the child from an ordinary component.

The child cannot be a `simple = True` component, a transparent component,
or a `<c-component>` that chooses its target with `c-is`. Each of these
puts its HTML into its caller's template, which a `simple = "vue"`
template cannot hold. Rendering the parent raises an error that names the
child:

```citry-html
<!-- Fails when Row is simple = "vue"
     and Label is simple = True -->
<c-Label c-text="row['title']" />
```

Make `Label` an ordinary or `simple = "vue"` component, or call it from
an ordinary component.

Calls outside `c-if` and `c-for` are the fastest. Citry builds the browser
template (the template Citry sends to Vue) once and reuses it for every row, unless the parent defines
`css_data`. Calls inside `c-if` or `c-for` work too, but Citry builds the
browser template for each row from that row's values, so turning the page
into HTML takes longer.

An ordinary child has no Python parent in the `simple = "vue"` component.
Its `self.parent` is the nearest ordinary component above, and it
receives the values provided above that component.

Error messages still show the whole path, for example
`Page > Row > Details`.

## Find the failing check

Citry checks a simple component at three points and raises an error at
the first problem:

| Checked when | Examples of what fails |
| --- | --- |
| The class is defined | A `simple` value other than `False`, `True`, or `"vue"`; instance data methods or lifecycle hooks. With `simple = True`, also `js`, `css`, messages, and `State`, `Events`, `Cache`, `Dependencies`, or `I18n`. |
| The template is loaded | With `simple = True`, named or fallback slots and unsupported custom tags, even inside a `c-if` branch that never runs. With `simple = "vue"`, a child call that passes content, a `c-bind` spread, Vue bindings, or `#c-ignore`. Both modes reject `$c-tr` translation bindings. |
| Each call | With `simple = True`, `<c-fill>`, Vue bindings or `#c-key`/`#c-ignore` on the component tag, and unsupported slot names from Python. With `simple = "vue"`, a call to a `simple = True` component, a transparent component, or a `<c-component>` that uses `c-is`. Both modes reject invalid inputs, invalid returned data, and `$c-tr` keys passed through a `c-bind` spread. |

## Edge cases

### Empty declarations

The restrictions apply to everything the class inherits. An empty string
still counts as a declaration, so `css = ""` on a `simple = True` class
raises an error.

### Subclasses

`simple` is inherited. Citry checks each subclass on its own, and a
subclass can set `simple = False` to become an ordinary component.
[`LibraryComponent`][citry.LibraryComponent] accepts the flag too; Citry
checks the class when the library is loaded into an app.

### Later class changes

You cannot reassign `simple` or the nested `Kwargs` and `Slots` classes
after the class is defined. A `simple = True` class also rejects changes
to its other declarations. A `simple = "vue"` class allows them, and
Citry checks the class again on its next render. When hot reload or a
template reset reloads the template, Citry checks the new template too.

### Data method timing

For a component tag, the data method runs at the same point in the
render as an ordinary component's. For a value inserted from Python, it
runs when the expression that inserts it runs.

### Rendering it alone

Rendering a `simple = True` component as the whole page still costs the
setup that every page render has. The saving comes from many calls
inside a larger page.

### With `<c-component>`

`<c-component>` can choose a simple class. The `<c-component>` tag itself
keeps its own instance and hooks, and the chosen class still follows its
simple rules.

### Translations

A simple template cannot use `$c-tr`, even when its caller has a
translation catalog active.

### Combining with `pure`

A component can declare both `simple = True` and
[`pure = True`][citry.Component.pure] when both promises hold. Its data
method still runs on every call. A `simple = True` body that contains
`<c-slot />` renders again on every call, even with `pure = True`.
`simple = "vue"` cannot be combined with `pure = True`; every call
raises an error.

## Related pages

- [Performance overview](/performance/) compares simple components with
  the other ways to speed up rendering.
- [Component hooks](/advanced/hooks/) covers what an ordinary instance
  can do.
- [Benchmarks](/about/benchmarks/) compares page-load times with other
  frameworks.
