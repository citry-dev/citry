# Public API audit for citry 1.0.0

From 1.0.0 on, everything this audit marks **keep** can change only in a
major release, after a deprecation period. The audit lists every public
name, setting, CLI option and documented extension hook, so the
maintainer can decide what to rename, make private or mark experimental
in 0.9.0, the last release that may break the API
([#624](https://github.com/citry-dev/citry/issues/624), "Freeze the API
and the contracts").

Decision 2 of #624 says the promise covers everything the docs describe,
except features marked experimental:

- the names in `citry.__all__`;
- the names in the `__all__` of each `citry.ext.<name>` package and each
  `citry.contrib.<name>` module;
- the template syntax;
- component class attributes and nested classes (`Kwargs`, `Slots`,
  `State`, `Lint` and the rest);
- settings, CLI commands and their options, the JSON from
  `citry check --format json`, the diagnostic rule names, and the
  documented extension hooks.

Names that start with `_`, `citry_core._rust`, generated template code,
the messages Citry's own server and browser code send each other, error
message text and the whitespace of rendered HTML are not covered. The
one exception among those messages is the Events protocol,
`citry-events/1` (calls, results and the browser manifest, as
`packages/protocol/events/v1/spec.md` describes them), which custom
transports use and which is frozen for all of 1.x.

This audit lists the Python API, settings, CLI options, diagnostic codes
and extension hooks. The Events v1 freeze task added the browser
JavaScript API and the HTTP routes Citry serves (sections 4.10 and
4.11). Section 5 names the covered parts it does not list (template
syntax and the VS Code extension), and which #624 task owns each.
`citry-ui` stays at 0.x (decision 8), so its components are not listed.

The audit was made at commit `499f4fcfc` (`origin/main` after the 0.8.0
release). It is an internal design record. The model for it is the
[0.6.0 audit](public_api_0_6_0_audit.md).

## 1. Decisions before 0.9.0

Most of the API stays as it is. The audit proposes **no renames that it
calls necessary**. One rename is listed as optional. The other changes
are experimental marks (docstrings and docs only) and a few small
removals of internal names.

"Uses" counts files, as code / docs / examples / tests:

- code: `packages/py/**` outside tests;
- docs: `docs_site/content`, `docs/` and `README.md`;
- examples: `examples/`;
- tests: test folders under `packages/py`.

Counts were taken at `499f4fcfc` with `git grep -lw` on the names in the
row, over tracked files. Most docs hits are design docs under `docs/`;
the "site" note gives the count under `docs_site/content`.

**Must** means: decide before 1.0.0, because after 1.0.0 the same change
needs a deprecation period or a major release. **Fine** means: leaving it
as it is would also be acceptable.

### 1.1 Proposed changes

The maintainer decided every row; the Decision column records it. The
0.9.0 pull request that landed these decisions also changed the code, so
the "Uses" counts, and the `file:line` citations in this audit, describe
the code at the audit commit, before that pull request.

| # | What | Proposed change | Uses | Risk | Must or fine | Decision |
|---|---|---|---|---|---|---|
| 1 | Template analysis names (the classes and functions `citry check`, `citry format` and citry-lsp use to find and read templates in Python source): 27 names in `citry.__all__` (all of `citry.analysis` except `LspPosition` and `LspRange`, plus `TemplateLintInfo` and `TemplateVariableInfo`) and the method `Citry.template_analysis()` | Mark experimental | 11 / 4 (site 1) / 0 / 9 | Low: docstrings and one reference intro. No code changes, and citry-lsp needs no change | Must | Approved, done in 0.9.0 |
| 2 | Host template names (the hooks and types that let another template engine, such as Django templates, embed Citry tags): `CompiledBody`, `ForeignClaim`, `ForeignCompileContext`, `ForeignSpan`, `ForeignSpanSet`, `OnTemplateForeignSpansContext`, `OnTemplateForeignCompiledContext`, `render_compiled_body`, `collect_compiled_body_fills`, and the hooks `on_template_foreign_spans` and `on_template_foreign_compiled` | Mark experimental | 11 / 4 (site 1) / 0 / 9 | Low: docstrings, two reference intros, one note in `advanced/extensions.md` | Must | Approved, done in 0.9.0 |
| 3 | `citry.ext.preview` (all 12 exports) and the `citry ext run preview` commands | Mark experimental | 6 / 4 / 0 / 7 | Low: docs badge and docstrings | Must | Approved, done in 0.9.0 |
| 4 | Render cache `"payload"` mode, where an extension saves its own data with a cached render and restores it on a cache hit: `render_cache_mode = "payload"`, `Extension.export_render_cache()`, `Extension.stage_render_cache()` | Mark experimental | 4 / 2 / 0 / 2 | Low | Must. Their five context and return types are not exported, so leaving the mode stable without exporting them is the one clearly wrong option | Approved, done in 0.9.0 |
| 5 | `Extension.browser_plugin()` and `Extension.prepare_browser_render()` | Mark experimental | 5 / 5 / 0 / 8 | Low | Must. Their types are not exported either | Approved, done in 0.9.0 |
| 6 | Events extension hooks `on_event`, `on_event_result`, `on_event_error` | Mark experimental | 3 / 9 / 0 / 2 | Low | Fine. Their contexts are not exported and no guide teaches them; the 0.6.0 upgrade guide names `on_event_result` | Approved, done in 0.9.0 |
| 7 | Settings `event_result_resolvers` and `event_payload_codecs` | Mark experimental | 5 / 3 (site 0) / 0 / 2 and 4 / 3 (site 0) / 0 / 2 | Low | Must. The setting is public but the shape of a resolver or codec is defined only in internal modules (`PayloadCodec` in `citry.ext.events.codecs`) and the design doc | Approved, done in 0.9.0 |
| 8 | `RenderFrame`, and the `CitryRender.frame` attribute and `CitryRender(frame=...)` parameter that use it | Mark experimental. Stopping the export instead would leave the public `CitryRender.frame` typed with a class that is not exported | 6 / 8 (site 0) / 0 / 3 | Low: docstrings only | Must, unless extensions may replace `ctx.render.frame` as a supported feature (see 1.4) | Approved, done in 0.9.0 |
| 9 | `ExtensionManager.on_*` (21 methods the engine calls to run every extension's hook) and `ExtensionManager.has_attrs_resolved_hook` | Say in their docstrings that they are internal and not covered. Renaming them to `_on_*` can follow later, because the note already leaves them free to change | 13 / 1 (site 0) / 0 / 0 | Low for the note. The rename would touch at least 37 call lines in 13 core files | Must (the note) | Approved, done in 0.9.0 |
| 10 | Keyword-only constructors: `Citry(...)` takes 13 parameters by position, and every field of `CitrySettings`, `LintSettings` and `URLRoute` can be passed by position | Move the `*` in `Citry.__init__` right after `self`; add `kw_only=True` to `CitrySettings` and `LintSettings`; make `URLRoute` keyword-only after `handler`. Accept the rest in writing: `Component.__init__(id, kwargs, slots, parent, provides)`, `InMemoryCache(max_entries)` and `CitryRender.serialize(deps_strategy, deps_position)` stay positional | No positional call found in code, docs, examples or tests | Low | Fine, but cheap now and impossible later without a deprecation | Approved, done in 0.9.0 |
| 11 | `Events._topics` config name | Stop accepting it until server push exists | 3 / 3 (site 0) / 0 / 1 | Low: validated and stored, but only tests read it. The `citry.ext.events` module docstring mentions it (`ext/events/__init__.py:29`), so that line goes too | Fine | Approved, done in 0.9.0: `_topics` now fails at class definition as an unknown config attribute |
| 12 | `URLRoute.extra` field | Remove, but only together with the `URLRoute` part of row 10. `extra` sits before `max_body_bytes` and `dotless_params`, so removing it alone would silently shift a positional `max_body_bytes` | 1 / 0 / 0 / 0 | Low: fits the `URLRoute` note #602 already adds | Fine | Approved, done in 0.9.0 |
| 13 | `citry.ext.debug.Debug` | Optional rename to `DebugExtension` | 2 / 13 (site 2) / 0 / 6 (searching `citry.ext.debug`) | Low | Fine. **Recommended: keep.** It is the only built-in extension class without the suffix, and it shares its name with the nested `class Debug:` users write, but it is a consistency fix, not a correctness one | Not approved: `Debug` keeps its name |

Rows 1 to 9 change only docstrings and docs, and have one "now marked
experimental" line and one "documented as internal" line under Changed
in `CHANGELOG.md`. Rows 10 to 12 change what users may pass, and each
has a bullet under "Upgrading from 0.8.x". Row 13 was the only rename,
and it was not approved.

**The experimental marker (open question 8).** Every experimental name
carries an `Experimental:` section in its docstring, the one
`ComponentGraph` uses (#629). The API reference renders it as a box
titled "Experimental", in the same style as the "Example" box. The
reference intro of a category that holds experimental names says so in
one sentence, and a guide page that teaches or names an experimental
feature has a `!!! warning "Experimental"` box
(`advanced/component-discovery.md`, `advanced/previews.md`) or one
sentence where the feature is a paragraph of a larger page
(`advanced/extensions.md`, `advanced/js-and-css-dependencies.md`).
There is no separate badge.

Already done:

- `ComponentGraph` and its five helper types, plus
  `Citry.inspect_component_graph()`, are marked experimental (#629,
  commit `16f25ac77`).
- The i18n editor index is back at version 1 in `citry` and citry-lsp
  (same commit). The #624 task can be ticked.
- The API comment in `citry/__init__.py:9-15` already names the
  `__all__` of `citry.ext.<name>` and `citry.contrib.<name>`. 0.9.0 adds
  `citry.reload` to it (1.2).

### 1.2 Additions that #624 already asks for, or that close a gap

These only add names, so none needs an upgrade note. All four were
approved and are done in 0.9.0, except naming `citry.reload` on the
Versioning page, which waits for that page (#624). Running the test
suite with `CitryDeprecationWarning` turned into an error is also left
to its own #624 task; one test checks the filter string the docstring
teaches. `CitryDeprecationWarning` is a
`DeprecationWarning` subclass. `citry.reload.__all__` is `watch`,
`WatchHandle`, `FileWatcher`, `WatchfilesWatcher`, `WatchdogWatcher` and
`PollingWatcher`; `default_watcher` stays internal. The docs site counts
`citry.reload` as a public entrypoint, so the reference test checks that
every name in its `__all__` has a reference page.

| What | Change | Risk | Must or fine |
|---|---|---|---|
| `safe_eval` and `unsafe` (decision 8) | Re-export from `citry`; change the two imports in `docs_site/content/security.md:936` and `:1007`. Their docstrings are thin, so use a `description_overrides` entry in `reference.yml` rather than a new citry-core release | Low | Must |
| `CitryDeprecationWarning` (decision 4) | Add the public class. The helper that warns at the caller's line already exists, privately, as `warn_at_caller` (`citry/_caller_warnings.py:51`). No pytest `filterwarnings` setting exists yet. Choose the base class: a `DeprecationWarning` subclass (as Django does) is hidden by default outside `__main__` and test runners, while `FutureWarning` is always shown | Low | Must |
| `citry.reload` | `guides/hot-reload.md:116` teaches `from citry.reload import watch`, and `reload_lifespan()` takes a `FileWatcher`, but `citry.reload` has no `__all__` and no reference page. Give `citry.reload` an `__all__` (`watch`, `WatchHandle`, `FileWatcher` and the watcher classes the guide names), add a reference category, and name the module on the Versioning page. That covers what the guide teaches without growing `citry.__all__` | Low | Must |
| `I18nExtension` | The i18n guides call `get_extension("i18n").for_context(...)`, and `reference.yml:287` renders it, but it is not in `citry.ext.i18n.__all__`. Add it | Low | Must |

### 1.3 Defaults (#624 "Review the defaults")

No default on the #624 list is clearly wrong, so none has to change.
Every row below is "fine to keep" except where it says otherwise.
Making a lint rule less strict later lets more CI runs pass, so it is not
a breaking change. Making a lenient default stricter later is.

| Default | Current value | Recommendation |
|---|---|---|
| Lint rules | 35 `rule_*` settings: 22 error, 11 warning, 2 ignore (`citry/settings.py:459-496`). All match `defaultSeverity` in `packages/protocol/diagnostics/v1/catalog.json` | Keep. A rule that proves noisy can be softened in 1.x |
| `check_input_types` | `True`, also in production (`settings.py:497`) | Keep. Safe by default, and one setting turns it off |
| Expression sandbox | `sandbox_expressions=True` (`settings.py:852`), the only switch | Keep. Must not change |
| `security_csp` | `"off"` (`settings.py:862`) | Keep. It is an opt-in output check; `"warn"` by default would warn on every page with an inline `<script>` |
| `security_javascript` | `"allow"` (`settings.py:863`) | Keep. The stricter modes remove behavior most apps use, and #601 already decided to keep today's URL behavior for 1.0 |
| `security_script_integrity` | `"off"` (`settings.py:864`) | Keep |
| Default cache | a new `InMemoryCache()` per `Citry` (`citry.py:1736`), `max_entries=None` (`cache.py:143`), State budget 64 MiB (`cache.py:102`) | Keep. Under default settings nothing grows without limit, because the render cache is off. A default `max_entries` can still come in 1.x, since it only drops entries earlier |
| Render cache | `ttl=300` s, `max_entry_bytes=1_000_000` (`ext/cache/config.py:19-20`), `enabled=False` per component | Keep |
| Page-file store | `vue_asset_max_bytes` 64 MiB (`settings.py:36`) | Keep |
| Server-stored State lifetime | 24 h when `_max_age` is unset (`ext/events/tokens.py:160`) | Keep |
| Signed State token lifetime (not on the #624 list) | Never expires when `_max_age` is unset (`ext/events/tokens.py:537`; documented in `security.md:67-69`) | The one default that looks loose for a stable release: a captured token stays valid until the secret rotates. Decide with the security review whether to give it a default. Decision 7 already accepts that an old page may reload once |

### 1.4 Questions that are not renames

1. **citry-lsp and decision 8.** citry-lsp imports about 200 names from
   `citry`: 17 from `citry`, 95 from `citry.analysis`, and 86 from 24
   private `citry._*` modules, plus two `citry.ext.events` internals
   (`citry_lsp/app_worker.py:35-36`). Only 5 imports have an
   `except ImportError` fallback. No label in this audit makes
   "citry-lsp 1.x works with every citry 1.x" true. Choose one before
   1.0.0: a CI job that runs the oldest citry-lsp 1.x against the new
   citry, feature checks in citry-lsp, or one versioned internal module
   that citry-lsp imports instead of 24.
2. **Node classes.** `Node`, `ComponentNode`, `IfNode` and the other 10
   node classes are what compiled templates create, which decision 2
   leaves out. But `on_template_compiled` hands them to extensions in
   `ctx.nodes`, so they stay public. Suggested wording for the Versioning
   page: class names and the attributes extensions read are covered;
   constructor arguments are not.
3. **`RenderFrame` and extensions.** `tests/test_render.py:78-95` has an
   extension replace `ctx.render.frame`. If that is a supported feature,
   keep `RenderFrame` stable and accept that its fields are frozen;
   otherwise row 8 stands. Decided: row 8 was approved, so replacing
   `ctx.render.frame` is experimental too.
4. **Host template hooks.** The design promised them as supported
   (`template_host_interop.md:13-17`), but the only user is a Django
   proof of concept whose Citry patch is not public. If that counts as an
   outside user, keep row 2 stable. Decided: row 2 was approved, so the
   hooks are experimental.
5. **Underscore names users set.** The Events config (`_guard`, `_csrf`,
   `_max_body_bytes`, ...) and State options (`_public`, `_storage`,
   `_max_age`, ...) start with `_` on purpose, so they do not clash with
   handlers and fields. Decision 2 says `_` names are not covered. The
   Versioning page must say these documented names are covered.
6. **Decision 3 wording.** It says each check rule has a `rule_*`
   setting. Three warnings have none:
   `citry.template.undeclared-template-data-key`,
   `citry.vue.unknown-slot-prop` and `citry.js-data.unsupported-type`.
   Several error-level findings have no setting either, so CI cannot turn
   them off: for example `citry.browser.undeclared-emit` (severity fixed
   at `analysis.py:2043`), `citry.browser.unknown-server-event`,
   `unknown-state-field`, `invalid-state-binding-target`,
   `missing-component-prop`, `incompatible-component-prop`,
   `citry.template.unknown-component`, `marker-name-invalid`,
   `citry.i18n.unknown-message` and `argument-invalid`. This list was
   matched by name, so some may be deliberate hard errors for templates
   that cannot render. Reword the decision ("each rule a user may
   reasonably disagree with has a setting"), or add settings; adding one
   is additive and can come in 1.x.
7. **`EventsDispatcher` and `TransportContext`** pass the Events v1 call
   and result data. If the Events v1 task keeps that format internal,
   mark both experimental; if it freezes it, keep them. Decided: keep.
   `citry-events/1` is frozen for all of 1.x, and both classes stay
   stable (`packages/protocol/events/v1/spec.md`, "Versioning").
8. **One experimental marker.** Decided: the `Experimental:` docstring
   section, as described after the table in 1.1.

## 2. What changed since the 0.6.0 audit

The 0.6.0 audit compared 0.5.1 with the 0.6.0 branch. Since `citry@0.6.0`:

- `citry.__all__` gained `ComponentSourceLint` and `Secret` (both in
  0.7.0) and lost nothing. It has 194 names.
- The `__all__` of every `citry.ext.*` and `citry.contrib.*` module is
  unchanged.
- The extension base class has the same hook methods.
- `CitrySettings` gained `model_base`. `LintSettings` gained 27 fields:
  25 `rule_*` settings and the flags `check_input_types` and
  `include_libraries`. Nothing was removed.
- `citry check` gained `--include-libraries`. No other CLI option
  changed.
- `ComponentGraph` and its helpers are now marked experimental, and the
  i18n index went back to version 1 (#629).
- Coming in 0.9.0, already in the Unreleased changelog: `URLRoute`
  refuses two parameters with nothing between them (#602).

## 3. How this audit was made

Four read-only passes divided the work: `citry.__all__` in two halves,
`citry.ext.*` with `citry.contrib.*` and the hooks, and settings with
the CLI and defaults. Each pass:

- imported `citry` with the repository virtual environment to list
  names, kinds and defining modules;
- counted files with a word-boundary search over tracked files;
- checked which names a prose page under `docs_site/content` teaches,
  and which appear only on the generated reference page;
- read `--help` for every command;
- compared with the `citry@0.6.0` tag.

Every name in scope is on a reference page:
`docs_site/tests/test_reference_pages.py` enforces that. "Ref only" in
the tables below means no guide page teaches the name.

## 4. Inventory

### 4.1 `citry.__all__` (194 names)

These counts are from the audit commit. 0.9.0 adds
`CitryDeprecationWarning`, `safe_eval` and `unsafe` (1.2), which makes
197 names.

151 keep, 37 mark experimental (27 in row 1, 9 in row 2, 1 in row 8),
and 6 already experimental. `ComponentNode` is listed once, under
Components.

| Group | Names | Status |
|---|---|---|
| Engine and settings | `Citry`, `citry`, `CitrySettings`, `LintSettings`, `LintSeverity`, `Secret`, `SecurityCspMode`, `SecurityJavascriptMode`, `SecurityScriptIntegrityMode` | keep |
| Components | `Component`, `ComponentLike`, `ComponentNode`, `Const`, `const_value`, `is_const`, `NestedClassDeclaration`, `NestedSchemaReplacedWarning` | keep |
| Registry and lifecycle errors | `AlreadyRegistered`, `NotRegistered`, `CitryLifecycleInProgress` | keep (the missing `Error` suffix matches Django) |
| Component libraries | `ComponentLibrary`, `LibraryComponent`, `LibraryComponentContextError`, `LibraryComponentInvocation`, `LibraryInstallation`, `LibraryInstallationStale`, `LibraryManifestChanged`, `LibraryNotInstalled` | keep (the three `Library*` errors without a suffix could be renamed cheaply, but it is taste) |
| Rendering | `CitryContext`, `CitryElement`, `CitryRender`, `CitryTemplate`, `Placeholder`, `SerializedRender`, `SerializedScriptSecurity`, `SerializedSecurity`, `OnRenderGenerator`, `RenderReplacement`, `Markup`, `SecurityError`, `VueCodeError` | keep |
| Rendering | `RenderFrame` | mark experimental (row 8) |
| Attributes | `format_attrs`, `merge_attrs`, `normalize_class`, `normalize_style`, `parse_string_style` | keep |
| Slots | `Slot`, `SlotContext`, `SlotData`, `SlotFunc`, `SlotInput`, `SlotResult` | keep |
| Node classes | `Node`, `ElementAttrsNode`, `ElementKeyNode`, `ExprHtmlAttr`, `ExprNode`, `FillNode`, `ForNode`, `HtmlAttr`, `IfNode`, `SlotNode`, `StaticHtmlAttr`, `TemplateHtmlAttr` (`ComponentNode` is under Components) | keep (see 1.4 question 2) |
| Cache | `CitryCache`, `InMemoryCache`, `CacheConfig` | keep |
| Dependencies | `DependenciesConfig`, `DepsPosition`, `DepsStrategy` | keep |
| Events | `Events` | keep |
| Routes | `URLRoute`, `RouteRequest`, `RouteResponse`, `RouteHeaders` | keep (`URLRoute.extra`: row 12) |
| Extensions | `Extension`, `ExtensionCommand`, `ExtensionConfig`, `ExtensionManager`, `CommandArg`, `CommandArgGroup`, `CommandSubcommand`, `ComponentIntrospectionContext`, `TemplateNamespaceContext`, `TemplateNamespaceContribution` | keep (`ExtensionManager.on_*`: row 9) |
| Hook contexts | `OnAttrsResolvedContext`, `OnCitryClearedContext`, `OnComponentClassCreatedContext`, `OnComponentDataContext`, `OnComponentInputContext`, `OnComponentRegisteredContext`, `OnComponentRenderedContext`, `OnComponentUnregisteredContext`, `OnCssLoadedContext`, `OnExtensionCreatedContext`, `OnFilesResetContext`, `OnJsLoadedContext`, `OnMessagesLoadedContext`, `OnRenderContextMergeContext`, `OnSerializeContext`, `OnSlotRenderedContext`, `OnTemplateCompiledContext`, `OnTemplateLoadedContext`, `OnTemplateResetContext` | keep (none of these 19 has a class docstring, so the reference page shows only the signature; worth fixing) |
| Introspection | `AssetInfo`, `ComponentAssets`, `ComponentCatalog`, `ComponentExtensionInfo`, `ComponentInfo`, `ComponentIntrospectionError`, `ComponentSchemas`, `ExtensionVersion`, `FieldInfo`, `FrozenJsonObject`, `FrozenJsonValue`, `SchemaInfo` | keep |
| i18n (also in `citry.ext.i18n`) | `I18n`, `I18nError`, `I18nNotConfiguredError`, `I18nRuntimeUnavailableError`, `I18nFormatter`, `I18nParser`, `I18nService`, `LocaleContext`, `LocalizedText`, `FormatRegistry`, `CurrencyFormat`, `DateFormat`, `DateFormatFields`, `DateInput`, `DateTimeFormat`, `DateTimeInput`, `ListFormat`, `NumberFormat`, `NumberInput`, `PercentFormat`, `PercentInput`, `RelativeTimeFormat`, `TimeFormat`, `TimeInput`, `UnitFormat`, `DateParseResult`, `DateSegments`, `DateTimeParseResult`, `DateTimeSegments`, `NumberParseResult`, `PercentParseResult`, `TimeParseResult`, `TimeSegments` | keep |
| Source positions | `LspPosition`, `LspRange` | keep (two settled fields; also used by `ComponentGraphLocation`) |
| Template analysis | `ComponentSourceLint`, `PythonComponentAssetDiscovery`, `PythonComponentAssetFile`, `PythonComponentAssetFormatResult`, `PythonComponentAssetKind`, `PythonComponentAssetNotice`, `PythonComponentAssetPlan`, `PythonComponentAssetRegion`, `PythonComponentAssetRequest`, `PythonTemplateDiscovery`, `PythonTemplateFormatError`, `PythonTemplateFormatResult`, `PythonTemplateNotice`, `PythonTemplateRegion`, `PythonTemplateSourceMap`, `TemplateAnalysis`, `TemplateLintConsumer`, `TemplateLintFinding`, `TemplateLintInfo`, `TemplateVariableInfo`, `discover_python_component_assets`, `discover_python_templates`, `finish_python_component_assets`, `format_python_component_assets`, `format_python_templates`, `lint_unknown_template_variables`, `prepare_python_component_assets` | mark experimental (row 1) |
| Host templates | `CompiledBody`, `ForeignClaim`, `ForeignCompileContext`, `ForeignSpan`, `ForeignSpanSet`, `OnTemplateForeignCompiledContext`, `OnTemplateForeignSpansContext`, `collect_compiled_body_fills`, `render_compiled_body` | mark experimental (row 2) |
| Component graph | `ComponentGraph`, `ComponentGraphLocation`, `ComponentGraphNode`, `ComponentGraphProblem`, `ComponentGraphReference`, `UnresolvedComponentReference` | already experimental (#629) |

Why row 1: these names are how `citry check`, `citry format` and
citry-lsp read Python source. No guide page teaches them,
`analysis.py` has had 17 commits since September 2026, and
`TemplateLintInfo` gains a field with every new lint rule. Two of its
fields use a type that is not public (`VueVariableInfo`). Making them
private instead would mean changing five citry-lsp files in the same
release, and `Citry.template_analysis()` would then return a private
type.

Why row 8: `RenderFrame.prepared_occurrence` is typed
`PreparedOccurrenceMetadata`, which is not exported, and its `call`
field uses the private `_PreparedCallMetadata`
(`citry/citry_render.py:223`, `:326-336`). The frame already gained a
field in 0.6.0.

### 4.2 `citry.ext.*` (73 names)

| Module | Names | Status |
|---|---|---|
| `citry.ext.cache` | `CacheConfig`, `CacheKeyError`, `OnComponentCacheHitContext`, `component_cache_key`, `fragment_cache_key` | keep |
| `citry.ext.debug` | `Debug` | keep (optional rename, row 13) |
| `citry.ext.dependencies` | `CitryDependencies`, `DependenciesConfig`, `DependenciesExtension`, `Dependency`, `DependencyRecord`, `OnDependenciesContext`, `Script`, `Style`, `get_dependencies` | keep |
| `citry.ext.events` | `X_CITRY_EVENTS_HEADER`, `CallEvent`, `EventError`, `EventRequest`, `EventsExtension`, `UploadedFile`, `ViewEvents`, `event`, `get_event_url`, and the module `actions` (`Action`, `Data`, `Dispatch`, `Download`, `PushUrl`, `Redirect`, `Render`, `ReplaceUrl`) | keep |
| `citry.ext.events` | `EventsDispatcher`, `TransportContext` | keep: Events v1 is frozen (1.4 question 7) |
| `citry.ext.i18n` | the 33 i18n names listed in 4.1, plus `make_context` | keep (add `I18nExtension`, see 1.2) |
| `citry.ext.preview` | `Layout`, `PreviewComponent`, `PreviewError`, `PreviewExtension`, `PreviewGroup`, `PreviewItem`, `PreviewMetadata`, `PreviewPage`, `PreviewVariant`, `Variant`, `Viewport`, `variant` | mark experimental (row 3) |

Why row 3: no package outside Citry uses it, preview fails for any
component with Events (#580), and its design leaves interactive controls and
fixtures for later work (`docs/design/extensions_preview.md:13-14`). It
is a development tool, so the label costs app authors nothing.

The browser parts of i18n that its design defers (date and time parsing
in the browser, request helpers, pseudo-locales) are not shipped, so
there is nothing to mark. The shipped browser i18n API (`$i18n.tr()`,
`format.*`, `parse.number`, `parse.percent`, `$c-tr`, `bind()`) stays
covered.

### 4.3 `citry.contrib.*` (11 names)

| Module | Names | Status |
|---|---|---|
| `citry.contrib.asgi` | `asgi_app`, `reload_lifespan` | keep |
| `citry.contrib.caches` | `DiskCache`, `RedisCache` | keep |
| `citry.contrib.django` | `DjangoCache`, `enable_hot_reload`, `secret`, `urlpatterns` | keep |
| `citry.contrib.fastapi` | `mount` | keep |
| `citry.contrib.flask` | `mount` | keep |
| `citry.contrib.wsgi` | `wsgi_app` | keep |

The parameter that takes the `Citry` instance has four names across these
functions and `citry.ext.*`: `citry_instance`, `engine`
(`reload_lifespan`), `app` (`make_context`) and `citry`
(`fragment_cache_key`). Every docs example passes it by position, so keep.
Making that parameter positional-only in 0.9.0 would stop the names from
becoming part of the promise; that is optional.

No docs page or example imports from a deeper `citry.ext.*` or
`citry.contrib.*` path. citry-ui imports only public names from these
modules (`Script`, `Style`, `Dependency` and `event`), apart from its
development-only `citry_ui/quality/` package, which the wheel leaves
out. citry-lsp imports two `citry.ext.events` internals (1.4 question 1).

### 4.4 Extension hooks and attributes

| Hook or attribute | Status |
|---|---|
| `Extension.name`, `class_name`, `Config`, `commands`, `citry`, `urls`, `validate_config_fields`, `introspection_version`, `inspect_component`, `inspect_template_namespace` | keep |
| `on_extension_created`, `on_component_class_created`, `on_component_registered`, `on_component_unregistered`, `on_citry_cleared` | keep |
| `on_component_input`, `on_component_data`, `on_component_rendered`, `on_slot_rendered`, `on_attrs_resolved`, `on_render_context_merge`, `on_serialize` | keep |
| `on_template_loaded`, `on_template_compiled`, `on_template_reset`, `on_js_loaded`, `on_css_loaded`, `on_messages_loaded` | keep |
| `on_files_reset` | keep. It is not declared on `Extension`, and only the `ExtensionManager.on_files_reset` docstring describes it; move that text to the `Extension` docstring. 0.9.0 keeps the text there and adds that the extension's `on_files_reset` is public while the manager method is internal; the move is still open |
| `on_dependencies` (fired by the dependencies extension) | keep |
| `on_component_cache_hit` (fired by the cache extension) | keep. Its context is exported, but no guide teaches it |
| `render_cache_mode` `"deny"` and `"stateless"`, `render_cache_version`, `render_cache_bypass_reason` | keep |
| `render_cache_mode = "payload"`, `export_render_cache`, `stage_render_cache` | mark experimental (row 4) |
| `browser_plugin`, `prepare_browser_render` | mark experimental (row 5) |
| `on_template_foreign_spans`, `on_template_foreign_compiled` | mark experimental (row 2) |
| `on_event`, `on_event_result`, `on_event_error` (fired by the events extension) | mark experimental (row 6) |
| `ExtensionManager.get_extension`, `emit`, `has_hook`, `commands`, `urls`, `get_extension_command` | keep |
| `ExtensionManager.on_*` (21 methods), `has_attrs_resolved_hook` | internal, by docstring note (row 9) |
| `URLRoute.path`, `handler`, `handler_async`, `children`, `name`, `methods`, `max_body_bytes`, `dotless_params` | keep (#602 changes matching in 0.9.0) |
| `URLRoute.extra` | removed (row 12) |

Decision 9 names "the extension hooks no outside extension uses yet" as
experimental candidates. Read literally, that is every hook, because no
Citry extension exists outside this repository. This audit marks a hook
experimental only when a type it takes or returns is not exported, or
when no guide teaches it and its only intended user is a proof of
concept. Every other hook has exported types, so it stays covered.
These kept hooks appear on no guide page (only on the reference page and
in upgrade guides): `on_component_class_created`,
`on_component_registered`, `on_citry_cleared`, `on_render_context_merge`,
`on_template_reset`, `on_files_reset`, `on_component_cache_hit`,
`render_cache_bypass_reason` and `inspect_template_namespace`. A short
guide entry for each would help before 1.0.0, but none needs a change.

### 4.5 Settings

`Citry(...)` and `CitrySettings` (`citry/settings.py:848-869`):

| Setting | Default | Status |
|---|---|---|
| `extensions` | `()` | keep |
| `extensions_defaults` | `{}` | keep |
| `dirs` | `()` | keep |
| `cache` | `None` (a new `InMemoryCache`) | keep |
| `sandbox_expressions` | `True` | keep |
| `autodiscover` | `True` | keep |
| `mode` | `"production"` | keep |
| `template_globals` | `{}` | keep |
| `lint` | `LintSettings()` | keep |
| `id_generator` | `None` | keep (ref only) |
| `secret` | `None` | keep |
| `event_result_resolvers` | `()` | mark experimental (row 7) |
| `event_payload_codecs` | `()` | mark experimental (row 7) |
| `security_csp` | `"off"` | keep |
| `security_javascript` | `"allow"` | keep |
| `security_script_integrity` | `"off"` | keep |
| `ssr` | `True` | keep |
| `ssr_element_threshold` | `0` | keep |
| `vue_asset_max_bytes` | 64 MiB | keep |
| `max_component_depth` | `2000` | keep |
| `model_base` | `None` (dataclasses) | keep |

`LintSettings` (`citry/settings.py:459-498`), all keep. Each `rule_*`
takes `"ignore"`, `"warning"` or `"error"`:

- Error by default (22): `rule_unknown_template_variable`,
  `rule_unknown_vue_variable`, `rule_unknown_component_js_variable`,
  `rule_unknown_component_js_member`, `rule_alpine_cloak`,
  `rule_invalid_attribute_value`, `rule_misspelled_directive`,
  `rule_misspelled_attribute`, `rule_misspelled_element`,
  `rule_unknown_aria_attribute`, `rule_invalid_nesting`,
  `rule_duplicate_id`, `rule_invalid_model_target`,
  `rule_invalid_vue_expression`, `rule_vue_compile_error`,
  `rule_missing_component_key`, `rule_prop_assignment`,
  `rule_unknown_server_event_field`, `rule_missing_server_event_field`,
  `rule_incompatible_server_event_field`, `rule_unknown_form_field`,
  `rule_missing_form_field`.
- Warning by default (11): `rule_i18n_missing_param_type`,
  `rule_vue_python_variable`, `rule_alpine_attribute`,
  `rule_i18n_cross_language_fallback`, `rule_missing_image_alt`,
  `rule_misspelled_event`, `rule_undeclared_component_event`,
  `rule_misspelled_css_variable`, `rule_misspelled_css_class`,
  `rule_unknown_url`, `rule_unknown_inject_key`.
- Ignore by default (2): `rule_undeclared_css_class`,
  `rule_undeclared_css_variable`.
- Other fields: `template_variables`, `vue_variables`,
  `component_js_globals`, `check_input_types` (`True`),
  `include_libraries` (`False`).

The `rule_*` names do not follow one pattern from their diagnostic codes
(`citry.vue.misspelled-event` is `rule_misspelled_event`, while
`citry.vue.compile-error` is `rule_vue_compile_error`). Renaming 35
settings is not worth it. Instead, add each rule's setting name to its
entry in `catalog.json` and to the diagnostics page. That change is
additive.

Built-in extension settings, all keep except where noted:

| Extension | Settings |
|---|---|
| events (component `Events` or `extensions_defaults["events"]`) | `_guard`, `_context`, `_csrf` (`"auto"`), `_methods` (`("POST",)`), `_debounce`, `_throttle`; engine only: `_max_body_bytes` (1 MiB), `_max_form_fields` (1000), `_csrf_field_names`, `_csp_nonce`. `_topics` is no longer accepted (row 11). `_debounce` and `_throttle` work but have no docs page |
| events State options | `_public`, `_model`, `_storage` (`"signed"`), `_max_bytes` (8192 signed, 65536 server), `_max_age` (see 1.3) |
| i18n | `source_locale`, `locales`, `default_locale`, `fallbacks`, `catalogs`, `formats`; component: `messages_locale`, `client_messages` |
| cache | `ttl` (300), `namespace`, `generation`, `max_entry_bytes`; component: `enabled` (`False`), `vary`, `version` (1) |
| dependencies (component) | `js`, `css`, `extend` (`True`), `local_files` (`"inline"`) |
| debug | `highlight_components`, `highlight_slots` (both `False`) |
| preview | `group`, `viewport`, `variant_layout`, `page_layout`, `enabled`, `template`, `template_file`, `variants`. These follow row 3 |
| `InMemoryCache(...)` | `max_entries` (`None`), `state_max_bytes` (64 MiB) |

Every boolean setting is named positively. No docs page names a setting
the code lacks, apart from the old names in the 0.6.0 upgrade guide,
which describe them correctly.

### 4.6 CLI

All keep.

| Command | Options |
|---|---|
| `citry` | `--version`; `--app module:attr` (first argument only). `--app` is missing from `citry --help`; adding it is a help-text fix |
| `citry check` | `--static`, `--types`, `--include-libraries`, `--format {text,json}` |
| `citry format [PATH ...]` | `--check`, `--diff`, `--verbose`, `--embedded {off,available,required}`, `--javascript-provider`, `--css-provider` |
| `citry list` | none |
| `citry inspect [component]` | `--json` (required) |
| `citry create name` | `--path`/`-p` |
| `citry watch` | `--path`/`-p` (repeatable) |
| `citry ext list` | none |
| `citry ext run events openapi` | `--out`, `--only-data` (`--only-data` has no docs) |
| `citry ext run i18n extract`, `check`, `compile [packages ...]` | none |
| `citry ext run i18n inspect` | `--out` |
| `citry ext run i18n coverage` | `--locale` (repeatable), `--json`, `--fail-on-missing` |
| `citry ext run preview serve [components]` | `--dir`/`-d`, `--variant`, `--port`. Follows row 3 |
| `citry ext run preview render [components]` | `--dir`/`-d`, `--variant`, `--outdir`/`-o`, `--overwrite`, `--base-url`, `--timeout`, `--ready-selector`. Follows row 3 |
| `citry-lsp` | no options; anything else is refused |

`citry check`, `citry inspect` and `citry ext run i18n coverage` ask for
JSON in three ways (`--format json`, `--json` as a required flag, and
`--json`). That can stay: accepting
`--format json` everywhere later only adds an option.

### 4.7 Check JSON and diagnostic codes

- `citry check --format json` is built in `citry/commands/check.py:159-190`
  and carries `"schema_version": 1`. Keys: `schema_version`, `mode`,
  `app`, `app_failure`, `notes`, `exit_code`, `findings`. Each finding
  has `origin`, `code`, `severity`, `message` and `range`.
  `docs_site/content/advanced/cli.md:164-212` documents it. That page
  should also say the current value is 1, and that a new optional key
  does not change it.
- 80 diagnostic codes live in
  `packages/protocol/diagnostics/v1/catalog.json` (generated into
  `citry/_diagnostic_catalog.py`). All are `citry.<group>.<name>`. Keep
  them all. The `citry.browser.*` group mixes Vue and Events checks, but
  renaming codes would break every CI filter on them.

### 4.8 Contract versions

Every version number Citry writes into stored or exchanged data is 1,
as CLAUDE.md requires before 1.0.0. That covers signed and server-stored
State tokens, `citry-events/1`, the Vue fragment and prepared payloads,
render cache keys and entries, extension cache and introspection data,
template analysis data, the component catalog and graph, the i18n editor
index, i18n catalogs and browser data, `citry check` JSON, the
diagnostics catalog, and the preview manifests. citry-lsp still requires
an exact match for the analysis data, the catalog and the i18n index, so
the decision 8 task to accept a newer citry 1.x is still open (1.4
question 1).

### 4.9 Members of `Component`, `Citry` and `CitryRender`

The classes are in `citry.__all__`, so their public members are covered
too. All keep. Members the rows above mark are noted.

| Class | Public members |
|---|---|
| `Component` (41) | Nested classes `Kwargs`, `Slots`, `State`, `Lint`, `Events`, `Cache`, `I18n`, `Dependencies`, `TemplateData`, `JsData`, `CssData`. Class attributes `template`, `template_file`, `js`, `js_file`, `css`, `css_file`, `messages`, `messages_file`, `name`, `pure`, `simple`, `transparent`, `citry`. Methods `template_data`, `js_data`, `css_data`, `on_render`, `on_dependencies`, `provide`, `inject`, `unprovide`, `get_template`, `get_js`, `get_css`, `get_messages`, `get_dependencies`, `reset_template`, `reset_files`, and the properties `ancestors` and `root`. `Component.__init__` stays positional (row 10) |
| `Citry` (27) | `register`, `unregister`, `register_library`, `get`, `has`, `components`, `get_component_by_class_id`, `get_components_for_file`, `get_library_installation`, `atomic_registration`, `autodiscover`, `initialize`, `clear`, `render_template`, `build_url`, `runtime_url`, `urls`, `commands`, `mounted_prefix`, `set_mounted_prefix`, `invalidate_all`, `invalidate_file`, `inspect_component`, `inspect_components`, `engine_id`. `inspect_component_graph` is already experimental; `template_analysis` follows row 1 |
| `CitryRender` (8) | `context`, `parts`, `is_component_root`, `owner_citry`, `render_target`, `serialize`, `serialize_result`. `frame` follows row 8. `serialize(deps_strategy, deps_position)` stays positional (row 10) |

### 4.10 Browser JavaScript API

Added for the Events v1 freeze, at `origin/main` after the 0.9.0 release
(`c9b3fc23b`). The model is section 3.1 of the 0.6.0 audit. A name is
**covered** when a page under `docs_site/content` teaches it, and then
only with the meaning that page gives. **Not covered** names are globals
and members that Citry's own generated code and runtime use; a page can
read them today, but any release may change them.

Sources are paths under `packages/`. `client.js` is
`py/citry/citry/_vue/client.js`, the hand-written part of `runtime.js`;
`events-vue.ts` is `js/citry-client/src/citry-events-vue.ts`. "BA" is
`docs_site/content/reference/browser-apis.md`.

#### Window globals and `Citry.*`

| Name | Source | Documented | Status |
|---|---|---|---|
| `window.Citry` | `client.js:98-116` | BA, throughout | covered |
| `Citry.configure({csrf})` | `client.js:385-410` | BA "Page-wide settings" | covered |
| `Citry.events.send(target, name, args?, opts?)` | `client.js:289-291`, `3546-3558` | BA `#citry-events-send` | covered for the documented targets, a render ID or an element. The `render:<id>` form of `target` (`client.js:3548`) is undocumented and not covered |
| `Citry.events.on(name, fn)` | `client.js:292-298` | BA `#citry-events-on` | covered for events that server handlers dispatch. It listens on `document`, so it also hears any other DOM event with that name; that is not promised |
| `Citry.events.configure({csrf, timeout, transport, url})` | `client.js:299-313` | BA `#citry-events-configure` | covered |
| `Citry.events.registerTransport(name, {send})` | `client.js:314-319`; `send` called at `events-vue.ts:876-886` | BA `#citry-events-register-transport`, "Custom event transports" | covered, with `send(envelope, request)`, the `request` fields `url`, `method`, `headers`, `signal`, and the headers listed in the spec's "HTTP adapters" section. Registering under the name `"fetch"` replaces the built-in transport (`client.js:4298-4303`); undocumented, not covered |
| `Citry.events.applyActions(actions)` | `client.js:245-277`, `320-322` | BA `#citry-events-apply-actions` | covered. The actions are `citry-events/1` actions |
| `Citry.vue`, `Citry.vue.use(plugin, ...)` | `client.js:111-115`, `197-215` | BA `#citry-vue`, `#citry-vue-use` | covered |
| `Citry.fragments.load` | `js/citry-client/src/citry-fragments.ts:111-137` | none | not covered |
| `window.Vue` | `js/citry-client/build-support.mjs:175` | none (BA names only `Citry.vue`, the same object) | not covered |
| `window.CitryVueEvents`, `window.CitryVueFragments` | `build-support.mjs:177-182` | none | not covered |
| `window.__citryRuntime`, `window.__citryRuntimeDefinitions` | `client.js:5762`; `py/citry/citry/_vue/compiler.py:716-726` | none | not covered. Generated code calls them |
| `window.CitryVueDevChecks`, `__citryHydrationDiagnostics`, `__citryHydrationReport` | `py/citry/citry/_vue/dev_checks.js:619`; `client.js:4506`, `4742-4752` | none | not covered (development and test hooks) |
| `Symbol.for("citry:built-in-members")`, `Symbol.for("Citry.i18n.vue-plugin.registered")` on `window` | `client.js:5761`; `js/citry-client/src/citry-i18n-vue.ts:117` | none | not covered |
| `$component(...)` in component JavaScript | rewritten by `py/citry/citry/ext/dependencies/scripts.py:500-531` | BA `#component` | covered. It is source text the server rewrites, not a global |

#### Callback context and component instance members

| Name | Source | Documented | Status |
|---|---|---|---|
| `onServerRender` option, and the older `init` | `client.js:2342`, `2655-2657`, `4929-4975` | BA `#on-server-render` | covered |
| Callback fields `component`, `revision`, `onEvent`, `id`, `els`, `state`, `i18n`, `sendEvent`, `loading`, `error`; cleanup return value | `client.js:4941-4975` | BA `#on-server-render` | covered |
| `$state`, `$loading`, `$error`, `$sendEvent`, `$onEvent` | `client.js:2428-2450`; `$sendEvent` options at `events-vue.ts:165-196` | BA "Events helpers" | covered |
| `$i18n` and its ten members | `citry-i18n-vue.ts:820-835` | BA `#i18n` | covered |
| `js_data()` keys as instance members | `client.js:1511`, `2389` | BA `#js-data-members` | covered |
| `$c-tr:` bindings | `py/citry/citry/_i18n_directives.py` | `docs_site/content/i18n/browser.md` | covered (template syntax) |
| `$citryPrepared`, `$citryEvents`, prop `citryId` | `client.js:2349`, `2427`, `2453-2470` | `docs_site/content/vue/component-options.md` names them reserved | not covered; the names stay reserved |
| `$citryI18nBinding` | `js/citry-client/src/citry-i18n-vue.ts:831-834` | `component-options.md` reserves "names that a Citry extension adds", not this name | not covered |
| Directives `v-citry-control`, `v-citry-vue-owned`, `v-citry-runtime-events`, `v-citry-on`, `v-citry-event-timing`; component `citry-opaque-html` | `client.js:4511-4652` | none | not covered. `@c-*` attributes compile to them |

#### DOM events

| Event | Source | Documented | Status |
|---|---|---|---|
| `citry:events:before` (cancelable), `after` `{ok}`, `error` `{error}`, `swapped` `{els}`, `stale` `{reason}` (cancelable for reason `version`), with `{instance, class, event}` | `client.js:4891-4905`; `events-vue.ts` | BA `#events-fired-around-each-call` | covered. The `error` detail is a `citry-events/1` error, or one with code `timeout` or `transport` for a failure in the browser (`events-vue.ts:242-256`); BA does not describe that shape yet |
| A server `Dispatch` event, under the app's own name | `client.js:4217-4230` | BA (`$onEvent`, `Citry.events.on`) | covered |
| `citry:ready` `{appId, revision}` | `client.js:4776` | `docs_site/content/vue/server-rendering.md` | covered as documented there; the detail fields are not described |
| `citry:rendered` `{appId, revision}` | `client.js:4327` | none | not covered |

#### Data attributes

| Marker | Source | Documented | Status |
|---|---|---|---|
| `data-cid-<render_id>` | `py/citry/citry/serialize.py:923` | `docs_site/content/guides/migrate-from-django-components.md` | covered as that guide describes it: only on output with no browser behavior |
| `data-citry-vue-document`, `data-citry-vue-fragment`, `data-citry-processed`, `data-citry-css-url`, `data-citry-css-class`, `data-citry-vue-style-app`, `data-citry-i18n`, `data-citry-i18n-binding`, `data-citry-key`, `data-citry-morph`, `data-citry-opaque-*`, `data-citry-security-*`, `data-citry-omit-handler-*` | `client.js:5745`; `js/citry-client/src/citry-fragments.ts:116`; `py/citry/citry/ext/dependencies/emission.py:273`, `582-589`, `887`; `py/citry/citry/ext/i18n/`; `py/citry/citry/nodes/__init__.py:1542-1567` | none | not covered |
| `data-citry-runtime-control`, `data-citry-runtime-events`, `data-cev-*` | `py/citry/citry/nodes/__init__.py:150-165` | none | not covered; a template that writes one is rejected, so the names stay reserved |

### 4.11 HTTP routes

The examples mount every route under the prefix `/citry`
(`py/citry/citry/contrib/asgi.py:9`). The protocol package
(`packages/protocol/events/v1/spec.md`, "HTTP adapters") is the exact
contract for the Events routes. A route is **covered** when a host may
link to it or call it: its path, method and meaning stay the same in
1.x. A digest route is covered as a pattern, and the server answers only
the digests it holds.

| Route | Source | Documented | Status |
|---|---|---|---|
| `POST <prefix>/ext/events/call` | `py/citry/citry/ext/events/routes.py:93`, `242-249` | spec "HTTP adapters" | covered (`citry-events/1`) |
| `<method> <prefix>/ext/events/e/{class_id}/{handler}`, with the handler's declared methods from `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS` | `py/citry/citry/ext/events/routes.py:97`, `263-270`; `py/citry/citry/ext/events/handlers.py:81` | spec "HTTP adapters"; `docs_site/content/events/routes.md` | covered |
| `<prefix>/ext/events/e/{class_id}` (`ViewEvents` verbs `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`) | `py/citry/citry/ext/events/view_events.py:50-57`, `192-202` | `docs_site/content/guides/migrate-from-component-view.md` ("Build the verb URL", built with `citry.build_url`) | covered |
| `GET <prefix>/citry.{digest}.js` | `py/citry/citry/ext/dependencies/routes.py:209-214`; `py/citry/citry/_hashed_runtime.py` | spec "HTTP adapters"; `docs_site/content/advanced/web-frameworks.md` | covered |
| `GET <prefix>/citry.js`, `GET <prefix>/ext/events/runtime.js` | `py/citry/citry/ext/dependencies/routes.py:206`; `py/citry/citry/ext/events/routes.py:96`, `179-183` | spec "HTTP adapters"; `web-frameworks.md` | covered (stable addresses for hand-written links) |
| `GET <prefix>/ext/i18n/runtime.js`, `GET <prefix>/ext/i18n/runtime.{digest}.js` | `py/citry/citry/ext/i18n/routes.py:57-64` | `web-frameworks.md` | covered; mounted only when i18n is configured |
| `GET <prefix>/cache/{class_id}.{hash}.{type}`, `GET <prefix>/cache/{class_id}.{type}`, `GET <prefix>/asset/{file_name}` | `py/citry/citry/ext/dependencies/routes.py:160-203` | `web-frameworks.md` | covered as routes a host must forward; pages Citry renders build the exact addresses |
| `GET <prefix>/ext/events/definitions/{digest}.js`, `GET <prefix>/ext/events/assets/{digest}.css` | `py/citry/citry/ext/events/routes.py:94-95`, `185-215` | `web-frameworks.md`; `docs/design/events.md` 3.8 | covered as routes a host must forward; the request and response are between Citry's own server and browser code |
| `POST <prefix>/ext/i18n/messages` | `py/citry/citry/ext/i18n/routes.py:31-55`, `66-72` | `docs_site/content/i18n/browser.md` (by name only) | covered as a route a host must forward; the JSON it carries is between Citry's own server and browser code |
| `/citry/ext/preview/catalog`, `render/{id}`, `gallery` | `py/citry/citry/ext/preview/routes.py:20`, `77-79` | `docs_site/content/advanced/previews.md` | not covered: served only by the preview command's own server, and preview is experimental (row 3) |

Open items found while making this inventory, left for the maintainer:

- **A server bridge cannot answer Citry's own pages with a render.**
  `EventsDispatcher()` registers only the `html-fragment/1` renderer
  (`py/citry/citry/ext/events/dispatcher.py`, `__init__`), while Citry's
  browser code asks only for `vue-prepared/1`
  (`js/citry-client/src/citry-events-vue.ts:810-814`), so every render
  fails with `handler_error`. The Vue-capable dispatcher comes from
  `citry.ext.events.renderers.dispatcher_for`, which is not exported; the
  docs playground and the benchmark app import it. The constructor
  keywords `render_encoders` and `preferred_renderer` take a
  `RenderEncoder`, and `dispatch(csrf_check=...)` takes an
  `EventHandler`; no public module exports either. The docs now say that
  a bridge for Citry's own pages forwards to the HTTP routes. A public
  way to get the Vue-capable dispatcher would be an addition in 1.x.
- **Prepared renders during an upgrade.** The `prepared` object of a
  `vue-prepared/1` render carries a helper contract hash
  (`py/citry/citry/_vue/compiler.py:526-540`) that the browser checks
  against its own (`client.js:1462`). A page rendered by the old release
  cannot apply a render from a newer server whose helpers changed. The
  spec now says so. Rolling deploys are promised only between 1.x
  releases (decided; 0.x to 1.0.0 starts fresh), so the rolling-deploy
  test (decision 10) should cover a 1.x upgrade that changes the
  helpers.
- **Security fixes.** Decided: a 1.x release may refuse a
  `citry-events/1` input that earlier releases accepted when a security
  fix needs it, and says so in the changelog. The public "Versioning and
  support" page (#624 item 14) should state the same exception for every
  covered part.

## 5. Covered parts this audit does not list

Decision 2 covers these too. They need their own pass before 1.0.0,
owned by the #624 task named in each row.

| Part | Where it is described | Owner |
|---|---|---|
| Template syntax: `<c-*>` tags, `c-*` and `#c-*` attributes, `$c-` bindings, reserved names | [`template_grammar.md`](template_grammar.md) | Decision 11 task (0.9.0): write down the reserved names and mark the V3 syntax frozen |
| VS Code extension settings (`citry.app`, `citry.python`, `citry.envFile`, `citry.typeCheck`, `citry.trace.*`) and commands (`citry.restartServer` and others) | `packages/editors/vscode/package.json` | The citry-lsp and VS Code 1.0.0 task (decision 8) |
