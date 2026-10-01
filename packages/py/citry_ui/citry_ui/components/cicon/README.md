# Icon maintainer notes

Runtime implementation: [`cicon.py`](cicon.py). Generated SVG geometry and
source digests: [`_catalog.py`](_catalog.py). Rebuild that file with
[`tools/vendor_lucide.py`](tools/vendor_lucide.py) only after updating the
[`Icon specification`](../../../../../../docs/design/ui_components/icon.md).

The generator downloads a fixed Lucide version, accepts only the audited SVG
root attributes and `path`, `circle`, and `rect` geometry, then records each
source file's SHA-256 digest. Review the generated diff and update
[`THIRD_PARTY_LICENSES.md`](../../../THIRD_PARTY_LICENSES.md) when the upstream
version changes.

Follow the package [`component policy`](../../../docs/component-authoring.md).
The public guide is [`api.md`](api.md), and its structured reference is
[`api.yml`](api.yml). The docs catalog validates and combines them directly;
no synchronized copy is required.

Components such as Alert, Accordion, Disclosure, and Menu that need one
registered decorative glyph use the private `_resolve_registered_icon()`
helper. It owns allowlist lookup, semantic aliases, and logical-direction
metadata, and it renders the glyph through `Citry.render_template()`. The
template places the result with `{{ glyph.content }}` inside its `<svg>`, so
both the server and Vue build real SVG elements. The helper never returns the
catalog string, because `{{ }}` escapes a plain string and the page would
show `<path ...>` as text. Do not read `_catalog.py` directly or create a
parallel resolver.
