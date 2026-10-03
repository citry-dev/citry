---
title: Vue in templates
description: Add immediate browser behavior to Citry component templates with Vue directives and expressions.
---

# Vue in templates

Some parts of a page should react the moment the user acts: a click opens a
panel, typing updates a preview, a button counts up. Waiting for the server to
render again would be slow and unnecessary. For these, write
[Vue](https://vuejs.org/){: target="_blank" rel="noopener"} attributes in the
component's template. They run in the browser.

Citry adds Vue to the page as soon as one component on it uses Vue. You write
Vue's own attributes, such as `@click` and `v-show`, on the HTML in the
template, and define the component's browser data with `$component({...})` in
the component's `js`.

## Add a browser counter

In the component's `js`, call `$component({...})` and return the values the
browser keeps from a `data()` function, as in any Vue component. The
`template` holds the Vue attributes and can read and change `count`
directly:

```citry
from citry import Component


class Counter(Component):
    template = """
      <button type="button" @click="count += 1">
        Add one
      </button>
      <output v-text="count"></output>
    """

    js = """
      $component({
        data() {
          return { count: 0 };
        },
      });
    """
```

Each copy of the component on the page keeps its own `count`.

To start `count` from a Python value instead, return it from
[`js_data()`](/vue/component-options/#seed-browser-data-from-python).
[Vue in Citry](/vue/) explains what runs on the server and what runs in the
browser.

## Vue `v-*` directives { #use-vue-directives }

Vue attributes that start with `v-` are called directives. Vue also has short
forms for listening to events and setting attributes:

| Form | What it does |
| --- | --- |
| `v-text="label"` | Sets an element's text. |
| `v-show="open"` | Shows the element while the expression is true. |
| `v-if="ready"` | Adds or removes the element. |
| `v-for="item in items"` | Repeats the element in the browser. |
| `v-model="query"` | Keeps a form field and a value in step. |
| `@click="open = true"` | Short for `v-on:click="open = true"`. |
| `:disabled="busy"` | Short for `v-bind:disabled="busy"`. |

Modifiers stay in the attribute name. `@keydown.enter.prevent="submit()"`
listens for Enter and stops the browser's default action.

See Vue's
[template syntax guide](https://vuejs.org/guide/essentials/template-syntax.html){: target="_blank" rel="noopener"}
for every directive and modifier.

!!! warning "Citry rejects key names on non-keyboard events"

    Citry accepts a key name such as `.enter` or `.escape` only on
    `keydown`, `keyup`, and `keypress`. On any other event the template
    fails when it loads. Other events, such as `click`, have no key, so Vue
    would ignore `@click.enter` and run the listener on every click. The
    same applies to a `@c-*` binding such as `@c-click.enter`. To react to a
    key, listen to `keydown` or `keyup`, as in `@keydown.enter`. System keys
    such as `.ctrl` and mouse buttons such as `.left` still work on `click`.

!!! warning "Write directive names in lowercase"

    Write the `v-` prefix and Vue's own directive names in lowercase.
    `V-IF` and `v-If` fail when the template loads, on HTML elements and
    component tags alike, because Vue would read `V-IF` as a plain attribute
    and `v-If` as a custom directive named `If`. Names that start with `v-c-`
    or `v-citry-` fail too, because Citry keeps them for its own use.

!!! warning "Citry rejects Vue code from `c-bind`"

    Citry rejects a Vue directive, `:` binding, or `@` listener that comes
    from `c-bind` or is written with a `c-` prefix, such as `c-v-if`, and
    the page fails to render. Write the directive directly in the template,
    as in `v-if="open"`.
    [Security and CSP](/vue/csp/#c-bind-never-carries-vue-code) explains
    why.

## Choose `v-for` or `<c-for>`

Use `v-for` and `v-if` for HTML that the browser adds, removes, or repeats
inside one component:

```citry-html
<ul>
  <li v-for="item in items" :key="item.id" v-text="item.label"></li>
</ul>
```

Use `<c-for>` and `<c-if>` when the loop or condition creates Citry
components. Only Python creates Citry components, so a `v-for` cannot repeat
one; see [`v-for` on components](/vue/props-and-events/#repeat-a-component).

## `c-*` with `:` bindings { #combine-class-and-style-with-c-class-and-c-style }

`:class` adds to an element's classes rather than replacing them. Vue joins
it with `class`, and Citry joins it with `c-class` the same way:

```citry-html
<article
  class="card"
  c-class="{'card--done': task.completed}"
  :class="{ 'card--dragging': dragging }"
>
  ...
</article>
```

The card starts as `card card--done`, and Vue adds `card--dragging` while
`dragging` is true. `:style` works the same way with `style` and `c-style`.
Vue applies `:style` last, so it wins when both set the same property.

Every other attribute must be set in one place. Setting it from Python and
from Vue, such as `c-title` with `:title`, fails when the template loads:

```citry-html
<!-- Fails: Python and Vue both set `title`. -->
<a c-title="label" :title="hint">...</a>
```

Keep only `c-title` when Python decides the value. Keep only `:title` when
the browser should change it later, and send the starting value with
[`js_data()`](/vue/component-options/#seed-browser-data-from-python).

## Vue on component tags

A Citry component tag, such as `<c-StatusBadge>`, accepts Vue props,
listeners, `v-if`, `v-model`, and `v-show`.
[Props and events](/vue/props-and-events/#use-vue-directives-on-a-component-tag)
lists them and shows how a parent and child pass data and events.

## More about Vue in Citry

- [Vue in Citry](/vue/) explains how Citry runs Vue and which Vue version
  it ships.
- [Component options](/vue/component-options/) covers `$component({...})`:
  `data()`, `methods`, `js_data()`, lifecycle hooks, and `setup()`.
- [Content and slots](/vue/slots/) shows which Vue data slot content reads.
- [Plugins and the Vue app](/vue/plugins/) adds directives and components
  to every Vue app on the page.
- [Limits and errors](/vue/limits/) lists what Citry does not support and
  how to fix common template errors.
