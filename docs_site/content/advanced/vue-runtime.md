---
title: Vue runtime
description: Use Citry's managed Vue runtime and preserve interactive component output in production.
---

# Vue runtime

When a component on the page uses Vue, Citry loads Vue in the browser,
starts Vue on the HTML the server sent, and applies each new server render
to the live page. You write Vue directives and `$component({...})` options;
there is no Vue application to create and no build step.

This page covers what that runtime does on your behalf and where it affects
you: what happens to a field the user is typing in, which names you cannot
use, what the page shows before Vue starts, how to use a Content Security
Policy, and what your deployment must leave untouched. To learn how to add
Vue behavior to a component, start with
[Client interactivity](/concepts/client-interactivity/).

## Add Vue behavior

Give the component browser state and methods in its JavaScript:

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

Then use them in the template:

```citry-html
<button type="button" @click="toggle">Toggle details</button>
<p v-show="open">Ships within two working days.</p>
```

Citry also starts Vue for a component that has its own JavaScript, uses
`js_data()`, uses Vue props or events, or keeps
[server-event](/events/) `State`. Complete pages and
[HTML fragments](/advanced/html-fragments/) work the same way.

Citry creates the Vue app itself, so do not mount another Vue app over
Citry's output. For Composition API helpers such as `ref`, use `Citry.vue`,
which is the Vue build the page already loaded.

