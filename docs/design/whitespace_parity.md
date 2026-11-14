# Whitespace parity between Python and Vue rendering

Status: design with the maintainer's decisions recorded (issue
[#152](https://github.com/citry-dev/citry/issues/152)). Nothing here is
built yet. It targets 0.9.0, which the maintainer plans as the last
release with breaking changes before 1.0.0. "Decisions" at the end lists
each choice and the part of the design it shaped.

## What this decides

Citry renders a component's template in two ways. On a page without Vue,
Python renders it and keeps every space and line break as written. On a
page Vue hydrates (Vue adopts the server's HTML instead of building it
again), the HTML comes from Vue's compiled render, and Vue's compiler
removes or shortens some whitespace first. Vue calls this condensing. The
same template can therefore show different text depending on how the
page was sent.

This document decides which whitespace rule Citry uses for 1.0.0, and where
that rule is applied so that every way of sending a page shows the same
text.

## The problem in one example

```citry-html
<p>
  <a href="#">one</a>
  <a href="#">two</a>
</p>
```

| How the page is sent | HTML for the paragraph | Visible text |
|---|---|---|
| Vue hydrates the page (component has `js`) | `<p><a>one</a><a>two</a></p>` | `onetwo` |
| Vue mounts, but the server declined to hydrate (for example a custom `on_dependencies` hook) | Python's HTML until Vue mounts, then Vue's | `one two`, then `onetwo` |
| Static page (no component needs Vue) | `\n<p>\n  <a>one</a>\n  <a>two</a>\n</p>\n` | `one two` |

Vue drops a whitespace-only text node between two elements when it holds
a line break, so the links touch. Python keeps the line break, and the
browser shows it as one space. On the declined page the visitor sees the
text shift when Vue takes over.

## How whitespace flows today

Line numbers are on `main` at `c6bf31ead`.

### Python rendering keeps authored text

- The grammar keeps each text token byte for byte; Pest's automatic
  whitespace skipping is off for these rules
  (`crates/citry_template_parser/src/grammar.pest:47-49`, `:422-429`).
- The compiler turns each text token into a node that carries the text,
  the template it came from and its byte range
  (`crates/citry_template_parser/src/compiler.rs:268-274`, `:789-801`).
  The Python runtime writes the text unchanged
  (`packages/py/citry/citry/_vue/capture.py:908-925`,
  `packages/py/citry/citry/serialize.py:1331-1346`).
- The render cache relies on that byte range. When it replays a cached
  render, it rejects any text whose bytes differ from that range of the
  template (`packages/py/citry/citry/ext/cache/replay.py:993-998`). This
  check also stops a tampered cache store from adding markup, because the
  static writer appends authored text without escaping it.
- Citry already drops whole whitespace-only text nodes in a few places:
  between the branches of one `c-if` / `c-elif` / `c-else` group and
  between `</c-for>` and `<c-empty>` (`compiler.rs:341-377`,
  `:2134-2186`), in a component body that holds only whitespace
  (`compiler.rs:1051-1056`), and between `<c-fill>` tags
  (`capture.py:919-925`). These checks use Python `str.strip()` and Rust
  `trim()`, which also treat a no-break space as whitespace.
- No whole-page whitespace pass runs per render. `serialize.py`,
  `_vue/serialization.py` and `citry_html_transform` contain none.

### Vue rendering condenses

Citry compiles Vue templates with vize, a Rust port of Vue's compiler. Two
of its crates are patched copies in `third_party/rust/`; the rest come
from crates.io (`Cargo.toml:174-177`).

- vize condenses by default, and Citry never asks it not to
  (`crates/citry_vue_compiler/src/lib.rs:634-647`).
- vize has two implementations of the rule. Its parser (`vize_armature`)
  has a `WhitespaceStrategy` option whose `Preserve` value skips
  condensing entirely, at the template root and element edges included
  (`vize_armature-0.420.0/src/parser.rs:176-181`). The code that usually
  emits the render function runs a second copy in `vize_s1_to_s2`
  (`third_party/rust/vize_s1_to_s2/src/lower/text/condense.rs:230-315`),
  which has no option; it only stops inside `<pre>`. `vize_atelier_dom`
  fills the parser options with defaults
  (`vize_atelier_dom-0.420.0/src/compile/stage_options.rs:23-35`).
- The rules, matching upstream Vue's `condenseWhitespace` in
  `compiler-core/src/parser.ts`:
  1. Whitespace-only text that is the first or last child of an element
     or of the template is dropped.
  2. Whitespace-only text between two non-text neighbours is dropped when
     it holds a line break. Without a line break, it becomes one space.
  3. Whitespace next to text or `{{ }}` becomes one space.
  4. Inside text with words, each run of whitespace becomes one space.
  5. Nothing inside `<pre>` changes.
- Vue counts only space, tab, line feed, form feed and carriage return as
  whitespace (`condense.rs:21-26`).

The text Vue compiles is the text Python rendered. Citry builds each Vue
template from the same nodes it uses for static output
(`packages/py/citry/citry/_vue/compiler.py:1451-1455` appends each
template-authored text node as it is).

### Hydrated output already differs between two render paths

Citry writes a component's Vue template in one of two ways
(`packages/py/citry/citry/_vue/static_template.py:10-17`). When every node
of the body has a fixed Vue form, Citry compiles the body once into a
reusable Vue template, with each `<c-if>` branch inside a
`<template v-if>` and each `<c-for>` body inside a `<template v-for>`.
Otherwise it writes the branch it picked and every loop row inline among
their siblings.

The two forms condense differently. In the first, whitespace at a branch
edge is the first or last child of a `<template>`, so vize drops it:
`a<template v-if="x"> {{ y }} </template>b` renders `ayb`. In the second,
the same whitespace sits next to text and stays. So a hydrated page's
spacing today depends on which form Citry picked for a component, which
users cannot see or control.

### Two places where vize differs from upstream Vue

- **The first line break after `<pre>`.** The HTML parser drops a line
  break written straight after `<pre>`, `<textarea>` or `<listing>`, and
  upstream Vue drops it when it compiles. vize keeps it: `<pre>\n  a\n</pre>`
  compiles to the text `"\n  a\n"`. The browser drops that line break from
  the server HTML, so the server's text and Vue's text differ. Citry
  therefore writes the `<pre>` with `data-allow-mismatch="children"` and
  lets Vue rebuild its content in the browser
  (`crates/citry_vue_compiler/src/server_render.rs:3375-3381`,
  `:4361-4365`). Citry's own code assumes Vue drops the line break
  (`packages/py/citry/citry/_vue/direct_capture.py:1944-1948`).
- **`<textarea>` content.** Upstream Vue reads `<textarea>` and `<title>`
  as plain text without tags (HTML's RCDATA) and does not condense them
  (since Vue 3.0.8). vize condenses `<textarea>`: `"\n  t\n"` becomes
  `" t "`, so the field's initial value differs between a static page and
  a Vue page.

### Every render path

| Path | Whose whitespace rules | Where decided |
|---|---|---|
| Hydrated | Vue's: the server writes the text the compiled render emits | `server_render.rs:20-21`; `_vue/serialization.py:431-486` |
| Hydration declined (`custom-hooks`, `compile-error`, `security-policy` and others) | Python's until Vue mounts, then Vue's | `_hydration_page_reason` in `_vue/serialization.py:384-428`; `serialize.py:762-778` |
| Static page | Python's | `serialize.py:722-726` |
| `ssr=False`, below `ssr_element_threshold` | Empty mount element, Vue's only | `_vue/serialization.py:1024-1028`, `:461-464` |
| `{{ value }}`, `<c-raw>`, `Markup`, `v-pre` | Written unchanged on every path | text bindings in `capture.py`; `direct_capture.py:2955-2970`, `:1936-1960` |

When any component on a page needs Vue, the whole page becomes one Vue
app, so a parent without `js` is also compiled by Vue
(`packages/py/citry/tests/test_vue_events.py:857-890`). A slot fill is
written as `<template #name>` inside the caller's Vue template
(`static_template.py:602-636`), so its whitespace follows the caller's
template, and vize drops whitespace at the fill's edges.

### The authored text plan

The Rust Vue compiler also reports which authored text vize condenses or
drops, as the authored text plan
(`crates/citry_vue_compiler/src/lib.rs:821-953`). Python validates it and
stores it on `CompiledRender` (`compiler.py:809-940`, `:233`), and the
plan feeds the definition content id (`compiler.py:1359`). No code acts on
it.

## Measurement on real pages

A throwaway harness (deleted afterwards) applied Vue's condense rules to
every literal component template under `examples/` and `docs_site/`: 154
templates, 34 from the examples and 120 from the docs site, 166 KB. Its
Python model of the rules matched vize's authored text plan exactly on all
93 templates where the plan was complete. It then rendered six pages
before and after condensing and compared the visible text in headless
Chrome, with the page scripts removed so the browser showed the server
HTML.

| Measure | All | examples | docs_site |
|---|---|---|---|
| Templates with any change | 143 of 154 | 34 of 34 | 109 of 120 |
| Templates with `js` (Vue-condensed today when hydrated) | 25 | 5 | 20 |
| Whitespace-only first or last children dropped | 1,898 | 506 | 1,392 |
| Whitespace-only text dropped between siblings | 776 | 235 | 541 |
| ... between two elements whose tags are inline by default (may show as a missing space) | 188, of which 36 in templates with `js` | 69 | 119 |
| Template source bytes saved | 22.7% | 23.0% | 22.7% |

| Rendered page | Markup change | Visible text |
|---|---|---|
| Standalone starter app | 24 B smaller | identical |
| `project_board` example | 45 B smaller | identical |
| `htmx` example | 113 B smaller (2.0%) | identical |
| Docs `docs.md` | 12.2% smaller | identical |
| Docs `getting-started/add-slots.md` | 10.0% smaller | identical |
| Docs `concepts/slots.md` | 6.9% smaller | identical |

What the numbers show:

- **The 188 places where condensing could join two words did not show on
  any rendered page.** Their containers use flex or grid layout, where
  whitespace between items does not render. Without the component's CSS
  the change does show: in `examples/` `team_picker.py:25,35`, "Team "
  became "Team".
- **Text that is not HTML breaks under condensing.** The docs pipeline
  renders every Markdown page as a Citry template before the Markdown pass
  (`docs_site/_internal/pipeline.py:201-241`). Condensing removes the
  blank lines that separate paragraphs, which would break all 127 docs
  pages. Condensing one landing-page component
  (`docs_site/_internal/components/landing.py:1108-1178`) made the landing
  page fail with `ValueError: A Markup value ... is not a complete HTML
  fragment`, because a helper that reads its HTML line by line
  (`docs_site/_internal/util.py:23-58`) relies on the line breaks.
- **`<pre>` and `<textarea>` are rare in templates.** The corpus has five
  `<pre>` and two `<textarea>`, none with authored whitespace inside.
  Code blocks get their text through `{{ }}` values or slot fills, which
  is the case that crosses a component boundary (see Option 1).

Limits: the harness guessed display from tag names, so 188 is an upper
bound; it changed template source only, not `{{ }}` values; it did not
model text that crosses a component boundary; it did not cover
`packages/py/citry_ui`, the published component library; and it did not
measure the hydration cost of keeping whitespace-only text nodes.

## How other frameworks handle it

- **Vue 3** condenses by default and added `whitespace: 'preserve'` in
  3.1.0 after users reported broken spacing between inline buttons in
  3.0. Even `preserve` drops whitespace-only first and last children of
  every element and of the template, and turns other whitespace-only
  text into one space (`compiler-core/src/parser.ts` in 3.5.13). vize's
  `Preserve` keeps both as written, so it keeps more than Vue's own
  `preserve`. Vue SSR uses
  the same parser options as the client build, and hydration compares
  text nodes exactly (`runtime-core/src/hydration.ts:172-198` in 3.5.13),
  so the server and client builds must get the same option.
- **Angular** removes every whitespace-only text node by default and keeps
  `<pre>` and `<textarea>`. `ngPreserveWhitespaces` keeps one subtree.
- **Svelte 5** collapses whitespace between nodes to one space, trims it
  at tag edges and keeps `<pre>`. `preserveWhitespace` is a compiler
  option for the whole build.
- **React JSX and Astro** remove whitespace that touches a line break and
  need `{" "}` for an explicit space; JSX has no `<pre>` exception. Astro
  7 made this its default (`compressHTML: 'jsx'`), and users reported
  words running together.
- **Jinja2 and Django** never touch whitespace between HTML tags by
  default. Django's `{% spaceless %}` removes it where the author asks.

All of these apply one rule on the server and the client, because one
compiler produces both. Those that condense decide by tag name (`<pre>`,
`<textarea>`) and cannot see CSS `white-space: pre`.

## Options

Every option has to leave the hydrated, declined and static paths showing
the same text. Vue compiles the text Python rendered, so the simplest way
to get the same text everywhere is to let only one party change it.

### Option 1: condense in Citry's compiler, vize stops condensing

Citry's Rust template compiler condenses authored text with Vue's rules,
and vize keeps the text it receives. A setting and a per-component
attribute switch condensing off. This was the first draft of this
document. Three problems block it:

- **It breaks the render cache's replay check.** Condensed text no longer
  equals the bytes of its range in the template, so every cached render
  holding condensed text would fail to replay. Keeping the cache working
  needs a new meaning for the byte range and an equally strict check, and
  that check is also a security guard.
- **Text that ends up in a `<pre>` from another template gets
  condensed.** A caller that passes a multi-line slot fill to a component
  whose template is `<pre><c-slot /></pre>` has no `<pre>` around the
  fill in its own template, so Citry condenses the fill. Today's static
  output keeps it (`test_vue_events.py:857-912` checks the same case for a
  child component inside `<pre>`).
- **The rule is not fully defined on Citry's tree.** HTML comments are
  ordinary text tokens in Citry, while vize drops comments and joins the
  whitespace around them; `{# #}` splits one text run into two tokens; and
  a `<c-if>`, `<c-slot>` or component tag needs a defined role as a
  neighbour. Each choice changes real output.

Static pages would also lose spaces between inline elements and between
words at the edges of `c-for` and `c-fill` bodies, and text-only templates
(Markdown, plain-text email) would need an opt-out.

### Option 2: condense in Python, keep vize as it is

A setting makes Python apply Vue's rule, and vize keeps condensing. It has
Option 1's problems, plus a setting that can only be turned off on pages
that never hydrate, because vize would still condense the hydrated page.
Rejected.

### Option 3: keep authored whitespace on every path (chosen)

Python stays as it is. vize compiles in `Preserve` mode, so the hydrated
page keeps the same whitespace the static page shows. Only one party (the
template author) decides the text, and both paths render it.

- Static pages: unchanged, apart from the root rule in item 2 of the
  design.
- Pages that use Vue: spaces appear where vize removed them, as plain
  HTML, Jinja2 and Django would show them. In the example, `onetwo`
  becomes `one two`. Every template on such a page is compiled by Vue,
  including templates without `js`, so all 188 places in the corpus
  could show a new space before CSS is applied. Inline-block items
  separated by line breaks gain the usual small gap between them.
- Cost: whitespace-only text nodes that Vue removed become nodes Vue
  creates and hydrates, and they add bytes to the render functions and
  the server HTML. Not measured.
- Cost: whitespace at the root of a Vue template turns a one-root
  template into several roots, and whitespace directly in the page's
  mount element makes the server give up hydrating the page. Item 2 of
  the design handles both. Its edge cases are built and tested first,
  against the checks in "What would show this wrong".

### Option 4: a setting that only affects pages without Vue

Condense in Python behind a setting, leave vize alone, and document that
the setting does not affect hydrated pages. Rejected: it keeps the text
shift on declined pages, which is the bug.

## Design for 0.9.0

The maintainer chose **Option 3**, with these parts:

1. **vize keeps authored whitespace.** Every place that runs vize must get
   `WhitespaceStrategy::Preserve`:
   - the option wiring in `vize_atelier_dom`, in a new patched copy of
     that crate under `third_party/rust/vize_atelier_dom/` (see "The
     patched copy of `vize_atelier_dom`" below);
   - the condense pass in `vize_s1_to_s2`, and the `try_emit_s2` call in
     `vize_atelier_dom` that runs it;
   - Citry's own calls in `crates/citry_vue_compiler/src/lib.rs`:
     `parse_generated_template` (`:309-325`, used by the element walk and
     the hydration plan, which today skip text and so may line up by
     accident), the `v-pre` check `s2_lane_compiles_v_pre` (`:799-823`)
     and the direct `vize_s1_to_s2::lower` call behind the authored text
     plan (`:829-830`; `lower` takes no options today, so it needs the
     same patch as the condense pass).

   **The patched copy of `vize_atelier_dom`.** Citry adds the copy for
   0.9.0 because asking upstream and waiting for a release would hold up
   0.9.0. It follows the repository's convention for patched crates (see
   `third_party/README.md` and "Patched Vize compiler crates" there):
   - The source is the crates.io archive `vize_atelier_dom-0.420.0.crate`.
     The copy keeps the archive's normalized `Cargo.toml` and the
     registry's original manifest as `Cargo.upstream.toml`, and adds the
     upstream `LICENSE` text from the upstream commit. Its
     `README.citry.md` records the archive's SHA-256, the upstream commit
     and the exact patch.
   - The two existing patched crates share one version suffix (`+citry.7`
     today), and it moves when either changes. The new copy joins them,
     so 0.9.0 raises the suffix on all three. The places that carry it
     are `crates/citry_vue_compiler/src/lib.rs:764`,
     `packages/py/citry/citry/_vue/compiler.py:392`,
     `packages/py/citry/tests/test_vue_prepared.py:348`,
     `scripts/verify_citry_core_distribution.py` (`PATCHED_CRATES`),
     `Cargo.lock`, `third_party/README.md`, and the `Cargo.toml` and
     `README.citry.md` of each patched crate.
     `docs/design/vue_migration.md` asks that request caches do not
     survive an incompatible compiler replacement, so a test checks that
     the new identity keeps old compile caches from being reused.
   - In the root `Cargo.toml`, the `vize_atelier_dom = "=0.420.0"` entry
     under `[workspace.dependencies]` (`:175`) becomes a `path` entry like
     the other two, and `[patch.crates-io]` gets a line (`:215-217` hold
     the other two). `crates/citry_vue_compiler/Cargo.toml:31` asks for
     the `davinci-differential` test feature, so the copy keeps it.
   - The build and distribution checks list the patched crates: the build
     cache inputs in `packages/py/citry_core/pyproject.toml` (`:81-84`
     for the other two) and the checks in
     `packages/py/citry_core/tests/test_distribution_artifacts.py`
     (`:182-194`, `:233-236`). `.gitattributes:60` has a line for the
     snapshot files of `vize_atelier_core` only; the new copy gets one if
     it has snapshot files. The `third_party/README.md` entry and the
     "two" in its text change to match.
   - Later, and not as part of 0.9.0, Citry offers the option to upstream
     vize (a way to pass the whitespace strategy through
     `vize_atelier_dom`), so the patched copy can be dropped once a
     released vize has it and Citry's regression tests pass.
     `third_party/README.md` states the same rule for the other two
     copies.
2. **Drop whitespace at the root of each Vue template, on both paths.**
   A Vue template with one root element must stay one root: otherwise
   `root_shape` becomes `"fragment"`
   (`crates/citry_vue_compiler/src/hydration.rs:510-535`), `v-show` on
   the component fails a server check (`_vue/events.py:1477-1503`), the
   client refuses the render (`client.js:2518-2527`) and attributes
   passed to the component no longer reach its root element. A pass over
   the `<c-*>` template cannot decide this, because the root Vue sees
   depends on what was rendered: a `<c-if>` or `<c-for>` at the root, a
   transparent or built-in component written in place
   (`direct_capture.py:157-164`), and HTML comments, which vize drops.
   So the rule is defined on the rendered nodes of each component
   occurrence that becomes a Vue component: drop whitespace-only text
   nodes before its first and after its last element, looking through
   control flow, components written in place and comments. Every place
   that writes a component's Vue template calls one shared function for
   this, and so does the Python static writer, so all of them drop the
   same nodes. The writers are `definition_compile_input`
   (`compiler.py:1431-1571`), `_DefinitionFragment` in
   `direct_capture.py`, the leaf program compiler (`leaf_program.py`,
   which writes the reusable Vue template) and `static_vue_template`
   (`static_template.py`, which `citry check` uses). A change to what
   the leaf program writes also changes `LEAF_TEMPLATE_CONTRACT_DESCRIPTOR`
   (`leaf_program.py:134`), which stamps cached renders and has a
   locking test, so entries cached before the change miss and render
   again.
   Transparent and `simple` components copied into their caller's
   template are not roots and keep their whitespace, so
   `Hello<c-t/>!` with a template of `"\n  {{ name }}\n"` still shows
   `Hello Bob !`.
   - The same function covers the page's mount element, on a page that
     becomes a Vue app: one that hydrates, declines to hydrate, or mounts
     without server HTML. The Rust server writer gives up hydrating a
     page when any text sits directly in the mount element
     (`server_render.rs:3204-3209`, reason `host-root`), so a page
     template such as `<c-nav/>\n<main>...</main>` would stop hydrating.
     The shared function drops every whitespace-only text node that
     would sit directly in the mount element, before, between and after
     the page's top-level nodes, whichever template wrote it: the page
     template, a component with several roots, or a slot fill that lands
     at the top level. None of that whitespace reaches the server writer.
     The `host-root` rule stays as it is and still stops hydration for
     text that is not whitespace. A page with no Vue has no mount
     element and keeps its whitespace between top-level nodes.
   - Citry drops whole nodes and never changes the text of a node it
     keeps, so the render cache's replay check keeps working. Spans are
     recorded only for nodes that are written (`capture.py:908-910`).
3. **The first line break after `<pre>`, `<textarea>` and `<listing>`
   follows HTML.** The HTML parser drops a line break written straight
   after these start tags. Upstream Vue does the same for `<pre>` and
   `<textarea>` when it compiles; doing it for `<listing>` follows HTML,
   not Vue.
   - Every place that writes a component's Vue template (the writers
     listed in item 2) drops one authored line break straight after the
     start tag, before vize sees the text, through one shared rule. It is
     not done in vize, which keeps that line break (see "Two places where
     vize differs from upstream Vue"), and not in Citry's text nodes,
     which keep the authored bytes.
   - The Rust server writer adds one line break after the start tag when
     Vue's text for the element starts with a line break, as HTML
     serializers do.
   - The Python static writer adds one only when the first content after
     the start tag is not the element's own authored text: a `{{ }}`
     value, a slot fill or a child component's output that starts with a
     line break. Authored text is written as is, and the browser drops
     the line break itself. `serialize.py:1370-1391` already makes this
     split for `<textarea>` values when the Vue runtime is not on the
     page.
   - "First content" is decided on the rendered order of nodes, so a
     `<c-if>` or `<c-for>` at the start of a `<pre>` gives the same
     result in both ways Citry writes a component's Vue template.
   - Server text and browser text then match, and the `<pre>` no longer
     needs `data-allow-mismatch`.
4. **`<textarea>` and `<title>` keep their content as written**, as
   upstream Vue does. `Preserve` mode gives this for free.
5. **No setting in 0.9.0.** Condensing can come later as an opt-in,
   because adding it does not break anyone. It needs Option 1's three
   problems solved first; this document records them.
6. **The authored text plan stays.** Under `Preserve` it holds only the
   comment and branch-gap drops, which do not depend on the whitespace
   rule. Citry keeps its producer, its validation and its part in the
   content id as they are, so the later condense opt-in of item 5 can
   use it.
7. **A separate small fix:** treat a no-break space as text, not
   whitespace, in every place Citry drops whitespace-only text. The sites
   are the parser's `validate_tag_grouping`
   (`crates/citry_template_parser/src/parser.rs:6162`), `compiler.rs:342`,
   `:1051-1056` and `:2134-2186`, `capture.py:920`,
   `static_template.py:771` and `nodes/__init__.py:415-421`. All of them
   must change together, or a no-break space between branches passes the
   parser and then splits the group.

Why authored whitespace rather than Vue's rule:

- **The failures are not equal.** Condensing fails quietly: words join,
  Markdown and plain text break, and code passed into a `<pre>` from
  another template collapses. Keeping whitespace fails with an extra
  space, the one plain HTML would show.
- **Static pages do not change,** apart from the root rule. 129 of the
  154 measured templates have no `js`; on a page where no component needs
  Vue, their output stays as it is.
- **It changes no text in the template compiler**, which is a high-risk
  area, and it leaves the render cache's check alone. Item 2 only drops
  whole nodes, at render time.
- **It removes today's hidden difference** between the two ways Citry
  writes a component's Vue template, since neither drops anything.
- The cost is the unmeasured hydration work and bytes for the extra text
  nodes, and visible new spaces on some hydrated pages. "What would show
  this wrong" says how to check the first before building.

### What the change touches

- vize and the Citry call sites in item 1, including the new patched
  copy and the files that list the patched crates. A `citry_core`
  release must ship before `citry` 0.9.0.
- The shared root function in item 2, called from each writer of a
  component's Vue template and from the Python static writer. The
  `host-root` rule in
  `server_render.rs` stays as it is. The `<c-*>` template compiler, the
  five `src/lang/*.rs` implementations, the PyO3 glue and the
  `_rust.pyi` stub need no change.
- Each writer of a component's Vue template, for the line break in
  item 3.
- `crates/citry_vue_compiler/src/server_render.rs` and
  `packages/py/citry/citry/serialize.py`: the line break after `<pre>`,
  `<textarea>` and `<listing>`, and removal of the whitespace-only `<pre>`
  case that writes `data-allow-mismatch`.
- Tests that lock condensed hydrated text today and must change, for
  example `test_vue_events.py:977`,
  `e2e/test_vue_events_default_e2e.py:5117` and the `<pre>` and
  `<textarea>` cases in `test_vue_hydration_regions.py:703-723`, and
  exact-HTML static tests whose component templates have whitespace
  around a single root.
- Tests for item 2's edge cases: a root `<c-if>`, `<c-for>`, transparent
  and built-in components, a root HTML comment or `{# #}` comment,
  `v-show` on such a component, and a page template with whitespace
  between its top-level components that must still hydrate.
- The parity test the issue asks for: for inline elements separated by
  line breaks, `<pre>` (authored, from a slot fill, and from a `{{ }}`
  value starting with a line break), `<textarea>`, slot fills, `c-if` and
  `c-for` edges, and `<c-raw>`, the static output, the declined server
  HTML and Vue's browser render produce the same text nodes. Run each case
  through both ways Citry writes a component's Vue template.

### Security

The change alters how authored text and `<pre>` / `<textarea>` content
reach the page (Mechanism 7 in `CLAUDE.md`, "Text and markup").

- No new input. All text involved is written by the template author, or
  is a `{{ }}` value Citry already escapes.
- HTML that Citry writes must mean the same once parsed. The added line
  break after `<pre>`, `<textarea>` and `<listing>` exists so the parsed
  text equals the intended text; the parity test checks it in a browser.
- The render cache's replay check stays as strict as today, because Citry
  keeps every remaining text node byte for byte.

## Error modes

- **CSS `white-space: pre` or `pre-wrap` on an element that is not
  `<pre>`.** Works on every path, since nothing condenses the text.
- **Whitespace inside `<c-raw>`, `Markup` or a `{{ }}` value.** Kept as
  written on every path, as today.
- **Text that crosses a component boundary or a slot fill.** Kept as
  written on every path, including into a `<pre>`.
- **A component with whitespace around its single root element.** That
  whitespace is dropped on both paths (item 2). A component used between
  two words with no spaces around it then touches them, as it already
  does on hydrated pages today. Transparent and `simple` components keep
  it.
- **Whitespace between a Vue page's top-level components.** Dropped on
  both paths (item 2), so two inline components written next to each
  other touch. A page with no Vue keeps it.
- **A template that is not HTML** (Markdown, plain text). Unchanged, as
  long as it does not become a Vue component; item 2 applies only to
  Vue component roots and the mount element of a Vue page.
- **Cached renders from 0.8.0.** The render cache keys entries by the
  template source, so entries stored before the upgrade may fail the
  replay check once and be rendered again (reported as a corrupt entry).
  Entries stamped with the old leaf template descriptor miss and render
  again. This happens once per entry.
- **An HTML minifier run on a hydrated page.** It removes text nodes Vue
  expects, and hydration then reports mismatches. This is true today and
  stays true; the docs should say to minify only pages without Vue.
- **vize cannot be told to keep whitespace** (the patch in item 1
  proves harder than expected). Then the design cannot ship as written;
  see "What would show this wrong".

## Migration notes

For the 0.9.0 upgrade guide:

- **Pages that use Vue now keep the whitespace you wrote, like pages
  without Vue.** A line break between two inline elements, such as two
  links or a label and a value, now shows as a space on hydrated pages
  too. Inline-block items written on separate lines get a small gap. To
  keep elements touching, write them without whitespace between them, or
  lay them out with flex or grid.
- **Whitespace between the top-level components of a page that uses
  Vue is dropped.** If two inline components at the top of a page relied
  on a line break for spacing, wrap them in an element that holds the
  space.
- **`<textarea>` content keeps its whitespace on Vue pages.** If the
  template indents the content, remove that whitespace from the template.
- **Whitespace around a component's single root element is dropped on
  pages without Vue,** as it already is on Vue pages. If a component used
  between words relied on its own line breaks for spacing, put the spaces
  in the parent template.

## What would show this wrong

- **Hydration cost, measured before building.** On the 1,400-output
  benchmark page, compare Vue's render and hydration time and the HTML
  size with and without condensing. If keeping whitespace makes hydration
  more than 5% slower or the compressed HTML more than 3% larger, prefer
  Vue's rule and solve Option 1's three problems before 0.9.0 instead.
  The maintainer accepted these thresholds. Check first that the
  benchmark page still hydrates in both runs; a page that falls back to
  mounting without hydration would make the numbers meaningless.
- **The page root rule on text pages.** Under item 2, a Markdown or
  plain-text page template that also becomes a Vue app loses the blank
  lines between its top-level nodes, and the Python static writer must
  know, after the render, that the page needs Vue. Test a plain-text
  page that mounts Vue. If the writer cannot know, or such pages are
  common, the page-root part of item 2 needs another rule.
- **The root rule needs too many exceptions.** If a prototype of item 2
  finds Vue templates whose root it cannot reduce to one element without
  dropping text a user can see, keeping authored whitespace costs more
  than this document assumes.
- **Visible damage on Vue pages.** Before 0.9.0, render the hydrated
  pages of the examples, the docs site and `citry_ui`'s components with
  and without condensing, and compare screenshots. If many components
  gain visible gaps that their authors would have to fix, the migration
  cost is higher than this document assumes.
- **The patch to `vize_atelier_dom` needs more than passing the
  strategy through** (for example, because the code that emits the
  render function ignores it). Then the choice is between carrying the
  larger patch and Option 1.
- **Vue tooling assumptions.** If Vue devtools or a Vue library Citry
  supports depends on condensed whitespace, keeping it breaks that tool.
  No such case is known.

## Decisions

The maintainer decided these. The part of the design each one shaped is
in brackets.

1. Keep the author's whitespace on every path, which is Option 3.
   Condensing is not built for 0.9.0 (Options 1 and 2). [Option 3, items
   4 and 5]
2. Drop the whitespace around each Vue component's root, and in the
   page's mount element, with one shared function that runs on both
   paths. This also clears the `host-root` hydration failure, so the
   server writer's rule stays as it is. [Item 2]
3. Drop the line break after `<pre>` in Citry's own code that writes the
   Vue template, not in vize. [Item 3]
4. Add a patched copy of `vize_atelier_dom` under `third_party/rust/` for
   0.9.0, because asking upstream is too slow. The option should still be
   offered upstream later, so the patched copy can be dropped. [Item 1]
5. Keep the authored text plan for a possible condense opt-in later.
   [Item 6]
6. Accept the benchmark thresholds in "What would show this wrong": 5%
   slower hydration and 3% larger compressed HTML.
