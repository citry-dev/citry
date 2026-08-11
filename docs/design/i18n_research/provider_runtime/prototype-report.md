# Server and browser provider behavior

**Status:** Bounded Phase 0 exploration passed in Chromium, Firefox, and
WebKit. The candidate is research code, not the shipped i18n extension.

## What this settled

The public `<c-i18n>` API can use Citry's existing server `provide()` and
browser `$component` provide/inject systems. The active request locale still
belongs in a `ContextVar`, not in a mutable extension field. Twenty-four
concurrent threads, twenty-four async tasks, and an exception path kept and
restored separate bindings.

A server-only provider can stay transparent and add no i18n browser payload.
A client provider needs one real wrapper. The wrapper owns `lang` and `dir`,
and the provider exposes one frozen service with readonly `context` and
`status`, `bindMessage()`, subscriptions, and `switchLocale()`.

One design detail changes: a server-only provider nested below a client
provider cannot form a browser barrier while remaining rootless and invisible.
Python `Component.unprovide()` affects server render context, but the current
client graph does not serialize server provide/inject records. The browser's
ambient `unprovide` operation acts on a real element boundary.

The v1 rule is therefore:

- `client=False` outside a client boundary is transparent and emits no i18n
  browser dependency or data;
- `client=False` below a client boundary must supply `tag`, so Citry can render
  a real barrier wrapper and apply the core ambient `unprovide` operation;
- omitting `tag` in that nested case fails the production check;
- a nearer `client=True tag="..."` provider establishes a new independent
  service inside the barrier.

This keeps one public `<c-i18n>` component and avoids a new client-graph schema.
The outer provider already loads the shared browser runtime, so the barrier
adds no separate i18n runtime or catalog dependency.

## What the browser probe checked

The real Citry page contained:

- an outer English client provider;
- an inherited child with an explicit Prague time zone;
- a Czech child with an explicit locale and cleared time zone;
- a server-only barrier;
- a Japanese client provider below that barrier; and
- message sinks under every boundary.

Switching the outer provider to Arabic changed the outer and inherited child
to Arabic and RTL. The inherited child kept Prague. The explicit Czech child
and independent Japanese provider did not change. The reader directly below
the false barrier had no client service.

All wrappers and message sinks changed in one synchronous commit. A
`MutationObserver` saw only complete states. The same behavior passed in all
three browsers.

The candidate also proved these failures:

- an underscore locale alias was rejected without calling the loader;
- a failed catalog chunk kept the prior context and page;
- a mismatched artifact revision kept the prior context and page;
- an older delayed locale request became stale when a newer request won;
- an undeclared message ID was rejected;
- assigning to the frozen service or context could not change it;
- a server context mismatch at mount would reject the provider before use.

## Production contract

The build emits the canonical locale and accepted-alias tables. The client maps
only through those tables. It does not ask ambient browser ICU to canonicalize
an input.

Every provider serializes a strict policy that distinguishes inherited,
explicit, and cleared fields. A switch computes the whole nested provider tree
from outer to inner, validates every required catalog and sink, and only then
changes wrappers, sinks, and readonly contexts. Explicit child fields remain
fixed. Inherited fields follow the new parent.

`switchLocale()` uses a generation number. A completed load may commit only if
its generation is still current. A load, validation, or sink failure leaves
the previous context and visible content intact and exposes a readonly error
status.

## Limits

- The candidate uses a small in-memory artifact loader. Browser partition
  loading, digests, parser canaries, and the complete typed formatter wire are
  covered by the final runtime and payload stage.
- It binds text sinks only. Attribute sinks use the same staged target model
  but still need production tests with Pagination and Combobox.
- It proves DOM atomicity, not assistive-technology announcement timing.
- The server-only payload check uses a dedicated no-JS provider fixture. The
  production component achieves the same result by rendering its private
  browser-service child only when `client=True`.
- This session did not have an independent agent reviewer. The evidence is
  executable and adversarial, but not independently reviewed.

The frozen results are in [`evidence.json`](evidence.json). Reproduction steps
are in [`prototype-environment.md`](prototype-environment.md).
