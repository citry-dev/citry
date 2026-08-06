# Client-graph JavaScript runtime

This private workspace package is the browser implementation of
`citry-client-graph/1`. It owns strict JSON checks, closed record shapes,
canonical revisions, logical record relationships, and ownership-comment
parsing. Product browser code owns only work that needs the live DOM.

`build.mjs` bundles the browser boundary from `src/core-embed.ts`, minifies it,
and writes it between one marker pair in the committed core `citry.js` file.
The first insertion requires `build:initialize`. Normal builds replace only
the marked bytes. `build:check` reconstructs the complete expected file in
memory and fails when the block is absent, duplicated, moved, or stale.

The Events bundle imports the ownership-comment parser from this package
directly, so it adds no dependency on the generated core browser global. The
existing core-before-Events runtime order remains unchanged because Events
uses the core hook broker.

Run the complete package gate from the repository root:

```bash
pnpm --dir packages/protocol/client_graph/v1/js run check
```

The gate type-checks and lints the package, replays every shared conformance
mutation, checks all 47 manifests and 13 canonicalization vectors, exercises
JavaScript-only invalid values, runs 16 runtime tests, verifies generated core
freshness, and reports
the combined browser payload against its approved guard.
