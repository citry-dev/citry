# Public API audit for citry 1.0.0

From 1.0.0 on, everything this audit marks **keep** can change only in a
major release, after a deprecation period. The audit lists every public
name, setting, CLI option and documented extension hook, so the
maintainer can decide what to rename, make private or mark experimental
in 0.9.0, the last release that may break the API
([#624](https://github.com/citry-dev/citry/issues/624), "Freeze the API
and the contracts").

It follows decision 2 of #624 for what counts as public:

- the names in `citry.__all__`;
- the names in the `__all__` of each `citry.ext.<name>` package and each
  `citry.contrib.<name>` module;
- settings, CLI commands and their options, the JSON from
  `citry check --format json`, diagnostic codes, and the documented
  extension hooks.

Names that start with `_`, `citry_core._rust`, generated template code,
error message text and the whitespace of rendered HTML are not covered.
Template syntax and reserved names are decision 11 and belong in
[`template_grammar.md`](template_grammar.md), so this audit leaves them
out. `citry-ui` stays at 0.x (decision 8), so its components are not
listed either.

The audit was made at commit `499f4fcfc` (`origin/main` after the 0.8.0
release). It is an internal design record. The model for it is the
[0.6.0 audit](public_api_0_6_0_audit.md).

## 1. Decisions for tonight

Most of the API stays as it is. The audit proposes **no renames that it
calls necessary**. One rename is listed as optional. The other changes
are experimental marks (docstrings and docs only) and a few small
removals of internal names.

"Uses" counts files, as code / docs / examples / tests:

- code: `packages/py/**` outside tests;
- docs: `docs_site/content`, `docs/` and `README.md`;
- examples: `examples/`;
- tests: test folders under `packages/py`.

Most docs hits are design docs under `docs/`; the "site" note gives the
count under `docs_site/content`.

**Must** means: decide before 1.0.0, because after 1.0.0 the same change
needs a deprecation period or a major release. **Fine** means: leaving it
as it is would also be acceptable.

### 1.1 Proposed changes

| # | What | Proposed change | Uses | Risk tonight | Must or fine |
|---|---|---|---|---|---|
| 1 | Template analysis names: 27 names in `citry.__all__` (all of `citry.analysis` except `LspPosition` and `LspRange`, plus `TemplateLintInfo` and `TemplateVariableInfo`) and the method `Citry.template_analysis()` | Mark experimental | 14 / 5 (site 1) / 0 / 11 | Low: docstrings and one reference intro. No code changes, and citry-lsp needs no change | Must |
| 2 | Host template names: `CompiledBody`, `ForeignClaim`, `ForeignCompileContext`, `ForeignSpan`, `ForeignSpanSet`, `OnTemplateForeignSpansContext`, `OnTemplateForeignCompiledContext`, `render_compiled_body`, `collect_compiled_body_fills`, and the hooks `on_template_foreign_spans` and `on_template_foreign_compiled` | Mark experimental | 11 / 4 (site 1) / 0 / 12 | Low: docstrings, two reference intros, one note in `advanced/extensions.md` | Must |
| 3 | `citry.ext.preview` (all 12 exports) and the `citry ext run preview` commands | Mark experimental | 6 / 4 / 0 / 7 | Low: docs badge and docstrings | Must |
| 4 | Render cache `"payload"` mode: `render_cache_mode = "payload"`, `Extension.export_render_cache()`, `Extension.stage_render_cache()` | Mark experimental | 5 / 3 / 0 / 3 | Low | Must. Their five context and return types are not exported, so leaving the mode stable without exporting them is the one clearly wrong option |
| 5 | `Extension.browser_plugin()` and `Extension.prepare_browser_render()` | Mark experimental | 5 / 5 / 0 / 8 | Low | Must. Their types are not exported either |
| 6 | Events extension hooks `on_event`, `on_event_result`, `on_event_error` | Mark experimental | 3 / 9 / 0 / 2 | Low | Fine. Their contexts are not exported and no guide teaches them; the 0.6.0 upgrade guide names `on_event_result` |
| 7 | Settings `event_result_resolvers` and `event_payload_codecs` | Mark experimental | 5 / 3 (site 0) / 0 / 2 and 4 / 3 (site 0) / 0 / 2 | Low | Must. The setting is public but the shape of a resolver or codec is defined only in private modules |
| 8 | `RenderFrame` | Make private (drop from `citry.__all__` and `reference.yml`; it stays in `citry.citry_render`) | 6 / 8 (site 0) / 0 / 3 | Low: two lines in `__init__.py`, one in `reference.yml`, one test import | Must, unless extensions may replace `ctx.render.frame` (see 1.4) |
| 9 | `ExtensionManager.on_*` (22 dispatch methods) and `ExtensionManager.has_attrs_resolved_hook` | Make private (rename to `_on_*`) | 13 / 1 (site 0) / 0 / 0 | Medium-low: mechanical, but 34 call lines in 12 core files. Move the `on_files_reset` description out of `ExtensionManager.on_files_reset` first | Must. If time runs short, a docstring note "internal, not covered" works as an experimental mark |
| 10 | Keyword-only constructors: `Citry(...)` takes 12 parameters by position, and every `CitrySettings` and `LintSettings` field can be passed by position | Move the `*` right after `self`; add `kw_only=True` to both dataclasses | No positional call found in code, docs, examples or tests | Low | Fine, but cheap now and impossible later without a deprecation |
| 11 | `Events._topics` config name | Stop accepting it until server push exists | 3 / 3 (site 0) / 0 / 1 | Low: validated and stored, but nothing reads it | Fine |
| 12 | `URLRoute.extra` field | Remove | 1 / 0 / 0 / 0 | Low: fits the `URLRoute` note #602 already adds | Fine |
| 13 | `citry.ext.debug.Debug` | Optional rename to `DebugExtension` | 2 / 5 (site 2) / 0 / 6 | Low | Fine. **Recommended: keep.** It is the only built-in extension class without the suffix, and it shares its name with the nested `class Debug:` users write, but it is a consistency fix, not a correctness one |

Every row except 13 is a mark or a removal of something internal.
Rows 1 to 7 change no code. Rows 8 to 12 each need one bullet under
"Upgrading from 0.8.x" in `CHANGELOG.md`. Rows 1 to 7 need a "now marked
experimental" note.

Already done, nothing left tonight:

- `ComponentGraph` and its five helper types, plus
  `Citry.inspect_component_graph()`, are marked experimental (#629,
  commit `16f25ac77`).
- The i18n editor index is back at version 1 in `citry` and citry-lsp
  (same commit). The #624 task can be ticked.
- The API comment in `citry/__init__.py:9-15` already names the
  `__all__` of `citry.ext.<name>` and `citry.contrib.<name>`.

### 1.2 Additions that #624 already asks for, or that close a gap

These only add names, so none needs an upgrade note.

| What | Change | Risk | Must or fine |
|---|---|---|---|
| `safe_eval` and `unsafe` (decision 8) | Re-export from `citry`; change the two imports in `docs_site/content/security.md:936` and `:1007`. Their docstrings are thin, so use a `description_overrides` entry in `reference.yml` rather than a new citry-core release | Low | Must |
| `CitryDeprecationWarning` (decision 4) | Add the public class. The helper that warns at the caller's line already exists, privately, as `warn_at_caller` (`citry/_caller_warnings.py:51`). No pytest `filterwarnings` setting exists yet | Low | Must |
| `citry.reload` | `guides/hot-reload.md:116` teaches `from citry.reload import watch`, but `citry.reload` has no `__all__` and no reference page. Export `watch`, `WatchHandle`, `FileWatcher` and the three watcher classes from `citry` | Low | Must (or say in the decision 2 text that `citry.reload` is covered) |
| `I18nExtension` | The i18n guides call `get_extension("i18n").for_context(...)`, and `reference.yml:287` renders it, but it is not in `citry.ext.i18n.__all__`. Add it | Low | Must |

### 1.3 Defaults (#624 "Review the defaults")

No default on the #624 list is clearly wrong, so none has to change.
Making a lint rule less strict later lets more CI runs pass, so it is not
a breaking change. Making a lenient default stricter later is.

| Default | Current value | Recommendation |
|---|---|---|
| Lint rules | 35 `rule_*` settings: 22 error, 11 warning, 2 ignore (`citry/settings.py:459-496`). All match `defaultSeverity` in `packages/protocol/diagnostics/v1/catalog.json` | Keep. Fine to keep |
| `check_input_types` | `True`, also in production (`settings.py:497`) | Keep. Fine to keep |
| Expression sandbox | `sandbox_expressions=True` (`settings.py:852`), the only switch | Keep. Must not change |
| `security_csp` | `"off"` (`settings.py:862`) | Keep. An opt-in output check. Fine to keep |
| `security_javascript` | `"allow"` (`settings.py:863`) | Keep. #601 already decided to keep today's URL behavior for 1.0. Fine to keep |
| `security_script_integrity` | `"off"` (`settings.py:864`) | Keep. Fine to keep |
| Default cache | a new `InMemoryCache()` per `Citry` (`citry.py:1736`), `max_entries=None` (`cache.py:143`), State budget 64 MiB (`cache.py:102`) | Keep. Under default settings nothing grows without limit, because the render cache is off. A default `max_entries` can still come in 1.x, since it only drops entries earlier. Fine to keep |
| Render cache | `ttl=300` s, `max_entry_bytes=1_000_000` (`ext/cache/config.py:19-20`), `enabled=False` per component | Keep. Fine to keep |
| Page-file store | `vue_asset_max_bytes` 64 MiB (`settings.py:36`) | Keep. Fine to keep |
| Server-stored State lifetime | 24 h when `_max_age` is unset (`ext/events/tokens.py:160`) | Keep. Fine to keep |
| Signed State token lifetime (not on the #624 list) | Never expires when `_max_age` is unset (`docs_site/content/security.md:67-69`) | The one default that looks loose for a stable release: a captured token stays valid until the secret rotates. Decide with the security review whether to give it a default. Decision 7 already accepts that an old page may reload once |

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
   extension replace `ctx.render.frame`. If that is supported, keep
   `RenderFrame` public and accept that its fields are frozen; otherwise
   row 8 stands.
4. **Host template hooks.** The design promised them as supported
   (`template_host_interop.md:13-17`), but the only user is a Django
   proof of concept whose Citry patch is not public. If that counts as an
   outside user, keep row 2 stable.
5. **Underscore names users set.** The Events config (`_guard`, `_csrf`,
   `_max_body_bytes`, ...) and State options (`_public`, `_storage`,
   `_max_age`, ...) start with `_` on purpose, so they do not clash with
   handlers and fields. Decision 2 says `_` names are not covered. The
   Versioning page must say these documented names are covered.
6. **Decision 3 wording.** It says each check rule has a `rule_*`
   setting. Three warnings have none:
   `citry.template.undeclared-template-data-key`,
   `citry.vue.unknown-slot-prop` and `citry.js-data.unsupported-type`.
   Reword the decision, or add the settings (additive, can come in 1.x).
7. **`EventsDispatcher` and `TransportContext`** pass the Events v1 call
   and result data. If the Events v1 task keeps that format internal,
   mark both experimental; if it freezes it, keep them.
8. **One experimental marker.** `ComponentGraph` uses an `Experimental:`
   docstring section, a sentence in the reference intro, and a warning
   box on the guide page. Decision 9 says "badge". Choose one marker
   before rows 1 to 7 copy it.

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

Four read-only passes split the surface: `citry.__all__` in two halves,
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

151 keep, 27 + 9 mark experimental (rows 1 and 2), 6 already
experimental, 1 make private.

| Group | Names | Status |
|---|---|---|
| Engine and settings | `Citry`, `citry`, `CitrySettings`, `LintSettings`, `LintSeverity`, `Secret`, `SecurityCspMode`, `SecurityJavascriptMode`, `SecurityScriptIntegrityMode` | keep |
| Components | `Component`, `ComponentLike`, `ComponentNode`, `Const`, `const_value`, `is_const`, `NestedClassDeclaration`, `NestedSchemaReplacedWarning` | keep |
| Registry and lifecycle errors | `AlreadyRegistered`, `NotRegistered`, `CitryLifecycleInProgress` | keep (the missing `Error` suffix matches Django) |
| Component libraries | `ComponentLibrary`, `LibraryComponent`, `LibraryComponentContextError`, `LibraryComponentInvocation`, `LibraryInstallation`, `LibraryInstallationStale`, `LibraryManifestChanged`, `LibraryNotInstalled` | keep (the three `Library*` errors without a suffix could be renamed cheaply, but it is taste) |
| Rendering | `CitryContext`, `CitryElement`, `CitryRender`, `CitryTemplate`, `Placeholder`, `SerializedRender`, `SerializedScriptSecurity`, `SerializedSecurity`, `OnRenderGenerator`, `RenderReplacement`, `Markup`, `SecurityError`, `VueCodeError` | keep |
| Rendering | `RenderFrame` | make private (row 8) |
| Attributes | `format_attrs`, `merge_attrs`, `normalize_class`, `normalize_style`, `parse_string_style` | keep |
| Slots | `Slot`, `SlotContext`, `SlotData`, `SlotFunc`, `SlotInput`, `SlotResult` | keep |
| Node classes | `Node`, `ElementAttrsNode`, `ElementKeyNode`, `ExprHtmlAttr`, `ExprNode`, `FillNode`, `ForNode`, `HtmlAttr`, `IfNode`, `SlotNode`, `StaticHtmlAttr`, `TemplateHtmlAttr` (and `ComponentNode` above) | keep (see 1.4 question 2) |
| Cache | `CitryCache`, `InMemoryCache`, `CacheConfig` | keep |
| Dependencies | `DependenciesConfig`, `DepsPosition`, `DepsStrategy` | keep |
| Events | `Events` | keep |
| Routes | `URLRoute`, `RouteRequest`, `RouteResponse`, `RouteHeaders` | keep (`URLRoute.extra`: row 12) |
| Extensions | `Extension`, `ExtensionCommand`, `ExtensionConfig`, `ExtensionManager`, `CommandArg`, `CommandArgGroup`, `CommandSubcommand`, `ComponentIntrospectionContext`, `TemplateNamespaceContext`, `TemplateNamespaceContribution` | keep (`ExtensionManager.on_*`: row 9) |
| Hook contexts | `OnAttrsResolvedContext`, `OnCitryClearedContext`, `OnComponentClassCreatedContext`, `OnComponentDataContext`, `OnComponentInputContext`, `OnComponentRegisteredContext`, `OnComponentRenderedContext`, `OnComponentUnregisteredContext`, `OnCssLoadedContext`, `OnExtensionCreatedContext`, `OnFilesResetContext`, `OnJsLoadedContext`, `OnMessagesLoadedContext`, `OnRenderContextMergeContext`, `OnSerializeContext`, `OnSlotRenderedContext`, `OnTemplateCompiledContext`, `OnTemplateLoadedContext`, `OnTemplateResetContext` | keep (19 of 20 have no class docstring; worth fixing for the reference page) |
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

Why row 8: `RenderFrame.prepared_occurrence` is typed with a class that
is not public and that holds an underscore type
(`citry/citry_render.py:223`, `:326-336`). The frame already gained a
field in 0.6.0.

### 4.2 `citry.ext.*` (73 names)

| Module | Names | Status |
|---|---|---|
| `citry.ext.cache` | `CacheConfig`, `CacheKeyError`, `OnComponentCacheHitContext`, `component_cache_key`, `fragment_cache_key` | keep |
| `citry.ext.debug` | `Debug` | keep (optional rename, row 13) |
| `citry.ext.dependencies` | `CitryDependencies`, `DependenciesConfig`, `DependenciesExtension`, `Dependency`, `DependencyRecord`, `OnDependenciesContext`, `Script`, `Style`, `get_dependencies` | keep |
| `citry.ext.events` | `X_CITRY_EVENTS_HEADER`, `CallEvent`, `EventError`, `EventRequest`, `EventsExtension`, `UploadedFile`, `ViewEvents`, `event`, `get_event_url`, and the module `actions` (`Action`, `Data`, `Dispatch`, `Download`, `PushUrl`, `Redirect`, `Render`, `ReplaceUrl`) | keep |
| `citry.ext.events` | `EventsDispatcher`, `TransportContext` | keep, unless Events v1 stays internal (1.4 question 7) |
| `citry.ext.i18n` | the 33 i18n names listed in 4.1, plus `make_context` | keep (add `I18nExtension`, see 1.2) |
| `citry.ext.preview` | `Layout`, `PreviewComponent`, `PreviewError`, `PreviewExtension`, `PreviewGroup`, `PreviewItem`, `PreviewMetadata`, `PreviewPage`, `PreviewVariant`, `Variant`, `Viewport`, `variant` | mark experimental (row 3) |

Why row 3: no package outside Citry uses it, #580 breaks it for any
component with Events, and its design leaves interactive controls and
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
`citry.contrib.*` path. Neither citry-lsp nor citry-ui imports any name
in 4.2 or 4.3.

### 4.4 Extension hooks and attributes

| Hook or attribute | Status |
|---|---|
| `Extension.name`, `class_name`, `Config`, `commands`, `citry`, `urls`, `validate_config_fields`, `introspection_version`, `inspect_component`, `inspect_template_namespace` | keep |
| `on_extension_created`, `on_component_class_created`, `on_component_registered`, `on_component_unregistered`, `on_citry_cleared` | keep |
| `on_component_input`, `on_component_data`, `on_component_rendered`, `on_slot_rendered`, `on_attrs_resolved`, `on_render_context_merge`, `on_serialize` | keep |
| `on_template_loaded`, `on_template_compiled`, `on_template_reset`, `on_js_loaded`, `on_css_loaded`, `on_messages_loaded` | keep |
| `on_files_reset` | keep. It is not declared on `Extension`, and only the `ExtensionManager.on_files_reset` docstring describes it; move that text to the `Extension` docstring before row 9 |
| `on_dependencies` (fired by the dependencies extension) | keep |
| `on_component_cache_hit` (fired by the cache extension) | keep. Its context is exported, but no guide teaches it |
| `render_cache_mode` `"deny"` and `"stateless"`, `render_cache_version`, `render_cache_bypass_reason` | keep |
| `render_cache_mode = "payload"`, `export_render_cache`, `stage_render_cache` | mark experimental (row 4) |
| `browser_plugin`, `prepare_browser_render` | mark experimental (row 5) |
| `on_template_foreign_spans`, `on_template_foreign_compiled` | mark experimental (row 2) |
| `on_event`, `on_event_result`, `on_event_error` (fired by the events extension) | mark experimental (row 6) |
| `ExtensionManager.get_extension`, `emit`, `has_hook`, `commands`, `urls`, `get_extension_command` | keep |
| `ExtensionManager.on_*` (22 methods), `has_attrs_resolved_hook` | make private (row 9) |
| `URLRoute.path`, `handler`, `handler_async`, `children`, `name`, `methods`, `max_body_bytes`, `dotless_params` | keep (#602 changes matching in 0.9.0) |
| `URLRoute.extra` | remove (row 12) |

Decision 9 names "the extension hooks no outside extension uses yet" as
experimental candidates. Read literally, that is every hook, because no
Citry extension exists outside this repository. This audit marks a hook
experimental only when a type it takes or returns is not exported, or
when no guide teaches it and its only intended user is a proof of
concept. Every other hook has exported types and a guide example, so it
stays covered.

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
| events (component `Events` or `extensions_defaults["events"]`) | `_guard`, `_context`, `_csrf` (`"auto"`), `_methods` (`("POST",)`), `_debounce`, `_throttle`; engine only: `_max_body_bytes` (1 MiB), `_max_form_fields` (1000), `_csrf_field_names`, `_csp_nonce`. `_topics`: stop accepting it (row 11). `_debounce` and `_throttle` work but have no docs page |
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

The three commands ask for JSON in three ways (`--format json`,
`--json` as a required flag, `--json`). That can stay: accepting
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
