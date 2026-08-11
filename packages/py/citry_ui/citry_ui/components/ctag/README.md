# Tag and TagGroup

`CTagGroup` owns labelled descriptive, selectable, actionable, and removable
Tag collections. `CTag` declares one stable item.

- Authoritative design: [`docs/design/ui_components/tag.md`](../../../../../../../docs/design/ui_components/tag.md)
- Public guide: [`api.md`](api.md)
- Structured API: [`api.yml`](api.yml)

The family is not a free-form TagsInput and contributes no FormData. Use
`CBadge` for static status text and keep ordinary links as native anchors.
