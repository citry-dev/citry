# Design playbook: adding an embedded component language to Citry IDE tooling

**Status (2026-08-11): canonical contributor playbook.** This document is the
implementation checklist for adding or extending editor support for a source
body embedded in a Citry component. It applies to the primary component assets
(`template`, `messages`, `js`, and `css`), their file-backed forms, and smaller
language islands inside those assets. Feature-specific designs still decide
the language semantics; this document decides how those semantics enter
`citry check`, `citry-lsp`, and editor clients without creating a second parser,
an unsafe source map, or a VS Code-only truth.

Read this together with:

- [`ide_integration.md`](ide_integration.md), for the current language-server
  architecture and shipped capability history;
- [`source_languages.md`](source_languages.md), for asset language declaration
  and compiler selection;
- [`template_formatter.md`](template_formatter.md), when the new language is
  formatted;
- [`python_template_expressions.md`](python_template_expressions.md), when the
  feature needs Python type intelligence; and
- the feature design that owns the language contract, such as
  [`i18n.md`](i18n.md) or [`alpinejs.md`](alpinejs.md).

The short rule is:

> Discover authored regions conservatively, parse each language with its
> authoritative parser, retain portable source-bearing facts, and make every
> editor feature a projection of those facts through one exact coordinate map.

---

## 1. What counts as one embedded-language integration

An integration is not complete merely because an editor colors a multiline
string or an LSP handler returns completion. The complete vertical slice has
five independently testable layers:

1. **Authored source ownership:** identify the effective inline or file-backed
   declaration, its component owner, inheritance behavior, and language.
2. **Portable analysis:** parse it once with the language authority and retain
   immutable facts and exact authored ranges usable by batch and editor tools.
3. **Project join:** combine those facts with registry ownership, other source
   units, schemas, call sites, and synchronized open documents without
   importing project code into the long-lived LSP process.
4. **Editor semantics:** diagnostics, completion, hover, navigation, symbols,
   rename, formatting, and provider delegation consume the same joined facts.
5. **Presentation and delivery:** grammar/highlighting artifacts, editor
   activation, status/degradation, diagnostics documentation, tests,
   changelogs, and package boundaries all agree.

The first four layers belong to the implementation even when one editor client
cannot present every capability. A client limitation is documented as a
coverage difference; it does not authorize a second editor-specific semantic
model.

### 1.1 Terms used below

- **Host source:** the physical Python document containing an inline literal.
- **Embedded source:** the decoded language text seen by its parser.
- **Standalone source:** a file whose complete contents are the language body.
- **Source unit:** the smallest language-defined scope for identity, private
  names, and compilation. One Fluent catalog, for example, is a source unit.
- **Portable fact:** an immutable, JSON-safe or language-neutral record whose
  meaning does not depend on VS Code, LSP, or a generated virtual file.
- **Projection:** a synthetic document offered to another analyzer/provider,
  together with a reversible authored-source map.
- **Confidence:** the proof level under which a result is safe: syntax-only,
  registry-backed, complete project index, or external-provider-backed.

---

## 2. Parser and analyzer authority

Choose an authority by the language and question, not by which dependency is
already linked nearby. Ruff and OXC are not general-purpose answers for every
embedded block.

| Question | Authority | What it must not become |
| --- | --- | --- |
| Citry V3 markup, structural scope, template hosts, and expression spans | The Rust Citry parser exposed through `citry_core` | A regex or editor-only markup parser |
| Fluent syntax, message/term identity, variables, selectors, references, comments, and spans | The span-preserving `citry_i18n` Fluent compiler/index | Ruff, OXC, or a second Python Fluent parser |
| Valid Python module/class/literal structure | CPython `ast` plus `tokenize`/the existing lexical recovery for incomplete source | Importing the open module or treating AST byte columns as LSP columns |
| Python expression syntax and parser-owned free-variable metadata in V3 templates | The existing Ruff-backed Python language implementation in the Rust template parser | A separate LSP tokenizer with different name/scope behavior |
| Python expression types, narrowing, member completion, signatures, and semantic diagnostics | The exactly pinned published `ty server` child using Citry shadow documents | Linking Ruff's unpublished internal crates or asking ty to discover Citry regions |
| Conservative Python method-return shapes such as `template_data()` | The shared CPython-AST source analyzer under `citry.analysis` | Executing the method or growing a second Python type checker |
| JavaScript and Alpine syntax, free roots, local bindings, static object shapes, and component initializer facts | OXC through portable `citry.analysis` records | A TypeScript client scan or using OXC to parse Fluent/Python |
| General JavaScript, HTML, and CSS language-service behavior | The installed editor provider, reached only through a bounded mapped projection | Vendoring another complete web-language service into `citry-lsp` |
| Citry-owned CSS/JS cross-language names and provenance | Portable `CssData`/`JsData`/props/events records joined by Citry | Treating a provider's generated-document location as authored source |

