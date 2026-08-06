# Field and Input maintainer notes

Runtime implementation: [`cfield.py`](cfield.py).

Before changing the public contract, update the
[`Field and Input specification`](../../../../../../docs/design/ui_components/field-input.md).
Follow the package
[`component policy`](../../../docs/component-authoring.md). Focused browser
tests live in this directory; cross-family registration and asset contracts
remain in the package-level suite.

The public guide is [`api.md`](api.md), and its structured reference is
[`api.yml`](api.yml). The docs catalog validates and combines them directly;
no synchronized copy is required.

Rendered public examples live in [`snippets/`](snippets/). The reusable
qualification route is [`quality/scenario.py`](quality/scenario.py), while
focused browser behavior lives in [`tests/e2e/`](tests/e2e/). Keep generated
IDs, Field-owned state, the exactly-one-control check, native value/reset
behavior, API data, and example claims aligned.
