# Button maintainer notes

Runtime implementation: [`cbutton.py`](cbutton.py).

Before changing the public contract, update the
[`Button specification`](../../../../../../docs/design/ui_components/button.md).
Follow the package
[`component policy`](../../../docs/component-authoring.md). Focused browser
tests live in this directory; cross-family registration and asset contracts
remain in the package-level suite.

The public guide is [`api.md`](api.md), and its structured reference is
[`api.yml`](api.yml). The docs catalog validates and combines them directly;
no synchronized copy is required.
