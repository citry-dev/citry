# Changelog

## Unreleased

### Added

- Added Timeline, Sidebar, Tour, Data Grid, Virtual List, Virtual Window, and
  Transfer List component families with public guides, structured API
  references, examples, localization keys, and browser coverage.

### Changed

- Citry UI now requires `citry>=0.4.2` for component-owned source messages and
  checked browser translation bindings.
- Production component styles and the largest new interaction runtimes ship as
  deterministic checked-in minified assets while readable sources remain next
  to each component.

## [0.1.0] - 2026-08-19

### Added

- Build application interfaces from 55 styled component families by registering `citry_ui` once with a Citry instance.
- Use the same components in Citry templates or compose them from typed Python invocations.
- Customize light and dark themes through documented CSS variables, parts, variants, sizes, slots, and attributes.
- Render accessible server HTML, add keyboard and pointer interaction through
  Citry's client runtime, and localize built-in labels through the bundled
  catalog.

[0.1.0]: https://github.com/citry-dev/citry/releases/tag/citry-ui%400.1.0
