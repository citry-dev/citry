# Phase 7 Citry UI production-slice report

**Status: implementation slice complete; release-quality evidence in
progress. Snapshot updated: 2026-08-08.** Phase 7 advances one public architecture:
styled `LibraryComponent` definitions in the separate `citry-ui` distribution,
registered explicitly into each `Citry` instance. Current source development
targets `citry>=0.3.2,<0.4.0` with `citry_core 1.5.0`; release-artifact
qualification waits for those versions to publish.

This is a cumulative implementation report, not a release declaration. The
remaining quality profiles and artifact matrix are listed in section 5.

## 1. Implemented production slice

The public catalog contains eleven definitions across seven specified
families:

| Family | Main production evidence |
|---|---|
| [`Button`](../ui_components/button.md) | Native action, submit and reset; variants, intents, sizes, slots, loading and disabled guards; reactive client overrides; light/dark tokens and parts. |
| [`Field and Input`](../ui_components/field-input.md) | Stable label, description, error and control relationships; native constraints; inherited Form state; controlled and uncontrolled values; edit and focus preservation. |
| [`Form`](../ui_components/form.md) | Native form and fieldset; dynamic control registration; aggregate validity; reset and duplicate-submit policy; inherited client context and cleanup. |
| [`Tabs`](../ui_components/tabs.md) | Automatic/manual activation; pointer and complete keyboard matrix; disabled, vertical, RTL and loop behavior; controlled props; nested roots; keyed reorder, removal and focus recovery. |
| [`Dialog`](../ui_components/dialog.md) | Native modal top layer; initial and contained focus; Escape, outside and explicit close; controlled requests; nested locks; focus restoration; theme continuity and cleanup. |
| [`Combobox`](../ui_components/combobox.md) | Local and remote single select; ARIA keyboard model; canonical form value; cancellation and stale-result rejection; loading, empty and error states; callback and cleanup contracts. |
| [`Table`](../ui_components/table.md) | Native semantic table; keyed rows and columns; scoped composition; loading, empty and error states; overflow and sticky header; Events reorder and edit identity; zero component JavaScript. |

Headless APIs remain parked. Specialist data grids, charts, rich editors, and
maps remain companion-product candidates rather than being approximated in
this slice.

## 2. Cross-family application evidence

The [`repeatable contact workflow`](../ui_components/repeatable-form-workflow.md)
combines Form, Field, Input, Combobox, Button, and Citry Events. It proves
stable keyed add, remove and reorder; native nested form names; aggregate
registration and validation; browser-owned edit preservation; deterministic
post-mutation focus; native submission; and cleanup.

The [`representative compositions`](phase7-compositions.md) provide a
public-site access form and an application delivery dashboard. The dashboard
combines Button, Dialog, Tabs, and Table. Orbit and Ledger brand adaptations
use only consumer scope styles, `color-scheme`, system canvas colors,
documented `--cui-*` variables, and public parts. Tests reject package-class,
private marker, private variable, and `!important` dependencies.

These compositions expose one expected future gap: the current slice has no
layout, card, typography, navigation, or feedback family. Phase 8 should
consider those product surfaces rather than turning application layout CSS
into private component coupling.

## 3. Automated evidence

| Evidence | Result at snapshot |
|---|---|
| Focused Citry UI non-browser suite | 130 passed, including registration, component families, Storybook spike compatibility, and frozen asset budgets |
| CButton browser matrix | 21 passed across Chromium, Firefox, and WebKit |
| CForm/CField/CInput browser matrix | 21 passed across Chromium, Firefox, and WebKit |
| CDialog browser matrix | 18 passed across the three engines |
| CCombobox browser matrix | 21 passed across the three engines |
| CTable browser matrix | 12 passed across the three engines |
| CTabs browser matrix | 60 passed across the three engines |
| Repeatable workflow | 3 passed across the three engines |
| Representative compositions | 12 passed across the three engines, including six complete-page axe scans and desktop plus narrow interaction samples |
| Complete Citry UI browser matrix | 168 passed across Chromium, Firefox, and WebKit |
| Core lifecycle fixes found by the slice | physical ancestor initialization before slot descendants; focus restoration for an exact keyed input preserved by Events morph |
| JavaScript source checks after core Events change | Citry client typecheck, lint, and 10 JavaScript tests pass; generated bundle and playground artifacts are current |
| Repository checker | Lock, Rust, formatting, mypy, Pyright, JavaScript, pytest coverage, and validators pass; root Ruff reports four pre-existing unused arguments in `benchmarks/client_scenario.py` |

