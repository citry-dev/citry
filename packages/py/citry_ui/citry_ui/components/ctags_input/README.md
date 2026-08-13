# TagsInput maintainer notes

The authoritative design is
[`docs/design/ui_components/tags-input.md`](../../../../../../docs/design/ui_components/tags-input.md).
The reader-facing guide and structured reference live beside this file as
`api.md` and `api.yml`.

`CTagsInput` owns one ordered free-form string collection and one unfinished
editor draft. Keep those state axes independent, preserve repeated native Form
values through the multiple Select proxy, and clear a draft only after its
value request is accepted.

The editor remains the only custom focus owner. Keep delimiter and paste work
atomic, retain the exact editor node through active composition, reconstruct
the immutable baseline after an uncanceled reset, and fail closed to the
native Select when the settled anatomy is invalid.
