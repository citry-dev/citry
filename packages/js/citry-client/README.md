# citry-client

Source of citry's events client runtime, `citry-events.js`: the pinned
AlpineJS + `@alpinejs/morph` bundle, the component scopes, the magics
(`$state`, `$loading`, `$error`, `$sendEvent`, `$onEvent`, `$provide`,
`$inject`, and `$unprovide`), the actions applier (`applyActions`), and the
wire transport (envelope, fetch, CSRF, timeout). Designs:
[`docs/design/events.md`](../../../docs/design/events.md) section 5 and
[`docs/design/component_provide.md`](../../../docs/design/component_provide.md)
section 10.

This package is private and never published. The runtime is written in
TypeScript (`src/citry-events.ts`); its build output is committed at
[`packages/py/citry/citry/ext/events/client/citry-events.js`](../../py/citry/citry/ext/events/client/citry-events.js),
which the `ext/events/runtime.js` route serves, so Python packaging and
serving never run node.

Fixed `citry-events/1` records are not redefined here. The private
[`@citry/protocol-events-v1`](../../protocol/events/v1/js/) workspace package
builds outgoing calls and envelopes and validates incoming manifests, result
envelopes, and public action lists. esbuild includes those helpers in the same
IIFE, so this creates no browser request, global, or runtime package lookup.

## Working on it

The package is part of the repo's pnpm workspace; install from the repo root:

```sh
pnpm install
```

Then, from this directory:

```sh
pnpm run build      # rebuild the committed bundle from src/citry-events.ts
pnpm run typecheck  # tsc --noEmit (strict; esbuild stays the only emitter)
pnpm run lint       # biome check (lint + format)
pnpm test           # the pinned-version canary over the Alpine private APIs
pnpm run check      # all three in one go; the repo gate's citry-client phase
```

Commit the rebuilt bundle together with the source change; the two files are
one change. The repo-wide gate (`python scripts/check.py`) runs `pnpm run
check` here as its `citry-client` phase, so a stale type error or lint issue
fails the same command CI runs.

Run `pnpm --dir ../../protocol/events/v1/js run check` when changing a wire
boundary. It replays the shared Python/JavaScript conformance mutations against
the actual protocol validators.

## TypeScript and the bundle

`tsconfig.json` is for type-checking only (`noEmit`); esbuild compiles the
TypeScript directly and is the only emitter. `build.mjs` passes an empty
`tsconfigRaw` so esbuild ignores `tsconfig.json` when bundling: with
the config visible, its `strict` (hence `alwaysStrict`) setting would stamp a
top-level `"use strict"` across the whole iife bundle and flip the vendored
Alpine out of the non-strict mode the committed bundle has always shipped in.
The runtime's own iife carries its explicit `"use strict"` either way.

Alpine and morph ship no type declarations; the narrow surface the runtime
calls is declared locally in `src/alpine.d.ts` (including the pinned-version
evaluator, attribute-removal, scope, and lifecycle APIs described below).

## Version pins

`alpinejs` and `@alpinejs/morph` are pinned exactly (no range). The runtime
uses Alpine internals for scope isolation, held-fragment release, and exact
client-context directive cleanup (`addScopeToNode`, `_x_dataStack`,
`_x_ignore`, `initTree`, and per-directive `utilities.cleanup`), narrowly
instruments the pinned `getDirectiveHandler` execution path at build time,
and rides morph's Alpine bridge (`Alpine.cloneNode`). These are version-coupled; the
pins and the reasoning are recorded in
[`docs/design/alpinejs/spike-morph-alpine.md`](../../../docs/design/alpinejs/spike-morph-alpine.md).
When bumping either pin: run `pnpm test` (the canary trips on any drift in
those internals), rebuild, and run the browser e2e suite in
[`packages/py/citry/tests/e2e/`](../../py/citry/tests/e2e/).