When a feature crosses languages, each parser retains its own part. For
example, `self.i18n.tr("account-title")` uses Python structure to identify the
literal call and the Fluent project index to resolve the ID. Neither parser is
asked to approximate the other's syntax.

### 2.1 Parser output is the feature boundary

Before adding LSP handlers, define the portable record that the language
parser/index returns. It should carry only facts the parser can prove, such as:

- stable symbol identity and kind;
- exact UTF-8 byte range in the embedded source;
- definition/reference relationship or an unresolved reference token;
- scope/source-unit identity;
- documentation and declared type metadata;
- dependency edges and index-completeness requirements; and
- explicit open/unknown reasons rather than an optimistic boolean.

Do not serialize editor objects, LSP positions, PSI nodes, open document
instances, analyzer implementation objects, or generated-document ranges into
portable metadata. Convert to LSP coordinates only at the presentation edge.

---

## 3. The implementation pipeline

Every embedded language follows this flow:

```text
Python literal / standalone file
            │
            ▼
conservative region + effective-owner discovery
            │
            ▼
decoded embedded source + reversible source map
            │
            ▼
language-owned parser/index → portable source-bearing facts
            │
            ▼
registry/project join + synchronized open-source validation
            │
            ├──────────────► citry check / compile / inspect
            │
            ▼
Citry LSP feature engines
            │
            ├──────────────► standard LSP answers
            └──────────────► bounded private provider projection, if needed
```

The CLI/checker and LSP join the same portable facts. If live editing requires
additional source, the difference is the source provider—synchronized editor
text versus disk—not a different analyzer.

### 3.1 Stage A: establish the authored asset contract

Write down before implementation:

- inline and file attribute names;
- mutual exclusion and explicit-clear behavior;
- inheritance/effective-owner behavior;
- supported runtime values (`str`, `Path`, or another closed set);
- standalone suffix and LSP language ID;
- source-unit boundaries and private-name scope;
- whether extensions can transform the source;
- whether transformed source has an authored-source map; and
- which dynamic/factory declarations remain runtime-valid but statically
  unprovable.

Use Citry's shared asset loader and ownership model. Do not make the LSP invent
a parallel rule for which inherited source wins. Dynamic declarations may work
at runtime while editor results degrade; that boundary must be explicit.

### 3.2 Stage B: discover regions conservatively

For valid Python, discovery uses the shared Python asset analysis. For an
incomplete file, add recovery only for a shape that can be identified without
guessing its component or literal boundaries. Keep these cases distinct:

- valid direct literal with a complete AST;
- recoverable unfinished direct multiline literal;
- valid but non-contiguous implicit literal join;
- f-string or bytes value;
- computed/dynamic value;
- inherited or file-backed asset; and
- source transformed by an extension.

Only return an interactive region when its source map can round-trip every
range the feature will expose. Syntax coloring may accept a broader lexical
region than navigation or edits, but that distinction must be represented as
confidence, not hidden in a consumer.

The current shared component-asset discovery covers template, JavaScript, and
CSS in `citry.analysis`; a new primary language such as `messages` must either
extend that generic asset model deliberately or add a sibling source record.
Do not append `messages` to a formatter-owned enum accidentally: discovery,
formatting, runtime assets, and LSP regions have related but different closed
sets.

### 3.3 Stage C: build one coordinate adapter

Parser ranges are UTF-8 byte ranges in decoded embedded text. Python AST
columns are UTF-8 byte columns in host source. LSP lines use UTF-16 code units.
These are three coordinate systems, not interchangeable integers.

The source map must support both directions needed by the feature:

- embedded parser range → authored LSP range; and
- authored LSP position → embedded parser byte position.

