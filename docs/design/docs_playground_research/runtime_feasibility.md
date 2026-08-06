# Playground runtime feasibility

**Status (2026-07-28): Direct runtime, real Pyodide Worker, opaque preview,
bounded cross-origin broker, deterministic wheel-build, sealed current
package, exact-package, and cached-desktop performance proofs passed. Mobile
performance, a production-origin deployment test, release-workflow
integration for future versions, and runtime-bundle deployment remain rollout
work. The tested PyEmscripten core 1.4.0 wheel is now published on PyPI, and a
fresh exact-package smoke passed from the public bytes. Stage 1 authorizes
iterative product implementation.**

**Shipping override (2026-07-29):** The separate-origin and mirrored-bundle
recommendations below remain risk research, not v1 requirements. V1 uses a
same-origin Worker, existing docs static hosting, the pinned Pyodide CDN, and
exact PyPI wheel URLs. The accepted risks and triggers for future hardening are
recorded in the current Stage 7 plan.

## Outcome

The existing PyO3 binding can be built as a Pyodide wheel without a binding
rewrite. Both custom wheels imported in an otherwise unmodified Pyodide
314.0.3 runtime:

- `citry_core==1.4.0` passed direct parse, compile, safe evaluation, and HTML
  marking calls;
- `citry_core==1.3.0` plus published `citry==0.2.0` passed a public API render
  covering static markup, expressions, control flow, a nested component, CSS,
  plain JavaScript, and `$component` JavaScript;
- published `citry==0.3.0` declares the intended exact
  `citry-core==1.4.0` dependency. The published pair passed a native Python
  smoke, including the `#c-key` case that breaks 0.2.0 over core 1.4.0;
- published `citry==0.3.0` plus the deterministic tagged 1.4.0 PyEmscripten
  wheel passed the complete minified playground matrix in Chromium 149,
  Firefox 151, and WebKit 26.5. Each engine asserted the installed versions
  and rendered a keyed nested component through the public API;
- that exact 7,011,715-byte core wheel was subsequently published on PyPI.
  Its public SHA-256 matches the matrix input, and a fresh Pyodide 314.0.3
  package smoke loaded the files.pythonhosted.org bytes together with
  `citry==0.3.0`, rendered the starter, and exercised a keyed nested component;
- the public-package proof repeated one module 100 times with a syntax failure
  and a render failure between successes. A fixed test render-id generator
  produced byte-identical output without a registry collision. Determinism
  under the production render-id policy remains untested;
- `citry.clear()` did not remove deliberate mutations to `builtins`,
  `sys.modules`, or the in-memory filesystem. Warm reuse is therefore an
  optimization, not an isolation boundary.
- setting `SOURCE_DATE_EPOCH` to the tagged source commit time stabilized the
  SBOM, while remapping the source, Cargo target, and Cargo home prefixes
  stabilized Rust debug paths. Two independent clean builds of both core
  versions were then byte-identical and contained no local build paths;
- one manifest now records every Pyodide runtime artifact and the historical
  and current public-package tracks by exact name, byte count, and SHA-256. The
  Node loader verifies and consumes local bytes in the recorded order without
  live package resolution. The browser prototype preflighted those bytes but
  Pyodide then re-fetched URL inputs, so verified-buffer consumption remains an
  explicit implementation proof;
- a rebuilt 1.4.0 wheel passed the direct API matrix inside a real module
  Worker in Chromium 149, Firefox 151, and WebKit 26.5. Terminating an
  infinite-loop Worker and bootstrapping a fresh Worker restored a working
  runtime in every engine;
- a same-origin Worker fetched with the docs test cookie in every engine. It
  also exposed `fetch`, `postMessage`, `close`, `WebSocket`, IndexedDB, and
  Cache Storage to Python. A Worker protects responsiveness but does not
  contain visitor code;
- an opaque-origin `sandbox="allow-scripts"` preview blocked parent DOM access,
  local storage, IndexedDB, popups, and top navigation in all three engines. It
  still requested local resources, a download URL, self-navigation, and all
  250 flood messages. WebKit attached the docs cookie to image, download, and
  self-navigation requests even though Chromium and Firefox did not;
- a cross-origin broker proof passed in all three engines. It kept the
  docs cookie out of the runner and its Worker, transferred a private
  `MessagePort` after exact source/origin/session/version validation, rejected
  an attacker-origin handshake, bounded source/result/rate, dropped an
  unsolicited Worker flood, rate-limited a direct runner-to-parent flood,
  recovered after timeout, and replaced a self-navigated preview. The same
  runner then loaded real Pyodide and the manifest-verified core wheel and
  passed the direct API matrix.
- two cached-desktop performance repetitions in each engine used five fresh
  Workers, 20 warmups, and 200 measured renders. Worst observed fresh-Worker
  p95 was 5.92 seconds in Firefox and worst warm edit-to-result p95 was 10.20
  milliseconds. The 61,669,376-byte Wasm heap, Python GC-object count, and
  loaded-module count did not grow across either 200-render sample window.

The technical result rules out a wasm-bindgen rewrite as the next step and
accepts a credential-free, different-site runner topology for continued
design. The build, public package availability, and exact package compatibility
uncertainties are closed. The production browser loader must still prove that
Pyodide consumes the buffers whose hashes were checked rather than re-fetching
their URLs. Stage 1 accepts the PyO3/Emscripten path for iterative
implementation. Production-origin, permanent release-CI, and physical-mobile
work remains explicit rollout validation.

