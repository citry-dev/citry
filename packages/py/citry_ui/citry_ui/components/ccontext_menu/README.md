# ContextMenu maintainer notes

The authoritative design is
[`docs/design/ui_components/context-menu.md`](../../../../../../docs/design/ui_components/context-menu.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CContextMenu` binds one standard target Element to the existing Menu
declaration model. Keep native context behavior on editing, selection, links,
media, embedded content, and explicit native-escape paths. Keyboard access
depends on a focusable target or descendant.

The public family adds no Menu declaration, coordinate input, placement input,
or imperative controller. Reuse the shared Menu collection, surface, keyboard,
layer, style, and callback contracts. The controlled opening callback claims a
trusted native default only by setting owner state and returning literal
`true` in the same turn.
