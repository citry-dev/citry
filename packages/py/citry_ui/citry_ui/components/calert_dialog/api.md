---
title: AlertDialog
description: Ask for an immediate cancel-or-action decision in an urgent modal prompt.
---

# AlertDialog

Use `CAlertDialog` when a consequential action needs an immediate explicit
decision. It requires a visible title, concise description, Cancel control,
and Action control. Use `CAlert` for persistent feedback and `CDialog` for
general modal content, forms, or more than two decisions.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/calert_dialog/snippets/at_a_glance.py" title="AlertDialog at a glance" />

```citry-html
<c-CAlertDialog id="delete-project">
  <c-fill name="activator" data="{activator_attrs}">
    <c-CButton c-attrs="activator_attrs" intent="danger">Delete project</c-CButton>
  </c-fill>
  <c-fill name="title">Delete this project?</c-fill>
  <c-fill name="description">This permanently removes all project data.</c-fill>
  <c-fill name="cancel" data="{cancel_attrs}">
    <c-CButton c-attrs="cancel_attrs" variant="outline">Keep project</c-CButton>
  </c-fill>
  <c-fill name="action" data="{action_attrs}">
    <c-CButton c-attrs="action_attrs" intent="danger">Delete</c-CButton>
  </c-fill>
</c-CAlertDialog>
```

## Choose the right interruption

AlertDialog is intentionally narrow. The native surface has
`role="alertdialog"`, a required name and description, and exactly two owned
decision regions. Outside presses never close it. Escape acts like Cancel when
`close_on_escape=True`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/calert_dialog/snippets/blocking_error.py" title="Acknowledge a blocking error" />

## Control asynchronous decisions

A supplied client `open` Boolean is authoritative. `onOpenChange` requests the
next state; accept it when application work is ready. Cancel and Action both
use `reason="action"`; inspect `detail.returnValue` for `"cancel"` or
`"action"`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/calert_dialog/snippets/controlled_action.py" title="Control an asynchronous decision" />

```citry-html
<c-CAlertDialog
  $c-props="{
    open: confirming,
    onOpenChange: (open, detail) => {
      if (detail.returnValue === 'action') archiveThenClose()
      else confirming = open
    }
  }"
>
  ...
</c-CAlertDialog>
```

Omit or supply `null` for the client `open` prop to release control while
preserving the effective state.

## Compose native Buttons safely

`CButton` already owns `type="button"`; pass only `*_attrs` to it. A native
Button must consume both the attribute mapping and adjacent type field.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/calert_dialog/snippets/native_buttons.py" title="Use native decision Buttons" />

```citry-html
<c-fill name="cancel" data="{cancel_attrs, cancel_type}">
  <button c-type="cancel_type" c-bind="cancel_attrs">Stay</button>
</c-fill>
```

Native click handlers run before the component open-change request. This lets
the application perform or schedule domain work without a duplicate custom
confirm event.

## Focus and accessibility

Cancel receives initial focus so the destructive choice is never the default.
Tab and Shift+Tab remain inside the modal. Closing restores the connected
activator unless application code deliberately moved focus elsewhere. The
required title and description become the exact `aria-labelledby` and
`aria-describedby` targets.

## Size and customization

Sizes are `sm`, `md`, and `lg`; `sm` is the default. Full-screen workflows
belong to Dialog. AlertDialog shares Dialog layout behavior while exposing
family-specific variables.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/calert_dialog/snippets/sizes.py" title="Compare AlertDialog sizes" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/calert_dialog/snippets/customization.py" title="Customize AlertDialog" />

```css
.archive-alert {
  --cui-alert-dialog-radius: 1.25rem;
  --cui-alert-dialog-inline-size: 30rem;
  --cui-alert-dialog-border-color: #8b5cf6;
}
```

See [`api.yml`](api.yml) for the exhaustive inputs, callbacks, variables,
attributes, selectors, slots, and public interfaces.

<!-- UI_LIBRARY_API_REFERENCE -->