## Verified scope

The following claims were executed locally rather than inferred:

| Claim | Result |
| --- | --- |
| Build tagged core 1.4.0 for Pyodide | Passed |
| Import `citry_core._rust` | Passed indirectly through all four direct APIs |
| Parse and compile a Citry template | Passed |
| Run `safe_eval` | Passed, `value * 2` returned `42` |
| Run `mark_html` | Passed, root attribute was added correctly |
| Build tagged core 1.3.0 | Passed |
| Render through published `citry==0.2.0` over core 1.3.0 | Passed |
| Install the historical public package without any resolver or live fetch | Passed from five hash-verified local wheels |
| Repeat a module 100 times | Passed with explicit Citry cleanup and a fresh namespace |
| Prove complete cleanup | Failed as expected; non-Citry state remained |
| Reproduce 0.2.0 plus 1.4.0 incompatibility | Passed; `#c-key` raised the known 8-versus-9 argument `TypeError` |
| Install published `citry==0.3.0` with its exact published core 1.4.0 dependency | Passed in native Python 3.14 |
| Render the 0.3.0/1.4.0 keyed-component regression case | Passed natively and in all three Pyodide browser engines |
| Run the complete playground against published Citry 0.3.0 and tagged core 1.4.0 | Passed after preflighting five exact local wheels in Chromium, Firefox, and WebKit; the prototype then re-fetched their URLs, so this does not prove verified-buffer consumption |
| Obtain the 1.4.0 PyEmscripten wheel from PyPI | Passed; the public file has the manifest name, 7,011,715-byte size, and SHA-256 |
| Run the exact 0.3.0/1.4.0 package smoke from public core bytes | Passed in Pyodide 314.0.3, including starter and keyed nested-component renders |
| Load and call core 1.4.0 in Chromium, Firefox, and WebKit module Workers | Passed |
| Terminate an infinite Python loop and recover with a fresh Worker in all three engines | Passed |
| Keep docs-origin credentials out of a same-origin Worker | Failed in all three engines; the Worker fetch sent the test cookie |
| Block preview access to the parent DOM and origin storage | Passed in all three engines with the candidate sandbox |
| Treat the preview sandbox as a network boundary | Failed; local fetch, images, and a download request reached the server |
| Bound hostile Worker or iframe messages in the browser | Failed; all 250 messages from each source reached the parent |
| Keep docs credentials out of a cross-origin runner and Worker | Passed in the local three-browser broker proof |
| Validate and bound the cross-origin host protocol | Passed for the proof schema, limits, timeout, and attacker probe |
| Load real Pyodide and core inside the cross-origin runner | Passed in all three desktop engines |
| Recover from preview self-navigation | Passed in the local three-browser broker proof |
| Reproduce 1.4.0 wheel bytes across different clean source and target paths | Passed with pinned tools, source epoch, path remapping, and SBOM normalization |
| Reject a substituted sealed artifact before startup | Passed with a deliberate wrong-hash wheelhouse |
| Keep the sealed historical proof off the live network | Passed with zero HTTP(S) attempts |
| Measure cached-desktop cold and warm p50/p95 in three engines | Passed across two repetitions per engine |
| Bound warm heap growth across 200 representative renders | Passed for observed Wasm heap, GC objects, and modules |

The scripts and observed artifact record are in
[`runtime_proof`](runtime_proof/). Built wheels are intentionally not checked
in because the proof directory should stay small. Their observed hashes are in
[`runtime_manifest.json`](runtime_proof/runtime_manifest.json).

This is executable feasibility evidence and an all-public package-input proof,
not yet a deployed production-runner proof.
The Node and browser proofs read the same manifest. The Node proof consumes its
verified local files. The browser vertical proof verified each fetched body,
then imported only `pyodide.mjs` from that body; Pyodide re-fetched its WASM,
standard library, lock, and wheel URLs. Every selected current-track artifact
has an exact public URL, but a preflight hash does not bind a later fetch. The
production browser loader must pass verified buffers through a supported
Pyodide boundary and include a mutation-between-fetches test. The historical
1.3.0 core remains a local research wheel; the 1.4.0 core entry records both
its tagged build source and immutable PyPI URL. Permanent release CI must
reproduce the exact artifact set for future core versions, and runtime
deployment must promote those bytes into the immutable docs wheelhouse.

## Pinned build tuple

