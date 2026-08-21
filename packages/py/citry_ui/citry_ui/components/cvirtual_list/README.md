# Virtual List family

`CVirtualList` keeps a complete server-rendered list while the browser skips
off-screen layout and paint. `CVirtualWindow` renders an application-supplied
fixed-size range and requests new ranges through `$c-props`.

The authoritative contract is
[`docs/design/ui_components/virtual_list.md`](../../../../../../../docs/design/ui_components/virtual_list.md).
Public guidance lives in [`api.md`](api.md), structured reference data lives in
[`api.yml`](api.yml), executable examples live in [`snippets/`](snippets/), and
the shared qualification fixture lives in [`quality/scenario.py`](quality/scenario.py).
