# Design: component tracing

**Status (2026-07-22): exploration, not yet approved for implementation.** This
document collects the request-level observability work needed by a future
debug-toolbar extension. It is separate from the registry-backed runtime
component catalog in
[`component_introspection.md`](component_introspection.md).

For the implemented visual boundary extension see
[`extensions_debug.md`](extensions_debug.md). For the extension backlog see
[`extensions_roadmap.md`](extensions_roadmap.md). For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Scope and terminology

Component tracing records runtime attempts. Rendering and serialization are
separate operations: one `CitryRender` may never serialize, or it may serialize
more than once. The design therefore uses an immutable `RenderTrace` for one
render attempt and an immutable `SerializationTrace` for each serialization
attempt. A context-local collector can group those records for one host request.

Structured component tracing is distinct from Python TRACE-level log output.
Logs are prose for operators. The structured records are versioned values that
a tool can query without parsing log messages.

The first consumer is expected to be a `debug_toolbar` extension. That name is
deliberately distinct from the shipped `debug` extension, which inserts visual
boundaries into HTML.

## 2. Relationship to component metadata

Each traced component occurrence records `engine_id`, `class_id`, and
`definition_id`. The triple joins exactly only when a retained
`ComponentCatalog` contains that matching generation. A snapshot may predate
registration, follow removal, or exclude a built-in, in which case metadata is
absent rather than guessed. `class_id` alone is insufficient because separate
engines can define the same package component and a hot replacement at the same
Python path intentionally reuses it.

For a current lookup, a consumer starts from a `Citry` instance whose
`engine_id` matches the occurrence, calls
`Citry.get_component_by_class_id()`, passes the resulting class to
`Citry.inspect_component()`, and compares the returned `definition_id`. A
mismatch means the trace describes an older class generation. If the consumer
does not have the matching engine or retained catalog entry, it marks metadata
unavailable. It must not silently attach another engine's or replacement
class's schemas and assets.

The records have different lifetimes:

- a component catalog describes registered class definitions, including ones
  that have never rendered;
- a render record describes one ordered attempt, including work that failed;
- a serialization record describes one attempt to turn a `CitryRender` into
  output and emit its final dependencies;
- catalog generation is observational and does not install runtime recording;
- tracing is explicit instrumentation and has per-operation cost.

Neither API embeds the other. A toolbar may retain catalog and runtime snapshots
and join them by `(engine_id, class_id, definition_id)`.

## 3. Required value model

The exact public Python records and serialized schema need a later approval
round. The minimum immutable `RenderTrace` must represent:

- a render trace ID and start/end monotonic times;
- total elapsed time and final success or failure status;
- one ordered component-occurrence record per attempted component;
- a recorder-owned occurrence ID allocated before component instance creation;
- each occurrence's `engine_id`, `class_id`, `definition_id`, and nullable
  component render ID, since ID generation itself may fail;
- start, end, elapsed time, and success or failure status per occurrence;
- a bounded redacted error summary for a failed occurrence;
- slot occurrences, requiredness, and fill-versus-fallback results;
- authored invocation and physical placement as separately named relations.

The minimum immutable `SerializationTrace` must represent:

- its own serialization trace ID and the originating render trace ID when one
  is available;
- the origin engine ID and every participating engine ID observed while walking
  the render contexts;
- start/end times, elapsed time, and success or failure status;
- the serialization mode or dependency strategy that affects output;
- dependency kind, public URL, resolved path, and content-hash summaries;
- a bounded redacted serialization error summary.

A render can have zero, one, or many serialization records. Repeated
serialization never mutates an earlier frozen record. Partial work is valid
data: if either operation fails halfway through, its record retains the
completed and active occurrences that explain the failure.

## 4. Observation points and failure isolation

Current extension hooks cannot build these records completely.
`on_component_rendered` observes an error when a component has already produced
a finalize task, but direct failures before that task is queued have no matching
component callback. Slot failures also have no failure callback. Elapsed times
are not captured, and final dependency output exists only during serialization.

