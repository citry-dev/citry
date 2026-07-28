# Recon: the Vue IDE tooling lineage (Vetur, Volar, JetBrains)

Research input for the citry IDE integration design
([`../ide_integration.md`](../ide_integration.md)), written 2026-07-07. This
report traces how Vue's editor tooling evolved through three generations
(Vetur, Volar v1, Volar v2/v3 plus the extracted volar.js framework), how the
JetBrains IDEs handled the same problem with a separate implementation, and
what the whole arc teaches citry. Vue is the primary inspiration here because
it is the longest, best-documented case of exactly citry's problem: a
component template DSL that must be highlighted, completed, navigated, and
type checked against code written in the host language.

All web claims were checked against live sources on 2026-07-07 (see Sources).
Version and release dates were verified against the GitHub API where the
fetched pages were ambiguous. A small number of background facts are marked
as training knowledge where noted.

---

## 1. Why this lineage maps onto citry

The structural parallel is close:

- A Vue single-file component (SFC, a `.vue` file) holds a template, a
  script, and styles in one file. A citry component holds a template, JS, and
  CSS as class attributes on a Python class, either inline strings or file
  paths ([`packages/py/citry/citry/component.py:295-324`](../../../packages/py/citry/citry/component.py)).
- Vue templates reference script-side state and component props. Citry
  templates reference `template_data` variables and typed inputs declared as
  inner `Kwargs` / `Slots` dataclasses
  ([`packages/py/citry/citry/component.py:332`](../../../packages/py/citry/citry/component.py)
  and `:344`).
- Vue components compose by tag name in templates. Citry components compose
  by `<c-*>` tag name ([`README.md:146`](../../../README.md)).
- Vue's tooling ultimately succeeded by reusing the framework's own compiler
  inside the editor tooling. Citry already has a single-source-of-truth
  parser and compiler in Rust
  ([`crates/citry_template_parser/`](../../../crates/citry_template_parser/)),
  exposed to Python through PyO3
  ([`crates/citry_template_parser/src/ast.rs:20`](../../../crates/citry_template_parser/src/ast.rs)
  marks the first `#[pyclass]`), with the compiler generating host-language
  source per target language
  ([`crates/citry_template_parser/src/compiler.rs:110`](../../../crates/citry_template_parser/src/compiler.rs)).

The one structural difference that matters is flagged throughout and
collected in section 8.4: a `.vue` file is its own file type, while an inline
citry template lives inside a Python string in a `.py` file that Python
tooling already owns.

## 2. Vetur, the first generation

### What Vetur was

Vetur was the official VS Code extension for Vue through the Vue 2 era
(first published 2016, author Pine Wu; background knowledge, not re-verified
this pass). Architecturally it was a single language server, the "Vue
Language Server" (VLS), that split each `.vue` file into block regions and
delegated each region to an embedded language service: an HTML service for
the template, the TypeScript service for the script, CSS services for
styles.

Three Vetur mechanisms are worth remembering because each one reappears
later in more mature form:

1. **Declarative component metadata.** Library authors shipped `tags.json`
   and `attributes.json` files describing their components (tag names,
   attributes, docs) and pointed to them from a `vetur` key in
   `package.json`; Vetur read the user's `package.json` to discover which
   libraries were installed and loaded their data for tag and attribute
   completion. Vue Router, Nuxt, Element UI, Vuetify, Bootstrap Vue, and
   Quasar all shipped these. This is the direct ancestor of JetBrains
   web-types (section 6).
2. **Template expression support as a virtual TypeScript file.** Behind the
   experimental flag `vetur.experimental.templateInterpolationService`,
   Vetur compiled the template into a virtual TypeScript file, kept a
   sourcemap between template expressions and the generated code, ran
   language feature requests on the virtual file, and mapped results back.
   That gave diagnostics, hover, jump to definition, and find references in
   template expressions, including prop existence and prop type validation.
   Completion inside expressions was weaker because the generic compiler
   could not process syntactically incomplete files. Vetur even had a
   command, "Show corresponding virtual file and sourcemap".
