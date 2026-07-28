# Component-first Alpine integration: exploration report

**Decision update (2026-07-20):** the maintainer selected this report's
graph-first Alpine recommendation and `$c-props`, including the orthogonal
`c-$c-props` form. The integrated product gate and remaining open choices are
now tracked in [`../alpinejs_plan.md`](../alpinejs_plan.md). The normative
architecture is [`../alpinejs.md`](../alpinejs.md); older provisional wording
below remains part of the exploration record.

Status: architecture exploration and a partial real-render composition slice
completed on 2026-07-20. The architecture has since been selected, while
product support remains gated on the integrated Stage 3 evidence. This is
research output, not production runtime code. The original brief is
kept after the findings so its requirements and falsifiers remain
reviewable.

This report calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

The question is not merely whether Citry should replace Alpine. The useful
question is:

> What becomes simpler, safer, or more general if Citry's rendered component
> instances and slot ownership are the primary client-side model, while
> Alpine is one possible consumer or extension of that model rather than the
> source of component identity and scope ancestry?

The exploration must be willing to retain stock Alpine, extend it, contribute
an upstream hook, maintain a narrow fork, build a Citry directive layer, or
adopt a different reactive or rendering core. It must compare those avenues
against the same evidence. It must not begin with a preferred implementation
and then redefine the requirements around it.

## Verified result

### Recommendation

Adopt a component-first representation, but do not replace Alpine in the near
term.

The recommended architecture has four layers:

1. Citry's server render owns a runtime-neutral graph of component instances,
   executed call edges, exact lexical source locations, logical fills,
   physical regions, and component-tag client bindings.
2. A general Citry client registry owns stable anchors, reactive component
   scope, props bags, root groups, rootless ranges, mirrors, binding records,
   and lifecycle. DOM markers and Alpine stacks are projections of this
   registry rather than the source of component identity.
3. Pinned stock Alpine 3.15.12 remains the near-term expression, directive,
   modifier, local `x-data`, reactivity, and morph engine. One concentrated
   Citry adapter projects the graph into Alpine and carries the same pinned
   private integration already required by the accepted Alpine-first work.
4. Citry-specific client syntax uses a Citry namespace. The maintainer
   accepted this spike's `$c-props` recommendation, including `c-$c-props`,
   after the spike completed.
   Genuine Alpine features keep genuine Alpine names inside rendered HTML and
   fills. On a component tag, non-handler `x-*` remains a Python component
   input, while Alpine event handlers are client bindings. Do not add a broad
   `$c-*` copy of Alpine unless Citry later owns those semantics.

This is a layered decision, not a claim that Alpine's DOM model disappeared.
Ordinary `x-*` inside source-linked fills still needs a pinned Alpine source
projection for exact `$refs`, `$root`, `$id`, structural clones, and
teleports. Component-first changes the authority and protocol. It does not
magically remove every Alpine-specific adapter.

Do not build a Citry evaluator, a fine-grained Alpine replacement, a VDOM, or
an Alpine fork for the first implementation. Keep the runtime-neutral graph
capable of supporting those later. Revisit them only when a measured trigger
in section 13 occurs.

### Why this won

The graph-first Alpine prototype and the Citry-evaluator prototype both
passed the same-fixture comparison in Chromium 149, Firefox 151, and WebKit
26.5. Both preserved:

- parent-owned ordinary data, `$refs`, and `$root` inside child DOM;
- child-local genuine Alpine `x-data` isolation;
- one props effect per logical target;
- multi-root boundary delivery with shared `.once` state;
- exact source re-election after the source root was replaced; and
- boundary-listener group and props-effect cleanup after runtime teardown.

The Citry evaluator needed its own `new Function` compiler, assignment proxy,
effect installation, event installation, source invalidation, and an explicit
bridge back into Alpine for `$refs`, `$root`, and `$id`. That bridge is the
beginning of two expression domains, not a simplification. It also fails
strict CSP in its prototype form. Extending it to `x-model`, transitions,
async behavior, every event modifier, official plugins, and Alpine error
parity would reproduce a large part of Alpine before Citry gained a product
feature that the graph-first adapter cannot provide.

The comparison's small unoptimized 1,000-read loop is not a production
benchmark, but it is a useful negative control. Median times were:

| Engine | Alpine graph projection | Citry evaluator with Alpine magic bridge |
|---|---:|---:|
| Chromium 149 | 3.8 ms | 10.2 ms |
| Firefox 151 | 11 ms | 34 ms |
| WebKit 26.5 | 4 ms | 14 ms |

The result does not say a purpose-built evaluator must always be slower. It
shows that the supposed simpler path already pays repeated bridge work before
it has Alpine feature parity. The architecture decision rests primarily on
correctness, compatibility, and responsibility count, not these timings.

### What was executed

The retained evidence is:

| Artifact | What it proves |
|---|---|
| [`component_first_server_ownership_harness.py`](component_first_server_ownership_harness.py) and [`component_first_server_ownership_findings.md`](component_first_server_ownership_findings.md) | Research monkeypatches over real V3 parsing, compiled nodes, Python render objects, slots, deferred rendering, and serialization identify the capture clocks and assert key provenance relationships in ten server cases. They do not implement the production capture-to-wire path. |
| [`component_first_syntax_server.py`](component_first_syntax_server.py), [`component_first_syntax_browser.py`](component_first_syntax_browser.py), and [`component_first_syntax_report.md`](component_first_syntax_report.md) | `$c-*` transport through Citry and current HTML browsers, DOM APIs, templates, contextual parsing, MutationObserver, clone, Alpine coexistence, and morph. |
| [`component_first_adapter.js`](component_first_adapter.js), [`component_first_scenarios.js`](component_first_scenarios.js), and [`component_first_harness.py`](component_first_harness.py) | Broad graph-first and Citry-directive prototypes across ownership, fallback, nesting, shared roots, teleport, `x-if`, props, grouped events, source replacement with and without a fill, replace-then-reinsert source-cache rekeying, pre-stamped shared-root order, morph, bounded validation, and runtime-owned cleanup. The same page also reuses isolated generic rootless and mirror mechanisms, but does not connect them to graph instances or fills. Three runs per engine pass. |
| [`component_first_comparison_scenarios.js`](component_first_comparison_scenarios.js) and [`component_first_comparison_harness.py`](component_first_comparison_harness.py) | Both competing engines consume exactly the same DOM and manifest. Five runs per mode and engine pass. |
| [`component_first_vertical_scenarios.js`](component_first_vertical_scenarios.js) and [`component_first_vertical_harness.py`](component_first_vertical_harness.py) | A partial composition slice combining a real Citry template, render trace, serializer HTML, and captured boundary kwargs with a manually assembled graph and selectors, then exercising client adoption, Alpine evaluation, props, active boundary events after target morph, and teardown. It does not prove automatic production graph emission or cap adoption. Three runs per engine pass. |
| [`component_first_scaling_harness.py`](component_first_scaling_harness.py) | Chromium boot and adoption for 100, 300, and 500 bare graph roots, plus a plain `x-data` control. Three runs per count and mode pass. |
| Existing RootGroup, rootless, refs client binding, scoped-slot, and x-props round-two harnesses | The selected adapter reuses the previously verified grouped listener, element-free lifetime, exact DOM magic, structural source-link, and loop-scope mechanisms. All five harnesses were rerun after this exploration and passed. |

All browser claims in this report use the repository's exact Alpine and morph
3.15.12 dependencies and Playwright 1.61.0. Research adapters do not modify
production packages.

## Architecture checkpoint

### Candidate outcomes

| Avenue | Outcome | Reason |
|---|---|---|
| Existing Alpine-first adapters | Keep as the behavior control, not as the long-term authority model. | It is viable, but component and fill identity remain reconstructed from DOM and Alpine state. |
| Citry graph first, Alpine binding engine | Provisionally select for the integrated Stage 3 spike. | It passed the broad, same-manifest, and partial real-render composition slices while making the intended server ownership explicit and leaving room to integrate the proved generic rootless mechanism. The prototype does not yet consume every typed edge. |
| Public-Alpine-hooks-only variant | Reject only as a constraint, not as an architecture. | Public-only access cannot preserve all exact-source magics today, but the control design already pays private Alpine costs. |
| Citry evaluator plus Alpine islands | Defer. | The prototype passed its bounded cases but immediately duplicated evaluator and magic work, lacked CSP, and did not cover Alpine's directive surface. |
| Citry fine-grained runtime | Defer until there is a product requirement for Citry-owned browser rendering or fragment directives. | A reactive core does not supply the missing DOM responsibilities. |
| Compiled hydration instructions | Retain as a future encoding optimization. | The selected runtime-neutral graph is compatible with compiled instructions, but current work does not need a second evaluator. |
| VDOM or incremental reconciliation | Defer. | Citry still receives server HTML and morphs real DOM. VDOM does not itself solve lexical slot ownership. |
| Alpine fork | Do not start. | The needed behavior is achievable with the exact pin and one adapter. A narrow upstream hook remains useful but optional. |
| Wrapper custom elements | Reject. | It fails text-only, empty, shared-root, contextual HTML, and invisible component-tag requirements. |

The selected graph is not identical to the earlier general-registry sketch.
The server spike proves that these identities must remain separate:

| Identity | Why it cannot be collapsed |
|---|---|
| Render ID | Identifies one faithful server component render. |
| Executed call or init edge | Connects one runtime call execution to the target render and orders initialization. One compiled node can execute many times. |
| Lexical source location | Identifies where client expressions were authored and where a live Alpine provider chain must be elected. |
| Logical fill | Groups one supplied fill or fallback independently from the number of outlets. |
| Physical region | Identifies one actual output occurrence, including multi-root, text-only, empty, nested, or mirrored output. |
| Stable client anchor | Owns continuity and is assigned during adoption, not serialized merely to complete the graph. |

The browser prototype is intentionally smaller than that target model. It
stores and validates the lexical, render-parent, and provide-parent fields,
but source evaluation currently resolves an already authored `sourceToken`
to a live provider. It does not walk `lexicalParentLocationId` or
`provideParentRenderId` to construct the provider chain. The only active use
of `renderParentId` is topological projection order when several instances
share one physical root. The fixture reverses both manifest records and a
pre-existing stale DOM token list; projection rewrites the list to the graph
order before Alpine initialization. Render-parent and provide-parent
cycles are rejected, but full typed-edge adoption and initialization remain
Stage 3 work. The graph is the provisional authority model, not a claim that
this research adapter already implements the whole model.

## Server representation findings

### Capture before flattening

Citry already knows the normal template-call facts, but no final object knows
all of them. The latest safe capture points are:

1. Each execution of `ComponentNode.render` records the authoring render,
   exact call span, target class, containing fill region, and a fresh call ID.
2. `_make_body_slot` records the lexical writer and whether the closure is a
   named fill, implicit fill, or fallback.
