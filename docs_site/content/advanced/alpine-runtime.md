---
title: Alpine runtime
description: Use Alpine with Citry, add plugins before startup, and keep client-active HTML intact in production.
---

# Alpine runtime

Use Alpine when part of a component should respond immediately in the browser:
open a menu, switch a tab, or update text while someone types. Citry includes
Alpine, so you can write its normal attributes without installing or starting
another browser runtime.

This page covers the less common jobs around that setup: adding an Alpine
plugin, deploying through HTML optimizers, and understanding which DOM
operations can safely move Citry components.

## Use Alpine normally

Standard Alpine attributes activate Citry's browser runtime. That includes
attributes beginning with `x-`, `@`, and `:`:

```citry-html
<div x-data="{ open: false }">
  <button type="button" @click="open = !open">
    Toggle details
  </button>
  <p x-show="open">Ships within two working days.</p>
</div>
```

Citry also activates the runtime for its own browser features, including
[`$component`][$component], client props, event handlers, and Events state.
The same rules apply whether you render a whole document or an
[HTML fragment](/advanced/html-fragments/).

Do not add a separate Alpine `<script>` tag. Citry ships Alpine and the morph
plugin, registers its own browser features, and calls `Alpine.start()` once.
If Citry finds a foreign Alpine global, it warns and restores its own runtime.
If its own bundle runs twice, the first runtime and its registrations remain
in place.

## Add an Alpine plugin

Use [`Citry.alpine.beforeStart`][Citry.alpine.beforeStart] to register a plugin
before Citry starts Alpine:

```js
Citry.alpine.beforeStart((Alpine) => {
  Alpine.plugin(myPlugin);
});
```

Run this code during initial page loading. Calling `beforeStart` after Alpine
has started raises an error, because installing a plugin at that point would
leave existing components in an inconsistent state.

Some plugins assume that a value always comes from the nearest physical DOM
parent. Slotted content can keep the Alpine scope of the template that wrote
it, even when Citry renders it elsewhere. Test a plugin with nested
components, slots, fragments, and server-rendered updates before relying on it
across an application.

## Plan for Content Security Policy

The standard Alpine build evaluates Alpine expressions in the browser. Pages
that use those expressions currently need `unsafe-eval` in `script-src`.
Citry does not ship Alpine's CSP build.

Citry can also emit inline executable scripts for client-active output. There
is currently no page-wide Citry setting that adds a CSP nonce to every such
script. A nonce on one application script therefore does not, by itself,
authorize every script Citry may emit.

If your policy cannot allow `unsafe-eval` or the required inline execution,
treat Alpine and other Citry browser behavior as unavailable on that page.
This is separate from the server-side Python expression sandbox described in
[Security](/security/).

## Preserve client-active HTML

Citry adds small comments, attributes, and JSON manifests to client-active
HTML. They tell the browser which rendered nodes belong to each component,
including components with several root nodes or no element root.

Configure HTML minifiers, CDN optimizers, sanitizers, streaming transforms,
and DOM libraries to preserve:

- Citry ownership comments beginning with `citry:g1`, in order;
- Citry JSON manifest `<script>` elements;
- `data-cid`, `data-cid-*`, `data-citry-*`, and `data-cev-*`
  attributes.

Do not move or merge the ownership comments independently of the HTML between
them. If a tool strips or rearranges these markers, Citry rejects the affected
client graph instead of attaching behavior to the wrong nodes.

## Choose the right kind of loop or condition

Use Alpine's `x-if`, `x-for`, and `x-teleport` for ordinary browser-owned DOM
inside a component. For example, Alpine can repeat plain HTML that does not
contain another client-active Citry component.

Use server-side `<c-if>` and `<c-for>` when the repeated or conditional content
contains Citry component instances. Cloning already-rendered, client-active
component HTML would also clone its identity, state, event anchors, and
lifecycle resources. Stock Alpine directives cannot create fresh versions of
those values.

## Diagnose a browser failure

Start with the first `[Citry]` error in the browser console. Later errors are
often consequences of the first one. Common causes include:

- another Alpine build on the page;
- invalid or asynchronous `$c-props` data;
- ownership comments removed or moved during deployment;
- a fragment inserted without Citry's routes and runtime available;
- `x-if` or `x-for` cloning a client-active Citry component.

The [Debug extension][citry.ext.debug.Debug] can draw component and slot
boundaries. [Troubleshooting](/guides/troubleshooting/) covers the wider
server and browser investigation workflow.

## See also

- [Client interactivity](/concepts/client-interactivity/) for Alpine data,
  props, handlers, and component lifecycles.
- [HTML fragments](/advanced/html-fragments/) for inserting client-active
  output into an existing page.
- [Component JavaScript and CSS](/advanced/js-and-css-dependencies/) for
  non-Alpine assets.
- [Compatibility](/about/compatibility/) for supported browsers.
