# Framework interaction benchmarks

This suite measures how quickly a browser shows the same project page, and
how quickly it finishes the same server actions on that page, when the page is
built with Citry and with other Python and JavaScript frameworks. Each
framework gets its own small application under `apps/`. Every app serves the
canonical project page from
[`scenarios/project_board`](scenarios/project_board/README.md), keeps its own
frozen dependencies, serves its browser assets locally, runs as one production
server process, and calls the same in-memory domain operations.

The runner, `citry-bench` in [`runner/`](runner/README.md), installs each app
into an ignored folder, checks that every action produces the expected page,
then drives native Chromium through the actions and records timings and
payload sizes.

| App | Rendering and updates |
| --- | --- |
| [Citry](apps/citry/README.md) | Citry 0.6.0: server HTML from Citry's Vue renderer, hydrated by Vue at every board size, and signed HTTP server events |
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

The `cohort` profile runs fourteen apps: every row above except the Nuxt CSR
control, which has its own profiles. Each app's README names its exact
framework release, what its server timing covers, and its known limits.

The [design](../../docs/design/framework_interaction_benchmarks.md) explains
why the suite measures what it does and what a publishable comparison
requires. Current profiles use native Chromium, fresh browser contexts,
loopback HTTP/1.1 and no compression. The reports are diagnostic: they record
how much time the runner's own page checks and each app's reported server
work take, but those costs are not calibrated across frameworks. Container
runs, network shaping, cache and compression variants and publication
statistics are not built yet. A profile that asks for one of them fails with
an error.

## Which Citry the Citry app measures