3. Every actual Slot invocation mints a physical region and records receiver,
   slot site, logical fill, lexical owner, and containing region. This is
   early enough to preserve the child-fallback transition nested inside a
   parent-owned fill.
4. `_render_one` binds the fresh target render ID to the earlier call record.
5. Serialization emits or consumes the already recorded graph. It cannot
   reconstruct it from flattened HTML.

The ten-case server harness records and asserts representative relationships
for ordinary and implicit fills, nested child fallback, a component inside a
fill, multi-root output, text-only output, empty output, a reused Python Slot,
mirrored outlets, and dynamic `<c-component>`. One mirrored logical fill
produces two unique physical regions. Reusing the same Python Slot at two
supplies produces two logical fills and two physical regions, not one fill
keyed by Python object identity. This is a capture-clock spike, not production
graph serialization.

### Two real server gaps

Two origins need an explicit production policy and capture path:

- A Python-provided `Slot` has no rendered supply location. Its optional
  construction position is not a live component-call location. The caller
  that attaches it needs to provide or mint a supply descriptor. Unknown
  source must remain explicit if no honest lexical source exists.
- Dynamic `<c-component>` currently records the Page-to-wrapper call, but the
  selected target reaches `_render_one` without the wrapper as parent and
  without a target call record. The dynamic component must emit an explicit
  wrapper-to-target edge or a specified transparent Page-to-target edge.

These are representation changes, not reasons to abandon component-first.
They are precisely the information that DOM ancestry cannot recover later.

### Range caps and emission policy

The server harness uses paired research comments around every observed Slot
invocation because this gives one representation to element, multi-root,
text, and empty output. It proves capability, not the final cap-every-fill
policy.

The recommended production rule is conservative:

1. Every client-active rootless or shape-changing component needs persistent
   range ownership.
2. Every client-active fill whose lexical ownership cannot be reconstructed
   from an existing region token needs a physical region record.
3. Nested inverse transitions must have their own record even when an outer
   fill is element-rooted.
4. Purely inert fills may omit caps only when the serializer can prove that
   no client ownership, lifecycle, morph, or diagnostic feature needs them.

The exact inert-fill optimization remains a product encoding decision. Start
with correctness and measure comment cost before making prediction logic
load-bearing.

## `$c-*` findings and decision

`$c-props` is viable in Citry's current HTML delivery model:

- direct `$c-props="..."` is preserved as a literal component kwarg;
- `c-$c-props="python_expression"` produces the dynamic `$c-props` key;
- server `c-bind` mappings preserve or conditionally omit `$c-props`;
- Chromium, Firefox, and WebKit preserve `$c-*` in HTML parsing,
  serialization, templates, cloning, MutationObserver, table and select
  contextual parsing, and HTML-parsed SVG;
- stock Alpine ignores it, which gives the attribute one clear owner; and
- Alpine morph changes, removes, and adds it without special handling.

The contract must also record the limitations:

1. Raw CSS `[$c-props]` is invalid. Use `CSS.escape`, `getAttribute`, or
   attribute iteration.
2. Alpine `x-bind:$c-props` and an `$c-props` key in Alpine object `x-bind`
   misparse on 3.15.12. Citry owns evaluation. Server `c-bind` owns dynamic
   server-time presence.
3. Require lowercase names and a non-empty `$c-props` expression.
4. XML SVG rejects the name. XHTML and standalone XML/SVG would need another
   transport if Citry ever supports them.

The architecture recommendation was to use `$c-props` for component-boundary
client props. The maintainer accepted it on 2026-07-20, superseding the
historical `x-props` decision in
[`exploration-x-props-round-2.md`](exploration-x-props-round-2.md). The
implementation uses the same structured binding record while the public
spelling, diagnostics, examples, and migration story move together.

Keep Alpine boundary handlers as `@event` or `x-on:event` and Citry Events
handlers in their accepted `@c-*` family. A future `$c-text`, `$c-model`, or
`$c-for` should exist only if Citry deliberately implements and documents
those semantics. The syntax namespace does not require a separate Citry
evaluator. If `$c-props` is approved, Citry can own its discovery, validation,
target routing, and lifecycle while the pinned Alpine adapter evaluates its
expression at the recorded source.

## Alpine API and private-coupling result

Private Alpine access is a comparative cost, not a binary gate. The fair
inventory has three tiers:

| Tier | Current or selected examples |
|---|---|
| Documented extension API | `plugin`, `magic`, `reactive`, `effect`, `start`, and current documentation's `addScopeToNode` example |
| Exported but undocumented behavior used by the accepted design | `addRootSelector`, `interceptInit`, `evaluate`, `evaluateRaw`, `dontAutoEvaluateFunctions`, `closestDataStack`, `mergeProxies`, `release`, `walk`, `onElRemoved`, the element overload of `Alpine.bind`, directive `.inline`, and the third `addScopeToNode` argument |
| Private fields or internal morph behavior | `_x_dataStack`, `_x_refreshXForScope`, `_x_teleportBack`, `_x_teleport`, `_x_refs_proxy`, `_x_id`, `_x_isShown`, `_x_pendingModelUpdates`, and morph's stack transfer and internal `cloneNode` bridge |

The required comparative view is:

| Dependency group | Landed runtime | Accepted Alpine-first props and scoped-fill control | Incremental graph-first need |
|---|---|---|---|
| Root discovery and init interception | `addRootSelector`, `interceptInit` | same | none |
| Component isolation and morph stack transfer | `_x_dataStack`, internal morph `cloneNode` | same | none |
| Raw exact-source evaluation and managed effects | narrower `evaluate`, `effect`, `release` use | adds `evaluateRaw`, `dontAutoEvaluateFunctions`, `closestDataStack`, `mergeProxies`, `walk`, `onElRemoved` | none beyond the accepted control |
| Ref, root, ID, and teleport source projection | not the full scoped-fill surface | adds `_x_teleportBack`, `_x_teleport`, `_x_refs_proxy`, `_x_id` | none beyond the accepted control |
| Direct native loop-source propagation | not landed | adds `_x_refreshXForScope` when that feature is claimed | none beyond the same feature |
| Grouped listener parity | not landed | adds `_x_isShown` and `_x_pendingModelUpdates` in the Citry-owned RootGroup adapter | none beyond the accepted control |
| Transaction-wide Alpine mutation control | not used | not required by the current control | avoid; would be a graph-first delta if product integration needs it |

The landed runtime already pays `_x_dataStack` and morph `cloneNode` costs.
The accepted Alpine-first props, scoped-fill, RootGroup, and refs direction
already needs the larger exact-source list. A graph-first registry can use
the same single adapter. Its inherent incremental private-field count is zero
relative to that complete accepted control, not relative to today's landed
runtime. This is why the public-only control failing does not falsify the
component-first design.

Component-first can remove repeated ownership inference, make rootless and
mirror lifetime independent of Alpine, route props and events from explicit
source records, and concentrate Alpine behavior in one module. It cannot
remove the Alpine stack while ordinary `x-*` must use component isolation,
or remove ref, ID, teleport, loop, and morph integration while promising
exact native Alpine behavior.

Avoid widening the selected design merely to implement an initialization
hold. Validate and stage the graph before DOM insertion and continue using
the existing initialization interception. If product integration proves that
insufficient, record `deferMutations`, observer stop/start, `initTree`,
`destroyTree`, or clone interception as an explicit incremental dependency.

The prototype's `destroy()` stops props effects, grouped listeners, ranges,
and instance groups. Alpine does not expose unregister functions for
`addRootSelector` or `interceptInit`, so production must install those hooks
once through a permanent broker whose removable active-runtime registry is
the lifecycle boundary. A destroyed prototype returns a nonmatching root
selector and guards its interception callback, and a post-destroy future-root
canary passes, but creating one permanent Alpine callback per fragment would
still leak callbacks even when their behavior is inert.

Source review indicates that the smallest useful upstream improvement is a
supported, retargetable logical
root-traversal parent used by Alpine's `findClosest`, with internal ref and ID
cache invalidation and correct composition with native teleport. It could
remove direct `_x_teleportBack`, `_x_teleport`, `_x_refs_proxy`, and `_x_id`
manipulation. It would not by itself solve data-stack projection, direct
`x-for` identity, fragment lifetime, or grouped listeners. Pursue it as an
optional upstream proposal, not a prerequisite for implementation. No
public-hooks-only browser control or patched Alpine build was executed in
this exploration, so the proposed hook's exact reach remains source-audited,
not experimentally settled.

One shared baseline bug also needs its own canary: Citry warns and leaves an
unrelated existing `window.Alpine` installed, but morph later calls
`window.Alpine.cloneNode`. The warning test does not currently morph. This
can break either architecture and must not be charged only to graph-first.

## Partial real-render composition slice

The selected-design composition slice starts from a real Citry template
containing:

```html
<c-card
  $c-props="{ theme, count }"
  @click.once="count += 1"
  @dblclick="count += 10"
>
  <c-fill name="body">
    <strong x-text="`${owner}:${$refs.same.id}`"></strong>
  </c-fill>
</c-card>
```

The Card renders two element roots. The research trace records one executed
call, two component instances, distinct call and fill source locations, one
physical fill region, and the literal boundary attributes passed through the
real component kwargs. The harness then manually composes those records with
region selectors, `sourceToken` values, and binding records to create a
versioned graph. It serializes the real HTML and adopts both through the
graph-first adapter before Alpine starts. That composition step is important:
this is not yet an automatic capture-to-wire or cap-adoption test.

`$c-props` in this fixture exercised the candidate syntax that the maintainer
later selected.

Across three runs in each engine, the slice verifies:

- the fill sees `parent` and the parent's `x-ref`, not child data or refs;
- genuine Alpine content in the Card sees the child component scope;
- `$c-props` supplies `{count: 0, theme: "blue"}` and reacts to the parent;
- the two Card roots share one `.once` listener, with the physical second root
  reported as carrier and target;
- replacing the source root re-elects `parent-new`, the new ref, and new prop
  values;
- replacing the second target root from `BUTTON` to `ARTICLE` preserves the
  stable `els` array object, updates its members, moves an active non-`.once`
  listener to the new root, and prevents the detached root from delivering;
  and
- destroying the runtime prevents later event delivery.

The broader browser fixture separately verifies that retargeting a descriptor
removes its old comment-cache entry and claims the new one. After the old
source comment is reinserted alongside the replacement, target-relative
election produces two distinct descriptors with the correct carriers.

The manifest for this intentionally readable two-instance slice is 1,401
bytes as compact JSON. Deterministic gzip was 438 to 443 bytes across sampled
runs because Citry's fresh render IDs change the payload contents. That is
evidence for payload shape, not a final encoding budget.

### What the vertical slice does not clear

The slice does not pretend to be the production Events runtime. These remain
integration acceptance work:

- atomic graph staging and rollback around the full product morph;
- the real Events queue, dequeue liveness, physical overlap, busy and loading
  state, cancellation, and `Citry.events.send(element)` policy;
