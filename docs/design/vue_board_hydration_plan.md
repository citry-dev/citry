# Plan: hydrate the public project board

Status: approved on 2026-09-25. Step 0 has run and passed for the
rows-region variant; see "Step 0 results". Steps 1 to 8 are implemented;
steps 3 to 8 replaced the mechanism of steps 1 and 2 (see "Steps 3 to 8 as
built"). Since 2026-09-27 every interactive document sends its content in
its served HTML by default, and the public board hydrates at every size
(see "Decision 2026-09-27: content in the served HTML by default").

## Why

At 1,400 outputs the public board builds every row in the browser. Vue
creates each element after the response arrives. In the release-build cohort
run, the browser worked about 187 ms after the response, and layout finished
about 73 ms after Citry reported ready (`public-vs-private-baseline/release-20260925/results.json`,
arm B). The research report
(`/Users/mac/repos/citry/report.html`, `citry_vue`, 1,400 outputs) sent
server HTML that Vue adopted instead of rebuilding ("hydration"). Its
request-to-layout time was 368 ms on first load against about 533 ms for the
public board today. Server time now explains only 25 to 40 ms of that
difference, so the browser work is the larger part.

A ceiling experiment (`.benchmarks/research/vue-architecture-experiments/ssr-ceiling/`)
captured the page Vue builds in the browser and served it back as server
HTML. It hydrated with zero mismatches and an identical final DOM. At 1,400
outputs it reached layout 84 to 98 ms sooner. At 140 outputs it was 13 to 20
ms slower, because the browser parses twice the HTML and then hydrates. On the
server, writing the body HTML cost about 56 ms, the native structure check
about 24 ms (release build), and copying the expected element list from
Python about 40 ms. Counting all three, the net result at 1,400 outputs was
about zero or negative. Full-board hydration is therefore not yet shown to be
worth building.

## Step 0: measure before building (research only)

Two measurements, both outside production code:

1. **Realistic server cost.** Force the board to write its body HTML, add the
   Vue anchor comments (explained in step 2), and build the expected element
   list the way a production path would. Time it warm at 140 and 1,400
   outputs after the current server optimizations land, with the release
   build.
2. **Rows-region gain.** Serve captured server HTML for the outputs panel
   only, and let the rest of the page mount in the browser inside the same
   Vue app, marked with Vue's `data-allow-mismatch="children"` on elements
   next to the rows (never on an element that contains them). Compare against
   full-page captured HTML and against client mount at 140 and 1,400.

Decision rule: build only if, at 1,400 outputs, the browser gain minus the
realistic server cost improves request-to-layout by at least 50 ms. If the
rows-region variant keeps most of the gain, build that first.

## Step 0 results

Measured on 2026-09-25 with the release native build
(`.benchmarks/research/vue-architecture-experiments/hydration-step0/README.md`).
The public board now declares `simple = "vue"` on `ProjectOutput` and has the
server optimizations from the rollout doc. It still mounts in the browser.

- Public board, request to layout: 111/63 ms at 140 outputs (first/second
  load) against the report's 162/79; 425/382 ms at 1,400 against 368/343.
  Server prepare at 1,400 is 151/111 ms against the report's 204/180, so the
  remaining gap is browser work and layout.
- Extra server cost of hydration output at 1,400 outputs: about 36 ms for the
  whole page (body HTML 9.5 ms, anchor comments under 0.4 ms, a modelled
  expected element list 3.4 ms, native structure check 23 ms). The anchor cost
  and the element list are modelled, not produced by a production path.
- Rows region: the server writes the outputs panel in full and its four
  ancestors; twelve other elements are written as empty shells marked
  `data-allow-mismatch="children"`, and Vue builds their contents in the
  browser inside the same app. At every count it hydrated with zero replaced
  elements and zero unexpected mismatches, and ended with the same DOM as
  client mount. Removing the markers made Vue report mismatches, so the check
  can fail.
- Net request-to-layout gain (browser gain minus extra server cost), rows
  region: -8.8, -4.8, -0.9, +6.9, +30.7 and +63.2 ms at 140, 280, 560, 840,
  1,120 and 1,400 outputs. Full page: -19.8 to +48.9 ms. Almost all the gain
  is layout finishing during parsing; measured to "ready" alone, hydration is
  about even.
- Break-even: about 15,300 Vue-managed elements for the rows region and
  22,300 for the full page. Between 15,000 and 25,000 elements the net stays
  within 10 ms either way.

Proposed rule: hydrate only when the hydrated region contains more than
20,000 Vue-managed elements. This holds for one machine on loopback without
compression; a slower client CPU lowers the break-even, a real network raises
it. The threshold is a setting with this default, so it can be tuned per
deployment.

## Prior art

- Supported selective hydration, all or nothing per page:
  `_vue/serialization.py` `_preflight_single_root_hydration` (~1010),
  `_bind_single_root_hydration_proof` (~1076), and `_single_root_typed_facts`,
  the function that walks the typed render (~578-709). The one-root rule lives
  in Python: `_single_root_hydration_parts` (~503). Tag list (~404-423),
  bound-prop list (~426), click-only events (~452-459), document shell
  (~799-917), comments rejected (~391). `serialize.py` whitespace guards
  (~679-683, ~940-945).
- Native check: `crates/citry_html_transform/src/hydration_structure.rs`. It
  already accepts several top-level elements; it rejects non-empty text at the
  fragment root (~128) and every comment (~148), and compares decoded
  attributes exactly (~88-99). Exposed through
  `citry_core_py/src/html_transform.rs`, `_rust.pyi`, and the
  `citry_core.html_transform` wrapper.
- Client: `client.js` `createSSRApp` path and the test-only hydration
  report. Vue 3.5.42 is pinned in `packages/js/citry-client/package.json`.
- The research prototype this plan replaces admitted only the benchmark
  page's exact root tags and cleaned up whitespace and attributes on the
  finished HTML inside the serializer; its benchmark driver was
  `.benchmarks/research/vue-architecture-experiments/four_region_page_tti_server.py`.
  Its ideas informed the plan; none of its code is reused.
- Row HTML for `simple = "vue"` rows, which a generated writer produces
  from each row's recorded values when serialize writes output that
  contains the rows (`tests/test_simple_vue_row_html.py`). A hydrated page
  never asks for it, so no board row HTML is reused.

## What stops the board today

The first construct that makes the server fall back to client mount is
`LocalDisclosure`'s `<p :hidden>`. Behind it:

- `c-for`/`c-if` around components produce output the Python preflight check
  rejects, and Vue's anchor comments are never written.
- Ordinary components write `@click`/`:title` into the HTML verbatim.
- Slot fills and the context provider component have no element root; the
  body has two roots.
- Missing tags: `nav`, `a`, `header`, `form`, `label`, `input`, `textarea`,
  table tags, `details`/`summary`; `<h3>` inside `<button>` needs a
  content rule.
- `v-show`, `:hidden`, truthy `:aria-expanded`, `@c-submit.prevent`,
  `c-checked`, Python-evaluated attributes, and the root `c-bind` spread in
  `project_output.html`, whose attribute names vary per row.
- Any `<title>` or `<textarea>` anywhere disables all whitespace decisions;
  every row has a `<textarea>`.

## Chosen design: hydrate proven regions, client-mount the rest

One Vue app still hydrates the whole page host. The server decides, per
subtree, whether it can prove the HTML Vue expects. A proven subtree is
written in full. An element whose own opening tag is proven but whose
contents are not is written as a shell marked
`data-allow-mismatch="children"`; Vue builds its contents in the browser
inside the same app, with ordinary state, provide/inject and events (see
"What a shell carries" in `vue_ssr_selected_tree_plan.md` for the HTML the
shell shows until then). The
marker is never placed on an element that contains a proven region, because
it would hide mismatches inside it. If no element with a proven opening tag
separates an unsupported part from a proven one, the decision moves to the
parent, and at the host the whole page client-mounts as today.

Steps, each landing with its own tests. The page keeps client-mounting until
the rows region of the board is proven.

1. **Per-page rule and decline reasons.** Count the Vue-managed elements
   inside proven regions; hydrate only above the threshold (default 20,000,
   a Citry setting). The Python check records a reason code and source
   location for each subtree it declines, so tests and diagnostics can show
   why a page client-mounts.
2. **Region verdicts and shells.** The walk returns a verdict per subtree
   instead of one yes/no per page, and the server writes empty marked shells
   for declined subtrees. The native check skips the children of marked
   shells.
3. **Vue anchor comments from the compiler.** Vue marks a fragment with
   `<!--[-->` and `<!--]-->`: each `v-for`, each item that is itself a
   fragment, slots, and multi-root components. It writes `<!--v-if-->` for an
   empty branch and `<!---->` for a component that renders nothing. The
   compiler reports where the compiled render function creates each one; the
   server never guesses from HTML. The native check learns comment events and
   root-level whitespace. The compiler half is built: the artifact's
   `hydrationPlan` reports each marker (see "What the compiler reports for
   hydration" in [`vue.md`](vue.md)).
4. **Loops and slots inside a region**, walked using those anchors.
5. **Attributes inside rows.** Vue patches, during hydration, the keys its
   compiled render marks as dynamic, event listeners, `.prop` bindings, and
   `value` on inputs; static attributes must match exactly. The compiler
   reports which case each attribute is (built, in the same
   `hydrationPlan`). Python-evaluated values, including
   the root `c-bind` spread and `c-checked`, are written exactly as Vue's
   first client render would. Spread names are checked per row.
6. **Tags and parsing contexts the rows use**: `form`, `label`, `input`,
   `textarea` (leading newline), `details`/`summary`, `<h3>` inside
   `<button>`. Results are stored per definition and parent context.
7. **Values only the browser knows** (`v-show`, `:hidden`, truthy
   `:aria-expanded`) are left out by the server and applied by Vue during
   hydration. Decided 2026-09-25: the pre-hydration state (hidden parts
   visible until hydration, forms working without JS, typed input replaced)
   is accepted. Document it for users and measure layout shift.
8. **Documents.** The board's `<title>` and each row's `<textarea>` today
   disable all whitespace decisions; decide whitespace per piece of authored
   text using its real ancestor elements instead.

### Steps 1 and 2 as built

This records the first implementation; steps 3 to 8 replaced its walk
(see "Steps 3 to 8 as built").

The setting is `Citry(ssr_element_threshold=20_000)`; it counts every
element the server writes for Vue to adopt, shells included. Declined parts
carry the reason codes listed on `HydrationDecline`. The native check requires
each shell to be empty instead of skipping its children, because Vue would
hide any mismatch in content left under one (the HTML a shell carries since
2026-09-27 is cut out of the checked HTML and checked on its own). Two limits
remain: a
shell can only be placed on an element written by a component's own template
parts, not inside compiled leaf output (most components with Python
expressions), and declines found inside authored static markup name the
component but not the template line. At 1,400 outputs the board declines at the page body for
these reasons, in walk order: the body has two roots (`LocalDisclosure` and
`Board`), which needs fragment anchors (step 3); the `Board` root
`<section>` carries `@c-submit.prevent` and `c-data-*` values (step 5);
`ProjectLayout` renders `Layout` at its root, which renders the context
provider at its root (steps 3 and 4); and `LocalDisclosure` has
`<p :hidden>` (step 7) and `label`/`input` (step 6), which make its `aside`
a shell. Deeper blockers are hidden behind these.

### Steps 3 to 8 as built

The Python walk of steps 1 and 2 compared Citry's own render parts with
what Vue would create, one construct at a time. Extending it to loops,
slots, component roots and attributes meant restating Vue's rendering rules
in Python for every construct, and running them per row. Steps 3 to 8
instead write the HTML from the same code the browser runs:

- The native compiler reads each compiled render function once, when its
  definition compiles, into a small program
  (`crates/citry_vue_compiler/src/server_render.rs`,
  `CompiledRender.server_render`).
- Per request, the server runs those programs over the prepared manifest,
  the same `preparedData` and `js_data` values the browser receives
  (`_rust.vue._render_for_hydration`, called from
  `prepare_vue_serialization`). The result is what Vue's first render in the
  browser creates: Fragment anchors for lists, `<template v-for>` rows,
  `v-if` branch Fragments, slots and multi-root renders; `<!--v-if-->` and
  `<!---->` placeholders; attributes as Vue's `patchProp` leaves them; and
  text exactly as the compiled render emits it.
- The same native call checks that the browser's parser keeps every
  written node in place. Parser answers are stored per list of open
  elements and token, so a request only parses the nestings it has not met
  before; a page the stored answers cannot cover is parsed in full with
  html5ever in the host's `div` context
  ([`vue_ssr_selected_tree_plan.md`](vue_ssr_selected_tree_plan.md#how-the-server-checks-the-browsers-parse)).

What each step became:

- Step 3: anchors come from the render function's Fragments and comment
  vnodes, which is also what the compiler's `hydrationPlan` reads; a Rust
  test checks, for representative templates, that the renderer writes the
  same kinds and numbers of anchors as the plan lists. Two roots, a
  component at the root and the provider at the root are Fragments with
  anchors and are written in full.
- Step 4: `c-for` over components, loops inside compiled leaf
  output, `c-if` branches, slot fills, forwarded slots and the context
  provider are ordinary render function calls. A slot whose content renders
  only placeholders falls back as Vue's `ensureValidVNode` does.
- Step 5: every attribute goes through the rules of Vue's `runtime-dom`
  `patchProp`: `true` on a custom attribute becomes `"true"`, `null`
  removes it, `checked`, `selected` and `value` are also written as
  attributes, classes are normalized, and a static `style` string is
  written as authored. Keys the render lists as dynamic, listeners, `value`
  on inputs and `v-show` are set by Vue while it hydrates, so a value only
  the browser knows is left out there. Vue hydrates every Citry element in
  its full mode, including slot content (Citry's runtime creates vnodes
  with patch flag 0, and hydration never keeps a slot's stable marker), so
  every listener and dynamic key is applied.
- Step 6: every HTML tag the parser keeps in place is written. The renderer applies the
  HTML parser's rules for a `<p>` closed by a block element, table parts,
  nested `a`, `form`, `button`, list items and `select` contents, and makes
  the parent a shell where the parser would move an element; the parse
  check catches anything else and makes the page mount in the browser.
- Step 7: `v-show`, and bound attributes the render marks as dynamic (such
  as `:hidden` and `:aria-expanded`) whose value comes from browser state,
  are left out and applied by Vue. `vue-runtime.md` documents the
  state before hydration.
- Step 8: whitespace is decided by the compiler for each piece of text,
  inside its real ancestors, because the server writes the render function's
  own text, so whitespace does not depend on `<title>` or `<textarea>`.

Shells follow the step 2 rule: an element whose own attributes are certain
but whose contents are not is written with the marker and Vue builds its
contents; with no such element, the page mounts in the browser. Reason codes
are listed on `HydrationDecline`, without a template line.

`simple = "vue"` row HTML is not reused for hydration, and a hydrated page
never writes it. It is the HTML Citry writes for static output: it has no Fragment anchors,
keeps Vue directive attributes for the browser to strip, and formats Python
values the way Citry's attribute formatter does rather than the way Vue's
`patchProp` does. Writing rows from the render programs costs about 11 ms
at 1,400 outputs including reading the manifest, which is less than
adapting that HTML would need.

Measured with the release build (warm, in process, median of 11 samples,
`render().serialize()` against `serialize(ssr=False)`): at 140 outputs the
page stays below the threshold (3,708 elements) and serialization costs
1.3 ms more; at 1,400 outputs it hydrates (36,018 elements, no shells) and
serialization costs about 36 ms more (the native call is about 29 ms, of
which the parse check is about 18 ms). "Server cost of hydration after
the stored parser answers" below has the numbers after that change.

The public board writes every part in full at 1,400 outputs, not only the
rows region: nothing in it depends on browser state except `v-show` and
bound attributes that Vue sets itself. Step 0 measured the full page (arm
b) about 14 ms less favorable than the rows region at 1,400 outputs, mostly
because the hidden tab panels are laid out before Vue hides them (arm k
measured that separately). Whether to send panels hidden by browser state as
shells is a separate decision.

Not built: components called with extra attributes, scoped and dynamic
slots, style objects, custom directives, and text with a carriage return or
NUL. Each is written as a shell. HTML Python hands over as a finished string
(`<c-raw>` contents or trusted `Markup` with tags) is written for Vue to
adopt since 2026-09-27 (see "Raw HTML blocks" in
[`vue_ssr_selected_tree_plan.md`](vue_ssr_selected_tree_plan.md#raw-html-blocks)).

### Server cost of hydration after the stored parser answers

Since 2026-09-25 the server first checks the page's tokens against stored
parser answers and parses the whole page only when they cannot decide. The
writer builds the list of expected nodes only for that full parse, and two
Python checks on the finished page count a long string only when a cheap
position check cannot decide.
Same measurement as above (release build, warm, in process, median of 15
samples, three runs after the change, `.benchmarks/research/vue-architecture-experiments/hydration-server-cost/`):

| Outputs | Hydrated minus client mount, before | After |
| ---: | ---: | ---: |
| 140 | 1.7 ms | 1.0 to 1.2 ms |
| 1,400 | 38.7 ms | 10.8 to 12.4 ms |

At 1,400 outputs the native call fell from 31.5 ms to 10.0 ms: reading the
manifest takes about 2.4 ms, writing the HTML about 6.5 ms, and the token
check about 1 ms. The host HTML is byte for byte the same as before.

Performance rule: compute facts once per compiled definition and parent
context; per request, only check values. Never run the Python HTML parser over
the document (it cost 109 ms in the research prototype page). Check parser
nesting against the stored per-thread answers, and build the expected node
list only for the full parse. Measure only with the release native build.

## Decisions after steps 3 to 8 (2026-09-25)

- **Server render programs are the chosen mechanism.** The server runs the
  compiled Vue render functions in Rust over the same prepared data the
  browser receives, instead of re-stating Vue's rules in Python for each
  construct. Conditions: a test runs every compiled template in the test
  suite through Vue's own `renderToString` and through the Rust program and
  compares the output, and the docs state which subset of compiled render
  code the Rust program supports. Anything outside that subset becomes a
  shell or client-mounts. Both conditions are in place for the non-browser
  tests: `scripts/vue_render_parity/check.py` compares the two renderers on
  every page those tests and the board's server tests prepare (browser
  tests are not recorded), and
  [`vue_ssr_selected_tree_plan.md`](vue_ssr_selected_tree_plan.md#the-render-code-the-server-runs)
  lists the supported render code. It runs on demand, not in CI.
- **Elements that start hidden: not built.** The server cannot know a
  `v-show` value that lives in component `data()` or injected state, so it
  writes those elements visible and Vue hides them while hydrating. Keeping
  the inactive board panels hidden measured about 7 ms faster at 1,400
  outputs in step 0, and the board meets its targets without it. Reading
  literal initial state from component JavaScript is tracked in
  [#146](https://github.com/citry-dev/citry/issues/146).

## Decision 2026-09-27: content in the served HTML by default

The maintainer decided that search engines and readers without JavaScript
must find a page's content in its served HTML without the author doing
anything. The rule is now:

- `ssr_element_threshold` defaults to 0, so every page that writes an
  element hydrates when it can. The step 0 rule (hydrate above 20,000
  elements) weighed only load speed; content in the HTML outweighs the
  few milliseconds a small page could save. The setting stays as an
  explicit choice to send small pages without content, next to
  `ssr=False`.
- A page that cannot hydrate (a page-level reason such as a Content Security Policy,
  custom hooks, another asset position, `host-root` or
  `browser-structure`) sends Citry's ordinary server HTML inside the Vue
  host, and Vue's client mount replaces it.
  [`vue_ssr_selected_tree_plan.md`](vue_ssr_selected_tree_plan.md#pages-that-cannot-hydrate)
  describes the mechanism and its error modes.
- A shell inside a hydrated page carries Citry's HTML for its children,
  and the browser runtime removes it right before Vue hydrates, because
  Vue's hydration does not correct static attributes on elements it adopts
  under `data-allow-mismatch` (see "What a shell carries" in the same
  document). A shell whose contents would hold a script, or something else
  that runs or loads again when Vue rebuilds it, is sent empty.
- Raw HTML blocks (`<c-raw>`, trusted `Markup`) are written for Vue to
  adopt when the page's parse keeps them as Vue would insert them.
- Measured cost (release build, warm, in process, median of 15 to 21
  samples, `.benchmarks/research/vue-architecture-experiments/ssr-shell-content/`):
  the board has no shells and no raw HTML blocks, and its HTML is byte for
  byte the same (296,950 bytes at 140 outputs, 2,697,083 at 1,400); its
  render and serialize times moved by the same few percent as the untouched
  render step, which is machine noise. A synthetic page with 200 rows, each
  with a browser-only `v-if`, an SVG icon and a trusted `Markup` note, grew
  from 729,594 to 775,338 bytes (host 45 KB to 84 KB), its 200 notes are now
  adopted rather than rebuilt, and serialization took about 4 ms more
  (17 ms to 21 ms). The docs landing page grew from 850 KB to 1.14 MB,
  because its 275 KB of copy is now in the host, and renders about 12 ms
  slower (three html5ever parses of that block).

The benchmark adapter (`benchmarks/web/apps/citry_vue/adapter.toml`)
declares no minimum hydration size, because every board size arrives as
server HTML. Warm in-process render and serialize times before and after
the change are in
`.benchmarks/research/vue-architecture-experiments/ssr-default-content/`.

## Alternatives considered

- **Full-page hydration first.** Nets 48.9 ms at 1,400 outputs against 63.2
  ms for the rows region, and needs every tag, document and whitespace
  mechanism before the first page hydrates. Rejected as the first target.
- **Rely on Vue's mismatch recovery.** Rejected: static attributes are not
  corrected, and mismatched subtrees are replaced, which is slower than client
  mount and wrong.
- **One Vue app per region.** Rejected: it breaks provide/inject between
  `ProjectTabs` and its panels, native slots, and the single Events
  coordinator.

## Contracts that change (Mechanisms 2 and 4)

- Native check: comment events and root-level whitespace in
  `hydration_structure.rs`, plus its PyO3 function
  (`citry_core_py/src/html_transform.rs`, registration in `lib.rs`),
  `_rust.pyi`, the `citry_core.html_transform` wrapper, the Python caller, and
  tests.
- Compiler artifact: anchor positions, attribute patch kinds, and text
  ancestry. Moves with it: `crates/citry_core_py/src/vue.rs`, the `vue` stub
  in `_rust.pyi`, the patched `third_party/rust/vize_atelier_core`, Python
  consumers, the compiled-definition cache (the artifact version stays 1
  under the pre-1.0 rule), and Rust tests.
- Client runtime: `client.js` and the `citry-client` bundle if the runtime
  changes; `runtime.js` is regenerated, never hand-edited.
- Docs and CHANGELOG for the per-page choice and any visible change.
- As built in steps 3 to 8: a new `server_render` module in
  `citry_vue_compiler` (which now depends on `citry_html_transform`); the
  PyO3 class `vue.ServerRenderProgram` and the functions
  `vue._read_server_render_program` and `vue._render_for_hydration`
  (`citry_core_py/src/vue.rs`, stub in `_rust.pyi`);
  `CompiledRender.server_render`; and `prepare_vue_serialization`'s
  `hydration_candidate` argument. The compiler artifact, the client runtime
  and the native check's Python tuple format did not change.
- Stored parser answers: a new `hydration_nesting` module in
  `citry_html_transform` (`tokens_nest_in_browser`, `NestingToken`), a
  `full_parse_check` field on `RenderRequest`, and the matching keyword-only
  `full_parse_check=False` argument of `vue._render_for_hydration`
  (`citry_core_py/src/vue.rs`, stub in `_rust.pyi`), used by the render
  parity check. Callers that pass four arguments are unchanged.
- Raw HTML blocks and shell contents (2026-09-27): the prepared record
  `{"html", "nodeCount"}` (Python `opaque_html_record` and
  `prepared_manifest`, the browser preflight and `citry-opaque-html` in
  `client.js`, the render parity stand-in); a new `static_html` module in
  `citry_html_transform` (`static_html_node_count`,
  `static_html_in_context`) and the PyO3 function
  `html_transform.static_html_node_count` (`citry_core_py`, `_rust.pyi`,
  the `citry_core.html_transform` wrapper); a fifth element, `shell
  content`, in each decline tuple of `vue._render_for_hydration` and the
  matching `HydrationDecline.shell_content`; the bootstrap key
  `emptyShells`; and mounted documents linking their initial stylesheets
  in `<head>`, which `loadStyle` adopts. Protocol versions stay 1 under the
  pre-1.0 rule. The compiled render functions and the helper contract do
  not change: the render passes the record, and only the component that
  receives it changed.
- Not affected: the template grammar, the AST, and the five `LangImpl`
  implementations.

## Verification

- Chromium hydration with the hydration report turned on
  (`globalThis.__citryHydrationDiagnostics = true`): zero mismatches, zero
  replaced elements, zero Vue hydration warnings.
- Client-mount versus hydrated parity on element state, then interaction:
  disclosure, row details, phase toggle, tab switch, and a server Render via
  `@c-submit`.
- Inputs: empty loop, one item, many items, empty slot, empty `v-if`, a
  component rendering nothing, entities, void elements, table and form
  contexts, truthy and falsy initial values, a spread with varying names.

## What would falsify this plan

- The production path's extra server cost for the rows region exceeds about
  45 ms at 1,400 outputs on the release build (step 0 modelled about 32 ms;
  at 1.4 times that, the net gain falls below 50 ms).
- The hydrated board does not improve request-to-layout by at least 50 ms at
  1,400 outputs in the cohort runner.
- In the cohort runner, the 140-output board with default settings (it
  hydrates) reaches layout more than 20 ms later than the same board with
  `ssr=False`. Content in the HTML is worth a few milliseconds; a larger
  loss needs a new decision.

## Behavior on unsupported input

- Page-wide preconditions fail (custom `on_serialize` hook, CSP policy,
  another asset position): the Vue host carries Citry's ordinary server
  HTML and Vue's client mount replaces it, unless the body holds a
  `<script>` element, which keeps an empty host. `ssr=False` or a page at or
  below a raised `ssr_element_threshold`: client mount from an empty host.
- An unsupported construct: the nearest element with a proven opening tag
  becomes a marked shell whose contents Vue builds in the browser; with no
  such element, the page client-mounts over Citry's server HTML. The
  reason code is recorded.
- The native check fails after writing: client mount over Citry's server
  HTML from the same render; callbacks do not run again.
- Teleport, Suspense, Transition and `v-html` inside a hydrated region
  decline.
- Text with a lone surrogate already makes serialization raise, with or
  without hydration, before any HTML is written. Text with a carriage
  return or NUL, and textarea or pre text starting with a newline, are
  written as shells.
- A mismatch in production caused by a checking bug is not detected at
  runtime; only tests with the hydration report turned on catch it.
