# Stage 3 typed-card pilot

**Status (2026-07-26): authored and automatically verified; maintainer review
time and acceptance are pending. The 2026-07-27 Examples architecture follow-up
split the gallery into recipe pages and moved bare demos below `/demo/`.**

This report records the bounded vertical pilot approved in
[`docs_content.md`](../docs_content.md). It is a review slice, not approval for
the full content rewrite or the Stage 4 navigation and editorial kit.

## Opening baseline and scope

- Baseline: `DC3-20260726T131933Z-6ad74ee1`.
- Opening commit: `6ad74ee165f846b3e1c59d7292e39ebdc1d3545e`.
- Opening observation: 2026-07-26 at 13:19 UTC, after the complete Stage 1 and
  Stage 2 validator passed against the live working-tree bytes.
- Pilot job: define and render a component with one typed input, one default
  slot, component-owned CSS, and an instance-scoped CSS value; follow that
  journey through Docs, Examples, and Reference.
- Stable reader locations: `/getting-started/your-first-component/`,
  `/examples/card/`, `/examples/card/demo/`, `/reference/component/`,
  `/reference/builtins/#c-slot`, and `/reference/slots/`.
- Explicit exclusions: navigation redesign, other content families, host
  integration, selector-scoping implementation, broad Reference rewriting,
  deployment, and the full content map.

The initial implementation estimate was 14 to 17 core files and roughly 250
to 450 changed lines. The estimate included the tutorial, recipe, card source,
two focused Reference docstrings, factual corrections, projection behavior,
and focused tests. The Stage 3 stop rule applies if the core file count exceeds
34 or the dependency path becomes unbounded.

## External-state update

The maintainer enabled GitHub Discussions before this stage. A public API check
at 13:24 UTC returned `has_discussions: true`, `has_issues: true`, default branch
`main`, and homepage `https://citry.dev`.

This resolves the disabled-channel observation recorded in Stage 2. The Stage
2 row remains an accurate time-bound observation and is not rewritten. The
Community Help page still sends ordinary questions to Issues, while the issue
chooser and Contributing page point to Discussions. Aligning that reader route
belongs to the later Community content wave, not this typed-card pilot.

## Pilot decision

The phrase "scoped CSS" in the proposal did not match the shipped static-CSS
behavior. Citry emits `Component.css` selectors as authored, so selectors are
page-wide. Citry does scope values returned from `css_data()` to rendered root
elements through generated `data-ccss-*` markers.

The pilot therefore demonstrates the shipped boundary:

- one required `accent: str` field in `Card.Kwargs`;
- one required `default: SlotInput` field in `Card.Slots`;
- a namespaced `.demo-card` selector that remains page-wide;
- one typed `CssData.accent` value returned by `css_data()` and scoped to the
  rendered Card instance;
- a complete `CardPage` that fills the slot and places CSS in its document
  head.

The tutorial and recipe state that plain annotations do not validate runtime
value types. They distinguish composition from render-time validation and do
not claim that `accent: str` alone rejects an integer.

## Authored review slice

The slice has 12 material facts in `fact_ledger.tsv`. Each row records reader
jobs, reader surfaces, current applicability, source and test locators,
prerequisites, supported context, security implications, successful outcome,
failure behavior, canonical ownership, links, example need, and review status.

Reader-facing changes are deliberately narrow:

1. The first-component tutorial now has an outcome, prerequisites, executable
   source, visible checkpoint, failure examples, CSS boundary, recap, and next
   actions.
2. The Card section on Examples is a source-first recipe linked to the tutorial
   and exact public Reference entries.
3. The executable Card owns the code shown by the tutorial, browser recipe,
   Markdown companion, and `llms-full.txt` projection.
4. `Component.css`, `Component.Slots`, and `SlotInput` Reference docstrings
   state the static-selector and required-field boundaries.
5. The two directly conflicting Getting Started sentences no longer claim
   automatic static selector isolation.

The browser widget now opens on Component source, exposes keyboard-operable tab
semantics, gives every demo frame a descriptive title, and ignores browser-only
controls and highlighted source during Pagefind indexing. Theme synchronization
is opt-in for the Card pilot. Existing demos with light-only styles keep their
own default scheme until their separate content waves make them theme-safe.

## Dependencies and conflicts

The pilot depends on six bounded implementation areas:

- component schema creation and render-time input finalization;
- slot normalization and static component tag rules;
- component CSS collection, CSS-data validation, and dependency placement;
- example discovery and the browser/text dual projection;
- Reference extraction and cross-reference anchors;
- Pagefind plus the docs theme and tab behavior.

Resolved conflicts:

- static `Component.css` selector isolation was a false docs claim;
- the old first-component page taught a redundant `template_data()` override as
  necessary for one-to-one inputs;
- "typed" could be misread as runtime value-type validation;
- the Examples browser widget appeared live-demo-first even though Examples is
  the code-first surface;
- generated Examples Markdown previously contained iframe, radio-tab, and
  syntax-highlighter HTML.

Open dependencies discovered by the pilot:

- generated Reference pages still have no `.md` companions, and their
  `llms-full.txt` projection remains HTML-heavy;
- the complete content sweep still needs page-archetype metadata and an
  approved content map from Stage 4;
- actual maintainer review minutes are unavailable until this slice is
  reviewed;
- the repository-wide gate currently reports failures in concurrent ownership,
  client-graph, cache, and component-node work plus the repository coverage
  threshold. The complete docs browser collection passes after those concurrent
  client-graph bytes changed during the pilot.

