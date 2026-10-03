---
title: Provide and inject
description: Make shared data available to a rendered subtree without passing it through every component in between.
---

# Provide and inject

Sometimes a component deep in the page needs a value that only the page
knows, such as the current theme or the signed-in user. Passing it as an
input through every component in between is tedious, and those components
do not use it.

Instead, a component higher up provides the value, and any component inside
it injects it, meaning it reads the value directly. This page covers
providing values while Citry renders HTML on the server, then the separate
browser version for Vue code.

## `<c-provide>` and `inject()`

Wrap part of a template in [`<c-provide>`](/reference/builtins/#c-provide)
and give the value a `key`. The tag adds no HTML of its own:

```citry
from citry import Citry, Component

c = Citry()


class ThemeLabel(Component):
    citry = c

    def template_data(self, kwargs, slots) -> dict[str, object]:
        theme = self.inject("theme")
        return {"theme_name": theme.name}

    template = """
      <span>Theme: {{ theme_name }}</span>
    """


class Page(Component):
    citry = c

    template = """
      <c-provide key="theme" name="dark">
        <main>
          <c-theme-label />
        </main>
      </c-provide>
    """
```

`Page` provides a value under the key `theme` with one field, `name`.
`ThemeLabel` reads it with
[`Component.inject()`][citry.Component.inject] and returns what its own
template needs. The fields are read-only and read as attributes, such as
`theme.name`.

Plain attributes are strings. Use the `c-` prefix to pass the value of a
Python expression, or `c-bind` to add every entry of a mapping:

```citry-html
<c-provide
  key="request_context"
  c-user="current_user"
  c-bind="feature_flags"
>
  <c-dashboard />
</c-provide>
```

The key can come from an expression too, as in `c-key="context_key"`. A
key must be a valid Python name.

## `inject()` default value

When no component above provides the key, `inject()` raises `KeyError`:

```python
theme = self.inject("theme")
```

Pass a second argument when the value is optional. Citry returns it when
the key is missing:

```python
theme = self.inject("theme", None)
locale = self.inject("locale", "en")
```

## `provide()` from Python

Call [`Component.provide()`][citry.Component.provide] in a data method when
Python is the easier place to build the value. Components that this
component renders can inject it:

```citry
from citry import Citry, Component

c = Citry()


class UserName(Component):
    citry = c

    def template_data(self, kwargs, slots) -> dict[str, object]:
        account = self.inject("account")
        return {"name": account.display_name}

    template = """
      <strong>{{ name }}</strong>
    """


class AccountPage(Component):
    citry = c

    def template_data(self, kwargs, slots) -> dict[str, object]:
        self.provide(
            "account",
            display_name="Ari",
            can_export=True,
        )
        return {}

    template = """
      <header><c-user-name /></header>
    """
```

Keyword arguments become the read-only fields shown above. To provide an
object you already have, pass it as the one value after the key:

```python
self.provide("citry_i18n", locale_context)
```

The component that injects it receives that same object. One call takes
either the object or keyword fields, not both.

## Global provide

Pass `provides` to `render()` when every component in the page may need the
value:

```python
page = Page()
rendered = page.render(
    provides={"request": request},
)
```

Each key must be a valid Python name.

A `render()` call starts a new page with its own provided values. If a data
method renders another component directly by calling `render()`, that call
does not see the values from the page around it. Pass them again:

```python
def template_data(self, kwargs, slots):
    request = self.inject("request")
    summary = Summary()
    rendered = summary.render(
        provides={"request": request},
    )
    return {"summary": rendered}
```

## Which provider wins

When two providers use the same key, a component reads the nearest one above
it. The inner value replaces the outer one for everything inside it; their
fields are not merged. Values under different keys are all available.

"Above" follows where a component ends up on the page, not where its tag is
written. If a component wraps its `<c-slot>` in `<c-provide>`, a component
that the outer template passes into that slot can inject the value.

## `unprovide()` hides a key

[`Component.unprovide()`][citry.Component.unprovide] makes a key look
missing to the components inside this one. The component itself can still
read the old value before it calls `unprovide()`:

```citry
from citry import Component, SlotInput


class NestedTabsBoundary(Component):
    class Slots:
        default: SlotInput

    def template_data(
        self,
        kwargs,
        slots: Slots,
    ) -> dict[str, object]:
        outer_tabs = self.inject("tabs", None)
        self.unprovide("tabs")
        return {"outer_tabs": outer_tabs}

    template = """
      <c-slot />
    """
```

This helps when components can nest inside copies of themselves. Here, a
tab set placed inside another tab set's panel does not attach to the outer
tab set by mistake. A component inside the boundary can still provide a new
`tabs` value.

## Vue `provide`/`inject` { #provide-and-inject-in-client-code }

The browser has its own provide and inject, from Vue. Use Vue's `provide`
and `inject` options in `$component`. A parent provides a reactive object:

```js
$component({
  data() {
    return { theme: { name: "dark" } };
  },
  provide() {
    return { theme: this.theme };
  },
});
```

A component inside it declares what it injects, then reads it in its
template:

```js
$component({
  inject: {
    theme: {
      default: () => ({ name: "system" }),
    },
  },
});
```

```citry-html
<output v-text="theme.name"></output>
```

Vue's usual rules apply: the nearest provider wins. To share data that
changes later, provide one reactive object and change its fields. Vue's
Composition API helpers are available as `Citry.vue` when options are not
enough.

Only a component can provide a value in the browser. To hide an inherited
value from part of the page, wrap that part in a component that provides a
replacement under the same key.

## Pass a value to Vue

Server values and browser values are stored separately. A value provided in
Python is not visible to Vue's `inject`, and a value provided in JavaScript
is not visible to `Component.inject()`.

When the browser needs a server value, return it from
[`js_data()`][citry.Component.js_data] as JSON-compatible data, then
provide it from that component's `$component` options.

## Fix unexpected values

### Not a template variable

A provided field named `mode` does not change what `{{ mode }}` reads.
Provided values are not template variables. Call `inject()` in a data
method and return the value the template needs.

### Reads the outer value

A component's own `provide()` call affects only the components inside it.
If the component calls `inject()` with the same key, it gets the value
from a provider above it, if there is one.

## Next steps

- [Slots](/concepts/slots/) explains which variables a fill reads.
- [Client interactivity](/concepts/client-interactivity/) covers browser
  data, local Vue state, and props.
- [Browser APIs](/reference/browser-apis/) lists the exact client helpers.
