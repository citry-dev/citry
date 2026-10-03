---
title: Component JS and CSS
description: Give a Citry component its own JavaScript and CSS, send it data from Python, and see how both behave on the page.
---

# Component JS and CSS

A component often needs a little browser code or a few styles of its own: a
panel that opens and closes, a chart that draws itself, a banner in a color
the page chooses. Put that code on the component, in `js` and `css`. Citry
adds it to every page that renders the component, once per page however many
times the component appears.

This page covers code that belongs to one component. To add a library or a
shared file, see [Dependency files](/advanced/dependency-files/). To choose
where the tags go in the page, see
[Place JavaScript and CSS](/advanced/asset-placement/). For the Vue
attributes you write in templates, such as `@click` and `v-show`, see
[Vue in templates](/syntax/vue/).

## `js` and `css` attributes

```citry
from citry import Component


class Disclosure(Component):
    template = """
      <section class="disclosure">
        <button type="button" @click="toggle">
          Details
        </button>
        <div v-show="open">
          <c-slot />
        </div>
      </section>
    """

    js = """
      $component({
        data() {
          return { open: false };
        },
        methods: {
          toggle() {
            this.open = !this.open;
          },
        },
      });
    """

    css = """
      .disclosure {
        border: 1px solid #d0d5dd;
      }
    """
```