- late class and fragment registration, duplicate registration, and class
  load failure;
- stable-anchor correlation with the product identity and epoch machinery;
- dynamic `<c-component>` target ancestry and Python Slot supply descriptors;
- malicious size limits, cross-fragment references, rolling schema versions,
  and missing or stripped caps; and
- production serializer emission and Rust marker-contract implications.

It also does not exercise a product implementation deriving the manifest,
selectors, source markers, or cap policy from the captured records. Those
parts are manually assembled in the harness.

Those need one integrated implementation spike after the protocol record
shape is reviewed. They do not need another blue-sky architecture survey.

## Acceptance summary

Legend: **pass** means exercised by retained browser or server-capture evidence;
**inherited** means the selected design deliberately reuses a passing pinned-
Alpine or Citry mechanism; **server** means provenance was proved but not the
complete browser lifecycle; **not tested** is an open acceptance item;
**unsupported** is an explicit boundary.

### Shapes and ownership

| Requirement | Graph-first Alpine | Citry evaluator prototype |
|---|---|---|
| Single and several element roots with shared component scope | pass | pass in the common multi-root boundary fixture |
| Text-only and empty component | inherited generic rootless mechanism; graph-instance integration not tested | not tested |
| Rooted to rootless and rootless to rooted | inherited generic rootless mechanism; graph-instance integration not tested | not tested |
| Wrapper-only component | not tested | not tested |
| Several instances on one physical root | pass, innermost scope wins | not tested |
| Nested isolated components | pass | child-local Alpine island pass, deeper nesting not tested |
| Ordinary and implicit fill | pass/server | common ordinary fill pass; implicit not tested |
| Child fallback and fallback nested in parent fill | pass/server | not tested |
| Component inside fill | server plus isolated browser equivalent | not tested |
| Nested passthrough and multiple named fills | server model supports transitions; full browser case not tested | not tested |
| Reusable Python Slot at two call sites | server, source policy open | not tested |
| Mirrored outlet and removal of one copy | server provenance plus inherited range mechanism; combined graph-fill lifecycle not tested | not tested |
| Two mirrors with colliding refs, IDs, handlers, and transitions | not tested | not tested |
| Typed default | not tested, public policy open | not tested |
| Trusted Python HTML and callable fill | not tested, source policy open | not tested |
| `{{ slot }}`, `CitryElement`, and `CitryRender` | server gaps classified, full browser case not tested | not tested |
| Static component | pass | pass in hand fixture |
| Dynamic `<c-component>` | server gap proved, client case not tested | not tested |
| Extension replacement | not tested | not tested |

### Alpine behavior

| Requirement | Graph-first Alpine | Citry evaluator prototype |
|---|---|---|
| Component base scope without user `x-data` | pass | component state exists, ordinary `x-*` exposure not implemented |
| Local and nested `x-data`, reads, writes, shadowing, assignment | pass/inherited | bounded reads, writes, and child island pass |
| `$data`, `$refs`, `$root`, `$id` | pass/inherited exact-source adapter | bounded `$refs` and `$root` bridge pass; `$id` bridge exists but was not exercised, and `$data` parity is incomplete |
| `$el`, `$dispatch`, `$event`, target, `currentTarget` | inherited from refs client binding and RootGroup | `$el` and `$event` bounded pass; full parity not tested |
| `x-ref` initialization, collision, replacement, and source replacement | pass/inherited | source replacement pass; full collision matrix not tested |
| `x-id` stability and repeated names | inherited exact-source spike | not tested beyond magic bridge |
| `x-show`, `x-text`, `x-html`, `x-bind`, `x-model` | native Alpine retained; `x-text` exact-source pass, full matrix inherited or not tested | `$c-text` prototype only; rest remain Alpine-island-only |
| Transition start, cancellation, removal | inherited RootGroup and Alpine behavior; graph-specific matrix not tested | not tested |
| Custom magic, directive, store, official plugin | native Alpine retained; integration matrix not tested | Alpine islands retain them, Citry expressions need one bridge per magic |
| Async expression and thrown expression | inherited evaluator behavior, graph-specific recovery not tested | not tested |
| Strict CSP | not tested with Alpine CSP build | unsupported by `new Function` prototype |
| Direct `x-if` template root | pass | genuine island control only |
| Direct `x-for`, iteration refresh, fresh Citry clone identity | source-frame substrate inherited; browser component instantiation unsupported | unsupported without a separate blueprint protocol |
| Nested and repeated teleport | pass/inherited source link; native event path remains physical | not tested |
| Open shadow root | inherited handler and RootGroup pass | not tested |
| Closed shadow root | unsupported without shadow-local ownership/listener design | unsupported |

### Props, events, identity, and lifecycle

| Requirement | Graph-first Alpine | Citry evaluator prototype |
|---|---|---|
| First props supply and reactive update | pass | pass |
| Dynamic key add, replace, remove, reorder | inherited props spike; graph wrapper not retested | not tested |
| Unknown, missing, invalid, recovering prop | accepted design/inherited validation; not integrated here | not tested |
| Multi-root supplier carrier replacement | pass for source replacement and target group refresh | source replacement pass |
| Rootless init and later roots | inherited generic mechanism; graph-instance, props, and anchor integration not tested | not tested |
| Alpine and Citry component-tag handlers | inherited exact-source client binding; Alpine vertical case pass | one generic boundary handler pass |
| Child-local handler and callback-through-props control | inherited exact-source spike | child-local genuine Alpine control pass; callback case not tested |
| Group modifiers including global, outside, once, debounce, throttle | inherited RootGroup pass | `.once` pass; full RootGroup can be reused but not wired in all cases |
| Native physical event values, capture, bubble, teleport path | inherited RootGroup and refs client binding | bounded physical values pass; full matrix not tested |
| Programmatic Citry send and queue states | not tested in component-first product integration | not implemented |
| Initial adoption and head-loaded manifest | pass for body manifest before start; head case not tested | same limitation |
| Late fragment and class registration order | not tested | not tested |
| Same-node morph, tag replacement, source and target replacement | physical replacement and active-listener refresh pass; fresh-render-ID to stable-anchor adoption not tested | source replacement pass; target morph not tested |
| Key reorder, root-count change, mirror add/remove, nested range | inherited physical mechanisms; combined graph and two-identity adoption not tested | not tested |
| Table, select, SVG context | inherited rootless pass; `$c-*` transport pass | syntax transport pass, directive lifecycle not tested |
| Move, remove, reinsert, pending timer/request cleanup | inherited RootGroup/rootless cases; request cleanup not integrated | not tested |
| Malformed, duplicate, dangling, cyclic, and schema-version records | exact negatives pass for unsupported version, duplicate instance ID, dangling instance region, and lexical, render-parent, and provide-parent cycles. Malformed shapes, ownership consistency, caps, limits, and atomic adoption are not tested | same bounded GraphModel validation |
| Missing or stripped comment cap | inherited rootless pointed failure; production transaction not tested | not tested |
| Duplicate registration and second Alpine copy | existing runtime behavior, extra morph canary required | not tested |
| Browser clone with fresh recursive identity | unsupported until blueprint protocol | unsupported |
| Exact once-only logical cleanup | runtime teardown stops owned props effects and grouped boundary listeners; product graph, permanent hook broker, and stable-anchor integration pending | bounded props-effect and listener cleanup pass |

### Delivery modes

| Requirement | Result |
|---|---|
| Current classic script | pass |
| Minified bundle | exact dependencies are minified-capable; research adapter not production-minified |
| TypeScript, JSX, TSX output | architecture-compatible, not executed |
| ESM with top-level import and dynamic import | architecture-compatible because it consumes registrations and structured manifests without wrapping user source; not executed |
| Fragment before module and failed module | protocol requirement retained, not tested |
| Source maps and pointed diagnostics | source spans captured server-side; client source-map integration not tested |

## Measurements and limits of measurement

| Measurement | Observed value | Interpretation |
|---|---:|---|
| Common comparison manifest | 1,590 bytes compact JSON | Same payload for both candidates, readable rather than optimized. |
| Real-render plus manual-graph two-instance manifest | 1,401 bytes raw, 438 to 443 bytes deterministic gzip in sampled runs | Fresh render IDs change compressed content. The range confirms moderate compression and exposes the need to measure realistic pages. |
| Readable 100-instance graph | 9,678 bytes raw, 1,373 bytes deterministic gzip | About 97 raw bytes or 14 gzip bytes per bare instance in this repetitive fixture. |
| Readable 300-instance graph | 29,878 bytes raw, 4,071 bytes deterministic gzip | Linear readable-record growth, before interning or token compaction. |
| Readable 500-instance graph | 50,078 bytes raw, 6,761 bytes deterministic gzip | About 100 raw bytes or 14 gzip bytes per bare instance. |
| Chromium bare graph boot and adoption | 8.4 ms at 100, 10.6 ms at 300, 13.1 ms at 500 | Exploratory timestamps only. Median of three, excludes adapter script parse, and has no bindings or user `x-data`. |
| Chromium plain `x-data` control | 19.7 ms at 100, 21.1 ms at 300, 25.2 ms at 500 | A workload and readiness control, not a comparable baseline or overhead subtraction. It compiles one `x-data` expression per root while the graph fixture supplies objects directly. |
| Research component-first adapter | 22,439 bytes raw, 5,297 bytes deterministic gzip | Unminified prototype with two engines and validation, not a production bundle estimate. |
| Five loaded research adapters | 74,300 bytes raw, 19,095 bytes as the sum of each deterministic gzip size | Strong upper-bound context only; production code would merge overlapping helpers. |
| Citry versus Alpine evaluation loop | about 2.7 to 3.5 times slower in this retained run | Different implementation paths perform different bridge work. This is a negative control, not evaluator overhead or a framework benchmark. |
| Browser repetitions | broad and vertical: 3 per engine; common comparison: 5 per mode and engine | All asserted runs passed. |

Combined startup when graph roots also carry real user `x-data`, representative
prop-update cost, large-manifest validation, same-root and root-count-changing product morph,
retained records after removal, final minified bundle size, and real work-app
migration performance were not measured here. They belong in the production
integration spike. The work-app audit makes a replacement runtime especially
high risk: it contains 51 `x-data` roots, 32 named Alpine components, broad
directive and custom-magic use, and pages that can reach hundreds of roots.
The graph-first design preserves that investment. The selected `$c-props`
spelling also avoids colliding with the audited application's existing
third-party `x-props` usage.

## Decisions and remaining work

### Decisions supported by this exploration

1. Use the server graph, not Alpine or DOM ancestry, as the
   authority model for Citry instances, calls, lexical sources, logical fills,
   and physical regions. Full typed-edge consumption remains a Stage 3 gate.
2. Pinned stock Alpine is the near-term directive and reactivity engine.
3. Private Alpine access is allowed behind one exact-version adapter and is
   judged by incremental delta and canary burden.
