# Stepper

**Status:** production implementation, public reference, examples, focused
browser evidence, and quality wiring are checked in. Manual visual and
assistive-technology review remains stabilization evidence.

## 1. Purpose and product bar

`CStepper` communicates progress through a finite ordered workflow. `CStep`
declares each labelled step. The family owns step status and optional direct
navigation, but it does not own wizard panels, application validation,
submission, or Previous/Next actions. Those remain ordinary composition.

The shortest progress-only job is:

```html
<c-CStepper label="Account setup" c-active="1">
  <c-CStep>Profile</c-CStep>
  <c-CStep>Security</c-CStep>
  <c-CStep>Review</c-CStep>
</c-CStepper>
```

Set `interactive` to make eligible step labels native Buttons. The active
index is zero based. Non-goals include a headless store, built-in form
validation, panel mounting, remote workflow orchestration, and a mobile-only
alternate component.

## 2. Prior art and complaints

| Product or standard | Version or review date | Surface inspected | Decision supported |
|---|---|---|---|
| Vuetify Stepper | current docs reviewed 2026-08-10, with v2 API used where current search was incomplete | linear/non-linear, editable, optional, error, horizontal/vertical, content | Retain familiar workflow states while separating application content from the indicator. |
| Material UI Stepper | current docs reviewed 2026-08-10 | zero-based `activeStep`, orientation, linear/non-linear, optional content and buttons | Adopt a zero-based active index and explicit interactive mode; leave optional/completion policy to the owner. |
| Chakra UI Steps | current docs reviewed 2026-08-10 | compound anatomy, controlled step, trigger, content and validation | Keep a small compound declaration API and permit external content/actions without copying the full store surface. |
| HTML and ARIA | current standards reviewed 2026-08-10 | ordered lists, navigation landmarks, `aria-current=step`, native Buttons | Use native list and Button semantics; no invented Stepper role or composite keyboard model. |

Vuetify remains the primary visual reference. Citry adopts orientation,
editable navigation, optional and error states, size and theme customization.
It omits a bundled content window and action footer because those make the
Stepper a second owner of application workflow and form state.

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| horizontal and vertical | direct API | `orientation` | Adopt. |
| editable/non-linear | direct API | `interactive`, `linear=False` | Adopt with native Buttons. |
| optional/error | direct API | `CStep(optional=True, error=True)` | Adopt as declared status metadata. |
| step content and actions | composition | content adjacent to `CStepper`, ordinary `CButton` | Do not duplicate application state. |
| alternate labels | CSS/variant | public parts and variables | Omit a structural mode; applications can style the stable parts. |
| rules/validation | composition | application callback and form controls | Omit policy from the visual progress component. |

## 3. Public composition and anatomy

```text
nav.cui-stepper
└─ ol.cui-stepper__list
   └─ li.cui-stepper__step × 2+
      ├─ button|span.cui-stepper__trigger
      │  ├─ span.cui-stepper__indicator
      │  └─ span.cui-stepper__copy
      │     ├─ span.cui-stepper__label
      │     └─ span.cui-stepper__description?
      └─ span.cui-stepper__separator? (decorative)
```

`CStepper` renders a named `<nav>` and `<ol>`. `CStep` is declaration-only and
must be a direct declaration of that Stepper. Two or more Steps are required.
The default Step slot supplies the visible label; `description` and `indicator`
are optional named slots. Declaration content is rendered only by the owning
Stepper and cannot contain nested interactive descendants.

## 4. Server inputs and client inputs

`CStepper`: `label: str`, `active: int = 0`, `interactive: bool = False`,
`linear: bool = True`, `disabled: bool = False`, `orientation:
"horizontal"|"vertical" = "horizontal"`, `variant: "plain"|"soft"|"outline"
= "plain"`, `size: "sm"|"md"|"lg" = "md"`, plus root `class_`, `style`, and
`attrs`. `interactive` is structural and server-only. All other configuration
except `label` has a matching optional client input. Client `active` is
controlled while supplied; `null` releases to the last effective index.

`CStep`: `disabled`, `optional`, and `error` Booleans plus `class_`, `style`,
and `attrs`. These declaration inputs are server-only. The owning Stepper
assigns the zero-based index.

Invalid client inputs report once per continuous invalid episode and fall
back to the current valid server or committed value.

## 5. State model

Each Step is exactly one of `complete`, `current`, or `upcoming`. A Step before
the active index is complete; the active index is current; later Steps are
upcoming. `error` and `optional` are independent declared metadata.

In interactive linear mode, complete and current Steps are eligible and
upcoming Steps are disabled. In non-linear mode every non-disabled Step is
eligible. A click on the current Step is a no-op. An uncontrolled eligible
click commits immediately; a controlled click only notifies until accepted.
Root disabledness dominates all Steps and a native disabled fieldset is
reflected through each Button's effective `:disabled` state.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
| `CStepper` | `default` | yes | one | `{}` | none; declarations only |
| `CStep` | `default` | yes | one | `index`, `state`, `is_current`, `is_disabled` | none |
| `CStep` | `description` | no | one | same | omitted |
| `CStep` | `indicator` | no | one | same | one-based ASCII step number, decorative |

