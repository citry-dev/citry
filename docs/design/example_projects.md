# Design: standalone example projects

**Status (2026-08-24): accepted and implemented.** This document defines how
Citry owns, structures, tests, publishes, and retires complete example projects
under the repository-root `examples/` directory. The initial starter roster,
Project Board and HTMX demos, qualification tooling, archives, discovery links,
and CI workflow implement this contract.

The repository already has a separate docs-site example system under
`docs_site/examples/`. That system remains independent. Its examples are
small, docs-native teaching units shaped for the docs renderer, preview
loader, and example contract. Root example projects are complete applications
that a reader can copy, install, run, test, and modify without the Citry
repository or docs machinery.

Related contracts:

- [`docs_site.md`](docs_site.md) and [`docs_content.md`](docs_content.md) own
  the reader-facing documentation and docs-native Examples surfaces.
- [`component_initialization.md`](component_initialization.md) owns Citry's
  startup lifecycle.
- [`events.md`](events.md) owns Events, State, actions, and transport.
- [`alpinejs.md`](alpinejs.md) owns Alpine expressions, client data, component
  boundaries, and browser lifecycle.
- [`security_csrf.md`](security_csrf.md) owns CSRF responsibility across Citry
  and its hosts.
- [`benchmarking.md`](benchmarking.md) owns benchmark fixture isolation and
  measurement.
- [`codebase.md`](../codebase.md) owns monorepo, dependency, CI, and release
  conventions.

---

## 1. Decision

Citry keeps its canonical first-party example projects in this monorepo:

```text
examples/
  AGENTS.md
  README.md
  catalog.toml
  tests/
  starters/
    standalone/
    fastapi/
    django/
    flask/
    asgi/
    wsgi/
  demos/
    project_board/
    htmx/
```

There are two project kinds:

- A **starter** is a small, idiomatic, complete project intended to be copied
  and changed. The initial web starters implement one shared behavioral story
  through different hosts. The standalone starter renders without an HTTP
  application.
- A **demo** is a richer application that proves Citry in a product-like
  composition. A demo may choose the host that best serves its story and is
  not required to repeat the starter host matrix.

The initial host roster is FastAPI, Django, Flask, bare ASGI, and bare WSGI,
plus the no-server standalone renderer. Starlette or another framework can be
added later by satisfying the same project contract; `etc.` is not an open
directory of unqualified snippets.

Root `examples/` and `docs_site/examples/` are deliberately separate:

- neither imports from, generates, or synchronizes source into the other;
- neither claims that files with similar teaching goals must be identical;
- docs pages may link to a root project, matching release tag, or downloadable
  release archive; and
- changing one surface requires changing the other only when a link, command,
  or explicit compatibility claim is affected.

There is no `citry init` command in this design. Copying a release-specific
project is the onboarding mechanism until the starter layouts have stabilized
through real use and releases.

## 2. Goals and non-goals

### 2.1 Goals

The root projects must:

1. give a new user a complete first run rather than only an adapter call;
2. use the public Citry API and an idiomatic project shape for their host;
3. demonstrate meaningful server and browser behavior, including Events in
   every web starter;
4. make the important data channels visible rather than hide them behind
   example-only helpers;
5. work after their project directory is copied outside the monorepo;
6. carry their own dependency metadata, tests, commands, and production
   caveats;
7. run without external services or runtime network access;
8. be tested through the real host, an actual listening server, and a real
   browser in proportion to what they promise; and
9. remain compatible with the Citry release or repository revision that
   presents them.

### 2.2 Non-goals

The initial project set does not:

- teach every Citry feature in every starter;
- make all framework source trees artificially identical;
- provide a production deployment stack, database, user system, or secret
  store;
- use `citry-ui` merely to make the starter look complete;
- depend on CDN scripts, fonts, APIs, or images;
- turn docs-site examples into project sources;
- turn benchmark fixtures into application imports;
- publish the example projects as Python distributions; or
- define a remote template registry or community-template trust policy.

## 3. Product taxonomy

### 3.1 Starters

A starter answers: "What does a sound first Citry application look like in
this environment?"

