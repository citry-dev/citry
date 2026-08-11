# Changelog

## 0.1.0 - Unreleased

- Require VS Code 1.101.0 or newer. That release is the first to embed Node 22,
  which the extension bundle now targets.

- Add one `citry-lsp` client per workspace folder, using that folder's selected
  Python environment and optional `citry.app` setting.
- Surface registry, syntax-only, interpreter, app, and protocol status with
  restart and status commands.
- Serialize overlapping restart requests so changing the selected app or
  interpreter cannot leave duplicate language-server clients and repeated
  hover results alive in one workspace.
- Keep the Python extension optional so compatible editor forks can use an
  explicitly configured `citry.python` executable.
- Add parser and registry diagnostics, completion, hover, navigation, and
  document symbols through the companion language server.
- Delegate Alpine expressions and registry-owned component JavaScript to VS
  Code's JavaScript provider through stable, version-bound virtual documents
  while retaining Citry's exact Python-backed `JsData`, Events State, props, and
  server-event hover and navigation. Citry also reports unknown Alpine roots,
  reports free `$component` initializer names, types and navigates `x-for`
  bindings and synchronous `$component` scope writes, completes server-handler
  string arguments, shows linked Citry browser-API hover help, and validates
  static `$c-props` objects against the child component. Registry-backed
  browser regions use one warmed JavaScript provider path, so generated
  `document.js` targets and duplicate provider work do not leak into authored
  navigation.
- Activate the workspace language-server client for CSS files so resolved
  component `css_file` assets receive `CssData` completion, hover, Definition,
  Declaration, and References alongside VS Code's ordinary CSS provider.
- Surface the application's shared unknown-template-variable lint policy,
  including runtime globals, lint-only variable completion and hover, and
  warning/error severity without adding a VS Code-only preference. Direct
  application and component lint-variable mappings also support Definition and
  Declaration navigation through the language server.
- Route References, Declaration, and Type Definition through the owning
  workspace client for proven template variables, and document the Pylance
  setting that keeps template literals from being changed into f-strings.
- Reuse VS Code's HTML, CSS, and JavaScript providers for completion, hover,
  and definitions inside exact Citry asset strings and standalone Citry
  templates, with no app configuration required.
- Add PascalCase component suggestions, precise component-class navigation,
  and typed slot-data completion and hover through `citry-lsp`.
- Add syntax-only structural-tag and Citry directive snippets, lexical
  `c-for`/`c-fill` completion and hover, and exact component-input and static
  fill-slot definitions when the catalog provides unambiguous authoring
  provenance.
- Show linked first-party Citry documentation when hovering structural tags,
  fixed directives, and structural attributes, including in syntax-only mode.
- Add conservative `TemplateData` root completion, hover, and exact annotated
  field navigation for proven component templates, intersecting shared and
  inherited consumers instead of guessing from one component.
- Add Python member/call completion, type hover, user-member navigation,
  signature help, and mapped expression diagnostics from the language
  server's pinned analyzer. This covers declared and inferred roots,
  narrowing, loop scope, nested templates, and synchronized Python edits.
- Match ordinary Python hover readability for template variables with a
  highlighted `(variable) name: type` declaration plus Citry provenance,
  including narrowed, inferred, loop, fill, and shared-template types.
- Reopen Citry tag suggestions after backspacing or undoing an incorrect
  partial tag name and then continuing the corrected name.
- Open root and structural-value suggestions when an identifier starts
  directly after an expression delimiter, attribute quote, or operator, with
  the same deletion and undo recovery as tag completion. This stays scoped to
  Citry hosts instead of registering every identifier character as a global
  Python completion trigger.
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
- Preserve installed HTML-provider hover documentation and links for direct
  dynamic native attributes such as `c-class`, with exact source-range mapping
  and conservative exclusion of Citry tags, directives, nested templates,
  comments, expressions, end tags, and raw-text bodies.
- Forward HTML completion, hover, and definitions through parser-proven nested
  template fragments. Forward `<c-element>` attributes through a statically
  selected native tag when exact, or a global-attribute-only custom element
  when the target is dynamic, while preserving exact mapped edits and native
  dynamic-attribute hover ranges.
- Keep nested-template, `<c-element>`, Alpine, and embedded-provider requests
  responsive with lexical routing, cancellable projection requests, bounded
  provider waits, stable virtual documents, region-level HTML projection
  reuse, and coalesced Python file notifications. Optional structured stage
  timings are available in the Citry Performance output channel.
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
