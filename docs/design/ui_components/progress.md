# Citry UI Progress specification

**Status (2026-08-08): production implementation, structured API, nine public
examples, quality route, scaling profile, wheel boundary, and focused server
and Chromium evidence are complete. Human visual and assistive-technology
release review remains.**

## 1. Purpose and product bar

`CProgress` communicates completion of an ongoing task through the native
`progress` element. A number represents determinate progress from zero to a
positive maximum; `None` represents ongoing work with unknown duration.

Shortest jobs:

```citry-html
<c-CProgress label="Importing mineral records" c-value="42" />
<c-CProgress label="Contacting archive" />
```

Progress is not a scalar gauge, capacity meter, slider, stepper, countdown,
navigation loader, Spinner, or general animation surface. Use `meter` for a
measurement that is not task completion and `CSpinner` for a compact unknown
wait without a linear progress track.

## 2. Prior art and complaints

| Source | Version or review date | Surface inspected | Decision |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | Input client ownership, Alert status, theme, component policy | Reuse server fallback/client override, one-diagnostic invalid episodes, public data reflection, exact strings, and inherited variables. |
| Vuetify | 4.0.7 reviewed 2026-08-08 | `VProgressLinear` value, buffer, indeterminate, reverse, rounded, striped, stream, slots, color, positioning | Adopt determinate/indeterminate, concise size/color treatment, rounding, and client value. Defer buffer, stream, striping, absolute positioning, and embedded label slots. |
| Mantine | 9.2.2 reviewed 2026-08-08 | Progress, compound sections, vertical, stripes, animation, transitions, labels, accessibility | Keep one task/value and native semantics. Defer segmented, vertical, tooltips, and transition-duration APIs. |
| Material UI | 9.0.1 reviewed 2026-08-08 | linear determinate/indeterminate/query/buffer, value text, transition limits, accessibility | Adopt explicit accessible name and custom value text. Avoid fixed smoothing that lags high-frequency updates. |
| Chakra UI | 3.35 reviewed 2026-08-08 | Progress root/track/range/label/valueText, value/max, variants, shape, stripes | Adopt size and shape vocabulary. Prefer native progress over a multipart ARIA recreation. |
| HTML Standard and MDN | reviewed 2026-08-08 | `progress`, value/max, indeterminate removal, labels, region relationship | Use native `progress`, require positive max and value within range, omit `value` for indeterminate, prohibit `min` and authored role. |

Vuetify disposition receives the strongest single-library weight. Citry can
achieve colors, arbitrary thickness, radius, direction, and positioning through
public CSS/class/style. Buffer and stream represent two-value media/network
models and remain deferred until a real application proves the contract.

## 3. Public composition and anatomy

One native root, no wrapper:

```html
<progress
  data-citry-ui-part="progress"
  data-state="determinate"
  data-intent="primary"
  data-size="md"
  data-shape="rounded"
  aria-label="Importing mineral records"
  value="42"
  max="100"
>Importing mineral records: 42 of 100</progress>
```

Indeterminate output omits `value`. Fallback child text supports legacy
browsers but is not the accessible name. `label` owns `aria-label`.

## 4. Server inputs and client inputs

Aliases:

```python
CProgressIntent = Literal["neutral", "primary", "success", "warn", "danger"]
CProgressSize = Literal["sm", "md", "lg"]
CProgressShape = Literal["square", "rounded", "pill"]
```

Server inputs:

| Input | Type | Default | Effect |
|---|---|---:|---|
| `label` | `str` | required | Nonempty accessible name and fallback text. |
| `value` | `float | int | None` | `None` | Current completion; `None` is indeterminate. |
| `max` | `float | int` | `100` | Positive task maximum. |
| `value_text` | `str | None` | `None` | Optional `aria-valuetext` for non-percentage units. |
| `intent` | `CProgressIntent` | `"primary"` | Visual range palette; surrounding text carries meaning. |
| `size` | `CProgressSize` | `"md"` | Track thickness. |
| `shape` | `CProgressShape` | `"rounded"` | Track and range radius. |
| `class_`, `style`, `attrs` | standard root inputs | `None` | Root customization and nonconflicting trusted attributes. |

Client inputs are passed through `$c-props="{...}"`:

| Input | Values | Ownership |
|---|---|---|
| `value` | finite number in `0..max`, or `null` | Supplied value controls the native `value` attribute; `null` removes it. Omission uses server fallback. |
| `label` | nonempty string | Supplied text controls `aria-label`; omission uses server label. |
| `valueText` | string or `null` | Supplied string controls `aria-valuetext`; null removes it; omission uses server fallback. |
| `intent`, `size`, `shape` | same aliases as server | Supplied valid value controls its public reflection; omission uses server fallback. |

Invalid client input reports once per continuous invalid episode and uses the
server fallback. A valid value or omission ends the episode. `max` remains
server-owned because changing the task unit/range is structural and normally
arrives with server data.

## 5. State model

Native state is determinate when `value` is present and indeterminate when it
is absent. The root reflects `data-state`. Client activation starts from the
server state, then applies supplied props. Repeated equal values do not assign.
Programmatic prop changes do not emit events.

Progress completion does not automatically change intent, announce a message,
or remove `aria-busy` from another region. The application owns those related
state transitions atomically.