The web starters are behaviorally equivalent but host-native. Their common
component story and observable browser behavior are the compatibility
contract. Their module layout, application factory, routing, response type,
startup hook, and server command follow the host's conventions.

This permits a small amount of deliberate duplication. A FastAPI user should
be able to copy `examples/starters/fastapi/` without also copying a shared
private package. Exact file synchronization across starters is not required;
the black-box behavior and data-flow requirements below prevent accidental
drift where it matters.

### 3.2 Demos

A demo answers: "What does Citry look like in a substantial application?"

Demos may contain more components, assets, routes, persistence, and browser
journeys. They must remain runnable and tested, but compactness and host parity
are not their goals. A demo chooses one reference host unless demonstrating
host portability is part of that demo's stated purpose.

The first demo is `project_board`, inspired by the large project-page
benchmark. It should use FastAPI as its initial reference host because the
repository already has a complete FastAPI tutorial and real adapter coverage.
Additional launchers are added only when they teach something the starters do
not already prove.

The `htmx` demo proves interoperability with an established browser-side
request and swap library. It also uses FastAPI, but it does not teach FastAPI
setup. It shows existing HTMX users how Citry-rendered fragments fit into their
current endpoints without replacing HTMX with Citry Events.

## 4. Repository ownership and catalog

### 4.1 Directory ownership

`examples/AGENTS.md` will contain contributor rules applying to every root
example without being copied as part of an individual project. At minimum it
will require:

- public Citry imports only;
- no imports from another example or from repository test helpers;
- host-native lifecycle and security behavior;
- project-local tests plus the shared qualification harness;
- deterministic data and no runtime network dependency; and
- catalog, README, lock, and CI updates when a project changes.

`examples/README.md` is the repository-facing index. It explains starters
versus demos, presents the host/capability matrix, gives the shortest command
for each project, and links to the framework and security documentation.

`examples/tools/` owns the repository-level catalog loader, clean-copy and
browser qualification runner, deterministic archive builder, and
release-surface validator. GitHub CI invokes this tooling directly, but it is
never a runtime dependency of an example project. `examples/tests/` owns the
tests for that maintenance tooling.

### 4.2 Catalog

`examples/catalog.toml` is the explicit inventory consumed by repository
checks. Its first schema version is `1`, following the repository rule that
pre-1.0 manifest formats start at `1` and change only when a consumer needs a
new contract.

Each entry records at least:

| Field | Purpose |
|---|---|
| `id` | Stable lowercase identifier used by tests, archives, and links. |
| `kind` | `starter` or `demo`. |
| `path` | Repository-relative project root below `examples/`. |
| `host` | `none`, `fastapi`, `django`, `flask`, `asgi`, or `wsgi` initially. |
| `python` | Supported Python constraint for the project. |
| `test` | Shell-free argument vector for the project-local test command. |
| `serve` | Shell-free argument vector with a `{port}` placeholder; absent for standalone. |
| `page_path` | HTTP path whose response is the complete page. |
| `citry_prefix` | Mounted Citry route prefix; absent for standalone. |
| `profile` | Fixed shared qualification profile such as `starter-web-v1`. |
| `docs` | Reader-facing guide URLs relevant to the project. |

Commands are argument arrays rather than shell strings. The shared runner
substitutes only its allocated port and supplies an explicit environment. It
does not evaluate shell syntax from the catalog.

Catalog validation fails when:

- an entry has an unknown kind, host, profile, field, or path;
- two entries reuse an id or path;
- an inventory path escapes `examples/` or resolves through a symlink;
- a project directory exists under `starters/` or `demos/` but is not listed;
- a required project file is missing; or
- the kind and path disagree.

The catalog is repository tooling, not a public Citry plugin or initializer
manifest. Its schema does not imply that arbitrary downloaded templates can be
trusted or executed.

### 4.3 Workspace independence

An example is not a package under `packages/py/` and is not a published
workspace member. Running its documented commands from its own directory must
use its own project metadata and environment. If the package manager would
otherwise absorb a nested project into the root workspace, implementation
must explicitly exclude the example tree from workspace membership.

