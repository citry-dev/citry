# Proposed framework rendering and interaction benchmarks

Status: implementation approved for local development on 10 September 2026.
Sources checked on that date. Comparative results require the qualification and
publication gates below; this document establishes no performance ranking.
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
[performance guide](../../docs_site/content/performance/pure.md) and a precise
list of opted-in declarations. Default versus `simple` belongs in internal
diagnostics or a separately labeled ablation, not two headline Citry entries.

| Core entry | Documented architecture | Why include it; feasibility condition |
| --- | --- | --- |
| Citry | Python component rendering with Vue and server events | Subject of the comparison. Keep the selected production configuration's actual dependencies, scope rules and event behavior. |
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
| Next.js App Router + native Server Actions | Node production SSR/hydration with an RSC/delta update path; initial HTML and update payloads are reported as separate phases. Pin the Node runtime and npm lockfile, and retain the first-stream timing caveat. [Next.js App Router](https://nextjs.org/docs/app), [Server Actions](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations) |
| Nuxt universal SSR + Nitro API | Node production SSR/hydration with SSR payload extraction and native `$fetch` JSON mutations; initial HTML and update JSON are separate phases. Pin the Node runtime and npm lockfile. [Nuxt rendering modes](https://nuxt.com/docs/guide/concepts/rendering), [Nitro server routes](https://nuxt.com/docs/guide/directory-structure/server) |
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

Use the canonical project page at 14 outputs (1x) and 140 outputs (10x), with
deterministic data, dates, locale, timezone and randomness. The opt-in 1,400-output
(100x) profile runs only after reviewing 1x and 10x time and memory use. Scaling
repeats content cohorts inside one project and five phase groups rather than
repeating a flat row template. Ship identical plain CSS, fonts/icons and asset
origins. Fix viewport, device scale, reduced motion and animation policy. Include
all outputs in the nonvirtualized baseline; virtualized lists are separate
variants. Historical 10/100/325/1,000-row reports remain a distinct workload.

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

The maintained local cohort measures two initial readiness intervals before the
action sequence. Both run in the same fresh application server process, but each
uses a distinct logical application session and fresh browser context. The first
therefore includes the process's first measured page request, while the second
observes warmed application and framework state without HTTP browser-cache reuse.
Both loads share a browser process and host state, so their difference is a
repeat-load outcome rather than attribution to server caches. Both use the same
readiness, correctness, phase, preparation, and size contracts. Only the second
page proceeds through actions. A `page_load` ordinal remains separate from the
protocol operation and revision, and reports do not combine the two initial
distributions. With profiles that request more than one session per server
process, only session index zero has the first-request property.

Each adapter defines a `framework-ready` signal from the relevant lifecycle and
pending work, with the required callbacks and asynchronous work documented per
scenario. Record its timestamp separately. On the next all-framework rerun, also
measure one common layout-inclusive readiness endpoint. Schedule the same
`requestAnimationFrame` chain synchronously inside each framework-ready callback.
In the first callback, read `getBoundingClientRect()` for the fixed page root and
last-row targets. Record `performance.now()` at entry to the following callback
as the common endpoint. This includes pending layout work reached by the geometry
read; it does not prove that pixels were painted to the display.

Apply this endpoint to first and second initial loads and to server-action
readiness when an adapter exposes the corresponding ready signal. Run semantic
DOM scans and correctness comparisons only after the second callback. Do not
perform other DOM, style or geometry inspections between framework readiness
and that callback. Keep capture and validation duration separate. Later checks
must not validate an early signal merely because initialization finished before
the check ran. There is no additional server-backed action inside either
measured interval. Final HTML snapshots taken after timing must still match the
recorded revision, before any verification action changes the page.

Historical ready-only observations remain labeled `framework-ready`. Do not
compare or combine them with the new layout-inclusive endpoint. The next
all-framework rerun must collect the shared endpoint for every entry.

Qualify the signal in separate correctness runs: after it fires, exercise real
controls and check handlers, state, focus, selection and sibling preservation.
The synchronous semantic snapshot is exact evidence from inside the callback;
the control exercise is a subsequent qualification. A server-backed verification
action may be used in those runs, but its duration is not part of readiness
latency. Such checks validate the adapter's endpoint; they do not establish the
earliest possible interactive instant. Record signal limitations explicitly. In
timed runs, collect correctness observations after stopping the timer and reject
incorrect outcomes rather than allowing an early signal to produce a favorable
result.

For initial loading, report navigation-start and request-start to both
framework-ready and layout-inclusive readiness. For an update, report
event-start to correlated DOM commit, framework-ready and layout-inclusive
readiness. First event after load, warm repeated events and post-reconnect events
are separate cases. Begin every event trial only after the prior operation has
finished and the UI is ready.

HTMX exposes after-swap and after-settle signals; Alpine has initialization
hooks. React/Vue commits and the Python-driven client protocols require their
own adapter signals. None of these signals alone proves every nested control is
usable. `load`, DOMContentLoaded and network-idle are likewise insufficient.
The second animation-frame callback is the shared layout-inclusive endpoint,
not proof of a physical display paint. [HTMX events](https://htmx.org/events/),
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

Start with Citry and Django + HTMX + Alpine, then add a persistent-connection
stack before freezing the common adapter interface. Then add the remaining
nominated frameworks without changing the completion contract. Separate reports show Python HTML cost, navigation to
readiness, event to revision commit, event to readiness,
payload and failure rates. No combined score hides architectural differences.

An independent technical and prose review must check adapters, instrumentation
and proposed claims before the first public comparison. Full browser behavior,
production feasibility and source pinning remain open implementation gates.
Nothing in this design establishes a winner or a performance improvement.


## Implementation layout and execution

The maintained suite lives under `benchmarks/web/`. Existing server-render,
Citry browser and i18n runners remain independently usable.

```text
benchmarks/web/
  README.md
  runner/
    pyproject.toml
    uv.lock
    src/citry_bench/
  scenarios/project_board/
    specification.md
    fixtures.json
    assets/
    actions.py
    assertions.py
  apps/
    citry/
    django_htmx_alpine/
  profiles/
    smoke.toml
    local.toml
    publication.toml
  tests/
```

Additional applications get their own directories as their adapters are built.
The scenario owns shared data, visible behavior, browser actions and assertions.
Each application implements rendering and interactions through its framework's
public APIs. The runner owns preparation, process management, browser control,
network accounting, raw records and reporting. It does not import competing
frameworks into its own process.

Every adapter declares production launch commands, owned processes, a reset
contract, browser readiness and operation correlation. A server health request
must not exercise the measured page, template or session. Server startup health
and browser readiness are separate conditions. Framework-required helper
processes count toward that application's resource budget.

### Dependency ownership and preparation

The runner and every application are independent uv projects, explicitly excluded
from the root Python workspace. Each owns its `pyproject.toml` and `uv.lock`.
Applications requiring a frontend build own their JS manifest and lockfile too.
They must not modify the shared development environment. Independent projects
allow incompatible dependencies and separate environments.
[uv workspace guidance](https://docs.astral.sh/uv/concepts/projects/workspaces/)

The runner environment lives in `benchmarks/web/runner/.venv`. Prepared
application snapshots, their environments and production assets live under
ignored `.benchmarks/builds/<build-id>/`; browsers live in `.benchmarks/browsers/`.
Preparation selects only requested applications, captures declared source inputs,
installs frozen dependencies and builds production assets. Build identities cover
source, locks, runtime/platform and build settings. A failed preparation remains
incomplete and cannot be selected for measurement.

Citry supports a pinned published release and wheels built from captured local
sources. Local inputs include declared uncommitted and untracked files. Retain
the source snapshot, manifest/diff and wheel hashes so another machine can
reconstruct the input. Core must have recorded release-build provenance.
Neither route imports Citry from the shared development environment.

### Commands and profiles

The runner exposes these commands from `benchmarks/web/runner/`:

```bash
uv sync --frozen
uv run --no-sync citry-bench prepare --profile smoke
uv run --no-sync citry-bench qualify --profile smoke
uv run --no-sync citry-bench run --profile smoke
uv run --no-sync citry-bench report <run-id>
```

Preparation installs and builds. Qualification checks behavior, readiness and
instrumentation independently of measurement. Running uses prepared, qualified
applications without installing or silently rebuilding. Reporting consumes saved
records without launching applications. Missing or stale inputs stop the command
with an actionable error. Qualification identities include runner, adapter,
scenario/assertions, instrumentation, profile and application build inputs.

Profiles select frameworks/configurations, scenarios, sizes, browsers,
cache/network settings, warmups, repetitions and deadlines. Reject unknown
settings, unsupported modes and out-of-range values. Smoke is a short correctness
exercise with the first two frameworks and one size, not a publishable ranking.
Local is for development comparisons; publication implements the complete frozen
schedule. Unsupported publication settings must fail explicitly, never silently
use local defaults. The runner allocates ports, starts servers, resets isolated
sessions and stops only its own processes, including after interruption.

### Results, evidence and publication

Raw output defaults to ignored local storage. An output-directory option supports
an external disk.

```text
.benchmarks/runs/<timestamp>-<unique-id>/
  manifest.json
  samples.jsonl
  sizes.jsonl
  server-timings.jsonl
  summary.json
  report.html
  charts/
  logs/
  captures/  # created only for failed operations
```

The manifest records exact source/build/lock hashes, runtime/browser/hardware,
commands and the resolved profile. Each sample retains correlated timings,
outcomes and failures. Size records implement the HTML and network definitions
above. Server-local durations carry operation identifiers. Successful records omit
full DOM and semantic snapshots after their in-memory correctness checks. Failed
operations may retain current-operation network evidence under `captures/`;
additional full snapshots and traces belong to explicit diagnostics outside primary
timing. Required low-overhead timing and byte counters remain consistent across
measured stacks.

Write raw records incrementally and mark interrupted runs incomplete. Retain
failed observations and original blocks. Any later resume feature must retain
whole paired blocks and immutable inputs; never merge runs across different
builds. Output remains until explicitly cleaned up. Export completed evidence as
a checksummed archive for durable external storage. The storage destination is
still to be selected; expiring CI artifacts are not permanent publication evidence.
The final PR contains maintained source, applications, locks, tests and compact
approved summaries/charts with archive links. Environments, large raw runs and
exploratory probes stay out of main.

Initially execute locally on the native host. Publication uses a fixed Linux host,
pinned application images and a separately pinned browser environment. Record
and control CPU, memory, processes and networking; containers alone do not make
measurements comparable. Native macOS development results have their own profile.
The Linux/container execution path follows qualification of the first adapters.
[Playwright container guidance](https://playwright.dev/python/docs/docker)

Future PR CI runs correctness smoke checks on relevant changes. Full timing is a
manual operation on the fixed benchmark machine, with publication a separate
explicit step. All current design, implementation and results stay local until
the agreed single combined PR at the end.


### Current local implementation scope

Fourteen native adapters in the maintained cohort implement the shared
project-board model and semantic assertions: Citry, Django + HTMX + Alpine,
Django Rusty Templates + HTMX + Alpine, FastHTML, Tetra, django-unicorn,
ReactPy, Reflex, Jinja + HTMX + Alpine, django-components + HTMX + Alpine,
Python API + Vue, Python API + React, Next.js and Nuxt. The Citry + Vue
adapter also implements the model with Citry's public Vue renderer. The
`vue-migration-cohort` and report-refresh profiles select it; the `cohort`
profiles do not. Twelve
use HTTP update paths; ReactPy uses a persistent WebSocket and Reflex uses its
native Socket.IO event protocol.
The Django Rusty Templates adapter pins unreleased experimental package
version 0.1.0 at commit `0725f875535b2fca93953a403a57df1d9b34e073` (2026-09-22),
licensed BSD-3-Clause, and requires Rust and Maturin during preparation. It
uses the official `django_rusty_templates.RustyTemplates` backend for initial
and fragment rendering. The upstream empty-branch behavior is worked around by
the adapter's standard-DTL `if`/`for`/`else` template variant; the parity test
compares it byte-for-byte with the original Django template. The focused
`vue-migration-rusty` profile has no Citry local-wheel inputs.
Reflex is a compiled browser-rendered Python UI entry, not a Python HTML
renderer. The Vue and React entries share the same Starlette JSON API and render
the board in the browser. Their initial shell, assets and JSON fetch all belong
to initial payload and readiness. The browser-only entries declare
`rendering = "browser"`, so delayed-initialization qualification can hold
scripts before a board exists. Next and Nuxt declare `rendering = "hybrid"` with
explicit `update_payload` values (`delta` and `json` respectively): their
initial document is SSR HTML, while actions use a different browser payload.
Citry + Vue is also hybrid with `update_payload = "json"`: with Citry's
default settings every board size arrives as server HTML that Vue hydrates. A
hybrid adapter whose smaller pages mount in the browser declares
`hydration_min_count`, the smallest board size that arrives as server HTML.
Unknown rendering modes,
undeclared hybrid payload kinds and a `hydration_min_count` that is not a
positive integer on a hybrid adapter are rejected.
Application READMEs record exact versions and configurations.

The implementation captures isolated published dependencies and application
sources, launches production processes, records browser lifecycle marks and
operation correlation, and measures final HTML plus identity-encoded HTTP and
WebSocket message bodies. Socket accounting matches browser messages to retained
server bytes and operation IDs after the timed boundary. It rejects compression,
reconnects and uncorrelated messages. Fault qualification and retained diagnostic
reports cover both transport paths. Reports include interactive timing and payload charts
and distinguish attempts from actions skipped after a prerequisite failure.

Interactive charts use additive segments only where retained evidence can compose
the browser endpoint honestly. Initial readiness separates the browser interval
before the main document request, that document's application-server duration,
its exchange residual, response receipt, and the browser plus all subsequent
requests through readiness. The server segment describes only the main document.
Parallel assets, API requests, socket bootstrap messages, parsing, and browser
work after its response remain in the final combined segment.

An action is segmented only when it has one correlated HTTP request and response
or one correlated outgoing and incoming WebSocket message pair. The segments are
browser time before the exchange, total measured application-server duration,
exchange residual, HTTP response receipt when observable, and browser time
afterward. WebSocket evidence has no invented response-receipt segment. Server
durations are same-server monotonic spans; absolute server timestamps are never
aligned to the browser clock. The exchange residual can contain transport and
unmeasured scheduling, so it is not an upload, download, or one-way network
measurement. Multiple exchanges, missing timestamps, negative residuals, and
inconsistent intervals retain a successful semantic observation but place its
whole elapsed time in an explicitly unclassified segment.

The report derives each representative stack from the observation that defines
the median total. For an even sample count it averages corresponding segments of
the two middle observations. The segment sum therefore equals the displayed
median endpoint. Measured and unavailable phase counts and reasons remain
visible. Segments are not independently medianed, and missing evidence never
becomes zero.

Seven HTML-rendering adapters additionally wrap their renderer entry points in
request-scoped timing spans. The outer span includes nested rendering once;
separate construction and serialization spans are summed. Each adapter documents
its boundary, including component callbacks invoked inside rendering. The server
emits `Server-Timing: render` only after a successful response actually renders.
Static resources and failed responses do not produce a render duration.

The raw `server_render_ms` field retains the renderer diagnostic. Every adapter
also records output preparation as `server_prepare_ms`, which the raw data and
`summary.json` keep for analysis; the report page does not chart it. HTTP
HTML adapters reuse their valid construction-and-serialization render span;
browser-rendered HTTP adapters emit `Server-Timing: prepare`; persistent
transports attach `prepare_ms` to the exact correlated server record. The span
measures creation and serialization of the documented HTML, JSON, or state-delta
output while excluding unrelated request handling, queue waits, transport, and
browser work.
HTML renderer timing remains distinct from the independent prepared-data
microbenchmark proposed above. An unobserved or invalid preparation metric stays
unavailable and is not a zero-time result.

The optional `citry_runtime = "workspace"` profile setting captures the local
core and standard/CSP Events JavaScript while keeping the published Python
package pinned. Preparation replaces only those isolated installed files, without
writing through uv cache hardlinks. Their input and installed-byte hashes enter
the prepared build evidence, and the report labels the workspace runtime.
`published` is the default; unknown modes and workspace mode without the Citry
adapter are rejected. The dedicated Citry and full-cohort workspace-runtime
profiles retain a single Citry entry per chart.

Tetra builds its component assets during preparation. Its selected 0.8.5 release
and stock unminified browser assets are documented exceptions, chosen for
packaging feasibility before timing comparisons. Reflex exports its production
frontend with pinned Node/Bun tools and a frozen frontend dependency lock. Its
current build supports macOS ARM64. The compiled API URL requires the reserved
local port 8917; launch fails when it is occupied. The static frontend and native
Python backend share that origin and process. Neither adapter compiles during a
measurement. Vue and React also bundle production browser assets with frozen
dependencies and a pinned macOS ARM64 build tool. Prepared build outputs are
checked along with source and installed artifacts. The Next and Nuxt adapters
add production Node SSR/hydration paths with Next Server Actions and Nuxt Nitro
APIs; each build downloads and verifies Node 22.22.0 locally and uses a frozen
npm lockfile, so the runner does not assume a system Node installation. These
are hybrid adapters: initial documents are server HTML, while Next action
responses are RSC/delta payloads and Nuxt action responses are JSON. The runner
keeps those update payload kinds separate from initial HTML. Next's streamed
`application`, `render` and `prepare` spans end at the first response chunk.
Its adapter declares `timing_boundary = "first-chunk"`, so `summary.json` lists
those rows' `server_prepare_boundaries` as first-chunk boundaries rather than
full-stream serialization durations.

Scenario data is deterministic in `scenarios/project_board/model.py`; the exact
source fixture and provenance are in `canonical_project.json`. Mutations update
state without constructing discarded snapshots, and the separate runner oracle
derives expected transitions without calling that model. The scenario README and
DOM contract specify behavior and markers. Smoke and local profiles retain the
first two adapters. The default fourteen-adapter cohort covers 14 and 140 outputs;
the 1,400-output cohort is an opt-in profile.

This stage does not qualify publication comparisons. Local Citry wheel
construction, additional proposed framework combinations, container/network
execution, compression/cache variants and the full statistical schedule remain
later implementation stages. The Citry readiness observer uses pinned internal
queue diagnostics whose scan cost is included in its endpoint. Other adapters
also have lifecycle-specific observer costs. The runner records semantic snapshot
overhead separately, but residual event-loop effects still need calibration before
publication. Focus/selection preservation inside updated content, arbitrary
future asynchronous hooks, nested lifecycle behavior and concurrent actions
remain separate qualification work. All source and evidence remain local until
the agreed combined PR.


## Memory measurements after the Vue migration

The user requested memory graphs alongside the final full-cohort comparison.
Memory measurement uses the same frozen applications and canonical scenarios,
but runs separately from latency timing. Sampling process memory or querying
heap state must not change the published latency observations.

The final cohort contains the current Citry adapter, the Citry + Vue control,
and every other maintained framework adapter: Django + HTMX + Alpine, Django
Rusty Templates + HTMX + Alpine, FastHTML,
Tetra, django-unicorn, ReactPy, Reflex, Jinja + HTMX + Alpine,
django-components + HTMX + Alpine, Python API + Vue, Python API + React,
Next.js and Nuxt. Include 140 and 1,400 outputs. Historical Citry + Alpine is
not a second Citry bar in the current comparison. Preserve its saved results.

### Distinguish the memory being measured

| Metric | Scope and interpretation |
| --- | --- |
| Server RSS | Resident memory of the launched server and its live child processes; includes framework, native code, domain state and caches |
| Server USS, when available | Memory private to those processes, recorded separately from RSS |
| Browser RSS | Resident memory of one dedicated browser instance and its processes, including renderer and browser overhead |
| Browser JavaScript heap | Used and allocated V8 heap reported for the measured page; not total browser or DOM memory |
| DOM counters | Document, node and listener counts explaining retained browser work; these are counts, not bytes |

The server root is the process launched by the adapter server command, plus
its descendants serving that application. Record the command and process group;
exclude the benchmark harness, package/build tools and browser processes. Any
wrapper included in the launch tree must be identified consistently across
observations. Process-tree RSS sums can count shared pages more than once. Do not label them
unique physical memory or add browser heap bytes to browser RSS. Show server and
browser figures separately. Unsupported or permission-denied USS measurements
are unavailable with a reason, never zero. Process exit and PID reuse must be
handled explicitly, with process identity and observation timestamps recorded.
The process API and platform distinctions are documented by
[psutil](https://psutil.readthedocs.io/en/stable/#psutil.Process.memory_full_info).

A fresh dedicated Chromium instance per memory session prevents other adapters'
tabs from contaminating browser-process totals. Discover browser process IDs
through [CDP SystemInfo](https://chromedevtools.github.io/devtools-protocol/tot/SystemInfo/)
where supported, and verify them against OS process identities. Page heap and
DOM counters use the pinned browser's supported
[Runtime](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/) and
[Memory](https://chromedevtools.github.io/devtools-protocol/tot/Memory/) commands.
Record browser/protocol versions and capabilities. If whole-browser attribution
cannot be established reliably, report it unavailable rather than attributing
a machine-wide Chromium process list to one page.

### Observation points and graphs

Record idle server and blank-browser baselines, first-load readiness, second-load
readiness, and readiness after each canonical server action. Capture memory
before the full DOM semantic observer serializes the document. Then run the
same semantic assertions; a failed scenario remains a failure in memory charts.
Transport polling, framework workers and persistent connections remain active
as required by each adapter. Take every ordinary reading without forcing
garbage collection, so natural GC variation stays in those observations. At the
last observation of each page load, after its ordinary readings, force V8
garbage collection twice and read the page heap again as a separate after-GC
value. It shows retained bytes rather than garbage not yet collected. Taking it
only at the last observation means no ordinary reading on that page follows a
forced collection. Reports show the after-GC value only for selections that
carry it and label other rows as not recorded.

During each memory-only operation, sample server RSS at a fixed documented
interval (initial target 50 ms). Include both endpoints and record actual sample
gaps. Call the maximum a sampled peak: short spikes may fall between samples.
Use endpoint USS rather than repeatedly paying its more expensive inspection.
A page heap snapshot is not an allocation peak or a leak detector. Browser
process totals can be sampled at boundaries first; add peak sampling only if
its attribution and overhead are demonstrated in the pilot.

Add graphs for server memory at readiness, server sampled peak, browser memory
at readiness, and JavaScript heap. Offer absolute values and growth from the
corresponding baseline; retain negative deltas rather than clamping away GC.
Provide DOM counts as a separate explanatory graph or detail. Use MiB for bytes,
show sample counts and ranges, and keep unsupported metrics visibly unavailable.

### Bounded implementation and qualification

Start with one small Citry/reference pilot to establish process ownership, CDP
availability and observer ordering. Reuse current scenario/readiness/lifecycle
code; do not create a second benchmark application implementation. Tests cover
process churn, unsupported metrics, sample aggregation, baseline deltas and
report rendering. Save small raw JSONL records and provenance, not heap dumps
or copied environments. Add the dependency only to the benchmark runner.

Before the final cohort run, record its selected artifact hashes, block/sample
budget and expected duration. Qualify each stack and scale once per frozen
implementation; repeat timing for local spread, not duplicated correctness
matrices. Memory results have their own run identity and cannot silently supply
latency samples. Link both runs from one standalone offline HTML report.

The report command should accept an explicit memory-run association, for example
`citry-bench report <latency-run> --memory-run <memory-run>`. Check the frozen
adapter, scenario, browser and local-wheel identities before combining results.
Different sample budgets are acceptable; different implementation artifacts
are not. Display both run IDs and explain that the measurements were taken
separately. A standalone memory report shows only memory graphs. A combined
report adds those graphs alongside the latency results without merging their
observations or using instrumented operation durations as latency samples.

Implemented: `report --memory-run` validates the retained runner, scenario,
adapter, generated-source, installed-artifact, browser-artifact, browser-version,
OS, architecture, and execution-profile identities before writing. Profile name
and sampling budgets may differ. The combined offline report labels both run IDs,
keeps latency and memory observations separate, and retains invalid memory records
for the affected adapter and scenario filters.

Compare the retained input and artifact manifests, not directory names or Git
HEAD alone: these runs can use uncommitted source and separately installed
local wheels. Require matching runner, scenario and adapter source hashes,
installed framework artifacts, generated application sources and browser
artifacts. Profile names and sample budgets can differ; adapter membership,
scenario configuration and runtime conditions must agree. Reject a missing or
mismatched identity with a useful error before rewriting the report. A failed
run can still produce a diagnostic report when its identities match, but its
failure status remains visible.

Keep per-adapter memory failures and unavailable metrics distinguishable. The
current standalone summary counts invalid observations globally; the combined
report should also retain their scenario groups so a failed memory observation
does not appear as a chart row with zero failures. This is report aggregation
work, not a reason to repeat the collector pilot.

The completed-migration cohort contains current Citry and the ten other
framework adapters, at 140 and 1,400 outputs. It does not include a second
historical Citry bar. Keep existing reports intact, and store display labels
with the new run's provenance so regenerating an old report cannot relabel
the former implementation as the current product. The current Citry adapter
must install the frozen local wheels from the completed migration.

### Local browser capability check

On 2026-09-13, the existing runner's Playwright installation launched its pinned
HeadlessChrome 151.0.7922.34 in a dedicated blank session. Public CDP commands
returned browser, renderer, GPU and network-service process IDs. OS inspection
confirmed that all four belonged to that browser's process group and that the
three child processes had the reported browser PID as their parent.
`Runtime.getHeapUsage` and `Memory.getDOMCounters` also succeeded.

This establishes that the required browser measurements are accessible on this
machine. It is not a framework memory result or proof that the process set stays
fixed: the implementation must rediscover processes at each observation and
handle renderer replacement. The blank page reported two documents and eight
nodes, which is another reason to retain baselines rather than interpreting
every counted node as application content. No forced GC or heap dump was used.

### Memory implementation review, before measured runs

The initial implementation review found the following required corrections;
qualification status is recorded after the fixes and pilot.

- Sample RSS with the cheap process-memory call. Read USS only at endpoints;
  the initial shared function requested USS on every 50 ms sample.
- Capture the launched server's PID and creation time once. Compare subsequent
  observations with that identity so PID reuse cannot silently select another
  process. Preserve child-process churn and failed-read notes in raw samples.
- Give RSS, USS, browser process memory, heap and DOM counts independent
  complete, partial or unavailable states. A failed read must not become zero,
  and a failed heap query must not discard a successful browser RSS reading.
- Select the browser root from CDP's explicit browser-process entry and verify
  its OS identity and descendants. A process-name/common-ancestor heuristic is
  insufficient.
- Stop the sampler before summarizing its observations. If bounded shutdown
  fails, mark the observation incomplete and do not race a live sampling thread
  while calculating a supposedly final peak.
- Preserve first-load and second-load identity when grouping observations.
  The initial summary grouped by app, scale and action, combining both page
  loads. The report needed memory graphs and a way to associate separate latency
  and memory run identities from the same frozen inputs.
- A memory-only report must suppress timing graphs and timing summaries, even
  though the reused correctness runner records operation durations. The first
  report fed those durations into the ordinary report.
- Memory observer errors, including CDP session creation or detachment, must
  produce unavailable metric records without failing a correct application
  scenario. Record operation cycle, page-load, session, pinned process identity,
  and browser/protocol version with the observations.

Test these cases with missing permissions, disappearing processes, PID reuse,
partial CDP failures and sampler shutdown. Then run one real application
through the canonical readiness and correctness path before starting the full
memory cohort. Latency samples from memory runs remain excluded from timing
graphs.

### Memory collector and report pilot

The corrected collector and standalone memory report passed independent review
on 2026-09-13. The runner suite passed 95 tests, its report passed the Node
syntax check, and Ruff passed. Reviewed source hashes include `memory.py`
`b2301a0d`, `results.py` `db1ee262`, and `report.js` `190951b7`.

The retained local pilot is
`.benchmarks/runs/memory-plumbing-smoke-20260913/report.html`. It reused an
existing prepared Django application through the canonical two-load/action
flow and produced 11 successful memory observations, zero timing-summary rows,
14 memory charts and no browser page errors. This proves the measurement and
report plumbing; it is not the frozen final cohort or a comparative performance
result. The combined latency and memory report path is implemented and covered
by synthetic offline browser checks. Running every maintained framework at 140
and 1,400 outputs remains pending.
