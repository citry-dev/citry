# Citry UI FileInput and DropTarget specification

**Status (2026-08-10):** implementation pass complete. Runtime, focused
server and three-engine browser evidence, public docs/reference, previews,
quality scenario, registration, assets, and packaging wiring are checked in.
Real device picker/drop and assistive-technology qualification remain manual.

## 1. Purpose and product bar

`CFileInput` is a styled native file picker. `CDropTarget` is the drag-and-drop
alternative backed by the same native file-input semantics and a click/touch
browse path. Both select files; neither uploads, reads, previews, transforms,
or persists them.

Common jobs stay short:

```citry-html
<c-CField>
  <c-fill name="label">Supporting document</c-fill>
  <c-CFileInput name="document" accept="application/pdf" />
</c-CField>

<c-CDropTarget label="Supporting documents" name="documents" multiple>
  PDF or image files
</c-CDropTarget>
```

Python composition uses the same `CFileInput(...)` and `CDropTarget(...)`
inputs. Native `@input` and `@change` listeners read
`$event.target.files`. Applications own upload transport, server validation,
progress, retry, object URLs, previews, file lists, and removal controls.
Directory picking, clipboard ingestion, remote URLs, file transformation, and
controlled `File` state are deliberately excluded.

## 2. Prior art and complaints

Sources reviewed on 2026-08-10:

| Source | Surface inspected | Decision |
|---|---|---|
| HTML file input and File API | native selection, `FileList`, form submission, required validation, reset, script restrictions | keep a real `<input type="file">`; never serialize or control files |
| HTML Drag and Drop and `DataTransfer` | protected data store, file-only drop, dragover cancellation | inspect types during drag and read files synchronously during drop |
| Vuetify file input | accept, capture, chips, counter, clear, multiple, show-size | adopt native configuration; leave presentation of selected files to composition |
| React Aria FileTrigger and DropZone | separate browse and drop jobs, accessible naming, accepted operations | provide a focused native picker and a drop-backed picker, not a general drag system |
| Chakra and Ark FileUpload | compound upload state, dropzone, previews, constraints, rejected files, directory and paste support | reject upload-manager scope; keep native form ownership and application validation |
| Material UI | no production first-party upload manager | supports avoiding a framework-specific upload state machine |

Vuetify capability disposition:

| Vuetify job | Citry path | Decision |
|---|---|---|
| accept and capture hints | direct `accept` and `capture` inputs | adopt |
| multiple selection | direct `multiple` input | adopt |
| clear | native form reset or application ref assigning `value = ""` | compose |
| chips, counters, file names, sizes | application output driven by native change | compose |
| prepend/append decorations | `CField` and ordinary layout composition | compose |
| loading and upload progress | `CProgress` plus application upload owner | separate |

The family does not infer security from `accept`: it is a picker hint, not
validation. Server code must validate content, size, type, and filename.

## 3. Public composition and anatomy

| Component | Semantic root | Stable anatomy |
|---|---|---|
| `CFileInput` | `<input type="file">` | the root is the form control |
| `CDropTarget` | `<label>` | direct hidden native file input, content span |

`CFileInput` may be the one control in `CField`. It receives Field label,
description, error, required, disabled, and invalid relationships and rejects
Field readonly. `CDropTarget` is standalone because nesting its label inside
`CField` would create competing label ownership. Its required `label` input is
the exact accessible name of the nested file input; the default slot is
optional visible supporting content.

Both accept root `class_`, `style`, and trusted `attrs`. `CFileInput.attrs`
lands on the input. `CDropTarget.attrs` lands on the label and `input_attrs`
lands on the native input. Owned identity, form, state, drag, role, focus, and
runtime attributes cannot be replaced or dynamically bound.

## 4. Server inputs and client inputs

Shared native inputs are `id`, `name`, `accept`, `capture`, `multiple`,
`required`, `disabled`, `invalid`, `variant`, and `size`. `CDropTarget` adds a
required `label` and `input_attrs`. `CFileInput` inside `CField` cannot also
supply `required`, `disabled`, or `invalid`.

