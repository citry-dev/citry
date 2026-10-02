---
title: Theme Citry UI
description: Customize Citry UI with color schemes, CSS variables, and stable component parts.
---

# Theme Citry UI

Citry UI components come with light and dark styles. To match your
application, set CSS variables on a part of the page, add a class or style
to one component, or restyle a named part inside a component. Each
component's page lists the variables and parts it supports.

## Theme part of the page { #theme-a-component-subtree }

Set `--cui-*` variables on an element. Every Citry UI component inside it
uses them:

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

## Choose light or dark { #choose-the-color-scheme-in-your-application }

Citry UI follows the CSS `color-scheme` property. Set it on your
application's root element, or on one region as in the example above.
Native controls and overlays inside that element use the same scheme.

Citry UI does not pick the scheme for you, remember the user's choice, or
provide a toggle. Your application does that.

## Style one component { #customize-one-component }

Every component accepts `class_` and `style`, which Citry puts on the
element that the component's page lists as its root. The underscore in `class_` makes it a valid
Python name; use the same name in a template:

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

Both accept the same class and style values as Citry's own `class` and
`style` attributes. For type annotations, import the `CClassValue` and
`CStyleValue` aliases from `citry_ui`.

To set other HTML attributes, such as ARIA or `data-*` attributes, pass
them in `attrs`. A `class` or `style` in `attrs` is merged with `class_`
and `style`.

`attrs` rejects Vue directives such as `:open` or `@click` with an error
that names the component. Write those on the component tag in your
template instead.

## Restyle a named part { #override-a-documented-part }

When no variable covers the change you want, target a named part of the
component. Each part listed on a component's page carries a
`data-citry-ui-part` attribute:

```css
.billing-app [data-citry-ui-part="header-cell"] {
  font-weight: 700;
  text-transform: uppercase;
}
```

!!! warning "Style only documented variables and parts"

    The `.cui-*` classes and `--_cui-*` variables you may see in the
    browser are internal and can change in any release. Use only the
    variables and parts listed on each component's page.