To run code each time the server renders the component again, such as
redrawing a chart, use the `onServerRender` option. See
[React to a re-render](/concepts/client-interactivity/#react-after-a-server-render).

## Use Citry control flow

Use Vue's `v-if` and `v-for` for plain HTML inside one component, and give
each repeated item a stable `:key`.

Use `<c-if>` and `<c-for>` when the branch or loop creates Citry
components. Components are created in Python on the server, and Vue cannot
create them in the browser.

## Keep typed input { #keep-what-the-user-typed-across-renders }

A text input, `<textarea>`, or `<select>` keeps the user's edit when its
component renders again, as long as the value the template gives it has not
changed. That holds for a fixed value and for a value Python computes:

```citry-html
<input name="role" value="Owner" />
<input name="email" c-value="row['email']" />
```

Say the server sent `ada@example.com` and the user typed
`draft@example.com`:

- A browser-only update, or a server render that sends `ada@example.com`
  again, leaves `draft@example.com` in the field.
- A server render that sends a different value, such as
  `new@example.com`, replaces the draft. Once the server's value changes,
  the field shows it.
- A `<select>` the user has not changed always shows the value the template
  gives it, even when a server render changes its options.

The same rule applies to a `value` that `c-bind` spreads onto the field.

A value bound to browser state with Vue's `:value`, including a `js_data()`
value, behaves as in Vue: every render writes it again. So does a `value`
inside an object spread with Vue's `v-bind="..."`. To keep a draft through
those renders, store it in Vue state with `v-model`.

Checkboxes and radio buttons are not affected. Whether they are checked
follows `v-model` or `c-checked` as usual.

When a server render reorders keyed rows, each row keeps its elements, and
the field the user is typing in keeps its focus and caret.

## Reserved names { #names-citry-reserves-on-the-component-instance }

Citry adds a few names to each component's Vue instance. Do not define a
`data()` key, `setup()` value, method, computed value, or injection with one
of these names:

- `$citryPrepared`, which holds the values Python computed for the
  template. Its contents can change between releases, so do not read it.
- `$citryEvents`, which connects `@c-*` attributes to the server.
- `$loading`, `$error`, `$state`, `$sendEvent`, and `$onEvent`, the
  [Events helpers](/reference/browser-apis/#component-events-helpers).
- Names that an installed browser extension adds, such as i18n helpers.
- `citryId`, a prop Citry adds to every component.

If a component uses one of these names, it fails with an error naming it
when it first appears in the browser. Vue already refuses props whose name
starts with `$`.

When your JavaScript needs a value from Python, return it from
[`js_data()`](/reference/browser-apis/#js-data-members) and read it as
`this.name` or `component.name`.

A `js_data()` key cannot start with `$` or `_`, and cannot be `citryId`.
Rendering such a component raises `ValueError` naming the component and the
key, before any HTML is sent. Rename the key, for example `_count` to
`count`.

A `js_data()` key that matches a prop, `data()` key, `setup()` value,
method, computed value, or injection of the same component is caught only
in the browser: the component fails when it first appears.

## Server-render the page { #send-page-content-in-the-served-html }

The HTML the server sends for an interactive page already contains the
page's content. Search engines, link previews, and readers without
JavaScript see it, and you do not need to turn anything on.

Citry puts the body's content in one element that Vue starts in, called
the Vue host. When Vue starts, it either adopts the server's HTML or
replaces it:

- **Vue adopts the HTML.** The server writes the page exactly as Vue's
  first render in the browser would, and Vue reuses those elements instead
  of creating them again. This is called hydration.
- **Vue replaces the HTML.** When the server cannot write the page the way
  Vue would, the host carries the same HTML a static page gets. Vue clears
  it and builds the page when it starts, in one step, so the browser never
  shows an empty page in between.

Most pages are adopted. [Cases where Vue rebuilds the server
HTML](#cases-where-vue-rebuilds-the-server-html) lists when Vue replaces a
page or builds part of it in the browser.

Vue starts after the browser has read the whole page, so the content can
appear first. Your own `defer` and module scripts placed before Citry's
scripts run before Vue starts. When your script needs the finished page,
listen for the `citry:ready` event.

Citry writes this HTML from the compiled templates and the data the
browser receives. It does not run Vue on the server, and it does not
offer general-purpose Vue server-side rendering.

### Before Vue starts { #what-a-hydrated-page-shows-before-vue-starts }

Until the browser has loaded and started Vue, the page is plain HTML:

- A part hidden with `v-show` or `:hidden` based on browser state is
  visible, and an `aria-expanded` bound to browser state is missing.
- Submitting a form does an ordinary browser submission, because handlers
  such as `@submit.prevent` are not attached yet.
- Text typed into an input before Vue starts is replaced by the rendered
  value when Vue starts.
- An element filled only by `v-text` shows its text when the value comes
  from `js_data()` and is a string, a whole number, `True` or `False`
  (shown as `true` and `false`), or `None` (shown as nothing). Other
  values, such as a fraction, a dict, a list, or browser state, leave the
  element empty until Vue sets the text. Content written next to `v-text`
  shows until Vue replaces it.
- A part that Vue builds in the browser (see
  [below](#parts-vue-builds-in-the-browser)) shows the HTML the server
  wrote for it. Both branches of a `v-if` and `v-else` that depend on
  browser state can be visible, and an `id` on both branches appears
  twice. Focus, a text selection, or text typed inside that part is lost
  when Vue builds it; the rest of the page keeps them.
- Component styles apply from the first paint. A page served through
  Citry's mounted routes links its component stylesheets in `<head>`, and a
  standalone page includes them there.

### Wrap browser parts

Some content depends on values that exist only in the browser, such as
text from `data()` or a `v-if` that reads it. The server cannot write it
for Vue to adopt, so Vue builds the contents of the nearest surrounding
element in the browser. Everything inside that element is created again.

Wrap such a part in its own element, such as a `<div>` around the `v-if`,
so that its siblings are still adopted:

```citry-html
<section>
  <h2>{{ title }}</h2>
  <div>
    <p v-if="open">Ships within two working days.</p>
  </div>
</section>
```

If no element surrounds the part, Vue replaces the whole page instead.

### Skip server content

Two settings send an empty Vue host and let Vue build the page in the
browser. Use them only for pages that search engines and readers without
JavaScript do not need, such as a signed-in dashboard.

- `Citry(ssr=False)` sends every page without its content.
  `serialize(ssr=False)` does it for one serialization.
- `ssr_element_threshold` sends a page without its content when the server
  would write that many elements or fewer. A small page can start slightly
  faster this way, because the browser does not parse the HTML and then
  hydrate it. The default, `0`, keeps the content of every page with at
  least one element. The setting applies only to pages Vue can adopt; a
  page Vue replaces always carries its server HTML.

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

`ssr_element_threshold` must be a non-negative `int`. Creating `Citry`
with another type raises `TypeError`, and with a negative value raises
`ValueError`.

## Add a CSP nonce { #use-content-security-policy }

Pass the request's nonce when you serialize the page:

```python
html = Page().render().serialize(csp_nonce=request_nonce)
```

Citry adds the nonce to the scripts and styles it places, including those
that dependency hooks add. Your application still generates the nonce and
sends the matching response header. A `<script>` or `<style>` tag written
directly in a template does not get the nonce. See
[Apply a request CSP nonce centrally](/security/#apply-a-request-csp-nonce-centrally).

An interactive [HTML fragment](/advanced/html-fragments/) uses the Citry
runtime the page already loaded. Before starting a fragment, Citry checks
that its runtime, CSP nonce, components, and assets match the page. If they
do not, the fragment does not start, and Citry reports an error in the
browser console.

A page with a Content Security Policy is sent with HTML that Vue replaces
rather than adopts. See
[Replaced pages](#pages-vue-replaces-instead-of-adopting).

## Send no JavaScript

Set `security_javascript="omit"` for output that should stay static, such
as an email. Citry keeps the server-rendered HTML and CSS, and sends no
Vue runtime, component JavaScript, Events client, or app data. Vue
attributes stay in the HTML, where the browser ignores them.

Set `security_javascript="forbid"` to make serialization fail when the
output needs browser behavior. See
[Choose how much JavaScript Citry may deliver](/security/#choose-how-much-javascript-citry-may-deliver).

## Preserve page HTML { #preserve-interactive-html }

For an interactive page, Citry keeps your page's `<html>`, `<head>`, and
`<body>`, and moves the body's content into the generated Vue host. It
adds a configuration script and the component and extension assets that
start Vue. An interactive fragment instead carries a small description of
its components for the runtime already on the page.

HTML minifiers, CDN optimizers, sanitizers, and streaming transforms must
keep:

- the Vue host element and everything inside it, byte for byte;
- Citry's configuration scripts;
- a fragment's description block.

Do not change elements inside the Vue host with code outside Vue. A
minifier that collapses whitespace in the host's text makes the browser
console report "Hydration completed but contains mismatches", and Vue then
rewrites the changed text.

Citry requests its own scripts and stylesheets with
`crossorigin="anonymous"` and answers with
`Access-Control-Allow-Origin: *`. When those requests cross origins, as in
a sandboxed iframe or behind a CDN that rewrites asset URLs, a proxy that
drops the header leaves the page showing its HTML while its components
never start. See
[Keep the CORS header when a proxy or CDN serves Citry's files](/security/#keep-the-cors-header-when-a-proxy-or-cdn-serves-citrys-files).

## Diagnose failures

Start with the first `[Citry]` error in the browser console. Later errors
are often caused by the first one. Common causes:

- a fragment or asset that did not load completely;
- a Vue host or configuration script that an optimizer changed or removed;
- component data from the server that the runtime rejects;
- browser code that moved or removed elements inside the Vue host.

[Troubleshooting](/guides/troubleshooting/) covers the wider server and
browser investigation.

## When Vue rebuilds HTML { #cases-where-vue-rebuilds-the-server-html }

The sections below list the exact cases in which Vue does not adopt the
server's HTML. Read them when a page loses focus or typed text as Vue
starts, or when the browser console reports a mismatch.

### Replaced pages { #pages-vue-replaces-instead-of-adopting }

Vue replaces the whole page's server HTML when the page:

- uses a Content Security Policy, `security_javascript="warn"`, script
  integrity, or a configured i18n extension;
- has a component with its own `on_dependencies()` method, or an extension
  that defines `on_dependencies()`, `on_serialize()`, `on_js_loaded()`, or
  a browser hook;
- places assets with a `deps_position` other than the default;
- has a browser-only part with no element around it, such as a `v-if` at
  the top level of the page component's template;
- contains HTML that the browser's parser would rearrange.

Before Vue starts, such a page shows its static HTML: both branches of a
`v-if` and `v-else` can be visible, `v-show`, `:class`, and other Vue
bindings have no effect yet, and attributes such as `@click` stay in the
HTML, where the browser ignores them. When Vue builds the page, focus, a
text selection, and text typed earlier are lost, and an `<iframe>` or
`<video>` loads again.

Some of these pages are sent with an empty Vue host instead:

- a page with `security_javascript="warn"`, because the warning would list
  every Vue attribute left in the HTML;
- a page under a Content Security Policy that would reject its HTML, such
  as an `onclick` attribute or a `javascript:` link;
- a page whose body contains a `<script>`, for example inside `<c-raw>`,
  because the browser would run it while reading the page, and a page Vue
  builds never runs it.

HTML fragments are always built in the browser.

!!! note "Inline `style` attributes under a strict Content Security Policy"

    When the policy's `style-src` does not allow inline styles, the
    browser blocks each `style` attribute in the served HTML and reports
    it. Vue then applies the same styles through the DOM, which the policy
    allows. To avoid the reports, allow `'unsafe-hashes'` with the style
    hashes, or move the styles to component CSS.

### Browser-built parts { #parts-vue-builds-in-the-browser }

Vue sets event listeners, bound attributes such as `:aria-expanded` or
`:hidden`, an input's `value`, and `v-show` itself while it hydrates, so
these can depend on browser state without any rebuild. The server leaves
out a value that exists only in the browser.

Anything else that depends on browser state, such as text or a `v-if`
condition, makes Vue build the contents of the nearest surrounding element
in the browser. That part runs in the same app, with the same state,
events, and provide and inject, as the rest of the page. Until Vue starts,
it shows HTML written from the values the server has, and it keeps the
classes and styles the server knows: a `class="card"` beside a `:class`
that reads `data()` still styles the card.

The same happens for:

- a component called with extra attributes, listeners, `v-model`,
  `v-show`, or a custom directive, and a component whose template is only
  text;
- a scoped slot, or slots created conditionally or in a loop;
- HTML inserted as one finished block, such as `<c-raw>` contents or a
  `Markup` value with tags, when the browser's parser would rearrange it
  where it sits (a `<p>` inside a `<p>`), when it holds a `<script>`, or
  when it starts with an HTML comment;
- markup the browser's parser would rearrange, such as a `<div>` inside a
  `<p>` or a table part outside its table;
- inline `<svg>` or `<math>`, `<template>`, `<iframe>`, `<noscript>`, and
  `<script>` or `<style>` inside a component;
- text containing a carriage return or NUL, text that displays a
  non-integer number or an object, and `<textarea>` or `<pre>` text that
  starts with a newline;
- a `:style` value the server cannot write the way the browser reads it: a
  fractional number, an empty value, `true` or `false`, a value with a
  semicolon, quote, backslash, brace, comment, or unbalanced parenthesis, a
  vendor-prefixed name such as `WebkitTransition`, or a list of fallback
  values;
- custom directives on elements.

Such an element is sent empty when its contents would hold something the
browser would run or load twice, such as a `<script>`, an `<iframe>`,
`<object>` or `<embed>`, a custom element, an `on*` attribute such as
`onerror`, or an `autofocus` or `autoplay` attribute. A `<textarea>` or
`<title>` whose text depends on browser state is sent empty too.

### Hydration differences

After hydration, the page is the same as a page Vue built in the browser,
except for details a script might notice:

- An element whose contents Vue built in the browser keeps a
  `data-allow-mismatch="children"` attribute.
- A `style` attribute keeps the text the server wrote, where the browser
  would otherwise rewrite it in its own form.
- Lists, slots, and HTML inserted as one block keep the server's `<!--[-->`
  and `<!--]-->` comments around them, where Vue would create empty text
  nodes.
- The Vue host has no `data-v-app` attribute. Listen for `citry:ready` to
  know the page is ready.

## See also

- [Vue in templates](/syntax/vue/) for directives and expressions.
- [Client interactivity](/concepts/client-interactivity/) for data, props,
  events, slots, and lifecycle callbacks.
- [Component JavaScript and CSS](/advanced/js-and-css-dependencies/) for
  component-owned assets.
- [HTML fragments](/advanced/html-fragments/) for interactive fragment loading.
