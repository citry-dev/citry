# Framework interaction benchmarks

This suite measures how quickly a browser shows the same project page, and
how quickly it finishes the same server actions on that page, when the page is
built with Citry and with other Python and JavaScript frameworks. Each
framework gets its own small application (an "adapter") under `apps/`. Every
adapter serves the canonical project page from
[`scenarios/project_board`](scenarios/project_board/README.md), keeps its own
frozen dependencies, serves its browser assets locally, runs as one production
server process, and calls the same in-memory domain operations.

The runner, `citry-bench` in [`runner/`](runner/README.md), installs each
adapter into an ignored folder, checks that every action produces the expected
page, then drives native Chromium through the actions and records timings and
payload sizes.

| Adapter | Rendering and updates |
| --- | --- |
| [Citry](apps/citry/README.md) | Python component rendering and HTTP server events |
| [Citry + Vue](apps/citry_vue/README.md) | Citry's Vue renderer: server HTML hydrated by Vue at every board size, and signed HTTP server events |
| [Django + HTMX + Alpine](apps/django_htmx_alpine/README.md) | Django templates and HTTP fragment replacement |
| [Django Rusty Templates + HTMX + Alpine](apps/django_rusty_templates/README.md) | Experimental Rust-backed Django template backend and HTTP fragment replacement |
| [FastHTML](apps/fasthtml/README.md) | Python FastTags and HTMX updates |
| [Tetra](apps/tetra/README.md) | Django components, encrypted state and HTTP updates |
| [django-unicorn](apps/unicorn/README.md) | Django components, serialized state and HTTP updates |
| [ReactPy](apps/reactpy/README.md) | Python component layout and persistent WebSocket updates |
| [Reflex](apps/reflex/README.md) | Compiled React frontend and native Socket.IO events |
| [Jinja + HTMX + Alpine](apps/jinja_htmx_alpine/README.md) | Jinja templates on Starlette and HTTP fragment updates |
| [django-components](apps/django_components/README.md) | Django components with HTMX updates and Alpine |
| [Python API + Vue](apps/python_vue/README.md) | Shared Starlette JSON API and browser-rendered Vue UI |
| [Python API + React](apps/python_react/README.md) | The same JSON API and browser-rendered React UI |
| [Next.js](apps/next/README.md) | Native App Router SSR HTML, hydration and Server Action RSC/delta updates |
| [Nuxt](apps/nuxt/README.md) | Universal SSR HTML, hydration and Nitro JSON server-action updates |
| [Nuxt CSR control](apps/nuxt_csr/README.md) | The same Nuxt board in client-rendered mode (`ssr: false`) |

The `cohort` profiles run the fourteen maintained adapters: every row above
except Citry + Vue and the Nuxt CSR control, which have their own profiles.
Each application README names its exact framework release, what its server
timing covers, and its known limits.

The [design](../../docs/design/framework_interaction_benchmarks.md) explains
why the suite measures what it does and what a publishable comparison
requires. Current profiles use native Chromium, fresh browser contexts,
loopback HTTP/1.1 and no compression. The reports are diagnostic: they record
how much time the runner's own page checks and each adapter's reported server
work take, but those costs are not calibrated across frameworks. Container
runs, network shaping, cache and compression variants and publication
statistics are not built yet. A profile that asks for one of them fails with
an error.

## Before you start

You need:

- **macOS on Apple silicon (arm64).** The build scripts for Reflex, Next.js,
  Nuxt, Nuxt CSR, Python API + Vue and Python API + React download pinned
  macOS arm64 builds of Node.js and Bun and stop on any other platform. The
  other adapters have no such check, but the suite has only been run on macOS
  arm64.
