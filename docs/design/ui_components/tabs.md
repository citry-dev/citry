# Citry UI Tabs

**Status: reference implementation for the current Tabs scope. Updated:
2026-08-05.** The styled `CTabs`, `CTab`, and `CTabPanel` implementation,
automated tests, structured API reference, and public example catalog are
complete for the scope below. Human visual and content polish plus live browser
testing remain before release. Later increments may extend this contract;
behavior changes require specification and acceptance-test updates together.

## 1. Purpose and product bar

Tabs present one panel from a related set while preserving an obvious,
keyboard-operable path between choices. This first production family must be
useful without application CSS and must feel native to Citry's server render,
component composition, client lifecycle, and Events model.

The product bar is Vuetify-like configuration and browser interactivity, not a
copy of Vuetify's Vue API or Sass surface. The first increment covers the
complete core interaction and a deliberate visual configuration set. Later
increments add breadth only with scenarios and acceptance evidence.

This family ships no headless component classes. Reconsider a headless Tabs
API only after a broader styled catalog and a real application expose concrete
composition needs and representative full-page performance measurements.

## 2. Prior art and resulting choices

The source set below was reviewed for this scope on 2026-07-30. Links to
rolling documentation or source must be checked again when a later increment
changes the corresponding contract.

The recurring compound shape is Root, List, Tab or Trigger, and Panel or
Content. Explicit values pair controls and panels independently of their DOM
position or labels.

- The [WAI-ARIA APG Tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)
  defines the semantic relationships, roving focus, automatic and manual
  activation, orientation-sensitive arrows, and optional Home and End keys.
