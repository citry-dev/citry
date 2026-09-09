# Iteration 64: qualify caller-owned SVG in the browser

Iteration 63 passed its whole-page performance screen with a changed contract:
selected icons have no independent identity or Alpine isolation. This experiment
checks how that change behaves with caller state, supplied slots and Alpine.

Existing coverage in `test_alpine_slot_scope_e2e.py` and
`test_ownership_manifest_e2e.py` checks ordinary isolation, source-owned fills and
client graph reconstruction. `test_alpine_structural_e2e.py` and section 8 of
`docs/design/alpinejs.md` establish a separate restriction: Citry rejects
client-active components under native Alpine structural templates. The shipped
`citry.js` function `rejectStructuralComponentClones` enforces that before graph
activation by looking for component roots inside template contents.

The initial combined fixture hit that restriction in the ordinary reference.
Its original sources and failure are retained. Split the cases before running the
qualification: ordinary slot behavior must work for all three variants; structural
templates must retain the existing rejection for the two variants with identity.
The caller-owned candidate must work in all cases without changing its adapter.

Render the unchanged selected HeroIcon under an ordinary caller, a supplied fill,
and a receiver fallback. Compare ordinary Citry, iteration 62's identity-preserving
function, and iteration 63's inline function. Ordinary and identity-preserving
icons must remain isolated; inline icons must see their lexical caller's Alpine
scope. The fallback belongs to the receiver, and the supplied fill belongs to its
source caller. Click actual SVG paths and verify handlers update the intended state.

Test x-if and x-teleport separately. For ordinary and identity-preserving variants,
require the specific clone error and zero activated graph revisions/anchors.
For inline output, verify caller scope and clicks; repeatedly destroy/recreate the
conditional icon and check behavior afterwards. The teleport originates inside a
supplied fill and moves outside its physical receiver and caller. Accepted cases
must leave exactly one graph revision and report no browser or console errors.
Run installed Chromium, Firefox and WebKit. Record missing browsers and failures
explicitly, keep remaining independent cases running, and return a failing exit
status if any required check fails.

This is bounded browser qualification, not timing, a public API or the final
repository gate. It does not establish server Events, keyed morphing, independent
icon lifecycle, arbitrary callbacks, custom directives or general slot topologies.
A wrong scope, lost click, stale recreated icon or client graph failure falsifies
the candidate for that case. Preserve failures and read the implementation before
changing the proposed contract or test. Production and measured iteration 63
sources remain unchanged; runtime fixes require a separate candidate or experiment.
