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

Request data is anything a visitor sends, such as a query
parameter, form field, or header. A plain string you pass to a
component, such as a label or a cell value, shows as text.

URL inputs check the scheme and raise `ValueError` for any other:

- link inputs such as `href` and `action` accept a relative URL or an
  `http:`, `https:`, `mailto:`, `sms:`, or `tel:` URL;
- image inputs such as `src` accept a relative URL or an `http:`,
  `https:`, `blob:`, or `data:image/` URL.

See [Check URL attributes](/security/#check-url-attributes) for the
other URLs on your page.

These inputs need checks of your own:

- Build attribute maps (`attrs=` and the other `*_attrs=` arguments)
  in your own code. Citry UI raises `ValueError` for a key such as
  `onclick`, a key the component sets itself, `is` or `key`, or a key
  that starts with `data-citry-`, `data-cui-`, `data-cev` or
  `data-cid`. Citry's browser code finds its elements by those names,
  and `is` and `key` change which element is rendered, so a key from
  request data could make the page act differently. Citry UI does not
  check what the other names mean. Choose the values of these keys
  in your own code too, because each one makes the browser act:
    - a URL, such as `formaction`, `href`, or `src`, which Citry UI
      checks only where the component writes a link, a form, an
      image, or a submit button;
    - `form`, which makes a submit button submit another form, or
      moves a field into another form when that form is submitted;
    - `commandfor` or `popovertarget`, which lets a button open
      another dialog or popover on the page;
    - `id`: Citry UI's browser code finds some elements by id. If an
      earlier element on the page has the same id as the form a
      component names, the browser finds that element first, and the
      component's values are missing when the form is submitted;
    - `name`, which sets the name a field is sent under. A field's
      name can also hide a property of its form that browser code
      reads.
- Choose `style` values in your own code. Citry does not check them as
  CSS, so a value from request data can add declarations of its own,
  such as a background image from another site.

A component can give you attrs in slot data, such as `CDialog`'s
`activator_attrs`. Pass them to a `<c-CButton>` as they are, or add
your own keys with `c-attrs="{**activator_attrs, 'title': 'More'}"`.

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
