# CRadioGroup and CRadio

Maintainer source for native single-choice groups.

- Runtime: `cradio.py`
- Public guide and reference source: `api.md` and `api.yml`
- Design authority: `docs/design/ui_components/radio.md`
- Examples: `snippets/`
- Focused evidence: `tests/`
- Shared qualification fixture: `quality/scenario.py`

`CRadioGroup` owns shared name, state, native validation, and browser control.
`CRadio` is valid only under its nearest Group and owns one native input and
visible label.
