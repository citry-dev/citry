# Proposed framework rendering and interaction benchmarks

Status: design only. Sources checked on 10 September 2026. No adapters,
dependencies, benchmark runs or comparative results are delivered by this document.
Select and lock exact released versions, browser builds and protocol versions
when implementation begins; the linked `latest` documentation is not a version pin.

The proposal compares the cost of delivering the same working interface through
different architectures. It keeps Python HTML generation, initial page readiness
and interactive updates separate. A fast serializer does not establish a fast
interactive application, and a compiled browser application is not a Python HTML
template engine.

## Existing work and scope

[The rendering design](benchmarking.md), especially sections 5 and 6.5, establishes
fresh-process measurements, idiomatic ports and release native builds. The current
[benchmark README](../../benchmarks/README.md) distinguishes first, actual second
and warmed renders, and explains that the ports emit different bytes and features.
Its existing large page is a useful source of data and UI complexity, not proof
that all ports implement equivalent browser interactions.

[A10](alpinejs/a10_performance.md) and [the client runner](../../benchmarks/client.py)
already measure Citry document activation, fragment adoption, morphing and resource
budgets. That runner serves prepared documents through a test server; it does not
measure a fresh production request's rendering cost. Its animation-frame settlement
and Citry-specific readiness checks are prior art, not a portable definition of
interactivity. Keep those regression budgets intact.

[Codebase build and dependency rules](../codebase.md) require checking the actual
imported native artifact and using a release build for timing. Any later adapter
dependencies belong to explicitly owned benchmark environments. This proposal
does not change the root lockfile or install another framework into Citry's runtime.

## Cohort and the question each entry answers

The proposed core interactive cohort has seven framework families. Selection
prioritizes architectural coverage and the requested comparisons, not a claimed
popularity ranking. Use one qualified Citry configuration in public comparison
charts, with an asterisk linking to the
[performance guide](../../docs_site/content/advanced/performance.md) and a precise
list of opted-in declarations. Default versus `simple` belongs in internal
diagnostics or a separately labeled ablation, not two headline Citry entries.

