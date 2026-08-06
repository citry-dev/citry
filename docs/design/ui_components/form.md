# Citry UI Form specification

**Status (2026-08-06): production contract implemented; automated repository
evidence passes; human visual, content, assistive-technology, and real-device
review remains.** `CForm` is a
styled native Form boundary. It coordinates inherited disabled and read-only
configuration, exposes a controlled submitting guard, and preserves the
browser's submission, reset, validation, and `FormData` contracts.

## 1. Purpose and product bar

`CForm` renders one native `<form>` and one stable internal `<fieldset>`. It makes
common native Form attributes concise, passes reactive disabled and read-only
configuration to supporting Citry UI controls, and reflects its own submitting
guard. It does not replace the browser with a second form-state or validation
engine.

Production-complete means:

- GET, POST, `method=dialog`, reset, Enter submission, multiple submitters,
  per-submitter overrides, constraint validation, and `FormData` remain native;
- the server render works without JavaScript;
- reactive disabled and read-only values have matching DOM, behavior, and
  descendant configuration; submitting has matching Form behavior and ARIA;
- an uncanceled reset clears Form-owned attempted-validation presentation only
  after native controls reset;
- ordinary native controls, external `form=id` controls, and third-party
  controls retain their browser-defined behavior; and
- Citry Events may handle the native submit event without becoming a required
  transport.

Common jobs are first-class:

| Job | Contract |
|---|---|
| Submit to a URL | set `action` and `method`; use native named controls |
| Submit through browser code or Citry Events | handle native `@submit`; call `preventDefault()` when the application owns transport |
| Upload files | set `method="post"` and `enctype="multipart/form-data"` |
| Open a target or close a Dialog | use native `target` or `method="dialog"` |
| Disable an editable region | set `disabled`; the internal fieldset disables physical descendant controls |
| Supply a read-only default | set `readonly`; supporting Citry controls inherit it unless configured locally |
| Block a duplicate submission | set reactive `submitting` after the first accepted submit begins |
| Use native validation | put constraints on controls and listen to native `invalid`, `input`, `change`, or `submit` |
| Show server errors | render Field error content; application code owns persistence and clearing |
| Reset values | use a native reset Button or `form.reset()`; canceled reset changes nothing |
| Add, remove, or reorder fields | retain stable component keys; the browser's live `form.elements` and `FormData` define current membership and order |
| Associate an external control | give Form an `id` and the control a matching native `form` attribute |

Template use:

```citry-html
<c-CForm
  action="/observations"
  method="post"
  @submit="saveObservation($event)"
>
  ...
</c-CForm>
```

Python composition:

```python
from citry_ui import CForm

observation_form = CForm(
    action="/observations",
    method="post",
    slots={"default": fields},
)
```

`CForm` is not a schema, rules, dirty/touched, request, localization, error-map,
or nested-object serialization library.

## 2. Prior art and complaints

The family was re-audited from its runtime, render and browser tests, quality
scenario, repeatable-Form workflow, structured reference, public guide, and
composed consumers before the external comparison. Existing behavior remained
provisional wherever those artifacts disagreed.

