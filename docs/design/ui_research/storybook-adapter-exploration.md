# Storybook adapter exploration for Citry UI

**Status (2026-07-25): static comparison and first interactive slice complete;
no adapter selected.** Both candidate adapters can preview the current
server-static Citry UI scenarios and the private reactive readiness probe,
accept useful Controls, activate Citry CSS and JavaScript, cleanly replace the
probe, expose standalone pages, and produce a static Storybook build. The
remaining interactive browser-readiness scenarios remain the selection gate.

This report implements the first half of the adapter gate defined in
[`scenario-catalog.md`](scenario-catalog.md). The disposable implementation is
in [`packages/py/citry_ui/storybook`](../../../packages/py/citry_ui/storybook/).

## 1. Scope and role

Storybook is evaluated as Citry UI's maintainer previewer. It browses isolated
component states, changes Args through Controls, shows authored usage, and
offers preview diagnostics. It does not run the catalog's Playwright journeys
and is not the canonical conformance, accessibility, visual-regression, or
performance runner.

A preserved direct Playwright smoke verifies the adapters themselves: preview
mounting from built output, manager Control replacement, CSS and JavaScript
readiness, exact cleanup, stale physical-listener disposal, and visible backend
failure. Additional manual browser inspection covered addon visibility and
autodocs behavior. The same Python scenario catalog also renders complete
standalone pages for later Playwright, Lighthouse, assistive-technology, and
performance work. No separate gallery is proposed.

The production-facing pressure components still contain no Citry UI client
JavaScript, and Tabs remains server-selected and inert. A private reactive
counter now supplies the first client-active framework proof. It does not
establish Events, morphing, teleports, remote-request protection, or the
cleanup requirements of those more demanding cases.

## 2. Version and environment snapshot

The spike pins the following exact versions:

| Tool | Version |
|---|---:|
| Storybook | 10.5.4 |
| `@storybook/server-webpack5` | 10.5.4 |
| `@storybook/server` | 10.5.4 |
| `@storybook/html-vite` | 10.5.4 |
| `@storybook/addon-a11y` | 10.5.4 |
| `@storybook/addon-docs` | 10.5.4 |
| Vite | 8.1.5 |
| Node used for the spike | 25.8.1 |
| pnpm used for the spike | 10.32.1 |

The published HTML/Vite package accepts Vite 5 through 8. Both framework
packages remain published in lockstep with Storybook 10.5.4. HTML and Server
are nevertheless absent from Storybook's current primary supported-framework
and feature-support tables, while the framework-author guide still recommends
`@storybook/html` as the simplest renderer starting point. This is a support
signal, not evidence that either package is abandoned.

Primary sources:

- [Server/Webpack package manifest](https://github.com/storybookjs/storybook/blob/v10.5.4/code/frameworks/server-webpack5/package.json)
- [HTML/Vite package manifest](https://github.com/storybookjs/storybook/blob/v10.5.4/code/frameworks/html-vite/package.json)
- [current framework feature table](https://storybook.js.org/docs/configure/integration/frameworks-feature-support)
- [framework-author guidance](https://storybook.js.org/docs/10.5/api/new-frameworks)

## 3. Shared Python source and runner

Both adapters consume five ordered Python scenarios:

| Stable ID | Subject | Controls | Important pressure |
|---|---|---|---|
| `button/static` | Button | label, loading, disabled, native type | native semantics and visible state |
| `field/static` | Field and Input | label, value, required, disabled, readonly, invalid, orientation, density | composition and ARIA relationships |
| `table/static` | Table | state, density, striped, hover, sticky header | nested Button and server states |
| `tabs/server-selected` | Tabs family | selected value, orientation, direction, activation metadata | compound structure and paired ARIA IDs |
| `readiness/reactive-state` | Private reactive counter | generation | fragment CSS/JS readiness, browser-local state, replacement, and cleanup |

The private runner:

- creates a fresh `Citry(autodiscover=False)` engine;
- registers `citry_ui` and a private scenario-helper component library;
- leaves the module-level default Citry registry untouched;
- exposes only explicit catalog, fragment, and complete-page routes;
- strictly rejects unknown, repeated, or incorrectly typed Args;
- binds through the contributor command to loopback;
- accepts only the enumerated loopback Storybook Hosts and Origins, with both
  proxies validating the incoming authority before rewriting the backend Host
  and the outer ASGI mount applying the policy to every `/citry/**` route;
- returns no-store responses and never enables credentialed wildcard CORS;
- serializes static fragments with Citry's `simple` dependency strategy and
  interactive fragments with the `fragment` strategy, so the latter carry the
  real Citry ownership graph and dependency manifest;
- mounts the ASGI application at `/citry` and uses that same-origin route for
  scenarios, the client runtime, extension assets, and component assets; and
- stays outside the `citry_ui` package selected by setuptools, so it cannot
  enter the wheel.

Generated Server JSON and HTML CSF are deterministic projections. A stale-file
check compares every committed output with the Python catalog. Both projections
carry the same title, stable ID, Args, `argTypes`, description, authored Python
usage, catalog schema version, generator version, and source digest. They
contain no copied implementation HTML and no Playwright journeys.

The implemented model is intentionally smaller than the accepted final
scenario contract. It proves the transport and projection shape without
prematurely implementing run records, server-fixture setup and teardown,
profiles, Events, authorized diagnostics, or host aggregation.

The contributor commands synchronize a private `storybook` Python dependency
group, so they do not depend on an already-prepared repository environment.
The principal reproducible checks are:

```sh
uv run --no-sync pytest packages/py/citry_ui/tests/test_storybook_spike.py -q
pnpm --dir packages/py/citry_ui/storybook run smoke
```

The Python test exercises every Control independently, checks semantic output
changes, drives the real ASGI route matcher and response headers, verifies the
shared projection model, and confirms default-engine isolation. The Chromium
smoke rebuilds both Storybooks and checks their built applications with and
without the live backend. It also runs the private reactive probe as a complete
standalone page. It remains an adapter check, not a component journey runner.

## 4. Measured static results

| Check | Server/Webpack | HTML/Vite |
|---|---|---|
| Exact five-story index | Pass | Pass |
| Default preview for all four scenarios | Pass | Pass |
| Text, boolean, and select Args | Pass | Pass |
| Manager Controls trigger a new Python render | Pass | Pass |
| Citry UI CSS active in Canvas | Pass | Pass |
| Unknown and invalid Args rejected | Pass | Pass |
| Nested Button inside Table | Pass | Pass |
| Accessibility addon inspects the mounted Button | Pass: 0 violations, 8 passes | Pass: 0 violations, 8 passes |
| Authored description and ArgTypes in autodocs | Pass | Pass |
| Live component inside autodocs Canvas | Missing | Pass |
| Authored Python source included in built story metadata | Pass | Pass |
| Static Storybook build | Pass | Pass |
| Built stories work with backend reachable | Pass | Pass |
| Built stories self-contained without backend | No | No |
| Backend absence is visibly reported | Pass, generic Storybook render error | Pass, generic Storybook render error |
| Citry client activation and cleanup | Not exercised | Not exercised |

The accessibility panel result proves that the addon can reach the current
mounted Button. It does not establish the Button's accessibility conformance or
replace axe, keyboard, screen-reader, forced-color, and cross-browser gates.
Storybook documents that its accessibility addon runs axe against the rendered
story; Citry keeps that result as maintainer feedback only. See Storybook's
[accessibility documentation](https://storybook.js.org/docs/writing-tests/accessibility-testing).

The static builds bundle Storybook and the generated adapters, not rendered
Python output. Opening any live story still fetches the Citry service. This
matches Storybook's model of publishing the built Storybook application, but
means deployment requires a reachable protected scenario service, a deliberate
reverse proxy, or a separately designed frozen-output mode. See Storybook's
[publishing documentation](https://storybook.js.org/docs/sharing/publish-storybook).

Build size warnings are contributor-tool observations, not application payload
budgets. With Docs and accessibility enabled, Webpack reported an 830 KiB
preview chunk and a 1.54 MiB chunk. Vite reported an approximately 871 KiB
preview chunk, 579 KiB axe chunk, and 370 KiB Docs renderer before gzip. None of
these assets ship in the Citry or Citry UI wheels.

### 4.1 Measured first interactive results

Both project previews now install a Citry-owned `renderToCanvas` lifecycle
adapter around their framework-specific fetch path. Server/Webpack starts its
generation before fetching; HTML/Vite's loader uses Storybook's abort signal,
then starts the Canvas generation when the loaded result reaches the renderer.
The lifecycle adapter rejects a stale or aborted result, initializes the
candidate inside a hidden connected root, recreates fragment bootstrap scripts,
and waits for the scenario's machine-readable readiness selector. Only then
does it dispose the previous Alpine tree and promote the candidate. The Python
service is mounted at `/citry`, and both development and built-output checks
proxy that path through the Storybook origin.

| Check | Server/Webpack | HTML/Vite |
|---|---|---|
| Private fragment reaches declared readiness | Pass | Pass |
| Component CSS is applied before readiness | Pass | Pass |
| Component JavaScript initializes once | Pass | Pass |
| Browser click mutates local reactive state | Pass | Pass |
| Generation Control replaces the fragment | Pass | Pass |
| Delayed candidate stays hidden while current content remains visible | Pass | Pass |
| Failed candidate cleans up, retains the last good DOM, and shows an error | Pass | Pass |
| Aborted slow response never initializes | Pass | Pass |
| First component cleanup runs exactly once | Pass | Pass |
| One component and one window listener remain | Pass | Pass |
| Removed physical button is inert | Pass | Pass |
| Replacement reports no Alpine expression error | Pass | Pass |
| Story navigation cleans up the active generation | Pass | Pass |
| Proxy rejects an untrusted incoming Host | Pass | Pass |
| Complete standalone page activates and cleans up | Pass | Pass |
| Built preview reports a stopped backend | Pass | Pass |

The browser pressure pass exposed two core requirements. First, assigning
`innerHTML` does not dispose Alpine's expression listeners, so the adapter must
call Alpine's public tree-disposal function before replacing Canvas. Second,
inserting a stylesheet link is not asset readiness. Citry now shares each
in-flight CSS request, settles it on load or error, retries after failure, and
waits for graph-linked CSS and JavaScript before component callbacks run.
Collecting a class stylesheet also clears its loaded marker so a later instance
can load and apply the sheet again.

This is deliberately one small interactive slice. The smoke proves basic story
navigation plus successful, delayed, failed, and stale Controls replacements.
It does not yet prove navigation between complex stateful stories, Events
requests, morphing, teleports, remote cancellation, or multi-component cleanup.
It also does not select an adapter.

The hidden connected root is a rendering mechanism, not an isolation boundary.
Citry and Alpine initialize its component graph before promotion. A component
can therefore affect global listeners, Events queues, focus, teleports, or
global CSS while the prior generation remains visible. The counter deliberately
waits to install its window listener until it declares readiness, so this smoke
does not prove a generic atomic client transition. Before complex scenarios can
satisfy the run-lifecycle contract, Citry needs a designed two-phase activation
protocol or an explicitly narrower readiness contract. This is now a core
constraint exposed by the pressure case, not an adapter difference.

## 5. Server/Webpack findings

### 5.1 Useful shape

The Server renderer maps naturally to Python fragments. Generated JSON names a
story ID; the browser fetches `${server.url}/${storyId}` with current Args and
inserts the returned HTML. The adapter configuration is compact and the normal
Canvas, Controls, accessibility panel, and static build all worked.

The stock fetch could not be used unchanged with a strict Citry scenario
schema. It merges Storybook globals into the request query. With the
accessibility and essential tools active, the first real preview sent fields
such as `a11y`, `backgrounds`, `outline`, `viewport`, and `vision`. Citry
correctly returned 400 because those are not component Args. The static spike
first used the supported `fetchStoryHtml` override to send only story Args and
to raise on a non-success HTTP response. The interactive slice moves that same
filtering into the project-level renderer so it can start an abortable
generation before the fetch and share the Citry Canvas lifecycle with
HTML/Vite.

The upstream default fetch reads every response as text without checking
`response.ok`. It replaces Canvas `innerHTML` and invokes Storybook's simulated
page-load handling. The source is small enough to audit directly:
[Server renderer source](https://github.com/storybookjs/storybook/blob/v10.5.4/code/renderers/server/src/render.ts).

### 5.2 Native JSON compiler defects

The official JSON/YAML path is not a safe general projection for the accepted
scenario contract. Reproduction against the exact installed 10.5.4 loader
confirmed:

1. `null` causes `Object.keys(null)` to raise. The loader logs the input and
   returns raw JSON instead of a CSF module.
2. Object keys are emitted without quotes. An Arg such as `aria-label` produces
   invalid JavaScript.
3. The indexer records the display story name while the compiler exports a
   sanitized identifier. Names with spaces or punctuation can disagree, and
   distinct names can collapse to one export identifier.
4. The compiler accepts broadly untyped nested input, so these failures are not
   rejected by a useful schema before Webpack runs.

Sources:

- [Server JSON/YAML indexer](https://github.com/storybookjs/storybook/blob/v10.5.4/code/renderers/server/src/preset.ts)
- [Server story stringifier](https://github.com/storybookjs/storybook/blob/v10.5.4/code/presets/server-webpack/src/lib/compiler/stringifier.ts)

The friendly static catalog avoids `None`, unsafe key names, and unsafe export
names, so its JSON build passes. That does not remove the defect. The full
catalog needs omission versus explicit null, Python-facing names, nested data,
and richer profiles. If Server advances, Citry should generate ordinary CSF
and bypass the native compiler. That extra generator cost removes a meaningful
part of Server's apparent simplicity.

### 5.3 Addon and lifecycle limits

The normal story Canvas and accessibility addon worked. Autodocs showed the
description, Controls, and authored source metadata, but its inline live story
Canvas was absent. HTML/Vite rendered the same live Button in autodocs. This is
consistent with the Server renderer's own warning that addons which assume a
JavaScript-rendered story may not work.

Every string result replaces the Canvas. Script recreation alone does not undo
global listeners, observers, teleports, subscriptions, or server runs from the
previous result. The shared lifecycle adapter passes the first reactive
replacement proof, including component cleanup and Alpine tree disposal.
Server/Webpack still needs the more demanding interactive cases and navigation
between stateful compound stories. There is no published Server/Vite framework,
so retaining this candidate also retains Webpack-specific contributor tooling.

## 6. HTML/Vite findings

The HTML renderer accepts a string or DOM Node, not a Promise. A generated CSF
story therefore uses the intended two-step bridge:

```text
Args and Controls
  -> async Storybook loader fetches validated Citry HTML
  -> synchronous HTML render returns context.loaded.citryHtml
  -> Citry renderToCanvas mounts, activates, awaits, and owns cleanup
```

Storybook documents loaders as asynchronous work that completes before render
and exposes its result through `context.loaded`. It also describes them as an
advanced escape hatch, which is appropriate here because Python owns the
renderer. See [Loaders](https://storybook.js.org/docs/writing-stories/loaders).
Args remain the user-facing state contract and rerender the story when changed;
see [Args](https://storybook.js.org/docs/writing-stories/args) and
[Controls](https://storybook.js.org/docs/essentials/controls).

This path uses standard generated CSF and therefore avoids the Server JSON
compiler. Explicit `argTypes` remain necessary. Storybook's Vite documentation
limits automatic inference to selected client frameworks, and Python
annotations are not among them. See the [Vite builder limitations](https://storybook.js.org/docs/builders/vite).

HTML/Vite passed the normal Canvas, Controls, accessibility, authored-source,
autodocs Canvas, and static-build checks. Its scenario path remains one shared
loader plus one synchronous story render function.

The stock HTML renderer is insufficient for interactive Citry. String
replacement does not await Citry asset readiness as part of the render result
or dispose state created by the prior render. The project preview now supplies
a Citry lifecycle-aware `renderToCanvas` implementation that:

1. mounts the new fragment and declared dependencies in a hidden connected
   root;
2. awaits Citry readiness;
3. rejects stale generations;
4. disposes the previous Canvas generation before promoting the candidate; and
5. returns teardown for story navigation and remount.

The first private reactive probe passes through this implementation, including
basic story-navigation cleanup. Stateful compound navigation, teleport,
Events, morph, and remote-request cases remain open.

The relevant implementation is the
[HTML renderer source](https://github.com/storybookjs/storybook/blob/v10.5.4/code/renderers/html/src/render.ts).

HTML is a current first-party package and Storybook's framework-author guide
uses it as the simplest renderer base. Its omission from the main current
framework list and feature table still needs to be treated as upgrade-risk
evidence during the interactive and maintenance comparison.

## 7. Shared deployment and security findings

Cross-origin loopback fetch was sufficient for the static spike because the
responses contained no credentials and the runner permitted only enumerated
local Origins. The interactive slice now uses a same-origin proxy: Storybook
owns the visible origin and forwards `/citry/**` to the mounted Python service.
This is the adopted comparison shape for later Events, forms, relative assets,
and host security checks. A deployed static Storybook still needs a deliberate
proxy to a protected live scenario service or a separately designed frozen
output mode.

Neither adapter's static output should imply that a live story is frozen or
self-contained. With the backend stopped, both show a visible Storybook render
error rather than stale component HTML, but the default message is generic.
The accepted runner still needs stable authorized diagnostic references and
redaction rather than Python tracebacks.

The archived CHK setup is useful only as historical evidence. It used
Storybook 8.5.5 and Server/Webpack with 93 generated JSON files. Only one file
had Args, none had `argTypes`, and the archived application no longer contains
a complete matching runner configuration. It proves that bulk Server story
generation was attempted, not that Controls, current builds, lifecycle, or
deployment worked.

## 8. Provisional conclusion and next gate

Both candidates advance. No adapter is selected from the static cases or the
first reactive probe.

Server/Webpack has the most direct server-fragment concept, but already needs a
custom fetch, has a defective native projection, misses the live autodocs
Canvas, and carries lower-confidence addon and Webpack maintenance. HTML/Vite
needs an explicit loader, but its standard CSF, successful autodocs Canvas, and
current Vite path produced a cleaner projection. Both candidates now use the
same Citry-owned `renderToCanvas` lifecycle adapter after their
framework-specific fetch step.

The next gate remains the sequence already frozen in the plan:

1. client ambient context (complete);
2. the first private reactive state and asset-activation probe (complete);
3. add focus-preserving fragment/morph pressure and stateful Tabs,
   Dialog/Overlay, remote Combobox or MultiSelect, form registration, and one
   composed repeatable-form workflow;
4. preview every case through both adapters;
5. run the behavioral journeys directly against standalone routes; and
6. compare stale-generation handling, readiness, Events, same-origin routing,
   replacement, cleanup, addon inspection, static deployment, and maintenance
   before choosing the adapter.

The spike and its private readiness components should remain disposable until
that combined evidence is complete.
