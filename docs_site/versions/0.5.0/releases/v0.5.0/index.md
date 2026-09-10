---
title: v0.5.0 (2026-09-09)
url: https://citry.dev/v/0.5.0/releases/v0.5.0/
description: "What changed in citry v0.5.0 (2026-09-09)."
---
# v0.5.0 (2026-09-09)

## Added

- Define named component variants with `PreviewExtension`, customize variant
  and page layouts with templates or components, browse previews with
  `citry --app module:app ext run preview serve`, and capture PNGs with the
  extension's `render` command. Preview endpoints exist only in servers started
  by these commands.

- Components, including `LibraryComponent` definitions, can declare `simple = True` to render
  presentation templates without an independent instance or component hooks,
  keeping data callbacks live; incompatible declarations and calls raise errors.
  See the [simple component guide](https://citry.dev/advanced/simple-components/).

- `RenderFrame` gains an `is_transparent_root` field defaulting to `False`,
  identifying a transparent component's whole output separately from caller-owned
  interiors. `RenderFrame.from_context()` and `CitryRender` accept the same keyword.

## Changed

- `simple` is a reserved, immutable boolean declaration on `Component` and
  `LibraryComponent`, including when set to `False`. Rename existing unrelated
  class attributes with this name.
- Direct `ElementAttrsNode.render()` calls can return plain `str` where they
  previously returned `Markup`. The `format_attrs()` helper still returns `Markup`.
- Persisted render-cache entries from earlier versions become cache misses and
  are regenerated when used after upgrading.
- Repeated component renders do less ownership bookkeeping, attribute
  normalization and text traversal. Core builds with native ownership storage
  further improve larger component trees. Renders without nested component calls
  avoid native storage setup.

## Fixed

- Dynamic HTML tags forwarded through constant component inputs render correctly
  from templates, including on repeated renders ([#107](https://github.com/citry-dev/citry/issues/107)).
- Components rendered through nested standalone templates, loops, and layout
  slots now initialize their JavaScript and `js_data()` state correctly.
- Transparent components with nested template blocks and slot fills emit one
  ownership boundary, allowing the browser to initialize their content.
- Deeply nested render fragments avoid Python's recursion limit during
  scheduling and serialization.