---
title: File input and drop target
description: Select files with a native picker or an accessible drop-backed picker.
---

# File input and drop target

Use `CFileInput` when the native picker is the right control. Use
`CDropTarget` when drag-and-drop should supplement the same click, touch,
keyboard, FormData, reset, and required-validation behavior.

## File selection at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/at_a_glance.py" title="File selection at a glance" />

## Use FileInput in Field

Field supplies the visible label, description, error relationship, required
state, and disabled state. File inputs do not support readonly.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/field.py" title="FileInput in Field" />

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

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/drop_target.py" title="Drop files or browse" />

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

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/multiple.py" title="Select several files" />

## Configure picker hints

`accept` and `capture` are native picker hints. They are not validation or a
security boundary, and capture support differs by device and browser.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/capture.py" title="Picker hints" />

## Respect disabled ownership

Local disabled state, enclosing `CForm` state, and native disabled fieldsets
prevent browse and drop. Native form reset clears the current FileList.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/disabled.py" title="Disabled file controls" />

## Customize surfaces

Variants, sizes, public variables, and parts customize the picker and drop
surface. The operating-system picker itself is outside the page styling
contract.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cfile_input/snippets/customization.py" title="Customize file controls" />

## Validate and upload in the application

Never trust the file name, MIME type, extension, path, or `accept` match.
Validate again on the server. Build previews with application-owned object
URLs and revoke them when no longer needed. Compose upload progress with
`CProgress`; this family does not own upload transport, retry, or cancellation.

<!-- UI_LIBRARY_API_REFERENCE -->
