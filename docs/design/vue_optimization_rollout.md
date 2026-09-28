# Supported Vue performance features and the experiments they replaced

The project board benchmark (`benchmarks/web/apps/citry_vue`) now reaches
the research report's request-to-layout targets using only supported code. Every
optimization it relies on is general: any component can use it, and none
of it checks for one benchmark class, template hash or page shape. The
[experiment log](performance_architecture_experiments.md) keeps the
measurements that led here.

## What the board uses and what each part replaced

Each row below is on by default or enabled by one public setting. The last
column names the research prototype whose job it took over; the prototypes'
results stay in the experiment log as results.

| Supported feature | What it does | Replaced experiment |
|---|---|---|
| `simple = "vue"` | A component renders without a Python `Component` instance, context or render frame, while each occurrence keeps its own Vue instance, state and assets. The board's `ProjectOutput` rows use it. Unsupported declarations are rejected before any callback runs. | Python row-instance erasure, which admitted only the exact benchmark `ProjectOutput` class. |
| Generated JSON evaluator | For a template whose expressions all fit the small set the generator supports, Citry generates a Python function that records the row's values. Before it runs, a check walks the exact paths the template reads (its read set) and falls back to the ordinary evaluator when any value is not plain JSON. Runs automatically. | The opt-in evaluator experiments, switched on per class. |
| Row HTML writer and per-row caches | Citry generates one function per compiled template that writes a `simple = "vue"` row's HTML from its recorded values, and reuses per-template work across rows. See the two sections below. | Writing each row's HTML during evaluation, and the research step that inserted the prototype's row HTML into the finished document. |
| Hydration from Rust server render programs | By default the server runs each compiled Vue render function in Rust over the same data the browser receives and writes the host HTML, for every page that writes more than `ssr_element_threshold` Vue-managed elements (0 by default). Vue then adopts that HTML instead of rebuilding it. [`vue_board_hydration_plan.md`](vue_board_hydration_plan.md) describes the mechanism. | The four-region partial SSR prototype, its count-only initial adoption, and the hydration probe that admitted only the benchmark page's root tags and cleaned up finished HTML. |
| Ordinary Vue hydration in the browser | The browser runtime calls Vue's `createSSRApp`, so every row keeps normal Vue bindings, events and state. | Whole-article static HTML with hand-written direct bindings for the benchmark row. |

Error modes:

- A component that declares `simple = "vue"` with an instance-dependent
  hook, slots, or another unsupported shape raises when rendered, before
  any data callback runs. Engine state that needs the ordinary path (an
  extension hook, configured i18n) renders the component ordinarily instead.
- A value the generated evaluator cannot accept (not plain JSON) sends that
  row through the ordinary evaluator, before any side effect.
- A row the writer cannot format uses the per-row path, which raises the
  same error the ordinary path raises.
- A page serialized with `ssr=False`, at or below a raised
  `ssr_element_threshold`, or as a fragment mounts in the browser from an
  empty host. A page with a `deps_position` other than `"smart"`, a custom
  extension or component hook, a CSP, JavaScript or script-integrity
  policy, or HTML the browser's parser would rearrange mounts in the
  browser over Citry's ordinary server HTML, which Vue replaces, so its
  content is still served; a body holding a `<script>` element keeps an
  empty host instead. A compile error stops serialization. Callbacks
  never run twice. `HydrationAdmission` records the reason code and whether
  server HTML was sent. A construct the render programs do not support
  turns its nearest enclosing element into a shell that Vue fills in the
  browser (it shows HTML the server writes for it until then); with no such element, the whole page mounts in the
  browser over server HTML. A negative or non-integer threshold is rejected
  when the `Citry` settings are built.