3. **A CLI diagnostics face** (VTI, the "Vetur Terminal Interface"), the
   ancestor of `vue-tsc`.

So the core Volar idea, virtual code plus sourcemaps, already existed inside
Vetur. It was just an experimental bolt-on rather than the architecture.

### Why Vetur hit limits

- **Memory doubling.** VS Code's built-in TypeScript extension kept one copy
  of the project's TypeScript ASTs; the VLS kept another for its own
  analysis. Johnson Chu's Volar 2.0 writeup gives a measured example:
  1254 MB combined for one large project, with extreme `.d.ts`-heavy
  projects exhausting machine memory outright.
- **Configuration fragility.** Without a `tsconfig.json`/`jsconfig.json`
  Vetur fell back to degraded settings (no path aliases, no decorators);
  without a `package.json` it could not detect the Vue version or load
  library component data. Monorepos needed late-added workarounds. The
  documented FAQ answer to slowness was "add a tsconfig and restart VLS".
- **Trust erosion.** Template type checking lived behind an experimental
  flag for years, and one more TypeScript AST copy was needed (a separate
  "TypeScript Vue Plugin") just so `.ts` files could resolve `.vue`
  imports, tripling parts of the memory cost. Users learned to treat
  template diagnostics as unreliable and turned them off.
- Vue 3, `<script setup>`, and a TypeScript-first user base raised the bar
  past what the architecture could deliver.

## 3. Volar generation one: virtual code as the whole architecture

Volar started as Johnson Chu's personal project while Vetur was still the
official recommendation, and was adopted as the official Vue extension on
the strength of its architecture and performance. Volar 1.0 ("Nika")
shipped in 2022 after about two years of development.

### The core mechanism

Volar's design promotes Vetur's experiment into the entire architecture.
For every `.vue` file the language tooling generates "virtual code":

- The template is compiled into one or more virtual TypeScript files in
  which every template expression appears in a type-checkable position.
  Identifier references are rewritten against a typed context object (the
  generated code is full of `__VLS_`-prefixed helpers, e.g. a template
  reference to `b` becomes `__VLS_ctx.b`), and component usages are
  generated as typed constructs checked against the component's props type.
- Styles and other blocks become virtual CSS/JSON/etc. documents.
- A mapping table links every generated range back to its original source
  range.

Then standard language services (TypeScript's, the CSS service, an HTML
service) run against the virtual documents, and every result, whether a
diagnostic, hover, completion, definition, or rename, is mapped back through
the table to the original file. One mechanism yields all features, which is
the property Vetur never had.

### Takeover mode: the memory workaround that failed

Volar v1 still had Vetur's double-AST problem: VS Code's built-in
TypeScript server and Volar's server each held the project. "Takeover mode"
asked users to disable the built-in TypeScript extension per workspace so
Volar's server handled `.ts`/`.js` files too. It worked (1254 MB down to
738 MB in Johnson Chu's measurements) but failed as a product:

- discoverability was poor and setup was manual per workspace,
- feature parity with VS Code's built-in TypeScript integration always
  lagged,
- TypeScript language server plugins from other tools did not work inside
  Volar's server.

Takeover mode was deprecated with v2.0 and its documentation removed. The
lesson is general: asking users to replace their host-language tooling with
your framework's fork of it is a losing position, no matter how good the
fork is.

### vue-tsc: the CLI twin, and its fragility

`vue-tsc` wraps TypeScript's own `tsc` binary so the same virtual-code layer
runs in CI: command-line type checking and `.d.ts` emit for `.vue` files.
It replaced Vetur's VTI and is now the standard "type check my Vue app"
command (the Vue docs recommend it directly).

