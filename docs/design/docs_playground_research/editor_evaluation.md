# Playground editor evaluation

**Status (2026-07-28): Stage 4 bounded research complete. Choose CodeMirror 6
for the first Citry playground. The editor proof passes in Chromium. Real
screen-reader sessions, real 400% browser zoom, other browsers, and a
production Citry language package remain later gates.**

## Outcome

Use **CodeMirror 6** for the first playground and build a small Citry language
package around it. Do not run Pygments as the interactive editor engine, and do
not choose Monaco for this version.

Both pinned candidates can provide an accessible named editing surface, undo,
search, bracket support, persistent diagnostics, and mixed Python, HTML,
JavaScript, and CSS highlighting. CodeMirror is the better fit because:

- its Lezer parser model can represent nested languages structurally and
  incrementally;
- the proof reused the official Python, HTML, JavaScript, and CSS parsers and
  mounted them inside the three Citry triple-quoted assignments;
- the measured initial editor payload was 178,063 bytes Brotli, compared with
  571,309 bytes for the scoped Monaco main-thread build, before Monaco's
  74,794-byte
  Brotli editor Worker;
- it does not introduce another Worker family next to the Python execution
  Worker;
- its extension surface lets the first version include only the editing
  features this playground needs.

Monaco remains a reasonable future choice if Citry later needs VS Code-grade
language services, a Python language server, or a larger IDE surface. Those are
not first-version requirements. Monaco's extra payload, explicit Worker asset
wiring, and regex-driven Monarch maintenance are costs without a compensating
product benefit here.

This decision does not authorize product implementation. Stage 1 runtime and
security gates in
[`runtime_feasibility.md`](runtime_feasibility.md) remain open.

## Scope and proof inventory

The runnable proof is in [`editor_proof`](editor_proof/):

- `layout/` is the editor-independent two-panel layout;
- `codemirror/` and `monaco/` load equivalent single-module samples;
- `samples/citry_component.py` exercises Python, a typed template assignment,
  interpolation, a dynamic attribute, nested HTML script and style blocks,
  direct JavaScript, and direct CSS;
- `src/` contains the two editor integrations and the shared proof shell;
- `tests/layout_probe.mjs` exercises layout, focus, resizing, mobile behavior,
  and document overflow;
- `tests/editor_probe.mjs` exercises the editor contract under a nested base
  path and restrictive Content Security Policy;
- [`measurements.json`](editor_proof/measurements.json) records minified raw,
  gzip, and Brotli sizes.

This is a static research spike, not product source. It does not execute Python
or render Citry output. That boundary keeps the editor choice independent of
the still-open runtime topology.

## Pinned comparison

The lockfile pins every package exactly. The most important versions are:

| Part | Pinned version |
| --- | --- |
| CodeMirror state | 6.7.1 |
| CodeMirror view | 6.43.7 |
| CodeMirror language | 6.12.4 |
| CodeMirror commands | 6.10.4 |
| CodeMirror Python | 6.2.1 |
| CodeMirror HTML | 6.4.11 |
| CodeMirror JavaScript | 6.2.5 |
| CodeMirror CSS | 6.3.1 |
| Monaco | 0.56.0 |
| esbuild | 0.28.1 |
| Playwright | 1.61.0 |

