# AGENTS.md - Citry UI

Read the repository root `CLAUDE.md` first. When editing Citry UI components,
also follow
[`docs/component-authoring.md`](docs/component-authoring.md).

## Gotchas

- Fold or compare an attribute key through `attr_name_text()`
  (`citry_ui/components/_attrs.py`), never through the key's own methods. A
  `str` subclass key can answer `lower()`, `casefold()`, `startswith()` or
  `==` with a different name from the text Citry writes into the page.
