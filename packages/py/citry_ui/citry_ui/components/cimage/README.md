# Image

`CImage` is the native-first responsive image primitive. It keeps one real
`<img>` as the semantic and request owner while adding required geometry,
ordered `<picture>` sources, visual-only loading and error slots, normalized
status callbacks, and safe lifecycle handoff.

The authoritative contract is
[`docs/design/ui_components/image.md`](../../../../../../docs/design/ui_components/image.md).

Keep galleries, lightboxes, upload, editing, zoom, pan, canvas access, image
maps, automatic CDN transforms, and policy-driven retries outside this family.
