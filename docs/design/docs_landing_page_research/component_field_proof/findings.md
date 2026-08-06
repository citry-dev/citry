# Component-field architecture findings

**Decision date:** 2026-07-28

**Decision:** Use a component-generated canvas projection with exactly 1,024
logical `LandingCell` components for the first production art prototype. Arrange
the descriptors on a 41-column by 25-row field. Keep literal DOM as the
inspectable small-count reference and CSS gradients as the static fallback.

This accepts an architecture for Research 2. It does not approve the final art
direction or authorize production landing-page implementation.

## Evidence

Two reviewed artifacts support the decision:

- [five-round scale sweep](results/reference-2026-07-28-practical.json), covering
  256, 512, 1,024, 2,048, and 4,096 logical cells on desktop and throttled
  mobile; and
- [12-round target cohort](results/reference-2026-07-28-target-1024.json),
  covering the selected 1,024-cell count on both profiles.

Both use the release Rust extension and fixture SHA-256
`59f5ecf820da0b8d44f07b6aa8baa13c7ff38f75015ec14a11f3153763f31bf4`.
The exact `browser_probe.py` used by both artifacts has SHA-256
`553d074ce416eda29a955ef3a74c2fa3b422a604b5fb7faaded184f414cfac34`.
The recorded host is an arm64 Mac with 24 GiB RAM, Python 3.13.12, Playwright
1.61.0, and Chromium 149.0.7827.55 using SwiftShader. Mobile uses a 390 by 844
viewport at DPR 2, 4x CPU throttling, and the fixed Slow 4G profile described in
the proof README. These are lab results, not field Core Web Vitals.

## Target-count result

The 12-round 1,024-cell cohort produced no invalid timing or retained-state
sample. Values below are baseline-relative where the label says `added`.

| Measure | Literal DOM | Canvas projection | Gate |
| --- | ---: | ---: | ---: |
| Added raw HTML | 903,634 B | 56,663 B | at most 307,200 B |
| Added deterministic-gzip HTML | 48,072 B | 11,775 B | at most 32,768 B |
| Total browser elements | 1,066 | 44 | diagnostic |
| Field DOM elements | 1,024 | 0 | diagnostic |
| Mobile lab LCP p75 | 348 ms | 252 ms | at most 2,500 ms |
| Mobile interaction proxy p75 | 160 ms | 64 ms | at most 150 ms |
| Mobile interaction proxy max | 160 ms | 72 ms | at most 200 ms |
| Mobile longest task | 109 ms | 0 ms | below 100 ms |
| Mobile maximum frame gap | 116.7 ms | 50.1 ms | below 100 ms |
| Mobile CLS max | 0 | 0 | at most 0.01 |

Canvas passed every target-count gate on both profiles. Literal DOM failed both
payload gates and the mobile interaction-p75, longest-task, and frame-gap gates.
The target result therefore invokes the predeclared rule: canvas wins when
literal DOM fails at the visual count and canvas passes.

After five complete ripples, both valid target implementations added zero DOM
nodes and zero JavaScript event listeners. Both reported zero active animation
handles and zero scheduled frames. The forced-GC heap values remain diagnostics,
not proof of leak absence from one retained-state round.

## Scaling result

The five-round sweep found these highest passing counts across desktop and
mobile:

| Renderer | Highest passing count | What limits the next range |
| --- | ---: | --- |
| Literal DOM | 256 | 512 exceeds the 300 KiB raw payload cap; 1,024 also fails mobile wave budgets |
| Canvas projection | 2,048 | 4,096 exceeds the gzip cap and fails mobile blocking and frame-gap budgets |

Canvas at 2,048 passed, including an 88 ms mobile interaction-proxy p75, 80 ms
total-blocking p75, and 66.7 ms maximum frame gap. The first prototype still
uses 1,024 because that is the selected public proof count and retains more
performance margin. Research 3 may reduce visible density through art direction,
but it may not increase the delivered descriptor count beyond 1,024 without a
new recorded decision.

Literal DOM at 4,096 missed the 20-second readiness window in all five desktop
and all five mobile samples. It also failed the mobile retained-state case at
2,048 and both retained-state profiles at 4,096. These failures remain explicit
invalid samples in the scale artifact.

Fresh-process median rendering at 1,024 was about 215 ms for canvas and 254 ms
for literal DOM in the 12-round artifact. Warm medians were about 217 ms and
249 ms, so both missed the optional 100 ms warm orientation target. The page is
static build output, making this a build-time cost rather than a per-request
latency. Revalidate it against the complete production page, but do not reject
the selected canvas path on this optional target.

## Correctness and fallback result

At 1,024 cells, both renderers preserved the exact descriptor digest and logical
count. The reviewed matrix also passed:

- readable hero and CTA with JavaScript unavailable;
- a visible CSS field fallback for no-JavaScript canvas;
- no focusable or pointer-active control inside the decorative field;
- a static field with no scheduled motion under reduced motion;
- a plain readable background in forced colors;
- keyboard operation plus 320 px reflow at 200% text;
- zero continuing animation work after a settled wave;
- bounded canvas DPR and backing allocation after resize;
- a stable fallback when the 2D context is unavailable or descriptors are
  corrupt; and
- 1,024-descriptor initialization without console or page errors in Firefox
  151 and WebKit 26.5.

The canvas is a projection, not a replacement for the component proof. Python
renders one transparent `LandingCell` per logical cell into a single inert JSON
descriptor block. One `LandingField` browser controller validates and draws the
ordered descriptors. Public copy may say that the field contains 1,024 Citry
components, but supporting copy or the inspector must not imply that it contains
1,024 DOM nodes.

## Accepted production contract

- Deliver exactly 1,024 descriptors to every first-navigation viewport. The
  responsive presentation may crop or soften detail, but static HTML cannot
  claim a smaller mobile payload after delivery.
- Use a 1,600 ms top-left radial arrival front plus 350 ms settle. Intentional
  ripples use a 550 ms front plus 350 ms settle and the fixed tested origins.
- Run no ambient animation in the first implementation. Research 3 may propose
  one only with a pause control and a fresh performance/accessibility result.
- Cap effective canvas DPR at 2 and backing allocation at eight million pixels.
- Keep the CSS fallback visible until descriptor validation, canvas allocation,
  and the first successful static draw all complete.
- Stop scheduled work while paused, hidden, offscreen, under reduced motion, or
  after controller cleanup. Persist the pause choice only for the site session.
- Keep the entire visual surface decorative, `aria-hidden`, outside focus order,
  and outside pointer hit testing. The visible wave control remains ordinary
  page content.
- Expose the logical count, descriptor hash, projection strategy, and a link to
  the proof in the proposed component inspector. Do not present machine-local
  timing from a dirty research worktree as a universal live metric.

## Revalidation boundary

Repeat the target cohort against a clean release build of the complete landing
page before publication. Reopen this decision if the component descriptor
schema, runtime initialization path, canvas controller, production CSS, page
shell, target count, animation timing, or performance budgets change
materially. Field Core Web Vitals after launch can challenge the lab result.