### Source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI prototype | 2026-08-06 | `cform.py`, Field/Input and repeatable-Form browser tests, `form.states`, `api.md`, and `api.yml` | Keep the native root, fieldset, inherited state, submitting guard, native events, and token/part model. Remove the incomplete aggregate-validity registry and repair canceled reset and first-legend behavior. |
| HTML Living Standard | reviewed 2026-08-06 | [Form element](https://html.spec.whatwg.org/multipage/forms.html#the-form-element), [fieldset](https://html.spec.whatwg.org/multipage/form-elements.html#the-fieldset-element), [form ownership](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#association-of-controls-and-forms), [submission](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-algorithm), and [reset](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#resetting-a-form) | Native ownership, successful controls, live `elements`, submitters, cancelable reset, constraint validation, external controls, and first-legend disabled exemption. |
| Vuetify | 4.1.7 source reviewed 2026-08-06 | [`VForm.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VForm/VForm.tsx) and [form composable](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/composables/form.ts) | Confirm disabled/read-only context, dynamic child registration, validation breadth, reset APIs, slot data, and submit coordination. Reject forced `novalidate`, custom rules as Form truth, mutated promise-like submit events, intercepted reset, and `form.submit()` after async validation. |
| React Aria | current docs reviewed 2026-08-06 | [Form](https://react-aria.adobe.com/Form) and [Forms guide](https://react-aria.adobe.com/forms) | Preserve native submission, direct native Form attributes, native validation, server-error composition, and first-invalid focus. Defer an ARIA-only validation mode and Form-level server-error map. |
| Quasar | current docs reviewed 2026-08-06 | [QForm](https://quasar.dev/vue-components/form/) and [QInput](https://quasar.dev/vue-components/input/) | Confirm native action/method/enctype/target jobs and explicit child communication. Avoid rule registration, imperative validation, and model-reset coupling. |
| PrimeVue | 4.5.5 docs reviewed 2026-08-06 | [Forms](https://primevue.org/forms) | Treat resolvers, initial-value stores, validation timing, field state, and schema integration as a separate form-management product rather than silently embedding them in `CForm`. |
| Web Awesome | current docs reviewed 2026-08-06 | [Form controls](https://webawesome.com/docs/form-controls) | Preserve standard `FormData`, reset, and constraint behavior for custom controls. Citry can use native elements directly instead of a form-associated custom-element bridge. |
| Bootstrap | 5.3 docs reviewed 2026-08-06 | [Validation](https://getbootstrap.com/docs/5.3/forms/validation/) | Avoid treating styling hooks as accessible validation by themselves; browser and application behavior remain required. |

Common shortcomings informed the contract:

- Rules engines often disagree with native constraints, third-party controls,
  external controls, reset, autofill, or server errors.
- Registry validity can say valid while native submission is blocked by a
  control the registry does not own.
- Dynamic fields can remain registered after removal or appear in stale order.
- Controlled state can fight browser editing, reset, autofill, and password
  managers.
- Custom validation feedback can lose native focus and announcements.
- Intercepting native submit and later calling `form.submit()` bypasses a new
  submit event, native validation, and submitter-specific behavior.
- Reset wrappers commonly clear presentation even when another listener
  canceled reset.

Vuetify receives roughly 30% of the comparative decision weight. Every
relevant VForm surface has an explicit disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `disabled` | native group disabling plus Citry context | `disabled` | adopt |
| `readonly` | Citry context for supporting controls | `readonly` | adopt |
| `fastFail` | browser stops submission and focuses according to native constraint validation | native constraints | omit custom rules behavior |
| `modelValue` / `isValid` | browser owns complete Form validity | `checkValidity()`, `reportValidity()`, native events | reject a partial registry mirror |
| `validateOn` | fields and applications choose native or application validation timing | control inputs and native events | omit |
| `validate()` | browser validation method | `checkValidity()` or `reportValidity()` | use native method |
| `reset()` | browser reset method | `reset()` | use native method |
| `resetValidation()` | application-owned error state and Form attempted marker | native reset plus application state | omit method |
| `errors`, `items`, `isValidating` slot data | consumer state or future form-management extension | ordinary slot composition | omit |
| forced `novalidate` | optional native validation suppression | `novalidate` | reject forced behavior |
| promise-like submit event | native event plus application-owned async work | native `submit` | reject mutation |
| intercepted reset | cancelable native reset | native `reset` | reject replacement |
| class and style | direct structured root inputs | `class_`, `style` | adopt |

Capability parity does not require prop parity. Form-level schemas, server-error
maps, async rules, and dirty/touched stores remain viable companion extensions.

## 3. Public composition and anatomy

| Component | Semantic root | Attribute destination | Required relationship |
|---|---|---|---|
| `CForm` | native `<form>` | direct native inputs and `attrs` merge onto the Form | cannot be nested in another `CForm`; native nested forms remain invalid consumer markup |

The Form contains one stable `<fieldset>` around its required default slot. A
private empty first `<legend hidden aria-hidden="true">` is the fieldset's first
element child. It reserves HTML's disabled-fieldset exemption without entering
layout or the accessibility tree, so consumer controls cannot accidentally
remain enabled by becoming descendants of the first legend. Grouped controls
use their own nested `<fieldset><legend>...</legend>...</fieldset>` inside the
default slot. A direct consumer legend under `CForm` is invalid fieldset
structure and unsupported. Citry cannot diagnose it because slot markup is
opaque to the component.

The `form` and `fieldset` parts are public. The reserved legend and behavior
markers are private. No FormSection, FormActions, or FormSummary component is
needed: headings, sections, summaries, and action rows are ordinary content.

`class_` and `style` are direct root inputs and accept Citry's structured
values. `attrs` accepts less-common native Form, ARIA, `data-*`, and Alpine
attributes. It cannot replace component-owned identity, configuration,
behavior markers, or public part attributes.

Direct native inputs own their corresponding attributes. Supplying `id`,
`action`, `method`, `enctype`, `target`, `autocomplete`, or `novalidate` through
`attrs` is always an error, even when the direct input is omitted. `action` and
`target` accept strings, including the empty string. Nullable string inputs
reject other types with `TypeError`; enum inputs accept only the exact lowercase
literals below and reject other values with `ValueError`. Native combinations
such as `method="get"` with an authored `enctype` pass through unchanged.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `id` | `str` or `None` | generated | structural server-only | unique native Form identity and external control ownership target; authored IDs must be unique in the document |
| `action` | `str` or `None` | `None` | structural server-only | native submission destination; omission uses the document's current URL behavior |
| `method` | `get`, `post`, `dialog`, or `None` | `None` | structural server-only | native submission method; omission uses the browser default |
| `enctype` | URL encoded, multipart, plain text, or `None` | `None` | structural server-only | native submission encoding |
| `target` | `str` or `None` | `None` | structural server-only | native browsing-context target |
| `autocomplete` | `on`, `off`, or `None` | `None` | structural server-only | native Form autocomplete hint |
| `disabled` | `bool` | `False` | reactive configuration fallback | disables physical descendant native controls and supplies Citry disabled context |
| `readonly` | `bool` | `False` | reactive configuration fallback | supplies a default to supporting Citry controls; it is not a native Form state |
| `submitting` | `bool` | `False` | reactive Form configuration fallback | exposes busy state and blocks later submit dispatch from reaching handlers reached after CForm's capture listener; it is not inherited by descendants |
| `novalidate` | `bool` | `False` | structural server-only | maps to native `novalidate` |
| `class_` | Citry class value or `None` | `None` | structural server-only | merges consumer classes onto the native Form |
| `style` | Citry style value or `None` | `None` | structural server-only | merges consumer inline styles onto the native Form |
| `attrs` | mapping or `None` | `None` | structural server-only | merges allowed less-common native and consumer attributes onto the Form |

Client inputs are passed through `$c-props`:

| Client input | Type | Omitted | `null` | Invalid value | Recovery and affected surfaces |
|---|---|---|---|---|---|
| `disabled` | Boolean | server fallback | invalid | report once per invalid episode and use server fallback | a later Boolean or omission recovers; fieldset, context, and `data-disabled` update |
| `readonly` | Boolean | server fallback | invalid | same | a later Boolean or omission recovers; context and `data-readonly` update |
| `submitting` | Boolean | server fallback | invalid | same | a later Boolean or omission recovers; the Form guard, `aria-busy`, and `data-submitting` update |

`id`, action attributes, `novalidate`, `class_`, `style`, and `attrs` remain
server-only because they define native structure, routing, or static ownership.

## 5. State model

| State | Trigger | Form result | Descendant result |
|---|---|---|---|
| ordinary | all reactive inputs false | normal native Form | controls use local configuration |
| disabled | effective `disabled=True` | `data-disabled`; internal fieldset is disabled | physical descendant native controls are disabled; supporting Citry controls reflect inherited disabled state; external controls are unaffected |
| read-only | effective `readonly=True` | `data-readonly` | supporting Citry controls use it as a fallback; ordinary native controls and Buttons have no Form-level read-only state |
| submitting | effective `submitting=True` | `aria-busy=true`, `data-submitting`; later native submit events are canceled and stopped at the Form capture listener | no inherited change; controls remain enabled and successful so values stay in `FormData` |
| disabled and submitting | both effective values are true | both markers apply; submit remains guarded | disabled behavior still wins and physical descendant controls are not successful |
| attempted validation | a physical descendant dispatches native `invalid`, including through `checkValidity()` or `reportValidity()` | `data-validation-attempted` appears | application CSS may reveal summaries or messages |

The first submit that causes application code to set `submitting=True` already
passed CForm's capture guard and proceeds. Later `requestSubmit()` calls and
user submissions are blocked while submitting. The guard can suppress only
listeners reached after CForm's capture listener. Earlier ancestor capture
listeners and same-node capture listeners registered first may observe the
event. Direct `form.submit()` bypasses the submit event and therefore bypasses
the guard, as defined by HTML. Server idempotency and request epochs remain
application responsibilities.

`disabled` must win over a descendant's explicit false configuration because
that matches the native fieldset. `readonly` is a default and may be overridden
by a supporting control. CForm does not apply group opacity; each styled control
owns its disabled presentation, avoiding compounded opacity.

`data-validation-attempted` clears only after an uncanceled native reset. A
canceled reset preserves values and the marker. Successful submit does not
clear it or set submitting automatically.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CForm` | `default` | yes | one | empty `CFormDefaultSlotData` | none |

Actions, error summaries, status content, sections, and nested field groups are
ordinary composition. Dynamic slots do not apply. Slot data is a server-render
snapshot and does not mirror reactive client configuration.

## 7. Callbacks, native events, and methods

`CForm` adds no component-authored callback, validity mirror, or custom DOM
event. Consumers use native `submit`, `reset`, `invalid`, `input`, `change`,
`formdata`, and click events. `SubmitEvent.submitter` identifies the accepted
submitter. A descendant registry cannot represent native Form validity:
external `form=id` controls, ordinary native controls, programmatic property
changes, and controls with separate validation and submitted-value elements can
all disagree with it.

Native Form methods and properties remain the imperative API:

- `checkValidity()` and `reportValidity()`;
- `requestSubmit()` and `requestSubmit(submitter)`;
- `reset()`;
- `elements`;
- `action`, `method`, `enctype`, `target`, and `noValidate`; and
- `FormData(form)`.

Controls named `submit`, `reset`, or another Form property can shadow that
property on the Form object. Applications that allow such names use the
prototype method explicitly or choose non-conflicting names.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a native Form and adds no role. Enter submission, submitter choice,
constraint validation, first-invalid focus, and platform announcements remain
native. Form layout must not alter source or focus order.

Applications may render an error summary in the default slot. If they cancel
native invalid behavior, they must provide equivalent focus and announcement
behavior. Form-level `aria-busy` describes submitting, but does not make every
control disabled or read-only. Error text alone does not change native
validity; use native constraints or `setCustomValidity()` when submission must
be blocked.

The private empty legend has no accessible content and exists only to reserve
the fieldset's disabled exception. A consumer field group uses its own nested
fieldset and visible legend.

## 9. Native forms and validation

Normal action/method submission, GET query construction, POST bodies,
`method=dialog`, multiple submitters, per-submitter overrides, encoding,
targets, autocomplete, Enter submission, reset, and constraint validation
remain browser-defined. Enabled successful controls with names contribute to
`FormData`; disabled and unnamed controls do not. Submitter name/value is
included only for the accepted submitter.

Controls outside the Form may associate through `form=id`. They participate in
the browser's live `form.elements`, validation, submission, reset, and
`FormData`, but are not physical fieldset descendants. CForm therefore does not
disable them and cannot observe their non-bubbling invalid events through the
Form subtree.

Compound Citry UI controls whose visible validation control differs from their
submitted-value control must keep both elements under one Form owner.
`CCombobox` therefore rejects `form` in `input_attrs`; a future external-owner
surface must associate both elements consistently.

`novalidate` suppresses interactive native validation for Form submission.
`formnovalidate` on a submitter provides the native per-action override.
`requestSubmit()` follows submit and validation behavior; `form.submit()` does
not. Server validation remains authoritative.

Citry Events binds the native submit event and may construct `FormData` or typed
event arguments. It must keep input edits, focus, and successful-control rules,
and must clear application-owned submitting state after success or failure.

## 10. Styling and theme contract

The Form follows [`../ui_theme.md`](../ui_theme.md). Its only public CSS
variable is `--cui-form-gap`, which controls spacing between direct children of
the fieldset. Public selectors are `form` and `fieldset`.

The fieldset reset removes native margin, padding, and border. CForm defines no
color, radius, shadow, or disabled opacity. Consumer classes and style may set
layout or tokens on the root. Child controls own their own design tokens and
state presentation.

## 11. Environmental behavior

CForm is color-scheme neutral and inherits the page. Layout uses logical
properties, preserves source order in RTL, wraps according to consumer content,
and does not require motion. The Form itself has no forced-color decoration and
no authored visible string. Print uses ordinary document flow.

At 200% and 400% zoom, narrow widths, and long translated labels, consumer
sections and action rows must wrap without page overflow. CForm's grid does not
impose columns or fixed widths.

## 12. Overlay and layering behavior

CForm creates no overlay. A Form may live inside `CDialog`; `method=dialog`
retains native Dialog submission semantics. A consumer must not nest another
physical Form inside it. A Dialog already containing a Form must not receive a
second CForm wrapper.

External form-owned controls in a portal or overlay keep native ownership but
do not inherit CForm's physical fieldset disabling or Citry context unless the
rendering ownership also supplies that context.

## 13. Collections, async data, and identity

Dynamic rows use stable application keys. The browser's live `form.elements`
and `FormData` order are authoritative after add, remove, reorder, disable, and
re-enable operations. CForm stores no parallel participant registry and cannot
retain detached controls.

Native bracket, dotted, or repeated names are serialized as authored. The host
framework or application owns parsing them into nested objects. CForm owns no
request, cancellation, stale-response, retry, optimistic update, or server
error state.

## 14. Server render, morph, and cleanup

Server output is a usable native Form and fieldset. The private Form context is
exactly `{form_id, disabled, readonly}` on the server and `{form, disabled,
readonly}` in the browser. It supplies disabled and read-only configuration
before descendant initializers consume it. Submitting is intentionally local to
the Form.

Morphing retained controls preserves browser value, focus, selection, and
autocomplete state according to Citry's ownership contract. Removed Form
initializers remove capture listeners, clear deferred reset work, and mark
captured helpers inactive. CForm has no control registry, observer, or detached
element storage to clean up.

## 15. Security and content trust

Form values, filenames, action destinations, and server errors are untrusted.
Server validation, authorization, CSRF protection, upload limits, MIME/content
inspection, and redirect policy remain required. Native `accept` and browser
constraints are user feedback, not a security boundary.

Citry UI does not log Form values or copy them into public attributes. `action`
and target policy remain application-owned. Consumer attributes cannot replace
component-owned identity, busy state, public parts, or behavior markers.

## 16. Assets and performance

CForm adds one compact initializer and fieldset reset, with no schema engine,
observer, request, icon, font, or control registry. It uses Form-level delegated
listeners for invalid, reset, and submit. Reactive state is constant-size.

The runtime target remains under 5 KiB gzip. One bounded hundred-control smoke
check should catch obvious initialization, reorder, cleanup, or retained-element
regressions. This is not a benchmark program.

## 17. Acceptance matrix

Focused repository evidence in this pass covers:

- exact server output, direct native inputs, generated ID, nested rejection,
  owned-attribute rejection, and no-JavaScript markup;
- representative client fallback, invalid-episode, recovery, and reflected
  behavior across the three reactive inputs;
- representative `FormData`, external ownership, and native methods;
- native required validity, validation-attempted, uncanceled and canceled
  reset, a new invalid attempt during deferred reset cleanup, and canceled
  Combobox reset;
- disabled/read-only inheritance, the reserved-legend guarantee, external
  control exception, effective Button/Field/Input/Combobox state, and no
  compounded opacity;
- first accepted submit, later submitting guard, `requestSubmit()`, FormData
  preservation, and cleanup;
- keyed add/remove/reorder, Citry Events success/failure replacement, edit and
  focus preservation, and no stale registry because no registry exists;
- root class/style merge, public parts, and `--cui-form-gap` overrides.

The [`repeatable contact workflow`](repeatable-form-workflow.md) remains the
cross-family identity and Events pressure test. Shared package gates cover
assets, hosts, wheel contents, and the bounded performance smoke check.

The release matrix additionally covers every client input's complete omitted,
valid, null, invalid, recovery, and server-fallback sequence; Enter and
multiple-submitter behavior; per-submitter overrides; custom validity and
first-invalid focus; direct `form.submit()` bypass; and pending-work cleanup.
Manual evidence covers keyboard, mobile input, screen readers,
autofill/password managers, visual review, Dialog composition, light/dark,
RTL, forced colors, zoom, and error-summary focus.

## 18. Compatibility classification

Stable API includes all server and client inputs, the required slot, native
event and Form behavior, inherited configuration, `--cui-form-gap`, public
parts, and reflected attributes. The native Form and fieldset are structural
contracts.

The reserved empty legend, context key, behavior markers, listener ordering
inside the initializer, classes, and private variables are private. Exact
default gap and diagnostics wording are evolvable. A future schema, rules,
server-error, or dirty/touched extension must not silently change CForm's native
contract.

## 19. Public documentation contract

[`cform/api.md`](../../../packages/py/citry_ui/citry_ui/components/cform/api.md)
is the component-owned guide. [`cform/api.yml`](../../../packages/py/citry_ui/citry_ui/components/cform/api.yml)
is the exhaustive structured reference. The guide teaches ordinary composition
and browser behavior before edge cases.

The page uses one coherent astronomy-observatory theme and this example
catalog:

| Order | Reader task | Fixture and copy | Visible states | Controls | Profiles | Evidence |
|---|---|---|---|---|---|---|
| 1 | recognize the family at a glance | telescope-time request and calibration queue | ordinary and submitting cards | none | desktop, narrow | screenshot and visual review |
| 2 | build the shortest useful Form | observation title, target, and notes | ordinary | edit fields; submit locally | desktop | preview render and `FormData` status |
| 3 | configure shared behavior | observatory access request | ordinary, disabled, read-only, submitting | three toggles and gap slider | desktop, narrow | DOM state and visual review |
| 4 | use native submission data | transient-object report | edited and submitted | edit, press Enter, submit, reset | desktop | `FormData`, submitter, and reset assertions |
| 5 | use browser validation | instrument booking with required email and date | untouched, invalid, corrected | edit and submit | desktop | native `:invalid`, focus, and attempted marker |
| 6 | preserve or cancel reset | exposure-plan defaults | edited, reset, canceled reset | edit, reset, cancel-reset toggle | desktop | values and marker assertions |
| 7 | guard duplicate submission | long-running plate solve | ordinary and submitting | submit; finish request | desktop | first/later submit counts and `FormData` |
| 8 | choose among submitters | observation draft | draft and publish actions | two submitters | desktop | `SubmitEvent.submitter` and overrides |
| 9 | associate an external control | proposal form with external allocation code | enabled and disabled internal group | disable toggle; submit | desktop | ownership, enabled exception, and `FormData` |
| 10 | show server feedback | observatory account request | server error and cleared error | edit the rejected field | desktop | Field presentation and application-owned clearing |
| 11 | change repeated fields | filter-wheel sequence | add, remove, reorder | row controls | desktop, narrow | stable identity and live `FormData` order |
| 12 | customize presentation | compact night-mode checklist | default and customized | gap, width, color-scheme controls | desktop, narrow | class/style, parts, token, and overflow review |

Each example follows [`_preview.md`](_preview.md): result first, concise text,
controls separated from rendered content, collapsed source, useful interaction,
and no invented application workflow that distracts from the contract.

The generated API reference records every input, slot, reflected attribute,
selector, CSS variable, type alias, and slot-data interface. Empty event and
method sections render as `-`.

## 20. Open decisions and deferred work

- A schema/rules engine, server-error map, dirty/touched store, and async
  validation coordinator require a separate extension design.
- A reusable error-summary component requires its own research and focus/live-
  region contract.
- Localization remains separate follow-up work after component-owned strings
  and translation-key boundaries are understood.
- Form-associated custom-element support belongs to the future control family
  that needs it; CForm already preserves the browser contract.
- CForm intentionally exposes no aggregate validity callback or attribute. Any
  future form-management extension must state whether it covers the complete
  native Form or only registered Citry controls.
