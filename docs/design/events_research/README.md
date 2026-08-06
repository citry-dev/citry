# Research behind the Events extension design

Full research and design-panel reports underlying
[`../events.md`](../events.md). The design doc carries the synthesized
conclusions; these are the source materials. The initial recon and design
panel were produced by multi-agent research runs on 2026-07-04; later sections
record the subsequent research, analysis, and spike rounds. File paths inside
the initial reports refer to session-local extractions of the `old-djc.zip`
and `old-chk.zip` snapshots at the repo root.

These reports call `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

Recon (the ground-truth sweep feeding the design panel):

- [`recon-citry-extensions.md`](recon-citry-extensions.md): the citry
  extension substrate as built (hooks, routes, config, gaps).
- [`recon-js-runtime.md`](recon-js-runtime.md): the client dependency
  manager, `$component`, and the fragment pipeline.
- [`recon-old-djc.md`](recon-old-djc.md): archaeology of the old
  django-components snapshot (Component.View, the `$emit`/`$on` sketch,
  the django_vue prototype, the Ninja trail).
- [`recon-citry-history.md`](recon-citry-history.md): decisions already
  recorded in citry's design docs and chat archive that constrain Events.
- [`recon-unicorn.md`](recon-unicorn.md),
  [`recon-tetra.md`](recon-tetra.md),
  [`recon-livecomponents.md`](recon-livecomponents.md): per-tool deep
  dives on the frameworks Events supersedes.
- [`recon-ecosystem.md`](recon-ecosystem.md): cross-framework patterns
  (Livewire, LiveView, Turbo, htmx, Datastar, django-ninja).

Design panel (three competing drafts, adversarially judged):

- [`design-A-dx-first.md`](design-A-dx-first.md),
  [`design-B-contract-first.md`](design-B-contract-first.md),
  [`design-C-supersede-first.md`](design-C-supersede-first.md).
- [`judge-1-practicality.md`](judge-1-practicality.md),
  [`judge-2-user.md`](judge-2-user.md): the adversarial verdicts whose
  graft recommendation shaped the first synthesis.

Handler-signature research (2026-07-05, feeding the section 3.3 redesign):

- [`typing-lab-report.md`](typing-lab-report.md): empirical matrix of
  nested-class annotation patterns against mypy and pyright on Python
  3.10+ (which spellings of `state: State` resolve, where, and why),
  with the experiment files' contents inlined.
- [`binding-models-report.md`](binding-models-report.md): how FastAPI,
  Django Ninja, and Litestar classify handler parameters, recognize
  injectables, wrap single-input schemas, handle files, and derive
  OpenAPI, with the recommendation candidates for citry Events.

- [`actions-semantics-report.md`](actions-semantics-report.md): prior-art
  verification for the actions vocabulary (target multiplicity, redirect
  terminality, URL history ops, event naming, download escapes, upload
  types) and public-API surface conventions across modern Python
  libraries.

Production audit (the golden reference, summarized in `events.md` 1.4):

- [`audit-chunk-1.md`](audit-chunk-1.md) through
  [`audit-chunk-4.md`](audit-chunk-4.md): per-component analysis of all
  View-bearing components in the maintainer's production app.
- [`audit-context.md`](audit-context.md): client-side call patterns,
  payload sizing, and component shape statistics.

Alpine implementation spikes are now collected under
[`../alpinejs/`](../alpinejs/README.md). The entries below cross-reference the
ones that directly shaped Events identity and queue behavior:

- [`spike-morph-alpine.md`](../alpinejs/spike-morph-alpine.md): the WP6 morph and
  Alpine spike report: the nine client-model assertions run against the
  real `citry.js` with pinned Alpine 3.15.12 plus `@alpinejs/morph`
  (all pass), the boot-order and private-API findings WP15 inherits,
  and the morph-vs-idiomorph verdict.
- [`spike-component-identity.md`](../alpinejs/spike-component-identity.md): the
  component-identity spike (2026-07-08) proving the two-identity model
  (faithful component id plus stable client anchor) through real morph
  and the byte-identical `citry.js`: the per-anchor epoch guard, the
  anchor representation choice, the three-way state split, the events-
  runtime and dependency-manager layer composition, and the deferred
  Component.css GC finding (all seven scenarios pass).
- [`spike-keyed-morph.md`](../alpinejs/spike-keyed-morph.md): the keyed-morph spike
  (2026-07-16) behind the `#c-key` scoping decision: Alpine morph key
  matching proved sibling-window scoped (so the class-id-scoped key
  form suffices and self-nested same-class instances cannot
  cross-pair), the keyed-position-swap preservation matrix (value,
  checked, and selection travel with the moved node; focus, scroll,
  iframe content, and media playback are move costs; `details open` is
  attribute faithfulness, so the server must echo it), the cascading
  move cost past the first out-of-order sibling, and the proven
  per-call contextual key callback kept as the recorded fallback.
