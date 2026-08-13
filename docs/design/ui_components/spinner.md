# Citry UI Spinner specification

**Status (2026-08-08): production implementation, structured API, nine public
examples, quality route, scaling profile, wheel boundary, and focused server
and Chromium evidence are complete. Human visual and assistive-technology
release review remains.**

## 1. Purpose and product bar

`CSpinner` is a compact visual cue for active work whose duration is unknown.
It renders one labelled, indeterminate `progressbar` and works before client
JavaScript loads.

```citry-html
<c-CSpinner label="Loading star catalog" />
```

Use `CProgress` when a task has a meaningful linear track or known completion.
Spinner is not a loading overlay, delayed-appearance controller, live
announcer, Button loading state, or determinate circular progress meter.

## 2. Prior art and complaints

| Source | Version or review date | Surface inspected | Decision |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | Progress, Button loading, Alert announcements, theme and attrs policy | Reuse required naming, intent/size vocabulary, client fallback, reduced-motion, and trusted-root rules. |
| Vuetify | 4.0.7 and current public docs reviewed 2026-08-08 | circular progress size, width, color, indeterminate, rotate, determinate value, centered slot | Adopt concise size and color treatment. Keep value and centered content in Progress or application composition. |
| Material UI | 9.0.1 reviewed 2026-08-08 | CircularProgress indeterminate/determinate, size, thickness, track, color, delay and CPU limitations | Adopt CSS-first indeterminate rendering and explicit name. Avoid determinate value, built-in delay, and JS animation. |
| Mantine | 9.2.2 reviewed 2026-08-08 | Loader oval/bars/dots, CSS animation, size, color, custom loaders and overlay composition | Keep one stable ring visual. Leave alternate and custom loader registries to user CSS or later evidence. |
| Chakra UI | 3.35 reviewed 2026-08-08 | Spinner sizes, color, track color, speed, thickness, label and overlay composition | Expose size, color, track, thickness, and duration through concise inputs plus public variables. Keep overlay ownership separate. |

Common shortcomings considered:

- unlabeled visual spinners provide no task context to assistive technology;
- infinite motion without a reduced-motion state excludes motion-sensitive users;
- a Spinner shown immediately for very short work can flash distractingly;
- putting overlay positioning or task lifecycle into the glyph creates two
  unrelated ownership systems;
- multiple built-in animation shapes enlarge API and QA surface without adding
  semantic capability.

## 3. Public composition and anatomy

One `span` is the component root, public selector, attrs destination, visible
ring, and semantic owner. It carries `role="progressbar"` without value ARIA,
because Spinner is always indeterminate. There are no internal wrappers or
slots.

The application owns presence, delayed appearance, surrounding text,
`aria-busy` on described regions, overlays, task cancellation, and completion.

## 4. Server inputs and client inputs

Server inputs:

| Input | Type | Default | Contract |
|---|---|---|---|
| `label` | `str` | required | Nonempty accessible task name. |
| `intent` | `neutral`, `primary`, `success`, `warn`, `danger` | `primary` | Visual ring palette. Color is not meaning. |
| `size` | `sm`, `md`, `lg` | `md` | Ring diameter and default thickness. |
| `class_` | class value | `None` | Root classes. |
| `style` | style value | `None` | Root inline styles. |
| `attrs` | mapping | `None` | Copied trusted, nonconflicting root attributes. |

Client `$c-props` support `label`, `intent`, and `size`. Valid values override
the server fallback. Omission restores it. Invalid values log once per
continuous invalid episode and use the server fallback.

No Boolean `loading` input exists. Presence of Spinner already means work is
active, so application conditionals own whether it renders or is visible.

## 5. State model

Spinner has one semantic state: indeterminate active work. Its presence is the
state signal. `intent` and `size` are presentation, not task state. The
application owns pending, success, failure, cancellation, and removal.

## 6. Slots and slot data

None. Visible explanatory text belongs next to Spinner. Centered values and
custom glyph content are separate composition jobs.

## 7. Callbacks, native events, and methods

No component-authored events, methods, State, timers, or async work. Native
metadata listeners passed through `attrs` do not acquire Spinner behavior.

## 8. Semantics, keyboard, focus, and assistive technology

The root has `role="progressbar"`, required `aria-label`, and no
`aria-valuenow`, `aria-valuemin`, `aria-valuemax`, or `aria-valuetext`. It is
not focusable and has no keyboard behavior.

Spinner is not a live region. When it describes a region, the application sets
`aria-busy="true"` on that region and points `aria-describedby` to Spinner or
nearby status text. The application clears busy state when work completes.
For frequently updated status phrasing, use a persistent, separately designed
live region rather than repeatedly replacing Spinner.

