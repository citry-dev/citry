# Stage 6 vertical playground prototype

**Status (2026-07-28): Accepted for iterative implementation.** The production-shaped local
prototype passes its automated Chromium, Firefox, and WebKit matrix against
minified output. Warm Worker reuse leaks state, and the public runner,
first-reader, uncached-network, physical-mobile,
assistive-technology, touch, and 400 percent zoom work remains follow-up
validation. The exact Citry 0.3.0/core 1.4.0 package-compatibility gate passes
locally.

**Shipping override (2026-07-29):** The cross-origin broker remains useful
evidence but is not the v1 deployment. V1 creates the Worker from the docs page
and serves first-party runtime files with the existing static site. External
runtime files come from pinned Pyodide CDN and exact PyPI URLs.

This document records evidence, not a shipped `/playground/` page. The proof is
under [`vertical_proof/`](vertical_proof/), its last complete browser result is
[`browser-results.json`](vertical_proof/results/browser-results.json), and the
route remains absent from the docs build.

## Scope and exact current tuple

The proof integrates the real boundaries selected in Stages 1 through 5:

```text
minified docs host and CodeMirror editor
  -> validated MessageChannel
  -> distinct-host runner document
  -> same-origin module Worker
  -> Pyodide 314.0.3
  -> exact local wheel list with byte and SHA-256 preflight
  -> Stage 3 final-expression executor
  -> docs-created iframe with runner-origin, opaque sandboxed preview document
```

It installs published `citry==0.3.0` plus the deterministic PyEmscripten wheel
built from the `citry-core==1.4.0` tag. The selected runtime has 21,174,090
bytes of Pyodide and wheel artifacts. The build performs no dependency
resolution and no package download. Every engine asserts the installed
versions and renders the `#c-key` regression case that failed for 0.2.0 over
core 1.4.0. This proof originally used sealed local wheel bytes. The exact
byte-identical 1.4.0 PyEmscripten wheel was subsequently published on PyPI,
and the current-package smoke passed again from its public URL.

The proof emits both `/playground/` and `/citry-docs/playground/` only inside
its ignored `dist/` directory to exercise base paths. It does not emit a
versioned route.

## Reproduction

The runtime directories point to the sealed artifacts produced in Stage 1:

```bash
cd docs/design/docs_playground_research/vertical_proof
npm ci --ignore-scripts
npx playwright install chromium firefox webkit
PYODIDE_DIR=/path/to/pyodide \
WHEELHOUSE=/path/to/sealed-wheelhouse \
npm run build
PLAYWRIGHT_BROWSERS=chromium,firefox,webkit npm test
```

The checked-in lock pins all 14 JavaScript build and runtime dependencies. The
build fails if a supplied runtime file differs in basename, size, or SHA-256.
Two consecutive builds from identical inputs produced the same
`build-manifest.json` digest:
`59d9d325d41f2a3226b2ccd359b0009d4d5281cd9a6574b736ce02d109f266cd`.

The final application payload measured:

| Asset | Raw | Gzip | Brotli |
| --- | ---: | ---: | ---: |
| CodeMirror host JavaScript | 601,932 B | 208,920 B | 174,980 B |
| Workspace CSS | 4,345 B | 1,627 B | 1,358 B |

These are route-only assets. The JavaScript Brotli result is consistent with
the focused Stage 4 CodeMirror measurement. It excludes the 21.2 MB runtime
artifact set.

## Browser results

The complete run used Chromium 149.0.7827.55, Firefox 151.0, and WebKit 26.5.
The following timings are local, cached-desktop observations from the host load
event or source replacement through the rendered-result acknowledgement:

| Engine | Guided first result | Warm explicit edit |
| --- | ---: | ---: |
| Chromium | 1,384 ms | 59 ms |
| Firefox | 7,183 ms | 63 ms |
| WebKit | 1,376 ms | 47 ms |

The artificial slow-loader case added 350 ms before each verified artifact
and reached a first result in 5,136 ms in Chromium. Offline Run produced a
persistent `Runner handshake timed out` diagnostic; restoring connectivity and
running again recovered. Retry uses a new session query as well as a fragment,
because changing only the fragment did not force Chromium to repeat a failed
offline iframe navigation. These observations are not network or product
budgets. In particular, Firefox exceeded the provisional 6.5-second cached
fresh-Worker guardrail in this complete current-package run.

