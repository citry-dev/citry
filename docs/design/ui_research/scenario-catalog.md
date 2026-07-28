# Python scenario catalog for Citry UI

**Status (2026-07-24): accepted contract for the Phase 7 entry program.** This
document defines the authored source for isolated component states, composed
workflows, Storybook stories, standalone quality pages, and browser tests. It
does not implement the runner or select the Storybook adapter.

The controlling roadmap is
[`../ui_library_plan.md`](../ui_library_plan.md). Quality consumers and release
evidence are defined in
[`quality-test-strategy.md`](quality-test-strategy.md).

## 1. Decision

Citry UI will own one adapter-neutral Python scenario catalog. Storybook is the
planned maintainer state browser after its feasibility gate passes. Standalone
scenario URLs exist for tests, assistive-technology review, performance work,
and debugging. They are not a second browsable gallery.

```text
Python scenario catalog
  |-- Storybook adapter and generated stories
  |-- standalone complete-page routes
  |-- Playwright interactions and screenshots
  |-- axe and Lighthouse inputs
  |-- manual keyboard and assistive-technology tasks
  `-- documentation examples
```

Python remains the source of component composition, fixture data, lifecycle,
requirements, and expected behavior. Generated Storybook files are disposable
projections. A scenario must not be re-authored in JavaScript to make it work
in Storybook.

Storybook consumes only the preview projection: identity, rendering, Args,
Controls, profiles, layout, and preview diagnostics. It does not consume or run
Playwright journeys, assertions, performance measurements, or manual review
tasks. Those remain direct quality-tool consumers of the same Python scenario.

Node may be required to develop or build the Storybook integration. It is not
a dependency of the `citry-ui` wheel, its import path, an application's Citry
UI runtime, or the standalone Python runner.

The catalog and runner are opt-in contributor and test tooling. Importing or
registering `citry-ui` never mounts scenario routes. A production host must not
gain setup, mutation, fixture, or traceback endpoints merely because the
library is installed.

## 2. Prior art and boundary

The docs-site example runner already proves useful lower-level mechanisms: it
can [discover Python examples](../../../docs_site/_internal/examples.py),
[render standalone and fragment routes](../../../docs_site/_internal/serve.py),
and [export referenced dependencies](../../../docs_site/_internal/build.py)
during a static build. Its current name-based discovery and small
`ExampleInfo` record are too narrow for UI scenarios. They do not describe
inputs, setup and teardown, run identity, actions, waits, hosts, Events, or
expected semantics.

The archived CHK Storybook used `@storybook/server-webpack5`, generated story
metadata, and a Django rendering endpoint. It demonstrates the value of
server-rendered component browsing, but its stories had no meaningful Args,
interaction contract, or lifecycle isolation. It is evidence for one adapter
candidate, not an architecture to copy.

Component introspection and the scenario catalog have different jobs:

| Component introspection | Scenario catalog |
|---|---|
| Mechanical registered-class metadata | Deliberate examples and workflows |
| Declared kwargs, slots, Events, and assets | Chosen public controls and initial values |
| Source and dependency provenance | Setup, teardown, actions, waits, and expectations |
| Tool-safe allowlisted projection | Host, transport, profile, and manual-review requirements |

A scenario may involve several components or an entire application page.
Scenarios therefore do not live under a `Component.Storybook` declaration and
are not discovered by scanning component subclasses. An eventual generic
Storybook extension may offer convenience declarations, but it must project to
this independent catalog model.

## 3. Goals and non-goals

The catalog must:

- define one stable identity for every isolated state and composed workflow;
- render through the exact Citry engine and host under test;
- support server-only, client-interactive, Events-backed, fragment, morph,
  form, and teleport cases;
- give Storybook useful Args, Controls, grouping, profiles, and diagnostics;
- provide complete standalone documents without Storybook chrome;
- share portable actions, waits, and semantic assertions with direct browser
  tests where that sharing remains clear;
- isolate concurrent runs and clean up after success or failure;
- keep time, randomness, remote data, and failure cases deterministic; and
- preserve Citry's ordinary asset, lifecycle, security, and transport
  contracts rather than replacing them with test-only behavior.

This contract does not yet define:

- a public third-party Storybook extension;
- a custom standalone gallery or catalog-navigation UI;
- arbitrary package discovery or aggregation across installed distributions;
- a general workflow programming language;
- automatic Controls for every possible Python annotation;
- a localization API;
- hosted Storybook, Chromatic, or another visual-review service; or
- static deployment of live Events scenarios.

## 4. Terminology

- **Scenario:** one deliberate initial state or workflow with stable identity,
  composition, inputs, requirements, profiles, and evidence.
- **Catalog:** an explicitly ordered and versioned group of scenarios.
- **Run:** one isolated execution of a scenario, including setup data, a Citry
  engine and host context, browser requests, and teardown.
- **Profile:** a named environment selection such as dark, RTL, narrow,
  reduced-motion, or forced-colors. Profiles are selected combinations, not an
  automatic Cartesian product.
- **Journey:** portable browser actions, waits, and assertions for a meaningful
  task.
- **Standalone page:** a complete Citry document for one scenario and run. It
  has no catalog navigation or control UI.
- **Storybook projection:** deterministic generated metadata and adapter code
  that exposes Python scenarios in Storybook.

Do not call the standalone runner headless. Citry UI already uses *headless*
for components that own behavior without owning HTML.

## 5. Python model

The exact public names may change during implementation, but the following
responsibilities are required:

```python
SCENARIOS = ScenarioCatalog(
    name="citry-ui",
    scenarios=(
        CButtonLoading,
        CTabsKeyboard,
        CDialogNested,
        CComboboxRemoteResults,
        SettingsFormValidation,
    ),
)


