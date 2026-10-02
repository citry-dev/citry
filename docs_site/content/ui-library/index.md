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
