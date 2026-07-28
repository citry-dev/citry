# A9 client instantiation decision

**Status:** structural hardening selected; browser component instantiation
deferred to a separate maintainer decision.

This record closes O10 for A9. Native Alpine structural directives may clone
ordinary DOM that is already inside a valid Citry component or supplied fill.
They may not clone the rendered output of a client-active server component.

## Why marker rewriting is not instantiation

Stock Alpine `x-for` creates only the template's first element child, gives
that clone an iteration scope, and reuses it by key. It does not copy a
multi-root range or mint Citry records. Rewriting `data-cid-*` would therefore
create a second DOM spelling of one server identity, not a new component.

A **component-tag client binding** is a browser-side `$c-props`, `@click`, or
`@c-poll.5s` binding resolved from a nested `<c-*>` tag. The parent owns its
expression or handler, while the child supplies the component boundary where
the browser applies it.

A real clone needs fresh values or records for at least:

- activation, render, logical-instance, and browser-anchor identity;
- logical parent, source location, component invocation, and init ancestry;
- exact physical caps, regions, placements, fills, mirrors, and teleport
  backlinks;
- component scope, props controller, callback call, effects, resources, and
  once-only cleanup;
- client bindings and their source and target routes;
- Events anchor, State, token policy, epochs, queue state, subscriptions,
  loading, errors, polls, and busy state when Events is supported;
- instance-specific dependency calls and static class asset reuse;
- literal DOM IDs and ID references, or an authoring rule that prevents them
  from being copied.

Class registration, class assets, and Events class descriptors may be shared.
Mutable instance state, lifecycle, placement, and call records may not.

## A9 behavior

Citry scans native `x-for`, `x-if`, and `x-teleport` template contents before
graph activation and before Alpine descendant initialization. If a template
would clone a server-rendered client-active Citry root, startup or fragment
activation fails with a pointed diagnostic. The diagnostic recommends server
`<c-for>` for server component lists or an ordinary Alpine structural
directive inside an existing Citry component.

This check also recognizes an already-created `x-for` clone through Alpine's
pinned clone marker. Valid `x-citry-fill-source` propagation remains allowed:
the generated root carries lexical source metadata, not copied component
identity.

## Smallest credible future target

The smallest future protocol is an explicit, pre-registered browser-only
component target. It is not a clone of arbitrary rendered Python output. A
first version would need:

1. an immutable public target name mapped to a preloaded Component.js class,
   props declaration, and data factory;
2. an explicit DOM marker that distinguishes it from ordinary `x-data`;
3. a fresh activation ID, render ID, browser anchor, and logical instance;
4. an enclosing logical-parent edge and a lexical source frame containing the
   current `x-for` iteration layer;
5. a client-owned physical range, RootGroup, removal observer, lifecycle,
   props controller, callback call, and cleanup;
6. keyed reuse that retains identity and refreshes the iteration layer;
7. strict exclusion or a full protocol for server Events, nested server
   components, fills, mirrors, rootless output, and multi-root output.

The current runtime has no atomic constructor for these records. Adding one is
a product and protocol decision, not an A9 implementation detail.

## Security and server policy

An ownership revision hash proves internal consistency, not authentication.
A future blueprint format needs a strict schema, count, depth, and byte
limits, immutable allowlisted registrations, collision rejection, and replay
tombstones. An Alpine expression must never supply executable asset URLs or
dependency descriptors.

Events State tokens are currently class-bound. Reusing one blueprint token
for several clones would create several client branches from the same initial
state. A future protocol must decide whether tokens can be forked, whether the
server mints one per clone, how server storage participates, and whether a
retired activation ID can ever be replayed.

## Reconsideration criteria

Reopen this decision only when all of the following have concrete answers:

- approved target syntax and capability set;
- an atomic client-instance constructor for registry, source, lifecycle,
  physical, dependency, and cleanup records;
- a server contract for client-minted IDs and State-token behavior;
- retained browser proof for keyed reuse, nested targets, self-render,
  removal, cleanup, and replay;
- a product need strong enough to justify the protocol and compatibility
  cost.

Until then, pointed rejection is the supported behavior.