4. `$c-props` is the selected Citry component-boundary props directive;
   `c-$c-props` and server `c-bind` are both allowed dynamic forms.
5. Genuine Alpine attributes retain Alpine ownership and names.
6. RootGroup remains the grouped-root physical adapter. The generic
   comment-bounded rootless and mirror mechanism remains the candidate for
   graph integration. No wrapper is introduced.
7. A VDOM, Alpine fork, or Citry directive framework is not justified only to
   solve component and slot ownership.

### Product decisions still required

1. The cap emission policy for inert element-rooted fills.
2. The source policy for Python Slot, callable, trusted HTML, and typed
   default origins without an honest client location.
3. The transparent versus explicit init edge for dynamic `<c-component>`.
4. The public `Citry.events.send(element)` owner inside source-linked fills.
5. Whether logical component listeners ever observe teleported events beyond
   the native DOM path.
6. Supported schema-version window, graph size limits, and comment-stripping
   policy.
7. Mirror state split, ref and ID collision behavior, copy-local listeners
   and transitions, source replacement, and final logical-fill cleanup.
8. Fresh-render-ID to stable-anchor graph revision, including class
   replacement and old-render retirement.

### Bounded implementation sequence

1. Add internal render-time call, source-location, logical-fill, transition,
   and physical-region records at the proved capture points. Resolve dynamic
   target and Python Slot policies before serializing them.
2. Define a versioned, atomically validated fragment manifest. Keep render
   IDs separate from browser stable anchors and include diagnostic spans.
3. Implement the general client registry below optional Events anchors. Make
   stable `scope`, `props`, and `els` registry fields.
4. Merge the existing source-link, RootGroup, rootless, refs, and morph
   mechanisms into one pinned Alpine adapter with a complete private-symbol
   canary inventory.
5. Recognize `$c-props`, `@...` / `x-on:...`, and `@c-*` as the three special
   client binding families. Change the spelling and related
   diagnostics together. All other attributes remain Python component inputs.
6. Integrate graph staging with the product morph and Events queue. Verify
   adoption before initialization, rollback or pointed terminal failure,
   dequeue liveness, physical overlap, busy state, and exact cleanup.
7. Run the full acceptance matrix, production-sized payload and startup
   measurements, and audited-work-app migration cases before freezing the
   wire schema.
8. Update [`events.md`](../events.md), [`component_slots.md`](../component_slots.md), and
   [`alpinejs.md`](../alpinejs.md) from the implemented and reverified result.

### Reproduction

Run from the repository root:

```bash
uv run python docs/design/alpinejs/component_first_server_ownership_harness.py
uv run python docs/design/alpinejs/component_first_syntax_server.py
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/component_first_syntax_browser.py
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/component_first_harness.py
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/component_first_comparison_harness.py
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/component_first_scaling_harness.py
uv run --isolated --offline --with 'playwright==1.61.0' \
  --with-editable packages/py/citry \
  python docs/design/alpinejs/component_first_vertical_harness.py
```

The original research brief follows.

## 1. Why this exploration comes next

The scoped-slot report says that its split-phase prototype does not prove
server serialization, the general Citry registry, Citry-magic routing, queue
integration, nested ownership encoding, mirrored or rootless fill lifetime,
or full product morph integration. That sentence compresses different kinds
of unfinished work. It does not mean that seven independent design
explorations are required.

| Item | Actual state | Next work |
|---|---|---|
| Server serialization | Citry's render objects still know the active Python context, but serialization drops slot invocation identity and logical ownership transitions. | Choose a structural source, transition, and optional range representation, then prove it through the real serializer. |
| General Citry registry | A general client-instance registry below optional Events anchors is already accepted in [`events.md`](../events.md) and [`exploration-x-props-round-2.md`](exploration-x-props-round-2.md). It is not yet the product runtime. | Reconsider its record shape in this exploration, then implement and verify the chosen form. |
| Citry-magic routing | The semantics are mostly settled: lexical Citry magics follow the exact authored source, while the physical element remains available separately. | Prove the chosen source representation in the real evaluator and runtime. This is not a fresh semantics exercise. |
| Queue integration | The request queue and its physical-overlap dependency graph already exist. The fill-specific gap is preserving both logical send ownership and physical overlap. | Add integrated queue, dequeue, liveness, busy, and cleanup acceptance cases after the representation is chosen. |
| Nested ownership encoding | This remains a real representation problem. Parent-owned fill, child-owned fallback, nested component, passthrough, and return to the parent can all occur in one flattened result. | Design and spike the encoding as part of the component-first model. |
| Mirrored or rootless fill lifetime | The generic comment-range, mirror, contextual-parse, and exact-cleanup mechanism passed [`spike-rootless-lifecycle.md`](spike-rootless-lifecycle.md). | Decide which fills need range caps, then integrate the proved mechanism with real serialization and morphing. |
| Full product morph integration | Product morphing, stable anchors, keyed linking, the grouped-root listener adapter (`RootGroup`), and rootless morph mechanisms already have positive evidence. Scoped-fill ownership is not integrated with them. | Run one end-to-end adoption and replacement spike after the representation is chosen. |

The genuinely open policy questions are narrower:

1. What client scope owns typed slot defaults and direct root composition when
   there is no outside component call site?
2. Must component-tag or outer listeners logically observe an event from a
   fill that was teleported outside their native propagation path?
3. Which text-only or empty fills pay for persistent comment caps?
4. What is the public behavior of `Citry.events.send(element)` inside a
   source-linked fill?
5. Does Citry accept permanent pinned-version Alpine internals, seek a public
   upstream hook, or own more of the client runtime?

The component-first exploration should happen before the final ownership
serialization, registry schema, and Alpine-specific source backlink are
frozen. Doing the integration first would harden the exact adapter machinery
this exploration is meant to question. The positive RootGroup, rootless,
identity, morph, and exact-source spikes remain prerequisites and falsifiers;
they should not be repeated from scratch.

The intended order is:

1. run this architecture exploration;
2. choose the near-term client ownership model;
3. choose the serialized source, transition, region, and binding records;
4. run one integrated vertical spike from the Python render tree through
   browser teardown; and
5. turn the result into implementation work and acceptance coverage.

Low-regret harness construction and measurement can proceed while the
exploration runs. A production metadata format or widening use of Alpine
private fields should not.

## 2. Evidence boundary

This brief starts from the following local evidence:

- [`exploration-slots-alpine-scope.md`](exploration-slots-alpine-scope.md)
  proves a viable split-phase source-link primitive and rejects several
  attractive but incorrect shortcuts.
- [`exploration-x-props-round-2.md`](exploration-x-props-round-2.md) defines
  component-boundary props and event client bindings, exact source evaluation, the
  parent-call init graph, and the general registry direction.
- [`spike-citry-handler-refs.md`](spike-citry-handler-refs.md) proves that an
  Alpine handler expression and a Citry binding's optional argument expression
  can use parent ordinary data, `$data`, `$refs`, `$root`, and `$id`, while
  `$el`, `$dispatch`, `$event`, `target`, and `currentTarget` remain physical.
  It does not prove Citry server-handler parsing or dispatch.
- [`spike-root-group.md`](spike-root-group.md) proves grouped element roots,
  union containment, shared listener state, stable `els`, and exact listener
  cleanup without a wrapper.
- [`spike-rootless-lifecycle.md`](spike-rootless-lifecycle.md) proves logical
  component lifetime through comment ranges, including text-only and empty
  output, root-count changes, mirrors, contextual parsing, and cleanup.
- [`spike-component-identity.md`](spike-component-identity.md),
  [`spike-keyed-morph.md`](spike-keyed-morph.md), and
  [`spike-morph-alpine.md`](spike-morph-alpine.md) constrain identity,
  linking, state preservation, and morph adoption.
- [`events.md`](../events.md) is the accepted Events design. This exploration
  may recommend changing the underlying client ownership mechanism, but it
  must name any public semantics it proposes to reopen.
- [`component_slots.md`](../component_slots.md) defines the server slot model. The browser model
  must not pretend that final DOM ancestry is the same thing as the Python
  writer and receiver contexts.
- [`alpine-vuetify-audit.md`](../alpinejs/alpine-vuetify-audit.md),
  [`alpine-workproject-audit.md`](../alpinejs/alpine-workproject-audit.md), and
  [`alpine-ecosystem-2026.md`](../alpinejs/alpine-ecosystem-2026.md) establish
  actual Alpine use, private-API exposure, migration pressure, and ecosystem
  costs.
- [`asset_compiler.md`](../asset_compiler.md) and [`esm.md`](../esm.md)
  require the runtime contract to remain compatible with compiled JS, TS,
  JSX, TSX, and a possible future module loader. No design may depend on a
  regex rewrite or wrapping the user's whole source file in a function.

The research pass must also read the pinned Alpine and morph sources in
`packages/js/citry-client/node_modules`, the current TypeScript client, the
Python render and serializer paths, and any current implementation that has
landed since these reports were written.

External prior art must come from primary sources and current code. At
minimum, compare Alpine's extension and reactivity APIs, Alpine and morph
source, Vue's standalone reactivity model, Preact Signals core, Livewire's
component and morph metadata, and one fine-grained DOM runtime. The point is
not to select a fashionable dependency. A reactive primitive supplies
dependency tracking; it does not supply expression evaluation, directives,
models, transitions, refs, structural cloning, event modifiers, or DOM
cleanup.

Useful starting references:

- <https://alpinejs.dev/advanced/extending>
- <https://alpinejs.dev/advanced/reactivity>
- <https://vuejs.org/guide/extras/reactivity-in-depth.html>
- <https://preactjs.com/guide/v10/signals/>
- <https://livewire.laravel.com/docs/3.x/morphing>

## 3. Product invariants every avenue must preserve

The exploration may replace mechanisms, but it must not quietly discard these
requirements.

### 3.1 Component and slot ownership

1. The Python render tree is the authority for server component instances,
   calls, fills, fallbacks, and nested ownership transitions.
2. A supplied fill evaluates in the exact client scope where the receiving
   component was invoked.
3. Child fallback belongs to the child, including fallback nested inside a
   parent-owned fill.
4. A nested component inside fill markup is isolated like any other component.
5. Shared physical roots, multiple roots, text-only output, and empty output
   are valid component shapes. No solution may require an inert wrapper.
6. Mirrored slot outlets may give one logical fill more than one physical
   region. Each physical copy needs independent liveness while sharing the
   intended logical state.

### 3.2 Props and handlers at component boundaries

1. Client props, Alpine event handlers, and Citry `@c-*` handlers are the
   three special client binding families on a component tag. The accepted Alpine-first
   spelling is `x-props`. An architecture with Citry-owned client directives
   must test `$c-props` so Citry-specific behavior does not claim Alpine's
   `x-*` namespace.
