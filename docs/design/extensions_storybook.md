# Design: Storybook extension for Citry

**Status (2026-07-29): optional extension research.** A private Citry UI spike
proves that both Server/Webpack and HTML/Vite can preview server-rendered Citry
components, accept Controls, activate Citry assets, replace an interactive
preview, and report failures. No adapter or public package has been selected.

Storybook is useful contributor tooling, but it is not a prerequisite for
building or publishing `citry-ui`. The docs site now provides the first-party
playground and opt-in live components without Node. Component quality remains
the responsibility of direct Playwright, axe, Lighthouse, screenshot, host,
and manual accessibility checks. Storybook can add a familiar state browser,
Controls, addons, and external review workflows on top of that foundation.

Supporting research lives in [`extensions_storybook/`](extensions_storybook/).
The current implementation remains the disposable spike in
[`packages/py/citry_ui/storybook`](../../packages/py/citry_ui/storybook/).

## 1. Decision and scope

Treat Storybook as a separate optional Citry extension. Citry UI may consume
it, but Citry UI's component specifications, implementation, tests,
documentation, and release do not wait for it.

The extension should eventually let a component library:

- project explicitly authored Python examples into Storybook stories;
- change selected Python inputs through Args and Controls;
- preview server-rendered fragments with their real Citry CSS and JavaScript;
- show authored usage, diagnostics, and accessibility-addon feedback;
- link to complete standalone pages for work that needs a full document; and
- rebuild deterministic generated stories when Python examples change.

It is not the browser-automation runner. Storybook does not own Playwright
journeys, conformance assertions, screenshots, Lighthouse runs, or manual
keyboard and assistive-technology tasks. Those tools run directly against
standalone Citry pages or the docs site's live examples.

The public package name, extension API, scenario-discovery API, and adapter are
still open. The Citry UI spike remains private until those decisions are backed
by a second consumer or a deliberate Citry-wide extension design.

## 2. Relationship to Citry UI and the docs site

Citry UI can begin its comparative production slice on the released
`citry==0.3.0` and `citry_core==1.4.0` baseline. Its first-party preview path is
the docs site's implemented live-component host. Component specifications
still need explicit state matrices, standalone composed pages, and direct
quality checks, but they do not need a Storybook projection.

If the Storybook extension advances, it should consume the same deliberate
Python examples or reusable fixtures used by Citry UI's documentation and
tests. It must not require authors to reproduce component behavior or fixture
setup in JavaScript. Storybook-specific metadata stays in the extension layer
and does not become a required nested declaration on every component.

The generic scenario work remains in the
[`Citry UI scenario catalog`](ui_research/scenario-catalog.md). That document
defines stable identities, standalone pages, direct browser work, isolation,
and quality-tool consumers. Storybook is one optional projection of that
model, not its owner.

When `citry-ui` is published, the docs playground has a separate requirement:
its pinned Pyodide runtime should install and register the library so examples
can import `citry_ui` and use registered `C*` tags immediately. That work is
tracked in [`docs_playground.md`](docs_playground.md), not in this extension.

## 3. Current spike evidence

The spike pins Storybook 10.5.4 and compares:

1. `@storybook/server-webpack5`, using generated JSON stories and a
   Citry-owned fetch and Canvas lifecycle; and
2. `@storybook/html-vite`, using generated CSF, an async loader, and the same
   Citry-owned Canvas lifecycle.

Both adapters currently pass the static Button, Field/Input, Table, and
server-selected Tabs previews plus a private reactive-state pressure case. The
interactive case proves CSS and JavaScript activation, local Alpine state,
delayed and failed readiness, stale-response rejection, last-good-preview
retention, Storybook failure status, and cleanup on replacement and basic
navigation.

HTML/Vite currently has the cleaner projection and a live autodocs Canvas.
Server/Webpack maps more directly to server fragments, but its native
projection needed repairs and its autodocs Canvas is not live. That evidence
is not yet enough to select an adapter for a general extension. The full
comparison is recorded in
[`adapter-exploration.md`](extensions_storybook/adapter-exploration.md).

The connected hidden candidate used during replacement is staging, not an
isolation boundary. Citry and Alpine initialize before promotion, so global
listeners, Events, focus, teleports, CSS, and remote work could overlap the
current preview. A general extension needs either a two-phase activation
contract or a deliberately narrower readiness guarantee before it claims
atomic replacement for complex components.