Python renders the HTML on the server. In the browser, each `Disclosure` on
the page becomes a [Vue](https://vuejs.org/){: target="_blank" rel="noopener"}
component with its own `open` value, and the CSS styles all of them.

## Call `$component` once

[`$component()`][$component] tells Citry how the component behaves in the
browser. It takes the same object of options as a Vue component, such as
`data`, `methods`, and `props`, and Citry applies it to every rendered copy
of the component. Pass a function instead when all you need is code that
runs after each server render; see
[`onServerRender` callback](#run-after-a-render).

Call it once, at the top level of the component's `js`:

- A `js` with no `$component()` call is fine. Its code runs, and
  [`js_data()`](#send-data-to-js) values still reach the template.
- A second call in the same script is ignored, without an error.
- A call that runs later, for example inside a `setTimeout` or an event
  listener, is too late. The page's Vue app does not start, so no
  component on the page responds, and the browser console shows an error.

## Share helpers

Code outside `$component()` runs once, when the browser loads the script,
not once for each copy of the component. Use it for constants and helper
functions that every copy shares:

```javascript
const formatter = new Intl.NumberFormat("en", {
  style: "currency",
  currency: "EUR",
});

$component({
  methods: {
    price(amount) {
      return formatter.format(amount);
    },
  },
});
```

Each component's script runs inside its own function, so its top-level
names do not clash with other scripts on the page.

A value that should differ between copies belongs in `data()`. A top-level
variable is shared, so every copy changes the same one:

```javascript
// Wrong: all copies on the page share one `count`.
let count = 0;

$component({
  methods: {
    add() {
      count += 1;
    },
  },
});
```

```javascript
// Right: each copy gets its own `count`.
$component({
  data() {
    return { count: 0 };
  },
  methods: {
    add() {
      this.count += 1;
    },
  },
});
```

## `$component()` options

`$component()` accepts the usual
[Vue options](https://vuejs.org/api/#options-api){: target="_blank" rel="noopener"}.
This section shows the ones most components use.
[Client interactivity](/concepts/client-interactivity/) shows how they
work together across components, including slots.

### `data()` and `methods`

`data()` holds values that change in the browser, `computed` derives
values from them, `methods` holds functions the template calls, and `watch`
runs code when a value changes:

```javascript
$component({
  data() {
    return { query: "" };
  },
  computed: {
    trimmed() {
      return this.query.trim();
    },
  },
  methods: {
    clear() {
      this.query = "";
    },
  },
  watch: {
    trimmed(value) {
      localStorage.setItem("last-query", value);
    },
  },
});
```

Inside these functions, `this` is the component's Vue instance. It also
carries the [`js_data()`](#send-data-to-js) values and the
[Events helpers](/reference/browser-apis/#component-events-helpers) such as
`$state`.

### `props` from a parent

A child component declares the props it takes:

```javascript
$component({
  props: {
    status: String,
  },
});
```

The parent passes a browser value with `:`:

```citry-html
<c-StatusBadge :status="currentStatus" />
```

`currentStatus` comes from the parent's `data()`, `setup()`, or `js_data()`.
A plain attribute such as `status="ok"` is a Python input instead; see
[Pass props to a child](/concepts/client-interactivity/#pass-props-to-a-child).

### `$emit` to a parent

A child declares the events it sends and sends them with `$emit`:

```javascript
$component({
  emits: ["select"],
  methods: {
    choose(color) {
      this.$emit("select", color);
    },
  },
});
```

The parent listens with `@` on the child's tag, and `chooseColor` runs in
the parent:

```citry-html
<c-ColorPicker @select="chooseColor" />
```

To run a Python handler instead, write `@c-select`; see
[Bind events in templates](/events/bindings/).

### `provide` and `inject`

A component can `provide` a value to every component inside it, which reads
it with `inject`. These are Vue's own options and are separate from
Citry's Python `<c-provide>`. See
[Vue `provide`/`inject`](/concepts/provide-and-inject/#provide-and-inject-in-client-code).

### Use `setup()`

Vue's `setup()` works when it is synchronous and returns a plain object.
Take the Composition API functions from [`Citry.vue`](#use-citry-vue):

```javascript
$component({
  setup() {
    const selected = Citry.vue.ref(null);
    return { selected };
  },
});
```

An `async` `setup()`, or one that returns a render function, fails when
the component first appears, and the page's Vue app stops. Move async work
into a lifecycle hook such as `mounted`.

### Lifecycle hooks

Vue's lifecycle hooks, such as `mounted`, `updated`, and `unmounted`, work
as in Vue. Citry also uses some of them, and runs its own code around
yours:

- `mounted` runs first, then the first
  [`onServerRender`](#run-after-a-render) call.
- In `beforeUnmount`, Citry first runs the `onServerRender` cleanup and
  removes the component's [`$onEvent`](/reference/browser-apis/#on-event)
  listeners, then calls yours.

### Unsupported options

Citry combines your options with the render function it generates from the
component's template, so a few Vue options do not apply:

- `mixins` and `extends` fail with an error that names the component.
  Write the data, methods, and computed values in the options directly.
- A `render` function or `template` option inside `$component()` is
  ignored, without an error. Citry builds the browser's render function
  from the component's Python `template`.
- A name that Citry already puts on the instance, such as `$state`, or a
  name that is also a `js_data()` key, fails with an error that names it.
  See [Reserved names](/advanced/vue-runtime/#names-citry-reserves-on-the-component-instance).

[Browser APIs](/reference/browser-apis/#component) lists every rule.

## Where each value goes

Each Python value goes to one place:

| Python | Reaches | Read it as |
| --- | --- | --- |
| `Kwargs` | The server only. Nothing is sent to the browser. | `kwargs.name` in Python methods |
| `template_data()` | The template, on the server | `{{ name }}` or `c-*` attributes |
| `js_data()` | The Vue instance, as JSON | `name` in Vue expressions, `this.name` in JS |
| `css_data()` | CSS custom properties | `var(--name)` in the component's CSS |
| [`State`](/events/state/) | The browser, through server events | `$state.name`, `this.$state.name` |

Vue props are separate from all of these: the parent component passes them
in the browser with `:name`.

A Vue expression cannot read a `template_data()` or `Kwargs` value. When
the browser needs one, return it from `js_data()` too.

## Send data to JS

Return a mapping from [`js_data()`][citry.Component.js_data] to give one
render's values to its JavaScript. Each key becomes a value on the Vue
instance, which the template reads by name and JavaScript reads as
`this.<key>`:

```citry
from citry import Component


class Sparkline(Component):
    class Kwargs:
        points: list[int]

    def js_data(self, kwargs: Kwargs, slots):
        return {"points": kwargs.points}

    template = """
      <canvas
        ref="canvas"
        width="120"
        height="30"
      ></canvas>
    """

    js = """
      $component({
        onServerRender({ component }) {
          // drawSparkline comes from a charting library.
          drawSparkline(component.$refs.canvas, component.points);
        },
      });
    """
```

Two sparklines on one page each get their own `points`. When the server
renders the component again, these values update in the browser, and
`onServerRender` draws the chart again; see
[`onServerRender` callback](#run-after-a-render).

A key must not start with `$` or `_`, and must not be `citryId`, because
Vue and Citry already use those names. Rendering a component that returns
such a key raises `ValueError`. Name keys the JavaScript way, such as
`itemCount`.

### JS data must be JSON

Citry sends `js_data()` values to the browser as JSON. Each value must be
one of:

- `str`, `int`, `bool`, or `None`;
- a `float` that is finite (`NaN` and infinity raise `ValueError`);
- a `list` or `tuple` (sent as a list) of these values;
- a `dict` with `str` keys and these values.

The top-level keys must be `str` too. Any other value raises an error when
you turn the render into HTML by calling `str()` or `.serialize()` on it.
That includes `datetime`, `Decimal`, `set`, enum members, subclasses of
`str` such as `Markup`, and dataclass or Pydantic instances nested inside
the data. The error names the component and the type:

```text
TypeError: js_data() of component 'Sparkline_c92051' returned an
unsupported value: data sent to the browser must contain only dicts,
lists, strings, numbers, booleans, and None, got datetime.
```

Convert such values in `js_data()` first:

```python
def js_data(self, kwargs: Kwargs, slots):
    return {
        "updatedAt": kwargs.updated_at.isoformat(),
        "total": str(kwargs.total),  # a Decimal
        "task": dataclasses.asdict(kwargs.task),
        "user": kwargs.user.model_dump(mode="json"),
    }
```

Returning a dataclass or Pydantic instance as the whole result works:
Citry turns its fields into the top-level keys. Values inside those fields
must still follow the rules above.

JavaScript numbers lose precision above 2^53, so send large IDs as
strings.

## `onServerRender` callback { #run-after-a-render }

Some code has to run again each time the server renders the component,
for example to connect a non-Vue widget to the new HTML. Put it in
`onServerRender`. Here the search box takes focus when the user presses
`/`:

```javascript
$component({
  onServerRender({ component }) {
    const onKey = (event) => {
      if (event.key !== "/") return;
      // Keep the "/" out of the search box.
      event.preventDefault();
      component.$refs.input.focus();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  },
});
```

`component` is the component's Vue instance, and `component.$refs.input`
is the element marked with `ref="input"` in the template.

Citry calls `onServerRender` after the component first appears on the
page, and again after each server render that updates it. A change made
only in the browser does not call it.

The callback may return a cleanup function. Returning anything else is an
error. Citry calls the cleanup before the next `onServerRender` call and
when the component is removed. At the same time it stops the watchers
that the callback created before it returned, and the listeners it added
with the [`onEvent`](/reference/browser-apis/#on-server-render-on-event)
member of its argument. A timer, or work that starts after an `await`,
must be stopped in your cleanup function.

Passing a function, as in `$component(callback)`, is short for passing
`{ onServerRender: callback }`. [Browser APIs](/reference/browser-apis/#on-server-render)
lists everything the callback receives, and how `async` callbacks work.

## What a render keeps

When an event handler returns the component and the server renders it
again, Citry updates the Vue component that is already on the page. It
does not create a new one:

- `data()` and `setup()` values keep what the browser set.
- `js_data()` values take the server's new values, replacing any change
  the browser made to them.
- Computed values update from the new values.
- `onServerRender` runs its cleanup, then runs again.

Vue creates a new component, which starts from `data()` again, when:

- the handler returns a different component in its place; see
  [`Render` another component](/events/actions/#swap-in-a-different-component);
- an element around it gets a different key in the new render, or a
  parent component is created again for one of these reasons;
- the user reloads the page.

When a component leaves the page, Vue runs its `beforeUnmount` and
`unmounted` hooks, after Citry's cleanup. A text field the user is typing
in keeps its text through a render in most cases; see
[Keep typed input](/advanced/vue-runtime/#keep-what-the-user-typed-across-renders).

## Use `Citry.vue` { #use-citry-vue }

`Citry.vue` is the Vue library the page already loaded, so a component
script can use Vue's functions without an import: `ref`, `reactive`,
`computed`, `watch`, `nextTick`, `h`, and the rest.

Use `this` for the component's own values and methods. Use `Citry.vue`
for Vue's functions, mostly inside `setup()` and in shared helpers:

```javascript
$component({
  methods: {
    async open() {
      this.expanded = true;
      // Wait until Vue has shown the panel.
      await Citry.vue.nextTick();
      this.$refs.panel.focus();
    },
  },
});
```

`Citry.vue.use()` installs a Vue plugin on every Vue app Citry creates.
See [Browser APIs](/reference/browser-apis/#citry-vue) for the details, and
[Customize Vue](/syntax/vue/#customize-the-vue-app) for plugins.

## Check JS code

The Citry editor extension and `citry check` read the code in `js`:

- In `$component()`, `this` has the component's type, including its
  `js_data()` keys, props, `data()`, methods, and computed values. See
  [Vue and component JS](/ide/vscode/#complete-vue-expressions-and-component-javascript).
- Reading `this.name` when the component has no such value is an error
  (`citry.component-js.unknown-member`). Citry reports it only when it can
  see all of the component's values in the source.
- `citry check --types` also reports TypeScript errors in the code. See
  [`check --types` typing](/cli/#check-types-with-typescript-and-ty).

## Send values to CSS

Return a mapping from [`css_data()`][citry.Component.css_data] to give one
render's values to its CSS. Each key becomes a CSS custom property that
you read with `var(--<key>)`:

```citry
from citry import Component


class Banner(Component):
    class Kwargs:
        color: str = "#fde68a"

    def css_data(self, kwargs: Kwargs, slots):
        return {"banner_color": kwargs.color}

    template = """
      <div class="banner">
        <c-slot />
      </div>
    """

    css = """
      .banner {
        background: var(--banner_color);
      }
    """
```

Citry marks the component's root element with a generated attribute and
sets the property only on the elements that carry it. Simplified,
`Banner()` renders:

```html
<style>
  .banner {
    background: var(--banner_color);
  }
</style>
<style>
  [data-ccss-b097b034] {
    --banner_color: #fde68a;
  }
</style>
<div class="banner" data-ccss-b097b034></div>
```

So the banner's background is `#fde68a`. Citry generates the attribute
name from the values, so do not write selectors against it. A
`Banner(color="#bfdbfe")` on the same page gets a different attribute and
its own color. Renders with the same values share one attribute and one
stylesheet.

The component needs its own `css` for this to work. Without it, Citry
drops the `css_data()` values without an error.

Each value must be a string, a finite number (not a boolean), or `None`,
which leaves the property empty. Any other value, such as a `bool` or a
`list`, raises `ValueError` when the component renders. A key must
be a string that is valid as the name of a custom property, without the
leading `--`. Citry quotes a string that contains spaces,
unless it starts with a CSS function such as `calc(...)` or `rgba(...)`.
It raises `ValueError` for a value that could break out of the generated
CSS, such as one with a top-level `;` or a `</style` end tag.

!!! warning "Keep secrets out of CSS data"

    Citry can deliver these values as a stylesheet at a URL. Anyone who
    has the URL can download it, so never put a secret in `css_data()`.

## Name CSS classes

Component CSS is not scoped to the component. Citry adds the rules to the
page as written, so `.label` in one component styles every `.label` on the
page, including those in other components.

Start every class name with the component's name, and name the parts and
variants after it:

```citry
class PriceBadge(Component):
    template = """
      <span
        class="price-badge"
        c-class="{'price-badge--high': high}"
      >
        <span class="price-badge__label">Price</span>
        {{ amount }}
      </span>
    """

    css = """
      .price-badge {
        padding: 0 0.5rem;
      }
      .price-badge__label {
        font-weight: 600;
      }
      .price-badge--high {
        color: #b42318;
      }
    """
```

This is the BEM naming style: `block__element` for a part and
`block--modifier` for a variant. Citry has no option that scopes component
CSS for you.

## `js_file` and `css_file`

Use `js_file` and `css_file` to keep the code in files next to the
component:

```citry
from citry import Component


class Calendar(Component):
    template_file = "calendar.html"
    js_file = "calendar.js"
    css_file = "calendar.css"
```

Citry finds these files the same way it finds `template_file`. Set either
`js` or `js_file`, not both, and either `css` or `css_file`. Setting both
raises `ValueError` when the class is defined.

## `JsData` and `CssData`

Declare a nested `JsData` or `CssData` class to have Citry check the names
that `js_data()` or `css_data()` returns. A missing or unexpected name then
raises `TypeError` when the component renders. Return either an instance of
the class or a plain dictionary:

```citry
class Sparkline(Component):
    class JsData:
        points: list[int]

    def js_data(self, kwargs: Kwargs, slots) -> JsData:
        return self.JsData(points=kwargs.points)
```

A plain annotated class checks names, not the type of each value. See
[Inputs and validation](/concepts/inputs-and-validation/) for schema styles
that also check types.

## How CSS loads

- **Once per page.** A component's CSS appears once, however many copies
  render. Two components with exactly the same CSS share one stylesheet.
- **Order.** Stylesheets from [dependency files](/advanced/dependency-files/)
  come first, then component CSS, in the order the components first
  render. When two rules conflict, give one a more specific selector
  rather than relying on the order.
- **Place.** By default the styles go at the end of `<head>`. See
  [Place JavaScript and CSS](/advanced/asset-placement/) to change it.
- **Media types.** Component CSS applies to every media type. To load a
  stylesheet only for print or another media type, use a
  [dependency file](/advanced/dependency-files/).
- **CSP nonce.** A nonce passed to `serialize(csp_nonce=...)` goes on every
  style tag Citry adds; see
  [Add a CSP nonce](/advanced/vue-runtime/#use-content-security-policy).

## When CSS is removed

On an interactive page, Citry tracks which components on the page use each
stylesheet. When a server render removes the last component that uses one,
Citry removes the stylesheet too, and adds it back if the component
returns. A stylesheet that other components on the page still use stays.

A component that disappears only in the browser, such as one inside a
`v-if` that turned false, keeps its stylesheet. So does every stylesheet
on a page without Vue, where nothing runs in the browser to remove it.

## Highlight inline code

JetBrains editors highlight a string in the language named by a comment
just above it:

```citry
class Calendar(Component):
    # language=HTML
    template = """
      <div class="calendar">Today</div>
    """

    # language=CSS
    css = """
      .calendar {
        width: 12rem;
      }
    """
```

Some VS Code extensions read type annotations instead, such as
`template: "html"`, `css: "css"`, and `js: "js"`. These hints change only
how the editor shows the code.

## Next steps

- [Client interactivity](/concepts/client-interactivity/) covers Vue
  props, events, and slots between components.
- [Browser APIs](/reference/browser-apis/) lists `$component`,
  `onServerRender`, and `Citry.vue` in full.
- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files that several components use.
- [Place JavaScript and CSS](/advanced/asset-placement/) chooses where the
  tags go in the page.
- [Component hooks](/advanced/hooks/) changes the tags one component adds.
- [HTML fragments](/advanced/html-fragments/) adds the JavaScript and CSS
  of new components to a page that is already open.
