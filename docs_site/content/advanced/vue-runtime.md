---
title: Vue runtime
description: Use Citry's managed Vue runtime and preserve interactive component output in production.
---

# Vue runtime

Citry loads a pinned Vue runtime when rendered output needs browser behavior.
Write native Vue directives in component templates and register component
options with `$component({...})`. You do not need a separate Vue application
or build step for ordinary component behavior.

## Use Vue normally

Define local state and methods in the component's JavaScript:

```js
$component({
  data() {
    return { open: false };
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
  },
});
```

Then use that state in the component template:

```citry-html
<button type="button" @click="toggle">Toggle details</button>
<p v-show="open">Ships within two working days.</p>
```

Citry also activates Vue for Python-seeded `js_data()`, native props and
events, component JavaScript, and server Events state. The same ownership
rules apply to complete documents and [HTML fragments](/advanced/html-fragments/).

Do not mount another Vue application over Citry-managed output. Citry creates
the component types, validates the prepared component graph, and coordinates
accepted server revisions with the live instances. Composition API helpers
from the pinned runtime are available through `Citry.vue`.

## React to accepted server renders

Use the `onServerRender` option for work that must run after initial mount and
after an accepted server render updates that component:

```js
$component({
  onServerRender({ component }) {
    const input = component.$refs.search;
    if (!(input instanceof HTMLInputElement)) return;
    const selectAll = () => input.select();
    input.addEventListener("focus", selectAll);
    input.focus();
    return () => input.removeEventListener("focus", selectAll);
  },
});
```

Citry runs the returned cleanup before the callback runs again and when the
component unmounts. A normal local reactive update does not call this hook.

## Use Content Security Policy

Pass the request nonce when serializing:

```python
html = Page().render().serialize(csp_nonce=request_nonce)
```

Citry applies it to structured scripts and inline styles after dependency
hooks run. The host application still owns nonce generation and the matching
response header. Raw script and style tags written directly in template HTML
do not gain trust automatically. See
[Security](/security/#apply-a-request-csp-nonce-centrally) for the complete
policy boundary.

An interactive fragment relies on the compatible Citry runtime already
installed by its document. The fragment loader rejects incompatible runtime,
nonce, graph, and asset metadata before mounting the fragment.

## Omit or forbid JavaScript

Set `security_javascript="omit"` for deliberate static output. Citry keeps
server-rendered HTML and CSS but leaves Vue directives inert and emits no
component JavaScript, Events runtime, or interactive manifest.

Set `security_javascript="forbid"` when reaching browser behavior should fail
serialization. See
[Security](/security/#choose-how-much-javascript-citry-may-deliver) for the
delivery modes and their interaction with CSP.

## Preserve interactive HTML

For an interactive document, Citry keeps the authored document shell and
replaces the logical body UI with one generated Vue host element. It emits a
validated configuration script and the component and extension assets needed
to mount that host. An interactive fragment carries a descriptor for the
existing document runtime instead.

HTML minifiers, CDN optimizers, sanitizers, and streaming transforms must
preserve the generated host, configuration scripts, and fragment descriptors.
Do not rewrite the mounted host's descendants outside Vue. Citry validates
incoming definitions and occurrence metadata before publishing a server
revision.

## Choose the right loop or condition

Use Vue `v-if` and `v-for` for browser-owned HTML inside one component. Give
each repeated item a stable `:key`.

Use Python `<c-if>` and `<c-for>` when the branch or loop creates Python Citry
component instances. Vue does not run Python or create new server component
identities.

## Diagnose a runtime failure

Start with the first `[Citry]` error in the browser console. Common causes are
an incomplete fragment or asset, altered ownership metadata, an invalid
prepared definition, or browser code that moved a managed range outside its
owner. Later errors are often consequences of the first failure.

[Troubleshooting](/guides/troubleshooting/) covers the wider server and
browser investigation workflow.

## See also

- [Vue in templates](/syntax/vue/) for directives and expressions.
- [Client interactivity](/concepts/client-interactivity/) for data, props,
  events, slots, and lifecycle callbacks.
- [Component JavaScript and CSS](/advanced/js-and-css-dependencies/) for
  component-owned assets.
- [HTML fragments](/advanced/html-fragments/) for interactive fragment loading.
