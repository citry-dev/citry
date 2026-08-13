# Phase 6 architecture hypotheses and packaging spike

**Snapshot:** 2026-07-23. **Status:** Phase 6 historical evidence, with a
2026-08-08 framework and publishing follow-up. The architecture comparison was frozen before
the original packaging spike was evaluated. Examples of package-owned
registration, invocation facades, and installation references below describe
that experiment, not the current authoring API. Current publishing behavior is
specified in [`component_publishing.md`](../component_publishing.md), and
current source rules are in the repository-wide
[`component authoring guide`](../../best-practices/component-authoring.md) and
Citry UI's
[`package policy`](../../../packages/py/citry_ui/docs/component-authoring.md).

**Phase 7 decision (2026-07-29):** one public architecture advances:
the separate `citry-ui` distribution publishes `LibraryComponent` definitions
that applications register explicitly into each Citry engine. The H1/H2/H3
headless-delivery comparison below remains historical research. Headless APIs
and their performance comparison are parked until a broader styled catalog,
real application usage, and representative full pages provide evidence.

The controlling product decisions are in the
[product charter](product-charter.md), the implemented framework boundary is
in the [Citry baseline](citry-baseline.md), and the Phase 5 synthesis is in the
[Citry fit matrix](citry-fit-matrix.md).

## 1. Outcome to prove

Phase 6 must leave at least two plausible product shapes able to implement the
same Phase 7 vertical slice. Every advancing shape must use the same Citry
server, Events, ownership, slot, asset, and lifecycle contracts. No hypothesis
may hide a second client component runtime inside the package.

The comparison freezes three component-delivery hypotheses:

1. installed paired components;
2. installed styled components plus source-owned headless components;
3. a hybrid installed behavior kernel, installed default assemblies, and
   optional source ownership above the kernel.

CSS foundations, structural styles, theme styles, utilities, and consumer
overrides are separate jobs within each hypothesis. They are not a component
architecture by themselves. Web Components remain a delivery comparison, not
a candidate second runtime.

The direct installation contract is fixed:

```sh
uv add citry-ui
```

The Python distribution is `citry-ui`, its import namespace is `citry_ui`, and
it depends on a tested compatible `citry` range. There is no `citry[ui-*]`
installation alias.

The package now targets the `citry>=0.3.2,<0.4.0` source line and Citry Core
1.5.0. Their release artifacts are pending. Citry UI still needs clean
released-artifact and multi-release installation fixtures before publication.

## 2. Fixed boundaries

The following constraints apply equally to every hypothesis:

- The styled surface must be polished and useful without consumer CSS.
- The headless surface renders no library-owned HTML. It exposes typed state,
  native attributes, ARIA relationships, handlers, focus targets, and other
  behavior through required slots or parts so the author owns the assembly.
- Styled and headless forms must not maintain independent behavior engines.
- Static component families must remain server-only when they have no browser
  behavior.
- Consumer installation must not require Node, a CSS compiler, a CDN, or a
  runtime network download.
- Packaged inline or module-relative templates, classic JavaScript, and CSS
  must be deterministic wheel content. File assets resolve relative to the
  declaring Python module.
- Explicit per-Citry registration happens before `Citry.initialize()`.
- Client ambient context uses Citry's public server and client
  provide/inject/unprovide contract. Phase 6 does not promote an application
  global or DOM-parent lookup into a UI API.
- Localization architecture remains separate follow-up work. Explicit
  direction and author-supplied text remain in scope.
- Charts, rich-text editors, maps, and domain-heavy data grids remain
  companion-package candidates.
- Accessibility acceptance uses WCAG 2.2 AA, WAI-ARIA APG, Open UI, and the
  HTML standard as baselines rather than library popularity as proof.

## 3. Live Citry facts that constrain the options

The architecture comparison uses these implemented facts rather than future
design intent:

| Concern | Implemented contract | Consequence for Phase 6 |
|---|---|---|
| Per-Citry classes | `register_library()` materializes each inert definition as a fresh `Component` subclass for the receiving engine; a concrete class cannot move to another engine | Every installation handle contains classes made for exactly one engine |
| Library registration | `ComponentLibrary` is an explicit ordered manifest and Citry owns exact definition-to-class and installation records | Citry UI component files directly define `LibraryComponent` classes and the package exposes one manifest without component-specific publishing plumbing |
| Atomic registration | Library classes and their installation record publish in one lifecycle transaction; an escaping `BaseException` restores all Citry-owned registration and library state | The UI catalog needs no compensating unregistration; uninstall and live replacement remain publishing work |
| Concurrency | Another thread that encounters an active Citry lifecycle mutation fails with `CitryLifecycleInProgress` | Another thread cannot observe or interleave with a component catalog before its atomic block commits |
| Initialization | `initialize()` is repeatable and retryable; discovery and built-in failures are not a global package transaction | The package registers first, then the application initializes and owns retry policy |
| Assets | Plain mixins and components may declare module-relative template, JavaScript, and CSS files; loading is lazy | A wheel can carry prebuilt assets without application search paths or a build step |
| Introspection | Engine-local component metadata includes identities, names, schemas, and asset provenance in canonical order | The package can prove deterministic discovery, but core metadata does not yet record library family or styled/headless pairing |
| Python composition | Calling a component class creates a `CitryElement`; expressions render `CitryElement`, `CitryRender`, `Slot`, and `ComponentLike` contextually | Per-Citry references and imported component-like values now resolve through the exact engine rendering them |

`register_library()` builds on Citry's atomic registration lifecycle and adds
library installations, exact definition maps, portable identity checks, and
required extension names to the same publication unit. Python side effects
and extension-owned state remain outside rollback. Uninstall, replacement,
and semantic dependency-version negotiation remain future publishing work.

### 3.1 Required usage patterns

The maintainer review fixes the order of importance for consumer APIs. These
patterns constrain every hypothesis even though they do not, by themselves,
decide whether an assembly is installed or source-owned.

The primary template path is a short registered tag:

```python
from citry import Component


class MyComp(Component):
    template = """
      <div>
        <c-CButton type="submit">Click me!</c-CButton>
      </div>
    """
```

`CButton` and `CButtonHeadless` are registry names. Their concrete classes are
created for one Citry engine and therefore are not module-level Python imports.
Registration must finish before the first render that compiles and validates
the containing template. Citry UI publishes a core `ComponentLibrary` manifest,
so `app.register_library(citry_ui)` materializes all of its definitions for that
Citry instance.

The primary Python composition target is an engine-neutral public value:

```python
from citry import Component
from citry_ui import CButton

cool_button = CButton(slots={"default": "Click me!"})


class MyComp(Component):
    def template_data(self, kwargs, slots):
        return {"cool_button": cool_button}

    template = """
      <div>{{ cool_button }}</div>
    """
```