A later implementation design must add internal recording points for:

1. component attempt start, before instance and render-ID creation;
2. component success or failure, including direct early failures;
3. slot placement and success or failure;
4. whole-render completion or failure;
5. serialization start and success or failure;
6. final dependency output for that serialization attempt.

These are core-owned recorder calls, not arbitrary extension callbacks on the
hot path. The recorder allocates paired occurrence IDs even when normal nesting
is interrupted. It stores copied primitive/value metadata and cannot replace a
result. If internal recording fails, Citry disables that operation's trace and
logs the recorder error; it does not replace a successful render or
serialization result with an observability failure.

The collector is context-local and propagates through nested calls even when a
foreign `CitryElement` renders through its own engine or a foreign
`CitryRender` participates during serialization. Every recorded occurrence or
serialization participation retains its engine ID, so one host-request group
can be partitioned back into per-engine catalogs without a process-global live
engine registry.

Extensions consume frozen records through the collector API after the observed
operation. If a future completion notification invokes extension code, Citry
must isolate and log that notification's exception so it cannot change the
render or serialization outcome. When no collector is installed, the runtime
keeps its existing short-circuit cost model apart from a minimal disabled check.

## 5. Two component relationships

Citry has no single honest component parent relation.
`Component.parent` records authorship: which component invocation produced a
child. Slot content can then be physically placed inside a different receiving
component. A component supplied through a slot therefore has both an authored
parent and a placement owner, and those relations can diverge.

Runtime records preserve both relations. Flattening them into one tree would
misattribute timing, slot placement, and ownership-sensitive client behavior.
A toolbar may offer separate authored and placed presentations, or annotate one
while displaying the other, but the underlying values cannot discard either.

## 6. Privacy, lifetime, and redaction

Tracing is disabled unless an application explicitly installs a collector. A
context-local collector groups records for one host request and does not enter a
process-global history by default.

The base records exclude:

- raw kwargs and slot values;
- rendered slot or component HTML;
- `State`, template data, JS data, CSS data, and provide/inject values;
- request objects, users, sessions, cookies, and headers;
- exception objects, traceback objects, and local variables.

Errors use a bounded redacted summary with a stable category and safe message
policy. Paths and dependency URLs can still reveal local layout or private
endpoints, so a host toolbar remains development-only and access-controlled.

Finished records contain copied values, not component instances, classes,
slots, requests, or render contexts. Retaining them after unregister must not
prevent plugin unload or class garbage collection.

## 7. Debug-toolbar consumption

The future toolbar can surface:

- ordered render and serialization attempts with timings;
- authored and physical-placement relationships;
- slot fills and fallbacks without their content;
- collected JS and CSS summaries per serialization attempt;
- failures linked to exact or explicitly stale component metadata;
- a catalog join for names, files, and declarations.

Unlike the visual `Debug` extension, the toolbar does not need to wrap component
HTML. It integrates through each supported host's development tooling and is
not enabled as a public production endpoint by default.

## 8. Alternatives and open decisions

Using runtime records as the component catalog was rejected. Components that
have not rendered would disappear, ordering would depend on traffic, and
ordinary tooling would pay instrumentation cost. Runtime recording is
appropriate here because this API deliberately describes attempted work.

The implementation round still needs decisions for:

- exact collector creation and access from `Citry` and host integrations;
- monotonic duration representation and optional wall-clock timestamp format;
- how a serialization started outside the original request finds or omits its
  originating render trace ID;
- bounded record count, dependency summarization, and truncation markers;
- exception-message allowlisting and path rebasing;
- nested and concurrent render isolation;
- polling partial internal state versus publishing frozen records only after
  each operation;
- host integration and authorization for ASGI, WSGI, Flask, FastAPI, and Django.

Those choices belong to this design and must not add request-state fields to
`ComponentInfo`.
