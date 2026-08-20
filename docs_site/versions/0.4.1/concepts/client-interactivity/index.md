---
title: Client interactivity
url: https://citry.dev/v/0.4.1/concepts/client-interactivity/
description: "Understand which component owns browser data, handlers, props, slot content, and lifecycle work."
---
# Client interactivity

When a page becomes interactive, Citry keeps browser behavior attached to the
component that authored it. This matters whenever components are nested: DOM
elements may sit inside one another, but a child's private Alpine variables do
not automatically become part of the parent's scope.

Use this ownership map when deciding where code belongs:

- Markup inside a component's own template uses that component's scope.
- A handler written on a `<c-child>` tag belongs to the parent that wrote it.
- A fill keeps the scope of the template that supplied it.
- A slot fallback uses the scope of the component that defined the slot.

This page explains the component boundary. For Alpine directives and magics,
see [Alpine in components](/v/0.4.1/syntax/alpine/). For runtime loading, plugins, CSP,
and deployment, see [Alpine runtime](/v/0.4.1/advanced/alpine-runtime/).

## Seed the component scope from Python

Return initial browser data from
[`Component.js_data()`](/v/0.4.1/reference/component/#citry-component-js-data). Citry makes every top-level
key available directly to Alpine expressions in that component:


```citry
from citry import Citry, Component

c = Citry()


class Counter(Component):
    citry = c

    class Kwargs:
        start: int = 0

    def js_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, int]:
        return {"count": kwargs.start}

    template = """
      <button
        type="button"
        @click="increment()"
        x-text="count"
      ></button>
    """

```


The value returned by `js_data()` must be JSON-serializable. Use strings,
numbers, booleans, `null`-equivalent `None`, lists, and dictionaries with
serializable contents. Convert dates, model instances, and other Python
objects before returning them. Identical JSON stays deduplicated in transport,
but each component instance gets a fresh nested graph.

## Initialize component JavaScript

Add [`$component`](/v/0.4.1/reference/browser-apis/#component) when the component needs setup code. Citry
seeds `scope` first, then calls the initializer once per live render:


```js
$component(({ data, scope }) => {
  console.log(data.count, scope.count);
  scope.increment = () => {
    scope.count += 1;
  };
});
```


The callback can replace seeded values or add client-only fields. On a
compatible rerender, Citry refreshes the keys owned by the new server payload,
removes formerly seeded keys that are now absent, and preserves other fields
the callback added. Treat `data` as the current snapshot and make ongoing
reactive changes through `scope`.

The setup callback receives:

- `data`: the fresh instance-local value returned by `js_data()`, or `null`;
- `scope`: the stable component-local Alpine scope, already seeded from `data`;
- `props`: reactive read-only values accepted from the parent;
- `els`: the component's current root elements;
- `state`: the Events State facade, or `null`;
- `reactive` and `effect`: Alpine reactivity managed by Citry;
- `provide`, `inject`, and `unprovide`: descendant context helpers;
- `sendEvent` and `onEvent`: instance-scoped Events helpers;
- `loading` and `error`: read-only accessors for the instance's handler calls;
- `id` and `graph`: render and ownership information.

`reactive(object)` returns a reactive proxy. An `effect(callback)` runs its
callback immediately, tracks reactive values read during that run, and runs it
again when those values change. Citry stops managed effects when that live
render is replaced or removed.

Setup must finish synchronously. Return a cleanup function for resources you
create outside Citry's managed helpers:


```js
$component(({ els }) => {
  const chart = makeChart(els[0]);
  return () => chart.destroy();
});
```


On a compatible rerender, Citry stops effects, runs the cleanup, and calls the
setup again with fresh server data. The logical component scope and the `els`
array keep their identity.

## Pass client props down

Use [`$c-props`][$c-props] on a component tag when the parent should pass live
browser values or callbacks to the child:


```citry-html
<c-chart
  $c-props="{
    theme: selectedTheme,
    onSelect: (value) => choose(value),
  }"
/>
```


The expression runs in the parent's scope and must synchronously return a
plain object. The child declares what it accepts in its `$component` setup:


```js
$component({
  props: {
    theme: {
      type: String,
      default: "light",
    },
    onSelect: {
      type: Function,
      required: true,
    },
  },
  init: ({ props, scope, effect }) => {
    scope.select = props.onSelect;
    effect(() => updateTheme(props.theme));
  },
});
```


The child must contain a `$component(...)` registration whenever `$c-props`
remains on the resolved component call. Citry checks the actual selected target
for dynamic `<c-component>` calls and raises during rendering if that target
has no registration. A final `None` or `False` from `c-$c-props` or `c-bind`
removes the binding, so no registration is required.

Props are reactive and read-only at the top level. Copy a callback or derived
operation onto `scope` when the child's own template needs to call it.

Citry reports missing required props, type mismatches, thrown expressions,
Promises, arrays, and other non-plain results in the browser. A later valid
value can recover normally.

With the Citry language server, a direct `$c-props="{...}"` object on a
statically named child is checked while you type. Unknown keys, omitted
required props, and incompatible proven value types point back to the child's
static `props` declaration. A spread can supply any required key, so it
suppresses only the omitted-key check. The Python-dynamic form below remains a
runtime contract because its JavaScript source is not known until rendering.

The Python-dynamic form is also valid:


```citry-html
<c-chart c-$c-props="props_expression" />
```


Here the Python expression returns a string containing the Alpine expression.
A `c-bind` mapping may contain a `$c-props` key too. If several forms provide
the same client binding, the last one in source order wins.

## Send events up from a component tag

Alpine and Citry handlers written on a child component tag belong to the
parent's scope:


```citry-html
<section x-data="{ selected: false }">
  <c-action-button
    x-on:click="selected = true"
    @c-save="saveSelection({ selected })"
  />
</section>
```


`x-on:click` and its `@click` shorthand are equivalent. Both run an ordinary
Alpine expression. The `@c-*` form calls a declared Python event handler; its
optional value is an Alpine expression that returns the handler arguments.
Both forms above can read the parent's `selected` value.

Physical event values still point at the child root that received the event.
That includes `$el`, `$event`, `$dispatch`, and `event.currentTarget`.

If the child's own markup needs to call parent behavior, pass a callback with
`$c-props`, declare it as a `Function`, and expose it from the child's setup. A
handler on the component tag does not grant the parent access to private child
scope.

## Pass arbitrary HTML attributes explicitly

`$c-props`, Alpine event handlers, and `@c-*` handlers have special
component-boundary behavior. Other attributes, including `x-show`, `x-model`,
`:class`, `x-transition`, and `class`, are ordinary Python component kwargs.
Citry does not guess which child element should receive them.

Accept a dictionary when your component should expose an HTML-attribute API,
then apply it at the intended element:


```citry-html
<c-card
  c-attrs="{
    'x-show': 'visible',
    ':class': '{ selected: selected }',
  }"
/>
```



```citry-html
<article c-bind="attrs">
  <c-slot />
</article>
```


This stays unambiguous for multi-root components and components whose public
attributes belong on a nested element.

## Understand slot scope

Template-authored fill content keeps the browser scope of its call site. A
slot's fallback content uses the receiving component's scope:


```citry-html
<section x-data="{ pageTitle: 'Reports' }">
  <c-panel>
    <c-fill name="title">
      <span x-text="pageTitle"></span>
    </c-fill>
  </c-panel>
</section>
```


The fill can read `pageTitle` even though `<c-panel>` has its own component
scope. It keeps that access when Citry updates the component later.

Slot content passed from Python cannot read private Alpine values from a
surrounding component. On an interactive page, it starts with an empty Alpine
scope, so pass in any values it needs. Rendering that content by itself does
not load Citry's browser runtime.

See [Slots](/v/0.4.1/concepts/slots/) for the server-rendered composition rules.

## Single, multi-root, and rootless components

For a component with several root elements, `els` lists every root in document
order. A handler written on the component tag listens on all of them. Citry
still treats it as one handler: `.once` runs only once across the roots, and
timing modifiers share one timer.

A component may also render no HTML elements. Its `els` array is then empty,
but setup, props, effects, cleanup, Events State, and polling still work.
When optimizing production HTML, follow the
[client-active HTML checklist](/v/0.4.1/advanced/alpine-runtime/#preserve-client-active-html).

An Alpine handler or DOM-event `@c-*` handler on a component tag needs a real
child element to receive the event. If that component renders no elements,
Citry reports the problem and leaves the handler inactive. It does not add a
wrapper. `$c-props`, setup, effects, cleanup, State, and `@c-poll` continue to
work.

## See also

- [Event bindings](/v/0.4.1/events/bindings/) for `@c-*`, State bindings, loading, and
  errors.
- [Event actions](/v/0.4.1/events/actions/) for server responses and browser actions.
- [Browser APIs](/v/0.4.1/reference/browser-apis/) for the exact helper contracts.
- [HTML fragments](/v/0.4.1/advanced/html-fragments/) for live HTML updates.
- [Troubleshooting](/v/0.4.1/guides/troubleshooting/) for browser diagnostic fixes.