It must account for:

- quote prefixes and delimiters;
- escape decoding and raw strings;
- host-only indentation/dedent;
- LF, CRLF, and lone CR line endings;
- non-ASCII and non-BMP characters;
- implicit literal concatenation and discontinuities; and
- standalone files, where the mapping is direct but still UTF-8/UTF-16 aware.

Every mapped result verifies that slicing the authored and embedded ranges
still identifies the intended token. Refuse a result when a range crosses an
ambiguous/discontinuous mapping. Never point a diagnostic at the beginning of
an entry merely because the parser did not retain the actual failing span.

### 3.4 Stage D: make project facts portable

The long-lived LSP stdio process must not import project code. Registry loading
stays in `citry_lsp.app_worker`; values crossing that boundary are copied,
validated records. A new language index decides which data belongs in:

- the public component catalog;
- a private, versioned worker envelope keyed by stable definition identity;
- a portable `citry.analysis` API rebuilt from synchronized source; or
- an editor-local cache that is never a project truth.

Prefer public catalog fields only when they are useful to non-editor consumers
and have a durable schema. Use private worker metadata for LSP provenance that
must follow the loaded runtime object but should not expand the public catalog.
Validate worker envelopes strictly and degrade on unknown/malformed records.

The joined project index records its completeness. An unknown symbol is a
diagnostic only when the relevant namespace is authoritative. Startup,
failed discovery, missing package catalogs, or a stale dependent source must
not become a false unknown-name error.

### 3.5 Stage E: synchronize and invalidate

Every answer captures the document/project generation it analyzed. Before
returning or publishing, verify that the generation still matches. An open
document's synchronized text wins over disk for facts Citry can rebuild
soundly. If an external analyzer still resolves an imported module from disk,
withhold the affected result while that dependency has unsaved changes.

Index invalidation follows language dependency edges. Editing a Fluent term,
for example, invalidates messages that reference it and call sites whose
transitive parameter interface changes; it should not rebuild every unrelated
component if the graph proves the smaller set. When dependency completeness is
unknown, retain the conservative broader refresh.

---

## 4. Capability checklist

Implement each capability from symbol identity and parser context. Do not
infer context by inspecting Markdown produced by another handler.

### 4.1 Syntax highlighting

Highlighting and semantics are separate deliverables.

- Add the standalone grammar/file mapping.
- Add the Python injection rule for the exact component attribute.
- Reuse the shared syntax fixture taxonomy and validate token scopes.
- Test raw/unicode prefixes, ordinary/triple quotes, indentation, incomplete
  literals, false lookalikes, and adjacent component attributes.
- Decide whether semantic tokens add symbol-aware coloring; they never replace
  the base grammar in clients that do not support them.

A TextMate injection may conservatively color a region that the semantic
engine declines. It must not claim runtime ownership or provide diagnostics.

### 4.2 Diagnostics

Citry-owned diagnostic codes, messages, trigger conditions, severities,
examples, surfaces, and documentation URLs originate in
`packages/protocol/diagnostics/v1/catalog.json`. Run the generator after
changing it; product code imports generated constants instead of repeating
strings.

Diagnostics must be shared with `citry check` whenever the finding is not
intrinsically editor-only. Map the parser's exact authored span, publish only
for the current document generation, and clear a finding when the source is
fixed. If the project namespace is incomplete, publish syntax/local findings
but defer completeness-dependent unknown-name findings.

### 4.3 Completion

Define completion by syntactic position, scope, and confidence:

- symbol definition versus reference;
- name, attribute, argument, option, profile, or value position;
- private/source-unit scope versus project-global scope;
- prefix replacement range and insert range;
- snippets versus plain text; and
- whether a partial token or empty value remains a valid context.

The server returns exact `InsertReplaceEdit` ranges and marks lists incomplete
when typing should re-filter/requery. The editor client must also cause the
first request to happen: identifier characters are usually not global LSP
trigger characters, so embedded-language activation may need a narrow lexical
retrigger. Test empty strings, first character, no-space operator boundaries,
deletion, Unicode identifiers, comments, quoted text, and incomplete syntax.

### 4.4 Hover