No checked-in dependency may use a repository-relative path. Repository CI
may overlay a locally built Citry artifact into a temporary copy, but the
committed project remains installable from a release index.

## 5. The shared starter application

### 5.1 Scenario

Every initial starter renders a small **Project Explorer**. This is large
enough to show Citry's actual data and browser model while remaining readable
in one sitting.

The deterministic data module defines a frozen Python `Project` record and a
small project catalog. The page displays project cards and lets a user:

1. reveal or hide a short help panel immediately in Alpine, without a server
   call;
2. type a project query whose debounced Citry Event reloads matching records
   and morphs the explorer; and
3. observe explicit loading and error feedback while the event settles.

The page route loads the initial rich `Project` values and passes them into
the root page. The event State carries only the small query string. On an
event, the handler treats State as client input, reloads the deterministic
records, and builds a fresh component tree from explicit inputs.

This shape deliberately avoids a fake database mutation. It proves the full
Events request, signed State, host route, dependency runtime, and morph path
without implying that a process-local list is a persistence design.

### 5.2 Required component shape

The shared story should need three or four authored components:

- `ProjectPage`: a complete HTML document containing `<c-css>` and `<c-js>`;
- `PageShell`: layout composition with at least one named slot and the default
  slot;
- `ProjectExplorer`: typed inputs, explicit State, `template_data()`,
  `js_data()`, Alpine expressions, and Events; and
- `ProjectCard`: a typed child component rendered from a server-side loop.

Names can vary if a host has a compelling convention, but reducing the story
to one monolithic class fails the starter contract.

The important schema distinction is:

```python
class Kwargs:
    projects: tuple[Project, ...]
    query: str = ""

class State:
    query: str = ""
```

Rich project records are render inputs and do not round-trip. The JSON-safe
query is the only value the next event call needs. The event handler has the
conceptual shape:

```python
class Events:
    def refresh(self, state):
        projects = find_projects(state.query)
        return ProjectExplorer(projects=projects, query=state.query)
```

This is illustrative design, not source to paste verbatim into every host.
The implementation must use the current public typing and component style.

### 5.3 Data-movement curriculum

The starters teach data by showing each channel in the code and naming it in
their READMEs:

| Movement | Citry surface | Starter requirement |
|---|---|---|
| Host route to page | component kwargs | Required. |
| Component Python to its template | `template_data()` | Required. |
| Parent to child | typed component kwargs | Required. |
| Parent-authored markup to a child/layout | slots and fills | Required. |
| Python render to browser scope | `js_data()` | Required. |
| Immediate browser-only state | Alpine expressions such as `@click`, `x-show`, and `x-text` | Required. |
| Browser to the next server call | `State` plus a `:c-*` or `@c-*` binding | Required in web starters. |
| Server result to live DOM | an Event handler returning a fresh component tree | Required in web starters. |
| Ambient server context | provide/inject | Reserved for demos or a focused example. |
| Reactive parent-to-child browser input | `$c-props` | Reserved for demos or a focused example. |
| Cross-target browser result | Events actions such as `Dispatch` or targeted `Render` | Reserved for demos or a focused example. |

The last three are intentionally not forced into a beginner starter. The
starter should explain the common channels well before becoming a catalog of
advanced mechanisms.

### 5.4 Required browser behavior

The Project Explorer must include:

- a `js_data()` seed with a browser-style key such as `tipsOpen`;
- an ordinary Alpine `@click` that changes that local value;
- `x-show` and `x-text` or an equivalent visible expression;
- `:c-query.debounce.300ms="refresh"` or the settled equivalent for the
  live server query;
- `$loading("refresh")` in a visible and accessible pending state;
- `$error("refresh")` in an `aria-live` error region; and
- an Events morph that preserves the focused query input and updates the
  result count and cards.

Citry owns Alpine startup. A starter must not add a second Alpine script tag.
It must not fetch its styling or JavaScript from a CDN.

### 5.5 Required server behavior

Every web starter must expose:

- `/` as the complete document page;
- the same Citry instance on every component, page render, and mounted route;
- Citry's browser and Events routes under `/citry`;
- initialization after application-time registration and before concurrent
  requests;
- an environment-provided signing secret for State;
- a documented development command using the host's real server; and
- a synchronous event handler that works on ASGI and WSGI hosts alike.

The shared story uses a synchronous handler so the code and outcome remain
portable. The ASGI and FastAPI READMEs may explain that those hosts also permit
async handlers. Django and WSGI must not imply that they do.

### 5.6 Host-specific responsibilities

| Starter | Required host-native choices |
|---|---|
| FastAPI | An `HTMLResponse` page route, root lifespan calling `initialize()` before `yield`, `citry.contrib.fastapi.mount`, and Uvicorn as the documented server. |
| Django | A normal Django view returning `HttpResponse`, project URL patterns including `citry.contrib.django.urlpatterns`, `AppConfig.ready()` initialization, `citry.contrib.django.secret()`, CSRF middleware, and a page response that ensures the default CSRF cookie exists for Events. |
| Flask | An application factory, normal Flask page route/response, `citry.contrib.flask.mount`, initialization after registrations and mounting but before returning the app, a real Flask test client, and Flask's development server command. |
| Bare ASGI | One small root ASGI application that owns lifespan and dispatches the page versus `/citry`, `citry.contrib.asgi.asgi_app`, explicit `set_mounted_prefix`, and Uvicorn. The mounted Citry subapplication is not relied on for root lifespan. |
| Bare WSGI | One small root WSGI dispatcher for the page and `/citry`, `citry.contrib.wsgi.wsgi_app`, explicit `set_mounted_prefix`, initialization before the server starts threads, and Waitress or another explicitly declared WSGI server. |

The host wrappers must remain visible. A shared example-only abstraction that
turns every framework into `run_project(host="...")` would defeat the reason
these projects exist.

### 5.7 Standalone, no-server starter

`examples/starters/standalone/` has no web framework, ASGI/WSGI callable,
Citry mount, signing secret, State, or Events. Its command renders the same
visual shell and initial Project Explorer data into a self-contained HTML
document using the document dependency strategy. It omits the server-backed
query control rather than rendering an interaction that cannot work.

It still demonstrates:

- typed kwargs and rich Python values;
- `template_data()`;
- parent/child composition and slots;
- `js_data()`;
- local Alpine `@click`, `x-show`, and `x-text`; and
- component CSS and the required browser runtime embedded into the document.

The generated file must open locally without a server and make no network
requests. Its browser test loads the produced `file://` document and exercises
the Alpine interaction. If Citry's settled document runtime cannot satisfy
that contract, implementation must surface the failure and revisit this
starter rather than quietly introducing an HTTP server.

The standalone README explains why Events are absent: without a Citry HTTP
transport there is nowhere to send a Python handler call. This is a real
capability boundary, not a reduced introductory mode.

## 6. Project file contract

### 6.1 Common inventory

Every project contains:

```text
README.md
pyproject.toml
uv.lock
.env.example        # web projects only
src/ or host-native application files
tests/
```

The exact source layout follows the host. Django keeps `manage.py`, settings,
URLs, and an application package. Flask may use an application factory.
FastAPI and the protocol starters may use a compact `src/<project>/` package.
The standalone project has a clear render entrypoint and a gitignored output
directory.

Each `README.md` includes:

1. what the project teaches;
2. prerequisites;
3. install, run, test, and clean commands for POSIX shells and any materially
   different Windows invocation;
4. the URL or generated-file path and expected visible result;
5. a short map from files to responsibilities;
6. the data-movement table as it applies to that project;
7. framework lifecycle and mount notes;
8. Events State and security caveats for web projects;
9. a production checklist and links to authoritative Citry/host guidance;
10. the supported Citry and Python versions.

### 6.2 Dependency policy

The standard `pyproject.toml` is the dependency source of truth. A starter
declares only:

- `citry`;
- its host framework, when any;
- the actual development server used by its run command; and
- project-local test dependencies in a development group.

