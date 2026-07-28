# Design: development and production mode

**Status (2026-07-25): proposal, partially implemented.** The `Citry(mode=...)`
setting is implemented. Its debug-extension consumer (section 4) is written but
temporarily gated off (`extension._AUTO_DEBUG_IN_DEVELOPMENT = False`) pending a
bug: the debug extension's render-cache participation turns a cached
(`<c-cache>`) component's ownership graph into an invalid manifest (an
uninvoked instance that still names a parent), even with both highlight flags
off, so auto-registering it in development would break dev pages that use
cache. The client ownership graph consumer (section 3) is specified here and
lands in a following change. Broader consumers (verbose diagnostics, source
maps for the browser error overlay, cache behavior) are future work. The
setting is the single source of truth for all of them.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md). For the error overlay
that consumes development provenance see section 6.8 of
[`early_validation_plan.md`](early_validation_plan.md).

---

## 1. Problem

Some output is useful for a developer and dead weight for an end user. The
clearest case is the client ownership graph. A **component-tag client
binding** is a browser-side `$c-props`, `@click`, or `@c-poll.5s` binding
resolved from a nested `<c-*>` tag. Every recorded nested component tag,
client binding, fill, and slot carries a byte range into its template source
so a future error overlay can show the authored snippet. Production never reads those
offsets, and they are roughly half of the uncompressed manifest, so shipping
them to every visitor pays for a feature only a developer uses.

The server is the only place that can decide this. It knows the component
tree, it builds the manifest, and it is where a framework-wide "this is a
development build" signal belongs. Today Citry has no such signal, so the
manifest cannot make the choice.

## 2. The setting

`Citry(mode="production")` is a construction-time setting with two values:

- `"production"` (the default): the engine omits developer-only output.
- `"development"`: the engine includes it.

Production is the default so that a project ships lean output unless it opts in,
the same way a deployment opts into verbose logging rather than opts out. A
host framework wires its own environment to this value (for example a Django
project passes `mode="development"` when `DEBUG` is true).

The value is fixed at construction, like the other engine settings, so every
render from one engine agrees. A project that needs both at once uses two
engines, which is already how isolated configuration works.

The name is `mode` rather than a `debug` boolean because the concept is an
environment, not a single switch, and because Citry already ships a `debug`
extension (visual boundaries); a `Citry(debug=...)` argument would read as
turning that extension on. A future value such as `"test"` stays open.

An unrecognized value is rejected at construction, not coerced or defaulted.
`mode` is a fixed set of strings, so a typo like `"prod"` or `"dev"` raises
immediately with the allowed values, rather than surfacing later as a build
that silently ships or omits developer output. Rejecting at construction also
means every later read of `citry.mode` can trust the value without re-checking.

## 3. First consumer: the client ownership graph

The manifest carries a top-level `mode` member echoing the engine setting, so
the browser can tell "this build sends no provenance" apart from "this build
sends provenance and this render happened to have none":

- `mode: "production"`: every graph's `sourceLocations` array is empty and
  every location reference is null. The browser skips the location-based
  consistency checks, because there is nothing to check against.
- `mode: "development"`: source locations are present with their
  `sourceOffset`, `sourcePos`, and `origin`, references resolve, and the browser
  runs the full checks.

The manifest still records source locations internally while rendering; `mode`
only decides whether they reach the wire. The reference validator and both
browser and server enforce the mode invariant: a production manifest with a
non-empty `sourceLocations` array, or a development manifest whose references
do not resolve, is rejected.

## 4. Second consumer: the debug extension

The built-in `debug` extension inserts visual component boundaries into the
rendered HTML, which is developer output by definition. In `"development"` it
is auto-registered alongside the always-on built-in extensions; in
`"production"` it is absent, so a deployed page carries no debug boundaries and
a project never has to remember to strip the extension before shipping.

Because it becomes a built-in in development, its name `debug` is reserved
there, and a project that also lists the extension explicitly in development
hits the normal duplicate-name rejection. In production the extension is not
built in, so a project may still opt into it explicitly for a production-like
build that wants boundaries.

## 5. Open questions

- whether host integrations should default `mode` from a detected environment
  variable or require an explicit value;
- whether a later `"test"` value differs from `"development"`;
- how development ships the template source itself (inline, fetched, or a
  source map) for the error overlay, which is the section 6.8 question in
  [`early_validation_plan.md`](early_validation_plan.md);
- which other outputs (diagnostic verbosity, cache bypass, unminified client
  assets) should read `mode` rather than their own separate flags.

## 6. Non-goals

`mode` is not a security boundary and not a correctness switch: a component
renders the same tree in both modes, and production still validates everything
it receives. It only decides whether developer-facing extras are included.
