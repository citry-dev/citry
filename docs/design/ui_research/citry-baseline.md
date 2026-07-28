# Citry baseline for the UI library

**Snapshot: 2026-07-24.** This report separates implemented Citry capabilities
from proposals and parked work. The component library may rely on the first
group. It must design around the second group or make a missing capability an
explicit prerequisite.

## 1. Capabilities the library may rely on

| Capability | Current contract | Evidence |
|---|---|---|
| Events | The v1 server, protocol, client applier, transport, dependency queue, bindings, forms, preservation, conformance, docs, and migration guides are implemented. | [`../events_plan.md`](../events_plan.md) lines 3-25 |
| Client ownership | Graph-first Alpine is the landed source of truth. Citry owns logical component, slot-source, physical-region, and stable browser identity while pinned Alpine supplies expressions, directives, reactivity, and morphing. | [`../alpinejs.md`](../alpinejs.md) lines 3-32 |
| Client component context | `$component` receives live roots, inert render data, Events State, reactive props, stable scope, managed effects/reactivity, graph data, and event helpers. Cleanup runs across compatible render revisions. | [`../alpinejs.md`](../alpinejs.md) lines 124-198 |
| Client props | `$c-props` provides reactive, declared, validated parent-to-child browser values in the exact authored source scope. | [`../alpinejs.md`](../alpinejs.md) lines 200-286 |
| Component-tag handlers | Alpine and Citry handlers authored on a child tag execute in the parent source scope while physical event values come from the child roots. | [`../alpinejs.md`](../alpinejs.md) lines 316-379 |
| Slot ownership | Template-authored supplied fills keep caller scope; fallback content uses receiver scope. Plain server-only slots do not activate the browser runtime. | [`../alpinejs.md`](../alpinejs.md) lines 381-414 |
| Root shapes | One logical lifecycle supports element roots, multiple roots, rootless ranges, mirrored placements, nesting, adjacency, and teleport. | [`../alpinejs.md`](../alpinejs.md), especially sections 6-10 |
| Typed component inputs | Components support typed `Kwargs`, `Slots`, template data, JavaScript data, and CSS data. | [`../../../packages/py/citry/citry/component.py`](../../../packages/py/citry/citry/component.py) |
| Explicit HTML attributes | Components can accept a declared mapping and spread it onto the chosen root or nested element with `c-bind`. The component controls placement. | [`../alpinejs.md`](../alpinejs.md) lines 288-314 |
| Assets | Components may use inline or file-backed templates, JavaScript, and CSS. File resolution supports reusable-package files relative to the declaring component module. | [`../asset_loading.md`](../asset_loading.md) section 3.2 |
| Asset collection and fragments | The dependencies extension collects, deduplicates, inlines or serves component JS/CSS and loads new assets for fragments through fingerprinted routes. | [`../dependencies.md`](../dependencies.md) sections 8, 9, and 16 |
| Initialization | `Citry.initialize()` completes discovery, built-in registration, and tag-rule construction before request concurrency. Asset files remain lazy. | [`../component_initialization.md`](../component_initialization.md) lines 74-103 |
| Component libraries | A package declares inert `LibraryComponent` classes and one explicit `ComponentLibrary`; `register_library()` atomically materializes fresh classes and a Citry-owned installation record for each receiving engine. | [`../component_publishing.md`](../component_publishing.md) |
| Server provide/inject | Python components can provide immutable named payloads to rendered descendants through `Component.provide()`, `Component.inject()`, and `<c-provide>`, including content rendered through slots. | [`../component_provide.md`](../component_provide.md) sections 2-6 |
| Introspection | The engine exposes deterministic component metadata for schemas, assets, identities, and extension-owned data. The CLI can emit a component catalog as JSON. | [`../component_introspection.md`](../component_introspection.md) sections 1-3 and implementation phases |
| Hosts | Core routes and assets work through the shipped Django, FastAPI, Flask, ASGI, and WSGI integrations. | [`../dependencies.md`](../dependencies.md) section 16 |
| Workspace | A new Python package under `packages/py/*` joins the uv workspace. Package dependencies belong to the package that imports them. | [`../../../pyproject.toml`](../../../pyproject.toml) lines 53-69; [`../../../CLAUDE.md`](../../../CLAUDE.md) "Python dependencies have one owner" |

## 2. Constraints the library must design around