At the expression site, Citry must resolve `cool_button` through the current
component's engine into the `CButton` class installed for that engine, then continue through
the normal live `CitryElement` render path. Standalone
`CButton(...).render()` and `str(CButton(...))` raise when no engine is passed;
`CButton(...).render(citry=app)` is the explicit out-of-tree form.

Citry's public `ComponentLike` protocol now supplies that automatic expression
resolution. It receives the current Citry engine and returns one
`CitryElement`, preserving ownership and dependency metadata without a package
global or module-level default fallback.

The headless template path requires author-owned HTML and scoped binding data:

```html
<c-CButtonHeadless loading type="submit">
  <c-fill name="default" data="data">
    <button class="brand-action" c-bind="data.attrs">
      Click me!
    </button>
  </c-fill>
</c-CButtonHeadless>
```

The advanced per-Citry handle remains available for introspection, runtime
extension, and explicit Python composition, with flat family-mode fields:

```python
installed = app.register_library(citry_ui)
element = citry_ui.CButton(slots={"default": "Save"})
headless_class = installed[citry_ui.CButtonHeadless]
```

Ordinary component modules should not import `installed`. It is an installation
and tooling surface, not the default authoring vocabulary.

### 3.2 Required maintainer layout

Component-family work stays separate from registration plumbing:

```text
citry_ui/
  __init__.py                    public imports and __citry_library__
  components/
    __init__.py                  explicit ordered definition catalog
    cbutton.py                   LibraryComponent definitions, schemas,
                                 behavior, assemblies, and theme
```

The Button spike keeps its Python, template, and CSS in one family file.
Behavior-heavy families may grow into one family directory with adjacent
private assets, but the catalog remains an explicit `ComponentLibrary` tuple.
Importing a family creates inert definition classes and no concrete Component.
Citry owns materialization, whole-catalog rollback, exact installation lookup,
and stale-generation checks. Filesystem discovery, runtime `__getattr__`, and
reflection-generated public handles remain outside this design.

### 3.3 Proposed component-like rendering protocol

Citry should expose one narrow structural protocol for values that become a
real `CitryElement` only after the current engine is known:

```python
from typing import Protocol, runtime_checkable

from citry import Citry, CitryElement


@runtime_checkable
class ComponentLike(Protocol):
    def __citry_element__(self, citry: Citry, /) -> CitryElement: ...
```

`ComponentInvocation` would implement it by resolving its stable package key
through Citry UI's installation record:

```python
class ComponentInvocation:
    def __citry_element__(self, citry: Citry, /) -> CitryElement:
        return self.resolve(citry)
```

That `resolve()` operation is lookup-only. It must never register a component,
rebuild the package installation, or invalidate tag rules during rendering.

The rendering path is intentionally small:

```text
value returned by {{ expression }}
  -> ComponentLike.__citry_element__(current_component.citry)
  -> validate that the result is a CitryElement owned by that Citry instance
  -> use the existing CitryElement render path
  -> preserve provides, ownership, dependencies, and error tracing
```

The protocol is not an HTML-safety protocol. Citry must detect it before
ordinary escaping, and implementations should not add `__html__`; flattening
to a trusted string would discard component ownership and dependency data.
Resolution runs once per occurrence and must return a `CitryElement` directly,
not another component-like value. A wrong result type or an element owned by a
different engine is a controlled render error attached to the expression's
template location.

The first implementation must update every structured-content boundary that
can legitimately carry a composed component: expression bodies, static and
callable slot fills, and `on_render` replacements. It must also classify a
component-like value as dynamic in const precomputation. HTML attribute values
remain scalar and do not gain component composition semantics.

Core Citry owns only contextual resolution and validation. It does not know
how a third-party package installs components. Citry UI's implementation must
resolve the stable key, such as `cbutton`, against the exact class stored for
that engine and package installation. A coincidentally named class returned by
`app.get("CButton")` is not sufficient evidence that Citry UI is installed.
Before this becomes public, normal application setup must install Citry UI
before tag-rule construction so direct `<c-CButton>` usage and Python
invocations share the same exact installed classes.

## 4. Hypothesis H1: installed paired components

### 4.1 Shape

`citry-ui` installs both styled and headless classes for every supported
family. Registration returns an engine-local typed handle with flat,
deterministic family-mode fields:

```python
ui = citry_ui.register_components(app)

ui.cbutton(slots={"default": "Save"})
ui.cbutton_headless(slots={"default": custom_button_slot})

styled_class = ui.cbutton.component_class
headless_class = ui.cbutton_headless.component_class
```

One internal behavior/conformance implementation supplies both modes. The
styled mode adds the default assembly and theme assets. The headless mode
renders a required scoped slot with behavior data but supplies no HTML or
default theme. The author-owned fill applies the required native bindings.

### 4.2 Strengths

- The default and headless experiences install, upgrade, and receive security
  fixes together.
- The package can run the exact same behavior suite against both modes.
- Documentation can present one stable Python and template vocabulary.
- Applications do not acquire copied source merely to remove theme styles.
- Deterministic pairing and compatibility can be represented by flat handle
  metadata and the package version without one wrapper dataclass per family.
- The styled default remains the shortest path, matching the product charter.

### 4.3 Risks and likely complaints

- A headless author can omit or misapply required native bindings because the
  package no longer owns the element.
- Styled markup and the headless conformance renderer can drift even with
  shared Python and JavaScript behavior.
- A broad installed package can ship more CSS than a route uses unless asset
  grouping is effective.
- Dynamically generated per-Citry class references are runtime-friendly but
  do not automatically give type checkers a named concrete component class.
- Subclassing an installed generated class raises ownership questions for
  upgrades, asset retirement, introspection, and eventual uninstall.

### 4.4 Falsifiers

H1 does not advance if any of these are true in the common Phase 7 suite:

- styled and headless forms need duplicated state, focus, keyboard, Events, or
  cleanup implementations;
- ordinary brand adaptations require private DOM selectors;
- headless slot data cannot describe all required elements, relationships,
  handlers, state, and focus targets without exposing private machinery;
- static controls load client behavior solely because their styled and
  headless implementation is paired;
- a useful route must load the whole catalog's CSS or JavaScript;
- the typed handle cannot support annotations, Python composition,
  introspection, and a documented extension alternative.

## 5. Hypothesis H2: installed styled, source-owned headless

### 5.1 Shape

`citry-ui` installs the styled default assemblies. A generator or source export
places a custom headless assembly in the application, where the application
owns markup and styling. Generated files retain provenance and a compatibility
declaration for the library version from which they came.

Two variants must be kept distinct:

- copied behavior, where the application owns behavior as well as markup;
- copied assembly, where application-owned markup still depends on a stable
  installed behavior kernel.

The first maximizes local control but also maximizes drift. The second is close
to H3 and must not be marketed as dependency-free source ownership.

### 5.1.1 Concrete H2 example

Tabs makes the distinction clearer than the intentionally static Button
probe. A generated application assembly might look like this:

```text
Installed distribution
  citry_ui/components/tabs/
    kernel.py                 typed state, roving focus, activation, cleanup
    behavior.js              installed browser behavior
    styled.html              installed default assembly
    styled.css               installed default theme

Application source
  myapp/ui/tabs/
    __init__.py              per-Citry AppTabs factory
    tabs.html                application-owned elements and parts
    tabs.css                 application-owned theme
    citry-ui-origin.json     source version and compatibility metadata
```

The application-owned class is still created for its receiving engine:

```python
from citry import Citry, Component
from citry_ui.components.tabs import TabsKernel


def create_app_tabs(app: Citry) -> type[Component]:
    class AppTabs(TabsKernel, Component):
        citry = app
        name = "AppTabs"
        template_file = "tabs.html"
        css_file = "tabs.css"

    return AppTabs
```

The two H2 variants have different upgrade behavior:

```text
Copied behavior

citry-ui 1 export -> app Python + behavior.js + HTML/CSS
citry-ui 2 fix   -X-> existing app copy receives no runtime fix

Copied assembly over installed kernel

citry-ui 2 kernel + behavior.js -> app-owned HTML/CSS assembly
                                  (keeps the runtime dependency)
```

In the second variant, focus and activation fixes can arrive through the
installed kernel. Element choice, IDs, ARIA references, form controls, focus
targets, and part topology still live in the application assembly and may
require a source merge. This is why the variant overlaps H3 mechanically but
does not equal H3's installed defaults plus optional ownership.

### 5.2 Strengths

- Headless consumers can change markup and parts without waiting for a new
  library hook.
- Application code makes the customization boundary explicit and inspectable.
- Unused generated components add no package registration or asset cost.
- The model is familiar to users of source-copy component systems.

### 5.3 Risks and likely complaints

- Accessibility and security fixes become application merge work when
  behavior is copied.
- Generated markup and installed styled components can drift into two APIs.
- The package must support provenance, regeneration, conflict handling,
  migrations, and compatibility diagnostics, not just a copy command.
- Local changes make support reports difficult to reproduce.
- Copying every requested component can turn framework upgrades into repeated
  manual review.
- A generator adds a toolchain and file-ownership product even if consumer
  runtime still needs no Node.

These risks directly match recurring complaint patterns BSR-1, BSR-2, CZA-2,
PCP-4, and PCP-5 in the [complaint register](complaint-register.md).

### 5.4 Falsifiers

H2 does not advance as a primary architecture if:

- a behavior or accessibility fix cannot be detected and migrated across
  locally changed copies;
- generated headless components no longer pass the same conformance suite as
  the installed styled form;
- the generator needs an application-specific compiler or a Node runtime;
- provenance cannot distinguish an unchanged generated file from an
  intentionally edited one;
- common users must choose source ownership merely to perform token, part, or
  slot customization promised by the charter.

H2 remains a useful pressure case even if it fails as the default headless
delivery. It tests whether the installed hypotheses expose enough legitimate
control.

## 6. Hypothesis H3: installed behavior kernel with optional ownership

### 6.1 Shape

`citry-ui` installs stable family behavior and conformance primitives. It also
ships the installed styled assembly and installed renderless headless surface.
Applications may optionally export or generate a reusable application-owned
assembly that continues to depend on the installed behavior kernel:

```text
citry-ui behavior and conformance kernel
  -> installed renderless headless slot/part surface
  -> installed styled assembly plus default theme
  -> optional application-owned assembly
```

Source ownership applies to markup, slots, parts, and local visual choices. It
does not silently fork focus management, keyboard rules, async ordering,
Events integration, or cleanup.

### 6.2 Strengths

- The common path is as direct as H1.
- Accessibility and lifecycle fixes remain centrally upgradeable.
- Advanced consumers can write a custom fill inline or own one reusable
  assembly without copying the hardest behavior.
- The same kernel can drive installed and application-owned assemblies in one
  conformance suite.
- Optional source ownership can be introduced after the installed API proves
  which structural overrides are genuinely needed.

### 6.3 Risks and likely complaints

- Kernel and assembly contracts create more concepts than H1.
- A kernel broad enough for arbitrary assemblies can become an awkward state
  machine API instead of a native Citry component API.
- DOM relationships, focus targets, IDs, portals, and form controls may be too
  structural to split cleanly from behavior.
- Compatibility now spans package version, kernel protocol version, assembly
  provenance, and theme version.
- If exported assemblies rely on private kernel hooks, source ownership is an
  illusion.

### 6.4 Falsifiers

H3 does not advance if:

- the behavior kernel requires raw executable strings, private Alpine state,
  DOM-parent discovery, or a second client tree;
- assembly authors must reproduce focus, keyboard, form, or cleanup rules;
- the kernel API is larger or less stable than the component public API it is
  meant to support;
- installed and exported assemblies cannot pass one behavior suite;
- version skew fails silently rather than producing a deterministic
  compatibility error.

## 7. CSS jobs shared by all hypotheses

CSS is divided by responsibility so customization does not become an all-or-
nothing choice:

| Layer | Responsibility | Headless loading rule | Styled loading rule |
|---|---|---|---|
| Foundation | box sizing, hidden/inert helpers, focus and forced-color primitives when behavior requires them | Load only the minimum behavior-critical subset | Load as the first low-specificity layer |
| Structure | overlay positioning, scroll regions, visually hidden labels, disclosure geometry, required animation containment | Load only when the family contract requires it | Load with the family |
| Theme | typography, spacing, color, radius, elevation, motion, density, and state appearance | Do not load | Load default semantic and component tokens |
| Utilities | opt-in layout and application composition helpers | Optional | Optional |
| Consumer overrides | public tokens, variants, parts, explicit classes, styles, data, ARIA, and slots | Application-owned | Application-owned above the library layers |

Required conventions for the prototype are:

- one documented package prefix for classes, data attributes, custom
  properties, and layer names;
- low-specificity selectors, using `:where()` where support and semantics
  permit;
- logical properties for direction-aware layout;
- public semantic tokens feeding private component tokens;
- stable named parts and state attributes rather than descendant selectors;
- no runtime recipe compiler for the default theme;
- deterministic aggregate and family-level asset measurements;
- no hidden reset that changes unrelated application elements.

Phase 7 must compare at least an aggregate stylesheet and automatic
family-level collection. Manual import ordering is not an acceptable default.

## 8. Web Components comparison

