---
title: Alpine runtime
url: https://citry.dev/v/0.4.1/advanced/alpine-runtime/
description: "Use Alpine with Citry, add plugins before startup, and keep client-active HTML intact in production."
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
[`$component`](/v/0.4.1/reference/browser-apis/#component), client props, event handlers, and Events state.
The same rules apply whether you render a whole document or an
[HTML fragment](/v/0.4.1/advanced/html-fragments/).

Do not add a separate Alpine `<script>` tag. Citry ships Alpine and the morph
plugin, registers its own browser features, and calls `Alpine.start()` once.
If Citry finds a foreign Alpine global, it warns and restores its own runtime.
If its own bundle runs twice, the first runtime and its registrations remain
in place.

## Add an Alpine plugin

Use [`Citry.alpine.beforeStart`](/v/0.4.1/reference/browser-apis/#citry-alpine-before-start) to register a plugin
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

## Use Content Security Policy

The standard Alpine build evaluates expression strings in the browser, so
pages using `security_csp="off"` or `"warn"` need `unsafe-eval` in
`script-src`. Set `security_csp="strict"` to select Citry's version-matched
Alpine CSP runtime and reject unsupported expressions before HTML is returned:


```python
app = Citry(security_csp="strict")
html = Page().render().serialize(csp_nonce=request_nonce)
```


The constrained evaluator supports ordinary property access, calls, arrays,
objects, and the documented Alpine directive transformations. It does not
support every JavaScript construct. In particular, move arrows, optional
chaining, template literals, and multi-statement logic to `Component.js`, then
call a scope method from the attribute. `citry check` and the Citry editor
extension report the pinned compatibility rule at the authored source.

Citry can also emit inline executable scripts for client-active output. There
is now a request-scoped serialization input that adds one CSP nonce to every
structured Citry script and inline style after dependency hooks have run:


```python
html = Page().render().serialize(csp_nonce=request_nonce)
```


The host still owns the matching response header and nonce generation. Raw
script and style tags authored directly in template HTML are not automatically
trusted. See [Security](/v/0.4.1/security/#apply-a-request-csp-nonce-centrally) for the
complete boundary.

A nonce authorizes specific tags, but it cannot remove the standard
evaluator's `unsafe-eval` requirement. Strict mode changes the evaluator as
well as validating final component output. Raw script and style elements,
native `on*` handlers, and `javascript:` URLs are rejected in the Citry render.

Strict fragments do not carry an executable preloader. Insert them only into a
base document that already installed Citry's CSP manager with the same document
nonce. The manager rejects runtime or nonce mismatches before adopting any
dependency. Without that manager, the inert fragment stays inactive. This is
separate from the server-side Python expression sandbox described in
[Security](/v/0.4.1/security/).

## Omit or forbid the browser runtime

Use `security_javascript="omit"` for a deliberate static rendering. Citry
keeps server HTML, authored Alpine attributes, and CSS, but emits no Alpine,
Events, component JavaScript, dependency preloader, or runtime manifest. The
attributes are inert, so test important content and controls for a useful
native fallback. An omit fragment emits CSS directly and does not need an
existing manager.

Use `security_javascript="forbid"` when a client requirement should fail the
serialization instead. The check applies above `deps_strategy`, so `simple`
and `ignore` cannot conceal a reached binding or JavaScript declaration. See
[Security](/v/0.4.1/security/#choose-how-much-javascript-citry-may-deliver) for the
complete mode contract and its interaction with strict CSP.

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

The [Debug extension](/v/0.4.1/reference/extensions/#citry-ext-debug-debug) can draw component and slot
boundaries. [Troubleshooting](/v/0.4.1/guides/troubleshooting/) covers the wider
server and browser investigation workflow.

## See also

- [Client interactivity](/v/0.4.1/concepts/client-interactivity/) for Alpine data,
  props, handlers, and component lifecycles.
- [HTML fragments](/v/0.4.1/advanced/html-fragments/) for inserting client-active
  output into an existing page.
- [Component JavaScript and CSS](/v/0.4.1/advanced/js-and-css-dependencies/) for
  non-Alpine assets.
- [Compatibility](/v/0.4.1/about/compatibility/) for supported browsers.