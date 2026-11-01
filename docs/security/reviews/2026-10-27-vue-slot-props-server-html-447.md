# Slot prop values in the server's HTML (#447)

- **Pull request:** [#447](https://github.com/citry-dev/citry/pull/447),
  merged 2026-10-27 (754ca907e)
- **Reviewer:** a separate reviewing agent, after the merge and before the
  change was released. A second agent reviewed the first one's results
  and this record, and the first agent then tested the routes the second
  one found missing.
- **Code:** the Rust server renderer in
  `crates/citry_vue_compiler/src/server_render.rs`:
  - `slot_function`, `slot_pattern` and `binding_names` read a fill's
    `v-slot` pattern;
  - `bind_slot_props` and `slot_prop` bind the values the `<c-slot>` tag
    passes to the names in that pattern;
  - `Writer::slot` writes the fill, and `StaticWriter` writes the HTML
    the server leaves inside a part that Vue rebuilds in the browser.

  Tests are in `packages/py/citry/tests/test_vue_slot_props.py` and
  `packages/py/citry/tests/e2e/test_vue_slot_props_e2e.py`.

## Who controls the input

A component can pass its `js_data()` values to a caller's fill, the
content the caller puts in its slot. The component writes
`<c-slot name="item" :row="row" />`, and the fill reads the value with
`<c-fill name="item" v-slot="{ row }">`. The
[review of #445](2026-10-27-vue-slot-props-445.md) covers who writes the
prop names, the expressions, and the pattern. Only the template author
writes them.

Before #447, the prop values reached the browser only inside the page's
JSON data. Now, when the page hydrates (Vue takes over the HTML the server
sent), the server renders the fill with those values and writes the
result into the page's HTML. The values can hold request data or stored
data. Because they reach the HTML before any script runs, the server must
escape each value for the place it lands, element text or an attribute
value, and write only plain attribute names when the fill spreads an
object with `v-bind`. The browser then shows the value as text, sets it
as an attribute, applies it as CSS, or follows it as a URL, depending on
what the fill's author bound it to.

## How it was checked

The reviewer read the new code in the server renderer, including the
functions that escape text and attribute values and the ones that decide
which attribute names it writes. Then
it rendered pages whose `js_data()` passed hostile values to a scoped
fill, and loaded each page in Chromium and Firefox (Playwright's builds),
on commit b4ca5d571 with a debug build of `citry_core`. When a value ran,
it only wrote a marker to the console.

The fills bound the values in these ways:

- `v-text`, including on `<textarea>` and `<pre>`;
- `:title`, data attributes, `:value`, `:placeholder`, and the boolean
  and enumerated attributes `:hidden`, `:disabled` and `:contenteditable`;
- `:class` and `:style`, as strings, objects and arrays;
- `:href` and `:src`, including a link inside SVG;
- an object spread with `v-bind`;
- a `v-for` over an array the slot passes.

A separate case used `v-html`, `<iframe :src>` and `<iframe :srcdoc>`.

The values tried included:

- markup, quote, and `>` breakouts;
- text that closes a script, style, comment, `<textarea>` or `<title>`
  element (the fills had a `<textarea>`, but no `<title>`);
- `{{ ... }}`;
- values that were already HTML-escaped, or held character references;
- `javascript:` URLs in several spellings, and `data:` URLs;
- objects with keys named `__proto__` and `constructor`;
- `v-bind` objects whose keys name event handlers, `innerHTML`, `id`,
  `name`, `formaction` or `style`, or are not valid attribute names.

The pages covered these routes:

- a fill with an object pattern, a renamed pattern such as
  `{ row: r }`, one name for the whole props object (`v-slot="props"`),
  and a `...rest` pattern;
- two nested fills that both name their prop `row`, with the inner one
  inside a part Vue builds in the browser;
- a prop that a middle component passes on to another slot;
- a fill written in a different component from the one that calls the
  slot, where Citry forwards the whole props object with `v-bind`;
- a cached component, on the first render and on a cache hit;
- the same template through `render_template()`;
- extension hooks that change the component's browser data, or return a
  different result from `on_slot_rendered`.

Most pages were loaded four ways:

- hydrated;
- built by Vue in the browser, with a CSP nonce and a CSP response
  header;
- with `ssr=False`;
- hydrated in development mode, which checks Vue's first render against
  the server's HTML.

The `render_template()` page was loaded hydrated only, the extension
pages hydrated only, and the cached page once more on a cache hit. One
more page, with the routes the second agent added, was loaded hydrated,
with `ssr=False`, and hydrated under a CSP header that blocked Citry's
scripts, so only the server's HTML showed. In all, that made 112 Citry
page loads, plus 6 plain-Vue loads. For each one, the reviewer read the
server's HTML with the scripts removed, then read the page as the
browser built it. On most pages it hovered over, focused and clicked the
probe elements; on the extra page it only clicked them.

The same values went through two comparisons:

- **Plain Vue:** three of the fills (the main one, the one inside a part
  Vue builds in the browser, and the `v-html` and iframe case) were
  rendered by Vue 3.5.44's own server renderer, then hydrated in both
  browsers.
- **The render parity check:** 11 of the pages went through
  `scripts/vue_render_parity/check.py`, which compares the server's
  HTML with Vue's server render of the same page. It found no difference
  in the 402 elements it compared. It does not compare the HTML inside
  parts Vue rebuilds in the browser.

## Ruled out

- **A value becoming markup in the server's HTML:** every value the
  server wrote was escaped for its place, in text and in attribute
  values. Text that tries to close `<textarea>` stayed text. In the HTML
  Vue takes over, the server writes no element whose contents the
  browser reads as raw text, such as `<script>` or `<style>`. Inside a
  part Vue rebuilds, it refuses `<script>`, and it escapes every `<` in a
  value, so data cannot close such an element. No
  page had an event attribute or element the template did not write.
  Already-escaped text and character references showed as literal text,
  as in Vue.
- **Parts Vue builds in the browser:** when a part depends on state only
  the browser has, the server writes its element empty, or with every
  branch of the condition, and Vue builds the contents in the browser.
  The server escapes the values it writes there too, and drops event
  attributes and `srcdoc` from that HTML.
- **Hydration changing what the page shows:** on the three pages compared
  with plain Vue, text and attribute values after hydration matched
  Vue's. Inside parts Vue rebuilds, a style string the browser rejects
  ends up empty, as in any page Vue builds in the browser. The
  development mode check logged no difference.
- **Nested fills with the same names:** each fill showed only the values
  its own slot passed, including the inner fill in a part Vue builds in
  the browser.
- **Values passed on through a middle component:** the output was the same
  as for a direct fill.
- **Data choosing attribute names:** when a fill spreads a data object
  with `v-bind`, the server writes the keys that Vue would set as
  attributes, escaped. It accepts only plain attribute names, so a key
  cannot end the tag. An event handler key, or any other key the server
  cannot write the way Vue would, makes the element a part Vue builds in
  the browser. Vue's own server renderer writes every key, event
  handlers included. Data that chooses attribute names can still set an
  `id` that a script reads as a global, a `formaction` URL that runs when
  the form is submitted, or a `style`, as Vue's own server renderer also
  does. Spreading request data with `v-bind` is the
  template author's choice.
- **Extension hooks:** a hook that changes the browser data gets the same
  escaping. When `on_slot_rendered` returns a string or `Markup` in place
  of a fill with `v-slot`, the render fails instead of writing it.
- **Cached renders and `render_template()`:** same output as a fresh
  render.
- **Values the author binds to code, URLs or CSS:** a `javascript:` URL in
  `:href` runs when clicked, `v-html` parses markup, an iframe loads its
  `data:` URL or `srcdoc`, a string `:style` applies its CSS, and a
  `v-bind` object can set event handler attributes and `innerHTML` in the
  browser. Plain Vue does the same, in both browsers. Binding request
  data there is the template author's choice. On the pages Vue built in
  the browser under a CSP without `unsafe-inline`, none of these ran. On
  the one page loaded under a CSP header that blocked Citry's scripts,
  the server's HTML ran nothing, the `formaction` button included.

## Fixed during the review

Nothing recorded.

## Not tested

- WebKit.
- The `security_javascript="warn"` setting, and a custom `deps_position`
  (where Citry puts its scripts on the page).
- A hydrated page with a CSP nonce, where Citry's scripts run.
- A changed cache entry under a CSP header.
- HTML inside a part Vue rebuilds that is larger than 1 MiB, the size
  above which the server writes that part empty.
- A release build of `citry_core`.
- MathML, and SVG elements other than a link.
- A `<title>` element inside a fill.

## Follow-ups

- Done in [#562](https://github.com/citry-dev/citry/pull/562): the
  Vue slots page now warns against binding request data with `v-html`,
  `:href` or `:src` in a fill, and against spreading an object from
  request data with `v-bind`, which lets the data choose attribute names
  in the server's HTML and in the browser. This was a follow-up from the
  [#445 review](2026-10-27-vue-slot-props-445.md).
