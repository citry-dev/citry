# Implementation plan: the asset compiler (work packages)

**Status (2026-07-04): plan drafted; no work package started.** This is the
delegation companion to [`asset_compiler.md`](asset_compiler.md): the six
implementation phases of that design's section 13, broken into twelve
self-contained work packages (WP1 to WP12) sized for one coding agent each.
The design doc stays the source of truth for *what* and *why*; this doc says
*who reads what, builds what, and proves it how*. When a decision here seems
to conflict with the design doc, the design doc wins; flag the conflict
instead of improvising.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. How to delegate a work package

Every agent brief must carry the rules with it (a delegated agent sees only
the brief). Copy this template and fill in the WP number:

```
You are implementing work package WP<N> of the citry asset compiler.
Repo: /Users/mac/repos/citry. Work in the fable-mode skill; effort: max.

Read first, in this order:
1. /CLAUDE.md (operating rules, code conventions, house style).
2. docs/design/asset_compiler.md, the sections listed under WP<N> in
   docs/design/asset_compiler_plan.md.
3. docs/design/asset_compiler_plan.md, your WP<N> entry: scope,
   deliverables, tests, boundaries.
4. The code files listed in the WP entry, before writing anything.

Rules that bind this work:
- Scope is exactly WP<N>. Respect its "Boundaries" list; if you believe
  the scope is wrong, stop and report instead of expanding it.
- New or changed behavior ships with tests. Tests that assert exact
  compiled output are authored observe-then-lock: run the real thing,
  read the output, then lock it into the assertion.
- Compiled and generated output must be deterministic (no set iteration
  into output, no timestamps).
- Finish with the full repo gate: python scripts/check.py --reporter
  agent, and fix everything it reports, including failures in files you
  changed indirectly.
- Report back: what you built, the test evidence, and any deviation from
  the plan with your reasoning.
```

Additional dispatch rules for the coordinator:

- **One WP per agent, one reviewable change set per WP.** Do not batch WPs.
- **Parallel WPs need worktree isolation** when they touch overlapping files
  (the wave table below marks safe parallelism; WP2/WP7 both edit
  `assets.py`, so they are sequenced, not parallel).
- **Land order follows the waves.** A WP whose dependency has not merged
  builds on a stale contract.
- When a WP lands, update its status line in section 3, and when a whole
  phase completes, update the status header of
  [`asset_compiler.md`](asset_compiler.md).

---

## 2. Sequencing

| Wave | Packages | Notes |
|---|---|---|
| 1 | WP1 | Foundation types and registry; everything depends on it |
| 2 | WP2 | Loader integration; serial after WP1 (same contract surface) |
| 3 | WP3, WP4, WP7 | Parallel: markdown (own module), tool ladder (own module), cache layer (touches `assets.py`, so WP7 goes first if WP3/WP4 agents also need loader context, but file-wise only WP7 edits `assets.py`) |
| 4 | WP5, WP6, WP8, WP9 | Parallel: esbuild and sass (own modules, after WP4), disk cache default (after WP7), compile command (after WP2 and WP7) |
| 5 | WP10, WP11 | Watch roots (reload machinery), tool auto-download (after WP4; its tests get nicer after WP5/WP6 exist) |
| 6 | WP12 | Docs sweep, sibling-doc updates, issue #10 reframe; strictly last |

Dependency edges: WP1 <- WP2 <- {WP3, WP7}; WP1 <- WP4 <- {WP5, WP6, WP11};
WP7 <- {WP8, WP9}; WP2 <- {WP9, WP10}; everything <- WP12.

---

## 3. Work packages

### WP1: compiler contract and registry (phase 1a)

**Status: not started.**

**Goal:** the `Compiler` contract, the per-instance registry, and the
`compilers` settings field, with no compilers and no loader changes yet.

**Read first:** `asset_compiler.md` sections 4.2 (base suffix sets,
provenance rule), 5.1 to 5.3, 11; code: `citry/settings.py`,
`citry/citry.py` (how `extensions=` and `cache=` specs are normalized,
including import strings), `citry/extension.py:535-549` (built-ins
prepended pattern).

