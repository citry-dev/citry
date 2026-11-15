---
title: Citry UI
description: Build application interfaces with Citry's first-party styled component library.
---

# Citry UI

Citry UI gives you ready-made, styled components, such as buttons, tabs,
dialogs, and form inputs, so you do not have to build and style them
yourself. The Citry team maintains it. Each component renders its HTML on
the server, adds its own browser behavior, and lets you change its look
with CSS variables.

Citry UI is a separate package from `citry`, so you install it only when
you want these components.

## Get started

1. [Install and register Citry UI](/ui-library/installation/).
2. Pick a component from the [list below](#components).
3. [Change colors and styles](/ui-library/theming/) to match your
   application.

## Components

<c-ui-library-list />

## Pass request data safely { #pass-request-data-safely }

Request data is any value a visitor controls, such as a query
parameter, form field, or header. A plain string you pass to a
component, such as a label or a cell value, shows as text.

URL inputs check the scheme and raise `ValueError` for any other:

- link inputs such as `href` and `action` accept a relative URL or an
  `http:`, `https:`, `mailto:`, `sms:`, or `tel:` URL;
- image inputs such as `src` accept a relative URL or an `http:`,
  `https:`, `blob:`, or `data:image/` URL.

See [Check URL attributes](/security/#check-url-attributes) for the
other URLs on your page.

Two inputs need checks of your own:

- Build attribute maps (`attrs=` and the other `*_attrs=` arguments) in
  your own code. Citry UI raises `ValueError` for a key such as
  `onclick`, a key the component sets itself, or a key that starts with
  `data-citry-`, `data-cev` or `data-cid`, because Citry's browser code
  acts on those names. It does not check what the other names mean.
  Attrs a component hands you in slot data, such as `activator_attrs`,
  can go on a `<c-CButton>` unchanged or with your own keys added.
- Choose `style` values in your own code. Citry does not check them as
  CSS, so a value from request data can add declarations of its own,
  such as a background image from another site.

## Upgrade with care { #upgrade-with-care }

Citry UI is in alpha, so a new release can change how a component looks
or behaves. Read the
[Citry UI changelog](https://github.com/citry-dev/citry/blob/main/packages/py/citry_ui/CHANGELOG.md){: target="_blank" rel="noopener"}
before you upgrade, and check the component states your application
depends on.

## Report a problem { #help-shape-citry-ui }

Report bugs, missing states, accessibility problems, and awkward APIs in
the
[Citry issue tracker](https://github.com/citry-dev/citry/issues){: target="_blank" rel="noopener"}.
Include the component name, the Citry UI version, your browser, and a
small example that shows the problem.
