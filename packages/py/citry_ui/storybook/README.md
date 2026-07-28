# Citry UI Storybook adapter spike

This contributor-only tool renders the same Python-owned scenarios through two
disposable Storybook integrations:

- `@storybook/server-webpack5`, using generated JSON stories and the server
  renderer with a Citry-owned fetch and Canvas lifecycle;
- `@storybook/html-vite`, using generated CSF, an async loader, and the same
  Citry-owned Canvas lifecycle.

It is an adapter comparison, not a public `citry-ui` package surface. The
directory is outside the `citry_ui` Python package and is excluded from the
wheel. Storybook previews components; direct Playwright checks verify the
adapters but are not authored as Storybook stories or journeys.

## Run it

From the repository root, install the Node workspace once:

```sh
pnpm install --frozen-lockfile
```

The package scripts resolve and synchronize their private Python dependency
group automatically. From this directory, use three terminals:

```sh
pnpm run generate
pnpm run backend
pnpm run storybook:server
```

The Server/Webpack preview is then available on `http://127.0.0.1:6106`.
Replace the final command with `pnpm run storybook:html` for the HTML/Vite
preview on `http://127.0.0.1:6107`.

The Python backend exposes the generated catalog at
`http://127.0.0.1:8123/citry/ext/storybook_scenarios/catalog` and complete
standalone pages below
`http://127.0.0.1:8123/citry/ext/storybook_scenarios/page/`. The Storybook
commands run the framework server on a private internal port and expose the
documented port through a same-origin proxy. The proxy reserves `/citry/**`
for the Python service, including scenario HTML, the Citry runtime, extension
assets, and component JS and CSS. It validates the incoming loopback authority
before rewriting the backend Host.

Generated Docs metadata uses a catalog-authored Python example. It must not
show the generated JavaScript bridge as Citry UI's public usage API. The static
comparison report records the Server adapter's current missing live Canvas in
autodocs.

Build the two static Storybook applications with:

```sh
pnpm run build:server
pnpm run build:html
```

Both builds still fetch live Citry markup when a story opens. They are not
self-contained frozen component snapshots.

The preserved browser smoke rebuilds both adapters, serves their static output,
starts the Python backend, and checks each adapter with Chromium:

```sh
pnpm run smoke
```

Install the Chromium binary once with
`uv run --project .. --group storybook playwright install chromium` if it is
not already present. This check covers the standalone reactive probe, adapter
mounting, client asset readiness, browser-local state, a Controls replacement,
delayed and failed readiness, stale-response rejection, last-good-generation
preservation, exact component and Alpine cleanup, basic story-navigation
cleanup, active CSS, stale physical listeners, hostile-Host rejection, and
visible backend failure. It does not author or execute journeys through
Storybook.

## Deliberate limits

Button, Field/Input, Table, and Tabs remain server-static, and Tabs is
explicitly labelled server-selected. A private reactive counter is a
disposable framework probe, not a proposed public component. It proves Citry
fragment activation, CSS and JS readiness, component-local Alpine state,
browser-local events, hidden candidate staging, failed-candidate recovery,
Controls replacement, returned component cleanup, Alpine tree disposal, one
owned window listener, and both adapter lifecycles.

It does not prove Events transport, morph focus preservation, ambient context
inside a production compound component, teleports, remote requests, form
registration, stale server-run disposal, or the later complex readiness
scenarios. Those remain required before adapter selection and production
component specifications.

The hidden connected candidate is not a transaction boundary. Citry and Alpine
initialize it before promotion, so a real component could affect global
listeners, Events, focus, teleports, or global CSS while the current preview is
still visible. The private counter delays its window listener until readiness.
Complex scenarios therefore need a two-phase client activation design, or a
narrower readiness contract, before they can claim atomic replacement.
