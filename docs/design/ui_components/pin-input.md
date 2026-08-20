# PinInput component specification

**Status:** ratified for Phase 8 implementation. Reviewed 2026-08-19.

## 1. Purpose and product bar

`CPinInput` captures a short fixed-length token such as a one-time verification
code, access PIN, or recovery code. The public value is always a string. A
numeric-looking code is not a number: leading zeroes remain meaningful and no
locale formatting or arithmetic applies.

```html
<c-CPinInput name="code" label="Verification code" />

<c-CField required>
  <c-slot name="label">Recovery code</c-slot>
  <c-CPinInput c-length="8" type="alphanumeric" name="code" />
</c-CField>

<c-CPinInput value="104729" mask readonly label="Current access code" />
```

The closest native primitive is one text `<input>` with `maxlength`, `pattern`,
`inputmode`, and optional `autocomplete="one-time-code"`. JavaScript adds the
segmented visual presentation while the one native input continues to own
focus, selection, paste, composition, autofill, validation, and submission.

The family is not a password field, arbitrary input mask, segmented account or
phone-number form, number field, or WebOTP client. Those jobs remain native
Input, NumberInput, application composition, or later specialist work.

## 2. Prior art and complaints

The review refreshed current official docs and source on 2026-08-19.

| Product or standard | Version or review date | Evidence inspected | Decision supported |
|---|---|---|---|
| HTML/MDN | 2026-08-19 | `https://developer.mozilla.org/en-US/docs/Web/Security/Authentication/OTP` | one text input, `one-time-code`, numeric input mode, exact pattern |
| WCAG 2.2 | 2026-08-19 | accessible authentication understanding and form-label guidance | preserve paste, password-manager/autofill recognition, and an ordinary accessible name |
| Vuetify | 4.1.6 | `VOtpInput.tsx`, `VOtpField.tsx`, `useOtpInput.ts` | one real input plus visual fields; string value; grapheme-aware selection; IME, RTL, paste, mask, focus methods |
| Base UI | 1.5.0 | OTP Field docs, root source, current release notes | controlled/uncontrolled string, completion and invalid callbacks, normalization, explicit slot labels, form states |
| Ark UI/Zag | current docs | Pin Input docs and changelog | multi-input alternative; input kinds, paste sanitation, completion/invalid callbacks, one-time-code, clear navigation |
| Chakra UI | current docs | Pin Input docs | common count, mask, attached/separated visuals, controlled and Field composition |
| Mantine | current docs | PinInput docs | single string API, forms, regexp filtering, one-time-code, mask |
| PrimeVue | 3.53.1 docs | InputOtp docs | multi-input keyboard/paste precedent and templated separators |
| Ant Design | 6.6.0 docs | Input.OTP docs and changelog | string API, length, separators, display-only mask, completion callback; Windows masking regression risk |

Citry adopts Vuetify's single-input architecture, Base UI's callback detail,
and the shared string-valued controlled contract. It rejects array-valued
public state, a separate real input per slot, automatic form submission,
programmatic WebOTP access, arbitrary regular expressions in browser props,
and string-format callbacks that would split server and browser behavior.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct API | `value` | adopt as one canonical string |
| `length` | direct structural API | `length` | adopt, bounded 1 through 32 |
| `type`, `pattern` | finite direct API | `type` | support numeric, alphabetic, alphanumeric |
| `masked` | direct API | `mask` | display-only masking; submitted value unchanged |
| `placeholder` | direct API | `placeholder` | one grapheme repeated in empty cells |
| `divider`, `merged` | CSS/composition | `attached`; `separator` slot | fixed accessible anatomy, authored visual separators |
| `label` | direct/Field | `label` or `CField` | adopt accessible-name requirement |
| `autofocus` | native input attrs | `input_attrs` | no duplicate convenience prop |
| `finish` | callback | `onComplete` | adopt transition-to-complete semantics |
| focus updates | callback/native events | `onFocusChange`, `@focus`, `@blur` | component callback plus native events |
| `focus()`, `blur()`, `reset()` | method | `focus()`, `blur()`, `clear()` | reset remains native form ownership |
| density/dimensions/colors | theme/CSS/direct | size, variant, variables, classes/styles | capability without broad prop duplication |
| loader | omitted | compose adjacent status | code entry never owns async verification |
| custom field slots | one separator slot | `separator` | preserve one real-input architecture |

## 3. Public composition and anatomy

```text
div pin-input root
├─ input type=text (the only focusable/form control)
└─ div cells (aria-hidden)
   ├─ span cell × length
   │  ├─ span character or placeholder
   │  └─ span fake caret when active and empty
   └─ separator slot output between requested group boundaries
```

