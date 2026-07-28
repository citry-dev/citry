# Stage 2 change-graph pilot

**Status (2026-07-23): bounded pilot complete; complexity circuit breaker
triggered before full expansion. Maintainer approval of a revised scope is
required.**

**Evidence baseline:** `B2-20260723T155146Z-cd177d74`, reconciled at pilot
close as `B2P-20260723T161330Z-cd177d74`.

**Pilot slice:** `actions.ReplaceUrl`, traced from its Python constructor to
the browser History API, generated and packaged artifact, tests, design, public
documentation, and release note.

At pilot close, 36 of 40 dirty product or evidence inputs retained their B2
content hashes. Four inputs moved during the review: the dispatcher, Events
routes, and their focused dispatcher and route tests. Each selected contract
point was re-inspected and the affected focused tests were rerun. Two
consecutive complete node-roster passes then produced the same aggregate
fingerprint, `d9739e67f5c1c0aafd1650d6747b866ca4912a05e0ea0531e56ccb354cacbcdf`.
The two tracked-clean workflows remain anchored to B2's HEAD. The exact four
input deltas and non-invalidating impact assessment are in
[`stage2_pilot_close_delta.tsv`](stage2_pilot_close_delta.tsv). The files
created by this pilot are research outputs rather than product inputs.

## Result

This deliberately small Events leaf is coherent from Python construction
through protocol encoding and browser behavior. Focused unit, conformance,
generated-bundle, and browser tests pass. It is not deliverable in the built
`citry` wheel, however: the generated Events browser runtime is absent because
the package-data declaration includes only the older dependency runtime. The
publish workflow's smoke test repeats that blind spot.

The reconciled trace contains **42 evidence nodes, 56 relationships, and eight
review layers**. Eleven nodes are specific to the history action, eighteen are
shared Events or delivery substrate, and thirteen are supporting design,
documentation, CI, or release records. An independent trace using a narrower
public-claim roster counted 35 files and 52 collapsed directed edges. The
difference is scope accounting, not a contract disagreement: this roster also
retains all four public migration/reference claims and separates configured CI
from executable tests. The machine-readable inventories are:

- [`stage2_pilot_nodes.tsv`](stage2_pilot_nodes.tsv);
- [`stage2_pilot_edges.tsv`](stage2_pilot_edges.tsv).

The 23 detailed node-layer labels roll up into eight review groups:

1. Python public API and server results: `public_api`, `server_result`,
   `python_test`, and `server_result_test`;
2. normative protocol and conformance: `protocol`, `protocol_fixture`,
   `protocol_test`, and `protocol_docs`;
3. browser source and build: `browser_source`, `browser_build`,
   `browser_generated`, and `browser_build_test`;
4. runtime delivery: `runtime_delivery` and `runtime_delivery_test`;
5. browser behavior and CI: `browser_e2e` and `ci`;
6. artifact packaging and release: `artifact_delivery` and `repository_gate`;
7. design and research: `governing_design`, `implementation_history`, and
   `research_evidence`; and
8. public documentation and release notes: `public_docs` and `release_notes`.

An edge reads as a typed evidence sentence: `from_node` followed by the
`relationship` followed by `to_node`. Its direction is not automatically a
causal or prerequisite direction. The later batch graph must convert these
evidence relationships into explicit `required_before` edges before using them
to order maintainer review.

This fan-out is large enough that a hand-authored feature-level graph for all
675 dirty paths would not be a bounded linear continuation of the pilot. The
Stage 2 and 3 circuit breaker therefore applies before any broad expansion.

## Scope rule

The pilot includes a file when it does at least one of the following:

1. constructs, encodes, validates, applies, generates, serves, or packages the
   selected action;
2. provides direct automated evidence for one of those operations;
3. governs or publicly claims the selected behavior; or
4. is required to reproduce the intended browser package artifact.

Generic Events machinery was included only at the point where the selected
action crosses it. Unrelated bindings, transports, host adapters, actions,
benchmark code, and broad Events research were not recursively expanded. One
transport test is included because it contains a URL action and proves that a
late timed-out response cannot mutate browser history.

This rule avoids pretending that every textual occurrence is a dependency. It
also exposes the important distinction between a slice-specific node and a
shared node that later review batches can reuse.

## Contract path

### Python API and result encoding

`citry.ext.events` exposes the `actions` module. `actions.ReplaceUrl` is a
frozen action value with a non-empty string URL plus the common `delay` and
`wait` fields. The result encoder maps it to:

```json
{"action": "url", "url": "...", "mode": "replace"}
```

The dispatcher applies client capability filtering, permits result hooks to
map the encoded list, validates the closed v1 action vocabulary again, updates
State metadata when needed, and places the actions in a success result. Its URL
hook validation accepts only a non-empty string and exact `push` or `replace`
mode.

### Normative protocol

