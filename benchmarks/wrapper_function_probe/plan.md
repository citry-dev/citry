# Iteration 65: render a presentation wrapper as a template function

The large page renders 114 Button components. Its fixed template chooses an anchor
or button, computes ordinary attributes, and inserts one default body. The wrapper
has no own assets, JS/CSS data callbacks, render hooks or instance-dependent data
function. Many callers supply Alpine attributes, so restricting this investigation
to output without Alpine would exclude the main case.

## Prior art and proposed contract

Read `test_benchmark_citry.py::Button`, `ComponentNode.render`, `_collect_slots`,
`SlotNode.render`, `_render_body`, `CitryContext` and `CitryRender`. The ordinary
component tag captures lazy fill objects, records an invocation, and schedules a
component. The slot later selects a fill and records a physical placement because
the component that wrote the body can differ from the component that places it. Iterations 55 and 56 tried
to reduce that machinery while preserving its public customization points;
iteration 63 instead removed independent identity from a leaf.

Test a larger distinction: a trusted presentation template can accept caller
content without becoming a component. Intercept direct tags for the exact benchmark
Button. Resolve ordinary kwargs, validate and copy the resolved built-in values, construct its
existing typed kwargs and run its existing data function without an instance.
Walk its unchanged compiled template in a fresh variable scope belonging to the
caller. Its one default outlet executes the captured body with the caller's
original variables. Neither the wrapper nor this insertion needs a new ownership
boundary when both belong to that same caller. Existing surrounding slot ownership
must remain live.

This first prototype also executes the wrapper immediately while walking its
caller's template. That removes its deferred descriptor and scheduling work, but
changes callback, body-expression and error order relative to other siblings.
Registered data callbacks must be side-effect-free; component initialization, data, and completion hooks and slot hooks do not run for this template function. Ordinary context
merge hooks still run when interior renders join; custom merge hooks are unqualified. This is an explicit API restriction,
not an automatic optimization of ordinary Component classes. Keep ordinary child
component execution deferred inside caller content.

Support only direct registered tags with an implicit default body. Reject named
fills, component client bindings, range metadata, globals, and unsupported custom
values in the resolved kwargs. Tag expressions and spreads still resolve through
ordinary Citry before that validation: a custom spread mapping can execute its
methods there. This is not a sandbox or a promise to reject arbitrary caller code. The fixed callback/template and module data are trusted; this is not
a general template classifier or a public API. The template exposes no slot data,
fallback handle, required outlet or custom slot hooks. Root and descriptor-based
uses continue through ordinary Citry because this prototype selects direct tags.
Alpine attributes passed in kwargs belong to the caller; losing wrapper isolation
is intentional. General hooks, Events, morphing and development provenance are
outside this experiment's claim.

## What would disprove the design

First check the complete large page and reduced inputs. Retain raw graph snapshots
and validate emitted browser manifests. Compare visible HTML after removing the
framework metadata affected by the changed contract; that comparison alone cannot
establish browser ownership behavior. Independently count removed wrapper instances,
fills, invocations and regions, and ensure all nonselected components still execute.
Any unexpected content change, missing application callback, graph validation error
or wrong lexical scope requires investigation before a main performance claim.

Then use focused wrappers with changing input values, plain and nested content,
errors, unsupported inputs, and wrappers inside supplied slots. Browser checks must
exercise caller attributes and a source caller different from the physical receiver.
A ContextVar selects the wrapper outlet while its template runs; supplied content must return to ordinary outlet handling. Do not change the
production runtime or measured iteration 63 sources.

Only after qualification define and run a fresh-process timing comparison. No
speedup is claimed from operation counts or a one-off diagnostic time. A passed
prototype remains an experimental API proposal until broader qualification and the
final repository gate.


## Timing screen after the bounded checks

Compare ordinary Citry with the Button function alone in eight fresh-process pairs,
with each variant first in four pairs and shuffled pair order (seed 20261101).
Run six initial and 80 warm renders per process, keeping ordinary GC and changing
IDs for every render. Retain all output strings until timers stop, as iteration 63
did, then validate every raw browser manifest and compare every full application
HTML projection. This is roughly 87 MB of retained output per process; only compare
variants within this experiment. Record actual second renders separately.

The screen is at least 0.25 ms median paired reduction in process mean warm wall
time and at least seven of eight pairs improving both wall and CPU time. Passing
justifies broader API qualification, not production adoption. There is no new
build/distribution requirement and no 1 ms threshold. Do not run browsers, tests,
builds or independent timing beside the main comparison. Check runtime activation
outside timers and compare nonselected component call counts between each pair.
The weaker graph oracle remains an explicit limitation: whole projected HTML plus
bounded browser cases does not prove arbitrary ownership and lifecycle behavior.