## 6. Slots and slot data

No slots. Use visible text next to Progress and connect it with the required
`label` or external relationships. The native element's child text is only a
fallback, not a visual label surface in modern browsers.

## 7. Callbacks, native events, and methods

No component callbacks, methods, or authored events. Progress is output, not a
control. Trusted root native listeners remain possible but are not a value
change API; browser prop updates are application-owned.

## 8. Semantics, keyboard, focus, and assistive technology

The native implicit role is `progressbar`; authored `role` is prohibited. The
element is unfocusable and has no keyboard behavior. `label` is always
required. `value_text` is recommended when units are not naturally understood
as a percentage. Do not redundantly author `aria-valuenow/min/max`; native
value/max own them.

When Progress describes a busy region, the application sets `aria-busy=true`
on that region and points its `aria-describedby` to Progress, then clears busy
state when work finishes. Progress itself is not a live region.

## 9. Native forms and validation

`progress` is labelable but not a successful form control, constraint
participant, or editable input. Native `<label for>` may reference an `id`
supplied through `attrs`, while `label` still ensures an accessible name when
the visible label is not structurally associated.

## 10. Styling and theme contract

Public variables:

| Variable | Purpose |
|---|---|
| `--cui-progress-track-color` | unfilled track |
| `--cui-progress-range-color` | completed range and indeterminate accent |
| `--cui-progress-height` | track thickness |
| `--cui-progress-radius` | track/range radius |

Stable selector: `[data-citry-ui-part="progress"]`. Browser-specific native
pseudo-elements are implementation details, not public selectors. Intent sets
the range fallback; size sets height; shape sets radius. Public variables win
over all presets.

## 11. Environmental behavior

Native direction determines fill direction. Logical consumer composition works
in LTR/RTL. Light/dark values use system-aware fallbacks. Forced colors uses
system colors and retains native progress recognition. Print freezes
indeterminate animation and keeps a visible track/range. Reduced motion removes
continuous indeterminate motion while retaining a striped unknown-state cue.

## 12. Overlay and layering behavior

No overlay, position, z-index, transform, portal, clipping, or containing-block
ownership. Toolbar/navigation loaders use ordinary CSS positioning around the
native root.

## 13. Collections, async data, and identity

One Progress represents one task. Segments, multiple ranges, buffers, stacked
storage categories, and aggregate job lists are separate composition/data
models. Async timing and cancellation stay with the application.

## 14. Server render, morph, and cleanup

Server HTML is complete. The client initializer synchronizes optional props,
sets one initialized marker, and removes it on cleanup. It owns no timers,
observers, global listeners, or async work. Correlated rerenders reinitialize
from new server data and latest props.

## 15. Security and content trust

Direct labels/value text are converted to exact plain strings before escaping.
Numbers reject Booleans, NaN, infinities, nonpositive max, and values outside
`0..max`. `attrs` is copied and rejects owned native/ARIA/configuration fields,
dynamic aliases, runtime namespaces, structural/child-replacing directives,
and whole-object binding. Nonconflicting metadata, `id`, `aria-describedby`,
targeted classes/styles, and listeners remain allowed.

## 16. Assets and performance

One CSS and one small component behavior asset; no icons, fonts, listeners,
observers, or timers. Each instance renders one native element. Diagnostic
scaling records 1, 10, 100, 500, and 1,000 instances without a timing gate.

## 17. Acceptance matrix

Focused evidence must cover server/client determinate and indeterminate states;
zero, fractions, custom max, custom value text; every invalid numeric/string/
enum path and diagnostic episode; native role/name/value/max/position; omitted
value attribute; repeated equal updates; exact public reflections; every
intent/size/shape; variable and selector overrides; LTR/RTL; nested schemes;
reduced motion; forced colors; print; cleanup/reinit; docs/previews; quality;
scaling; registration; and wheel boundaries.

Manual release evidence covers real screen-reader value phrasing, indeterminate
recognition, animation comfort, Safari/Firefox native pseudo styling, and
visual contrast in supported schemes.

## 18. Compatibility classification

Stable: class, server/client inputs, aliases, native root semantics, variables,
selector, reflected attributes, diagnostics, and initialized behavior.
Evolvable: fallback colors, thickness lengths, indeterminate visual pattern.
Private: native pseudo selectors, `.cui-*`, `--_cui-*`, and JS helpers.

## 19. Public documentation contract

The page uses an undersea research-expedition theme. Planned previews: at a
glance, determinate values, indeterminate work, custom maximum/value text,
intents, sizes/shapes, client-controlled progress, busy-region composition,
and theme customization. Examples show rendered output early and keep controls
visually separate from output.

## 20. Open decisions and deferred work

Implementation blockers: none. Deferred: buffer/stream, segments, vertical
orientation, circular progress, stripes on determinate values, transition
duration, query/reverse modes, automatic percentage labels, automatic busy
region mutation, delayed appearance, and navigation-service integration.

Falsifier for native ownership: if focused cross-browser evidence shows the
native `progress` element cannot uphold the documented styling or dynamic
indeterminate contract without inaccessible replacement markup, stop and
design a standards-compliant ARIA root rather than shipping browser-divergent
semantics.
