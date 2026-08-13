# Python scenario catalog for Citry UI

**Status (2026-07-29): accepted quality-scenario contract for Phase 7.** This
document defines reusable isolated component states, composed workflows,
standalone quality pages, direct browser tests, and documentation examples.
Storybook is an optional projection described in
[`../extensions_storybook.md`](../extensions_storybook.md), not a prerequisite
for this catalog or for Citry UI.

The controlling roadmap is
[`../ui_library_plan.md`](../ui_library_plan.md). Quality consumers and release
evidence are defined in
[`quality-test-strategy.md`](quality-test-strategy.md).

## 1. Decision

Citry UI will own one Python scenario catalog for repeatable quality work.
Standalone scenario URLs exist for tests, assistive-technology review,
performance work, and debugging. Public browsing and editable examples belong
to the docs site's UI catalog and live-component host.

```text
Python scenario catalog
  |-- standalone complete-page routes
  |-- Playwright interactions and screenshots
  |-- axe and Lighthouse inputs
  |-- manual keyboard and assistive-technology tasks
  |-- documentation examples and live components
  `-- optional preview-tool projections
```

Python remains the source of component composition, fixture data, lifecycle,
requirements, and expected behavior. An optional tool projection must not
require the same scenario to be re-authored in JavaScript.

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
Scenarios therefore do not live under a tool-specific nested declaration and
are not discovered by scanning component subclasses. An optional projection
may offer convenience declarations, but it must map to this independent model.

## 3. Goals and non-goals

The catalog must:

- define one stable identity for every isolated state and composed workflow;
- render through the exact Citry engine and host under test;
- support server-only, client-interactive, Events-backed, fragment, morph,
  form, and teleport cases;
- expose selected serializable inputs to optional preview tools;
- provide complete standalone documents without preview-tool chrome;
- share portable actions, waits, and semantic assertions with direct browser
  tests where that sharing remains clear;
- isolate concurrent runs and clean up after success or failure;
- keep time, randomness, remote data, and failure cases deterministic; and
- preserve Citry's ordinary asset, lifecycle, security, and transport
  contracts rather than replacing them with test-only behavior.

This contract does not yet define:

- a custom standalone gallery or catalog-navigation UI;
- arbitrary package discovery or aggregation across installed distributions;
- a general workflow programming language;
- automatic Controls for every possible Python annotation;
- a localization API;
- a hosted visual-review service; or
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
- **Tool projection:** deterministic generated metadata and adapter code that
  exposes selected Python scenarios in an optional preview tool.

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
    tags = ("a11y", "deep-host", "preview", "visual")

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
  host environment chooses safe HTTP or an allowed fallback. A scenario
  names a transport only when that transport is the subject under test.
- `ScenarioProfile` carries explicit viewport, theme, direction, motion,
  forced-color, locale, timezone, clock, and seed selections. Browser locale
  here makes a test environment deterministic and does not establish Citry
  UI's future localization API.
- `PlaywrightJourney` carries portable actions, waits, and semantic assertions
  executed by the direct Playwright harness.
- `ManualTask` carries instructions and expected results for keyboard, touch,
  and assistive-technology review.

Every scenario ID is unique within the catalog, stable across generated tool
projections and standalone URLs, and safe to serialize in a path. Moving a
scenario between display groups must not silently change its ID. Renaming or
removing a released documentation URL follows the docs redirect policy.

## 6. Composition, Args, Controls, and profiles

`render()` returns a Citry `ComponentLike` root or a deliberately composed page
root. The runner adds the document shell, dependency output, diagnostics, and
readiness marker. Render logic stays in Python and resolves against the exact
run's Citry instance.

The authored scenario owns its kwargs, slots, initial component state, and
fixture data. It may expose a useful subset through `Scenario.Args`. Incoming
values from a preview tool or a standalone URL are validated before setup or
rendering.

Args defaults must be JSON-portable and safe to expose. Non-serializable or
sensitive data belongs in run-local setup data, not a generated preview
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

Tags select scenarios for docs, optional previews, visual review, accessibility,
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
6. Preview replacement, a Control update, or a direct test reset requests a fresh
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
Citry assets and scenario initialization finish. Preview tools and Playwright wait
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

Preview tools do not receive these journeys. Direct Playwright is their only
automated browser runner. A
complex host-specific assertion may remain in a Python test beside the catalog
instead of introducing arbitrary callbacks into the journey vocabulary.

Manual tasks record setup, actions, expected announcements or focus, supported
browser and assistive-technology pairs, and the result. They remain first-class
scenario evidence even though they are not automatically executable.

## 9. Rendering surfaces and assets

Every scenario declares whether it supports standalone rendering and any
optional preview-tool projection. Complete pages may be standalone-only when
preview chrome or canvas sizing would invalidate the test.

The standalone route renders a complete document with the same components,
dependency discovery, CSS, JavaScript, Events manifest, and setup data used by
any preview projection. It includes no scenario list, controls, or custom
state-browser UI. It provides a stable input for Playwright, axe, Lighthouse,
browser traces, manual review, and links from optional preview tools.

The renderer uses Citry's dependency and asset contracts. Scenarios declare
capability requirements, not duplicate script and stylesheet URLs. Assertions
cover initial dependencies, fragment-time loading, URL deduplication, failed
loads, repeated initialization, and absence of client assets for server-only
scenarios.

Static-safe scenarios may be pre-rendered with their required assets. An
interactive static preview deployment either has a reachable Citry scenario
service or explicitly contains frozen, non-interactive output. A build must not
quietly present dead Events controls as a live scenario.

## 10. Events, CSRF, morphing, and preview origins

Same-origin standalone pages use the ordinary HTTP Events transport and the
host's real cookie and CSRF behavior. An optional embedded preview should
prefer same-origin mounting or reverse proxying. Sandboxed or cross-origin
previews that cannot use authenticated HTTP may use a separately designed
`postMessage` transport and parent-side HTTP bridge.

The bridge forwards the unchanged Events envelope. It validates parent and
child origin, `window.source`, an opaque channel/run nonce, scenario identity,
and allowed Event routes. It does not use wildcard origins with credentials,
place CSRF tokens in generated stories, or weaken application CORS policy.

Preview replacement and Control updates dispose old component roots, listeners,
observers, transport subscriptions, portal output, and run-local data before
the replacement becomes active. Morph journeys wait for Citry lifecycle
signals, then verify focus, selection, edits, component identity, state, and
cleanup.

Static and server-only preview scenarios do not depend on `postMessage`.
Failure of that optional transport is not failure of the catalog unless an
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

## 12. Optional preview-tool projections

A preview tool may consume an allowlisted subset of the catalog: stable
identity, rendering inputs, serializable controls, selected profiles, layout,
source examples, and preview diagnostics. It does not consume or run
Playwright journeys, performance measurements, screenshots, or manual-review
tasks.

Generated projections contain no fixture implementation, authored HTML
snapshot, credential, State content, absolute source path, or hand-written
browser behavior. Output is deterministic, overwriteable, and rejected when
its schema version or source digest is stale. A projection that cannot
represent a Python value omits that control with a diagnostic rather than
stringifying the value.

The optional Storybook design, adapter comparison, deployment constraints,
and maintainer workflow now live in
[`../extensions_storybook.md`](../extensions_storybook.md). Neither that
extension nor another preview tool can replace the direct quality suite.

## 13. Validation and security

Catalog validation fails before a host starts when it finds:

- duplicate or invalid scenario and journey IDs;
- Args defaults that do not match their schema or cannot be serialized;
- control metadata that refers to an unknown Arg;
- a required profile, capability, transport, or host with no harness;
- a scenario selected for a tool projection that cannot render there;
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

The original Phase 7 readiness slice covered Button, Field/Input, Form, Tabs,
Dialog, Combobox, and semantic Table with production specifications, direct
styled implementations, and focused browser evidence. Tabs also had a docs
live example. The active component inventory and contract tests own current
family coverage; this section retains the initial scenario rationale. The
repeatable contact workflow and the public-site form plus dashboard
compositions close the required cross-family implementation probes. Their remaining per-state
accessibility, visual-profile, manual assistive-technology, complete-page,
coexistence, and released-host scenarios still belong in the shared catalog.

The implemented browser-readiness scenarios cover:

1. reactive `LibraryComponent` client-state and asset activation;
2. client ambient context over logical ancestry across dependent cases;
3. stateful Tabs keyboard, focus, selection, morph, and dynamic removal;
4. Overlay/Dialog teleport, focus, document listeners, stacking, and cleanup;
5. remote Combobox or MultiSelect cancellation, stale-result, loading, and
   native-form behavior;
6. Form child registration, unregistration, validation, and submission; and
7. one composed repeatable-form workflow.

The first item now has a private counter probe in the optional Storybook
spike. It proves real fragment CSS and JavaScript activation, browser-local
reactive state, successful, delayed, failed, and stale Controls replacements, basic
story-navigation cleanup, exact component cleanup, Alpine tree disposal, and
one remaining window listener through both adapters. A hidden connected
candidate preserves the current visible generation until readiness, and a
failed candidate retains that DOM while the preview displays an error. The
hidden root does not isolate global client effects: Citry and Alpine initialization
already runs there. A two-phase activation protocol or narrower readiness
contract remains required before complex cases can claim an atomic transition.
This is the first slice of the list, not evidence for the compound, morph,
teleport, remote, form, or composed-workflow requirements.

Disposable supporting components stay outside the public `citry_ui` manifest.
The required production families themselves use the public manifest. New
families still freeze their state matrix, fixtures, budgets, and acceptance
evidence before implementation.

## 15. Falsifiers

The catalog contract must change if:

1. A consumer requires behavior or fixture implementation to be copied out of
   the Python scenario.
2. Citry scripts, CSS, or Events cannot activate reliably after
   server-rendered HTML insertion.
3. Run identity cannot survive render, Event, form, fragment, and morph
   requests without changing the Events envelope.
4. Setup data leaks or crosses runs during concurrency, cancellation, or
   failure.
5. The Playwright journey vocabulary cannot express Tabs, Dialog, Combobox,
   and form workflows without preview-specific test implementations or
   component behavior copied into test code.
6. Standalone and projected rendering produce different assets, semantics,
   state, or interaction results.
7. Importing the catalog requires a host framework, Node, network access, or a
   running server.
8. A preview tool becomes a runtime dependency of `citry-ui`.

Preview-tool-specific falsifiers and adapter decisions belong to that tool's
design. Storybook's are tracked in
[`../extensions_storybook.md`](../extensions_storybook.md).

## 16. Implementation work packages

The catalog contract, docs live-component host, standalone rendering
mechanisms, and first reactive readiness probe now exist. The optional
Storybook spike does not preempt the remaining production-component work.

The remaining work packages are:

1. run storage, setup/teardown, concurrency, failure, and TTL cleanup;
2. host adapters, beginning with Django and FastAPI;
3. Playwright actions, waits, assertions, and direct executor;
4. direct Playwright journeys against standalone routes;
5. Events origin strategy for standalone and embedded consumers;
6. docs embedding, static-safe export, and quality-tool consumers; and
7. final host, security, lifecycle, and generated-file conformance.

Storybook adapter selection, generation, and deployment are separate optional
work in [`../extensions_storybook.md`](../extensions_storybook.md).