The first-result timer starts after Playwright's page `load` wait. Guided
preparation may already have begun, so it is useful for cross-engine regression
comparison but can undercount navigation-to-result time. Stage 1's fresh-Worker
measurements remain the stricter runtime guardrail, and the deployed uncached
test must instrument navigation start, first shell paint, runtime ready, and
first result separately.

### Passed integrated scenarios

- exact artifact preflight, initial render, warm explicit edit, 500 ms
  latest-edit debounce, Auto-run preference persistence, reset source on
  reload, stale-preview marking, and both guided and on-demand shells;
- installed-version assertions and the previously failing keyed nested
  component through exact Citry 0.3.0/core 1.4.0 in all three engines;
- syntax errors, ordinary Python errors, `None`, unsupported output, traceback
  truncation, template compilation through the starter, and successful Citry
  rendering;
- user Stop, five-second hard timeout, Worker termination, clean bootstrap
  after either outcome, oversized result rejection, a 16 MiB allocation, and
  recovery. The complete Chromium host also recovered after a deliberate
  Worker self-close; Stage 1 already covers self-shutdown in all three engines;
- synchronous preview throw, rejected promise, `console.error`, blocked image,
  preview self-navigation, malformed parent messages, and message floods;
- iframe attempts at parent DOM access, opaque-origin storage, popup, download,
  and docs-origin fetch;
- Python attempts at docs-origin fetch and Worker message flooding;
- keyboard separator arrows, Home, End, equal-pane reset, pointer drag,
  clamping, persistence, and right-to-left direction;
- 375-pixel one-panel flow, tablet layout, root and non-root asset URLs, five
  future header links, light and dark preferences, reduced motion, forced
  colors, one main landmark, one H1, labelled tabs, a named separator, and a
  titled preview;
- missing wheel, hash mismatch, import failure, unavailable WebAssembly, slow
  loading, offline loading, and retry after the offline fault;
- no unexpected failed application assets and no docs cookie at the runner
  host. The sole Chromium failed request is the deliberately CSP-blocked image.

The generated JSON is the detailed browser record. The test also executes
the Stop, timeout, divider, mobile, diagnostic, and recovery assertions that
are summarized rather than expanded into individual JSON booleans.

### Iterative rollout scenarios

- permanent release-CI integration for future core PyEmscripten wheels;
- the real public runner origin, its deployed headers, cache replacement, and
  an uncached network run;
- physical phone and mid-tier mobile memory and timing;
- actual touch dragging, soft-keyboard viewport changes, browser 400 percent
  zoom, and a narrow desktop with the final production header;
- VoiceOver, NVDA, and other screen-reader sessions, including CodeMirror
  escape behavior and live-region verbosity;
- moderated first-reader comparison of guided Auto-run against run on demand;
- long-running heap sampling in the complete host, service-worker or offline
  product support, and a forced out-of-memory crash;
- an infinite preview-JavaScript loop under an outer process timeout, recording
  whether the iframe or whole tab becomes unresponsive in each engine;
- public release-CI and deployment preflight integration.

## Decisive state-reuse result

Warm reuse is fast but not clean. In every tested engine, one run changed each
of these and a later run observed the value:

- a `builtins` attribute;
- a synthetic `sys.modules` entry;
- a file in Pyodide's in-memory filesystem;
- a property on the Worker JavaScript global.

`citry.clear()` and a fresh module namespace therefore do not satisfy the
deterministic-rerun requirement. This reproduces the Stage 1 cleanup result at
the complete host boundary and falsifies the unqualified warm-reuse
hypothesis.

A fresh Worker per run restores deterministic state but makes every edit pay
the observed 1.2 to 5.9 second cached bootstrap and makes Auto-run unattractive.
A prewarmed disposable Worker pool may hide latency, but it would increase
memory and startup work substantially, especially on mobile. The accepted
initial policy is persistent reuse within the page session. The product
describes it as session state rather than clean interpreter execution, and
Stop, timeout, crash, and Reset provide the fresh-Worker path. Later mobile
evidence may justify a different strategy.

## Preview architecture correction

The Stage 5 `srcdoc` proposal failed under the proof's external-script docs
CSP. A `srcdoc` document inherits the host response policy; its own meta policy
can only tighten that policy. It cannot re-enable the inline Citry CSS and
JavaScript that the host deliberately disallows. Adding `unsafe-inline` to the
docs origin solely for visitor output would weaken the wrong trust boundary.

The proof selected a fixed, content-addressed preview shell on the
credential-free runner origin. Stage 7 review found that its external module
allowlist also permitted visitor script requests to the runner. The final
implementation corrects that detail as follows:

