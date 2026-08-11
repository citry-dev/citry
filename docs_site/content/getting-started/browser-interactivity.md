---
title: Add browser behavior
description: Use Alpine directives in a Citry component, then seed its browser scope from Python with js_data.
---

# Add browser behavior

Everything you have built so far finishes in Python. Now you will add behavior
that responds immediately in the browser, without a request or page reload.

Citry uses [Alpine.js](https://alpinejs.dev/){: target="_blank" rel="noopener"}
for these small interactions. In this step, Python gives each counter its name,
`js_data()` seeds its browser state, and Alpine attributes update the visible
count.

## Build independent counters

Use [`js_data()`][citry.Component.js_data] to pass initial values from Python
directly into the component's Alpine scope. A `$component()` callback is only
needed when the component also has JavaScript setup to run.

!!! note

    `js_data()` must return a dictionary that Citry can send as JSON. Use
    string keys and JSON-serializable values such as strings, finite numbers,
    booleans, `None`, lists, and nested dictionaries. Convert other Python
    objects to those types first.

Save this example as `click_counters.py`:

<c-live-code
  path="docs_site/live_snippets/click_counters.py"
  title="Independent click counters"
/>

Create the page:

```sh
python click_counters.py > click_counters.html
```

Open `click_counters.html` in your browser.

Both buttons begin at zero. Click Ada's button: Ada changes to one while Grace
stays at zero.

## Follow the interaction

Two Alpine attributes connect the button to that browser state:

- [`@click="count += 1"`](https://alpinejs.dev/directives/on){: target="_blank" rel="noopener"}
  increases the count when a visitor selects the button.
- [`x-text`](https://alpinejs.dev/directives/text){: target="_blank" rel="noopener"}
  writes the current name and count into their spans.

The Alpine attributes tell Citry that this page needs its owned browser
runtime. You do not need a separate JavaScript entry file or Alpine setup.

## Use JS data directly in Alpine

Python sends the browser value through `js_data()`:

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"name": kwargs.name, "count": 0}
```

Citry seeds both top-level keys into the component's reactive Alpine scope, so
the template can use `name` and `count` directly. Each rendered component gets
a fresh nested value graph, even when identical JSON is sent only once.

Add `$component` later when the component needs JavaScript setup beyond data
seeding. Its `data` argument receives the same instance-local snapshot, and
its `scope` is already seeded before the callback runs:

```js
$component(({ data, scope }) => {
  console.log(data.name, scope.name);
  scope.reset = () => {
    scope.count = 0;
  };
});
```

Ada and Grace each receive their own scope, so one click cannot change the
other counter.

The [Alpine runtime](/advanced/alpine-runtime/) page covers plugins, lifecycle,
security policy, and advanced configuration. The [Client
interactivity](/concepts/client-interactivity/) page covers everything
available inside `$component`. Keep
[Alpine in templates](/syntax/alpine/) nearby as a concise syntax guide.

## Next steps

You can now combine Alpine attributes with Python-provided browser data. Next,
[connect a parent and child component in the
browser](/getting-started/client-props-and-handlers/).
