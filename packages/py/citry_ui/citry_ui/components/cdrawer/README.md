# Drawer maintainer notes

Runtime implementation: [`cdrawer.py`](cdrawer.py).

Before changing the public contract, update the
[`Drawer specification`](../../../../../../docs/design/ui_components/drawer.md).
Follow the package
[`component policy`](../../../docs/component-authoring.md). The public guide is
[`api.md`](api.md), and its structured reference is [`api.yml`](api.yml).

Keep these runtime invariants together:

- `CDrawer` is a modal task surface backed by native `<dialog>`; persistent
  navigation belongs to application layout rather than this family;
- placements are logical, and `block-end` is the bottom-sheet composition;
- controlled close requests do not mutate visibility until accepted, while
  structural, ancestor, and modal-safety closes cannot be rejected;
- every open path passes the same composed-tree/modal eligibility gate;
- a retained `open=True` value is latched after a forced close until the owner
  supplies `False` or releases control; and
- open Drawer/Dialog instances share the modal scroll-lock record.

Public examples live in [`snippets/`](snippets/). Focused runtime tests live in
[`tests/e2e/`](tests/e2e/), and the reusable quality state lives in
[`quality/scenario.py`](quality/scenario.py). These repository-only files are
excluded from the wheel.
