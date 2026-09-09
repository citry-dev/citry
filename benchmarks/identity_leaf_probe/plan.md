# Iteration 61: render a selected leaf without a live component

## Prior art and hypothesis

Iteration 60 showed that trusted scalar templates can approach template-engine
throughput when each call skips the component lifecycle. Those standalone calls
also skipped the root ownership graph and document serializer. Nested components
already share those costs, so their result cannot be multiplied by the leaf count.
Iteration 59 found 41 HeroIcon calls in the large page, with no observed slots,
assets or client behavior. Its data method uses only kwargs and module constants.

`ownership.py:1349` binds an occurrence using IDs and class metadata without
retaining its Component argument. `citry_render.py:155` stores IDs and root-marker metadata separately in RenderFrame. `serialize.py:301` uses that frame for root
markers. Test whether a selected leaf can keep its identity and full ownership
records while omitting the live instance and lifecycle. This is an explicit
restricted-contract prototype, not an automatic classification of arbitrary
components or a production API.

## Candidate and restrictions

Intercept only the benchmark's exact HeroIcon class at `_render_one`. Reuse its
compiler, typed kwargs, data function, node renderer, attribute escaping and the
ordinary outer scheduler and serializer. Bind a temporary metadata holder through
the existing ownership API, retain a fresh root frame, and settle the invocation
at the normal finalize stage. The metadata holder supplies the binding fields and is not retained in the
returned render. It is not a Component and has no hooks or extension configurations.

The selected contract requires an ordinary enclosing component; direct root
rendering is rejected. It takes exact dictionaries and built-in scalar/container
values, also accepting Citry's Const wrappers by reading their underlying values.
It requires no supplied slots, component-tag client bindings, dynamic ordinary-element morph metadata,
forwarded invocations or template overrides. It excludes template globals,
instance/self/parent/provides access, render replacement, component hooks,
per-instance extension participation, assets and JS/CSS data. Ordinary enclosing
components retain their behavior. A parent context-merge hook still runs, but
sees no live child Component. Inspecting that child instance is a lost capability.

The trusted HeroIcon body is fixed for this experiment. Only a small explicit set
of ordinary SVG attributes is accepted in spreads; custom objects, renderables,
client/event directives and unknown attribute names raise before body rendering.
The existing data function runs with `self=None` and empty slots. This is an
explicit adapter for the inspected method, not a general proof of callback purity.
Unsupported input is rejected before body rendering; supported value changes
are read on every call.
The candidate walks its prepared body each call and adds no output cache; the
ordinary reference retains its current pure-body optimization.

A fully inline function that also removes identity is an alternative, but would
change markers and ownership simultaneously. Retaining identity first measures
whether instance capabilities themselves carry a useful full-page cost. No Rust,
Cython, ABI, compiler output, public type or production file changes are required.

## Evidence and decision

Before main timing, compare initial and repeated complete HTML and all four
canonical ownership snapshots. Exercise both benchmark data sizes, changing icon
inputs, attribute escaping, invalid variant/schema inputs and rejected contract
features. Count selected calls and omitted instance initialization outside timers.
Use eight balanced fresh-process pairs, six initial plus 80 warm renders each,
ordinary GC and all samples retained. Run no tests/builds during main timing.
Report second-call results separately. The ordinary full-page screen remains
at least 0.25 ms median paired warm wall saving and seven of eight joint wall/CPU
wins; there is no extra build burden to justify a 1 ms requirement. This screen
justifies further qualification, not production adoption of the restricted API.
HTML/ownership drift on supported inputs or no useful full-page saving falsifies
this candidate as written. Keep the outcome and limitations even if it fails.