| Constraint | Consequence for Citry UI | Evidence |
|---|---|---|
| Library replacement is deferred | Publishing, repeated installation, collision preflight, required extensions, rollback, clear, and retained-generation checks are implemented. Complete uninstall and live replacement still need a dedicated lifecycle design. | [`../component_publishing.md`](../component_publishing.md) sections 5-7 |
| No general root-attribute fallthrough | Every component family needs a consistent explicit attribute API and must define which element receives each mapping. Multi-root components need especially clear rules. | [`../alpinejs.md`](../alpinejs.md) lines 288-314 |
| Scoped CSS is roadmap work | Initial components need a deliberate class namespace, cascade-layer, specificity, and token strategy. They cannot assume automatic selector rewriting. | [`../extensions_roadmap.md`](../extensions_roadmap.md) lines 45-54 |
| Asset compiler is unimplemented | The distribution must ship deterministic, prebuilt plain JS/CSS. Consumer projects cannot be required to compile TypeScript, Sass, JSX, or Tailwind for ordinary use. | [`../asset_compiler_plan.md`](../asset_compiler_plan.md) opening status |
| Classic scripts are the live baseline | Component JavaScript and the Events bundle use classic IIFEs. ESM, module imports, source maps, and registration binding remain parked research. | [`../alpinejs.md`](../alpinejs.md) lines 999-1011; [`../esm.md`](../esm.md) lines 1-16 |
| Standard Alpine requires `unsafe-eval` | The first library inherits Citry's current CSP trade-off for expression-bearing components. The charter must not promise constrained CSP before Citry provides it. | [`../alpinejs.md`](../alpinejs.md) lines 992-997 |
| Client initialization is synchronous | Initializers cannot return a Promise to delay descendant readiness. Async work needs explicit ownership, cancellation, and stale-result guards. | [`../alpinejs.md`](../alpinejs.md) lines 154-169 and 1013-1020 |
| No browser instantiation of rendered server components | Alpine `x-for` and `x-if` may clone ordinary DOM inside a component, but not a client-active server component. Repeated component families use server `<c-for>` or client-owned DOM within one existing component. | [`../alpinejs/a9_client_instantiation.md`](../alpinejs/a9_client_instantiation.md) lines 1-42 |
| Detached Python slot content has no caller client scope | Rich interactive slot composition should use template-authored fills. Detached Python slot objects receive an isolated empty client base inside an active graph. | [`../alpinejs.md`](../alpinejs.md) lines 381-414 |
| Static and interactive costs differ | Static primitives should remain server-only. Making every visual component client-active would pay Alpine and graph startup costs unnecessarily. | [`../alpinejs.md`](../alpinejs.md) lines 112-120 and 1013-1020 |
| Client ambient context is not yet a public contract | The graph-first design names provide/inject as the intentional deep-context channel, but the shipped client exposes no `$provide`/`$inject` magic or `$component` provide/inject methods. Theme and later localization state need a dedicated design and conformance work. | [`../alpinejs.md`](../alpinejs.md) lines 24-48; current client source and public context contract |
| Package contents are fixed | Each wheel has one fixed file inventory. `citry-ui` therefore carries its own Python modules and prebuilt assets rather than adding files to the `citry` distribution. | Python packaging dependency and wheel specifications |

## 3. Packaging baseline

The leading package shape is:

```text
Distribution: citry-ui
Import:       citry_ui
Dependency:   a tested compatible range of citry
Assets:       templates and prebuilt CSS/JS inside the citry-ui wheel
Registration: explicit engine-local installation before app.initialize()
```

The direct dependency path is the baseline:

```sh
uv add citry-ui
```

`citry-ui` depends on the compatible `citry` API that it imports. Clean pip
and uv install, upgrade, downgrade, uninstall, and release-order tests cover
that one-way relationship. The separate `citry_ui` import package avoids two
distributions writing files into the same `citry/` directory.

## 4. Architectural implications

1. **Share behavior, not runtime duplication.** Styled and headless surfaces
   should use the same semantics, focus, keyboard, state, and cleanup logic.
2. **Keep static output static.** Layout, typography, cards, badges, and other
   non-interactive components should not register browser behavior by default.
3. **Use explicit attributes and parts.** Since root fallthrough is not a
   framework feature, the library must make attribute placement a predictable
   public convention.
4. **Prebuild the distribution.** Maintainers may use TypeScript, Sass, or
   other tools while building `citry-ui`, but consumers receive plain assets.
5. **Use the publishing API.** UI packages declare one `ComponentLibrary` and
   applications call `app.register_library(package)` before initialization.
   Package-specific constructors, registration caches, and invocation objects
   are compatibility layers during migration rather than the target model.
6. **Test live server-render paths.** Accessibility and state tests must cover
   fragments and morphs, not only an isolated first render.
7. **Avoid private browser contracts.** Component code uses `$component`, its
   managed helpers, public Alpine directives, and Events. Citry's own canaries
   remain the only code coupled to Alpine internals.
8. **Design client ambient context before relying on it.** The server-side
   provide/inject model is implemented, but a theme needs reactive values in
   the browser as well. A focused design must compare `$component` methods
   with `$provide`/`$inject` magics and define graph ancestry, slot ownership,
   teleport, morph continuity, updates, defaults, cleanup, and diagnostics.

## 5. Conflicts and stale status text

- [`../../../TODO/project_status_june_2026.md`](../../../TODO/project_status_june_2026.md)
  predates Events v1, graph-first Alpine, and current introspection. It is a
  dated historical snapshot for this project area.
- The opening line of [`../component_introspection.md`](../component_introspection.md)
  says phases 0 through 3 are implemented, while the implementation ledger
  later also marks the Events metadata phase implemented. The ledger and live
  code are the more specific evidence; the status line should be refreshed in
  a separate documentation cleanup.