The first aggregate run found the generated playground Events runtime stale and
the core client bundle 412 bytes over its guard after focus recovery was added.
Both in-scope findings were corrected: the playground was rebuilt and the
focus snapshot was simplified without changing its node, value, caret, or
focus behavior. The bundle budget, generated-source canary, focused morph
cases, and all scoped gates now pass. The benchmark Ruff findings are outside
this work and remain unchanged.

## 4. Asset and performance budgets

Source-form assets are compressed independently for measurement. Route
assembly delivers each class asset once.

| Component | JavaScript raw / gzip / Brotli | CSS raw / gzip / Brotli |
|---|---:|---:|
| CButton | 4,898 / 1,197 / 984 B | 8,450 / 1,430 / 1,208 B |
| CCombobox | 28,870 / 5,300 / 4,603 B | 7,158 / 1,339 / 1,121 B |
| CDialog | 13,648 / 2,893 / 2,490 B | 4,686 / 1,062 / 902 B |
| CField | 4,488 / 1,189 / 1,003 B | 2,325 / 597 / 497 B |
| CInput | 7,699 / 1,688 / 1,420 B | 4,307 / 823 / 708 B |
| CForm | 7,756 / 1,837 / 1,564 B | 953 / 319 / 270 B |
| CTable | none | 6,707 / 1,157 / 979 B |
| CTabs | 17,739 / 3,550 / 3,082 B | 6,370 / 1,244 / 1,037 B |
| Complete public catalog | 85,104 / 12,982 / 10,805 B | 40,963 / 5,152 / 4,458 B |

The complete catalog is below the 45 KiB Brotli JavaScript and 30 KiB Brotli
CSS limits. The Button, Field, Input, and Table route is 2,354 B Brotli
JavaScript and 2,591 B Brotli CSS, below its 8 and 12 KiB limits. Automated
tests freeze both gates.

The Button idle-work budget was revised after reactive `disabled` and
`loading` props became part of the production contract. One initializer is
allowed, but it retains no observer, timer, document/window listener, or global
entry while inactive. Table remains script-free. Thirty alternating local Tabs
selections stay below 50 ms p95 in the desktop test profile and below 100 ms in
the narrow viewport profile across the browser matrix. A pinned mobile device
and CPU profile remains release evidence.

## 5. Remaining Phase 7 release-quality work

No additional required component family or publishing architecture remains in
Phase 7. The actionable repository work is specified as
[`Phase 7.5`](../ui_library_plan.md#phase-75-repository-release-qualification).
The open work is:

- axe coverage for every frozen component state, not only the representative
  complete page;
- reviewed screenshots for light, dark, forced-colors, reduced-motion, RTL,
  long-label, narrow, zoom, error, loading, disabled, and controlled states;
- Nu HTML and Lighthouse runs against standalone complete pages;
- actual Bootstrap and Tailwind coexistence fixtures;
- pinned desktop and mobile interaction, initialization, and retained-resource
  profiles;
- manual keyboard, NVDA with Firefox or Chrome, and VoiceOver with Safari task
  scripts, plus real mobile and Safari checks;
- polished docs live examples beyond the existing Tabs example;
- Django and FastAPI host smoke tests for render, assets, forms, and Events;
- wheel contents, offline installation, uninstall, and released-artifact
  compatibility across the declared Citry range; and
- independent design review of the representative visual hierarchy and both
  brand adaptations.

Automated axe and Lighthouse scores are regression signals, not accessibility
conformance claims. Manual interaction and assistive-technology evidence cannot
be replaced by a passing scanner.

## 6. Architecture result and Phase 8 handoff

No architecture falsifier fired. Direct styled `LibraryComponent` definitions
express native forms, compound context, top-layer overlays, remote async state,
keyed collections, server morphs, cleanup, stable styling hooks, template tags,
and imported Python composition without a package-owned registration facade or
second client framework.

Phase 8 should freeze the v1 inventory, global token and provider direction,
compatibility and deprecation policy, host matrix, documentation support, and
release roadmap after the remaining release-quality profiles are complete.
Localization remains a separate research project after the shipped families'
user-visible strings and formatting requirements are inventoried. Storybook
remains optional extension work in [`../extensions_storybook.md`](../extensions_storybook.md).