**Build:**

- `citry/compilers/__init__.py`, a new package:
  - `Compiler` base class per design 5.1: ClassVars `kind`
    (`Literal["template", "js", "css"]`), `languages: tuple[str, ...]`,
    `suffixes: tuple[str, ...]`; `cache_tag(self) -> str` (default:
    module-qualified class name; built-ins override later);
    `compile(self, ctx) -> str | CompileResult` (abstract).
  - `CompileContext` frozen dataclass: `source: str`, `lang: str`,
    `filepath: Path | None`, `resolve_dir: Path`, `component_class`,
    `citry`.
  - `CompileResult` frozen dataclass: `code: str`,
    `dependencies: tuple[Path, ...] = ()`.
  - The base-dialect suffix sets: template `{html, htm}`, js
    `{js, mjs, cjs}`, css `{css}`, and the base language name per kind.
  - Registry construction from `CitrySettings.compilers`: entries may be
    instances, classes (instantiated with no arguments), or import strings;
    normalize the same way `extensions=` does (reuse the existing
    import-string helper rather than writing a new one). Scan order: user
    entries, then a (reserved, currently empty) extension slot, then
    built-ins.
  - Lookup keyed by provenance (design 4.2 step 3): a name from `*_lang`
    matches `languages`; a suffix-inferred name matches `suffixes`; `kind`
    must match; first hit wins.
  - The unclaimed-language error type. Suggested name
    `NoCompilerError`; check the package's existing exception conventions
    first and align. The message must name the component class, the asset
    kind, the resolved language, and the three fixes (register a compiler,
    install the providing extra, set `*_lang` to the base dialect).
- `citry/settings.py`: the frozen `compilers` field (default `()`), docstring
  per the public-docstring conventions.
- Engine wiring: the registry is built once per `Citry` instance and lives
  on it (no module globals).

**Tests** (`tests/test_compilers.py`): registration by instance, class, and
import string; user entry shadows a built-in claiming the same language;
provenance matching (an explicit lang never matches `suffixes` and vice
versa); kind mismatch does not match; error message content; determinism of
scan order.

**Boundaries:** no changes to `assets.py`, no real compilers, no caching, no
CLI. `Extension.compilers` is explicitly out of scope (the design defers it).

---

### WP2: language resolution and loader integration (phase 1b)

**Status: not started.**

**Goal:** `*_lang` declaration with the inheritance rule, language
resolution, and the compile step wired into the three asset loaders, proven
end to end with toy compilers.

**Read first:** `asset_compiler.md` sections 3.2 (template flow), 4.1, 4.2
(all of it, especially the inheritance rule and the behavior-change note),
6 (hook ordering invariant); `asset_loading.md` sections 3 and 6; code:
`citry/assets.py` (whole file; the pair rule at `assets.py:89-118`, the
discarded path at `assets.py:268`, `load_template` at `assets.py:208-234`),
`citry/component.py:295-324` (the six ClassVars).

**Build:**

- `template_lang` / `js_lang` / `css_lang` ClassVars on `Component`
  (default `None`), docstrings written for the API reference.
- The inheritance rule as a helper next to `_find_pair_declaration`,
  implementing design 4.2 exactly: walk the MRO most-derived first; the
  first class whose own `__dict__` declares the lang wins, except that a
  class declaring both the lang and a member of the same pair, sitting
  above the pair-owning class, is skipped (its lang died with its replaced
  source); a lang-only class is a standing default; an explicit `None` is
  a declared "infer" and stops the walk.
- Retain the resolved JS/CSS file path after load (today discarded at
  `assets.py:268`), following the existing per-class cache-attr pattern.
- The resolution algorithm (design 4.2 steps 1 to 3) and the compile step in
  all three loaders, upstream of `on_template_loaded` / `on_js_loaded` /
  `on_css_loaded`. `resolve_dir` is the file's directory, or the module
  directory for inline bodies.
- Register `CompileResult.dependencies` in the engine file index
  (`Citry._register_component_file`).

