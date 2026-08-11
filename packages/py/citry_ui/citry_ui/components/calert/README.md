# CAlert maintainer notes

The authoritative design is
[`docs/design/ui_components/alert.md`](../../../../../../../docs/design/ui_components/alert.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CAlert` owns persistent feedback presentation only. Visual intent and
announcement urgency are independent. Dismissal, focus restoration, Toast
queues, guaranteed announcements, and Form summaries stay outside this
family.

The indicator uses one package-owned SVG shell. Its glyphs come through
CIcon's private safe catalog resolver, including logical-direction metadata.
Do not copy raw SVG into Alert or reintroduce multiple nested CIcon roots.
