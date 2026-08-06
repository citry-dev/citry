# Changelog

All notable changes to `pygments-citry` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-08-06

### Fixed

- Stop Python comments inside `{{ ... }}` before the host `}}` delimiter even
  when the comment text contains apostrophes, quotes, or braces.

## [0.1.1] - 2026-07-30

### Added

- Highlight the current Citry directive channels: `$c-props` and Alpine
  values as JavaScript; Citry Events values as server-handler references with
  optional Alpine arguments; `c-$c-props`, `c-*`, and `#c-key` values as
  Python; and `#c-ignore` as framework metadata.
- Highlight nested Citry templates inside `c-*` attribute values and preserve
  useful language coloring for unfinished interpolations, dynamic attributes,
  and component template strings.
- Share a behavior-oriented syntax fixture corpus with editor integrations so
  Pygments and TextMate implementations can check the same current syntax.

### Fixed

- Accept Citry's `$`/`#`/`@`/`:` attribute channels, dotted `@c-*`/`:c-*`
  modifiers, and template comments at attribute boundaries without stray
  error tokens.
- Keep the non-opening triple-quote family and backslash-escaped matching
  delimiters inside `template`, `js`, and `css` bodies instead of ending the
  embedded language early.
- Style `<>...</>` as fragment punctuation only inside a nested `c-*` template
  value; standalone `<>` remains ordinary text.

## [0.1.0] - 2026-07-27

### Added

- First release. A `citry` Pygments lexer that highlights a Citry component: the
  Python class plus the HTML, JavaScript, and CSS embedded in its `template`,
  `js`, and `css` string attributes.
- Citry-aware template highlighting: `<c-*>` component and built-in tags, `c-*`
  dynamic attributes (whose values are Python expressions), the built-in tags'
  own Python-valued attributes (`cond`, `each`, `is`), `{{ ... }}` interpolation
  (with a brace-counting scan so a nested dict like `{{ {"a": {1: 2}} }}` ends
  at the right place), `{# ... #}` comments, and verbatim `<c-raw>` content.
- A second `citry-html` lexer for a fenced block that shows only a template
  (no surrounding Python).
- Registered as Pygments plugins (the `pygments.lexers` entry points), so
  `get_lexer_by_name("citry")` and `get_lexer_by_name("citry-html")` resolve
  once the package is installed.

### Fixed

- Built-in Citry tag names now receive the same tag styling as HTML and user
  component tags, including in dark themes.

[Unreleased]: https://github.com/citry-dev/citry/compare/pygments-citry@0.1.2...HEAD
[0.1.2]: https://github.com/citry-dev/citry/compare/pygments-citry@0.1.1...pygments-citry@0.1.2
[0.1.1]: https://github.com/citry-dev/citry/compare/pygments-citry@0.1.0...pygments-citry@0.1.1
[0.1.0]: https://github.com/citry-dev/citry/releases/tag/pygments-citry@0.1.0