A Web Component build could provide encapsulated elements and cross-framework
reuse, but it would also introduce a second custom-element lifecycle, a second
property/event boundary, Shadow DOM styling and accessibility decisions, and
client-side upgrade timing on top of Citry's server components and ownership
graph.

Web Components may inform these questions:

- public parts and custom-property naming;
- pre-upgrade useful HTML;
- direction and form-associated behavior;
- asset registration and version skew;
- styling boundaries and portal behavior.

They do not advance as the implementation architecture for the first-party
Python library. A future Web Component adapter would have to wrap the same
Citry behavior contracts rather than replace them.

## 9. Provisional package registration contract

The Phase 6 package spike used a package-owned compatibility installer. The
selected core contract replaces that target shape with:

```python
import citry_ui
from citry import Citry

app = Citry(...)
installed = app.register_library(citry_ui)
app.initialize()
```

The returned core handle provides:

- exact-definition lookup of the installed `Component` class for
  introspection and supported runtime extension;
- one generic installation shape without a wrapper dataclass per family;
- no package-global default `Citry` engine.

This is the advanced installation handle from section 3.1. Template tags and
engine-neutral public composition values remain the ordinary consumer APIs.
Exact component-specific call signatures remain an independent typing
enhancement. Specifically:

- a repeated successful call should return the original classes without
  firing registration hooks for those UI classes again;
- two engines should receive distinct classes with matching stable class IDs;
- a name or class-ID collision should leave no package-created class behind;
- a rejected registration should be retryable;
- failed `Citry.initialize()` should release lifecycle ownership and remain
  retryable;
- `Citry.clear()` retires the installation record; runtime uninstall, hot
  replacement, and revocation of externally retained raw classes remain
  follow-up lifecycle work.

## 10. Packaging and compatibility contract

### 10.1 Distribution metadata

The Phase 6 package skeleton uses:

| Field | Contract |
|---|---|
| Distribution | `citry-ui` |
| Import package | `citry_ui` |
| Initial spike version | `0.0.1` |
| Python range | Same floor and ceiling as the compatible Citry line |
| Citry dependency | `citry>=0.3.2,<0.4.0`, widened only after its full matrix passes |
| Type marker | `citry_ui/py.typed` included in wheel |
| Assets | Inline or module-relative templates and prebuilt plain CSS/JavaScript; the static Button probe uses inline template/CSS and no JavaScript |
| Consumer tools | Python installer only; no Node, compiler, CDN, or runtime fetch |

The spike version is not a public stability promise. Production component APIs
start only after their Phase 7 specifications and the Phase 8 decision record.

### 10.2 Release ordering

For a compatible Citry minor line:

1. Citry publishes the required public framework contracts first.
2. `citry-ui` CI tests against the final Citry artifact, not only a workspace
   checkout.
3. `citry-ui` publishes with a lower bound containing those contracts and a
   conservative upper bound.
4. A later Citry release cannot remove the used public contracts while a
   supported `citry-ui` line depends on them.
5. Compatibility widening is a tested `citry-ui` release, never an untested
   metadata edit.

Security fixes that span both distributions publish Citry first, then
`citry-ui`. Documentation states the minimum safe pair.

### 10.3 Upgrade, downgrade, and deprecation

- Upgrades and downgrades replace wheel files only within `citry_ui`; they
  never write into the `citry` namespace.
- Asset names and content hashes must prevent an old page from silently
  executing incompatible new component behavior.
- Registration metadata must eventually record the package and protocol
  version so an already-running engine cannot mix incompatible generations.
- Removing a component name, kwarg, slot, state attribute, token, part, or
  behavior is a public compatibility change.
- Accessibility-driven DOM changes may be necessary, but still require a
  migration note and retained conformance fixtures.
- Deprecations need a warning at the Python registration or render boundary
  plus at least one supported migration window. CSS-only silent deprecations
  are insufficient.
- Uninstall from an environment must remove the `citry_ui` namespace while
  leaving `citry` importable. Runtime deregistration from a live engine is a
  different future contract.

## 11. Phase 6 scenario matrix

The executable spike must classify every row as passed, exposed prerequisite,
or unavailable until multiple real releases exist:

| Scenario | Required observation |
|---|---|
| Clean pip install | Wheel installs into an empty environment with its compatible Citry dependency and imports `citry_ui` |
| Clean uv install | Direct local wheel or published-name flow resolves the same distribution metadata |
| Wheel contents | Python modules, `py.typed`, and every asset actually declared by the catalog are present; no source toolchain or unrelated files ship |
| Offline install | A prepared wheelhouse installs with `--no-index`/offline mode; runtime performs no network fetch |
| Repeat install | Reinstalling the same wheel is deterministic and does not create another import namespace |
| Upgrade/downgrade | Replacement leaves no stale package files; real compatibility claims wait for at least two release artifacts |
| Environment uninstall | `citry_ui` disappears and `citry` remains usable |
| First registration | All expected classes resolve to the returned per-Citry handle |
| Repeated registration | Original installation and class identities are returned; UI-class registration hooks do not refire |
| Concurrent registration | One complete result is published; callers receive the same classes or one documented retry result |
| Two engines | Equivalent classes are distinct objects with distinct engine/definition identity and matching stable class IDs |
| Collision | First, middle, and last name/class-ID conflicts identify the requested and existing registrations without unrelated mutation |
| Registration failure | `Exception` and `BaseException` paths leave no ordinary partial package registration and permit retry |
| Rollback | Citry restores its registration state directly without firing vetoable unregistration hooks |
| Initialization failure | Engine lifecycle is released; retry is possible; the package's committed registration policy is explicit |
| Typed access | Styled/headless references support annotation, Python composition, introspection, and the documented extension path |
| Introspection | Family and mode metadata, installation class order, schemas, asset provenance, and resolved files are deterministic |
| No build runtime | Render and asset loading work with no Node executable, compiler, CDN, or runtime download |

## 12. Quantitative budgets frozen for Phase 7

These began as comparative-prototype budgets and now gate the one styled
production architecture. A budget may change only through a recorded decision
made before the affected implementation increment begins.

### 12.1 Assets and interaction

| Measure | Phase 7 budget |
|---|---:|
| Incremental Brotli CSS for the complete eight-probe route | at most 30 KiB |
| Incremental Brotli JavaScript for the complete eight-probe route, excluding Citry, Alpine, and Events | at most 45 KiB |
| Incremental Brotli assets for a route containing only Button, Field/Input, and semantic Table | at most 12 KiB CSS and 8 KiB JavaScript |
| Semantic Table client work | zero component JavaScript, observers, timers, and global listeners |
| Inactive Button retained work | one shared reactive initializer is allowed; zero observers, timers, document/window listeners, or retained global entries |
| Duplicate family asset execution after fragment insertion | zero |
| First local interaction handler duration in the pinned desktop CI profile | p95 at most 50 ms over 30 measured runs |
| First local interaction handler duration in the pinned mobile-emulation profile | p95 at most 100 ms over 30 measured runs |
| Retained package listeners, observers, timers, requests, or portal entries after removal | zero after the documented cleanup checkpoint |

