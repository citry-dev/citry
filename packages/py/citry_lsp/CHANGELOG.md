# Changelog

All notable changes to `citry-lsp` are documented here.

## [0.1.0] - Unreleased

### Changed

- Keep editor requests responsive during project discovery by loading through
  an asynchronous, cancellation-safe worker. Python-file bursts now debounce
  into serialized latest-wins registry reloads, catalog refreshes preserve the
  incremental `ty` process, and stale semantic diagnostics are cancelled
  before they can delay interactive completion or hover. Analyzer shutdown and
  late cancelled responses retain bounded child ownership instead of leaving
  language-server or `ty` processes behind.
- Reuse immutable class-resolution fingerprints across the app worker's data
  and asset channels, keeping large component-library registries within the
  bounded startup window without weakening source-provenance checks.
- Use concise catalog-backed template diagnostic messages, rename the
  unreleased unknown-component code to `citry.template.unknown-component`, and
  attach canonical help links while retaining `citry` as the diagnostic source.
- Present declared, source-inferred, loop, and fill variables as
  Python-highlighted declarations on hover, using the analyzer's narrowed type
  while retaining Citry provenance and safe catalog fallbacks.
- Keep member completion useful for direct optional roots by offering the
  non-`None` member surface without weakening hover or diagnostics, and retain
  completion and signature help while repairing incomplete `cond` and `each`
  expressions in explicit or shorthand structural hosts.
- Keep root completion independent of surrounding whitespace while declining
  root-only suggestions inside Python strings, comments, numeric literals, and
  mapping string keys. Complete f-string replacement expressions remain
  eligible on every supported Python version.
- Match the runtime casing contract: only an exact lowercase `c-` prefix is
  component syntax, suffix lookup stays case-insensitive, and component kwarg
  and slot names remain case-sensitive in completion and hover.
- Filter and rank registered component completion on the server across class,
  normalized, and alias spellings, including separator-insensitive partial
  matches such as `c-cfo` to `c-CForm` while preserving exact aliases.
- Allow explicit custom formatting requests for registry-proven HTML
  `template_file` documents without registering Citry as an ordinary HTML
  formatter.
- Preserve the complete catalog-v1 component, schema, asset, extension, and
  envelope records in the server instead of projecting only kwargs, slots,
  and template paths.

### Fixed

- Register standalone formatting with the portable language-only selector that
  PyCharm's native LSP client, LSP4IJ, and VS Code all accept, without exposing
  the Citry formatter on ordinary Python files in LSP4IJ.
- Convert editor file URIs through one platform-aware path resolver, so
  Windows drive-letter and UNC workspaces retain registry-backed completion,
  hover, navigation, synchronized Python sources, and formatting.

### Added

- Treat registered component message assets as an available source catalog
  even when the application has no explicit i18n settings, so source-mode
  `tr()` calls retain diagnostics, hover, completion, and navigation.
- Add live i18n diagnostics and navigation. Component `messages` blocks now
  use the checked Rust Fluent analyzer for malformed or unsupported `@param`
  declarations, including exact source ranges. Literal `tr()`, formatter,
  parser, and `<c-trans>` calls report unknown keys and profiles, missing or
  extra arguments, proven type mismatches, and fill/value contract mistakes.
  Translation argument names hover with their compiler-checked `@param` type
  and description and navigate to the exact declaration across component and
  file owners. Template formatter methods now expose uniform signatures and
  reject misspelled operations or profiles, including multiline calls.
  Template `fmt` methods expose completion and signatures, browser `$i18n`
  and component-context `i18n` expose their nested APIs, component input
  completion includes static and `c-` spellings, and private Fluent term
  references navigate within their own source unit.
- Recognize checked `$c-tr` directive names and Alpine named-value objects.
  Message and Fluent-attribute segments hover and navigate to the exact catalog
  output, malformed owned spellings are errors, and statically proven keys and
  JavaScript value types are checked against the message interface. Literal
  `i18n.bind()` message and output fields share the same navigation.
- Publish the same version-pinned Alpine CSP compatibility findings as
  `citry check`, using the selected app's configured `security_csp` mode and
  exact template ranges. Syntax-only projects do not infer a security policy.
- Add a parser-backed, version-bound HTML-provider projection for nested
  templates and `<c-element>` attributes. Literal element targets preserve
  tag-specific assistance, dynamic targets preserve only global attributes,
  and uncertain or non-linear source mappings fail closed.
- Add registry-backed Alpine and component-JavaScript intelligence. Declared
  or conservatively inferred `JsData` roots now complete, hover, navigate, and
  receive JSON-derived JavaScript types; `$component` data, scope, static
  props, public Events State, Alpine `x-for` bindings, synchronous scope writes,
  and literal server-event names use the same synchronized Python provenance.
  Unknown Alpine roots are errors by default; declarative `@c-*`, `$loading()`,
  and `$error()` handler names share event diagnostics and navigation. Static
  `$c-props` objects validate child keys, required props, and proven value
  types, with exact navigation to the child JavaScript declaration.
  Unsupported JSON types warn and shared assets retain only facts proven for
  every owner. Direct values read from an inferred `js_data()` method's kwargs
  parameter use the effective `Kwargs` field annotation instead of degrading
  to `unknown`. Free `$component` initializer names are errors by default and
  can use typed application or component globals. Citry browser APIs show
  linked first-party hover help, and server-handler string arguments complete
  from empty or partial values.
- Join registry-owned inline and file-backed component CSS to declared
  `CssData` fields and conservative literal keys inferred from `css_data()`.
  Exact `var(--name)` uses now receive completion, hover, Definition,
  Declaration, and same-stylesheet References while shared assets and
  synchronized Python edits retain conservative ownership checks. Arbitrary
  custom properties remain open-world and do not produce Citry diagnostics.
