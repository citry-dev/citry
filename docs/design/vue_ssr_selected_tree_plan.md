# Vue hydration of server HTML: current status

An interactive page sends its content in its served HTML, so search engines
and readers without JavaScript see it. When the server can write the page
exactly as Vue's first render creates it, Vue adopts those nodes
("hydration") instead of building every element in the browser. When it
cannot, the Vue host carries Citry's ordinary server HTML and Vue's client
mount replaces it (see "Pages that cannot hydrate" below). Both are on by
default; `Citry(ssr=False)` or `serialize(ssr=False)` sends an empty host
instead. Output without Vue requirements keeps its existing behavior. The
board measurements and the reasoning behind the design are in
[`vue_board_hydration_plan.md`](vue_board_hydration_plan.md).

## How the server writes what Vue adopts

Vue adopts server HTML only when every comment marker, element, attribute
and text node is exactly what its first render in the browser creates. That
render is the compiled render function of each component, run over the
component's `preparedData` and `js_data` values. The server runs the same
thing:

1. When a definition compiles, the native compiler reads its render
   function once into a small program
   (`crates/citry_vue_compiler/src/server_render.rs`), kept on
   `CompiledRender.server_render`.
2. After the prepared manifest is built, `prepare_vue_serialization` passes
   the manifest JSON (the exact text the configuration data block carries) to
   `_rust.vue._render_for_hydration`, which runs the programs from the root
   occurrence down through component calls and slots, and writes the host's
   inner HTML.
3. The same native call checks that the browser's HTML parser keeps every
   written node where it was written, as described in "How the server
   checks the browser's parse" below. A page that fails the check mounts in
   the browser.

The written HTML therefore contains Vue's own Fragment anchors
(`<!--[-->`/`<!--]-->`), `<!--v-if-->` and `<!---->` placeholders, attributes
as Vue's `runtime-dom` `patchProp` leaves them, text exactly as the
compiled render emits it, whitespace included, and HTML Python hands over as
a finished string written unchanged (see "Raw HTML blocks" below). Nothing is
inferred from Citry's own HTML, and no rendered document is parsed in Python.

## Raw HTML blocks

HTML that Python hands over as a finished string, `<c-raw>` contents or a
trusted `Markup` value with tags, reaches the browser as a prepared record
`{"html": ..., "nodeCount": ...}`. The `citry-opaque-html` component in
`client.js` renders it as a Fragment holding one static vnode,
`createStaticVNode(html, nodeCount)` (an empty Fragment when `nodeCount` is
0). When Vue builds the page, it parses the HTML inside a `<template>`
element and inserts the nodes, ignoring the count. When the page hydrates,
the server has already written the HTML between the Fragment's
`<!--[-->` and `<!--]-->`, and Vue's `hydrateNode` (the `Static` case in
runtime-core 3.5.42) steps over `nodeCount` DOM nodes without reading them,
then expects the closing `<!--]-->`.

Python computes `nodeCount` when it captures the record
(`static_html_node_count` in `citry_html_transform`, exposed as
`citry_core.html_transform.static_html_node_count`): the number of
top-level elements, texts and comments html5ever builds for the HTML inside
a `<template>` element, the same parse Vue's insertion uses. The Python
protocol (`prepared_manifest`), the browser preflight (`checkOpaqueHtmlRecord`
in `client.js`) and the Rust writer accept a record only with exactly those
two keys, a string, and a non-negative integer that is 0 for empty HTML.

The server writes a block only when the page's parse gives it exactly the
nodes Vue would insert (`static_html_in_context` in
`crates/citry_html_transform/src/static_html.rs`). It parses the block
twice with html5ever: alone inside a `<template>`, and inside the open
elements around it in the page, between Vue's Fragment comments and
followed by a probe text. The block is written when the two trees are
equal, every open element around it holds only the next one, the closing
comment and the probe come right after the block (so the block closed
everything it opened and left no formatting element to be reopened), and
the record's `nodeCount` equals the count. Otherwise the enclosing element
becomes a shell with the code `opaque-html`. Cases that decline:

- the parser would repair the block where it sits: a `<p>` inside an open
  `<p>`, a block element inside `<p>`, a nested link, table parts outside
  a table, text directly inside a table, a stray end tag;