2. Other Alpine-looking attributes such as `x-show`, `x-model`, `:class`, and
   `x-transition` remain ordinary Python component inputs. A component may
   accept an `attrs` mapping and decide where to place them.
3. Props travel down. A component-tag Alpine handler expression and a Citry
   binding's optional argument expression evaluate at the exact parent source
   location. The Citry server-handler name travels separately to the source
   Events anchor.
4. A handler authored inside the child template remains child-local. Passing a
   callback through props is the explicit capability grant to child scope.
5. Ordinary data and lexical magics come from the authored source. `$el`,
   `$dispatch`, `$event`, native `target`, and native `currentTarget` remain
   physical.
6. Citry `@c-*` additionally sends through the logical source Events anchor,
   while the child root is the physical trigger and busy carrier.

### 3.3 Identity and lifecycle

1. Fresh server render IDs and stable client anchors are different
   identities. The first is faithful to the current render. The second owns
   continuity across a morph.
2. Stable-anchor resources and per-render invocation resources remain
   different lifetimes. State, the resolved props bag, exposed scope, and the
   stable `els` collection can survive a linked morph. A `$component`
   invocation's managed effects and returned cleanup are torn down once and
   recreated when that callback fires for the new render, as required by the
   accepted Events lifecycle. Client bindings and physical listeners follow
   their own record and region revisions.
3. Incoming ownership records must be linked before Alpine or any replacement
   directive engine initializes the incoming DOM.
4. Morph, replacement, move, removal, failed init, and partial-root loss must
   each have exact cleanup semantics.
5. Server-created and browser-created components cannot share an identity
   shortcut. A browser clone needs a real instantiation protocol and fresh
   recursive identities.

### 3.4 Alpine coexistence

1. Existing user-authored `x-data` remains useful. In a component-first model,
   it should add local template variables to the Citry-owned base scope rather
   than become the source of component identity.
2. Existing `x-show`, `x-text`, `x-model`, `x-bind`, `x-transition`, `x-ref`,
   `x-id`, event modifiers, plugins, and custom magics need an explicit
   compatibility answer.
3. A second copy of Alpine must not initialize the same DOM independently.
4. Citry ownership must not depend on the grammar or wrapper form of
   `Component.js`. Class registration must work with classic scripts, future
   ESM, and asset compiler output.
5. Strict CSP behavior, async expressions, errors, assignment, `this`, and
   cleanup are part of evaluator parity, not incidental details.

## 4. The model to test

The most promising abstraction is not initially a virtual DOM. It is a typed
logical graph plus a physical region index over the real DOM.

One graph should not encode every relation. Citry has at least four different
structures:

1. **Instance relations.** Stable client anchor, fresh render ID, class,
   rendered parent, component call parent, provide/inject parent, and init
   dependency are typed fields or edges. They must not be collapsed into one
   unqualified parent pointer merely because several coincide in simple DOM.
2. **Lexical scope graph.** The exact source location and provider chain under
   which an expression was authored. A slot edge can diverge from physical
   containment and can temporarily return from parent ownership to child
   fallback ownership.
3. **Physical region mapping.** One instance or fill can map to an ordered
   element group, a comment-bounded range, several mirrors, a teleported
   region, or no live element. Multiple logical instances can also map to the
   same physical element.
4. **Native DOM and request relations.** Events dispatch through the browser's
   physical path. Request overlap is computed from live physical regions,
   while logical send ownership comes from the source record. These relations
   change as nodes move.

The combined model is a typed graph, not one DOM-derived tree and not one
unqualified "scope DAG." Each individual parent relation should be acyclic,
and cycle detection must fail pointedly. Shared roots and mirrors are natural
many-to-many mappings rather than fake parent edges.

A runtime-neutral sketch, deliberately not a wire schema, is:

```ts
type Instance = {
  anchorId: string | null // Client-assigned; absent in unadopted server data.
  renderId: string
  callId: string
  classId: string
  renderParentId: string | null
  callParentId: string | null
  initDependencyCallId: string | null
  provideParentRenderId: string | null // Server-authored provider edge.
  provideParentAnchorId: string | null // Resolved by the browser at adoption.
  scopeHandle: string | null // Client-assigned with the stable anchor.
  regionIds: string[]
  capabilities: Array<"component-js" | "props" | "handlers" | "events">
}

type ScopeLocation = {
  id: string
  ownerRenderId: string | null
  lexicalParentLocationId: string | null
  liveProviderHandle: string | null // Client-assigned after source adoption.
  kind: "component" | "fill" | "fallback" | "local-data" | "client-binding-source"
  diagnosticSource?: { template: string; start: number; end: number }
}

type PhysicalRegion = {
  id: string
  logicalOwner: { kind: "instance" | "fill"; id: string }
  kind: "elements" | "range" | "mirror" | "teleport"
  rootTokens: string[]
  startCap?: string
  endCap?: string
}

type Binding = {
  id: string
  sourceLocationId: string
  targetRegionId: string
  logicalTargetRenderId: string
  family: "props" | "alpine-event" | "citry-event" | "directive"
  expressionOrSpec: unknown
}
```

The sketch intentionally gives the different relations different fields. The
spike may later prove that two fields share one encoded value, but it must not
infer one relation from another. In particular, the accepted Events anchor is
client-internal and is not added to the server wire merely to complete this
example.

The identity authorities and lifetimes to verify are:

| Identity | Authority | Lifetime | Normally serialized? | Purpose |
|---|---|---|---|---|
| Client anchor | Browser | Stable across a successfully linked morph | No | State, continuity, epoch, and stable scope owner |
| Render ID | Server | One rendered instance version | Yes | Faithful current server identity and DOM correlation |
| Call ID | Server | One component callback/invocation record | Yes when client-active | Init dependency and callback ordering |
| Class ID | Component registration | Component class | Yes when client-active | Code, prop, and event contract lookup |
| Scope handle | Browser | Stable-anchor lifetime | No, unless a future protocol proves otherwise | Reactive component base scope |
| Source-location ID | Server plus browser adoption | One rendered authored location, re-elected while live | Yes | Exact lexical evaluation owner |
| Fill or binding ID | Server | One rendered logical record revision | Yes | Client binding and ownership record lookup |
| Physical region ID | Server or fragment normalizer | One physical rendered region | Yes when needed | Root group or range membership |
| Mirror token | Server or fragment normalizer | One physical copy | Yes when needed | Independent copy liveness and cleanup |
| Diagnostic span | Compiler | Template source revision | Only for diagnostics when useful | Pointed errors |

One `sourceId` is insufficient. An exact location inside a multi-root or
teleported source can have a different Alpine provider chain and `$refs`
namespace from the source instance's first root.

### 4.1 Worked ownership transition

Consider a parent-owned fill that invokes another child whose own template
contains fallback:

```html
<!-- Page template -->
<c-tooltip>
  <button x-text="label">
    <c-icon />
  </button>
</c-tooltip>

<!-- Icon template -->
<span class="icon">
  <c-slot><span x-text="fallbackLabel"></span></c-slot>
</span>
```

The final DOM may look like a normal nested tree, but the lexical sequence is
not simply "nearest component wins":

```text
Tooltip-owned template region
  Page-owned fill region
    Page-owned button expression
    Icon component boundary
      Icon-owned template region
        Icon-owned fallback expression
    Page-owned fill region resumes
  Tooltip-owned template region resumes
```

The serializer must preserve every transition and its inverse. Stamping only
the outside fill does not distinguish the nested fallback. Stamping every
descendant with the outside source destroys nested component isolation.

### 4.2 Evaluation has four explicit inputs

For every installed binding, record these separately:

| Input | Example responsibility |
|---|---|
| Lexical owner | ordinary variables, `$data`, `$refs`, `$root`, `$id`, Citry magics |
| Physical carrier | `$el`, `$dispatch`, `$event`, native target and `currentTarget` |
| Logical target | component anchor used for props delivery or Citry event dispatch |
| Physical listener group | one element, a `RootGroup`, `window`, `document`, or no carrier |

This decomposition is required even if the chosen implementation later packs
some fields together.

## 5. Architecture avenues to compare

The spike must carry at least the following avenues through the same examples
and acceptance matrix. It may add stronger alternatives.

### 5.1 Baseline: Alpine-first adapters

This is the current direction used as a control. Citry emits instance and
client binding records, attaches stable reactive scopes to roots, and uses Alpine data
stacks plus teleport-like backlinks to recreate lexical ownership.

Advantages:

- smallest change from the accepted x-props and slots work;
- maximum compatibility with existing `x-*` syntax and Alpine plugins;
- existing exact-source, RootGroup, rootless, and morph spikes are directly
  reusable; and
- no new expression language or directive engine.

Costs and risks:

- component ownership is still translated into Alpine's physical-root model;
- `$refs`, `$root`, `$id`, clone propagation, and cache invalidation require
  coordinated private fields;
- rootless scopes remain Citry-owned but cannot host normal Alpine directives;
- shared physical roots expose one effective Alpine stack; and
- every new Alpine feature must be checked against the adapter.

Falsifier: the private patch surface keeps widening, or exact source behavior
cannot survive source replacement and structural clones without destructive
restamping.

### 5.2 Citry graph first, Alpine as the DOM binding engine

Citry owns the authoritative instance, lexical-location, region, binding, and
lifecycle records. Alpine supplies reactivity, ordinary directives, modifier
behavior, and morphing. Alpine data stacks are a projection of Citry state for
ordinary rooted content, not the registry itself.

Key implications:

- props and handlers resolve directly through `Binding.sourceLocationId`;
- component and fill lifetime is independent of the presence of an element;
- local `x-data` contributes an Alpine-owned provider layer at a recorded
  location without defining the component boundary;
- Citry can preserve logical ownership through a teleport without pretending
  native events bubble through the source component;
- the client registry can outlive and re-adopt physical roots during morph;
  and
- a future non-Alpine consumer can read the same runtime-neutral records.

This is the leading low-regret hypothesis, not an accepted outcome. The
research must show whether stock Alpine can consume the graph without the
adapter becoming as complex as the baseline.

Falsifier: ordinary Alpine directives and lexical magics cannot use recorded
Citry ownership without an expanding page-global evaluator or directive
override.

### 5.3 Stock Alpine hooks and private-API delta

Build the graph from 5.2 using documented Alpine extension hooks where they
fit and the same pinned private integration techniques the Alpine-first
baseline already requires where they do not. Explore root selectors,
`interceptInit`, custom directives, magics, managed directive effects,
`Alpine.bind`, clone and evaluator hooks, and the current private scope,
teleport, ref, ID, and loop fields.

The comparison must have three columns:

1. private dependencies already required by the current Alpine-first
   design and runtime;
2. incremental private dependencies introduced only by the component-first
   graph; and
3. baseline private dependencies the component-first graph can remove or
   concentrate behind one adapter.