- [`spike-root-group.md`](../alpinejs/spike-root-group.md): the WP23 multi-root listener
  spike (2026-07-19): an isolated Citry-owned `RootGroup` prototype matched
  pinned Alpine 3.15.12 in the single-root differential and proved union
  containment, shared modifier/timer state, dynamic root membership, native
  DOM values, open-shadow behavior, one poll cadence, and a stable live `els`
  array across Chromium, Firefox, and WebKit. It clears the stage-two mechanism
  gate while recording the intentional cleanup strengthening, native pointer-
  capture variance, and remaining real-runtime integration work. The checked-
  in [`root_group_harness.py`](../alpinejs/root_group_harness.py) reproduces the evidence.
- [`spike-rootless-lifecycle.md`](../alpinejs/spike-rootless-lifecycle.md): the WP23
  text/empty-root spike (2026-07-19): a Citry-owned comment-range registry
  proved element-free init, props, managed helpers, polling, stable live
  `els`, contextual table/select/SVG morphing, nested and adjacent isolation,
  fresh-ID normalization, grouped mirrors, keyed locality, movement, and exact
  cleanup in Chromium, Firefox, and WebKit. It pins contextual parsing, a
  synchronous nested-island guard, physical region tokens, and preserved Citry
  comments as load-bearing. The checked-in
  [`rootless_lifecycle_harness.py`](../alpinejs/rootless_lifecycle_harness.py) reproduces
  the evidence.
- [`spike-citry-handler-refs.md`](../alpinejs/spike-citry-handler-refs.md): the WP23
  component-boundary handler isolation spike (2026-07-19): relocated Alpine
  and Citry profiles both preserved exact parent ordinary data, `$data`,
  `$root`, `$id`, and `$refs`, while `$el`, `$dispatch`, and `$event` came from
  the physical child. Native `currentTarget` remained untouched. Colliding and one-sided source
  and child values, a child-local handler control, grouped source and target
  roots, a shared physical root, morph, delayed delivery, teleport, liveness,
  native `x-if`/`x-for` canaries, and open shadow behavior passed across
  Chromium, Firefox, and WebKit. The checked-in
  [`refs_client_binding_harness.py`](../alpinejs/refs_client_binding_harness.py) reproduces the evidence and
  clears F23.

Design analyses for the WP16/17 client work (2026-07-14) remain here. Later
Alpine-specific explorations are cross-referenced from their new evidence
directory:

- [`research-rerender-preservation-and-concurrency.md`](research-rerender-preservation-and-concurrency.md):
  cited web research across Livewire, Phoenix LiveView, the hypermedia
  cluster (HTMX, Turbo, Unpoly, Datastar), and the morph-library and
  client-cache prior art, answering two design questions: how mid-edit
  client state survives server-driven re-renders (keying, ignore
  markers, focused-element rules), and how overlapping event requests
  are ordered and surfaced (queues, policies, drop events). Ends in
  recommendations R1 to R3 with falsifiers.
