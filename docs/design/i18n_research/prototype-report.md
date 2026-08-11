# I18n source and rich-message spike report

Status: bounded spike passed on 2026-08-10.

The [executable probe](run_catalog_and_rich_message_spike.py),
[fixtures](fixtures/source.ftl), [normal evidence](evidence.json), and
[optimized evidence](evidence-optimized.json) are the source of truth. The
recorded run rebuilt the PyO3 extension first and binds its claims to the exact
path-level input manifest, locked local Cargo dependency closure, clean vendored
Ruff HEAD/tree identity, dependency/tool inventory, and extension digest. The
manifest identifies the tested dirty-tree bytes; it is not a substitute for
committing or archiving them.

## Result

The proposed source declaration and ordinary-component rich-message shape are
feasible against current Citry mechanisms. The spike required no Rust grammar,
AST, compiler, or PyO3 change and added no production dependency.

The normal and `PYTHONOPTIMIZE=1` records both report `PASS_BOUNDED`. The runner
contains no Python `assert` statements, derives the result from measured proof
groups, and proves its always-on failure path with an optimized negative
self-test. Its isolated environment and complete path-to-digest manifest make
dependency or input drift visible before a result can be compared.

Specifically, the run proved:

- `fluent.syntax` exposes message IDs, attributes, selectors, term references,
  attached comments, and character spans. Citry can normalize those spans to
  UTF-8 byte offsets and one-based line/column locations.
- Attached source comments can carry `@param {PythonType} $variable`
  declarations. A small passive Python AST allowlist accepts the intended type
  examples without evaluating or importing code, and pointed validation rejects
  malformed, duplicate, missing, unused, orphaned, and translation-side
  declarations. Duplicate Fluent message IDs also fail instead of replacing an
  earlier definition.
- Citry's existing pair loader already supplies inline dedent, UTF-8 file
  loading, declaration-owner-relative paths, inheritance, explicit clearing,
  and file-index registration for a provisional `messages`/`messages_file`
  pair. Production still has to promote the pair into the public asset surface,
  cache, reset, watcher, checker, and introspection paths.
- The current extension mechanism composes and validates
  `Component.I18n.client_messages`, exposes it as `self.i18n` during render,
  supports child replacement, and restores the extension default after
  `I18n = None`.
- A transparent ordinary Python `<c-trans>` can turn a direct Fluent pattern
  into escaped text/scalar segments plus structural Citry `Slot` segments. A
  translation moved the application-owned terms link before the scalar value;
  the link stayed an `<a>`, while `<Ada>` and hostile catalog text were escaped.
  A translation that omits the required `Slot` fails before rendering, while
  repeated occurrences invoke the repeatable Slot independently.
- The existing V3 parser retains the ordinary `<c-trans>` component,
  `<c-fill>` child, source indices, line/column data, and `contains_fills`
  marker. A special parser node would add no demonstrated value for this SSR
  shape.

## What did not pass yet

The spike's rich evaluator deliberately handles only text plus direct variable
placeables. It rejects the selector fixture. This is not a production Fluent
runtime. The follow-up
[`runtime_backend` comparison](runtime_backend/prototype-report.md) executes one
provisional opaque-marker adapter across three runtimes using hand-generated
selectors, scalar isolation, and allowlisted functions. It covers fresh
markers, collision checks, literal/escaped catalog bidi controls, scalar
paragraph-boundary rejection, and per-paragraph whole-message isolation. It
also confirms that current Fluent terms cannot forward a variable-valued Slot.
Rich-message ratification still depends on compiling authored Fluent with source maps,
concurrent marker tests, wrapperless rich fallback checks, a structural Slot
direction boundary, and browser DOM ownership/state tests.

The run also does not establish locale canonicalization or fallback, plural or
formatter semantics, CLDR and timezone parity, catalog compilation, production
diagnostics, message-asset hot reload, browser artifacts, in-page locale
switching, cache variation, or provider ownership. Those remain the later
Phase 0 spikes in the main design.

The later
[`production_slice` report](production_slice/prototype-report.md) now proves a
reduced catalog compiler/runtime through a real Rust/PyO3 wheel, selective
parsed-catalog invalidation, template `tr()`, `self.i18n.tr()`, and ordinary
`<c-trans>` rendering. It does not change the bounded limits above: the complete
source language, exact wire values, message hot reload, browser ownership,
cache variation, and provider behavior remain open.

The source extractor also handles only a message's direct AST variables and
literal Slot occurrences. It does not prove the design's linker-owned
transitive public-reference interface or repeated Slot ownership across
selectors and nested references. Those are explicit compiler gates rather than
claims of this bounded spike.

## Promotion path

The production-shaped follow-up confirmed that the backend-neutral pieces fit
the real binding and render boundaries. Production can promote only these
parts:

1. Add `messages`/`messages_file` as a real primary asset pair with cached load,
   invalidation, file watching, checking, and introspection.
2. Add the built-in i18n extension's nested config and source-metadata parser,
   retaining the no-eval type grammar and source diagnostics from this probe.
3. Register an ordinary engine-bound `trans` built-in only after a runtime
   backend proves structural rich placeholders across the supported Fluent
   forms.

Do not copy the spike evaluator into production. Its rejection of the selector
fixture is evidence of the exact boundary it was built to test.