A public-hook-only experiment remains valuable because it identifies the
smallest plausible upstream "logical evaluation parent" hook. Failure of that
experiment does not falsify component-first. Requiring private Alpine access
is already a cost paid by the control architecture.

Falsifier: compared with the Alpine-first control, component-first materially
widens the pinned private surface or upgrade-canary burden without reducing
ownership reconstruction, destructive restamping, or another measured source
of complexity. Report that delta rather than using private access as a binary
criterion.

### 5.4 Citry evaluator and directives with Alpine islands

Citry owns evaluation for component props, optional Citry event argument
expressions and routing, component-boundary Alpine handler expressions,
component state, and a new explicit client-directive namespace. Citry handler
names remain parsed server identifiers, not executable expressions. Alpine
remains supported for ordinary local `x-data` islands and existing `x-*`
markup.

Variants to compare:

1. a minimal `$c-*` family beginning with `$c-props`, the Citry-owned spelling
   for client prop supply;
2. a larger, deliberately Citry-specific family such as `$c-effect` or
   `$c-text` only if Citry actually owns those semantics; and
3. an Alpine interoperability bridge where genuine Alpine features retain
   their real names, including `x-data`, `x-if`, `x-for`, `x-teleport`,
   `x-show`, and `x-model`.

Citry must not silently compile or reinterpret genuine `x-*` attributes as
Citry directives. If both runtimes can operate in one subtree, each attribute
has exactly one owner. The syntax spike must prove that `$c-*` survives the
V3 parser, Python rendering, browser parsing, cloning, mutation observation,
contextual HTML, and morphing before this namespace is recommended.

This can make component isolation and rootless lifetime independent of Alpine,
but it creates two expression domains. The user must be able to predict which
scope, magics, cleanup rules, and modifier semantics apply. A magic bridge
alone is insufficient if arbitrary Alpine directives in a fill are expected
to use exact Citry ownership.

Falsifier: compatibility requires Citry to reproduce nearly every Alpine
directive immediately, or both engines initialize and mutate the same binding.

### 5.5 Citry fine-grained runtime on a reactive core

Citry owns expression evaluation, fine-grained effects, refs, models, event
modifiers, structural templates, teleports, transitions, morph adoption, and
cleanup. It may use Alpine's reactivity package, `@vue/reactivity`, Preact
Signals core, or another small primitive after measuring it. Alpine becomes
an optional compatibility island rather than a dependency of Citry
components.

Potential gains:

- component and slot scopes come directly from server graph metadata;
- comment ranges and grouped roots are first-class binding targets;
- props and component-boundary events become normal graph edges;
- a Citry-owned `if` or `for` can instantiate range blueprints with fresh
  identities; and
- the runtime controls morph transactions and cleanup end to end.

The cost is easy to underestimate. Reactivity does not provide Alpine's
expression evaluator, async receiver behavior, assignment rules, CSP story,
events and modifiers, `x-model`, transitions, refs and IDs, mutation adoption,
teleport, plugin API, or browser hardening. The exploration must inventory the
whole responsibility set before comparing bundle sizes.

Falsifier: Alpine feature parity becomes a prerequisite for the first useful
release, turning a focused ownership runtime into an unbounded framework
rewrite.

### 5.6 Compiled binding and hydration instructions

Extend the Citry template compiler and serializer to emit static HTML plus a
compact instruction stream containing scope ownership, binding expressions,
source and target IDs, fragment operations, and optional browser-instantiation
blueprints. The browser adopts existing DOM and installs effects directly on
nodes or ranges.

This avenue could avoid a full-document Alpine scan and make the component
graph primary without a VDOM. It is also the most natural long-term path if
Citry wants first-class client components while keeping server HTML.

Questions:

- Can stable binding locations be represented compactly after Python control
  flow, dynamic components, slots, extension replacement, and morph output?
- Which expressions remain opaque JavaScript strings, and which are compiled?
- How does this cross the Rust parser, generated Python, Python render tree,
  browser protocol, JS/TS asset compiler, and future ESM boundaries?
- Can browser-created fragment blueprints mint complete recursive identities?
- Does the instruction payload become more expensive than runtime discovery?

Falsifier: reliable adoption requires markers on nearly every node or a second
client rendering representation as large as the HTML.

### 5.7 Virtual DOM or incremental reconciliation

The server emits HTML plus enough VNode, template, or render metadata for a
client renderer to hydrate component and fragment boundaries. Client updates
use VDOM or incremental reconciliation rather than only morphing server HTML.

Potential gains:

- persistent fragment identity and keyed child lists;
- explicit component and slot owners;
- natural portals and rootless fragments;
- browser-side component creation; and
- one client reconciliation model if Citry eventually renders components in
  the browser.

However, a VDOM does not itself solve scope isolation. It still needs
component instances, lexical provider chains, scoped-slot render contexts,
portal targets, native event policy, and lifecycle ownership. Citry currently
has server-generated HTML, not a browser render function that naturally
produces the same VNode tree. Parsing arbitrary returned HTML into VNodes adds
bookkeeping without recovering where expressions were authored.

The exploration must separately evaluate a lighter "logical fragment graph"
that keeps the real DOM as the rendered surface. Existing RootGroup and
rootless-range results suggest that this may capture the useful fragment
benefits without virtualizing every node.

Falsifier: most updates remain server HTML and Citry has no product intent to
execute component render functions in the browser. In that case, VDOM cost is
not justified by scope isolation alone.

### 5.8 Alpine fork or upstream logical-ancestry hook

Prototype the smallest general Alpine change that could make 5.2 durable:

- a supported logical scope-parent provider;
- a supported logical root/ref/id parent provider;
- fragment owners and comment-bounded ranges;
- clone metadata transfer hooks; or
- grouped root lifecycle hooks.

An upstream proposal should be general Alpine vocabulary, not Citry component
knowledge. A promising narrow shape is a registered function Alpine consults
when choosing the scope and root parent of a node. The spike must verify
whether that one abstraction really reaches ordinary evaluation, `$refs`,
`$root`, `$id`, `x-ref`, clones, teleports, and cleanup. If it touches most
directives and magics, it is not a narrow hook.

A maintained fork offers compatibility with existing `x-*` markup, but Citry
would inherit Alpine upgrades, plugin compatibility, morph coupling, and
ecosystem divergence. Pinning plus behavioral canaries may be cheaper if the
private surface remains concentrated.

Falsifier: the patch cannot be expressed as a few general scope, root, and
fragment primitives, or ordinary Alpine plugins observe materially different
semantics.

### 5.9 Wrapper custom elements as a control, not a recommendation

Keeping `<c-*>` as custom elements, perhaps with `display: contents`, gives a
convenient physical owner but fails the established constraints: text and
empty output, shared roots, contextual HTML such as tables, accessibility and
event behavior, invisible component-tag semantics, mirrors, and teleports.

Include it as a negative control so any proposed wrapper shortcut must pass
the same shape matrix. Do not retain it merely because it makes one demo easy.

## 6. What a component-first model means for Alpine

### 6.1 `x-data` becomes an extension, not the component boundary

Citry establishes the component's stable base scope from its client registry.
An `x-data` inside the component adds a nearer Alpine provider for its subtree.
It can shadow component-scope names under normal Alpine rules without changing
the logical owner of the Citry instance.

For slot content, the exact authored source location includes any local
`x-data` providers active at that call site. The server cannot serialize their
runtime values. It must serialize a location identity that the client can
associate with the live provider chain after initialization. Source-carrier
replacement must re-elect that chain and invalidate ref/id caches without
reinstalling every initialized descendant stack.

The spike must distinguish:

- server-known component scope ancestry;
- client-discovered local `x-data` ancestry;
- scope values and proxies;
- a source location that can be live, absent, or replaced; and
- physical carriers used only for DOM magics and native events.

### 6.2 Rootless logical scopes are useful but not magic elements

A text-only or empty component can own identity, reactive state, props,
managed effects, polling, queue state, comment-bounded regions, and cleanup.
It has no physical carrier for `x-data`, `x-ref`, `x-id`, `x-on`, `$el`, or
`$dispatch`. A component-first design should state this honestly.

If a later morph adds element roots, the existing logical scope can attach to
them before the chosen directive engine initializes those roots. If roots
disappear, physical handlers stop while logical state may remain alive until
the owning range is retired.

The spike must not fabricate a hidden element solely to make Alpine APIs run.
It should test whether component init and props resolution can occur with no
element and which context members are unavailable or empty.

### 6.3 Mirrored copies need an explicit state split

Mirrors need a state policy as well as a range-lifetime mechanism. The spike
must test, not assume, this candidate split:

| Concern | Candidate ownership to verify |
|---|---|
| Exact source descriptor and source component state | Shared by the logical fill |
| Fill-local `x-data` object | One per physical copy by default, unless the template explicitly lifts the value into logical component scope |
| Fill-local physical listener, transition, and timer | One per physical copy, with copy-local cleanup |
| Component-tag client binding targeting the whole mirrored group | One logical binding with grouped physical carriers and shared modifier state where RootGroup semantics apply |
| `x-ref` and `$id` | Open policy: test collisions, DOM-ID uniqueness, lookup order, and whether a collection API is needed rather than accepting last-write behavior |
| Registry props, exposed component scope, and stable anchor State | Shared by the logical component instance |
| Region cleanup | Copy-local on one mirror's removal; logical cleanup only after the last owning copy and per-render invocation are retired |

Run two live mirrors with colliding refs and IDs, local `x-data`, independent
transitions, simultaneous handlers, removal of one copy, source replacement,
and final cleanup. If a different split is chosen, record it as public
semantics rather than an implementation accident.

### 6.4 Shared physical roots need explicit precedence

The registry can represent several component instances on one physical
element. Stock Alpine exposes one effective data stack to an ordinary
directive on that element. The accepted proposed rule in `events.md` makes the
innermost client-active instance the direct expression surface; outer wrappers
remain addressable by explicit source or target records. The landed runtime
currently has only its narrower Events-oriented marker behavior, not the
general-registry rule.

The exploration must decide whether that remains the public rule. Supporting
arbitrary per-directive selection among several component scopes on one node
would require owner metadata on each directive plus a custom evaluator,
directive override, or Alpine change.

### 6.5 `x-if` and `x-for` remain distinct questions

Stock Alpine clones only the first element child of `x-if` and `x-for` source
templates. The component-first exploration does not need to solve transparent
multi-root native Alpine loops.

It must still cover two narrower interactions:

1. A Citry fill or binding directly under native `x-if` or `x-for` needs its
   ownership metadata and iteration scope propagated to the generated root.
2. Cloning a complete server-rendered Citry component needs a browser
   blueprint protocol that mints a fresh anchor, render identity, region
   tokens, scope, client bindings, nested identities, and cleanup. Rewriting
   `data-cid-*` attributes is not sufficient.

A Citry-owned future `c-if` or `c-for` could be fragment-aware without
forking Alpine. That is an avenue to evaluate, not a requirement to design the
entire feature in this spike.