It does not depend on repository packages by path. It does not duplicate the
same dependencies into `requirements.txt`. A checked-in universal `uv.lock`
makes the copied project reproducible while the standard metadata remains
usable by other installers.

Dependency bounds must represent the versions the example is tested against.
Automated dependency updates are accepted only when the project-local,
clean-copy, host, and browser tests all pass. One bulk lock refresh without
running the host matrix is not sufficient evidence.

### 6.3 Configuration and secrets

No real secret is committed. Stateful Events projects read `CITRY_SECRET`, or
the host's authoritative equivalent, and refuse to start when it is absent.
The README gives a copyable command for generating and exporting a development
secret. Tests supply a fixed test-only value through the environment.

Django uses its configured `SECRET_KEY` through Citry's public helper. The
example still treats the checked-in Django key, if a development fallback is
used at all, as development-only and requires an environment secret for a
production settings mode.

All workers for one application must share the same Citry signing secret.
State is signed, not confidential, and every handler treats it as client
input. The starter's deterministic search needs no authentication, database
authorization, or custom CSRF token, but its README must not generalize that
fact to credentialed mutations.

Django preserves its CSRF middleware and default cookie/header convention.
Other hosts preserve installed host middleware and Citry's always-on Events
request floor; their READMEs link to the custom-host-token recipe before a
reader adds authenticated state changes.

### 6.4 Quality and style

Starters should look intentional but remain framework examples, not Citry UI
showcases. They use a small local stylesheet, semantic HTML, visible focus,
labels, accessible loading/error status, and no external assets. Decorative
icons are inline and licensed or omitted.

Starter code favors explicitness over abstraction. Comments explain Citry- or
host-specific lifecycle boundaries, not ordinary Python syntax. Test-only
selectors are avoided when roles, labels, and visible results describe the
user contract adequately.

## 7. Demo contract and benchmark adaptation

### 7.1 Project Board

`examples/demos/project_board/` is a new application inspired by the large
benchmark page. "Inspired" permits copying and adapting useful component
shapes, deterministic data, and visual structure. It does not mean importing
the benchmark module, preserving its one-file layout, or requiring byte or
component parity.

The benchmark remains self-contained because its harness reads and slices
source to measure startup, import, first-render, and warm-render boundaries.
The demo must not become part of those measured imports without an explicit
benchmark redesign and re-baseline.

The adaptation must:

- record source provenance and preserve applicable attribution and license
  notices;
- split components and data into maintainable modules;
- replace fake request, bookmark, and CSRF objects with real application
  behavior or remove the affected controls;
- provide complete local CSS, JavaScript, icons, and routes;
- fix incomplete Alpine registrations and JavaScript handlers;
- use deterministic time and fixture data;
- implement or clearly disable every visible form, link, and action;
- exercise Events, forms, State, actions, Alpine expressions, slots,
  provide/inject, dependencies, and dynamic composition where they serve the
  application; and
- pass the browser-readiness gate below before it is linked as a public demo.

### 7.2 HTMX patterns

`examples/demos/htmx/` reimplements the examples from the MIT-licensed
`iwanalabs/django-htmx-components` project with FastAPI and Citry. It credits
the original project and preserves its license notice. The new version keeps
its sample data in memory and includes tests for its routes and browser
behavior.

The demo teaches three patterns in one small contacts application:

- filter contacts as the user types, without letting a slow response replace
  newer results;
- replace one contact row with its form, show server-side validation errors,
  and save the changes in that same row; and
- update the list of teams when the user chooses a department.

The code keeps each tool's job easy to see:

- FastAPI reads requests and updates the application data;
- HTMX sends requests and replaces parts of the page; and
- Citry renders each response and supplies its CSS and JavaScript.

The page loads the bundled HTMX file and Citry's browser script from the local
`/citry` mount. HTMX replaces the contents of plain `<div>` elements that
remain on the page. Each contact row keeps one of these wrappers so its Edit,
Save, and Cancel actions update only that row. Each HTMX route has its own URL
and serializes each component with `deps_strategy="fragment"` before returning
that output unchanged.

