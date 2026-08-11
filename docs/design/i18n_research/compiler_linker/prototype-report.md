# Fluent compiler/linker exploration

Status: the bounded authored-catalog spike passed on 2026-08-10. The
compiler/linker design is viable for the tested subset, but no production
implementation or backend combination is ratified.

The [runner](run_compiler_linker_spike.py), [fixtures](fixtures), and checked
[evidence](evidence.json) are the source of truth.

## Plain-language outcome

Citry can let developers and translators write normal Fluent. A build step can
then turn that source into a safer, unambiguous catalog for the Python,
JavaScript, and Rust runtimes. Authors did not need to write Citry's internal
`CITRY_TEXT`, `SLOT`, or `CITRY_PLURAL` operations themselves.

The generated Czech and English catalogs rendered 19 cases identically in
`fluent.runtime` 0.4.0, `@fluent/bundle` 0.19.1, and `fluent-bundle` 0.16.0.
Those cases cover overrides, references, per-package fallback, message
attributes, exact/cardinal/ordinal selection, formatting calls, and a rich Slot
used twice. The compiler emitted 28 mappings from generated operations back to
their authored files and positions.

## Architectural findings

### Fallback selects a linked graph, not isolated strings

A message and every public message it references must be available in the same
candidate locale. If a Czech wrapper exists but its referenced Czech target is
missing, Citry cannot combine the Czech wrapper with an English target and call
the result one localized message. The spike rejects that Czech graph and
continues to the owning package's English source graph. The selected artifact
then evaluates with English plural rules, formatter defaults, and private-term
scope.

This also confirms that one engine-wide source locale is insufficient. The
library's source fallback was English while the application's source fallback
was Czech, and both resolved correctly in the same engine topology.

### Ownership and precedence are different facts

The application successfully overrode a `citry_ui` message, but the message's
defining owner remained `citry_ui`. Ownership decides the final source locale
and stable input contract. Layer precedence decides which definition wins in a
particular locale. Changing the winner must not silently change ownership.

Message attributes need their own resolution records. In the Czech fixture the
application overrides the visible message value but does not provide its
`aria-label`; the value comes from the application layer while the attribute
falls back to the lower `citry_ui` layer.

### Public messages and private terms need different linking rules

Public message references use ordinary same-locale layer precedence. Private
terms stay in the layer that defined the selected message. Raw Fluent bundles
cannot represent both rules safely when layers reuse IDs, so the linker gives
every selected message output and private term a deterministic internal ID and
rewrites references to those IDs.

The 12-hex-character IDs used by the probe are illustrative. Production needs
a versioned identity scheme, explicit collision detection, and a stable
artifact schema.

### Typed interfaces are transitive

A wrapper that only says `{ my-app-target }` still needs every input required
by `my-app-target`. The spike computes that closure automatically, including
`str` and `Slot` inputs. It rejects a graph where two referenced messages call
the same variable by incompatible Python types, and rejects a translation that
introduces an undeclared variable.

This means an author should declare `@param` metadata at the defining message
that directly consumes the value. A wrapper does not repeat inherited
annotations merely because the referenced message shares its argument map.

### Repeated Slots work with a path rule

The rich-message fixture uses one named Slot twice. Lowering creates one opaque
marker for that filled Slot name and preserves both occurrences, so the later
renderer can invoke the lazy Slot independently at each position. Static
validation requires at least one occurrence on every reachable selector path;
it deliberately sets no maximum. A negative fixture with one selector branch
that omits the required Slot is rejected.

This proves catalog linking and marker preservation. It does not prove the
browser DOM ownership, focus, cleanup, or direction boundary for the two
eventual rendered Slot instances.

### Generated operations and source maps are practical

The probe rewrites displayed scalar inputs to `CITRY_TEXT`, rich inputs to
`SLOT`, cardinal and ordinal selectors to `CITRY_PLURAL`, public
references to linked message IDs, and private terms to layer-local IDs. Named
`NUMBER` calls remain explicit formatter operations. It records both the
authored and generated position for each compiled operation and rejects a
generated operation order that no longer matches those records.

The output was identical when catalog discovery order was reversed. That is a
useful deterministic-build result, not proof that the prototype's Python data
structures are the final artifact compiler.

## Negative results and limits

The executable compiler rejected four important invalid shapes:

- incompatible types inherited through public references;
- a required Slot omitted from one reachable branch;
- a public reference cycle; and
- a translation-introduced variable absent from the source contract.

The probe does not implement every legal Fluent construct. In particular, it
does not settle term arguments, message references inside terms, all selector
forms, nested formatter expressions, decoded bidi validation across the full
linked graph, or a complete diagnostic schema. It uses a Python research
compiler and invokes an isolated Rust executable; it does not prove the real
Rust/PyO3 boundary, integration with Citry's V3 call metadata, or incremental
rebuild performance.

## Decision

Keep the design's compiler/linker architecture. Do not expose the internal
generated functions as authoring API, do not merge raw package catalogs directly,
and do not evaluate an owner-source fallback with the active locale's rules.

The follow-up
[`production_slice` exploration](../production_slice/prototype-report.md) moved
a reduced linked-artifact and diagnostic contract across a real Rust/PyO3
wheel, connected it to current Citry message assets and render hooks, and proved
selective parsed-catalog invalidation plus bounded timings. It also found that
`fluent-syntax`'s successful AST cannot supply operation-level source spans.
Production must now combine this spike's broader operation-generation rules with that
slice's real boundary and a span-preserving parsing route before the backend is
ratified.
