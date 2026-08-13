# Citry UI Button specification

**Status (2026-08-05): production specification, implementation, automated
evidence, structured API reference, and public example catalog complete;
human visual, keyboard, and assistive-technology sign-off remains.** This
document defines the direct styled `CButton`. A headless component API,
purpose-built icon Button, toggle Button, ButtonGroup, and split Button remain
separate future product decisions.

## 1. Purpose and product bar

`CButton` presents one native command, form action, or visually prominent link
with useful default styling, explicit intent and presentation choices,
optional leading and trailing content, and a pending state that can also be
controlled in the browser. It must retain native `<button>` or `<a>` semantics
and useful server-rendered behavior.

Production-complete means:

- Enter, Space, pointer, touch, form submission, form reset, and submitter
  name/value behavior come from a native `<button>`;
- navigation, modifier clicks, context menus, previews, and link attributes
  come from a native `<a>` when `href` is set;
- loading prevents new activation without moving focus from an operation that
  just became pending;
- server inputs and reactive client overrides produce the same DOM, semantic,
  styling, and activation state;
- all variants, intents, sizes, public variables, parts, and meaningful states
  work in light and dark schemes; and
- consumer attributes and native events remain available without allowing
  replacement of component-owned semantics.

An icon may be its only visible content when the consumer supplies an
accessible name, but `CButton` does not provide the square geometry or stricter
naming API of a future purpose-built icon Button. It does not own router
integration or the operation that sets or clears loading.

The common jobs are intentionally first-class:

| Job | Contract |
|---|---|
| Trigger an ordinary action | omit `href`; native `<button type="button">` |
| Submit or reset a form | omit `href`; set `type`; pass form-owner attributes through `attrs` |
| Navigate with Button presentation | set `href`; native `<a>` with link attributes through `attrs` |
| Express emphasis and meaning | combine `variant` and `intent` |
| Show pending or unavailable work | use reactive `loading` or `disabled` |
| Add decoration or fill available width | use slots or `block` |

## 2. Prior art and complaints