| Core entry | Documented architecture | Why include it; feasibility condition |
| --- | --- | --- |
| Citry | Python component rendering with browser ownership, Alpine and server events | Subject of the comparison. Keep the selected production configuration's actual dependencies, scope rules and event behavior. |
| Django templates + HTMX + Alpine | Python HTML rendering, HTTP fragment replacement and local browser state | Explicit conventional composition baseline. HTMX requests typically receive HTML; it is a browser library, not another Python renderer. [HTMX documentation](https://htmx.org/docs/) |
| FastHTML | Python FastTags on Starlette, with HTMX for hypermedia interactions | Covers a Python HTML construction API rather than a Django template language. Include its normal response processing and required browser assets. [Official technical stack](https://fastht.ml/about/tech), [concise reference](https://www.fastht.ml/docs/ref/concise_guide.html) |
| Tetra | Django components with Alpine; public Python methods and server-rendered updates | Closest explicit slot/JS component comparison. Current protocol documentation describes HTTP method calls and WebSockets for realtime updates. Pin the chosen transport and verify it in the installed release. [Introduction](https://tetra.readthedocs.io/latest/), [protocol](https://tetra.readthedocs.io/latest/development/protocol_specification/) |
| django-unicorn | Django templates plus serialized component state, AJAX actions and DOM updates | Covers component reconstruction and server rendering after actions. Preserve its state/checksum and request queue behavior. [Architecture](https://www.django-unicorn.com/docs/architecture/) |
| Reflex | Python-defined UI compiled to a React frontend, Python backend state and WebSocket events | Covers a compiled frontend with server-held application state. It must not receive a Python HTML-render timing by timing frontend compilation or returning a static shell. [Architecture](https://reflex.dev/docs/advanced-onboarding/how-reflex-works/), [state](https://reflex.dev/docs/state/overview) |
| ReactPy | Python components and event handlers connected to a browser client, including WebSocket mounting | Covers Python-driven component/layout updates. Qualify a supported production backend and its actual client protocol; a Python layout/model is not serialized HTML. [Running ReactPy](https://reactpy.dev/docs/guides/getting-started/running-reactpy.html), [events](https://reactpy.dev/docs/guides/adding-interactivity/responding-to-events/index.html) |

Freeze Citry's host integration and production server before the pilot. A bare
WSGI/ASGI integration and a Django-hosted integration are distinct stack entries;
select one for the public comparison and name it in the configuration manifest.

These are nominations, not assertions that every adapter already supports every
scenario. Tetra's introduction explicitly cautions that its API is still evolving.
Record unsupported cases and installation/production feasibility failures instead
of removing a framework from the report after seeing its timings.

Adoption evidence is limited and separately labeled: Django's official overview
documents its use on large sites; Reflex publishes named customer accounts,
including Dell. The latter is vendor-published customer evidence, not an
independent census or comparative performance study. This review found sufficient
official architecture and working-example documentation to nominate the other
requested projects, but did not establish comparable production deployment counts
for them. Neither GitHub stars nor vendor performance claims determine inclusion
or a ranking. [Django overview](https://www.djangoproject.com/start/overview/),
[Reflex customer account](https://reflex.dev/customers/dell)

Secondary entries are additions after the core adapters pass the common contract:

| Entry | Placement and limitation |
| --- | --- |
| Jinja2 + HTMX + Alpine on Starlette/FastAPI; Flask as a separate backend variant | Useful alternative template and request stack. Name the complete stack in request charts. Jinja is the renderer; FastAPI documents using Jinja templates but does not itself become a template engine. [Jinja](https://jinja.palletsprojects.com/en/stable/), [FastAPI templates](https://fastapi.tiangolo.com/advanced/templates/) |
| django-components + Django + HTMX + Alpine | Retains the existing component-render baseline while adding an explicitly implemented interaction layer; django-components alone does not supply this whole interaction stack. |
| Django or Starlette/FastAPI JSON API + Vue | Browser-rendered UI with a Python API. A progressively enhanced Vue island and a full SPA are distinct configurations. [Vue usage modes](https://vuejs.org/guide/extras/ways-of-using-vue.html) |
| The same Python JSON API + React | Browser-rendered UI with a Python API; isolate frontend choice by sharing the API and data contract with the Vue entry. [React client APIs](https://react.dev/reference/react-dom/client) |
| React or Vue SSR followed by hydration, alongside a Python API | Separate full-stack comparison with the JS rendering service, build output and resources included. Do not label it Python server HTML rendering or hydrate arbitrary Django/Jinja markup as if it were matching framework SSR output. [React server rendering](https://react.dev/reference/react-dom/server/renderToString), [Vue SSR](https://vuejs.org/guide/scaling-up/ssr) |
| Dash, Streamlit and NiceGUI | Secondary dashboard/UI cohort if the common behavior can be implemented without replacing each framework's model. Dash uses reactive callbacks, Streamlit has explicit rerun/session-state concepts, and NiceGUI exposes browser widgets from Python. Qualify equivalent widgets and session behavior first; do not place their Python component construction in the HTML-render table. [Dash callbacks](https://dash.plotly.com/basic-callbacks), [Streamlit execution model](https://docs.streamlit.io/develop/concepts/architecture), [NiceGUI official repository](https://github.com/zauberzeug/nicegui) |

Avoid the Cartesian product of every backend, template engine and browser library.
Each secondary entry must answer a named question before expanding the matrix.

## Three separate experiments

| Experiment | Timed work | Eligible entries and exclusions |
| --- | --- | --- |
| Python server HTML microbenchmark | Current prepared data to fully serialized output, including escaping and required per-render metadata | Citry, Django templates, Jinja2, django-components; add FastHTML's actual HTML serializer after qualification. Tetra/Unicorn render entry points may be added only with their request/state dependencies explicit. Reflex/ReactPy layout generation is not an HTML entry. |
| Initial request to interactive UI | Navigation/request, server work, all required assets, transport setup, DOM construction and behavioral readiness | All qualified interactive stacks. A shell, SSR HTML or first paint is an intermediate observation. |
| Server event to interactive updated UI | Real user event, client queue, request or socket message, server action and committed state, update delivery and working updated controls | All qualified interactive stacks. Client-only actions are measured separately and cannot stand in for a server event. |

For the microbenchmark, report startup/initialization separately, actual first
and second renders separately, and a predeclared warm sequence. Template parsing
and lazy compilation belong to the call that performs them. Build-time frontend
compilation belongs to build/startup reporting, not a fictional first Python render.
Validate all outputs after timing. Normal GC remains enabled. Document whether
results stay alive through a block, as in the historical publication harness, or
are consumed and released between calls; never compare these lifetime policies
as the same experiment.

Do not subtract the microbenchmark from navigation latency and label the remainder
"JavaScript." It also contains routing, queues, network, decoding and scheduling.
Stack-level measurements use actual request and event paths with rendering inside
the measured transaction, not pre-rendered strings prepared by the harness.

## HTML and network sizes

Record sizes alongside each experiment, not just timing:

| Measure | Definition |
| --- | --- |
| Server HTML output size | UTF-8 byte length of the fully serialized HTML emitted by an HTML renderer, before transfer compression. A shell is labeled as a shell. |
| Final browser HTML size | UTF-8 byte length of the document type plus serialized document element at readiness, after initial activation and after each measured update. Capture outside the timed interval. This is a representation of the final DOM, not browser memory usage or necessarily the original response bytes. |
| Total initial page payload | Sum every response body needed to reach initial readiness: document HTML, separate JSON/data responses, JS, CSS and other required assets, plus server-to-browser bootstrap messages on persistent connections. Report request count and a per-resource breakdown alongside the total. |
| Server-action request size | Sum browser-to-server request bodies or application messages attributable to the action, including additional requests, retries and required control messages. |
| Server-action response size | Sum server-to-browser response bodies or application messages needed to apply the final correlated revision and return to readiness. An acknowledgement alone is not the complete response. |

For network payloads report both decoded application bytes and actual encoded
body/message bytes after negotiated compression. Report headers, protocol framing
and transport overhead separately where measurable; distinguish body totals from
wire totals. Do not mix differently defined byte counters across frameworks.
Count each transferred response once: HTML containing inline JSON or JavaScript
already includes those bytes. Multiple requests for the same resource still count
as multiple transfers. Cached resources contribute their actual transferred bytes
in that cache profile, with the logical resource size recorded separately.

The final-DOM serialization rule is shared by every adapter and retains framework
attributes, comments and scripts. Record the exact serializer and encoding.
HTML serialization does not capture live input properties, listeners, canvas
pixels or all shadow DOM contents; check those behaviors separately and inventory
shadow roots if used. Take comparable full-document snapshots after updates,
while reporting the smaller transmitted update independently.

Correlate HTTP requests and socket messages with the operation and readiness
window. If batched messages include unrelated work, retain the complete batch
and identify that contribution rather than inventing exact attribution. Report
background traffic during the window separately, plus an observed total including
it. Late requests required by the scenario mean readiness was declared too early;
optional post-readiness work is listed separately. Required initial data fetched
through JSON or sockets must never disappear from the page-load total.

## Shared interface and data contract

Start with a framework-neutral specification, fixtures and browser assertions.
Each adapter implements the same visible content, accessible names, inputs,
validation rules, row keys, sorting, state transitions and persistence semantics
using idiomatic public APIs. Equal component counts and byte-identical HTML are
not requirements. Record logical widgets, DOM counts, state records and payload
sizes to explain differences rather than deleting framework metadata.

Use three fixed sizes, 10, 100 and 325 rows/widgets, and deterministic data,
dates, locale, timezone and randomness. The existing project page can inform the
largest fixture after auditing its actual interactions. Ship identical plain CSS,
fonts/icons and asset origins; avoid comparing a rich widget library with bare
HTML. Fix viewport, device scale, reduced motion and animation policy. Include
all rows in the nonvirtualized baseline; virtualized lists are separate variants.

The common sequence covers initial render, row selection, server-side filtering,
valid and invalid form submission, insertion/removal and keyed reordering. An
unchanged sibling must retain its edited input and focus where specified. An
updated control must actually respond again. A local disclosure widget provides
a separate client-only measurement. Where a framework does not implement local
state without a round trip, report that protocol choice instead of calling the
action local or adding a benchmark-only handler that bypasses the framework.

Add named content, scope isolation, multi-root output and component lifecycle
as a feature suite with explicit support cells. Do not demand Citry's exact
ownership implementation from every adapter, and do not treat a failed required
user behavior as a harmless HTML difference. An adapter that cannot meet the
common sequence remains a documented nonparticipant for that scenario.

The primary dataset is a deterministic in-memory domain service with no DB I/O.
Every server action must apply the same transition and return a new server-generated
revision/token; optimistic client text alone cannot satisfy completion. Each
session has isolated state and the same reset contract. Framework-required state
storage, serialization and locks remain in the measured path.

A separate database profile uses one pinned PostgreSQL version, schema, indexes,
seed, isolation level, connection limits and prescribed reads/writes. It resets
mutations between trials. Publish SQL/transaction counts and query durations.
Use the same domain operations; if idiomatic ORMs issue different SQL, label that
profile as a full-stack/ORM comparison. Never preload one adapter's DB result
while charging another for queries. Cold DB caches, artificial delay and external
services are separate scenarios, not hidden parts of the render baseline.

## Behavioral readiness and timing boundaries

Use correlation keys `(run, process, session, navigation, operation, revision)`.
The server echoes the operation key in its acknowledged result, and the updated
UI exposes the revision through normal rendering. For HTTP, correlate the exact
request/response; for sockets, correlate every application message and terminal
update, including batched messages. An unrelated heartbeat or first state message
must not complete the measurement.

All end-to-end elapsed times use the browser document's monotonic clock.
Navigation Timing supplies navigation/request boundaries in the destination
document; `performance.now()` supplies event and readiness marks. Capture the
event start in the browser before framework handling, not around a Playwright
command in Python. Do not subtract server timestamps from browser timestamps or
subtract clocks from different browser sessions. Server-local monotonic durations
can be attached as diagnostics. Timer precision and foreground-tab policy are
recorded. [High Resolution Time specification, current draft](https://www.w3.org/TR/hr-time-3/)

Initial loading and server actions are separate measured flows:

1. **Initial readiness:** start at navigation/request and stop when the required
   interface is present, framework runtime and dependencies have loaded, required
   initialization/hydration and component callbacks have completed, and its
   handlers are attached and able to respond. For Citry this includes Citry and
   Alpine activation; for a Vue hydration configuration it includes hydration
   and relevant initialization. Include required asynchronous initialization;
   unrelated polling or future user actions do not keep the interval open.
2. **Server-action readiness:** establish initial readiness before starting the
   trial. Start the clock at the actual UI action, before framework handling.
   Include client queuing, the server event or REST request, server processing,
   all response messages, DOM updates and any required reinitialization. Stop
   when the correlated new revision is applied and the affected UI can respond
   again. An optimistic update or acknowledgement before the final UI update
   cannot end the interval.

Each adapter defines a `ready` signal from the relevant lifecycle and pending
work, with the exact required callbacks and async work documented per scenario.
This signal is the timing endpoint. Capture the correlated revision and required
initialization/pending-work state synchronously with its timestamp. Later checks
must not validate an early signal merely because initialization finished before
the check ran. There is no additional server-backed action inside either measured
interval. Record DOM commit separately where observable, so initialization after
insertion is visible. Final HTML snapshots taken after timing must still match
the recorded revision, before any verification action changes the page.

Qualify the signal in separate correctness runs: immediately after it fires,
exercise real controls and check handlers, state, focus, selection and sibling
preservation. A server-backed verification action may be used in those runs,
but its duration is not part of readiness latency. Such checks validate the
adapter's endpoint; they do not establish the earliest possible interactive
instant. Record signal limitations explicitly. In timed runs, collect correctness
observations after stopping the timer and reject incorrect outcomes rather than
allowing an early signal to produce a favorable result.

For initial loading, report navigation-start and request-start to readiness,
and time to correct visible content separately. For an update, report event-start
to correlated DOM commit and to readiness. First event after load, warm repeated
events and post-reconnect events are separate cases. Begin every event trial only
after the prior operation has finished and the UI is ready.

HTMX exposes after-swap and after-settle signals; Alpine has initialization
hooks. React/Vue commits and the Python-driven client protocols require their
own adapter signals. None of these signals alone proves every nested control is
usable. `load`, DOMContentLoaded, network-idle and one or two animation frames
are likewise insufficient. Animation-frame callbacks are scheduled before a
repaint; report any paint-settlement approximation separately from
framework readiness. [HTMX events](https://htmx.org/events/),
[Alpine lifecycle](https://alpinejs.dev/essentials/lifecycle),
[HTML animation-frame processing](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#animation-frames)

Qualification must deliberately delay initialization, drop a handler, return a
stale revision and interrupt the transport, disconnecting a socket where applicable
or interrupting an HTTP request. The harness must detect all four fault categories;
otherwise its readiness metric is not qualified. Polling intervals and observer
overhead are fixed and measured in a separate instrumentation check.

## Attribution without inventing an additive breakdown

Collect browser marks for event dispatch, outbound message, response/body or
correlated message completion, DOM commit and readiness. Record navigation/resource
timing for document and asset fetching. Record
server-local routing, state decode, queue/lock wait, domain/DB work, template or
layout generation, serialization and response construction, where available.
Unavailable phases are `unobserved`, not zero.

Use `Server-Timing` or correlated sidecar records for HTTP server durations and
protocol-compatible tracing for sockets. Record every message needed for the
revision, not just the acknowledgement. Use a diagram of overlapping intervals;
parsing, downloads, rendering and application work may overlap. A residual from
subtracting server duration from browser elapsed time is not pure network time.
[Server Timing](https://www.w3.org/TR/server-timing/),
[Resource Timing](https://www.w3.org/TR/resource-timing/)

Profiles and deep instrumentation run separately from headline timings. Keep the
small correlation/readiness hooks identical between measured and qualified builds,
archive their source and quantify overhead. The all-stack verification must not
remove Citry metadata, Reflex state messages or another stack's safety checks.

## Deployment, cache and network profiles

Use production builds, debug/reload disabled, compiled/minified browser assets
and one fixed CPU/memory budget. Select supported production WSGI/ASGI servers;
do not force an incompatible common server. Record all frontend/backend workers,
threads, event-loop and HTTP implementations, state-store processes, affinity,
sticky routing and reverse-proxy settings. The resource budget covers the whole
stack, including Reflex's frontend service or any JS SSR service. The primary
latency run has one active user; concurrency/load is a separate experiment.
Flask explicitly rejects its development server for production, ReactPy describes
backend-specific production deployment, and Reflex documents self-hosting modes.
[Flask deployment](https://flask.palletsprojects.com/en/stable/deploying/),
[ReactPy deployment](https://reactpy.dev/docs/guides/getting-started/running-reactpy.html),
[Reflex self-hosting](https://reflex.dev/docs/hosting/self-hosting/)

Keep authentication/session and applicable CSRF protections equivalent. A
deterministic authenticated fixture can exclude login from the measured operation,
but do not disable security only in a favored framework. Production bundles,
native binaries, OS, Python/JS runtimes and all server commands are pinned and
hashed. No hot-reload or devtools extension runs during measurements.

Declare cache state along independent axes:

| Profile | Process/application state | Browser and transport state |
| --- | --- | --- |
| First request | Fresh processes, documented startup completed; no previous application request | Fresh browser context, empty asset cache, new TCP/TLS and socket sessions |
| Repeat navigation | Warm application; new application session | Asset-cold and asset-warm variants, with actual cache state verified; no BFCache shortcut |
| Repeated interaction | Warm application and same isolated session | Existing page and connection; include normal protocol batching, queues and keepalives |
| Reconnect | Existing or restored session under a declared policy | Deliberately closed connection, handshake and resynchronization included |

Exclude cross-request application/page/result/fragment caching in the primary
comparison while retaining normal template compilation caches, declared
render-local reuse and framework-required state caches.
Report explicit opt-in memoization, `simple`, `pure`, full response caching or
CDN caching in a configuration manifest. A later cache-hit scenario must require
the same invalidation behavior and state lifetime across adapters. An unavoidable
framework cache is described and traced, not silently disabled or called absent.

Primary transport profiles are local loopback and an emulated network with fixed
40 ms RTT, 20 Mbit/s downstream and 5 Mbit/s upstream, no injected loss. Specify
the shaper placement and verify effective RTT/throughput on both HTTP and
WebSockets; a browser-only HTTP throttle is not adequate if it misses sockets.
Treat these values as proposed experimental settings, not representative user
population statistics. Use a separate calibrated slower-client profile rather
than mixing CPUs within a chart. Keep browser/server contention controlled and
record whether they share a machine. Real WAN/cloud runs are separately labeled.

Serve assets locally through the same proxy policy; no public CDN or third-party
font variability. Run an uncompressed diagnostic and a declared production
compression profile. Pin gzip/Brotli implementations and levels, streaming/flush
policy, TLS/HTTP version and negotiated WebSocket compression. HTTP body
compression and per-message socket compression are not interchangeable.
Report raw application bytes, encoded body bytes, and measured transfer bytes
with headers/framing distinguished. Include initial JS/CSS, incremental chunks,
state, bootstrap messages, upload payloads and keepalives for the observation
window. Resource Timing alone does not count an entire socket conversation.

## Trials, failures and reporting

First run a separately archived feasibility/instrumentation pilot. Freeze fixture,
adapter, readiness, timeout, cache, transport and analysis definitions before the
main run. Do not select the fastest pilot configuration without disclosing the
selection process. Allow equal, documented adapter review and tuning effort.

The proposed latency run uses 20 fresh-process blocks per published scenario and
profile, three independent browser sessions per configuration per block, and 20
sequential measured updates per warm session after five prescribed warmups. Balance
framework order with randomized cyclic and reversed schedules. If the cohort size
prevents exact balance in 20 blocks, choose the next balanced block count before
running. Fresh contexts, first events and reconnects are sampled separately;
warmups do not erase their recorded costs. Do not execute different competitors
concurrently during a latency block.

Sessions within a process and events within a session are correlated. Aggregate
and resample whole process blocks, retaining sessions/event order, for paired
differences or log ratios and confidence intervals. Report medians, p95 with
uncertainty, successful-completion rate and full raw distributions; sparse cold
samples cannot support a precise tail claim. Predeclare comparisons to the one
Citry configuration, avoid ranking every pair from noisy estimates, and do not
extend sampling until a preferred winner appears.

Use fixed, profile-specific deadlines, initially proposed as 30 seconds for
initial readiness and 10 seconds for each server-action readiness interval.
Correctness-only verification actions have separate deadlines. Qualify these in
the pilot and freeze them. Keep timeouts, HTTP errors, browser errors, wrong state,
missing acknowledgements, disconnected sessions and retries in the denominator
and raw records. Report timeouts as failures/right-censored latency observations,
not fast samples or deletions. Successful-only latency summaries must show their
success rate beside them. No failed framework receives a winner claim based on
the remaining fast successes. A documented infrastructure failure may trigger a
whole paired block rerun; preserve the original records and the exclusion reason.

For load testing later, define arrival rate, user count, think time and socket
lifetimes explicitly. Report queue growth and offered versus completed work;
closed-loop clients alone can hide overload. Do not mix throughput and idle
single-user latency results.

## Deliverables and implementation gates

Proposed artifacts are a neutral scenario specification, per-stack adapters and
lockfiles, behavioral tests, production launch manifests, a clock/correlation
schema, raw events and failures, compact summaries and trace/asset archives.
Every report names its source commit, dirty state, hashes, browser/server versions,
protocol and cache settings, excluded features and the exact analysis script.

Implement one HTTP stack and one persistent-connection stack first to qualify
the common harness. Then add the remaining nominated frameworks without changing
the completion contract. Separate reports show Python HTML cost, navigation to
readiness, event to revision commit, event to readiness,
payload and failure rates. No combined score hides architectural differences.

An independent technical and prose review must check adapters, instrumentation
and proposed claims before the first public comparison. Full browser behavior,
production feasibility and source pinning remain open implementation gates.
Nothing in this design establishes a winner or a performance improvement.