Its weakness is the implementation strategy: it patches TypeScript's
internals at load time (intercepting file reads of `tsc`'s own source and
rewriting it with string searches). Maintainers flagged in 2022 that
TypeScript's module refactor could break the approach entirely, and it did
keep breaking: TypeScript 5.7 shipped and `vue-tsc` failed with
`Search string not found` until patched. Anything built on private
internals of the host toolchain is a permanent compatibility treadmill.

## 4. Volar generations two and three: hybrid mode and the TypeScript plugin

### v2.0: move TypeScript work into the TypeScript server

v2.0 (released 2024-03-01) inverted takeover mode. Instead of Volar's
server absorbing TypeScript, TypeScript's own server absorbed Vue:
`@vue/typescript-plugin`, a TypeScript server plugin, teaches the editor's
existing tsserver to understand `.vue` files (using the same
virtual-code core, `@vue/language-core`). The Vue language server keeps
only what tsserver cannot do: HTML/CSS features, Vue-specific completions,
formatting. This split was named "hybrid mode". Measured memory dropped to
639 MB for the same reference project, with zero user configuration.
Building it took seven months (August 2023 to March 2024) because nobody
had pushed the TypeScript plugin API that deep before.

### The rollout was rough, and instructive

- Older VS Code builds bundled a Node version that broke tsserver when the
  Vue plugin loaded.
- Worst, the plugin API had no fault isolation: "whenever any TS plugin
  crashes in a .vue file, it will cause @vue/typescript-plugin to be
  invalidated and make intellisense completely wrong" (PR #4119).
