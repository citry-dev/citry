# Changelog

## 0.1.0 - Unreleased

- Add one `citry-lsp` client per workspace folder, using that folder's selected
  Python environment and optional `citry.app` setting.
- Surface registry, syntax-only, interpreter, app, and protocol status with
  restart and status commands.
- Keep the Python extension optional so compatible editor forks can use an
  explicitly configured `citry.python` executable.
- Add parser and registry diagnostics, completion, hover, navigation, and
  document symbols through the companion language server.
- Reuse VS Code's HTML, CSS, and JavaScript providers for completion, hover,
  and definitions inside exact Citry asset strings and standalone Citry
  templates, with no app configuration required.
- Add PascalCase component suggestions, precise component-class navigation,
  and typed slot-data completion and hover through `citry-lsp`.
- Add syntax-only structural-tag and Citry directive snippets, lexical
  `c-for`/`c-fill` completion and hover, and exact component-input and static
  fill-slot definitions when the catalog provides unambiguous authoring
  provenance.
- Add conservative `TemplateData` root completion, hover, and exact annotated
  field navigation for proven component templates, intersecting shared and
  inherited consumers instead of guessing from one component.
- Reopen Citry tag suggestions after backspacing or undoing an incorrect
  partial tag name and then continuing the corrected name.
- Add **Citry: Format Document** and **Citry: Format at Cursor**, standard
  `citry-html` formatting, the `source.format.citry` Python save action, and
  deterministic per-folder routing for nested workspaces. Formatting now uses
  the complete conservative structural layout shared by every Citry
  surface.
- Apply the shared Python expression, `c-for`, and `c-fill data` formatting
  results without client-side rewriting, and show the active Python provider
  in project status.
- Extend both commands and `source.format.citry` to
  direct `template`, `js`, and `css` literals. JavaScript and CSS use VS Code's
  first public formatter result through validated, idempotent virtual
  documents with one stable provider-selection and configuration context while
  keeping the selected provider identity explicit as unknown.
  Each provider pass has a bounded wait and discards its virtual source when
  Citry cancels the invocation.
  VS Code format cancellation is forwarded to the language-server request;
  language-server cancellation aborts the current virtual-document request and
  prevents later idempotence passes or regions from starting.
- Include an explicit empty parameter object in status and reload requests so
  pygls 2.1 can deserialize those JSON-RPC messages during extension startup.
- Preserve Citry attribute-language highlighting when ordinary HTML tags are
  embedded in Python template strings, including Python-valued `c-*`
  attributes and the existing Alpine and Events channels.
- Keep the public formatter surface document-oriented: the document command
  formats every definite Citry section in the current file, while the cursor
  command formats only the containing direct Python literal. Registry-owned
  HTML template files are accepted without claiming unrelated HTML. Embedded
  JavaScript formatting currently needs a provider such as Prettier that
  accepts Citry's non-file virtual documents.

## 0.0.1

- Add Citry template highlighting for standalone templates.
- Highlight `template`, `js`, and `css` multiline strings inside Python files.
- Cover Citry expressions, directive channels, Events bindings, Alpine
  expressions, comments, raw blocks, and nested templates.
