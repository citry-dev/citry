---
title: Dialog
description: Build accessible native modal workflows with Citry UI Dialog.
---

# Dialog

Use `CDialog` for a task or decision that temporarily blocks the page. It
renders a native `<dialog>`, enters the browser top layer, makes background
content inert, contains focus, restores focus, and locks page scrolling.

## Dialog at a glance

Use `sm` for one clear decision, `md` for ordinary tasks, `lg` for richer
content, and `full` when the task needs the viewport.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/at_a_glance.py"
  title="Dialog at a glance"
/>

## Build a Dialog

Provide a required title and body. Spread `activator_attrs` onto the control
that opens it. Spread `close_attrs` onto explicit completion or cancel actions.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/open_field_note.py"
  title="Open a field note"
/>

```citry-html
<c-CDialog>
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Read field note
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Aurora over the northern ridge
  </c-fill>
  <c-fill name="description">
    Recorded at 01:42 under a clear sky.
  </c-fill>
  <c-fill name="default">
    ...
  </c-fill>
  <c-fill name="actions" data="{ close_attrs }">
    <c-CButton c-attrs="close_attrs">
      Close note
    </c-CButton>
  </c-fill>
</c-CDialog>
```

Compose a Dialog in Python when its content is already available there:

```python
from citry_ui import CDialog

field_note = CDialog(
    slots={
        "title": "Aurora over the northern ridge",
        "default": note_content,
    },
)
```

The title becomes the accessible name. Use `description` for one concise
summary. Keep structured or lengthy content in the body so assistive technology
does not announce it as one uninterrupted description.

The activator is optional. A controlled owner may open the Dialog without one.

## Configure Dialog

Server inputs are passed in Python through `<c-CDialog ... />` attributes or a
`CDialog(...)` composition call. Client inputs are passed in the browser
through `$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/configuration.py"
  title="Configure Dialog"
/>

A valid client input wins over its server value. Removing it restores the
server value, except `open`, which preserves the last committed state and
becomes uncontrolled. An invalid `open` value does the same after reporting a
diagnostic. Other invalid client values use their server fallback.

```citry-html
<c-CDialog
  size="md"
  scroll="body"
  $c-props="{
    size: preferredSize,
    scroll: preferredScroll,
    dismissible: allowPassiveClose,
  }"
>
  ...
</c-CDialog>
```

`id`, `close_label`, `class_`, `style`, and `attrs` are server-only because
they define rendered identity, text, and native structure.

## Control visibility

Pass a Boolean client `open` input to control visibility. `onOpenChange`
reports user requests; update `open` to accept one or keep it unchanged to
decline it.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/controlled_dialog.py"
  title="Control Dialog visibility"
/>

```citry-html
<c-CDialog
  $c-props="{
    open,
    onOpenChange: (nextOpen, detail) => {
      if (mayApply(nextOpen, detail)) open = nextOpen;
    },
  }"
>
  ...
</c-CDialog>
```

The callback detail identifies the `trigger`, `close-button`, `action`,
`escape`, `outside`, or `native` reason. It also includes controlled ownership,
the browser source, and the Dialog return value. Owner commits do not notify
again.

When no client `open` input is supplied, CDialog commits requests itself and
then notifies. Passing `null` or removing the input releases control without
resetting the current state.

## Choose dismissal rules

`dismissible=True` shows the built-in close Button and permits passive
dismissal. `close_on_escape` and `close_on_outside` refine which passive paths
are allowed. All three have matching client inputs.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/explicit_decision.py"
  title="Require an explicit decision"
/>

With `dismissible=False`, Escape, backdrop presses, and the built-in close
control are unavailable. Actions with `close_attrs` still work, so a deliberate
workflow can always complete.

Outside dismissal requires a press that starts and ends on this Dialog's
backdrop. Dragging from content to the backdrop does not close it.

## Place initial focus

The server `initial_focus` input and matching client `initialFocus` input accept
`auto` or `title`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/initial_focus.py"
  title="Place initial focus"
/>

- `auto` keeps native `[autofocus]` and browser Dialog focus steps. Put
  `autofocus` on the control that should receive focus first.
- `title` focuses the visible title. Use it for long or structured content so
  reading starts at the top without jumping to a later control.

Tab and Shift+Tab stay within the nearest open Dialog. Nested Dialog controls
do not enter a parent's focus loop. Closing returns focus to the element that
was active before opening when it remains available. A workflow that needs a
different destination can focus it after the close callback.

Do not add `tabindex` to the native Dialog. CDialog owns its focus contract and
rejects that attribute.

## Scroll long content

The server `scroll` input and matching client `scroll` input accept `body` or
`dialog`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/long_content.py"
  title="Scroll long Dialog content"
/>

- `body` keeps the header and actions visible while the body scrolls.
- `dialog` scrolls the complete surface.

Both modes stay inside the dynamic viewport. `full` fills that viewport and
removes ordinary radius, border, and shadow. Long titles and actions wrap.

## Use a native Dialog Form

A native `<form method="dialog">` requests closure and sets the Dialog return
value to the accepted submitter's value.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/dialog_form.py"
  title="Use a native Dialog Form"
/>

```citry-html
<c-CDialog
  $c-props="{
    onOpenChange: (open, detail) => {
      if (detail.reason === 'native') result = detail.returnValue;
    },
  }"
