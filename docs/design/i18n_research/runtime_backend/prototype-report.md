# Fluent runtime comparison report

Status: bounded runtime comparison passed on 2026-08-10. No production backend,
catalog linker, or rich-message protocol is ratified.

The [runner](run_runtime_backend_spike.py), [fixtures](fixtures), and checked
[evidence](evidence.json) are the source of truth.

## Result

The same hand-generated runtime fixtures produced identical normalized output through
`fluent.runtime` 0.4.0, `@fluent/bundle` 0.19.1, and `fluent-bundle` 0.16.0 for:

- message values, attributes, private terms, and literal term parameters;
- English and Czech exact, cardinal, and ordinal branches, including Czech
  fractional `many` and signed negative zero matching exact zero;
- explicit Citry-owned `NUMBER`, `DATETIME`, `CITRY_PLURAL`, and `CITRY_TEXT`
  operations;
- one illustrative already-generated public reference with two distinct internal
  private-term IDs; and
- a rich placeholder reordered by the Czech translation.

The runner uses always-on checks, derives its parity result from the candidate
outputs, and passes with both normal Python and `PYTHONOPTIMIZE=1`. It also
parses both Python harness sources and fails if either contains an `assert`
statement, so optimization cannot silently strip a Python gate. Each run
creates a random marker seed and derives a different marker for each locale;
none survives in normalized output.

This proves that the three runtimes can execute the tested generated contract. It
does not prove the compiler that turns ordinary Fluent authoring into that
contract. The fixtures hand-write internal operations which production source
must not expose:

- numeric selector heads are represented by `CITRY_PLURAL`; the compiler must
  turn ordinary cardinal and ordinal Fluent selectors into that operation and preserve source
  maps;
- displayed scalars are represented by `CITRY_TEXT`; the compiler must generate
  that operation for every displayed scalar boundary while leaving selector operands unwrapped;
  and
- the illustrative linked artifact already has unique internal IDs. It does
  not exercise real package layers, precedence, linker diagnostics, or source
  maps.

Direct display of a typed number or date remains a source error because no
named format profile can be inferred safely. Exact selector keys come from
compiler metadata rather than the runtime operand spelling, which makes `-0`
select the declared exact-zero branch in all three candidates.

## Error result

The wrapper rejected missing variables, missing functions, invalid rich
arguments, non-finite or non-numeric plural inputs, malformed marker output,
marker collisions, every Bidi_Class `B` scalar boundary, and the catalog bidi
canary matrix. That matrix covers all 12 `Bidi_Control` code points in literal,
four-digit Fluent `\u`, and six-digit Fluent `\U` forms: 36 cases per runtime.
It validates decoded standalone canary output after raw-source validation, so
the escape bypass is exercised. Production still needs decoded Fluent AST
validation across every value, attribute, term, and branch rather than
formatting only canaries. The
invalid plural fixture has a default branch specifically to prove that
pre-resolution validation runs before a runtime callback error could be
swallowed by selector resolution.

Rust `fluent-bundle` callbacks return a value, not a structured error channel
that Citry can reliably observe after selector evaluation. The spike therefore
prevalidates the generated value contract and assumes the compiler has already
validated every function name, option, and literal. It does not prove that the
production Rust/PyO3 adapter can bind an infallible closed callback surface.
That remains a ratification gate.

## Rich placeholder and bidi result

All three public runtime APIs flatten a formatted pattern to one string. A
Citry `Slot` object therefore never enters Fluent. The probe supplies a random
opaque marker to the allowlisted `SLOT` operation, requires at least one
occurrence in the result, and rehydrates every occurrence into an indexed
structural Slot segment. The English and Czech selected branches each repeat
the marker twice in different positions; all three runtimes preserve both.
Citry's repeatable Slot contract can invoke the fill separately for each
segment instead of attempting to reuse one rendered DOM node.

