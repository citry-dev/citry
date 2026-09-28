# citry-client

Build and verification tooling for Citry's committed browser runtime.

Citry ships Vue as its sole interactive renderer. The package pins Vue 3.5.42
and builds the production runtime-only API, the prepared-tree Events bridge,
and the independent Fluent i18n runtime. Node and pnpm are repository build
tools; applications serve the committed JavaScript from the Python package and
do not require Node in production.

The maintained TypeScript sources are:

- `src/citry-vue.ts`, which exposes the pinned Vue runtime-only package;
- `src/citry-fragments.ts`, which manages server-rendered HTML fragments;
- `src/citry-events-vue.ts` and `src/citry-events-shared.ts`, which implement
  signed Events transport, scheduling, forms, and the prepared-tree host port;
- `src/citry-i18n-vue.ts`, `src/citry-i18n-runtime.ts`, and
  `src/citry-i18n-core.ts`, which implement the native Vue Fluent plugin.

`pnpm run build` writes `_vue/vue.js`, `_vue/fragments.js`, `_vue/events.js`,
the ordered combined `_vue/runtime.js`, and
`ext/i18n/client/vue-plugin.source.js` under the Python package.
The combined runtime also carries the hand-written prepared coordinator,
`_vue/client.js`, with its comments and indentation removed. Edit
`client.js`, then run the build so `runtime.js` picks up the change.
Generated files are committed so installed Citry applications never compile
browser code at startup.

Run the package checks with:

```console
pnpm --dir packages/js/citry-client run build
pnpm --dir packages/js/citry-client run check
```

The canary tests rebuild the Vue runtime, fragment manager, Events bridge, and
i18n plugin with esbuild and compare each with its committed file. They also
rebuild `runtime.js` from its committed parts and check that it loads Vue
before the coordinator and Events bridge.