**Tests** (extend `tests/test_compilers.py` or a sibling module), using toy
compilers (e.g. an uppercasing "language"):

- Inheritance matrix: parent-declares-pair-and-lang / child-redeclares-pair
  (no leak, infers); lang-only base class (standing default applies);
  child redeclares only the lang (reinterprets inherited source); diamond
  (pair from one base, standing-default lang from a sibling base); explicit
  `None` stops the walk.
- Base suffixes: `.htm`, `.mjs`, `.cjs` files load unchanged, no registry
  lookup.
- Explicit lang overrides suffix in both directions (`css_file="card.txt"`
  + `css_lang="toy"` compiles; `js_file="card.toy"` + `js_lang="js"` skips).
- Unknown suffix raises with the full error content.
- Hook ordering: `on_js_loaded` observes compiled output; template dialect
  output reaches the parser (toy template compiler emitting citry-HTML).
- Dependencies land in the file index; `reset_files()` then next access
  recompiles (toy compiler with a call counter).

**Boundaries:** no cache layer (recompile on every post-reset load is
correct here), no real compilers, no CLI, no `reload.py` changes.

---

### WP3: the markdown compiler (phase 2)

**Status: not started.**

**Goal:** the first real compiler, pure Python, proving the template path.

**Read first:** `asset_compiler.md` sections 3.2, 7.3; `/CLAUDE.md` extras
rule and mirrored-pins gotcha; code: `citry/compilers/__init__.py` (WP1),
the loader seam from WP2; `docs/codebase.md` extras naming
(`citry[<category>-<name>]`).

**Build:**

- `citry/compilers/markdown.py`: `MarkdownCompiler` (kind `template`,
  languages `("markdown", "md")`, suffixes `("md", "markdown")`) on
  `markdown-it-py`, per design 7.3:
  - `html=True` pinned explicitly regardless of preset.
  - An inline rule tokenizing `{{ ... }}` and `{# ... #}` as opaque raw
    tokens before escaping and emphasis run.
  - Code spans and fences escape citry delimiters as numeric entities
    (`&#123;`), on top of markdown-it's own escaping.
  - Inline sources are dedented before compiling.
  - Lazy import of `markdown-it-py` inside the compiler with an actionable
    ImportError naming the extra.
  - `cache_tag()` folds in the markdown-it-py version and the compiler's
    own version.
- Register as a built-in in the registry.
- The `compiler-markdown` extra in `packages/py/citry/pyproject.toml`,
  mirrored into the root `pyproject.toml` dev/ci extras (follow the
  cross-comments in those files).

**Tests** (`tests/test_compilers_markdown.py`, observe-then-lock):

- The corruption shapes from the design: quotes and ampersands inside
  `{{ }}` survive verbatim; `*` in two adjacent expressions does not become
  `<em>`; an expression adjacent to a backtick is not swallowed into a code
  span.
- Fences and inline code: `{{ }}` inside them arrives entity-escaped;
  `<c-*>` inside them arrives escaped.
- `<c-*>` tags outside code pass through as raw HTML; the CommonMark
  blank-line HTML-block behavior is locked as documented behavior.
- Dedent: an indented triple-quoted markdown template does not become a
  code block.
- End to end: a markdown template renders through the real citry parser and
  the escaped entities appear as literal text in the output.

**Boundaries:** no pug, no grammar or parser changes, no other compilers.

---

### WP4: the tool resolution ladder (phase 3a)

**Status: not started.**

**Goal:** shared binary resolution for subprocess compilers, steps 1 to 4
and 6 of the ladder, with a seam for the WP11 downloader.

**Read first:** `asset_compiler.md` section 7.4 (the ladder and the version
pinning paragraph).

**Build:**

- `citry/compilers/tools.py`: `resolve_binary(tool, *, explicit, env_var,
  pinned_version, downloader=None) -> Path` implementing: explicit
  constructor path, env var (`CITRY_ESBUILD_PATH` / `CITRY_SASS_PATH`
  passed by the caller), `./node_modules/.bin/<tool>` from cwd, `PATH`
  (`shutil.which`), then the `downloader` seam (None in this WP), then the
  step-6 error naming the tool, the component context the caller supplies,
  and the fixes (including how to enable download once WP11 exists;
  phrase it so the message is truthful before and after WP11 lands).