### 6.6 Teleport has lexical and native halves

A teleported fill can retain its Citry lexical source record regardless of
destination. Its native events bubble at the destination and do not cross the
component roots it left. These are compatible facts.

The default no-synthetic-redispatch rule remains. If product semantics require
outer or component-tag handlers to observe teleported descendant events, that
is a logical event propagation feature. It needs separate naming, ordering,
modifier, cancellation, and duplication rules. It must not claim native DOM
equivalence.

Nested teleports must retain the complete logical source chain. A single
backlink that overwrites Alpine's own teleport ancestry is invalid.

### 6.7 Existing Alpine plugins and syntax need a migration story

For each avenue, state whether these are:

- fully native Alpine behavior;
- adapted to a Citry lexical source;
- available only inside Alpine islands;
- replaced by a Citry directive; or
- unsupported.

The inventory must include `x-data`, `x-init`, `x-effect`, `x-show`, `x-text`,
`x-html`, `x-bind`, `x-model`, `x-modelable`, `x-ref`, `x-id`, `x-if`, `x-for`,
`x-teleport`, `x-transition`, `x-ignore`, event modifiers, official plugins,
custom magics, custom directives, stores, CSP mode, and async expressions.

## 7. Server and wire representation questions

The exploration starts at the unflattened render tree. It must trace where
each required record can be derived and how long that fact survives.

### 7.1 Identities to keep separate

At minimum, distinguish:

- stable client anchor;
- fresh server render/component ID;
- component call or init-dependency ID;
- component class ID;
- logical scope ID and optional scope version;
- exact authored source-location ID;
- logical fill or binding ID;
- physical region ID;
- physical mirror-copy token; and
- diagnostic source span.

The spike should try to eliminate redundant identities, but only after showing
that replacement, mirror, shared-root, teleport, nested fallback, and direct
`x-for` cases remain unambiguous.

### 7.2 Candidate manifest shape

Produce at least one fully worked, safely encoded manifest example. A
referentially complete schematic form is:

```json
{
  "version": 1,
  "instances": [
    {
      "renderId": "c-page-1",
      "callId": "call-page-1",
      "classId": "Page_d4e5f6",
      "renderParentId": null,
      "callParentId": null,
      "initDependencyCallId": null,
      "provideParentRenderId": null,
      "regions": ["region-page-1"]
    },
    {
      "renderId": "c-tooltip-7",
      "callId": "call-tooltip-7",
      "classId": "Tooltip_a1b2c3",
      "renderParentId": "c-page-1",
      "callParentId": "call-page-1",
      "initDependencyCallId": "call-page-1",
      "provideParentRenderId": "c-page-1",
      "regions": ["region-tooltip-7"]
    }
  ],
  "locations": [
    {
      "id": "loc-page-root",
      "ownerRenderId": "c-page-1",
      "lexicalParentLocationId": null,
      "sourceToken": "source-page-root"
    },
    {
      "id": "loc-page-tooltip-call",
      "ownerRenderId": "c-page-1",
      "lexicalParentLocationId": "loc-page-root",
      "sourceToken": "source-page-tooltip-call"
    }
  ],
  "fills": [
    {
      "id": "fill-9",
      "sourceLocationId": "loc-page-tooltip-call",
      "receiverRenderId": "c-tooltip-7",
      "regions": ["region-fill-9-copy-1"]
    }
  ],
  "regions": [
    {
      "id": "region-page-1",
      "logicalOwner": {"kind": "instance", "id": "c-page-1"},
      "kind": "elements",
      "rootTokens": ["root-page-1"]
    },
    {
      "id": "region-tooltip-7",
      "logicalOwner": {"kind": "instance", "id": "c-tooltip-7"},
      "kind": "elements",
      "rootTokens": ["root-tooltip-7"]
    },
    {
      "id": "region-fill-9-copy-1",
      "logicalOwner": {"kind": "fill", "id": "fill-9"},
      "kind": "range",
      "start": "cap-fill-9-1-start",
      "end": "cap-fill-9-1-end"
    }
  ],
  "bindings": [
    {
      "id": "binding-save",
      "sourceLocationId": "loc-page-tooltip-call",
      "targetRenderId": "c-tooltip-7",
      "targetRegionId": "region-tooltip-7",
      "family": "alpine-event",
      "expression": "save()"
    }
  ]
}
```

Every reference in this example resolves inside the payload. No stable client
anchor or client scope handle appears on the wire. During adoption, the
browser maps the fresh render IDs to existing or new anchors according to the
separate identity and morph rules.

The server-side location record identifies where the client must capture or
re-elect any local `x-data` provider chain. It does not claim to serialize
those runtime values or a client-created local-scope ID. This is not a
recommendation to send every record separately or use these names. The final
representation may intern strings, derive regions from caps, or combine
records. The worked form exists to expose ambiguity before compression.

### 7.3 Emission policy

Answer all of these:

1. Which components force a registry record: component JS, props declaration,
   supplied props, boundary handler, Events, scoped fill, or any combination?
2. Which fills need explicit caps: every fill, only client-active fills, only
   rootless or shape-changing fills, or a server-predicted subset?
3. How are inverse ownership transitions encoded without decorating a nested
   component's roots as ordinary outer fill HTML?
4. How are trusted Python HTML, callable fills, reusable Slot objects,
   `{{ slot }}`, `CitryElement`, `CitryRender`, dynamic `<c-component>`, and
   extension replacement represented?
5. Can the representation stay in Python's serializer, or must the generic
   Rust HTML marker contract change?
6. How do minifiers, sanitizers, caches, fragment extraction, and comment
   stripping affect load-bearing markers?
7. Can a fragment's ownership records arrive before, with, or after its HTML,
   and how is early adoption guaranteed?
8. What happens during a rolling deploy when cached HTML, the client runtime,
   and a late fragment carry different supported schema versions?
9. Is the whole payload referentially validated before adoption, including
   dangling and cross-fragment references, duplicate IDs, invalid ownership
   cycles, and collisions with live records?
10. What byte, record-count, nesting-depth, and range-count limits reject a
    malicious or accidentally explosive graph before allocation?

Version handling must be explicit. Test an unknown major version, an older
cached document with a newer runtime, a newer fragment reaching an older
runtime, a partially delivered manifest, and a fragment whose references
depend on records that were retired or never arrived. Adoption must be atomic:
either the validated record set becomes visible as one transaction, or none
of it can route evaluation, events, or cleanup.

### 7.4 ESM and asset compiler neutrality

The registry must consume structured registrations and capability records. It
must not discover ownership by scanning source code, rewriting arbitrary
identifiers, or wrapping the user's whole source file.

Compare all candidate designs under:

- current classic script registration;
- compiled TS, TSX, and JSX that lower to classic JS;
- future `type="module"` execution and top-level imports;
- late dynamic import;
- async class registration;
- duplicate or failed module load; and
- fragment manifests that arrive before class code.

This exploration does not choose the ESM product design. It must avoid making
that future harder.

## 8. Morph and lifecycle transaction

Every candidate must specify one transaction for initial document adoption,
late fragment insertion, server rerender, and removal. A useful reference
order is:

1. parse incoming HTML contextually;
2. parse and atomically validate the versioned ownership record graph;
3. correlate incoming fresh render IDs with stable client anchors;
4. suspend directive initialization and event delivery for the affected
   transaction, then stage incoming instances, source locations, regions, and
   client bindings without exposing half-adopted records;
5. mark bindings being replaced as disabled for the held transaction while
   retaining the old committed graph for rollback;
6. morph or install physical DOM under that initialization hold;
7. update stable `els` and range membership, re-elect every live source
   carrier against the final physical DOM, install lexical links, and
   invalidate source-dependent ref and ID caches;
8. after the final graph validates, run the old per-render `$component`
   effects and cleanup once and retire the replaced listener/effect records;
9. atomically commit the staged graph;
10. initialize newly admitted directives and component callbacks in ancestry
   order, now that their lexical ownership is usable;
11. re-evaluate props and activate the new client bindings;
12. retire stale physical regions and copy-local resources that were not
    retained by the committed morph; and
13. clean a stable logical instance exactly once when its final owning region,
    in-flight continuity record, and per-render invocation are all retired.

This is an ordering contract for the spike, not a claim that Alpine already
offers one switch that suspends all initialization. Each candidate must show
how it enforces the hold. New directives must never observe the old lexical
source, and old and replacement listener/effect sets must never both be live.

The spike must verify rollback or pointed terminal behavior for malformed
metadata, missing caps, removed sources, init failure, class-load failure, and
exceptions during morph hooks. It must not leave half-adopted records that
route later events to retired scopes.

Morph comparison must include:

- same element and same key;
- key-preserving reorder;
- tag or node-type replacement;
- element to text to empty transitions;
- root-count changes;
- source root replacement;
- one mirror removed while another survives;
- shared-root inner component replacement;
- nested comment islands;
- contextual table, select, and SVG parsing;
- native DOM move in one mutation batch; and
- remove and reinsert in a later task.

## 9. Event, props, refs, and queue integration

### 9.1 Props

Test first supply, reactive updates, missing and unknown keys, invalid values,
source replacement, target replacement, multi-root carrier re-election,
rootless target init, dynamic `<c-component>`, shared physical roots, and
managed-effect cleanup.

The architecture must retain one supplier effect per logical target, not one
per physical root. The first live carrier may host an Alpine effect, but the
props bag and its lifetime belong to the instance registry.

### 9.2 Boundary handlers

Run Alpine handler expressions and Citry argument expressions through the same
isolation matrix. For the Citry path, use a real parsed server-handler binding
and assert that the handler name is dispatched unchanged. Assert colliding and
one-sided parent/child values for ordinary data, `$data`, `$refs`, `$root`,
`$id`, and Citry magics. Separately assert physical `$el`, `$dispatch`,
`$event`, target, and `currentTarget`.

Grouped listeners must retain RootGroup's union containment, modifier order,
shared `.once`, debounce, throttle, `.window`, `.document`, `.outside`, and
cleanup semantics. Do not install an independent listener state machine on
every root.

### 9.3 Refs and IDs

Refs and IDs are a major discriminator between candidates because they reveal
whether the implementation truly moved lexical ownership or only copied data
values. Test:

- inline `x-ref` before local `x-data`;
- source and child name collisions;
- ref replacement and source root replacement;
- multi-root sources where the authored location is not the first root;
- nested and repeated IDs;
- teleport and nested teleport;
- direct `x-if` and `x-for` template roots;
- source cache invalidation; and
- no fallback to child refs when a parent ref is absent.

### 9.4 Queue and Citry magics

Keep these as separate fields through enqueue and dequeue:

- source Events anchor;
- physical triggering element or RootGroup member;
- target component anchor;
- live physical overlap set; and
- source scope location.

