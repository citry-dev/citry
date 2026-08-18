# Changelog

All notable changes to `citry-lsp` are documented here.

## [0.1.0] - Unreleased

### Added

- Analyze inline Python templates, `citry-html` documents, and registered template files with Citry diagnostics, completion, hover, symbols, references, and precise navigation.
- Load a configured `Citry` app or `ComponentLibrary` in an isolated worker for component, input, slot, template-data, and asset knowledge, with an explicit syntax-only fallback when registry discovery is unavailable.
- Use the supported `ty` analyzer for Python expression diagnostics, member and call completion, narrowed hover types, definitions, and signature help.
- Check Alpine expressions, component JavaScript, Events handlers, `$c-props`, `JsData`, and `CssData` against their Python declarations and navigate between them.
- Check Fluent messages and `tr()`, formatter, `<c-trans>`, `$c-tr`, and `i18n.bind()` uses with key, argument, type, completion, hover, and navigation support.
- Format standalone and inline Citry templates through the shared structural formatter, with protocol-v1 requests for document, cursor, JavaScript, and CSS asset formatting.
- Provide protocol v1, conservative HTML projections, responsive cancellation, portable file-URI handling, and formatter registration compatible with VS Code, PyCharm's native LSP client, and LSP4IJ.
