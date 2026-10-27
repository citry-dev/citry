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

## Extra listener modifiers { #listener-modifiers }

Some listeners need to react to events outside their element, or should
not run on every keystroke. Citry adds five modifiers to Vue listeners on
HTML elements for this:

| Modifier | What it does |
| --- | --- |
| `.outside` | Runs the listener for an event that starts outside the element. |
| `.window` | Listens on `window`, for events such as `resize` or a key pressed anywhere. |
| `.document` | Listens on `document`, for events that bubble up from anywhere on the page. |
| `.debounce` | Runs once, with the last event, after 250 ms with no new event. |
| `.throttle` | Runs for the first event, then drops events for 250 ms, including the last one. |

Citry adds the listener when the element appears and removes it when the
element goes away. A listener that an event itself added, such as one on
a `v-if` menu that a click opens, ignores that click.

A menu that closes when you click elsewhere or press Escape:

```citry-html
<button type="button" @click="open = !open">
  Menu
</button>
<ul
  v-show="open"
  @click.outside="open = false"
  @keydown.escape.window="open = false"
>
  <li>Profile</li>
</ul>
```

A search field that searches 300 ms after the user stops typing, and a
scroll handler that runs at most once every 250 ms:

```citry-html
<input @input.debounce.300ms="search($event.target.value)">
<div @scroll.throttle="track">...</div>
```

To wait another time, write it after the modifier, as in
`.debounce.300ms` or `.throttle.2s`.

### When `.outside` runs

`.outside` skips an event if the element was hidden when the event began.
So in the menu above, the click that opens the list does not close it
again, and a click outside the open list closes it.

- An event counts as inside when it starts in the element or in anything
  inside it, including a shadow root. Content that `<Teleport>` moved
  elsewhere counts as outside.
- Hidden means: the element or an ancestor has `display: none` (as
  `v-show` sets), the element is `display: contents`, or it sits inside a
  closed `<details>` (outside its `<summary>`). An element with
  `visibility: hidden`, with `opacity: 0`, or with no size still counts as
  visible.
- `.outside` listens on `document`, so a listener between the clicked
  element and `document` that stops the event, such as `@click.stop` on a
  button, keeps it from running.
- `.outside` and `.document` hear only events that bubble up to
  `document`, unless `.document` also has `.capture`. For focus, use
  `focusin` and `focusout`.

### Debounced listeners

A debounced listener runs after the event has finished:

- `$event.currentTarget` is `null` by then. Read what you need from
  `$event.target`, such as `$event.target.value`.
- Calling `$event.preventDefault()` or `$event.stopPropagation()` in the
  listener does nothing. Put `.prevent` or `.stop` on the listener
  instead; they act on the event at once.
- If the element is removed before the wait ends, the listener does not
  run.
- If the component renders again during the wait, for example after a
  server event, the wait goes on, and the listener from the newest render
  runs.

A listener can use both `.throttle` and `.debounce`: Citry drops the
events inside the throttle wait, then debounces the rest.

### Modifier load errors

The template fails to load, with a message that names the problem, when a
listener that uses one of these five modifiers:

- sits on a component tag, `<template>`, `<slot>`, or `<component>` (put
  it on an element inside instead);
- combines two of `.outside`, `.window`, and `.document`;
- combines `.outside` with `.self`, `.capture`, or `.once`;
- combines `.passive` with `.prevent`;
- gives a time anywhere but right after `.debounce` or `.throttle`;
- gives a time that is not whole milliseconds or seconds, such as
  `.300MS` or `.500`; write `.300ms` or `.2s`;
- repeats a modifier;
- writes one of the five in capitals, such as `.Outside`.

Vue's own modifiers, such as `.stop`, `.prevent`, and key names like
`.escape`, combine with these. To give a key such as `.5` together with
`.debounce`, put the key first, as in `@keydown.5.debounce`.

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

!!! warning "Citry rejects Vue code from `c-bind`"

    Citry rejects a Vue directive, `:` binding, or `@` listener, or any
    name that starts with `.`, `^`, or `#`, that comes from `c-bind` or is
    written with a `c-` prefix, such as `c-v-if`.
    Rendering the template raises `citry.VueCodeError`, on every page,
    even one that does not use Vue. Write the directive directly in the
    template, as in `v-if="open"`.
    [Security and CSP](/vue/csp/#c-bind-never-carries-vue-code) explains
    why.

## Vue on component tags

A Citry component tag, such as `<c-StatusBadge>`, accepts Vue props,
listeners, `v-if`, `v-model`, and `v-show`.
[Props and events](/vue/props-and-events/#use-vue-directives-on-a-component-tag)
lists them and shows how a parent and child pass data and events. To
pass content into a named slot, use `<c-fill name="...">`, not Vue's
`<template #name>`; see
[`<template #name>` slots](/vue/slots/#vue-slot-syntax).

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
