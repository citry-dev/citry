# ScrollArea maintainer notes

The authoritative design is
[`docs/design/ui_components/scroll-area.md`](../../../../../../docs/design/ui_components/scroll-area.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CScrollArea` renders one native focusable overflow element. Keep the default
slot transparent, leave wheel, touch, and keyboard scrolling with the browser,
and never add replacement scrollbar anatomy or content measurement wrappers.

The client controller normalizes event-scoped horizontal offsets, repairs
disabled-axis and direction changes, and preserves only a retained root during
correlated morphs. A replacement root starts with native browser state. Keep
owned coordinate writes instantaneous and suppress only their exact matching
native callback edge.
