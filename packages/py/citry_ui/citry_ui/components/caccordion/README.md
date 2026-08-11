# CAccordion maintainer notes

The authoritative design is
[`docs/design/ui_components/accordion.md`](../../../../../../../docs/design/ui_components/accordion.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CAccordion` is the one group state owner. `CAccordionItem` is a real rendered
component and direct root child. The private transparent collector validates
the completed server registry without adding DOM. The private panel-content
boundary permits a nested Accordion only inside a panel.

Do not add public Trigger, Header, Panel, or Indicator components unless a real
job cannot be expressed through the item slots and exact attribute maps. Do not
unmount closed panels without redesigning form, browser state, source
visibility, and accessibility behavior.