The Citry app pins and locks the published `citry` 0.6.0 and `citry-core`
1.8.0 from PyPI, so every profile without a `[local_wheels]` table
measures that release. To measure an
unreleased change instead, see
[Test Citry with wheels you build](#test-citry-with-wheels-you-build).

## Before you start

You need:

- **macOS on Apple silicon (arm64).** The build scripts for Reflex, Next.js,
  Nuxt, Nuxt CSR, Python API + Vue and Python API + React download pinned
  macOS arm64 builds of Node.js and Bun and stop on any other platform. The
  other apps have no such check, but the suite has only been run on macOS
  arm64.
- **[uv](https://docs.astral.sh/uv/).** uv downloads Python 3.12.13 for the
  runner and for every Python app.
- **A Git checkout of this repository.** `qualify` and `run` record the
  commit and `git status` in each run's manifest, and fail outside a Git
  checkout.
- **Network access for the first `prepare`.** It downloads Python wheels,
  npm packages, Node.js, Bun, esbuild and Chromium. Later commands work
  offline.
- **A few gigabytes of free disk space** under `.benchmarks/` at the
  repository root, which holds every prepared build and run. A prepared
  Reflex build alone takes about 430 MB.
- **Port 8917 free** when the profile includes Reflex, which compiles that
  port into its frontend. An occupied port stops the launch.

Nothing is installed into Citry's own development environment. Each app gets
its own environment inside `.benchmarks/`.

## Run the canonical measurement

The canonical workload is the project page in
[`scenarios/project_board`](scenarios/project_board/README.md), labelled
`scenario_revision = "canonical-project-v1"` in every profile. The `cohort`
profile runs it for the fourteen cohort apps at 14 outputs (1x) and 140
outputs (10x).

Check your setup with the two-app `smoke` profile first, then run the
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

- `prepare` copies each selected app's source files, including uncommitted
  changes, into `.benchmarks/builds/<digest>/`, installs the app from its own
  lockfile, runs its `build.py` if it has one, and installs Chromium into
  `.benchmarks/browsers/`. Tetra builds its component assets; Reflex, Vue,
  React, Next.js and Nuxt build their production frontends. All of this
  finishes before anything is measured.
- `qualify` starts each server and checks every action, the readiness
  signal and the measurement plumbing. `run` refuses to start until
  qualification has passed for the same profile and the same source inputs.
- `run` measures and writes the run directory, including `report.html`.
- `report <run-id>` rebuilds `summary.json` and `report.html` from a run's
  records. Pass a directory path instead when the run is outside
  `.benchmarks/runs/`.
- `memory --profile <name>` is a separate run that records server and
  browser memory for the same prepared apps. The
  [runner README](runner/README.md) describes what it reads.
- `compose --output <folder> --runs <qualify-run> <run> [--runs ...]`
  combines passed runs into one report folder, taking each app from the run
  that measured it. The docs page is built from such a folder; see
  [Update the numbers on the docs page](#update-the-numbers-on-the-docs-page).

A changed app, scenario, runner or profile changes the build identity, so run
`prepare` and `qualify` again. The runner rejects prepared sources, installed
packages or browser files that changed after preparation. A failed
preparation never counts as a usable build.

Each of `prepare`, `qualify`, `run`, `memory` and `compose` prints the
directory it wrote. `qualify` and `run` exit with status 1 when the run did
not pass.

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
| `run --profile cohort` | 3 to 26 minutes |
| `prepare` of one app at 140 and 1,400 outputs (Reflex, Citry), packages cached | about 30 seconds |
| `qualify` of one app at 140 and 1,400 outputs (Reflex, Citry) | about 2 minutes |

The first `prepare` of the cohort takes longer, mostly downloads and the
frontend builds; its time was not recorded. `cohort-100x` and `release-0.6.0`
measure 1,400 outputs and take considerably longer; run them only after
reviewing the 1x and 10x time and memory.

## Profiles

Profiles live in [`profiles/`](profiles/). Pass the file name without
`.toml`.

| Profile | Apps | Outputs | Purpose |
| --- | --- | --- | --- |
| `smoke` | Citry, Django + HTMX + Alpine | 14 | Setup check, one short action sequence |
| `local` | Citry, Django + HTMX + Alpine | 14, 140 | Two process blocks, one warmup and two measured action sequences per session |
| `cohort` | the fourteen cohort apps | 14, 140 | The canonical measurement |
| `cohort-100x` | the fourteen cohort apps | 1,400 | Opt-in large board |
| `release-0.6.0` | the fourteen cohort apps | 14, 140, 1,400 | The `cohort` settings plus the 1,400-output board the docs page shows; run once for the Citry 0.6.0 release |
| `citry-local-wheels` | Citry | 14, 140, 1,400 | Citry from wheels you build; for testing before a release |
| `nuxt-csr` | Nuxt CSR control | 14, 140 | The client-rendered control on its own |
| `nuxt-ssr-csr` | Nuxt, Nuxt CSR control | 140, 1,400 | Server-rendered and client-rendered Nuxt side by side |

These are development schedules, not publication samples. Servers start
automatically and stop when their block ends or the run is interrupted. Health
requests do not render the measured page.

### Test Citry with wheels you build

A profile can replace the `citry` and `citry-core` packages of the Citry app
with wheels built from this repository, to measure a change before it is
released. This is for testing only: the numbers describe whatever source you
built, not a release. The profile names the wheels in a `[local_wheels]`
table, relative to the repository root. `citry-local-wheels` is set up for
the 0.6.0 wheels:

```toml
[local_wheels]
citry = ".benchmarks/wheels/citry-0.6.0/citry-0.6.0-py3-none-any.whl"
citry-core = ".benchmarks/wheels/citry-0.6.0/citry_core-1.8.0-cp312-cp312-macosx_11_0_arm64.whl"
```

Build both wheels into exactly those paths before `prepare`. The
`citry-core` build takes about 3 minutes on an Apple M4 and needs about
1.5 GB of free disk space for the Rust build output, which the last command
frees. From the repository root:

```bash
# citry-core compiles against ruff's Python parser, a Git submodule.
git submodule update --init --depth 1 third_party/rust/ruff
mkdir -p .benchmarks/wheels/citry-0.6.0
uv build --wheel packages/py/citry \
  --out-dir .benchmarks/wheels/citry-0.6.0
cd packages/py/citry_core
CARGO_TARGET_DIR=../../../.benchmarks/cargo-target \
  uvx --from maturin==1.15.0 maturin build --profile release-wheel \
  --interpreter "$(uv python find 3.12.13)" \
  --out ../../../.benchmarks/wheels/citry-0.6.0
cd ../../..
rm -rf .benchmarks/cargo-target
```

Loading a profile fails while a named wheel is missing. The runner hashes the
wheel bytes into the build identity and installs them only into the Citry
app's environment, in place of the packages from its lockfile. When
`citry-core` reports its build profile, `prepare` refuses a debug build, and
`qualify`, `run` and `memory` refuse a build prepared from one; set
`CITRY_BENCH_ALLOW_DEBUG_NATIVE=1` to measure a debug build on purpose. A
wheel that does not report its build profile is accepted with a note on
stderr.

## Update the numbers on the docs page

The [Benchmarks page](../../docs_site/content/about/benchmarks.md) draws its
charts from
[`docs_site/data/benchmark_time_to_interactive.json`](../../docs_site/data/benchmark_time_to_interactive.json):
the time until the 1,400-output page is ready for input, first and second
load, for Citry and eleven other frameworks.

The numbers there now come from one composed report,
`composed-70d4a8802900`, built on 2026-10-19 from the `release-0.6.0`
qualify run `20261019T210740Z-2b5cd077` and the measurement run
(`citry-bench run`) `20261019T213948Z-c6248185`. All fourteen apps of the
profile, including the twelve frameworks on the docs page, ran in that one
run, with Citry 0.6.0 and citry-core 1.8.0 installed from PyPI. The runner
recorded commit `55740fd66` with no uncommitted changes; that local commit
has the same benchmark sources as the change that published these numbers.
To repeat it from `benchmarks/web/runner/` (for a later release, copy the
profile under a new name first):

```bash
uv run --no-sync citry-bench prepare --profile release-0.6.0
uv run --no-sync citry-bench qualify --profile release-0.6.0
uv run --no-sync citry-bench run --profile release-0.6.0
uv run --no-sync citry-bench compose \
  --output ../../../.benchmarks/reports/release-0.6.0 \
  --runs <qualify-run> <run>
cd ../../..
uv run --no-sync python -m docs_site.scripts.benchmark_data \
  .benchmarks/reports/release-0.6.0
```

`qualify` and `run` print their run folders; pass both to `compose`. One
failed app fails the whole run, and `compose` accepts only passed runs. To
recover, copy `release-0.6.0.toml` twice under new names: one without the
failed app and one with only that app. Prepare, qualify and run each, then
pass both pairs to `compose`. It refuses runs that did not pass, that use
different settings, runner or scenario sources, browsers or hosts, or that
measured the same app twice. The docs script needs exactly one
passed observation per framework and page load at 1,400 outputs, which the
`release-0.6.0` profile gives. It rewrites the JSON file; update the prose
on the Benchmarks page to match the new numbers in the same change.

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

HTTP apps report server-local application duration in `Server-Timing`; socket
apps retain server receive-to-send preparation durations in their audit. Each
app's README defines its boundary. These application measurements include
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

The seven apps that render HTML on the server with a template or component
library (Django + HTMX + Alpine, Django Rusty Templates, Jinja, Tetra,
django-unicorn, django-components and FastHTML) also measure their renderer
entry points and emit `Server-Timing: render`. Nested calls count once; separate rendering and
serialization spans are summed. These are renderer spans during real requests,
not an independent microbenchmark. Component data callbacks invoked by a
renderer are included; shared state mutation, transport and browser work are
outside the spans. Each app's README names the exact functions measured.
FastHTML includes both construction of its HTML tree and its serialization.

The raw data keeps `server_render_ms` as a legacy renderer diagnostic. Every
app also records output preparation as `server_prepare_ms`, which raw data
and `summary.json` keep for analysis; the report page does not chart it. It
covers HTML for server-rendered UI, JSON for API-driven browser UI, and state deltas for
persistent browser protocols. Hybrid apps record HTML for the initial page
and their declared payload for updates; an app that mounts small boards in
the browser records that page's output as JSON or deltas instead.
HTML apps use their existing valid construction-and-serialization render
span; browser-rendered HTTP apps emit `Server-Timing: prepare`; socket
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

Git holds the app, scenario, runner and profile sources and their
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

The tests cover invalid profiles, that every profile in `profiles/` loads,
source and installation drift, lockfiles that need unpublished wheels, byte
accounting, socket heartbeats, readiness faults, retention of failed
observations and composed reports. They take
about 15 seconds. The paint-timing test
`test_server_html_paints_before_its_later_readiness` can fail on the first
launch of a freshly installed Chromium, when the browser starts slowly; it
passes on the next run.

Each app also has its own tests, run with that app's environment
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