HTMX 2.0.8 and newer can ask Chromium to parse a response in a way that removes
HTML comments. Citry uses comments to mark where components start and end, so
the demo includes an HTMX extension that protects those comments while HTMX
parses and inserts the response. The extension recognizes only comments that
match Citry's client-graph v1 marker format and raises an error unless the
response uses `innerHTML` on a wrapper that stays on the page. The demo does
not use `hx-select`, out-of-band swaps, other swap styles, or direct insertion
into `<tbody>` and `<select>`.

This demo deliberately does not use Citry Events. Its README and public guide
tell people who are starting a new Citry application to try Events first. This
setup is for existing HTMX applications and teams that want to introduce Citry
one component at a time.

Browser tests use the same HTMX file that the demo serves. They exercise
search, editing and validation, and the department/team picker. They also
confirm that a newer search cancels an older one, the edit form's CSS loads
when the form opens, remains through validation, and is removed after Cancel
or Save. The page sends no Citry Events requests, and the browser reports no
unexpected errors.

### 7.3 Demo freedom and limits

A demo can add SQLite, `citry-ui`, i18n, uploads, or another integration when
that capability is part of its declared story. Such additions must be local,
deterministic, resettable, and tested. A demo must not require cloud accounts,
paid services, unpinned CDN assets, or personal credentials for its default
journey.

A demo README separates the shortest happy path from optional production or
integration setup. It states which visible features are real, which use local
fixtures, and which are intentionally out of scope.

## 8. Qualification model

Testing is layered because a rendered-string assertion cannot prove a host
starts, a route is mounted, a browser runtime loads, or an Event completes.

### 8.1 Project-local tests

Every project owns readable tests that a copier receives. These use only the
project and its declared dependencies.

For a web starter they cover:

- the host's real in-process test client or transport;
- application construction with a fixed test secret;
- a `GET /` response with status 200 and `text/html` content type;
- stable visible page content and escaped data;
- the configured Citry runtime URL under the mounted prefix;
- initialization through the host's intended lifecycle; and
- at least one Events route or manifest assertion that does not rely on a
  private Citry implementation detail.

For standalone they cover:

- the documented render command;
- deterministic output at the documented path;
- a complete HTML document containing the expected content; and
- no mounted or externally fetched Citry asset URL.

Framework configuration is isolated per project process. The repository test
runner must never import all starters into one Python interpreter, where
Django settings, registries, application globals, and identical package names
could contaminate one another.

### 8.2 Clean-copy qualification

The shared runner copies each cataloged project into a fresh temporary
directory outside the checkout. It then:

1. validates the copied inventory and lock;
2. installs the project in its own environment;
3. overlays the Citry artifacts under test when running against repository
   source or release candidates;
4. runs the cataloged project-local test command; and
5. proves that imports and commands do not depend on the repository root.

Release qualification uses built `citry` and `citry-core` wheels, not editable
source. This catches missing package data, incompatible dependency metadata,
and accidental reliance on the monorepo environment.

### 8.3 Real-server smoke

For each web starter, the shared runner:

1. allocates a loopback port;
2. starts the exact cataloged development-server command in a new process
   group with a test secret;
3. polls the page URL with a bounded timeout;
4. asserts the page status, content type, and visible sentinel;
5. fetches the mounted Citry runtime and checks for a successful JavaScript
   response;
6. records server output for failure diagnostics; and
7. terminates the complete process group on success, failure, or interruption.

There are no fixed ports, unbounded sleeps, daemon processes left behind, or
silent retries. A startup timeout prints the command, environment names (not
secret values), captured stdout/stderr, and the last connection failure.

### 8.4 Shared browser journey

All web starters must pass the same Chromium journey against their actual
spawned server:

1. load `/` and wait for Citry/Alpine readiness;
2. assert there are no unexpected console errors or failed same-origin
   resources;
3. open the help panel and assert the visible Alpine change;
4. prove that local interaction sent no Events request;
5. focus and edit the project query;
6. observe one debounced Events request under `/citry`;
7. assert a successful response, updated result count/cards, preserved input
   value and focus, and settled loading state; and
8. reload the document and prove deterministic initial state.

