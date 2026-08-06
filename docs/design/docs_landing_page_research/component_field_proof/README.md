# Component-field architecture proof

This proof compares two ways to render Citry's landing-page component field:

- `dom`: every logical cell is a normal Citry component with one inert DOM
  element;
- `canvas`: every logical cell is a transparent Citry component that writes one
  compact descriptor into a shared JSON block, then one field component paints
  those descriptors to a canvas; and
- `baseline`: the same page shell and field allocation without cells or a field
  controller, used to calculate incremental cost.

The production landing page is not implemented here. The current docs builder
has no landing layout dispatch, and Research 2 must not add it indirectly.

## Fixed comparison contract

Both renderers consume the same ordered descriptor list. A descriptor contains
a stable integer ID, normalized coordinates, radial phase, and palette index.
The harness records the list's SHA-256 digest and rejects missing, duplicate,
non-finite, or out-of-range data. Canvas does not generate logical cells in the
browser.

Test counts are 256, 512, 1,024, 2,048, and 4,096. They are scaling probes. A
static page cannot know the first-navigation viewport, so desktop and mobile
receive the same fixed payload. The field may crop its coordinate plane on a
narrow screen, but it may not pretend that fewer descriptors were delivered.

The animation protocol uses a top-left radial arrival followed by five fixed
ripple origins. The server output is readable and static before JavaScript.
Reduced motion, paused motion, an offscreen field, and a hidden document must
schedule no continuing animation work.

Portable evidence:

- exact component and descriptor count plus ordered digest;
- raw and deterministic gzip HTML size;
- DOM and listener counts;
- JavaScript-disabled, reduced-motion, forced-color, keyboard, resize, corrupt
  data, and unavailable-canvas behavior; and
- cleanup after repeated ripples.

Machine-local evidence:

- fresh and warm Citry render time;
- lab FCP, LCP, CLS, synthetic interaction latency, long tasks, animation-frame
  intervals, and CDP main-thread counters; and
- forced-GC heap and DOM counters.

Lab measurements are not field Core Web Vitals or INP. They guide this renderer
decision on the recorded machine and browser only.

## Decision gates

At a candidate delivered count, a renderer must:

- preserve the exact descriptor count and digest;
- produce no console error, page error, browser crash, or invalid descriptor;
- keep the complete hero readable when the field or JavaScript is absent;
- keep the decorative field out of focus and pointer hit-testing;
- render a static field under reduced motion and a plain background in forced
  colors;
- release animation handles, field listeners, and retained DOM after five
  settled ripples;
- keep lab CLS at or below `0.01` in every sample;
- keep synthetic interaction p75 at or below `150 ms`, with no valid sample
  above `200 ms`;
- produce no long task or frame gap at or above `100 ms` during a wave;
- add no more than `300 KiB` raw HTML and `32 KiB` deterministic gzip relative
  to the baseline; and
- cap canvas backing allocation at eight million pixels and effective DPR at
  two.

Lab LCP budgets are `1.5 s` on the desktop profile and `2.5 s` on the
CPU-throttled mobile profile. Render-time targets of `100 ms` warm and `500 ms`
fresh-process median are orientation targets because the deployed docs page is
static build output.

Literal DOM wins when both renderers pass at the lowest count that satisfies
Research 3's approved art direction. Canvas wins only when DOM fails a hard
gate at that count and canvas passes. If both fail, reduce the scope or count;
do not weaken the budgets after seeing the result.

## Run the proof

Install the existing optional browser tools and Chromium, then build the Rust
extension in release mode before recording render timings:

```bash
uv sync --locked --all-packages --group e2e
uv run --no-sync playwright install chromium
(cd packages/py/citry_core && uv run --no-sync maturin develop --release)
```

Run component and static-contract tests:

```bash
uv run --no-sync pytest \
  docs/design/docs_landing_page_research/component_field_proof/test_components.py
```

Run the practical local browser cohort:

```bash
uv run --no-sync python \
  docs/design/docs_landing_page_research/component_field_proof/browser_probe.py \
  --counts 256 512 1024 2048 4096 \
  --rounds 5 \
  --output results/local-component-field.json
```

Use `--rounds 12` for a reference decision run. The runner discards one suite
warmup, randomizes count and renderer order with a recorded seed, creates a
fresh browser context per navigation, and records baseline-relative deltas.
The accessibility and fallback matrix defaults to the selected 1,024-cell
candidate; change that with `--correctness-count` for a focused investigation.
Run `--help` for all focused-run controls.

The harness fails closed on an invalid count, missing Playwright installation,
unavailable browser, malformed result, or harness failure. Renderer-specific
timeouts and browser errors remain in the artifact as invalid samples, and
cohort completeness becomes a failed architecture gate. They are never dropped
or converted to zero-valued performance data.

The reviewed outcome and its limitations are in [findings.md](findings.md).
The underlying practical scale sweep and focused 12-round target cohort live in
[`results/`](results/).
