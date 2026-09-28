# Tabs maintainer notes

Runtime implementation: [`ctabs.py`](ctabs.py).

Before changing the public contract, update the
[`Tabs specification`](../../../../../../docs/design/ui_components/tabs.md).
Follow the package
[`component policy`](../../../docs/component-authoring.md). Focused browser,
scenario, and Phase 7.5 quality tests live in this directory; cross-family
registration and asset contracts remain in the package-level suite.

`CTab` and `CTabPanel` are public declaration components. `CTabs` renders its
default slot through `CInternalTabsDeclarations`, which validates that the
otherwise-empty first pass contains declarations only. The sibling
`CInternalTabs` tag is later in Citry's deferred queue, so its `template_data()`
runs only after every declaration registered its inputs and lazy Slot. It then
validates the complete registry and renders through `CInternalTab` and
`CInternalTabPanel`. All four private definitions belong in the library
manifest because they need engine-specific registration, but they are absent
from public exports. Do not replace this queue ordering with a synchronous
nested `.render()`: fragment ownership adoption requires the internal
components to remain ordinary logical children of `CTabs`.

Tab and Panel content is compiled with its author: the assembler passes it
as a Vue slot from `CInternalTabs` up to the call of the component that wrote
it (see "Fills keep their author's Vue scope" in
[`docs/design/vue.md`](../../../../../../docs/design/vue.md)). A component used
only to group declarations must be transparent when the declarations use Vue
bindings. A non-transparent wrapper is a sibling of `CInternalTabs`, and Vue
slots cannot travel from a sibling, so assembly rejects its Vue-bound content
and copies content that shows only Python values.

The public guide is [`api.md`](api.md), and the structured reference is
[`api.yml`](api.yml). The docs catalog validates and combines them at the public
Tabs route; no synchronized copy is required.