The standalone browser journey renders the output, opens the resulting
`file://` URL, performs the Alpine interaction, and asserts zero network
requests and console errors.

The browser profile is fixed in repository tests. A starter cannot weaken the
shared journey through project-local catalog flags. A project can add stronger
tests of its own.

### 8.5 Demo browser-readiness gate

A public demo additionally requires:

- explicit happy-path journeys for every claimed interaction;
- no missing local asset, broken internal link, failed request, unhandled
  page error, or unexpected console error;
- serious and critical automated accessibility findings resolved or recorded
  with a bounded, reviewed exception;
- keyboard coverage for the primary workflow;
- deterministic fixture reset between tests;
- a test for every visible form/action's success and meaningful failure path;
- no dependency on external network availability; and
- a manual visual and responsive review before first publication.

Screenshot comparison is optional and adopted only when a demo intentionally
owns a stable visual contract. It is not a substitute for semantic browser
assertions.

### 8.6 CI placement

Example qualification should have a dedicated Python workflow or dedicated
jobs with path filters that include:

- `examples/**`;
- Citry Python runtime and contrib adapters;
- the client runtime and wire protocol packages;
- Citry-core sources and version metadata;
- root Python dependency metadata and locks; and
- the example workflow and qualification tooling.

The proposed cadence is:

| Gate | Matrix |
|---|---|
| Pull request | Project-local and clean-copy tests on Linux at the oldest and newest supported Python; real-server and Chromium journey for every starter; demo journeys affected by the change. |
| Main branch | Same gate, with archive construction and inventory checks. |
| Weekly | The golden FastAPI starter, standalone starter, and public demos in Chromium, Firefox, and WebKit; host server smokes remain browser-independent. |
| Release candidate | Every project copied outside the checkout, installed with the exact candidate wheels, then tested, started, and exercised in Chromium. |

If framework support constraints differ by Python version, the catalog and CI
matrix state the supported intersection explicitly. A dependency resolver
skip is not counted as a passing starter.

## 9. Discovery, downloads, and versioning

### 9.1 Discovery layers

Root projects are surfaced through:

1. one concise "Start a project" call to action in the root README;
2. the root `examples/README.md` host and capability matrix;
3. links from the substantive Web frameworks documentation;
4. code-first docs pages that link to the relevant standalone project where
   useful; and
5. release-specific source and download links.

The root README should lead with FastAPI and link to the matrix rather than
embedding six full setup recipes. The docs Web frameworks guide continues to
own framework choice, lifecycle, mounting, security, production behavior, and
troubleshooting. Root project READMEs own exact project commands and file maps.

### 9.2 Version-correct links

The `main` branch examples target the current repository and may require an
unreleased Citry change. Released documentation must link to either:

- the example directory at the matching Citry release tag; or
- a deterministic archive built from that tag.

It must not link a released docs snapshot to the example on GitHub `main`.

Archive construction copies only the selected project inventory, preserves
text bytes and executable bits where intentional, excludes caches and generated
output, uses deterministic ordering and timestamps, and publishes a checksum.
Extracting an archive yields the same tree exercised by clean-copy
qualification. The docs site may link to that artifact; it does not ingest the
project as a docs-site example.

### 9.3 Compatibility updates

When a Citry release changes a public contract used by an example, the same
release work updates and qualifies the affected projects. A tagged example is
immutable historical guidance. Fixes for an old release use a patch tag or a
clearly versioned replacement artifact rather than rewriting a published
archive.

Generated GitHub Template repositories may be added later as read-only mirrors
for discoverability. The monorepo remains canonical, mirrors identify their
source tag and generated status, and pull requests to mirrors redirect to the
monorepo.

## 10. Adding, changing, and retiring projects

### 10.1 Add

A new project needs:

- a named reader job not already served by an existing project;
- an owner and project kind;
- a complete project-local inventory and README;
- a catalog entry and appropriate shared profile;
- project-local, clean-copy, and promised runtime/browser evidence;
- dependency and license review; and
- root/docs discovery updates proportional to its importance.

A framework adapter's existence alone is insufficient. The project must show
the complete host application and pass a real-host test.

