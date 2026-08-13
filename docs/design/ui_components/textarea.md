# Citry UI Textarea specification

**Status (2026-08-08): production pass complete; independent implementation
review found no remaining high- or medium-severity issue.** This specification advances one styled
`CTextarea` with a native `<textarea>` root. Auto-grow, counters, adornments,
and rich-text behavior remain separate work.

## 1. Purpose and product bar

`CTextarea` enters and edits multiline plain text inside or outside `CField`.
It keeps native editing, selection, scrolling, form submission, validation,
reset, spelling, direction, and mobile-keyboard behavior while adding the
suite's presentation and client-controlled-value contract.

Common jobs and shortest support paths:

| Job | Shortest template | Python composition | Support path |
|---|---|---|---|
| Enter labelled multiline text | `<c-CField>...<c-CTextarea name="notes" />...</c-CField>` | `CField(slots={"default": CTextarea(name="notes")})` | Field composition |
| Use a standalone control | `<c-CTextarea c-attrs="{'aria-label': 'Notes'}" />` | `CTextarea(attrs={"aria-label": "Notes"})` | native accessible name remains caller-owned |
| Set initial text | `value="..."` | `CTextarea(value="...")` | server default and reset value |
| Control current text in the browser | `$c-props="{ value: draft }"` | same rendered component | client `value` ownership |
| Show more or fewer lines | `rows="6"` | `CTextarea(rows=6)` | direct API; client override also supported |
| Permit manual resizing | `resize="vertical"` | `CTextarea(resize="vertical")` | direct API; `none`, `horizontal`, and `both` supported |
| Configure submission wrapping | `wrap="hard" cols="48"` | `CTextarea(wrap="hard", cols=48)` | native HTML contract |
| Add length and writing hints | `c-attrs="{'maxlength': 500, 'spellcheck': True}"` | `attrs={...}` | native attrs escape path |
| Validate and submit | `required name="report"` | direct API | native successful-control and constraint behavior |
| Change visual treatment | `variant="filled" size="lg"` | direct API | concise suite vocabulary |

Production completeness means native semantics without a wrapper, safe
untrusted initial text, correct newline and reset behavior, browser-owned
uncontrolled editing, IME-safe client control, preserved caret and scroll on
unrelated morphs, Field/Form integration, manual-resize behavior, narrow and
RTL layouts, public theme surfaces, and no observer or auto-size runtime.

Non-goals: rich text, Markdown preview, code editing, syntax highlighting,
mentions, masks, automatic height, character counters, prefix/suffix content,
clear actions, loading state, validation-message generation, or a headless
variant.

## 2. Prior art and complaints