Hover uses a structured internal symbol/context record, then one renderer.
Prefer the host language's familiar declaration shape for types, followed by
Citry provenance and a link to the relevant public documentation. Do not parse
or concatenate another provider's arbitrary Markdown without validating its
shape. A provider answer unavailable for one shared consumer/path means the
composed type is withheld or falls back to a proven declared type; never show a
partial type as complete.

### 4.5 Definition, Declaration, Type Definition, and References

Name these relationships before implementing them:

- **Definition:** the authored value/symbol that supplies this reference.
- **Declaration:** the authored contract introduction; often the same location
  as Definition for Citry-owned symbols.
- **Type Definition:** the actual declared value type, never the value
  declaration used as a fallback.
- **References:** occurrences resolving to the same exact symbol identity, not
  every matching spelling.

Return multiple locations when a shared asset has several exact origins.
Deduplicate and source-order results. `includeDeclaration` adds declarations
only when they are proven. Lexical bindings with the same spelling in sibling
scopes remain distinct. A generated virtual-document target must map through a
complete source copy or be rejected.

### 4.6 Rename

Rename is stricter than References. It requires a complete affected-symbol
graph, exact editable ranges, collision validation in every destination scope,
and one atomic `WorkspaceEdit`. Do not implement rename by applying a spelling
search to the reference list. Define behavior for translated/overridden
definitions, private names, generated artifacts, read-only package sources,
and partially indexed workspaces before advertising the capability.

### 4.7 Symbols, signature help, formatting, and code actions

- Document symbols come from parser-owned definitions and preserve hierarchy.
- Signature help uses a typed callable/interface record and exact active
  argument position; it does not parse hover text.
- Formatting is a separately versioned rewrite contract with suppression,
  idempotence, semantic-equivalence checks, and provider bounds. Adding a
  language region does not automatically make it formatter-owned.
- Code actions edit only authored ranges and state the diagnostic or source
  fact that makes the edit safe.

---

## 5. Direct Citry answers versus editor-provider delegation

Citry directly answers facts it owns: component data, schemas, message IDs,
event handlers, lexical bindings, source-unit symbols, exact Python/Fluent
provenance, and stable diagnostics. It delegates general HTML, JavaScript, and
CSS behavior to the installed editor provider.

A delegated projection needs:

1. a cheap client-side filter that only decides whether to ask;
2. parser-backed server eligibility;
3. a stable virtual-document identity;
4. exact authored and virtual ranges;
5. current document/project versions in the request/cache key;
6. bounded waits and propagated cancellation;
7. validation that every returned edit/range stays inside mapped source; and
8. rejection of commands, imports, or generated-document navigation that
   cannot be mapped safely.

Cache a successful projection by the deepest containing source region, not by
an overly broad outer host or an exact cursor only. Do not cache a null answer
for a region if another position inside it may be valid. Invalidate caches when
the project registry generation changes, not only when the text document
changes.

Prefer a standard LSP capability when it expresses the complete result. Add a
private client request only when a client must invoke a host provider or carry
data standard LSP cannot represent. An additive private request does not by
itself require a protocol-version bump; an incompatible wire-shape change does.

---

## 6. Performance and lifecycle contract

Interactive work must not queue behind broad background work.

- Parse/discover once per document revision and cache immutable region facts.
- Join owner/schema/source context once per region or consumer generation, not
  once per expression/reference.
- Batch compatible diagnostics requests while preserving exact source maps.
- Debounce background diagnostics and file-watcher reload bursts.
- Let completion, hover, and navigation preempt background analyzer work.
- Run blocking project discovery off the event loop.
- Preserve one analyzer child across catalog-only reloads when its interpreter
  and workspace do not change.
- On cancellation, consume/clean late protocol responses and retain ownership
  of every child until it is reaped.
- Give custom requests, virtual-document readiness, and delegated providers
  explicit deadlines so the editor never shows an unbounded `Loading...`.

Add opt-in stage timings for client routing, projection, virtual-document
refresh, provider execution, source mapping, and total latency. Benchmark the
decision-relevant warm and cold path in a clean editor host. Pure parser timing
does not prove end-to-end provider latency.

---

## 7. Confidence and degradation matrix

Each feature records the minimum proof it needs.

