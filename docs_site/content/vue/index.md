---
title: Vue in Citry
description: Make Citry components interactive in the browser with Vue, and see which values Python and Vue each control.
---

# Vue in Citry

Some interactions should happen in the browser without a call to the
server: opening a menu, counting clicks, switching a tab. For these, a Citry
component is also a [Vue](https://vuejs.org/){: target="_blank" rel="noopener"}
component. Python renders its HTML on the server, and Vue makes it
interactive in the browser.

## Add a browser counter

Write Vue attributes, such as `@click` and `v-text`, in the component's
`template`. In the component's `js`, call `$component({...})` with Vue's
component options. `$component` tells Citry how the component behaves in
the browser. Here `data()` returns the value the browser keeps:

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

## How Citry runs Vue

You write Vue directives, the Vue attributes such as `v-show` and
`@click`, in the template, and Vue options in `$component({...})`. Citry
does the rest:

- Citry compiles each template on the server into the code Vue uses to
  render it in the browser. There is no build step.
- Citry loads Vue in the browser, starts it on the HTML the server sent,
  and applies each new server render to the live page. See
  [Server-rendered HTML](/vue/server-rendering/).
- Citry creates the Vue app itself, so there is no Vue app for you to
  create. Do not mount another Vue app over Citry's output. To add a
  plugin or a global directive, see
  [Plugins and the Vue app](/vue/plugins/).

## When Vue turns on

Citry adds Vue to the page as soon as one component on it does any of
these:

- uses Vue directives in its template;
- has its own JavaScript;
- returns data from `js_data()`;
- uses Vue props or events;
- keeps [server-event](/events/) `State`.

Complete pages and [HTML fragments](/advanced/html-fragments/) work the
same way.

## Which Vue version

Citry ships Vue 3.5.42. Each Citry release bundles one fixed Vue version,
and you cannot swap in another. To check the version a page runs, enter
`Citry.vue.version` in the browser console.

## Tell Python from Vue { #tell-python-from-vue }

Citry runs `{{ ... }}` and `c-*` values as Python on the server, once per
render. Vue runs directive values as JavaScript in the browser. Both can
sit in one template:

```citry-html
<section c-class="{'has-results': results}">
  <button type="button" @click="open = !open">
    Toggle details
  </button>
  <p v-show="open">{{ details }}</p>
</section>
```

Python sets the class and inserts `details` once. After the page loads, Vue
changes `open`. Define `open` in `data()`, `setup()`, or
[`js_data()`](/vue/component-options/#seed-browser-data-from-python).

A Vue expression cannot see Python names. A common first attempt inside a
`c-for` loop reads the loop name from Vue, and no item gets a title:

```citry-html
<!-- Wrong: Vue looks for `item` in browser data. -->
<li c-for="item in items" :title="item">{{ item }}</li>

<!-- Right: Python sets `title` for each item. -->
<li c-for="item in items" c-title="item">{{ item }}</li>
```

`citry check` and the editor report the first form. They also report it
when the browser data has its own `item`: then every item shows that one
value, and nothing fails. When Vue needs the value too, for example in a
`v-show` that changes later, send it with `js_data()` or loop with Vue's
`v-for`.

## Choose `<c-if>` or `v-if` { #choose-c-if-or-v-if }

Use Vue's `v-if` and `v-for` for plain HTML that the browser adds,
removes, or repeats inside one component. Give each repeated item a
stable `:key`.

Use `<c-if>` and `<c-for>` when the branch or loop creates Citry
components. Only Python creates Citry components, on the server, so Vue
cannot create them in the browser. See
[Choose `v-for` or `<c-for>`](/syntax/vue/#choose-v-for-or-c-for) for an
example of each.

## Where each value goes { #where-each-value-goes }

Each Python value goes to one place:

| Python | Reaches | Read it as |
| --- | --- | --- |
| `Kwargs` | The server only. Nothing is sent to the browser. | `kwargs.name` in Python methods |
| `template_data()` | The template, on the server | `{{ name }}` or `c-*` attributes |
| [`js_data()`](/vue/component-options/#seed-browser-data-from-python) | The Vue instance, as JSON | `name` in Vue expressions, `this.name` in JS |
| [`css_data()`](/advanced/js-and-css-dependencies/#send-values-to-css) | CSS custom properties | `var(--name)` in the component's CSS |
| [`State`](/events/state/) | The browser, through server events | `$state.name`, `this.$state.name` |

[Vue props](/vue/props-and-events/#pass-props-to-a-child) are separate
from all of these: the parent component passes them in the browser with
`:name`.

A Vue expression cannot read a `template_data()` or `Kwargs` value. When
the browser needs one, return it from `js_data()` too.

## Vue pages

- [Vue in templates](/syntax/vue/): the `v-*` directives, `@` listeners,
  and `:` bindings you write in a template.
- [Component options](/vue/component-options/): `data()`, methods,
  `js_data()`, `onServerRender`, and the rest of `$component({...})`.
- [Props and events](/vue/props-and-events/): pass values to a child
  component and listen to the events it emits.
- [Content and slots](/vue/slots/): which component's Vue data the
  content you pass into a slot reads.
- [Server-rendered HTML](/vue/server-rendering/): what the page shows
  before Vue starts, and what it keeps when the server renders again.
- [Plugins and the Vue app](/vue/plugins/): add Vue plugins, global
  directives, and an error handler.
- [Security and CSP](/vue/csp/): use a Content Security Policy, or send
  no JavaScript at all.
- [Limits and errors](/vue/limits/): the Vue features Citry rejects, and
  how to find the cause of a failure.
- [Browser APIs](/reference/browser-apis/): the reference for
  `$component`, `onServerRender`, and `Citry.vue`.
