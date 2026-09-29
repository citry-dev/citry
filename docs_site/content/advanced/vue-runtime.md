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

Citry also starts Vue for Python-seeded `js_data()`, native props and
events, component JavaScript, and server Events state. Complete documents
and [HTML fragments](/advanced/html-fragments/) work the same way.

Do not mount another Vue application over Citry-managed output. Citry creates
the component types, validates the prepared component graph, and coordinates
accepted server revisions with the live instances. Composition API helpers
from the pinned runtime are available through `Citry.vue`.

## React to server renders the page applies

Use the `onServerRender` option for work that must run after initial mount and
after each server render that the page applies to this component:

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

In a Python event handler, return `actions.Render(...)` when the server should
update component output. Return `actions.Data(value)` (or a dictionary) when an
imperative `$sendEvent()` caller needs a result without rerendering. Declarative
`@c-*` calls do not expose a Data result to the browser.

## Keep what the user typed across renders

A text input, `<textarea>`, or `<select>` keeps the user's edit when its
component renders again, as long as the value the template gives it has not
changed. That holds for a constant value and for a value Python computes:

```citry-html
<input name="role" value="Owner" />
<input name="email" c-value="row['email']" />
```

Say the server sent `ada@example.com` and the user typed
`draft@example.com`:

- A local update, or a server render that sends `ada@example.com` again,
  leaves `draft@example.com` in the field.
- A server render that sends a different value, such as
  `new@example.com`, replaces the draft with it. The field always shows the
  server's latest value once that value changes.
- A `<select>` the user has not changed always shows the value the
  template gives it, even when a server render changes its options.

The same rule covers a `value` key that `c-bind` spreads onto the field. For
a constant, the value changes when a later server render uses a template that
writes a different constant.

A value bound to browser state with Vue's `:value`, including a `js_data`
value, works as it does in Vue: every render writes the state again. So does
a `value` inside an object you spread with Vue's `v-bind="..."`. Keep a draft that must survive those
renders in Vue state with `v-model`.

Checkboxes and radio buttons are not affected. Their `value` is not typed by
the user, and whether they are checked follows `v-model` or `c-checked` as
usual.

When a server render reorders keyed rows, each row keeps its elements, and the
field the user is typing in stays focused with its caret in place.

## Names Citry reserves on the component instance

Citry adds a few names to each component's Vue instance. Generated templates
and the Events helpers read them, so a component must not define a prop,
`data()` key, `setup()` binding, method, computed value, or injection with
these names:

- `$citryPrepared`, the values Python computed for Citry's generated
  template;