The family was re-audited from its local runtime, render and browser tests,
quality scenario, public guide, structured API, and composed uses before the
external comparison. Existing behavior remained provisional where those
artifacts disagreed.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI prototype | 2026-08-05 | `cbutton.py`, render and browser tests, `button.states`, `api.md`, and `api.yml` | Keep the native root, server/client precedence, native forms, public parts, and token model; repair loading placement and replace the invalid nested-Button public snippet. |
| HTML Living Standard | updated 2026-07-20 | [Button element](https://html.spec.whatwg.org/multipage/form-elements.html#the-button-element) | Native `button`, `submit`, and `reset` behavior; form-owner attributes; no interactive descendants. |
| WAI-ARIA APG and WCAG 2.2 | reviewed 2026-08-05 | [Button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/), [Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html), and [Target Size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | Enter and Space activation, accessible naming, retained focus visibility, unavailable semantics, and minimum target evidence. |
| Material UI | 7.3.11 docs and default-branch source reviewed 2026-08-05 | [Button guide](https://mui.com/material-ui/react-button/), [API](https://mui.com/material-ui/api/button/), [source](https://github.com/mui/material-ui/blob/master/packages/mui-material/src/Button/Button.js), and [translation crash #27853](https://github.com/mui/material-ui/issues/27853) | Three presentation strengths and sizes, start/end decorations, full width, stable loading wrapper, centered replacement, and start/end replacement of only the corresponding decoration. Reject arbitrary root polymorphism and ripple-dependent focus styling. |
| React Aria | current docs reviewed 2026-08-05 | [Button](https://react-aria.adobe.com/Button) | Pending stays focusable, blocks press and hover, and is distinct from disabled; link styling belongs on a semantic Link. Its unstyled delivery is useful behavior evidence but does not meet Citry UI's styled default-library goal alone. |
| React Spectrum | v3 docs and source reviewed 2026-08-05 | [Button guide](https://react-spectrum.adobe.com/v3/Button.html) and [source](https://github.com/adobe/react-spectrum/blob/main/packages/%40react-spectrum/button/src/Button.tsx) | Separate semantic role from fill style, accept native form overrides, and keep icon-only naming explicit. Reject a fixed one-second pending delay and `preventFocusOnPress`. |
| Web Awesome | current docs reviewed 2026-08-05 | [Button docs and API](https://webawesome.com/docs/components/button/) | Semantic variant plus appearance, sizes, start/end slots, stable parts, width stability, form attributes, and `href`. Avoid custom-element form-association complexity by rendering the corresponding native element. |
| Vuetify | default-branch source and issue reviewed 2026-08-05 | [VBtn source](https://github.com/vuetifyjs/vuetify/blob/master/packages/vuetify/src/components/VBtn/VBtn.tsx) and [active-route complaint #11149](https://github.com/vuetifyjs/vuetify/issues/11149) | Confirm expected breadth across variants, color, size, block layout, loading, slots, and `href`. Adopt native link selection but keep router activity out after users reported that route-derived active styling was difficult to disable. |
| Browser interoperability | issue reviewed 2026-08-05 | [WHATWG disabled-event issue #5886](https://github.com/whatwg/html/issues/5886) | Do not promise ancestor-observed descendant clicks from disabled content; test Button and form boundaries instead. |

The shared pattern is a real Button for actions, an explicit non-submit default,
orthogonal presentation and semantic color, leading and trailing content,
native form support, semantic links for navigation, and loading that blocks new
activation without changing the control's identity. Citry adopts that shape.
It rejects arbitrary element polymorphism, route awareness, ripple, implicit
icon lookup, component-owned async work, and a framework-specific press-event
abstraction.

Vuetify carries roughly 30% of the comparative decision weight. Every relevant
`VBtn` surface received an explicit disposition:

| Vuetify surface | Citry disposition |
|---|---|
| `href` and link root | adopt as server-only `href`; render native `<a>` |
| router `to`, active route, and exact matching | omit; a routing integration can supply `href` without coupling Button to a router |
| `variant` | adopt the common `solid`, `outline`, and `ghost` subset |
| color | expose semantic `intent`; use CSS variables or consumer classes for arbitrary colors |
| size, block, loading, prepend, append, loader | adopt as concise sizes, `block`, `loading`, and named slots |
| width, height, density, elevation, rounded, position | achieve through public CSS variables, `attrs`, and utility classes instead of expanding the frequent constructor |
| icon-only mode | defer to a purpose-built component with a stricter accessible-name contract |

Loading placement needs a precise contract. Material UI supplies the only
reviewed three-position implementation: center hides all ordinary visual
content, while start and end hide only the decoration they replace and leave
the label plus opposite decoration visible. Citry adopts that behavior. When
the replaced decoration is absent, the loading state reserves one decoration
position so the indicator cannot overlap the label. Center preserves the
Button's intrinsic inline size; start or end may add the missing decoration
position while loading.

## 3. Public composition and anatomy

Template use:

```citry-html
<c-CButton
  type="submit"
  intent="primary"
  variant="solid"
>
  <c-fill name="start">
    <svg aria-hidden="true">...</svg>
  </c-fill>
  Save changes
</c-CButton>
```

Python composition:

```python
from citry_ui import CButton

save = CButton(
    type="submit",
    intent="primary",
    slots={
        "default": "Save changes",
        "start": icon,
    },
)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CButton` without `href` | native `<button>` | `attrs` merges onto that Button | non-empty accessible name supplied by default content or consumer ARIA attributes |
| `CButton` with `href` | native `<a>` | `attrs` merges onto that link | non-empty accessible name and a consumer-owned destination |

The stable anatomy is one Button with optional `start`, required `content`,
optional `end`, and always-mounted `loading-indicator` parts. Stable loading
markup prevents client prop changes from replacing translated text nodes. No
other wrapper or private class is public structure.

`class_` and `style` are direct root inputs and accept Citry's structured
class/style values. `attrs` accepts other native root, ARIA, `data-*`, and Alpine
attributes. It may still contribute class and style values, which merge with
the direct inputs. Button roots also accept native form attributes; link roots accept
attributes such as `target`, `rel`, and `download`. It cannot replace `href`,
`type`, `disabled`, `aria-busy`, `aria-disabled`, any documented reflected
attribute, or `data-citry-ui-part`. Class and style values merge through
Citry's ordinary HTML attribute rules.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `type` | `button`, `submit`, `reset` | `button` | structural server-only | sets native Button behavior |
| `href` | `str` or `None` | `None` | structural server-only | selects a native link instead of a native action Button |
| `disabled` | `bool` | `False` | reactive configuration fallback | sets local disabled state; a disabled enclosing CForm always wins, sets native Button disabled state or makes a link inert, and blocks activation |
| `loading` | `bool` | `False` | reactive configuration fallback | sets pending semantics and blocks new activation while retaining focus |
| `variant` | `solid`, `outline`, `ghost` | `solid` | reactive configuration fallback | selects presentation strength |
| `intent` | `primary`, `neutral`, `success`, `warn`, `danger` | `primary` | reactive configuration fallback | selects semantic color role |
| `size` | `sm`, `md`, `lg` | `md` | reactive configuration fallback | sets target height, spacing, and text size |
| `block` | `bool` | `False` | reactive configuration fallback | fills the available inline size |
| `loading_pos` | `start`, `center`, `end` | `center` | reactive configuration fallback | replaces the matching visual position while loading; center replaces all ordinary visual content |
| `class_` | Citry class value or `None` | `None` | structural server-only | merges consumer classes onto the selected root |
| `style` | Citry style value or `None` | `None` | structural server-only | merges consumer inline styles onto the selected root |
| `attrs` | mapping or `None` | `None` | structural server-only | merges allowed native and consumer attributes onto the selected root |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `disabled` | Boolean | server fallback | invalid, server fallback | log once per invalid episode and use server fallback | local disabled state; disabled CForm still wins for native `disabled`, `aria-disabled`, state attribute, and activation |
| `loading` | Boolean | server fallback | invalid, server fallback | same | `aria-busy`, `aria-disabled`, state attribute, indicator, activation and submitter behavior |
| `variant` | enum | server fallback | invalid, server fallback | same | configuration attribute and CSS |
| `intent` | enum | server fallback | invalid, server fallback | same | configuration attribute and CSS |
| `size` | enum | server fallback | invalid, server fallback | same | configuration attribute and CSS |
| `block` | Boolean | server fallback | invalid, server fallback | same | configuration attribute and layout |
| `loadingPosition` | enum | server fallback | invalid, server fallback | same | configuration attribute and loading layout |

A supplied valid client prop wins. Removing it returns that field to its
server-rendered fallback. Independent fields continue working when one field is
invalid. Client props never mutate the Python invocation or `attrs`.

## 5. State model

| Current state | Trigger | Native and ARIA result | Activation result |
|---|---|---|---|
| enabled Button | neither disabled nor loading, no `href` | focusable native Button | native click, submit, or reset proceeds |
| enabled link | neither disabled nor loading, `href` set | focusable native link with `href` | native navigation and link interactions proceed |
| disabled | effective local or inherited CForm `disabled=True` | native `disabled` for Button; link drops `href` and uses `tabindex=-1`; `aria-disabled=true` | browser and component block activation |
| loading | effective `loading=True`, not disabled | Button or link remains focusable; link drops `href`; `aria-busy=true`; `aria-disabled=true` | click, navigation, and submitter use are blocked |
| disabled and loading | both effective values true | disabled semantics plus busy semantics | blocked |

Loading presentation follows these visual rules:

| Position | Hidden ordinary content | Visible ordinary content | Missing decoration behavior |
|---|---|---|---|
| `start` | start decoration | label and end decoration | reserve one start-decoration position |
| `center` | start decoration, label, and end decoration | none | not applicable; existing content keeps intrinsic size |
| `end` | end decoration | start decoration and label | reserve one end-decoration position |

Loading is controlled configuration, not an internal asynchronous state. If a
consumer changes loading from false to true while handling a submit click, that
current native activation completes and later activation is blocked. This is
what allows the first request to start. A Button that is already loading when
activation begins cannot submit, reset, or invoke consumer click handlers.

Hover and active visuals apply only when neither disabled nor loading. Focus
remains visible during loading. Native disabled behavior governs focus when
disabled becomes true.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CButton` | `default` | yes | one | empty `CButtonDefaultSlotData` | none |
| `CButton` | `start` | no | one | empty `CButtonStartSlotData` | omitted |
| `CButton` | `end` | no | one | empty `CButtonEndSlotData` | omitted |
| `CButton` | `loading` | no | one | empty `CButtonLoadingSlotData` | CSS spinner |

Slot data is a server-render snapshot. Reactive client configuration is exposed
through documented reflected attributes, not by rerendering Python slot data.
All slot content becomes Button content and must not contain interactive
elements. The `loading` slot supplies a compact visual indicator within the
one-em loading position; it is hidden from the accessibility tree because the
Button itself carries pending semantics. Dynamic slots do not apply.

## 7. Callbacks, native events, and methods

`CButton` adds no component-authored callback or custom DOM event. Consumers
listen to native events such as `@click`, and forms listen to native `submit`
and `reset`. A blocked loading activation does not reach a consumer click
listener. No public imperative method is needed because native `focus()` and
`click()` remain available on the rendered Button.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a native `<button>` for actions and a native `<a>` for navigation,
so keyboard, focus, browser, and platform semantics come from the chosen
element. The default slot or consumer-provided ARIA attributes must give it an
accessible name. Icon-only content requires an accessible name such as
`aria-label`; title text alone is insufficient. The family does not provide
specialized square icon-Button geometry.

The loading indicator is hidden from the accessibility tree. The Button keeps
its accessible name, exposes `aria-busy=true`, remains focusable, and rejects
new actions. The visual indicator must not be the only loading cue. Focus uses
an unconditional `:focus-visible` ring. Forced-colors mode preserves a visible
border and focus outline.

Touch targets are at least 2.25rem, 2.5rem, and 2.75rem for `sm`, `md`, and
`lg`. Application layouts must provide additional target spacing where WCAG
2.2 Target Size exceptions do not apply.

## 9. Native forms and validation

`type=submit` submits its form owner and participates as the submitter.
`type=reset` invokes native reset. `name`, `value`, `form`, `formaction`,
`formenctype`, `formmethod`, `formnovalidate`, and `formtarget` pass through
`attrs`. A disabled Button is not a successful submitter. A loading Button
blocks pointer, keyboard, `.click()`, and `form.requestSubmit(button)` while
retaining focus.

Form-only attributes and `type=submit` or `type=reset` are invalid when `href`
is set. Link attributes such as `target`, `rel`, and `download` pass through
`attrs`. Link destinations remain consumer-owned.

With JavaScript unavailable, server-rendered disabled and loading Buttons both
use native `disabled`, because there is no client lifecycle that needs focus
retention. During client activation, loading-only state removes native disabled
and uses guarded pending semantics. This intentional enhancement must not
permit an activation during initialization.

With JavaScript unavailable, disabled and loading links omit `href`. Disabled
links use `tabindex=-1`; loading links remain focusable with their authored
tab index or `0`. Client activation restores the destination only when both
states clear.

The Button owns no validation message or Events request. Native submit and
reset behavior composes with the Form and Citry Events specifications.

## 10. Styling and theme contract

The component follows [`../ui_theme.md`](../ui_theme.md).

Variants and intents are orthogonal. `solid` is strongest, `outline` carries a
border and quiet surface, and `ghost` is the lowest-emphasis action. Intent
changes semantic color, not action mechanics.

| Public variable | Value type | Purpose | Current default role |
|---|---|---|---|
| `--cui-button-background` | color | resting background | variant and intent derived |
| `--cui-button-foreground` | color | text and decoration | contrast color derived from intent |
| `--cui-button-border-color` | color | resting border | variant and intent derived |
| `--cui-button-hover-background` | color | enabled hover background | mixed from the effective colors |
| `--cui-button-active-background` | color | enabled active background | stronger mix from effective colors |
| `--cui-button-focus-color` | color | focus outline | `Highlight` |
| `--cui-button-radius` | length | corner radius | `0.5rem` |
| `--cui-button-font-weight` | number or keyword | label weight | `600` |
| `--cui-button-gap` | length | gap between parts | `0.5rem` |
| `--cui-button-disabled-opacity` | number | disabled presentation | `0.48` |
| `--cui-button-height` | length | minimum target height | size derived |
| `--cui-button-inline-padding` | length | logical inline padding | size derived |
| `--cui-button-block-padding` | length | logical block padding | size derived |
| `--cui-button-font-size` | length | label size | size derived |

| Public selector value | Element and purpose | Supported states | Stable relationship |
|---|---|---|---|
| `button` | native Button or link root and attribute destination | all | root |
| `start` | leading content wrapper | enabled, disabled, loading | before content in logical order |
| `content` | required label/content wrapper | all | accessible Button content |
| `end` | trailing content wrapper | enabled, disabled, loading | after content in logical order |
| `loading-indicator` | stable pending wrapper | hidden or loading | child of Button; positioned by loading position |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-loading` | present or absent | effective loading state |
| `data-disabled` | present or absent | effective local or inherited CForm disabled state |
| `data-variant` | `solid`, `outline`, `ghost` | effective presentation |
| `data-intent` | five intent names | effective semantic role |
| `data-size` | `sm`, `md`, `lg` | effective size |
| `data-block` | present or absent | fills inline size |
| `data-loading-position` | `start`, `center`, `end` | effective indicator placement |

Public variables are inherited inputs. Private effective variables resolve
the defaults, and `.cui-*` classes remain private.

## 11. Environmental behavior

Default intent pairs must pass in light and dark, including an opposite nested
`color-scheme` scope. Layout uses logical properties and follows the document's
text direction. The spinner reverses no directional meaning. Reduced motion
uses a static pending mark instead of rotation. Forced colors preserves native
Button and focus affordances. Labels wrap when necessary, and block Buttons
fit narrow containers. Center loading preserves intrinsic inline size. Start
or end loading may add one decoration position when that slot is absent.

The component authors no visible string. Consumer slot content owns language
and translation.

## 12. Overlay and layering behavior

The Button creates no overlay and owns no stacking behavior. A Button may
trigger another component's overlay through native events; that component owns
focus movement and restoration.

## 13. Collections, async data, and identity

The Button owns no collection or request. `loading` reports an operation owned
by application code. The application owns cancellation, retries, stale results,
and clearing pending state after failure or success.

## 14. Server render, morph, and cleanup

The server output is a useful native Button or link. The loading indicator
wrapper is stable across state changes. Client activation attaches guarded
click and, for Button roots, form submission listeners, reactive prop effects,
and no global observer. Cleanup removes every listener. Morphing must preserve
focus when the same root identity remains and must not duplicate guards after
reactivation.

## 15. Security and content trust

Slot text follows Citry's ordinary escaping rules. Trusted HTML remains an
explicit application decision. `attrs` cannot replace owned activation,
semantic, state, or part attributes. URLs in `href` and native form attributes
are consumer-owned and are not treated as trusted by Citry UI.

## 16. Assets and performance

The family adds one shared CSS asset and one shared JavaScript initializer only
when used. It adds no icon, font, network request, observer, timer, or external
dependency. Phase 7 records raw, gzip, and Brotli size after implementation.
The target is under 5 KiB gzip combined for the family and no retained listener
after removal. One hundred Buttons must not create document-level listeners.

## 17. Acceptance matrix

Automated evidence must cover:

- schema validation, owned-attribute rejection, every slot, and direct Python
  composition;
- all variants, intents, sizes, loading positions, server states, and reactive
  prop transitions;
- pointer, Enter, Space, `.click()`, submit, reset, submitter name/value,
  `requestSubmit`, link navigation and modifier-click propagation, disabled
  and loading guards, and focus retention;
- light, dark, nested scheme, ancestor and root variables, parts, two brands,
  reduced motion, forced colors, RTL, narrow width, wrapping, zoom, and long
  labels through computed style and screenshots;
- axe, accessible name, busy/disabled state, and accessibility-tree assertions;
- initial activation, repeated initialization, morph, fragment insertion,
  removal, and retained-resource counts; and
- raw/compressed assets plus repeated-instance and first-activation timing.

Manual evidence must cover keyboard behavior, VoiceOver/Safari,
NVDA/Firefox, touch, 400% zoom, forced colors, and visual hierarchy across all
intent and variant pairs.

## 18. Compatibility classification

Stable API includes the component and schema names, server and client inputs,
slot names and data types, native event policy, form behavior, public variables,
selectors, reflected attributes, validation errors, and loading guards.
Native semantics, focus retention while loading, useful server output, and the
documented stable anatomy are behavioral and structural contracts.

Exact default colors, spacing, radius, spinner drawing, and transitions are
evolvable design. Private classes, private variables, JavaScript organization,
and incidental slot-wrapper implementation are private.

## 19. Public documentation contract

[`cbutton/api.md`](../../../packages/py/citry_ui/citry_ui/components/cbutton/api.md)
is the component-owned reader-first guide. Its sibling `api.yml` is the
exhaustive generated reference. The guide shows the component before its first
large code block, teaches native composition before reactive control, and
places specialized behavior and customization after the common visual choices.

The page uses one botanical field-guide theme. Copy stays concrete and
recognizable: specimens, habitats, trails, spores, and night gardens. It does
not mix unrelated motifs or use generic workplace and dashboard fixtures.

| Order and module | Reader task and fixture | Visible states and interaction | Controls and environmental cases | Contract coverage and focused evidence |
|---|---|---|---|---|
| 1. `at_a_glance.py` | Recognize the family in a small botanical expedition action set. | Solid, outline, ghost, leading decoration, disabled, and centered loading shown together. | Responsive wrapping; light and dark inherited from docs. | First visual impression, variants, common intents, slots, disabled/loading distinction; load and narrow-overflow browser check. |
| 2. `basic_actions.py` | Write a native action with optional decoration. | Ordinary Button plus start and end fills. | No controls. | Minimal template and Python composition, `type=button`, accessible label, slot order. |
| 3. `navigation.py` | Navigate with Button presentation. | Internal and external native links. | Native modifier clicks and context menus; narrow wrapping. | `href`, anchor root, `target` and `rel`, identical inline layout, unavailable-link behavior. |
| 4. `configuration.py` | Compare the reactive configuration in one place. | One specimen-catalog Button updates variant, intent, size, loading position, block, disabled, and loading. | Selects for enums; checkboxes for booleans; controls are docs chrome above the rendered result. | Every client input, valid precedence, loading placement; focused control-to-DOM browser check with no console errors. |
| 5. `variants.py` | Choose action emphasis. | Solid, outline, and ghost in one row. | Narrow wrapping. | Variant hierarchy and stable geometry. |
| 6. `intents.py` | Choose semantic color without changing mechanics. | Primary, neutral, success, warn, and danger across representative solid and outline Buttons. | Light and dark inherited schemes. | Intent combinations, contrast, and separation from variant. |
| 7. `sizes_and_layout.py` | Choose target size and full-width layout. | `sm`, `md`, `lg`, and block Buttons. | Narrow container; long label. | Size targets, wrapping, `block`, and no horizontal overflow. |
| 8. `decorations.py` | Add leading, trailing, and icon-only visual content safely. | Start, end, both, and icon-only content with an explicit accessible name. | RTL comparison for logical order. | Slots, no interactive descendants, naming requirement, and direction. |
| 9. `loading_states.py` | Understand pending versus disabled and choose indicator placement. | Start, center, end, custom loading slot, and disabled shown side by side. | Reduced-motion behavior is covered by the shared scenario; no demo controls. | Focus retention contract, visual replacement rules, busy/disabled ARIA, blocked activation, compact loading slot. |
| 10. `native_forms.py` | Use Button as native submitter and reset control. | A field-journal form reports submitter value and resets its input. | In-preview interaction through native `submit` and `reset`. | Types, form attributes, submitter identity, reset, and no custom component event. |
| 11. `theme_customization.py` | Apply public variables to a group and one root. | Day and night garden surfaces with different token overrides and a public part selector. | Explicit light and dark `color-scheme`. | Ancestor/root variables, public selectors, nested schemes, focus color; computed-style browser check. |

The reference records every server input, client input, slot and exact slot-data
shape, event policy, reflected attribute, selector, public variable, and named
interface with stable entry anchors. Visual examples do not use private
`.cui-*` classes or `--_cui-*` variables.

## 20. Open decisions and deferred work

- A delayed pending indicator remains deferred until application evidence
  demonstrates that instant feedback causes harmful flicker.
- Purpose-built icon, toggle, group, and split variants require separate
  specifications rather than polymorphic flags on `CButton`.
- A future global token tier may replace literal component fallbacks while
  preserving every public variable's meaning and precedence.
- Full manual assistive-technology and visual sign-off blocks release, not the
  initial Phase 7 implementation.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