Raw, gzip, and Brotli sizes are all recorded. The limits apply to Brotli only
because one compression basis is needed for the gate. Interaction timing is
incremental and local; transport latency is measured separately.

The Button row was revised on 2026-07-30 after the production input contract
made `disabled` and `loading` reactive client props. A Button with false server
values can receive either prop later, so the class cannot truthfully promise
zero initialization. The replacement budget limits idle retained work while
keeping semantic Table completely script-free. Conditional per-instance asset
delivery remains a future compiler or runtime optimization, not a hidden
requirement on component authors.

#### 12.1.1 Whole-catalog reconciliation after the seven-family batch

The eight-probe and basic-route budgets above remain route gates. They do not
double as a complete-catalog ceiling. The later 80 KiB Brotli JavaScript and
30 KiB Brotli CSS whole-catalog checks were set against the 2026-08-11
promoted snapshot, before the approved Disclosure, SplitButton, TagsInput,
ScrollArea, ContextMenu, Image, and CommandPalette batch completed. The final
batch falsifies only that aggregate ceiling, not any family-specific,
attributed, standalone, or narrow-route limit.

The immutable pre-batch snapshot without Disclosure contained 93 public
component definitions and 48 unique JavaScript / 54 unique CSS frames:

| Asset | SHA-256 | Raw | gzip | Brotli |
|---|---|---:|---:|---:|
| JavaScript | `b63e9837b956e858cfc96ce9fa5d345ab08adf39fe1b6eee746daa5de2f24980` | 631,952 | 111,715 | 77,389 |
| CSS | `31d68dfe59ff9ce13990a0e12da514ad0518bf6c450f45c33e9946192f04dd68` | 261,668 | 31,676 | 25,072 |

Shared Dialog, collection, anchored-layer, geometry, form, and lifecycle
foundations continued to evolve while the batch was implemented. Rebuilding
the current catalog with all seven new public roots excluded measures that
foundation change separately as +73,521 / +13,680 / +11,869 JavaScript and
+4,454 / +603 / +456 CSS bytes. Adding the final public roots in the approved
order produces these positive whole-catalog marginals. Compression is
recomputed over the complete ordered unique frame set after each addition;
the numbers are therefore catalog marginals, not sums of independently
compressed frames.

| Family | JavaScript raw/gzip/Brotli | CSS raw/gzip/Brotli |
|---|---:|---:|
| Disclosure | +26,797 / +5,483 / +3,586 | +8,060 / +575 / +391 |
| SplitButton | +11,340 / +2,146 / +1,403 | +2,108 / +343 / +136 |
| TagsInput | +10,546 / +3,616 / +3,245 | +4,464 / +682 / +545 |
| ScrollArea | +6,648 / +2,585 / +2,215 | +3,929 / +435 / +351 |
| ContextMenu | +27,160 / +8,709 / +7,182 | +440 / +57 / +48 |
| Image | +27,668 / +5,691 / +4,410 | +2,640 / +340 / +293 |
| CommandPalette | +38,166 / +7,522 / +4,378 | +9,715 / +1,166 / +949 |

The final 101-definition catalog contains 62 unique JavaScript and 62 unique
CSS frames. Newline-framed canonical measurements are:

| Asset | SHA-256 | Raw | gzip | Brotli |
|---|---|---:|---:|---:|
| JavaScript | `65ca8587e1d6e54bbb8d0d414fe8a72673bce85b0ebaab02a7ad4108b9ef28b8` | 853,798 | 161,147 | 115,677 |
| CSS | `f2806359ebdf9751cbf33ccc0b3afcfa9180aabebdb879f70be117ec3ade527e` | 297,478 | 35,877 | 28,241 |

The reconciled whole-catalog limits are less than 960 KiB raw / 192 KiB gzip
/ 128 KiB Brotli JavaScript and less than 336 KiB raw / 40 KiB gzip / 32 KiB
Brotli CSS. They leave 129,242 / 35,461 / 15,395 JavaScript bytes and 46,586
/ 5,083 / 4,527 CSS bytes of headroom. The smallest margin is 11.75% of its
round ceiling for JavaScript and 12.41% for CSS. Every dimension is frozen so
a favorable aggregate compression change cannot hide raw or alternate-codec
growth.

This is a secondary worst-case catalog guard. A family change must still pass
its own attributed or incremental ceiling, complete standalone ceiling where
specified, exact frame/provenance assertions, deduplication checks, and the
basic action/form/table route budget. Aggregate shrink in another family never
offsets those gates. A future legitimate catalog overage requires another
recorded reconciliation with exact current frames, intervening family deltas,
and independent asset review rather than an unreviewed constant increase.

### 12.2 Customization and visual coverage

| Measure | Phase 7 budget |
|---|---:|
| Publicly documented token coverage for library-owned color, typography, spacing, radius, elevation, density, and motion choices in the slice | 100% |
| Undocumented selectors or internal DOM queries needed by either required brand theme | zero |
| Consumer `!important` declarations needed by either required brand theme | zero |
| Selector specificity above one package class or state attribute plus one documented part | zero without a recorded accessibility or browser justification |
| Frozen styled states, variants, sizes, densities, responsive modes, dark mode, RTL mode, and error states represented by scenarios and docs live examples | 100% |
| Screenshot maximum differing-pixel ratio in pinned browser images | 0.1% after masking only genuinely nondeterministic content |
| Required theme and coexistence fixtures | default light, default dark, two brand themes, plain CSS, Bootstrap, and Tailwind |

Screenshot comparison also uses a fixed per-pixel threshold recorded beside
the baseline. A screenshot budget never replaces semantic, accessibility, or
focus assertions.

### 12.3 Registration, lifecycle, and accessibility

| Measure | Phase 7 budget |
|---|---:|
| Required package registration and asset scenarios passing | 100% |
| Required styled production component conformance cases passing | 100% |
| Automated axe violations at serious or critical impact | zero |
| Nu HTML validation errors caused by library output | zero |
| APG keyboard cases in the supported mode matrix | 100% |
| Required focus, edit, identity, form, morph, portal, async-ordering, and cleanup cases | 100% |
| Lighthouse accessibility score on frozen representative complete pages | 100 as a regression smoke gate, not a conformance claim |

A missing framework prerequisite is not counted as a passing component case.
If ambient context, publishing, morphing, or cleanup cannot meet a required
case, the affected hypothesis pauses until the framework contract is fixed or
the component scope is narrowed.