## 4. Authored examples and generated output

Python remains the source of component composition, fixture data, selected
Controls, lifecycle requirements, and expected behavior. Generated Storybook
files are disposable projections. They contain only allowlisted metadata and
adapter code, including identity, serializable Args, explicit `argTypes`,
layout, selected profiles, schema versions, source digests, and the
adapter-specific render call.

Generated output must be deterministic and fail its freshness check when an
authored example is added, changed, or removed. It must not contain Python
fixture implementations, credentials, cookies, State contents, absolute
source paths, copied HTML snapshots, or hand-written behavior.

If a value cannot be represented safely as a Control, the generator omits that
Control and reports why. It does not stringify arbitrary Python objects. A
render request with an unknown, repeated, or incorrectly typed input is
rejected before component rendering.

## 5. Runtime and deployment boundary

The current spike uses a loopback Python scenario service and exposes it below
the Storybook origin at `/citry/**`. That route carries rendered scenarios,
the Citry client runtime, extension assets, and component assets. Both the
development and static-build proxies validate the incoming Host before
rewriting the backend authority.

A built Storybook bundles the Storybook application and generated adapter, not
frozen Citry HTML. Opening a story still needs a reachable Citry rendering
service. A future publishing mode must explicitly deploy a protected renderer,
export a deliberately static-safe subset, or reject scenarios that require
live rendering, Events, or mutable fixtures.

Installing or registering a component library must never mount Storybook
routes. The extension is enabled explicitly for contributor or test hosts.
Node and Storybook dependencies stay outside the component library's runtime
wheel and outside ordinary Citry applications.

## 6. Manual validation

Manual validation is optional for Citry UI work, but useful if you want to
judge the Storybook experience itself. Start from the repository root:

```sh
pnpm install --frozen-lockfile
cd packages/py/citry_ui/storybook
pnpm run generate
```

Then use three terminals in that Storybook directory:

```sh
pnpm run backend
```

```sh
pnpm run storybook:html
```

```sh
pnpm run storybook:server
```

Open HTML/Vite at `http://127.0.0.1:6107` and Server/Webpack at
`http://127.0.0.1:6106`. The backend listens on `127.0.0.1:8123`. You can run
one Storybook adapter at a time if you do not need a side-by-side comparison.

Check the following:

1. Open Button, Field/Input, Table, and Tabs and change their Controls.
2. Open **Readiness / Reactive state**, increment it, then choose `second`,
   `delayed`, `never`, and `slow`. A delayed candidate should not replace the
   current preview early; a failed candidate should show an error and retain
   the last good DOM; a later successful choice should recover.
3. Open Docs for the same story. HTML/Vite should show a live Canvas. The
   missing live Server/Webpack Canvas is a known comparison result.
4. Open the Accessibility addon and confirm it inspects the rendered preview.
5. Open the standalone reactive page at
   `http://127.0.0.1:8123/citry/ext/storybook_scenarios/page/readiness/reactive-state`.

Stop the three manual processes before running the automated smoke because it
starts its own backend and preview servers on the same ports. Alternatively,
skip the manual startup and use the smoke as the standalone automated path.
Install Chromium once and run:

```sh
uv run --project .. --group storybook playwright install chromium
pnpm run smoke
```

The smoke rebuilds both adapters and verifies Controls, asset readiness,
failed and stale replacement, Storybook failure reporting, cleanup,
same-origin routing, hostile-Host rejection, and stopped-backend diagnostics.

If a documented port is occupied, startup fails rather than launching an
unreachable private Storybook process. A missing Chromium binary fails with
the Playwright installation command needed to prepare it. A stopped backend is
expected to produce a visible render error rather than cached component HTML.

## 7. Deferred extension work

The following work is useful only when Storybook becomes a prioritized
extension:

1. decide whether the generic extension uses HTML/Vite, Server/Webpack, or a
   Citry-specific adapter;
2. generalize the Citry UI scenario service without making that model
   mandatory for component libraries;
3. define the public extension command, configuration, discovery, diagnostics,
   and package boundary;
4. prove Events, morph focus preservation, teleports, remote requests, forms,
   pending-navigation cleanup, and complex composed scenarios;
5. define authenticated remote use and a static-publishing policy; and
6. validate a second component library before freezing a Citry-wide API.

Failure to complete any of this work does not block Citry UI. It means the
optional Storybook extension remains experimental or unpublished.