Runtime-owned Fluent isolation is disabled because it differs across the three
candidates. Hand-generated `CITRY_TEXT`, `NUMBER`, and `DATETIME` results instead
return Citry-owned FSI/PDI boundaries. This preserves scalar boundaries even
after Fluent flattens the result. Untrusted scalar values reject every Unicode
`Bidi_Control` and Bidi_Class `B` paragraph boundary, preventing an embedded
control or paragraph break from terminating the inline isolation. Multiline
catalog messages remain valid: the probe wraps each known-direction bidi
paragraph independently with LRI/PDI and preserves its separator, including
CRLF. Compiler-owned controls exist only in runtime results.

The protocol is still not ratified. Production must also:

- prove the authored-to-generated `CITRY_TEXT` transform and source maps;
- create a fresh cryptographically unpredictable, domain-separated marker for
  every message resolution and never persist or reuse it;
- scan every selected catalog resource and scalar input for marker collisions;
- permit a `Slot` only as the sole positional argument to `SLOT`, never as
  a selector, term argument, formatter input, or ordinary interpolation;
- symbolically verify that every required Slot appears on each reachable source
  and selected-translation path, allow any positive occurrence count, then
  rehydrate every marker occurrence as an independently invoked Slot instance;
- render every text segment through Citry's ordinary escaping path; and
- define a structural `<bdi>`/`dir` or equivalent checked boundary for the
  rehydrated Slot range, including unknown-direction content and browser DOM
  movement.

Because v1 `<c-trans>` is wrapperless, it also cannot attach the selected
catalog language to fallback prose. The design therefore makes equivalent-
language coverage mandatory at rich call sites and rejects cross-language rich
fallback. The spike has not yet exercised that application-level checker or
Slot-owned language metadata.

The hostile scalar case proves only scalar isolation. It does not prove Slot
direction ownership. Every runtime also accepted an opaque Slot marker as an
ordinary selector string when static validation was disabled, so runtime typing
cannot replace the catalog checker.

Current Fluent syntax rejects a variable-valued named term argument with
`Expected literal`. Terms may take literal grammatical parameters, but a Slot
cannot flow through a term.

## Browser artifact result

The ES2020 build containing `@fluent/bundle` and 100 embedded simple FTL
messages measured 14,407 bytes minified and 4,703 bytes gzip on the recorded
run. It includes `resource.js`, Fluent's catalog parser, because the public
browser API accepts FTL source and exposes no stable compiled-resource loader.

This is an upstream-runtime baseline, not the complete Citry payload gate. It
does not include the Citry client adapter, switching service, wire decoder,
artifact verification, or real catalog metadata. It demonstrates headroom
under 35 KiB, not a passing full-budget result.

If a parser ships inside an explicit client-switching boundary, build-time
validation must use the exact pinned browser runtime and produce transitive
canaries for public IDs, attributes, private terms, references, functions,
selectors, and variants. The client must validate and execute every reachable
canary branch before committing a locale. Checking only public IDs and
attributes cannot detect a silently dropped private term or nested branch.

## Candidate decisions

- Released `fluent.runtime` remains a comparison oracle, not the production
  server choice. Version 0.4.0 is Alpha, dates from 2023, and does not advertise
  Citry's current Python range.
- `fluent-bundle` remains the leading server runtime for another spike. Its
  concurrent bundle passed a compile-time `Send + Sync` assertion, but a real
  PyO3 binding, exact Decimal handling, closed callback errors, diagnostics,
  and benchmarks remain unproved.
- `@fluent/bundle` remains the leading dynamic-browser runtime. Its resolved
  installed version is checked independently of `package.json`; real client
  switching and typed-wire operands remain unproved.
- Fluent remains the leading message language. This probe did not ratify a
  production package combination or the formatter backend.

## Next Phase 0 slice

The next dependency is the formatter matrix: compare Babel 2.18.0's declared
subset and PyICU 2.16.2's broader behavior with browser `Intl`, including exact
typed values, calendars, numbering systems, time zones, digit shaping, parsing,
and versioned data sources. The runtime probe has shown where normalized
operations plug into Fluent; it has not shown that those operations meet the
semantic parity matrix.
