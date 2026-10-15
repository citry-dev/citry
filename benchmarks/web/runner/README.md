# Framework benchmark runner

Prepare and qualify a profile before measuring it:

```console
citry-bench prepare --profile smoke
citry-bench qualify --profile smoke
citry-bench run --profile smoke
```

Memory is a separate command and run identity. It reuses the qualified frozen
applications and canonical readiness/assertion path, but launches a dedicated
Chromium instance for each two-page pair:

```console
citry-bench memory --profile smoke
```

Every initial page load also records the browser's own first contentful
paint (`fcp_ms`) and largest contentful paint (`lcp_ms`). The instrumentation
script registers `PerformanceObserver`s for `paint` and
`largest-contentful-paint` entries with `buffered: true` before any page script
runs. Each entry's `startTime` counts from navigation start
(`performance.timeOrigin`), which is also the zero of `ready_elapsed_ms` and
`layout_inclusive_elapsed_ms` for an initial load. Those intervals therefore
include the short wait before the document request; the request's own start is
kept as `paint_timing.request_start_ms`, so subtract it for request-relative
times. The runner never measures these times itself; it only reads the entries
afterward.

Chromium stops reporting LCP candidates at the first click, key press, tap or
user scroll, and the runner's local-behavior checks click tabs. The runner
therefore reads the paint record after the readiness endpoint, page capture and
network accounting, and before any assertion or action touches the page. The
read waits two frames and one task to give entries for frames already drawn
time to arrive, drains any queued entries, then disconnects the observers. That freezes the
values, and `paint_timing.finalized_ms` records when it happened. Content that
becomes larger after the read is not counted.

Both page loads record paint timing. Each uses a fresh browser context, so
neither load reuses the browser's HTTP cache; the second load runs against a
warmed server in a browser process that has already rendered the page once.
Chromium reports paint times in coarse steps (whole multiples of 4 ms were
observed with the pinned build), while ready and layout times are finer, so
differences smaller than a step are noise. A page whose
HTML arrives from the server can paint before its framework reports readiness.
A page built by JavaScript has no FCP until it paints text or an image, which
may be loading text in its shell or the rendered board itself; its LCP then
follows the render and may
land after readiness. Chromium reports a paint when the frame is shown, so a
paint caused by the ready render can be a frame or two later than
`ready_elapsed_ms`.

A value the browser did not report stays `null` with `fcp_status` or
`lcp_status` set to `unavailable` and a `fcp_reason` or `lcp_reason`: no entry
before the read, an unsupported entry type, an observer error, a failed read, or
an input before the read (which cuts LCP short). Action rows and loads that
fail before the read carry no paint fields, and the summary and report use only
successful loads. Rows from earlier runs have no paint fields either; the report
labels those as not recorded, and their summary rows keep their original keys.
The read happens after page capture and network accounting (and, in memory
runs, the forced garbage collection), so its delay after readiness differs by
adapter; `finalized_ms` records it. The observers add a small amount of work
inside the measured interval, which has not been measured. Changing the instrumentation changes the runner
source identity, so run `prepare` and `qualify` again before the next
measurement.

An adapter may declare a relative `node` executable and use `{node}` in its
launch command. This is reserved for applications whose build step downloads
and verifies its own runtime (the Next and Nuxt adapters do this); the runner
never falls back to a system Node installation.

`rendering = "hybrid"` is used when the initial navigation delivers server
HTML but measured actions deliver a browser-side payload. Such adapters must
also declare `update_payload = "json"` or `"delta"`; the runner reports initial
HTML preparation and update preparation separately.

A hybrid framework that writes server HTML only for large pages also declares
`hydration_min_count`: the smallest board size (output count) whose first page
arrives as server HTML for the browser framework to hydrate. The browser mounts
smaller boards itself, so the runner labels their initial output by transport
(JSON over HTTP, deltas over WebSocket) and does not expect the board in the
document before scripts run. The value must be a positive integer on a hybrid
adapter; anything else is rejected. The runner cannot check it while measuring,
so the adapter's own tests must.

An adapter may set
`timing_boundary = "first-chunk"` when its framework streams and the reported
server span ends at the first response chunk; `summary.json` keeps that boundary
in `server_prepare_boundaries` so it is not read as complete response
serialization.

The memory run records idle-server and blank-browser baselines, endpoint server
RSS/USS, a 50 ms sampled server RSS peak, browser RSS when CDP process ownership
can be verified, V8 heap usage, and DOM counters. Unsupported or partially read
metrics carry reasons. None of these readings follows a forced garbage
collection. At the last observation of each page load, after those readings
and after the runner has read that observation's response bodies, it forces V8
garbage collection twice and reads the heap again as `heap_after_gc`: the bytes
the page still retains. The collection waits for the response bodies because
Chromium drops some already-received script bodies when it collects garbage. A
failed collection leaves that one reading unavailable with a reason. When the
last observation fails before the collection step, its `heap_after_gc` is also
unavailable, and the reason names the observation's status. Earlier
observations never ask for the reading, so they have no `heap_after_gc` key.
If an earlier observation fails, the page stops there and records no after-GC
reading.
The runner does not create heap dumps. Memory rows captured for a scenario
that later fails correctness are marked invalid and excluded from successful
aggregates.

The report draws server USS only when some row has a reading. psutil reads
USS through `memory_full_info()`, which macOS refuses for the server process
(`AccessDenied`), so every reading on macOS is unavailable and the chart is
left out. The rows still record the value or its reason in `memory.jsonl` and
`summary.json`.

## Reading the report

`report.html` lists every framework in the same order, split into groups
with a heading on the chart axis: Citry, Django libraries, Other Python
libraries, JavaScript SSR (Next.js, Nuxt), and Server API + CSR (Python API +
React, Python API + Vue). An app the report does not know yet appears
last, under "Other".

The charts sit in sections: Timings, Sizes, Memory at page load, Memory after
a server action, and DOM size at page load. Clicking a section or chart title
collapses it (click it again to expand it). A viewer's collapsed titles are remembered in that browser
when it allows local storage.

The selects at the top choose the number of canonical outputs, the server
action and the page load for the detail charts. Each chart title also carries small copies of only
the selects that change that chart; changing any copy changes the top select
and every other copy.

The first- and second-load charts mark the median FCP and LCP with triangles
and print them below the bold total time. The report does not repeat them in
a table.

The report charts the server's work only as the server segment of the load and
action charts: for a page load, the application span of the main document's
`Server-Timing` header, the server's whole handling of the request. Each
observation also records the narrower output-preparation span as
`server_prepare_ms`: the `prepare` span (or the adapter's `render` span) added
up over every response of the load. It usually covers only the part that
builds the output, and for a page built in the browser it covers the later JSON or WebSocket output that
the document request never includes. `summary.json` keeps its median per row
as `server_prepare_median_ms` for analysis; the report page does not chart it.
