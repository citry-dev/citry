# CDisclosure maintainer notes

The authoritative design is
[`docs/design/ui_components/disclosure.md`](../../../../../../docs/design/ui_components/disclosure.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CDisclosure` owns one Boolean expansion state, one native heading/button, and
one always-mounted panel. It is not a one-item Accordion: do not add item
identity, collection keyboard behavior, or group coordination here.

Keep title/content validation, focus-before-close, effective fieldset
disabledness, controlled ownership, and rapid animation reversal aligned with
the authoritative specification. Native `details` remains the raw-HTML choice
when no-JavaScript toggling matters more than the Citry contract.