| State | Allowed behavior |
| --- | --- |
| Definite local region, no registry | Syntax highlighting, local parsing, local syntax diagnostics, local symbols that need no project namespace |
| Registry ready, source ownership current | Component/source-specific completion, hover, diagnostics, and navigation |
| Complete language project index | Unknown global-symbol diagnostics, cross-unit references, rename, duplicate/global consistency findings |
| External analyzer/provider healthy and mapped | General Python/HTML/JS/CSS semantic answers inside exact projection ranges |
| Invalid current parse with exact narrow recovery | Only recovery-safe coloring/context; no stale ranges moved onto changed source |
| Ambiguous owner, stale dependency, incomplete index, malformed worker record, or unmappable provider answer | No speculative result; retain independent lower-confidence features |

Syntax-only mode is a product mode, not an error path. Registry failure is
reported clearly and does not let partial runtime names leak into a supposedly
complete namespace.

---

## 8. Required test matrix

New language work adds focused tests at every layer it touches.

### 8.1 Source and coordinates

- inline triple-quoted and ordinary literal;
- raw and unicode prefixes;
- single and double quotes;
- host indentation and blank leading/trailing lines;
- LF and CRLF;
- non-ASCII whitespace, composed/decomposed text, and astral UTF-16 positions;
- escapes whose decoded length differs from host text;
- implicit/split literals, f-strings, bytes, and dynamic values (accept or
  explicitly decline);
- unfinished host source and last-good recovery; and
- standalone file plus inherited/shared asset ownership.

### 8.2 Language semantics

- every supported definition/reference/scope shape;
- incomplete tokens at every completion boundary;
- comments, strings, raw bodies, and lookalikes that must not trigger;
- duplicate, ambiguous, private, shadowed, and canonically equivalent names;
- invalid source with exact diagnostic ranges; and
- unsupported syntax producing no partial semantic claim.

### 8.3 Project and editor behavior

- syntax-only and registry modes;
- app import failure and incomplete index;
- synchronized unsaved inline and external source;
- edit/open/close during project reload;
- multiple consumers and multiple exact definitions;
- completion, hover, Definition, Declaration, Type Definition, References,
  rename (if shipped), symbols, formatting, and diagnostics through real stdio;
- client activation on the first identifier character;
- stale generation and cancellation during each async operation;
- external provider timeout/malformed answer/unmappable edit;
- multi-root ownership and unrelated files not claimed; and
- repeated restart/reload/cancellation leaving one LSP and at most one owned
  analyzer child per workspace.

### 8.4 Cross-surface parity

- the same portable analyzer fixture passes in `citry check` and the LSP;
- parser inventories, TextMate scopes, and shared syntax fixtures agree;
- diagnostic codes/messages are generated from the catalog;
- runtime/catalog/worker/source identities join one-to-one; and
- public docs examples use syntax that the parser and checker accept.

Observe parser/compiler output before locking exact AST, source-map, or
generated-document assertions. Do not calculate byte/UTF-16 offsets by hand.

---

## 9. Package and release checklist

Before declaring the integration complete, audit all applicable owners:

- language/parser crate and its tests;
- PyO3 registration, `_rust.pyi`, Python wrapper, and cross-binding audit when
  Rust metadata crosses into Python;
- portable `citry.analysis` records and checker;
- runtime asset loading, inheritance, reload/watch, and catalog provenance;
- app-worker/private metadata validation;
- `citry-lsp` regions, project state, engine, server capabilities, README,
  tests, version constraints, and changelog;
- diagnostics catalog plus generated Python/Rust/TypeScript bindings and public
  diagnostic docs;
- VS Code grammar, language IDs/file associations, activation/retrigger,
  projection client, tests, README, changelog, and rebuilt VSIX;
- LSP4IJ/other editor coverage when the feature uses only standard LSP;
- feature design, this playbook if a reusable fact changed, user docs, and
  executable examples; and
- lockfiles/package dependencies when a parser or provider is newly shipped.

Keep product protocol/schema versions at `1` while their owning package is
pre-1.0.0. Change every producer, consumer, fixture, test, and current doc
together for an in-place breaking correction. Do not bump the public component
catalog merely to carry private LSP provenance.

---

## 10. Applying the playbook to `Component.messages` and Fluent

[`i18n.md`](i18n.md) owns Fluent semantics and its Phase 6 feature list. This
section records how that plan enters the existing IDE architecture.

### 10.1 Authored surfaces