`attrs`, `class_`, and `style` land on the root. `input_attrs` lands on the
native input except for owned identity, state, value, validation, selection,
and runtime attributes. `id` identifies the native input and `${id}-root`
identifies the root. The input remains a normal, visible text box without
JavaScript. After activation it is laid over the visual cells with transparent
text and caret, so it remains recognized by browsers, assistive technology,
autofill, and password managers.

The stable parts are `pin-input`, `input`, `cells`, `cell`, `character`,
`caret`, and `separator`. Cells and separators are not controls and are
`aria-hidden` as one presentation subtree.

## 4. Server inputs and client inputs

`CPinInputType` is `"numeric" | "alphabetic" | "alphanumeric"`. Numeric means
ASCII digits `0` through `9`; protocol tokens are not localized numbers.
Alphabetic and alphanumeric likewise use ASCII. Applications accepting a
broader alphabet use ordinary Input until a locale-independent normalization
contract is specified.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | `""` | initial value | accepted characters only, at most `length` graphemes |
| `name`, `form`, `id` | `str \| None` | `None` | structural | native form ownership and identity |
| `length` | `int` | `6` | structural | 1 through 32 visual slots and exact complete length |
| `type` | finite literal | `"numeric"` | structural | accepted character set, pattern, and input mode |
| `required` | `bool \| None` | `None` | reactive configuration | native required validity outside Field |
| `disabled`, `readonly`, `invalid` | `bool \| None` | `None` | reactive configuration | inherited form and interaction state |
| `mask` | `bool` | `False` | reactive configuration | obscures visual cells without changing the value |
| `one_time_code` | `bool` | `True` | structural/native | emits `autocomplete="one-time-code"` unless overridden |
| `placeholder` | one Unicode code point or `None` | `"○"` | server presentation | repeated in empty visual cells; caller-authored text |
| `attached` | `bool` | `False` | styling | joins adjacent cells visually |
| `label` | `str \| None` | `None` | server accessibility | standalone accessible name; Field label wins |
| `size` | `"sm" \| "md" \| "lg"` | `"md"` | reactive styling | cell and text size |
| `variant` | `"outline" \| "subtle"` | `"outline"` | reactive styling | cell surface treatment |
| `class_`, `style`, `attrs` | structured values/mapping | `None` | server styling | merged on root |
| `input_attrs` | mapping | `None` | server attributes | copied to native input except owned attributes |

| Client input | Type | Omitted | Invalid | Affected surfaces |
|---|---|---|---|---|
| `value` | string | uncontrolled | retain/report | input, cells, completion, form value |
| `required`, `disabled`, `readonly`, `invalid`, `mask` | boolean | server/owner | retain/report | native and reflected state |
| `size`, `variant` | finite literal | server value | retain/report | visual style |
| `onValueChange`, `onComplete`, `onValueInvalid`, `onFocusChange` | function | no callback | ignore/report | notifications |

An explicit valid client `value` controls the component. Prop omission releases
it to the last committed uncontrolled value. Structural `length`, `type`,
`one_time_code`, and separator layout require a server render.

## 5. State model

State is the accepted value, current selection/caret, composition draft,
initial reset value, focus, control ownership, and whether completion has been
reported for the current full value.

| Trigger | Guard | Result |
|---|---|---|
| type, autofill, paste, drop | editable | filter by type, clamp to length, request accepted value |
| invalid character | editable | discard character and call `onValueInvalid` once per interaction |
| composition update | editable | retain native draft; commit/filter only at composition end |
| Backspace/Delete/selection replacement | editable | native text-edit semantics; visual slots resync |
| Arrow/Home/End or pointer cell | editable/readonly focusable | move the one native selection/caret in logical slot order |
| accepted value reaches length | any request | call `onComplete` once for that distinct complete value |
| controlled request refused | controlled | restore owner value and selection safely |
| form reset | form owner | request/restore initial value; clear completion latch |
| disable/remove | any | clear focus presentation, listeners, and pending callbacks |

Uncontrolled changes commit before callbacks. Controlled changes are requests;
the owner value remains authoritative. Repeating the same request produces no
value callback. A complete value may complete again only after the value first
becomes incomplete or changes to another complete value.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Data | Fallback |
|---|---|---|---|---|---|
| `CPinInput` | `separator` | no | rendered at declared boundaries | `{index: int}`: after zero-based cell index | none |

