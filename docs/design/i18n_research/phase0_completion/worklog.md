# Phase 0 completion work log

This log keeps the remaining decisions and evidence checks in one place while
the final Phase 0 slices run. The final report replaces the running notes below
with settled results.

## Stage map

1. Freeze the baseline. List the remaining decisions, acceptance thresholds,
   and failure cases without repeating questions that earlier probes answered.
2. Finish rich-message ownership. Prove a direction and language boundary for
   each structural Slot and exercise the checked relocation path through the
   current Citry ownership graph in Chromium, Firefox, and WebKit.
3. Finish provider behavior. Prove isolated server bindings, transparent
   server-only providers, real-element client providers, nested inheritance,
   hard client barriers, a readonly service, stale-generation handling, and an
   atomic context/content commit.
4. Finish cache behavior. Prove that an i18n-dependent component or fragment
   cannot read the cache backend without an authentic current variation token,
   that locale-independent sharing is explicit, and that dormant i18n does not
   disable caching.
5. Choose the runtime scope. Run the remaining formatter, parser, package, and
   cross-runtime cases needed to select the first server/message combination
   or narrow it to an honestly supported subset.
6. Ratify the bounded release shape. Measure the fixed-locale payload, dynamic
   runtime and catalog partitions, render cost, and loaded locale-switch cost
   against the design thresholds.
7. Freeze and reproduce every artifact, update the main design, run the
   repository checks, and record any gate that remains outside the chosen first
   release.

All seven stages are complete. The normal and optimized evidence runs
reproduce, the focused Python, Rust, JavaScript, browser, and Cache checks pass,
and the main design records the final decisions and remaining formatter gate.

The repository-wide fast profile still reports unrelated worktree failures in
existing `citry-ui` formatting and typing, three form/menu tests, and the
existing client-runtime payload budget. This Phase 0 work does not change those
production files. The fast profile passed Rust formatting, Clippy and tests,
Ruff lint, Pyright, both JavaScript protocol checks, client checks, playground,
VS Code, and repository validators.

## Decisions that earlier probes already settled

- Fluent FTL remains the authoring language candidate.
- The Rust compiler with a thin PyO3 boundary can parse, check, link, and
  generate the tested private runtime operations with exact source ranges.
- Authors write ordinary variables and Slots. Only generated artifacts contain
  `CITRY_TEXT`, `CITRY_PLURAL`, and `SLOT` operations.
- Parameters belong to one message contract. Public references contribute a
  checked transitive interface. Private terms stay in their source unit.
- A named rich Slot may occur more than once on a reachable path.
- The first browser release may require the same occurrence count in every
  selectable locale. Count changes use navigation.
- Existing source-aware Slot regions are sufficient for equal-count browser
  movement. The graph schema does not need an i18n record.

## Remaining acceptance gates

### Rich Slots

- Opposite-direction Slot content cannot reorder the translated sentence.
- Hostile bidi controls inside application-owned Slot content cannot escape the
  structural boundary.
- The boundary keeps application-owned `lang` values and does not relabel Slot
  content as catalog prose.
- Moving the occurrence keeps caller scope, component identity, focus,
  selection, teleports, and one-time cleanup.
- Missing, duplicate, foreign, stale, corrupt, or overlapping ranges fail
  before any visible or semantic state changes.

### Providers

- Server bindings remain isolated across concurrent contexts.
- `client=False` adds no browser i18n service or dependency and blocks a service
  inherited from an enabled ancestor.
- `client=True` owns one real wrapper and exposes a readonly service with a
  checked `switchLocale()` operation.
- Nested provider policy distinguishes inherited, explicit, and cleared fields
  and recomputes from outer to inner.
- Invalid aliases, stale generations, failed chunks, and false barriers keep
  the last complete locale.
- Content, client references, and every provider wrapper change in one commit.

### Cache

- An i18n-dependent declaration without an authentic current token performs no
  backend read.
- The token distinguishes every ambient input that can change settled output.
- A token from another engine or context is rejected before lookup.
- Locale-independent sharing requires an explicit declaration.
- Dormant i18n uses stateless replay version 1 and does not deny otherwise safe
  entries.

### Runtime and performance

- The selected server runtime passes its declared semantic profile matrix and
  rejects profiles it cannot support.
- Message plural and formatter operations use the same selected CLDR service as
  direct formatting.
- The fixed-locale page adds no i18n browser bytes without a client boundary.
- The dynamic runtime stays within 35 KiB gzip and a 100-message locale
  partition stays within 15 KiB gzip.
- The measured warm server overhead and loaded client-switch p95 stay within
  the thresholds in section 14.3 of the main design.
- Every checked result records exact source, dependency, runtime, and harness
  identities and reproduces under normal and optimized Python.

## Review limitation

The repository workflow normally requires a separate adversarial reviewer.
The active collaboration rule for this session does not permit spawning one.
No final claim will be labeled independently reviewed. Each slice must include
always-on negative checks, a frozen evidence file, and a clean reproduction to
reduce the risk this leaves.
