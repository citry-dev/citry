---
title: v0.3.1 (2026-07-29)
url: https://citry.dev/v/0.4.6/releases/v0.3.1/
description: "What changed in citry v0.3.1 (2026-07-29)."
---
# v0.3.1 (2026-07-29)

## Fix

- Event handlers now work when Citry is installed from PyPI. In 0.3.0 the
  browser runtime that Citry serves for `Events` was left out of the published
  package, so a page with an event handler loaded a script the server could not
  produce, and the call never reached Python. Upgrade to use `Events`; no code
  change is needed.
- `format_attrs()` now omits empty `class` and `style` values produced by
  `merge_attrs()`, matching hand-built structured values.
- `<c-error-fallback>` now escapes ordinary fallback strings. Use a fallback
  fill when the fallback needs markup.
- `$component()` is now recognized only as a live call expression. Matching
  text inside strings, comments, template-literal text, regular expressions,
  and function or method declarations no longer activates Citry's browser
  runtime or gets rewritten as a component callback.
- A configured extension instance can no longer be silently moved from one
  `Citry` engine to another. Pass the extension class or create a fresh
  instance for each engine. A failed engine construction restores the
  instance's previous owner.
- `citry create` now scaffolds both `Kwargs` and `Slots`, and relies on Citry's
  default template data instead of generating a redundant data method.