- the block holds a `<script>` (the browser runs a served script while it
  parses the page, while Vue inserts the same HTML without running it) or a
  `<noscript>` (parsed differently inside `<template>`);
- its first top-level node is a comment, where Vue's static hydration
  cannot start, or a top-level comment is one of Vue's own `[` or `]`
  comments, which Vue counts to find the end of the Fragment;
- an element in it carries `data-allow-mismatch`, which the browser runtime
  reads as a shell to empty (see "What a shell carries");
- it holds what html5ever, the reference parser, does not model: a
  declarative shadow root (`<template shadowrootmode>`), which the page's
  parse attaches to the parent element, or an `<html>`, `<head>`, `<body>`
  or frame tag, whose attributes the page's parse copies onto the
  document's own elements.

Text inside a block merges into one node as the parser reads it, and the
Fragment comments keep the block's first and last text apart from text
around it, so a block's count never depends on its neighbours. A block
checked this way leaves the parser in the state it found it, so the page's
own check (next section) treats it as absent.

`serialize.py` builds the page HTML the same way for hydration and client
mount. The HTML inside the Vue host never carries `data-cid-*` markers; a document's
`<html>` element, which is outside the host, keeps its marker as in client
mount.

## How the server checks the browser's parse

The browser's HTML parser can close, move or drop an element that is
written in the wrong place (a `<div>` inside `<p>`, a `<tr>` directly inside
`<table>`, text directly inside a table). Vue would then find a different
tree from the one it expects. The writer avoids the cases it knows, and a
check after writing catches the rest.

Most of that check would repeat on every request, because whether the
parser keeps a tag in place depends on which elements are open around it,
not on the text or attribute values in the page. So the writer records the
page as a list of tokens: each start tag, end tag, comment, and whether each
text is whitespace only. `hydration_nesting.rs` in `citry_html_transform`
runs html5ever on a short document for each (open elements, token) pair it
has not seen yet and keeps the answer for the thread. A page passes when the
parser keeps every one of its tokens in place. The module docs give the
argument why a stored answer holds for any later page; in short:

- as long as every earlier token stayed in place, everything the parser
  uses to handle the next token follows from the list of open elements;
- text and attribute values are escaped, so the parser reads them back
  unchanged, and whether a text is whitespace only is part of the token;
- the one attribute value the parser reads for an element the writer can
  write, `type="hidden"` on `input` inside a table, is part of the token.

The writer checks per request what the stored answers do not cover: every
attribute name is lowercase letters, digits, `-`, `_` or `:` and appears
once, no text or value holds a carriage return or NUL, only a shell carries
`data-allow-mismatch`, and a void element such as `br` has no children
(its parent becomes the shell). A text or value holding a control
character or a Unicode noncharacter, which the full parse's tokenizer
reports as an error, sends the page to the full parse. The writer declines
a `pre`, `textarea` or `listing` whose text starts with a newline, and the
token check rejects such a text too, because the parser drops that
newline.

