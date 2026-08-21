---
title: Theme Citry UI
url: https://citry.dev/v/0.4.2/ui-library/theming/
description: "Customize Citry UI with color schemes, CSS variables, and stable component parts."
---
# Theme Citry UI

Citry UI supplies styled light and dark defaults. Your application chooses the
active color scheme and can override the documented variables inherited by a
component subtree.

## Customize one component

Every component accepts `class_` and `style` directly on its documented root.
The underscore keeps the input valid in Python and the same name is used in a
component tag.


```citry-html
<c-CButton
  class_="checkout-action"
  c-style="{
    'inline-size': button_width,
  }"
>
  Continue
</c-CButton>
```


Both inputs accept Citry's structured class/style values. Use `attrs` for
other native, ARIA, Alpine, and `data-*` attributes. If `attrs` also contains
class or style values, Citry merges them with the direct inputs.
Python annotations can import the corresponding `CClassValue` and
`CStyleValue` aliases from `citry_ui`.

## Theme a component subtree


```css
.billing-app {
  color-scheme: dark;
  --cui-button-background: #6d28d9;
  --cui-button-foreground: #ffffff;
  --cui-button-border-color: #a78bfa;
  --cui-tabs-accent: #c4b5fd;
}
```



```citry-html
<section class="billing-app">
  <c-CButton>
    Create invoice
  </c-CButton>
</section>
```


## Override a documented part

`data-citry-ui-part` identifies a stable element in a component's public
anatomy. Use it when a variable cannot express the focused change:


```css
.billing-app [data-citry-ui-part="header-cell"] {
  font-weight: 700;
  text-transform: uppercase;
}
```


Each component page lists its public parts and variables. Internal `.cui-*`
classes and `--_cui-*` variables are implementation details.

## Keep application ownership explicit

Citry UI responds to `color-scheme`, but it does not choose, persist, or toggle
an application's theme. Put the scheme on the application root or on a nested
themed region. Native controls and overlays then inherit the same scope.