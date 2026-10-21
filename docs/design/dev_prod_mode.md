# Design: development and production mode

**Status (2026-07-25): proposal, partially implemented.** The `Citry(mode=...)`
setting is implemented. Its debug-extension consumer (section 4) is written but
temporarily gated off (`extension._AUTO_DEBUG_IN_DEVELOPMENT = False`) pending a
bug: the debug extension's render-cache participation turns a cached
(`<c-cache>`) component's ownership graph into an invalid manifest (an
uninvoked instance that still names a parent), even with both highlight flags
off, so auto-registering it in development would break dev pages that use
cache. The client ownership graph consumer (section 3) is specified here and
lands in a following change. The two page checks in section 5 are
implemented (2026-10-21). Broader consumers (verbose diagnostics, source
maps for the browser error overlay, cache behavior) are future work. The
setting is the single source of truth for all of them.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md). For the error overlay
that consumes development provenance see section 6.8 of
[`early_validation_plan.md`](early_validation_plan.md).

---

## 1. Problem

Some output is useful for a developer and dead weight for an end user. The
clearest case is the client ownership graph. A **component-tag client
binding** is a browser-side `$c-props`, `@click`, or `@c-poll.5s` binding
resolved from a nested `<c-*>` tag. Every recorded nested component tag,
client binding, fill, and slot carries a byte range into its template source
so a future error overlay can show the authored snippet. Production never reads those
offsets, and they are roughly half of the uncompressed manifest, so shipping
them to every visitor pays for a feature only a developer uses.

The server is the only place that can decide this. It knows the component
tree, it builds the manifest, and it is where a framework-wide "this is a
development build" signal belongs. Today Citry has no such signal, so the
manifest cannot make the choice.

## 2. The setting

`Citry(mode="production")` is a construction-time setting with two values:

- `"production"` (the default): the engine omits developer-only output.
- `"development"`: the engine includes it.

Production is the default so that a project ships lean output unless it opts in,
the same way a deployment opts into verbose logging rather than opts out. A
host framework wires its own environment to this value (for example a Django
project passes `mode="development"` when `DEBUG` is true).

The value is fixed at construction, like the other engine settings, so every
render from one engine agrees. A project that needs both at once uses two
engines, which is already how isolated configuration works.

The name is `mode` rather than a `debug` boolean because the concept is an
environment, not a single switch, and because Citry already ships a `debug`
extension (visual boundaries); a `Citry(debug=...)` argument would read as
turning that extension on. A future value such as `"test"` stays open.

An unrecognized value is rejected at construction, not coerced or defaulted.
`mode` is a fixed set of strings, so a typo like `"prod"` or `"dev"` raises
immediately with the allowed values, rather than surfacing later as a build
that silently ships or omits developer output. Rejecting at construction also
means every later read of `citry.mode` can trust the value without re-checking.

## 3. First consumer: the client ownership graph

The manifest carries a top-level `mode` member echoing the engine setting, so
the browser can tell "this build sends no provenance" apart from "this build
sends provenance and this render happened to have none":

- `mode: "production"`: every graph's `sourceLocations` array is empty and
  every location reference is null. The browser skips the location-based
  consistency checks, because there is nothing to check against.
- `mode: "development"`: source locations are present with their
  `sourceOffset`, `sourcePos`, and `origin`, references resolve, and the browser
  runs the full checks.

The manifest still records source locations internally while rendering; `mode`
only decides whether they reach the wire. The reference validator and both
browser and server enforce the mode invariant: a production manifest with a
non-empty `sourceLocations` array, or a development manifest whose references
do not resolve, is rejected.

## 4. Second consumer: the debug extension

The built-in `debug` extension inserts visual component boundaries into the
rendered HTML, which is developer output by definition. In `"development"` it
is auto-registered alongside the always-on built-in extensions; in
`"production"` it is absent, so a deployed page carries no debug boundaries and
a project never has to remember to strip the extension before shipping.

Because it becomes a built-in in development, its name `debug` is reserved
there, and a project that also lists the extension explicitly in development
hits the normal duplicate-name rejection. In production the extension is not
built in, so a project may still opt into it explicitly for a production-like
build that wants boundaries.

## 5. Third and fourth consumers: page checks

Issue #207 measured two mistakes that only show on a whole, running page.
`"development"` turns on a check for each. `"production"` runs neither, and a
production page carries neither check's code; the runtime keeps only the
short call that looks for the browser check's script.

### 5.1 Browser render differs from served HTML

The server writes a page's HTML for Vue to adopt. Where it cannot write a
part exactly as Vue would, it marks the nearest element as a shell
(`data-allow-mismatch="children"`, see
[`vue_ssr_selected_tree_plan.md`](vue_ssr_selected_tree_plan.md)); Vue builds
that element's children in the browser and never reports a difference there.
A shell appears whenever a component is called with listeners or extra
attributes, so a mistake such as `created() { this.open =
window.matchMedia(...).matches }` silently changes the page as Vue starts
(benchmark case m14).

How it works:

1. In development the document configuration of every Vue page carries
   `"development": true`. When the page hydrates and has served shell
   contents (`"emptyShells": true`), it also inlines
   `citry/_vue/dev_checks.js` as a classic script before the module script
   that starts the app.
2. `client.js` asks that script to keep each shell's served child nodes
   (`CitryVueDevChecks.captureShells`) right before it empties the shells,
   in the same task as the mount.