## 13. Original executable spike, retained as historical evidence

This section records the original Button-only helper and package experiment.
Its constructors, facades, flat references, caches, and package-owned
registration logic were superseded by the core publishing API. They are kept
only to explain the evidence that caused that replacement. Current behavior is
specified in [`component_publishing.md`](../component_publishing.md), and the
fresh multi-family result is in section 15.

The original architecture-neutral skeleton lived at
[`packages/py/citry_ui`](../../../packages/py/citry_ui) and deliberately used
one probe family rather than pretending Phase 7's component work was complete.
That historical probe was enough to exercise:

- a real `citry-ui` distribution and `citry_ui` import namespace;
- the then-current workspace-only dependency placeholder, which did not count
  as compatibility evidence before Citry 0.3.0 was released;
- inert import and explicit per-Citry registration;
- an explicit component-family catalog, generic registration plumbing, thin
  package installation layer, and flat class references;
- a true renderless `CButtonHeadless` that exposes typed bindings through its
  required scoped slot, plus a styled `CButton` that consumes that contract;
- direct registered-tag rendering, explicit `CButton(...).render(citry=app)`,
  and a deterministic error for context-free imported composition;
- family-local inline templates and styled-only CSS in a cascade layer; the
  static Button declares and executes no component JavaScript;
- exact typed public invocations plus access to the real `type[Component]`;
- first, repeated, recursive, concurrent, two-engine, clear/reinstall, stale
  canonical-name, name and class-ID collision, atomic rollback,
  failed-initialization, styled and headless rendering, public composition,
  typing, introspection, and distribution-resource cases.

The probe names and button markup are not proposed public component APIs. They
exist to validate the distribution and engine contracts before the shared
Phase 7 slice freezes an API.

### 13.1 Registration behavior observed

Twenty-eight focused source cases passed on Python 3.13:

| Scenario | Result | Interpretation |
|---|---|---|
| Inert import | Pass | Importing `citry_ui` registers no component in Citry's default engine |
| First registration | Pass | The returned classes resolve under the two names and belong to the receiving engine |
| Repeated registration | Pass | New immutable references point to the same class objects and registration hooks for those UI classes do not fire again; caches are isolated by catalog key and spec signature |
| Independent generic catalogs | Pass | Custom-first and UI-first installation orders construct both named catalogs exactly once |
| Concurrent package call | Pass with retry result | A competing caller receives `CitryUIRegistrationInProgress`; after the owner completes, retry returns the committed classes |
| Recursive package call | Pass with retry result | A registration hook that re-enters the helper receives `CitryUIRegistrationInProgress` rather than waiting on the package mutex |
| Two engines | Pass | Class objects, engine IDs, and definition IDs differ; corresponding stable class IDs match |
| `Citry.clear()` then register | Pass | Cached weak references are rejected through public class-ID lookup and a fresh per-Citry class generation is created |
| Canonical name removed while alias remains | Pass | Cached class identity alone is not accepted; a retry detects the occupied class ID and raises a dedicated collision error |
| Name collision on first or last probe class | Pass | A dedicated collision error is raised and no package-created sibling remains |
| Class-ID collision on first or last probe class | Pass | A class registered under an unrelated name is still detected by stable ID, and an earlier package-created sibling is rolled back |
| Registered-hook `Exception` | Pass | Citry restores the successful earlier registration and the operation can retry |
| Registered-hook `BaseException` | Pass | Citry restores the full group and preserves the original failure |
| Unregistration hook rejects cleanup | Pass | Atomic rollback restores Citry-owned state directly and never calls the rejecting cleanup hook |
| Failed built-in initialization | Pass | Committed package classes remain available by their per-Citry class IDs, lifecycle ownership is released, and initialization retries |
| Direct template composition | Pass | `<c-CButton>` resolves the registered styled class for that Citry instance and renders without importing an installation handle |
| True headless assembly | Pass | `<c-CButtonHeadless>` renders only the consumer fill; its scoped data carries native attributes and state, and it loads no styled asset or JavaScript |
| Python composition | Pass | `CButton(...).render(citry=app)` and contextual `{{ button }}` rendering both use the exact class installed for the rendering Citry instance through `ComponentLike` |
| Runtime subclass and foreign-engine rejection | Pass | Same-engine subclassing works; another engine rejects the resulting concrete class |
| Asset and introspection resolution | Pass | Each mode resolves its own inline template, neither declares JavaScript, styled CSS resolves only for styled, and catalog order is canonical |

Cached canonical-name validation uses Citry's public `get()` API rather than
private registry state. If an application makes an unusual second package
call before its explicit `initialize()`, that lookup can complete Citry's
normal lazy discovery and built-in registration. It does not refire UI
registration hooks. A future engine-owned package identity should make
side-effect-free installed-bundle validation possible.

Citry now prevents competing threads from seeing an in-progress registration
group and restores engine-owned registration state without compensating public
unregistration hooks. A public release still requires package identity,
dependency requirements, uninstall, replacement, and transactional extension
notification contracts.

### 13.2 Wheel and installer behavior observed

The revised family-local 0.0.1 wheel was built and exercised with a locally
built development Citry artifact in a fresh Python 3.13 environment. At the
time, this did not establish compatibility with the published Citry 0.2.0
artifact. Citry 0.3.0 has since supplied the compatible floor. An
earlier synthetic upgrade experiment used the superseded
external Button asset layout. It is excluded from evidence for the revised
package rather than carried forward as if the artifacts were equivalent:

| Scenario | Result | Evidence boundary |
|---|---|---|
| Wheel build | Pass | Setuptools produced `citry_ui-0.0.1-py3-none-any.whl` |
| Wheel inventory | Pass, refreshed 2026-07-23 | The expanded pure wheel has 16 entries: 11 `citry_ui` source/type-marker files and five own dist-info/license entries; it contains no generated client assets or source toolchain |
| Namespace isolation | Pass | No path in the wheel writes into `citry/**` |
| Clean/offline pip install | Pass for local artifacts | `python -m pip` in a fresh standard-library venv installed locally built Citry Core, development Citry, Citry UI, and three Python dependencies from a prepared wheelhouse with index access disabled; testing the released 0.3.0 floor remains a refreshed fixture |
| Repeat same-wheel install | Historical pass for the Button-only artifact | The expanded 16-entry wheel still needs the isolated repeat-install and fingerprint fixture rerun before release evidence is current |
| Isolated runtime | Pass | An installed-wheel smoke test imported, registered, initialized, rendered styled and consumer-owned headless markup, and resolved the public `CButton` with an explicit engine |
| No-Node runtime | Pass | The same render succeeded with an otherwise empty environment whose `PATH` contained only the consumer virtual environment and no `node` executable |
| Upgrade/downgrade replacement | Unavailable for the revised layout | The older synthetic experiment is superseded; two revised artifacts have not been built and compared |
| Environment uninstall | Pass | `citry_ui` metadata and imports disappeared while the separately installed `citry` remained importable |
| Offline uv add | Pass | A standalone no-workspace project added direct `citry` and `citry-ui` dependencies from the wheelhouse |
| Offline uv upgrade/downgrade | Unavailable for the revised layout | Resolver selection passed only for the superseded synthetic pair and is not counted here |
| Offline uv remove | Pass | After resync against the wheelhouse, `citry_ui` disappeared and direct `citry` remained installed |

