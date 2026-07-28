# Boundary handler scope spike: isolation at the source location

An empirical preimplementation spike for WP23, run on 2026-07-19 against the
repo's pinned Alpine 3.15.12 and morph 3.15.12 in headless Chromium, Firefox,
and WebKit. It resolves F23: when a parent-authored Alpine or Citry handler is
relocated from a child component tag onto the child's physical roots, which
parts of an Alpine handler or Citry argument expression follow the exact parent
source and which parts follow the real event carrier.

**Contract correction (2026-07-21):** the Citry profile in this spike passed an
arbitrary expression through the source evaluator as a stand-in. A real
`@c-*` value is a declared server-handler name with an optional parenthesized
Alpine expression for its argument object. The spike therefore proves source
scope, physical event values, liveness, and cleanup for that optional argument
expression. It does not prove handler-call parsing, source Events validation,
dispatch, or queue integration. Those require a real compiled binding in the
product acceptance pass.

This report calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

**Verdict: whole Alpine handlers and optional Citry argument expressions use
the exact parent source scope.** Ordinary data, `$data`, `$root`, `$id`,
`$refs`, and the other lexical magics come from the location where the
component tag was authored. They do not come from the child root, the source
component's first root, or a union over every source root. Only `$el`,
`$dispatch`, and `$event` are supplied from the physical child. Native
`event.currentTarget` is left untouched, so it follows DOM listener mode and
timing. A handler authored inside the child's own template remains child-local.

All semantic assertions passed in Chromium, Firefox, and WebKit, three full
passes per engine, with no page errors or console output. The spike clears
F23's isolation gate. It leaves the named client-target helper as the separate
remaining direct-`x-for` gate and does not implement the component-tag client
binding in the product runtime.

## Artifacts and rerun

- [`refs_client_binding_adapter.js`](refs_client_binding_adapter.js) is the isolated
  source-anchor and evaluator prototype. It composes the preceding
  [`RootGroup`](root_group_adapter.js) research adapter and is not bundled into
  Citry.
- [`refs_client_binding_scenarios.js`](refs_client_binding_scenarios.js) contains the browser
  scenarios.
- [`refs_client_binding_harness.py`](refs_client_binding_harness.py) loads local pinned Alpine
  and morph bytes, runs three deterministic passes in all three Playwright
  engines, and asserts the evidence.

The ordinary repo environment intentionally omits Playwright. The recorded run
used the already-cached lock-matching package without changing that
environment:

```console
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/refs_client_binding_harness.py
```

| Piece | Pin |
|---|---|
| Alpine | 3.15.12 |
| `@alpinejs/morph` | 3.15.12 |
| Playwright | 1.61.0 |
| Chromium | 149.0.7827.55 |
| Firefox | 151.0 |
| WebKit | 26.5 |

Every contract assertion was stable across all nine passes.

## Why the child evaluator is wrong for both boundary expression paths

Pinned Alpine's `x-ref` directive stores each ref in the `_x_refs` object on
the nearest Alpine root. Citry registers every `[data-cid]` element as an
Alpine root, so a child component normally has its own ref map. The `$refs`
magic starts at its evaluation element, walks outward through Alpine roots,
and merges those maps nearest first. It caches the resulting proxy on the
evaluation element.

That behavior makes a child-root evaluator observably different from the
parent source location. The same problem exists for ordinary Alpine data:
evaluator extras have priority, but Alpine still retains the child's captured
data stack as fallback. Overlaying a few parent values therefore leaks any
missing name from child `x-data`.

- if parent and child both declare `x-ref="same"`, the child root resolves the
  child's element;
- if only the child declares `x-ref="childOnly"`, the child root exposes that
  name even though it did not exist in the handler's authored scope;
- if only the parent declares `x-ref="parentOnly"`, the child root falls back
  to it, which can make an incomplete test look correct.
- if parent and child both define `owner`, the child wins unless the evaluator
  starts at the source;
- if only the child defines `childOnly`, a partial parent facade does not hide
  it.

The single-root falsifier used collisions and one-sided names in both data and
refs. A handler authored locally on the child returned child `owner`, `$data`,
`$root`, `$id`, and refs, then incremented child state. The relocated Alpine
handler and the Citry stand-in argument expression both returned the parent
values, could not see child-only data or refs, shared the source `$id`, and
incremented parent state. Each also read and incremented the same reactive
source facade despite colliding child facade names. All three kept `$el`, the
exact `$event`, and immediate `event.currentTarget` on the child, and
`$dispatch` originated at that child. This locks evaluator isolation rather
than inferring it from a parent-only happy path.

## Mechanism proved

### Source evaluation with physical-event overrides

Pinned Alpine constructs evaluator scope from the chosen evaluation element,
then gives call-time `extras.scope` first priority. The prototype evaluates on
the exact source carrier and overrides only physical event values:

