# Changelog

All notable changes to `citry-lsp` are documented here.

## [0.1.0] - Unreleased

### Changed

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

### Added

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
- Require Citry 0.3.2 or newer in the compatible 0.3 series, which supplies
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