At dequeue, reverify liveness and overlap against current regions. A moved or
morphed root must not retain stale overlap. `$loading` and busy markers must
reflect the logical call and its physical trigger according to the accepted
Events rules.

Test all Citry magics inside ordinary component content, source-linked fills,
nested fallback, shared roots, mirrors, teleports, and rootless logical init.
Also decide and test `Citry.events.send(element)` when physical nearest
component and lexical source differ.

## 10. Spike program

This should be a staged exploration with retained evidence, not a single demo.

### Stage 0: current-state trace

Produce a trace for each representative template showing:

- Python writer context;
- receiving component and slot invocation;
- `CitryRender` structure before serialization;
- final HTML and existing markers;
- current client records;
- Alpine data and root stacks;
- expected lexical owner;
- physical roots or ranges; and
- lifecycle across one morph.

Use at least these examples: single-root component, multi-root component,
empty component, shared root, ordinary fill, nested fallback inside fill,
component inside fill, reusable Slot rendered twice, mirror, dynamic
component, teleport, and direct native `x-for` call site.

### Stage 1: paper models and payloads

For each architecture avenue:

1. draw the instance, lexical, and physical relations for the examples;
2. produce concrete initial and fragment manifest payloads;
3. specify initialization and cleanup order;
4. state which Alpine APIs and private fields it uses;
5. estimate payload and retained-runtime costs; and
6. record product syntax or migration changes.

Reject an avenue on paper only when a hard invariant is impossible, not merely
because it is unfamiliar.

### Stage 2: two or more competing browser prototypes

Prototype at least:

1. Citry graph first with pinned stock Alpine as the DOM binding engine; and
2. the strongest credible alternative, likely either a Citry evaluator with
   Alpine islands or a compiled fine-grained binding prototype.

Also run the narrow public-hook or upstream-hook falsifier. If one general
logical-parent hook fixes the important Alpine private dependencies, retain a
small patch and document it. If it does not, show the patch spread.

The prototypes must consume the same hand-authored runtime-neutral manifest
and scenario fixtures. Do not let each prototype receive a tailor-made easier
input.

Stage 2 ends with an explicit architecture checkpoint. Compare the prototypes
against the hard invariants, private-API surface, compatibility inventory, and
measured costs. Select one design for the real-server vertical slice. If the
evidence is tied, run one bounded discriminating experiment; do not build two
complete server integrations merely to postpone the decision.

### Stage 3: real server vertical slice

Take the selected design through:

```text
Citry template
  -> compiled Python nodes
  -> render objects with writer/receiver ownership
  -> real serializer and fragment manifest
  -> client registry adoption
  -> expression and magic evaluation
  -> props and boundary handlers
  -> queue enqueue/dequeue
  -> product morph
  -> exact teardown
```

This stage, not the isolated browser prototype, clears the scoped-fill product
gate.

### Stage 4: integration report and final recommendation

The final report must contain:

- verified claims with reproduction commands;
- failed controls and negative findings;
- a requirements and edge-case matrix;
- private API and fork surface by file and symbol;
- payload, startup, update, and cleanup measurements;
- migration impact on the audited production application;
- recommended near-term and long-term architecture;
- representation changes to `events.md`, `component_slots.md`, and `alpinejs.md`;
- explicit product decisions still required; and
- a bounded implementation plan only after the architecture choice.

## 11. Acceptance matrix

Every serious candidate must report pass, fail, unsupported-by-design, or not
tested for each row. No blank cells.

### 11.1 Shapes and ownership

- single element root;
- several element roots with one shared scope;
- text-only component;
- empty component;
- rooted to rootless and rootless to rooted;
- wrapper-only component;
- several components sharing one physical root;
- nested isolated components;
- ordinary and implicit fill;
- child fallback;
- fallback nested inside parent fill;
- component inside fill;
- nested passthrough;
- multiple named fills;
- reusable Slot at two call sites;
- mirrored outlet with shared source state and copy-local `x-data`;
- two mirrors with colliding refs, IDs, handlers, and transitions;
- removal of one mirror while the logical fill survives;
- typed default;
- trusted Python HTML and callable fill;
- `{{ slot }}`, `CitryElement`, and `CitryRender`;
- static and dynamic `<c-component>`; and
- extension replacement.

### 11.2 Alpine and directive behavior

- component base scope without user `x-data`;
- local and nested `x-data`;
- ordinary reads, writes, shadowing, and assignment;
- `$data`, `$refs`, `$root`, `$id`, `$el`, `$dispatch`, and `$event`;
- `x-ref` initialization and replacement;
- `x-id` stability and repeated names;
- `x-show`, `x-text`, `x-html`, `x-bind`, and `x-model`;
- transition start, cancellation, and removal;
- custom magic, directive, store, and official plugin;
- async expression and thrown expression;
- strict CSP mode;
- direct `x-if` and `x-for` template root;
- iteration variable refresh;
- nested and repeated teleport;
- open shadow root; and
- closed shadow root failure behavior.

### 11.3 Props and events

- first supply and reactive update;
- dynamic client binding key add, replace, remove, and reorder;
- unknown, missing, invalid, and recovering prop;
- multi-root supplier carrier replacement;
- rootless init and later roots;
- Alpine and Citry component-tag handlers;
- child-local handler control;
- callback passed explicitly through props;
- `.window`, `.document`, `.outside`, `.away`, `.once`, debounce, and
  throttle across RootGroup;
- physical event values and delayed `currentTarget`;
- native capture and bubble order;
- teleported event path;
- programmatic Citry send; and
- busy, loading, error, and cancellation state.

### 11.4 Identity, morph, and cleanup

- initial document and head-loaded manifest;
- late fragment before and after component class registration;
- same-node morph;
- wholesale tag and key replacement;
- keyed reordering;
- source replacement and target replacement;
- root-count change;
- mirror added and removed;
- nested range island;
- contextual table, select, and SVG output;
- move in one mutation batch;
- remove and reinsert later;
- pending timer, debounce, poll, and request at removal;
- malformed ownership record;
- unknown, older, and newer manifest schema versions;
- old cached document with a newer runtime and the inverse;
- dangling, cross-fragment, cyclic, and duplicate record references;
- payload byte, record-count, nesting-depth, and range-count limits;
- partially delivered or atomically rejected manifest;
- missing or stripped range comment;
- duplicate registration and second Alpine copy;
- client clone with fresh blueprint identity; and
- exact once-only logical cleanup.

### 11.5 Delivery and language modes

- current classic script;
- minified bundle;
- TypeScript compiler output;
- JSX and TSX compiler output;
- future ESM with top-level imports;
- async dynamic import;
- fragment loaded before module;
- failed module load; and
- source maps and pointed diagnostics.

## 12. Measurements and decision criteria

Measure rather than infer:

- added server metadata bytes before and after compression;
- DOM marker and comment count;
- initial adoption time at representative component counts;
- number of Alpine or Citry effects and mutation observers;
- cost of a prop update;
- cost of a same-root and root-count-changing morph;
- retained registry records after removal;
- bundle size by architecture and optional compatibility layer;
- number of private Alpine symbols and source files depended upon;
- Alpine upgrade diff and canary count;
- code needed to implement one simple and one complex directive; and
- migration changes in the audited work project.

Judge the avenues in this order:

1. ownership and isolation correctness;
2. lifecycle and morph correctness;
3. predictable user model and compatibility;
4. maintenance and upgrade surface;
5. server/client protocol clarity;
6. performance and payload;
7. ESM, CSP, compiler, and ecosystem compatibility;
8. devtools, diagnostics, and testability; and
9. implementation size.

A smaller prototype that fails source replacement is not simpler. A larger
architecture that solves no likely product need is not automatically more
future-proof.

## 13. Strong fork or replacement triggers

Pinned stock Alpine remains a credible near-term engine. A fork, upstream
change, or greater Citry ownership becomes justified if one or more of these
are real product requirements or repeated maintenance failures:

1. one supported logical-parent hook must govern data lookup, root lookup,
   refs, IDs, clones, teleports, and cleanup;
2. native fragment-aware multi-root `x-if` and `x-for` are required;
3. normal directives must attach directly to comment-bounded logical regions;
4. several selectable component scopes must coexist on one physical element;
5. logical event propagation across teleports must behave like a first-class
   directive feature;
6. private Alpine field drift becomes costly despite exact pins and canaries;
7. transparent lazy or chunked initialization needs lifecycle controls Alpine
   does not expose;
8. full CSP behavior must support the same expression surface; or
9. Citry requires browser-side component creation and reconciliation as a
   primary rendering mode.

These are triggers to investigate, not a pre-commitment to fork.

## 14. Non-goals

This exploration does not:

- implement production runtime changes;
- choose the final ESM design;
- require replacing server rendering;
- promise transparent multi-root stock Alpine `x-if` or `x-for`;
- solve browser component blueprints in full;
- add synthetic native event propagation across teleports;
- select a reactive library by bundle size alone;
- reopen accepted client-props and handler semantics without explicit
  evidence; or
- assume a VDOM is inherently more isolated than a real-DOM region graph.

## 15. Falsifiers for the exploration itself

The research is incomplete if any of these occurs:

1. It compares implementation libraries without first modeling instance,
   lexical, physical, and native event relations.
2. It treats a copied Alpine data stack as proof for `$refs`, `$root`, `$id`,
   source replacement, or nested ownership.
3. It demonstrates only a single element root.
4. It calls a wrapper or cloned `data-cid-*` values a solution to rootless or
   browser-created instances.
5. It claims VDOM solves slot scope without showing the lexical owner model.
6. It compares a full Alpine bundle against only a reactive primitive and
   ignores the DOM responsibility gap.
7. It tests each architecture against a different, easier manifest.
8. It relies on mutation-observer order instead of proving adoption before
   initialization.
9. It omits negative controls where physical nearest component and lexical
   source deliberately disagree.
10. It reports isolated browser success as proof of server serialization,
    morph transactions, or queue integration.
11. It makes current classic-script assumptions load-bearing for compiled TS
    or future ESM.
12. It recommends a fork without listing the exact touched Alpine files,
    symbols, plugin effects, and upgrade burden.

## 16. Expected decision shape

The likely result is not one irreversible choice for all time. A useful final
decision may be layered:

- a runtime-neutral instance, lexical-location, binding, and physical-region
  model owned by Citry;
- pinned stock Alpine as the near-term directive and reactivity engine;
- a deliberately small compatibility adapter covered by upgrade canaries;
- a public or upstream logical-ancestry hook investigated in parallel;
- a separate Citry directive or compiled-binding path only where evidence
  shows Alpine's physical model is a continuing liability; and
- VDOM or browser rendering deferred unless client-side reconciliation becomes
  a product goal in its own right.

That is a hypothesis for the spike to challenge. The final report must be
equally willing to show that the existing Alpine-first adapter remains the
simplest correct model, or that taking over a larger client responsibility set
is justified.

No runtime implementation is authorized by this brief.