The consumer interpreter had to be pinned to Python 3.13 because the prepared
`citry-core` wheel is ABI- and platform-specific. An initial unpinned uv
consumer selected Python 3.14 and correctly rejected that wheel. This is not a
`citry-ui` pure-wheel failure, but it proves that the release wheelhouse and CI
matrix must align the consumer interpreter, platform, and Citry Core artifact.

Replacement and stale-file cleanup remain unavailable until two revised
release artifacts and their migration fixtures exist.

### 13.3 Typing behavior observed

The source contract passed mypy and pinned pyright. Exact public facades reject
invalid component keywords, invalid value types, unknown slot names, and slot
callbacks with incompatible data contracts.

The public and advanced surfaces deliberately have different typing jobs:

- `CButton(...)` and `CButtonHeadless(...)` are thin, component-specific
  facade functions. Their explicit signatures produce a generic
  `ComponentInvocation` without defining fake engine-neutral component
  classes.
- `UIComponents.cbutton` and `UIComponents.cbutton_headless` are generic
  `CompRef` values for introspection and advanced composition. Their
  `component_class` fields are the real per-Citry `type[Component]` values.

Runtime slot schemas remain dataclasses because Citry uses them to parse and
validate template slots. Call-site slot fills use component-specific
`TypedDict` types, so a dictionary literal such as
`slots={"default": callback}` is checked structurally instead of requiring the
caller to construct a slot-schema dataclass.

Contextual interpolation of `ComponentInvocation` now uses Citry's public,
structural `ComponentLike` protocol. Standalone calls still require an
explicit Citry instance, so no process-global engine is inferred.

Directly subclassing the dynamic `component_class` works at runtime but is not
a portable statically typed class-base expression. Phase 7 must compare a
typed extension factory or mixin callback if supported customization needs
more than tokens, parts, slots, and ordinary composition. A `.pyi` file must
not invent import-time global component classes, because those classes would
violate Citry's engine ownership model.

### 13.4 Transitional scenario classification, now historical

This table captured the expanded catalog while it still used the removed
package helper. Every row in this subsection is historical, including rows
that mention 16 definitions. Current publishing and pressure-catalog evidence
begins in section 15.

This table closes every row frozen in section 11. A pass is limited to the
mechanism actually exercised. An unavailable or prerequisite result is not
silently counted toward the Phase 7 requirement of 100% passing cases.

| Frozen scenario | Classification | Evidence or remaining obligation |
|---|---|---|
| Clean pip install | Pass for local artifacts | A fresh Python 3.13 standard-library venv installed the wheel and locally built development Citry dependency with `python -m pip`, then imported and rendered the styled probe; the now-released 0.3.0 floor still needs a refreshed isolated fixture |
| Clean uv install | Pass for local artifacts | A no-workspace project resolved direct `citry` and `citry-ui` dependencies from the prepared development wheelhouse |
| Wheel contents | Pass, refreshed 2026-07-23 | The 16-entry pure wheel contains only 11 `citry_ui` source/type-marker files and five own dist-info/license entries; family assets remain inline and no build toolchain ships |
| Offline install | Pass | Both pip and uv installations completed from local artifacts with index access disabled; runtime performed no fetch |
| Repeat install | Historical pass; expanded wheel rerun required | The Button-only artifact preserved one namespace and fingerprint; repeat-install evidence must be refreshed for the expanded catalog |
| Upgrade/downgrade | Unavailable for the revised layout | The superseded external-asset experiment is excluded; replacement, stale-file cleanup, and compatibility need two revised release artifacts and migration fixtures |
| Environment uninstall | Pass | `citry_ui` was removed while the separately installed `citry` remained importable |
| First registration | Pass | All 16 per-Citry classes resolve through the returned handle and canonical names |
| Repeated registration | Pass | The original class identities return without refiring UI registration hooks |
| Concurrent registration | Pass with documented retry | A competing caller fails fast with `CitryUIRegistrationInProgress`; retry returns the committed classes |
| Two engines | Pass | Corresponding classes have distinct object, engine, and definition identities with matching stable class IDs |
| Collision: first/last name and class ID | Pass | Occupied canonical names and unrelated classes with matching IDs are detected; any earlier package-created class is removed |
| Collision: middle of a larger bundle | Available in the expanded pressure catalog | Button, Field/Input, Table, and Tabs now create a 16-class catalog; first, middle, and last injected failures remain a final focused matrix item |
| Registration failure | Pass | Both `Exception` and `BaseException` hook failures clean ordinary partial state and allow retry |
| Cleanup failure | Pass for Citry-owned registry state | `Citry.atomic_registration()` restores the captured registry state directly, so unregister hooks cannot veto rollback; extension-owned side effects remain outside its scope |
| Initialization failure | Pass | A failed built-in initialization releases lifecycle ownership, preserves committed UI classes, and succeeds on retry |
| Typed access | Exposed framework and extension obligations | Exact component facades, explicit invocation resolution, contextual `ComponentLike` interpolation, flat installed references, annotation, introspection, and runtime subclassing pass; a portable typed library-definition and extension model remains future work |
| Introspection | Pass for the current scope | Canonical names, flat handle order, separate styled/headless schemas, asset provenance, and files are deterministic; richer versioned family and partner metadata is deferred until a concrete consumer requires it |
| No build runtime | Pass | Isolated rendering and asset loading succeed with no Node executable, compiler, CDN, or network access, and the static Button emits no component JS |

## 14. Phase 6 advancement decision and Phase 7 resolution

The executable gate passed for comparative prototyping. Citry now supplies the
small atomic registration primitive the package needs, while the broader
package-lifecycle contract remains future work:

The required usage patterns materially narrow the architecture, but do not
fully choose H1 over H3. Direct tags, engine-neutral Python invocations, true
renderless components, flat advanced references, and family-local authoring
are cross-cutting public and maintainer contracts. They rule out an API built
around importing an installation handle into every component module. They also
make copied-behavior H2 less attractive. H2's more viable assembly-over-kernel
form is mechanically close to H3.