Tests can ask the browser runtime for a hydration report: set
`globalThis.__citryHydrationDiagnostics = true` before the page's scripts
run (for example with Playwright's `add_init_script`). A page that
hydrates then publishes `globalThis.__citryHydrationReport` with element
counts, reused and replaced elements, every console warning and error logged
during the mount, the mismatch count, the mount time and any mount error. A page that mounts in the browser publishes no
report. The report captures `console.warn` and `console.error` during the
mount, so it is off unless a test turns it on.

## Current performance checkpoint

Public board, release native build, default settings (arm H) against the
same app with `Citry(ssr=False)` (arm C). Medians of 5 runs per cell, one
fresh Chromium per cell, first and second page load, 2026-09-25
(`.benchmarks/research/vue-architecture-experiments/hydrated-board-2/`).
The 1,400-output page hydrates; the 140-output page stayed below the
threshold at that time (20,000 elements) and mounted in the browser in
both arms. Since 2026-09-27 the default threshold is 0 and both sizes
hydrate; a clean browser run of the new default has not been recorded yet.

| Outputs | Load | Arm | Server prepare | Browser after response | Ready to layout | Request to layout | Report target |
|---:|---:|---|---:|---:|---:|---:|---:|
| 140 | 1 | H | 63.5 | 34.5 | 11.8 | 113.3 | 162.0 |
| 140 | 2 | H | 16.0 | 33.9 | 11.7 | 63.7 | 79.1 |
| 1,400 | 1 | H | 170.4 | 160.7 | 15.8 | 360.0 | 368.2 |
| 1,400 | 1 | C | 154.9 | 195.5 | 74.8 | 430.4 | 368.2 |
| 1,400 | 2 | H | 122.2 | 161.3 | 15.8 | 310.5 | 342.9 |
| 1,400 | 2 | C | 109.2 | 194.2 | 74.6 | 382.3 | 342.9 |

All times are ms. The targets are the research report's Citry
request-to-layout medians. At 1,400 outputs hydration costs about 13 to 16
ms more on the server and saves about 34 ms of browser work and 59 ms of
layout after ready. The hydrated document is about 2.7 MB against 1.3 MB
uncompressed. These are small single-machine samples on loopback, not a
general claim for other pages.

### Every component body renders as ordinary Vue output

Citry sends each component body to the browser as a compiled Vue template
plus the values Python computed. Only HTML that Python hands over as a finished
string (`<c-raw>` contents and trusted `Markup` values that contain tags) travels as one fixed
block, and Vue mounts that block as a static node.

An earlier prototype also sent a component body made only of simple
presentation tags and plain Python text (for example
`<section><h4>…</h4><span>{{ label }}</span></section>`) as one such block
of HTML, so Vue would skip building its inner nodes. It was measured
against ordinary Vue output on a page of 140 or 1,400 small independent row
components, at four block sizes, and then removed:

| Rows | Average block size | Ordinary Vue output | One HTML block per row |
|---:|---:|---:|---:|
| 140 | 95 characters | 11.1 ms | 19.0 ms |
| 1,400 | 97 characters | 111.6 ms | 203.5 ms |
| 1,400 | 479 characters | 134.0 ms | 304.9 ms |
| 1,400 | 1,912 characters | 193.8 ms | 655.4 ms |
| 1,400 | 7,754 characters | 420.6 ms | 2,065.3 ms |

The times are warm in-process render and serialization medians with
`ssr=False`, 12 samples per cell on one machine. The HTML-block version was
slower at every block size: Python parsed each row's HTML to prove it was
safe to send as one block, and every record repeated the root element's
metadata. In the browser it also lost at every size (request to layout
317.6 ms for the HTML blocks against 196.4 ms for ordinary output, at 1,400
rows of the smallest block).

It also changed what readers saw and what the server could do:

- Vue condenses the whitespace in a compiled template's text, but a block of
  HTML keeps the authored bytes, so an indented template showed different
  text spacing in the two versions.
- The server counted each block as one element when deciding whether a page
  is large enough to hydrate. At 1,400 rows with the two largest block sizes,
  ordinary output wrote 60,202 and 235,202 elements and hydrated, while the
  block version counted 1,402 and stayed below the 20,000-element threshold.

The public board sent no such blocks, so removing the prototype left its
served HTML at 140 and 1,400 outputs unchanged, with hydration on and
off: the pages match byte for byte once per-request ids and signed tokens
are normalized. The measurement scripts and raw results are in
[`vue-free-grouping-2`](../../.benchmarks/research/vue-architecture-experiments/vue-free-grouping-2/).

### Serializing `simple="vue"` rows

Evaluating a `simple="vue"` row only records its values: each text, each
opening's attributes, the chosen `c-if` branch and one record per `c-for`
item. Serialize writes a row's HTML whenever it builds the frame that holds
the row: static pages (`deps_strategy="simple"`), fragments, and
client-mounted pages that are not a full HTML document. Only static output
keeps that HTML; the others drop it, as they did when evaluation wrote it.
A client-mounted full document skips the frames that hold the rows, and a
hydrated page gets its HTML from the Rust server render programs, so
neither writes row HTML. A `simple="vue"` component rendered directly as
the root is the exception: serialize builds the root frame, so it writes
that one row's HTML once per serialization.

When every root tag of the template is fixed at compile time (no root inside
`c-if` or `c-for`) and the compiler can prove where the component's marker
attributes go, Citry generates a row HTML writer once per compiled template.
The writer is a Python function that reads a row's recorded values and
writes the same HTML the per-row path would, cut at the marker positions.
Serialize joins the pieces with the markers, so it does not rebuild the
row through the general path or rescan it. The writer runs no template
expression, so calling it late, or not at all, cannot change what the
template evaluated. The per-row path, where serialize rebuilds the row
from its recorded values and scans it for marker positions, handles every
other case:

- a template whose roots or marker positions are not fixed;
- a template that calls child components: serialize gives each row a
  frame of its own and writes every child through the child's frame, as
  it does under an ordinary parent;
- replaced escaping or formatting helpers, checked each time a row is
  written;
- a value the writer cannot format, such as an int too large to convert
  to text. The per-row path then raises the same error the ordinary path
  raises.

The output is byte-identical to the ordinary path and to the per-row path.

Medians of 15 warm in-process samples of the real board (render +
serialize, ms), one process per cell, two interleaved processes per cell
averaged, while another agent's jobs shared the CPU. The 1,400-row
fragment cell is three pairs of 21 samples, because its first run was
noisy:

| Rows | Output | Before | After |
|---:|---|---:|---:|
| 140 | Document, default settings (client mount) | 7.6 + 8.7 | 6.5 + 8.8 |
| 140 | Document, `ssr=False` | 7.6 + 7.6 | 6.4 + 7.6 |
| 140 | Static (`deps_strategy="simple"`) | 7.6 + 1.7 | 6.5 + 2.3 |
| 140 | Fragment (`deps_strategy="fragment"`) | 7.5 + 9.5 | 6.4 + 10.3 |
| 1,400 | Document, default settings (hydrates) | 63.0 + 61.0 | 52.4 + 60.6 |
| 1,400 | Document, `ssr=False` | 64.3 + 47.0 | 53.0 + 46.9 |
| 1,400 | Static (`deps_strategy="simple"`) | 63.3 + 10.9 | 53.1 + 17.7 |
| 1,400 | Fragment (`deps_strategy="fragment"`) | 55.1 + 55.9 | 44.3 + 61.9 |

"Before" wrote the row HTML during evaluation for every output. Documents
now save about 11 ms at 1,400 rows. At 1,400 rows, static and fragment
output move the work from render to serialize and come out 3 to 5 ms
faster (about 0.5 ms at 140): the writer takes about 6.3 ms for 1,400 rows,
and it writes each run of fixed markup with one append.

### Reusing per-row work in `simple="vue"` rows

Rows repeated work that depends only on their template or on attribute
names. Four places now do it once and reuse it; the HTML, manifest and
prepared data stay byte-identical. The first applies to every component whose
template Citry turns into generated Python, ordinary or `simple="vue"`; the
other three apply only to `simple="vue"` rows:

- Serialize records where each template's authored text sits (the text
  written in the template itself) once per serialization, not once per row.
