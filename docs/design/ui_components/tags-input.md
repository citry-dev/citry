# Tags input (`CTagsInput`)

**Status:** implemented and independently reviewed, 2026-08-11.

## 1. Purpose and product bar

`CTagsInput` lets a person create, inspect, and remove an ordered list of
free-form strings inside one Field-compatible control. It is for jobs such as
email aliases, search terms, labels, and routing keys where the application
does not own a suggestion collection.

The production bar is styled use without utility CSS, keyboard and touch
operation, persistent editor focus, ordered repeated native form values,
independent controlled value and draft axes, safe IME and paste behavior,
Field ownership, reset and external-form support, server morph survival, and
light, dark, RTL, narrow, forced-colors, and print behavior.

The closest native substrate is `<select multiple>` for ordered repeated form
entries and native required validity. The visible interaction has no complete
native or APG pattern. It is an ordinary text input followed by component-owned
token visuals, not a listbox, grid, combobox, or toolbar.

Common jobs and shortest paths:

| Job | Template expression | Python expression | Path |
|---|---|---|---|
| Free-form labels | `<c-CTagsInput name="labels" c-input_attrs="{'aria-label': 'Labels'}" />` | `CTagsInput(name="labels", input_attrs={"aria-label": "Labels"})` | direct API |
| Required field | `<c-CField required>...<c-CTagsInput name="labels" />...</c-CField>` | `CField(required=True, slots={"label": "Labels", "default": CTagsInput(name="labels")})` | Field composition |
| Initial ordered values | `<c-CTagsInput :value='["red", "blue"]' c-input_attrs="{'aria-label': 'Colors'}" />` | `CTagsInput(value=("red", "blue"), input_attrs={"aria-label": "Colors"})` | direct API |
| Controlled tags and draft | `$c-props="{ value, inputValue, onValueChange, onInputValueChange }"` | client state after server render | direct client API |
| Fixed choices | `<c-CMultiSelect>...</c-CMultiSelect>` | `CMultiSelect(...)` | separate component |
| Suggestions or remote search | none | none | future `CCombobox`, unsupported here |
| Display-only tags | `<c-CTagGroup>...</c-CTagGroup>` | `CTagGroup(...)` | separate component |

V1 does not include suggestions, remote collections, rich or slotted tokens,
drag reorder, inline tag editing, per-tag metadata, headless primitives, or
blur-to-add. Arbitrary reorder remains an owner operation on controlled
`value`. There is no public declaration child and no public headless API.

## 2. Prior art and complaints

