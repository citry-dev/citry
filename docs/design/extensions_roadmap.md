# Design: extensions roadmap

**Status (2026-07-23): active roadmap; Cache, Events, and Debug are shipped.** This document is the
prioritized list of *extensions* (plugins) still to build for citry, with the
things that look like extensions but are deliberately out of scope called out
so they do not get rebuilt by reflex. It is the "what next" companion to
[`extensions.md`](extensions.md), which is the design of the extension/hook
*system* itself.

For the system the items below plug into see [`extensions.md`](extensions.md).
For the CLI the command-bearing ones use see
[`extensions_commands.md`](extensions_commands.md). For the migration context and
the per-file verdicts that seeded this list see
[`migration_djc.md`](migration_djc.md). For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Where things stand

The extension *substrate* is built and is richer than the django-components
original: an `ExtensionManager` scoped to each `Citry` instance (not a module
global), name-keyed dispatch that calls only the extensions that implement a
hook, the `emit()` mechanism for extension-owned custom hooks, `Extension.urls`
with contrib mount adapters, `ExtensionCommand` plus the `citry` CLI, and the
`on_attrs_resolved` / `on_serialize` / `on_render_context_merge` hooks.

What ships on top of it today is **three built-in extensions**: `cache`, with
component and named-fragment render caching plus public introspection
([`caching.md`](caching.md)), `dependencies` (the asset-loading subsystem,
[`dependencies.md`](dependencies.md)), and `events` ([`events.md`](events.md)).
The bundled opt-in `Debug` visual boundary extension is described in
[`extensions_debug.md`](extensions_debug.md). Other
django-components extensions are folded into citry core, deliberately
deferred, or waiting in `_djc_reference/` to be built fresh.

**Extensions are host-language-specific by design.** An extension hooks runtime
lifecycle data, so it lives in the host language (Python today; JS/PHP/Go later),
not in the shared Rust core. The Rust core shares only the parser, AST, and
compiler output. So each live binding grows its own extension layer; this is the
intended shape, not a cost to remove.

---

## 2. Build now

These have their enabling hooks already in place, so they are the next concrete
work.

