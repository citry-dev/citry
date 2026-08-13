# CSplitButton maintainer notes

The authoritative design is
[`docs/design/ui_components/split-button.md`](../../../../../../docs/design/ui_components/split-button.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CSplitButton` owns one dominant native Button and one separate Menu Button.
Keep the primary action visible, name the Menu Button explicitly, and reuse the
existing Menu declarations without adding SplitButton-specific item models.

The primary may submit or reset a native Form. The Menu Button and every
button-root Menu declaration stay `type="button"`. Keep the two-phase primary
close transaction, whole-root layer containment, controlled ownership, shared
Button/Menu assets, and correlated cleanup aligned with the authoritative
specification.