These dependencies are finite. The Reference text projection belongs in the
Stage 4 editorial-kit and builder decision unless the maintainer promotes it to
a separate focused builder task. The concurrent client-graph failure belongs
to its active product work and does not change the typed-card facts.

## Review size and generated output

The closing slice changes 26 files: 19 core reader, builder, presentation,
Reference, or test files and seven research-control files. The core count is
1.12 to 1.36 times the initial 14 to 17 file estimate, below the 2x stop rule.
The extra scope came from fixing the already exposed machine projection,
keyboard behavior, search boundary, and theme propagation rather than adding a
second reader journey.

The opening Examples measurements were 1,290 authored bytes, 178,564 rendered
HTML bytes, and 154,873 Markdown-body bytes. The pilot's closing build produced
the following historical measurements. They predate the per-recipe split:

| Artifact | Closing bytes | Observation |
| --- | ---: | --- |
| `/examples/index.html` | 193,162 | Rich browser source tabs and live demos remain. |
| `/examples/index.md` | 33,952 | Fenced component/page source and live-result links; no iframe or tab markup. |
| Examples block in `llms-full.txt` | 33,865 | Same concise text projection; no browser-only markup. |
| First-component HTML | 59,964 | Full tutorial with highlighted included source. |
| First-component Markdown | 6,678 | Self-contained tutorial source and prose. |
| Complete `llms-full.txt` | 1,232,726 | Still dominated in part by HTML-heavy generated Reference. |

The Examples machine-readable payload fell by about 78 percent while retaining
both executable source files. Browser HTML grew because the source remains rich
and now carries explicit accessibility relationships.

Automated review adds four validator failure tests, four focused content-pilot
tests, three new Card behavior checks, and three browser journey checks. Existing
example, snapshot, build, Reference, search, and guard tests provide supporting
coverage.

Maintainer active review minutes and number of review passes are `unavailable`.
They must be supplied by the maintainer rather than inferred from agent elapsed
time. Once supplied, record minutes per accepted fact and any fact or surface
that caused rereading.

## Closing reconciliation

The closing fingerprint preview identified the Stage 3 report, ledger,
reader-evidence refresh, pilot implementation, and pilot tests as expected
changes. It also identified concurrent changes to the changelog, parser, two
non-pilot docs pages, and active component, cache, Events, ownership, and client
runtime sources.

The concurrent inputs were not folded into the pilot. The two affected Stage 2
observations were rechecked: the Unreleased section still has 92 top-level
entries, and the current Component still supports the construction behavior
recorded in EV-004. Cargo tests passed, the 318 focused component and dependency
tests passed, and the 18 docs browser tests passed against the final live bytes.
The remaining repository-wide failures are recorded below rather than treated
as pilot evidence. The reconciled closing fingerprint records the exact bytes
used for these conclusions.

## Verification record

Verified on the closing live bytes:

- Stage 3 fact-ledger validator failure paths: 22 passed.
- Focused Card, projection, and content-pilot tests: 15 passed.
- Docs tests excluding browser collection: 323 passed.
- Focused component, slot, tag-rule, CSS-data, and dependency tests: 318 passed.
- Strict docs build and all generated-site guards: passed with no findings.
- New search, source-first keyboard, and light/dark/auto Card browser tests:
  three passed on Chromium. The theme test also passed five consecutive focused
  runs after its asynchronous media-change wait was made explicit.
- Full docs browser collection: 18 passed on Chromium.
- Production-equivalent `docs_site assemble`: passed, with 76 root pages and no
  committed version snapshots mounted under `/v/`.
- Repository-wide gate: Rust format, Clippy, Rust tests, Ruff, mypy, pyright,
  client checks, validators, and the 93 percent coverage threshold passed. The
  gate remains red on 54 unrelated concurrent client-graph browser tests.
- Independent adversarial review: `MET`. It reproduced the risk of applying a
  dark scheme to existing light-only demos, which led to the Card-only opt-in;
  it also required iframe titles, a deterministic media-change wait, and a
  narrower FACT-004 evidence claim before accepting the pilot. A second
  newcomer-focused review required the tutorial's plain-language rewrite, a
  directly importable Card page, and two differently colored Cards in one
  parent render before returning `MET`.

The final validator passes against the reconciled 450-file fingerprint set.

## Provisional full-sweep estimate

The core pilot calibrates only a first-success journey. It must not be
multiplied blindly across every subsystem. A provisional planning range is:

| Work | Low | Likely | High | Confidence |
| --- | ---: | ---: | ---: | --- |
| Subsystem fact deep dives | 8 | 10 | 12 | Medium for count, low for non-core effort. |
| Review-sized authoring waves | 10 | 13 | 16 | Medium; assumes three to six related pages plus their projections per wave. |
| Unique material facts | 180 | 240 | 320 | Low until Stage 5 samples hosts, Events, security, and operations. |
| Runnable recipe families | 25 | 34 | 45 | Low; depends on the accepted product and support scope. |

Simple evergreen material should cost roughly 0.75 to 1.25 core-pilot units;
integration and API material 1.25 to 2 units; security, operations, and
migrations 2 to 4 units. Stage 5 must recalibrate after one representative
sample from each higher-risk bucket. Time estimates remain intentionally open
until the maintainer reports the active review cost of this slice.

## Gate and failure response

The pilot is ready for one coherent maintainer review. If the maintainer rejects the CSS
boundary, schema-required slot choice, source-first Examples projection, or
review size, keep the fact rows at `authored`, record the rejected decision,
and revise this pilot before Stage 4. Do not expand the content sweep while a
material pilot fact is disputed.
