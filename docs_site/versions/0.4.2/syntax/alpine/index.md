---
title: Alpine in templates
url: https://citry.dev/v/0.4.2/syntax/alpine/
description: "Add immediate browser behavior to Citry component templates with Alpine attributes and expressions."
---
# Alpine in templates

Use Alpine when part of a component should respond immediately in the browser.
A click can open a panel, an input can update a preview as someone types, and a
button can change local state without a request to Python.

Citry includes [Alpine.js](https://alpinejs.dev/){: target="_blank" rel="noopener"}
and starts it when the rendered page needs it. Write Alpine attributes directly
on the HTML inside a component. Do not add another Alpine script tag.

## Add a browser-side counter

This counter changes as soon as someone clicks the button:


```citry-html
<div x-data="{ count: 0 }">
  <button type="button" @click="count += 1">
    Add one
  </button>
  <output x-text="count"></output>
</div>
```


The three Alpine attributes divide the work:

- `x-data` creates the browser value `count`.
- `@click` changes it after a click.
- `x-text` inserts its current value into `<output>`.

Citry notices Alpine's standard `x-`, `@`, and `:` attributes in the rendered
HTML and includes its owned browser runtime. The interaction does not need a
`Component.js` block or a separate JavaScript entry file. Browser behavior
added only through JavaScript should use a
[`$component()` callback](/v/0.4.2/advanced/js-and-css-dependencies/#add-behavior-and-styles).

## Read the common Alpine forms

Alpine directives begin with `x-`. Its two common shorthands make browser
events and bound attributes easier to read:

| Form | Job |
| --- | --- |
| `x-data="{ open: false }"` | Create local browser data. |
| `x-show="open"` | Show an element when an expression is truthy. |
| `x-text="label"` | Insert text into an element. |
| `x-model="query"` | Keep a form control and a value in step. |
| `@click="open = true"` | Short for `x-on:click="open = true"`. |
| `:disabled="busy"` | Short for `x-bind:disabled="busy"`. |

Modifiers stay part of the attribute name. For example,
`@keydown.enter.prevent="submit()"` runs only for Enter and prevents the
browser's default action.

Use the [Alpine documentation](https://alpinejs.dev/start-here){:
target="_blank" rel="noopener"} for its complete directive, modifier, and magic
API.

## Write JavaScript in Alpine attributes

An Alpine attribute contains a JavaScript expression. A Citry `c-*` attribute
contains a Python expression:


```citry-html
<section
  c-class="{'has-results': results}"
  x-data="{ open: false }"
>
  <button type="button" @click="open = !open">
    Toggle details
  </button>
  <p x-show="open">Details</p>
</section>
```


Python decides the `class` while rendering the component. Later, Alpine owns
`open` in the browser and changes it without rendering the component again.
Python template names are not automatically available to Alpine, and Alpine
names are not automatically available to Python. `js_data()` is the explicit
way to expose Python-produced browser data.

Do not put `{{ ... }}` inside an Alpine expression. A static attribute keeps
those braces as literal text. When Alpine needs a starting value from Python,
pass it deliberately.

## Seed Alpine from Python

Return per-instance browser data from [`js_data()`](/v/0.4.2/reference/component/#citry-component-js-data).
Citry seeds every top-level key into this component's Alpine scope before any
Alpine expression runs:


```citry
from citry import Component


class Counter(Component):
    class Kwargs:
        start: int = 0

    class JsData:
        count: int

    def js_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> JsData:
        return {"count": kwargs.start}

    template = """
      <div>
        <button type="button" @click="count += 1">
          Add one
        </button>
        <output x-text="count"></output>
      </div>
    """
```


The returned data must be JSON-serializable: strings, numbers, booleans,
`None`, lists, and string-keyed
dictionaries made from those values. Use JavaScript naming in that object,
such as `itemCount`, even when its Python source is named `item_count`.

Add [`$component`](/v/0.4.2/reference/browser-apis/#component) only when the component also needs JavaScript
setup, managed effects, client props, or additional callback-owned scope data.
The [Add browser behavior](/v/0.4.2/getting-started/browser-interactivity/) tutorial
builds that path one step at a time.

## Keep Alpine data inside its component

HTML nested inside the same component follows Alpine's normal scope rules. An
active nested Citry component starts a separate component scope, so its own
template does not silently inherit the parent's `x-data` values.

An Alpine event handler on a child component tag is a deliberate exception.
The caller owns the expression, and Citry attaches the handler to the child's
rendered roots:


```citry-html
<section x-data="{ selected: false }">
  <c-ActionButton @click="selected = true" />
  <p x-show="selected">Selected</p>
</section>
```


Other Alpine attributes on a component tag are ordinary Python component
inputs. This does not copy `x-show` to the child's root:


```citry-html
<c-Panel x-show="open" />
```


Put the directive on a plain wrapper, or let the child accept an explicit
attribute mapping. To pass reactive values or callbacks across the component
boundary, use
[`$c-props`](/v/0.4.2/concepts/client-interactivity/#pass-client-props-down).

## Choose the right kind of loop

Alpine's `x-for`, `x-if`, and `x-teleport` work with browser-owned HTML inside
an active component. For example, Alpine can repeat a plain `<li>`:


```citry-html
<ul x-data="{ items: ['Ocean', 'Forest'] }">
  <template x-for="item in items">
    <li x-text="item"></li>
  </template>
</ul>
```


Do not use a native Alpine structural directive to clone an active Citry
component. The clone would not receive a new Citry identity, State, client
props, or lifecycle. Use server-side `<c-for>` and `<c-if>` around Citry
component tags instead.

Read [Alpine runtime](/v/0.4.2/advanced/alpine-runtime/#choose-the-right-kind-of-loop-or-condition)
for the complete structural-directive and deployment limits.

## Use Citry values from Alpine

When a component declares State, its Alpine expressions can read and write it
with `$state`. When it declares server events, Alpine can use the related
status and event magics:

- `$loading()` and `$error()`
- `$sendEvent()` and `$onEvent()`

Inside any active Citry component, Alpine can use the rendered-context magics
`$provide()`, `$inject()`, and `$unprovide()`.

The [Browser APIs reference](/v/0.4.2/reference/browser-apis/#alpine-magics) gives the
exact contract for each name. Continue to
[Client interactivity](/v/0.4.2/concepts/client-interactivity/) for component-owned
JavaScript, reactive client props, handlers, and lifecycle.

When the Citry language server knows the owning component, it treats unknown
free Alpine variables as errors by default. Names from `JsData`, `x-data`, an
enclosing `x-for`, synchronous `$component` scope writes, Alpine/Citry magics,
browser globals, and configured lint-only variables are included
automatically. The application or component lint policy can reduce unknown
names to warnings or ignore them for a deliberately open integration.

## TODO - Alpine attrs on Component
Not only event handlers, and our `$c-props`.

## TODO Alpine attrs on HTML elements
All allowed. `@c-` events and `$c-props`.