The proof selected the newest official patch available on the research date,
[Pyodide 314.0.3](https://github.com/pyodide/pyodide/releases/tag/314.0.3),
rather than the earlier 0.29.4 line. The official
[314 ABI record](https://pyodide.org/en/stable/development/abi/314.html)
specifies the compatible platform and compiler requirements. Pyodide's
[general ABI guidance](https://pyodide.org/en/stable/development/abi.html)
also explains why an exact Emscripten and Pyodide ABI match is required.

| Part | Pinned value |
| --- | --- |
| Pyodide | 314.0.3 |
| `pyodide-cli` | 0.5.0 |
| `pyodide-build` | 0.37.0 |
| CPython in xbuild environment | 3.14.2 |
| Emscripten | 5.0.3 |
| Rust | 1.93.0 |
| Rust target | `wasm32-unknown-emscripten` |
| PyO3 | 0.27.1 from the workspace lockfile |
| maturin used by the isolated build | 1.14.1 |
| `wheel` used to regenerate normalized `RECORD` | 0.46.2 |
| wheel platform | `pyemscripten_2026_0_wasm32` |

The selected Rust version came from `pyodide config list`; the repository's
unversioned nightly was not used. Both core source trees are clean release
content: `citry-core@1.3.0` resolves to
`776eb1e60b1c09f55f335f5c9fd30ac5471ca9cc`, and the 1.4.0 binding inputs are
unchanged from the peeled `citry-core@1.4.0` commit at
`9c951efb3e69fb5a5c56295ee6ac84fa1fe5b3f2`. The annotated tag object itself
is `0bb5d7ad9e300fb47a8312b0bc480406efc2fc33`.

## Reproduction

The proof ran on macOS 26.3.1 arm64 with Node 25.8.1, pnpm 10.32.1, uv
0.10.12, rustup 1.29.0, and 23 GiB initially free. No `emcc` or
`pyodide-build` installation existed before the run.

Install the exact cross environment and compiler:

```sh
uvx --python 3.14.2 \
  --from pyodide-cli==0.5.0 \
  --with pyodide-build==0.37.0 \
  pyodide xbuildenv install 314.0.3 --path "$PROOF_XBUILDENV"

uvx --python 3.14.2 \
  --from pyodide-cli==0.5.0 \
  --with pyodide-build==0.37.0 \
  pyodide xbuildenv install-emscripten --path "$PROOF_XBUILDENV"

rustup toolchain install 1.93.0 \
  --profile minimal \
  --target wasm32-unknown-emscripten
```

Build core 1.4.0 from a clean tagged source archive. The checked-in wrapper
rejects Python cache artifacts and an incorrectly nested xbuild path, checks
the source version, pins the build and repack tools, remaps Rust paths,
normalizes generated SBOM workspace paths, and requires a source epoch:

```sh
CITRY_CORE_SOURCE="$PROOF_CORE_14_SOURCE" \
CITRY_CORE_VERSION=1.4.0 \
CITRY_CARGO_HOME="$PROOF_CARGO_HOME" \
SOURCE_DATE_EPOCH=1785157442 \
PYODIDE_XBUILDENV_PATH="$PROOF_XBUILDENV" \
PYODIDE_BUILD_OUT="$PROOF_DIST_A" \
CARGO_TARGET_DIR="$PROOF_CARGO_A" \
docs/design/docs_playground_research/runtime_proof/build_pyodide_wheel.sh
```

The 1.3.0 build used `git archive citry-core@1.3.0` in a temporary directory.
Because Git archives do not include submodule contents, the Ruff submodule was
archived separately at commit
`45bbb4cbffe73cf925d4579c2e3eb413e0539390`. The same build command then
targeted that temporary package tree with version `1.3.0` and source epoch
`1782839550`.

`PROOF_CARGO_HOME` is an explicit prepared Cargo home, not an output directory;
the wrapper remaps it along with the source and target roots before compiling.
Run the 1.4.0 wrapper again with independent output and Cargo target
directories, then require exact wheel equality:

```sh
docs/design/docs_playground_research/runtime_proof/verify_reproducible_wheels.sh \
  "$PROOF_DIST_A/citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
  "$PROOF_DIST_B/citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
  "$PROOF_CORE_14_ROOT" "$PROOF_CARGO_A" "$PROOF_CARGO_B" "$PROOF_CARGO_HOME"
```

Assemble the exact manifest-listed files into a temporary wheelhouse, then run
the checked-in sealed harness. `PYODIDE_DIR` is the matching xbuild
environment's `pyodide-root/dist` directory:

```sh
PYODIDE_DIR="$PROOF_PYODIDE_DIR" \
WHEELHOUSE="$PROOF_WHEELHOUSE" \
RUNTIME_MANIFEST="$PWD/docs/design/docs_playground_research/runtime_proof/runtime_manifest.json" \
RUNTIME_TRACK=direct-core-1.4 \
SMOKE_FILE="$PWD/docs/design/docs_playground_research/runtime_proof/core_smoke.py" \
node docs/design/docs_playground_research/runtime_proof/run_node.mjs
```

For the historical public track, use `RUNTIME_TRACK=historical-public-0.2` and
`public_api_smoke.py`. The harness verifies core 1.3.0, MarkupSafe,
typing-extensions, wrapt, and Citry 0.2.0 and passes their local paths directly
to `pyodide.loadPackage()` in manifest order. It does not load Micropip or
invoke a dependency resolver. A fetch guard rejects any HTTP(S) attempt.

The desktop browser proof uses the static
[`browser_harness.html`](runtime_proof/browser_harness.html), module
[`runtime_worker.mjs`](runtime_proof/runtime_worker.mjs), and automated
[`browser_probe.mjs`](runtime_proof/browser_probe.mjs). The probe verifies the
size and SHA-256 of every served Pyodide runtime artifact and the 1.4.0 core
wheel against the shared `runtime_manifest.json` before starting its server.
Playwright was installed only in the temporary proof directory:

```sh
npm install --prefix "$PROOF_BROWSER" \
  --ignore-scripts --no-audit --no-fund \
  playwright@1.61.0

PLAYWRIGHT_BROWSERS_PATH="$PROOF_BROWSER/browsers" \
  "$PROOF_BROWSER/node_modules/.bin/playwright" install \
  chromium firefox webkit

PYODIDE_DIR="$PROOF_PYODIDE_DIR" \
CITRY_CORE_WHEEL="$PROOF_DIST/citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
PLAYWRIGHT_MODULE="file://$PROOF_BROWSER/node_modules/playwright/index.mjs" \
PLAYWRIGHT_BROWSERS_PATH="$PROOF_BROWSER/browsers" \
PLAYWRIGHT_BROWSERS="chromium,firefox,webkit" \
RUNTIME_MANIFEST="$PWD/docs/design/docs_playground_research/runtime_proof/runtime_manifest.json" \
node docs/design/docs_playground_research/runtime_proof/browser_probe.mjs
```

The recorded runs used matching engines already present in Playwright's host
cache. The explicit install step above is required on a clean machine;
`npm install --ignore-scripts` alone does not provide browser binaries.

By default, the local cross-origin protocol proof does not load Pyodide. That
mode isolates the broker, credential, schema, timeout, flood, spoof, and
preview-navigation claims so their failures are not hidden behind runtime
startup:

```sh
PLAYWRIGHT_MODULE="$PROOF_BROWSER/node_modules/playwright/index.js" \
PLAYWRIGHT_BROWSERS="chromium,firefox,webkit" \
node docs/design/docs_playground_research/runtime_proof/cross_origin_probe.mjs
```

Set `CROSS_ORIGIN_PYODIDE=1` and supply the same verified runtime inputs to add
the real runtime and binding smoke inside that topology:

```sh
PYODIDE_DIR="$PROOF_PYODIDE_DIR" \
CITRY_CORE_WHEEL="$PROOF_DIST/citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
PLAYWRIGHT_MODULE="$PROOF_BROWSER/node_modules/playwright/index.js" \
PLAYWRIGHT_BROWSERS="chromium,firefox,webkit" \
RUNTIME_MANIFEST="$PWD/docs/design/docs_playground_research/runtime_proof/runtime_manifest.json" \
CROSS_ORIGIN_PYODIDE=1 \
node docs/design/docs_playground_research/runtime_proof/cross_origin_probe.mjs
```

The cached-desktop performance harness verifies and serves the complete
historical public-package track, starts five fresh Workers, then measures 200
renders after 20 warmups:

```sh
PYODIDE_DIR="$PROOF_PYODIDE_DIR" \
WHEELHOUSE="$PROOF_WHEELHOUSE" \
PLAYWRIGHT_MODULE="$PROOF_BROWSER/node_modules/playwright/index.js" \
PLAYWRIGHT_BROWSERS="chromium,firefox,webkit" \
RUNTIME_MANIFEST="$PWD/docs/design/docs_playground_research/runtime_proof/runtime_manifest.json" \
COLD_RUNS=5 WARMUP_RUNS=20 WARM_RUNS=200 \
node docs/design/docs_playground_research/runtime_proof/performance_probe.mjs
```

Run it twice before comparing against the provisional local guardrails. The
checked-in [`performance_observations.json`](runtime_proof/performance_observations.json)
records both 2026-07-28 repetitions and the exact manifest hash they used.

The harness CSP required `script-src 'wasm-unsafe-eval'` for Pyodide. Without
that source expression, Chromium blocked WebAssembly instantiation during
Worker bootstrap. The final proof retained `connect-src 'self'`,
`img-src 'self' data:`, `worker-src 'self'`, and no popup, download,
same-origin, or navigation sandbox permissions.

## Artifact and timing observations

| Artifact | Bytes | SHA-256 prefix |
| --- | ---: | --- |
| Pyodide WebAssembly | 9,596,462 | `e7f8fac36f8b` |
| Python standard library zip | 2,545,106 | `444c770dfd75` |
| deterministic core 1.3.0 wheel | 6,585,067 | `ed6d3eda67ec` |
| deterministic core 1.4.0 wheel | 7,011,715 | `765e4211b1d3` |
| published Citry 0.2.0 wheel | 194,448 | `8aa129681714` |
| published Citry 0.3.0 wheel | 532,890 | `953c18c67756` |

The two core wheels are already zip-compressed. Gzip reduced the selected
1.4.0 wheel only from 7,011,715 to 6,936,924 bytes. Payload size is therefore a
real product concern, not a server-compression oversight.

The initial 1.4.0 wheel and its immediate rebuild differed even though every
payload file, including `_rust.cpython-314-wasm32-emscripten.so`, was
byte-identical. The originating differences were cargo-cyclonedx's random SBOM
`serialNumber` and current `timestamp`; `RECORD` then changed transitively.
`SOURCE_DATE_EPOCH=1785157442` stabilized that layer, but independent source and
Cargo target directories exposed two more variables: release debug information
embedded absolute source, target, and Cargo-cache paths in the Wasm binary, and
the generated SBOM used absolute workspace package URLs. The final wrapper
rejects Python cache artifacts, remaps Rust paths, normalizes the generated
SBOM workspace URI, regenerates `RECORD` with `wheel==0.46.2`, and pins host
Python and Maturin. Two different clean tag-archive source directories and two
independent target directories then produced the same 7,011,715-byte 1.4.0
wheel and SHA-256. The 1.3.0 builds passed the same test with their own tagged
source epoch. Neither selected wheel contains any tested local source, target,
or Cargo-home path. The manifest keeps all earlier observations as evidence
rather than treating their hashes as selected artifacts.

The complete historical track is 20,409,000 fetched bytes: 13,522,699 bytes of
Pyodide runtime files and 6,886,301 bytes of core, pure-Python package, and
transitive wheels. This is a fetched-file baseline, not a cold-network or
post-cache transfer measurement.

The current 0.3.0/1.4.0 vertical track is 21,174,090 fetched bytes. Its exact
current-package matrix records first results of about 1.38 seconds in Chromium,
7.18 seconds in Firefox, and 1.38 seconds in WebKit on the local cached-desktop
host. Warm explicit edits were 47 to 63 milliseconds through the complete UI.

One local Node run measured 0.76 seconds to initialize Pyodide, 0.14 seconds to
load core 1.4.0, and 0.10 seconds for the direct smoke. The public track
measured 0.76 seconds for Pyodide, 0.15 seconds for pinned prerequisites and
core, 0.32 seconds for Citry installation, and 0.29 seconds for the full matrix
including 100 repeats. Earlier isolated runs reported about 471 MB peak
process footprint for the direct track and 453 MB for the public track.

These are warm-cache Node measurements on a current desktop. They are not
browser transfer timings or mobile evidence.

### Cached-desktop performance observations

The performance proof ran twice on the same macOS arm64 host. Each repetition
used five fresh Worker starts, 20 unmeasured warmups, and 200 measured renders
of a representative nested public-API component with CSS and JavaScript. All
assets were already present on a loopback server, so "cold" below means a new
Worker and Python runtime, not a cold browser cache or network. Values are the
ranges between the two repetitions:

| Engine | Fresh Worker p50 | Fresh Worker p95 | Warm end-to-end p50 | Warm end-to-end p95 |
| --- | ---: | ---: | ---: | ---: |
| Chromium 149 | 1,111.03-1,141.39 ms | 1,119.66-1,294.36 ms | 1.68-1.72 ms | 2.20-2.31 ms |
| Firefox 151 | 5,795.48-5,898.20 ms | 5,827.50-5,921.88 ms | 9.12-9.18 ms | 9.92-10.20 ms |
| WebKit 26.5 | 1,093.06-1,100.68 ms | 1,096.46-1,106.10 ms | 1.70-1.72 ms | 2.62-2.68 ms |

The nearest-rank p95 of only five fresh starts is the slowest sample, so these
are useful regression baselines but not population claims. Across 11 metric
samples per repetition, the post-warmup Wasm heap stayed at 61,669,376 bytes
and the Python GC-object and loaded-module counts had zero first-to-last
growth. `sys.getallocatedblocks()` returned zero in Pyodide. Chromium exposed
`measureUserAgentSpecificMemory()` but rejected the call in this headless
environment, and the other engines did not expose it. The proof therefore
does not claim complete process-heap measurement.

The evidence supports these **provisional local engineering guardrails** for
the same pinned runtime, representative workload, current desktop engines,
and warm filesystem cache:

| Guardrail | Candidate maximum |
| --- | ---: |
| Manifest-listed fetched payload | 21 MiB |
| Fresh Worker p95 | 6.5 s |
| Warm edit-to-result p95 | 15 ms |
| Post-warmup Wasm heap | 64 MiB |
| Wasm heap growth over 200 renders | 8 MiB |
| Python GC-object growth over 200 renders | 500 |
| Loaded-module growth over 200 renders | 5 |

These bounds are intentionally regression alarms with some measurement
headroom. They are not final product budgets, do not approve Auto-run, and do
not cover download latency, first uncached render, low-memory behavior, or a
physical mobile device. Stage 6 must replace or supplement them with deployed
network and device budgets.

## Desktop Worker and iframe observations

The local automated matrix used Playwright 1.61.0 with headless Chromium
149.0.7827.55, Firefox 151.0, and WebKit 26.5 on the same macOS arm64 host. It
served only hash-verified local runtime artifacts over `http://127.0.0.1`.

One warm-filesystem run measured:

| Engine | Load Pyodide | Load core | Direct smoke | Terminate and recover |
| --- | ---: | ---: | ---: | ---: |
| Chromium 149 | 0.77 s | 0.15 s | 0.02 s | 0.88 s |
| Firefox 151 | 3.88 s | 0.73 s | 0.04 s | 4.67 s |
| WebKit 26.5 | 0.78 s | 0.14 s | 0.01 s | 1.01 s |

Every Worker completed parse, compile, safe evaluation, and HTML marking.
Python called `postMessage` 250 times and every message arrived. Python also
fetched the same-origin probe endpoint, which received
`probe_cookie=docs-secret` in every engine. The Worker exposed `fetch`,
`postMessage`, `close`, `WebSocket`, IndexedDB, and Cache Storage, but not
`document` or `localStorage`.

The infinite-loop Worker did not answer a ping after entering Python. The
parent terminated it, created a fresh Worker, and obtained another successful
direct result in every engine. This verifies hard termination and recovery,
not graceful interruption or state transfer. The individual timings above are
observations, not p50, p95, cold-network, or product budgets.

The opaque-origin preview produced:

| Probe | Chromium 149 | Firefox 151 | WebKit 26.5 |
| --- | --- | --- | --- |
| Frame/message origin | `null` | `null` | `null` |
| Parent DOM, local storage, IndexedDB | Blocked | Blocked | Blocked |
| Local `fetch` | Succeeded with `Origin: null`, no cookie | Succeeded with `Origin: null`, no cookie | Blocked by the inherited `connect-src 'self'` policy |
| Local images | Loaded, no cookie | Loaded, no cookie | Loaded with the docs cookie |
| External fetch and image | Blocked by CSP | Blocked by CSP | Blocked by CSP |
| Popup and top navigation | Blocked | Blocked | Blocked |
| Self navigation | Requested and completed | Requested and completed | Requested and completed with the docs cookie |
| Download | Resource requested, no download began, no cookie | Resource requested, no download began, no cookie | Resource requested, no download began, with the docs cookie |
| Message flooding | All 250 delivered | All 250 delivered | All 250 delivered |

The result confirms that `sandbox="allow-scripts"` is useful DOM and storage
isolation, but it is not a credential, network, navigation, resource-request,
or message-rate boundary. In particular, WebKit's credential behavior means a
production design cannot infer credential omission from Chromium and Firefox.
The preview must have no credential-bearing same-origin resources to reach.

## Cross-origin broker observations

The broker proof served the docs parent from `127.0.0.1`, and the
runner and attacker from distinct `localhost` ports. The docs parent set an
HttpOnly, `SameSite=Strict` test cookie. The runner frame used
`sandbox="allow-scripts allow-same-origin"` and `referrerpolicy="no-referrer"`,
then created its same-origin module Worker. The proof passed in all three
engines with no page errors:

- exact origin, source window, session, protocol version, and message type were
  validated for the initial handshake;
- after validation, the parent transferred one `MessageChannel` and removed
  the window-message listener;
- an attacker-origin frame that knew the correlation value could not complete
  the handshake;
- the runner and Worker received no docs cookie, including on a deliberate
  credentialed cross-site request to the docs test endpoint;
- source was limited to 64 KiB, results and parent messages to 2 MiB, and runs
  to 10 per one-second window;
- monotonically increasing run ids were required, a 300 ms proof timeout
  terminated the active Worker, and a later run succeeded;
- 250 unrecognized Worker messages were counted and dropped rather than
  forwarded;
- the parent accepted at most 100 valid bounded port messages per second and
  dropped 150 messages from a direct 250-message runner flood;
- a second preview load was treated as unexpected navigation, after which the
  parent replaced the frame with an inert named frame and persistent
  diagnostic.

With its Pyodide option enabled, the same runner loaded the verified 314.0.3
runtime and core 1.4.0 wheel in its Worker. Parse, compile, safe evaluation,
and HTML marking passed in all three engines. The Worker origin was the runner
origin, and its deliberate credentialed request to the docs test endpoint sent
no docs cookie. One warm-filesystem run measured about 0.95 seconds for runtime
plus core in Chromium, 4.55 seconds in Firefox, and 0.92 seconds in WebKit.

The sizes, rate, and timeout are deliberately small proof constants, not
accepted product values. The session value correlates messages; it does not
authenticate code in a compromised runner artifact. The lightweight modes and
real Pyodide mode share the broker. The later Stage 6 vertical proof replaces
the fixed core smoke with the final AST runner and complete exact Citry
package through the same topology.

Loopback is a potentially trustworthy browser context and only approximates
distinct deployed sites. Production must use a credential-free origin on a
different schemeful site, not merely another hostname under the docs
registrable domain. It must avoid shared Domain cookies, expose no sensitive
endpoints, and set a runner CSP that permits only immutable runtime assets and
frames only from the exact docs origin. The proof allowed one docs endpoint in
`connect-src` solely to test cookie behavior; production must not carry that
allowance.

## Distribution and release policy

The PyEmscripten build is another platform wheel of the existing
`citry-core` distribution, not a separate browser package. PEP 783 standardizes
the `pyemscripten_${YEAR}_${PATCH}_wasm32` platform tag, and current Pyodide
publishing guidance says these are standard wheels that can be uploaded to
PyPI and selected by `micropip` or a Pyodide virtual environment's `pip`.
Native installers ignore the incompatible WebAssembly tag, while the verified
Pyodide tuple selects:

```text
citry_core-<version>-cp314-cp314-pyemscripten_2026_0_wasm32.whl
```

Sources, checked 2026-07-28:

- [PEP 783](https://peps.python.org/pep-0783/)
- [Publishing Wasm wheels](https://pyodide-build.readthedocs.io/en/latest/how-to/publishing.html)
- [Python package formats](https://packaging.python.org/en/latest/discussions/package-formats/)

The unique PyEmscripten wheel was added to the current
`citry-core==1.4.0` release on 2026-07-28 through GitHub Actions Trusted
Publishing. PyPI accepted the file during the release's 14-day addition
window. The exact Citry 0.3.0 dependency made this the practical repair: its
immutable metadata pins core 1.4.0, and the uploaded bytes are identical to
the tagged 1.4.0 browser wheel that passed the full local matrix. A late file
still changes what the same version can install according to date, cache, and
mirror state, so future releases must assemble their complete platform
inventory before upload.

Sources, checked 2026-07-28:

- [PyPI Upload API](https://docs.pypi.org/api/upload/)
- [PyPI JSON API metadata behavior](https://docs.pypi.org/api/json/)
- [PyPI's 14-day release-file policy](https://blog.pypi.org/posts/2026-07-22-releases-now-reject-new-files-after-14-days/)
- [`citry-core==1.4.0` release](https://pypi.org/project/citry-core/1.4.0/)

The selected policy and completed repair are therefore:

1. Completed on 2026-07-28: during PyPI's 14-day file-addition window for
   `citry-core==1.4.0`, upload the exact tested PyEmscripten wheel and verify
   its filename, 7,011,715-byte size, and SHA-256 from PyPI.
2. Treat that late platform addition as a one-time repair. Future core
   releases must collect the sdist, native wheels, and PyEmscripten wheel in
   one tested inventory before the publishing job.
3. The fallback was not needed. If a similar late upload is declined for a
   future repair, release a new core version and a new Citry patch that exactly
   pins it, then repeat this matrix.
4. Keep PyPI as the public package source of truth. Promote the exact browser
   wheel and runtime files into a content-addressed, immutable docs wheelhouse
   only after their names, sizes, and SHA-256 hashes match the release
   manifest. The page must not resolve packages from live PyPI on startup.

PyPI has no multi-file transaction, so "one release" means a workflow-level
guarantee: build, test, inventory, hash, and attest the whole artifact set,
then let one Trusted Publishing job upload it. The docs wheelhouse needs only
the PyEmscripten and pure-Python browser dependencies, not native wheels or the
sdist.

## Release defect kept separate from WebAssembly

Published Citry 0.2.0 declares `citry-core>=1.3.0`. PyPI can therefore resolve
core 1.4.0. The proof installed the custom 1.4.0 wheel first and then installed
Citry 0.2.0 without dependencies to reproduce the resulting runtime contract
failure:

```text
ComponentNode.__init__() takes 8 positional arguments but 9 were given
```

The exact 0.2.0 plus 1.3.0 pair renders correctly. This distinguishes a package
compatibility defect from a Pyodide or PyO3 failure. Published Citry 0.3.0
fixes the dependency contract by pinning core 1.4.0. That pair passed the
native regression smoke, and the published Citry wheel plus deterministic
tagged core browser wheel passed the three-engine playground matrix. The exact
core browser bytes are now public on PyPI.

## Current package acceptance on 2026-07-28

PyPI reports `citry==0.3.0` with `citry-core==1.4.0` in `Requires-Dist`. The
published pure-Python wheel is 532,890 bytes with SHA-256
`953c18c677563ef312416fb2e3c17df29d2e14aad86b96a1be011aaf2f95820e`.
The core release now includes
`citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl`, uploaded at
`2026-07-28T20:33:57.231639Z`, with 7,011,715 bytes and SHA-256
`765e4211b1d333800d9d620c6f310f0a06ddac1574fbfac4af1bd53c9c31c964`.

Sources, checked 2026-07-28:

- [`citry==0.3.0` JSON metadata](https://pypi.org/pypi/citry/0.3.0/json)
- [`citry-core==1.4.0` JSON metadata](https://pypi.org/pypi/citry-core/1.4.0/json)

An isolated native Python 3.14 run installed the published pair and passed the
starter output contract plus string, `CitryElement`, `CitryRender`, and
`#c-key` cases. The browser wheelhouse then combined that exact published
Citry wheel with the deterministic tagged core wheel and the three pinned
transitive wheels. The minified vertical build emitted bundle
`b724f52d9cbd5ebcb2fa`; two builds produced build-manifest SHA-256
`59d9d325d41f2a3226b2ccd359b0009d4d5281cd9a6574b736ce02d109f266cd`.

The complete matrix passed in Chromium 149.0.7827.55, Firefox 151.0, and WebKit
26.5. Every engine asserted the installed package versions and rendered a
keyed nested component. The result record is
[`browser-results.json`](vertical_proof/results/browser-results.json). This
closes the exact-package compatibility question. The public PyPI wheel is
byte-identical to that matrix input. A fresh Node-hosted Pyodide 314.0.3 smoke
then downloaded the public core file, verified its size and hash, loaded it
with the four other public current-track wheels, asserted both package
versions, and rendered the starter plus a keyed nested component. The
all-public package-input question is therefore closed; immutable docs
wheelhouse promotion remains deployment work.

## Threat model and boundaries

The assets to protect are the editor source buffer, the parent docs DOM,
docs-origin cookies and storage, authenticated or state-changing endpoints,
visitor data in other tabs, the visitor's device resources, and the integrity
of diagnostics shown by the parent page. The playground application excludes
source from its analytics, telemetry, and logs while the full docs and runner
application, dependency, build, and hosting chain is trusted. This includes the
editor dependencies, Pyodide, and every wheel. Pins and hashes detect byte
substitution but do not make selected code trustworthy. Visitor Python retains
runner-origin network APIs, and preview self-navigation and download activation
remain possible, so visitor code can construct URLs that enter hosting logs.
The runner document and broker can also read the
source and forge results, so a compromised runner is outside the application
privacy claim and is part of the trusted computing base.

Visitor Python can also create runner-origin IndexedDB and Cache Storage data
that survives Worker termination and may be visible to another runner-origin
tab. Preview download activation, like self-navigation, can issue a docs-origin
request even when the sandbox prevents a completed download. These capabilities
are accepted only for the locally edited v1 model and must be disclosed and
probed on the production origins.

The actors are locally typed code, future copied or shared code, rendered HTML
and JavaScript, compromised runtime artifacts, and accidental infinite or
resource-intensive programs.

The proposed boundaries have deliberately limited claims:

- A Worker protects main-thread responsiveness. It is not a sandbox. Official
  Pyodide guidance places browser execution in a module Worker, and Python can
  reach Web APIs exposed in that realm. See the official
  [Worker example](https://pyodide.org/en/stable/usage/webworker.html).
- Worker termination is the proposed hard cancellation mechanism because
  `citry.clear()` cannot restore arbitrary Python, filesystem, or JavaScript
  state.
- A same-origin Worker is rejected for production containment because every
  tested engine sent the docs cookie. The docs page also cannot directly
  create a Worker from a dedicated cross-origin entry, and a blob Worker would
  inherit its creator's origin. The selected production topology is a runner
  iframe on a credential-free, different-site origin with only the sandbox
  flags needed to retain that origin and create its same-origin module Worker.
  The bounded broker passed in all three desktop engines. Runtime artifacts
  must be self-hosted there, with no secrets or sensitive endpoints and a
  response CSP limited to immutable runner assets and the exact docs
  `frame-ancestors` origin. The runner document, broker, and hosting account are
  trusted for source confidentiality and result integrity. Visitor Python retains
  every channel that static allowlist permits; same-origin requests can put
  visitor-created paths or queries in runner logs. A stricter post-bootstrap
  denial would require a separately designed lifecycle that moves preverified
  bytes into a new connect-blocked context; CSP does not change dynamically
  for an existing document or Worker. Combined-Pyodide verification passed
  locally; production-origin verification remains open.
- `sandbox="allow-scripts"` without `allow-same-origin` is the candidate result
  frame policy. It should block direct parent DOM access, but it does not by
  itself promise network isolation. Self-navigation and download activation can
  still issue requests and may carry docs cookies in some engines.
- Every iframe message must be treated as hostile. A nonce is correlation, not
  authentication, because visitor JavaScript can read and spoof it.
- v1 may automatically run only the built-in trusted starter and code edited
  locally by the visitor. Automatically loading code from a share link remains
  out of scope until the threat model is revisited.

## Iterative rollout validation

The following tests and release tasks remain. Stage 7 makes the IndexedDB,
Cache Storage, preview-navigation, and download probes production-activation
requirements while keeping broader capability and performance work iterative:

- exercise real Cache Storage and IndexedDB write/read/delete operations across
  Worker restart and a second runner-origin tab, then clean up the test keys.
  WebSocket operations remain a broader follow-up because the production
  runner exposes no WebSocket endpoint;
- repeat the broker and preview matrix on the production runner origin with
  its real headers, cookie domain, cache behavior, immutable asset paths, and
  no deliberate docs `connect-src` test exception. Include both preview
  self-navigation and download-triggered requests;
- derive product message sizes, rate limits, timeouts, and concurrent-session
  limits from measured source/output distributions and abuse tests. The proof
  constants only establish enforcement mechanics;
- collect uncached network and representative physical mid-tier mobile cold,
  warm, p50, p95, heap-pressure, and termination-recovery measurements. The
  local desktop cached-artifact matrix is complete;
- run the performance workload inside the accepted deployed cross-origin
  broker, not only its equivalent verified Worker package track;
- integrate the deterministic build wrapper and repeated-build comparison into
  release CI on its publishing host. The local proof is byte-reproducible, but
  the release workflow does not yet enforce it;
- promote the published core 1.4.0 PyEmscripten wheel into the docs
  wheelhouse and verify that the promoted bytes exactly match PyPI;

The local runner topology is accepted for implementation. Deployment promotes
it only after the public-origin smoke confirms the configured headers and
credential boundary.

## CI and release sketch

1. Pin the tuple in one machine-readable manifest and reject an unversioned
   Rust toolchain.
2. Add a Linux `pyodide` job to
   `.github/workflows/py--citry-core--publish.yml` and include it in the
   existing release job's dependencies. Build from the release-tag checkout
   with the exact xbuild environment and Emscripten installer. A second macOS
   build can detect host-specific drift, but Linux should own the release
   artifact.
3. Build only from clean tag archives and reject Python cache artifacts. Set
   `SOURCE_DATE_EPOCH` from the peeled release commit, pin host Python,
   Maturin, and `wheel`, remap Rust source, target, and Cargo-home paths, and
   normalize generated SBOM workspace paths before regenerating `RECORD`. Run
   the checked-in wrapper twice with different source, output, and target
   directories, then use the comparison script to require identical bytes and
   no host paths. Assert that the selected wheel has the expected project,
   version, Python, ABI, and
   `pyemscripten_2026_0_wasm32` tags. Validate its metadata, `RECORD`, byte
   size, and SHA-256 before upload.
4. Install the wheel in stock Pyodide 314.0.3 and run `core_smoke.py`.
5. Install only manifest-listed wheels with dependency resolution disabled and
   run the exact 0.3.0/1.4.0 public matrix plus browser Worker tests.
6. Completed for the 1.4.0 repair: verify the existing PyPI inventory, attest
   the tested PyEmscripten wheel, and upload only that missing platform
   artifact through controlled Trusted Publishing. For every later release,
   collect the full sdist and wheel inventory before the sole publishing job.
7. Completed for the 1.4.0 repair: verify that PyPI reports the expected
   filename, size, and hash, then run the current-package smoke from the public
   bytes before promoting the browser bundle.
8. Promote the exact browser artifacts and manifest to the immutable docs
   wheelhouse, then make the docs build fail if its requested runtime version
   or hashes differ from that manifest.

The next Stage 1 rollout work is to prove the production origin, enforce the
proven build contract in the permanent release workflow, measure
physical-mobile and uncached network behavior, and promote the exact public
artifacts into the docs wheelhouse, not to design a new binding architecture.
