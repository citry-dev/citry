---
title: Versioning and support
description: Which Citry versions get fixes, how to pin Citry, what a 1.x upgrade can change in your project, and how deprecations work.
---

# Versioning and support

What each Citry release may change in your project, which versions get
fixes, and how to pin Citry.

## Pin and upgrade { #pin-citry }

Citry follows [semantic versioning](https://semver.org/){: target="_blank" rel="noopener"}.
Allow any 1.x release:

```toml
# pyproject.toml
[project]
dependencies = [
    "citry>=1.0.0,<2",
]
```

What each kind of release does:

- **Patch** (1.0.0 to 1.0.1): bug fixes. Code that uses
  [covered parts](#what-is-covered) needs no changes, except for a
  [security fix](#security-exception) that refuses input your code
  relied on. An open page's next event call may fail with the error
  code `stale_state`, which means the page is out of date (see
  [Rolling deploys](#rolling-deploys)).
- **Minor** (1.0.0 to 1.1.0): new features. Code that uses
  [covered parts](#what-is-covered) keeps working. A minor release may
  also:
    - deprecate a feature (it warns but still works, see
      [Deprecations](#deprecations));
    - change an [experimental feature](#experimental);
    - add a [check rule](#new-check-rules);
    - drop an end-of-life Python version, raise the oldest supported
      Django, FastAPI or Flask version, or move to a newer Vue minor
      version (see [Python and browsers](#platforms));
    - change the State token format, so an open page's next event call
      fails with `stale_state` (see [Rolling deploys](#rolling-deploys)).
- **Major** (1.x to 2.0.0): may remove deprecated features and make other
  breaking changes. The release notes say what to change.

Depend on `citry`, not `citry-core`. Each `citry` release installs the
one `citry-core` version it needs.

## Supported versions { #supported-versions }

- Bug and security fixes go to the newest 1.x minor release only. Once
  1.2.0 is out, a fix ships as 1.2.1, not as a 1.1.x release.
- With `citry>=1.0.0,<2`, upgrading gives you the newest 1.x release,
  the one that gets fixes.
- After 2.0.0 comes out, the last 1.x minor release gets security fixes
  only, for 12 months.
- 0.x releases get no fixes.

Other packages:

| Package | Versions | Which releases get fixes |
| ------- | -------- | ------------------------ |
| `citry-lsp` (editor support) | 1.x | The newest release |
| VS Code extension | 1.x | The newest release |
| `pygments-citry` (syntax highlighting) | 1.x | The newest release |
| `citry-core` | Its own numbers | The version a supported `citry` release installs |
| `citry-ui` | 0.x, alpha | The newest release |

- **`citry-ui`:** not covered by the 1.x rules, so a minor release may
  break your code. Pin one minor release, for example
  `"citry-ui>=0.6.0,<0.7"`.
- **`citry-lsp`:** every 1.x works with every `citry` 1.x, so you can
  upgrade either one first.
- **VS Code extension:** it runs the `citry-lsp` installed in your
  project and does not install it. Extension 1.x accepts `citry-lsp`
  0.1.x to 0.4.x and any 1.x, and for another version it shows "Citry
  unavailable" with the versions it accepts. Each extension release is
  tested with one `citry-lsp` release (extension 1.0.0 with `citry-lsp`
  1.0.0). No other pairing is promised, so keep both on their newest
  release.
- **`pygments-citry`:** the `citry` and `citry-html` lexer names keep
  working in every 1.x release.

## Python and browsers { #platforms }

The [Compatibility](/about/compatibility/) page lists the exact Python
versions, operating systems and wheels. How that list changes:

- **CPython:** every version still maintained upstream. A minor release
  may add a new version, and may drop one after its end of life (the
  release notes say so).
- **PyPy and free-threaded CPython:** best effort. Tested weekly, not on
  every change. The Compatibility page lists the known differences.
- **Django, FastAPI and Flask:** a minor release may raise the oldest
  supported version, for example after Django ends support for it. A
  patch release never does, and the release notes name every change.
- **Browsers:** the latest two versions of Chrome, Edge, Firefox and
  Safari, tested in Chromium, Firefox and WebKit.
- **Vue:** Citry ships one exact Vue version. A minor release may move to
  a newer Vue minor version; a new Vue major version needs a new Citry
  major version.

## Deprecations { #deprecations }

A deprecated feature keeps working for the rest of 1.x and is removed no
earlier than 2.0.0. Each use issues a `CitryDeprecationWarning` that
names the line in your code and what to use instead.

`CitryDeprecationWarning` is a `DeprecationWarning`, which Python hides
unless the line is in the script you ran directly. In a web server you
usually will not see it. To find every use, make it an error in your
tests:

```toml
# pyproject.toml
[tool.pytest.ini_options]
filterwarnings = [
    "error::citry.CitryDeprecationWarning",
]
```

To see it in a running server, add this to your startup code:

```python
import warnings

from citry import CitryDeprecationWarning

warnings.simplefilter("default", CitryDeprecationWarning)
```

## New check rules { #new-check-rules }

A minor release may add a `citry check` rule, so a CI job that passed
before can fail without a code change.

- The release notes list each new rule.
- A new rule never stops a template that renders today from rendering.
  It only reports in `citry check` and the editor.
- A rule that projects may reasonably disagree about gets a `rule_*`
  setting on `LintSettings`, so you can make it a warning (which never
  fails `citry check`) or turn it off (see
  [Change rule severity](/ide/template-linting/#change-how-strict-a-rule-is)).

Some rules have no setting. The [Diagnostics](/ide/diagnostics/) page
marks each rule you can change with "Your application can change this
severity".

## Rolling deploys { #rolling-deploys }

During a deploy that upgrades one server at a time, a page from an old
server talks to a new server, and the other way round. Citry supports
this between any two 1.x releases, not across 1.x and 2.x. What can
happen:

- **Event calls:**
    - old page to new server: accepted;
    - new page to old server: accepted, unless the new release added
      `citry-events/2`; then the old server answers `protocol_mismatch`.
- **Data an old page cannot read:** a State token (the signed copy of a
  component's State in the page), a render or a fragment written by
  another release. The page's next event call fails with the error code
  `stale_state`, or the fragment does not start. Citry fires events your
  app can use to tell the visitor (see
  [Handle out-of-date pages](/reference/browser-apis/#out-of-date-pages)).
  After a reload the page works with the new release.
- **[Render cache](/performance/caching/):** every upgrade, patch
  releases too, ignores entries that another Citry version wrote. While
  old and new servers share one cache, expect slower renders until the
  deploy finishes.
- **Browser runtime:** an old page loads the old runtime file. Clear
  whole-page caches and give every server one shared cache (see
  [Deploy a Citry upgrade](/advanced/web-frameworks/#deploy-a-new-version)).

## Events protocol { #events-protocol }

Server events exchange data in the `citry-events/1` protocol.

- No 1.x release changes or removes it, apart from the
  [security exception](#security-exception).
- A custom transport registered with
  [`Citry.events.registerTransport`](/reference/browser-apis/#citry-events-register-transport)
  keeps working across 1.x.
- A change that `citry-events/1` cannot carry arrives as
  `citry-events/2`, added beside it in a 1.x release.
- Running calls from your own server code with `EventsDispatcher` and
  `TransportContext` is [experimental](#experimental).

## State token lifetime { #state-token-lifetime }

Unless you keep State on the server (`State._storage = "server"`), Citry
sends each component's State to the page as a signed State token.

- Signed tokens and State kept on the server both expire 24 hours after
  Citry issues them, unless you set `State._max_age`.
- An expired token fails the call with `stale_state`. Show visitors a
  message for it, as
  [Handle out-of-date pages](/reference/browser-apis/#out-of-date-pages)
  shows.
- For a longer lifetime, set `State._max_age` to a longer `timedelta`.
  [Treat State as input](/security/#treat-state-as-client-input) explains
  why tokens expire.

## What the promise covers { #what-is-covered }

A covered part keeps working, as the docs describe it, in every 1.x
release. Covered, unless marked [experimental](#experimental):

- **Python names:**
    - every name in `citry.__all__`;
    - the `__all__` of each `citry.ext.<name>` package and each
      `citry.contrib.<name>` module;
    - the names in `citry.reload`.
- **Options that start with `_`** (the `_` keeps them from clashing with
  your handler and field names), when the docs or the
  [API reference](/reference/) tell you to set them:
    - `class Events`: `_guard`, `_context`, `_csrf`, `_methods`,
      `_debounce`, `_throttle`;
    - `class State`: `_public`, `_model`, `_storage`, `_max_bytes`,
      `_max_age`;
    - set in `extensions_defaults["events"]` (app-wide):
      `_max_body_bytes`, `_max_form_fields`, `_csrf_field_names`,
      `_csp_nonce`.
- **Components and templates:** the template syntax, component class
  attributes, and nested classes such as `Kwargs`, `Slots`, `State` and
  `Lint`.
- **Settings and extension hooks:** every setting and every documented
  hook.
- **Node classes:** the node objects Citry builds from a template, which
  extension hooks read as `ctx.nodes` (see
  [Walk deep node lists](/advanced/extensions/#walk-deep-node-lists)):
  the class names `citry` exports, such as `Node`, `ComponentNode` and
  `IfNode`, and the attributes extensions read.
- **Command line:** the `citry` commands and options, the JSON from
  `citry check --format json`, and rule names such as
  `citry.template.unknown-component`.
- **VS Code extension:** its settings and commands, such as `citry.app`
  and **Citry: Restart Language Server** (listed on the
  [VS Code page](/ide/vscode/)).
- **Browser JavaScript API:** what the docs teach, with the meaning they
  give, mostly on the [Browser APIs](/reference/browser-apis/) page:
    - `window.Citry` and its documented members;
    - `$component(...)` in component JavaScript;
    - the `onServerRender` callback;
    - the Events helpers such as `$state` and `$sendEvent`, and `$i18n`;
    - the `citry:events:*` DOM events and `citry:fragments:stale`.
- **HTTP routes** under Citry's prefix, such as the event routes and the
  runtime script addresses: paths, methods and meaning, so your
  forwarding or proxy rules keep working. Preview server routes are
  experimental.
- **Server events:** the [Events protocol](#events-protocol).

### Security fixes { #security-exception }

The one exception for every covered part: a 1.x release may refuse input
it used to accept, such as an Events call or a template value, when that
is needed to close a security hole. The changelog says so.

## What is not covered { #what-is-not-covered }

These may change in any release, even a patch release. If you rely on
one, pin the exact Citry version and read the release notes before each
upgrade.

- **Node constructor arguments:** Citry creates nodes itself.
- **Data in browser-only routes:** what the routes that only Citry's own
  browser code calls carry, such as event definition scripts and
  translated messages. Their paths and methods are covered.
- **Other `_` names:** any module, function, attribute or option that
  starts with `_`, except the options above and the experimental
  `_render_inputs` option, which follows the
  [experimental](#experimental) rules.
- **Deeper modules:** import from `citry`, `citry.reload`,
  `citry.ext.<name>` or `citry.contrib.<name>`, not from modules such as
  `citry.ext.events.handlers` or `citry.nodes`.
- **Browser internals:** globals, attributes and members no docs page
  teaches, such as `window.__citryRuntime`, the `data-citry-*` attributes
  in rendered HTML, and component members starting with `$citry`.
- **`citry-core`'s own API:** only `citry` is meant to call it.
- **Generated output:** the Python code the template compiler writes, the
  exact whitespace of rendered HTML, and error message text. Test what a
  page shows, and match errors by class, not message.

## Experimental features { #experimental }

Experimental features work and are tested, but their design is not
settled. They may change in a minor release; the release notes say so.
Each has an **Experimental** box on its [API reference](/reference/)
page, and a guide says so where it teaches one.

The release notes say when this list changes. Experimental now:

- `ComponentGraph`, its helper types such as `ComponentGraphNode`, and
  `Citry.inspect_component_graph()`
- the template analysis API behind `citry check`, `citry format` and the
  editor:
    - `Citry.template_analysis()`, `TemplateAnalysis`,
      `TemplateLintInfo`, `TemplateVariableInfo`, `TemplateLintConsumer`,
      `TemplateLintFinding`, `ComponentSourceLint`,
      `lint_unknown_template_variables()`;
    - names containing `PythonTemplate`, `python_templates`,
      `PythonComponentAsset` or `python_component_assets`
- hooks that let another template engine, such as Django templates, embed
  Citry tags:
    - `Extension.on_template_foreign_spans()`,
      `Extension.on_template_foreign_compiled()`;
    - classes starting with `Foreign` or `OnTemplateForeign`;
    - `CompiledBody`, `render_compiled_body()`,
      `collect_compiled_body_fills()`
    - the errors Citry raises when it cannot put such an engine's
      output inside an interactive component: `StaticHtmlError` and
      its subclasses `IncompleteStaticHtmlError`,
      `VueInsideStaticHtmlError`, `ScriptInStaticHtmlError`,
      `VueSyntaxInStaticHtmlError` and `StaticHtmlPlacementError`
- component previews (`citry.ext.preview`)
- the `"payload"` render cache mode, with
  `Extension.export_render_cache()` and `Extension.stage_render_cache()`
- `Extension.browser_plugin()` and `Extension.prepare_browser_render()`
- the Events extension hooks `on_event`, `on_event_result`,
  `on_event_error`
- `EventsDispatcher` and `TransportContext` (running event calls from
  server code instead of Citry's HTTP routes)
- the `event_result_resolvers` and `event_payload_codecs` settings
- the `_render_inputs` option, in `class Events` or
  `extensions_defaults["events"]`, and its `RenderInputs` type
  (request values for `Render` actions)
- `RenderFrame` and `CitryRender.frame`
- returning asset tags apart from the HTML: the `"separate"` value of
  `DepsPosition`, `SerializedAssets`, the `runtime_assets`,
  `app_assets` and `component_assets` fields of `SerializedRender`,
  `CitryRender.needs_browser_runtime()`, `combine_assets()`,
  `SerializedAssetEntry` with the `css_entries` and `js_entries`
  fields of `SerializedAssets`, and `OutsideSlotContentError`
- `CitryRender.has_server_events()`