3. Right after `vueApp.mount()` returns, the script compares the kept nodes with what Vue built and logs one
   `console.warn` per shell that differs, naming the component whose
   template wrote the differing element (the vnode's `ctx`), the element,
   and the first difference. A failure inside the check is logged with
   `console.error` and never stops the app. By then Vue has run the
   `mounted()` hooks, but the re-render their state changes ask for waits
   for Vue's scheduler, so the comparison sees the first render.

The server writes a shell's contents from the values it knows: it leaves out
a list, a text node or an attribute only the browser can compute, and it
writes every branch of a condition only the browser can test. So the
comparison is one-sided. It pairs elements of the same tag in order (the
pairing that agrees most), ignores elements, attributes and text that only
one side has, ignores comments and whitespace, and reports a served
attribute value the browser changed or removed, a served class or style
property missing in the browser, or served text the browser shows
differently. An attribute Vue sets as a DOM property (`value`, `checked`,
`selected`) is compared through the property. A `display: none` only the
browser has is skipped, because the server keeps an element's own
`display` when only the browser can test its `v-show`. When one parent has
so many children that pairing them would take more than 40,000 steps, its
children are not compared. `data-allow-mismatch` on an element in Vue's
render silences the kinds it names, with Vue's own reading of the value:
the nearest element carrying it decides a text or children difference.

Error modes and limits:

- Only values the server has are compared: `js_data()` keys and prepared
  values from Python. State that starts in `data()` or `setup()` exists
  only in the browser, so the server leaves out what reads it and the
  check never sees it.
- Content meant to differ (a clock that `created()` sets from a
  `js_data()` value, data from `localStorage` written over a server value)
  warns too. The author adds `data-allow-mismatch` (empty
  for every kind, or `text`, `children`, `class`, `style`, `attribute`) to
  the element, as for Vue's own hydration warnings, or moves the code to
  `mounted()`.
- An element or text that only one side has is never reported, so a
  `v-if` whose server-known condition flips in the browser warns only
  through a value next to it, such as the `:aria-expanded` in m14.
- Only shells are compared. Elements Vue adopts are Vue's to check: its
  production build logs "Hydration completed but contains mismatches."
  without details. A page that cannot hydrate sends HTML with Vue's
  bindings unevaluated, and a shell the server sent empty has nothing to
  compare, so neither is checked.
- The comparison sees the first render only: state changed in `mounted()`,
  after an `await`, or by a later update is not compared, because Vue's
  scheduler re-renders after `mount()` returns. A direct DOM edit in a
  `mounted()` hook or a directive's `mounted` hook is already on the page
  and can be reported.
- Text from a browser-only `v-if` over bare text, merged by the browser's
  parser with text only the browser knows, can be reported; wrapping the
  text in an element avoids it.

Alternatives considered: a static warning when `data`, `setup` or
`created` reads `window` and writes state (rejected in the #207 proposal for
its false reports), and comparing component state before and after
`created()` (it cannot tell whether the changed key reaches the HTML).
Shipping the check inside the runtime bundle was rejected because standalone
pages inline the runtime, so production pages would carry its bytes.

### 5.2 One id on two elements of a page

The `citry.template.duplicate-id` rule sees one template. The same id from
two components, or from one component rendered twice, needs the whole page
(benchmark case m57). Serialization already builds each component's own HTML
with its children as `<template>` placeholders, so in development
`serialize.py` passes each of those pieces to `PageIdCheck`
(`citry/_page_ids.py`), which counts every `id` and issues one
`RuntimeWarning` per serialization listing each repeated id with the
components (and their template origins) that wrote it. A page Vue hydrates
skips building its body's components; the check builds them separately and
discards the result, so the serialize hooks receive the same placeholders as
in production.

The check runs on the server because only the server can name every
component, including components that have no browser code. A browser check
after mount would also see ids from Vue bindings (`:id`), rows a Vue
`v-for` repeats, and ids that browser code adds, but it could not name
server-only components and would run only on pages that load Vue.

Error modes and limits:

- Ids inside a `<template>` or `<noscript>` and on or inside an element
  with `v-if`, `v-else-if`, `v-else` or `v-for` are not counted: the
  browser decides whether they exist. The same holds for a child
  component whose placeholder sits there; the scanner returns those
  placeholders and the frame builder skips them and their descendants.
- A `v-if` or `v-else` written on a component's own tag does not reach
  the caller's HTML (it holds only the child's placeholder), so the child
  is counted, and the same component in both branches can warn.
- A component declared `simple` writes its HTML into its caller's, so its
  ids are named under the caller. A Citry `<c-if>` or `<c-for>` has already run, so its
  rendered branches and rows count.
- Ids in `<c-raw>` contents and trusted `Markup` count, because the browser
  shows them; they are named under the component whose HTML holds them,
  which for a slot fill is the component that renders the slot.
- Ids that a Vue binding or browser code sets are not seen.
- Each serialization is one page. A fragment, or a component an Events
  action renders again, is checked on its own, so an id it shares with the
  page it lands in is missed.
- The warning goes through Python's `warnings` module, so a repeated
  identical message is shown once per process under the default filters.
  The cost, in development only, is one HTML parse of the page per
  serialization, plus a second build of the body's components on a page
  Vue hydrates.
- A component whose HTML the parser cannot read is skipped without a
  warning, so its ids are not counted.

## 6. Open questions

- whether host integrations should default `mode` from a detected environment
  variable or require an explicit value;
- whether a later `"test"` value differs from `"development"`;
- how development ships the template source itself (inline, fetched, or a
  source map) for the error overlay, which is the section 6.8 question in
  [`early_validation_plan.md`](early_validation_plan.md);
- which other outputs (diagnostic verbosity, cache bypass, unminified client
  assets) should read `mode` rather than their own separate flags.

## 7. Non-goals

`mode` is not a security boundary and not a correctness switch: a component
renders the same tree in both modes, and production still validates everything
it receives. It only decides whether developer-facing extras are included.
