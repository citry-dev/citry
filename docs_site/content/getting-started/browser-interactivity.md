---
title: Add browser behavior
description: Use Vue directives in a Citry component, then seed reactive browser data from Python with js_data.
---

# Add browser behavior

Some interactions should respond at once, without asking the server: a
counter, a toggle, a menu that opens. So far everything you built finishes in
Python. In this step you add behavior that runs in the browser, with no
request and no page reload.

Citry uses [Vue](https://vuejs.org/){: target="_blank" rel="noopener"} for
browser behavior. You write Vue attributes in the template, and Python gives
each component its starting browser data.

## Build independent counters

Save this example as `click_counters.py`:

<c-live-code path="docs_site/live_snippets/click_counters.py" title="Independent click counters" />

Create the page and open it in a browser:

```sh
python click_counters.py > click_counters.html
```

Both buttons start at zero. Click Ada's button: Ada changes to one, and Grace
stays at zero.

## Update the page when the user clicks

Two Vue attributes, called directives, connect the button to its data:

- [`@click="count = count + 1"`](https://vuejs.org/guide/essentials/event-handling.html){: target="_blank" rel="noopener"}
  adds one to `count` when the button is clicked.
- [`v-text`](https://vuejs.org/api/built-in-directives.html#v-text){: target="_blank" rel="noopener"}
  writes the current name and count into their spans.

When Citry sees Vue directives in a template, it adds its browser code to the
page. You do not need a separate JavaScript entry file or Vue setup.

## Give each component its starting browser data

[`js_data()`][citry.Component.js_data] returns the data the component starts
with in the browser:

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"name": kwargs.name, "count": 0}
```

The values must be JSON-serializable. Vue watches each top-level key, and
when one changes, it updates the parts of the page that show it. Each counter
gets its own copy, so clicking Ada cannot change Grace.

## Add methods and other Vue options

When a component needs more than data, such as methods, props, emitted
events, or code that runs when it mounts, pass Vue options to
[`$component`][$component] in the component's `js`:

```js
$component({
  methods: {
    reset() {
      this.count = 0;
    },
  },
});
```

The next step uses this to connect two components. The [Client
interactivity](/concepts/client-interactivity/) guide documents everything
`$component` accepts, and [Vue in templates](/syntax/vue/) covers the template
syntax.

## Next steps

Next, [connect a parent and child component in the browser](/getting-started/client-props-and-handlers/).
