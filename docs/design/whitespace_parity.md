# Whitespace parity between Python and Vue rendering

Status: proposal for review (issue
[#152](https://github.com/citry-dev/citry/issues/152)). Nothing here is
built yet. The recommendation targets 0.9.0, the last release before 1.0
that may change behavior without a deprecation period.

## What this decides

Citry renders a component's template in two ways. On a page without Vue,
Python renders it and keeps every space and line break as written. On a
page Vue hydrates, Vue's compiler builds the HTML and removes some of that
whitespace first. The same template can therefore show different text
depending on how the page was sent. This document decides which
whitespace rule Citry uses for 1.0, who applies it, and how a template
keeps its whitespace exactly when it needs to.

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

- The Pest grammar keeps text tokens byte for byte: `template` is
  compound-atomic and `text` is atomic
  (`crates/citry_template_parser/src/grammar.pest:47-49`, `:422-429`).
- The compiler turns each text token into a node that carries the same
  text (`crates/citry_template_parser/src/compiler.rs:268-274`,
  `:789-801`), and the Python runtime writes it unchanged
  (`packages/py/citry/citry/_vue/capture.py:908-925`,
  `packages/py/citry/citry/serialize.py:1331-1346`).
- Citry already drops three kinds of whitespace-only text today:
  between the branches of one `c-if` / `c-elif` / `c-else` group
  (`compiler.rs:2134-2186`), a component body that holds only whitespace
  (`compiler.rs:1051-1056`), and whitespace between `<c-fill>` tags
  (`packages/py/citry/citry/nodes/__init__.py:415-421`).
- No whole-page whitespace pass runs per render. `serialize.py`,
  `_vue/serialization.py` and `citry_html_transform` contain none.

### Vue rendering condenses

Citry compiles Vue templates with vize, a Rust port of Vue's compiler.
Two of its crates are patched copies in `third_party/rust/`; the rest come
from crates.io (`Cargo.toml:174-177`).

- vize runs in Vue's default `condense` mode. Citry never asks for
  `preserve` (`crates/citry_vue_compiler/src/lib.rs:634-647`), and
  `vize_atelier_dom`'s options have no whitespace field.
- The rules (`third_party/rust/vize_s1_to_s2/src/lower/text/condense.rs:230-315`,
  matching upstream Vue `compiler-core/src/parser.ts` `condenseWhitespace`):
  1. Whitespace-only text that is the first or last child of an element
     is dropped.
  2. Whitespace-only text between two elements is dropped when it holds a
     line break. Without a line break, it becomes one space.
  3. Whitespace next to text or `{{ }}` becomes one space.
  4. Inside text with words, each run of whitespace becomes one space.
  5. Nothing inside `<pre>` changes.
- Vue counts only space, tab, line feed, form feed and carriage return as
  whitespace (`condense.rs:21-26`). Citry's three existing drops use
  Python `str.strip()` and Rust `trim()`, which also treat a no-break
  space as whitespace.

The text Vue compiles is the text Python rendered. Citry builds each Vue
template from the same prepared nodes it uses for static output
(`packages/py/citry/citry/_vue/compiler.py:1451-1455` appends each
template-authored text node as it is). So whatever Citry's own compiler
does to text, Vue sees the result.

### Two places where vize differs from upstream Vue

The measurement and code read found two differences from
`@vue/compiler-dom` 3.5:

- **The first line break after `<pre>`.** Upstream Vue drops it, as the
  HTML parser does. vize keeps it: `<pre>\n  a\n</pre>` compiles to the
  text `"\n  a\n"`. The browser drops that line break from the server
  HTML, so the server text and Vue's text differ, and Citry writes the
  `<pre>` as a shell with `data-allow-mismatch="children"` that Vue fills
  in (`crates/citry_vue_compiler/src/server_render.rs:3375-3381`,
  `:4361-4365`). Citry's own code assumes Vue drops it
  (`packages/py/citry/citry/_vue/direct_capture.py:1944-1948`).
- **`<textarea>` content.** Upstream Vue reads `<textarea>` and `<title>`
  as raw text and does not condense them. vize condenses `<textarea>`:
  `"\n  t\n"` becomes `" t "`, so the field's initial value differs
  between a static page and a Vue page.

### Every render path

| Path | Whose whitespace rules | Where decided |
|---|---|---|
| Hydrated | Vue's: the server writes the text the compiled render emits | `server_render.rs:20-21`; `_vue/serialization.py:431-486` |
| Hydration declined (`custom-hooks`, `compile-error`, `security-policy` and others) | Python's until Vue mounts, then Vue's | `_hydration_page_reason` in `_vue/serialization.py:384-428`; `serialize.py:762-778` |
| Static page | Python's | `serialize.py:722-726` |
| `ssr=False`, below `ssr_element_threshold` | Empty mount element, Vue's only | `_vue/serialization.py:1024-1028`, `:461-464` |
| `{{ value }}`, `<c-raw>`, `Markup`, `v-pre` | Written unchanged on every path | `capture.py` text bindings; `direct_capture.py:2955-2970`, `:1936-1960` |

When any component on a page needs Vue, the whole page becomes one Vue
app, so a parent without `js` is also compiled by Vue
(`packages/py/citry/tests/test_vue_events.py:857-890`). A slot fill is
written as `<template #name>` inside the caller's Vue template
(`packages/py/citry/citry/_vue/static_template.py:602-636`), so its
whitespace follows the caller's template.

### The authored text plan

The Rust Vue compiler also reports which authored text Vue condenses or
drops, as the authored text plan (`crates/citry_vue_compiler/src/lib.rs:821-953`).
Python validates it and stores it on `CompiledRender`
(`packages/py/citry/citry/_vue/compiler.py:809-940`, `:233`), and the plan
feeds the definition content id (`compiler.py:1359`). No code acts on it.
It reports `unsupported` for 45 of the 138 corpus templates the
measurement could compile, mostly where whitespace sits next to `{{ }}`,
so it cannot drive a rewrite as it stands.

## Measurement on real pages

A throwaway harness (deleted afterwards) applied Vue's condense rules to
every literal component template under `examples/` and `docs_site/`: 154
templates, 34 from the examples and 120 from the docs site, 166 KB. Its
Python model of the rules matched vize's authored text plan exactly on all
93 templates where the plan was complete. It then rendered six pages
before and after condensing and compared the visible text in headless
Chrome with the page scripts removed, so the browser showed the server
HTML.

| Measure | All | examples | docs_site |
|---|---|---|---|
| Templates with any change | 143 of 154 | 34 of 34 | 109 of 120 |
| Templates with `js` (already Vue-condensed when hydrated) | 25 | 5 | 20 |
| Whitespace-only first or last children dropped | 1,898 | 506 | 1,392 |
| Whitespace-only text dropped between siblings | 776 | 235 | 541 |
| ... between two inline elements by tag name (could be visible) | 188 | 69 | 119 |
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
- **Text that is not HTML breaks.** The docs pipeline renders every
  Markdown page as a Citry template before the Markdown pass
  (`docs_site/_internal/pipeline.py:201-241`). Condensing that template
  removes the blank lines that separate paragraphs, which would break all
  127 docs pages. Condensing one landing-page component
  (`docs_site/_internal/components/landing.py:1108-1178`) made the landing
  page fail with `ValueError: A Markup value ... is not a complete HTML
  fragment`, because a helper that reads its HTML line by line
  (`docs_site/_internal/util.py:23-58`) relies on the line breaks.
- **One element uses CSS `white-space: pre-wrap`**
  (`landing.py:2974`, styling the `div` at `landing.py:1557`). Its
  authored line breaks show today and would disappear.
- **`<pre>` and `<textarea>` are rare.** The corpus has five `<pre>` and
  two `<textarea>`, none with authored whitespace that condensing would
  change.

Limits: the harness guessed display from tag names, so 188 is an upper
bound; it changed template source only, not `{{ }}` values; it did not
model text that crosses a component boundary; and the docs byte figures
are before the docs build's own HTML minifier runs.

## How other frameworks handle it

- **Vue 3** condenses by default and offers `whitespace: 'preserve'` as a
  global compiler option (added in 3.1.0 after users reported broken
  spacing between inline buttons in 3.0). Even `preserve` drops
  whitespace-only first and last children. Vue SSR uses the same parser
  options as the client build, and hydration compares text nodes exactly
  (`runtime-core/src/hydration.ts:172-198` in 3.5.13), so the server and
  client builds must get the same option.
- **Angular** removes every whitespace-only text node by default and keeps
  `<pre>` and `<textarea>`. `ngPreserveWhitespaces` keeps one subtree.
- **Svelte 5** collapses whitespace between nodes to one space and trims
  it at tag edges, keeps `<pre>`, and offers `preserveWhitespace` per
  component through `<svelte:options>`.
- **React JSX and Astro** (whose `compressHTML` default is `'jsx'` since
  Astro 7) remove whitespace that touches a line break and need `{" "}`
  for an explicit space. JSX has no `<pre>` exception.
- **Jinja2 and Django** never touch whitespace between HTML tags by
  default. Django's `{% spaceless %}` removes it where the author asks.

All of these apply one rule on the server and the client, because one
compiler produces both. The ones that condense decide by tag name (`<pre>`,
`<textarea>`); none reads CSS, so each offers a per-component or
per-subtree opt-out for `white-space: pre` content.

## Options

Every option below has to leave the hydrated, declined and static paths
showing the same text. Vue receives the text Python rendered, so the
cleanest way to get there is to have one party apply the rule.

### Option 1: condense in Python to match Vue, keep vize condensing

Citry's template compiler applies Vue's condense rules to the `<c-*>`
template, and vize keeps condensing as it does today. A setting turns
Python's condensing off. This is the issue's first proposal.

- Hydrated pages: unchanged.
- Static and declined pages: whitespace between elements disappears where
  Vue would remove it. No visible change on the six measured pages; a
  possible change at the 152 inline sites in templates without `js`.
- Weak point: vize decides "first or last child" on the Vue template
  Citry generates, which wraps control flow and slot fills in its own
  elements. Python's rule, applied to the `<c-*>` template, can miss an
  edge that vize sees, and then vize drops a space Python kept. The text
  shift returns for those cases.
- Weak point: turning the setting off leaves vize condensing, so a page
  that hydrates still changes text. The setting can only safely apply to
  pages that never hydrate.

### Option 2: keep authored whitespace everywhere

Python stays as it is. vize compiles with condensing fully off, including
the first and last child rule that even Vue's `preserve` keeps.

- Static pages: unchanged.
- Hydrated pages: spaces appear where Vue removed them, as plain HTML,
  Jinja2 and Django would show them. In the example, `onetwo` becomes
  `one two`. Templates that wrote `<a>one</a><a>two</a>` to get touching
  links are unaffected.
- Cost: every whitespace-only text node becomes a node Vue creates and
  hydrates. The corpus has about 17 of them per template, and they add
  bytes to the render functions and the server HTML. On a large page this
  is the work Vue's condensing exists to avoid. Not measured.
- Cost: an HTML minifier must not run on hydrated pages, because it would
  remove text nodes Vue expects. That is true today and stays true.

### Option 3: Citry owns the rule; vize stops condensing (recommended)

Citry's template compiler applies one whitespace rule to the `<c-*>`
template when it compiles it. vize compiles with condensing off, so it
keeps the text it receives. Because the hydrated, declined and static
paths all render the text Citry's compiler produced, they agree by
construction.

The default rule is Vue's condense rule, applied to the `<c-*>` tree.
"First or last child" counts the edges of every Citry construct as well
as HTML elements: the template root, an element, a `c-if` / `c-elif` /
`c-else` branch, a `c-for` body, a `<c-fill>`, a component body and a
`<c-slot>` default. A setting and a per-component opt-out choose
`preserve`, which leaves the text as written.

- Hydrated pages: unchanged for nearly all templates, since vize was
  already applying the same rule. They differ only where the fixes below
  apply and where Citry's edges and vize's edges disagreed.
- Static and declined pages: change as in Option 1.
- Text-only templates (Markdown, plain-text email): opt out with
  `preserve`, which now works on hydrated pages too.
- Cost: a new pass in the Rust template compiler, a vize option to turn
  condensing off, a setting, and a per-component attribute.

### Option 4: a setting that only affects pages without Vue

Condense in Python, controlled by a setting, and leave vize alone. This
is Option 1 without the claim of parity: the docs state that the setting
does not affect hydrated pages. Rejected because a setting that changes
only one side keeps the text shift on declined pages, which is the bug.

## Recommendation for 0.9.0

Choose **Option 3**, with these parts:

1. **One rule, applied once.** Citry's Rust template compiler
   (`crates/citry_template_parser/src/compiler.rs`) condenses authored
   text with Vue's rules, treating the edges of every Citry construct as
   child-list edges. The compiler emits the condensed text in the same
   node shapes it emits today.
2. **vize keeps what it receives.** Pass a "do not condense" option to
   vize. The parser side already has `WhitespaceStrategy`; wiring it
   through `vize_atelier_dom`, which comes from crates.io, needs either an
   upstream change or a third patched crate in `third_party/rust/`.
   Until that lands, leaving vize in `condense` mode is a safe fallback:
   on text Citry has already condensed, vize can only remove whitespace
   at an edge Citry did not treat as one, and the check in item 6 catches
   that.
3. **Exceptions, decided by tag name:**
   - `<pre>`, `<textarea>`, `<title>`, `<script>`, `<style>`: content kept
     as written. This matches upstream Vue for `<pre>`, `<textarea>` and
     `<title>`, and fixes vize's `<textarea>` difference.
   - `<pre>` and `<textarea>`: the compiler drops one line break written
     straight after the start tag, as the HTML parser does, and the Rust
     server writer adds one back when the remaining text starts with a
     line break. Server text and browser text then match and the `<pre>`
     shell is no longer needed.
   - `{{ value }}`, `<c-raw>`, `Markup` and `v-pre` content: written
     unchanged, as today.
4. **A setting and a per-component opt-out.** A `CitrySettings` field
   (proposed: `whitespace: Literal["condense", "preserve"] = "condense"`)
   and a component class attribute of the same name that overrides it for
   that component's template. The docs pipeline sets `preserve` on
   `DocsContent` and the landing helper that reads line breaks.
5. **Cache identity.** The chosen mode joins the template compile cache
   key (`packages/py/citry/citry/component_render.py:3036-3078`) and the
   Vue compile identity (`_vue/compiler.py:582-606`), so a change of mode
   never reuses a compiled template from the other mode.
6. **A check that proves the rule matches Vue.** In tests and in
   development mode, compile the condensed template once more with vize
   in `condense` mode and assert that vize's authored text plan holds no
   actions: Vue has nothing left to condense. A non-empty plan names the
   text where Citry's rule and Vue's differ. This gives the authored text
   plan a job; if it is not wanted for that, remove it with the rest of
   its validation.
7. **Treat a no-break space as text,** not whitespace, in the three
   existing drops (branch gaps, empty component bodies, gaps between
   fills), so Citry's whitespace set matches Vue's.

Why Option 3 over the others:

- It is the only option where parity holds by construction rather than by
  two implementations agreeing, and it keeps working when the user opts
  out.
- Hydrated pages, which are the pages Vue users compare against Nuxt and
  plain Vue, keep the output they have today.
- The measured cost to static pages is small: no visible change on six
  real pages, 7 to 12% smaller docs HTML before minification. The real
  risk is templates that are not HTML, and the per-component opt-out
  covers them.

Why condense rather than preserve as the default: Vue users expect Vue's
rule, hydrated output stays as it is, and a page has fewer text nodes to
hydrate. The cost is a break for static pages that relied on a line break
showing as a space between inline elements. The opposite default (Option
2's rule under Option 3's mechanism) is a one-line change if the
maintainer prefers authored whitespace; it breaks hydrated pages instead.

### What touches the contract

The recommendation changes text content in the compiler's output, not
its shape, and adds an input to the compiler. That makes it a high-risk
change under `CLAUDE.md`. The implementation plan must cover:

- The compiler (`compiler.rs`) and its option, plus the five
  `src/lang/*.rs` implementations if the option reaches `LangImpl`
  (Python needs real work; JS, PHP, Go and Rust are stubs).
- The PyO3 glue (`crates/citry_core_py/src/lib.rs`) and the `_rust.pyi`
  stub, if `compile_template` gains a parameter. That needs a
  `citry_core` release before `citry` 0.9.0.
- vize: the option in `third_party/rust/vize_s1_to_s2` and its wiring
  through `vize_atelier_dom`.
- `crates/citry_vue_compiler/src/server_render.rs` for the `<pre>` and
  `<textarea>` line break, and removal of the whitespace-only `<pre>`
  shell.
- Tests that lock authored whitespace today and must change:
  `crates/citry_template_parser/tests/tag_compiler.rs:682-700`, `:321`,
  `:406`, `:440`; `packages/py/citry/tests/test_vue_events.py:857`,
  `:920`; `test_vue_hydration_regions.py:703-723`, `:1173-1199`; and the
  exact-HTML assertions in static `serialize()` tests.
- The new parity test from the issue: for inline elements separated by
  line breaks, `<pre>`, `<textarea>`, slot fills and `<c-raw>`, the static
  output, the declined server HTML and Vue's browser render produce the
  same text nodes.

## Error modes

- **The setting has another value.** `CitrySettings` raises `ValueError`
  when it is created, as `mode` does; a non-string raises `TypeError`.
- **The component attribute has another value.** Raised when the class is
  defined, with the component name.
- **A component sets `preserve` and the page hydrates.** Both sides keep
  the authored text; hydration matches. This is the case Option 1 cannot
  handle.
- **CSS `white-space: pre` or `pre-wrap` on an element that is not
  `<pre>`.** Citry cannot see CSS, so the text is condensed and the
  authored line breaks do not show. The docs say to use `<pre>`, `<c-raw>`
  or the component opt-out. Vue has the same limit.
- **Whitespace inside `<c-raw>`, `Markup` or a `{{ }}` value.** Kept as
  written in every mode.
- **Text that crosses a component boundary or a slot fill.** A fill's
  text follows the mode of the template it is written in (the caller's),
  and the receiving component's own text follows its own mode. Both paths
  render the same bytes, because both read the text Citry compiled.
- **A template that is not HTML** (Markdown, plain text) left in
  `condense` mode. Its line breaks collapse. This is the main break; the
  migration notes and the setting's docstring call it out.
- **vize's plan check finds a difference** (item 6). In tests it fails
  the test. In development mode it logs a warning naming the template and
  the text; it never fails a production render.

## Migration notes

For the 0.9.0 upgrade guide:

- **Static pages now drop whitespace between tags the way Vue does.** A
  line break between two inline elements, such as two links or a label
  and a value, no longer shows as a space. Add the space inside the text
  (`<a>one</a> <a>two</a>` on one line keeps it), use CSS `gap`, or set
  `whitespace = "preserve"` on the component.
- **Templates that produce Markdown or plain text need
  `whitespace = "preserve"`.** Otherwise their line breaks collapse.
- **Content styled with `white-space: pre-wrap` needs `<pre>`, `<c-raw>`
  or `preserve`.**
- **`<textarea>` content now keeps its whitespace on Vue pages too.** If a
  field relied on Vue trimming it, trim the value in Python.
- **To keep 0.8.0's static output,** set `whitespace="preserve"` in the
  settings. Hydrated pages then keep authored whitespace as well, so
  their spacing changes instead.

## What would show this wrong

- **The plan check fails often.** If item 6 finds many templates where
  Citry's `<c-*>` rule and vize's result differ, the "one rule on the
  `<c-*>` tree" premise is wrong and the edge list needs rethinking
  before 0.9.0.
- **vize cannot turn condensing off** without a deep patch to a crate
  Citry does not control. Then fall back to item 2's safe mode and decide
  whether `preserve` can be offered on hydrated pages at all.
- **Real apps break visibly.** If a survey of a few user apps (beyond this
  repo's examples and docs) finds visible spacing changes on static
  pages, condense is the wrong default and authored whitespace should be
  the default instead.
- **Hydration cost.** If someone prefers the authored-whitespace default,
  measure hydration time on the 1,400-output benchmark page with and
  without condensing first. This recommendation assumes the extra text
  nodes cost something; that is not measured.

## Decisions for the maintainer

1. Option 3 (Citry owns the rule, vize stops condensing): yes or no.
2. Default rule: `condense` (recommended) or `preserve`.
3. The names: setting `whitespace` and the component attribute of the
   same name, or other names.
4. Keep the authored text plan as the parity check (item 6), or remove it.
5. Patch `vize_atelier_dom` in `third_party/rust/` or ask upstream for the
   option.
