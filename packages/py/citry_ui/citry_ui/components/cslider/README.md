# Slider family maintenance notes

`CSlider` owns one exact-decimal value. `CRangeSlider` owns two stable lower and
upper values and never swaps thumb identity. The family shares one progressive
native-range fallback, exact `BigInt` grid runtime, CSS contract, and number
format profile.

Keep the public contract synchronized across `cslider.py`, `api.md`, `api.yml`,
the focused tests, quality scenario, snippets, and
`docs/design/ui_components/slider.md`. Regenerate `citry_ui_i18n` after changing
the final `CRangeSlider.messages` block.
