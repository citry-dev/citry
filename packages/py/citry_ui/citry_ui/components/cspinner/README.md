# CSpinner

Maintainer source for the compact indeterminate activity family.

- Runtime: `cspinner.py`
- Public guide and reference source: `api.md` and `api.yml`
- Design authority: `docs/design/ui_components/spinner.md`
- Examples: `snippets/`
- Focused evidence: `tests/`
- Shared qualification fixture: `quality/scenario.py`

`CSpinner` owns one labelled, indeterminate `progressbar`. It does not own task
timing, delayed appearance, overlays, live announcements, or determinate value.
