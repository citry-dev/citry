---
title: File input and drop target
url: https://citry.dev/v/0.4.0/ui-library/components/file-input/
description: "Select files with a native picker or an accessible drop-backed picker."
---
# File input and drop target

Use `CFileInput` when the native picker is the right control. Use
`CDropTarget` when drag-and-drop should supplement the same click, touch,
keyboard, FormData, reset, and required-validation behavior.

## File selection at a glance


### File selection at a glance

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileInputAtAGlance(Component):
    template = """
      <c-CStack gap="lg">
        <c-CField>
          <c-fill name="label">Profile photo</c-fill>
          <c-fill name="default"><c-CFileInput name="photo" accept="image/*" /></c-fill>
        </c-CField>
        <c-CDropTarget label="Project files" name="project_files" multiple>
          Drop files here or browse from this device
        </c-CDropTarget>
      </c-CStack>
    """


preview = FileInputAtAGlance()

preview  # noqa: B018
````


## Use FileInput in Field

Field supplies the visible label, description, error relationship, required
state, and disabled state. File inputs do not support readonly.


### FileInput in Field

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/field/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileInputField(Component):
    template = """
      <c-CField required>
        <c-fill name="label">Supporting document</c-fill>
        <c-fill name="default">
          <c-CFileInput name="document" accept="application/pdf" />
        </c-fill>
        <c-fill name="description">Choose one PDF for review.</c-fill>
        <c-fill name="error">Choose a supporting document.</c-fill>
      </c-CField>
    """


preview = FileInputField()

preview  # noqa: B018
````



```citry-html
<c-CField required>
  <c-fill name="label">Supporting document</c-fill>
  <c-fill name="default">
    <c-CFileInput name="document" accept="application/pdf" />
  </c-fill>
</c-CField>
```


## Add a drop target

DropTarget always keeps its native file input. Dragging is an enhancement;
click, touch, and keyboard users open the system picker through the same
control. Its `label` is the exact accessible name, while default content adds
visible instructions.


### Drop files or browse

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/drop-target/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileDropTarget(Component):
    template = """
      <div x-data="{names: []}">
        <c-CDropTarget
          label="Supporting documents"
          name="documents"
          multiple
          @change="names = [...$event.target.files].map(file => file.name)"
        >
          PDF or image files
        </c-CDropTarget>
        <p x-text="names.join(', ')"></p>
      </div>
    """


preview = FileDropTarget()

preview  # noqa: B018
````


Read files from native events. On DropTarget the event bubbles to the label,
so use `event.target.files`, not `currentTarget.files`.


```citry-html
<c-CDropTarget
  label="Supporting documents"
  name="documents"
  multiple
  @change="files = [...$event.target.files]"
>
  PDF or image files
</c-CDropTarget>
```


## Select several files

`multiple` uses native `FileList` ordering and repeated multipart form values.
The component does not deduplicate, render, remove, or upload files.


### Select several files

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/multiple/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultipleFiles(Component):
    template = """
      <form @submit.prevent="window.__selectedFiles = [...new FormData($event.target).getAll('evidence')]">
        <c-CDropTarget label="Research evidence" name="evidence" multiple variant="soft">
          Select or drop several files
        </c-CDropTarget>
        <c-CButton type="submit">Inspect FormData</c-CButton>
      </form>
    """


preview = MultipleFiles()

preview  # noqa: B018
````


## Configure picker hints

`accept` and `capture` are native picker hints. They are not validation or a
security boundary, and capture support differs by device and browser.


### Picker hints

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/capture/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileCaptureHints(Component):
    template = """
      <c-CGroup>
        <c-CField>
          <c-fill name="label">Take a photo</c-fill>
          <c-fill name="default">
            <c-CFileInput name="photo" accept="image/*" capture="environment" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Record a note</c-fill>
          <c-fill name="default">
            <c-CFileInput name="note" accept="audio/*" capture="user" />
          </c-fill>
        </c-CField>
      </c-CGroup>
    """


preview = FileCaptureHints()

preview  # noqa: B018
````


## Respect disabled ownership

Local disabled state, enclosing `CForm` state, and native disabled fieldsets
prevent browse and drop. Native form reset clears the current FileList.


### Disabled file controls

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/disabled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledFiles(Component):
    template = """
      <c-CStack>
        <c-CFileInput c-attrs="{'aria-label': 'Disabled picker'}" disabled />
        <fieldset disabled>
          <legend>Archived upload</legend>
          <c-CDropTarget label="Archived evidence" c-disabled="False">
            Uploads are unavailable
          </c-CDropTarget>
        </fieldset>
      </c-CStack>
    """


preview = DisabledFiles()

preview  # noqa: B018
````