When the token check cannot show the page is kept as written, the page is
written a second time with the full list of nodes it meant to write, and
the whole HTML is parsed with html5ever in the host's `div` context and
compared with that list (`browser_fragment_matches_nodes`). That answer is
final. This happens for an attribute outside
the rules above, for a tag the check leaves to the full parse (raw-text
elements, `template`, `svg`, `math`, and the document's own tags), and
for a page the parser would repair, which then mounts in the browser as
before.

Raw HTML blocks and shell contents are not part of the token list or the
full parse: each is checked where it sits with `static_html_in_context`,
which also shows that the parser is back in the state it was in before the
block. The writer records their byte ranges, and the full parse runs on the
page with those ranges cut out.

On error: a thread keeps at most 65,536 stored element lists; past that it
drops them and learns them again. Each worker thread learns its own
answers, so its first pages pay for a few small parses. A token the stored
answers reject never rejects the page by itself; the full parse decides.

## Values only the browser knows

Component state from `data()` or `setup()`, injected values and event
handlers exist only in the browser. The renderer treats them in two ways:

- Vue sets some values itself while it hydrates, so the server leaves them
  out: event listeners, keys the render lists as dynamic (`:aria-expanded`,
  `:hidden`), `value` on `input` and `option`, and `v-show` (written as
  `display: none` only when the server knows the value is false). Vue
  hydrates every Citry element in its full mode, which applies all of
  these: Citry's runtime creates vnodes with patch flag 0, and a slot's
  Fragment carries Vue's bail flag because hydration never keeps a slot's
  stable marker (`initSlots` in runtime-core).
- Anything else that depends on browser state, such as text, a `v-if` test,
  a `v-for` source or a spread of component state, cannot be written.

A `v-if` written on a Citry component tag compiles to the same conditional
as one on an element, so a test the server can evaluate (prepared data or a
`js_data` value) writes the chosen component or Vue's `<!--v-if-->`
placeholder, and a browser-only test makes a shell.

## Shells and the page-size rule

When a part cannot be written, the nearest enclosing element whose own
attributes are certain is written with `data-allow-mismatch="children"`
(a shell). Vue 3.5 then builds its children in the browser inside the same
`createSSRApp`, without reporting a mismatch, even in the production build,
because `isMismatchAllowed` is not a development-only check. Until then the
shell carries Citry's HTML for its children, which the browser runtime
removes right before Vue hydrates ("What a shell carries" below). With no
element around the part, the page mounts in the browser.

Two conditions keep a shell correct. Vue fills an empty element only when
its vnode is an ordinary element vnode; in production it skips the children
of a vnode compiled as fixed, reusable content. Citry compiles with static
hoisting off (`citry_vue_compiler`), and a browser test with fully static
shell contents fails if that changes. The marker also stays on the element
after hydration, because Vue does not remove attributes its vnode never had.

Besides browser-only values, these parts become shells: a component whose
render is a single text node (Vue steps over one DOM node per component, so
merged or empty text would shift its siblings), a component called with
extra attributes, listeners, `v-model` (a `modelValue` prop and its update
listener), `v-show`, or a custom directive (the server does not apply the
caller's directives to the child's root element), scoped and dynamically
built slots, HTML Python hands over as a finished string (`<c-raw>` contents
or trusted `Markup` with tags) when one of the cases in "Raw HTML blocks"
declines it, style objects, custom directives on elements, text with a carriage return or NUL, `<textarea>` or
`<pre>` text starting with a newline, and elements the browser's parser
would move (a block element inside `<p>`, table parts outside their table,
nested `a`, `form` or `button`).

The page hydrates only when the elements the server writes for Vue to
adopt, shells included, exceed `CitrySettings.ssr_element_threshold`. The
default, 0, hydrates every page that writes an element. A larger value is
an explicit choice to send small pages without their content: such a page
is sent exactly as a browser-mounted page is, with an empty host, and the
parse check is skipped. Each serialization records a `HydrationAdmission`
on the render (`_vue.serialization.hydration_admission`): the page-level
reason, the element count, and one `HydrationDecline` per declined part with
its reason code, the component type key, and the shell's tag or `page`.

Page-level preconditions still apply before any rendering: custom
`on_serialize`, dependency or browser hooks, a configured i18n extension,
a `deps_position` other than `"smart"`, a CSP or JavaScript policy,
call-local security modes, and `deps_strategy` other than `document` keep
the client mount. Unless its `deps_strategy` is not `"document"`, such a
page still sends its content, as described next.

### What a shell carries

The server writes Citry's HTML for a shell's children inside the shell, so
search engines and readers without JavaScript see that part of the page too.
The browser runtime removes it again right before `createSSRApp(...).mount`
hydrates, and Vue builds the shell's children from nothing.

The removal is required, not a clean-up. In Vue 3.5.42's production build,
`hydrateElement` in runtime-core patches only listeners, keys the vnode
lists as dynamic, `value`-like keys on `input` and `option`, `.prop` keys
and custom-element keys; it leaves every other attribute as the DOM has
it. Inside an element marked `data-allow-mismatch="children"`, a mismatched
element with the same tag is adopted silently with its served attributes. A
browser-only `v-if`/`v-else` over two `<p>` elements shows the problem: Vue
adopts the served first `<p>` for the `v-else` branch, keeps its `id` and
`class`, and only corrects its text, with no mismatch reported
(`test_shell_contents_are_served_then_rebuilt_by_vue` in
`test_vue_served_content_e2e.py` fails without the removal).

How the pieces fit:

1. When an element becomes a shell, the writer runs the element's children
   again in a second mode (`StaticWriter` in `server_render.rs`) that
   writes what the server can know before Vue runs: a condition the server
   can test shows its branch, one only the browser can test shows every
   branch, a list or text only the browser knows is left out, listeners and
   directives are ignored, attributes are written from the values the server has (a value
   it cannot print is left out), a `v-show` known to be false hides the
   element, child components are written from their own programs, and raw
   HTML blocks are written unchanged. The server does not locate the
   shell's part in the HTML Python rendered; it writes that part from the
   same render code and data the browser receives.
2. The contents are written only when `static_html_in_context` shows the
   browser's parse keeps them inside the shell, parsed the same way as
   inside a `<template>`. Otherwise the shell is written empty.
3. Contents that would run or load a second time once Vue rebuilds them are
   not written: `<script>` and `<noscript>`, `iframe`, `frame`, `object`,
   `embed`, `applet`, `meta`, `base`, `link`, `portal`, custom elements, and
   any `on*` handler, `is`, `autofocus`, `autoplay`, `preload`, `srcdoc` or
   `http-equiv` attribute. A served script would run while the browser parses the page,
   while a script Vue inserts never runs; a handler would run once for the
   served element and again for Vue's; an autofocused element would take
   focus and then be removed. The shell is then written empty.
4. Each shell's `HydrationDecline` records whether it carries contents
   (`shell_content`). When any does, the bootstrap configuration carries
   `"emptyShells": true`, and `client.js` runs
   `replaceChildren()` on every `[data-allow-mismatch="children"]` element in
   the host in the same task as the mount. A page without served shell HTML,
   such as the benchmark board, never runs that search. The writer declines
   an authored `data-allow-mismatch` in adopted content, leaves it out of
   shell contents, and rejects raw HTML blocks that carry it, so every marked
   element the runtime finds is a shell the server wrote.

Error modes and limits:

- Until the runtime starts, a shell shows every branch of a browser-only
  condition, and an `id` that both branches carry appears twice. The runtime
  removes the contents before Vue creates any element, so no Vue-built
  element ever shares an `id` with a served one, and `getElementById` during
  mount finds only Vue's elements.
- Focus, a text selection or typed text inside a shell's served contents is
  lost when the runtime removes them; focus elsewhere on the page is not
  touched (a browser test pins this).
- Under a Content Security Policy whose `style-src` does not allow inline
  styles, which the site sends without telling Citry (Citry's own CSP modes
  keep a page from hydrating), the browser blocks each served `style`
  attribute and reports it once; Vue then sets the style through the DOM,
  which the policy allows. An adopted element with a `style` attribute
  behaves the same way.
- `<textarea>` and `<title>` shells stay empty: the parser reads their
  contents as text, so the check never matches.
- A component call with `v-show` or a custom directive, and anything the
  program reader left unread, are left out of the contents. Contents
  larger than 1 MiB are not written: every branch of a browser-only
  condition is written, so conditions nested around a slot could repeat
  the same content many times.
- A `<style>` element in a shell's contents applies to the whole page while
  it is shown, as the same element does once Vue builds it.
- If the mount throws after the runtime emptied the shells, they stay
  empty; the failed mount has already left the page broken.

## Pages that cannot hydrate

A page that hydrates sends its content as Vue's own HTML. A page that
cannot hydrate, for any reason other than the author's choice, still sends
its content: the Vue host carries Citry's ordinary server HTML, the same
HTML `deps_strategy="simple"` writes, and the browser's client mount
replaces it. Vue's `createApp().mount(host)` in runtime-dom sets
`host.textContent = ""` and then renders synchronously in the same task,
so the browser never paints an empty host between the two, and no served
element (or its `id`) survives next to the one Vue builds. The root
component always has a compiled render function, so Vue never reads the
host's HTML as a template.

How the server builds it (`serialize.py`, `prepare_vue_serialization`):

1. A client-mounted document normally skips building its body children's
   HTML (`_can_defer_vue_body_children`). The frame pass keeps those
   children aside instead of dropping them, and `server_html()` builds
   them only when `prepare_vue_serialization` asks, so a page that
   hydrates or opts out pays nothing.
2. `prepare_vue_serialization` asks for it when the page did not hydrate,
   `deps_strategy` is `"document"`, and the recorded page reason is not an
   explicit opt-out (`ssr-disabled`, `below-threshold`) or output that is
   not a document (`not-a-document`).
3. `_server_host_contents` takes the body's contents (or the whole output
   when it is not a document), removes every dependency placeholder, and
   declines when a `<script` start tag remains.
   `_server_contents_pass_policies` then declines for any JavaScript
   policy, and for a CSP mode when a private CSP validator finds anything
   in the copy (inline handlers, `javascript:` URLs).
