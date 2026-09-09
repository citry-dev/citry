# Iteration 68: emit function text without building interior render trees

Iteration 67 found that the prototype executing Button, Icon and HeroIcon templates
immediately under their caller's ownership still constructs 1,151
render objects and walks 1,036 part lists looking for deferred work. All selected
function subtrees contain finished text in the large case, although many carry
dependency records from caller content. This motivates appending function output
directly to a shared parts list.

## Prior art and chosen design

Read `_render_body`, `IfNode.active_branch_body`, `ForNode.iter_bodies` and its
precomputed-text guard, `CitryRender`, the physical-region wrappers,
`_merge_dependencies`, `_append_frame_parts`, `Component.transparent` and the
dependency extension's context merge. Keep the fixed trusted Button/Icon/HeroIcon
contract from iteration 66, with immediate execution only. Preserve those measured
sources and use that implementation as the control.

Walk selected function bodies into one ordered parts buffer. Branch selection and
loop iteration use their existing helpers. Nested selected functions append into
that buffer; ordinary nodes, child components and slots may still append structured
parts. Supplied content uses its original caller variables and normal slot handling.
Do not evaluate a value twice to decide whether it needs structured output.

Wrappers share their caller's collected-data dictionary while retaining fresh
variables. Complete text can return as one string; mixed output retains an interior
render for the scheduler. Keep ordinary context merges at the containing boundary
and preserve error propagation. Internal merge-hook observation changes when an
interior render is omitted, so arbitrary custom merge hooks remain unqualified.
Caller on_render hooks can inspect result.parts; hooks inspecting or modifying
function interior structure also remain unqualified because that structure changes.
Whole-result replacement and recovery hooks need their own checks.
HeroIcon retains its existing render-local pure-body key and replay mechanism,
storing a text part when its fixed body finishes without metadata or graph effects.

Transparent callers use iteration 66's path because serialization may surround
a transparent component's interior output with identity markers. Preserve ordinary structured foreign
renders and physical regions. The existing parser/compiler and native artifact
remain unchanged; there is no new build requirement.

## Checks before timing

First compare complete serialized output, including framework markers, and all
server ownership snapshots with the immediate control under deterministic IDs.
Check fixed callback/outlet activation and operation counts on large and reduced
inputs. Test dynamic whitespace, branches, loops, nested ordinary children, source
and physical slot ownership, transparent callers, metadata, changed values, errors
and callback order. Browser checks must retain caller state, ordinary child
isolation and click behavior. If any case differs, read its source and retain the
failure before changing the design. No timing claim is justified by object counts.

A successful candidate then gets a predeclared fresh-process paired comparison
against iteration 66's immediate mode. Advance qualification if median paired warm
wall savings reach 0.25 ms and both wall and CPU improve in at least seven of eight
pairs. This is a practical screening rule. Main timing must not overlap tests or browser work.
This remains an experimental API contract, not a production adoption or Django
parity claim.

The first large-page check matched full HTML and ownership snapshots but ran one
fewer Icon and HeroIcon callback: returning text let an enclosing pure component
capture the function output as a reusable body part. Keep a small FunctionRender
around text returned to a pure caller so that its function call remains live.
This experiment must keep the existing callback counts; skipping them would be a
separate purity-contract change. Retain the initial counts in `function-text-first.json`.

## Timing after bounded qualification

Use eight fresh-process pairs, with each variant first four times and shuffled
order using seed 20261104. Pair members share a Python hash seed. Each worker reuses
iteration 66's loop: six initial renders, then 80 warm renders with ordinary GC,
changing IDs every time and retaining all 86 output strings until timing ends.
The control is iteration 66's immediate composition, not ordinary Citry. Compare
within this experiment and do not add savings from separate runs.

All paired raw output digests must match, including framework markers and dependency
payloads. The existing worker also validates every raw browser manifest and output
projection after timing, checks fixed function counts and all four graph-count
vectors, and retains a normalized full-snapshot digest from an untimed observation.
Require matching activation records and observed snapshot digests between pair
members. Freeze measured sources and check their hashes after the run. Record
actual second renders separately; a short smoke pair validates the harness only.