The index covers:

- inline `Component.messages`;
- component `messages_file` source-locale files;
- configured/package-owned standalone Fluent source units and their translated
  locale files;
- Python calls such as `self.i18n.tr(...)`, `resolve(...)`, and named formatter
  calls;
- template `tr(...)`, `fmt.*(...)`, and `<c-trans>` values/fills;
- `Component.I18n.client_messages`; and
- statically supported JavaScript/client message references.

Inline/file declaration precedence, inheritance, loading, package resources,
and watcher identity come from Citry's existing message asset runtime. The LSP
must not implement a fourth rule for which source catalog belongs to a
component.

### 10.2 Parser responsibilities

The span-preserving `citry_i18n` parser/compiler is authoritative for:

- public message IDs and attributes;
- private terms and source-unit scope;
- variables, selectors, variants, functions, and options;
- direct and transitive message/term references;
- attached comments and `@param` type/description declarations;
- definition/reference/parameter spans;
- source-locale ownership, layer/precedence, and translated definitions; and
- the complete/incomplete project graph.

Python AST or existing Ruff-backed literal-call metadata identifies supported
Python call sites. The Citry V3 AST identifies template call sites and
`<c-trans>` structure. OXC identifies only supported JavaScript call sites.
None of those reparses Fluent source or decides Fluent name resolution.

### 10.3 Portable index records

Before LSP handlers, expose or reuse immutable records for:

- source-unit identity, owner, locale, layer, path, content revision, and
  completeness;
- each message/attribute/term definition and exact authored range;
- direct and transitive parameter interface, type, description, declaration
  range, and origin path;
- resolved and unresolved references with exact scope;
- named formatter profiles and accepted value types;
- every supported Python/template/JavaScript call-site reference and argument
  range; and
- dependency edges needed for incremental invalidation.

Do not make the LSP scrape the compiled manifest JSON when the in-memory
compiler/index already owns a richer typed record. If the app worker must copy
loaded package/owner identity, validate that private envelope independently;
rebuild edited Fluent/Python facts from synchronized source.

### 10.4 Feature behavior

**Highlighting** covers Fluent messages, terms, attributes, variables,
placeables, selectors, variants, functions, comments, and `@param` metadata in
both inline `messages` and standalone Fluent files. The VS Code Python
injection must match the runtime attribute exactly and reject lookalike strings.

**Completion** includes context-appropriate public IDs/attributes at `tr`,
`<c-trans>`, `client_messages`, and supported client call sites; private terms
and public references inside Fluent according to source-unit scope; variables
from the effective transitive interface; formatter functions/options; and
configured profile names. Empty and first-character positions must trigger.

**Hover** shows the message/attribute or parameter contract, translator-facing
description, source owner/locale where useful, Python type, and a public-doc
link. It must distinguish a source definition from a selected translated
definition and must not imply that a fallback text is the authored call-site
contract.

**Definition/Declaration** takes a literal use to the effective source
definition or parameter declaration specified by the i18n design. **Type
Definition** follows a typed parameter to its Python type only when the type
resolver has an exact target. **References** uses canonical message/output
identity across Fluent, Python, templates, and supported JavaScript without
including same-spelled private terms from another source unit.

**Rename**, when added, is project-index-complete only. A public message rename
must account for source and translated definitions, public references, all
supported call sites, generated-artifact policy, collisions, and read-only
package sources. A private term rename stays inside its defining source unit.
Until that complete atomic edit is proven, ship References without Rename.

**Diagnostics** reuse the i18n compiler/checker findings and the central
diagnostic catalog. Unknown messages/attributes/profiles are deferred while the
relevant project index is incomplete. Duplicate IDs report both definitions;
wrong/missing arguments cite the call and parameter declaration; source-map or
revision mismatch produces no guessed location.

**Symbols** expose messages with nested attributes and optionally private terms
as language-appropriate symbols. **Formatting** is a separate Fluent decision;
syntax highlighting and semantic indexing do not silently opt the source into
the component formatter.

### 10.5 Incremental and failure behavior

- Editing one Fluent unit reparses that unit and invalidates its reverse
  reference dependants and affected call interfaces.
- Editing `@param` metadata invalidates completion, hover, signatures,
  diagnostics, and browser/client eligibility that depend on the type.
