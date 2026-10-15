# Canonical project-page scenario

The thirteen cohort applications use this deterministic in-memory model through
their native framework hosts. The `Citry + Vue` adapter, which uses Citry's
public Vue renderer, also uses the model but is not in the `cohort` profiles.
The scenario keeps the `project_board` directory name
to avoid adapter path churn, but it now represents the canonical project page
from `packages/py/citry/tests/test_benchmark_citry.py`. Historical captured runs
with 10, 100, 325, or 1,000 simple rows remain a separate workload and must not
be compared as though they used this scenario revision.

[`canonical_project.json`](canonical_project.json) contains the exact embedded
`data_json` extracted through Python's AST, its source path, and the SHA-256 of
that complete source file. The shared model normalizes the 14 canonical outputs
to stable contiguous IDs while retaining each `source_id`. It builds one project,
five phase groups, three note tabs, roles, bookmarks, attachments, and dependency
references. It does not import or copy the fixture's HTML renderer.

The supported counts are 14 outputs (1x), 140 outputs (10x), and 1,400 outputs
(100x). Scaling repeats each content cohort inside the same project and five
phase groups. IDs remain unique and dependency references stay inside their
replica. The default profiles cover 1x and 10x. The 100x profile is opt-in until
1x and 10x timings and memory use have been reviewed. Profiles and run manifests
identify this contract as `scenario_revision = "canonical-project-v1"` so a
regenerated historical report without that revision continues to label its
counts as flat rows.

The Next and Nuxt adapters use `node_model.mjs`, a framework-neutral
translation of the same frozen source data and state transitions. It is copied
into each prepared application beside the Python scenario modules; each build
generates its data module from `canonical_project.json` and does not maintain a
second hand-edited fixture.

## Actions and state

The fixed sequence selects output 1, filters with the first canonical output
title, clears the filter, rejects and accepts a project-title edit, inserts an
output, reverses phase groups and their outputs, removes the inserted output,
and sends a final server probe. Every accepted action, including business
validation failure, returns a new revision. Invalid protocol input is an error.
An entire sequence restores the original output count.

Filtering retains all five phase groups, including empty groups. Reorder reverses
the group order and each group's output order, so flattening the groups equals the
reversed flat output list. Insert appends to the last current group. The model and
the independent runner oracle reproduce these rules separately from the same
frozen source data.

All adapters follow [`DOM_CONTRACT.md`](DOM_CONTRACT.md). They keep all five tab
panels mounted, show Outputs initially, and render phase and output expansions
open. Tabs, disclosure, description fields, completed checkboxes, and output
selection use each framework's native controls. Per-output Save/Add and attachment
editing from the rendering fixture are outside the shared model. The project-title
Save action remains active.

## Readiness and qualification

Each adapter keeps its framework completion endpoint. Vue awaits the full JSON
response and `nextTick`; React signals from its committed-board effect; the other
adapters retain their documented native lifecycle endpoints. The runner does not
add network-idle, animation-frame, or paint delays.

At that endpoint, the common instrumentation records the timestamp, synchronously
captures the complete semantic DOM, and compares it with expected state prepared
by the independent oracle before the operation. The mark is rejected when the
snapshot differs. Capture and validation time is reported separately as
`semantic_observer_ms`; it is outside the elapsed endpoint, though its DOM reads
and `getComputedStyle` can still perturb later event-loop work. Adapter-provided
`observer_ms` retains its existing meaning. Response and socket completion checks
remain in the runner's transport accounting.

Untimed qualification proves first, last, and newly inserted real controls. It
also checks unique document IDs, all five native tabs, local disclosure and form
controls, and actual visibility of initially expanded output content. Further
cases cover missing or delayed DOM tails, stale/pending/premature marks, dropped
handlers, interrupted transport, and delayed framework initialization. The DOM
tail checks establish that later completion of the same revision cannot rescue
an earlier rejected mark. They are synthetic DOM checks, not a claim about
partial JSON transport. Arbitrary future asynchronous application hooks remain
outside the generic readiness proof.

The static files and responses use `Cache-Control: no-store`; profiles report
identity encoding and loopback transport. No database, authentication, response
compression, or application result cache is involved. Django-based hosts report
their existing `Server-Timing` boundary, while browser-only adapters keep server
HTML rendering as not applicable. The Next and Nuxt hybrid adapters report
server HTML timing for the initial document and their explicit delta/JSON
preparation kind for actions.

Run the shared model and oracle checks with an application's Python interpreter:

```sh
../../apps/citry/.venv/bin/python -m unittest test_model test_assertions
```