The first release exposes a simple `separator_after: tuple[int, ...]` server
input to choose boundaries. Supplying a separator slot without boundaries, a
boundary outside `0..length-2`, or duplicate boundaries is an error. Separator
content is application-authored presentation and is hidden from accessibility;
instructions belong in Field description text.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing and controlled behavior |
|---|---|---|---|
| `onValueChange` | `(str, CPinInputValueChangeDetail)` | accepted user edit or reset | commit first if uncontrolled; request-only if controlled |
| `onComplete` | `(str, CPinInputCompleteDetail)` | transition to a complete accepted value | after the value request/commit; no automatic submit |
| `onValueInvalid` | `(CPinInputInvalidDetail)` | one interaction includes rejected characters | reports rejected plain text and source; never inserts it |
| `onFocusChange` | `(bool, CPinInputFocusChangeDetail)` | native input focus/blur | after reflected focus state changes |

Change detail has `value`, `previousValue`, `controlled`, `source`
(`input`, `paste`, `autofill`, `composition`, or `reset`), and `sourceEvent`.
Completion adds the same source fields. Invalid detail has `value`, `rejected`,
`source`, and `sourceEvent`. Focus detail has `focused` and `sourceEvent`.

The family exposes no wrapper methods. Authors can keep an Alpine `x-ref` on
the native input through `input_attrs` when imperative native `focus()`,
`blur()`, `select()`, or value access is required. Native `input` and `change`
stay available through Alpine listeners; there are no custom DOM events.

## 8. Semantics, keyboard, focus, and assistive technology

The native text input is the only semantic and focusable control. It requires
an accessible name from `CField`, `label`, `aria-label`, or `aria-labelledby`.
The visual cells are one `aria-hidden` presentation group, avoiding repeated
“character N of M” labels and multiple Tab stops.

Tab and Shift+Tab enter and leave once. Normal text editing, selection,
clipboard shortcuts, undo/redo, and mobile input remain native. Left/Right
operate on the input selection; visual active-cell mapping follows logical text
position and CSS logical order in both LTR and RTL. Home/End move to the first
or last available slot. Clicking a cell focuses the input and selects that
slot, clamped to the current insertion point. Disabled is not focusable.
Readonly remains focusable/selectable and submitted.

Masking changes only the visual cells. The real input's rendered glyphs and
selection highlight must not leak through the overlay, including Windows high
contrast. Assistive technology still owns the actual text-field value; mask is
shoulder-surfing mitigation, not a security boundary.

## 9. Native forms and validation

The one native input submits the exact string. Disabled submits nothing;
readonly submits. `required` plus the generated exact-length `pattern` means a
partial token is invalid. `maxlength` limits UTF-16 code units only, so browser
runtime also clamps by accepted characters; ASCII modes make both counts equal.

`form` supports an external native form. A `CForm` owner cannot be redirected.
Reset restores the initial uncontrolled value or requests it from a controlled
owner. Without JavaScript the native input remains usable, labeled, pasteable,
autofillable, validated, and submitted. Citry Events success/error morphs use
the shared Field/Form value-preservation contract.

`one_time_code=True` sets `autocomplete="one-time-code"`; explicit
`input_attrs["autocomplete"]` may choose another valid token. No WebOTP API is
invoked. Paste is never blocked.