## 7. Callbacks, native events, and methods

Client `onActiveChange(requestedIndex, detail)` fires for an eligible different
Step activation. Detail contains `previousActive`, `active`, `controlled`,
`step`, and `sourceEvent`. Native click listeners authored on a Step Button
remain available through `attrs`. There are no public imperative methods or
custom DOM events.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a labelled navigation landmark containing an ordered list. The
current trigger has `aria-current="step"`. Interactive Steps are ordinary
`<button type="button">` elements and therefore use native Tab, Shift+Tab,
Enter, and Space behavior. Static Steps are spans and never enter the Tab
order. Disabled Steps use native disabled Button behavior.

The label alone supplies the accessible name. Description is connected with
`aria-describedby`; the indicator and separator are decorative. There is no
roving focus or Arrow-key contract because Stepper is not an ARIA composite.

## 9. Native forms and validation

Stepper is not a form control and submits no value. Interactive step Buttons
always use `type="button"`, so they never submit an enclosing form. Application
panels may contain ordinary form controls outside the Stepper.

## 10. Styling and theme contract

Variants are `plain`, `soft`, and `outline`; sizes are `sm`, `md`, and `lg`.
Public parts are `stepper`, `list`, `step`, `trigger`, `indicator`, `copy`,
`label`, `description`, and `separator`.

Public variables: `--cui-stepper-gap`, `--cui-stepper-indicator-size`,
`--cui-stepper-trigger-gap`, `--cui-stepper-radius`,
`--cui-stepper-active-color`, `--cui-stepper-complete-color`,
`--cui-stepper-muted-color`, `--cui-stepper-background`,
`--cui-stepper-border-color`, and `--cui-stepper-focus-color`.

Public semantics and reflections are root `aria-label`, `data-orientation`, `data-linear`,
`data-interactive`, `data-disabled`, `data-variant`, `data-size`, and
`data-active`; Step `data-index`, `data-state`, `data-disabled`,
`data-optional`, and `data-error`.

## 11. Environmental behavior

All layout uses logical properties and supports RTL. Horizontal Steps can
wrap at narrow widths rather than create page overflow; vertical Steps use a
single column. Long labels/descriptions use `overflow-wrap:anywhere`.
Reduced-motion removes decorative transitions. Forced colors retains visible
indicators, focus rings, and separators. Print preserves list order and status
without depending on background color. The only library-visible strings are
the fallback ASCII step numbers; applications can replace them with the
indicator slot.

## 12. Overlay and layering behavior

The family never creates or controls an overlay.

## 13. Collections, async data, and identity

Step identity is its zero-based settled order. Adding, removing, or reordering
Steps therefore changes indices deliberately. A client active index outside
the current range is invalid. Async loading and workflow completion are
application concerns.

## 14. Server render, morph, and cleanup

Server output is a complete named ordered list with current status and native
buttons when interactive. Activation adds one delegated click listener and a
bounded native-fieldset observer. A retained rerender preserves an
uncontrolled committed index while the server `active` baseline is unchanged;
a changed baseline resets it. Cleanup removes listener, observer, scheduled
reconciliation, runtime marker, and private handoff data.

## 15. Security and content trust

Labels and descriptions use ordinary trusted Citry slots and default escaping.
No raw-HTML shortcut exists. Root and Step attrs reject owned roles, identity,
status, focus, visibility, child-replacement directives, and runtime markers.
Settled client validation fails closed when Step content adds an interactive
descendant inside the owned trigger.

## 16. Assets and performance

The family adds one CSS asset and one small client initializer. It uses one
root click listener and, only for interactive instances, one bounded observer
for effective fieldset disabledness. No icon, font, overlay, or network asset
is added.

## 17. Acceptance matrix

Checked-in focused tests cover declaration grammar, server state, exact native
anatomy, controlled and uncontrolled activation, linear/non-linear eligibility,
disabled/fieldset behavior, form safety, client configuration, invalid input
episodes, structure fail-close/recovery, RTL/narrow layout, public variables,
reduced motion, forced colors, print, axe, cleanup, exports, API projection,
docs previews, assets, scenarios, and wheel inclusion. Manual release evidence
still includes VoiceOver/Safari, NVDA/Firefox, JAWS/Chromium, touch, 400% zoom,
and visual design review.

## 18. Compatibility classification

`CStepper`, `CStep`, their inputs, slot data, callback detail, parts, public
attributes, and CSS variables are stable. Initialization markers, private
collector components, classes, runtime data, and observer details are private.

## 19. Public documentation contract

The guide includes at-a-glance progress, interactive linear navigation,
non-linear navigation, vertical/optional/error states, controlled state,
disabled behavior, and customization. Examples compose workflow content and
Next/Back Buttons outside Stepper so the ownership boundary is visible.

## 20. Open decisions and deferred work

Built-in panels, validation, completion stores, a compact mobile progress
variant, async workflow orchestration, and locale-aware fallback numbering are
deferred. They require separate evidence and are not implied by this family.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
