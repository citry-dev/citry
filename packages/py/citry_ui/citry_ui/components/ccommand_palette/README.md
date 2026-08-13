# CommandPalette

`CCommandPalette` is a modal, locally searchable collection of application
commands. It keeps focus in one search input, exposes grouped listbox options,
and sends stable command values to one application callback.

The authoritative contract is
[`docs/design/ui_components/command-palette.md`](../../../../../../docs/design/ui_components/command-palette.md).

Keep global shortcut registration, routing, authorization, native navigation,
remote results, fuzzy ranking, history, nested pages, and virtualization
outside this family.