- Package discovery/indexing marks the graph incomplete until every configured
  manifest/source needed for global absence is known.
- Invalid current Fluent source retains independent coloring and local parser
  diagnostics, but does not move last-good symbol ranges onto new text.
- A stale compiled manifest never overrides synchronized authored source.
- Translation/source-locale changes and fallback graph changes advance the
  project generation and invalidate affected caches.

### 10.6 Fluent acceptance matrix

At minimum, test:

- inline and file-backed source-locale catalogs;
- translated package files and precedence/override layers;
- messages, attributes, private terms, variables, selectors, variants,
  functions/options, comments, and `@param` metadata;
- direct/transitive public references and private-term isolation;
- duplicate IDs, cycles, missing references, missing/wrong parameter types,
  wrong call arguments, and incomplete-index deferral;
- literal calls in Python, template expressions, `<c-trans>`,
  `client_messages`, and supported JavaScript;
- definition/reference navigation in both directions across all those surfaces;
- unsaved Python plus Fluent edits, dependency invalidation, and stale compiled
  artifacts;
- inline dedent/escape/source maps, standalone CRLF, Unicode IDs/content, and
  astral text before/after target spans;
- empty/partial completion, rename collisions if Rename ships, and generated
  locations never escaping; and
- checker/LSP identical diagnostic code, message variant, severity, and source
  range for the same fixture.

### 10.7 Likely implementation owners

The Fluent vertical slice should expect coordinated changes in:

- `crates/citry_i18n/` for source-bearing index records and compiler facts;
- `crates/citry_core_py/` and `packages/py/citry_core/` if those records cross
  the Rust/Python boundary;
- `packages/py/citry/` for portable analysis, checking, asset ownership, and
  app-worker-safe snapshots;
- `packages/py/citry_lsp/citry_lsp/regions.py`, `project.py`, `engine.py`, and
  `server.py` for live documents and standard LSP capabilities;
- `packages/editors/vscode/` for Fluent grammar injection, activation, client
  routing, tests, and packaging;
- `packages/protocol/diagnostics/v1/` for stable Citry-owned findings; and
- i18n, IDE, diagnostics, and editor user documentation.

The exact list follows the final portable-record design. Do not start by adding
an LSP-only dictionary of messages or by teaching TypeScript to scan Fluent.

---

## 11. Anti-patterns this playbook forbids

- Adding coloring and calling the language integration complete.
- Adding one LSP handler before defining parser-owned identity and ranges.
- Parsing a language with Ruff or OXC merely because it is already vendored.
- Importing the user's open project in the LSP stdio process.
- Treating a runtime catalog snapshot as current after synchronized source
  changes without revalidation.
- Comparing names by spelling when lexical/source-unit identity exists.
- Converting UTF-8 bytes directly to LSP character columns.
- Publishing a partial answer from only the consumers/return paths/providers
  that succeeded.
- Returning a virtual/generated file as a user-facing definition.
- Letting an editor client become the only implementation of a diagnostic that
  also belongs in `citry check`.
- Repeating diagnostic IDs or prose outside the diagnostic catalog.
- Restarting analyzers or reloading the complete project for every keystroke.
- Expanding a public protocol/catalog schema for private provenance without a
  demonstrated external consumer.
- Claiming another editor supports a private VS Code provider bridge merely
  because it can attach to the standard LSP server.

---

## 12. Definition of done

An embedded-language IDE slice is done when:

1. the runtime/checker and LSP consume one parser-owned portable fact model;
2. inline and standalone coordinates are round-trip tested;
3. every shipped capability has explicit context, confidence, stale-result,
   and failure behavior;
4. syntax highlighting, standard LSP semantics, and any private provider bridge
   are documented as separate coverage claims;
5. the central diagnostic catalog and public diagnostic docs own every new
   Citry finding;
6. focused unit, cross-surface, real-stdio, client, and lifecycle tests cover
   the acceptance matrix;
7. performance is measured at the user-visible request boundary and no child or
   virtual document leaks after cancellation/restart; and
8. package READMEs, changelogs, design docs, public docs, built editor artifact,
   and version constraints describe the same released behavior.

If any item is intentionally deferred, name it as a coverage limitation and
leave a tracked reopening condition. Do not let an omitted layer hide behind
the phrase "IDE support."
