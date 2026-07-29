---
title: Client interactivity
url: https://citry.dev/v/0.3.1/concepts/client-interactivity/
description: "Use Citry's Alpine runtime, component scopes, client props, boundary handlers, slots, and lifecycle APIs without breaking component isolation."
---
# Client interactivity

Citry includes and starts a pinned Alpine runtime when a rendered page needs
client behavior. Components remain the ownership boundary: each active
component has its own reactive scope, and nested components do not inherit the
child-local variables of their parents merely because their elements are
nested in the DOM.

This page covers the author-facing contract. For loading, plugins, CSP, and
deployment, see [Alpine runtime](/v/0.3.1/advanced/alpine-runtime/).

## Initialize a component once per live render

Define client behavior with `Component.js` and
[`$component`](/v/0.3.1/reference/browser-apis/#component). Citry registers the callback once per component
class, then calls it for every live instance after the ownership graph,
props, and parent initialization are ready.


```citry
from citry import Component


class Counter(Component):
    template = """
      <button @click="count += 1" x-text="count"></button>
    """
    js = """
      $component(({ scope }) => {
        scope.count = 0;
      });
    """
```


The callback receives:

- `id`: the current server render ID;
- `els`: one stable array containing every current element root;
- `data`: the inert value returned by `js_data()`;
- `graph`: the current ownership route and source metadata;
- `state`: the Events State facade, or `null`;
- `props`: the reactive read-only declared props;
- `scope`: the stable component-local Alpine scope;
- `effect` and `reactive`: lifecycle-managed Alpine helpers;
- `provide`, `inject`, and `unprovide`: rendered descendant context;
- `sendEvent` and `onEvent`: instance-scoped Events helpers.

Initialization is synchronous. Return a cleanup function for resources that
are not registered through a managed helper:


```js
$component(({ els }) => {
  const chart = makeChart(els[0]);
  return () => chart.destroy();
});
```


On a compatible rerender, Citry stops managed effects, runs the cleanup, and
calls the initializer with fresh render data while preserving the logical
component scope and the `els` array identity.

## Pass client props down

`$c-props` passes a reactive client-side object from a parent-authored
component tag to its child:


```html
<c-chart $c-props="{ theme: selectedTheme, onSelect: (value) => choose(value) }" />
```


The expression runs in the parent's scope and must synchronously return a
plain object. The child declares the fields it accepts:


```js
$component({
  props: {
    theme: { type: String, default: "light" },
    onSelect: { type: Function, required: true },
  },
  init: ({ props, scope, effect }) => {
    scope.select = props.onSelect;
    effect(() => updateTheme(props.theme));
  },
});
```


Props are read-only at the top level. Copy a value or callback into `scope`
when child-authored Alpine markup should use it. Invalid declarations, missing
required values, type mismatches, thrown expressions, Promises, arrays, and
other non-plain objects produce pointed browser diagnostics. A later valid
value recovers normally.

`$c-props` is one kind of **component-tag client binding**: a browser-side
binding resolved from a nested `<c-*>` tag. The parent owns its data or handler,
while the child supplies the component boundary where Citry applies it. Alpine
event handlers such as `@click` and Citry handlers such as `@c-save` or
`@c-poll.5s` are the other kinds.

The Python-dynamic form is also valid:


```html
<c-chart c-$c-props="props_expression" />
```


Here `props_expression` is a Python value containing the Alpine expression
string. A `c-bind` mapping may contain a `$c-props` key too. When several
forms supply the same component-tag client binding, source order decides the
winner.

## Send events up from a component tag

Alpine and Citry handlers authored on a child component tag belong to the
parent's scope:


```html
<section x-data="{ selected: false }">
  <c-action-button
    @click="selected = true"
    @c-save="saveSelection({ selected })"
  />
</section>
```


The Alpine handler is an ordinary client expression. The `@c-*` value names a
declared server event handler, optionally followed by an Alpine expression
that returns its argument object. Both execute with parent-owned variables.
Physical event values such as `$el`, `$event`, `$dispatch`, and
`event.currentTarget` still refer to the child root that received the event.

If child-authored markup should invoke a parent callback, pass that callback
through `$c-props`, declare it as `Function`, and expose it deliberately from
the child's initializer. A handler placed on the component tag does not grant
access to the child's scope.

## Pass arbitrary HTML attributes explicitly

Only `$c-props`, Alpine event handlers, and `@c-*` handlers have special
component-boundary behavior. Other names, including `x-show`, `x-model`,
`:class`, `x-transition`, and `class`, are ordinary Python component kwargs.
Citry does not implicitly copy them onto a root element.

For a reusable attribute API, accept a dictionary and let the child decide
where it belongs:


```html
<c-card c-attrs="{ 'x-show': 'visible', ':class': '{ selected: selected }' }" />
```



```html
<article c-bind="attrs"><c-slot /></article>
```


That choice remains explicit for multi-root components and for components
whose public attributes belong on a nested element.

## Understand slot scope

Template-authored fill content keeps the client scope of the call site. A
slot's fallback content uses the receiving component's scope. This remains
true when the rendered nodes move across component boundaries or survive a
compatible morph.

Detached Python content does not invent a source component. If it participates
in an already active client graph, it receives an isolated empty base scope;
detached content alone does not activate the client runtime.

See [Slots](/v/0.3.1/concepts/slots/) for the server-side API.

## Single, multi-root, and rootless components

For a multi-root component, `els` contains every live root in document order.
Component-tag handlers behave as one logical listener group across those
roots, including shared `.once`, outside, global, and timing behavior.

A rootless component has an empty `els` array but still owns its scope, props,
initializer, effects, cleanup, Events State, and polling lifetime through
Citry's boundary comments. Those comments are load-bearing deployment data;
see the [rootless deployment checklist](/v/0.3.1/advanced/alpine-runtime/#preserve-client-graph-markers).

A component-tag Alpine handler or DOM-event `@c-*` handler still needs a real
child element to receive the native event. When the child is rootless, Citry
reports a pointed placement diagnostic and leaves that handler dormant; it
does not add a wrapper or invent an event target. If a later compatible update
gives the same logical child an element root, the handler activates there.
`$c-props`, initialization, effects, cleanup, State, and `@c-poll` continue to
work while the component is rootless.

## See also

- [Event bindings](/v/0.3.1/events/bindings/) for `@c-*`, State bindings, loading, and
  errors.
- [Event actions](/v/0.3.1/events/actions/) for rendered updates and browser actions.
- [Direct event routes](/v/0.3.1/events/http/) for server-handler security.
- [Alpine runtime](/v/0.3.1/advanced/alpine-runtime/) for plugins, CSP, loading, and deployment.
- [HTML attributes](/v/0.3.1/concepts/html-attributes/) for Python-side attribute merging.
- [HTML fragments](/v/0.3.1/advanced/html-fragments/) for client graph adoption.
- [Troubleshooting](/v/0.3.1/guides/troubleshooting/) for browser diagnostic fixes.