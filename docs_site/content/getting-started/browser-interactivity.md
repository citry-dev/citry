---
title: Add browser behavior
description: Use Alpine directives in a Citry component, then pass Python data into component-owned browser code with js_data and $component.
---

# Add browser behavior

Everything you have built so far finishes in Python. Now you will add behavior
that responds immediately in the browser, without a request or page reload.

Citry uses [Alpine.js](https://alpinejs.dev/){: target="_blank" rel="noopener"} for these small interactions. You write [Alpine attributes](https://alpinejs.dev/essentials/templating){: target="_blank" rel="noopener"} in
the component's HTML, and Citry includes the browser code the rendered page
needs.

## Open and close a panel

Save this as `disclosure.py`:

```citry
from citry import Component

class Disclosure(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"details_id": f"disclosure-details-{self.id}"}

    template = """
      <section class="disclosure" x-data="{ open: false }">
        <button
          type="button"
          c-aria-controls="details_id"
          :aria-expanded="open"
          @click="open = !open"
        >
          Show details
        </button>
        <p c-id="details_id" x-show="open" x-cloak>
          Citry rendered this. Alpine opened it.
        </p>
      </section>
    """

    css = """
      [x-cloak] {
        display: none !important;
      }
    """


class DisclosurePage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Browser behavior</title>
        </head>
        <body>
          <c-Disclosure />
        </body>
      </html>
    """

print(DisclosurePage())
```

Create the HTML file, then open it in your browser:

```sh
python disclosure.py > disclosure.html
```

The details start hidden. Click “Show details” and the paragraph appears. The
button's [`aria-expanded`](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-expanded){: target="_blank" rel="noopener"} value changes at the same time.

## Follow the interaction

Five Alpine attributes work together:

- [x-data](https://alpinejs.dev/directives/data){: target="_blank" rel="noopener"} - `x-data="{ open: false }"` creates browser state for this section.
- [x-on](https://alpinejs.dev/directives/on){: target="_blank" rel="noopener"} - `@click="open = !open"` switches state when the button is clicked.
- [x-show](https://alpinejs.dev/directives/show){: target="_blank" rel="noopener"} - `x-show="open"` shows or hides the paragraph.
- [x-bind](https://alpinejs.dev/directives/bind){: target="_blank" rel="noopener"} - `:aria-expanded="open"` keeps the button's accessibility state in step with
  the visible panel.
- [x-cloak](https://alpinejs.dev/directives/cloak){: target="_blank" rel="noopener"} - hides the paragraph while Alpine starts. (Works with the small CSS rule)

`template_data()` uses [`self.id`][citry.Component.id] to give each rendered
disclosure a fresh panel ID. The `c-aria-controls` and `c-id` options use that
same value to connect the button to its own panel, even when a page contains
more than one disclosure.

Citry sees that the rendered component uses Alpine and includes its owned
browser runtime. You do not need a JavaScript entry file or a separate Alpine
setup for this page.

## Send a Python value to browser code

Plain Alpine is enough when all the data starts in the browser. Use
[`js_data()`][citry.Component.js_data] and [`$component`][$component] to pass
data from Python to JavaScript.

`$component()` is special Citry syntax inside a component's `js` block. It
connects that JavaScript to the component class and gives Citry a function to
run for each rendered instance. With each call, Citry passes in that instance's
Python data and its own reactive Alpine scope.

!!! note

    `js_data()` must return a dictionary that Citry can send as JSON. Use
    string keys and JSON-serializable values such as strings, finite numbers,
    booleans, `None`, lists, and nested dictionaries. Convert other Python
    objects to those types first.

Save this second example as `click_counters.py`:

```citry
from citry import Component

class ClickCounter(Component):
    class Kwargs:
        name: str

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"name": kwargs.name}

    template = """
      <button class="counter" type="button" @click="count += 1">
        <span class="counter__name" x-text="name"></span>
        clicked
        <span class="counter__count" x-text="count"></span>
        times
      </button>
    """

    js = """
      $component(({ data, scope }) => {
        // Pass data from Python to Alpine
        scope.name = data.name;
        scope.count = 0;
      });
    """


class CounterPage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Component data</title>
        </head>
        <body>
          <c-ClickCounter name="Ada" />
          <c-ClickCounter name="Grace" />
        </body>
      </html>
    """

print(CounterPage())
```

Create and open this page too:

```sh
python click_counters.py > click_counters.html
```

Both buttons begin at zero. Click Ada's button: Ada changes to one while Grace
stays at zero.

## Keep each component's data separate

Python sends the browser value through `js_data()`:

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"name": kwargs.name}
```

That value arrives as `data.name` inside the component's JavaScript. The
`$component` callback copies it into Alpine's reactive `scope` and creates the
counter:

```js
$component(({ data, scope }) => {
  scope.name = data.name;
  scope.count = 0;
});
```

Citry runs this callback once for Ada and once for Grace. Each rendered
component receives its own `data` and `scope`, so one click cannot change the
other counter.

The [Alpine runtime](/advanced/alpine-runtime/) page covers plugins, lifecycle,
security policy, and advanced configuration. The [Client
interactivity](/concepts/client-interactivity/) page covers everything
available inside `$component`.

## Pass browser data to a child

You can now use Alpine by itself and combine it with Python-provided data.
Next, [connect a parent and child component in the
browser](/getting-started/client-props-and-handlers/).
