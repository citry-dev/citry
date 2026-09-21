---
title: Add browser behavior
description: Use Vue directives in a Citry component, then seed reactive browser data from Python with js_data.
---

# Add browser behavior

Everything you have built so far finishes in Python. Now add behavior that
responds immediately in the browser, without a request or page reload.

Citry mounts interactive components with [Vue](https://vuejs.org/){: target="_blank" rel="noopener"}.
Python gives each counter its name, [`js_data()`][citry.Component.js_data]
seeds its reactive state, and Vue directives update the visible count.

## Build independent counters

Save this example as `click_counters.py`:

<c-live-code path="docs_site/live_snippets/click_counters.py" title="Independent click counters" />

Create the page and open it:

```sh
python click_counters.py > click_counters.html
```

Both buttons begin at zero. Click Ada's button: Ada changes to one while Grace
stays at zero.

## Follow the interaction

Two Vue directives connect the button to its state:

- [`@click="count = count + 1"`](https://vuejs.org/guide/essentials/event-handling.html){: target="_blank" rel="noopener"}
  updates the count when the button is selected.
- [`v-text`](https://vuejs.org/api/built-in-directives.html#v-text){: target="_blank" rel="noopener"}
  writes the current name and count into their spans.

The directives tell Citry that this page needs its browser runtime. You do not
need a separate JavaScript entry file or Vue setup.

## Seed component data from Python

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"name": kwargs.name, "count": 0}
```

`js_data()` must return a dictionary containing JSON-serializable values.
Citry makes each top-level key reactive in that component instance. Each
counter gets its own data graph, so clicking Ada cannot change Grace.

Use [`$component`][$component] when a component also needs Vue Options such as
methods, props, emitted events, or lifecycle work:

```js
$component({
  methods: {
    reset() {
      this.count = 0;
    },
  },
});
```

The [Client interactivity](/concepts/client-interactivity/) guide documents the
complete `$component` contract. Keep [Vue in templates](/syntax/vue/) nearby
for syntax.

## Next steps

Next, [connect a parent and child component in the browser](/getting-started/client-props-and-handlers/).
