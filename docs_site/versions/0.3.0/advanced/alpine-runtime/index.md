---
title: Alpine runtime
url: https://citry.dev/v/0.3.0/advanced/alpine-runtime/
description: "Configure Citry's owned Alpine runtime, register plugins, deploy client graphs safely, and understand CSP and structural-directive limits."
---
# Alpine runtime

Citry ships Alpine and the Alpine morph plugin as part of its browser runtime.
Citry owns plugin registration order, graph adoption, scope isolation, and the
single call to `Alpine.start()`.

Do not add another Alpine `<script>` tag or declare Alpine as a component
dependency. A foreign Alpine global produces a warning and Citry restores its
owned runtime. Evaluating Citry's own bundle twice preserves the first runtime
and its registrations instead of stacking permanent hooks.

## Register a plugin before startup

Use [`Citry.alpine.beforeStart`](/v/0.3.0/reference/browser-apis/#citry-alpine-before-start) to register a plugin
before startup:


```js
Citry.alpine.beforeStart((Alpine) => {
  Alpine.plugin(myPlugin);
});
```


The callback runs after Citry has installed its pinned Alpine object and
before Citry starts it. Register the callback in a script that executes before
the end of initial startup. A late `beforeStart` call throws a pointed error.

A plugin that assumes physical DOM ancestry is the only scope authority may
not work with source-linked slot content. Test plugins against nested
components, fills, fragments, and morphs before adopting them.

## Content Security Policy

A nonce can authorize Citry's inline script tags, but it does not remove
Alpine's expression evaluator requirement. The standard Alpine build used by
Citry currently requires `unsafe-eval` in `script-src` on pages that execute
Alpine expressions.

Citry does not currently support Alpine's CSP build. If your policy cannot
allow `unsafe-eval`, treat client-side Alpine expressions as unsupported for
that page. The Python expression sandbox is a separate server-side security
boundary; see [Security](/v/0.3.0/security/).

## Documents and fragments use the same graph

Any of these can activate Citry's client ownership graph:

- `Component.js` and [`$component`](/v/0.3.0/reference/browser-apis/#component);
- Alpine directives or component-tag Alpine handlers;
- component-tag client bindings, such as `$c-props="{ theme }"`,
  `@click="select()"`, or `@c-poll.5s="refresh()"` on a nested component tag;
- Events State, handlers, and bindings;
- active template fills whose client scope must be preserved.

For a component-tag client binding, the parent owns the expression or server
handler and the child supplies the component boundary where the browser
applies it.

Activation is not limited to components with JavaScript or CSS files. A
fragment carrying client-active ownership still needs the Citry routes mounted
so its graph, dependencies, and callbacks can be adopted atomically. See
[HTML fragments](/v/0.3.0/advanced/html-fragments/).

## Preserve client graph markers

Client-active output contains an inert ownership manifest and paired comments
similar to `<!--citry:g1:...:s-->` and `<!--citry:g1:...:e-->`. These pairs own
single-root, multi-root, and rootless ranges. They also let Citry reject a
partial graph before any callback observes it.

Configure HTML minifiers, CDN optimizers, sanitizers, streaming transforms,
and client DOM libraries to preserve:

- Citry ownership comments beginning with `citry:g1`, exactly and in order;
- `<script type="application/json" data-citry-graph>` and other Citry manifest tags;
- Citry `data-cid`, `data-cid-*`, `data-citry-*`, and compiled `data-cev-*` attributes.

Do not move a cap independently from its range, merge comments, or strip
comments as "unnecessary." Missing caps fail before graph activation with a
deployment diagnostic. Caps changed after activation cause the affected range
to retire rather than continue with ambiguous ownership.

## Structural Alpine directives

Stock Alpine `x-if`, `x-for`, and `x-teleport` work inside an already active
Citry component, including slot-source propagation and exact clone cleanup.
They cannot clone a server-rendered client-active Citry component. Such a
clone would need new graph IDs, Events anchors, state, props suppliers,
lifecycle resources, and physical cap ownership, which stock Alpine does not
mint.

Use server-side `<c-if>` and `<c-for>` around Citry component instances. Keep
native Alpine structural directives inside the component when their cloned
content does not contain another server-rendered client-active component.

## Debug browser failures

Read the first `[Citry]` browser-console error. Diagnostics identify the
component or render ID, the failed directive or handler when applicable, and
the required author or deployment fix. Common causes are:

- a second Alpine build on the page;
- invalid or asynchronous `$c-props` supply;
- stripped or moved graph comments;
- a fragment inserted without mounted Citry routes;
- a native Alpine structural directive cloning an active Citry component.

The [Debug extension](/v/0.3.0/reference/extensions/#citry-ext-debug-debug) visualizes server component and
slot boundaries, while [Troubleshooting](/v/0.3.0/guides/troubleshooting/) covers
render traces and browser symptoms.

## Browser support

The client conformance suite runs in Chromium, Firefox, and WebKit. The full
suite runs across all three engines on a schedule, with a compact graph and
resource-growth gate used for changes to the browser runtime.

## See also

- [Client interactivity](/v/0.3.0/concepts/client-interactivity/) for props, handlers, scopes, and lifecycle APIs.
- [JS and CSS dependencies](/v/0.3.0/advanced/js-and-css-dependencies/) for non-Alpine assets.
- [Compatibility](/v/0.3.0/about/compatibility/) for server and browser coverage.