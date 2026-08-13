# citry-client

Source of Citry's Events and i18n browser runtimes.

`citry-events.js` and `citry-events-csp.js` contain the same Events client
code with the pinned standard or CSP Alpine evaluator plus
`@alpinejs/morph`,
the component scopes, the magics
(`$state`, `$loading`, `$error`, `$sendEvent`, `$onEvent`, `$provide`,
`$inject`, and `$unprovide`), the actions applier (`applyActions`), and the
wire transport (envelope, fetch, CSRF, timeout). `citry-i18n.js` contains the
opt-in `$i18n` service and pinned Fluent browser runtime. It loads only for a
client-enabled `<c-i18n>` boundary. Designs:
[`docs/design/events.md`](../../../docs/design/events.md) section 5 and
[`docs/design/component_provide.md`](../../../docs/design/component_provide.md)
section 10, plus [`docs/design/i18n.md`](../../../docs/design/i18n.md) section
6.8.

This package is private and never published. The runtimes are written in
TypeScript. Their build outputs are committed at
[`packages/py/citry/citry/ext/events/client/citry-events.js`](../../py/citry/citry/ext/events/client/citry-events.js),
[`packages/py/citry/citry/ext/events/client/citry-events-csp.js`](../../py/citry/citry/ext/events/client/citry-events-csp.js),
and
[`packages/py/citry/citry/ext/i18n/client/citry-i18n.js`](../../py/citry/citry/ext/i18n/client/citry-i18n.js).
Python packaging and serving never run Node.

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
pnpm run build      # rebuild the three committed bundles from their TypeScript sources
pnpm run typecheck  # tsc --noEmit (strict; esbuild stays the only emitter)
pnpm run lint       # biome check (lint + format)
pnpm test           # the pinned-version canary over the Alpine private APIs
pnpm run check      # all three in one go; the repo gate's citry-client phase
```

Commit each rebuilt bundle together with its source change. The standard and
CSP Events outputs intentionally share one source and differ only in Alpine's
aliased entry point. The repo-wide gate
(`python scripts/check.py`) runs `pnpm run
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

`alpinejs`, `@alpinejs/morph`, `@alpinejs/csp`, and `@fluent/bundle` are pinned
exactly, with no version range. The CSP package is built from the same Events
source by aliasing only `alpinejs/src/index` to `@alpinejs/csp/src/index`.
Off and warning serialization select `citry-events.js`; strict CSP
serialization selects `citry-events-csp.js`. A fragment manifest records that
variant and an existing manager rejects a mismatch before adoption. The Events runtime
uses Alpine internals for scope isolation, held-fragment release, and exact
client-context directive cleanup (`addScopeToNode`, `_x_dataStack`,
`_x_ignore`, `initTree`, and per-directive `utilities.cleanup`), narrowly
instruments the pinned `getDirectiveHandler` execution path at build time,
and rides morph's Alpine bridge (`Alpine.cloneNode`). These are version-coupled; the
pins and the reasoning are recorded in
[`docs/design/alpinejs/spike-morph-alpine.md`](../../../docs/design/alpinejs/spike-morph-alpine.md).
When bumping an Alpine-family pin: update all three together, run `pnpm test`
(the canary trips on any drift in those internals), rebuild, and run the browser e2e suite in
[`packages/py/citry/tests/e2e/`](../../py/citry/tests/e2e/).
When bumping Fluent, rebuild and run the i18n browser tests in that same suite.
