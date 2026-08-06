---
title: Provide and inject
description: Make shared data available to a rendered subtree without passing it through every component in between.
---

# Provide and inject

Use provide and inject when several descendants need the same surrounding
information, but the components between them do not. A page can provide its
theme once, for example, and a deeply nested label can read it without every
intermediate component accepting and forwarding a `theme` kwarg.

The server and browser each have a provide/inject channel. Start with the
server model, which applies while Citry renders HTML. The browser version uses
the same nearest-provider idea after that HTML reaches the page, but it holds
separate JavaScript values.

## Provide a value to server-rendered descendants

[`<c-provide>`](/reference/builtins/#c-provide) wraps the part of the render
tree that should receive a value. It adds no HTML of its own:

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

The provider stores fields under the key `theme`. The descendant reads the
nearest matching payload with
[`Component.inject()`][citry.Component.inject]. Its fields are immutable and
available through attribute access, such as `theme.name`.

Static attributes are strings. Prefix an attribute with `c-` to evaluate a
Python expression, or use `c-bind` to add a mapping:

```citry-html
<c-provide
  key="request_context"
  c-user="current_user"
  c-bind="feature_flags"
>
  <c-dashboard />
</c-provide>
```

The key can be dynamic too:

```citry-html
<c-provide c-key="context_key" c-value="current_value">
  <c-reader />
</c-provide>
```

Server keys must be non-empty valid Python identifiers.

## Provide from Python

Call [`Component.provide()`][citry.Component.provide] in a data method when
Python is the clearest place to assemble the fields. The value becomes visible
to descendants rendered by that component:

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

The key argument is positional-only, so `key` may also be one of the provided
field names.

## Follow the rendered path

A value reaches descendants along the path where Citry renders them. It is not
limited to tags literally nested in the same template file. If a provider
wraps `<c-slot>`, components in the surrounding template's fill can inject
that value too.

When providers use the same key, the nearest one wins for its whole subtree.
It replaces the outer payload rather than merging with it. Providers with
different keys remain available together.

The component that establishes a value cannot inject its own new value during
the same render. Its `inject()` still sees an inherited value, if one exists.
The new value is outgoing to descendants.

Provided fields also do not become template variables. A field named `mode`
does not change `{{ mode }}`. A descendant must call `inject()` and deliberately
return anything its own template needs.

## Handle a missing value

Without a default, a missing key raises `KeyError`:

```python
theme = self.inject("theme")
```

Pass a default when absence is valid:

```python
theme = self.inject("theme", None)
locale = self.inject("locale", "en")
```

An explicit `None` is a real default and does not raise.

## Stop an inherited value

[`Component.unprovide()`][citry.Component.unprovide] makes an inherited key
appear missing to descendants. The current component can still read the old
value before setting that boundary:

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

A descendant can establish a new `tabs` provider below the boundary. This is
useful for compound components whose inner instance must not accidentally join
the outer instance. The [`SlotInput`][citry.SlotInput] declaration lets the
boundary wrap that descendant without accepting unknown named fills.

## Keep server and browser values separate

Server provide/inject and browser provide/inject do not share storage. A value
provided by Python is available while HTML renders; `$inject()` in the browser
cannot read it automatically. Likewise, a JavaScript value does not appear in
`Component.inject()` on a later request.

When both sides need the same information, cross the boundary deliberately.
For example, return JSON-compatible data from
[`js_data()`][citry.Component.js_data], then provide that value during the
component's browser setup.

## Provide and inject in client code

The [`$component` hook][$component] receives `provide`, `inject`, and
`unprovide` helpers:

```js
$component(({ reactive, provide, inject, unprovide }) => {
  const inherited = inject("theme", null);
  const theme = reactive({
    name: inherited?.name ?? "light",
  });

  provide("theme", theme);
  unprovide("outerTabs");
});
```

Alpine expressions use [`$provide`][$provide], [`$inject`][$inject], and
[`$unprovide`][$unprovide]:

```citry-html
<section x-init="$provide('theme', { name: 'dark' })">
  <output x-text="$inject('theme').name"></output>

  <div x-init="$unprovide('theme')">
    <output
      x-text="$inject('theme', { name: 'system' }).name"
    ></output>
  </div>
</section>
```

The nearest-provider and outgoing-only rules match the server model. The value
shape is different: JavaScript provides one value rather than a set of keyword
fields, and `inject()` returns that exact value.

Establish or remove client providers during synchronous initialization. When
the shared data must change later, provide one stable `reactive()` object and
mutate its fields. Descendant expressions and managed effects can then react
to those changes without replacing the provider.

Client keys may be non-empty strings or symbols. A missing key without a
default raises a browser error; an explicitly provided `undefined` still
counts as a provided value.

## Next steps

- [Slots](/concepts/slots/) explains how fills keep the surrounding template's
  scope while they follow the rendered path.
- [Client interactivity](/concepts/client-interactivity/) covers component
  ownership, setup, props, and lifecycle helpers.
- [Browser APIs](/reference/browser-apis/) lists the exact client helper and
  Alpine magic contracts.