`CButton` proves the installed styled/renderless pair and the authoring layout.
It does not have enough behavior to prove that an independently useful H3
kernel can stay smaller and more stable than its assemblies. Phase 7 must make
that comparison with Tabs, Dialog, or Combobox, where focus, identity,
keyboard, and cleanup contracts create real pressure.

- **H1 advances** because it gives the styled default and headless surface one
  upgrade, conformance, and support path.
- **H3 advances** because it tests whether optional source ownership can be
  added above a stable installed behavior kernel without forking difficult
  behavior.
- **H2 remains a mandatory pressure case but does not advance as a primary
  implementation.** Its copied-behavior form fails the evidence-derived
  upgrade and drift burden before a prototype can justify that cost. Its
  installed-kernel form is represented by H3.

That was the Phase 6 conclusion. Phase 7 now advances one public publishing and
authoring architecture: styled `LibraryComponent` definitions in the separate
`citry-ui` package. It does not implement the eight probes twice. Headless H1,
H2, and H3 work is parked until real application usage identifies an API worth
supporting and representative pages make its performance costs measurable.

The following work remains before a public `citry-ui` release:

1. Real installation, multi-release upgrade, downgrade, retained-page, and
   deprecation fixtures for the `citry>=0.3.2,<0.4.0` line after its release.
2. Atomic live uninstall and hot replacement only if the product requires
   them; additive publication, preflight, collision handling, repeated
   registration, concurrent visibility, and rollback are implemented.
3. Versioned UI family/mode/partner metadata in introspection, if a concrete
   consumer cannot obtain it from the library definition map, without
   requiring an extension to be installed after `Citry` construction.
4. Production-family verification of the implemented client ambient-context
   contract across slots, teleports, morphs, updates, defaults, cleanup, and
   diagnostics.
5. The complete Phase 7 accessibility, browser, forms, lifecycle, security,
   styling, visual, and asset-budget suite.

## 15. July 2026 pressure-batch evidence

The Phase 6 spike now includes 16 component definitions across four family
modules. This expansion is intentionally broader than the original Button
packaging proof and narrower than the complete Phase 7 slice.

### 15.1 ComponentLike result

Citry now exports the runtime-checkable `ComponentLike` protocol. A value
implements `__citry_element__(citry)` and may render through `{{ ... }}`, a
static or callable Slot, and plain or generator `on_render` replacement.
Resolution is one step, uses the exact rendering Citry instance, rejects a
foreign-engine element, preserves provide/inject and dependency collection,
and has no global fallback outside a render.

Core `LibraryComponentInvocation` implements this protocol for Citry UI.
Imported calls such as `CButton(...)`, `CInput(...)`, and `CTable(...)` compose
normally in Python while collision-safe resolution uses Citry's exact
per-library definition map rather than a same-named registry entry.

### 15.2 Added pressure families

This table records the Phase 6 pressure state. The styled Tabs row was
superseded on 2026-07-29 by the Phase 7 production specification and first
interactive increment in [`../ui_components/tabs.md`](../ui_components/tabs.md).

| Family | Implemented evidence | Explicitly unproven |
|---|---|---|
| Field plus Input | Separate styled/headless schemas, stable label/control/description/error IDs, persistent polite error region, native form attributes, tri-state Field inheritance, open-attribute precedence, and `ComponentLike` returned from a scoped slot callback | Focus, caret, autofill, native reset, validity, live-region timing, and Events morph preservation in browsers |
| Semantic Table | Validated keyed columns and rows, semantic table/header/cell output, row headers, explicit rejection of unvalidated spans, ready/loading/error states, repeated scoped slots, nested `ComponentLike` cell values, and zero JavaScript | A validated logical span grid, large-data performance, fragment row replacement, and visual/browser matrix |
| Tabs | Eight compound styled/headless definitions, one accessibly named TabList, enforced TabList ownership, explicit values, stable paired ARIA IDs, initial selection, disabled-selection rejection, duplicate and missing-pair rejection after descendants settle, orientation/direction metadata, and zero unclaimed JavaScript | Keyboard navigation, activation modes, focus ownership, dynamic removal, client/server state, morph preservation, and cleanup |

Tabs began server-first on purpose. Its first production interaction was added
only after the specification and Chromium, Firefox, and WebKit behavior tests
existed. The remaining release matrix stays open in the component spec.

### 15.3 Constraints exposed

1. `c-slot` uses `name`, `required`, and `c-bind` as control inputs. Passing a
   scoped-data mapping with a `required` key changes slot behavior instead of
   exposing data. The public Field/Input slot contracts therefore use
   `is_required`, `is_disabled`, and `is_invalid`. A future slot-data namespace
   or explicit data channel would remove this avoidable naming constraint.
2. The original explicit constructor, spec, installation-reference, and typed
   facade work grew linearly with every definition. The 16-class catalog
   justified moving those responsibilities into the core publishing API.
3. Styled composition over headless definitions worked for the Phase 6 server
   pressure case. Phase 7 parked that comparison and the production styled
   Tabs now owns its DOM and client behavior directly.
4. Compound validation can observe descendants only after they render. The
   Tabs probe uses a render-local mutable registry carried inside an immutable
   provided payload, then validates it in generator `on_render`. This is
   acceptable for falsification, but it should not become the public client
   state model.

### 15.4 LibraryComponent feasibility

The two-stage model is implemented: inert `LibraryComponent` definitions
become concrete per-Citry `Component` classes inside
`Citry.register_library(...)`, while calling a definition produces a generic
`ComponentLike` invocation. Handwritten catalog keys are replaced by explicit
definition objects plus validated module and qualified-name identities.

The executable multiple-inheritance probe and focused core falsifier suite
pass. ComponentMeta preserves
authored nested declarations, normalizes inherited raw `Kwargs` and `Slots`,
and gives extensions their exact C3-ordered source records. Generic extension
configs, Events, State, and Dependencies consume that shared contract with
their appropriate inheritance policies. Cross-branch core schemas validate
adapter compatibility, and concrete nested declarations are immutable after
materialization. Citry-owned installation state commits inside the same
lifecycle operation as its component classes, rolls back on `BaseException`,
retires on `clear()`, and rejects a reloaded definition generation while the
old generation remains active. Exact mypy/pyright component-call signatures
remain an optional follow-up rather than a runtime publishing gate.
The complete proposed API and falsifier suite are in
[`library-component-feasibility.md`](library-component-feasibility.md).
Citry UI now defines all 16 pressure components directly as
`LibraryComponent` classes and publishes one `ComponentLibrary`. The package
does not retain compatibility adapters for the unpublished spike API. Runtime,
typing, manifest, rollback, component-family, and packaging tests exercise the
core API directly.