4. `finalize` accepts the host without the whole-page `HTMLParser` check
   when it reached the page byte for byte and the only `on_serialize` hook
   is the built-in dependency hook; otherwise the parser check runs and
   accepts any content inside the host.

`HydrationAdmission.server_html` records whether the host carried server
HTML.

Error modes:

- A dependency placeholder (`<c-js />`, `<c-css />`) inside the body is
  removed from the host, as it is from the empty host, so assets go to
  their default place after the host. An asset placed inside the host
  would be removed by Vue's mount.
- A body holding a `<script` start tag keeps an empty host: the browser
  would run the script while parsing, while Vue inserts trusted HTML
  without running its scripts. Python text and attribute values are
  escaped, so the tag comes from trusted HTML; a false match (for example
  inside an HTML comment in trusted HTML) only costs the served content.
- The copy is Citry's static HTML, not Vue's first render: both branches
  of a browser-only `v-if`/`v-else`, `v-show`-hidden elements, a `v-for`
  template once, and Vue directive attributes are served and shown until
  Vue mounts. Stripping them needs an HTML rewrite of the copy; not built.
- A page with a JavaScript policy, or with a CSP mode whose check of the
  copy finds inline handlers or `javascript:` URLs, keeps an empty host,
  so serialization neither fails nor warns where it did not before.