- The version check: run `<bin> --version` once per process per resolved
  path, warn (not error) on mismatch with the pinned version; expose the
  resolved version so compilers fold it into `cache_tag()`.

**Tests** (`tests/test_compilers_tools.py`): ladder order with
monkeypatched env/fs/PATH; the warning fires once per process on mismatch;
error content when nothing resolves; downloader seam is invoked in position
when supplied.

**Boundaries:** no downloading (WP11), no compiler classes (WP5/WP6).

---

### WP5: the esbuild compiler (phase 3b)

**Status: not started.**

**Goal:** `ts` / `tsx` / `jsx` compilation via the esbuild CLI, with sound
invocation mechanics and dependency reporting.

**Read first:** `asset_compiler.md` sections 5.2 (determinism, cwd rule),
6 (the `$component` reserved-name decision), 7.1 (all invocation
mechanics); code: `citry/compilers/tools.py` (WP4),
`citry/extensions/dependencies/scripts.py:56-91` (the transform whose input
domain this changes).

**Build:**

- `citry/compilers/esbuild.py`: `EsbuildCompiler` (kind `js`, languages and
  suffixes `("ts", "tsx", "jsx")`), constructor options (`bin`, `target`,
  extra args), pinned tool version constant. Invocation per design 7.1:
  - subprocess cwd pinned to `ctx.resolve_dir`; inline bodies via stdin
    with the right `--loader`; file bodies by entry path.
  - `--bundle --format=iife --platform=browser`, `--outfile` and
    `--metafile` into a per-invocation `tempfile.mkdtemp` (removed in a
    finally block); code read from the outfile.
  - Dependencies from the metafile `inputs`, with the entry (`<stdin>` or
    the entry path) stripped and the rest absolutized against the compile
    cwd.
  - The `$component` definition guard: raise at compile time when the
    bundle *defines* the symbol (function/const/let/var/class declaration),
    with the fix in the message (call-only; use the ambient declaration).
  - `cache_tag()`: compiler version + resolved esbuild version + normalized
    options.
- Register as a built-in.
- CI: provision esbuild in the citry test workflow (follow the workflow
  naming and layout conventions in `docs/codebase.md`).

**Tests** (binary-gated: skip cleanly when esbuild is unavailable, run
fully in CI):

- Inline body with `import { x } from "./util"` resolves against the
  component's module directory; file body resolves against its own
  directory.
- Dependency list: absolute paths, entry stripped, matches the imported
  files.
- Determinism: identical output bytes for the same component when the host
  process cwd differs (the pinned-cwd rule).
- The definition guard fires on `import`ed/defined `$component`; a plain
  `$component(...)` call survives bundling and still matches the
  cache-time transform regex.
- Compile errors from esbuild surface with the component name and the tool
  message.

**Boundaries:** no minify, no sourcemaps, no ESM, no downloading, no
cross-component chunks.

---

### WP6: the sass compiler (phase 3c)

**Status: not started.**

**Goal:** `scss` / `sass` compilation via the dart-sass CLI with the
over-approximated dependency reporting.

**Read first:** `asset_compiler.md` sections 5.2 and 7.2; code:
`citry/compilers/tools.py` (WP4), `citry/assets.py` resolve chain (for the
load-path order).

**Build:**

- `citry/compilers/sass.py`: `SassCompiler` (kind `css`, languages and
  suffixes `("scss", "sass")`); stdin for inline (`--indented` for the
  `sass` dialect), file path otherwise; `--load-path` for the component's
  module directory then each `settings.dirs` entry (that order); no
  reliance on subprocess cwd for resolution (dart-sass deprecates it).
- Dependencies: every `.scss`/`.sass` file under the load paths, sorted,
  absolute (the deliberate over-approximation; the design records why).
