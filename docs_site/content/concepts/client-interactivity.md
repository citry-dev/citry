---
title: Client interactivity
description: Understand Vue state, props, events, slots, and server-render lifecycle work in a Citry component.
---

# Client interactivity

Each interactive Citry component is a Vue component. The component's template
can read its Python-seeded data, local Vue state, props, setup bindings,
methods, computed values, and injections.

Use [Vue in templates](/syntax/vue/) for directive syntax. This page explains
how data and behavior cross Citry component boundaries.

## Seed browser data from Python

Return initial browser data from
[`Component.js_data()`][citry.Component.js_data]. Citry exposes every top-level
key as a reactive member of that component's Vue instance:

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

The returned value must be JSON-serializable. When an accepted server render
updates this component, Citry updates these keys on its live Vue instance.
Member assignment such as `this.count += 1` remains available for local
browser changes.

Choose distinct names for Python-seeded data and native Vue `data()`,
`setup()`, props, injections, methods, and computed values. Citry reports a
collision rather than silently overwriting a member.

## Define local Vue state and behavior

`$component({...})` accepts native Vue Options. Use `data()` for local mutable
state, `methods` and `computed` for behavior derived from that state, and
normal Vue lifecycle hooks when the work follows the component lifetime:

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

Citry also accepts Vue's synchronous `setup()` form. Composition API helpers
come from the exact runtime used by the page:

```js
$component({
  setup() {
    const selected = Citry.vue.ref(null);
    return { selected };
  },
});
```

## React after a server render

Use `onServerRender` when an integration must inspect the updated DOM or start
work again after Citry updates this component in an accepted server render:

```js
$component({
  onServerRender({ component, revision }) {
    const canvas = component.$refs.chart;
    if (!(canvas instanceof HTMLCanvasElement)) return;

    const chart = createChart(canvas, component.points);
    console.log("rendered revision", revision);
    return () => chart.destroy();
  },
});
```

Add the matching Vue ref to the template:

```citry-html
<canvas ref="chart"></canvas>
```

Citry calls the callback after this component mounts and after an accepted
server render updates it. An unrelated reactive update does not call it.
`component` is the live Vue public instance, and `revision` is the accepted
server revision. Citry runs the optional cleanup before the callback runs
again and when the component unmounts.

Reactive effects created synchronously during the callback share that cleanup
lifetime. Use `Citry.vue.watchEffect()` or another Composition API helper when
you need one. Work started later by a timer or Promise must arrange its own
cleanup.

The callback shorthand has the same arguments and cleanup behavior:

```js
$component(({ component }) => {
  component.$refs.input?.focus();
});
```

## Pass props to a child

Declare native Vue props in the child's `$component` options:

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

The parent passes a reactive value with `:` or `v-bind`:

```citry-html
<c-StatusBadge :status="currentStatus" />
```

A plain component attribute remains a Python component input. The Vue binding
prefix is what makes `:status` a browser prop.

## Listen to child events

Use Vue event bindings on the child component tag:

```citry-html
<c-ColorPicker @select="chooseColor" />
```

Declare and emit the event in the child's native Vue definition. This works
the same way when the child renders several roots:

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

The handler belongs to the parent that wrote the component call. The child
emits the event through Vue's normal component event API. Citry's `@c-*`
bindings are separate: they call declared Python event handlers on the server.
See [Event bindings](/events/bindings/) for that contract.

## Pass arbitrary HTML attributes explicitly

An ordinary attribute on a Citry component tag is a Python component input.
When a component should expose an HTML-attribute API, accept a mapping and
apply it to the intended element:

```citry-html
<c-Card c-attrs="{'class': 'featured', 'aria-label': label}" />
```

```citry-html
{# Inside Card #}
<article c-bind="attrs">
  <c-slot />
</article>
```

This is explicit for components with one root, several roots, or a nested
interactive element.

## Understand slot scope

Template-authored fill content keeps the Vue expression context of its call
site. A slot fallback uses the receiving component's context:

```citry-html
<c-Panel>
  <c-fill name="title">
    <span v-text="pageTitle"></span>
  </c-fill>
</c-Panel>
```

The fill can read `pageTitle` from the caller. The panel's fallback cannot.
See [Slots](/concepts/slots/) for the server-rendered composition rules.

## Work with one or several roots

Vue components may render one root, several roots, text, or no HTML element.
Do not assume `component.$el` is an `Element`. Add a template ref to the exact
element your JavaScript needs, then check its type before using it.

## See also

- [Vue in templates](/syntax/vue/) for directives and expressions.
- [Browser APIs](/reference/browser-apis/) for `$component`, `Citry.vue`, and
  the component Events helpers.
- [Event actions](/events/actions/) for server responses and page updates.
- [HTML fragments](/advanced/html-fragments/) for interactive fragments.