- A page served through Citry's mounted routes links each initial component
  stylesheet in `<head>` with the `integrity` and `crossorigin="anonymous"`
  the runtime requests owned files with, so the served HTML paints styled
  and each file downloads once. The runtime's `loadStyle` adopts a linked
  stylesheet whose `sheet` exists (the browser runs no inline script before
  the stylesheets above it have loaded or failed) and replaces one whose load
  failed with a new request. A standalone document inlines the same
  stylesheets in `<head>`. A mounted fragment is inserted into a page later,
  so the runtime still loads its stylesheets then.
- The `<script` rule also declines scripts that never run
  (`type="application/ld+json"`, inside `<template>`), and it does not
  catch `on*` attributes, `<iframe srcdoc>` or custom elements, which run
  once from the copy and again after Vue rebuilds.
- Under a CSP whose `style-src` has no inline allowance, the browser
  blocks and reports each `style` attribute in the served HTML; Vue then
  sets the style through the DOM, which CSP allows. A browser test pins
  this.
- A custom `on_serialize` hook sees the host's content and may change it;
  Vue replaces whatever the host holds, so only the host element itself
  is checked.
- Focus, selection and typed text in the served HTML are lost when Vue
  replaces it, and media and frames load again.

## The render code the server runs

The server does not run JavaScript. `server_render.rs` parses the
compiler's render function with the oxc JavaScript parser, keeps only the
shapes listed here, and runs them over the manifest's JSON.
Everything else is either left for Vue to set while hydrating or declined.

A render function is read when it is a `function render(...)` declaration
whose first parameter is a plain name (the component instance) and whose
body holds only variable declarations of `_resolveComponent("tag")` or
`_resolveDirective(...)` and a `return` (the last one counts).
If it is not (or the code does not parse), reading raises `ValueError`,
the definition gets no program (`CompiledRender.server_render` is `None`),
and every occurrence of it is declined as `component-lookup`.

Inside the returned expression, parentheses and `(_openBlock(), vnode)` are
skipped, and these vnode shapes run:

| Compiled code | What the server writes |
| --- | --- |
| `_createElementVNode`, `_createElementBlock`, `_createVNode` or `_createBlock` with a string tag (a `<component :is>` alias maps to its real tag) | the element, its attributes and its children |
| the same helpers with a component from `_resolveComponent`, or `_resolveDynamicComponent("literal")` | the child occurrence named by the `citry-id` prop, rendered with its own program; the call may carry only `citry-id` and `key` |
| the same helpers with `citry-opaque-html` | `<!--[-->`, the record's HTML unchanged, `<!--]-->`, after the checks in "Raw HTML blocks"; otherwise the enclosing element becomes a shell (`opaque-html`) |
| `_Fragment` with an array or with `_renderList(source, (item, index) => vnode)` | `<!--[-->`, the children or one child per array item, `<!--]-->`; the source must be an array, `null` or `undefined`, and the function takes at most two parameters |
| `test ? vnode : vnode` | the branch the test selects |
| `_createCommentVNode("v-if")`, `_createCommentVNode()`, `return null` | `<!--v-if-->` or `<!---->`; other comment text is declined |
| `_createTextVNode(x)`, `_toDisplayString(x)`, a string literal or a `+` of them | the text, escaped |
| `_renderSlot(_ctx.$slots, "name", props, () => [fallback])` | `<!--[-->`, the caller's fill or the fallback, `<!--]-->` |
| `_withDirectives(vnode, [[_vShow, value]])` | the element, with `style="display: none;"` only when the value is known to be false; an element that also has its own `style` and a false value is declined |
| a `textContent` prop (what `v-text` compiles to) on a non-void element with no children | the value as the element's text, escaped, when `toDisplayString` of it is known (see the expression rules below). Hydration neither reads nor compares that text (`hydrateElement` in runtime-core 3.5.42 checks children only when the vnode has some) and sets the prop itself when the render lists it as dynamic, so an unknown value, or text the parser would change (a carriage return, text in a table part, a leading newline in `<pre>`), is written as an empty element with no decline. A `textContent` key from a `v-bind` object is not dynamic, so hydration keeps the server's text: it is written exactly, and text the parser would change is declined (`text-value`), which makes the parent the shell. With authored children, the children are written: hydration either compares the DOM with them (text children, or an empty value) or skips them (element children with a non-empty value), then sets the prop |

Slot fills must be an object literal of `name: _withCtx(() => [...])`
entries; `createSlots` (conditional or looped slots) is not run, and a fill
with slot parameters (a scoped slot) is declined when it renders.

Props are an object literal with fixed keys, `_mergeProps(...)`,
`_normalizeProps(x)`, `_guardReactiveProps(x)`, or a spread value
(`v-bind="obj"`), which must evaluate to a JSON object or to nothing. Keys
`on` + a non-lowercase letter are listeners: the server never evaluates
them, and hydration attaches them.

Expressions are limited to what JSON data can answer:

- string, number, `true`/`false`, `null`, `undefined` and `void` literals,
  and a negated number literal;
- `_ctx.$citryPrepared`, the occurrence's `preparedData` (an empty object
  when the occurrence has none),
  `_ctx.<key>` for each `js_data` key, and the parameters of the
  surrounding `_renderList` and slot functions;
- property reads with `.name` or `["literal"]`, `length` of an array or
  string, and array indexes;
- `!`, `===`, `!==`, `&&`, `||`, `? :`, and `+` when one side is a string
  and the other a string or an integer;
- `_toDisplayString`, `_normalizeClass` of a string, array or object, and
  `_normalizeStyle` of a string or nothing.

Any other expression is a browser-only value: another name on `_ctx`
(`data()`, `setup()`, props, methods, injections, `$slots` used as a
value), a function call, `??`, `==`, comparisons, optional chaining, a
computed property name that is not a literal, a property JavaScript
objects inherit (`toString`), and an object or array printed as text. A
number that is not a safe integer can still be tested and compared, but
printing it as text or as an attribute is declined.

