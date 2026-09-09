# Iteration 59: identify component cases before choosing an optimization

## Research direction

The user requested an explicit change of approach after iteration 58: identify
semantically distinct component cases and the work each needs, starting with a
component without slots, Alpine, or JS/CSS variables. The objective remains warm
render parity with template engines. Representation changes and caches are tools
to use after identifying an avoidable operation, rather than the starting point.

Reading extension dispatch and the code that records template locations did not
identify more work to omit. The extension manager already records which config
constructors to call and which extensions implement each hook; iterations 5 and 21 measured
related source-site reuse without establishing a useful gain. Close that read-only
investigation without claiming another measured experiment or changing production.

## Prior art and census

Read `component_render.py::_render_one`, `_settle_render`, `_finalize`, component
input construction, node invocation/slot paths, `ExtensionManager` dispatch and
`ext/dependencies/extension.py::on_component_data`. The dependency hook already
returns early for components without assets, external dependencies or JS data.
`ownership_manifest.py::_render_parts_use_alpine` identifies direct Alpine in
settled output while excluding separate child-component roots. Reuse that
implementation for observations. The extension, rendering, ownership and pure-body
designs govern behavior that may still be visible outside a component.

Record each actual component occurrence in the large benchmark and a reduced-input
version. Distinguish observed supplied slots, executed slot outlets and nested
component tags; do not equate an empty slot mapping with a slot-free template.
Also inspect settled child frames and component calls with an explicit parent,
since expressions and callbacks can insert children without a component tag.
Record effective assets, normalized JS/CSS data, observed direct Alpine, client
tag bindings, custom initialization/data/render methods, schemas, pure declarations,
provides and extension participation. Count repeated runtime operations by their
owning component. Use these observations to propose cases, not to certify an
optimization for arbitrary inputs.

Keep all instrumentation outside performance comparisons. Compare instrumented
and ordinary full HTML and all four canonical ownership snapshots with identical
ID seeds. A changed digest invalidates the census. The census deliberately retains
component/render references until analysis finishes, so it is not lifetime or
allocation-timing evidence. It adds no CI or release step and reuses the existing
benchmark fixture, snapshot canonicalizer and settled-output Alpine scanner.
Independent review checks the classification and the separate explanatory prose.

## Questions the next design must answer

For the simplest case, determine whether templates/data alone determine output,
and which current behaviors still observe an instance or boundary: input validation,
custom constructors/data callbacks, extension hooks, parent/root/provides, ownership
and ID markers, security, errors, cache replay and caller-retained renders. Separate
class/template facts from facts known only after executing callbacks or resolving
attributes. Define how a case remains valid when inputs, the registry or extensions
change, and which unknown cases need the existing renderer. No shortcut is adopted
from an empty value observed in one benchmark render.

## Contract changes to investigate

The user also asked which API conveniences constrain performance enough to be
worth changing. For each candidate case, record a compatible option and any
explicit restriction that could remove more work, the behavior users would lose,
and the experiment needed to measure the tradeoff. Candidates include component
instance observability, mutable inputs, instance data callbacks, hook coverage,
per-occurrence identity and provenance, and when template/extension configuration
can change. This is authorization to investigate alternatives, not evidence that
any particular restriction improves rendering.

Slot-capture calls have no component/context argument. Report their total
separately rather than silently dropping it or assigning a guessed owner.
Direct Alpine is observed in the settled physical output, including slot content
inside the component boundary; it is not a declaration-level classification.

A second Alpine observation stops at captured slot regions. It separates Alpine
in surrounding output from Alpine that arrives inside supplied/fallback content;
it does not certify that supplied attributes or expression values are inert.
