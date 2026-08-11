---
title: Toggle
description: Build standalone or grouped pressed Buttons with Citry UI.
---

# Toggle

Use `CToggle` for a Button whose pressed state persists. Use `CToggleGroup` for related exclusive or multiple choices.

## Toggle at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/at_a_glance.py" title="Toggle at a glance" />

## Choose Toggle, Switch, or Button Group

Toggle changes an active tool or view. Switch changes an immediate setting. Button Group groups related actions without selection.

## Toggle one tool

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/standalone.py" title="Toggle one tool" />

## Select one or several values

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/groups.py" title="Compare single and multiple Toggle Groups" />

## Keep one value selected

`mandatory=True` rejects only the user action that would clear the final value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/mandatory.py" title="Keep one Toggle selected" />

## Control selection in the browser

Client inputs are passed with `$c-props="{...}"`. `onValueChange` reports the next requested value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/controlled.py" title="Control Toggle selection" />

## Choose presentation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/presentation.py" title="Compare Toggle variants and sizes" />

## Customize Toggle

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoggle/snippets/customization.py" title="Customize Toggle" />

## Accessibility and behavior

Each Toggle is a native Button with `aria-pressed`. Space and Enter activate it. All enabled Toggles remain in ordinary Tab order; the family does not claim arrow keys or Form submission.

<!-- UI_LIBRARY_API_REFERENCE -->