- Serialize copies the data the generated evaluator wrote without checking
  and converting every value again. Data from any other path is still
  checked and converted.
- The root `c-bind` works out attribute names, order, source positions and
  static attributes once per compiled template and set of keys, for up to 32
  different key sets; each row only places its values. Rows with a key set
  beyond those 32, a value that is not a plain scalar, or names that need
  special merging (duplicates, `class`, `style`, reserved or invalid names)
  use the full per-row merge, which also raises its usual errors.
- The check that admits a row before the evaluator runs is written out as
  plain code once per compiled template. It still reads the live
  `ComponentLike` state on every row.

Medians of 11 warm in-process samples of the real board (render + serialize,
ms), one process per cell:

| Rows | Ordinary before | Ordinary after | `simple="vue"` before | `simple="vue"` after |
|---|---:|---:|---:|---:|
| 140 | 12.3 + 11.0 | 11.9 + 7.6 | 9.3 + 11.1 | 6.6 + 7.2 |
| 1,400 | 104.3 + 103.4 | 107.5 + 60.6 | 79.9 + 100.8 | 51.3 + 50.2 |

Ordinary components gain only from the first change; the other three apply
to `simple="vue"` rows.

## Prior art

- [Experiment log](performance_architecture_experiments.md) records the
  accepted paths, rejected attempts, measurements and remaining limits.
