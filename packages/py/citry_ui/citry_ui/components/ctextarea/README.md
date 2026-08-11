# Textarea component family

`CTextarea` is Citry UI's styled native multiline text control. Its production
contract lives in [`docs/design/ui_components/textarea.md`](../../../../../../../docs/design/ui_components/textarea.md).

The family deliberately renders one `<textarea>` with no wrapper or slots.
`CField` owns labels, descriptions, errors, and composed state. `CTextarea`
owns native default/current value behavior, optional browser control through
`$c-props`, rows, wrapping, resize presentation, and root styling.

Repository-only files in this directory provide the public guide, structured
reference, rendered snippets, quality scenario, and focused tests. The wheel
contains only `__init__.py` and `ctextarea.py`.