class CComboboxRemoteResults(Scenario):
    id = "combobox/remote-results"
    title = "Remote results"
    group = "Combobox"
    subjects = (CCombobox,)
    tags = ("a11y", "deep-host", "storybook", "visual")

    class Args:
        query: str = ""
        fail_first_request: bool = False

    controls = (
        ("fail_first_request", BooleanControl()),
    )

    requirements = ScenarioRequirements(
        capabilities=frozenset({"csrf", "events", "javascript", "morph"}),
    )

    profiles = (
        ScenarioProfile.default(),
        ScenarioProfile.dark(),
        ScenarioProfile.rtl(),
        ScenarioProfile.narrow(),
    )

    playwright_journeys = (
        PlaywrightJourney(
            id="reject-stale-result",
            steps=(
                Fill(Label("Search"), "c"),
                WaitForRequest(QueryEquals("c")),
                Fill(Label("Search"), "citry"),
                WaitForResponse(QueryEquals("citry")),
                WaitForResponse(QueryEquals("c")),
                ExpectText(Role("option"), "Citry"),
                ExpectAbsentText("Older response"),
            ),
        ),
    )

    async def setup(self, context: ScenarioContext) -> ScenarioData:
        ...

    async def teardown(
        self,
        context: ScenarioContext,
        data: ScenarioData,
    ) -> None:
        ...

    def render(
        self,
        context: ScenarioContext,
        args: Args,
        data: ScenarioData,
    ) -> ComponentLike:
        ...