Current evidence was reviewed on 2026-08-11. Version means the exact docs or
public source snapshot used, not an assumed transitive package version.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| HTML Living Standard | 2026-08-11 | [form infrastructure](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html), [select and option](https://html.spec.whatwg.org/multipage/form-elements.html), [input](https://html.spec.whatwg.org/multipage/input.html) | ordered successful controls, form owner, required select, reset, readonly |
| UI Events | 2026-08-11 | [composition and key events](https://www.w3.org/TR/uievents/) | composition guards and event ordering |
| Input Events Level 2 | 2026-08-11 | [input types and paste](https://www.w3.org/TR/input-events-2/) | post-composition input and paste handling |
| Zag Tags Input | 1.43.0 | [docs](https://zagjs.com/components/react/tags-input), [tagged connection source](https://github.com/chakra-ui/zag/blob/%40zag-js%2Ftags-input%401.43.0/packages/machines/tags-input/src/tags-input.connect.ts) | independent value/draft, editor focus, paste, max, announcements |
| Ark UI Tags Input | 5.38.1 | [docs](https://ark-ui.com/docs/components/tags-input) | anatomy, Field use, controlled axes, readonly, validation |
| Chakra UI Tags Input | 3.36.1 | [docs](https://chakra-ui.com/docs/components/tags-input) | styled variants, Field use, paste and controlled examples |
| Mantine TagsInput | 9.5.1 | [docs](https://mantine.dev/core/tags-input/), [source](https://github.com/mantinedev/mantine/blob/9.5.1/packages/%40mantine/core/src/components/TagsInput/TagsInput.tsx) | free values distinct from MultiSelect, search draft, split characters, IME guard |
| Reka UI Tags Input | 2.10.3 | [docs](https://reka-ui.com/docs/components/tags-input), [source](https://github.com/unovue/reka-ui/blob/v2.10.3/packages/core/src/TagsInput/TagsInputRoot.vue) | Vue controlled state, keyboard, max, clipboard, duplicate policy |
| React Aria TagGroup | 1.20.0 | [docs](https://react-spectrum.adobe.com/react-aria/TagGroup.html) | removal and focus prior art only; not an editable tags input |
| Vuetify VCombobox | 4.1.8 | [tagged source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VCombobox/VCombobox.tsx) | broader multiple custom-value job, deliberately not copied |
| Citry Field, MultiSelect, Tag | current workspace | `field-input.md`, `multi-select.md`, `tag.md`, runtime and focused tests | Field ownership, native proxy precedent, family boundary |

Citry adopts separate value and draft ownership, persistent editor focus,
atomic paste, polite announcements, and max/duplicate rejection. It rejects
Zag and Mantine's single delimiter-joined hidden form value because Citry
promises repeated entries. It rejects silent deduplication, partial paste,
blur commit, a popup collection, and editable tags.

A disposable Playwright 1.62.0 proof used Chromium 151.0.7922.34, Firefox
153.0, and WebKit 26.5. In every engine a required multiple select with one
selected option per tag produced `FormData.getAll(name) == ["alpha", "beta"]`
in option order, reported `valueMissing` when empty, followed external `form`
ownership, and allowed `invalid` to redirect focus to the editor. Reset
listeners observed pre-default state and a microtask observed restored state.
Removing an original option proved that native reset cannot resurrect it.
Readonly repeated hidden inputs submitted both values; disabled state
submitted none; canceled reset preserved values and draft. The proof was an
inline stdin harness and left no workspace artifact.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| Multiple free custom values | direct API | `CTagsInput.value` | adopt the job without collection machinery |
| Search text | direct API | `inputValue` | independent draft axis |
| Items, filtering, remote loading | separate component | future `CCombobox` | omitted from V1 |
| Fixed multiple choices | separate component | `CMultiSelect` | do not overload TagsInput |
| Chips | owned rendering | private tag visuals | no public rich token slot |
| Clearable | native editing/composition | select all draft or remove tags | no extra clear prop in V1 |
| Validation and messages | Field plus native form | `CField`, proxy validity, callbacks | capability parity, not prop parity |
| Density and appearance | direct API and CSS | `size`, `variant`, variables | smaller intentional surface |
| Reorder or inline edit | omitted | none | outside boundary |

## 3. Public composition and anatomy

Minimal template:

```citry-html
<c-CField required>
  <c-fill name="label">Routing labels</c-fill>
  <c-fill name="default">
    <c-CTagsInput name="labels" :value='["urgent", "billing"]' />
  </c-fill>
  <c-fill name="description">
    Press Enter or comma to add a label.
  </c-fill>
</c-CField>
```

Minimal Python composition:

```python
from citry_ui import CField, CTagsInput

CField(
    required=True,
    slots={
        "label": "Routing labels",
        "default": CTagsInput(name="labels", value=("urgent", "billing")),
        "description": "Press Enter or comma to add a label.",
    },
)
```

Stable anatomy:

```text
div[root]
├── select[native proxy][multiple]
│   └── option[selected] × effective value count
├── div[control]
│   ├── span[tag-list]
│   │   └── span[tag] × effective value count
│   │       ├── span[tag-label]
│   │       └── button[remove][type=button][tabindex=-1]
│   └── input[input][type=text]
├── span[readonly-values, private]
│   └── input[type=hidden] × effective value count
└── span[status][role=status][aria-live=polite]
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CTagsInput` | `div` | `class_`, `style`, and `attrs` merge on root; `input_attrs` lands on editor | proxy/editor exchange the public control ID by mode; editor is always the sole Field control; tags and options have identical order |

Let `P` be the supplied `id`, Field `control_id`, or generated stable public
control ID; `E = P + "-input"`; and `N = P + "-native"`. Identity is
mode-dependent and one correlated set:

| Mode | Proxy ID | Editor ID | Field label `for` | Visible/focus target |
|---|---|---|---|---|
| SSR, no JavaScript, passive invalid, or fail-closed | `P` | `E` | `P` | native proxy |
| successfully initialized | `N` | `P` | unchanged `P` | visible editor |

The hidden editor always bears the sole `data-citry-field-control` marker, so
the CField client controller registers that exact node before any ID exchange.
Changing its ID never changes the marker or Field capability generation. Both
proxy and editor receive Field `aria-labelledby` and `aria-describedby`
relationships; standalone's required static `aria-label` is copied to both.
After successful initialization, proxy invalid focus redirects to the editor.

Inside `CField`, `CTagsInput.id` must be absent or exactly equal to the Field's
`control_id`; a conflicting ID raises `ValueError`. The editor receives that
public ID only in initialized mode, plus the persistent Field marker,
accessible name, descriptions, error relationship, and `aria-invalid`. Field
`required` configures native `required` only on the select proxy, never on the
unnamed editor; the editor instead reflects effective requiredness through the
component-owned `aria-required="true"`, removed when false. Field `readonly`
activates the readonly proxy/hidden transport matrix; the editor also receives
native `readOnly` only as its input interaction guard, not as the form-validity
substrate. Field `disabled` disables both proxy and editor and removes all
successful controls.

The component owns every child. There are no declaration children or public
slots. Unknown children are rejected server-side. Consumers may rely on the
listed parts and relationships, not incidental wrappers. The implementation
may reuse private Tag presentation helpers, but it must not instantiate
`CTag`, `CTagGroup`, or their grid/removal state.

## 4. Server inputs and client inputs

Python inputs appear in this order:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `name` | `str | None` | `None` | structural | nonempty HTML name or nonparticipant |
| `form` | `str | None` | `None` | structural | nonempty form ID; forwarded to proxy and readonly hidden inputs |
| `id` | `str | None` | generated | structural | valid nonempty public ID `P`; destinations exchange by section 3 mode |
| `value` | `Sequence[str]` | `()` | initial value | canonical unique strings in order; copied immutably |
| `input_value` | `str` | `""` | initial draft | raw string without NUL, CR, or LF; not trimmed |
| `required` | `bool | None` | `None` | reactive config | standalone only; Field owns it when nested |
| `disabled` | `bool | None` | `None` | reactive config | standalone only; Field owns it when nested |
| `readonly` | `bool | None` | `None` | reactive config | standalone only; Field owns it when nested |
| `invalid` | `bool | None` | `None` | reactive config | visual/server invalidity; Field owns it when nested |
| `placeholder` | `str | None` | `None` | reactive config | editor placeholder |
| `delimiters` | `Sequence[str]` | `(",",)` | structural server-only | unique single Unicode scalars; no whitespace, controls, CR, LF, or NUL |
| `max_tags` | `int | None` | `None` | reactive config | positive integer; initial value may not exceed it |
| `autocomplete` | `str | None` | `None` | reactive config | editor hint |
| `inputmode` | `str | None` | `None` | reactive config | editor hint |
| `variant` | `CTagsInputVariant` | `"outline"` | reactive presentation | `outline`, `filled`, or `plain` |
| `size` | `CTagsInputSize` | `"md"` | reactive presentation | `sm`, `md`, or `lg` |
| `messages` | `CTagsInputMessages | None` | English defaults | structural localization | validated text templates from the exact placeholder allowlist below |
| `class_` | structured class value | `None` | styling | merges on root |
| `style` | structured style value | `None` | styling | merges on root |
| `attrs` | attribute mapping | `None` | root destination | filtered by section 15 |
| `input_attrs` | attribute mapping | `None` | editor destination | filtered by section 15 |

Server values must already be canonical: normalize CRLF/CR to LF, reject LF
and NUL, trim HTML ASCII whitespace at both ends, then require that the result
equals the supplied string. Values containing a delimiter are rejected.
Duplicates use exact code-point, case-sensitive equality after this check.
`"Tag"` and `"tag"` are distinct. Invalid server data raises `ValueError`; it
is never silently trimmed or deduplicated.

`CTagsInputMessages` contains `remove_label`, `added_message`,
`removed_message`, `selected_message`, `duplicate_message`, `maximum_message`,
`empty_message`, `invalid_message`, and `uncommitted_message`. Each must be a
nonempty plain string. `remove_label`, `added_message`, `removed_message`,
`selected_message`, and `duplicate_message` accept exactly `{value}`;
`maximum_message` accepts exactly `{max}`; the remaining three accept no
placeholder. Required placeholders must occur at least once. Unknown,
conversion, format, and attribute placeholders are rejected. Substitution
creates text, never HTML. Defaults are `Remove {value}`, `Added {value}`,
`Removed {value}`, `Selected {value}`, `{value} is already added`,
`Add at most {max} tags`, `Tags cannot be empty`, `That tag is invalid`, and
`Add or clear the unfinished tag before submitting`.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | `string[]` | release to latest committed baseline | release | retain prior mode/value; one diagnostic episode | tags, proxy, hidden inputs |
| `inputValue` | `string` | release to latest committed draft | release | retain prior mode/value; one diagnostic episode | editor and draft validity |
| `placeholder` | string | server value | release to server value | retain prior value; one diagnostic episode | editor placeholder; empty string removes visible copy |
| `autocomplete` | string | server value | release to server value | retain prior value; one diagnostic episode | editor native attribute; empty string removes attribute |
| `inputmode` | string | server value | release to server value | retain prior value; one diagnostic episode | editor native attribute; empty string removes attribute |
| `required` | boolean | server/Field value | remove override | retain prior value | proxy, reflections |
| `disabled` | boolean | server/Field value | remove override | retain prior value | editor, remove actions, form participation |
| `readonly` | boolean | server/Field value | remove override | retain prior value | editor, remove actions, proxy/hidden transport |
| `invalid` | boolean | server/Field value | remove override | retain prior value | ARIA and styling |
| `maxTags` | positive integer | server value | no maximum | retain prior value | addition guard and reflection |
| `variant` | variant literal | server value | server value | retain prior value | root reflection |
| `size` | size literal | server value | server value | retain prior value | root reflection |
| `onValueChange` | function | no callback | no callback | ignore and diagnose | component notification |
| `onInputValueChange` | function | no callback | no callback | ignore and diagnose | component notification |
| `onValueInvalid` | function | no callback | no callback | ignore and diagnose | rejected request notification |

Inside `CField`, client and Python `required`, `disabled`, `readonly`, and
`invalid` on `CTagsInput` are rejected; configure the Field. Python conflicts
raise `ValueError`; browser conflicts are ignored with one diagnostic episode
while Field state remains authoritative. Client values win
per axis while supplied. Each controlled axis retains its latest uncontrolled
committed baseline separately; omitted or `null` releases to that retained
baseline, not to the last controlled value. A later server baseline change
updates the retained baseline without replacing a still-controlled effective
axis. Mirrors such as `data-empty` are outputs and cannot be used as inputs.
Nested instances isolate all state and registrations.

Public exports are exactly `CTagsInput`, `CTagsInputMessages`,
`CTagsInputVariant`, `CTagsInputSize`, `CTagsInputChangeSource`,
`CTagsInputInvalidReason`, `CTagsInputValueChangeDetail`,
`CTagsInputInputValueChangeDetail`, and `CTagsInputInvalidDetail`. The family
and package `__all__` contain exactly those nine names. Parser records,
controllers, render helpers, and reset registries remain private.

## 5. State model

The two owner axes are independent:

- effective value is an ordered tuple of canonical strings;
- draft is the editor's raw string;
- an optional visually active tag is identified by its unique value;
- composition, focus, native validity, and pending controlled acceptance are
  internal state.

Uncontrolled additions commit synchronously. Controlled additions are
requests: visual tags, proxy options, hidden values, and announcements remain
at the supplied effective value until the owner accepts.

Each commit attempt snapshots effective value, raw draft, selection, draft
generation, candidate batch, callbacks, and controlled modes. The whole batch
is validated before change. `onValueChange(next, detail)` runs first. Draft
clearing is allowed only after an effective-value edge exactly equal to that
request and only while the draft generation is unchanged.

The acceptance matrix is exact:

| Value axis | Draft axis | Accepted value behavior | Rejected value behavior |
|---|---|---|---|
| uncontrolled | uncontrolled | commit value, notify, clear/set trailing draft, notify | no mutation; one invalid callback |
| uncontrolled | controlled | commit and notify value, then request draft change; displayed draft remains owner value until accepted | value validation failure leaves both axes |
| controlled | uncontrolled | request value; on exact later acceptance clear/set draft and notify if generation still matches | preserve raw draft; no proxy/tag change or added announcement |
| controlled | controlled | request value first; request draft only after exact value acceptance unless owner already changed draft | preserve both owner values; no stale draft request |

Client `value` uses the same canonical, duplicate, delimiter, and string checks
as server value. Client `inputValue` rejects NUL, CR, and LF. A changed client
value that exceeds the already-effective max is invalid; lowering `maxTags`
below an unchanged effective value is allowed and blocks only later additions.
When one update changes both, validate value against the proposed max, except
that an unchanged prior value remains allowed under a lower max.

For an ordinary editor `input` without a tokenizing delimiter, an uncontrolled
draft commits the browser value before `onInputValueChange`. A controlled draft
calls the callback with the browser value and then, after the connected-root
and generation checks, restores the latest supplied value in the same task.
During composition it records the request but performs no restoration until
the final post-composition reconciliation. Tokenizing input does not first
notify the transient delimiter-containing draft; it runs the value transaction
and only its accepted trailing-draft transition.

The value detail includes `source`, `added`, `removed`, `candidates`,
`previousValue`, and `nextInputValue`, so an owner can accept both axes in one
update. If a value callback changes controlled draft, that owner change is
authoritative and cancels the pending draft request. Any editor input, newer
transaction, reset, morph replacement, disable/readonly transition, cleanup,
or incompatible server baseline increments the draft generation and cancels
the pending transition. Repeated same supplied values do not manufacture an
acceptance edge.

Disabled or readonly state exits silently before a transaction begins. Active
addition guards then run in this order: composition, canonical form, empty,
delimiter occurrence, exact duplicate against current values and the batch,
then `maxTags`. Lowering max below the current count never removes tags; it
sets `data-at-max` and blocks additions. Removal remains allowed.

Disabled blocks editor, pointer, keyboard, callbacks, validation, and form
entries. Readonly keeps the editor focusable but blocks edits and removal and
submits committed values through hidden inputs. A dynamic readonly transition
preserves the raw draft as dormant state and displays it; because the user
cannot resolve it, dormant readonly draft does not block submission and is
never submitted. Leaving readonly restores editable draft validation. At max,
the editor stays editable so the person can correct or replace the draft.

TagsInput has no loading, async, or pending state. Server validation error is
the effective Field/`invalid` state and does not replace value or draft.

An enabled, editable, nonempty draft is unfinished data. It sets custom
validity on the native proxy with `uncommitted_message`, even when committed
tags satisfy `required`. This prevents ordinary submission from silently
omitting draft text. The component never auto-commits on submit because a
controlled owner cannot accept synchronously. Disabled and readonly controls
are explicitly exempt because their drafts are not interactive; only their
committed transport participates according to section 9.

## 6. Slots and slot data

There are no public slots, children, item declarations, or render callbacks.
This is deliberate: free-form `str[]` needs no collection declarations, and
rich token content would introduce trust, focus, naming, and identity surfaces
outside V1.

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CTagsInput` | none | no | zero | none | component-owned tags, editor, proxy, and status |

Passing ordinary children, dynamic slot names, or `slots=` raises a clear
server error. Styling uses parts and variables rather than markup replacement.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(nextValue, CTagsInputValueChangeDetail)` | valid add/remove; controlled reset request only | synchronous after full validation, before any draft request | request only on controlled axis; uncontrolled reset is silent | return value ignored |
| `onInputValueChange` | `(nextDraft, CTagsInputInputValueChangeDetail)` | user input, accepted clear/trailing draft; controlled reset request only | synchronous for direct input; acceptance-gated for commit | request only on controlled axis; uncontrolled reset is silent | return value ignored |
| `onValueInvalid` | `(reason, CTagsInputInvalidDetail)` | enabled/editable candidate rejected by empty, duplicate, maximum, delimiter, or invalid-value guard | once per attempted transaction | does not mutate either axis | return value ignored |

`CTagsInputChangeSource` is exactly `"input" | "enter" | "delimiter" |
"paste" | "backspace" | "delete" | "remove" | "reset"`. `input` reaches
draft details; `enter`, `delimiter`, and `paste` reach add details;
`backspace`, `delete`, and `remove` reach removal details; `reset` reaches only
controlled reset-request details. Morph handoff is silent and has no source.
`CTagsInputInvalidReason` is exactly `"empty" | "duplicate" | "maximum" |
"delimiter" | "invalid-value"`. Disabled and readonly interaction is ignored
without callbacks. Native required and unfinished-draft validity do not call
`onValueInvalid`. Invalid external client inputs use the shared diagnostic
channel rather than this callback.

Details are immutable plain records. `CTagsInputValueChangeDetail` fields are
`source: CTagsInputChangeSource`, `added: tuple[str, ...]`,
`removed: tuple[str, ...]`, `candidates: tuple[str, ...]`,
`previous_value: tuple[str, ...]`, `next_input_value: str`, and
`controlled: bool`. `CTagsInputInputValueChangeDetail` fields are
`source: CTagsInputChangeSource`, `previous_value: str`, `next_value: str`,
`controlled: bool`, and `composing: bool`. `CTagsInputInvalidDetail` fields are
`source: CTagsInputChangeSource`, `candidate: str | None`,
`candidates: tuple[str, ...]`, `value: tuple[str, ...]`, `input_value: str`,
`max_tags: int | None`, and `controlled: bool`. Browser callback objects expose
camelCase spellings for record fields.

Uncontrolled effective value commits update proxy/hidden transport, then call
the component callback. Before native proxy events or any draft request, the
controller rechecks the root is connected and the captured value/draft
generations still match. It then dispatches native bubbling `input` and
`change` on the proxy. Controlled requests dispatch no native change event.
Native editor
`input`, `change`, `focus`, `blur`, `paste`, and key events remain observable
with Alpine `@...`. No custom DOM event is dispatched.

There are no public methods. The editor is reachable through ordinary refs and
the Field label; state changes use `$c-props`.

## 8. Semantics, keyboard, focus, and assistive technology

The initialized editor is a native `input type=text`, the sole sequential Tab
stop, and the Field control. Root, tag list, and tags have no widget role.
Remove controls are native `button type=button`, named from `remove_label`, and
have `tabindex=-1`; they remain pointer and touch operable. DOM focus remains
on the editor while a tag is visually active.

Inside a Field, its label or its documented explicit accessible-name path must
name the editor. Standalone use requires exactly one nonempty static
`aria-label` in `input_attrs`; after Unicode White_Space removal it must retain
at least one non-whitespace code point and must not contain NUL, CR, or LF,
otherwise server render raises `ValueError`.
Consumer-authored `aria-labelledby`, including a missing ID, a later-created
ID, or a dynamic binding, is rejected server-side. Use `CField` when a visible
or external naming element is required. Field's own generated
`aria-labelledby` remains internal and is mirrored to the proxy. The server,
template, and destination-security suites must prove missing-ID and dynamic-ID
attempts fail rather than initializing an unnamed control.

Effective requiredness always remains native only on the proxy, but the
visible editor mirrors it for accessibility with component-owned
`aria-required="true"` and removes the attribute when false. This mirror
follows standalone Python/client state and CField state in the same reconcile;
it is not a consumer-writable constraint. Browser AX snapshots must expose
required on the initialized editor and no required state after release/false,
for both standalone and Field composition.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| composing | Enter, delimiter, Backspace, Delete | no tag action | editor unchanged | no |
| draft nonempty | Enter | validate and request/commit one canonical tag | editor | yes, whether accepted or rejected |
| draft empty, no candidate | Enter | ordinary implicit form submission | browser default | no |
| input produces terminal delimiter | non-composing `input` | transact complete fragments and trailing draft | editor | input already occurred; reconcile |
| paste contains delimiter/newline | paste | atomic transaction from would-be selected-text replacement | editor | yes |
| caret at start, no selection | Backspace | first press activates last tag; second removes it | editor | yes when acting on tag |
| tag active | Delete | remove active tag | editor | yes |
| caret at start, no selection | physical Left in LTR / Right in RTL | activate previous or last tag | editor | yes |
| tag active | opposite physical arrow | advance; beyond edge clears active tag | editor | yes |
| tag active | Home / End | activate first / last tag | editor | yes |
| tag active | Escape or printable input | clear active tag | editor | Escape yes; printable no |
| remove pointer/touch | activation | remove named tag | editor restored without scroll | button default contained |
| Tab / Shift+Tab | navigation | leave component | next/previous page stop | no |

Selection-aware arrow behavior runs only at the logical draft boundary: caret
at index zero with no selection. Physical arrows invert in RTL so movement
matches the visual row. After Backspace removal activate the previous tag, then
the next if none. After Delete removal activate the next tag, then the previous
if none. When no tag survives, clear activation.

The persistent `role=status aria-live=polite aria-atomic=true` node announces
only effective accepted additions/removals, active-tag movement, and rejected
transactions. A controlled request that is not accepted never announces
addition/removal. A batch announces one sentence per effective value in order.
Status text is cleared on the next distinct interaction, not by replacing the
live-region node.

Composition is guarded by both a local composition latch and
`event.isComposing`, with legacy key code 229 as defense. A delimiter that is
present in final composition text is reconciled by one replaceable microtask:
`compositionend` schedules it and a following non-composing `input` replaces
it, so engines that order final input before or after `compositionend` process
the final editor value exactly once. Keydown alone never commits. A supported
correlated morph must retain the exact editor node during composition. The
cross-engine falsifier records the node before morph, asserts
`before === after`, then
dispatches the final `compositionend` and input and proves one reconciliation.
If Citry morph cannot preserve that keyed node, implementation stops and this
design reopens; the component does not claim an unproven replacement deferral.

## 9. Native forms and validation

The form substrate is one `<select multiple>` with one selected option for
each effective tag in the same order. Its `name`, `form`, `required`,
and `disabled` are native. It owns public ID `P` in SSR/fail-closed mode and
derived ID `N` after successful initialization, as section 3 defines.
`FormData.getAll` therefore returns repeated values in tag order. The editor
is always unnamed and never receives native `required`.

| State | Proxy | Hidden values | Submitted entries | Validation |
|---|---|---|---|---|
| enabled/editable | named, enabled, required as configured | none | one per effective tag | native `valueMissing`; custom unfinished-draft error |
| readonly | unnamed and disabled | named, one per effective tag | one per committed tag | barred, matching readonly semantics |
| disabled | disabled | none | none | barred |
| no `name` | enabled but unnamed | none | none | required and draft validity still apply |

Native constraint truth and visible invalid state are separate. The component
updates proxy options, `required`, and custom validity immediately, but tracks
an internal `nativeInvalidRevealed` latch. Effective visible invalidity is
`serverOrFieldInvalid || nativeInvalidRevealed`; only that value controls root
`data-invalid` plus editor/proxy `aria-invalid`. The transition contract is:

| Trigger | Proxy validity | `nativeInvalidRevealed` and Field | Status/error result |
|---|---|---|---|
| initialization or ordinary draft edit | set `uncommitted_message` iff enabled, editable draft is nonempty; native `valueMissing` remains independent | false; call `field.setNativeInvalid(false)` after an edit | ordinary typing alone does not expose invalid styling or Field error |
| rejected explicit Enter/delimiter/paste candidate | keep current custom/native validity | true while the unresolved editable draft/empty required state remains; call `field.setNativeInvalid(true)` | announce the specific rejection message once |
| captured native `invalid`, including `checkValidity()`, `reportValidity()`, or `requestSubmit()` | unchanged | true; call `field.setNativeInvalid(true)` | announce `proxy.validationMessage` once and expose Field error |
| accepted commit, explicit draft clear, or uncanceled reset | recompute custom error from the resulting effective draft and recompute native required validity | false; call `field.setNativeInvalid(false)` | clear validation episode before any accepted-change announcement |
| disabled or readonly becomes effective | clear custom error; proxy becomes barred as section 9 defines | false; call `field.setNativeInvalid(false)` | clear native episode; independent server/Field invalid may remain visible |
| disabled/readonly ends | recompute custom and required validity | false until the next explicit validation attempt | do not announce merely because validity exists |
| server/Field `invalid` changes | native validity unchanged | native latch unchanged | reflect server/Field state without manufacturing native status text |

Canceled reset changes none of these values. A later ordinary edit clears only
the native episode; Field/server invalidity stays authoritative. Cleanup calls
`field.setNativeInvalid(false)` only for the generation it registered.

The proxy's capture `invalid` handler prevents native focus, snapshots the
current deep active element and nearest open composed-ancestor native
`dialog`, updates the episode above, and schedules one generation-owned focus
task. `deepActiveElement` starts at `ownerDocument.activeElement` and descends
through open-shadow `activeElement` values. At task time:

1. if deep focus changed since the snapshot and now lies outside this
   TagsInput, owner-moved focus wins and the task exits;
2. otherwise focus the editor with `preventScroll` only when it is connected,
   enabled, rendered (`getClientRects().length > 0`), and not inert, then
   verify deep focus equals the editor;
3. if that attempt is unavailable or fails, focus the captured nearest open,
   connected, rendered composed-ancestor `dialog`, adding `tabindex="-1"`
   only when needed and removing only the temporary attribute after focus;
4. if no dialog accepts focus, focus `ownerDocument.body` using the same
   temporary-tabindex rule and verify it; if no connected body exists, stop.

A composed ancestor walk follows `assignedSlot`, `parentNode`, and
`ShadowRoot.host`. A newer invalid episode, reset, morph, successful edit, or
cleanup cancels stale focus work and removes any temporary tabindex it owns.
Focused browser falsifiers cover Document and open-ShadowRoot roots, an open
ancestor Dialog, editor disable and disconnect between invalid event/task,
owner-moved outside focus, body fallback, verification failure, and cleanup.

Reset ownership is resolved from the live `select.form`, including external
`form=id`. One capture reset listener per actual `Document` or open ShadowRoot
scope holds a registry keyed by current proxy elements. It filters by
`proxy.form === event.target`. After the cancelable reset event, a queued
microtask exits when `defaultPrevented`; otherwise it reconstructs immutable
server baseline options/value and initial draft because native reset cannot
resurrect removed options. Uncontrolled axes commit baseline without public
callbacks or native `input/change`. Controlled axes issue one `source="reset"`
request and remain supplied until accepted. When both axes are controlled,
`onValueChange` runs before `onInputValueChange`; each callback is followed by
the same connected-root and generation recheck used by interaction. A new
reset, morph, or cleanup cancels stale work.

The scope registry re-registers on correlated moves between Document/open
ShadowRoot roots and removes its capture listener when the last component
leaves. Native form-owner recalculation handles form ID replacement and
`form`-attribute changes without per-form listeners.

Empty Enter is not prevented and permits native implicit submission and any
submitter behavior. Nonempty Enter is prevented: it commits or reports a
rejection. A nonempty editable draft also blocks click/request submission via
custom validity, so committed values are never silently submitted as though
the draft did not exist. Readonly's dormant draft exception is stated in
section 5.

Citry Events success may morph server validation and baseline data. Transport
failure or cancellation retains uncontrolled value, draft, selection, active
tag, focus, and validity. Retry submits the same effective ordered values.
No-JavaScript shows the native multiple select containing server values. It
supports deselection, native required validity, repeated submission, external
form ownership, and reset, but cannot create new free-form values. In Field
SSR/no-JavaScript and every fail-closed mode, `label[for=P]` focuses the visible
`select#P`. After successful initialization the unchanged label focuses the
visible `input#P`. Both behaviors, plus reversal and recovery, are browser
acceptance requirements rather than incidental ID placement.

## 10. Styling and theme contract

`variant` is `outline`, `filled`, or `plain`; `size` is `sm`, `md`, or `lg`.
All nine combinations are supported. Default rules live in the Citry
component cascade layer with low specificity.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-tags-input-background` | color | control background | `Canvas` |
| `--cui-tags-input-foreground` | color | editor/text foreground | `CanvasText` |
| `--cui-tags-input-border-color` | color | default border | `color-mix(in srgb, CanvasText 28%, transparent)` |
| `--cui-tags-input-hover-border-color` | color | hover border | `color-mix(in srgb, CanvasText 55%, transparent)` |
| `--cui-tags-input-focus-color` | color | focus ring | `Highlight` |
| `--cui-tags-input-invalid-border-color` | color | invalid border | `light-dark(#b42318, #fda29b)` |
| `--cui-tags-input-disabled-background` | color | disabled surface | `color-mix(in srgb, CanvasText 6%, Canvas)` |
| `--cui-tags-input-tag-background` | color | tag background | `color-mix(in srgb, CanvasText 8%, Canvas)` |
| `--cui-tags-input-tag-foreground` | color | tag foreground | `CanvasText` |
| `--cui-tags-input-tag-border-color` | color | tag border | `color-mix(in srgb, CanvasText 18%, transparent)` |
| `--cui-tags-input-tag-highlighted-background` | color | active tag background | `light-dark(#dbeafe, #19376d)` |
| `--cui-tags-input-tag-highlighted-border-color` | color | active tag border | `Highlight` |
| `--cui-tags-input-radius` | length | control/tag rounding | `0.5rem` |
| `--cui-tags-input-min-height` | length | control height | `2.5rem` |
| `--cui-tags-input-padding` | length | internal inset | `0.375rem 0.5rem` |
| `--cui-tags-input-gap` | length | tag/editor gap | `0.375rem` |
| `--cui-tags-input-tag-gap` | length | label/remove gap | `0.25rem` |
| `--cui-tags-input-font-size` | length | editor/tag text | `1rem` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="tags-input"]` | component root | all | contains all other public parts |
| `[data-citry-ui-part="control"]` | visible wrapping control | all initialized states | contains tag list and editor |
| `[data-citry-ui-part="tag-list"]` | wrapping tag container | zero or more tags | precedes editor in control |
| `[data-citry-ui-part="tag"]` | one token visual | effective values only | contains label and remove |
| `[data-citry-ui-part="tag-label"]` | token text | all tags | exact effective string |
| `[data-citry-ui-part="remove"]` | native removal button | all tags | direct child of tag |
| `[data-citry-ui-part="input"]` | visible editor | all | one per component |
| `[data-citry-ui-part="status"]` | visually hidden live status | all | persistent node |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-empty` | present/absent | no effective tags |
| `data-required` | present/absent | effective required |
| `data-disabled` | present/absent | effective disabled |
| `data-readonly` | present/absent | effective readonly |
| `data-invalid` | present/absent | server/Field invalid or a revealed native-invalid episode |
| `data-focused` | present/absent | editor has focus-visible context |
| `data-at-max` | present/absent | count is at or above max |
| `data-variant` | `outline`, `filled`, `plain` | effective variant |
| `data-size` | `sm`, `md`, `lg` | effective size |
| tag `data-highlighted` | present/absent | visually active tag |

`part` and `data-*` mirrors are read-only outputs. Private proxy, readonly
transport, initialization, and error markers are not public selectors.

## 11. Environmental behavior

The control wraps tags and editor without horizontal page overflow at 320 CSS
pixels and at 400 percent zoom. Long unbroken tag text wraps or clips inside
the component; remove controls keep a 44 by 44 CSS-pixel touch target through
padding without forcing row height in compact mode.

RTL reverses visual row flow and physical arrow interpretation while retaining
value and FormData order. Nested light/dark schemes resolve local tokens.
Forced colors preserves visible control, focus, invalid, tag, and highlighted
boundaries using system colors. Reduced motion removes nonessential
transitions. Print shows committed tag text and hides editor/remove controls;
it does not expose private proxy or dormant draft. Mobile virtual-keyboard
input is handled through non-composing input reconciliation, not keydown only.

The family supports light DOM and components rooted inside an already-open
ShadowRoot. It does not traverse closed descendant shadows or imperatively
reparent its owned children into top-layer/opaque roots.

## 12. Overlay and layering behavior

TagsInput creates no overlay, top-layer element, anchor, portal, or shared
layer registration. It may live inside Menu, Popover, Drawer, or Dialog
content. Its root and editor count as ordinary descendants for those owners'
inside/focus logic. Closing an ancestor removes or hides the editor under the
ancestor's existing focus contract; TagsInput does not restore focus outside
itself. Suggestions remain a future Combobox responsibility.

## 13. Collections, async data, and identity

There is no declaration collection or async loader. Effective value order is
the only collection order. Exact canonical strings are unique identities in
V1; therefore duplicates are rejected and active-tag identity survives reorder
by value. Each option and tag uses the value as a private keyed identity, with
safe DOM text/value assignment rather than HTML interpolation.

Delimiter input and paste are atomic. For paste, form the would-be editor text
by replacing `[selectionStart, selectionEnd]` with clipboard `text/plain`.
Configured delimiters plus CR/LF split completed fragments; the final
unterminated fragment becomes trailing draft. If there is no delimiter/newline,
allow ordinary native paste.

CRLF is normalized to one newline separator before splitting. Before ordinary
editing, `beforeinput` snapshots the prior draft and selection; the controller
also retains the last settled snapshot for mobile fallback. If a later
non-composing `input` contains a configured delimiter, it parses the entire
resulting value atomically. A rejected typed-delimiter transaction restores
the pre-input draft and selection (or the latest supplied controlled draft)
and emits one invalid callback. A valid one never emits a transient
delimiter-containing `onInputValueChange` before the value transaction.

When tokenizing paste, canonicalize and validate every completed fragment
against current values, earlier candidates, and max before any change.
Leading or consecutive separators create an empty candidate and reject the
whole batch. A terminal separator creates an empty trailing draft, not an
extra candidate. Any empty, duplicate, invalid, or overflow candidate prevents
default, keeps the original draft and selection, mutates no tag/proxy value,
and emits exactly one structured invalid callback. Valid candidates append in
clipboard order in one value transaction; the trailing draft uses the
acceptance-gated rules in section 5. There is no partial acceptance.

Ordinary delimiter typing is reconciled from the resulting editor value using
the same atomic parser. A nonempty draft that contains no delimiter remains
draft. Network suggestions, remote data, and optimistic server tokens are not
part of this family.

## 14. Server render, morph, and cleanup

Server output contains a usable native multiple select and hidden custom
control. Client initialization validates the entire owned anatomy, canonical
baselines, IDs, Field registration, option/tag correlation, and callback/config
inputs before revealing the custom control. Invalid anatomy fails closed to
the native select and removes the private
`data-citry-tags-input-initialized` marker. The marker is set only after the
first complete successful reconcile and removed on every invalidation and
cleanup.

Successful initialization performs one synchronous, observer-suppressed
handoff before revealing custom UI: validate the SSR set `(proxy.id=P,
editor.id=E, label.for=P)`; set `proxy.id=N`; set `editor.id=P`; synchronize
the editor's Field relationships and `aria-required`; visually clip the proxy;
set proxy `aria-hidden="true"` and `tabindex="-1"`; remove custom-control
`hidden`; then set the initialized marker. Label `for=P` never changes. Moving
the proxy first creates no duplicate public ID, and MutationObserver callbacks
cannot observe the within-task temporary absence as a settled state.

Fail-closed recovery and cleanup of a retained DOM tree reverse the handoff in
one synchronous, observer-suppressed turn: remove the initialized marker; hide
custom UI; set `editor.id=E`; set `proxy.id=P`; remove proxy `aria-hidden` and
`tabindex`; remove visual clipping; expose the proxy. It never leaves both
interactive surfaces visible or both hidden, and every settled state has one
and only one `P`. The CField controller's retained control reference remains
the marker-bearing editor node across both ID modes.

The immutable server fingerprint includes root/control IDs, `name`, `form`,
canonical value baseline, raw draft baseline, delimiters, messages, variant,
size, max, and Field ownership. On a correlated morph:

- unchanged value baseline preserves uncontrolled effective value;
- changed value baseline replaces only an uncontrolled value axis;
- unchanged draft baseline preserves uncontrolled draft and selection;
- changed draft baseline replaces only an uncontrolled draft axis;
- controlled axes remain owner-supplied;
- active tag follows its unique value, then the nearest surviving neighbor;
- proxy options and readonly inputs rebuild from effective value;
- form/reset scope and Field/fieldset ownership re-resolve; and
- a changed public ID/Field `control_id` rebuilds `(P,E,N)`, label `for`, both
  elements' naming/description IDREFs, and the current mode's ID destinations
  as one correlated set before readiness.

During composition, correlated morph must retain the exact editor node and
must not write its value, selection, or controlled draft. Reconciliation waits
for `compositionend` plus the first final non-composing input. Node replacement
during active composition is outside the frozen contract and fails the
implementation gate rather than invoking an unspecified recovery path.

A scoped MutationObserver protects the fixed anatomy, owned IDs, part markers,
proxy/editor relationships, proxy options, and reflections. Repair uses
immutable server baselines, the current `(P,E,N)` mode, and effective state,
never hostile live attributes. Repeated invalid mutation enters one passive
invalid episode, fails closed with `proxy.id=P`, and may recover through the
same successful handoff after a settled valid structure.

Cleanup removes all editor/proxy/root listeners, Field capability registration,
fieldset and anatomy observers, reset-scope registry entry, queued reset work,
pending controlled acceptance, status work, and retained node references.
Mutation/listener accounting and cleanup must pass 1, 10, and 100 instance
fixtures, repeated morph, cross-root moves, and removal during composition.

## 15. Security and content trust

Tag values, drafts, placeholders, and message substitutions are always assigned
as text or native values. No path evaluates HTML, script, URL, selector, or
Alpine expressions derived from a value. The server JSON bridge uses the
shared safe serializer.

`attrs` may contain ordinary global attributes, `data-*`, static classes and
styles, and native event observers. It rejects owned `id`, `role`, `part`,
`hidden`, `inert`, `popover`, `contenteditable`, `tabindex`, `is`, form-control
attributes, runtime markers, reflections, owned ARIA relationships/states, and
whole-object or lifecycle Alpine directives (`x-data`, `x-init`, `x-effect`,
`x-id`). Bindings that can rewrite an owned destination are rejected.

`input_attrs` may contain the required static standalone `aria-label`, plus
safe editor hints such as `aria-describedby`, `spellcheck`, `autocapitalize`,
and native event observers. It rejects `aria-labelledby` from consumers in all
forms, including static, missing-ID, and dynamic bindings. It also rejects
`id`, `name`, `form`,
`type`, `value`, `defaultValue`, `required`, `disabled`, `readonly`, `role`,
`tabindex`, `part`, `hidden`, `inert`, `popover`, `is`, `list`, `multiple`,
`pattern`, `minlength`, `maxlength`, `placeholder`, `autocomplete`,
`inputmode`, `aria-invalid`, `aria-errormessage`, `aria-required`,
`aria-disabled`, `aria-readonly`, `aria-controls`, `aria-activedescendant`,
runtime
markers/reflections, unsafe directives, and bindings to those names. Inside a
Field, standalone naming/description overrides are rejected in favor of Field
ownership. The component rejects unresolved custom elements or authored shadow
hosts because it accepts no consumer children.

## 16. Assets and performance

TagsInput may privately reuse Field form/reset utilities, MultiSelect native
proxy helpers, and Tag presentation CSS only when existing family behavior and
asset deduplication remain unchanged. It must not duplicate a Field controller,
the MultiSelect collection runtime, or TagGroup selection runtime.

The family target is less than 4 KiB incremental minified+gzip JavaScript and
less than 1 KiB incremental minified+gzip CSS after a Field+MultiSelect+Tag
baseline. One shared reset listener per root scope, one anatomy observer per
instance, and no polling are allowed. Rendering and reconciliation are O(tag
count); a single transaction performs at most one tag/proxy rebuild. The
documented supported operating profile is 100 tags per instance and 100
instances per page; larger values need profiling, not silent truncation.

Asset tests must compare unique payload hashes, prove shared helpers appear
once, and keep catalog budgets separate from this incremental gate. No icon
font, third-party dependency, or eager overlay asset is added.

## 17. Acceptance matrix

| Area | Required evidence |
|---|---|
| Server API | exact ordered signatures, nine exports, strict canonical/delimiter/message validation, no children/slots, standalone static non-whitespace `aria-label` examples/rejection, missing/dynamic consumer `aria-labelledby` rejection, safe attrs destinations |
| Anatomy | SSR/fail-closed `(proxy=P, editor=E)` and initialized `(proxy=N, editor=P)` sets; unchanged label `for=P`; no settled duplicate/missing public ID; sole editor Field marker survives handoff; no-JS/fail-closed label focuses proxy and initialized label focuses editor; morph/hostile repair/reversal/recovery; parts and options/tags correlation |
| Basic value | add/remove ordered values, exact case-sensitive duplicate rejection, max, silent disabled/readonly guards, native proxy events |
| Controlled axes | all four ownership combinations; controlled rejection preserves draft; exact acceptance edge and generation; callback ordering; same-value and owner-mutates-in-callback falsifiers; `placeholder`/`autocomplete`/`inputmode` update, empty, `null`, removal, and invalid episodes |
| Paste | selection replacement, prefix/suffix, newline/configured delimiters, trailing draft, leading/consecutive separators, duplicate/max atomic rejection, no partial loss |
| IME | composition delimiter/Enter ignored; post-composition terminal delimiter; mobile input; correlated morph retains the exact editor; Chromium/Firefox/WebKit |
| Keyboard/focus | one Tab stop; empty Enter submits; nonempty Enter commits/blocks; two-step Backspace; Delete/arrows/Home/End/Escape; RTL; pointer/touch remove; focus-visible |
| Assistive technology | Field generated naming and standalone static non-whitespace `aria-label`, mirrored proxy name, rejected missing/dynamic consumer IDREF naming, editor `aria-required` transitions for standalone client/release and Field state while native `required` remains proxy-only, remove names, no listbox/grid, persistent polite accepted/rejected/selection announcements, axe and browser AX snapshots |
| Forms | repeated FormData order, required empty, draft custom validity without premature visible error, reveal/clear transitions for invalid/reportValidity/requestSubmit/rejection/edit/commit/reset/readonly/disabled/server invalid, Field native-invalid calls, readonly hidden values, disabled omission, unnamed behavior, external form/id replacement, multiple submitters |
| Reset | uncanceled and canceled reset, removed-option baseline reconstruction, controlled request-only, external owner, queued-work cancellation, no synthetic native change |
| Field | absent/equal `control_id` rule, exactly one editor control marker registered across ID handoff, label/description/error IDs, native required only on proxy plus editor `aria-required`, readonly transport plus editor interaction guard, disabled omission, dynamic fieldset ancestry/moves, nested isolation |
| Morph/lifecycle | baseline fingerprints, controlled/uncontrolled handoff, selection/active tag, correlated root moves, exact editor-node identity during composition, final-input reconciliation, 1/10/100 accounting, cleanup |
| Environment | 320px, 400% zoom, long text, LTR/RTL, light/dark nested schemes, forced colors, reduced motion, print, touch targets, open ShadowRoot |
| Trust | hostile strings/messages, NUL/newlines, attrs/directives/destination security, CSP-safe rendering, no innerHTML |
| Performance/assets | 100 tags, 100 instances, one rebuild per transaction, reset listener budget, observer cleanup, exact unique incremental gzip limits |

The browser matrix is current stable Chromium, Firefox, and WebKit. Form,
reset, IME, paste, focus, RTL, morph, and cleanup cases run in all three; visual
snapshots may use Chromium with cross-engine computed assertions. Server tests
must prove both template and direct Python composition.

## 18. Compatibility classification

This is a new family, not compatibility work. Local precedents are reused by
contract, not copied wholesale:

| Existing surface | Classification | Required compatibility proof |
|---|---|---|
| `CField` | shared owner contract | existing Field suites unchanged; exactly one TagsInput control/capability registration |
| `CMultiSelect` | native form substrate precedent | existing server/browser suites unchanged after any helper extraction |
| `CTag` / `CTagGroup` | presentation vocabulary only | no public dependency or selection/grid behavior; existing Tag suites unchanged if CSS helper extracted |
| native `<select multiple>` | progressive fallback | three-engine repeated value, required, external form, reset proof |

Implementation must stop if helper extraction changes any existing family's
DOM, public assets, event order, validity, or registration, or if direct
repeated free-form values cannot be preserved through form/reset/morph without
duplicating the MultiSelect substrate.

## 19. Public documentation contract

The eventual family documentation must contain an `api.yml`, `api.md`, README,
and executable examples matching this frozen catalog. No public artifact is
implemented in the design phase.

| Example | Exact lesson and evidence |
|---|---|
| `basic_tags.py` | template and direct Python forms; ordered add/remove and repeated FormData |
| `controlled_axes.py` | four ownership combinations, refusal, acceptance-gated draft clear, owner mutation during callback |
| `paste_and_ime.py` | atomic selection-aware paste, trailing draft, duplicate/max rejection, composition terminal delimiter |
| `forms_and_reset.py` | required, unfinished-draft invalidity, external form, canceled/uncanceled reset, readonly and disabled transport |
| `field_states.py` | Field-owned required/disabled/readonly/invalid, descriptions/errors, dynamic fieldset move |
| `keyboard_and_focus.py` | one Tab stop, visual tag activation/removal, RTL arrows, touch remove, live status |
| `variants_and_sizes.py` | all variants/sizes, max/empty/invalid states, long values, narrow and dark profiles |
| `customization.py` | public variables and one public selector in two brand scopes, forced colors and print preview |
| `morph_and_cleanup.py` | uncontrolled preservation, baseline change, controlled handoff, exact-node composition morph, listener/observer stats |

API prose must explicitly link the native
[`select multiple`](https://html.spec.whatwg.org/multipage/form-elements.html#the-select-element)
fallback, distinguish committed tags from unfinished draft, state the readonly
dormant-draft exception, and direct suggestion jobs to the future Combobox and
fixed-choice jobs to MultiSelect. It must distinguish callbacks from native
Alpine events and say that no custom DOM event or public method exists.

The quality scenario includes a required Field, ordered initial values, an
editable draft, readonly and disabled controls, two brand scopes, dark/RTL,
external form, reset, and a long token. The docs E2E proves every row above;
static schema tests prove all tables and exports agree.

## 20. Open decisions and deferred work

There are no open high/medium design decisions. Implementation remains blocked
until an independent adversarial reviewer reports PASS on this exact snapshot.

Deferred, deliberately unsupported work:

- suggestions, remote data, filtering, virtualization, and popup ownership;
- rich/slotted tokens, icons, per-token disabled state, and arbitrary metadata;
- drag or keyboard reorder and inline tag editing;
- case-insensitive, locale-aware, or application-defined duplicate equality;
- multi-character delimiters and application-defined token parsers;
- blur-to-add, create-on-submit, and silent partial paste;
- form-associated custom elements and ElementInternals;
- public headless parts or imperative methods.

Implementation falsifiers that reopen design are: native repeated entry order
differs in a supported engine; unfinished draft cannot block submission without
breaking readonly/required behavior; controlled acceptance cannot preserve raw
draft exactly; composition-safe morph requires replacing the editor; reset
scope cannot follow external form and ShadowRoot moves within the listener
budget; or the incremental asset ceiling cannot be met without behavior drift.

## 21. Internationalization

Remove labels, accepted/rejected interaction announcements, and unfinished-
draft validity text use the nine keys and typed values recorded in the
structured [Translation keys table](../../../packages/py/citry_ui/citry_ui/components/ctags_input/api.yml).
Initial remove controls use `$c-tr`; controls recreated for changed tag values
use `i18n.bind()`. Interaction announcements call `i18n.tr()` once at the
event's active locale and do not replay after a later switch. The package-owned
`citry-ui-tags-input-maximum` profile formats the maximum. Every non-`None`
field in `CTagsInputMessages` overrides only that field and registers no default
binding for it.