>
  <c-fill name="title">
    Choose a constellation
  </c-fill>
  <c-fill name="default">
    <form method="dialog">
      <button value="Orion">Orion</button>
      <button value="Cygnus">Cygnus</button>
    </form>
  </c-fill>
</c-CDialog>
```

In uncontrolled mode, the browser performs the native close. In controlled
mode, CDialog intercepts only that final close so the owner can accept or
decline it through `onOpenChange`. Validation, the submit event, reset,
`FormData`, and Citry Events remain native.

For asynchronous work, control `open`, show loading on the submit Button, keep
the Dialog open on validation or transport failure, and close after success.
Do not put `close_attrs` on a submit Button when closing before the result would
lose feedback.

## Nest Dialogs

Nest one `CDialog` inside another body when a focused subtask genuinely needs a
second modal layer.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/nested_dialogs.py"
  title="Nest Dialogs"
/>

Each Dialog owns only its nearest activators, close actions, focus loop, and
scroll-lock claim. Closing the nested Dialog leaves its parent open and returns
focus to the nested trigger. Closing a parent also closes its open descendants,
so an invisible nested modal cannot retain page inertness. Escape affects the
top Dialog.

Avoid deep modal stacks. A page, expansion, or inline disclosure is usually
easier to understand after one nested task.

## Theme and customize Dialog

Dialog follows the surrounding `color-scheme` even in the browser top layer.
Set documented `--cui-dialog-*` variables on an ancestor or the Dialog root.
Use public `data-citry-ui-part` selectors for targeted region styling.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/theme_customization.py"
  title="Theme Dialog"
/>

```css
.moonlit-observatory {
  --cui-dialog-backdrop: rgb(15 23 42 / 78%);
  --cui-dialog-background: #172033;
  --cui-dialog-foreground: #e0e7ff;
  --cui-dialog-border-color: #818cf8;
  --cui-dialog-radius: 1.25rem;
}

.moonlit-observatory [data-citry-ui-part="title"] {
  letter-spacing: 0.03em;
}
```

The optional `close` slot replaces only the icon inside the built-in accessible
Button. Keep its content non-interactive. CDialog retains its label, behavior,
and public `close` selector.

The documented variables, selectors, and reflected attributes are public CSS
API. `.cui-*` classes, `--_cui-*` variables, and behavior markers are private.

## Support narrow viewports and zoom

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/narrow_dialog.py"
  title="Use a full Dialog"
/>

Dialog uses logical properties, wraps actions, and constrains ordinary sizes
to the dynamic viewport. It supports nested light and dark scopes, RTL content,
forced colors, text spacing, and high zoom without requiring motion.

The built-in close Button is at least 2.5rem square and always has an accessible
name. A non-dismissible Dialog must provide an explicit action or another clear
completion path.

Without JavaScript, `open=False` keeps content in a closed native Dialog.
`open=True` shows non-modal content because only browser `showModal()` enters
the top layer. Client activation upgrades it immediately.