The versions were current on the research date. Monaco 0.56.0 was published
on 2026-07-20. CodeMirror view 6.43.7 was published on 2026-07-27, and the
[CodeMirror changelog](https://codemirror.net/docs/changelog/) shows continuing
mixed-language, mobile, bidirectional-text, and input fixes across its modular
packages.

The clean proof install's 2026-07-28 `npm audit` also reported one moderate and
one low advisory in Monaco's transitive `dompurify`; it reported no high or
critical advisory and attributed neither finding to the selected CodeMirror
packages. The comparison lockfile is research evidence, not a production
dependency set. Any future reconsideration of Monaco must begin with a fresh
security audit rather than promoting this proof bundle.

## Decision matrix

| Criterion | CodeMirror 6 | Monaco | Decision effect |
| --- | --- | --- | --- |
| Single Python module editing | Passed | Passed | Tie |
| Undo and search | Passed | Passed | Tie |
| Tab indentation and brackets | Configured, not directly probed | Configured, not directly probed | Tie, Stage 6 gate |
| Structural mixed-language model | Lezer nested parsers | Monarch tokenizer states in this proof | CodeMirror |
| Citry grammar extension path | Dedicated Lezer grammar plus `parseMixed` | Monarch regex states, semantic-token provider, or a separate TextMate integration | CodeMirror |
| Named accessible editing surface | Passed DOM check | Passed DOM check | Tie, manual AT gate open |
| Persistent editor diagnostic | Passed | Passed | Tie |
| Main-thread Brotli editor assets | 178,063 bytes | 571,309 bytes | CodeMirror |
| Additional editor Worker | None | 74,794 bytes Brotli | CodeMirror |
| Nested base path | Passed | Passed | Tie |
| Restrictive CSP | Passed | Passed with explicit self-hosted Worker | CodeMirror is simpler |
| Maintenance surface | Modular packages and a Citry grammar | Editor core, contributions, workers, and custom token states | CodeMirror |
| Future IDE/language-server depth | Possible but assembled | Strong built-in IDE base | Monaco, but not required |

## Layout proof result

The layout-only spike deliberately used a textarea and an empty iframe before
either editor was introduced. This kept panel behavior from being confused
with editor behavior.

The Chromium probe passed:

- one named `main`, one `h1`, and a titled result iframe;
- desktop Code and Result panels with no document-level overflow;
- an accessible vertical separator with value, range, and instructions;
- Arrow keys at 1%, Shift plus Arrow at 10%, Home, End, and Enter reset;
- pointer drag, pointer capture, real CDP touch drag, and double-click reset;
- a 30% to 70% clamp and persisted split position;
- physical Arrow behavior reversed under RTL;
- a 24 CSS-pixel separator target in the touch split view;
- a 320 CSS-pixel one-panel Code/Result switch;
- preservation of editor selection and scroll position when panels switch,
  plus a result iframe that can receive focus;
- viewport-height updates through `visualViewport`;
- persistent in-flow diagnostics that do not cover panel controls;
- a working small-screen header menu.

The 400% check is explicitly a 1280-to-320 CSS-pixel reflow proxy. Headless
Chromium does not control real browser chrome zoom. A manual 400% test remains
required in Stage 6, as do VoiceOver, NVDA, JAWS, and TalkBack sessions. The
proof also needs WebKit and Firefox runs before product acceptance.

### Layout contract to carry forward

Use the layout spike's behavior as the starting contract:

1. On wide viewports, show two independently scrolling panels separated by a
   keyboard and pointer operable separator.
2. On narrow or short viewports, show one panel at a time with explicit Code
   and Result controls. Do not force a very narrow split editor.
3. Keep the site header and a single page heading. Omit the docs left rail and
   right table of contents on this route.
4. Keep diagnostics in flow at the bottom of their owning panel. A live-region
   announcement may supplement them, but a toast must not be the only record.
5. Make the code editor, preview iframe, diagnostics, and header menu own their
   scroll and focus behavior. Do not let a drag gesture or rerun steal focus.

## Editing behavior comparison

The two editor proofs use the same source and controls. Automated checks passed
for:

- an accessible name of `Citry Python module`;
- editing and undo through the editor's own history;
- a keyboard-accessible Search control and visible search UI;
- a persistent Python diagnostic plus an in-editor error marker;
- direct JavaScript and CSS regions inside Citry assignments;
- loading with no page or console errors.

Both integrations configure ordinary Python highlighting. The proof's direct
top-level Python tree/token assertions are recorded separately from the nested
language checks.

CodeMirror required explicit feature composition. The proof includes line
numbers, history, search, Tab indentation, selection, brackets, folding,
autocomplete support, and linting. This is helpful for Citry because every
feature has an explicit payload and product decision.

Monaco required importing the editor API, the find contribution, four Monarch
language definitions, the custom Citry tokenizer, CSS, and a self-hosted editor
Worker asset. Monaco has deeper built-in IDE affordances, but the first
playground does not need the command palette, multi-file model, minimap,
language server, or diff editor.

## Citry mixed-language evaluation

The existing Pygments lexers are the syntax behavior reference, not code that
can be transplanted into either editor. They contain important behavior that a
live Citry language package must preserve:

- `template`, `js`, and `css` triple-quoted assignments;
- optional type annotations;
- double and single triple quotes;
- Citry tags and dynamic attributes;
- balanced `{{ Python }}` expressions that skip strings and nested braces;
- Python-valued structural attributes;
- JavaScript-valued `$c-props`;
- Citry template comments and verbatim `c-raw` content.

The proof comparison is intentionally honest about partial coverage:

| Pygments fixture behavior | CodeMirror proof | Monaco proof |
| --- | --- | --- |
| Ordinary Python | Structural Python parse | Python Monarch tokens |
| `template = """..."""` | Mounted HTML parser | Embedded Citry HTML state |
| Typed template opener | Recognized by assignment context | Recognized by opener rule |
| Triple single quotes | Recognized | Recognized |
| Direct `js` assignment | Mounted JavaScript parser | Embedded JavaScript state |
| Direct `css` assignment | Mounted CSS parser | Embedded CSS state |
| HTML `<script>` and `<style>` | Nested by official HTML support | Nested by Monaco HTML tokens |
| Citry tag names | Visual decoration over HTML parse | HTML tag token |
| `{{ Python }}` | Delimiters decorated; no Citry parse node yet | Python tokenizer between simple delimiters |
| `c-*` Python value | Name decorated; value remains HTML | Python tokenizer for quoted values |
| Balanced braces and strings in interpolation | Not implemented | Not implemented robustly |
| Structural `cond` and `each` values | Not implemented | Not implemented |
| `$c-props` JavaScript value | Not implemented | Not implemented |
| `c-raw` verbatim body | Not implemented | Not implemented |

CodeMirror's main proof is the outer composition: its Python syntax tree finds
a triple-quoted `String` in the right assignment and mounts the official HTML,
JavaScript, or CSS parser over the string body. The official
[mixed-language example](https://codemirror.net/examples/mixed-language/)
documents this hierarchical and overlay model, including recursively nested
HTML script and style parsing and the need to include each nested language's
support extensions.

The small Citry decorations in the spike exist only to make the missing syntax
visible. They must not ship as the final language implementation. A regular
expression cannot match the existing Pygments lexer's balanced interpolation
scanner or the template parser's full behavior.

Monaco's proof uses Monarch state transitions. It can enter Python tokenization
between a simple `{{` and `}}`, and in quoted `c-*` attributes. That makes a
useful visual proof, but the closing rules are regex boundaries rather than a
Citry syntax tree. Python strings, nested dictionaries, malformed input, and
Citry recovery rules would require increasingly complex states or a separate
semantic-token service. That is the central maintenance disadvantage.

### Production Citry language package

Build a first-party CodeMirror language package before product integration:

1. Parse the Python module with the official Lezer Python parser.
2. Recognize only `template`, `js`, and `css` string assignments supported by
   Citry, including typed assignments and both triple-quote forms.
3. Mount a Citry template parser in `template`, and official JavaScript and CSS
   parsers in the other assignments.
4. In the Citry template parser, represent interpolation, dynamic attributes,
   comments, raw content, and structural tags as real nodes. Mount Python or
   JavaScript parsers only over expression nodes.
5. Translate every current `pygments_citry` fixture into editor token or syntax
   tree tests. Add malformed and unfinished-source fixtures because an editor
   sees invalid source continuously.
6. Keep Pygments for static documentation and use the shared fixture corpus as
   the compatibility contract. Do not try to make its server-oriented token
   stream the incremental browser editor.

The Citry grammar can start as a thin structural grammar around the existing
HTML parser. It does not need completion or type checking in the first version.

## Accessibility evaluation

Both proofs expose a named textbox and keyboard-accessible surrounding
controls. CodeMirror also exposes `EditorView.announce` for changes that need a
polite screen-reader announcement. Its
[reference manual](https://codemirror.net/docs/ref/) warns that purely visual
layers are invisible to screen readers, which reinforces the requirement for
the separate persistent diagnostic.

Monaco's official
[integrator accessibility guide](https://github.com/microsoft/monaco-editor/wiki/Accessibility-Guide-for-Integrators)
requires a friendly `ariaLabel`, considers high-contrast behavior, recommends
enabling `accessibilitySupport`, and asks hosts to provide product-specific
accessibility help. The proof sets the label and forces accessibility support
on. A production Monaco integration would also owe an accessibility help page
and full keybinding documentation.

No automated DOM assertion proves screen-reader usability. Before release,
test the chosen CodeMirror build with:

- VoiceOver and Safari on macOS;
- NVDA and Firefox or Chromium on Windows;
- TalkBack and Chromium on Android;
- keyboard-only use at default and 400% zoom;
- long lines, line wrapping policy, composition input, and bidirectional text;
- editor, separator, panel switch, diagnostics, Run, Reset, and preview
  focus as one end-to-end sequence.

## Deployment, Worker, and CSP result

The editor test server mounts the proof at `/nested/editor-proof/`. Both pages
resolve their JavaScript and CSS assets there with no absolute-root assumption.

The server sends this bounded policy:

```text
default-src 'none';
script-src 'self';
style-src 'self' 'unsafe-inline';
worker-src 'self';
img-src 'self' data:;
font-src 'self' data:
```

Both proofs passed without a console or page error. The inline-style allowance
is required because both editors generate styles in the page. The product CSP
must merge these needs with the stricter runtime and preview policies from
Stage 1. This proof does not weaken the preview iframe policy.

CodeMirror created no editor Worker resource. The future Python execution
Worker is independent.

Monaco's worker URL is constructed relative to its loader with `new URL(...,
import.meta.url)` and uses `type: "module"`. The test explicitly loads the
self-hosted editor Worker and waits for a ready message from inside it. This
proves nested-path resolution, successful Worker execution, and `worker-src
'self'` compatibility. The proof therefore requests this Worker eagerly. The
scoped Monaco editor features did not themselves require that Worker during
ordinary tokenization, so a production integration could defer it until a
feature needs it. Monaco's
official tracker shows the explicit
[`MonacoEnvironment.getWorker` pattern](https://github.com/microsoft/monaco-editor/issues/2605)
and the failure mode when bundlers or origins do not resolve a Worker correctly.

No CDN is needed or recommended for either editor. Pin and self-host all editor
assets with the docs build.

## Plain-textarea fallback

The static page should contain a real, named textarea with the starter module
before CodeMirror loads. CodeMirror progressively enhances that control. Keep a
single source store and mirror every editor transaction to the textarea value
or another source buffer that can be restored without CodeMirror.

If the editor chunk fails to download, its integrity check fails, or editor
initialization throws:

- leave or restore the textarea with the latest known source and selection;
- show a persistent `Editor unavailable` diagnostic, not only a toast;
- keep ordinary textarea editing, selection, scrolling, copy, download, and
  Reset available;
- provide a `Retry editor` action that reimports and rehydrates CodeMirror
  without replacing the user's source;
- disable automatic reruns while degraded, so a load failure cannot create an
  unexplained run loop;
- keep explicit Run available when the Python runtime is healthy and the
  current textarea value is the authoritative source.

An editor-library failure is not an execution-security boundary. Disabling Run
in every textarea fallback would turn a nonessential enhancement failure into a
complete playground outage. The runner can execute the same source string from
a textarea, and its diagnostics can still use line and column text.

There is one stricter failure branch. If the application cannot prove that the
textarea contains the latest complete source, or if the runtime itself is not
healthy, disable Run. Preserve the recovered text, keep copy and download, offer
Reset and `Retry editor`, and explain why execution is unavailable. Never reset
or replace visitor source merely because editor initialization failed.

The fallback does not promise syntax highlighting, line numbers, bracket
matching, completion, lint marks, or editor-specific shortcuts. Its purpose is
source preservation and continued basic use. Stage 6 should force a failed
editor import after edits and verify source, selection, manual Run, Reset,
copy/download, diagnostics, and retry recovery.

## Bundle measurements

`npm run build` produced minified editor and Worker ESM with esbuild 0.28.1 and
copied the small Monaco loader unchanged. `npm run measure` then measured
exact file bytes. Shared proof-shell CSS is excluded from both editor totals.

| Candidate asset set | Raw | gzip | Brotli |
| --- | ---: | ---: | ---: |
| CodeMirror initial | 614,719 B | 213,087 B | 178,063 B |
| Monaco main-thread editor assets | 2,825,562 B | 715,730 B | 571,309 B |
| Monaco editor Worker | 304,399 B | 93,805 B | 74,794 B |
| Monaco proof initial network total | 3,129,961 B | 809,535 B | 646,103 B |

The Monaco main-thread set includes `monaco-loader.js`, `monaco.js`, and
`monaco.css`. The proof initial network total also includes the Worker because
the CSP and execution handshake requests it immediately. The editor build is a
scoped import of the editor API, find contribution, and four language
definitions, not the package's all-language entry point. The comparison
therefore does not artificially charge Monaco for every bundled language.

The CodeMirror build includes more than a bare editor: autocomplete support,
linting, search, folding, four languages, and the mixed-language proof. The
production bundle should remove unused completion support and establish a
performance budget, but optimization is unlikely to reverse the result.

The Brotli initial ratio in this proof is about 3.2 to 1 in CodeMirror's favor.
The absolute bytes are a build artifact measurement, not a transfer-time or
parse-time benchmark. Stage 6 must measure cold load, JavaScript parse, first
editable time, and low-end mobile memory together with Pyodide.

## Maintenance and upgrade risk

Both projects are actively released. The maintenance difference is ownership,
not project health.

With CodeMirror, Citry owns:

- exact package pins across several modular packages;
- one Citry language package and its fixture compatibility tests;
- editor configuration, theme, diagnostics, and toolbar integration.

With Monaco, Citry would own:

- a larger editor integration and contribution import list;
- module Worker entries and public base-path behavior;
- a custom Monarch language or semantic-token provider;
- high-contrast and accessibility-help integration;
- tracking package-level breaking changes. Monaco's repository states that the
  typed API is versioned while other internals may break, so deep imports need
  an upgrade smoke test.

Pin either choice exactly and make the browser proof an upgrade gate. For
CodeMirror, update related packages as a tested set even though they have
independent version numbers.

## Known failure modes and open gates

The following are not solved by choosing CodeMirror:

- A malformed Citry module needs useful parser recovery rather than losing all
  embedded highlighting after an unfinished quote.
- The production grammar does not exist yet. The spike's decorations are not an
  acceptable substitute.
- Diagnostics from the Python Worker need source offsets that map correctly to
  the editor after debounce, cancellation, and stale-run suppression.
- Editor state must survive mobile Code/Result switching without re-creating
  the editor.
- The result iframe must not capture shortcuts intended for the page, and the
  editor must not capture the separator or header shortcuts.
- Browser zoom, virtual keyboard resize, input methods, RTL, high contrast, and
  screen readers need manual tests with the real editor inside the full layout.
- Editor startup must be measured together with Pyodide. The smaller editor
  cannot justify eager Python startup by itself.
- CSP style handling needs a deliberate production policy. A nonce or extracted
  static styles may be preferable to a broad inline-style allowance.

## Recommendation for the design plan

Record these Stage 4 decisions in the final playground design:

1. CodeMirror 6 is the selected editor, exact versions pinned by the docs
   package lockfile.
2. A first-party Citry CodeMirror language package is a prerequisite, with the
   current Pygments fixtures as the initial compatibility corpus.
3. The editor-independent layout contract comes from the textarea proof.
4. Diagnostics are persistent and owned by their panel; announcements and
   toasts are supplementary.
5. Editor assets are self-hosted. CodeMirror uses no editor Worker.
6. Stage 6 includes the real assistive-technology, zoom, mobile, and browser
   matrix plus combined editor/runtime performance budgets.
7. Monaco is reconsidered only if the product scope expands to language-server
   or IDE features that CodeMirror would require Citry to rebuild.

## Reproducing the evidence

From `docs/design/docs_playground_research/editor_proof`:

```bash
npm ci --ignore-scripts
npm run install:browser
npm test
npm run test:layout
npm run measure
```

The browser-install step downloads the Playwright-pinned Chromium build when it
is not already present in the local cache. Linux CI may also need Playwright's
documented operating-system dependencies. `npm test` rebuilds the static assets
before running the editor probe. The
layout test is separate so the original textarea baseline stays independent.
The browser output should report passed accessibility, diagnostics,
mixed-language, search, undo, nested-base-path, CSP, and Worker checks.

The tests use Chromium only. A green result is the Stage 4 proof result, not a
cross-browser release certification.
