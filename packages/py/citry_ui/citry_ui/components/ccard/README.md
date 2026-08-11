# Card maintainer notes

`CCard` is a static styled subject container. Its complete contract lives in
[`docs/design/ui_components/card.md`](../../../../../../../docs/design/ui_components/card.md).

Keep these boundaries intact:

- the default root is a neutral `div`;
- every slot is optional, but at least one must be supplied;
- root, header, body, and footer content do not clip overlays or create a
  stacking context;
- only the media wrapper clips its own visual edge, including every edge when
  it is the sole section;
- the six part-attrs mappings fail when their destination is absent; and
- Card has no JavaScript, click inference, whole-Card link, disabled state, or
  generic Surface export.
