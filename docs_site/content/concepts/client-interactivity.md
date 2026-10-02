---
title: Client interactivity
description: Understand Vue state, props, events, slots, and server-render lifecycle work in a Citry component.
---

# Client interactivity

Some interactions should happen in the browser without a call to the
server: opening a menu, counting clicks, switching a tab. For these, a Citry
component is also a Vue component. Python renders its HTML, and Vue makes it
interactive in the browser.

This page shows how to start a component with data from Python, add browser
state and behavior, and pass data and events between components. For the
directive syntax itself, such as `v-if` and `@click`, see
[Vue in templates](/syntax/vue/).

## Set data from Python { #seed-browser-data-from-python }

Return the starting data from
[`Component.js_data()`][citry.Component.js_data]. Each top-level key becomes
a reactive value that the template and the component's JavaScript can read
and change:

```citry
from citry import Component


class Counter(Component):
    class Kwargs:
        start: int = 0

    def js_data(self, kwargs: Kwargs, slots) -> dict[str, int]:
        return {"count": kwargs.start}

    template = """
      <button type="button" @click="increment">
        Add one
      </button>
      <output v-text="count"></output>
    """

    js = """
      $component({
        methods: {
          increment() {
            this.count += 1;
          },
        },
      });
    """
```

The returned data must be JSON-serializable. When the server renders the
component again, for example after an
[event handler](/events/) returns it, Citry updates these values in the
browser.

## Add state and methods

`$component({...})` takes standard Vue options. Use `data()` for state that
lives only in the browser, `methods` and `computed` for behavior, and Vue's
lifecycle hooks such as `mounted` for work tied to the component's life:

```js
$component({
  data() {
    return { open: false };
  },
  computed: {
    buttonLabel() {
      return this.open ? "Close" : "Open";
    },
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
  },
});
```

Vue's synchronous `setup()` works too. Take Composition API helpers such as
`ref` from `Citry.vue`, which is the Vue build the page uses:

```js
$component({
  setup() {
    const selected = Citry.vue.ref(null);
    return { selected };
  },
});
```

Give each value a different name from the others: the keys from
`js_data()`, `data()`, `setup()`, props, injected values, methods, and
computed values. When two of them share a name, Citry reports an error
instead of letting one hide the other.

## Pass props to a child

Declare Vue props in the child's `$component` options:

```js
$component({
  props: {
    status: {
      type: String,
      required: true,
    },
  },
});
```

The parent passes a browser value with `:` or `v-bind`:

```citry-html
<c-StatusBadge :status="currentStatus" />
```

The `:` prefix makes `status` a Vue prop that updates in the browser. A
plain attribute, such as `status="ok"`, is a Python input instead, used
when the server renders the component.

## Listen to child events

Put a Vue event listener on the child's tag:

```citry-html
<c-ColorPicker @select="chooseColor" />
```

The child declares the event and sends it with Vue's `$emit`:

```js
$component({
  emits: ["select"],
  methods: {
    choose(color) {
      this.$emit("select", color);
    },
  },
});
```

```citry-html
<button type="button" @click="choose('#7f56d9')">Purple</button>
<button type="button" @click="choose('#12b76a')">Green</button>
```

`chooseColor` runs in the parent, the component whose template contains the
`<c-ColorPicker>` tag.

This listener runs JavaScript in the browser. To run a Python handler on
the server when the child emits `select`, write `@c-select` instead; see
[Bind events in templates](/events/bindings/).

## Pass HTML attributes { #pass-arbitrary-html-attributes-explicitly }

A plain attribute on a component tag is a Python input. To let the template
that uses a component set
HTML attributes such as `class` or `aria-label`, accept a mapping as an
input and spread it onto the element that should get them:

```citry-html
<c-Card c-attrs="{'class': 'featured', 'aria-label': label}" />
```

```citry-html
{# Inside Card #}
<article c-bind="attrs">
  <c-slot />
</article>
```

## Forward attributes

In Vue, attributes and listeners that a component does not declare as props
or events are collected in `$attrs`. To place them on a specific child
rather than the component's outer element, set `inheritAttrs: false` and
spread `$attrs` there:

```js
$component({
  inheritAttrs: false,
});
```

```citry-html
<header>Wrapper content</header>
<c-Child v-bind="$attrs" />
```

Declared props and declared events do not appear in `$attrs`.

To attach an object of Vue listeners, use `v-on` with the object:

```citry-html
<c-Child v-on="listeners" />
```

## Understand slot scope

A fill, the content you put into another component's slot, reads Vue values
from the template you wrote it in. A slot's fallback reads values from the
component that defines the slot:

```citry-html
<c-Panel>
  <c-fill name="title">
    <span v-text="pageTitle"></span>
  </c-fill>
</c-Panel>
```

Here `pageTitle` comes from the outer component. `Panel`'s own values are
not visible inside the fill. [Slots](/concepts/slots/) covers the same rule
for Python expressions.

## React to a re-render { #react-after-a-server-render }

Use `onServerRender` for work that must run again each time the server
renders this component, such as drawing a chart into the new HTML:

```js
$component({
  onServerRender({ component }) {
    const canvas = component.$refs.chart;
    if (!(canvas instanceof HTMLCanvasElement)) return;

    const chart = createChart(canvas, component.points);
    return () => chart.destroy();
  },
});
```

Mark the element with a matching Vue `ref`:

```citry-html
<canvas ref="chart"></canvas>
```

Citry calls the function once the component first appears on the page, and
again each time the server renders it again. A change in browser state
alone does not call it. `component` is the component's Vue instance.

Reach elements through a `ref`, as above, not through `component.$el`. A
Vue component can render one root element, several, only text, or nothing,
so `$el` is not always the element you expect. Check the element's type
before you use it.

Return a cleanup function to undo the work. Citry runs it before the next
call and when the component is removed.

The callback can also be passed directly to `$component`:

```js
$component(({ component }) => {
  component.$refs.input?.focus();
});
```

!!! note "Cleanup for watchers, timers, and promises"

    Watchers and effects you create synchronously inside the callback, for
    example with `Citry.vue.watchEffect()`, are stopped with the cleanup
    automatically. Work that starts later, from a timer or after an
    `await`, is not stopped automatically. Stop it in your cleanup function.


## See also

- [Vue in templates](/syntax/vue/) for directives and expressions.
- [Browser APIs](/reference/browser-apis/) for `$component`, `Citry.vue`,
  and the full `onServerRender` arguments.
- [Event actions](/events/actions/) for what the server can do after a
  handler runs.
- [HTML fragments](/advanced/html-fragments/) for interactive fragments.
