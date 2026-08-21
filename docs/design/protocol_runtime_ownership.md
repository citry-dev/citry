# Protocol-owned wire construction and validation

**Status (2026-08-04): Implemented; all six stages passed independent review.**
This document records the design for
[GitHub issue #39](https://github.com/citry-dev/citry/issues/39). The client
graph and Events v1 wire shapes stay in their existing versioned directories.
The remaining repository-wide release blockers are recorded in the Stage 6
evidence and belong to concurrent work.

## Why this work exists

Citry currently describes its browser protocols in JSON Schema, prose, and
worked examples. The Python server and browser runtimes then repeat the field
names and validation rules in product code. Tests show that the copies mostly
agree, but an edit to only one copy can still introduce drift.

For example, `componentClasses[].className` is a required string in the client
graph schema. The current browser reader checks that the field exists but does
not check its type. A re-signed manifest can therefore satisfy the browser
while failing the schema.

After this work, the versioned protocol directories own executable builders
and validators. Product code decides what to render or dispatch, then gives
normalized facts to those helpers. The helpers construct the exact JSON records
or reject invalid input before product code acts on it.

## What remains unchanged

- The wire protocols remain `citry-client-graph/1` and `citry-events/1`.
- The protocol implementations remain private parts of the `citry` release.
  This work does not create separately published PyPI or npm packages.
- Existing public Python APIs remain product-facing adapters.
- Closed protocol records reject missing, extra, and wrongly typed fields.
  Application-owned JSON containers stay open where the schemas say they are
  open.
- The installed Python package serves checked-in JavaScript and does not need
  Node or `jsonschema`.

The only accepted-input changes planned here are listed explicitly in
"Decisions that affect accepted input". Any other schema, normalized golden
example, public API, or emitted-wire change needs maintainer approval before it
is implemented.

## Where the executable code lives

The language-neutral files keep their protocol-major directory:

```text
packages/protocol/events/v1/
  python/citry_events/
  js/
  call.schema.json
  result.schema.json
  descriptor.schema.json
  manifest.schema.json
  spec.md
  tests/

packages/protocol/client_graph/v1/
  python/citry_client_graph/
  js/
  manifest.schema.json
  spec.md
  tests/
```

The Python packages use only the standard library and relative imports. Their
files are copied byte for byte into private packages shipped by `citry`:

```text
packages/py/citry/citry/_protocol/events/
packages/py/citry/citry/_protocol/client_graph/
```

The canonical source contains its own generated-copy warning because a
copy-only header would break the byte comparison. CI copies the canonical
packages into a temporary directory and compares every file with the shipped
copies. It then runs the same protocol cases against both locations.

The JavaScript packages are private pnpm workspace packages. The Events client
imports its protocol package while esbuild creates the existing browser IIFE.
The handwritten core runtime keeps its current source form. The initial
explicit build inserts one marked, private helper block immediately after the
outer IIFE's `"use strict"`. Later builds replace only that block. Check mode
requires one existing marker pair, reconstructs the expected file in memory,
and compares it with the checked-in file. This avoids an unrelated rewrite of
the full core runtime and prevents the generator from changing surrounding
authored bytes.

The Events bundle includes the small client-graph comment parser from the same
source. It does not read the generated `CitryClientGraphProtocol` global, so
this migration adds no new dependency on that global. The existing runtime
order remains unchanged: the core hook broker loads before Events.

That shared parser treats the first eight revision characters in `citry:g1`
comments as a page-local alias. The manifest and core registry keep the
complete revision, and the core owns the active alias-to-revision mapping and
its collision rejection. Events only preserves or rewrites the alias already
present in a validated ownership comment.

## What the protocol helpers own

### Events

The Events helpers own:

- the protocol string, capabilities, result codes, action kinds, swap kinds,
  exact field sets, and the 16-call envelope limit;
- strict JSON parsing and checks for application-owned JSON values;
- builders and validators for calls, envelopes, results, errors, actions,
  descriptors, and manifests;
- result count, request ID, `sendSequence`, capability, and data-action
  relationship checks;
- reserved GET carrier names and pure conversion between an already-decoded
  multimap and protocol fields.

Citry keeps handler lookup, state, authorization, CSRF, hooks, dispatch,
content-type and HTTP-method handling, the configurable request byte limit,
and route response conversion. `Download` and `RouteResponse` remain HTTP
responses rather than Events actions. Early route failures still ask the
protocol helper to build their error envelopes.

### Client graph

The client-graph helpers own:

- the protocol and comment constants;
- every closed record and component-tag client-binding variant;
- manifest construction from normalized records;
- logical references and relationships between records;
- canonical JSON, revision calculation, and ownership-comment formatting and
  parsing.

Citry keeps render-tree traversal, deciding which components and fills appear,
object lookup, and placement of ownership comments. The browser runtime keeps
DOM scanning, parent and ordering checks that require live DOM nodes, component
lifecycle, and registry mutation.

## How validation reports a problem

Every validator is deterministic and stops at the first problem. Success
returns no issue. Failure returns:

```json
{
  "path": "/results/0/actions/1/action",
  "category": "enum",
  "message": "Unknown action type."
}
```

`path` is an RFC 6901 JSON Pointer. `category` comes from a small fixed
vocabulary. The path and category are part of the executable protocol contract;
the human-readable message is not. JSON Pointer escapes `~` as `~0` and `/` as
`~1` in a member name.

Validation follows one order in both languages:

1. Reject non-JSON language values and cycles.
2. Check the current value's broad type.
3. Check missing required fields in their schema order.
4. Check unknown fields in lexicographic UTF-16 code-unit order, matching
   JavaScript string ordering.
5. Check present declared fields in their schema order, and array entries from
   first to last.
6. Check scalar constraints such as constants, enums, patterns, and ranges.
7. Check relationships, correlation, and capabilities in their documented
   protocol order.

A discriminated union checks the discriminator before the selected record. A
nullable union checks null versus the other type first. Validators do not
modify or normalize their input.

The initial categories are `required`, `unknown_field`, `type`, `enum`,
`pattern`, `range`, `strict_json`, `semantic`, `correlation`, and
`capability`. A new category requires one shared Python/JavaScript case.

Python builders raise `ProtocolValueError` carrying one validation issue.
JavaScript builders throw `ProtocolValueError` with the same `issue` shape.
Validators return either no issue or one issue; they do not throw for ordinary
invalid wire data. Builders return fresh mutable records and recursively copy
open application JSON, so later changes to the caller's input do not alter the
built record.

Open JSON checking uses an explicit work stack, detects cycles by object
identity, and defines no protocol depth limit. Unsupported values and cycles
produce `strict_json`. Allocation failure or a language runtime resource limit
is not converted into a wire error. The final serialization boundary validates
assembled output again, so a caller that mutates a built record or a hook result
cannot bypass the protocol after construction.

Incoming remote data is validated in production. The server validates Events
calls before invoking any handler. The browser validates complete Events and
client-graph inputs before applying the first side effect. The more expensive
audit of a graph that Citry itself just built runs in development and tests; a
production option may enable it for diagnosis. Revision creation always runs.

## How schemas stay connected to executable checks

JSON Schema remains the authority for structure. A small generator extracts
simple record information such as required fields, optional fields, primitive
types, enums, patterns, and numeric limits. Relationship rules stay in named,
handwritten protocol functions.

The generator also writes a constraint-coverage report. Every relevant schema
keyword and constraint must be either generated or assigned to one named
handwritten rule. An unknown or unassigned constraint fails generation. This is
important for Events schemas that use `$ref`, `oneOf`, `allOf`, `if`, `then`,
`else`, and `not`; silently ignoring one would make the executable checker
weaker than the schema.

The conformance index starts from a valid example for each boundary and creates
one small mutation for each structural constraint. A mutation records its valid
seed, the change, the expected path and category, and every implementation that
must run it. Relationship and transport mutations are listed explicitly. The
test must observe the intended issue, not merely any rejection.

If this work starts requiring a general-purpose JSON Schema engine, an
unexpectedly large case expansion, or material CI cost, implementation pauses
for a narrower design decision.

## Decisions that affect accepted input

### The browser follows the client-graph schema

The browser will require strings for these schema fields:

- `componentClasses[].classId`
- `componentClasses[].className`
- nullable `sourceLocations[].origin`
- nullable `sourceLocations[].mappingKey`
- `nestedComponents[].tagName`
- `fills[].slotName`

Each tightened check gets its own re-signed invalid manifest. This changes what
the browser accepts but does not change valid output.

### A zero data delay remains valid

`data.delay` accepts zero. Citry's `Data` action constructor omits a zero delay
from its canonical output. A hook that explicitly authors `{"delay": 0}` keeps
that field after the mapping passes validation. `data` actions do not carry a
wait flag.

### Client-graph revisions use exact cross-language bytes

The existing Python and browser algorithms disagree when a manifest contains
non-ASCII text. Both implementations will canonicalize the decoded unsigned
manifest, not the original JSON text:

1. Remove the top-level `revision` member.
2. Accept only null, booleans, strings, arrays, objects, and decoded
   non-negative safe-integer values. A boolean is not an integer.
3. Require every decoded integer to be at most `9007199254740991`. Parsed forms
   such as `1`, `1.0`, `1e0`, and `1.0000000000000001` all decode to the same
   value and emit as `1`. Emit ordinary decimal digits and normalize negative
   zero and numeric underflow to `0`. The original number characters are not
   preserved or checked by a second parser.
4. Escape strings exactly as `JSON.stringify` does. Quotes, backslashes, and
   control characters use JSON escapes. Other paired Unicode characters are
   emitted literally. An unpaired UTF-16 surrogate is emitted as a lowercase
   `\udxxx` escape. Unicode text is not normalized.
5. Preserve array order. Sort object names lexicographically by UTF-16 code
   units, then apply these rules recursively to each value.
6. Join tokens with `,` and `:` and no whitespace, encode the result as strict
   UTF-8, hash it with SHA-256, and emit lowercase hexadecimal.

Graph records contain only non-negative integers, so the safe-integer bound is
the only numeric-domain change required. Existing ASCII manifests inside that
bound keep their revisions. Existing non-ASCII values receive the corrected
revision. Unpaired surrogates remain representable through their ASCII JSON
escape, avoiding an unnecessary accepted-input change.

[`canonicalization.json`](../../packages/protocol/client_graph/v1/tests/canonicalization.json)
records the exact canonical bytes and hashes for a valid Unicode manifest,
control and escape characters, astral text, UTF-16 key ordering, alternate
integer spellings, the safe-integer boundary, and unpaired surrogates. Python
and Node produced identical bytes for these vectors. Transport escaping remains
separate: JSON embedded in a script element still escapes `<` as `\u003c`, then
the browser decodes it before calculating the canonical revision.

### Client-graph JSON is safe inside its script element

After the revision is calculated, the server encodes the complete manifest for
HTML transport and replaces every literal `<` with `\u003c`. This is the same
script-safe JSON rule the Events manifest already uses. The browser's JSON
parser restores the original value before validation and hashing.

The client-graph transport can therefore carry a value containing `</script>`;
the current producer rejects that value because its transport JSON leaves `<`
literal. This is an approved accepted-input expansion. It does not weaken the
ordinary `Script` dependency rule for authored JavaScript, which continues to
reject its own closing tag.

## Current disagreements and their decisions

| Current disagreement | Decision in this work |
|---|---|
| The graph schema requires six strings that the browser does not type-check. | The schema wins and the browser adds the checks. |
| The browser requires safe integers but the schema has no maximum. | Every graph integer shape gains the safe-integer maximum. |
| The built-in Python checker rejects decoded `1.0` where JSON Schema and JavaScript accept it as an integer. | Integer validation follows the decoded value and accepts it. |
| Python canonical JSON preserves decoded `1.0` as `1.0`. | The protocol canonicalizer emits the decoded safe-integer value as `1`. |
| Python escapes all non-ASCII strings while the browser emits paired Unicode literally. | Both use the exact string rules and shared vectors above. |
| Client-graph transport leaves `<` literal while Events transport is script-safe. | Client-graph transport escapes `<` after revision calculation. |
| A canonical `Data` builder omits zero delay while a hook can author it explicitly. | Both are valid: builders omit zero and validated hook mappings preserve it. |

## Implementation and review order

### Stage 0: design and moving baseline

Record this design, fingerprints for only the contract inputs and generated
outputs, canonicalization vectors, current bundle size and focused timings, and
a measured browser composition prototype. `scripts/protocol_runtime_baseline.py`
owns the exact scope, ordering, hashing rules, environment report, sample
counts, and timing command. Refresh its result at each later stage; ongoing work
elsewhere is not frozen.

### Stage 1: conformance foundation

Add the deterministic issue contract, constraint inventory, coverage report,
bounded mutation generator, explicit relationship mutations, and independent
Python and JavaScript package checks.

Implementation note: the attempted generator crossed the stop condition for a
general-purpose schema compiler. Stage 1 therefore uses strict, explicit
mutation records plus an uncovered-constraint report. Runtime stages add cases
as each field family moves. The evidence and opening counts are in
[`v1_beta_research/protocol_runtime_stage1.md`](v1_beta_research/protocol_runtime_stage1.md).

### Stage 2: Events Python

Create and embed the Events Python package. Migrate dispatcher validation,
result/error/action construction, manifest construction, hook mappings, early
route errors, and the pure GET carrier conversion. Run the cases through the
real dispatcher and routes before removing replaced fixed-field code.

Implementation note: the canonical package, embedded copy, server migration,
and focused checks are complete. Evidence and the remaining cross-language
coverage work are recorded in
[`v1_beta_research/protocol_runtime_stage2.md`](v1_beta_research/protocol_runtime_stage2.md).

### Stage 3: Events JavaScript

Migrate call construction and incoming Events validation. Check calls captured
at the transport boundary, complete result preflight, manifests, actions,
atomic failure, and source-to-bundle freshness before removing duplicate code.

Implementation note: the private JavaScript protocol package, browser
migration, focused Chromium checks, and moving payload evidence are complete.
Evidence and the maintainer-approved payload reset are recorded in
[`v1_beta_research/protocol_runtime_stage3.md`](v1_beta_research/protocol_runtime_stage3.md).

### Stage 4: client graph Python

Move closed-record construction, comments, canonical bytes, revisions, and
logical graph validation. Keep record selection in Citry. Check development and
production output, every binding kind, golden manifests, and deterministic
revisions.

Implementation note: the canonical Python package, embedded copy, server
migration, focused checks, performance comparison, and independent review are
complete. Evidence is recorded in
[`v1_beta_research/protocol_runtime_stage4.md`](v1_beta_research/protocol_runtime_stage4.md).

### Stage 5: client graph browser

Generate the protocol helper block, replace duplicated logical checks, and keep
DOM-specific checks in product code. Run the shared cases through real browser
staging and adoption, including all tightened fields and atomic failure.

The first explicit build inserts one marker pair immediately after the outer
IIFE's `"use strict"`. Every later build requires exactly one pair at that
position and replaces only the bytes between it. Check mode reconstructs the
whole expected file in memory and compares it with the checked-in file. It
never inserts a second block.

Implementation note: the private JavaScript validator, generated core helper,
shared Events comment parser, focused Chromium checks, and maintainer-approved
payload reset are complete and passed independent review. Evidence is in
[`v1_beta_research/protocol_runtime_stage5.md`](v1_beta_research/protocol_runtime_stage5.md).

### Stage 6: completion gate

Audit constraint coverage and every producer and consumer. The
maintainer-approved bounded audit assigns every schema constraint to named
Python and JavaScript validators and supporting tests, with counts and
fingerprints that fail on schema drift. The exact shared mutation set remains
the cross-language path/category proof. Exhaustive one-mutation-per-constraint
exploration is tracked separately in
[#54](https://github.com/citry-dev/citry/issues/54).

Build a wheel and
sdist, then build another wheel from the sdist outside the checkout. Compare
artifact inventories and hashes and exercise the installed package without the
repository, Node, or `jsonschema`. Update current protocol, architecture, and
build documentation. Run focused performance comparisons, Chromium, Firefox,
WebKit, and the full `python scripts/check.py --reporter agent` gate.

Implementation note: constraint ownership, the boundary audit, distribution
proof, three-engine browser matrix, payload and performance checks, and
independent review are complete. The review corrected strict-JSON ordering and
integral-number behavior in the Python Events validators. The aggregate
repository gate remains red only for the concurrent release blockers listed in
[`v1_beta_research/protocol_runtime_stage6.md`](v1_beta_research/protocol_runtime_stage6.md).

Each stage gets an independent adversarial review. Review findings are fixed or
recorded as an explicit maintainer decision before the next stage begins.

## When implementation stops for approval

Implementation pauses before making any of these changes:

- a wire change beyond the accepted-input decisions above;
- a public API or compatibility change;
- a new runtime dependency or separately published package;
- a general-purpose schema compiler;
- an extra browser request or load-order dependency;
- a browser bundle that exceeds the current hard budget;
- a repeatable slowdown above 5 percent and at least 1 microsecond for Events
  dispatch or 0.5 milliseconds for client-graph rendering, using the Stage 0
  command's seven-sample median;
- a stage whose required work grows beyond one reviewable unit.

## Completion criteria

Issue #39 is complete when:

1. Product code no longer repeats fixed protocol field sets or vocabularies.
2. Every producer constructs output through protocol helpers, and every remote
   consumer validates before acting.
3. Schema constraints and named relationship rules have mechanical coverage in
   both languages and at applicable real boundaries.
4. Generated Python copies and both shipped JavaScript files have stale-output
   checks.
5. A clean wheel and wheel built from the sdist work without repository tools.
6. Existing public APIs, valid golden exchanges, atomic behavior, and bundle
   budgets remain intact except for explicitly approved corrections.
