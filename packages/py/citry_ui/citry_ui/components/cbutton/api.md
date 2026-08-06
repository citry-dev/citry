---
title: Button
description: Render styled native actions, links, and form submitters with Citry UI Button.
---

# Button

Use `CButton` for prominent actions and links. It renders a native `<button>`
by default and a native `<a>` when `href` is set. Both roots share styled
variants, semantic intents, three sizes, decoration slots, and a
focus-preserving loading state.

## Button at a glance

Solid, outline, and ghost variants set emphasis. Loading and disabled both
block activation, but only loading keeps the Button focusable in the browser.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/at_a_glance.py"
  title="Button at a glance"
/>

## Create an action

`CButton` defaults to `type="button"`, so it does not accidentally submit a
surrounding form.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/basic_actions.py"
  title="Create Button actions"
/>

```citry-html
<c-CButton intent="primary">
  Record specimen
</c-CButton>
```

Compose the same Button in Python:

```python
from citry_ui import CButton

record_button = CButton(
    intent="primary",
    slots={"default": "Record specimen"},
)
```

## Navigate with a link

Set the server `href` input for navigation. `CButton` renders a native anchor,
so modifier clicks, context menus, link previews, and browser navigation remain
available.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/navigation.py"
  title="Use Button styling for links"
/>

```citry-html
<c-CButton
  href="https://example.com/field-guide/ferns/"
  c-attrs="{'target': '_blank', 'rel': 'noreferrer'}"
>
  Read the fern guide
</c-CButton>
```

The anchor keeps the same `inline-flex` layout as an action Button. Pass link
attributes such as `target`, `rel`, and `download` through `attrs`. `href` is
server-only because changing the native root after render would replace the
element and its browser state.

## Configure Button

Server inputs are passed in Python through `<c-CButton ... />` attributes or a
`CButton(...)` composition call. Client inputs are passed in the browser through
the `$c-props="{...}"` attribute.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/configuration.py"
  title="Configure Button"
/>

A supplied valid client input wins over its server input. Removing it restores
the server value. Invalid client values report one diagnostic per invalid
episode and use the server value for that field.

```citry-html
<c-CButton
  variant="outline"
  $c-props="{
    loading: scanning,
    disabled: !trailOpen,
    variant: preferredVariant,
  }"
>
  Begin survey
</c-CButton>
```

`type`, `href`, and `attrs` remain server-only because they define native
structure and browser behavior.

## Choose a variant

Use `solid` for the strongest action, `outline` for a visible alternative, and
`ghost` for a quiet action near stronger controls.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/variants.py"
  title="Compare Button variants"
/>

## Choose an intent

Intent communicates meaning without changing mechanics. Use `primary` for the
main action, `success` for a completed or beneficial outcome, `warn` for
caution, `danger` for a destructive outcome, and `neutral` when no semantic
color is needed.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/intents.py"
  title="Compare Button intents"
/>

## Set size and available width

`sm`, `md`, and `lg` change target height, padding, and text size. Set
`block=True` to fill the available inline size. Labels wrap instead of forcing
horizontal page overflow.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/sizes_and_layout.py"
  title="Compare Button sizes and layout"
/>

## Add decoration

Use `start` and `end` for icons or other non-interactive decoration. Their
order follows text direction.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/decorations.py"
  title="Decorate Button content"
/>

```citry-html
<c-CButton variant="outline">
  <c-fill name="start">
    <svg aria-hidden="true">...</svg>
  </c-fill>
  <c-fill name="default">
    Identify bloom
  </c-fill>
  <c-fill name="end">
    <svg aria-hidden="true">...</svg>
  </c-fill>
</c-CButton>
```

Do not place links, inputs, or other interactive content inside a Button. For
icon-only content, pass an accessible name through `attrs`, such as
`{"aria-label": "Inspect leaf"}`. `CButton` does not add square icon-Button
geometry.

## Show loading and disabled states

The server `loading` input sets the initial pending state. The client `loading`
input is passed through `$c-props` when browser code owns later changes.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/loading_states.py"
  title="Compare Button loading states"
/>

Loading blocks click, keyboard, submit, reset, `.click()`, and
`requestSubmit(button)` activation. It keeps focus on the Button, exposes
`aria-busy="true"` and `aria-disabled="true"`, and preserves the accessible
name. The application still owns the operation and decides when loading begins
and ends.

Loading placement changes visual replacement:

| Position | Result |
|---|---|
| `start` | Replace the start decoration; keep the label and end visible. |
| `center` | Replace all ordinary visual content without changing intrinsic width. |
| `end` | Replace the end decoration; keep the start and label visible. |

If a start or end decoration is absent, loading reserves that position to avoid
overlapping the label. The optional `loading` slot replaces the built-in
spinner with a compact visual indicator; the root owns pending semantics.

`disabled=True` uses native `disabled` behavior on an action Button. On a link,
it removes `href`, removes the link from the focus order, and blocks scripted
clicks. A loading link also removes `href` but stays focusable. Both restore the
original destination when their unavailable state clears. Use loading for an
in-progress operation and disabled for an unavailable control.

A disabled enclosing `CForm` always wins over the Button's local value. Action
Buttons become natively disabled; Button links become inert. Both reflect the
effective state through `aria-disabled` and `data-disabled`.

## Use native forms

Set the server `type` input to `submit` or `reset` for native form behavior.
Native submitter attributes pass through the server `attrs` mapping.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/native_forms.py"
  title="Use Button in a native form"
/>

Supported native attributes include `name`, `value`, `form`, `formaction`,
`formenctype`, `formmethod`, `formnovalidate`, and `formtarget`. Listen to native
`click`, `submit`, and `reset` events with Alpine. `CButton` does not duplicate
them with component callbacks or custom DOM events.

Form attributes and `type="submit"` or `type="reset"` are incompatible with
`href`. Use a Button for form actions and a link for navigation.

Without JavaScript, server-disabled and server-loading Buttons both render with
native `disabled`. Submit and reset Buttons otherwise keep native behavior.

## Theme and customize Button

Button follows the surrounding `color-scheme`. Set documented
`--cui-button-*` variables on an ancestor or one root. Use public
`data-citry-ui-part` selectors for targeted element styling.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/theme_customization.py"
  title="Theme Button"
/>

```css
.garden-actions {
  --cui-button-background: #166534;
  --cui-button-foreground: #ffffff;
  --cui-button-hover-background: #14532d;
  --cui-button-focus-color: #7c3aed;
}

.garden-actions [data-citry-ui-part="content"] {
  letter-spacing: 0.025em;
}
```

The documented variables, parts, and reflected attributes are public CSS API.
`.cui-*` classes and `--_cui-*` variables are private.

## Accessibility and keyboard behavior

The native Button supplies action and form semantics; the native anchor
supplies navigation and link semantics. Default content or consumer ARIA
attributes must provide an accessible name. Focus-visible and forced-colors
treatments remain visible.

Minimum heights are 2.25rem, 2.5rem, and 2.75rem for `sm`, `md`, and `lg`.
The surrounding layout remains responsible for additional target spacing
required by its context.