- Add registry-backed unknown-template-variable diagnostics through Citry's
  shared lint policy. Runtime globals, application/component lint metadata,
  extension contributions, declared schemas, inferred roots, and synchronized
  source participate in the same namespace used by `citry check`. Explicit
  extra-preserving schemas cap findings at warning, while syntax-only files do
  not guess ownership. Known global and lint-only roots also complete, hover,
  and use their conservative types for Python member intelligence.
- Navigate application and component lint-only variables to exact direct
  `template_variables` dictionary keys, while declining dynamic, stale, or
  ambiguous settings construction.
- Add same-template references and declaration navigation for proven roots and
  exact loop/fill bindings. Type Definition now follows those variables to
  their actual Python or standard-library types when every mapped consumer and
  return path has a safe answer, including neutral `Any` targets for unused
  fill bindings. Synchronized component inheritance and template ownership are
  revalidated before registry-backed variable results are served. Direct
  literal and `pathlib.Path(...)` declarations receive exact freshness checks;
  dynamic or imported asset selection fails closed while Python source is
  synchronized.
- Add type-aware Python template expressions through a pinned `ty` child from
  the selected project environment. Proven roots now receive member and call
  completion, hover, user-member navigation, signature help, and source-mapped
  diagnostics across interpolations, Python-valued attributes, loop clauses,
  narrowing, nested templates, inferred return paths, and shared consumers.
  Unknown-root policy remains deferred, analyzer failures degrade once to the
  existing parser and root features, and sandboxed members are filtered.
- Infer conservative template roots from statically resolvable
  `template_data()` source when no `TemplateData` schema is declared. Direct
  dict keys, modelled aliases, mutations, branches, and unpacks now provide
  completion, hover, and exact key navigation from synchronized Python text;
  the inherited `return kwargs` implementation reuses effective `Kwargs`
  fields and their types without treating a typed `Kwargs` carrier as a dict.
  Ambiguous, stale, or unsupported shapes withhold claims, and shared templates
  retain only roots proven for every consumer.
- Add syntax-only first-party hover documentation and canonical Citry guide
  links for every parser-owned structural tag, fixed directive, and contextual
  structural attribute. Exact source ranges cover standalone, nested, and
  inline Python templates without requiring a registry or HTML provider.
- Accept a `ComponentLibrary` as the configured registry target. The server
  materializes it with Citry's built-ins in an isolated registry, reports the
  library-only scope in project status, and directs libraries requiring
  host-provided extensions to expose a configured `Citry` instance.
- Add parser and registry-backed diagnostics for conservative inline Python
  template regions, explicit `citry-html` documents, and registry-resolved
  associated template files.
- Isolate app import and discovery in a bounded subprocess, with explicit
  syntax-only degradation and project status reporting.
- Add component, attribute, slot, and typed slot-data completion; catalog
  hover with exposed slot-data shapes; lexical loop and fill navigation;
  precise component-class navigation with safe file fallback; and document
  symbols.
- Offer valid PascalCase component spellings alongside registered lowercase
  spellings, ranking the form that matches the user's typed casing first.
- Expose a versioned LSP/client protocol and refuse incompatible clients.
- Add protocol v1 with workspace-scoped dynamic `citry-html` document
  formatting and the versioned `citry/formatTemplates` request for
  document-wide or cursor-scoped Python template formatting. Clients can keep
  the standard provider disabled when they own multi-root routing.
- Serve the same structural formatter bytes as the Rust and Python APIs for
  standalone templates and safe embedded Python template rewrites.
- Serve the built-in Python expression formatting bytes and report its
  pinned provider identity in additive protocol-v1 project status.
- Add the protocol-v1 `citry/formatComponentAssets` request and negotiated
  `citry/formatEmbedded` client callback for atomic template, JavaScript, and
  CSS formatting. Embedded results are bound to the synchronized document and
  plan identities, while unavailable providers leave their regions unchanged
  with explicit notices. Client callbacks are cancelled after a bounded wait
  using their exact JSON-RPC request ID, and malformed status or forged
  provider-identity payloads are refused without an edit.
- Report the active embedded-language selection mechanism without claiming a
  provider identity or version that the client cannot prove.
- Require Citry 0.4.0 or newer in the compatible 0.4 series, which supplies
  the portable analysis and source-coordinate contracts used by the server.
- Add schema-free structural-tag and directive-attribute snippets plus lexical
  completion and hover for `c-for` and `c-fill` bindings, including shorthand
  loops, aliases, rest/fallback names, nested templates, and incomplete active
  expressions.
- Add exact component-input and static fill-slot go-to-definition through
  conservative per-field Python source provenance; ambiguous and generated
  declarations return no target.
- Add `TemplateData` root completion, hover, and exact field definitions for
  AST-proven inline templates and registry-owned files. Shared and inherited
  templates expose only identical fields common to every effective consumer;
  structured asset-owner provenance also covers unregistered declaring bases.
  Open namespaces and ambiguous ownership produce no unknown-root diagnostic
  or guessed schema result, and member positions do not receive root-only
  suggestions.
- Keep expression completion live from an empty value through partial typing,
  return every applicable lexical and `TemplateData` root with explicit fuzzy
  filtering metadata, and replace the exact identifier around the cursor using
  source-mapped UTF-16 edit ranges.
- Replace the complete partial tag name during structural and registered
  component completion. Structural start tags add their primary syntax, such
  as `<c-for each="">`, with the cursor in the value; closing-tag completion
  remains a bare name. Completion also stays live while the tag name changes.
- Replace complete directive, structural-attribute, and component-input names
  with source-mapped atomic completion edits. Existing assignments and values
  are preserved, while names and quotes inside values or comments do not affect
  duplicate suppression or completion context.