| Extension | What it is | Effort | Available hooks / notes |
|---|---|---|---|
| **Scoped CSS** | Isolates a component's CSS to its own DOM subtree: stamp a per-component data attribute on the elements the component renders (stopping at nested component boundaries), rewrite each top-level selector to target that attribute, and let in-template slot fills inherit the defining component's scope. Per-selector and per-component opt-out. | L | Marquee single-file-component parity feature ([`extensions.md`](extensions.md) section, upstream #1230). The root-marker lookup and `on_template_compiled` hooks are built; `on_slot_rendered` / `on_css_loaded` are wired. The upstream `css_scope.py` is a broken draft: **build properly, do not port.** The selector-rewrite primitive is a candidate for the Rust `html_transform` layer so JS/PHP/Go can reuse it. |
| **ColorLogger (tutorial)** | A tiny logging/observability extension whose real value is as the canonical "your first extension" walkthrough. | S | Low priority, high leverage: it is the documentation recipe and a smoke test of the hook surface end to end. |

---

## 3. Build later

Genuine extensions, but each waits on a design decision, a larger build, or one
of the open hooks in section 4.

| Extension | What it is | Notes |
|---|---|---|
| **Head-tag injection** | A `Component.Head` nested class (title, meta, link, style, script) that places tags in `<head>` with dedup/merge across the component tree, processed alongside JS/CSS resolution. | A natural sibling of `dependencies`, reusing the same `emit`/merge machinery and the `on_serialize` whole-page integration point (upstream #1444). |
| **Inline CSS** | Inlines the collected component CSS into the page (a `<style>` block) instead of serving linked files, applied as a whole-tree pass after render. | A separate, self-contained extension. Needs the post-render hook in section 4. (Critical-CSS extraction is a related but separate idea and is not actionable yet.) |
| **Tailwind** | Exposes component template and Python file paths to Tailwind's content scanner so co-located utility classes are not purged, and optionally drives the Tailwind build. | The dominant CSS approach for citry's audience; class-purge breakage with co-located styles is a known footgun. Sits on the component-introspection core API and the asset compiler (issue [#10](https://github.com/citry-dev/citry/issues/10)). |
| **[Storybook](extensions_storybook.md)** | An optional `ExtensionCommand` consumes explicit Python examples or a scenario catalog and emits a deterministic preview projection; scenario routes return server-rendered Citry output. | The Citry UI spike compares Server/Webpack and HTML/Vite, but adapter selection and publication are independent of Citry UI. Playwright runs behavioral journeys directly against standalone routes. A generic extension can later build on `ExtensionCommand`, `Extension.urls`, component introspection, and the proven scenario contract instead of requiring every component to declare nested Storybook metadata. |
| **Pydantic integration** | An optional ecosystem add-on layering Pydantic validation/serialization onto component inputs, on top of citry's built-in typed inputs. | Modest, opt-in; only the Pydantic add-on from the old "packs" list is a real extension candidate. |
| **`Component.Docs`** | Lets a citry *user* generate documentation for *their own* components: a component declares doc metadata (description, per-prop docs, examples), and the extension emits a docs page (or small site) plus a preview gallery that renders each component in isolation with sample inputs. | Distinct from the citry docs site, which documents citry's own public API; this documents the user's component library. Builds on the component-introspection API ([#26](https://github.com/citry-dev/citry/issues/26)) and a render endpoint, the way Storybook does. Delivered as an extension. |
| **Debug toolbar panel** | A per-request panel (Django-debug-toolbar style) surfacing render info: which components rendered, timings, slot fills, and the collected JS/CSS. | Hooks the render lifecycle plus a host integration. Delivered as an extension. Its structured runtime data is designed separately in [`component_tracing.md`](component_tracing.md). |

---

## 4. Open / conditional hooks

These are **not goals in themselves.** In django-components, extensions could
change how tags parse and resolve; in citry that is intentionally not supported,
because the engine optimizes its internals heavily and tags are not meant to be
swappable. Build these only if a concrete consumer above needs them, and decide
at that point.

- **Parse-time tag hooks** (`on_tag_*`) and **resolved-input hooks**
  (`on_*_input_resolved`). Only if **Scoped CSS** (section 2) concretely
  requires reading or mutating tag inputs. Decide while building it; do not add
  speculatively.
- **Asset post-process hooks** (`on_js_postprocess` / `on_css_postprocess`
  before caching, and a post-render `on_template_postprocess`). citry has the
  load-time `on_js_loaded` / `on_css_loaded` and `on_template_loaded` /
  `on_template_compiled`, but not these. Build when the first consumer lands: the
  asset compiler (issue [#10](https://github.com/citry-dev/citry/issues/10))
  or the inline-CSS extension.

---

## 5. Related core work (not extensions)

Surfaced during the survey, tracked elsewhere because they are core features or
standalone tooling, not extensions:

- **Asset compiler pipeline + static export** (TS/Sass/esbuild, a
  `collectcomponent`-style export). A core feature: it defines the
  `js_lang` / `css_lang` contract and the static-export model the `dependencies`
  extension consumes. Issue [#10](https://github.com/citry-dev/citry/issues/10).
- **Browser live-reload.** Dev tooling, issue
  [#9](https://github.com/citry-dev/citry/issues/9).
- **Component-introspection API**
  ([#26](https://github.com/citry-dev/citry/issues/26)). A core capability (list
  components, their inputs, their file paths) that **Tailwind** and **Storybook**
  consume. Not an extension itself.
- **Component-tracing API**
  ([`component_tracing.md`](component_tracing.md)). Opt-in, per-render and
  per-serialization structured observations for the future debug-toolbar
  extension. The value model and observation points are core runtime work; the
  toolbar UI and host integration are extension work.
- **Language server / linter**
  ([#23](https://github.com/citry-dev/citry/issues/23)), **formatter**
  ([#22](https://github.com/citry-dev/citry/issues/22)), and **syntax
  highlighting** ([#24](https://github.com/citry-dev/citry/issues/24)).
  Standalone tooling that benefits from the Rust parser, but is not part of the
  extension layer. (Three consumer-facing UIs are the exception and ship as
  extensions in section 3: Storybook, `Component.Docs`, and the debug-toolbar
  panel.)
- **Template-only components**
  ([#17](https://github.com/citry-dev/citry/issues/17)) are a core/parser
  concern, not an extension.

---

## 6. Explicitly not an extension to build

Recorded so they are not reintroduced. Each was decided against, with the reason.

| Item | Why not |
|---|---|
| `defaults` | Superseded: citry `Kwargs` are dataclasses, so defaults live on the field declarations. |
| `autodiscovery` (as an extension) | Runs from the `Citry` instance, not an extension (the only setup hook fires too early to import instance-bound modules). |
| Hot-reload (as an extension) | Built as the core `reload` module, not a plugin. |
| Cotton / `<c-*>` syntax translator | V3 `<c-*>` is the core syntax, so there is nothing to translate. |
| MCP server for component metadata | Dropped ([`extensions_commands.md`](extensions_commands.md) section 14). |
| `url` extension | Named handler URLs ship as part of the built-in Events extension ([`events.md`](events.md)). |
| `on_registry_created` / `on_registry_deleted` | Dropped in citry: one registry per `Citry`, and other hooks cover the space ([`extensions.md`](extensions.md) section 6.3). |
| Vue "feel" transpilers and a Vue single-file-component loader | citry's V3 syntax is already Vue-like, so a translation layer adds nothing. Client ownership and slot scope ship through the graph-first Alpine integration ([`alpinejs.md`](alpinejs.md)). |
| htmx component pack, critical-CSS, asset prefetch / preload / service-worker, per-component `render_js` wrap, icon-set packs, AI generation, a cross-language linter | Out of scope for the extensions roadmap (either not actionable, or not extension-shaped, or not aligned with citry's goals). |
| Pluggable component resolver | No concrete driver. Registry lookup is a fixed dict, and template-only components ([#17](https://github.com/citry-dev/citry/issues/17)) cover the "resolve from a template file" case. Revisit only if a real need appears. |

---

## 7. Sequencing

1. **Build now** (section 2): Scoped CSS is the high-value feature; the
   ColorLogger tutorial is small and will make the hook system legible. Cache
   and Debug are already shipped and exercise short-circuit, render, and
   serialize hooks.
2. **Decide the open hooks** (section 4) *while* building Scoped CSS, not
   before. Let the consumer prove the need.
3. **Build later** (section 3) in roughly the order Head-tag, Inline CSS,
   Tailwind, Storybook, and Pydantic.