## 10. Styling and theme contract

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-pin-input-cell-size` | length | inline/block size | size-dependent |
| `--cui-pin-input-gap` | length | gap between cells | theme spacing |
| `--cui-pin-input-separator-gap` | length | space around separators | theme spacing |
| `--cui-pin-input-border-color` | color | outline cell border | control border token |
| `--cui-pin-input-focus-color` | color | focused cell ring | focus token |
| `--cui-pin-input-invalid-color` | color | invalid border/ring | danger token |
| `--cui-pin-input-background` | color | cell surface | input background |
| `--cui-pin-input-color` | color | character | foreground token |
| `--cui-pin-input-placeholder-color` | color | empty marker | muted token |
| `--cui-pin-input-radius` | length | cell corner radius | control radius |
| `--cui-pin-input-disabled-opacity` | number | disabled treatment | shared opacity |

Selectors follow the stable parts in section 3. Reflected root attributes are
`data-disabled`, `data-readonly`, `data-required`, `data-invalid`,
`data-focused`, `data-complete`, `data-filled`, `data-size`, and
`data-variant`. Cells expose `data-active`, `data-filled`, and `data-masked`.
Private classes and behavior attributes are not public.

## 11. Environmental behavior

Logical properties and DOM order support LTR and RTL; the protocol value input
uses `dir="ltr"` by default so token order does not visually reverse inside an
RTL page, while visual cell order remains first-character first. An explicit
native `dir` override is accepted. ASCII token values are never localized,
case-folded, number-formatted, or direction-transformed.

The component supports light/dark scopes, forced colors, reduced motion, 400%
zoom and reflow, narrow widths with horizontal overflow rather than shrinking
touch targets, coarse pointers, and virtual keyboards. Print shows the
unmasked visual value only when `mask=False`; masked output remains masked.

There are no library-authored visible or accessibility strings. `label`,
placeholder, Field content, and separators belong to the application. Thus the
family owns no FTL messages, `$c-tr`, `i18n.bind()`, format profiles, parsing,
sorting, or matching. This explicit zero-key result still appears in its API
reference translation section.

## 12. Overlay and layering behavior

The family creates no overlay, portal, top-layer element, focus trap, scroll
lock, or outside-interaction policy.

## 13. Collections, async data, and identity

The bounded visual cells are structural presentation, not a public collection.
Indices are stable for one server render. The component performs no async work
and does not own verification, loading, retry, resend, or error copy.

## 14. Server render, morph, and cleanup

Server output is one usable native input followed by presentation cells. Client
activation is idempotent, preserves an in-progress value and selection, and
adds one set of input, selection, composition, focus, pointer, and reset
listeners. Morphing preserves live edits under the shared form-control rule;
controlled props then reconcile. Removal releases listeners and Form/Field
registrations. Late fragments and nested instances remain isolated.

## 15. Security and content trust

Values, labels, placeholders, and separator output use normal escaped Citry
rendering. The token value is browser-visible and present in form data; mask is
not encryption and must not be described as one. Owned identity, value,
pattern, length, state, browser expressions, and runtime attributes cannot be
replaced through general mappings. Callback rejected text is untrusted plain
text. No HTML, URL, remote data, clipboard read, SMS read, or WebOTP permission
is owned.

## 16. Assets and performance

The family adds its component CSS and one self-contained component JavaScript
block, plus existing shared Field/Form runtime dependencies. It uses no icon,
font, observer, timer, network request, or global listener. One document-level
`selectionchange` listener per live instance is avoided; selection is tracked
from the input's `select`, keyboard, pointer, and input events.

The implementation records raw/gzip/Brotli family sizes and the full catalog
headroom. A 32-cell instance must initialize and update within the shared
component interaction budget. Static no-JavaScript output remains useful.

## 17. Acceptance matrix

Automated evidence covers schemas and type stubs; value/length/type validation;
HTML escaping and owned attributes; native form submission, external owner,
required validity, readonly/disabled, reset, no-JavaScript output; controlled
and uncontrolled typing, deletion, replacement, paste, autofill-shaped input,
invalid filtering, completion, callbacks, methods; selection, pointer cells,
masking, Field/Form state, RTL, morph/removal; CSS variables/selectors and
reflections; CSP; axe; docs previews; installed-wheel exports; three-browser
Playwright; and asset budgets.

Manual release evidence covers keyboard-only editing, iOS/Android
`one-time-code` suggestion, VoiceOver/NVDA text-field output, password-manager
recognition, Windows forced-colors masking, 400% zoom, touch targets, and
light/dark visual review. WebOTP itself is not an acceptance surface.

## 18. Compatibility classification

Stable API includes `CPinInput`, its Python/client inputs, callback payloads,
methods, slot data, native form value, public variables/selectors/reflections,
validation errors, and defaults. The one-real-input semantics, one Tab stop,
string value, paste/autofill/no-JavaScript behavior, controlled requests, and
documented relationships are behavioral contracts. Exact colors, spacing,
shadow, and animation are evolvable. Private classes, temporary runtime
attributes, JavaScript organization, and incidental wrappers are private.

## 19. Public documentation contract

`api.md` teaches basic, Field, alphanumeric recovery-code, controlled, masked,
separator, form, locale/RTL, and state use. Planned snippets are `basic`,
`alphanumeric`, `controlled`, `forms`, `masked`, `separator`, `locales`, and
`states`. The quality scenario includes numeric OTP, alphanumeric, partial,
complete, masked, readonly, disabled, invalid, attached, separators, narrow,
dark, and RTL states. Focused browser tests share those fixtures.

`api.yml` exhaustively lists Inputs, Slots, Events, CSS, Attributes,
Selectors, Interfaces, and the final Translation keys section. Stable entry
IDs use the `pin-input-` prefix.

## 20. Open decisions and deferred work

The ratified first release has no implementation-blocking decision. Deferred:
Unicode token alphabets, application normalization callbacks, auto-submit,
WebOTP, custom per-cell renderers, multi-segment semantic input, and headless
parts. Each needs a concrete application and separate security, IME, locale,
and accessibility evidence.

## 21. Internationalization

The family has no Citry-owned translation key. Labels, help/errors,
placeholders, and separators are caller-authored and remain in the caller's
locale. ASCII token strings are opaque identifiers: they are not numbers and
must not be localized or reordered. The final API translation table records
this zero-key contract explicitly rather than omitting the audit.