| Input | Type and default | Class | Effect |
|---|---|---|---|
| `id` | `str | None = None` | structural | exact native identity; generated when omitted |
| `name` | `str | None = None` | structural | native form name |
| `accept` | `str | None = None` | reactive configuration | native picker hint only |
| `capture` | `"user" | "environment" | None` | reactive configuration | native media-capture hint |
| `multiple` | `bool = False` | reactive configuration | native multi-selection |
| `required` | `bool | None = None` | reactive configuration | native constraint validation |
| `disabled` | `bool | None = None` | reactive configuration | local disabled state; Form and fieldset still dominate |
| `invalid` | `bool | None = None` | reactive configuration | external invalid reflection and Field error relationship |
| `variant` | `"outline" | "soft" | "plain" = "outline"` | reactive visual | theme treatment |
| `size` | `"sm" | "md" | "lg" = "md"` | reactive visual | control geometry |
| `label` | nonempty `str` | structural, DropTarget only | accessible input name and visible primary text |
| `class_`, `style`, `attrs` | structured values | server/root | trusted customization |
| `input_attrs` | mapping or `None` | server/input | unrelated native and ARIA input attrs |

The client surface supports `accept`, `capture`, `multiple`, `required`,
`disabled`, `invalid`, `variant`, and `size`. Omission uses the server
fallback. Invalid values report once per continuous episode and use the last
valid/server value. `null` is invalid rather than an ownership release.
Selected files are never a server or client prop.

## 5. State model

Public states are empty/has-files, dragging/not-dragging, disabled, required,
invalid, variant, and size. Native picker selection and a file drop replace
the native `FileList`; multiple mode keeps all dropped files while single mode
uses the first. A drop containing no files is ignored. Disabled controls never
open, accept a drop, dispatch synthetic input/change, or invoke callbacks.

The `data-has-files` mirror follows `input.files.length > 0`. Native reset
clears it after the reset algorithm settles. Native invalid creates a Field
native-invalid episode; a later valid selection or reset clears that episode.
Programmatic changes do not create an invalid episode.

## 6. Slots and slot data

`CFileInput` has no slots. `CDropTarget.default` is optional phrasing content
rendered after the visible label. It must not contain interactive, labelable,
form-associated, editable, or nested label content because the whole root is
a label. The runtime fail-closes drag enhancement if settled content violates
that rule; templates should treat this as an authoring error.

## 7. Callbacks, native events, and methods

No component callback duplicates the browser file-input API. Consumers use
native `@input` or `@change`; `event.target` is always the native input for
both components. DropTarget assigns the dropped `FileList` and dispatches one
bubbling `input`, then one bubbling `change`, matching picker event order.
Root-level `@change` on DropTarget therefore uses `event.target.files`, not
`currentTarget`.

There are no public methods. A ref to the native input may call `click()` or
clear `value`; applications remain responsible for user-activation and
security rules.

## 8. Semantics, keyboard, focus, and assistive technology

`CFileInput` retains the native focusable picker. DropTarget is a label whose
input is visually hidden but remains focusable; clicking or pressing the
native input through the label opens the system picker. The label gets
`:focus-within` treatment. Dragging is an enhancement, never the only path.

`aria-label` on DropTarget's input is component-owned from `label`.
`CFileInput` relies on `CField` or a caller-supplied static ARIA naming
relationship. Both reserve contradictory `role`, `aria-disabled`,
`aria-required`, `aria-readonly`, and `aria-hidden` values.

## 9. Native forms and validation

The native input is the successful form control. `name`, `form`, `multiple`,
disabledness, required validity, multipart form submission, and reset use
browser behavior. An enclosing `CForm` supplies the native owner and dominates
disabled state. A disabled native fieldset also dominates through `:disabled`.
`readonly` is unsupported and never emitted.

Dropped files are assigned to the same native input, so `FormData` sees them.
`accept` does not participate in constraint validation. Applications and
servers validate selected and dropped files identically.

## 10. Styling and theme contract

Variants are outline, soft, and plain; sizes are sm, md, and lg. Stable
variables are:

