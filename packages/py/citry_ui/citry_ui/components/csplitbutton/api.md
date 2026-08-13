---
title: Split Button
description: Keep one dominant action visible beside a Menu of related actions.
---

# Split Button

Use `CSplitButton` when one action is clearly dominant and a short Menu holds
closely related alternatives. The primary and Menu trigger are separate native
Buttons with separate names and Tab stops.

Use `CButton` for one action, `CButtonGroup` for visible peers, and `CMenu` when
there is no dominant action. Use `CSelect` or `CCombobox` when the reader is
choosing a value rather than running an action.

Related guidance: [Button](/ui-library/components/button/),
[Button Group](/ui-library/components/button-group/),
[Menu](/ui-library/components/menu/), the
[WAI-ARIA APG Menu Button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/),
and the [native Button element](https://developer.mozilla.org/docs/Web/HTML/Reference/Elements/button).

## Split Button at a glance

Save the specimen directly or open related save actions. The Menu does not
repeat the dominant Save action.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/at_a_glance.py" title="Split Button at a glance" />

## Compose the two actions

Supply a nonempty group `label`, a specific `menu_label`, visible primary
content, and at least one existing Menu declaration.

```citry-html
<c-CSplitButton
  label="Save specimen actions"
  menu_label="More save specimen actions"
>
  <c-fill name="default">Save specimen</c-fill>
  <c-fill name="menu">
    <c-CMenuItem value="save-copy">Save a copy</c-CMenuItem>
    <c-CMenuItem value="export">Export record</c-CMenuItem>
  </c-fill>
</c-CSplitButton>
```

Direct Python composition uses the same slots and public Menu declarations:

```citry
from citry_ui import CMenuItem, CSplitButton

save_actions = CSplitButton(
    label="Save specimen actions",
    menu_label="More save specimen actions",
    slots={
        "default": "Save specimen",
        "menu": (
            CMenuItem(
                value="save-copy",
                slots={"default": "Save a copy"},
            ),
            CMenuItem(
                value="export",
                slots={"default": "Export record"},
            ),
        ),
    },
)
```

The next example renders both composition forms.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/basic_actions.py" title="Template and Python composition" />

## Submit and reset native Forms

Only the primary Button participates in a Form. Set `type="submit"` or
`type="reset"`, then pass `name`, `value`, `form`, and submitter overrides
through `primary_attrs`. The Menu Button and Menu items never submit.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/forms.py" title="Submit, reset, and related export actions" />

An open Menu closes internally before an uncontrolled primary default action.
Its public `onOpenChange` action notice runs afterward, so the callback cannot
cancel or duplicate the accepted native submit or reset. A valid
`form.requestSubmit(primary)` follows the same rule. Native constraint
validation can prevent submission before a submit event; that path leaves the
Menu unchanged.

Without JavaScript, an enabled primary submit or reset remains a useful native
Button, while server disabled or loading output uses CButton's native-safe
fallback. The Menu Button cannot toggle before initialization. A closed Menu
stays noninteractive in server flow, and an initially open Menu remains
readable; neither path can submit the Form.

## Control Menu visibility

Pass a Boolean client `open` to own Menu visibility. Omit it or pass `null` to
release control from the latest committed state. `onOpenChange` reports Menu
gestures and the primary action close request. Forced disabled or ancestor
closes cannot be refused.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/controlled_menu.py" title="Control Split Button Menu visibility" />

Primary native events remain distinct from Menu callbacks. Pass `@click`
through `primary_attrs`, and use `onAction` for valued Menu commands and
choices.

## Choose presentation and placement

`variant`, `intent`, and `size` style both Buttons. `block` fills the available
inline size while the Menu Button keeps its target width. `placement` and
`match_width` use the full joined group as their anchor, not the narrow Menu
Button.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/variants_and_sizes.py" title="Variants, sizes, and placement" />

## Keep alternatives available while loading

`loading` affects only the primary action. It remains focusable, exposes busy
state, and blocks new activation while an otherwise enabled Menu remains
available. Use common `disabled` when both halves must be unavailable, or the
per-half inputs when only one action is unavailable.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/disabled_and_loading.py" title="Disabled and loading states" />

Native disabled `fieldset` ancestry remains authoritative. When disabling the
Menu hides focused Menu content, focus moves to an enabled primary Button or a
safe modal/document fallback.

## Reuse the complete Menu collection

The `menu` slot accepts the current `CMenuItem`, `CMenuCheckboxItem`,
`CMenuRadioGroup`, `CMenuRadioItem`, `CMenuGroup`, `CMenuSeparator`, and
`CMenuSubmenu` declarations. Their values, callbacks, paths, parts, keyboard
rules, and content limits remain the CMenu contract.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/menu_composition.py" title="Commands, choices, groups, and submenus" />

Do not repeat the primary action in the Menu. Give the Menu Button a full
secondary name such as “More save specimen actions”, not only “More”.

## Use the two-stop keyboard model

Tab visits the primary Button and then the Menu Button in DOM order in both
LTR and RTL. Enter and Space activate the focused native Button. Arrow Down or
Arrow Up on the Menu Button opens and focuses the first or last item. The
primary does not gain Menu arrow behavior.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/focus_and_keyboard.py" title="Focus and keyboard behavior" />

Once open, the collection uses CMenu arrow navigation, Home, End, typeahead,
submenus, Escape, and Tab behavior without trapping focus.

## Compose with clipping and Dialogs

The Menu uses the native top layer and the shared anchored-layer coordinator.
It escapes ordinary overflow while placement and width still follow the full
SplitButton root. A sibling Dialog opened by either action owns modal focus.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/layers_and_dialog.py" title="Clipped layers, ShadowRoot, and sibling Dialog" />

Render Dialog and other peer overlays as siblings. Menu declaration content
still follows CMenu's noninteractive item-content boundary.

## Customize the joined control and Menu

Both Buttons consume the public `--cui-button-*` variables, and the Menu keeps
the public `--cui-menu-*` contract. SplitButton adds variables for its divider,
Menu Button width, and joined radius. Stable part selectors target each half
and its content without changing semantic ownership.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitbutton/snippets/customization.py" title="Brand and environment customization" />

The horizontal compound keeps the primary at logical start in RTL, preserves
the Menu Button target width at narrow sizes, removes motion under reduced
motion, and retains visible focus and divider boundaries in forced colors.

## Choose explicit composition for a different policy

Compose `CButtonGroup` and `CMenu` when the primary must be a link, actions are
equal peers, the layout must be vertical, or the two surfaces need separate
state owners. SplitButton intentionally keeps one dominant command, one Menu
owner, one horizontal anatomy, and no imperative methods or custom DOM events.

## Trust the four attribute destinations deliberately

`attrs`, `primary_attrs`, `trigger_attrs`, and `menu_attrs` are copied and
validated for their documented roots. They accept ordinary styling, language,
permitted ARIA, and `data-*` except `data-citry-*`, `data-cev*`, `data-cid*`,
and owned reflections. `@event` and `x-on:event` Alpine listeners are allowed;
raw `on*` browser-expression attributes are rejected. The primary also accepts
the documented native Form attributes, but URL-like action destinations remain
consumer-owned and are not sanitized or trusted by Citry. Component-owned
identity, semantics, state, focus order, popover targeting, Citry runtime
fields, and structural Alpine ownership are rejected.

Primary content accepts text and decorative noninteractive content. The final
Button needs a nonempty accessible name from visible text, `aria-label`, or
`aria-labelledby`. Menu declarations retain CMenu's exact trust boundary.

<!-- UI_LIBRARY_API_REFERENCE -->