## Customize surfaces

Variants, sizes, public variables, and parts customize the picker and drop
surface. The operating-system picker itself is outside the page styling
contract.


### Customize file controls

[Open the rendered preview](/v/0.4.0/ui-library/components/file-input/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedFiles(Component):
    css = """
      :where(.evidence-drop) {
        --cui-file-input-background: light-dark(#eef8f2, #10271d);
        --cui-file-input-border-color: light-dark(#28724d, #6ed59b);
        --cui-file-input-active-color: light-dark(#15623e, #82e8ad);
        --cui-file-input-radius: 1.25rem;
      }
    """
    template = """
      <c-CDropTarget label="Botanical records" class_="evidence-drop" size="lg">
        CSV, PDF, or field images
      </c-CDropTarget>
    """


preview = CustomizedFiles()

preview  # noqa: B018
````


## Validate and upload in the application

Never trust the file name, MIME type, extension, path, or `accept` match.
Validate again on the server. Build previews with application-owned object
URLs and revoke them when no longer needed. Compose upload progress with
`CProgress`; this family does not own upload transport, retry, or cancellation.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CFileInput server inputs

Server inputs are passed in a template through `<c-CFileInput ... />` or in Python through
`CFileInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="file-input-input-cfileinput-server-inputs-id"></span>`id` | `str | None` | `None` | Sets exact native input identity or uses a generated ID. |
| <span id="file-input-input-cfileinput-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native form field name. |
| <span id="file-input-input-cfileinput-server-inputs-accept"></span>`accept` | `str | None` | `None` | Sets the native picker hint without validating files. |
| <span id="file-input-input-cfileinput-server-inputs-capture"></span>`capture` | `"user" | "environment" | None` ([`CFileInputCapture`](#file-input-interface-capture)) | `None` | Sets the native media capture hint. |
| <span id="file-input-input-cfileinput-server-inputs-multiple"></span>`multiple` | `bool` | `False` | Allows more than one native selected file. |
| <span id="file-input-input-cfileinput-server-inputs-required"></span>`required` | `bool | None` | `None` | Sets native required validity outside Field. |
| <span id="file-input-input-cfileinput-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Sets local disabledness outside Field; Form and fieldset still dominate. |
| <span id="file-input-input-cfileinput-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Reflects an external invalid state outside Field. |
| <span id="file-input-input-cfileinput-server-inputs-variant"></span>`variant` | `"outline" | "soft" | "plain"` ([`CFileInputVariant`](#file-input-interface-variant)) | `"outline"` | Selects the picker surface. |
| <span id="file-input-input-cfileinput-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CFileInputSize`](#file-input-interface-size)) | `"md"` | Selects picker geometry. |
| <span id="file-input-input-cfileinput-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#file-input-interface-class-value)) | `None` | Adds root classes. |
| <span id="file-input-input-cfileinput-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#file-input-interface-style-value)) | `None` | Adds root inline styles. |
| <span id="file-input-input-cfileinput-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted native attributes without replacing owned file input semantics or state. |

</div>

#### CDropTarget server inputs

Server inputs are passed in a template through `<c-CDropTarget ... />` or in Python through
`CDropTarget(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="file-input-input-cdroptarget-server-inputs-label"></span>`label` | `str` | required | Supplies the exact native input accessible name and visible primary text. |
| <span id="file-input-input-cdroptarget-server-inputs-id"></span>`id` | `str | None` | `None` | Sets the nested native input identity. |
| <span id="file-input-input-cdroptarget-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the nested native form field name. |
| <span id="file-input-input-cdroptarget-server-inputs-accept"></span>`accept` | `str | None` | `None` | Sets the native picker hint without validating dropped files. |
| <span id="file-input-input-cdroptarget-server-inputs-capture"></span>`capture` | `"user" | "environment" | None` ([`CFileInputCapture`](#file-input-interface-capture)) | `None` | Sets the native media capture hint. |
| <span id="file-input-input-cdroptarget-server-inputs-multiple"></span>`multiple` | `bool` | `False` | Keeps all dropped or selected files instead of only the first. |
| <span id="file-input-input-cdroptarget-server-inputs-required"></span>`required` | `bool | None` | `None` | Sets native required validity. |
| <span id="file-input-input-cdroptarget-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables browse and drop locally. |
| <span id="file-input-input-cdroptarget-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Reflects external invalid state. |
| <span id="file-input-input-cdroptarget-server-inputs-variant"></span>`variant` | `"outline" | "soft" | "plain"` ([`CFileInputVariant`](#file-input-interface-variant)) | `"outline"` | Selects drop surface treatment. |
| <span id="file-input-input-cdroptarget-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CFileInputSize`](#file-input-interface-size)) | `"md"` | Selects drop surface geometry. |
| <span id="file-input-input-cdroptarget-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#file-input-interface-class-value)) | `None` | Adds label-root classes. |
| <span id="file-input-input-cdroptarget-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#file-input-interface-style-value)) | `None` | Adds label-root inline styles. |
| <span id="file-input-input-cdroptarget-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted root label attributes. |
| <span id="file-input-input-cdroptarget-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds unrelated trusted attributes to the nested native input. |

</div>

#### CFileInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CFileInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="file-input-input-file-client-inputs-accept"></span>`accept` | `str` | Uses the server value. | Reactively changes the native picker hint. |
| <span id="file-input-input-file-client-inputs-capture"></span>`capture` | `"user" | "environment"` | Uses the server value. | Reactively changes the native capture hint. |
| <span id="file-input-input-file-client-inputs-multiple"></span>`multiple` | `bool` | Uses the server value. | Reactively changes single or multiple selection. |
| <span id="file-input-input-file-client-inputs-required"></span>`required` | `bool` | Uses the server or Field value. | Reactively changes native required validity outside Field. |
| <span id="file-input-input-file-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server or Field value. | Reactively changes local disabledness outside Field. |
| <span id="file-input-input-file-client-inputs-invalid"></span>`invalid` | `bool` | Uses the server or Field value. | Reactively reflects external invalidity outside Field. |
| <span id="file-input-input-file-client-inputs-variant"></span>`variant` | `"outline" | "soft" | "plain"` | Uses the server value. | Reactively changes surface treatment. |
| <span id="file-input-input-file-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` | Uses the server value. | Reactively changes geometry. |

</div>

#### CDropTarget client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDropTarget />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="file-input-input-drop-target-client-inputs-accept"></span>`accept` | `str` | Uses the server value. | Reactively changes the native picker hint. |
| <span id="file-input-input-drop-target-client-inputs-capture"></span>`capture` | `"user" | "environment"` | Uses the server value. | Reactively changes the native capture hint. |
| <span id="file-input-input-drop-target-client-inputs-multiple"></span>`multiple` | `bool` | Uses the server value. | Reactively changes single or multiple selection and drop behavior. |
| <span id="file-input-input-drop-target-client-inputs-required"></span>`required` | `bool` | Uses the server value. | Reactively changes native required validity. |
| <span id="file-input-input-drop-target-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server value. | Reactively changes local browse and drop disabledness. |
| <span id="file-input-input-drop-target-client-inputs-invalid"></span>`invalid` | `bool` | Uses the server value. | Reactively reflects external invalidity. |
| <span id="file-input-input-drop-target-client-inputs-variant"></span>`variant` | `"outline" | "soft" | "plain"` | Uses the server value. | Reactively changes surface treatment. |
| <span id="file-input-input-drop-target-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` | Uses the server value. | Reactively changes geometry. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CDropTarget slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="file-input-slot-cdroptarget-slots-default"></span>`default` | no | `{}` ([`CDropTargetDefaultSlotData`](#file-input-interface-drop-target-default-slot-data)) | No supporting text. Content must be noninteractive phrasing content. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CFileInput CSS variables

Apply these variables to `CFileInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="file-input-css-file-input-css-variables-background"></span>`--cui-file-input-background` | `color` | Picker or drop surface. | `Canvas or the soft surface mix.` |
| <span id="file-input-css-file-input-css-variables-foreground"></span>`--cui-file-input-foreground` | `color` | Text color. | `CanvasText` |
| <span id="file-input-css-file-input-css-variables-border-color"></span>`--cui-file-input-border-color` | `color` | Resting border. | `a 38 percent CanvasText mix` |
| <span id="file-input-css-file-input-css-variables-active-color"></span>`--cui-file-input-active-color` | `color` | Focus and drag emphasis. | `Highlight` |
| <span id="file-input-css-file-input-css-variables-invalid-color"></span>`--cui-file-input-invalid-color` | `color` | Invalid border. | `scheme-aware red` |
| <span id="file-input-css-file-input-css-variables-radius"></span>`--cui-file-input-radius` | `length` | Corner radius. | `0.65rem` |
| <span id="file-input-css-file-input-css-variables-padding"></span>`--cui-file-input-padding` | `padding` | Drop surface padding. | `size-dependent` |
| <span id="file-input-css-file-input-css-variables-min-height"></span>`--cui-file-input-min-height` | `length` | Minimum control height. | `sm: 2.25rem; md: 2.75rem; lg: 3.25rem` |

</div>

#### CDropTarget CSS variables

Apply these variables to `CDropTarget` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="file-input-css-drop-target-css-variables-background"></span>`--cui-file-input-background` | `color` | Drop surface. | `Canvas or the soft surface mix.` |
| <span id="file-input-css-drop-target-css-variables-foreground"></span>`--cui-file-input-foreground` | `color` | Text color. | `CanvasText` |
| <span id="file-input-css-drop-target-css-variables-border-color"></span>`--cui-file-input-border-color` | `color` | Resting border. | `a 38 percent CanvasText mix` |
| <span id="file-input-css-drop-target-css-variables-active-color"></span>`--cui-file-input-active-color` | `color` | Focus and drag emphasis. | `Highlight` |
| <span id="file-input-css-drop-target-css-variables-invalid-color"></span>`--cui-file-input-invalid-color` | `color` | Invalid border. | `scheme-aware red` |
| <span id="file-input-css-drop-target-css-variables-radius"></span>`--cui-file-input-radius` | `length` | Corner radius. | `0.65rem` |
| <span id="file-input-css-drop-target-css-variables-padding"></span>`--cui-file-input-padding` | `padding` | Drop surface padding. | `size-dependent` |
| <span id="file-input-css-drop-target-css-variables-min-height"></span>`--cui-file-input-min-height` | `length` | Minimum drop surface height input. | `sm: 2.25rem; md: 2.75rem; lg: 3.25rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CFileInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="file-input-attribute-file-input-attributes-data-has-files"></span>`data-has-files` | Styled root | `present-or-absent` | Present when the native FileList is nonempty. |
| <span id="file-input-attribute-file-input-attributes-data-disabled"></span>`data-disabled` | Styled root | `present-or-absent` | Mirrors effective native disabledness. |
| <span id="file-input-attribute-file-input-attributes-data-required"></span>`data-required` | Styled root | `present-or-absent` | Mirrors native required state. |
| <span id="file-input-attribute-file-input-attributes-data-invalid"></span>`data-invalid` | Styled root | `present-or-absent` | Mirrors external or native invalid state. |
| <span id="file-input-attribute-file-input-attributes-data-variant"></span>`data-variant` | Styled root | `outline | soft | plain` | Mirrors effective variant. |
| <span id="file-input-attribute-file-input-attributes-data-size"></span>`data-size` | Styled root | `sm | md | lg` | Mirrors effective size. |

</div>

#### CDropTarget attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="file-input-attribute-drop-target-attributes-data-has-files"></span>`data-has-files` | Root label | `present-or-absent` | Present when the nested native FileList is nonempty. |
| <span id="file-input-attribute-drop-target-attributes-data-dragging"></span>`data-dragging` | Root label | `present-or-absent` | Present during an accepted file drag over the target. |
| <span id="file-input-attribute-drop-target-attributes-data-disabled"></span>`data-disabled` | Root label | `present-or-absent` | Mirrors effective native disabledness. |
| <span id="file-input-attribute-drop-target-attributes-data-required"></span>`data-required` | Root label | `present-or-absent` | Mirrors native required state. |
| <span id="file-input-attribute-drop-target-attributes-data-invalid"></span>`data-invalid` | Root label | `present-or-absent` | Mirrors external or native invalid state. |
| <span id="file-input-attribute-drop-target-attributes-data-variant"></span>`data-variant` | Root label | `outline | soft | plain` | Mirrors effective variant. |
| <span id="file-input-attribute-drop-target-attributes-data-size"></span>`data-size` | Root label | `sm | md | lg` | Mirrors effective size. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CFileInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="file-input-selector-file-input-selectors-file-input"></span>`[data-citry-ui-part="file-input"]` | FileInput native input | Stable picker root. |

</div>

#### CDropTarget selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="file-input-selector-drop-target-selectors-drop-target"></span>`[data-citry-ui-part="drop-target"]` | DropTarget label | Stable drop surface and root attrs destination. |
| <span id="file-input-selector-drop-target-selectors-input"></span>`[data-citry-ui-part="input"]` | DropTarget native input | Stable native input destination. |
| <span id="file-input-selector-drop-target-selectors-label"></span>`[data-citry-ui-part="label"]` | DropTarget primary text | Stable visible label. |
| <span id="file-input-selector-drop-target-selectors-content"></span>`[data-citry-ui-part="content"]` | DropTarget supporting content | Stable supporting content. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="file-input-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="file-input-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="file-input-interface-capture"></span>`CFileInputCapture` | `Literal["user", "environment"]` |
| <span id="file-input-interface-variant"></span>`CFileInputVariant` | `Literal["outline", "soft", "plain"]` |
| <span id="file-input-interface-size"></span>`CFileInputSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="file-input-interface-drop-target-default-slot-data"></span>

#### `CDropTargetDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-