```

The records are immutable and ordered:

- `ScenarioCatalog` carries a name, schema version, and explicit scenario
  sequence. Importing it does not start a host, require Node, or perform
  network I/O.
- `Scenario` carries stable identity, title, group, description, subjects,
  typed args, control hints, renderer, requirements, profiles, Playwright
  journeys, manual tasks, and tags.
- `ScenarioContext` carries the exact `Citry` instance, opaque run ID, host,
  transport, request context where applicable, route helpers, fixed clock and
  random services, and an async cleanup stack.
- `ScenarioRequirements` declares capabilities such as JavaScript, Events,
  morph, fragment insertion, teleport, database access, CSRF, and supported
  hosts. An ordinary Events scenario does not require one transport. The
  adapter environment chooses safe HTTP or an allowed fallback. A scenario
  names a transport only when that transport is the subject under test.
- `ScenarioProfile` carries explicit viewport, theme, direction, motion,
  forced-color, locale, timezone, clock, and seed selections. Browser locale
  here makes a test environment deterministic and does not establish Citry
  UI's future localization API.
- `PlaywrightJourney` carries portable actions, waits, and semantic assertions
  executed by the direct Playwright harness.
- `ManualTask` carries instructions and expected results for keyboard, touch,
  and assistive-technology review.

Every scenario ID is unique within the catalog, stable across generated
Storybook files and standalone URLs, and safe to serialize in a path. Moving a
scenario between display groups must not silently change its ID. Renaming or
removing a released documentation URL follows the docs redirect policy.

## 6. Composition, Args, Controls, and profiles

`render()` returns a Citry `ComponentLike` root or a deliberately composed page
root. The runner adds the document shell, dependency output, diagnostics, and
readiness marker. Render logic stays in Python and resolves against the exact
run's Citry instance.

The authored scenario owns its kwargs, slots, initial component state, and
fixture data. It may expose a useful subset through `Scenario.Args`. Incoming
values from Storybook or a standalone URL are validated before setup or
rendering.

Args defaults must be JSON-portable and safe to expose. Non-serializable or
sensitive data belongs in run-local setup data, not the generated Storybook
manifest, URL, or browser controls. The generator may consult allowlisted
component introspection for names, types, descriptions, Events, and asset
provenance, but it must not publish every component field automatically.

The example's setup uses a controlled fake search service whose `"c"` response
is released after the `"citry"` response. The journey waits until both requests
have started and completed, so a debounce cannot make the stale-result test
pass without exercising request ordering.

Control metadata describes presentation such as number bounds, finite
options, colors, booleans, or text. It does not contain Python render logic.
Changing Controls creates a fresh run and tears down the previous run. It does
not mutate a workflow that the maintainer has already exercised.

Tags select scenarios for Storybook, docs, visual review, accessibility,
performance, host smoke, deep host coverage, or other named jobs. Profiles
select reviewed environment combinations. A release matrix may add further
browser permutations without multiplying authored scenarios.

## 7. Run lifecycle and isolation

An interactive scenario is not a stateless HTML snippet. Events, forms,
fragments, remote results, and database fixtures continue across requests, so
the runner owns an explicit run:

1. The host harness creates and initializes its Citry engine, registers the
   target library, validates catalog uniqueness and portability, and mounts
   Citry assets and scenario routes. The engine is normally reused across runs;
   immutable component classes and installation records are host-scoped while
   scenario state is run-scoped. A scenario creates another engine only when
   engine isolation is the subject under test.
2. Creating a run assigns an opaque run ID, replacement generation, and async
   cleanup stack.
3. `setup()` runs exactly once and returns run-local data.
4. The scenario renders with the exact Citry dependency and Events manifests.
5. Later Event, fragment, form, and transport requests resolve to the same run
   without changing the Events envelope.
6. Story navigation, a Control update, or a direct test reset requests a fresh
   generation. Only the newest requested generation may activate. A stale
   setup or render result is discarded and torn down exactly once. The current
   run remains coherent until its replacement is ready; replacement activation
   and old-run deactivation form one ordered transition. A failed replacement
   leaves no partially active candidate.
7. Every setup that starts owns exactly one idempotent teardown, including
   partial setup, cancellation, supersession, and render failure. Explicit test
   cleanup calls it. Browser unload is only a
   best-effort hint. Time-to-live cleanup and server shutdown are backstops.
8. Teardown is idempotent and runs after setup, rendering, actions,
   assertions, or transport failure.

Two concurrent runs of one scenario must not share run-local mutable Python
state, database rows, generated files, clocks, random streams, or fake
remote-service responses. Scenario state is keyed by run identity rather than
stored only in a shared host session. Same-origin previews may intentionally
share host-authentication cookies. Use separate browser contexts when cookie
isolation itself is under test. A run ID belongs to route or channel framing,
not to the Events protocol envelope.

The page exposes a stable machine-readable marker containing the scenario ID,
run ID, and `loading`, `ready`, or `error` status. It becomes `ready` only after
Citry assets and scenario initialization finish. Storybook and Playwright wait
for that marker or an explicit scenario wait, never generic `networkidle`.

## 8. Playwright journeys and manual tasks

The first Playwright journey vocabulary only covers the browser-readiness and
Phase 7 probes. Add a construct when a real scenario needs it, not in
anticipation of every possible test.

Initial actions:

- click, focus, fill, press, option selection, and form submission;
- pointer or touch input when keyboard or click cannot express the contract;
- direct navigation to another run-local scenario URL when a composed
  workflow requires it.

Initial waits:

- scenario ready and Citry idle;
- named Event observed;
- visible, hidden, attached, or removed state;
- matching request completion;
- fragment inserted or morph applied.

Initial assertions:

- visibility, absence, and text;
- focus and selection;
- role, accessible name, relationship, and exposed state;
- attribute, property, URL, list order, and item count.

Locators prefer roles and accessible names, labels, and native relationships.
A stable `data-citry-ui-part` locator is appropriate only when that public part
is itself under test. Arbitrary sleeps are forbidden. Timeouts are outer
failure limits, not synchronization.

Storybook does not receive these journeys and no generated story contains a
`play` function. Direct Playwright is their only automated browser runner. A
complex host-specific assertion may remain in a Python test beside the catalog
instead of introducing arbitrary callbacks into the journey vocabulary.

Manual tasks record setup, actions, expected announcements or focus, supported
browser and assistive-technology pairs, and the result. They remain first-class
scenario evidence even though they are not automatically executable.

## 9. Rendering surfaces and assets

Every scenario declares support for standalone rendering, Storybook embedding,
or both. Component states intended for Storybook normally support both.
Complete pages may be standalone-only when Storybook chrome or canvas sizing
would invalidate the test.

The standalone route renders a complete document with the same components,
dependency discovery, CSS, JavaScript, Events manifest, and setup data used by
the Storybook preview. It includes no scenario list, controls, or custom
state-browser UI. It provides an "Open standalone" target from Storybook and a
stable input for Playwright, axe, Lighthouse, browser traces, and manual review.

The renderer uses Citry's dependency and asset contracts. Scenarios declare
capability requirements, not duplicate script and stylesheet URLs. Assertions
cover initial dependencies, fragment-time loading, URL deduplication, failed
loads, repeated initialization, and absence of client assets for server-only
scenarios.

Static-safe scenarios may be pre-rendered with their required assets. An
interactive static Storybook deployment either has a reachable Citry scenario
service or explicitly contains frozen, non-interactive output. A build must not
quietly present dead Events controls as a live scenario.

## 10. Events, CSRF, morphing, and preview origin

Same-origin standalone pages use the ordinary HTTP Events transport and the
host's real cookie and CSRF behavior. The Storybook feasibility spike first
tests same-origin mounting and reverse proxying. Sandboxed or cross-origin
previews that cannot use authenticated HTTP may use the planned `postMessage`
transport and a parent-side HTTP bridge.

The bridge forwards the unchanged Events envelope. It validates parent and
child origin, `window.source`, an opaque channel/run nonce, scenario identity,
and allowed Event routes. It does not use wildcard origins with credentials,
place CSRF tokens in generated stories, or weaken application CORS policy.

Story replacement and Control updates dispose old component roots, listeners,
observers, transport subscriptions, portal output, and run-local data before
the replacement becomes active. Morph journeys wait for Citry lifecycle
signals, then verify focus, selection, edits, component identity, state, and
cleanup.

Static and server-only Storybook scenarios do not depend on `postMessage`.
Failure of that optional transport is not failure of Storybook unless an
Events-backed requirement has no safe same-origin or proxied alternative.

## 11. Host contract

The catalog and Playwright journeys are host-neutral. Host harnesses supply the
real request lifecycle and run environment.

- Django and FastAPI run the deep catalog through real middleware, sessions,
  CSRF, forms, Events, async behavior, database setup, fragments, morphs,
  errors, and cleanup.
- Flask, generic ASGI, and generic WSGI run scenarios tagged `host-smoke`,
  covering registration, document rendering, assets, fragment insertion,
  native forms, Events, error mapping, and teardown.
- WSGI scenarios do not claim async-handler behavior that Events reserves for
  ASGI.
- The same rendered scenario and Playwright assertions run through every host.
  Host-specific tests may add assertions but do not replace the common
  contract.

## 12. Storybook projection and adapter gate

The next roadmap step compares two candidates against the same catalog:

1. [`@storybook/server-webpack5`](https://www.npmjs.com/package/@storybook/server-webpack5)
   with server-rendered HTML and story metadata;
2. [`@storybook/html-vite`](https://www.npmjs.com/package/@storybook/html-vite)
   with an async Citry loader and synchronous HTML render for static cases,
   followed by a lifecycle-aware `renderToCanvas` adapter for interactive
   cases.

The server-static tranche and first private reactive slice are complete and
recorded in
[`storybook-adapter-exploration.md`](storybook-adapter-exploration.md). Both
candidates advance to the remaining interactive readiness set; no adapter has
been selected.

The spike must record the exact Storybook and package versions. Continued
support of the server framework is itself a gate because the current Storybook
documentation emphasizes its supported client frameworks. The comparison
therefore verifies the exact installed package versions rather than assuming
either adapter remains supported.

Generated Storybook files contain only:

- title, story name, group, and stable scenario ID;
- args and `argTypes`;
- tags, layout, globals, and profile mappings;
- the adapter-specific renderer or fetch call;
- catalog schema version, generator version, and source digest.

They contain no Python fixture implementation, authored HTML snapshots,
credentials, secrets, absolute source paths, or hand-written behavior. Output
is deterministic, sorted, overwriteable, and rejected by a build check when
stale. Small hand-authored `.storybook` adapter configuration is allowed, but
it is not duplicated per scenario.

The gate has two stages. Current server-static pressure scenarios first prove
catalog projection, rendering, controls, and basic preview operation without
selecting a winner. Both candidates then preview every interactive
browser-readiness scenario. Direct Playwright runs the behavioral journeys
against standalone routes; Storybook is not the automation runner. Selection
happens only from the combined preview and direct-test evidence.

Both candidates must prove or classify:

- useful Args and Controls with validated errors;
- docs and source/example display;
- accessibility inspection and whether addons inspect the actual preview;
- manual interaction with rendered previews and useful state inspection;
- Citry CSS, JavaScript, Events, fragment, and morph activation;
- cleanup and run disposal on navigation and Control updates;
- nested components and composed workflows;
- server errors plus authorized and redacted diagnostics;
- same-origin, reverse-proxy, and fallback transport behavior;
- direct standalone URLs;
- regeneration and live reload after adding, editing, or removing a Python
  scenario; and
- development, static-build, generated-file, and contributor maintenance
  cost.

Direct Playwright remains canonical for cross-browser behavior, Events,
morphing, hosts, and lifecycle. Lighthouse runs complete standalone pages.
Pinned local Playwright screenshots remain the default visual-regression
record unless a later decision deliberately adopts a hosted service. A
Storybook addon supplements those gates but does not silently replace them.

Failure of one addon does not automatically fail an adapter if the same
scenario still works in direct quality tooling. Failure to browse, control,
activate, isolate, or reliably clean up realistic Citry scenarios is an
adapter failure.

## 13. Validation and security

Catalog validation fails before a host starts when it finds:

- duplicate or invalid scenario and journey IDs;
- Args defaults that do not match their schema or cannot be serialized;
- control metadata that refers to an unknown Arg;
- a required profile, capability, transport, or host with no harness;
- a Storybook-tagged scenario that cannot render in a preview;
- a journey with an unknown action, wait, assertion, or ambiguous locator;
- mutable catalog records or nondeterministic ordering; or
- generated output whose schema version or source digest is stale.

Authored class declarations are normalized into immutable canonical records
before `ScenarioCatalog` construction. Later mutation of a class attribute,
source mapping, or input collection cannot change a running catalog.

Generated metadata is an allowlist. It never contains secrets, opaque State
contents, database values, cookies, CSRF tokens, absolute local paths, or
unrequested component introspection. Scenario render errors are visible to
authorized contributors without reflecting secrets into preview HTML. Public
or static output receives a stable error reference rather than a Python
traceback.

Scenario routes are disabled by default and mount only through an explicit
development or test command or host configuration. The default live runner
binds to loopback, but still enforces an explicit allowed-Host and Origin
policy to reject browser and DNS-rebinding requests. Any remotely reachable
runner additionally requires explicit trusted-user authentication,
authorization, transport authorization, and an isolated fixture environment.
The host's authentication, CSRF, and authorization remain active. An opaque run
ID prevents accidental collisions; it is not authentication or authorization.
Every document, control, setup, Event, fragment, form, diagnostic, and cleanup
request applies the runner's access policy before resolving that ID.

A cacheable public GET never creates a run whose setup mutates files,
databases, queues, or remote systems. Such a run is created only by an
authenticated, authorized, CSRF-protected POST or explicitly in-process by the
test driver, after which its authorized standalone URL may render it. Trusted
debug mode may show a redacted traceback. Other modes return only the error
reference.

Setup that writes files, databases, queues, or remote services uses an
explicit disposable fixture provider. The runner must not infer that an
application database is safe to mutate. Live docs embedding requires an
intentionally deployed runner with the same access controls; otherwise the
scenario is static-safe or omitted. Runner policy also limits active runs per
principal, setup and run duration, request body size, retained output, and
fixture resources. TTL cleanup is a recovery mechanism, not an authorization
boundary.

Setup data is isolated per run. Cleanup executes after partial setup and all
failure paths. Concurrency tests deliberately overlap two runs of the same
scenario and two different scenarios. Security tests cover forged run IDs,
expired runs, cross-run requests, origin confusion, and Event routes outside a
bridge allowlist.

## 14. Initial catalog and readiness coverage

The existing Button, Field/Input, semantic Table, and server-static Tabs
pressure cases seed the Storybook adapter comparison. They are not production
specifications.

Disposable browser-readiness scenarios then cover:

1. reactive `LibraryComponent` client-state and asset activation;
2. client ambient context over logical ancestry before dependent cases;
3. stateful Tabs keyboard, focus, selection, morph, and dynamic removal;
4. Overlay/Dialog teleport, focus, document listeners, stacking, and cleanup;
5. remote Combobox or MultiSelect cancellation, stale-result, loading, and
   native-form behavior;
6. Form child registration, unregistration, validation, and submission; and
7. one composed repeatable-form workflow.

The first item now has a private counter probe in the Storybook spike. It
proves real fragment CSS and JavaScript activation, browser-local reactive
state, successful, delayed, failed, and stale Controls replacements, basic
story-navigation cleanup, exact component cleanup, Alpine tree disposal, and
one remaining window listener through both adapters. A hidden connected
candidate preserves the current visible generation until readiness, and a
failed candidate retains that DOM while Storybook displays an error. The hidden
root does not isolate global client effects: Citry and Alpine initialization
already runs there. A two-phase activation protocol or narrower readiness
contract remains required before complex cases can claim an atomic transition.
This is the first slice of the list, not evidence for the compound, morph,
teleport, remote, form, or composed-workflow requirements.

These scenarios and supporting components stay outside the public `citry_ui`
manifest. Formal Phase 7 begins only after the entry results freeze production
component specifications, the final scenario set and fixture profiles,
reconfirm or revise the drafted budgets, and confirm the advancing
architectures.

## 15. Falsifiers

The contract or adapter choice must change if:

1. The same Python scenario needs adapter-specific render markup or fixture
   implementation.
2. Storybook cannot replace a scenario or change Controls without leaking
   Citry roots, listeners, assets, portals, transport state, or setup data.
3. Citry scripts, CSS, or Events cannot activate reliably after
   server-rendered HTML insertion.
4. Neither candidate exposes useful Controls and interaction for realistic
   server-rendered output.
5. A required addon silently skips the actual Citry preview.
6. Run identity cannot survive render, Event, form, fragment, and morph
   requests without changing the Events envelope.
7. Cross-origin operation requires weakened CORS or CSRF rules, wildcard
   messaging, or credentials in the preview.
8. Setup data leaks or crosses runs during concurrency, cancellation, or
   failure.
9. The Playwright journey vocabulary cannot express Tabs, Dialog, Combobox,
   and form workflows without adapter-specific test implementations or
   component behavior copied into test code.
10. Standalone and Storybook rendering produce different assets, semantics,
    state, or interaction results.
11. Importing the catalog requires a host framework, Node, network access, or a
    running server.
12. Storybook becomes a runtime dependency of `citry-ui`.

A server-framework failure advances the HTML/Vite candidate. Failure of both
candidates against the frozen requirements is the point at which a custom
Storybook adapter or separate maintainer state browser becomes justified.

## 16. Implementation work packages

The catalog, standalone document and fragment routes, the provisional static
two-adapter comparison, and the first reactive readiness probe now exist. They
do not select an adapter or preempt the remaining interactive readiness and
production-component work.

The remaining work packages are:

1. run storage, setup/teardown, concurrency, failure, and TTL cleanup;
2. host adapters, beginning with Django and FastAPI;
3. Playwright actions, waits, assertions, and direct executor;
4. both adapters previewing the complete interactive readiness set, direct
   Playwright journeys against standalone routes, a recorded comparison, and
   adapter selection;
5. selected Storybook adapter, generator, diagnostics, and standalone links;
6. Events origin strategy and any required `postMessage` bridge;
7. docs embedding, static-safe export, and quality-tool consumers; and
8. final host, security, lifecycle, and generated-file conformance.
