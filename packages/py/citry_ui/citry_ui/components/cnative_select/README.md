# Native Select component family

`CNativeSelect` is Citry UI's styled native single-choice Select. Its
production contract lives in
[`docs/design/ui_components/native-select.md`](../../../../../../../docs/design/ui_components/native-select.md).

The family renders one `<select>` with native options and groups. `CField`
owns labels, descriptions, errors, and composed state. `CNativeSelect` owns
the finite option snapshot, native value/reset behavior, optional browser
control through `$c-props`, and root styling.

Repository-only files in this directory provide the public guide, structured
reference, rendered snippets, quality scenario, and focused tests. The wheel
contains only `__init__.py` and `cnative_select.py`.
