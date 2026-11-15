---
title: Versioning and support
description: What a Citry 1.x upgrade can and cannot change in your project, how deprecations work, which versions get fixes, and which Python versions and browsers Citry supports.
---

# Versioning and support

Read this page before you upgrade Citry or decide how to pin it. It says
what each kind of release may change in your project, how much warning you
get before a feature goes away, and which versions get bug and security
fixes.

From 1.0.0, Citry promises that parts of its API stay compatible across
every 1.x release; [What the promise covers](#what-is-covered) lists
them. Until then Citry is at 0.x, where a
minor release can break your code and the release notes list what to
change.

## Pin a major version { #pin-citry }

Citry uses [semantic versioning](https://semver.org/){: target="_blank" rel="noopener"}
from 1.0.0 on. Once 1.0.0 is out, allow any 1.x release:

```toml
# pyproject.toml
[project]
dependencies = [
    "citry>=1.0.0,<2",
]
```

Before 1.0.0, pin one 0.x minor release, because the next one may break
your code, for example `"citry>=0.9.0,<0.10"`.

What each kind of 1.x release does:

- **A patch release** (1.0.0 to 1.0.1) fixes bugs. Upgrade without
  changing your code, unless its release notes name a security fix that
  refuses input your code relied on (see
  [the exception](#security-exception)).
- **A minor release** (1.0.0 to 1.1.0) adds features. Code that uses
  what the [promise covers](#what-is-covered) keeps working. A minor
  release may also:
    - deprecate a feature, which then warns but still works (see
      [Deprecations](#deprecations));
    - change an [experimental feature](#experimental);
    - add a `citry check` rule that reports something new (see
      [New check rules](#new-check-rules));
    - change the arguments of a node class constructor (see
      [What the promise covers](#what-is-covered));
    - drop a Python version that has reached its end of life, or move to
      a newer Vue minor version (see [Python and browsers](#platforms));
    - change data that only Citry reads, so open pages may need a reload
      (see [Rolling deploys](#rolling-deploys)).
- **A major release** (1.x to 2.0.0) may remove deprecated features and
  make other breaking changes. Its release notes say what to change.

Depend on `citry` rather than on `citry-core`. Each `citry` release
requires one exact `citry-core` version and installs it for you.

## What the promise covers { #what-is-covered }

A part of Citry is **covered** when no 1.x release removes it or changes
it in a way that breaks code that uses it as the docs describe. These
parts are covered, except the ones marked
[experimental](#experimental):

- **Python names.** Every name in `citry.__all__` (everything you import
  from `citry`), the names in the `__all__` of each `citry.ext.<name>`
  package and each `citry.contrib.<name>` module, and the names in
  `citry.reload`.
- **Configuration names that start with `_`.** Citry's own options in
  `class Events` and `class State` start with `_` so that they cannot
  clash with your handler and field names. Every such option that the
  docs or the [API reference](/reference/) tell you to set is covered,
  also when you set it in `extensions_defaults`. On `class Events` these
  include `_guard`, `_context`, `_csrf`, `_methods`, `_debounce` and
  `_throttle`; on `class State`, `_public`, `_model`, `_storage`,
  `_max_bytes` and `_max_age`. Four Events options apply to the whole
  app and are set only in `extensions_defaults["events"]`:
  `_max_body_bytes`, `_max_form_fields`, `_csrf_field_names` and
  `_csp_nonce`.
- **Components and templates.** The template syntax, component class
  attributes, and the nested classes such as `Kwargs`, `Slots`, `State`
  and `Lint`.
- **Settings and extension hooks.** Every setting, and every documented
  extension hook.
- **Node classes.** When Citry compiles a template, it turns each tag and
  each piece of text into a node object, and an extension hook can read
  the result as `ctx.nodes` (see
  [Walk deep node lists](/advanced/extensions/#walk-deep-node-lists)).
  The names of the node classes that `citry` exports, such as `Node`,
  `ComponentNode` and `IfNode`, are covered, and so are the attributes an
  extension reads from them. How you construct a node is not: Citry
  creates nodes itself, and the constructor arguments may change in a
  minor release.
- **The command line.** The `citry` commands and their options. For
  `citry check`, which checks your templates for mistakes, that also
  means the JSON that `citry check --format json` prints and the names of
  the rules it reports, such as `citry.template.unknown-component`.
- **The VS Code extension.** The settings and commands it adds to VS Code,
  such as `citry.app` and **Citry: Restart Language Server**. The list is
  on the [VS Code page](/ide/vscode/).
- **The browser JavaScript API.** What the docs teach, with the meaning
  they give, mostly on the [Browser APIs](/reference/browser-apis/)
  page: `window.Citry` and its documented members, `$component(...)` in
  component JavaScript, the `onServerRender` callback, the Events
  helpers such as `$state` and `$sendEvent`, `$i18n`, and the
  `citry:events:*` DOM events.
- **HTTP routes.** The paths, methods and meaning of the routes Citry
  serves under its prefix, such as the event routes and the runtime
  script addresses, so the forwarding rules you set up in your web
  framework keep working. Some routes are called only by Citry's own
  browser code, such as the ones for event definition scripts and
  translated messages: their paths and methods are covered, but not the
  data they carry. The routes of the preview server are experimental.
- **Server events.** The requests that Citry's browser code sends to your
  server and the replies it gets back (see
  [Events protocol](#events-protocol)).

### Security fixes { #security-exception }

One exception applies to every covered part: a 1.x release may refuse
input it used to accept, such as an Events call or a template value,
when that is needed to close a security hole, and the release notes say
so.

## What is not covered { #what-is-not-covered }

Everything in this list may change in any release, even a patch release.
If you build on it, pin the exact Citry version and check the release
notes before each upgrade:

- **Other names that start with `_`.** A module, function, attribute or
  option whose name starts with `_` is internal, unless it is one of the
  configuration names above.
- **Modules not listed above.** Import from `citry`, `citry.ext.<name>`
  or `citry.contrib.<name>`, not from deeper modules such as
  `citry.ext.events.handlers` or `citry.nodes`.
- **Browser internals.** Globals, attributes and members that no docs
  page teaches, such as `window.__citryRuntime`, the
  `data-citry-*` attributes in rendered HTML, and component members whose
  names start with `$citry`.
- **`citry-core`'s own API.** It is the compiled part of Citry, and
  `citry` is the only package meant to call it. It keeps its own version
  numbers, which follow their own rules.
- **Citry UI.** The `citry-ui` component library is at 0.x and is
  marked alpha, so a minor release of `citry-ui` may break your code. Its
  release notes say what to change. Pin it to one minor release, for
  example `"citry-ui>=0.6.0,<0.7"`; 0.6.0 is the first release for
  `citry` 1.x.
- **What Citry generates.** The Python code the template compiler writes,
  the exact whitespace in rendered HTML, and the text of error messages.
  Test what a page shows, not its exact whitespace, and match errors by
  their class rather than their message.

## Experimental features { #experimental }

An experimental feature works and is tested, but its design is not
settled yet. It may change in a minor release, and the release notes say
so when it does.

Each experimental class or function has an **Experimental** box on its
[API reference](/reference/) page, and a guide says so where it teaches
one. In 1.0.0 these are experimental:

- `ComponentGraph`, its helper types such as `ComponentGraphNode`, and
  `Citry.inspect_component_graph()`
- the template analysis API that `citry check`, `citry format` and the
  editor use to find templates in Python files:
  `Citry.template_analysis()`, `TemplateAnalysis`, `TemplateLintInfo`,
  `TemplateVariableInfo`, `TemplateLintConsumer`, `TemplateLintFinding`,
  `ComponentSourceLint`, `lint_unknown_template_variables()`, and the
  classes and functions whose names contain `PythonTemplate`,
  `python_templates`, `PythonComponentAsset` or
  `python_component_assets`
- the hooks that let another template engine, such as Django templates,
  embed Citry tags: `Extension.on_template_foreign_spans()`,
  `Extension.on_template_foreign_compiled()`, the classes whose names
  start with `Foreign` or `OnTemplateForeign`, `CompiledBody`,
  `render_compiled_body()` and `collect_compiled_body_fills()`
- component previews (`citry.ext.preview`)
- the `"payload"` render cache mode, with
  `Extension.export_render_cache()` and `Extension.stage_render_cache()`
- `Extension.browser_plugin()` and `Extension.prepare_browser_render()`
- the Events extension hooks `on_event`, `on_event_result` and
  `on_event_error`
- `EventsDispatcher` and `TransportContext`, which let server code run
  event calls itself instead of through Citry's HTTP routes
- the `event_result_resolvers` and `event_payload_codecs` settings
- `RenderFrame` and `CitryRender.frame`

## New check rules { #new-check-rules }

A minor release may add a `citry check` rule. A new rule can make a CI job
fail that passed before, even though your code did not change.

When that happens:

- The release notes list each new rule.
- A new rule never makes a template that renders today fail to render. It
  reports a finding in `citry check` and the editor only.
- A rule that projects may reasonably disagree about gets a `rule_*`
  setting on `LintSettings`, so you can make it a warning or turn it off. See
  [Change rule severity](/ide/template-linting/#change-how-strict-a-rule-is).

Some rules have no setting. Two of them,
`citry.vue.unknown-slot-prop` and `citry.js-data.unsupported-type`, are
warnings, and a warning never makes `citry check` fail. The
[Diagnostics](/ide/diagnostics/) page marks each rule you can change
with "Your application can change this severity".

## Deprecations { #deprecations }

When Citry plans to remove a feature, it deprecates the feature first. A
deprecated feature keeps working, but each use issues a
`CitryDeprecationWarning` that names the line in your code and says what
to use instead.

A feature deprecated in a 1.x release keeps working, and keeps warning,
for the rest of 1.x. Citry does not remove it before 2.0.0.

`CitryDeprecationWarning` is a subclass of Python's `DeprecationWarning`,
which Python hides unless the line that uses the feature is in the
script you ran directly (the `__main__` module). In a web server your
code usually runs in imported modules, so you will not see the warning
there. To find every use before you upgrade, turn it into an error in
your tests:

```toml
# pyproject.toml
[tool.pytest.ini_options]
filterwarnings = [
    "error::citry.CitryDeprecationWarning",
]
```

To see the warnings in a running server, show them once per line in
your startup code:

```python
import warnings

from citry import CitryDeprecationWarning

warnings.simplefilter("default", CitryDeprecationWarning)
```

## Supported versions { #supported-versions }

Only the newest 1.x minor release gets bug fixes and security fixes.
For example, once 1.2.0 is out, a fix ships as 1.2.1, and there is no
1.1.x release with that fix. To get fixes, stay on the newest minor
release; with `citry>=1.0.0,<2` a normal upgrade does that.

When 2.0.0 comes out, the last 1.x minor release gets security fixes for
12 months after the 2.0.0 release.

The 0.x releases get no fixes once 1.0.0 is out. The 1.0.0 release notes
list what to change when you upgrade from 0.9.x.

The other packages follow their own version numbers:

| Package | Versions | Which releases get fixes |
| ------- | -------- | ------------------------ |
| `citry-lsp` (editor support) | 1.x, from the 1.0.0 that ships with `citry` 1.0.0 | The newest release |
| VS Code extension | 1.x, from the 1.0.0 that ships with `citry` 1.0.0 | The newest release |
| `citry-core` | Its own numbers | The version that a supported `citry` release installs |
| `pygments-citry` (syntax highlighting) | 1.x, from the 1.0.0 that ships with `citry` 1.0.0 | The newest release |
| `citry-ui` | 0.x, alpha | The newest release |

## Rolling deploys { #rolling-deploys }

When you deploy a new Citry version one server at a time, old and new
servers answer the same visitors for a while. A page rendered by an old
server sends its server event calls and State tokens (the component state
Citry keeps in the page) to a new server, and the other way round. Citry
keeps such pages working only during an upgrade from one 1.x release to
another. During an upgrade from 0.x to 1.0.0, expect a page that was
open before the upgrade to show errors until the visitor reloads it. If
that matters, switch every server at once.

Within 1.x, this is what can happen to a page that is open during the
deploy:

- **Event calls** from an old page keep working on a new server, because
  every 1.x server accepts the same [Events protocol](#events-protocol).
  A call from a new page to an old server works too, unless the new
  release added `citry-events/2`; the old server then answers with a
  `protocol_mismatch` error.
- **State tokens** hold data that only Citry reads, and a minor release
  may change their format. A new server then refuses a State token from
  an old page, and an old server refuses one from a new page. The call
  fails with an `invalid_state` error, no reload prompt appears, and the
  page works again once the visitor reloads it.
- **The [render cache](/performance/caching/)** entries that one version
  wrote are ignored by any other, because each entry records the Citry
  version that wrote it. This happens on every upgrade, patch releases
  too. While old and new servers share one cache, each renders again
  over the other's entries, so expect slower renders until the deploy
  finishes.
- **The browser runtime.** A page from the old release loads the old
  runtime file. Clear whole-page caches and give every server one shared
  cache, as
  [Deploy a Citry upgrade](/advanced/web-frameworks/#deploy-a-new-version)
  explains.
- **Server renders.** When an event handler returns a render, the page
  applies it with the browser code it loaded. If the new release changed
  that browser code, a page from the old release cannot apply a render
  from a new server. The call fails with an error, and later calls that
  return a render fail the same way until the visitor reloads the page.

## Events protocol { #events-protocol }

Server events send requests from the browser to your server and replies
back. The data they exchange follows a protocol named `citry-events/1`.
No 1.x release changes or removes it: every 1.x server accepts
`citry-events/1` calls, unless a release must refuse one to close a
security hole (see [the exception](#security-exception)). A
[custom transport](/reference/browser-apis/#citry-events-register-transport)
you registered with `Citry.events.registerTransport` keeps working
across 1.x. Server code that runs calls itself with `EventsDispatcher`
and `TransportContext` is [experimental](#experimental).

If Citry needs a change that `citry-events/1` cannot carry, a 1.x release
adds `citry-events/2` beside it. Only 2.0.0 or a later major release may
stop accepting `citry-events/1` calls, apart from the
[security exception](#security-exception).

## Mix editor versions { #editor }

`citry-lsp` is the language server behind Citry's editor support. Every
`citry-lsp` 1.x works with every `citry` 1.x, so you can upgrade either
one first. Upgrade `citry-lsp` to get new editor features.

## State token lifetime { #state-token-lifetime }

Citry sends each component's State to the page as a signed string, the
State token, unless you keep State on the server
(`State._storage = "server"`). From 1.0.0, a signed State token without
`State._max_age` expires 24 hours after Citry issues it, the same as
State kept on the server.

When a page calls a server event with an expired token, Citry answers
with a `stale_state` error and its browser code offers to reload the
page. To keep tokens valid longer, set `State._max_age` to a longer
`timedelta`. [Treat State as input](/security/#treat-state-as-client-input)
explains why tokens should expire.

## Python and browsers { #platforms }

The [Compatibility](/about/compatibility/) page lists the Python
versions, operating systems and wheels Citry supports today. These
rules decide how that list changes:

- **Python.** Citry supports every CPython version that is still
  maintained upstream. A minor release may add a new Python version. Once
  a Python version reaches its end of life, a minor release may drop it,
  and the release notes say so.
- **PyPy and free-threaded CPython.** Citry runs on both, but support is
  best effort: they are tested weekly rather than on every change, and
  the Compatibility page lists their known differences.
- **Browsers.** Citry supports the latest two versions of Chrome, Edge,
  Firefox and Safari. Its browser code is tested in Playwright's
  Chromium, Firefox and WebKit.
- **Vue.** Citry ships one exact Vue version. A Citry minor release may
  move to a newer Vue minor version. Moving to a new Vue major version
  needs a new Citry major version.