Attributes follow Vue's `runtime-dom` `patchProp`, not its server renderer:
the server writes what the element holds after Vue's first render in the
browser. `class` is normalized and a null class is removed; `style` is
written only from a string; `value` on `input`, `button`, `option` and
`data`, `checked` on `input` and `selected` on `option` are written as
attributes; `hidden` is written for `true`, `false`, `null` or `""`; names
containing `-`, `:` or `_`, a fixed list of attribute-only names (`for`,
`tabindex`, `colspan`, ...), the names Vue always sets as attributes
(`spellcheck`, `draggable`, `translate`, `form`, and `width`/`height` on
media elements) and a fixed table of reflected DOM properties per tag are
written; `true` on a custom attribute becomes `"true"`, and `null` removes
it. An authored `data-allow-mismatch` is declined, because it would hide a
mismatch. A key with capital letters, a `.prop` or `^attr`
modifier, a name outside those lists (`popover`, `fetchpriority`), or an
object value cannot be written. When such a key is one Vue sets again
while hydrating (a key the render lists as dynamic, or a key ending in
`value`, or `indeterminate`, on `input` and `option`), it is left out; otherwise the
element is declined.

Elements are declined when their tag is not lowercase letters and digits,
when the browser parses them as raw text or foreign content, or they
belong to the document itself (`script`, `style`, `xmp`, `iframe`,
`noembed`, `noframes`, `noscript`, `plaintext`, `template`, `svg`, `math`,
`html`, `head`, `body`, `frameset`), when a void element has children, or
when the HTML parser would move them (see "Shells and the page-size
rule"). Text is declined when it holds a carriage return or NUL, when it
is non-whitespace text directly inside `table`, `thead`, `tbody`, `tfoot`,
`tr` or `colgroup`,
when a `pre`, `textarea` or `listing` starts with a newline, when it is a
component's whole render, and when it is the page's root.

A declined part becomes a shell as described above: the error travels up
to the nearest element whose own attributes were written, and that element
is written as a shell. With no such element, the page mounts in the browser
(`host-root`). Render code nested deeper than 200 vnode or expression
levels is not read, and
output nested deeper than 256 levels is not written; both are declined
like any other part.

## Checking the server's HTML against Vue

`scripts/vue_render_parity/check.py` compares the server's HTML with Vue's
own server rendering for every page the non-browser Python tests and the
benchmark board's server tests prepare:

1. A pytest plugin (`collect.py`) records each prepared page while the
   non-browser suite and the benchmark board's server tests run: the
   manifest JSON, the component tags, and each compiled definition.
2. The script reads the definitions into programs and makes the call the
   server makes, `_rust.vue._render_for_hydration`, with the page-size
   threshold at 0 so every page is written.
3. `render.mjs` loads each definition's browser JavaScript and renders the
   page with `renderToString` from Vue 3.5.42 in the client package's
   `node_modules`. A small stand-in for the Citry client supplies the
   compiler helpers (patch flag 0, dynamic element aliases, the
   `citry-opaque-html` component) and component options that expose
   the occurrence's `preparedData` as `$citryPrepared` and the `js_data`
   keys. A browser-only value reads as a
   marker that can be called and read at any depth, so the render
   finishes. The Rust side declines these values, so they should only
   reach shells or keys Vue sets while hydrating; the check prints each page
   where Vue read one and the Rust side declined nothing, for a person to
   read.
4. The two HTML strings are split into tags, text and comments and walked
   together.
5. Each page is also written a second time with `full_parse_check=True`,
   which parses the whole HTML instead of using the stored parser answers.
   The two results must be identical.

Pages the Rust side declines as a whole are counted, not compared. Inside a
compared page, a shell is compared by its tag and attributes; the Citry HTML
the Rust side wrote inside it (removed by the runtime before Vue hydrates)
and Vue's contents for it are both skipped. Raw HTML blocks are compared
like any other written HTML. The walk treats these as equal, because each
pair is the same page to the browser or is set by Vue while hydrating:

- character references and their characters (`&quot;` and `"`), and
  adjacent texts and one joined text (the parser joins them);
- `checked` and `checked=""`;
- two `style` values with the same declarations, spaced differently;
- `class=""` or `style=""` from Vue's server renderer and no attribute:
  Vue's server renderer writes the empty value for a null class or style,
  while the client removes it, and the server follows the client;
- an attribute Vue sets again while hydrating (a key the render lists as
  dynamic, `value`-like keys on `input` and `option`, any key of a custom
  element) and no attribute, and likewise `display` under `v-show`. The
  stand-in marks these keys on each element while Vue renders; the Rust
  side is not trusted to name them;
- for a `textContent` or `innerHTML` key listed as dynamic, the element's
  own children: Vue's server renderer writes the key's value as the
  contents, but hydration sets the key itself and replaces whatever the
  server wrote, so the stand-in drops the key before Vue renders. A
  `textContent` key on an element with no children is kept instead, so any
  text the Rust side writes there is compared with Vue's; an element the
  Rust side left empty for hydration to fill is accepted.

Each run also checks the comparison: small wrong variants of every
compared page's Rust HTML (a missing Fragment anchor, a changed attribute
value, a changed text, a dropped attribute Vue does not set while
hydrating, an added `display: none`) must each be reported. The run fails
on a mismatch, a Vue render error, a missed variant, a page whose HTML
fails the native parse check, a page where the token check and the full
parse disagree, or no page compared at all.