The result schema requires `action`, `url`, and `mode` for a URL action, with a
non-empty string URL and a `push` or `replace` mode. The protocol specification
defines this as a history update without navigation. Its canonical `history`
handler returns a timed non-blocking push followed by a replace.

The history call/result pair is registered in the fixture index. The protocol
self-validator checks schemas, fixture shapes, call/result alignment, and the
index. Separately, the Python conformance test renders a fresh component,
dispatches every indexed call, validates the result against the schema, masks
only declared volatile fields, and compares the remaining JSON exactly. This
is stronger evidence than a fixture that is only parsed.

### Browser implementation and generated output

The TypeScript runtime advertises `url` in its client action capabilities.
`applyUrlAction` rejects an empty URL or unknown mode, preserves the page's
current `history.state`, uses `history.replaceState` for this action, and warns
without interrupting later actions when the browser rejects a URL. The common
action scheduler retains authored order and the action's `delay` and `wait`
semantics.

The private `citry-client` package is the source owner. Its build command uses
esbuild to produce
`packages/py/citry/citry/ext/events/client/citry-events.js`. A canary performs
the same in-memory build and compares it byte-for-byte with the working-tree
generated bundle. The Python Events route serves that bundle at
`ext/events/runtime.js`; the emission path also reads it for inline delivery.

### Browser behavior

The focused real-browser tests prove:

- a Python handler's `ReplaceUrl("/from-handler")` reaches the browser;
- the tested push-then-replace sequence adds exactly one history entry;
- `history.state` is preserved and no synthetic `popstate` is emitted;
- invalid modes and browser-rejected cross-origin URLs warn and do not stop a
  later valid action;
- Back and Forward change the address without restoring Citry component DOM or
  State; and
- a URL action in a response delivered after timeout is dropped with the whole
  stale response.

The compatibility route deliberately turns a history-only non-JavaScript form
call into `204` with no `Location` header. It does not claim to reproduce
client-side history mutation.

## Verification evidence

Observed on 2026-07-23 and rerun where affected after the B2P close-delta
reconciliation.

Python action and dispatcher conformance:

```console
uv run --package citry pytest packages/py/citry/tests/test_events_actions.py packages/py/citry/tests/test_events_conformance.py -q
```

Result: 112 passed.

Focused dispatcher visibility after its concurrent edit:

```console
uv run --package citry pytest packages/py/citry/tests/test_events_dispatch.py -q -k 'no_hint_when_navigation_or_history_ships'
```

Result: 2 passed and 125 deselected.

Protocol package, runtime emission, and routes:

```console
uv run --package citry pytest packages/py/citry/tests/test_events_protocol_package.py packages/py/citry/tests/test_events_emission.py packages/py/citry/tests/test_events_routes.py -q
```

Result: 201 passed with one third-party Starlette deprecation warning.

Private browser-source package:

```console
pnpm --dir packages/js/citry-client test
```

Result: 9 passed, including exact generated-bundle equality.

Focused browser behavior in explicit Chromium:

```console
uv run --package citry --group e2e pytest packages/py/citry/tests/e2e/test_events_applier_e2e.py packages/py/citry/tests/e2e/test_events_transport_e2e.py --browser chromium -q -k 'url_action_and_unknown_kinds or back_and_forward_leave_component_dom_and_state_untouched or timeout_rejects_then_a_late_response_drops'
```

Result: 3 passed and 56 deselected. This is observed Chromium evidence. The
Firefox and WebKit workflows in the node roster are configured evidence, not a
claim that those CI jobs were run during the pilot.

Fresh wheel contents:

```console
pilot_dist_dir=$(mktemp -d)
uv build --package citry --wheel --out-dir "$pilot_dist_dir" >/dev/null
python -m zipfile -l "$pilot_dist_dir"/*.whl | rg 'citry/ext/(events|dependencies)/client/.*\.js|citry/py\.typed'
rm -r "$pilot_dist_dir"
```

Result: the build passed; `citry.js` and `py.typed` were listed;
`citry-events.js` was absent.

The wheel build also emitted setuptools' deprecation warning for the current
TOML-table `project.license`. That is a Stage 4 metadata signal, not part of the
selected action's change graph.

The repository-wide opening gate remains the B2 evidence recorded in
[`stage2_baseline.md`](stage2_baseline.md): unrelated current failures exist in
`citry-ui` typing and client payload budgets. The focused pass does not
supersede that result.

## Confirmed delivery gap

`packages/py/citry/pyproject.toml` declares:

```toml
citry = ["py.typed", "ext/dependencies/client/*.js"]
```

It does not include `ext/events/client/*.js`. A fresh wheel consequently omits
the runtime that `routes.py` and `emission.py` read. An installed application
that activates Events would therefore lack a required file even though source
tree and browser tests pass.

The publish workflow says both client JavaScript assets are package data, but
its installed-wheel smoke test asserts only
`ext/dependencies/client/citry.js`. It would allow this broken wheel through.
This pilot records the gap and does not fix it because Stage 2 is mapping work,
not implementation or release work.