```js
const physicalEventScope = {
  $dispatch: Alpine.dontAutoEvaluateFunctions(
    () => Alpine.evaluateRaw(triggeringChildRoot, "$dispatch"),
  ),
  $el: triggeringChildRoot,
  $event: event,
};

const evaluationScope = bridgeOwnAccessors(
  physicalEventScope,
  sourceCitryFacade,
);

Alpine.evaluateRaw(sourceCarrier, expression, {
  scope: evaluationScope,
});
```

Because the child data stack never enters expression evaluation, absent parent
names cannot fall through to child state. Source assignments retain Alpine's
write-through behavior. Source `$data`, `$root`, `$id`, and `$refs` arise
naturally from the evaluation carrier rather than from a copied snapshot. The
explicit source Citry facade remains reactive and write-through because the
prototype gives every facade key an own accessor that delegates reads and
writes to the original facade. This bridge is necessary: Alpine nests
`extras.scope` inside another merge proxy, whose ownership test does not treat
the inner merge proxy's virtual keys as own properties. Passing
`Alpine.mergeProxies([physicalEventScope, sourceCitryFacade])` directly keeps
reads but misroutes assignments to facade-only keys.

`$dispatch` needs an explicit physical function because Alpine binds that
magic to its evaluation element. `dontAutoEvaluateFunctions` prevents the raw
evaluator from immediately calling the function while it is captured. The
prototype does not forge `currentTarget`; its immediate listener value is the
actual root, and its delayed value becomes `null` as the DOM requires.

For an Alpine boundary handler, `Alpine.bind` may install a client binding callback and
retain its modifier semantics, but Citry must not give it the authored
expression directly. Doing so would make Alpine capture the child evaluator.
The Citry `@c-*` listener profile uses the same source evaluator only for its
optional argument expression after its own modifier machinery admits the
event. Its handler name remains a server binding identifier.

### Exact source location, not instance union

The grouped-source falsifier created physical roots A and B for one logical
source identity, with colliding refs, then authored the client binding under B. Root A
was deliberately first in the logical source's live `els`. Both child target
roots saw B's values; neither saw A-only values. Triggering target A or target
B changed `$el` and `currentTarget`, but not source scope. Removing target A
and adding target C kept the same source view.

This is the meaning of parent lexical: evaluate as if the vanished component
tag still occupied its exact authored location. Selecting
`sourceInstance.els[0]` would be wrong whenever the tag was authored under a
different source root. Building a synthetic union over source roots would
also invent semantics Alpine does not have.

### Shared physical targets remain separable

One physical target root can carry several logical Citry identities. Its
native data and refs cannot distinguish the source of each client binding. The spike
attached two logical client bindings to the same root with distinct source anchors. One
resolved source one, the other source two, and neither leaked target-only
values.

This proves that the client binding must not cache an expression evaluator or refs view
by physical target root. It does not require a second Citry-owned ref namespace.
Alpine's own data stacks and ref maps remain sufficient when the client binding retains
the correct source-location carrier.

### Delivery-time freshness and liveness

The source scope must be resolved when the handler is delivered, not when the
client binding is registered or when a debounce timer starts. The passing probes
covered:

- morph replacement of the source ref with a different tag;
- removal and re-addition of the `x-ref` attribute;
- replacement of the entire source Alpine root followed by source-carrier
  re-election;
- replacement of a ref while a child event was waiting in debounce;
- source removal while the child and its pending timer remained live;
- target removal while the source and pending timer remained live;
- idempotent client binding teardown with pending work.

The delayed handler saw the newly inserted ref rather than the element that
existed at trigger time. Logical source retirement dropped delivery even while
its physical carrier remained connected, which covers shared-root retirement.
Target death was dropped by the already-proved `RootGroup` liveness check.
Replacing the source root required replacing the source carrier, which
constructed a new native Alpine refs proxy rather than retaining the dead
element's cached proxy.

### Teleport agrees with the decision

Alpine's own relocation primitive is a useful oracle. `x-teleport` stores an
origin link on the physical clone, and Alpine's closest-root walk follows that
link before the destination ancestry. With conflicting origin and destination
refs, both a real teleported target and the boundary-scope prototype resolved
`origin-same`, while direct evaluation at the destination resolved
`destination-same`.

This supports the logical-source choice and adds an integration requirement:
the source-location resolver must preserve Alpine's teleport origin. A plain
`triggerRoot.parentElement` rule is insufficient for teleported carriers.

## Native Alpine limits that Citry keeps

The client binding changes ownership, not Alpine's ref model.

- `x-if` removal clears its ref, and recreation publishes the new element.
- Repeated same-name refs under `x-for` are not an array. The last initialized
  clone wins. Cleanup of another same-name clone can delete the shared key even
  while one clone remains. The canary reproduced that pinned behavior through
  keyed reorder, removal, and fresh creation.
- A `$refs` proxy sees mutation within the root maps it captured, but it does
  not discover a completely different source-root chain. Source-carrier
  replacement must therefore rebuild the view.
- An explicitly initialized open shadow root can participate because Alpine's
  closest-root walk crosses its host. Citry's normal document observer does
  not initialize or destroy shadow contents itself. Closed-shadow ownership
  and cleanup remain unsupported unless a future feature owns that lifecycle.