- `cache_tag()` with the resolved dart-sass version.
- Register as a built-in; CI provisioning alongside WP5's.

**Tests** (binary-gated): `@use` partial resolution from the module dir and
from `settings.dirs`; the indented `sass` dialect; the dependency list is
sorted, absolute, and includes never-imported partials under the load paths
(locking the over-approximation as contract); tool errors surface with
component context.

**Boundaries:** no less/stylus, no embedded protocol, no sourcemaps.

---

### WP7: the compile cache layer (phase 4a)

**Status: not started.**

**Goal:** content-addressed caching of compile results with make-style
dependency revalidation, wired into the loader compile step.

**Read first:** `asset_compiler.md` section 8.1 (all of it: key shape,
revalidation, the shadowing limit, previous-key cleanup); code:
`citry/cache.py`, the WP2 loader seam, `citry/settings.py`.

**Build:**

- The key and value exactly per design 8.1: key
  `citry:compile:<kind>:<md5 of the JSON array [kind, lang, cache_tag,
  resolve_dir, source]>`; value `{"code": ..., "deps": [{"path": ...,
  "hash": ...}]}`.
- Lookup before compiling; on hit, rehash every recorded dependency
  (missing or unreadable counts as mismatch); on mismatch or miss, compile
  and overwrite.
- Previous-key memory per class and kind; best-effort delete of the
  superseded key when a reset leads to a recompile.
- The `compile_cache` settings field (`CitryCache | str | Path | None`).
  In this WP, `None` resolves to a per-instance `InMemoryCache` as a
  placeholder; WP8 replaces the `None` branch with the disk default.
  `Path` and instance/import-string handling land here.

**Tests** (`tests/test_compile_cache.py`, with toy compilers and
`InMemoryCache`): hit and miss; edited dependency fails revalidation;
changed `cache_tag` misses; identical sources in two different directories
get distinct entries; a deleted dependency file forces recompile; the
superseded key is deleted after reset-recompile; the structured hash does
not collide across field boundaries (differing `(lang, cache_tag)` splits).

**Boundaries:** no disk backend, no location logic, no pruning, no CLI
(all WP8/WP9).

---

### WP8: the default disk cache, hygiene, and pruning (phase 4b)

**Status: not started.**

**Goal:** the zero-config persistent default: platform cache dir, project
keying, hygiene markers, the age sweep, and the `citry cache` commands.

**Read first:** `asset_compiler.md` section 8.2 (all of it); code:
`citry/contrib/caches.py` (`DiskCache`: decide whether to reuse it for the
per-file JSON store or add a small core file store; read it before
deciding), `citry/command.py` and `citry/commands/__init__.py:72-84` (how
commands register), `/CLAUDE.md` mirrored-pins gotcha (platformdirs is a
new dependency: pin in `packages/py/citry/pyproject.toml` and mirror per
the cross-comments; check Dependabot config per `docs/codebase.md`).

**Build:**

- The `None` branch of `compile_cache`: `platformdirs.user_cache_dir("citry",
  appauthor=False)` + `/compile/v1/<project-key>/`; read-only locations
  degrade to in-memory with a warning.
- Project keying per design 8.2: walk up from cwd to the nearest
  `pyproject.toml` or `.git` (file or dir), else cwd; key =
  sanitized root name (capped) + first 8 chars of urlsafe-base64
  sha256 of `normcase(realpath(root))`; a `project.json` in the tree
  records the plain root path and a last-used stamp.
- Store: one JSON file per entry named by a hex digest of the full cache
  key; temp-file-in-same-dir + `os.replace`; a short retry loop around
  replace/delete on Windows.
- Hygiene at the citry cache root, create-new semantics: `CACHEDIR.TAG`
  (exact signature line per the spec), `.gitignore`
  (`# Automatically created by citry.` + `*`), a two-line README.
- Pruning: last-used stamps touched at most hourly; a best-effort sweep at
  most daily (entries unused 30 days; sibling project trees unused 30 days
  or with a vanished recorded root); never raises.