- [React Spectrum Tabs](https://react-spectrum.adobe.com/Tabs) separates
  `selectedKey` from `defaultSelectedKey`, supports automatic/manual keyboard
  activation, orientation, disabled keys, density, and a selection callback.
- [Radix Tabs](https://www.radix-ui.com/primitives/docs/components/tabs)
  combines controlled/uncontrolled values with orientation, direction,
  activation mode, looping, disabled triggers, and stable state attributes.
- [Material UI Tabs](https://mui.com/material-ui/api/tabs/) adds alignment,
  full-width and scrollable presentation, selection-follow-focus, indicator,
  and overflow controls.
- [Vuetify Tabs](https://vuetifyjs-vuetify.mintlify.app/components/tabs) adds
  density, alignment, growth, fixed widths, stacking, colors, indicator
  control, and overflow arrows around a controlled selection model.

Their notification APIs also informed the client contract. Radix uses
`onValueChange(value)`, React Spectrum uses `onSelectionChange(key)`, Material
UI uses `onChange(event, value)`, and Vuetify uses `update:modelValue`. These
are model-update callbacks: user selection reports a requested value, while an
external controlled-value update does not echo the callback. Web Component
libraries may instead expose DOM lifecycle events; for example,
[Web Awesome Tab Group](https://webawesome.com/docs/components/tab-group/)
emits separate tab-show and tab-hide events. CTabs has no independent panel
lifecycle in this increment, so it adopts the callback model without adding a
duplicate custom DOM event.

Their composition APIs differ more than their selection APIs. Radix and React
Spectrum expose explicit Root, List, Tab, and Panel children; React Spectrum
also renders dynamic collections from item data. Material UI exposes
replaceable internal slots for its list, indicator, scrollbar, and scroll
buttons. Vuetify's current
[`VTabs` source](https://github.com/vuetifyjs/vuetify/blob/master/packages/vuetify/src/components/VTabs/VTabs.tsx)
supports general `tab` and `item` slots, `prev`, `next`, and `window` slots,
plus keyed `tab.<value>` and `item.<value>` families. Citry's first increment
uses explicit compound components and their default slots. It does not render
tabs from a collection or own an indicator or scroll controls, so a dynamic
slot namespace or replaceable internal-control slots would have no supported
job yet.

These libraries agree on the core state and keyboard model. They also show a
common failure mode: overflow, routing, lazy content, animated indicators, and
editable tabs greatly enlarge the state machine. Reports collected in the
[Vuetify reconnaissance](../ui_research/recon-vuetify.md) include eager panel
cost and unstable slider behavior. Citry therefore ships the accessible core
before adding pagination, animated geometry, or conditional mounting.

APG examples are instructional rather than production certification. Citry's
own DOM, lifecycle, direction, focus, and assistive-technology behavior remains
our responsibility.

## 3. Public composition

```citry-html
<c-CTabs
  default_value="account"
  aria_label="Account settings"
  activation="automatic"
  variant="underline"
  density="default"
>
  <c-CTab value="account">
    Account
  </c-CTab>
  <c-CTab value="security">
    Security
  </c-CTab>
  <c-CTabPanel value="account">
    Account preferences
  </c-CTabPanel>
  <c-CTabPanel value="security">
    Security preferences
  </c-CTabPanel>
</c-CTabs>
```

The same definitions remain directly composable from Python through
`from citry_ui import CTabs, CTab, CTabPanel` after the application registers
`citry_ui`.

`CTab` and `CTabPanel` are declaration components. They must render while a
`CTabs` declaration pass is active, register their validated inputs and lazy
default Slots, and produce no HTML of their own. The `CTabs` template queues a
private declaration collector before the private implementation. Citry settles
the collector and its declaration children first; the implementation then
validates the populated registry, creates the single accessibly named
`role="tablist"` element, renders every Tab inside it, and renders every Panel
as its sibling. The empty declaration ranges remain in the render tree as
ownership source carriers. Slot content stays lazy and renders once at its
final location with its caller scope, dependencies, ownership, and render-site
provides intact.

Only `CTab` and `CTabPanel` declarations, formatting whitespace, and
transparent components that produce no other output may appear in the root's
default Slot. Other rendered output is an error rather than content that is
silently discarded. Values are non-empty and unique, the Tab and Panel value
sets match exactly, and the initial value identifies an enabled Tab. A
declaration rendered outside `CTabs` fails immediately.

The private implementation guarantees the styled DOM layout: the TabList and
TabPanels are direct element children of the Tabs root, and Tabs are direct
element children of TabList. The client still diagnoses later browser-owned
DOM changes that violate this layout.

A `CTab` and `CTabPanel` end the current Tabs context for their descendants.
A nested tab or panel therefore needs a fresh `CTabs`. Styled nested Tabs may
appear in a panel, not inside the native button rendered by `CTab`.

## 4. Inputs and slots

### `CTabs`

| Input | Type | Default | Contract |
|---|---|---|---|
| `default_value` | `str` | required | Uncontrolled initial selection and server fallback. |
| `value` | `str | None` | `None` | Server-controlled selection for this render. It wins over `default_value`. |
| `activation` | `"automatic" | "manual"` | `"automatic"` | Whether keyboard focus also selects, or Enter/Space selects explicitly. |
| `orientation` | `"horizontal" | "vertical"` | `"horizontal"` | Visual arrangement and applicable arrow keys. |
| `direction` | `"ltr" | "rtl" | None` | Optional explicit direction. When absent, inherit computed browser direction. |
| `loop` | `bool` | `True` | Whether arrow navigation wraps at either end. |
| `disabled` | `bool` | `False` | Disable every tab without losing the selected state. |
| `variant` | `"underline" | "pill"` | `"underline"` | Selection treatment. |
| `density` | `"default" | "comfortable" | "compact"` | `"default"` | Tab padding and minimum target size. |
| `align` | `"start" | "center" | "end"` | `"start"` | Tab alignment on the list's main axis. |
| `grow` | `bool` | `False` | Make tabs share the available main-axis size. |
| `id` | `str | None` | generated | Stable root and relationship prefix when supplied. An explicit value must be non-empty and contain no ASCII whitespace. |
| `aria_label` | `str | None` | `None` | Direct accessible name for the generated element with `role="tablist"`. At least one accessible-name input is required. |
| `aria_labelledby` | `str | None` | `None` | ID reference naming the generated element with `role="tablist"`. At least one accessible-name input is required. |
| `class_` | Citry class value or `None` | `None` | Consumer classes on the Tabs root. |
| `style` | Citry style value or `None` | `None` | Consumer inline styles on the Tabs root. |
| `attrs` | `dict[str, object] | None` | `None` | Additional root attributes; owned identity, state, and ARIA attributes win. |
| `tab_list_attrs` | `dict[str, object] | None` | `None` | Additional attributes for the generated `role="tablist"` element; owned role, orientation, accessible name, part, and behavior attributes win. |

The required `default` slot receives an empty data object and accepts the
family's Tab and TabPanel declarations.

### `CTab`

`value: str` is required. `disabled: bool = False` disables one tab. `class_`
and `style` target the native Button directly. `attrs` targets the same Button;
owned type, role, relationships, state, disabled
state, and part attributes win. The required `default` slot receives `value`,
`is_selected`, and `is_disabled` from the server render.

### `CTabPanel`

`value: str` is required. `class_`, `style`, and `attrs` target the panel; owned role,
relationships, visibility, state, and part attributes win. The required
`default` slot receives `value` and `is_selected` from the server render.

Slot data describes the server render. Caller-authored slot content does not
become reactive merely because the browser changes selection. Browser-visible
state belongs on the documented DOM and callback surfaces below.

| Component | Slot | Cardinality | Slot data | Fallback |
|---|---|---|---|---|
| `CTabs` | `default` | exactly one | none | none |
| `CTab` | `default` | exactly one | `value`, `is_selected`, `is_disabled` | none |
| `CTabPanel` | `default` | exactly one | `value`, `is_selected` | none |

Unknown or duplicate fills are rejected by Citry's slot contract. A missing
required default fill is rejected. The compound validation described above
rejects fills that place a Tab or TabPanel outside its valid Tabs context. This
increment defines no dynamic slot names.

## 5. Selection and client integration

The server always renders one complete initial state. Without JavaScript, the
selected panel remains visible and all semantic relationships remain valid,
but the tab buttons do not switch panels. Interactive use therefore requires
the component's client asset; the fallback preserves meaningful content rather
than hiding the entire family.

With the Citry client active, `CTabs` owns browser-local selection. Pointer and
keyboard activation update `aria-selected`, roving `tabindex`, `hidden`, and
documented state attributes without a Python round trip.

`CTabs` declares these optional `$c-props`:

| Client prop | Type | Meaning |
|---|---|---|
| `value` | `String` | Reactive controlled browser value. When present, user interaction requests a change but the prop remains authoritative. |
| `onValueChange` | `Function` | Called as `onValueChange(nextValue, detail)` for user requests. |
| `activation` | `String` | Reactive override for `"automatic" | "manual"`. |
| `orientation` | `String` | Reactive override for `"horizontal" | "vertical"`; updates layout, list ARIA, and the keyboard axis together. |
| `direction` | `String | null` | Reactive override for `"ltr" | "rtl"`; `null` removes the explicit direction and inherits from the document. |
| `loop` | `Boolean` | Reactive override for arrow-key wrapping. |
| `disabled` | `Boolean` | Reactive client override for the root disabled state. |
| `variant` | `String` | Reactive override for `"underline" | "pill"`. |
| `density` | `String` | Reactive override for `"default" | "comfortable" | "compact"`. |
| `align` | `String` | Reactive override for `"start" | "center" | "end"`. |
| `grow` | `Boolean` | Reactive override for equal main-axis tab growth. |

None of these declarations has a JavaScript default. For configuration props,
`undefined` means omitted and restores the validated Python value carried by
`js_data()` for this render. A valid supplied prop wins over that fallback.
`null` is valid only for `direction`; it is invalid for the other configuration
props. Invalid client configuration is reported and restores the Python
fallback. CTabs validates these values inside its initializer rather than using
constructor declarations that would skip the entire initializer on an invalid
first supply. A malformed `$c-props` supplier object remains a Citry boundary
error. The effective value, rather than the public DOM attribute, drives
behavior and synchronizes native properties, ARIA, keyboard handling, and
public state or configuration attributes.

For an uncontrolled instance, a user activation commits immediately. For a
controlled instance, it reports a request through `onValueChange` and waits for
the parent to update the reactive `value` prop. If a previously controlled
`value` becomes `undefined`,
the component preserves its last valid browser selection and continues as an
uncontrolled instance; it does not jump back to `default_value`. A later valid
`value` makes it controlled again. Any supplied value, including `null`, marks
the component controlled. A non-string value or a string that does not identify
an enabled tab is reported and leaves the last valid selection unchanged;
eligible user requests still call `onValueChange` but cannot commit locally
until the prop becomes omitted or valid. A server rerender reconciles to the
new valid server value without notifying the callback unless a
client-controlled prop is present.

`default_value`, `id`, `attrs`, `tab_list_attrs`, slot topology, Tab and
TabPanel values, TabList accessible-name inputs, and per-Tab `disabled` remain
fixed for one server render. In particular, reactive per-Tab disabling is
deferred until the specification defines what happens when the selected or
focused tab becomes disabled and when every tab is disabled. It must not be
added as a prop by copying the root-disabled behavior.

Every eligible user-requested change calls the optional `onValueChange`
callback with the requested value and this detail object:

```js
{
  value: "security",
  previousValue: "account",
  source: "pointer" | "keyboard" | "removal",
}
```

The callback runs only when the requested value differs from the current value
and identifies an enabled tab. It runs before an uncontrolled instance commits
the requested selection. In a controlled instance it communicates the request
and the parent remains responsible for updating `value`. Initial state and
external controlled updates do not call it.

When the selected tab is removed by client-owned DOM work and the server has
not supplied a new valid value, Tabs requests and commits a deterministic
fallback. It prefers the next enabled tab at the removed tab's former
position, then the previous enabled tab, then the first enabled tab. The
callback uses `source: "removal"`. If the removed tab held focus, focus moves
to that fallback. If no enabled tab remains, all tabs and panels become
inactive, the root removes `data-value`, and no callback fires. A server
replacement that supplies a valid new value applies it without a callback;
if it removed the focused tab, focus moves to the server-selected tab.

CTabs does not dispatch a component-authored custom DOM event. Consumers use
`onValueChange` for Tabs selection requests and Alpine `@click`, `@keydown`,
`@focus`, and similar listeners when they need the native events emitted by the
rendered buttons. Nested Tabs keep their selection behavior and callback
ownership isolated to the nearest root.

## 6. Semantics, keyboard, and focus

- `CTabs` renders one internal `role="tablist"` element with an accessible
  name and explicit `aria-orientation`.
- Each `CTab` is a native `button type="button"` with `role="tab"`,
  `aria-controls`, `aria-selected`, and roving `tabindex`.
- Each `CTabPanel` has `role="tabpanel"`, `aria-labelledby`, and `hidden` when
  inactive. Panels remain mounted. Panels use `tabindex="0"` in this increment
  so panel content has a dependable next tab stop.
- Disabled tabs are native-disabled, never selected through user interaction,
  and skipped during focus movement.

Keyboard behavior:

| Context | Key | Result |
|---|---|---|
| Horizontal LTR | Right / Left | Focus next / previous enabled tab. |
| Horizontal RTL | Right / Left | Focus previous / next enabled tab. |
| Vertical | Down / Up | Focus next / previous enabled tab. |
| Either | Home / End | Focus first / last enabled tab. |
| Manual activation | Enter / Space | Select the focused tab. |
| Automatic activation | Any focus movement above | Focus and select together. |

Horizontal Tabs do not consume Up or Down. Vertical Tabs do not consume Left
or Right. If `loop=False`, movement stops at the first or last enabled tab.
Pointer activation selects the clicked enabled tab and leaves native focus on
that button. Tab enters the composite at its current roving tab stop.

## 7. Public styling contract

All default rules live in `@layer citry-ui.theme` and use low-specificity
`:where(...)` selectors. Every `data-citry-ui-part` value below is stable,
semantic-versioned public API for CSS overrides, inspection, and tests. The
marker identifies the owned semantic element and is not a state or instance
identifier.

The public component page presents these markers under **Selectors**, because
consumers use exact `[data-citry-ui-part="..."]` attribute selectors and this
surface is not the Shadow DOM `::part()` API. It presents the reflected
`data-*` values under **Attributes**, not "state attributes", so the wording
cannot be confused with Citry's server event-handler State.

| Component | Public part | Element and purpose |
|---|---|---|
| `CTabs` | `tabs` | Root `div` that owns configuration and selection mirrors. |
| `CTabs` | `tab-list` | Generated element with `role="tablist"` that arranges the controls. |
| `CTab` | `tab` | Native tab `button` and its active, focus, hover, and disabled styling. |
| `CTabPanel` | `tab-panel` | Element with `role="tabpanel"` that contains one panel's content. |

Public reflected attributes are:

- Tabs: `data-value`, `data-activation`, `data-orientation`, `data-direction`,
  `data-loop`, `data-density`, `data-variant`, `data-align`, `data-grow`, and
  `data-disabled`;
- TabList: `data-orientation`;
- Tab: `data-state="active|inactive"`, `data-value`, and `data-disabled`;
- TabPanel: `data-state="active|inactive"` and `data-value`.

The initial public variable set is:

| Variable | Use | Default |
|---|---|---|
| `--cui-tabs-accent` | Selected indicator and text; pill-track derivation. | `LinkText` |
| `--cui-tabs-border-color` | List divider. | 22% `currentColor` |
| `--cui-tabs-muted-color` | Inactive tab text. | 68% `currentColor` |
| `--cui-tabs-list-background` | Tab-list track; the pill fallback derives from the accent. | transparent; 12% accent for pill |
| `--cui-tabs-active-background` | Selected pill-tab background. | `Canvas` |
| `--cui-tabs-hover-background` | Enabled tab hover background. | 8% `currentColor` |
| `--cui-tabs-focus-color` | Focus-visible outline. | `Highlight` |
| `--cui-tabs-radius` | Pill-list radius; tab radius is smaller by `0.125rem`. | `0.5rem` |
| `--cui-tabs-gap` | Root gap between list and panels. | `1rem` |
| `--cui-tabs-tab-inline-padding` | Tab inline padding. | `0.875rem`; `0.75rem` comfortable; `0.625rem` compact |
| `--cui-tabs-tab-block-padding` | Tab block padding. | `0.625rem`; `0.5rem` comfortable; `0.375rem` compact |
| `--cui-tabs-panel-padding` | Panel padding. | `1rem` |

Consumers may set variables on any ancestor or use the stable part and state
attributes. The library does not assign defaults to the public variables on
the root, because doing so would defeat inheritance from an ancestor. Private
effective variables resolve the public input and fallback for implementation
rules; those private names are not API.

The root `data-value` and state or configuration attributes are read-only
mirrors of effective component values for CSS, inspection, and selectors.
Changing a mirror directly does not reconfigure the component, and the next
component update may overwrite it. Native properties and ARIA remain the
semantic truth. The Tab and TabPanel `data-value` attributes instead carry
their immutable server-rendered pairing identity; they are still not a
supported mutation API. Private `.cui-*` class names support implementation
rules and are not the customization contract. Private `data-citry-tabs-*`
attributes support client ownership and lookup; they are not styling or
customization API.

The variable set grows when real brand adaptations expose another recurring
override need. A library-wide design-token tier waits until multiple
production families reveal shared semantic roles rather than merely similar
values. Acceptance coverage must inspect computed styles for ancestor and
root variable overrides, part-selector overrides, and variant or density
fallbacks.

The styled component must preserve visible focus and selected state in forced
colors, remove nonessential transitions under reduced motion, use logical
properties, inherit direction by default, and remain operable at 400% zoom.

## 8. Lifecycle, nesting, and security

The Tabs initializer installs listeners and one child-list observer only on
its own root and returns a cleanup function. Event delegation and structural
reconciliation must ignore nested `CTabs` DOM. A compatible Citry morph may
replace descendants, so every interaction obtains the current owned tab and
panel collection rather than retaining stale child nodes. Tabs and panels use
their value as a private Citry morph key; public inspection uses `data-value`.

On reinitialization, valid server or controlled state wins. Initialization and
external controlled updates never move focus. User keyboard movement may move
focus only to an enabled tab in the same owned Tabs root.

Values are identifiers, not selectors or HTML. Client code compares dataset
strings directly and does not interpolate values into CSS selectors. Slot
content follows Citry's normal escaped-content contract. Open attribute maps
cannot replace library-owned semantic or relationship attributes.

## 9. First-increment acceptance matrix

### Required before calling the increment production-complete

- Render tests for IDs, roles, names, initial selected/disabled state, every
  validation error, configuration attributes, parts, variables, and direct
  Python composition.
- Browser tests for pointer selection; automatic/manual activation; Home,
  End, arrows, disabled skipping, loop on/off, vertical layout, RTL horizontal
  navigation, callback detail, controlled props and control removal, runtime
  configuration overrides and fallback, two independent roots, nested roots,
  reinitialization, and listener cleanup.
- Browser assertions for focus location, roving `tabindex`, panel visibility,
  ARIA state, and no page-scroll key interception on the irrelevant axis.
- Automated accessibility checks in every selected, disabled, orientation,
  variant, and density scenario once the shared axe harness lands.
- Reviewed light, dark, forced-colors, reduced-motion, narrow, long-label,
  vertical, RTL, and 400%-zoom scenarios in the docs live host and standalone
  quality page.
- Manual keyboard script plus NVDA/Firefox and VoiceOver/Safari checks before a
  public package release.
- Component asset-size and repeated-initialization measurements against the
  Phase 7 budgets.

### Explicit later increments

- overflow buttons, active-tab centering, fixed-width tabs, and an animated
  geometry indicator;
- lazy or conditional panel mounting and its form/focus implications;
- link and router tabs;
- deletable/reorderable tabs and APG Delete behavior;
- icons, stacked icon/label presentation, badges, and close affordances;
- server Events convenience bindings beyond `$c-props` callbacks;
- theme-provider defaults and locale-owned labels for future overflow actions;
- reactive TabList accessible names and per-Tab disabled state, after their
  atomic naming and selected/focused-tab transition policies are specified;
- any supported headless API.

## 10. First-increment evidence

Implemented and verified so far on 2026-07-30:

- `CTab` and `CTabPanel` collect lazy declarations, while a private styled
  implementation owns their final server markup and `CTabs` owns client
  behavior;
- focused render and validation tests pass for the compound contract,
  configuration, stable parts, public variables, and computed CSS overrides;
- 60 behavior cases pass across Chromium, Firefox, and WebKit for pointer,
  keyboard, activation mode, disabled items, axis, direction, looping,
  controlled props and control removal, reactive configuration and fallback,
  `onValueChange` callback handling, nested-root isolation, public-mirror
  integrity, deterministic dynamic-removal fallback, keyed Citry Events
  reorder and removal, focus recovery across initializer replacement, removal
  cleanup, ancestor and root variables, and public part selectors;
- the public composition and authoritative API render on
  `/ui-library/components/tabs/`; its complete reader-facing source is owned by
  `ctabs/snippets/` and projected through the docs live-code component. The
  block remains intentionally static until the published `citry-ui` package is
  present in the browser playground runtime; and
- `CTabs` contributes 17,739 raw / 3,550 gzip / 3,082 Brotli bytes of JavaScript
  and 6,370 raw / 1,244 gzip / 1,037 Brotli bytes of CSS in the development
  source form. The complete production catalog contributes 10,805 Brotli
  bytes of JavaScript and 4,458 Brotli bytes of CSS, inside the aggregate
  Phase 7 limits.

The remaining acceptance items in section 9 are not implied by this evidence.
In particular, per-state axe, screenshots, complete-page Lighthouse, and the
full visual-profile and manual accessibility matrices remain open.
Representative complete-page axe and local interaction budgets pass, but they
do not substitute for every exposed Tabs state.

## 11. Public documentation examples proposal

**Status: all 13 Tabs examples implemented; wide, narrow, light, dark, and
automated interaction checks pass. Human visual and content polish plus live
browser testing remain.**
This section records the Tabs-first documentation experiment. Do not apply it
mechanically to the other component families until the complete rendered page
has been reviewed.

The shared preview behavior, authoring contract, and implementation sequence
live in [`_preview.md`](./_preview.md). This section owns only the Tabs-specific
page progression and API coverage used to validate that shared contract.
The canonical modules live together in
[`ctabs/snippets/`](../../../packages/py/citry_ui/citry_ui/components/ctabs/snippets/).
Each `<c-ui-demo>` directive in `api.md` names its exact source module, and the
docs build validates that every module stays within this component family.

### 11.1 Tabs page progression

The conceptual section uses this order. The docs builder appends the structured
API reference from `ctabs/api.yml` at the end.

| Order | Section and example | What the reader can see or do | Contract covered |
|---|---|---|---|
| 1 | **Tabs at a glance** | Use two immediately interactive space settings to show underline and pill treatments, selected and inactive Tabs, Panels, and one disabled Tab. | Composition, default selection, variant, per-Tab disabled state. |
| 2 | **Compose Tabs** | Show the smallest complete composition, followed by its collapsed canonical source. | `CTabs`, `CTab`, `CTabPanel`, values, accessible naming. |
| 3 | **Try the configuration** | Change accent, variant, density, orientation, alignment, growth, loop behavior, and root disabled state from host-owned controls above the rendered component. | Public CSS variables, visually meaningful server and client inputs, client override behavior, and the preview-controls bridge. |
| 4 | **Choose a variant** | Compare underline and pill treatments side by side without requiring a toggle. | `variant`. |
| 5 | **Set density and available width** | Compare default, comfortable, and compact Tabs, then toggle equal growth. | `density`, `grow`. |
| 6 | **Align and orient Tabs** | Change start, center, and end alignment; show a vertical catalog of celestial objects. | `align`, `orientation`. |
| 7 | **Control selection** | Select a view from an external control, select a Tab, and inspect the latest `onValueChange` detail. | Controlled `value`, uncontrolled fallback, `onValueChange`. |
| 8 | **Disable selection** | Compare one disabled Tab with a control that disables the whole Tabs root. | `CTab.disabled`, `CTabs.disabled`. |
| 9 | **Choose keyboard activation** | Put automatic and manual Tabs side by side with concise focus instructions and visible current values. | `activation`, arrow keys, Home, End, Enter, Space, `loop`. |
| 10 | **Use long Tab lists** | Place long labels in a narrow card so the reader can use the supported horizontal scroll behavior. State that this increment has no overflow arrows or menu. | Current overflow behavior and its explicit limit. |
| 11 | **Nest Tabs** | Put a second Tabs root inside a Panel and make both roots independently interactive. | Declaration boundaries, nested context isolation. |
| 12 | **Support direction** | Compare LTR and RTL examples and exercise direction-aware arrow keys. | `direction`. |
| 13 | **Theme and customize Tabs** | Compare light and dark surroundings and a branded example driven only by public CSS variables. | color-scheme contract, public selectors, CSS variables. |

Not every reference input needs a visual heading. IDs, accessible-name
plumbing, and raw attribute maps are important but not intrinsically visual;
the composition example and API reference can own them. Every visual or
interactive contract should appear in at least one rendered example, and the
coverage table above should remain traceable as inputs are added.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
