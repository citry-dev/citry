# Source-aware rich-Slot relocation

**Status:** Bounded exploration passed. It did not change the shipped runtime.

## Plain-language result

Citry already records enough information to keep a rich Slot connected to the
component that supplied it. We do not need to add an i18n-specific record to
the shared client graph.

Each browser-switchable rich Slot occurrence can use a real
`<bdi dir="auto">` element as its structural direction boundary. The boundary
does not set `lang`: application-owned nodes inside the Slot keep their own
language markup, or inherit the active application language when they do not
declare one. HTML gives `bdi` structural isolation, so a bidi-control character
inside the Slot cannot close the boundary around it.

`<c-trans>` can render the supplied Slot directly, once for each occurrence in
the selected message. Each call creates an existing Citry `slotRegion`. The
component can save that region's ID next to its i18n occurrence key, then send
that small mapping to its browser code through `js_data()`:

```json
{"key": "message:terms_link:0", "slot": "terms_link", "regionId": 1}
```

The browser can use the mapping and its normal graph route to find the live
comment-capped DOM range and its `bdi` parent. It can then check the complete
new message and move the existing boundaries in one synchronous operation.
This keeps the original DOM nodes and their ownership. It does not clone them
or run the Python Slot again.

The result fixes the apparent caller-scope blocker from the preceding
exploration. That exploration put a keyed child component around each Slot.
The wrapper lost the fill's caller scope. The wrapper is not needed. A direct
Slot call already gives every occurrence its own physical region while keeping
the fill's original source.

## Why the existing records are enough

- The graph spec says a direct Python call to a `Slot` creates a `slotRegion`,
  and that every region points back to its fill
  (`packages/protocol/client_graph/v1/spec.md:206-215`). The `SlotRegion`
  contract carries both receiver and owner information
  (`packages/protocol/client_graph/v1/spec.md:533-549`).
- `OwnershipGraph.capture_slot_call()` creates a new region for each direct
  call, records the fill and ownership fields, and returns a transparent result
  that carries the region ID (`packages/py/citry/citry/ownership.py:1132-1227`).
- Citry calls a component's `template_data()` before its `js_data()`
  (`packages/py/citry/citry/component_render.py:1047-1060`). `<c-trans>` can
  therefore invoke its Slots while building template data, then expose the
  resulting occurrence-to-region mapping as browser data.
- The browser component callback already receives the current graph route
  (`packages/py/citry/citry/ext/dependencies/client/citry.js:7201-7204`), and
  the runtime has a read surface for the live graph revision
  (`packages/py/citry/citry/ext/dependencies/client/citry.js:7864-7903`).

Existing tests already cover the important underlying behavior: a same-task
range move (`test_alpine_root_shapes_e2e.py:717`), caller-owned fill scope
(`test_alpine_slot_scope_e2e.py:50`), teleported fill scope and event routing
(`test_alpine_slot_scope_e2e.py:337`), and repeated regions from one fill
(`test_alpine_slot_scope_e2e.py:412`). The research harness reruns all four
tests in Chromium, Firefox, and WebKit before running the i18n-specific probe.

## What the new probe checked

The server rendered three direct Slot occurrences from two named fills. Two
occurrences contained stateful nested components. One contained an Alpine
teleport. The client then reordered those same three occurrences between an
English and Arabic message while changing the provider's `lang` and `dir`.
Every occurrence used a real `bdi` with `dir="auto"`; the application content
included explicit English language markup and hostile PDI/RLO/PDF characters.

All three browsers kept:

- the fill's original caller-side Alpine scope and event owner;
- the exact nested component records and physical DOM ranges;
- input values, focus, and text selection;
- teleport placement, DOM identity, event behavior, and local state;
- the same ownership revision, with no cleanup or reinitialization;
- the same structural `bdi` elements with browser-computed bidi isolation;
- application-owned `lang="en"` values under the Arabic provider;
- hostile bidi controls inside, rather than outside, the structural isolates;
- catalog text as text, including a literal `<unsafe>` string.

A `MutationObserver` saw only the completed Arabic content together with
`lang="ar"` and `dir="rtl"`. It never saw a half-switched state. The round trip
back to English preserved the same state again.

The candidate rejected every tested bad plan before changing the live message:

- a missing or duplicated occurrence;
- an actual Slot region owned by another component;
- a Slot boundary with a language override;
- a destination that was not the registered component root;
- an unknown graph revision;
- a corrupt comment-capped range;
- overlapping ranges;
- invalid locale-direction context;
- a second commit of an already used plan.

## Production decision

Keep the existing client-graph schema. The language-neutral graph should keep
describing fills, Slot regions, ownership, and physical placement. The i18n
artifact should separately map each message occurrence key to an existing
region ID.

For v1 browser switching, render every rich occurrence inside one real
`<bdi dir="auto">` that contains only that Slot region. The boundary is
i18n-owned, but it has no `lang`; language remains owned by the application
nodes inside it. Rich Slots are inline content, so a statically known block
root fails `check`, and an unexpected runtime block root fails the rich render
rather than relying on browser HTML repair. Teleported content that leaves the
inline boundary must carry its own application-owned language and direction
markup at the teleport target.

Add a supported runtime operation that performs the checks and atomic move now
implemented by the research candidate. Production i18n code must not depend on
private registry maps directly. The operation should accept the current
component graph route, the occurrence mapping, the complete next segment list,
the locale provider, and the next `lang` and `dir`. It should return a checked,
one-use plan and fail before changing the page when preflight does not pass.

The first browser contract remains limited to the same occurrence count for
each named Slot in every selectable locale. Reordering those existing
occurrences is now a viable path. Adding or removing occurrences still needs a
separate browser creation and removal protocol, or a normal navigation.

## Limits

This is a deliberately small proof:

- The relocation code is research JavaScript loaded after Citry, not a shipped
  browser API.
- Every tested occurrence has one physical placement. Shared or mirrored
  placements need a separate rule.
- The probe checks the browser's structural `bdi` semantics and preservation of
  application language markup. It is not a screen-reader pronunciation study.
- It moves existing occurrences only. It does not create or destroy component
  instances.
- Provider inheritance, nested client-provider policy, stale locale-change
  generations, catalog chunk loading, and cache variation are separate work.
- The locale spelling check in the candidate is only a test guard. It is not
  the locale canonicalization implementation proposed by the main design.
- This session could not use an independent agent reviewer because the active
  collaboration rules did not permit spawning one. The executable negative
  cases and three-browser matrix are the available review evidence.

[`evidence.json`](evidence.json) records equal results for Chromium
151.0.7922.34, Firefox 153.0, and WebKit 26.5. Exact normal and optimized-Python
reproduction commands are in
[`prototype-environment.md`](prototype-environment.md).
