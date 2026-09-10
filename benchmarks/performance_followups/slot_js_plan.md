# Avenue 3: named content with static Alpine registration

This is the third of the four authorized avenues. It evaluates one contract and
does not change runtime code, public declarations or the published benchmark.
No timing is authorized during this qualification.

## Prior art and the distinct case

- `packages/py/citry/tests/test_benchmark_citry.py:1867`: ExpansionPanel renders
  19 times, has two named outlets and registers a static Alpine factory. Its
  Python data callback does not use `self`; per-panel state is in Alpine.
- The same file at `2784`: Form renders 14 times and has a static Alpine factory,
  a default outlet and three named outlets. Its Python callback does not use
  `self`. Static registration therefore does not imply a stateless browser.
- The same file at `2048`: Tags renders 16 times and reads `self.raw_slots`; it
  fails the proposed callback restriction and is excluded.
- `citry/_simple_declarations.py:79` rejects assets and instance behavior.
  `citry/_simple_runtime.py:107` accepts only default content, while its
  `SimpleContent.render` and `render_simple_outlet` preserve Python source
  context without creating the receiver's ordinary slot boundary.
- `citry/component_render.py:1045` constructs the instance, binds supplied
  slots, initializes extensions, runs input/data/render hooks and schedules
  finalization. An instance-free contract could omit these receiver ceremonies.
- `citry/nodes/__init__.py:2041` records ordinary outlet selection and supplies.
  `citry/ext/dependencies/extension.py:203` captures assets with component IDs.
  Asset emission and retirement currently use instance ownership too.
- `packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py:43` proves supplied
  named content reads caller Alpine state across a receiver's local `x-data`.
  Python source context alone does not establish this browser behavior.

Paths beginning with `citry/` above are relative to `packages/py/citry/`.

## The one proposed contract

An explicitly opted-in template may have literal named outlets and static
Alpine registration JS. Its synchronous static Python callback uses only current
kwargs and supplied slots. It has no Python instance, server events, dynamic
JS/CSS data, authored component hooks, custom extension configuration or
receiver replacement. Supplied content must retain the ordinary caller's
browser scope and event target. The receiver's own Alpine factory must still
create independent state at each authored `x-data` element.

The candidate mechanism is lowering named supplies to lazy caller-owned content
and hoisting the static registration into a retained ancestor's assets. It
omits the receiver's component and slot ownership records. The potential saving
is orchestration for the 33 Form/ExpansionPanel calls, not their callbacks or
browser functionality. This screen alone does not qualify those declarations.

An alternative would retain a lightweight browser identity and the ordinary
fill projections while omitting Python instance hooks. That is a different
mechanism, not a second candidate to pursue in this bounded avenue.

## Eligibility, errors and falsification

Arbitrary static JS is not safe to hoist just because it has no Python inputs.
The proposed initial eligibility requires an explicit promise of a self-contained
Alpine factory with no `$c`, instance-addressed API, server event or CSS-variable
dependency. Named outlets are literal, with no fallback, scoped data, required
flag or slot hook. Reject unsupported declarations and call shapes; never drop
their behavior or silently fall back. Callback errors must still reach the
enclosing ordinary error boundary. These are proposed restrictions, not a new
public flag or an implemented validator.

The first qualification checks the smallest supported named-slot case: a
receiver registers a static factory with `owner` and `count`, and receives a
named button from a caller that also has `owner` and `count`. The expected button
reads the caller's owner and increments the caller's count. The receiver's own
button must continue to increment the receiver's separate count.

The executable witness manually lowers that one named outlet to the existing
simple default-content path and hoists its identical JS into the page. It is
only a model of the proposed lowering, not an implementation of general named
slots. All authored elements, expressions and factory code remain present.
Check registration activation, evaluated scope, click routing, page errors and
console errors in Chromium, Firefox and WebKit. A scope or event-target change
falsifies this mechanism before any performance measurement. HTML projection
alone cannot qualify it. Failure ends this avenue without a revised candidate.

## Qualification outcome

The witness rejects this candidate in Chromium, Firefox and WebKit. The control
fill reads `owner == 'caller'`; clicking it changes caller/receiver counts to
`1/0`, then clicking the receiver's own button produces `1/1`. The lowered fill
instead reads `owner == 'receiver'`; its click produces `0/1`, and the receiver's
own button then produces `0/2`. Both modes activate the same static Alpine
factory and report no browser or console errors.

The removed boundary carried an observable distinction between the supplier's
scope and the receiver's local state. Static JS and an instance-independent
Python callback do not make that distinction unnecessary. Named-slot support
cannot be added to this lowering by selecting a different lazy content value
alone. Preserving the contract requires a representation of the scope crossing
that the tested mechanism removes. Accepting receiver-scope fills instead would
be a different public contract, not a correctness fix to this candidate.

This is a counterexample to this one mechanism, not proof that every broader
slot/JS API or lighter server instance is impossible. No full-page prototype,
timing or speed claim follows. The proposed class eligibility validator, lazy
asset registration, replacement handling and error integration were not built
because the minimal browser contract already failed. The 33-call inventory is
an opportunity screen, not a measured count of safely removable instances.

Evidence: [browser witness](slot_js_witness.py) and
[retained results](../results/performance-render/followups/slot-js-witness.json).
Run the witness with
`python benchmarks/performance_followups/slot_js_witness.py` from the repository
root. It exits unsuccessfully if the control fails; the JSON records candidate
rejection explicitly rather than treating a rejected research idea as a broken
test. No runtime monkeypatch is installed.