- `component_render.py::_render_simple_vue_leaf` renders a `simple = "vue"`
  call into a `SimpleVueRecord` (`citry_render.py`) without a Python
  component.
- `_vue/leaf_program.py::LeafProgramNode` holds the generated JSON evaluator
  (`_SimpleJsonCodegen`) and the row HTML writer (`_RowHtmlWriterCodegen`).
- `_vue/serialization.py::prepare_vue_serialization` decides whether a page
  hydrates and writes the host HTML with `vue._render_for_hydration`;
  `_vue/client.js` adopts it with `createSSRApp`.

## Approved boundaries

| Feature | Decision or restriction | Activation |
|---|---|---|
| Generated evaluator for plain JSON | Keep Python semantics, escaping, sandbox rules, errors and evaluation order; unsupported inputs use the ordinary evaluator before side effects | Automatic when the read-set check passes |
| No Python component instance | Reject instance-dependent capabilities rather than silently skip them; keep `simple = True` semantics separate | Explicit `simple = "vue"` |
| Partial SSR and hydration | Browser-only values stay unavailable to Python; unsupported constructs become shells, or client mount over Citry's server HTML, without running callbacks twice | On by default. Global `Citry(ssr=...)` with a per-serialization `serialize(ssr=...)` override; a raised `ssr_element_threshold` sends small pages without content |
| Reusing initial server HTML | Vue adopts the host HTML; later Render actions stay independently complete | Automatic inside a hydrating page |
| HTML regions with direct browser bindings | Not supported. Unsupported bindings use ordinary VNodes; any deliberate loss of Vue behavior would need a separately agreed opt-in | None |

The per-serialization SSR override takes precedence over the global setting;
omitting it inherits the global default. Disabling Vue SSR does not suppress
ordinary static HTML output.

## Whitespace after the rollout

The recorded 4.957 ms was one instrumented 1,400-output shell scan, not a
measured saving. It processed about 363 KB. Repeated row literals already use
compile-time cleanup; their one-time preparation took about 0.145 ms in that
run. The shell also has separate attribute cleanup and placeholder assembly.

The current cleanup drops whitespace-only text broadly. It is not a complete
Vue whitespace implementation. Define shared authored-text normalization,
verified against the pinned Vue/Vize compiler behavior, for both server output
and compiled browser definitions. A reusable shared plan is new work:

- Compute reusable literal keep/drop/condense decisions once per cached plan.
- Preserve Python-produced text, including whitespace-only strings and
  non-breaking spaces. Preserve ordinary static HTML serialization behavior.
- Account for sibling/comment context, selected branches, slots, nested `pre`,
  raw-text elements, entities and browser newline parsing.
- Treat unclassified raw HTML or output-changing hooks as requiring a safe
  fallback; do not normalize arbitrary rendered strings as template source.

This can remove the final whole-shell scan, but a new per-render walk could
erase the gain. Compare cold plan construction and warm full render/serialize,
not only the removed helper. Reprofile the final implementation first, then
measure the candidate at 140/1,400 outputs with DOM/text/hydration parity. Net
saving is the removed scan minus additional emission work; no 5 ms gain is
promised. Whitespace correctness belongs in SSR implementation; the final
performance experiment follows productionization.

## Deferred work and issue coverage

Verified open: [streaming #19](https://github.com/citry-dev/citry/issues/19),
[deferred performance umbrella #144](https://github.com/citry-dev/citry/issues/144),
and [script execution-order design #145](https://github.com/citry-dev/citry/issues/145).
The streaming issue includes the prototype, numbers and production requirements.

[Issue #37](https://github.com/citry-dev/citry/issues/37) is closed as obsolete.
Issue #144 owns incremental updates, Vue islands/activation, Teleport, native
rendering and other deferred experiments without dedicated issues, and links
work with separate owners. These are not prerequisites for the supported
optimizations above.