The protocol README also says Python conformance was passing "as of Citry
0.2.0", while the local changelog presents the history actions as unreleased.
That phrase may refer to the still-unbumped development manifest rather than
the published `0.2.0` artifact. It needs version-baseline reconciliation before
publication; this pilot does not infer which wording is intended.

## Review burden observed in the pilot

The likely maintainer review cost for this one leaf is **2.5 to 4.25 hours**:

| Review unit | Estimated focused review |
| --- | ---: |
| Public API, encoding, hook validation, and normative protocol | 45 to 75 minutes |
| Browser source, ordering behavior, generated-output proof, and focused tests | 45 to 75 minutes |
| Runtime delivery and installed-wheel failure | 30 to 45 minutes |
| Governing design, public docs, migration claims, and release note consistency | 30 to 60 minutes |

A later live-project acceptance check would add roughly 20 to 30 minutes once
the package-delivery blocker is fixed. These are planning ranges, not a
maintainer time commitment.

## Expansion estimate and circuit-breaker decision

B2 contains 675 dirty paths. The selected Events area alone has 22 server
source files, 24 Python Events test files, 46 protocol files, 7 private client
files, and 27 Events design or research files. Those prefix counts overlap by
purpose but show that this 42-node leaf is only a narrow part of one domain.
The wider tree also contains 212 docs-site paths, 184 `citry` package paths,
164 design paths, parser and binding work, cache and introspection work,
`citry-ui`, workflows, metadata, and local archives.

Feature-level expansion would repeatedly encounter shared dispatcher,
protocol, browser, generated-artifact, docs, and packaging nodes. It would also
duplicate work reserved for the Stage 3 design register and Stage 4 technical
audit. A credible full hand-authored estimate is **40 to 70 vertical slices**,
roughly **20 to 40 agent-hours** and **8 to 15 maintainer review-hours**, with
low confidence because boundaries are still emerging. It would probably
exceed the shared six-task delegation cap or leave a large sequential audit.

That is an unbounded, more-than-linear shape under the approved circuit-breaker
rule. The useful completed checkpoint is the B2 baseline, this exact pilot,
the passing focused evidence, and the confirmed artifact-delivery gap. No
other domain has been expanded.

## Revised-scope options

### Option A: batch ownership graph, recommended

Assign every dirty path exactly one primary review batch using an automated
path/import/reference classification, then manually trace only cross-batch
contracts, public APIs, generated artifacts, and release boundaries. Each path
still receives a design family, test family, source/generated/evidence role,
and unique review owner. Stage 3 retains per-design completion and follow-up
records; Stage 4 retains line-level implementation, metadata, and test audits.

- Expected output: 10 to 14 ordered review batches and a 675-path ownership
  ledger with a smaller batch dependency graph.
- Agent cost: 4 to 7 hours, likely two root work cycles and no more than two
  additional bounded delegated tasks across Stages 2 and 3.
- Maintainer review: 1.5 to 3 hours for batch boundaries, prerequisites, risk,
  and burden estimates.
- Confidence: medium-high. It directly serves the Stage 2 output without
  duplicating later audits.

### Option B: complete Events first

Build exact feature-level traces for the roughly 126 Events-related source,
test, protocol, client, and design paths, then pause again before other
domains.

- Expected output: approximately 8 to 15 Events slices plus their shared
  substrate.
- Agent cost: 8 to 14 hours.
- Maintainer review: 3 to 6 hours.
- Confidence: medium. It produces deep knowledge of a launch-critical domain
  but leaves Stage 2 incomplete and biases the overall review order toward
  Events.

### Option C: one pilot per broad domain

Repeat the vertical-slice method for parser/bindings, rendering/ownership,
dependencies/browser, cache, introspection/debug/CLI, docs, and release
infrastructure before choosing the graph granularity.

- Expected output: seven to nine more pilots and a better global estimate, but
  not the required all-path review batches.
- Agent cost: 10 to 18 hours.
- Maintainer review: 4 to 8 hours.
- Confidence: medium-high about estimation, low about near-term Stage 2
  completion. It risks consuming the shared Stage 2 and 3 delegation budget.

### Option D: full feature-level graph

Continue the current granularity until every dirty path and dependency edge is
hand traced.

- Expected output: 40 to 70 slices and hundreds of repeated shared edges.
- Agent cost: 20 to 40 hours or more.
- Maintainer review: 8 to 15 hours or more.
- Confidence: low until much later in the work.
- Recommendation: do not choose this approach unless the exhaustive graph is
  itself a desired product artifact and the delegation cap is deliberately
  revised.

## Recommended decision

Approve Option A and treat this pilot as the reference pattern for high-risk
boundary nodes, not as the required granularity for every file. This preserves
complete path ownership, produces the prerequisite-aware batches Stage 2 is
meant to deliver, and leaves the deeper evidence in the stages designed to
hold it.
