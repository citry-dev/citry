# Design: the Preview extension

**Status: implemented, 2026-09-09.**

Preview lets authors keep useful examples beside their components, open one
example in a browser, and capture it from the CLI. A component declares a
nested `Preview` configuration with named variants and, optionally, a template
that composes several components. The same examples appear in a gallery for one component or for every selected
component.

The recommended first release provides single-variant pages, a gallery, custom
variant and page layouts, persistent serving, and PNG capture. Preview endpoints
exist only in a server created by a preview command. Interactive controls and
fixture orchestration remain later work.
Preview-specific symbols and commands below describe the implementation.
Existing Citry APIs used by the extension are identified separately.

## 1. Existing APIs and prior work

The design follows the checked-in Python implementation. Some older sections
of design documents describe historical implementation states.

| Source | Existing behavior used here |
| --- | --- |
| [`extension.py:596`](../../packages/py/citry/citry/extension.py#L596), `ExtensionConfig` | A nested configuration inherits the extension's `Config`; `component_class` is bound by the manager. It can be instantiated with `None` outside a component render. |
| [`extension.py:1681`](../../packages/py/citry/citry/extension.py#L1681), `_init_component_class` | Effective configuration follows component declarations, engine defaults, then extension defaults. |
| [`extension.py:641`](../../packages/py/citry/citry/extension.py#L641), `Extension` | Extensions expose command classes and neutral HTTP routes and have an engine-bound `self.citry`. |
| [`citry.py:1153`](../../packages/py/citry/citry/citry.py#L1153), `components` and `inspect_components` | The registry is a name-to-class mapping; inspection supplies canonical names, aliases, source files, and identities. |
| [`citry.py:329`](../../packages/py/citry/citry/citry.py#L329), `render_template` | Trusted source plus variables, slots, template globals, root provides, and origin produces a `CitryRender`. It does not accept a template filename as source. |
| [`citry_element.py:130`](../../packages/py/citry/citry/citry_element.py#L130), `render` | Rendering creates fresh instance state and accepts explicit root provides and template globals. |
| [`citry_render.py`](../../packages/py/citry/citry/citry_render.py), [`component_like.py`](../../packages/py/citry/citry/component_like.py) | Elements and structured render results compose without first becoming HTML strings. `ComponentLike` can resolve a fresh element in the active engine. |
| [`contrib/asgi.py`](../../packages/py/citry/citry/contrib/asgi.py), [`util/routing.py`](../../packages/py/citry/citry/util/routing.py) | Existing adapters serve the engine's routes and dependencies through `RouteRequest`, `RouteResponse`, and `URLRoute`. |

Read alongside [`extensions.md`](extensions.md),
[`extensions_commands.md`](extensions_commands.md),
[`component_rendering.md`](component_rendering.md), and
[`codebase.md`](../codebase.md). Preview belongs in the Python extension layer;
this proposal requires no Rust grammar, AST, compiler, language implementation,
or PyO3 changes.

The existing [Storybook research](extensions_storybook.md) and
[Citry UI scenario catalog](ui_research/scenario-catalog.md) cover richer
workflows, fixture lifetime, browser actions, and tool projections. Preview
provides a smaller authoring and rendering facility. A future adapter can
read explicitly selected scenario examples through public APIs; Preview does not
require Citry UI to move its scenario catalog into nested component classes.
The existing Storybook spike's readiness and isolation findings apply here,
particularly to focus, teleports, global listeners, and server events.

## 2. Authoring previews

Enable the bundled, optional extension when constructing the development app:

```python
from citry import Citry, Component
from citry.ext.preview import PreviewExtension, variant

app = Citry(extensions=[PreviewExtension])
```

The extension class is `PreviewExtension`, with `name = "preview"` and explicit
`class_name = "Preview"`. Component declarations remain `class Preview:`.
Install it before defining or discovering components. Installation registers
configuration and commands only. Even an application that installs the extension
has no preview endpoints in its ordinary server; `serve` and `render` create
the separate server that registers them.

### Direct component variants

A preview without a template renders its owning component with the selected
variant's `params`. This is sufficient for the Button example:

```citry
class Button(Component):
    citry = app
    name = "button"

    class Kwargs:
        label: str = "Save & Test Connection"
        size: str = ""
        disabled: bool = False
        focused: bool = False

    class Preview:
        group = "Primitives"

        def variants(self):
            return [
                variant(
                    slug="default",
                    label="Button / default",
                    description="Primary action, default size.",
                    params={"label": "Save & Test Connection"},
                ),
                variant(
                    slug="small",
                    label="Button / small",
                    params={"label": "Save", "size": "small"},
                ),
                variant(
                    slug="disabled",
                    label="Button / disabled",
                    params={"label": "Confirming...", "disabled": True},
                ),
                variant(
                    slug="focus",
                    label="Button / focus-visible",
                    description="Authored visual focus example.",
                    params={"focused": True},
                ),
            ]

    def template_data(self, kwargs, slots):
        classes = ["button", kwargs.size]
        if kwargs.focused:
            classes.append("is-focused")
        return {
            "label": kwargs.label,
            "disabled": kwargs.disabled,
            "class_name": " ".join(filter(None, classes)),
        }

    template = """
        <button c-class="class_name" c-disabled="disabled">
            {{ label }}
        </button>
    """
```

`variant()` constructs a `Variant` data record. `label` and `description` are
preview metadata; a button's visible text lives in `params["label"]`. Use
`params` consistently, with no second `args` alias. Citry's ordinary `Kwargs`
schema remains the component input contract.

`variants(self)` runs on the effective config, constructed as
`component_class.Preview(None)`. Authors may use `self.component_class` to
refer to the owner; there is no live `self.component` during enumeration.
Return an ordered list or tuple of `Variant` records. The method is synchronous
and must describe examples deterministically, without database mutation,
network work, or browser setup. Inherited methods receive the subclass as
`self.component_class`.

### Templates for composed examples

Use a template when an example needs children, slot markup, providers, or a
particular HTML parent. It receives two variables: `params` for example inputs
and `preview` for read-only component and variant metadata.

```citry
class Accordion(Component):
    citry = app
    name = "accordion"
    # Ordinary component implementation omitted.

    class Preview:
        template = """
            <c-accordion>
                <c-accordion-item>
                    <c-accordion-header>
                        {{ params["heading"] }}
                    </c-accordion-header>
                    <c-accordion-body>
                        Body 1
                    </c-accordion-body>
                </c-accordion-item>
            </c-accordion>
        """

        def variants(self):
            return [
                variant(
                    slug="default",
                    label="Two levels of composition",
                    params={"heading": "Heading 1"},
                ),
            ]
```

The Accordion fragment assumes the application registers the shown components
with compatible slots. An authored template owns the whole example: Preview
does not also render the owning component. In template mode `params` are
variables, not automatically forwarded kwargs. Missing variables or invalid
child inputs fail through normal Citry rendering.

`template_file = "accordion.preview.citry-html"` is the file alternative.
`template` always means inline source; strings are never guessed to be paths.
Resolve a relative file beside the Python class that authored that declaration,
including inherited declarations. Absolute author-configured paths are allowed.
Read UTF-8 and retain the absolute path as the render origin for diagnostics.
Missing files, decoding failures, and unknown declaration origins are errors.
No path or source can be supplied by a URL request.

## 3. Configuration and validation

`PreviewExtension` implements `Extension.Config` using `ExtensionConfig` and the existing
configuration validation hooks. It validates field names and values rather
than relying on Python annotations to enforce them.

| Component field | Default and behavior |
| --- | --- |
| `enabled` | `None`: participate when the component declares or inherits preview content or a variants method. `True` explicitly enables direct rendering with defaults; `False` opts out. Only `None` or actual booleans are accepted. |
| `group` | `None`; otherwise a nonempty display string. It does not affect identity or filesystem paths. |
| `template`, `template_file` | Both `None`; select direct mode. Exactly one may be non-`None`. Source must be a nonempty string; file must be a nonempty string or `Path`. |
| `variants()` | If not overridden, yields one `default` variant with empty params and the component name as label. An override returning an empty sequence declares no available variants. |
| `viewport` | `Viewport(width=1280, height=800, device_scale_factor=1)`. Positive integer dimensions up to 8192; finite scale greater than zero and at most 4. Booleans are not numbers here. |
| `variant_layout` | `None`, meaning pass the example through without a wrapper. Otherwise a `Layout` value as defined below. |
| `page_layout` | Built-in complete HTML document; otherwise a `Layout` value. |

Engine defaults use `extensions_defaults={"preview": {...}}` and accept only
`group`, `viewport`, `variant_layout`, and `page_layout`. Reject `enabled`,
`template`, `template_file`, and methods at this site. Global defaults affect
presentation but do not make every registered component previewable. Participation checks authored component
configuration, using the public declaration-inspection context rather than
presence of the manager-generated `Preview` class.

Normal nested-class inheritance applies. Sequences returned by `variants()`
replace, rather than implicitly concatenate, a parent's sequence. A subclass
can explicitly extend `super().variants()`. Conflicting effective inline and
file templates are errors; override the inherited alternative with `None`.
`enabled=False` wins over inherited content.

`variant()` accepts keyword-only fields:

- Required `slug`: `[a-z0-9]+(?:-[a-z0-9]+)*`, at most 80 characters; unique
  within the component. Never derive identity from the label or list index.
- Required `label`: a nonempty string. Optional `description` is plain text,
  defaulting to `""`; neither field is interpreted as HTML or Markdown.
- `params`: a string-keyed mapping, default empty. It may contain ordinary
  Python values and is not required to be JSON serializable.
- `viewport`: optional override of the effective component viewport.

Unknown fields, duplicate slugs, wrong return types, awaitables, and invalid
values raise a Preview configuration error naming the component and field.
Validate declarations without executing variants during component registration;
validate returned records when building a preview catalog, before browser
startup. In direct mode, validate params against the owning `Kwargs` through
the normal component input path when rendering. Do not claim that annotations
provide runtime validation beyond what Citry already enforces.

Copy mappings when constructing records and when preparing each render. Records
are immutable at the top level; arbitrary nested Python objects cannot be made
immutable safely. Authors must return fresh mutable values from `variants()`
and treat them as render inputs. Enumerate afresh for each request, never keep
instances or arbitrary params in a process-global catalog. Stateful fixtures
and teardown belong to the later scenario integration.

## 4. Render content, then apply two layout levels

The renderer constructs a fresh example, wraps it if requested, embeds it in a
complete page, and serializes once at the HTTP boundary:

```text
component + variant slug
  -> fresh example content
  -> optional variant layout
  -> page layout
  -> CitryRender.serialize(deps_strategy="document")
  -> HTML response
  -> browser initialization and PNG capture
```

Direct mode composes a `CitryElement` for the owning component. Template mode
uses a lazy `Slot` that calls `Citry.render_template()` with the specified origin
and variables. `SlotContext.provides` supplies the values active at the insertion
site, and the renderer passes its root template globals explicitly. Both paths
return structured `CitryRender` values for the outer page to serialize.

Keep the example as a lazy `Slot` until the page renders it. Each insertion
creates a fresh render occurrence. Do not cache a
rendered subtree or concatenate serialized HTML to build galleries: rendering
within the final tree gives each occurrence fresh state and IDs, lets provides
reach children, and lets Citry collect CSS, JavaScript, and Events metadata.
If implementation needs a direct nested render, every root-provided value must
be passed explicitly and the result kept structured until final serialization.

### A common layout value

Use `Layout(template=...)`, `Layout(template_file=...)`, or
`Layout(component=SomeComponent)`. Exactly one source is required. A component
must belong to the active engine. Inline/file templates compile as ordinary
Citry templates. Layout files resolve relative to the declaration owner using
the same rules as preview files; engine-default relative paths resolve from
the process working directory captured when the extension is attached. Citry
has a list of asset search directories, not a single application-root setting.
Use absolute engine-default layout paths when running from different directories.
Invalid source combinations, missing files, and cross-engine components fail
before serving a successful preview.

Both template and component layouts receive a `preview` input and a named
`content` slot. Component layouts accept `preview` through `Kwargs` and declare
the `content` slot using ordinary Citry schemas. A variant layout receives the
component and variant metadata; a page layout receives a `PreviewPage` record
with `selection` (`"variant"`, `"component"`, or `"all"`) and ordered component
groups. Each group has component metadata and ordered
`PreviewItem` values. Each item contains variant metadata and a lazy `content`
value that composes the example with its variant layout. A single-variant page
has one group and one item. Metadata records contain no renderables; page items
carry renderables separately. Neither exposes live component instances or
arbitrary params.

A variant layout can show labels without changing the example:

```python
Layout(template="""
    <section>
        <h2>{{ preview.variant.label }}</h2>
        <p>{{ preview.variant.description }}</p>
        <c-slot name="content" />
    </section>
""")
```

A page layout owns `<!doctype html>`, `<html>`, `<head>`, and `<body>`, and
places its content slot once. It can supply global CSS, themes, providers, and
ordinary Citry dependency placeholders. The built-in page adds document
metadata and a neutral body without navigation or cards. A preview template
is a fragment; full documents belong in a page layout. Do not attempt to detect
and repair arbitrary document markup. The author owns valid HTML, including
proper parents for table rows and options.

A layout normally places `content` once. Built-in layout tests verify that
placement. Custom layout authors own omitted or repeated content, just as they
do for ordinary Citry slots; Preview does not add runtime insertion counting.
Each repeated insertion must compose fresh elements and IDs. Supplying a layout
whose schemas cannot accept the inputs fails with component context. An empty
custom layout can render successfully, so use an explicit readiness selector
when capture must prove that a particular example is visible.

### Galleries use the same declarations

The first release supports three page selections: one variant, all variants of
one component, and all variants of all selected components. `/gallery` shows the
command's entire selection; `/gallery?component={component_id}` narrows it to one
component. Single-variant URLs stay independent of gallery presentation.

For a gallery, `PreviewPage.components` holds ordered groups of `PreviewItem`
values. Each item's `content` composes the selected embedding, while a
single-variant page item's content composes the example directly. A custom page
layout may render the prearranged `content` slot or iterate these groups to build
its own grid. Authors may deliberately filter or repeat items; every insertion
creates a fresh occurrence. A component's page layout applies to its individual
preview and single-component gallery; the all-component gallery uses the engine
page layout. Per-component variant layouts apply around each example.

The built-in gallery shows component names, variant labels and descriptions,
and links to individual previews. It groups components by canonical name in
catalog order and preserves declared variant order. An empty selection shows a
clear empty state. Custom page layouts receive the same items and can provide
a different arrangement using either templates or component classes.

The first release uses iframe embedding. Each frame loads the ordinary
single-variant route, including that component's page and variant layouts. The
gallery shows its own label and description outside the frame, so those remain
available even if a preview fails. It does not silently substitute a neutral
page layout. Authors who want different framing can supply custom layouts.

A frame's CSS width and height are the variant's declared viewport dimensions;
its container scrolls when the available gallery width is smaller. Do not shrink
frames to fit, because that would change responsive behavior. Browser zoom and
device scale belong to the containing browser context; an iframe cannot apply
its own `device_scale_factor`. Individual CLI captures still use each variant's
full viewport and scale. Frames load eagerly in the first release; pagination,
lazy loading, and automatic content-height sizing remain later work.

Frames isolate documents, CSS, focus, and teleport targets. Same-origin frames
still share server data and may share storage; they do not isolate fixtures.
A failed frame leaves the other previews usable and displays the single-page
route's error response. Serving the gallery does not wait for all frames to
finish application work. The PNG command captures individual variants; gallery
screenshots and aggregate readiness remain later work.

Future inline embedding can reuse the same page items, but requires an explicit
mode because CSS, authored DOM IDs, focus, listeners, and teleport targets share
one document. It also has one effective viewport. The first release does not
expose an inline-mode option.

## 5. Discovery, identity, and HTML routes

Initialize the selected Citry app through its existing discovery lifecycle.
Exclude the extension's internal rendering and layout components from the
preview catalog. Take a
registry snapshot, group aliases by exact component class, and use
`inspect_component()` metadata to obtain canonical names, `class_id`, and
`python_file`. Render each class once. Do not discover Python subclasses outside
that engine or scan arbitrary import paths supplied by a request.

A variant's identity is `(component class_id, variant slug)`. Class IDs survive
label and variant-order changes, but module/class renames can change them.
Registered component names and aliases are user-friendly CLI selectors. Sort
components by canonical name and preserve each declared variant order.

The command-owned server registers these routes below `ext/preview/`:

| Route | Response |
| --- | --- |
| `catalog` | Version-1 JSON containing component IDs, names, groups, variant slugs, labels, descriptions, viewports, and generated render URLs. No params, source paths, or Python object serialization. |
| `render/{component_id}?variant={slug}` | Complete HTML for exactly one selected variant. |
| `gallery` | HTML containing every component and variant selected by the command. |
| `gallery?component={component_id}` | HTML containing the selected variants of one component. |

The catalog response is an object with `service="citry-preview"`,
`version=1`, and an ordered `components` array. The marker identifies the
command service for CLI compatibility checks. The catalog path remains JSON;
`gallery` serves HTML. The command selection
limits catalog entries, gallery items, and render targets; excluded targets
return 404. Components used inside an example remain normally renderable.

The render route requires an explicit slug, including `default`; avoid unstable
numeric indexes. Gallery accepts only the optional `component` query key;
catalog accepts no query keys. Missing required, blank, repeated, or unknown
query keys return 400. An unknown component,
unknown variant, or disabled preview returns 404. Render/configuration failures
return 500 with a concise preview error; CLI reports the failing identity and
server logs retain the exception. Routes accept GET and HEAD, with HEAD omitting
the body. Other methods return 405. Responses use `Cache-Control: no-store`.
A catalog failure is explicit rather than silently dropping invalid previews.

Use the existing `URLRoute` and `RouteResponse` APIs to describe the command's
routes. `PreviewExtension.urls` remains empty at all times. A command-owned
host assembles an immutable preview route table at `/citry/ext/preview/` and
serves ordinary Citry dependency and Events routes through the existing ASGI
adapter at `/citry`. Preview dispatch belongs only to this host, not to
`Citry.urls` or the application's host. Do not toggle a global flag, mutate the
extension list, or temporarily expose routes on a shared application engine.
The command host must apply the existing request/response conventions; if
reusing them needs a general adapter API addition, review that addition before
implementation.

Build URLs with `Citry.build_url()` using the relative extension path and the
command host's recorded mount. Encode path segments and query values explicitly;
`build_url()` only joins strings. HTML responses use
`text/html; charset=utf-8`; catalog responses use JSON content type.

The extension's `PreviewRenderer` accepts explicit `provides` and
`template_globals` and returns `CitryRender`. The command host invokes it;
it does not automatically recreate application middleware, cookies, CSRF,
request-scoped provides, static routes, or fixture setup. Examples requiring
those facilities need a separately approved command-host integration. Do not
mount preview handlers into the real application as a workaround, read private
Events state, or add Preview-only fields to peer extensions.

Hot reload rebuilds component configuration through the existing engine
lifecycle. A render request resolves the current class generation. A CLI batch
compares the catalog's IDs, slugs, and labels before capture and fails if they
change during the batch; captures may reflect different source revisions if an author edits files
during the batch. Preview and layout files are reread on each request. The command does not
start a Python watcher; restart it after Python changes.

## 6. Serve, capture, and server lifetime

Register `ServeCommand` and `RenderCommand` through `PreviewExtension.commands` using `ExtensionCommand`,
`CommandArg`, and `self.citry`. The existing command runner owns parsing and application selection. Implement
`handle(..., **kwargs)` because it also receives parent-command options. Write
diagnostics to stderr and raise `SystemExit(1)` after reporting failures: the
runner ignores the return value of `handle()` and otherwise returns success.

```sh
citry --app project.citry_app:app ext run preview serve
citry --app project.citry_app:app ext run preview serve Button,Table --port 8001
citry --app project.citry_app:app ext run preview render
citry --app project.citry_app:app ext run preview render Button,Table
citry --app project.citry_app:app ext run preview render \
  --dir 'components/layout/**' --outdir ./preview_imgs
citry --app project.citry_app:app ext run preview render Button \
  --variant small --base-url http://127.0.0.1:8001/citry
```

Both commands accept component names, `--dir`, and `--variant` with the same
selection rules. No selector means every enabled component with at least one variant. Explicit
names are comma-separated; strip surrounding whitespace and reject empty
entries. Unknown names and explicitly selected components with no available
previews fail before starting a server or browser. Repeated aliases collapse to one
class. `--variant` is repeatable and selects slugs on every selected component;
a selected component lacking a requested slug is an error.

`--dir/-d` is repeatable. Match normalized component `python_file` paths relative
to the CLI working directory using path-segment globs: `*` stays within a segment and `**`
matches zero or more segments. A plain directory selects descendants. Patterns
combine by union; when names are also supplied they are intersected with that
selection. An explicitly named component excluded by the filter is an error.
Classes without a known source path do not match; report them if explicitly
selected. Filters never import extra modules. A supplied filter matching
nothing is an error. With no filters and no previews, `render` exits successfully
with a zero-result message; `serve` stays running with an empty gallery. Reject absolute filter patterns and `..` segments;
components outside the working directory remain selectable by name.

`--outdir/-o` defaults to `./preview_imgs` relative to the CLI working directory.
Write `<component_id>/<slug>.png` and a version-1 `manifest.json` with ordered
identities, labels, viewport, URL, relative output path, success/failure, and
concise diagnostics. Validate every output segment and resolved path remains
inside the output root. Fail preflight if an output exists unless `--overwrite`
is supplied. Overwrite only selected files; never delete unrelated images.
Write successful PNGs atomically. Reserve manifest output too; partial runs
still emit a manifest and return nonzero. Fatal setup errors return nonzero
without claiming any completed captures.

### Persistent serving

`serve` initializes the selected engine, validates the selection, and starts
the command-owned loopback server. It prints the gallery and catalog URLs and
stays alive until interrupted. Automatic Python reload is deferred: restart
`serve` after Python changes, and refresh the browser after preview/layout file
changes. It neither imports nor launches Playwright, and
does not open a browser automatically. `--port` defaults to 8001; accept integers
from 0 through 65535, with 0 requesting an OS-assigned port. An occupied explicit
port fails with a clear error. Binding is `127.0.0.1` in the first release.
Capture-only flags (`--outdir`, `--overwrite`, `--base-url`, `--timeout`, and
`--ready-selector`) are not accepted by `serve`.

`serve` exposes the catalog, gallery, and individual rendering endpoints for as
long as its server runs. Stopping it closes the listener and its resources.
An ordinary application server has no preview routes before, during, or after
this command, even if it imports the same app module in another process.

### Capture server choices

`render` offers two server modes:

- With `--base-url`, connect to a server already started by `preview serve`.
  The URL denotes that server's mounted Citry root, not the real application's
  root. Require the catalog's version-1 preview service marker and verify the
  requested identities exist in its selection. It may expose a superset of the
  capture selection. A missing marker or incompatible selection is an error;
  never add routes to the target server. Resolve local metadata without URL
  generation; remote mounted paths resolve against the supplied origin. Reject
  non-HTTP(S) URLs, query/fragment, or catalog URLs leaving that origin. Do not
  stop the persistent server after capture.
- Otherwise, start the same command-owned host used by `serve` on an OS-assigned
  loopback port. Register the same routes, including `/gallery`, and keep the
  host running concurrently with browser work. Stop it when capture completes.

`serve` and `render` without `--base-url` explicitly initialize the engine,
record the command host's mount with `set_mounted_prefix("/citry")`, and wait for
a bounded runtime-route startup health check (default 10 seconds). `render --base-url` only
validates the existing remote service within that timeout; it does not set a
local mount or start a host. The ASGI adapter alone does not initialize the engine.
Use an isolated CLI process with its selected engine; overlapping host sessions
on one engine are unsupported and must fail before changing its mounted prefix.
Clean up the owned listener, server task, and browser resources in `finally`,
including startup errors and interruption. A missing server or failed startup
must terminate with a diagnostic, not hang waiting for endpoints.

Recommend Uvicorn and Playwright under the package-owned `citry[ext-preview]`
extra. Rendering HTML and importing the extension must not import those optional
dependencies. `serve` requires the server dependency only; `render` also checks for Playwright
and Chromium before capture startup. Missing dependencies produce an actionable
installation error. Choose dependency versions against the
workspace lock during implementation; do not add Node or Storybook dependencies.

Use one Chromium browser and a fresh browser context per variant, with its
viewport and scale. Capture the full page by default, including its selected
layouts. A fixed viewport determines responsive CSS, while full-page capture
may be taller. Element-only crops, alternate browsers, and parallel captures
are deferred.

Readiness is bounded by `--timeout` (positive finite seconds, default 30 per
variant). Wait for successful HTML navigation, document load, the optional
visible selector, and fonts and image decode. Capture does not wait directly
on Citry's ownership initialization API. `ownership.whenReady(revision)`
promises a particular ownership graph, not completion of all application work.
`networkidle` is not a readiness contract for polling or Events components.
Provide `--ready-selector` as an optional application-owned visible-state wait;
invalid selectors and timeouts fail the variant. A rendered page is not proof
that a delayed application task has finished. Real focus-visible states and
user interaction journeys remain authored browser tests, not inferred from a
variant's display label.

Disable CSS animations for the screenshot through Playwright's screenshot
options; this does not freeze JavaScript clocks or external data. Record browser
errors and failed resource requests, failing captures on uncaught page errors,
non-success preview responses, or required asset failures. Continue after a
variant failure, close its context, and report aggregate failure. Visual output
is only repeatable when fonts, data, environment, and fixtures are repeatable.

## 7. Implementation boundaries and alternatives

`citry/ext/preview/` contains configuration/records, selection, rendering,
routes, command hosting, and browser capture in separate modules.
Export `PreviewExtension`, `variant`, `Variant`, `Viewport`, `Layout`, and the public page
metadata types from `citry.ext.preview`. Keep it out of built-in extensions.
The extension is stateless for render caching: it stores declaration ownership
and configuration, not state for an individual render.

Implementation evidence and remaining limits:

1. Lazy slots pass root globals and insertion-site provides to ordinary public
   rendering calls. Repeated slots receive fresh IDs and merge dependencies.
   Focused tests cover component and template layouts, inherited file origins,
   file refresh, and missing-file failures. No new core rendering API was needed.
2. Capture waits for document load, the optional visible selector, and then
   fonts and image decode before taking the screenshot. There is no whole-application readiness claim.
   The browser test uses a selector set by the component's JavaScript callback.
3. Preview and layout files are read per request. Python changes require
   restarting `serve`; browser refresh is sufficient for file-template edits.
4. The command host uses a separate ASGI dispatcher and existing neutral routing
   values. Tests verify `Citry.urls` never gains preview handlers, ordinary
   adapters return 404 during preview serving, and the listener closes on exit.
5. Browser verification exposed a general serialization defect: interior loop
   renders inside a transparent nested template emitted duplicate instance caps.
   The serializer now scopes transparent-frame traversal to the frame being
   joined, so interior fragments do not repeat its boundary. Regression tests
   exercise plain template rendering without Preview, nested loops, provided
   values, and inherited markers; no browser protocol or Rust change was needed.

Alternatives considered:

- A render hook activated by ambient context makes nested previews and ordinary
  component calls depend on hidden state. Explicit selection at the route or
  Python service is easier to compose and test.
- Requiring a template for every Button-like example duplicates ordinary
  component invocation. Direct mode keeps simple examples short while template
  mode handles meaningful compositions.
- The first gallery uses existing single-variant pages in iframes. Inline
  galleries, automatic frame sizing, and gallery capture remain later work so
  their shared-document behavior does not delay browsing examples.
- A Storybook dependency would introduce a second frontend application for a
  workflow Citry can serve itself. The separate Storybook research remains
  available for consumers who want its Controls and addons.

## 8. Validation and delivery

Use the smallest test that proves each behavior. Do not add release jobs
or a screenshot baseline matrix for this extension.

1. **Records and discovery:** focused Python tests for validation, inheritance,
   implicit defaults, opt-out, duplicate slugs, aliases, source filters, and two
   engines. These are fast local and ordinary Python CI checks.
2. **Rendering and routes:** test direct and template modes, inline/file layouts,
   inherited origins, missing files, escaped metadata, provides, dependency
   placement, repeated renders with fresh IDs, built-in content placement, repeated custom slot insertion,
   URL prefixes, HEAD, malformed queries, gallery filtering, and errors. Verify
   ordinary application adapters expose no preview endpoints even with the
   extension installed and a command host active. Reuse current route and
   render fixtures rather than duplicating adapter suites.
3. **CLI orchestration:** fake browser/server boundaries for selection, safe
   output paths, overwrite, partial failures, timeouts, catalog changes, and
   cleanup after interruption, persistent serve shutdown, port conflicts, and
   capture against an existing serve session. Verify `serve` works without
   importing Playwright. This belongs in normal Python tests.
4. **One focused Chromium test:** start the temporary host, render a composed
   interactive example with actual assets, wait for visible readiness, capture
   two variants, and verify the PNGs and manifest. Add one failure/cleanup case.
   Reuse the existing browser CI lane; target seconds, not a new long matrix.
5. **Gallery checks for this release:** verify all-component and single-component
   pages, custom template/component layouts, frame dimensions, links, empty
   selections, and an individual frame failure. In a focused browser case prove
   CSS and teleport targets stay within each frame and focus remains usable.
   Inline composition and aggregate screenshot readiness remain deferred.

Update public extension/CLI docs, package exports, optional dependencies and
`uv.lock`, package-owned release notes, and affected API-reference listings in
the implementation change. Run focused checks while developing and the required
repository profiles at the settled integration boundary per `codebase.md`.
The implementation includes the package extra, public reference entries, a
preview guide, command tests, and the focused browser check described above.

## 9. Delivered scope

The first release includes `PreviewExtension`, nested `Preview` configuration,
`variant(..., params=...)`, direct and template modes, custom variant/page
layouts, `/gallery`, persistent `serve`, and individual PNG capture with `render`.
Preview routes are registered only by the command-owned server. Interactive
controls, state editing, inline galleries, gallery screenshots, fixture
setup/teardown, and application-host integrations remain later scopes.