- `$citryEvents`, which connects `@c-*` handlers to the server;
- `$loading`, `$error`, `$state`, `$sendEvent`, and `$onEvent`, the
  [Events helpers](/reference/browser-apis/#component-events-helpers);
- the names that an installed browser extension adds, such as i18n helpers;
- `citryId`, a prop Citry adds to every component.

A `data()`, `setup()`, method, computed value, or injection with one of
these names stops the component when it mounts, with an error that names it.
Vue refuses a prop whose name starts with `$`, so only the other kinds of
names need care. `$citryPrepared` is internal and its contents can change
between releases, so do not read it from your own JavaScript. When your JavaScript
needs a value from Python, return it from
[`js_data()`](/reference/browser-apis/#js-data-members) and read it as
`this.name` or `component.name`.

A `js_data()` key cannot start with `$` or `_`, because Vue and Citry own
those instance names, and it cannot be `citryId`. Rendering such a component
raises a `ValueError` that names the component and the key, before any HTML
is sent, so rename the key (`_count` to `count`). A `js_data()` key that
matches one of the component's own props, `data()`, `setup()`, method, computed, or
injection names is only detected in the browser, where the component stops
when it mounts.

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
component JavaScript, Events client, or app data.

Set `security_javascript="forbid"` when reaching browser behavior should fail
serialization. See
[Security](/security/#choose-how-much-javascript-citry-may-deliver) for the
delivery modes and their interaction with CSP.

## Send page content in the served HTML

An interactive document's content is in the HTML the server sends, so
search engines, link previews, and readers without JavaScript see it. You
do not need to turn anything on.

Citry sends the content in one of two ways:

- **Vue adopts the server's HTML.** The server writes the page exactly as
  Vue's first render in the browser creates it, and Vue adopts those nodes
  ("hydrates") instead of building every element again. The browser can lay
  the page out while it is still parsing.
- **Vue replaces the server's HTML.** When the server cannot write the page
  the way Vue would, the Vue host (the element Citry generates for Vue to
  mount into) carries Citry's ordinary server HTML, the
  same HTML a static page gets. Vue clears it and builds the page when it
  starts.

The server writes each component by running its compiled Vue render
function over the same data the browser receives. Loops, `c-if` branches,
slots, nested components, spreads (`c-bind`), Python-bound attributes such
as `c-checked`, forms, tables and Python text are written this way. HTML
you insert as one finished block, such as `<c-raw>` contents or a `Markup`
value that contains tags, is written unchanged, and Vue adopts its nodes as
they are.

Vue starts only after the browser has read the whole page, so the served
content can appear before the browser spends time starting the app. Citry
sends the app's data as JSON that the browser reads without running it, and
starts the app from a one-line module script (`<script type="module">`),
which the browser runs once parsing finishes. Your own `defer` and module
scripts placed before Citry's scripts run before Vue starts. Listen for the `citry:ready` event when your script
needs the finished page.

### Send a page without its content

Two settings send an empty Vue host and let Vue build the page in the
browser. Use them only for pages that search engines and readers without
JavaScript do not need, such as a signed-in dashboard.

- `Citry(ssr=False)`, or `serialize(ssr=False)` for one serialization,
  sends every page without its content.
- `ssr_element_threshold` sends a page without its content when the server
  would write that many elements or fewer. A small page can be slightly
  faster this way, because the browser does not parse the HTML and then
  hydrate it. The default, `0`, keeps the content of every page that
  contains at least one element. The setting applies only to pages Vue
  can adopt; a page Vue replaces always carries its server HTML.

```citry
from citry import Citry, Component

app = Citry(ssr_element_threshold=5_000)

class Page(Component):
    citry = app
    template = """
<main>Ready</main>
"""
    js = """
$component({});
"""

html = Page().render().serialize(ssr=False)
```

`ssr_element_threshold` must be a non-negative `int`. Another type raises
`TypeError` and a negative value raises `ValueError` when the engine is
created.

### Pages Vue replaces instead of adopting

The page is sent with Citry's ordinary server HTML, and Vue replaces it,
when it uses a Content Security Policy, a JavaScript policy, script
integrity, a configured i18n extension, custom `on_dependencies` methods,
or extension dependency, serialization or browser hooks, or places assets
with a `deps_position` other than the default. The same happens when no
element separates a browser-only part from the top of the page (see the
next section) and when the browser's HTML parser would rearrange the
written HTML.

That HTML is what a static page shows, so before Vue starts:

- both branches of a `v-if` and `v-else` can be visible, and `v-show`,
  `:class` and other Vue bindings have no effect yet;
- Vue directive attributes such as `@click` stay in the HTML, where the
  browser ignores them.

When Vue starts, it clears the host and builds the page in the same step,
so the browser never paints an empty page between the two. Vue creates new
elements, so focus, a text selection, and text typed before Vue started are
lost, and an `<iframe>` or `<video>` loads again.

Under a Content Security Policy whose `style-src` does not allow inline
styles, the browser blocks each `style` attribute in the served HTML and
reports it. Vue then applies the same styles through the DOM, which the
policy allows. Allow `'unsafe-hashes'` with the style hashes, or move the
styles to component CSS, if the reports are a problem.

A page with a JavaScript policy is sent without its content, because the
policy would report every Vue attribute in that HTML. So is a page under
a Content Security Policy whose served HTML the policy would reject, such
as an `onclick` attribute or a `javascript:` link: sending it would make a
page that serializes cleanly fail or warn.

A page Vue replaces is sent without its content when its body contains a
`<script>` element, for example inside trusted HTML such as `<c-raw>`
contents,
because the browser would run that script while parsing the page, and a
page Vue builds never runs it.

HTML fragments are always built in the browser.

### Parts Vue builds in the browser

Some values exist only in the browser: state from `data()` or `setup()`,
injected values, and event handlers. Vue sets event listeners, bound
attributes that change at runtime (such as `:aria-expanded` or `:hidden`),
an input's `value`, and `v-show` itself while it hydrates, so when their
value exists only in the browser, the server leaves it out. Anything else
that depends on browser state, such as text or a `v-if` condition, cannot
be written for Vue to adopt. Vue then builds the contents of the nearest
element around that part in the browser, inside the same app, with the same
state, events, and provide/inject as the rest of the page. If no element
surrounds the part, the page is sent with Citry's ordinary server HTML as
described above.

Until Vue starts, that element shows HTML for its contents written from
the values the server has, so readers and search engines still see them.
An element keeps the classes and styles the server knows, so a
`class="card"` beside a `:class` that reads `data()` still styles the
card before Vue starts. When Vue starts,
Citry removes that HTML and Vue builds the contents from its own state, in
the same step, so the browser never paints the element empty.

Vue builds every element inside that one again, so wrap a browser-only part
in its own element, such as a `<div>` around a `v-if`. Its siblings are then
adopted as they are.

The same happens for:

- a component called with extra attributes, listeners, `v-model`,
  `v-show`, or a custom directive, which reach the child's root element or
  its props, and a component whose template is only text;
- a scoped slot, or slots created conditionally or in a loop;
- HTML that Python inserts as one finished block, such as `<c-raw>`
  contents or a `Markup` value that contains tags, when the browser's
  parser would rearrange it where it sits (a `<p>` inside a `<p>`), when it
  holds a `<script>`, or when it starts with an HTML comment;
- markup the browser's parser would rearrange, such as a `<div>` inside a
  `<p>` or a table part outside its table;
- inline `<svg>` or `<math>`, `<template>`, `<iframe>`, `<noscript>`, and
  `<script>` or `<style>` inside a component;
- text containing a carriage return or NUL, text that displays a non-integer
  number or an object, and `<textarea>` or `<pre>` text that starts with a
  newline;
- a `:style` value the server cannot write the way the browser reads it:
  a fractional number, an empty value, a `true` or `false` value, a value
  with a semicolon, quote, backslash, brace, comment, or unbalanced
  parenthesis, a vendor-prefixed name such as `WebkitTransition`, or a
  list of fallback values;
- custom directives on elements.

Such an element is sent empty instead when its contents would hold
something the browser would run or load a second time when Vue builds them
again, for example a `<script>`, an `<iframe>`, `<object>` or `<embed>`, a custom
element, an `on*` handler attribute such as `onerror`, or an `autofocus`
or `autoplay` attribute. A `<textarea>` or `<title>` whose text depends on
browser state is sent empty too.

### What a hydrated page shows before Vue starts

Until the browser has loaded and run Vue, the page is plain HTML:

- A part hidden with `v-show` or `:hidden` from browser state is visible
  until Vue hydrates it, and an `aria-expanded` bound to browser state is
  missing.
- Submitting a form does an ordinary browser submission, because handlers
  such as `@submit.prevent` are not attached yet.
- Text typed into an input before Vue starts is replaced by the value the
  component renders.
- An element filled only by `v-text` shows its text when the value comes
  from `js_data()` and is a string, a whole number, `True` or `False`
  (shown as `true` and `false`), or `None` (shown as nothing). Other values, such as a fraction, a dict, a
  list, or browser state, leave the element empty until Vue sets the text.
  An element with its own content next to `v-text` shows that content until
  Vue replaces it.
- A part Vue builds in the browser shows the HTML the server wrote for it:
  both branches of a `v-if` and `v-else` that depend on browser state can
  be visible, and an `id` that both
  branches carry appears twice until Vue starts. Focus, a text selection, or
  text typed inside that part is lost when Vue builds it; the rest of the
  page keeps them.
- Component styles apply from the first paint. A page served through
  Citry's mounted routes links its component stylesheets in `<head>`, and a
  standalone page includes them there.
- If your site sends a Content Security Policy whose `style-src` does not
  allow inline styles, the browser blocks each `style` attribute in the
  served HTML and reports it once. Vue then applies the styles through the
  DOM, which the policy allows.

After hydration, the page is the same as a page Vue built in the browser,
with four exceptions a script might notice. An element whose contents Vue
built in the browser keeps a `data-allow-mismatch="children"` attribute. A `style` attribute written as a
string keeps that text where the browser would otherwise rewrite it in its
own normalized form. Where Vue marks the start and end of a list, a slot, or HTML inserted as one
finished block, the page keeps the server's `<!--[-->` and `<!--]-->`
comments instead of the empty text nodes Vue creates when it builds the
list itself. The Vue
host has no `data-v-app` attribute, which Vue adds only when it builds the
page itself; wait for the `citry:ready` event to know the page is ready.

Citry does not run Vue on the server and does not provide general-purpose
Vue SSR.

## Preserve interactive HTML

For an interactive document, Citry keeps the authored document shell and
moves the body's content into one generated Vue host element. It emits a
validated configuration script and the component and extension assets needed
to mount that host. An interactive fragment carries a descriptor for the
existing document runtime instead.

HTML minifiers, CDN optimizers, sanitizers, and streaming transforms must
preserve the generated host, configuration scripts, and fragment descriptors.
Do not rewrite the mounted host's descendants outside Vue. When the page
hydrates, keep the host's content byte for byte: a minifier that collapses
whitespace in its text makes the browser console report "Hydration completed
but contains mismatches", and Vue then rewrites the changed text. Citry validates
incoming definitions and occurrence metadata before publishing a server
revision.

Citry requests its own scripts and stylesheets with `crossorigin="anonymous"`
and answers them with `Access-Control-Allow-Origin: *`. When those requests
cross origins, as in a sandboxed iframe or behind a CDN that rewrites the
asset URLs, a proxy that drops the header leaves the page showing its HTML
while its components never start. See
[Keep the CORS header when a proxy or CDN serves Citry's files](/security/#keep-the-cors-header-when-a-proxy-or-cdn-serves-citrys-files).

## Choose the right loop or condition

Use Vue `v-if` and `v-for` for browser-owned HTML inside one component. Give
each repeated item a stable `:key`.

Use Python `<c-if>` and `<c-for>` when the branch or loop creates Python Citry
component instances. Vue does not run Python or create new server component
identities.

## Diagnose a runtime failure

Start with the first `[Citry]` error in the browser console. Common causes are
an incomplete fragment or asset, a Vue host or configuration block that an
optimizer changed or removed, an invalid prepared definition, or browser code
that moved or removed elements inside a Vue app. Later errors are often
consequences of the first failure.

[Troubleshooting](/guides/troubleshooting/) covers the wider server and
browser investigation workflow.

## See also

- [Vue in templates](/syntax/vue/) for directives and expressions.
- [Client interactivity](/concepts/client-interactivity/) for data, props,
  events, slots, and lifecycle callbacks.
- [Component JavaScript and CSS](/advanced/js-and-css-dependencies/) for
  component-owned assets.
- [HTML fragments](/advanced/html-fragments/) for interactive fragment loading.