- A DOM boundary handler still needs a real target `EventTarget`. A rootless
  target receives the pointed no-element-root error settled by the rootless
  spike. Rootless logical polling remains a different mechanism.

Citry must not convert duplicate refs to arrays, repair Alpine's cross-root
move behavior as part of this client binding, or claim automatic shadow lifecycle.

## Product integration contract

Stage two should implement the following split:

1. Each parent-owned Alpine component-target handler and each Citry binding
   with an argument expression retains a live Alpine evaluation carrier for
   its exact source location. A Citry `@c-*` client binding additionally retains its
   parsed server-handler name, the exact source Events anchor, and Citry
   facade.
2. Each physical target uses the proved `RootGroup` delivery carrier. A
   grouped handler has one logical lifetime and one source anchor even though
   `$el` changes by trigger root.
3. Immediately before evaluating an Alpine handler or Citry argument
   expression, recheck both logical source and physical target liveness, then
   evaluate against the current source carrier.
4. Supply `$el`, the child-bound `$dispatch`, and the exact `$event` through
   evaluator extras. Leave native `event.currentTarget` untouched. Every other
   ordinary name and Alpine magic resolves from the source carrier. Do not
   choose the child evaluator, `sourceInstance.els[0]`, or a component-wide
   source union.
5. Bridge each explicit source-facade key through an own getter/setter in
   evaluator extras. Do not nest an Alpine merge-proxy facade directly, because
   that preserves reads but misroutes assignments to facade-only names.
6. Re-elect or replace the source carrier when morph replaces its Alpine root.
   Do not retain an evaluator or refs proxy from a detached source.
7. Preserve teleport origin when selecting the source location. Ordinary
   component roots commonly make their shared physical parent a sufficient
   location, but that is an integration optimization, not the semantic
   identity.
8. Client binding replacement, source retirement, target retirement, and logical
   teardown cancel pending work and cleanup exactly once.
9. A handler authored inside the child template is not a client binding. It
   keeps ordinary child evaluation. A parent grants an intentional child
   capability by passing a callback through declared props, exposing that
   callback through the child's stable `scope`, and calling it from a
   child-local handler.

The spike does not prove how the manifest serializes that location. A
`sourceId` alone is insufficient for a multi-root source, and a child root's
physical parent alone is insufficient under teleport. Stage-two acceptance
must therefore include the source-location election path, including dynamic
`<c-component>` replacement and real morph adoption. If existing DOM topology
cannot retain the exact location reliably, a Citry-owned opaque location mark
is the correct fallback; falling back to the first source root is not.

## Evidence matrix

| Area | Passing probe |
|---|---|
| Child-local baseline | A real Alpine handler authored on the child used child data, `$data`, `$root`, `$id`, and child-first refs, then mutated child state only. |
| Both boundary profiles | The relocated Alpine handler and Citry stand-in argument expression used the same exact parent source scope, mutated parent state only, and read then wrote through an Alpine merge-proxy Citry facade. Handler parsing and server dispatch were not modeled. |
| Single collision | Parent data and ref duplicates won, parent-only names remained visible, and child-only data and refs stayed absent. |
| Physical event split | `$el`, `$dispatch`, and the exact `$event` came from the physical child. Native `currentTarget` was untouched: the immediate direct-listener case reported the child root, while delayed delivery reported `null`. |
| Grouped target | Two target roots shared one source scope while retaining per-root event values; removal and addition did not change ownership. |
| Exact source root | Handler authored under source root B saw B, not source root A or an instance-wide union. |
| Shared physical root | Two logical client bindings on one root retained distinct source scopes and hid target-only values. |
| Dynamic source | Morph replacement, ref removal/re-addition, and source-root replacement returned current source values. |
| Delayed work | Source replacement during debounce was visible; logical source retirement with a connected carrier and target death each suppressed delivery. |
| Teleport | Origin refs beat conflicting destination refs, matching Alpine's native relocation behavior. |
| Alpine canaries | `x-if` and duplicate-name keyed `x-for` kept Alpine's observable behavior, with no invented array. |
| Shadow | Explicitly initialized open-shadow refs crossed the host; automatic shadow lifecycle was not claimed. |
| Rootless | Both DOM-event boundary profiles failed with the pointed no-EventTarget error on a settled no-Element target. Logical `@c-poll` was outside this spike. |
| Cleanup | Repeated client binding destruction was idempotent and canceled pending work. |

## Decision

F23's evaluator-scope question is DONE and positive. A parent-authored Alpine
handler and a parent-authored Citry binding's optional argument expression use
the exact source location's complete lexical scope. Only `$el`, `$dispatch`,
and `$event` come from the physical child carrier. Native
`event.currentTarget` remains untouched and therefore follows DOM listener
mode and timing. A handler authored inside the child template remains
child-local. This split is the isolation boundary. Real Citry handler parsing,
validation, dispatch, and queue ownership remain product integration work.

This is the last focused mechanism spike blocking the core WP23 client binding build.
It is not the last open WP23 product edge. The named client-target helper still
gates the public direct-`x-for` claim, and browser blueprint instantiation
remains separate later work.