Result on 2026-09-27: 568 recorded pages using 951 compiled render
functions; 17 pages had no compiled definitions (the server never renders
them for hydration), 17 mounted in the browser (`host-root`), and 534 were
compared, with 55,230 elements and 954 shells. There were no mismatches,
no Vue errors and no parse-check failures, and all 1,907 wrong variants
were reported. Shells held 19,106 more elements of Vue's output that were
not compared; the most frequent decline codes were `unsupported-attribute`
(697) and `component-attrs` (195). Raw HTML blocks declined once
(`opaque-html`).

What the check does not cover: browser tests (their pages are not
recorded); user component options (`data()`, `setup()`, methods, `inheritAttrs`) are not loaded, so values from them
read as browser-only; attributes Vue sets while hydrating are allowed to be
missing even when the server could have known them; the browser's own
parse of the HTML is covered by the native parse check, not here; where
Vue's server renderer and its client disagree (a `false` class is `"false"`
in the browser but empty from the server renderer) and the Rust side
followed the server renderer by mistake, the check cannot tell.

Run it from the repository root after `pnpm install` and a native build.
Collection runs the non-browser test suite with 4 workers once (about 80
seconds on a laptop); the comparison takes a few seconds:

```sh
.venv/bin/python scripts/vue_render_parity/check.py
.venv/bin/python scripts/vue_render_parity/check.py --reuse   # skip collection
```

It exits with status 1 on any of the failures listed above, and
`--report FILE` writes every page's HTML from both renderers.

The repository gate (`scripts/check.py`, which CI runs) also runs it without
a second test run: its main `pytest` phase loads the recording plugin, and
its `vue render parity` phase then runs `check.py --reuse` over the pages
that phase recorded. That run leaves out the qualification tests and the
benchmark board's server tests, so the standalone command above also
compares the pages those tests prepare.

## After hydration

The hydrated page equals a page Vue mounted in the browser, except that
shells keep their marker, a static `style` attribute keeps its authored text
where client mount leaves the browser's normalized form, and Fragment
boundaries (raw HTML blocks included) are the server's comment nodes where
client mount uses empty text nodes. The host also lacks `data-v-app`, which Vue's runtime-dom adds
only in `createApp().mount`; tests wait for `citry:ready` instead. Before
Vue starts, parts hidden by browser state are visible and
typed input is replaced when Vue sets `value`; `vue-runtime.md` documents
this for users.

## Remaining limits

- The parse check is the final word on parser repairs; a repair the
  renderer's rules miss makes the whole page mount in the browser over
  Citry's server HTML rather than one shell.
- A shell whose contents would hold a script or another element listed in
  "What a shell carries" is still sent empty, so that part is not in the
  served HTML.
- The compiler's `hydrationPlan` is not read at runtime. It stays as the
  compiler's independent report of anchors and attribute rules; a Rust test
  checks, for representative templates, that the renderer writes the same
  kinds and numbers of anchors.
- Citry does not run Vue on the server; directives other than `v-show`,
  Teleport, Suspense, Transition and `v-html` are left to the browser.
