# Whitespace parity between Python and Vue rendering

Status: proposal for review (issue
[#152](https://github.com/citry-dev/citry/issues/152)). Nothing here is
built yet. The recommendation targets 0.9.0, which the maintainer plans
as the last release with breaking changes before 1.0.

An independent reviewer checked the evidence and the recommendation in
this document, including a separate prose pass. Its corrections are
folded in; the largest one changed the recommended default from Vue's
rule to the authored whitespace.

## What this decides

Citry renders a component's template in two ways. On a page without Vue,
Python renders it and keeps every space and line break as written. On a
page Vue hydrates (Vue adopts the server's HTML instead of building it
again), the HTML comes from Vue's compiled render, and Vue's compiler
removes or shortens some whitespace first. Vue calls this condensing. The
same template can therefore show different text depending on how the
page was sent.

This document decides which whitespace rule Citry uses for 1.0, and where
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
  3.0. Even `preserve` drops whitespace-only first and last children,
  partly so a template with one root element stays one root. Vue SSR uses
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
there is for only one party to change the text.

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

### Option 3: keep authored whitespace on every path (recommended)

Python stays as it is. vize compiles in `Preserve` mode, so the hydrated
page keeps the same whitespace the static page shows. Only one party (the
template author) decides the text, and both paths render it.

- Static pages: unchanged, apart from the template-root rule in the
  recommendation.
- Hydrated pages: spaces appear where vize removed them, as plain HTML,
  Jinja2 and Django would show them. In the example, `onetwo` becomes
  `one two`. In the corpus, 36 places in templates with `js` could show a
  new space before CSS is applied. Inline-block items separated by line
  breaks gain the usual small gap between them.
- Cost: whitespace-only text nodes that Vue removed become nodes Vue
  creates and hydrates, and they add bytes to the render functions and
  the server HTML. Not measured.

### Option 4: a setting that only affects pages without Vue

Condense in Python behind a setting, leave vize alone, and document that
the setting does not affect hydrated pages. Rejected: it keeps the text
shift on declined pages, which is the bug.

## Recommendation for 0.9.0

Choose **Option 3**, with these parts:

1. **vize keeps authored whitespace.** Pass `WhitespaceStrategy::Preserve`
   from Citry through `vize_atelier_dom` to the parser, and make the
   condense pass in `vize_s1_to_s2` honour the same option. That is three
   patches that must agree: the option wiring in `vize_atelier_dom` (a
   crates.io crate, so either a new patched copy in `third_party/rust/` or
   an upstream change), the `vize_s1_to_s2` pass, and the call that runs
   it.
2. **Both paths drop whitespace at the edges of a component template's
   root.** Citry's compiler drops whitespace-only text nodes before the
   first and after the last top-level node of each component template, as
   whole nodes. A template with one root element then stays one root in
   Vue, which keeps attribute fallthrough and the root attributes Citry
   adds working. Because Citry drops whole nodes and never changes the
   text of a node it keeps, the render cache's replay check keeps working
   unchanged. Vue never sees the dropped nodes, since it compiles the
   nodes Citry produced.
3. **The first line break after `<pre>`, `<textarea>` and `<listing>`
   follows HTML.** The Vue template drops one line break written straight
   after the start tag, as upstream Vue and the HTML parser do. Do this in
   vize to match upstream, or in Citry's Vue template builder
   (`compiler.py:1431-1460`), but not in Citry's text nodes. The Rust
   server writer and the Python static writer then add one line break
   after the start tag when the element's content starts with a line
   break, which is how HTML serializers write these elements
   (`serialize.py:1384-1391` already does this for `<textarea>` values
   when the Vue runtime is not on the page). Server text and browser text
   then match, `{{ }}` values that start with a line break are covered,
   and the `<pre>` no longer needs `data-allow-mismatch`.
4. **`<textarea>` and `<title>` keep their content as written**, as
   upstream Vue does. `Preserve` mode gives this for free.
5. **No setting in 0.9.0.** Condensing can come later as an opt-in,
   because adding it does not break anyone. It needs Option 1's three
   problems solved first; this document records them.
6. **The authored text plan** is empty under `Preserve`. Remove its
   producer, its validation and its part in the content id, or keep it
   for a later condense opt-in. A maintainer decision below.
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
- **Most pages do not change.** 129 of the 154 measured templates have no
  `js`, and their static output stays exactly as it is.
- **It needs no new text rewrite in the template compiler**, which is a
  high-risk area, and it leaves the render cache's check alone.
- **It removes today's hidden difference** between the two ways Citry
  writes a component's Vue template, since neither drops anything.
- The cost is the unmeasured hydration work and bytes for the extra text
  nodes, and visible new spaces on some hydrated pages. "What would show
  this wrong" says how to check the first before building.

### What the change touches

- vize: the three patches in item 1, and the line break in item 3 if it
  is done there.
- `crates/citry_template_parser/src/compiler.rs`: the template-root drop.
  The generated code keeps its shape, so the five `src/lang/*.rs`
  implementations, the PyO3 glue and the `_rust.pyi` stub need no change
  unless the drop gets an option. A `citry_core` release must still ship
  before `citry` 0.9.0, because the compiled output changes.
- `crates/citry_vue_compiler/src/server_render.rs` and
  `packages/py/citry/citry/serialize.py`: the line break after `<pre>`,
  `<textarea>` and `<listing>`, and removal of the whitespace-only `<pre>`
  case that writes `data-allow-mismatch`.
- Tests that lock condensed hydrated text today and must change, for
  example `test_vue_events.py:977`,
  `e2e/test_vue_events_default_e2e.py:5117` and the `<pre>` and
  `<textarea>` cases in `test_vue_hydration_regions.py:703-723`. Rust
  tests in `crates/citry_template_parser/tests/tag_compiler.rs` that keep
  whitespace at a template's root edges.
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
- **A component template with whitespace around its single root.** That
  whitespace is dropped on both paths (item 2). A component used between
  two words with no spaces around it then touches them; this is already
  the hydrated behavior today.
- **A template that is not HTML** (Markdown, plain text). Unchanged.
- **An HTML minifier run on a hydrated page.** It removes text nodes Vue
  expects, and hydration then reports mismatches. This is true today and
  stays true; the docs should say to minify only pages without Vue.
- **vize cannot be told to keep whitespace** (item 1 proves harder than
  expected). Then the recommendation cannot ship as designed; see "What
  would show this wrong".

## Migration notes

For the 0.9.0 upgrade guide:

- **Pages that use Vue now keep the whitespace you wrote, like pages
  without Vue.** A line break between two inline elements, such as two
  links or a label and a value, now shows as a space on hydrated pages
  too. Inline-block items written on separate lines get a small gap. To
  keep elements touching, write them without whitespace between them, or
  lay them out with flex or grid.
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
  The thresholds are a starting proposal for the maintainer to set.
- **Visible damage on Vue pages.** Before 0.9.0, render the hydrated
  pages of the examples, the docs site and `citry_ui`'s components with
  and without condensing, and compare screenshots. If many components
  gain visible gaps that their authors would have to fix, the migration
  cost is higher than this document assumes.
- **vize's option cannot be wired** without a deep patch to a crate Citry
  does not control. Then the choice is between carrying that patch and
  Option 1.
- **Vue tooling assumptions.** If Vue devtools or a Vue library Citry
  supports depends on condensed whitespace, keeping it breaks that tool.
  No such case is known.

## Decisions for the maintainer

1. Keep authored whitespace on every path (Option 3): yes, or prefer
   Vue's rule and fund Option 1's three problems.
2. Drop whitespace around a component template's root on both paths
   (item 2): yes or no.
3. Where to drop the line break after `<pre>`: in vize (matches upstream
   Vue) or in Citry's Vue template builder.
4. Patch `vize_atelier_dom` in `third_party/rust/` or ask upstream for the
   option.
5. Remove the authored text plan, or keep it for a later condense opt-in.
6. The measurement thresholds in "What would show this wrong".