- `citry cache clean` and `citry cache prune` commands (one grouping
  command with two subcommands, following the `ext` grouping pattern),
  registered in `build_cli`.
- `CITRY_CACHE_DIR` env var relocating the citry cache root; precedence
  setting > env > default.

**Tests:** default path shape with platformdirs monkeypatched per OS;
keying (symlinked project roots collapse; walk-up finds the marker from a
subdirectory; cwd fallback); markers created once and never overwritten;
sweep behavior against faked stamps (entries, orphaned trees, vanished
roots); both commands; read-only degradation warns and still compiles;
env-var precedence.

**Boundaries:** the cache layer logic itself is WP7 and must not change;
no tool-cache work (`tools/` subtree is WP11's).

---

### WP9: the `citry compile` command (phase 4c)

**Status: not started.**

**Goal:** the warmup and CI-validation command.

**Read first:** `asset_compiler.md` section 9.2; code: `citry/command.py`,
`citry/commands/list.py` (engine access and autodiscovery trigger),
`citry/component_render.py:777-804` (how a template is compiled on demand;
pick the supported entry point for forcing the parse),
`citry/extensions/dependencies/scripts.py:75-106` (`cache_component_js/css`
with `force=True`).

**Build:** `citry/commands/compile.py` registered in `build_cli`: for every
discovered component, load the three assets (which compiles), force the
template parse, warm the class-script cache with `force=True`; collect and
report per-component failures; exit non-zero if any step failed; warn when
the compile cache backend is per-process.

**Tests:** exit 0 on a healthy fixture set; a dialect compiler emitting
broken citry-HTML fails at the parse step with the component named; class
script keys exist in the cache afterwards; the non-persistent-cache warning
fires with `InMemoryCache` and not with a disk-backed cache.

**Boundaries:** no new compile logic; the command only drives existing
seams.

---

### WP10: watch roots for compiler dependencies (phase 4d)

**Status: not started.**

**Goal:** `watch()` grows its default roots to cover the directories of
engine file-index entries, so edits to compiler-reported dependencies
outside `settings.dirs` invalidate live.

**Read first:** `asset_compiler.md` section 8.3; `hot_reload.md` sections
4, 5, and 11 (the open question this resolves); code: `citry/reload.py`
(all watcher backends, `_resolve_roots`, `watch()`),
`citry/citry.py:463-494` (the file index).

**Build:**

- Root derivation includes the directories of current file-index entries;
  a refresh mechanism for roots discovered after watch start (the index
  grows lazily). Design the mechanics within `reload.py`'s existing
  structure (e.g. re-derive on the watcher's own cadence, or restart the
  backend when the root set grows); keep all three backends working.
- Update `hot_reload.md` sections 5 and 11 in the same change (the
  code-adjacent doc edit belongs with the code; WP12 only cross-checks it).

**Tests:** integration: a component whose toy/real compiler reports a
dependency outside `settings.dirs`; editing that file triggers
`invalidate_file` and a recompile on next access; a root added after watch
start is picked up; all three watcher backends still pass their existing
suites.

**Boundaries:** no changes to the invalidation chain itself; no compiler
changes.

---

### WP11: tool auto-download and `citry tools install` (phase 5)

**Status: not started.**

**Goal:** ladder step 5: verified download of the pinned esbuild and
dart-sass binaries, plus the explicit install command and the pin-bump
hash-refresh script.

**Read first:** `asset_compiler.md` section 7.4 (the whole trust model:
consent, verification, mirrors, tool cache layout, the
overridden-version policy); code: `citry/compilers/tools.py` (WP4's
downloader seam), `citry/commands/__init__.py`; `scripts/check.py` (for
where repo scripts live and their conventions).

**Build:**

- The downloader in `citry/compilers/tools.py` (or a sibling module):
  - Sources: esbuild from the npm registry per-platform package tarball;
    dart-sass from the GitHub release archive. Platform/arch target
    detection with a clear unsupported-platform error.
  - Verification: per-platform hashes vendored in citry next to the pinned
    versions; a hash mismatch aborts with nothing installed. Overridden
    versions require a user-supplied hash or
    `CITRY_TOOLS_ALLOW_UNVERIFIED=1`; never a silent downgrade.
  - Install: `<citry cache root>/tools/<tool>-<version>-<target>/`;
    download to a temp file in the destination dir, fsync, `chmod 0o755`,
    atomic rename; existing destination counts as success; never overwrite
    a binary in place.
  - Controls: `CITRY_TOOLS_AUTO_DOWNLOAD=0` (plus a settings equivalent)
    disables step 5; `CITRY_ESBUILD_MIRROR` / `CITRY_SASS_MIRROR` with
    `$version` / `$target` placeholders; `CITRY_TOOLS_DIR` relocates the
    tools subtree; `HTTPS_PROXY`/`HTTP_PROXY` honored.
  - The loud log line per download: tool, version, resolved URL,
    destination, verified hash.
- `citry tools install` command (same code path as the lazy download),
  registered in `build_cli`.
- `scripts/refresh_tool_hashes.py`: fetches and rewrites the vendored hash
  tables for a new pin (esbuild from registry metadata, dart-sass by
  hashing downloaded archives), with a note in its header that CI
  cross-checks upstream attestations at pin-bump time.
- Step-6 error text updated to mention the disable knob when it caused the
  skip.

**Tests** (`tests/test_tool_download.py`): against a local HTTP fixture
serving known artifacts: hash match installs atomically; mismatch aborts
cleanly; disable knob stops step 5 and the error says so; mirror
substitution builds the right URL and verification still applies;
overridden version without a hash refuses unless allow-unverified is set;
concurrent install (pre-existing destination) succeeds. One CI job
exercises a single real download per tool (gate it so PR runs stay
hermetic; follow the workflow conventions).

**Boundaries:** no signature/sigstore code at runtime; no wheels; no new
tools beyond esbuild and dart-sass.

---

### WP12: docs and sibling updates (phase 6)

**Status: not started.**

**Goal:** user documentation and the cross-doc consistency sweep, last.

**Read first:** `asset_compiler.md` section 13 phase 6 (the authoritative
update list) and section 2.1 (the findings to fold into issue #10);
`/CLAUDE.md` house style (user docs lead with the symptom; no internals in
user docs; changelog rules); `docs_site/` structure and
`docs_site/content/community/development.md` (docstring/docs conventions).

**Build:**

- User docs: declaring `*_lang`; the built-in compilers and their tool
  setup (consent model, off-switch, mirrors, airgap); dev workflow (hot
  reload of imported files) and production guidance (persistent cache,
  `citry compile` in image builds); the `$component` ambient-types
  snippet for TS authors; the shared-code pattern (a `.ts` file both
  components import).
- Sibling design docs, per the design doc's phase-6 list:
  `source_languages.md` 3.2/3.3/6.2/6.4/7/8; `extensions_roadmap.md`
  sections 4 and 5; `asset_loading.md` 3.2 and 6; verify WP10's
  `hot_reload.md` edits landed and cross-reference them.
- Issue #10: reframe to point at `asset_compiler.md` and fold in the
  section 2.1 prototype findings so the record outlives the local
  snapshot.
- `CHANGELOG.md`: one user-facing entry ("you can now write component
  JS/CSS/templates in TS/SCSS/markdown ..."), full `x.y.z` versioning.
- Update `asset_compiler.md`'s status header to reflect what is built.

**Boundaries:** no code changes beyond doc-adjacent strings; if a doc edit
reveals a code discrepancy, report it rather than patching code in this WP.

---

## 4. Cross-cutting acceptance

Every WP, before it is declared done:

- `python scripts/check.py --reporter agent` passes clean (the full gate,
  not a scoped run).
- New behavior has tests; exact-output assertions were observed, then
  locked.
- No em dashes in any new doc, comment, or docstring; sentence-case
  headings; comments explain intent, not mechanics.
- Public docstrings written for the API reference (one-line summary +
  Google-style sections), since they render into the docs site.
- Changelog entries only where WP12 says so (the feature ships one entry;
  internal WPs add none).
