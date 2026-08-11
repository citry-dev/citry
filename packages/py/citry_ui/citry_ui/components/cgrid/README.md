# Grid and Container maintainer notes

The authoritative contract is
[`docs/design/ui_components/grid-container.md`](../../../../../../../docs/design/ui_components/grid-container.md).

`CContainer`, `CGrid`, and `CGridItem` are CSS-only layout components. Keep
their common responsive surface flat and limited to track count/span. Bespoke
breakpoints, alignment, ordering, and utility styling belong in consumer CSS
or a utility framework such as Tailwind.
