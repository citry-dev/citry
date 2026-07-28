# Design: the asset compiler (compiling template / js / css dialects)

**Status (2026-07-04): proposal, awaiting review.** This document is the design
pass that [`source_languages.md`](source_languages.md) section 3.3 asks for
before building issue
[#10](https://github.com/citry-dev/citry/issues/10): it settles *when*
compilation runs, what the compiler interface and registry look like, how
compiled output is cached and invalidated, and what ships built in. The
declaration contract (`template_lang` / `js_lang` / `css_lang`, default `None`
= infer, explicit value overrides a file's suffix) and the dual-keyed registry
shape are already decided in `source_languages.md` sections 2 and 3.1 and are
recapped here, not reopened. (One deliberate divergence from that doc's
section 6.4 is flagged in section 4.2 below.)

The headline decisions, in one paragraph: compilation is **lazy, per component
class, at asset-load time**, for all three source kinds; template dialects
(Markdown, Pug) compile **once at template load into citry-HTML** (ordinary
HTML plus the `<c-*>` / `{{ }}` syntax the citry parser reads), upstream of
the parser, not per render. Compiled output is cached under
**content-addressed keys** in a dedicated compile cache (a `CitryCache`
backend, **defaulting to a per-user disk cache**), so stopping and restarting
recompiles only what changed, with no separate build world (no export step,
manifest, or output directory to manage). A `citry compile` CLI command
exists only to **warm that cache eagerly and validate that everything
compiles** (CI, deploys); there is **no `collectcomponent`-style static
export**, no per-component meta files, and no cross-component bundling. This
confirms the provisional takeaway of `source_languages.md` 3.3.

Related docs: the umbrella source-language design
([`source_languages.md`](source_languages.md)), the asset loading substrate
this plugs into ([`asset_loading.md`](asset_loading.md)), the dependency
emission and serving paths that consume the output
([`dependencies.md`](dependencies.md)), the invalidation chain
([`hot_reload.md`](hot_reload.md)), and the extension positioning
([`extensions_roadmap.md`](extensions_roadmap.md) sections 4 and 5). Future
ESM support is parked, without amending this proposal's IIFE choice, in
[`esm.md`](esm.md). For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

Upstream references: issue
[#10](https://github.com/citry-dev/citry/issues/10) (records the
django-components prototype in depth), the prototype's own prior art (the
Tetra framework's esbuild integration, which bundles per app/library; the
prototype adapted it to per-component entries), and the ecosystem survey in
section 2.3 below (Vite, Phoenix, Rails, Laravel, django-compressor).

---

## 1. Scope

In scope:

- The compilation lifecycle for all three source kinds (template / js / css),
  including template dialects.
- The compiler interface, the registry, and its registration API.
- Caching, invalidation, hot reload, and the multi-worker story.
- The built-in compilers (esbuild for TS/TSX/JSX, dart-sass for SCSS/Sass,
  Markdown) and how their external tools are found, and, when missing,
  downloaded and verified.
- The `citry compile` warmup and validation command, plus the `citry tools`
  and `citry cache` maintenance commands.

Out of scope, with reasons given where they are decisions rather than
deferrals:

- **Editor support** for the compiled dialects
  ([`source_languages.md`](source_languages.md) sections 4 to 6; issues #23,
  #24). Registering a compiler buys no editor intelligence, by design.
- **Cross-component bundling and code splitting** (section 3.4).
- **Type checking** (section 7.5).
- **Minification** (section 7.5).
- **Secondary `Dependencies` entries** (section 7.5).
- **A CDN/static export command** (section 3.4).

---

## 2. Prior art

### 2.1 The django-components prototype (recorded in issue #10)

Issue [#10](https://github.com/citry-dev/citry/issues/10) records the
prototype in depth. A fresh read of the actual working tree adds
design-bearing facts beyond what the issue captures. (The file:line cites in
this subsection point into that working tree, which is not part of this
repository: it is the `old-djc.zip` snapshot, django-components commit
`63a05adc` plus uncommitted changes. Phase 6 folds these findings into issue
#10 so the record outlives the snapshot.)

- **The pipeline ran end to end exactly once, manually.** A surviving esbuild
  metafile (`sampleproject/meta.json`) proves a real run with TS compilation,
  per-component hashed bundles, and cross-component code splitting
  (`--splitting --format=esm` producing a shared chunk). The Python plumbing
  around it was never finished: the code that set the component-path
  attribute the export relied on (`_comp_path_relative`) survives in no copy,
  the runtime read path has an unbound-variable error in its static-file
  branch, and the esbuild argv in the final `ts_compiler` has a missing-comma
  bug (`--metafile=metafile.json--outdir=.`), so the last *verified* pipeline
  differs from the last *written* code.
- **The per-component meta-file model was never implemented.** It exists only
  as a design comment (`compilers.py:15-45`) and a pasted chat note
  (`todo/TODO_COMPILERS.md`). Its two load-bearing purposes were recording
  bulk-build hashed outputs and enabling cross-component CSS code splitting.
  Both purposes are tied to the batch-export model.
- **Batching existed for bundling.** The `compile_files` orchestration groups
  files per compiler explicitly for compilers that need to process all files
  of the same kind together (`compilers.py:91-93`, paraphrased), and the
  single registered compiler used esbuild `--splitting`. The Tetra-derived
  blocks kept in the file state the underlying stance: compilation is a
  preprocess step, not a runtime concern of the component library
  (`compilers.py:404-407`).
- **Two static-file layouts coexisted unreconciled**: the writer produced
  `<component-relative-dir>/<stem>-<class-hash>.<lang>` while the runtime
  redirect built `django_components/cache/<class-id>.<type>`. The meta file
  was the intended resolution; it never arrived. Lesson: a design where the
  writer and the reader derive the location independently drifts; the reader
  must look up what the writer recorded, or (this design) both must derive it
  from content.
- **Two declaration mechanisms were prototyped side by side**: explicit
  `js_lang = "ts"` attributes and `types.ts` annotation inference, with the
  metaclass wiring for the latter commented out. `source_languages.md`
  section 2 settled this in favor of the attributes.
- **Type checking was in the compile path**: `ts_compiler` optionally ran
  `tsc --noEmit` via a temporary `tsconfig.json` that `extends` the user's
  real one (a workaround for tsc's CLI not accepting both a project file and
  a file list). Ambient types for the component-JS globals lived in a
  `global.d.ts` (`$onLoad`, `ComponentContext` with `$id`/`$name`/`$data`/
  `$els`), i.e. type-checking inline component JS was part of the intent.
- **Template dialects were never built.** Markdown and Pug appear only in a
  roadmap comment (`compilers.py:359-373`): they were *intended* to run in
  `render`, right after the template renders and before any HTML postprocess
  hook. Section 3.2 decides differently.
- The prototype's `collectcomponent` command, `COMPILERS_ENABLED` setting
  sketch, "copy files when compilation is disabled" idea, and live-reload
  plan (a comment floating re-running the collect command when component
  files change) are all artifacts of the batch-export model and are
  superseded by the lifecycle chosen below.

### 2.2 What citry has already built (the substrate)

Checked: `citry/assets.py`, `citry/extension.py`,
`citry/extensions/dependencies/*`, `citry/settings.py`, `citry/cache.py`,
`citry/citry.py`, `citry/reload.py`, `citry/command.py`, `citry/commands/*`,
plus the design docs listed above. The pieces the compiler slots between:

- **Lazy per-class asset loading** (`asset_loading.md` section 3;
  `citry/assets.py`). `Component.get_template()/get_js()/get_css()` load
  inline or file content once per class, fire `on_template_loaded` /
  `on_js_loaded` / `on_css_loaded` (map hooks, i.e. hooks that can replace
  the content they receive; the post-hook content is what gets cached), and
  cache on the class. No I/O at import. One relevant gap:
  `_load_asset_content` discards the resolved file path after reading
  (`assets.py:268`), so a suffix-keyed compiler needs the path retained
  (section 4.2).
- **The script cache and lazy repopulation** (`dependencies.md` sections 4
  and 9; `extensions/dependencies/scripts.py`). Class scripts have mutable
  compatibility entries plus content-addressed versions in the pluggable
  `CitryCache`; generated URLs name the version. A compatibility read validates
  its payload against `get_js()`/`get_css()`. The one pre-cache transform that
  exists today, the `$component(` expansion, runs at that point.
- **Content-hash asset URLs** (`dependencies.md` sections 9.4 and 15;
  `scripts.py:225-236`): `asset/<md5-12-of-content>.<ext>`, where the hash
  fingerprints the URL so a changed file gets a new URL. The precedent this
  design generalizes into the compile cache.
- **The invalidation chain** (`hot_reload.md`; `citry.py:496-514`):
  `Citry.invalidate_file(path)` resolves classes via the engine file index
  and calls `reset_template()` + `reset_files()`, which fires
  `on_files_reset`; the dependencies extension drops its merged result and
  the class's script cache keys. Everything downstream reloads lazily.
- **The CLI** (`extensions_commands.md`; `commands/__init__.py:72-84`): core
  commands are one `ExtensionCommand` subclass plus one tuple entry; the
  engine is reachable as `self.citry` and autodiscovery runs before the
  registry is read.
- **`CitrySettings`** (`settings.py:25-26`, fields at `settings.py:80-87`):
  a frozen dataclass that grows field by field; no compiler-related field
  exists yet.

### 2.3 The ecosystem survey (what the industry converged on)

Surveyed for this design: Vite (dev transform-on-demand, prod bundle +
manifest), Phoenix (the `esbuild`/`tailwind` hex packages), Rails (propshaft,
jsbundling-rails, tailwindcss-rails, dartsass-rails, importmap-rails, and
sprockets' live compilation), Laravel (Vite plugin, the `hot` dev-marker
file), esbuild itself (metafile, splitting, CLI vs API), dart-sass, Lightning
CSS, SWC, Bun, and django-compressor. Findings that shaped this design:

- **Two layers everywhere**: a swappable compile layer (esbuild, sass,
  tailwind) and a framework-owned digest/manifest layer. citry already owns
  the second layer (content-hash URLs, the script cache); this design adds
  only the first.
- **Per-file transform is the norm; whole-graph passes exist only for
  bundling.** Vite transforms each module on demand in dev and bundles only
  for production because code splitting needs the whole module graph. This
  is the industry echo of `source_languages.md` 3.3's conclusion, and it is
  why excluding cross-component bundling (section 3.4) removes the need for
  any batch step.
- **Lazy compile-on-request in production is the documented anti-pattern**
  when the unit is a request: Rails calls sprockets live compilation "not
  recommended"; django-compressor needed per-node locking after concurrency
  failures on high-traffic sites. citry's unit is different (once per
  component class, output regenerable from source, cached), which avoids the
  per-request failure mode, but the cold-start cost is real and is addressed
  with the persistent compile cache plus the `citry compile` warmup
  (section 8).
- **Every serious compiler is a native binary**; no maintained full-featured
  esbuild Python binding was found as of this writing (the PyPI `esbuild`
  wrapper is stale and unsafe; `esbuild-py` is transform-only). The two
  proven acquisition shapes are Phoenix's (download the pinned platform
  binary at first use, no prompt, env-var override for airgapped setups;
  note its verification is uneven: the esbuild path checks the npm
  registry's signature and integrity metadata, the tailwind/GitHub path
  verifies nothing beyond TLS) and Rails' (platform-specific packages
  through the language's package manager). Section 7.4 adopts the download
  model with a deliberately stronger verification scheme than Phoenix's.
- **esbuild specifics**: the incremental context API and plugins (virtual
  modules) are JS/Go only; a CLI-driven integration gets stdin/file entries,
  `--bundle`, `--metafile`, and `--watch`. The metafile's `inputs` map is how
  a compiler reports which files a bundle read, which this design uses for
  dependency-aware caching (section 5.2). Two CLI facts that shaped
  section 7.1: the resolve directory for stdin input is the subprocess
  working directory (esbuild's docs say the CLI has no flag for it), and
  `--metafile` requires an output path (it cannot combine with
  stdout-only output).

---

## 3. When compilation runs: lazy, per class, at load time

### 3.1 The decision

A component's source is compiled **the first time the class's asset is
loaded**, inside the existing loaders in `citry/assets.py`, once per class:

```
raw source (inline attr or file)
  -> [compiler, if the resolved language needs one]     <- new step
  -> on_template_loaded / on_js_loaded / on_css_loaded  <- existing hooks
  -> cached on the class (_citry_template / _resolved_js / _resolved_css)
  -> everything downstream unchanged (parse, $component, script cache,
     emission, serving)
```

There is no build step, no export directory, and no freeze point (no moment
at which the component set must be declared complete). This is the same
lifecycle the rest of citry already uses: lazy, cached per class, reset by
`invalidate_file`, repopulated on next use. The reasons, restating
`source_languages.md` 3.3 as decisions:

- **Batching exists for bundling, and citry does not bundle across
  components** (section 3.4). Without a whole-graph pass there is nothing a
  build step computes that the lazy path cannot.
- **An export exists to hand assets to further processing.** citry serves its
  own assets (inline tags or the `cache/` and `asset/` endpoints); there is
  no further processor to hand them to. The "static directory" the prototype
  wrote is, in citry terms, a cache, and citry already has a pluggable cache.
- **Everything already built points this way**: lazy loaders, lazy script
  repopulation, content-hash URLs, reset-then-lazily-reload invalidation. A
  batch build would be the one eager subsystem in an otherwise lazy engine.

The eager path still exists, but as a *warmup of the same lazy machinery*:
`citry compile` (section 9.2) runs autodiscovery, loads and compiles every
component's assets, and reports errors. Deploy pipelines run it at
image-build time so production processes start with a hot compile cache.

### 3.2 Template dialects compile at load, not per render

A `template_lang = "markdown"` (or `.md` template file) compiles **once, at
template load, into citry-HTML**, and the citry parser then parses that
output exactly as if the author had written it. The dialect step runs inside
`load_template`, before `on_template_loaded`, so the hook (and the cache, the
parser, `on_template_compiled`, and the const machinery, the pass that
pre-renders the constant parts of a template, [`component_constness.md`](component_constness.md))
sees only citry-HTML. Per-render work is unchanged.

The prototype *intended* to run Markdown/Pug on the rendered output of every
render (a roadmap comment; never implemented). The two models differ
semantically, and choosing load time is a deliberate decision:

- **`template_lang` describes the source, not the data.** With load-time
  compilation, `{{ }}` expressions are preserved as opaque text through the
  dialect compile, and their *values* are not markdown-processed at render
  time. Rendering markdown that arrives in a variable (`{{ post_body }}`) is
  a different feature (a filter or a component that transforms its slot
  content) and is out of scope here. The prototype's post-render model
  conflated the two.
- Load-time compilation is also the cache-friendly arrangement: the dialect
  cost is paid once per class, upstream of the per-class template compile
  cache and the cache of pre-rendered constant parts, instead of on every
  render downstream of both.

**What dialects do with `{{ }}` and `<c-*>`:** the rule is pass-through. A
template-dialect compiler must emit citry expressions, citry comments, and
`<c-*>` tags verbatim so the citry parser interprets them; it never
interprets them itself. Pass-through is not free (a markdown renderer will
happily escape quotes or wrap `*` in emphasis inside an expression), so each
dialect compiler must actively protect citry syntax; how the built-in
Markdown compiler does it is specified in section 7.3. Whether `<c-*>` tags
survive a specific dialect intact is a property of that dialect's compiler
(CommonMark passes block-level HTML through when the html option is on; Pug
has its own syntax for embedding raw HTML) and is documented per compiler,
not legislated globally.

### 3.3 Consequence: this feature consumes no postprocess hooks

Issue #10 listed `on_js_postprocess` / `on_css_postprocess` and a post-render
`on_template_postprocess` as prerequisites. Under this design the compiler is
not hook-based and runs upstream of the existing `on_*_loaded` hooks, so
**this feature consumes none of the three**. Per the rule in
[`extensions_roadmap.md`](extensions_roadmap.md) section 4 (build a hook only
when its first consumer lands), they stay unbuilt; their remaining candidate
consumers are the inline-CSS extension, the reactive extension's whole-HTML
wrap (both already on the roadmap's list), and the minifier extension this
document proposes in section 7.5.

### 3.4 Alternatives considered and rejected

- **A batch build step after autodiscovery (the prototype's
  `collectcomponent`, made citry-native).** Rejected: its only unique
  capability is cross-component bundling (shared chunks, one type-check
  pass), which this design excludes; everything else it does, the lazy path
  does with less machinery (no freeze point, no export directory, no meta
  files, no stale-export-vs-edited-source window). The `citry compile`
  warmup preserves the operationally useful part (pay the cost at deploy,
  not first request).
- **Render-time template dialects (the prototype's intended model).**
  Rejected for the reasons in 3.2: per-render cost for a per-class
  transform, cache hostility, and the source-vs-data conflation.
- **Compilers as `on_*_loaded` hook subscribers (an extension, not a core
  registry).** Mechanically possible today, rejected as the primary
  mechanism: a map hook sees every component's content with no language
  resolution, no claims ("I handle `.scss`"), and no error story for an
  unclaimed language. The registry gives declarative claims and lets citry
  raise "no compiler registered for `scss`" with fixes. Extension packages
  can still *ship* compilers (section 5.3).
- **Cross-component bundling / code splitting.** Excluded from this design.
  It requires the whole-graph build world (an export, a manifest, chunk
  serving) for a benefit that is real but narrow: deduplicating modules
  shared between components. The cost of not having it: a util imported by
  five components' TS is inlined five times. Accepted for now; the falsifier
  below records the revisit trigger.
- **A CDN/static export command.** Not part of this feature. If it is ever
  wanted, it is a thin separate command that walks the same compiled outputs
  and writes them to a directory; nothing in this design blocks it, and
  nothing here depends on it.
- **Delegating the whole feature to Vite (or another bundler's dev server +
  manifest).** The tempting version: citry manages no compilers at all;
  users run Vite, citry emits dev-server URLs in dev and reads
  `manifest.json` in prod, the laravel-vite / django-vite pattern. Rejected
  as the core mechanism for four reasons. (1) **The unit does not match.**
  Vite compiles a module graph rooted at file entry points; citry's unit is
  per-component source bodies, many of them inline Python strings. Feeding
  those to Vite means either materializing every inline body to disk or
  writing and maintaining a citry Vite plugin in JS (virtual modules are a
  plugin-API feature), plus a bridge that exports the component list as
  entries, i.e. the component-introspection API (#26) as a prerequisite.
  (2) **It inverts the serving story.** In dev the browser loads assets from
  Vite's own HTTP server (with its HMR client injected); in prod the build
  writes hashed files citry does not serve. Both replace the dependencies
  extension's inline-or-endpoint model rather than feeding it, and the
  runtime integration points (`$component` expansion, `css_data`
  variables) would need re-plumbing through Vite's pipeline. (3) **It is the
  batch world again**: entries known upfront, a build step, a manifest
  consumed at render, everything section 3.1 rejects, now owned by an
  external tool. (4) **It makes Node plus a JS project scaffold
  (package.json, vite.config) a hard requirement for every citry user**,
  where this design keeps zero-config for markdown and "bring a binary" for
  TS/SCSS. Note the design is not anti-Vite: it delegates the actual
  compilation to the same tools Vite uses (esbuild, dart-sass) and copies
  Vite's own dev-mode shape (per-file transform, content-hash cache) minus
  bundling; citry owns only the thin orchestration. And a `citry-vite`
  *ecosystem extension* for projects that already run Vite (component assets
  as Vite entries via #26, manifest-reading emission, dev-server tag
  rewriting) remains possible on top of the extension and introspection
  seams; nothing here blocks it, and this feature does not depend on it.

### 3.5 What would falsify this design

- **Cold-start cost at scale.** The model assumes compiling one component
  (one subprocess, roughly 20 to 200 ms) lazily per class, amortized by the
  persistent compile cache, is acceptable. If a real project (hundreds of
  compiled components, multi-worker fleet, no persistent cache possible)
  shows unacceptable first-request latency even with the warmup command
  documented, the design needs an eager parallel compile pass or a batched
  single-invocation compiler, which the per-file interface deliberately does
  not offer.
- **Cross-component duplication pain.** If measured bundle duplication (the
  same vendored module inlined into many components) becomes a practical
  problem for real users, code splitting, and with it a build step and a
  manifest, must be revisited.
- **A dialect that cannot pass citry syntax through.** The template-dialect
  rule assumes a dialect compiler can treat `{{ }}` / `<c-*>` as opaque. A
  dialect whose own syntax collides irreconcilably (so that pass-through
  cannot be implemented) would need render-time or AST-level integration,
  reopening 3.2 for that dialect.

---

## 4. Declaration and language resolution

### 4.1 Recap of the decided contract

From `source_languages.md` section 2, unchanged: `template_lang` / `js_lang`
/ `css_lang` are plain string class attributes, default `None`.

- `None` means **infer**: for a file body, from its suffix; for an inline
  body, the base dialect (`html` / `js` / `css`).
- An explicit value **wins over a file's suffix** (`css_file = "card.txt"`
  with `css_lang = "scss"` compiles as SCSS; `js_file = "card.ts"` with
  `js_lang = "js"` is served as plain JS, no compile).

### 4.2 Resolution algorithm

Per asset kind, at load time:

1. Determine the language: the effective `*_lang` if set (see the
   inheritance rule below), else the file suffix (without the dot), else the
   base dialect name for inline bodies.
2. If the language is in the kind's **base suffix set**, skip compilation
   entirely: templates `{html, htm}`, scripts `{js, mjs, cjs}`, styles
   `{css}`. Base dialects are not registry entries; there is no identity
   compiler to configure or accidentally shadow. (This is a deliberate
   divergence from `source_languages.md` 3.2/6.4, which list `html`/`js`/
   `css` among the shipped compilers and frame every built-in as a plugin.
   An identity entry would add a shadowing hazard with no capability:
   transforming plain JS/CSS/HTML is exactly what the `on_*_loaded` hooks
   already do. Phase 6 updates those sections.)
3. Otherwise look up a compiler in the registry (section 5.3) for that asset
   kind. **The match is keyed by the provenance of the name**: a language
   set explicitly via `*_lang` matches the compilers' `languages` claims
   (for inline and file bodies alike); a language inferred from a file
   suffix matches their `suffixes` claims. Found: compile. Not found: raise
   at load time with an error naming the component class, the asset kind,
   the resolved language, and the fixes (register a compiler, install the
   extra that provides one, or set `*_lang` to the base dialect if the
   content is actually plain).

Step 3's error is new surface: today `assets.py` loads any file it can read,
so a `js_file = "card.coffee"` that silently served CoffeeScript to the
browser will start failing loudly at load instead. That is the intended
behavior change (the draft guard the prototype only sketched); the base
suffix sets in step 2 keep every suffix that is legitimately plain today
(`.htm`, `.mjs`, `.cjs`) working unchanged.

Two supporting changes this needs:

- **Retain the resolved file path for JS/CSS.** `_load_asset_content`
  currently discards it (`assets.py:268`); the loader must keep it (as
  `load_template` already keeps `CitryTemplate.filepath`) for suffix
  inference, for the compiler context, and as the resolve directory for
  relative imports (section 7.1).
- **The `*_lang` inheritance rule.** `asset_loading.md` 3.2 makes each
  inline/file pair one inheritance unit (the first class in the MRO whose
  own `__dict__` declares either member wins for both). The lang attribute
  needs its own rule, because a lang can describe a specific source or serve
  as a standing default:

  - A `*_lang` declared on a class that **also declares a member of the same
    pair** describes that class's source. It applies only while that pair
    declaration is the winning one: if a subclass redeclares the pair, the
    ancestor's lang is discarded along with the ancestor's source (a parent's
    `js_lang = "ts"` must not leak onto a child that replaces `js` with
    plain JS).
  - A `*_lang` declared on a class that **declares neither pair member** is a
    standing default and inherits normally (the
    `class TSBase(Component): js_lang = "ts"` pattern, where subclasses
    supply the sources).
  - Mechanically: walk the MRO from the most derived class; the first class
    whose own `__dict__` declares the lang wins, except that a
    lang-and-pair-declaring class above the winning pair declaration is
    skipped (its lang died with its source). An explicit `*_lang = None`
    is a declared value meaning infer, and stops the walk.

  Phase 1 locks all three behaviors (leak prevention, standing default,
  lang-only override) with tests, including the diamond case (the pair from
  one base, a standing-default lang from a sibling base).

Aliases are just extra registered names (`"md"` and `"markdown"` resolve to
the same compiler), so the alias set is visible in one place, the registry.

---

## 5. The compiler interface and registry

### 5.1 The `Compiler` class

A compiler is a class (citry's extension idiom, giving options a natural home
in the constructor), registered as an instance:

```python
class Compiler:
    # Which asset slot this compiler feeds. A compiler produces the base
    # dialect of its kind: citry-HTML, plain JS, or plain CSS.
    kind: ClassVar[Literal["template", "js", "css"]]
    # Names this compiler claims when *_lang selects the language explicitly,
    # e.g. ("ts", "tsx", "jsx").
    languages: ClassVar[tuple[str, ...]]
    # File suffixes this compiler claims when the language is inferred from
    # a file, without the dot, e.g. ("ts", "tsx").
    suffixes: ClassVar[tuple[str, ...]]

    def cache_tag(self) -> str:
        """A string that changes whenever this compiler's output could
        change for the same input and resolve directory: implementation
        version, tool version, and options. Part of the compile-cache key
        (section 8.1)."""

    def compile(self, ctx: CompileContext) -> str | CompileResult:
        ...
```

`CompileContext` carries `source: str`, `lang: str` (the resolved name),
`filepath: Path | None` (`None` for inline bodies), `resolve_dir: Path` (the
file's directory, or the component's module directory for inline bodies),
`component_class`, and `citry`. Returning a plain string is shorthand for a
`CompileResult` with no dependencies.

This is the Svelte-preprocessor shape (`{content, attributes, filename} ->
{code}`) adapted to citry: one source string in, one compiled string out, per
component, per kind. It is deliberately not the prototype's batch signature
(`CompilerFn(entries, args) -> List[Path]`), which existed for bundling
(section 3.1).

### 5.2 `CompileResult`, dependency reporting, and determinism

```python
@dataclass(frozen=True)
class CompileResult:
    code: str
    # Files the compiler read besides the entry source (imports, partials),
    # as absolute paths.
    dependencies: tuple[Path, ...] = ()
```

`dependencies` matters for two things:

- **Hot reload.** The loader registers each reported dependency in the
  engine file index (`Citry._register_component_file`), so editing an
  imported `.ts` module or an `@use`d SCSS partial invalidates the components
  whose compiled output embeds it. Without this, only edits to the entry file
  would trigger recompiles.
- **Cache validation.** The compile cache stores each dependency's content
  hash and revalidates on lookup (section 8.1).

The esbuild compiler gets the list from the metafile's `inputs` (with the
entry itself stripped and paths absolutized, section 7.1); the sass compiler
over-approximates (section 7.2); the markdown compiler has none. This is
Eleventy's `addDependencies` in citry shape. The result type has room to grow
(a `sourcemap` field is the obvious later addition) without changing the
interface.

Compilers must be deterministic: same input, same resolve directory, same
tool version, same options, byte-identical output. Compiled output is a
cache-keyed contract (the repo determinism rule,
[`/CLAUDE.md`](../../CLAUDE.md) gotchas); a compiler that embeds timestamps
or unordered collections in its output breaks content-hash caching and
fingerprint URLs. For subprocess compilers the working directory is part of
"same input" (esbuild, for one, embeds cwd-relative path comments in
bundles), so the built-in compilers pin the subprocess cwd to
`ctx.resolve_dir` rather than inheriting the host process's.

### 5.3 Registration and precedence

A new frozen field on `CitrySettings`:

```python
Citry(compilers=(MyPugCompiler(), EsbuildCompiler(target="es2020")))
```

Entries are compiler instances, classes (instantiated with no arguments), or
import strings (`"myapp.compilers.PugCompiler"`), matching what
`extensions=` accepts, so config-file-driven setups work the same way for
both fields.

The engine builds one per-instance registry, scanned in order: **user
entries, then extension-provided entries, then built-ins**; the first
compiler whose kind matches and whose claim (per the provenance rule in 4.2
step 3) covers the source wins. User-first means a project can override a
built-in for the same language with no privileged path, per
`source_languages.md` 6.4. Registration is data on the instance like
everything else (the
[django-components #1413](https://github.com/django-components/django-components/issues/1413)
rule: all engine state lives on the `Citry` instance, no module globals);
there is no global mutable registry.

Rejected registration shape: **an extension hook as the only mechanism**.
Indirection with no benefit for the common case (one project, one custom
compiler), and the compiler registry is core, below the extension layer.

An `Extension.compilers` surface (extensions shipping compilers, alongside
`commands`, a ClassVar, and `urls`, a property) is the expected growth path,
added when the first extension needs it (the Tailwind extension is the
likely candidate), not speculatively; the precedence slot above is reserved
for it now so adding it later changes no existing behavior. One limitation
is accepted as a decision until then: composing *around* a registered
compiler (say, injecting SCSS variables before the user's SCSS compiles) is
app-author territory, done by registering a wrapper compiler for the same
language; an extension that needs it ships such a wrapper class and
documents its registration.

### 5.4 What ships built in

As they get built (phasing in section 13): `markdown` (template), `ts` /
`tsx` / `jsx` (js, via esbuild), `scss` / `sass` (css, via dart-sass). `pug`
(template) and `less` (css) are candidates once someone wants them; no
promise is implied by the registry being open.

---

## 6. Pipeline placement and the hook invariant

**The invariant: everything downstream of the compiler sees base dialects
only.** `on_template_loaded` receives citry-HTML, `on_js_loaded` receives JS,
`on_css_loaded` receives CSS, whatever the author wrote. Hook authors never
branch on source language; the parser, the script cache, the emission paths,
and the endpoints are untouched by this feature.

The full per-class flow with the new step marked:

```
template:  attr/file -> [dialect compiler] -> on_template_loaded -> CitryTemplate
                        -> parse -> on_template_compiled -> const machinery
js:        attr/file -> [compiler] -> on_js_loaded -> _resolved_js
                        -> cache_component_js ($component expand) -> CitryCache
                        -> inline tag or cache/<class_id>.<content_hash>.js endpoint
css:       attr/file -> [compiler] -> on_css_loaded -> _resolved_css
                        -> cache_component_css -> CitryCache -> tag or endpoint
```

One existing transform needs its contract tightened rather than moved: the
`$component(` expansion (`scripts.py:56-91`) is a regex applied to the
class's whole JS at cache time. Today its input is author-written component
JS; under `--bundle` the input becomes concatenated module code, and an
author who *imports or defines* a value named `$component` (instead of
using the ambient global) would get the definition site rewritten into
invalid JS, failing in the browser with no build-time error. The decision:
`$component` is a **reserved name in component JS, compiled or not**; it
may only be called, never defined or imported. The esbuild compiler enforces
this loudly, raising at load time when the compiled bundle *defines* the
symbol (a `function`/`const`/`let`/`var` declaration of that name), with the
fix in the message (use the ambient global; citry's docs ship the `.d.ts`
declaration for TS authors, the prototype's `global.d.ts` pattern). The
alternative considered, injecting a real `$component` binding at compile
time via an esbuild banner and dropping the regex for compiled languages,
was rejected for v1: it makes compiled output class-specific (the class id
is baked into the banner), which shrinks compile-cache sharing and splits
the expansion into two mechanisms; it remains the evolution path if the
reserved-name rule proves too restrictive.

A transform that must see the *pre-compile* source is not a hook use case;
it composes at the registry instead (a wrapper compiler for that language,
section 5.3). This keeps one seam per job: compilers translate languages,
hooks transform base dialects.

---

## 7. Built-in compilers

### 7.1 esbuild (`ts`, `tsx`, `jsx`)

One esbuild CLI invocation per component: `--bundle` so relative imports in
component JS work (`import { x } from "./util"`, the prototype's proven
case), `--format=iife` (the output is one self-running script, no module
loader involved) to match how component scripts are emitted today,
`--metafile` for dependency reporting, browser platform, configurable
`target`. Options are constructor arguments on `EsbuildCompiler` with
sensible defaults.

Invocation mechanics, pinned down because two esbuild CLI constraints shape
them:

- **The resolve directory is the subprocess working directory.** esbuild's
  CLI has no flag for the stdin resolve dir; it uses the cwd. So the
  compiler always runs esbuild with cwd = `ctx.resolve_dir`: inline bodies
  are piped via stdin (`--loader=ts`) and their relative imports resolve
  against the component's module directory (the same base as the file-lookup
  chain's rule 2); file bodies pass the entry path and resolve from the
  file's own directory as usual. No temp files in the user's source tree,
  nothing for the file watcher to see.
- **`--metafile` requires an output path** (esbuild refuses metafile output
  with stdout-only output). Each invocation therefore writes `--outfile` and
  `--metafile` into a per-invocation OS temp directory (created with
  `tempfile.mkdtemp`, outside any watched root, removed afterwards); the
  compiler reads the code from the outfile and the dependency list from the
  metafile's `inputs`, strips the entry itself (the synthetic `<stdin>` key
  for inline bodies, the entry path for files), and absolutizes the
  remaining paths against the compile cwd before returning them. Recording
  the entry as its own dependency would make cache revalidation rehash a
  nonexistent file and recompile on every load, so stripping it is
  correctness, not tidiness.

Bundling is per component: an import shared by several components is
duplicated into each bundle (section 3.4). That is also the documented way
to share code between components: put it in a `.ts`/`.js` file each
component imports. Importing another *component's* module is out of scope,
and IIFE output is the settled format; ESM would force `type="module"`
emission through the dependencies extension's tag rendering for a use case
the shared-file pattern already covers.

### 7.2 dart-sass (`scss`, `sass`)

One `sass` CLI invocation per component: stdin (`--stdin --indented` for the
`sass` dialect) for inline bodies, the file path otherwise, with
`--load-path` entries for the component's module directory and each
`settings.dirs` entry. Relative imports ride the load paths, not the
subprocess cwd (dart-sass has deprecated cwd-relative resolution for stdin).
dart-sass is the canonical Sass implementation and ships as a standalone
binary; the node-based `esbuild-sass-plugin` route the prototype took is not
needed once compilation is per component.

**Dependency reporting is an over-approximation.** The sass CLI, unlike the
JS API, does not report which files a compile loaded, and the closest proxy
(the source map's `sources` list) omits loaded files that contribute no CSS
output, which is exactly the shape of the variable/config partials users
edit most. Instead of an under-report that would leave hot reload and cache
revalidation blind to those edits, the compiler reports **every `.scss` /
`.sass` file under its load paths** as a dependency. The cost is
over-invalidation (editing any stylesheet partial recompiles every
sass-using component) and proportional rehashing on cache lookup; both are
bounded by project size and are the safe side of the trade. Precise
reporting can later ride the embedded Sass protocol (a persistent host
process speaking dart-sass's structured protocol), which is a heavier
integration shape than a CLI call and deliberately not v1.

### 7.3 markdown (`markdown`, `md`)

Pure Python via `markdown-it-py` (CommonMark), installed by the
`citry[compiler-markdown]` extra and imported inside the compiler rather
than at module top, so `import citry` works without the extra installed (the
same pattern as the watcher backends, [`hot_reload.md`](hot_reload.md)
section 8).

Pass-through of citry syntax is real work, not a default: out of the box a
markdown renderer entity-escapes quotes and ampersands inside `{{ }}` and
can pair `*` characters across two expressions into an `<em>` span,
corrupting the expressions before the citry parser ever sees them. The
compiler therefore:

- pins `html=True` explicitly (so `<c-*>` tags flow through as raw HTML
  regardless of the markdown-it preset),
- registers an inline rule that tokenizes `{{ ... }}` and `{# ... #}` as
  opaque raw tokens *before* escaping and emphasis run (the established
  pattern of markdown-it jinja/nunjucks plugins),
- escapes citry delimiters inside code spans and fences as numeric character
  entities (`&#123;` for `{`), on top of markdown-it's own `<`/`&` escaping
  there, because a code sample is literal by definition and must not reach
  the parser as live syntax (the parser reads entities as plain text, so the
  escaped form renders as the author wrote it),
- dedents inline sources before compiling (Python authors indent
  triple-quoted strings, and Markdown reads 4-space indentation as a code
  block).

One authoring gotcha gets documented with the compiler rather than fixed: in
CommonMark, markdown inside a raw HTML block (a `<c-card>` element with no
blank line separating its content) is not processed, while blank-line
separated content is. That is CommonMark's HTML-block rule, not a citry
choice.

### 7.4 Finding and installing the external tools

Subprocess compilers resolve their binary in order:

1. An explicit constructor argument (`EsbuildCompiler(bin="/opt/esbuild")`).
2. An environment variable (`CITRY_ESBUILD_PATH`, `CITRY_SASS_PATH`), the
   airgapped/CI override.
3. `./node_modules/.bin/<tool>` relative to the current working directory
   (projects that already have a JS toolchain).
4. The tool name on `PATH`.
5. Citry's own tool cache; if the pinned version is not there and
   auto-download is enabled (the default), download it, verify it against
   the hash vendored in citry, and install it into the cache.
6. Failing all: an error naming the tool, the component that needed it, and
   the fixes (including how to enable the download when it was disabled).

Phase 3 builds steps 1 to 4 and 6 ("bring your own binary", the
jsbundling-rails model); phase 5 adds step 5. The download design, settled
against an industry survey (Phoenix esbuild/tailwind, Playwright, Cypress,
Puppeteer, Electron, node-gyp, Next.js SWC, pytailwindcss; primary sources
read):

**Consent: download on first use, no prompt, with a hard off-switch.** No
surveyed tool shows an interactive prompt; consent is structural. Playwright
alone requires an explicit install command, and its reasons do not apply
here (gigabyte-scale browsers vs single-digit-MB compilers). The 2025-2026
trendline away from npm postinstall downloads (pnpm 10 blocks lifecycle
scripts after the Rspack attack; Electron 42 and Playwright 1.38 dropped
their install scripts) is about *install-time script execution*, an attack
class Python does not have; a first-use download executes with no more
privilege than the framework code already running. What supply-chain-
sensitive environments actually need, per every precedent, is determinism
and control, not a prompt:

- `CITRY_TOOLS_AUTO_DOWNLOAD=0` (and a settings equivalent) disables step 5
  entirely; the step-6 error then says the download was skipped and why
  (django-tailwind-cli's `TAILWIND_CLI_AUTOMATIC_DOWNLOAD` is the
  precedent).
- `citry tools install` pre-downloads the pinned tools explicitly (the
  Playwright / `mix esbuild.install` shape), sharing one code path with the
  lazy download; the natural companion of `citry compile` in CI and Docker
  builds.
- Every auto-download logs one loud line: tool, version, resolved URL,
  destination, and the verified hash. That line is the consent surface.

**Verification: per-platform hashes vendored in citry, next to the version
pin.** Citry already pins a known-good version per tool, so it can vendor
the exact per-platform hashes the way esbuild's own npm installer
(`esbuild.binaryHashes`) and Electron (`checksums.json`) do, refreshed by a
small script at pin-bump time. This is deliberately stronger than the
Phoenix precedent it supersedes in this doc: Phoenix's esbuild path trusts
the npm registry's signature and integrity metadata (and vendoring npm's
signing keys carries a rotation obligation; Corepack broke worldwide when
npm rotated keys in 2025), and Phoenix's tailwind/GitHub path verifies
nothing beyond TLS. Vendored hashes survive even a registry compromise, need
no signature code, and cover mirrors by construction. Runtime
signature/provenance verification is deliberately skipped; instead, the
pin-bump script cross-checks upstream attestations once, in CI (npm
provenance for `@esbuild/*`; dart-sass publishes GitHub artifact
attestations verifiable via `gh attestation verify`, and no plain checksum
files).

- **esbuild** downloads from the npm registry's per-platform package
  tarballs (the URL shape esbuild's own docs endorse for manual downloads),
  verified against the vendored hash.
- **dart-sass** downloads the GitHub release archive, verified against the
  vendored hash (computed and attestation-checked at pin-bump). Recorded
  alternative: the npm `sass-embedded-<platform>` packages also contain the
  dart-sass executable, which would give both tools one npm code path;
  rejected for now as a less obvious source, revisit if the GitHub path
  proves awkward.
- **A user-overridden tool version has no vendored hash.** Then citry
  requires either a user-supplied hash (a compiler option / env var) or an
  explicit `CITRY_TOOLS_ALLOW_UNVERIFIED=1`. It never silently downgrades
  to an unverified download.

**Mirrors and proxies**: `CITRY_ESBUILD_MIRROR` / `CITRY_SASS_MIRROR` accept
a base URL with `$version` / `$target` placeholders (the Phoenix-tailwind /
Electron pattern, the top enterprise ask across surveyed tools); vendored-
hash verification applies to mirrored bytes too, so an internal mirror
cannot weaken the trust model. `HTTPS_PROXY`/`HTTP_PROXY` and the OS trust
store are honored.

**Tool cache layout**: `<citry cache root>/tools/<tool>-<version>-<target>/`
(the citry cache root is shared with the compile cache, section 8.2, and
overridable via `CITRY_TOOLS_DIR` for the tools half alone). Version-and-
target-scoped directory names are the industry norm and avoid Phoenix
esbuild's unversioned-binary "outdated version" warning dance. Downloads go
to a temp file in the destination directory, are fsynced, `chmod 0o755`-ed,
and atomically renamed into place; an existing binary is never overwritten
in place (macOS does not recompute code-signing information for overwritten
binaries, a gotcha Phoenix's source documents), and "destination already
exists" counts as success, which makes concurrent multi-worker cold-start
downloads a benign race.

**Platform wheels as an alternative channel** (the tailwindcss-ruby /
sass-embedded gem model, ruff-style binaries in `.data/scripts/`): viable,
proven in Ruby, and it composes with the ladder (optional
`citry-esbuild-bin` wheels could become a rung above PATH later). Rejected
as the first move: it commits citry to a repackaging treadmill (esbuild and
dart-sass together shipped ~40 releases in the last year) across a platform
matrix, and the PyPI graveyard of exactly this idea (a squatted `esbuild`
package that disables TLS verification, a dead `dart-sass` package,
lagging `sass-embedded` wheels) shows how it decays without a standing
maintainer commitment.

Version pinning: each built-in compiler pins a known-good tool version and
warns (not errors) when a binary resolved from steps 1 to 4 differs; the
resolved version is part of `cache_tag()`, so a tool upgrade invalidates the
compile cache correctly instead of serving stale output.

### 7.5 Non-goals, and why

- **Type checking.** The compile path strips types (esbuild) and never runs
  `tsc`. Type checking belongs to the editor and CI, not to a render-path
  step; this is the industry norm (Vite ships no type checking) and it keeps
  the compile step fast and dependency-light. A `tsc`-based check can later
  ride the same tool-resolution machinery as a CLI command or extension if
  wanted; nothing here blocks it.
- **Minification.** The compiler translates, it does not optimize. Compiled
  output stays readable; minification is the job of a future minifier
  extension (proposed here as the natural first consumer of the
  `on_js_postprocess` / `on_css_postprocess` family from
  [`extensions_roadmap.md`](extensions_roadmap.md) section 4), applied
  uniformly to compiled and hand-written assets alike. Bundled-in
  minification would also make dev output undebuggable without introducing
  a dev/prod mode concept citry does not have.
- **Secondary `Dependencies` entries.** Compilation covers the three primary
  bodies only. `Dependencies` entries (extra files, globs, URLs) are served
  verbatim as today; they carry no language declaration, and their existing
  contract (URLs pass through, paths inline or serve) has no compile slot. If
  demand appears, suffix-matched compilation of local-file entries can be
  added later inside `_resolve_entry` without touching this design.
- **Sourcemaps** are not emitted in v1 (the `CompileResult` shape leaves room
  for them). Compiled component assets are small and per component, so the
  mapping burden is low; revisit alongside the minifier extension.

---

## 8. Caching and invalidation

### 8.1 A content-addressed compile cache, persistent by default

The compile step gets its own cache, speaking the existing `CitryCache`
protocol (string-valued JSON, `dependencies.md` section 10) but held in a
**dedicated settings field with its own default**:

```python
compile_cache: CitryCache | str | Path | None = None
```

`None` (the default) means a disk cache in the platform's per-user cache
directory, in a per-project subtree (section 8.2), so **stopping and
restarting a dev server recompiles only what changed**, with zero
configuration. A `Path` means a disk cache at that location; an instance or
import string means that backend (pass an `InMemoryCache()` to opt out of
persistence). If the default location is not writable (read-only containers),
the compiler degrades to an in-memory cache with a warning rather than
failing.

Why a separate field instead of persisting the main `cache=`: the layers cache
different work. The main cache holds final dependency payloads after source
loading and compilation have already happened; persisting it cannot avoid the
compiler invocation needed to identify that payload. The compile cache sits
around the expensive compiler call and validates source plus dependencies, so
it is the persistence lever that makes restart-without-rebuild possible.

The key and value shapes:

```
key:   citry:compile:<kind>:<md5 of the JSON array
           [kind, lang, cache_tag, resolve_dir, source]>
value: {"code": "...", "deps": [{"path": "...", "hash": "..."}, ...]}
```

The key hashes a JSON array, not a string concatenation, so field boundaries
cannot collide. Every field earns its place:

- **`resolve_dir` is load-bearing, not hygiene.** Compiled output is a
  function of the source *and* where its relative imports resolve from: two
  components in different directories with byte-identical
  `import {x} from "./util"` sources correctly produce different bundles.
  Without the resolve dir in the key they would share an entry and serve
  each other's code; with it, the cache is per-location (a moved file
  recompiles once), which is correct and cheap.
- `cache_tag` folds in the compiler implementation, tool version, and
  options (section 5.2), so upgrades and option changes miss cleanly.

Lookup at load time: compute the key (everything in it is known before
compiling); on a hit, rehash every recorded dependency file; if all match,
use the cached code, else recompile and overwrite. A recorded dependency
that cannot be read counts as a mismatch. This is make-style dependency
checking, and it is what makes a persistent shared backend safe: edited
sources, edited imports, moved components, upgraded tools, and changed
options all produce a different key or a failed revalidation.

One honest limit, inherent to make-style checking: it validates the files
the *recorded* compile read, so a change in import *resolution* that the
recorded files cannot witness (adding a new `_theme.scss` earlier in the
load-path order that now shadows the one the cached compile used) is not
caught until the entry or a recorded file changes. The workaround is
mechanical (touch the entry, or run `citry compile` after adding files); the
sass over-approximation in 7.2 also shrinks this window for the style side.
Exact negative-dependency tracking (recording where resolution *looked*) is
deliberately not promised.

To keep the store tidy across many edits (each edit writes a new
content-addressed entry), the loader remembers the class's previous compile
key and best-effort-deletes it when a reset leads to a recompile, so a long
dev session does not accumulate dead entries on disk.

Concurrency needs no locking: workers cold-starting on the same component
run the compiler with the same pinned cwd and inputs and write byte-identical
values under the same key, a benign race (contrast django-compressor's
per-block locking, which guarded per-request work).

### 8.2 The default disk cache: location, keying, hygiene, pruning

Settled against a survey of how dev tools place and key their caches (pip,
uv, black, ruff, mypy, pytest, Poetry, pre-commit, Bazel, Gradle, Go,
ccache, Vite; primary sources read).

**Location.** The citry cache root is `platformdirs.user_cache_dir("citry",
appauthor=False)`: `~/.cache/citry` on Linux (XDG honored),
`~/Library/Caches/citry` on macOS (an explicit `XDG_CACHE_HOME` wins there
too on platformdirs 4.6+, which satisfies the uv-style XDG camp), and
`%LOCALAPPDATA%\citry\Cache` on Windows. `platformdirs` becomes a real
dependency (pip vendors it, black depends on it; it encodes the Homebrew
and XDG-on-macOS subtleties a hand-rolled version gets wrong). The compile
store lives at `<root>/compile/v1/<project-key>/`; the `v1` segment is an
on-disk format version (uv's model), bumped only when the entry shape
changes, never per citry release (black namespaces by tool version and pays
with a cold cache every release; compiler-version invalidation is already
`cache_tag()`'s job inside the key).

**Project keying.** Keying by raw cwd is mypy's documented mistake (stray
caches appearing in unrelated directories). Instead: walk up from the
working directory to the nearest directory containing `pyproject.toml` or
`.git` (file or directory, for worktrees); fall back to cwd itself. The key
is Poetry's recipe: the root's directory name (sanitized, capped) plus the
first 8 chars of a urlsafe-base64 sha256 of `normcase(realpath(root))`, so
symlinked and case-varied paths collapse to one key and a listing of the
cache stays human-readable. A `project.json` inside the tree records the
plain root path and a last-used stamp (the pattern VS Code uses for its
hashed workspace storage), which is what makes pruning and debugging
possible. Two rejected anchors: the Citry app module's path (citry has no
mandatory entry point, and `sys.argv[0]` is the server binary under
gunicorn) and `settings.dirs[0]` (defaults to empty). One structural point
lowers the stakes: entry keys already embed `resolve_dir` (8.1), so the
project key can never affect correctness, only how entries group for
sharing and pruning; a bind-mounted project at a new path starts a cold
tree, the same accepted trade as Bazel and Poetry.

**Store shape.** One JSON file per entry, named by a hex digest of the full
cache key, written via a temp file in the same directory then `os.replace`
(the black/pip/Go consensus; last-writer-wins is exactly right for
content-addressed entries), with a short retry loop around
replace-and-delete on Windows (uv's documented antivirus mitigation). Not
SQLite: mypy's SQLite store exists for a many-thousands-of-files problem
citry does not have, it serializes writers, and it misbehaves on NFS home
directories. Falsifier: if real projects show thousands of entries or
profiling shows directory-scan cost, move to SQLite behind the same
`CitryCache` protocol.

**Hygiene markers**, written once at cache-root creation with create-new
semantics (never overwriting a user's edit): a `CACHEDIR.TAG` (the
cache-directory tagging spec that tar, restic, and borg honor for backup
exclusion; cargo, ruff, uv, mypy, pytest all write it), a `.gitignore`
containing `*` (the ruff/pytest convention; uv proves it belongs in global
caches too, guarding users who point the cache inside a repo), and a
two-line README saying the directory is regenerable and safe to delete.

**Pruning**, shipped in v1 because the survey's lesson is that it never
gets retrofitted (Bazel's path-keyed output bases have leaked for years
behind an open feature request): on top of the previous-key delete in 8.1,
a best-effort daily sweep (Go-style: last-used stamps touched at most once
an hour, a sweep at most once a day) deletes entries unused for 30 days and
sibling project trees unused for 30 days or whose recorded root path no
longer exists (pre-commit gc's liveness test). Plus explicit commands,
uv's verb pair: `citry cache clean` (delete everything) and
`citry cache prune` (stale entries and orphaned project trees).

**Overrides**, following the `<TOOL>_CACHE_DIR` ecosystem convention:
the `compile_cache` setting beats the `CITRY_CACHE_DIR` environment
variable (which relocates the whole citry cache root, tools included),
which beats the platform default; that precedence order is ruff's
documented one.

### 8.3 Hot reload

Nothing new is invented; the compiler joins the existing chain:

- The entry file is already registered in the file index by `_load_pair`;
  reported dependencies (section 5.2) are registered alongside it.
- `Citry.invalidate_file(edited path)` finds the classes and calls the
  resets; the next access reloads, recompiles (compile-cache miss or
  revalidation failure), re-fires the hooks, re-caches.
- Inline-source edits are Python-file edits: the host reloader restarts, as
  today (`hot_reload.md` section 7).

One boundary needs widening: invalidation fires only for paths the watcher
reports, and `watch()` roots default to `settings.dirs` (`hot_reload.md`
5.2, with "watch py-file-relative asset dirs?" already an open question
there, section 11). Compiler-reported dependencies are the file class most
likely to live outside those roots (a colocated layout with empty `dirs`, a
shared partial tree, `node_modules`). **Decision: `watch()` grows its
default roots to cover the directories of engine file-index entries**, which
picks up both py-file-relative assets and compiler-reported dependencies
(resolving hot_reload.md's open question in the affirmative; phase 6 records
it there). The mechanics (roots snapshot at watch start, refreshed when new
files register in the index, since the index grows lazily) belong to
hot_reload.md and are settled during phase 4. Until a path is watched, a
changed dependency recompiles on the next process start or `citry compile`
run instead of live.

`citry watch` plus the lazy path already produce the live-reload behavior
the prototype planned to bolt on; compiled assets need nothing extra.

### 8.4 Multi-worker and cold start

Compiled output, unlike JS/CSS variables scripts, is **regenerable from
source**, so no shared cache is *required* for correctness; every worker can
rebuild independently (the lazy-repopulation property, `dependencies.md`
4.3). With the persistent compile-cache default (8.1), the operational
guidance is:

- **Dev**: defaults do the right thing. Restarting the server recompiles
  nothing whose sources are unchanged (same content, same key, disk hit);
  an edit compiles once. The main cache stays per-process, so class scripts
  are always rebuilt fresh from the (correctly cached or recompiled)
  sources.
- **Production, single host**: defaults already share the compile cache
  across workers and restarts (same per-user directory). Configuring the
  *main* cache (`DiskCache`/Redis) remains the separate, fragments-driven
  decision it is today (`dependencies.md` 8.3).
- **Production, fleet**: run `citry compile` at image-build time so the
  baked image ships a hot compile cache (point `compile_cache` at a path
  inside the image if the per-user default is not baked in); or use a shared
  Redis backend. Worst case without either is redundant recompilation per
  host, never wrong output.

---

## 9. Dev and production stories

### 9.1 Dev

No new processes, no watchers to configure. The first render after an edit
recompiles the affected component (one subprocess, tens of milliseconds),
courtesy of the invalidation chain (subject to the watch-roots boundary in
8.3). Compiler errors surface at load time with the component name and the
underlying tool's message, the same place a missing template file errors
today.

### 9.2 `citry compile` (warmup and validation)

A core CLI command (one `ExtensionCommand` subclass plus a `build_cli` tuple
entry), following the established engine resolution (a leading
`--app module:attr`, autodiscovery before work):

```
citry [--app module:attr] compile
```

For every discovered component it loads the three assets (compiling whatever
needs it), **parses the loaded template** (so a dialect compiler emitting
broken citry-HTML fails here, not on first render), and warms the
class-script cache (`cache_component_js`/`cache_component_css` with
`force=True`). It reports per-component errors and exits non-zero if any
step failed, which doubles as CI validation ("all my components compile and
parse"). When the configured compile cache is per-process (an in-memory
backend), it warns that the warmup will not outlive the command.

Scope, stated so operators do not over-read "warm": what persists is the
compile-cache entries and class-script entries in a persistent backend;
per-class in-memory caches die with the command's process by design, so a
production worker still parses templates and resolves classes on first use,
it just never shells out to a compiler for unchanged sources.

It is not an export: it writes nothing outside the configured cache backend,
and serving is unaffected by whether it ran.

### 9.3 Production serving

Unchanged. Compiled JS/CSS flows into the same class-script cache, the same
inline tags or `cache/<class_id>.<content_hash>.js` endpoints, the same
content-hashed `asset/` URLs for served files, and the same fragment manifest.
A CDN in front of the citry routes caches the fingerprinted URLs as today.

---

## 10. Cross-binding and cross-language audit

Per Mechanism 4, stated explicitly: **this feature touches no Rust contract
surface.** No grammar rule, no AST struct, no compiler-output format, no
`LangImpl` method, no PyO3 registration, no `_rust.pyi` change. Template
dialects compile to citry-HTML *before* `parse_template` is called; the Rust
parser sees ordinary V3 input. The work is Python-package-only, the same
scoping precedent as the CLI
([`extensions_commands.md`](extensions_commands.md) section 2).

What would pull Rust in later, none of it required now: a tree-sitter or
language-server integration mapping dialect positions (issue #23 territory),
or moving a text transform into `citry_html_transform` for reuse by other
bindings. The *shape* of this design (the `*_lang` trio, the dual-keyed
registry, content-addressed compile caching) is language-neutral and is what
a JS/PHP/Go binding would mirror; only the implementation is Python.

---

## 11. Layout

- `citry/compilers/__init__.py`: `Compiler`, `CompileContext`,
  `CompileResult`, the registry build and lookup, the resolution algorithm's
  error type.
- `citry/compilers/markdown.py`, `citry/compilers/esbuild.py`,
  `citry/compilers/sass.py`: the built-ins (each lazily importing its
  tool/library).
- `citry/compilers/tools.py`: the tool downloader (resolution ladder steps
  5, vendored hashes, mirrors, the tool cache).
- `citry/assets.py`: the compile step in the three loaders, retained JS/CSS
  file paths, the `*_lang` inheritance rule (next to the pair rule it
  extends).
- `citry/settings.py`: the `compilers` and `compile_cache` fields.
- `citry/commands/compile.py`, `citry/commands/tools.py`,
  `citry/commands/cache.py`: the `citry compile`, `citry tools install`,
  and `citry cache clean|prune` commands.
- Tests: `packages/py/citry/tests/test_compilers.py` (contract, resolution,
  registry), `test_compilers_markdown.py`, `test_compilers_tools.py`
  (esbuild/sass, binary-gated), `test_compile_cache.py`,
  `test_tool_download.py` (against a local HTTP fixture).

---

## 12. Decisions at a glance

| Question | Decision | Why |
|---|---|---|
| When does js/css compilation run? | Lazily, once per class, inside the asset loaders, upstream of `on_js_loaded` / `on_css_loaded` | Matches every existing citry lifecycle; batching exists only for bundling, which is excluded |
| When do template dialects run? | Once at template load, producing citry-HTML for the parser; never per render | `template_lang` describes source, not data; cache-friendly; hooks and parser see one language |
| Static export (`collectcomponent`)? | No | An export exists to hand assets to further processing; citry serves its own. Confirms `source_languages.md` 3.3 |
| Eager option? | `citry compile`: warms the compile and class-script caches, parses every template, non-zero exit on failure (CI validation) | Deploy-time cost paying and validation, no second build world |
| Per-component meta files? | No | Their purposes (bulk-build records, CSS code splitting) belong to the rejected export/bundle model; content-addressed keys replace them |
| Cross-component bundling / splitting? | No (falsifier recorded) | Needs the whole-graph build world; duplication accepted for now |
| Compiler interface | Class with `kind` / `languages` / `suffixes` / `cache_tag()` / `compile(ctx) -> str \| CompileResult`, per-file | Svelte-preprocessor shape; batch signature existed for bundling |
| Base dialects (`html`/`js`/`css`)? | Skip the registry via per-kind base suffix sets ({html, htm} / {js, mjs, cjs} / {css}) | No identity compiler to shadow; plain-dialect transforms are the `on_*_loaded` hooks' job (divergence from `source_languages.md` 6.4, flagged in 4.2) |
| Dependency reporting | `CompileResult.dependencies` (absolute paths), registered in the file index and hashed into cache validation | Imports and partials must invalidate like entry files (Eleventy `addDependencies`) |
| Registration API | `Citry(compilers=(...,))` settings field accepting instances, classes, or import strings (like `extensions=`); precedence user > extension-provided (future) > built-ins | Zero ceremony; no privileged built-in path; no speculative hooks |
| Delegate to Vite instead? | No as the core mechanism; a `citry-vite` ecosystem extension stays possible | Wrong unit (file entries vs inline per-component bodies), inverts the serving story, reintroduces the batch/manifest world, hard Node requirement (3.4) |
| Hook ordering | Compiler first; all hooks see base dialects only | One invariant for every hook author; pre-compile transforms compose at the registry |
| `$component` under compilation | Reserved name: call-only in component JS; the esbuild compiler errors when a bundle defines it | Keeps the single cache-time expansion sound now that its input can be a bundle |
| `on_*_postprocess` hooks | Not built by this feature | The compiler consumes none of them; build when the minifier / inline-CSS consumer lands |
| Compile caching | `citry:compile:<kind>:<md5 of [kind, lang, cache_tag, resolve_dir, source] as JSON>`, make-style dep revalidation, in a dedicated `compile_cache` backend defaulting to a per-user disk cache | Resolve-dir in the key keeps identical sources in different components apart; content addressing makes persistence safe, so restarts rebuild only what changed |
| Persist the main `cache=` for dev instead? | No; the compile cache is the persistence lever | The main cache receives final scripts only after compilation; it cannot skip the expensive compiler call needed to identify their content-addressed version (8.1) |
| Watch roots | `watch()` default roots grow to cover file-index entry directories | Compiler-reported dependencies and py-file-relative assets invalidate live; resolves hot_reload.md section 11 affirmatively |
| esbuild output format | IIFE; importing other components' modules is out of scope | Matches current script emission; shared code goes in a `.ts`/`.js` file each component imports (inlined per component); ESM would force `type="module"` tag plumbing |
| Tool acquisition | Explicit path, env var, `node_modules/.bin`, `PATH`, then auto-download of the pinned version (phase 5) | Zero-config with escape hatches; the ladder keeps bring-your-own-binary first |
| Auto-download consent | On by default, no prompt; `CITRY_TOOLS_AUTO_DOWNLOAD=0` off-switch, explicit `citry tools install`, one loud log line per download | No surveyed tool prompts; supply-chain-sensitive setups need determinism and an off-switch, not a prompt (7.4) |
| Auto-download verification | Per-platform hashes vendored in citry next to the version pin; overridden versions need a user hash or explicit allow-unverified; mirrors covered by the same hashes | Stronger and simpler than Phoenix (whose GitHub path verifies nothing and whose npm path carries a key-rotation obligation); the esbuild/Electron in-package pinning model |
| Compile-cache location | `platformdirs.user_cache_dir("citry")/compile/v1/<project-key>/`; project key from a `pyproject.toml`/`.git` walk-up, Poetry's name+path-hash recipe | Raw-cwd keying is mypy's documented mistake; content-addressed entries make the key non-load-bearing (8.2) |
| Cache hygiene and pruning | `CACHEDIR.TAG` + self-`.gitignore` + README at the root; 30-day age sweep + `citry cache clean|prune`, shipped in v1 | The convention set of ruff/uv/pytest/cargo; Bazel's lesson is that pruning never gets retrofitted |
| Type checking / minification | Out of the compile path | Editor/CI job and postprocess-extension job respectively; keeps compile fast and semantic |
| Built-ins (as built) | markdown; ts/tsx/jsx (esbuild); scss/sass (dart-sass) | The dialects with proven demand; registry stays open |

---

## 13. Implementation phases

Each phase lands with tests (exact-output compiler tests are authored
observe-then-lock) and finishes with the full repo gate
(`python scripts/check.py`). The delegation-ready breakdown of these phases
into work packages, with per-package reading lists, deliverables, test
lists, and sequencing, lives in
[`asset_compiler_plan.md`](asset_compiler_plan.md).

1. **The contract.** `template_lang` / `js_lang` / `css_lang` attributes with
   the inheritance rule (4.2); retain resolved JS/CSS file paths in
   `assets.py`; language resolution with the base suffix sets; the
   `Compiler` / `CompileContext` / `CompileResult` types; the registry and
   `CitrySettings.compilers` (instances, classes, and import strings); the
   compile step in the three loaders; the
   unclaimed-language error. No real compilers yet; tests use toy compilers
   (e.g. an uppercasing "language") to lock resolution, precedence,
   inheritance (leak / standing default / lang-only override / diamond),
   base-suffix acceptance (`.htm`, `.mjs`, `.cjs`), error, and hook-ordering
   behavior.
2. **Markdown.** The first real compiler, pure Python
   (`citry[compiler-markdown]`): proves the template path end to end,
   including the opaque-token plugin, `html=True` pinning, code-fence
   entity escaping, and dedent. The observe-then-lock test set includes the
   known corruption shapes: quotes/ampersands inside `{{ }}`, `*` pairing
   across adjacent expressions, expressions adjacent to backticks, and the
   raw-HTML-block blank-line rule.
3. **Subprocess compilers.** `EsbuildCompiler` and `SassCompiler`: the tool
   resolution ladder, cwd pinning to `resolve_dir`, stdin for inline bodies,
   the temp-dir outfile/metafile mechanics with entry stripping and path
   absolutization, the sass load-path over-approximation, the
   `$component`-definition guard, version pinning and the mismatch
   warning. Tests skip gracefully where the binary is unavailable and run
   fully in a CI job that provisions the tools; one test locks that an
   inline-body compile-cache entry revalidates cleanly on second lookup.
4. **The compile cache and warmup.** The `compile_cache` settings field with
   the per-user disk default (platformdirs, a new dependency: remember the
   mirrored-pins gotcha for the root `pyproject.toml`; project-key walk-up;
   hygiene markers; read-only degradation); the `citry:compile:*` layer with
   dependency revalidation (missing file = mismatch) and previous-key
   cleanup on recompile; the age-based sweep and the `citry cache
   clean|prune` commands; file-index registration of reported dependencies;
   the `watch()` root extension to file-index entry directories (mechanics
   settled in hot_reload.md's context); the `citry compile` command (load +
   template parse + class-script warm, non-zero exit, non-persistent-cache
   warning); hot-reload integration tests (edit an imported partial, see the
   recompile; restart the process, see no recompile).
5. **Tool auto-download.** Resolution-ladder step 5 per 7.4: the downloader
   with vendored per-platform hashes and the pin-bump refresh script
   (attestation cross-check in CI), the tool cache layout with atomic
   installs, mirror and proxy support, the disable knob and
   allow-unverified policy, and `citry tools install`. Tests run against a
   local HTTP fixture serving known-hash artifacts; a CI job exercises one
   real download per tool.
6. **Docs and sibling updates.** User docs for `*_lang`, the built-in
   compilers, tool setup, the `$component` `.d.ts` for TS authors, and the
   production guidance (DiskCache / warmup). Sibling docs:
   `source_languages.md` sections 3.2, 3.3, 6.2, 6.4, 7, and 8 (lifecycle
   settled, base dialects out of the registry, ships-list);
   `extensions_roadmap.md` section 4 (the asset compiler is not a
   postprocess-hook consumer; add the minifier as one) and section 5 (point
   here); `asset_loading.md` sections 3.2 and 6 (the lang inheritance rule
   beside the pair rule; the compile step upstream of the loading hooks);
   `hot_reload.md` sections 5 and 11 (compiler-reported dependencies join
   the file index; the watch-roots question, now answered: roots grow to
   cover file-index entry directories). Re-frame issue #10 to point
   here and fold in the prototype findings from section 2.1 so their record
   outlives the local snapshot.

Later, separately triggered: `Extension.compilers` (5.3), further dialects
(pug, less), sourcemaps, precise sass dependency reporting via the embedded
protocol (7.2), optional platform wheels as an extra acquisition channel
(7.4), and compilation of `Dependencies` entries (7.5), each when a
concrete consumer appears.

---

## 14. Open questions

- **A `mode` setting (`"dev"` / `"prod"`).** The compile cache's persistent
  default (8.1) serves the immediate dev need without one, but candidate
  mode-driven divergences keep accumulating: minification and sourcemap
  defaults (7.5), watcher auto-start, debug output. Today citry deliberately
  has no dev/prod concept; whether to introduce one is a cross-cutting
  decision with its own design pass, not something to back into via
  compiler options. Recorded here so the next candidate consumer finds the
  list.
