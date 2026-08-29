# Changelog

All notable changes to `citry-lsp` are documented here.

## [0.1.2] - 2026-08-29

### Added

- Load app-discovery environment variables from an optional `envFile`, reread
  the file on registry reload, and report missing or malformed files without
  changing the language server or type analyzer environment.

### Changed

- Pin the supported `ty` analyzer directly so a clean `citry-lsp` install does
  not depend on optional-extra metadata from a separate Citry release.
- Allow 15 seconds for isolated app discovery so cold environments do not
  degrade prematurely while keeping the editor event loop free.

### Fixed

- Keep isolated app discovery responsive on Windows by isolating worker stdin
  from LSP stdio and owning startup, communication, and reaping in one bounded
  background transaction with cancellation-safe cleanup.
- Keep analyzer shadows inside the edited workspace when installed component
  source and the project occupy different Windows drives, and place local i18n
  declarations before their queries so Windows resolves formatter members.
- Recognize the Windows `ty` cache layout when filtering unsafe Python runtime
  members from template completions.

## [0.1.1] - 2026-08-20

### Fixed

- Formatted triple-quoted component assets now keep ordinary quotes and use
  readable, host-relative multiline JavaScript and CSS framing.

### Changed

- Python expression analysis now uses `ty` 0.0.71.

## [0.1.0] - 2026-08-19

### Added

- Analyze inline Python templates, `citry-html` documents, and registered template files with Citry diagnostics, completion, hover, symbols, references, and precise navigation.
- Load a configured `Citry` app or `ComponentLibrary` in an isolated worker for component, input, slot, template-data, and asset knowledge, with an explicit syntax-only fallback when registry discovery is unavailable.
- Use the supported `ty` analyzer for Python expression diagnostics, member and call completion, narrowed hover types, definitions, and signature help.
- Check Alpine expressions, component JavaScript, Events handlers, `$c-props`, `JsData`, and `CssData` against their Python declarations and navigate between them.
- Check Fluent messages and `tr()`, formatter, `<c-trans>`, `$c-tr`, and `i18n.bind()` uses with key, argument, type, completion, hover, and navigation support.
- Format standalone and inline Citry templates through the shared structural formatter, with protocol-v1 requests for document, cursor, JavaScript, and CSS asset formatting.
- Provide protocol v1, conservative HTML projections, responsive cancellation, portable file-URI handling, and formatter registration compatible with VS Code, PyCharm's native LSP client, and LSP4IJ.
