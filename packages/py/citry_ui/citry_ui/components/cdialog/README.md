# Dialog maintainer notes

Runtime implementation: [`cdialog.py`](cdialog.py).

Before changing the public contract, update the
[`Dialog specification`](../../../../../../docs/design/ui_components/dialog.md).
Follow the package
[`component policy`](../../../docs/component-authoring.md). Focused browser
tests live in this directory; cross-family registration and asset contracts
remain in the package-level suite.

The public guide is [`api.md`](api.md), and its structured reference is
[`api.yml`](api.yml). The docs catalog validates and combines them directly;
no synchronized copy is required.

Keep these runtime invariants together:

- the private `data-citry-dialog-host` scopes activators and close actions to
  their nearest Dialog;
- the native Dialog owns top-layer modality and the restoration target, with a
  same-target fallback for engines that omit restoration;
- focus-loop events belong only to the nearest native Dialog;
- open instances share a reference-counted document scroll lock; and
- native `method="dialog"` closes report `returnValue` through
  `onOpenChange`.

Public examples live in [`snippets/`](snippets/). Focused runtime tests live in
[`tests/e2e/`](tests/e2e/), and the reusable quality state lives in
[`quality/scenario.py`](quality/scenario.py). These repository-only directories
are excluded from the wheel.