- **[uv](https://docs.astral.sh/uv/).** uv downloads Python 3.12.13 for the
  runner and for every Python adapter.
- **A Git checkout of this repository.** `qualify` and `run` record the
  commit and `git status` in each run's manifest, and fail outside a Git
  checkout.
- **Network access for the first `prepare`.** It downloads Python wheels,
  npm packages, Node.js, Bun, esbuild and Chromium. Later commands work
  offline.
- **A few gigabytes of free disk space** under `.benchmarks/` at the
  repository root, which holds every prepared build and run.
- **Port 8917 free** when the profile includes Reflex, which compiles that
  port into its frontend. An occupied port stops the launch.

Nothing is installed into Citry's own development environment. Each adapter
gets its own environment inside `.benchmarks/`.

## Run the canonical measurement

The canonical workload is the project page in
[`scenarios/project_board`](scenarios/project_board/README.md), labelled
`scenario_revision = "canonical-project-v1"` in every profile. The `cohort`
profile runs it for all fourteen maintained adapters at 14 outputs (1x) and
140 outputs (10x).

Check your setup with the two-adapter `smoke` profile first, then run the
cohort. From the repository root:

```bash
cd benchmarks/web/runner
uv sync --frozen --python 3.12.13

# Quick setup check: Citry and Django + HTMX + Alpine, 14 outputs.
uv run --no-sync citry-bench prepare --profile smoke
uv run --no-sync citry-bench qualify --profile smoke
uv run --no-sync citry-bench run --profile smoke

# The canonical measurement.
uv run --no-sync citry-bench prepare --profile cohort
uv run --no-sync citry-bench qualify --profile cohort
uv run --no-sync citry-bench run --profile cohort

# Rebuild the HTML report of a finished run.
uv run --no-sync citry-bench report <run-id>
```

What each command does:

- `prepare` copies each selected adapter's source files, including
  uncommitted changes, into `.benchmarks/builds/<digest>/`, installs the
  adapter from its own lockfile, runs its `build.py` if it has one, and
  installs Chromium into `.benchmarks/browsers/`. Tetra builds its component
  assets; Reflex, Vue, React, Next.js and Nuxt build their production
  frontends. All of this finishes before anything is measured.
- `qualify` starts each server and checks every action, the readiness
  signal and the measurement plumbing. `run` refuses to start until
  qualification has passed for the same profile and the same source inputs.
- `run` measures and writes the run directory, including `report.html`.
- `report <run-id>` rebuilds `summary.json` and `report.html` from a run's
  records. Pass a directory path instead when the run is outside
  `.benchmarks/runs/`.
- `memory --profile <name>` is a separate run that records server and
  browser memory for the same prepared applications. The
  [runner README](runner/README.md) describes what it reads.

A changed application, scenario, runner or profile changes the build
identity, so run `prepare` and `qualify` again. The runner rejects prepared
sources, installed packages or browser files that changed after preparation.
A failed preparation never counts as a usable build.

Each of `prepare`, `qualify`, `run` and `memory` prints the directory it
wrote. `qualify` and `run` exit with status 1 when the run did not pass.

## How long it takes

These are observations from development runs on an Apple M4, not
guarantees:

| Step | Observed time |
| --- | --- |
| `uv sync` in `runner/` | a few seconds once uv has cached the packages |
| `prepare --profile smoke` | seconds after the first download |
| `qualify --profile smoke` | about 20 seconds |
| `run --profile smoke` | under 10 seconds |
| `run --profile local` | about 1 minute |
| `run --profile cohort-local` (same settings as `cohort`) | 3 to 26 minutes |

The first `prepare` of the cohort takes longer, mostly downloads and the
frontend builds; its time was not recorded. `cohort-100x` measures 1,400
outputs and takes considerably longer; run it only after reviewing the 1x and
10x time and memory.

## Profiles

Profiles live in [`profiles/`](profiles/). Pass the file name without
`.toml`.

| Profile | Adapters | Outputs | Purpose |
| --- | --- | --- | --- |
| `smoke` | Citry, Django + HTMX + Alpine | 14 | Setup check, one short action sequence |
| `local` | Citry, Django + HTMX + Alpine | 14, 140 | Two process blocks, one warmup and two measured action sequences per session |
| `cohort`, `cohort-local` | the fourteen maintained adapters | 14, 140 | The canonical measurement (the two files differ only in name) |
| `cohort-100x` | the fourteen maintained adapters | 1,400 | Opt-in large board |
| `nuxt-csr` | Nuxt CSR control | 14, 140 | The client-rendered control on its own |
| `nuxt-ssr-csr` | Nuxt, Nuxt CSR control | 140, 1,400 | Server-rendered and client-rendered Nuxt side by side |
| `vue-migration-rusty` | Next.js, Nuxt, Django Rusty Templates | 140, 1,400 | Three blocks, longer deadlines, no local Citry wheels |
| `report-full-20260928-extras`, `-next`, `-nuxtcsr`, `-reflex` | Citry and Nuxt CSR, Next.js, Nuxt CSR, Reflex | 140, 1,400 | Parts of the 2026-09-28 full report that need no local Citry wheels |
| `report-full-20260928` | Citry + Vue and eleven other adapters | 140, 1,400 | The 2026-09-28 full report; needs local Citry wheels |
| `vue-migration-cohort` | Citry + Vue and ten other adapters | 140, 1,400 | Three blocks; needs local Citry wheels |
| `vue-events`, `vue-direct` | Citry, Citry + Vue, Django + HTMX + Alpine, Python API + Vue, Python API + React | 14, 140 | Vue comparisons; need local Citry wheels |

These are development schedules, not publication samples. Servers start
automatically and stop when their block ends or the run is interrupted. Health
requests do not render the measured page.

### Profiles that need local Citry wheels

The Citry adapter installs the published `citry` release pinned in its
`uv.lock`. The Citry + Vue adapter instead installs `citry` and `citry-core`
wheels that you build, because it uses Citry's Vue renderer. That renderer is
not in a published Citry release, and it is not on `main` yet; the
`report-full-20260928` wheels were built from the Vue migration branch.
Profiles that select Citry + Vue name the wheel paths in a `[local_wheels]`
table, relative to the repository root:

```toml
[local_wheels]
citry = ".benchmarks/wheels/report-full-20260928/citry-0.5.1-py3-none-any.whl"
citry-core = ".benchmarks/wheels/report-full-20260928/citry_core-1.7.1-cp312-cp312-macosx_11_0_arm64.whl"
```

Build both wheels into exactly those paths before `prepare`, from a checkout
that contains the Vue renderer. Build `citry-core` in release mode
(`maturin build --release`). Loading a profile fails while a named wheel is
missing. The runner hashes the wheel bytes into the build identity and
installs them only into the Citry + Vue environment. When `citry-core`
reports its build profile, `prepare` refuses a debug build, and `qualify`,
`run` and `memory` refuse a build prepared from one; set
`CITRY_BENCH_ALLOW_DEBUG_NATIVE=1` to measure a debug build on purpose. A
wheel that does not report its build profile, such as the published
`citry-core` 1.7.0 the Citry adapter uses, is accepted with a note on stderr.

## What the runner measures

Vue and React request their initial JSON after loading the page shell. Initial
payload and readiness include that request as well as the framework assets. Their
shared Python API keeps backend behavior identical.

Initial timing starts at navigation in the destination document and stops at the
application's framework lifecycle readiness signal. Server-action timing starts at the
trusted browser click, before application handlers, and ends at the matching
server revision's readiness signal. The instrumentation records the endpoint
timestamp first, then synchronously captures and validates the complete semantic
DOM against expected state prepared before the operation. It reports that work
separately as `semantic_observer_ms`; the elapsed interval does not include it.
No network-idle, animation-frame or paint delay is added. No second verification
request is included in the interval. HTML serialization happens afterward.

Each measured session loads the initial page twice in the same fresh application
server process before any action mutates state. The loads use separate logical
sessions and fresh browser contexts, so both have empty browser asset caches. The
second load observes warmed application and framework state without measuring
HTTP browser-cache reuse. Both loads share a browser process and host state, so
their difference is a repeat-load outcome rather than attribution to server
caches. Only the second page continues through the configured action cycles.
Reports retain both initial observations under an explicit page-load ordinal and
show their phase and size evidence separately. Only session
index zero begins with the server process's first measured page request when a
profile configures multiple sessions.

Every initial load also records first contentful paint (FCP) and largest
contentful paint (LCP) from the browser's paint entries, counted from the same
navigation start as readiness. The report marks their medians on the first- and
second-load stacks and lists them beside ready and layout times. The
[runner README](runner/README.md) describes when LCP is read and how missing
values are reported.

Each action exposes its operation key in the normal request, server response and
rendered state. A readiness mark retains revision, session, pending-work state
and the full scenario snapshot from the instant it is emitted. Late HTTP response
completion, wrong acknowledgements, wrong DOM state, browser errors and timeouts
fail the observation. Later collection cannot turn an earlier incomplete
readiness signal into a passing sample. Reading computed visibility during
semantic capture can force browser style work after the timestamp and perturb
later event-loop work. The reported capture duration exposes that cost without
calling it paint timing.

Sizes include UTF-8 final document HTML, all initial response bodies and socket
bootstrap messages, and each action's request and response bodies or messages.
Identity encoding and uncached responses allow decoded and encoded body counts
to be compared directly. Raw Playwright and Chromium counters retain their
provenance. These body counts are not TCP/TLS wire
sizes. Socket messages are matched byte-for-byte between Chromium records and
the server audit, with browser timestamps assigning them to operation intervals.
Uncorrelated messages, reconnects, compression and unexpected cache hits fail the
observation. Socket frame overhead is not included.

HTTP adapters report server-local application duration in `Server-Timing`; socket
adapters retain server receive-to-send preparation durations in their audit. Each
application README defines its boundary. These application measurements include
rendering and other server work and exclude body transmission. Those
durations must not be subtracted from browser timestamps or summed with
overlapping metrics.

Latency stacks use browser-clock Resource Timing or correlated socket-message
boundaries and the server-local application duration. Initial stacks separate
the wait before the main document request, main-document application work,
document exchange residual, response receipt, and a combined browser plus
subsequent-request interval. Only the main document's server work is placed in
that stack; parallel assets, API calls, socket bootstrap messages, and browser
work after the document response remain combined. Action stacks are available
only for one correlated HTTP exchange or one correlated outgoing/incoming socket
message pair. They separate browser time before and after that exchange,
application-server work, HTTP response receipt where observable, and the
remaining exchange residual. The residual includes transport and unmeasured
scheduling; it is not one-way network latency.

Missing, malformed, overlapping, or multi-exchange phase evidence leaves the
successful endpoint intact and displays its whole duration as unclassified.
Nothing missing is replaced with zero. Each displayed stack uses the observation
that defines the median total, or averages the corresponding segment vectors of
the middle two observations. Its segments therefore sum to the displayed median;
measured and unavailable phase counts remain visible.

The seven HTML-rendering adapters also measure their renderer entry points and
emit `Server-Timing: render`. Nested calls count once; separate rendering and
serialization spans are summed. These are renderer spans during real requests,
not an independent microbenchmark. Component data callbacks invoked by a
renderer are included; shared state mutation, transport and browser work are
outside the spans. Each adapter README names the exact functions measured.
FastHTML includes both construction of its HTML tree and its serialization.

The raw data keeps `server_render_ms` as a legacy renderer diagnostic. Every
adapter also records output preparation as `server_prepare_ms`, which raw data
and `summary.json` keep for analysis; the report page does not chart it. It
covers HTML for server-rendered UI, JSON for API-driven browser UI, and state deltas for
persistent browser protocols. Hybrid adapters record HTML for the initial page
and their declared payload for updates; an adapter that mounts small boards in
the browser records that page's output as JSON or deltas instead.
HTML adapters use their existing valid construction-and-serialization render
span; browser-rendered HTTP adapters emit `Server-Timing: prepare`; socket
audits attach `prepare_ms` to the correlated outgoing server record. These
narrower spans exclude unrelated request handling, queue waits, transport, and
browser work. A missing metric stays unavailable and never becomes zero.

## Inspect and retain results

Each command prints its output directory. Runs are stored under:

```text
.benchmarks/runs/<timestamp>-<unique-id>/
  manifest.json
  samples.jsonl
  sizes.jsonl
  server-timings.jsonl
  summary.json
  report.html
  logs/
  captures/  # created only for failed operations
```

Use `--output-dir /path/to/results` with `qualify` or `run` to select another
parent directory. Pass the resulting directory to `report` when it is outside
the default storage location.

The manifest records inputs, installed artifact hashes, browser, host, commands,
profile and completion status. JSONL files retain individual observations and
failures. Successful operations in qualification and measurement keep correctness
outcomes, endpoint metadata, measurements and source/environment hashes without
duplicating full DOM or semantic snapshots on disk. Failed operations retain
current-operation errors and raw HTTP or socket diagnostic evidence under
`captures/`. Reports show stacked interactive timing and payload charts
alongside outcomes. They distinguish attempted observations from actions not run
after a failed prerequisite. An interrupted run remains incomplete and keeps its
written records.
Select the board size and server action in the report. Bars show medians and
dots show individual successful observations; failed and skipped counts remain
visible. Each chart can be downloaded as SVG. The report works offline.
There is no automatic resume, cleanup, upload or publication.

Git holds the adapter, scenario, runner and profile sources and their
lockfiles. Environments, prepared builds, raw observations and traces stay in
the ignored `.benchmarks/` folder. A published comparison needs a compact
approved report and links to durable, checksummed evidence.

## Test the harness

The runner's tests live in [`tests/`](tests/). Several of them drive a real
Chromium from `.benchmarks/browsers/`, so install it first: running `prepare`
once does that, or install it directly. From `benchmarks/web/runner/`:

```bash
uv sync --frozen --python 3.12.13
PLAYWRIGHT_BROWSERS_PATH=../../../.benchmarks/browsers \
  uv run --no-sync playwright install chromium
uv run --no-sync pytest
```

The tests cover invalid profiles, source and installation drift, byte
accounting, readiness faults and retention of failed observations. They take
about 15 seconds. The paint-timing test
`test_server_html_paints_before_its_later_readiness` can fail on the first
launch of a freshly installed Chromium, when the browser starts slowly; it
passes on the next run.

Each adapter also has its own tests, run with that adapter's environment
from its directory. Its README gives the command, for example
`uv run --no-sync python -m unittest test_app -q`.

The repository's `ruff check .` and `ruff format --check .` cover this
folder. Code under `runner/` follows the narrower rule set in
`runner/pyproject.toml`; everything else follows the root configuration, and
test files get the same exemptions as the package tests. To check only this
folder, from the repository root:

```bash
uv run --no-sync ruff check benchmarks/web
uv run --no-sync ruff format --check benchmarks/web
```
