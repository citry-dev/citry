# Release notes

## v0.3.0

### Breaking changes

- The built-in extensions package is now `citry.ext`: anything
  you imported from `citry.extensions.*` now lives at `citry.ext.*` (for
  example `from citry.ext.dependencies import Script`). The
  `Citry(extensions=[...])` setting is unchanged.
- The six JS/CSS dependency types (`Script`, `Style`,
  `CitryDependencies`, `Dependency`, `DependencyRecord`, and
  `OnDependenciesContext`) are now importable only from
  `citry.ext.dependencies`, so `from citry import Script` stops working. The
  one-line fix: `from citry.ext.dependencies import Script` (and likewise for
  the other five).

## v0.2.0

### Feat

- Citry now logs through the standard `logging` module, under the `"citry"`
  logger, with a `TRACE` level (5, below `DEBUG`). The logger traces each component,
  slot, and node as it renders. Turn it on to debug a render:

  ```python
  import logging
  logging.getLogger("citry").setLevel(5)
  ```

### Fix

- A default value for a slot set at `Component.Slot.<attr>` is now correctly used.

- Include JS runtime script when a Component has any JS/CSS scripts

### Refactor

- Citry now raises error when template contains `<c-slot name="X">`, but `Component.Slots` omits `X`.

  A component without a `Slots` class accepts any fills
  and is unaffected.

## v0.1.0

_30 Jun 2026_

Initial release.

## 2025-12-21

Initial commit.

This project was forked from [django-components/djc-core](https://github.com/django-components/djc-core) at commit [49e20dc](https://github.com/django-components/djc-core/commit/49e20dc).