Current source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | `CField`, `CInput`, `CForm`, controlled-value tests, theme contract, component policy | Reuse state ownership, validation relationships, concise variants/sizes, native events, direct root inputs, and client fallback rules. |
| Vuetify | 4.1.8 reviewed 2026-08-08 | [VTextarea source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VTextarea/VTextarea.tsx) and [styles](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VTextarea/VTextarea.sass) | Treat rows, resizing, controlled text, counters, auto-grow, max rows, prefix/suffix, validation, and forwarded attrs as the parity checklist. Adopt the native core and defer the behavior-heavy extras. |
| Material UI | 9.3.1 reviewed 2026-08-08 | [Text Field multiline guide](https://mui.com/material-ui/react-text-field/#multiline), [Textarea Autosize guide](https://mui.com/material-ui/react-textarea-autosize/), and API | Keep the ordinary fixed-height native job separate from auto-size. Preserve controlled/uncontrolled values and native attrs. |
| Chakra UI | 3.36.1 reviewed 2026-08-08 | [Textarea guide](https://chakra-ui.com/docs/components/textarea) and [source](https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui%2Freact%403.36.1/packages/react/src/components/textarea/textarea.tsx) | Confirm native root, `sm`/`md`/`lg`, variants, resize configuration, Field composition, and opt-in auto-resize. |
| Mantine | 9.5.1 reviewed 2026-08-08 | [Textarea guide](https://mantine.dev/core/textarea/) and source | Confirm native form use, controlled/uncontrolled values, variants, sizes, resize, rows, and separate auto-size complexity. Reject wrapper-owned label/error duplication because Citry has `CField`. |
| React Aria | current docs and source reviewed 2026-08-08 | [TextField and TextArea guide](https://react-aria.adobe.com/TextField) | Confirm a native TextArea composed under one Field relationship, with native input events, controlled/uncontrolled text, and caller-owned styling. |
| Web Awesome | 3.11 reviewed 2026-08-08 | [Textarea guide and API](https://webawesome.com/docs/components/textarea/) | Confirm four-row default, vertical resize default, sizes, variants, native hints/constraints, form association, and auto-size as an explicit separate mode. |
| Bootstrap | 5.3.8 reviewed 2026-08-08 | [Form control guide](https://getbootstrap.com/docs/5.3/forms/form-control/) | Confirm a styled native Textarea with rows, sizes, disabled/read-only states, and external label/help composition. |
| HTML | living standard reviewed 2026-08-08 | [`textarea` element](https://html.spec.whatwg.org/multipage/form-elements.html#the-textarea-element) | Freeze child text as default value, LF-normalized API value, dirty-value and reset behavior, positive rows/cols, `soft`/`hard` wrapping, native input events, and successful-control semantics. |

Material complaint disposition:

| Report | Status | Citry consequence |
|---|---|---|
| [Vuetify #21982](https://github.com/vuetifyjs/vuetify/issues/21982), auto-grow overshoots near a wrapping boundary | open, reviewed 2026-08-08 | Do not ship auto-grow until width changes, wrapping boundaries, manual resize, caret, morph, and cleanup have focused evidence. |
| [MUI #42520](https://github.com/mui/material-ui/issues/42520), multiline `minRows` visibly jumps from a small initial height | open, reviewed 2026-08-08 | Keep the first production contract fixed-row and useful before JavaScript. Do not hide an auto-size correction behind hydration. |
| [MUI #46543](https://github.com/mui/material-ui/issues/46543), TextareaAutosize adds a row for a long no-wrap placeholder | open, reviewed 2026-08-08 | Treat placeholder wrapping, white-space, and sizing as coupled auto-grow risks, not ordinary Textarea behavior. |
| [Mantine 9.0.2 release](https://github.com/mantinedev/mantine/releases/tag/9.0.2), Textarea could throw during resize | fixed, reviewed 2026-08-08 | Manual resize stays CSS-native and observer-free. Any future auto-grow owns resize teardown and regression evidence. |
| [Vuetify #20886](https://github.com/vuetifyjs/vuetify/issues/20886), request for a placeholder slot | open, reviewed 2026-08-08 | Keep placeholder plain text. Rich placeholder markup is not native, complicates naming and editing, and belongs outside the control. |

Adopted patterns: native root, four-row default, vertical resize default,
controlled and uncontrolled text, Field composition, native constraints and
events, concise visual inputs, and explicit auto-grow opt-in only after a later
qualification pass.

Rejected patterns: wrapper-owned label/error APIs, a placeholder slot,
automatic trimming, hidden sizing clones, ResizeObserver, prefix/suffix DOM,
counter DOM, and component-authored value-change callbacks that duplicate the
native `input` event.

Vuetify capability disposition:

| Vuetify job or surface | Citry support path | Citry surface | Decision |
|---|---|---|---|
| model value and update | direct API plus native event | Python `value`, client `value`, native `@input` | adopt without inventing `onValueChange` |
| rows | direct API | `rows` server and client input | adopt |
| no-resize | direct API | `resize="none"` | adopt and generalize to four CSS-native modes |
| auto-grow, max rows, max height, row-count event | later behavior contract | none in v1 Textarea | defer as one coupled feature |
| counter and custom counter value | composition or later family | Field description and native `maxlength` today | defer live counter |
| prefix, suffix, inner/outer prepend/append, icons | composition outside native root | Field content or ordinary layout | omit from Textarea |
| clear action | Button composition and consumer event | ordinary controls | omit |
| placeholder and persistent placeholder | native attribute | `placeholder`; no floating label | adopt native job only |
| autocomplete, autofocus, inputmode, spellcheck, enterkeyhint | direct/native attrs | named common inputs plus `attrs` | support without mirroring every HTML attribute |
| trim model modifier | consumer event policy | none | reject automatic data loss and caret rewriting |
| variants, density, color, rounded, dimensions | direct API and CSS | `variant`, `size`, class/style, public variables | consolidate to suite vocabulary |
| focus/click/update events and exposed focus methods | native DOM | Alpine native listeners and DOM APIs | no component events or methods |

## 3. Public composition and anatomy

Smallest labelled template:

```html
<c-CField>
  <c-fill name="label">Forest observation</c-fill>
  <c-CTextarea name="observation" />
</c-CField>
```

Python composition stays explicit about Field slots:

```python
from citry_ui import CField, CTextarea

observation = CField(
    slots={
        "label": "Forest observation",
        "default": CTextarea(name="observation", rows=6),
    },
)
```

`CTextarea` renders exactly one native `<textarea>` and no wrapper. It accepts
no slots or child content because its child text is reserved for the native
default value. The root receives `class_`, `style`, and `attrs`. Inside
`CField`, it registers as the one primary control and receives Field-owned IDs,
relationships, required, disabled, read-only, and invalid state.

Outside `CField`, the caller supplies an accessible name using a native label,
`aria-label`, or `aria-labelledby`. Placeholder never substitutes for a label.

Direct string inputs accept only `None` or a `str` subclass. `Markup` is
accepted because it is a `str`, but its trust is discarded; a non-string
object exposing `__html__` is rejected. Every accepted direct string is first
converted with `plain = "".join(value)` and asserted to have exact type `str`
before template rendering. `str.join` returns a base string for plain strings,
trusted string subclasses, and Citry `Const` string proxies without consulting
`__html__` or a self-returning `__str__` override.

The exact `value` pipeline is: validate `isinstance(value, str)`, convert with
`plain = "".join(value)`, assert `type(plain) is str`, normalize CRLF and CR to LF,
HTML-escape that plain string without consulting the original object's
`__html__`, and prepend one extra LF when the normalized value starts with LF.
The template emits no authored whitespace between the opening tag and encoded
text. HTML strips the extra first LF and preserves the user's original leading
LF. A literal `</textarea>` sequence cannot terminate the element.

## 4. Server inputs and client inputs

Python inputs:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `name` | `str | None` | `None` | structural server-only | non-empty native submitted name; `None` creates the only unnamed-control path |
| `id` | `str | None` | Field ID or generated | structural server-only | non-empty/no-ASCII-whitespace native identity, matching `CInput`, without breaking Field ownership |
| `value` | `str | None` | `None` | initial value | de-trusts `str` subclasses and rejects other `__html__` objects; sets escaped child text, initial current value, and reset default after LF normalization |
| `rows` | positive `int` | `4` | reactive presentation fallback | initial visible line count; client input may override the current `rows` property |
| `cols` | positive `int | None` | `None` | structural server-only | native preferred characters per line and required width for `wrap="hard"`; CSS still owns rendered inline size |
| `wrap` | `soft | hard` | `soft` | structural server-only | controls whether form submission inserts implementation-defined wrapping line feeds; `hard` requires `cols` |
| `required` | `bool | None` | Field value or `False` | standalone reactive fallback | valid only outside `CField` |
| `disabled` | `bool | None` | Field/Form value or `False` | standalone reactive fallback | valid only outside `CField`; disabled Form always wins |
| `readonly` | `bool | None` | Field/Form value or `False` | standalone reactive fallback | valid only outside `CField` |
| `invalid` | `bool | None` | Field value or `False` | standalone external-invalid fallback | combines with native invalidity without creating native invalidity |
| `autocomplete` | `str | None` | `None` | structural server-only | native autofill hint |
| `inputmode` | `str | None` | `None` | structural server-only | native virtual-keyboard hint |
| `placeholder` | `str | None` | `None` | structural server-only | short native hint; never an accessible-name replacement |
| `variant` | `outline | filled | plain` | `outline` | reactive presentation fallback | visual treatment |
| `size` | `sm | md | lg` | `md` | reactive presentation fallback | padding, text size, and minimum line geometry |
| `resize` | `none | vertical | horizontal | both` | `vertical` | reactive presentation fallback | native CSS resize policy; horizontal/both may exceed a narrow container by explicit caller choice |
| `class_` | `CClassValue | None` | `None` | structural server-only | adds classes to the native root |
| `style` | `CStyleValue | None` | `None` | structural server-only | adds inline styles to the native root |
| `attrs` | `Mapping[str, object] | None` | `None` | structural server-only | native constraints, ARIA, data, and trusted Alpine attrs not owned above |

`attrs` is the path for native `minlength`, `maxlength`, `dirname`, `form`,
`autocapitalize`, `autocorrect`, `spellcheck`, `enterkeyhint`, `autofocus`,
event listeners, and other supported global/native attributes. `form` cannot
retarget a Textarea nested in `CForm`.

Client inputs passed through `$c-props`:

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | string | uncontrolled native editing | invalid | log once per invalid episode and retain prior valid ownership/value | normalize CRLF/CR to LF at ingestion, then control current `.value`; not child text or reset default |
| `rows` | positive integer | server fallback | invalid | log once and use server fallback | native `rows` property and attribute |
| `required` | Boolean | server/Field fallback | invalid | log once and use fallback | native state, reflected attr, Field relationships |
| `disabled` | Boolean | server/Field/Form fallback | invalid | same | native state and reflected attr; disabled Form wins |
| `readonly` | Boolean | server/Field/Form fallback | invalid | same | native state and reflected attr |
| `invalid` | Boolean | server/Field fallback | invalid | same | external invalid source, ARIA, Field error visibility |
| `variant` | enum | server fallback | invalid | log once and use fallback | `data-variant` and CSS |
| `size` | enum | server fallback | invalid | same | `data-size` and CSS |
| `resize` | enum | server fallback | invalid | same | `data-resize` and CSS |

When nested in `CField`, client `required`, `disabled`, `readonly`, and
`invalid` values on `CTextarea` are rejected with the same one-per-episode
diagnostic as `CInput`; the Field context owns them. Omitted `value` releases
client ownership immediately and leaves the current DOM value untouched.

## 5. State model

Textarea owns three value concepts:

1. server child text is the native default value and reset target;
2. the browser `.value` is the current LF-normalized editing value; and
3. a valid client `value` prop temporarily controls the current value.

Invariants:

- `None` renders an empty default, not the string `"None"`;
- server values are treated as plain text and normalize CRLF/CR to LF;
- every valid client value also normalizes CRLF/CR to LF before it is stored,
  compared, assigned, or restored;
- uncontrolled typing sets the native dirty-value flag and remains browser-owned;
- an unrelated retained-node morph preserves current value, selection,
  direction, scroll position, focus, and manual resize;
- a changed server default updates child text/defaultValue; a dirty current
  value remains until native reset, while a pristine value follows the default;
- a valid client value wins over server/default/current values;
- client assignments are skipped when the normalized current value already
  matches, preserving caret and scroll;
- native `input` and `compositionend` schedule reconciliation after the whole
  native commit and the consumer's reactive `@input` update have settled;
- reconciliation reads the latest client prop at execution time, applies the
  release/invalid rules, normalizes a valid value to LF, and assigns only when
  it differs from current `.value`;
- a consumer that mirrors `$event.target.value` incurs no assignment or caret
  move, while an unchanged controlled prop restores its immutable value;
- composition is never interrupted. Prop changes are remembered but not
  assigned while composing; committed mirrored IME text or prop replacement is
  resolved from the latest prop after composition ends;
- an effect that sees omitted client `value` releases ownership immediately,
  including during composition, and never assigns the DOM. A later deferred
  reconciliation observes that the prop remains omitted and does nothing;
- native reset clears native-invalid state, then restores the latest server
  default when uncontrolled or the client value when controlled;
- read-only Textarea remains focusable/selectable and is barred from native
  constraint validation; disabled Textarea is not submitted;
- Field owns state when present, and disabled Form always dominates;
- `rows` and `cols` reject Boolean values even though Python `bool` is an `int`;
- `wrap="hard"` without positive `cols` fails before rendering; and
- no behavior measures layout or rewrites height.

## 6. Slots and slot data

`CTextarea.Slots` exists and is empty. Template fills, Python `slots`, and
literal child content are errors. A native Textarea's child text is an initial
value, so the component exposes only `value` and never overloads its default
slot.

There are no dynamic slots.

## 7. Callbacks, native events, and methods

Textarea emits no component-authored events and accepts no callback prop.
Consumers use native Alpine listeners such as `@input`, `@change`, `@focus`,
`@blur`, `@invalid`, `@compositionstart`, and `@compositionend`. This keeps the
event object, `inputType`, composition metadata, selection, and current native
value available without a translated payload.

There are no public methods. Focus, selection ranges, scrolling, validity, and
form APIs remain native DOM methods/properties.

## 8. Semantics, keyboard, focus, and assistive technology

The native `<textarea>` owns multiline edit semantics and platform keyboard
behavior. Citry UI does not add a role, keyboard handler, focus proxy, or
wrapper tab stop.

Required acceptance:

- external labels and `CField` labels activate/focus the native root;
- description and error IDs merge with caller ARIA relationships;
- external-invalid and native-invalid sources update `aria-invalid` without
  replacing native validity;
- required, disabled, and read-only semantics match native HTML;
- placeholder is never the only documented naming path;
- Enter inserts a line feed instead of submitting the Form;
- Tab follows browser behavior and does not insert a tab character;
- selection, shift-selection, clipboard, undo/redo, IME, dictation, spellcheck,
  writing-direction changes, and touch handles remain browser-owned;
- visible focus survives light, dark, forced-colors, and custom themes;
- resize affordances remain discoverable where the platform renders them;
- horizontal/both resize is an explicit overflow opt-in; default vertical
  resize causes no horizontal page overflow at narrow widths; and
- 200%/400% zoom and text-spacing overrides preserve label, control, help, and
  error reading order.

Manual release review includes VoiceOver/Safari, NVDA/Firefox, and
TalkBack/Chrome for label, description, error, required, read-only, invalid,
multiline editing, reset, and dynamic server replacement.

## 9. Native forms and validation

With a non-empty `name`, Textarea is a native successful control. FormData uses the
browser's submission value; API/current values use LF, while form encoding may
normalize line endings per HTML. `wrap="hard"` may insert implementation-
defined line feeds at `cols`; `soft` does not insert wrapping line feeds.

Native `required`, `minlength`, and `maxlength` constraints participate in
submission, subject to HTML's dirty-value rules. `minlength`/`maxlength`
validity is evaluated after user editing; an over- or under-length initial,
server-morphed, or script-controlled value is not promised to set
`tooLong`/`tooShort`. Browsers normally enforce `maxlength` by preventing
further user input. External `invalid=True` changes presentation and ARIA only.
A read-only Textarea is excluded from constraint validation but still submits;
a disabled Textarea does not submit.

`CForm` reset, submit, disabled, and read-only contracts match `CInput`.
Textarea itself owns no Citry `State` or `Events`, so it remains usable in
server-only pages. Citry Events may listen to native `input`/`change` and read
the native value through the established event protocol. A successful server
morph must preserve a dirty retained Textarea unless the application explicitly
replaces its identity or client-controls its value.

## 10. Styling and theme contract

Variants: `outline`, `filled`, `plain`. Sizes: `sm`, `md`, `lg`. Resize modes:
`none`, `vertical`, `horizontal`, `both`. Every combination is supported.

Public variables:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-textarea-background` | color | native root background | `Canvas` |
| `--cui-textarea-foreground` | color | entered text | `CanvasText` |
| `--cui-textarea-border-color` | color | resting border | mixed `CanvasText` |
| `--cui-textarea-hover-border-color` | color | hover border | stronger mixed `CanvasText` |
| `--cui-textarea-focus-color` | color | focus border/outline | `Highlight` |
| `--cui-textarea-invalid-border-color` | color | invalid border | scheme-aware red |
| `--cui-textarea-disabled-background` | color | disabled surface | mixed system colors |
| `--cui-textarea-placeholder-color` | color | placeholder text | muted mixed `CanvasText` |
| `--cui-textarea-radius` | length | corner radius | `0.5rem` |
| `--cui-textarea-inline-padding` | length | inline padding | size-dependent |
| `--cui-textarea-block-padding` | length | block padding | size-dependent |
| `--cui-textarea-font-size` | length | text size | size-dependent |
| `--cui-textarea-line-height` | number or length | editing line height and row geometry | `1.5` |

Public selector:

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="textarea"]` | native editable root and all root inputs | always | exactly one per `CTextarea` |

Public reflected/configuration attributes:

| Attribute | Values | Meaning |
|---|---|---|
| `data-required` | present/absent | effective required state |
| `data-disabled` | present/absent | effective disabled state |
| `data-readonly` | present/absent | effective read-only state |
| `data-invalid` | present/absent | effective external or native invalid state |
| `data-variant` | `outline`, `filled`, `plain` | selected visual treatment |
| `data-size` | `sm`, `md`, `lg` | selected size |
| `data-resize` | `none`, `vertical`, `horizontal`, `both` | effective resize policy |

Default rules live in `citry-ui.theme`, use low-specificity selectors, and
resolve public inherited variables through private fallbacks. Unlayered
consumer CSS and correctly ordered named layers follow the global theme
contract. Tests cover ancestor/root variables, the public selector, class
rules before/after component CSS, variant/size fallback precedence, and both
light and dark brand adaptations as release qualification. Checked-in focused
tests currently prove ancestor variables and the public selector.

## 11. Environmental behavior

Textarea follows surrounding `color-scheme` and uses logical sizing/padding.
Its entered text direction follows native `dir`/`dirname` behavior. The resize
mode names are physical CSS vocabulary because that is what browsers expose;
the default vertical mode works in LTR and RTL without inline overflow.

The native root uses `box-sizing: border-box`, `inline-size: 100%`, and
`min-inline-size: 0`. It does not set a max inline size when horizontal/both
resize is chosen, because that would make the explicit mode ineffective.
Consumers opting into those modes own surrounding overflow.

Forced colors retain a visible border and focus indicator. Reduced motion
adds no special behavior because Textarea has no motion. Print renders current
native text according to browser form-control printing; public docs do not
promise expansion of scrolled-off text. Long unbroken content scrolls inside
the native control rather than widening the default page layout.

Manual profiles cover desktop/mobile, touch handles, virtual keyboards,
autocorrect, spellcheck, autofill, RTL entry, zoom, long lines, many lines,
font loading, and manual resize.

## 12. Overlay and layering behavior

Textarea creates no overlay, containing block, stacking context, or portal.
Native selection handles, spelling UI, and platform editing affordances remain
browser-owned. Consumer overlays compose outside the native root.

Default `resize="vertical"` preserves container inline width. `rows` controls
the initial line count, not a responsive breakpoint. The control can shrink to
its container's available inline size and does not impose a `cols`-derived CSS
width.

`horizontal` and `both` are explicit exceptions and may overflow. Public docs
show them in a bounded scroll-safe fixture and state the tradeoff. `resize`
does not mutate rows or emit events. A retained node preserves browser manual
dimensions through unrelated morphs; changing class/style or replacing
identity may intentionally reset them.

Auto-grow is not a responsive mode in this contract.

## 13. Collections, async data, and identity

Textarea is one native scalar control, not a collection. It has no item keys,
pagination, async loading, empty state, or record identity. Applications place
async status and validation messages in `CField` or ordinary surrounding
content.

Citry component identity decides whether a server update retains or replaces
the native root. A retained root preserves browser editing state; a replaced
root initializes from the new server default.

## 14. Server render, morph, and cleanup

One `$component` behavior attaches to the native root. It injects Field/Form,
tracks native invalidity, applies effective state/presentation, and implements
optional client control of current text and rows. It owns no wrapper and adds
no observer.

Initialization reads the already parsed native current value. It must not
replace a value restored by browser history/autofill when client `value` is
omitted. Controlled assignment occurs only for a valid explicit client value.

The value effect releases ownership immediately when `props.value` is omitted.
Otherwise it normalizes and records a valid explicit client value, but never
assigns while composition is active. Native `input` and
`compositionend` schedule one replaceable deferred reconciliation task. The
task runs after consumer event handlers and their reactive flush, reads
`props.value` again, and then releases, retains a prior valid value for an
invalid prop, or normalizes and applies the latest valid value. It compares
against `.value` before assignment. This ordering is part of the public
controlled-value contract; a microtask that blindly restores a captured stale
value is not conforming.

Listeners: `invalid`, `input`, `change`, `compositionstart`,
`compositionend`, and native Form `reset`. Reconciliation remains one
replaceable task. Every reset event owns an independent bounded task because a
later reset may be canceled while an earlier one is not. Each reset task
checks its own event's final `defaultPrevented` state and reads the latest
controlled value. Cleanup removes all listeners, clears the reconciliation
task and every pending reset task, clears Field native-invalid state, and
removes the private initialized marker.

Citry retains the root when identity is stable. The behavior does not rewrite
child text, selection, scroll, direction, or inline geometry during unrelated
effects. Replacement initializes from the new server default as ordinary HTML.

Failure and recovery follow the same lifecycle:

Python raises before output for invalid types/enums, empty `name`, invalid
non-empty/no-ASCII-whitespace `id`, non-positive rows/cols, `wrap="hard"`
without `cols`, conflicting Field-owned state, conflicting IDs, Form
retargeting, slots/children, owned attrs, and reserved Citry runtime attrs.

Invalid client inputs log once per distinct invalid episode. Invalid `value`
retains its previous valid ownership and LF-normalized controlled value. Every
invalid Boolean, `rows`, `variant`, `size`, or `resize` input uses the current
server/Field/Form fallback rather than caching a prior client override.
Omitting `value` releases ownership; omitting every other input returns to its
current fallback. Invalid `value` never stringifies an object into user text.

If JS is unavailable, server Textarea remains fully editable, labelled,
resizable, validated, submittable, and resettable. Client overrides and
reactive Field state do not apply. No loading or fallback UI is necessary.

## 15. Security and content trust

`value`, placeholder, name, ID, autocomplete, and inputmode are data, not
markup. Every accepted direct string becomes an exact plain `str` before it
reaches interpolation or dynamic attributes. Non-string `__html__` objects are
rejected. Exact conversion uses `"".join(value)`, not `str(value)`, because
Django `SafeString` and other subclasses may return themselves from ordinary
`str()`, while Citry static attributes arrive as `Const` proxies that cannot be
passed to the base `str.__str__` descriptor. The implementation asserts
`type(plain) is str` and must not call Citry or MarkupSafe escaping on the
original trusted object because those APIs honor `__html__`.

The special leading-LF prefix is added only after escaping the complete plain
string. Hostile `Markup("</textarea><script>...")`, quotes, ampersands, bidi
text, and very long values remain native text and never create elements or
attributes. Hostile Markup in every named direct attribute is escaped as data.

`attrs`, `class_`, and `style` follow the established trusted-code boundary.
Owned attributes, `data-citry-*`, `data-cev*`, `data-cid*`, and the private
initialization marker are reserved. Native Alpine event attributes in `attrs`
are intentional trusted executable code.

Textarea performs no HTML sanitization because it accepts no HTML content.
Applications validate length and content on the server regardless of native
constraints.

## 16. Assets and performance

Textarea adds one CSS asset and one component JS asset, each emitted once per
registered concrete class. Each instance owns a bounded listener/effect set
equivalent to `CInput`. It has no hidden clone, measurement loop,
ResizeObserver, MutationObserver, request, recurring timer, icon, font, or
remote dependency. Controlled reconciliation uses one bounded replaceable
task. Reset uses one bounded task per event so independently canceled resets
cannot erase another outcome. Cleanup cancels all of them.

Asset reporting records raw, gzip, and Brotli bytes. Diagnostic scaling records
1, 10, 100, and 1,000 instances without a timing gate. Focused source and
browser tests prove bounded timer ownership and one successful initialization
per checked specimen. Repeated correlated-morph and removal cleanup remain
release qualification. Wheel qualification includes only runtime module files,
not specs, snippets, tests, or reports.

## 17. Acceptance matrix

Checked-in server tests cover schema/defaults; every enum and invalid type;
positive rows/cols and the hard-wrap dependency; Field/Form ownership;
standalone naming, empty names, and malformed IDs; hostile Markup in the value,
name, and placeholder paths; static numeric attributes and a
`Const(Markup)` value; rejected non-string `__html__`; leading-newline values;
root attrs, class/style merging, reserved attrs, native attribute forwarding;
no slots; reflected attributes; zero wrappers; Python composition; and the
exact asset set. Exhaustive safe-string-subclass and `Const` coverage across
every named direct input remains release qualification.

Checked-in focused browser tests cover:

- initial/default/current LF normalization, leading LF, hostile RCDATA and
  named-attribute data, native reset, and the native root;
- synchronous mirrored middle insertion and caret preservation, immutable
  controlled restoration, synthetic composition deferral and mirrored commit,
  and immediate release during composition;
- server fallback after invalid `rows`, `variant`, `size`, and `resize` client
  values, plus native/reflected required, disabled, read-only, and invalid
  states;
- Field relationships, ancestor variable overrides, and the public selector;
  and
- the shared quality scenario's initial and active release/reset states with
  exact initialization count, no console errors, and no serious or critical
  axe findings.

Configured release qualification still covers real correlated morph and
removal cleanup; external Form ownership; FormData and hard wrapping;
uncontrolled undo, selection, and scroll; complete invalid-prop recovery;
class-order and environmental CSS profiles; narrow overflow; and the remaining
cross-browser matrix. Real IME entry remains manual evidence.

Checked-in reset coverage includes same-turn uncanceled then canceled reset,
canceled then uncanceled reset, latest controlled-prop reads, and cleanup of
every pending reset task.

The shared quality route registers axe, Nu HTML, pairwise visual profiles,
asset/scaling tools, and exact wheel inventory. Manual release evidence covers
real resize handles, mobile keyboards, autofill/spellcheck/autocorrect,
assistive technology, 400% zoom, and real-device composition/editing.

## 18. Compatibility classification

1. **Stable public API:** `CTextarea`, aliases, inputs/defaults, no-slot rule,
   Field/Form ownership, native-root anatomy, controlled/uncontrolled phases,
   error behavior, variables, selector, reflected attributes, and event policy.
2. **Evolvable defaults:** exact colors, spacing, radius, and internal JS/CSS
   organization while semantic roles and accessibility floors remain.
3. **Private:** context keys, initialization marker, internal classes/effective
   variables, invalid-episode bookkeeping, timers, and source layout.

Breaking changes include adding a wrapper, changing native/default value
semantics, changing resize/rows defaults, changing Field ownership, adding a
component callback that competes with native input, or repurposing a public
variable/selector/attribute.

## 19. Public documentation contract

`ctextarea/api.md` is the reader-first guide and `api.yml` is the exhaustive
structured reference. The page uses one forest field-journal theme. It teaches
the complete labelled control first, then ordinary composition, rows/resize,
variants/sizes, form states and validation, controlled text, native newline and
wrapping behavior, direction/content, customization, and the auto-grow boundary.

Example catalog:

| Order and module | Reader task | Visible behavior | Controls/environment | Contract evidence |
|---|---|---|---|---|
| 1. `at_a_glance.py` | Record a woodland observation | entered multiline text plus visible invalid Field | narrow and dark smoke | first impression, labels, editing, focus, error relationship |
| 2. `compose_textarea.py` | Build labelled and standalone Textareas | generated Field relation and explicit standalone name | no controls | template/Python composition, native root, optional name |
| 3. `rows_and_resize.py` | Choose initial lines and manual resize | rows and four resize modes update immediately | rows slider, resize select; controls outside rendered fixture | server/client rows and resize, geometry, explicit overflow tradeoff |
| 4. `variants.py` | Choose presentation | outline, filled, plain | light/dark | variant fallback and identical native behavior |
| 5. `sizes.py` | Choose editing density | sm, md, lg with same rows | long text and narrow wrap | padding/font/line geometry |
| 6. `field_states.py` | Compare form states | required, disabled, read-only, external/native invalid | Form-disabled toggle | Field/Form ownership, ARIA, focus and submission distinctions |
| 7. `validation_and_forms.py` | Submit and reset a habitat report | required/minlength failures, maxlength enforcement, multiline FormData, reset | real submit/reset | native dirty-value constraints, server/client overlength non-guarantee, line breaks, successful-control behavior |
| 8. `controlled_values.py` | Control, release, and reacquire a draft | edit, replace, compose, preserve caret/scroll, reset | owner controls in preview | controlled phases and IME safety |
| 9. `native_text.py` | Configure plain-text submission | leading/blank lines, soft/hard wrap, spelling and mobile hints | fixed cols and long lines | LF/default/current values, native attrs, escaped hostile-looking text |
| 10. `direction_and_content.py` | Write long LTR and RTL notes | Arabic and English, long tokens, many lines | narrow/zoom | logical layout, internal scrolling, direction |
| 11. `theme_customization.py` | Brand two field journals | fern-light and charcoal-dark treatments | forced colors | every public variable/selector, two distinct brands |

Build discovery and rendering validate all eleven component-owned examples.
Focused docs browser checks cover the sampler, configurator, native Form/reset,
controlled release/reacquire, and theme examples with no console errors. The
shared quality route owns automated axe evidence; the remaining example-by-
example browser and visual sweep stays release polish. Every example avoids
private surfaces and appears before the generated API reference. Controls are
collapsible and visually separate from the rendered fixture.

## 20. Open decisions and deferred work

- Auto-grow remains a separate spike and production amendment. It must cover
  hidden measurement, placeholder wrapping, font/width changes, min/max rows,
  caret and scroll, browser manual resize, morph/reconnect, observer cleanup,
  no-JS layout, and the cited open complaints before joining `CTextarea`.
- A live character counter remains separate. Native `maxlength` works today;
  a counter needs update timing, localization, accessible announcement, custom
  counting, and Field layout decisions.
- Prefix/suffix content, clear actions, loading indicators, and bottom sections
  remain Field or ordinary layout composition until repeated applications prove
  stable Textarea-owned anatomy.
- Rich text, Markdown editors, code editors, mentions, and domain-heavy writing
  tools remain companion packages.
- Full manual assistive-technology, mobile, autofill, spellcheck, dictation,
  and visual sign-off blocks release, not implementation of the automated slice.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
