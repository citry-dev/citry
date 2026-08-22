# Flow layout maintainer notes

The authoritative contract is
[`docs/design/ui_components/flow-layout.md`](../../../../../../../docs/design/ui_components/flow-layout.md).

`CCol` and `CRow` are server-only one-root flex layouts. Keep them free of
child wrappers, child inspection, responsive breakpoint inputs, and client
assets. Their shared family is an authoring convenience, not a public generic
`CFlow` base.
