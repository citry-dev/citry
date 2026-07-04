# Changelog

All notable changes to `pygments-citry` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

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

[0.1.0]: https://github.com/citry-dev/citry/releases/tag/pygments-citry@0.1.0