## 9. Native forms and validation

Spinner is not a successful control, constraint participant, submitter, label
owner, or reset participant. It may appear beside controls without changing
native form behavior.

## 10. Styling and theme contract

Public variables:

| Variable | Purpose |
|---|---|
| `--cui-spinner-color` | active ring arc |
| `--cui-spinner-track-color` | quiet remainder of the ring |
| `--cui-spinner-size` | diameter |
| `--cui-spinner-thickness` | ring border width |
| `--cui-spinner-duration` | one rotation duration |

Stable selector: `[data-citry-ui-part="spinner"]`. Intent sets the color
fallback. Size sets diameter and thickness fallbacks. Public variables win
over presets. Consumer `class_` and unlayered CSS remain valid escape paths.

## 11. Environmental behavior

Default motion is a linear CSS rotation with no JavaScript. Reduced motion and
print stop rotation and show a static two-edge arc. Forced colors uses system
foreground and track colors. Light/dark fallbacks respond to the effective
color scheme. Direction does not reverse activity or encode progress.

## 12. Overlay and layering behavior

Spinner owns no position, inset, z-index, portal, backdrop, clipping,
containing block, or pointer interception. Centering over content uses an
application-owned container or a future LoadingOverlay family.

## 13. Collections, async data, and identity

Each Spinner represents one active task and has no collection identity or
async ownership. Common composition jobs:

- Inline activity pairs Spinner with concise visible text in `CGroup`.
- Region loading places Spinner near content while the owner controls
  `aria-busy` and presence.
- Button loading uses `CButton(loading=True)`, which owns disabledness,
  content stability, and its internal indicator.
- Known progress uses `CProgress`.
- Full-page startup, route transitions, delayed appearance, and minimum-visible
  duration stay with application infrastructure.

## 14. Server render, morph, and cleanup

Server output is complete and animated by CSS. Client initialization only
synchronizes optional props, sets one initialized marker, and removes it on
cleanup. It owns no listeners, observers, timers, animation frames, or global
state. Correlated rerenders start from new server fallbacks and latest props.

## 15. Security and content trust

Direct labels and choices are converted to exact plain strings before
escaping. `attrs` is copied and rejects role, name/value ARIA, focus/editing
ownership, public data fields, runtime namespaces, structural and
child-replacing directives, and whole-object binding. Nonconflicting metadata,
description relationships, targeted classes/styles, `hidden`, `x-show`, and
listeners remain allowed.

Stable root attributes:

- `role="progressbar"`;
- `aria-label` with the effective label;
- `data-intent` with the effective palette;
- `data-size` with the effective size;
- `data-citry-ui-part="spinner"`.

The initialization marker is private runtime evidence.

## 16. Assets and performance

One CSS and one small optional-prop behavior asset; one DOM element per
instance; no SVG, icon catalog, listeners, observers, timers, or JavaScript
animation. Diagnostic scaling records 1, 10, 100, 500, and 1,000 instances
without a timing gate.

## 17. Acceptance matrix

Focused evidence covers exact server schema; required label; all choices and
invalid paths; trust boundaries; native role/name/value absence and
nonfocusability; client override/omission/invalid episodes; every intent and
size; public variable and selector overrides; inline composition; narrow
layout; LTR/RTL; nested schemes; reduced motion; forced colors; print;
cleanup; docs/previews; quality route; scaling; registration; and wheel
boundaries.

Manual release review covers real screen-reader indeterminate phrasing,
animation comfort, visual contrast, inline baseline alignment, and the
supported browser matrix.

## 18. Compatibility classification

Stable: component name, server/client inputs, aliases, progressbar semantics,
public variables, selector, reflected attributes, invalid diagnostics, and
cleanup marker behavior. Evolvable: exact colors, size lengths, thickness, and
rotation duration. Private: `.cui-*`, `--_cui-*`, keyframe name, and JS helpers.

## 19. Public documentation contract

The page uses one astronomy-observatory theme. Nine previews cover at a
glance, basic use, intents, sizes, inline activity, browser-controlled
presentation, busy-region composition, delayed-appearance guidance, and CSS
customization. Rendered output appears early and controls remain visually
separate from it.

## 20. Open decisions and deferred work

Implementation blockers: none. Deferred: determinate circular progress,
alternate dots/bars shapes, custom loader registry, automatic delayed
appearance, minimum-visible duration, overlay ownership, live announcement,
centered content, custom speed input, and loading service integration.

Falsifier for the compact boundary: if real application use repeatedly needs a
second animation family that cannot be expressed through public variables,
research a small `variant` vocabulary rather than adding arbitrary child
rendering to Spinner.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