### 10.2 Change

Reviews distinguish:

- **host wiring changes**, which require that host's project tests, server
  smoke, and browser journey;
- **shared starter behavior changes**, which require all starter profiles so
  the behavioral story does not drift;
- **Citry runtime/protocol changes**, which require every affected web
  starter and release-wheel qualification; and
- **demo-only features**, which require that demo's declared journeys and
  capability documentation.

Copying a starter into a temporary directory is part of review evidence, not
an occasional release cleanup.

### 10.3 Retire

A starter is retired only when Citry drops the host integration or replaces it
with a documented successor. Remove it from current discovery and the catalog,
but leave release tags and archives intact.

A demo can retire when its maintenance cost no longer proves a useful Citry
job. Retirement records the reason and preserves source history. A broken,
unqualified demo must not remain linked as if supported.

## 11. Delivery sequence

1. Add `examples/` ownership rules, catalog schema, qualification harness
   skeleton, and the shared Project Explorer contract.
2. Build the standalone and FastAPI starters first. Together they prove both
   document-only and full Events paths.
3. Add Django and Flask, including real framework clients, CSRF behavior, and
   actual server startup.
4. Add bare ASGI and WSGI after the shared runner proves prefix routing,
   lifespan/startup, and serving commands.
5. Add README/docs discovery and deterministic release archives when the first
   starters pass clean-copy qualification.
6. Adapt the benchmark-inspired Project Board into a browser-complete demo.
7. Reconsider `citry init` only after starter layouts and dependency choices
   have survived releases and user feedback.

The qualification harness lands with the first projects, not after the host
matrix has accumulated untested copies.

## 12. Alternatives rejected

### Put complete projects in `docs_site/examples/`

Rejected. The existing docs-native examples are optimized for page assembly,
focused teaching, and preview machinery. Complete host projects have a
different lifecycle, dependency, execution, and copying contract. Keeping the
surfaces separate makes both clearer.

### Keep projects in a separate canonical repository

Rejected for now. It would split compatibility changes, CI, issue ownership,
release tags, and review. Read-only generated mirrors remain possible later.

### Share one private component package across every starter

Rejected. It makes a copied starter incomplete and hides the code a learner
needs to modify. Small source duplication is accepted and controlled through
black-box behavioral qualification.

### Make the benchmark fixture the demo source

Rejected. Its one-file isolation and source-slicing are measurement contracts,
while a public application needs modularity, real assets/routes, browser
behavior, and independent evolution.

### Omit Events from beginner projects

Rejected for web starters. Events is a central Citry capability and the main
reason mounting Citry's HTTP routes matters. A starter that only returns a
rendered string would fail to demonstrate the useful host integration.

Events remain absent from standalone because that project deliberately has no
server transport.

### Add `citry init` with the first starters

Rejected for the initial delivery. A generator would freeze file inventories,
packaging, versioning, overwrite, and migration contracts before the examples
have validated those choices. Release-tagged copies and archives provide the
onboarding value first.

## 13. Falsifiability and open decisions

This design should be revisited if evidence shows that:

- independently installable starters cannot coexist sanely under the current
  uv workspace boundary;
- five self-contained host projects drift despite the shared black-box
  contract, making a reviewed generation step cheaper and clearer;
- real-server/browser qualification is too slow for pull requests, in which
  case measured sharding or tiering is required without dropping release
  coverage;
- local `file://` document activation cannot support the standalone Alpine
  promise;
- a project's host dependency no longer supports Citry's full Python range;
- release-specific archives cannot be made reproducible from tagged source;
  or
- users repeatedly need to initialize these projects in ways copy/download
  cannot serve, providing evidence to design `citry init`.

Implementation must still decide:

- the exact catalog TOML spelling and archive filename convention;
- whether the first project packages use a flat or `src/` layout where the
  host has no strong convention;
- the bounded server-start timeout from measured CI startup data; and
- whether the project-board demo uses plain local CSS or Citry UI as part of
  its explicit product story.

Those decisions do not change the ownership, starter behavior, Events,
standalone, or qualification contracts settled here.