- [`analysis-nested-anchor-continuity.md`](analysis-nested-anchor-continuity.md):
  option analysis for child-anchor continuity under a parent morph
  (reset versus positional matching versus keyed linking versus
  Livewire-style islands), with edge-case walkthroughs.
- [`analysis-target-other-renders.md`](analysis-target-other-renders.md):
  option analysis for renders addressed to a different element
  (remove-and-replace versus caller-epoch guarding versus in-place
  target reconciliation), with edge-case walkthroughs.
- [`exploration-client-props-passing.md`](../alpinejs/exploration-client-props-passing.md):
  the WP23 stage-one exploration (2026-07-17) for how a parent
  supplies client-component prop values: tested the now-superseded `x-props`
  candidate, recommends plain-Alpine reactivity via
  one supplier effect per carrying element, and pins validation timing
  and the identity rules; ends in the maintainer decision list that
  gates WP23 stage two.
- [`exploration-x-props-round-2.md`](../alpinejs/exploration-x-props-round-2.md):
  the WP23 round-two exploration (2026-07-18), incorporating the
  maintainer's supply-on-component-tag amendments and partially ratified on
  2026-07-19. Accepted direction covers source-ordered direct/dynamic/spread
  client bindings for the historical props spelling, Alpine handlers, and Citry `@c-*`
  handlers; both
  handler families keep the exact parent source scope while only their event
  carrier values follow the child; ordinary attrs staying Python kwargs;
  dynamic `<c-component>`
  forwarding; the init ancestry DAG; managed Alpine helpers; and stable
  multi-root `scope`. The grouped-listener and stable live `ctx.els` mechanism
  subsequently passed the `RootGroup` spike; the comment-owned text/empty
  lifetime then passed the rootless lifecycle spike. Named client identity
  remains a separate spike. Sections 8 and 9, covering unknown keys and
  defaults, are accepted; section 7's update-validation recommendation remains
  pending maintainer review. Its checked-in
  [`xprops_round_two_harness.py`](../alpinejs/xprops_round_two_harness.py) proves the
  pinned Alpine loop-scope and clearing behavior; the report ends in the
  accepted decisions, pending decisions, spike gates, and falsifiers for WP23
  stage two.
- [`exploration-slots-alpine-scope.md`](../alpinejs/exploration-slots-alpine-scope.md):
  the redone slots-and-Alpine-scope exploration (2026-07-19). The original
  scratch report was rejected after its opening example and several
  load-bearing claims proved wrong. The replacement uses checked-in server
  and three-browser harnesses. It retains exact call-site ownership and
  child-owned fallback, rejects intercept-time stack copying, blanket Citry
  redirects, synthetic event redispatch, nested-boundary suppression, and
  blanket restamping, and proves a split-phase Alpine source-link prototype
  with explicit structural-template propagation and composed native teleport
  ancestry.
  Server provenance, the general registry, Citry-magic/queue integration,
  nested ownership serialization, and rootless/mirrored lifetime remain
  explicit product gates. Evidence lives in
  [`slots_scope_server_harness.py`](../alpinejs/slots_scope_server_harness.py),
  [`slots_scope_harness.py`](../alpinejs/slots_scope_harness.py), and their adjacent JS
  adapter/scenarios.
- [`exploration-alpine-component-first.md`](../alpinejs/exploration-alpine-component-first.md):
  the component-first architecture exploration (2026-07-20). The maintainer
  selected its Citry-owned runtime-neutral ownership graph with pinned stock
  Alpine as the near-term directive engine, plus `$c-props` and
  `c-$c-props`. The report rejects private-Alpine access as a binary
  falsifier because the accepted control already pays that cost. The
  retained server, syntax, broad browser, same-manifest comparison, and
  partial real-render composition harnesses live in the adjacent
  `component_first_*` files. Production queue, atomic morph transaction,
  dynamic-target ancestry, Python Slot source policy, and protocol hardening
  remain explicit integration work rather than another architecture survey.
