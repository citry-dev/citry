# Iteration 62: retain body reuse and measure the validation contract

## Prior art and question

Iteration 61 preserved checked identity and HTML without live HeroIcon components,
but was 0.154 ms slower on the whole page. Its diagnostic found 1,804 recursive
value-validation calls and 82 attribute regions per page. Ordinary Citry renders
11 distinct icon bodies and reuses prepared output for 30 other calls, resolving
only 22 attribute regions. Compare whole-page variants that separate these costs.

The current pure-body implementation lives in `_pure.py:72` and
`component_render.py:1390-1480`. Its lookup, output capture and replay helpers can store strings and transparent
render structure, then rebuild that structure with the current context without
a live component. The general capture procedure checks i18n and ownership effects
around each node. The inspected HeroIcon body reads ordinary values and emits SVG
markup, so this experiment can capture its output without constructing i18n
configuration.

## Four variants

1. `reference`: ordinary Citry, including its current pure-body reuse.
2. `guarded`: the unchanged iteration 61 candidate with recursive input/output
   checks and no pure-body reuse.
3. `reuse`: restore existing render-local pure lookup, detached-part capture and
   replay to that candidate. A cache miss walks the fixed body, checks for new
   ownership/extension state and unsupported parts, and stores its detached plan.
4. `contract`: retain that reuse and validate/copy caller input once. Check incoming
   attribute names, construct the same typed kwargs and run the same application
   data function. Omit the second full input check and recursive output checks.

The last variant makes an explicit additional promise: the registered trusted
callback and its module data produce only the declared ordinary SVG values and
remain valid for the lifetime of the registration. The fixed HeroIcon template reads attribute mappings and loops over icon paths;
it contains no slots, child components or i18n calls. The
fixed callback is inspected, not automatically proved safe by the prototype.
Runtime value changes within admitted caller inputs remain supported. Replacing
that callback or mutating its module data to violate the promise is outside this
contract; output violations are not guaranteed to be detected or safely rejected.
This is an internal mechanism study, not an application-facing API or a sandbox.

The contract still rejects custom objects/renderables in caller inputs, unknown
SVG attribute names, slots, globals and direct root calls, and retains typed
kwargs construction and application error behavior. It keeps ownership records,
IDs, frame markers and outer scheduling/serialization. Remaining restrictions
and lost component/extension capabilities are those of iteration 61, including
omitted template/attribute extension rewrites. No production source, compiler
output, native build, ABI or Cython changes.

## Falsifiers and measurement

Before timing, run the retained supported-output, ownership, error and input
rejection checks for both new variants. Check repeated values within one root
render actually use detached plans, keep fresh IDs, and read changed input on
subsequent roots. Use eight fresh-process blocks with balanced cyclic orders for
all four variants, six initial and 80 warm full renders per worker, ordinary GC
and every sample retained. No tests or builds during main timing. Compare all
HTML digests and four canonical ownership snapshots for every variant. Count
selected calls, initializations and new-variant cache hits outside timing.
A pre-timing observation finds 32 hits in each new variant: the retained input
normalization unwraps nested Const markers completely, while ordinary pure keying
unwraps one layer. Five ordinary calls have a doubly wrapped stroke-width value;
ordinary lookup has 11 distinct keys, versus nine after normalization. This changes
reuse opportunities but not the checked HTML or ownership. Report second renders separately.

The decision compares the final contract variant to ordinary Citry: at least
0.25 ms median paired reduction in mean warm wall time and seven of eight joint
wall/CPU wins justify further qualification. This is the same full-page criterion
as iteration 61; no extra build complexity requires a 1 ms saving. Other contrasts
explain costs and do not select a favorable subset of measurements. Output/graph
drift on admitted inputs falsifies the candidate as written. A passed screen
would qualify further API design and browser testing, not production adoption.
