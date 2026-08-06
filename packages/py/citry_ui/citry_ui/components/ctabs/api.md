---
title: Tabs
description: Organize keyboard-accessible views with Citry UI Tabs.
---

# Tabs

Switch between related views in place. `CTabs`, `CTab`, and `CTabPanel`
provide the ARIA structure, roving focus, activation modes, and controlled
selection.

## Tabs at a glance

Compare underline and pill treatments. Click a Tab or use the arrow keys. The
disabled **Crew** Tab shows the unavailable state.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/at_a_glance.py"
  title="Tabs at a glance"
/>

## Compose Tabs, Tab controls, and Panels

Compose one `CTabs` root from matching `CTab` and `CTabPanel` declarations.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/night_sky_guide.py"
  title="Night sky guide"
/>

```citry-html
<c-CTabs
  default_value="planets"
  aria_label="Night sky topics"
>
  <c-CTab value="planets">
    Planets
  </c-CTab>
  <c-CTab value="nebulae">
    Nebulae
  </c-CTab>

  <c-CTabPanel value="planets">
    Worlds orbiting stars
  </c-CTabPanel>
  <c-CTabPanel value="nebulae">
    Clouds of gas and dust
  </c-CTabPanel>
</c-CTabs>
```

Each component has one job:

- `CTabs` owns selection and configuration, renders the root and the single
  accessibly named `role="tablist"`, and groups the generated controls.
- `CTab` declares one value and its native Tab Button content.
- `CTabPanel` declares the view paired with that value.

Place the Tab declarations first, followed by their matching Panels. Tab
values are non-empty and unique, Panel values are non-empty and unique, and
both value sets must match. The initial value must identify an enabled Tab.
Provide either `aria_label` or `aria_labelledby` on `CTabs` to name the
generated Tab list.

`CTab` and `CTabPanel` are declarations, not standalone rendered components.
`CTabs` collects them before it renders the final Tab list and Panels. Using a
declaration outside `CTabs` fails. The default slot may contain formatting
whitespace, control flow, and transparent components, but no other rendered
HTML. This lets `CTabs` generate one correct semantic list without asking you
to maintain a structural-only list component.

## Try the configuration

Change accent, variant, density, orientation, alignment, growth, focus looping,
and disabled state. The controls use public CSS variables and `$c-props`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/configuration.py"
  title="Configure Tabs"
/>

## Choose a variant

Use `underline` for low-emphasis navigation. Use `pill` when the choices need a
contained track and stronger selected state.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/variants.py"
  title="Compare Tabs variants"
/>

## Set density and available width

`default`, `comfortable`, and `compact` change Tab height and padding. Enable
equal width when every Tab should share the available main-axis space.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/density_and_growth.py"
  title="Compare density and growth"
/>

## Align and orient Tabs

Alignment follows the main axis. Vertical orientation moves the Tab list beside
the active Panel and switches keyboard movement to Up and Down.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/alignment_and_orientation.py"
  title="Align and orient Tabs"
/>

## Control selection from JavaScript

Supplying client `value` makes selection controlled. A user request calls
`onValueChange`; the owner decides whether to commit the requested value.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/controlled_selection.py"
  title="Control Tabs selection"
/>

```citry-html
<c-CTabs
  default_value="planets"
  aria_label="Night sky topics"
  $c-props="{
    value: currentTopic,
    onValueChange: (value, detail) => {
      currentTopic = value;
      observationLog.record(detail);
    },
  }"
>
  ...
</c-CTabs>
```

Omit client `value` for immediate uncontrolled selection. Removing a controlled
value continues uncontrolled from the last valid selection. An invalid value
keeps the last valid selection, reports a diagnostic, and still reports eligible
user requests.

Other supplied client inputs override their server inputs. Removing one restores
the server value. `null` is valid only for `direction`, where it restores
inherited browser direction. Other invalid values report a diagnostic and use
their server value.

!!! note
    `onValueChange` runs only for a different enabled value. Initial selection
    and owner updates do not run it. Return values do not cancel the request.

    If client-owned DOM work removes the selected Tab, Tabs selects the next
    enabled Tab at that position, then the previous enabled Tab, then the first
    enabled Tab. If none remains, all Tabs and Panels become inactive and the
    event does not run.

## Disable selection

Disable one `CTab` to keep it visible but unavailable. Disable `CTabs` to block
the whole group without losing the selected value.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/disabled_states.py"
  title="Disable Tabs"
/>

## Choose keyboard activation

Automatic activation selects as focus moves. Manual activation moves focus
first, then waits for Enter or Space.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/keyboard_activation.py"
  title="Compare keyboard activation"
/>

| Context | Key | Result |
|---|---|---|
| Horizontal LTR | Right / Left | Focus next / previous enabled Tab. |
| Horizontal RTL | Right / Left | Focus previous / next enabled Tab. |
| Vertical | Down / Up | Focus next / previous enabled Tab. |
| Either | Home / End | Focus first / last enabled Tab. |
| Manual activation | Enter / Space | Select the focused Tab. |
| Automatic activation | Arrow, Home, or End focus movement | Focus and select together. |

Horizontal Tabs do not consume Up or Down. Vertical Tabs do not consume Left
or Right. Disabled Tabs are skipped, and `loop=False` stops movement at either
end. Pointer activation selects and focuses the clicked enabled Tab.

Each Tab is a native `button type="button"` with `role="tab"`,
`aria-controls`, `aria-selected`, and roving `tabindex`. Each Panel has
`role="tabpanel"`, `aria-labelledby`, and `tabindex="0"`. Panels remain mounted;
inactive Panels receive `hidden`.

Without JavaScript, the server-selected Panel remains visible and all ARIA
relationships are valid, but the Tab Buttons do not switch Panels.

## Use long Tab lists

Long horizontal lists scroll inside the Tab-list surface. Pointer and keyboard
selection bring the active Tab into view. Overflow arrows and menus are not part
of the current component.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/long_list.py"
  title="Scroll a long Tab list"
/>

## Nest Tabs

Place nested Tabs inside a `CTabPanel`. Each root keeps independent selection,
focus, configuration, and callbacks.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/nested_tabs.py"
  title="Nest Tabs"
/>

```citry-html
<c-CTabPanel value="jupiter">
  <c-CTabs
    default_value="moons"
    aria_label="Jupiter topics"
  >
    ...
  </c-CTabs>
</c-CTabPanel>
```

A Tab and Panel block access to their parent's Tabs context. Rendering Tabs
inside a Tab fails because native Buttons cannot contain interactive content. A
nested root also cannot sit directly among another root's declarations.

## Support text direction

Horizontal arrow keys follow visual direction. In RTL, Right moves toward the
previous declared Tab and Left moves toward the next. Vertical movement is
unchanged.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/direction.py"
  title="Compare LTR and RTL Tabs"
/>

Set server `direction` to `ltr` or `rtl`, or leave it unset to inherit computed
browser direction. Client `direction: null` explicitly restores inheritance.

## Theme and customize Tabs

Tabs follow the surrounding `color-scheme`. Set documented `--cui-tabs-*`
variables on an ancestor or one Tabs root to customize color and geometry.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/theme_customization.py"
  title="Theme Tabs"
/>

The two surfaces use the same component markup. Their explicit light and dark
schemes and public CSS variables supply every visual difference.
