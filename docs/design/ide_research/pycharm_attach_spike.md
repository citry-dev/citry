# PyCharm language-server attach spike

Status: completed 2026-08-11.

This spike answers the blocking question from
[`ide_integration.md`](../ide_integration.md): can Citry attach as a second
language server to a Python document already owned by PyCharm's Python plugin?
It also compares that path with a standalone `*.citry-html` file and with
JetBrains' native LSP API.

## Tested environment

- macOS 26.6 on Apple silicon
- PyCharm 2026.2.0.1, build `PY-262.8665.369`
- LSP4IJ 0.20.1
- Citry LSP protocol 1, catalog schema 1
- project interpreter `.venv/bin/python`
- registry target `packages.editors.jetbrains.spike_fixture.app:app`

The controlled fixture lives in
[`packages/editors/jetbrains/spike_fixture/`](../../../packages/editors/jetbrains/spike_fixture/).
The importable LSP4IJ definition lives in
[`packages/editors/jetbrains/lsp4ij/citry/`](../../../packages/editors/jetbrains/lsp4ij/citry/).

## Result

The attach question is resolved: **yes**. LSP4IJ attached one `citry-lsp`
process to both `app.py` and `external_card.citry-html`. PyCharm's own Python
support remained active on `app.py`; Citry was an additional server, not a
replacement.

The native JetBrains LSP API also attached one project-wide Citry client to
both files. Its client reached `Running`, published diagnostics for both
documents, and reported Citry's standard server capabilities. There is no
attachment advantage that requires an official plugin for the first PyCharm
semantics release. A plugin can still improve installation, configuration,
status presentation, and eventually language injection/coloring.

## Exercised matrix

Every request below went through LSP4IJ's own feature support, after PyCharm
left indexing mode. It was not a direct test client talking around the IDE.

| Feature | Inline `app.py` | Standalone `*.citry-html` | Evidence |
| --- | --- | --- | --- |
| Attach as a second server | Pass | Pass | one LSP4IJ server returned for each PSI file |
| Completion | Pass | Pass | `str.upper` / `str.capitalize` members returned |
| Hover | Pass | Pass | typed `(variable) title: str` plus Citry provenance |
| Definition | Pass | Pass | mapped to the exact `template_data()` key |
| References | Pass | Pass | five authored/root locations returned without consumer duplication |
| Declaration | Pass | Pass | mapped to the exact `template_data()` key |
| Type Definition | Pass | Pass | mapped to pinned typeshed's `str` definition |
| Push diagnostics | Pass | Pass | clean fixtures published zero diagnostics |
| Unsaved edit/clear | Not separately mutated | Pass | unknown root appeared as `citry.template.unknown-variable`, then cleared after removal |
| Full-document formatting | Not applicable | Pass | dynamic registration accepted; one exact text edit returned |
| Citry syntax coloring | No | No | Python remains Python with string coloring; standalone file type was `PLAIN_TEXT` |

Once PyCharm was smart, the six semantic requests completed in 36-226 ms in
the measured cold matrix. LSP4IJ's standalone formatting request completed in
43 ms. The native Citry client initialized in 1.625 seconds. Initial project
indexing delayed when the feature matrix could start; that delay is PyCharm's
normal dumb-mode gate, not Citry request latency.

## Interoperability correction discovered by the spike

Citry originally registered standalone formatting with an LSP 3.17
`RelativePattern`. LSP4IJ accepted it, but PyCharm's native client rejected the
object-shaped `pattern`. A string glob fixed native conversion, but source
inspection and a live probe then found that LSP4IJ 0.20.1 ORs the `language`,
`scheme`, and `pattern` fields of one document filter rather than ANDing them.
That made a file-scheme match expose Citry formatting on ordinary Python.

The final registration is therefore language-only (`citry-html`). The
registration already belongs to one initialized workspace client, so this
retains the intended effective scope. Both clients accept it; LSP4IJ reports
formatting for the standalone template and not for `app.py`.

## Honest limitations

- LSP4IJ does not add Citry-specific coloring. Inline templates remain Python
  string literals. The tested filename mapping leaves standalone templates as
  plain text unless another JetBrains language/file-type integration colors
  them.
- VS Code's nested-template HTML projection, `<c-element>` HTML delegation,
  and embedded JavaScript/CSS provider bridge use Citry-private client
  requests. A generic LSP4IJ definition cannot reproduce those delegated
  editor-provider features. Citry-owned standard LSP behavior inside those
  documents still works.
- LSP4IJ does not understand the private `citry/status` notification. Registry
  failures still arrive through standard `window/showMessage`; an official
  plugin could render the richer status by supplying a custom client.
- The spike used local PyCharm. JetBrains remote-development placement and
  interpreter discovery were not exercised and are not part of this result.
- PyCharm must leave indexing mode before the IDE invokes most semantic
  feature adapters. Requests themselves were fast once that gate opened.

## Decision

Publish the LSP4IJ template as the first PyCharm semantics route. Document its
manual interpreter/app configuration and its coloring/custom-provider limits.
Do not build a native plugin solely to make a second LSP attach to Python;
both routes already succeed. Reopen the thin-plugin rung when one of these is
valuable enough to justify a maintained JetBrains artifact:

1. one-click environment and app selection;
2. first-party status/troubleshooting UI;
3. Citry language injection or bundled standalone coloring;
4. private HTML/JavaScript/CSS provider bridges comparable to VS Code;
5. evidence that template import/setup is too error-prone for users.

The deferred implementation is tracked by
[GitHub issue #78](https://github.com/citry-dev/citry/issues/78). It separates
two upgrades that should not be conflated:

1. **Coloring through standard protocols first.** Add
   `textDocument/semanticTokens` to `citry-lsp`, backed by the existing parser,
   source maps, and syntax fixtures, then verify that LSP4IJ and the native
   client paint inline tokens cleanly over Python string highlighting. Reuse
   the existing TextMate grammar for standalone `*.citry-html` coloring.
2. **A native plugin for editor-side integration.** Use JetBrains'
   `LspIntegrationProvider` for interpreter/app selection, status, and server
   lifecycle; add Python language injections for Citry/HTML, JavaScript, and
   CSS; and bridge Citry's existing private projections where an ordinary
   injection cannot express `<c-element>`, nested templates, Alpine scope, or
   child-component contracts.

Semantic tokens may remove coloring as a reason to require a plugin. They do
not provide setup/status UI or invoke JetBrains' installed HTML, JavaScript,
and CSS services. Conversely, a TextMate bundle can color a standalone file
but cannot inject into a Python file type already owned by PyCharm.

For the full bridge, prefer native language injection with generated
prefixes/suffixes for `$component`, Citry magics, `JsData`, props, events,
Alpine scope, and `CssData`. Use mapped virtual documents only for the
specialized cases where injection is insufficient. The implementation must
retain exact authored-source navigation, never expose a generated document,
respect cancellation and project generations, and degrade when an optional
JetBrains HTML/JavaScript/CSS service is unavailable. Local PyCharm is the
first acceptance surface; remote development remains a separately proven
follow-up rather than an inherited claim.

## Reproduction

1. Install `citry-lsp` in the project's `.venv`.
2. Install LSP4IJ 0.20.1 or newer in PyCharm.
3. In LSP4IJ's **New Language Server** dialog, select **Import from custom
   template...** and choose
   `packages/editors/jetbrains/lsp4ij/citry/`.
4. Change the `app` initialization option if the project does not expose
   `app:app`, and adjust the command if its environment is not `.venv`.
5. Open an inline component module and a `*.citry-html` template. The LSP4IJ
   console should show one Citry server serving both mappings.
