# Checkbox maintainer notes

The authoritative design contract is
[`docs/design/ui_components/checkbox.md`](../../../../../../docs/design/ui_components/checkbox.md).
The public guide is [`api.md`](api.md), and its generated reference data is
[`api.yml`](api.yml).

Key boundaries:

- Keep a real native `input[type="checkbox"]`.
- The root is a neutral span. An authored default fill renders in an explicit
  sibling label; the description stays outside that label.
- `indeterminate` is runtime-enhanced native state. Never author
  `aria-checked`.
- Component-tag native listeners run on the neutral root. `input` and `change`
  read state from `event.target`.
- A Field owns visible label, description, error, required, disabled, and
  invalid state. Checkbox declares that read-only is unsupported.
- Group selection, minimum-selection validation, Checkbox Card, and custom
  indicator slots are separate future work.

Keep runtime, public docs, structured API data, snippets, focused tests, and
quality fixtures together in this directory. Packaging excludes every support
file except `__init__.py` and `ccheckbox.py`.