1. The docs host creates the iframe with `sandbox="allow-scripts"`, without
   `allow-same-origin`.
2. `preview.html` contains the small trusted bootstrap inline and transfers a
   private MessagePort after a session-bound handshake. No external script
   origin is allowed by its CSP.
3. The host sends bounded HTML, run id, and correlation data through that port.
4. The shell replaces only visitor content, activates visitor scripts, and
   forwards bounded diagnostics.
5. The preview response owns the restrictive policy: inline script and style
   are allowed, while network, frames, objects, forms, and base URLs are
   blocked. Data and blob images remain possible.
6. A test injects a runner-origin external script URL carrying query data and
   requires that the runner receive no request. The local proof did not cover
   this case, so it is an implementation acceptance test.
7. An unexpected frame navigation disconnects the port and leaves an inert
   frame. It does not re-execute the last malicious HTML. The next successful
   run creates a new preview session.

The host still treats preview diagnostics as best-effort hostile telemetry.
The content can spoof or suppress client errors, but it cannot acquire the
port closure, read the parent, reach docs credentials, or make a network
request under the tested policy. Parent-window floods are ignored and bounded
test instrumentation does not retain them indefinitely.

The local test deliberately uses `localhost` for the docs and `127.0.0.1` for
the runner. Changing only ports was rejected because cookies are scoped to a
host, not a port; a same-host, different-port test sent the docs cookie to the
runner. Production must use a credential-free origin on a different schemeful
site, not merely a sibling hostname under the docs registrable domain.

## Error and recovery findings

Persistent panel diagnostics worked better than toast-only messages for
tracebacks and repeated client failures. The previous successful output stayed
visible and was labelled stale for Python failure, Stop, timeout, and runner
failure. A successful explicit Run cleared the hard-failure Auto-run pause.

The proof exposed two behaviors that implementation must retain:

- oversized output and rate-limit rejection are request failures, not runtime
  crashes; their UI copy should not call the entire runner unavailable;
- preview error detail is browser-dependent. The diagnostic kind and ownership
  are reliable, but a browser may reduce a cross-origin error to generic text.
  Silence never proves client success.

## Auto-run and Stop recommendation

Stop is accepted. It visibly terminates the current Worker,
preserves stale output, pauses Auto-run, and makes the next explicit Run create
a new Worker. The same recovery path passed after timeout and Worker close.
The five-second execution timer is a suitable first product candidate; runtime
preparation has a separate 30-second local-proof limit.

Candidate A, guided live, works technically: it prepares after first paint,
runs the starter, defaults Auto-run on, and collapses rapid edits after 500 ms.
Candidate B keeps the heavy runtime dormant until Run, defaults Auto-run off,
and remembers a later explicit choice.

Use Candidate B as the initial product default. The always-visible Run action
remains the primary contract. First-reader and physical-mobile evidence may
later change the loading or Auto-run defaults.

## Accessibility notes

Automated checks passed the structural layer: one named main landmark, one H1,
a primary navigation current state, labelled controls, a titled iframe,
keyboard tabs, an adjustable separator with values, in-flow diagnostics, and
live status text. The 375-pixel layout uses Code and Result tabs rather than
two narrow columns. Pointer drag, keyboard resize, RTL direction, stored size,
forced colors, reduced motion, and dark preference all remained operable.

This is not an accessibility sign-off. Browser automation does not validate
screen-reader speech, CodeMirror's virtual cursor behavior, actual touch
geometry, 400 percent browser zoom, focus restoration after preview recovery,
or live-region fatigue during staged startup. Those sessions remain required.

## Stage 6 gate result

Stage 6 is accepted for an iterative first implementation. The local
production-shaped proof carries these decisions into the design:

- use a docs-created iframe with the runner-origin sandboxed preview shell
  instead of host `srcdoc`;
- require a credential-free, different-site runner, not only another port or
  hostname;
- keep no-resolution installation and replace the proof's preflight plus
  re-fetch with verified-buffer consumption;
- retain persistent panel diagnostics, hard Stop, stale output, and
  on-demand/off as the initial Auto-run default;
- reuse the warm Worker within a page session for responsiveness, while Stop,
  timeout, crash, and Reset create a fresh Worker.

The maintainer accepts production-origin checks, device budgets, reader
studies, accessibility sessions, and further input and zoom checks as
iterative rollout work. The tested browser wheel is now public. The remaining
findings can refine the first implementation without blocking Stage 7.