- Nineteen days after 2.0.0, v2.0.7 (PR #4119, merged 2024-03-20)
  reintroduced the complete v1-style language server as the default, with
  hybrid mode opt-in. Stability returned around v2.0.26, after which hybrid
  mode became the default again.
- v3.0 (released 2025-07-01) made hybrid mode always-on, reworked how the
  Vue language server and tsserver communicate, pinned exact volar.js
  versions so all editors behave identically, and shipped an explicit
  upgrade guide for non-VS Code editors, an acknowledgment that the
  tsserver-plugin architecture is hardest to adopt outside VS Code (Neovim
  and other LSP clients must wire the plugin into their own TypeScript
  server setup).

### Current state, July 2026

- Latest release v3.3.6 (2026-06-30, verified via the GitHub API); the
  marketplace extension is named "Vue (Official)".
- Template checking strictness is user-configurable and has grown
  fine-grained: v3.0 added `strictVModel`, `strictSlotChildren`, and
  `strictCssModules` compiler options; v3.3.0 added
  `checkRequiredFallthroughAttributes`. Strictness-as-a-dial, not a single
  experimental flag, is part of how template diagnostics stayed trusted.
- Vue 2 and `vue-class-component` support was scheduled for removal in
  v3.1, closing out the legacy surface.

## 5. How each editor feature is actually delivered

A per-feature breakdown of the current Vue stack, since citry will need an
answer for each row:

| Feature | Mechanism | Requires a server? |
|---|---|---|
| Base syntax highlighting | Declarative TextMate grammar; the Vue grammar embeds 20+ languages by block (HTML/Pug templates, JS/TS/JSX/TSX scripts, CSS/SCSS/Less/Stylus styles, JSON/YAML/TOML/GraphQL custom blocks) | No |
| Semantic highlighting | Semantic tokens from the language service for what a grammar cannot know (e.g. marking a tag as a component vs a plain element), mapped onto standard TextMate scopes so existing themes color them | Yes |
| Tag/attribute completion | HTML-service-style data plus component knowledge from the TypeScript side: which components are in scope, auto-import completion for components not yet imported, prop names with types, directives | Yes |
| Expression completion | Ordinary TypeScript completion inside the virtual file (so `v-for` variables and context properties complete with correct types) | Yes |
| Go to definition, template to script | Source-map lookup through the virtual code | Yes |
| Go to definition, `.ts` to `.vue` | The TypeScript plugin, because the editor's tsserver must resolve `.vue` imports | Yes (plugin) |
| Prop validation in templates | Component usages in the virtual TypeScript are typed against the component's props type; missing required props, wrong types, and (with strict options) unknown props surface as ordinary TypeScript diagnostics mapped back to template ranges | Yes |
| CI type checking | `vue-tsc`, same core as the editor | CLI |

Two things stand out. First, the zero-server tier (TextMate grammar) is
what every user sees in the first five minutes, and it ships as pure data.
Second, every server-tier feature is the same virtual-code mechanism worn
five different ways; there is no per-feature machinery.

### Type helpers beyond the editor

The type-level component contract escaped the editor and became shared
infrastructure. `vue-component-type-helpers` is a tiny, runtime-free types
package (`ComponentProps<T>`, `ComponentEmit<T>`, slot and exposed-member
extractors). It is a production dependency of `@vue/test-utils`
(`vue-component-type-helpers: ^3.0.0`) and of Storybook's vue3 renderer
(`^3.2.9`), both verified from their `package.json` files on 2026-07-07. A
sibling package, `vue-component-meta`, feeds docs generators. The pattern:
once the component contract is machine-readable, tests, docs, and stories
consume it too, not just the editor.

## 6. The JetBrains side: what a parallel reimplementation costs

WebStorm and the other IntelliJ-platform IDEs did not use Vetur or Volar
historically. Their Vue support is a from-scratch implementation on the
IntelliJ platform, today a multi-module Gradle plugin in the
`JetBrains/intellij-plugins` repository under `vuejs/` (modules like
`vuejs-backend`, `vuejs-common`, `vuejs-debugger`, verified via the GitHub
API), with its own parsing, resolution, and its own template type
evaluation.

Two consequences of that choice are the interesting part:

**They invented a metadata format to stay afloat: web-types.** Because the
IDE could not execute a library's TypeScript to learn its components,
JetBrains created web-types (2019 onward), a JSON standard describing a
component library's components, props, events, slots, and directives.
Libraries ship a `web-types.json` and point to it from `package.json`;
the IDE consumes it for completion and docs. Bootstrap-vue, Quasar,
Vuetify, Nuxt, and Ionic shipped web-types. Version 2.0 of the format is
explicitly framework-agnostic ("any kind of web framework, Web Components
library, or CSS icons pack"), fully supported since IDE version 2021.3.1,
and powerful enough to encode framework syntax patterns. This is Vetur's
`tags.json` idea, industrialized and vendor-backed, and it is still alive
in 2026.

**They eventually gave up on the parallel type checker.** TypeScript 5.0's
changes made keeping their own Vue template type evaluation current too
expensive. WebStorm 2023.2 integrated the Vue Language Server (Volar) for
projects on TypeScript 5.0+, keeping their implementation for older TS;
after a stabilization period the Vue Language Server became the default in
2024.1. In April 2024 JetBrains donated $10,000 to the Volar team, writing
that Volar "has become almost indispensable" and that their product's
capabilities were "closely tied to the well-being of projects like Volar."

The implication for anyone designing a template language: even a company
with a paid IDE, a dedicated team, and a purpose-built metadata format
concluded that reimplementing a framework's type-level template semantics
is not sustainable, and converged on (a) the framework's own language
server for semantics plus (b) declarative metadata for the cheap 80%. A
framework should therefore publish both and expect vendors to adopt rather
than reimplement.

## 7. volar.js and the ecosystem in 2026

In early 2023 (the `volarjs/volar.js` repository was created 2023-01-08;
the "Volar: a new beginning" announcement followed on the Vue blog) the
framework-agnostic layer was extracted from the Vue extension into
volar.js, "The Embedded Language Tooling Framework". The division of labor:
a framework provides a language plugin that parses its file format into
virtual code with mappings; volar.js provides the language server plumbing,
the composition of service plugins (TypeScript, CSS, HTML, and custom
ones), the editor glue (VS Code, with Monaco support planned from the
start), and the TypeScript-plugin machinery. The stated design goal is
supporting "any file format that involves embedded languages - not just
Vue, but also Astro, Svelte, or even Angular". Johnson Chu was funded
full-time by StackBlitz at extraction time; the core team includes Erika
(Astro) and Remco Haszing (MDX).

Who builds on it, as of 2026-07:

- **Vue**: `vuejs/language-tools`, the reference user. Since v3.0 the Vue
  language server pins exact volar.js versions for cross-editor
  consistency. volar.js itself is on the 2.4.x line (latest tag v2.4.28).
- **Astro**: the Astro language server 2.0 was a complete rewrite on
  volar.js. Erika (who built it) reports the rewrite "removed a huge
  amount of code, closed a lot of issues, and significantly reduced
  maintenance cost"; Astro granted the Volar team $10,000. Astro also ships
  the same trio as Vue: language server, TypeScript plugin, and an
  `astro check` CLI.
- **MDX**: `mdx-js/mdx-analyzer` is structured as `@mdx-js/language-service`
  (Volar integration), `@mdx-js/language-server`, `@mdx-js/typescript-plugin`,
  and the `vscode-mdx` extension. MDX matters as prior art because the
  container document is markdown with embedded JSX, i.e. the embedded
  language lives inside a host document that is not the framework's own
  invention.
- **Glint v2 (Ember)**: rebuilt "atop the Volar.js language tooling
  framework", explicitly following "along with Vue/Volar in the decision to
  shift type-checking and related functionality away from the Language
  Server and instead move it into a TypeScript Server Plugin", with an
  `ember-tsc` CLI. A second framework independently validated the v2
  architecture.
- **Counterexample, Svelte**: Svelte's language tools do not use volar.js;
  they are built on `svelte2tsx`, their own template-to-TSX converter
  (credited in the sveltejs/language-tools README). Independent convergence
  on the same idea: every serious template DSL ends up compiling templates
  into the host type checker's language.

Fragility note: this entire multi-framework stack rests on a very small
core team (single-digit maintainers), funded by sponsorships from
StackBlitz, JetBrains, Astro, and individuals. Depending on volar.js means
depending on that.

## 8. Lessons for citry

### 8.1 What to copy

1. **One parser, many frontends.** The single consistent thread from Vetur
   to Volar to Glint is that tooling quality tracks how directly it reuses
   the framework's own compiler. Citry already holds the strongest card in
   this game: the Rust parser and compiler
   ([`crates/citry_template_parser/src/compiler.rs:110`](../../../crates/citry_template_parser/src/compiler.rs))
   is the single source of truth, produces spans, and is already exposed to
   host languages. The IDE layer must be another thin frontend over it,
   never a second parser. (A future language server also naturally slots in
   as another consumer of the same crate, like the Python bindings in
   [`crates/citry_core_py/src/lib.rs`](../../../crates/citry_core_py/src/lib.rs).)
2. **Virtual code with source maps as the language server core.** Volar v1's
   architecture (compile the template to host-language code, keep a range
   mapping, run existing services, map results back) is the proven shape,
   and citry's compiler already generates Python source from templates. The
   design requirement to adopt early: the compiler output needs a slot for
   source mappings (generated expression range back to template offset).
   The compiler output format is a contract consumed by the Python runtime
   and possibly cache-keyed (per `/CLAUDE.md`, "The compiler output
   format"), so retrofitting a mapping channel later is a breaking change;
   reserving the slot is cheap now.
3. **Two-tier highlighting, declarative tier first.** Ship grammars as pure
   data before any server exists: a TextMate grammar for `.py` files that
   injects citry-template, JS, and CSS highlighting into the
   `template` / `js` / `css` string attributes, mirroring the logic the
   Pygments lexer already encodes
   ([`packages/py/pygments_citry/pygments_citry/lexers.py:49`](../../../packages/py/pygments_citry/pygments_citry/lexers.py)
   and [`citry_html.py:139`](../../../packages/py/pygments_citry/pygments_citry/citry_html.py)).
   Same region rules, multiple render targets: Pygments for docs, TextMate
   for editors. Semantic tokens come later, from the server, layered on
   top, exactly as Vue does it.
4. **Publish component metadata for IDEs we do not target.** web-types v2
   is framework-agnostic and consumed by JetBrains IDEs today. A
   `citry`-side generator that walks registered components and emits
   web-types (tag name from the class, attributes from the `Kwargs`
   dataclass fields with docs, slots from `Slots`) buys PyCharm/IntelliJ
   completion for `<c-*>` tags with zero JetBrains-side code. Vetur's
   `tags.json` and web-types both prove that libraries shipping declarative
   metadata is a workable, low-tech distribution channel, and PyCharm is
   where citry's users actually are.
5. **A CLI checker that is the language server's twin.** `vue-tsc`,
   `astro check`, and `ember-tsc` all expose the same core as a CI-friendly
   binary, and for Vue the CLI (VTI) existed before the good editor story.
   A `citry check` that parses all templates and validates structure (parse
   errors, unknown component tags, unknown or missing kwargs against the
   `Kwargs` dataclass) sits directly on the existing Rust parser, needs no
   editor integration at all, and is the honest MVP: Vetur demonstrated
   that metadata-driven completion plus reliable structural diagnostics
   deliver most of the perceived value long before deep type inference.
6. **Make the component contract programmatically extractable.**
   `vue-component-type-helpers` being a production dependency of
   vue-test-utils and Storybook shows the trajectory: the same contract the
   editor checks (for citry, `Kwargs` / `Slots` on the component class,
   [`component.py:332`](../../../packages/py/citry/citry/component.py))
   should be reachable by test helpers, docs generators, and the web-types
   generator from lesson 4 through one public API, not scraped
   independently by each tool.

### 8.2 What to avoid

1. **Never replace or fork the host language's tooling** (the takeover-mode
   lesson). Any design where users disable or subordinate Pylance/Pyright
   so a citry server can own `.py` files loses: feature parity with the
   host tool is an unwinnable race, and the failure mode costs users their
   whole editor experience, not just citry features. Scope the citry
   server to citry regions and formats; let Python tools own Python.
2. **Never patch private internals of the host checker** (the vue-tsc
   lesson). `vue-tsc` rewrites `tsc`'s source at load time by string
   search and has broken on TypeScript minor releases. The citry analog
   would be monkeypatching Pyright or importing mypy private modules.
   Where integration with a Python type checker is wanted, use public
   extension points (mypy's plugin API) or generate real files the checker
   reads natively.
3. **Do not ship template diagnostics as a permanently experimental flag**
   (the Vetur lesson). Vetur's interpolation service spent years behind
   `vetur.experimental.*`, taught users to distrust and disable it, and
   that reputation transferred to the extension as a whole. Either a check
   runs and is trustworthy, or it does not run. Configurable strictness
   (Volar's `strictVModel` and friends) is the mature version of the same
   need.
4. **Do not plan around per-IDE reimplementations** (the WebStorm lesson).
   JetBrains, with a paid product and a dedicated team, abandoned keeping
   their own Vue template type evaluation current and adopted the
   framework's server. Citry, maintained by one person, should only ever
   build protocol-level assets (an LSP server, web-types, TextMate
   grammar, Pygments lexer) that IDE vendors and communities can adopt.
5. **Budget honestly for architectural migrations in tooling.** Volar's
   move to hybrid mode took seven months of build time, shipped unstable,
   had its default flipped twice within one minor series, and needed a
   major version (v3.0) to become always-on. Where the checking runs (own
   server vs host-tool plugin vs generated files) is the decision to get
   right the first time.

### 8.3 What only makes sense for TypeScript-centric ecosystems

1. **The TypeScript server plugin architecture (hybrid mode).** The entire
   Volar v2/v3 arc, `@vue/typescript-plugin`, and Glint v2's copy of it
   exist because tsserver has a first-class plugin API and every JS-stack
   editor already runs tsserver. Python has no equivalent: Pyright has no
   plugin architecture, and mypy plugins extend type analysis inside a
   batch checker, not a live editor server's file-type support. So citry's
   server should take the Volar v1 shape (a self-contained server that
   embeds its own analysis and delegates to embedded services), not the
   v2 shape. Helpfully, the v1 shape is also the part volar.js fully
   automates.
2. **Deep template expression type inference.** Typed `v-for` items, slot
   prop inference, and discriminated-union prop completion all lean on
   TypeScript's generics and literal-type inference being drivable from
   generated code. Python's checkers cannot be driven this way from
   outside, and expression checking would additionally hinge on citry's
   own expression semantics
   (evaluated via [`crates/python_safe_eval/`](../../../crates/python_safe_eval/)).
   The realistic citry ceiling, in order: structural checks from the Rust
   side (component existence, kwarg names and arity, required kwargs),
   then simple type checks read off `Kwargs` annotations, and only then,
   maybe, generated `.py` stubs that the user's own checker analyzes. Full
   inference inside `{{ ... }}` is a research project, not a roadmap item.
3. **The memory economics that drove takeover and hybrid mode.** Those
   designs answer one question: how not to hold two copies of a huge
   TypeScript project graph in RAM. A citry language server hosts a Rust
   parser over template sources; it does not need to mirror the user's
   whole Python project. That failure mode only appears if the citry
   server ever embeds a full Python analyzer, which is one more reason not
   to (see 8.2.1). Do not import solutions to problems citry does not
   have.

### 8.4 The citry-specific wrinkle the Vue lineage does not answer

Vue never had to support templates inside host-language string literals:
`.vue` is its own file type, owned end to end by Vue tooling. Citry's
primary authoring mode is `template = """..."""` inside a `.py` file
([`component.py:295`](../../../packages/py/citry/citry/component.py)),
a container document owned by Python tooling (Pylance in VS Code). The
closest prior art is not Vue but the adjacent patterns: MDX (embedded
language inside a general-purpose document format, solved with volar.js),
and CSS-in-JS template literals (solved in VS Code with injection grammars
plus a tsserver plugin; pattern known from training, not re-verified this
pass). The candidate approaches to weigh in `ide_integration.md`:

- injection grammars only (highlighting without smarts, cheap, no server),
- a server that treats the `.py` file as the container document and the
  string bodies as embedded virtual documents (the volar.js model supports
  arbitrary containers, but the citry server must then locate the string
  regions itself, via the same detection logic the Pygments lexer uses),
- leaning on `template_file`
  ([`component.py:302`](../../../packages/py/citry/citry/component.py))
  as the full-feature path, where a citry template file is its own file
  type and the whole Vue playbook applies directly.

These are not mutually exclusive; Vue's history argues for shipping the
cheap declarative tier universally and reserving server smarts for
wherever the container problem is simplest.

---

## Sources

Web sources, all accessed 2026-07-07:

- Volar: a new beginning (Vue blog): https://blog.vuejs.org/posts/volar-a-new-beginning
- Volar 1.0 "Nika" released (Vue blog): https://blog.vuejs.org/posts/volar-1.0
- Johnson Chu, Volar 2.0 architecture writeup (gist): https://gist.github.com/johnsoncodehk/62580d04cb86e576e0e8d6bf1cb44e73
- vuejs/language-tools repository: https://github.com/vuejs/language-tools/
- v3.0.0 release notes: https://github.com/vuejs/language-tools/releases/tag/v3.0.0
- PR #4119, reintroducing the complete language server: https://github.com/vuejs/language-tools/pull/4119
- Hybrid mode preview and feedback thread: https://github.com/vuejs/language-tools/discussions/3789
- Takeover mode discussions: https://github.com/vuejs/language-tools/discussions/471 and https://github.com/vuejs/language-tools/discussions/3670
- vue-tsc TS-internals fragility: https://github.com/vuejs/language-tools/issues/2095 and https://github.com/vuejs/language-tools/issues/5018
- Vue docs, using Vue with TypeScript (vue-tsc, extension status): https://vuejs.org/guide/typescript/overview
- Vue (Official) extension, VS Code marketplace: https://marketplace.visualstudio.com/items?itemName=Vue.volar
- DeepWiki pages on vuejs/language-tools (architecture, VS Code extension, grammars): https://deepwiki.com/vuejs/language-tools
- Vetur FAQ: https://vuejs.github.io/vetur/guide/FAQ.html
- Vetur template interpolation guide: https://vuejs.github.io/vetur/guide/interpolation.html
- Vetur component data guide: https://vuejs.github.io/vetur/guide/component-data.html
- volar.js homepage: https://volarjs.dev/
- Astro + Volar announcement: https://astro.build/blog/astro-and-volar/
- Erika, "Things I've worked on at Astro in 2023": https://erika.florist/articles/thingsiveworkedonatastro2023/
- mdx-js/mdx-analyzer README: https://github.com/mdx-js/mdx-analyzer
- typed-ember/glint (GLINT_V2.md, README): https://github.com/typed-ember/glint
- JetBrains web-types repository and format: https://github.com/JetBrains/web-types
- Web-types announcement (WebStorm blog, 2021): https://blog.jetbrains.com/webstorm/2021/01/web-types/
- WebStorm 2023.2 EAP #2, Volar support: https://blog.jetbrains.com/webstorm/2023/05/webstorm-2023-2-eap2/
- Giving back to the ecosystem: JetBrains supports Volar (April 2024): https://blog.jetbrains.com/webstorm/2024/04/giving-back-to-the-ecosystem-jetbrains-supports-volar/
- JetBrains YouTrack WEB-61367 (Vue Language Server default): https://youtrack.jetbrains.com/issue/WEB-61367
- WebStorm Vue.js documentation: https://www.jetbrains.com/help/webstorm/vue-js.html
- JetBrains/intellij-plugins (vuejs modules): https://github.com/JetBrains/intellij-plugins
- sveltejs/language-tools README (svelte2tsx credit): https://github.com/sveltejs/language-tools
- VS Code syntax and semantic highlighting guides: https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide and https://code.visualstudio.com/api/language-extensions/semantic-highlight-guide

Verified via the GitHub API on 2026-07-07: vuejs/language-tools release
dates (v2.0.0 2024-03-01, v3.0.0 2025-07-01, v3.3.6 2026-06-30), volar.js
repository creation date (2023-01-08) and latest tag (v2.4.28),
JetBrains/intellij-plugins `vuejs/` module layout, and the
`vue-component-type-helpers` dependency entries in `vuejs/test-utils` and
`storybookjs/storybook` package manifests (fetched raw from GitHub).

Marked as training knowledge, not re-verified this pass: Vetur's author and
2016 start date, the exact 2022 date of Volar 1.0, and the CSS-in-JS
injection-grammar-plus-tsserver-plugin pattern.

Repository citations use `file:line` inline throughout; key files:
[`packages/py/citry/citry/component.py`](../../../packages/py/citry/citry/component.py),
[`crates/citry_template_parser/src/compiler.rs`](../../../crates/citry_template_parser/src/compiler.rs),
[`crates/citry_template_parser/src/ast.rs`](../../../crates/citry_template_parser/src/ast.rs),
[`packages/py/pygments_citry/pygments_citry/`](../../../packages/py/pygments_citry/pygments_citry/),
[`README.md`](../../../README.md).