| Variable | Purpose |
|---|---|
| `--cui-file-input-background` | control/drop surface |
| `--cui-file-input-foreground` | text |
| `--cui-file-input-border-color` | resting border |
| `--cui-file-input-active-color` | focus and drag emphasis |
| `--cui-file-input-invalid-color` | invalid border |
| `--cui-file-input-radius` | corner radius |
| `--cui-file-input-padding` | internal spacing |
| `--cui-file-input-min-height` | size override |

Stable parts are `file-input`, `drop-target`, `input`, `content`, `label`, and
`description`. Public mirrors are `data-has-files`, `data-dragging`,
`data-disabled`, `data-required`, `data-invalid`, `data-variant`, and
`data-size` on the styled root.

## 11. Environmental behavior

All sizing uses logical properties, wraps long labels, and avoids fixed inline
width. Light/dark follows system colors. Forced colors keeps a visible border
and focus indicator. Reduced motion removes transition. RTL needs no behavior
branch. Touch and coarse pointer use the browse path. Print shows the label
and supporting content but hides the native picker affordance.

There are no library-authored visible strings. The application supplies every
label and instruction, so this family adds no i18n contract.

## 12. Overlay and layering behavior

The browser owns the system file picker. Citry does not model it as an overlay,
intercept Escape, restore focus, or inspect picker lifecycle.

## 13. Collections, async data, and identity

`FileList` order is browser/drop order. The component does not deduplicate or
key files. No upload or asynchronous work is owned. File identity and
replacement policy belong to the application.

## 14. Server render, morph, and cleanup

No-JavaScript FileInput and DropTarget both retain a usable native picker.
Drag support activates once, removes all listeners on cleanup, and cancels no
global document behavior. Retained rerenders preserve the browser-owned
`FileList`; replacing the input follows native replacement and loses the
selection. Configuration changes never try to reconstruct `File` objects.

## 15. Security and content trust

File names are never inserted into component-authored HTML. Files are passed
only through native `FileList`. No path, content, MIME type, extension, or
`accept` match is trusted. `value`, `files`, directory APIs, ownership
directives, whole-object binds, structural Alpine directives, and dynamic
bindings to owned attributes are rejected. Drop handling reads
`DataTransfer.files` synchronously and ignores non-file data.

## 16. Assets and performance

FileInput uses one local component effect plus input/reset listeners.
DropTarget adds four root drag listeners and one mutation observer for settled
content. No shared global listener, icon, font, network request, object URL,
or file read exists. Repeated-instance and asset reports include both public
classes once the family is registered.

## 17. Acceptance matrix

Automated evidence must cover exact HTML/form anatomy, Field and Form
ownership, hostile attrs and strings, native selection simulation, drop
assignment, single/multiple, input-before-change, disabled and fieldset,
required validity, reset, focus, invalid episodes, drag-depth cleanup,
settled-content fail-close/recovery, reactive configuration, morph retention,
light/dark, RTL, narrow text, forced colors, print, axe, exports,
registration, docs projection, assets, wheel contents, and Chromium/Firefox/
WebKit. Manual release evidence covers real OS pickers, file-manager drops,
mobile capture, VoiceOver/Safari, NVDA/Firefox or Chromium, and JAWS/Chromium.

## 18. Compatibility classification

Public component/type names, inputs, native events, variables, parts, mirrors,
and form behavior are stable. Native semantics and the documented label/input
relationship are behavioral contracts. Exact theme values and incidental
wrappers are evolvable. Classes, private variables, initialization markers,
listener organization, and diagnostics are private.

## 19. Public documentation contract

The guide owns: at-a-glance native picker, Field validation, DropTarget,
multiple files, capture/accept, disabled/fieldset, and customization examples.
The quality scenario shows both variants, all sizes, form/reset, drag states,
long text, nested dark scope, RTL, and brand-token adaptation.

## 20. Open decisions and deferred work

Directory upload, paste, file constraints, rejection lists, preview URLs,
upload transport, progress ownership, retry, and controlled files require
their own product and security evidence. They do not block this native
selection family.
