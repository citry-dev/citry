# Recon: how comparable component frameworks solved IDE support

Date: 2026-07-07. Part of the IDE-integration research corpus under
`docs/design/ide_research/` (same register style as
[`../events_research/README.md`](../events_research/README.md)). This report
surveys how frameworks in citry's neighborhood, beyond Vue, built editor
support: what the architecture is, what it costs to maintain, and what citry
should copy or avoid. Special attention goes to templ, whose approach
(generate host-language code from templates, let the host language server do
the thinking) is the closest analogue to generating virtual Python for
Pyright or mypy to check.

Two terms used throughout: a **language server** is a standalone program that
gives an editor completions, diagnostics, hover text, and go-to-definition
over the **LSP** (Language Server Protocol), a JSON-RPC protocol supported by
essentially every modern editor. A **virtual file** (or virtual document) is
generated code that exists only so an existing tool can analyze it, with a
**source map** recording which position in the generated code corresponds to
which position in the original template.

All GitHub statistics below (stars, open issues, release dates, contributor
counts) were read from the GitHub API on 2026-07-07 and are cited as such.
Web sources are listed at the end with access dates.

## The survey

### Svelte language-tools (svelte-language-server + svelte2tsx)

**Architecture.** `svelte-language-server` implements the LSP for `.svelte`
files; for the TypeScript half it calls `svelte2tsx`, which transforms a
whole Svelte component (markup, props, reactive statements) into TSX code
that TypeScript's own language service can analyze, then maps diagnostics,
completions, and hovers back to `.svelte` positions. The same transform
powers `svelte-check`, a command-line batch checker used in CI, so the
editor experience and the CI type gate share one engine.

**Maintenance signals.** Repo created 2020-03; 1,434 stars; 277 open issues;
release cadence is near-weekly (`svelte-check` 4.7.2 on 2026-07-07, 4.7.1 on
2026-06-24, `svelte2tsx` 0.7.57 on 2026-06-23). Contribution is heavily
concentrated: the top two contributors (dummdidumm, jasonlyu123) have 874 and
376 commits, the next has 155. The project began as community work (James
Birtles' extension) that the Svelte org adopted in 2020 with help from the
TypeScript team. Net: roughly two dedicated people have carried it
continuously for six years, and the transform layer (`svelte2tsx`) is where
the ongoing cost lives, because it must track both Svelte syntax changes and
TypeScript releases.

**Take for citry.** Mapping template expressions onto the host language's
own type checker is the only way to get real typing without writing a type
checker. The transform is the expensive part; budget for it as a permanent
line item, not a one-off. And the CLI batch checker (`svelte-check`) falls
out of the transform nearly for free and delivers value in CI before any
editor integration exists.

### Astro language server (built on Volar.js)

**Architecture.** Astro's language server is built on Volar.js, the
framework extracted from the Vue language server for exactly this problem:
it models a source file as a set of virtual code fragments (TSX for the
frontmatter and expressions, CSS and HTML fragments for the rest) with
source maps, and reuses the existing TypeScript and CSS language services
over those fragments. Astro also ships `astro-check` (CLI batch checker) and
a TypeScript plugin from the same machinery.

**Maintenance signals.** The 2023 migration to Volar is the interesting data
point: the Astro team reported that rewriting onto Volar let them delete a
large amount of code, close a backlog of issues, and "significantly reduced
their maintenance cost" (Astro blog, 2023). The standalone
`withastro/language-tools` repo is now archived (verified via GitHub API,
2026-07-07) and the tooling lives inside the main `withastro/astro` monorepo
(`packages/language-tools/` with `language-server`, `ts-plugin`, `vscode`,
`astro-check`). Volar itself reports powering Vue, Astro, and MDX tooling
with 7M+ downloads.

**Take for citry.** Two lessons. First, shared infrastructure beats bespoke:
if an embedded-language framework exists for your ecosystem, standing on it
cuts the cost dramatically. Volar itself is TypeScript-ecosystem centric, so
it does not transfer directly to a Python checker, but its shape (virtual
code + source maps + delegate to existing services) is the same pattern
templ implements by hand. Second, keep the editor tooling in the framework
monorepo so the parser and the tooling cannot drift apart; Astro ended up
folding theirs back in.

### templ (Go): the closest analogue

**Architecture.** templ templates are standalone `.templ` files containing
HTML with Go expressions in braces. `templ generate` compiles each one to a
real Go file (`foo_templ.go`) next to the source, so the ordinary Go
toolchain builds and type-checks templates with no editor involved. On top
of that, `templ lsp` is a **proxy language server**: it starts and manages a
gopls instance (gopls is Go's official language server), keeps freshly
generated Go code for each open template, and forwards LSP traffic in both
directions, rewriting file URIs (`.templ` to `_templ.go` and back) and
remapping every position through a source map. Because the generator knows
exactly which output bytes came from which template bytes, the proxy can
piggyback the full gopls feature set (completions, diagnostics, hover,
go-to-definition) inside templates. HTML-side intelligence (tag and
attribute completion) is not covered by gopls and was added as a separate
layer inside the templ LSP.

**Maintenance signals.** 10,384 stars and only 40 open issues repo-wide;
releases roughly every two months (v0.3.1020 on 2026-05-10, v0.3.1001 on
2026-02-28). The project is overwhelmingly one person: a-h (Adrian Hesketh)
has 708 commits, the next contributor 69. Over the project's life, 68 issues
with "lsp" in the title have been closed and exactly one is open (GitHub
search API, 2026-07-07). So: a single experienced maintainer built and keeps
a production-grade proxy LSP as a feature of the framework repo itself.

**What the issue history says the hard parts were.** The closed-issue titles
cluster into a usable checklist:

- **Error-tolerant parsing.** Editors send broken, mid-keystroke code;
  templ needed partial parsing so the LSP keeps working while the file is
  invalid (#1155, #1178, #1102, #1086: completions failing inside control
  structures).
- **Source-map robustness.** The map is a first-class data structure that
  can fail in its own ways (#1292 and #1294: nil source maps cached, causing
  crashes; #1371: false diagnostics from generation mismatches).
- **Platform quirks.** Windows path and URI encoding broke diagnostics
  repeatedly (#900, #1121, #1274).
- **The proxied server fights back.** gopls warned users about editing a
  generated file and had to be suppressed (#1200, #1221); a missing gopls
  binary needed a clear error (#967).
- **The HTML half is separate work.** gopls only covers the Go side; HTML
  intellisense was its own feature (#498), and script/style formatting is
  handed off to prettier (templ IDE docs).

**Take for citry.** This is the feasibility benchmark for the
virtual-Python idea, assessed in detail in the dedicated section below. The
headline: feasible for a small team, with the cost concentrated in exactly
the four bullets above, and with the generate-to-disk half (CI-grade
checking through the normal toolchain) available long before the live proxy.

### Blade / Laravel

**Architecture.** Blade had no official language server for a decade; the
ecosystem carried it. PhpStorm ships built-in Blade support (an IDE vendor
absorbing the cost), and Laravel Idea, a commercial plugin built by one
developer (Adel Faizrakhmanov, 1.5M+ downloads), provided the deep
intelligence (view and component completion, Eloquent understanding, full
Blade component support); JetBrains made it free for PhpStorm users on
2025-07-30 as part of a Laravel partnership. On the VS Code side, formatting
came from community tools (blade-formatter, prettier-plugin-blade), and in
late 2024 Laravel shipped an official VS Code extension whose distinctive
mechanism is **runtime introspection**: it periodically boots your Laravel
app in the background and asks it what routes, views, config keys, and
components exist, then uses those answers for completion, linking, hovering,
and diagnostics.

**Maintenance signals.** blade-formatter: single maintainer (shufo), 541
stars, still active 2026-07. Laravel Idea: one developer for years, viable
only because it was paid. The official VS Code extension is company-backed
(Laravel became a funded company).

**Take for citry.** Runtime introspection is a legitimately cheap
architecture: instead of statically analyzing the project, ask the framework
at runtime what exists. Citry already maintains a component registry at
import time (components self-register via the metaclass;
`packages/py/citry/citry/component_registry.py:86`,
`packages/py/citry/citry/autodiscovery.py:39`), so a CLI command that dumps
component names, attributes, and slots as JSON would let a thin editor
extension offer registry-aware completions with no language server at all.
The other Blade lesson is negative: relying on a paid IDE vendor or a
commercial plugin only works at Laravel's scale.

### Phoenix LiveView / HEEx

**Architecture.** HEEx templates live both in standalone `.heex` files and
inline in Elixir source via the `~H` sigil, which makes them a close
analogue to citry's inline `template` strings. Editor-side intelligence has
historically been thin and fragmented across three community language
servers (ElixirLS, Lexical, Next LS); in 2024-2025 their authors joined
forces on **Expert**, the now-official Elixir language server, still at
v0.1.x as of 2026-06. The heavy lifting for template correctness sits in the
**compiler** instead: LiveView's `attr` and `slot` macros declare a
component's interface, and the HEEx compiler verifies call sites at compile
time (missing required attributes, unknown attributes), emitting ordinary
compiler warnings that every editor surfaces without any HEEx-specific
tooling. Formatting is likewise a compiler-ecosystem feature
(`Phoenix.LiveView.HTMLFormatter` as a `mix format` plugin).

**Maintenance signals.** Expert: 2,020 stars, 74 open issues, v0.1.5 on
2026-06-10 plus nightly builds; officially backed but early. The
consolidation itself is the signal: the Elixir ecosystem spent years with
three parallel half-complete servers before merging them.

**Take for citry.** Compile-time validation against declared component
interfaces delivers most of the day-to-day safety (typos in component names
and attributes, missing required inputs) with zero editor integration, in
every editor at once. Citry compiles templates when the component class body
runs, so it has the same natural hook. The cautionary half: fragmented,
competing editor tooling burns years; one official channel is worth
protecting from the start.

### Rails / ERB

**Architecture.** Two tracks. Shopify's Ruby LSP (official, company-backed)
added ERB support in 2024: it extracts the Ruby portions for its own
analysis and **delegates** host-language (HTML) requests to the editor's
existing HTML service; that delegation is not part of the LSP specification,
so it requires custom client code, which the Ruby LSP VS Code extension
ships (other editors must reimplement it). Separately, Herb (Marco Roth,
2024-2025) is an HTML-aware ERB parser written in C with Node and WebAssembly
bindings, powering a standalone ERB language server, formatter, and linter;
its stated goal is to be folded into Ruby LSP so the standalone server
eventually does not need to exist.

**Maintenance signals.** Ruby LSP: 2,019 stars, 123 open issues, a staffed
corporate team. Herb: essentially one maintainer (1,105 commits vs 58 for
the next contributor), 1,264 stars, 246 open issues, rapid releases (v0.10.1
on 2026-04-24); the language server shipped about a year after the parser
work began.

**Take for citry.** Herb demonstrates the build order: an error-tolerant,
position-preserving parser is the foundation, and the formatter, linter, and
language server are all consumers of it. Citry's Rust parser already
preserves exact positions (see the repo-facts section below); the missing
property for editor use is tolerance of broken input. Ruby LSP's delegation
pattern (hand the HTML half to the editor's HTML service) is real but costs
per-editor client work, which is worth knowing before promising support
beyond VS Code.

### htmx

**Architecture.** None, officially. Community micro-extensions exist for VS
Code (htmx-tags, HTMX IntelliSense), IntelliJ, and Visual Studio, and they
are all the same thing: a static list of the `hx-*` attributes with
documentation strings, wired into HTML completion.

**Why that is fine for htmx and not for citry.** htmx's entire editor
surface is a closed vocabulary: a few dozen fixed attributes on standard
HTML tags, whose values are URLs, CSS selectors, or plain strings. There are
no user-defined names and no embedded programming language, so a static JSON
completion list captures nearly all the available value, and a weekend
extension per editor is genuinely enough. Citry's surface is open: users
define their own component tags, each with its own attributes and slots, and
template expressions are real Python
(`crates/citry_template_parser/src/compiler.rs:172-195` treats `{{ ... }}`
content as a Python expression to evaluate). Meaningful support therefore
requires project-aware analysis (parser + registry + type checker); a static
list cannot know what `<c-user-card>` accepts.

### Tailwind CSS IntelliSense (the embedded-completion gold standard)

**Architecture.** Three npm packages in a standard LSP layout: the VS Code
client, `@tailwindcss/language-server`, and a reusable
`@tailwindcss/language-service`. The server loads the project's actual
Tailwind configuration (bundling fallback versions of Tailwind so it works
even without a local install) and provides class completions, hover
previews, and linting **inside other languages' files**: HTML, JSX, HEEx,
templ, Blade, and more, via per-language patterns that tell it where class
strings appear.

**Maintenance signals.** 3,446 stars, 54 open issues; roughly monthly
releases (v0.14.29 on 2025-10-22); two primary maintainers (bradlc 655
commits, thecrypticace 369), both Tailwind Labs employees.

**Take for citry.** Two-sided. As a consumer: citry should make its template
regions discoverable to third-party servers like Tailwind's, so citry users
get Tailwind and Emmet completions inside `template` strings for free; that
means either a language identifier for citry templates or an injection
grammar that marks the embedded HTML region (templ's VS Code extension
advertises exactly this Tailwind integration). As a producer: Tailwind's
per-host-language pattern list is evidence that "works in N editors and M
host languages" is N+M small integrations, not one; scope accordingly.

### django-components (citry's direct ancestor)

**Public editor story.** There is no official language server or editor
extension. The org ships `pygments-djc` (Pygments lexers so documentation
and READMEs can highlight component classes with their embedded HTML/JS/CSS)
and `djc-core` (Rust-based parsers and tooling, groundwork rather than a
shipped editor feature); marketplace and repo searches on 2026-07-07 found
no dedicated django-components VS Code extension, so users lean on generic
Django template extensions that know nothing about components.

**Take for citry.** This is the baseline citry inherits, and citry has
already moved one step past it: the `pygments-citry` package (docs
highlighting for component classes) is built, per
[`../pygments_citry.md`](../pygments_citry.md) (status 2026-07-03), with the
package at `packages/py/pygments_citry/`. Everything beyond highlighting is
open field, which is exactly what this report maps.

## Comparison table

Statistics from the GitHub API, 2026-07-07. "Carried by" is the visible
contributor concentration, not an org chart.

| Framework / tool | Architecture in one line | Carried by | Signals (2026-07-07) | Key take for citry |
|---|---|---|---|---|
| Svelte language-tools | Transform component to TSX (`svelte2tsx`), let TypeScript's service analyze it, map results back; same engine powers `svelte-check` CLI | ~2 dedicated maintainers, 6 years | 1.4k stars, 277 open issues, near-weekly releases | The transform is a permanent cost; the CI batch checker is nearly free once it exists |
| Astro language server | Virtual code fragments + source maps on Volar.js, reusing TS/CSS services | Astro core team on shared Volar infra | Standalone repo archived, folded into astro monorepo; Volar reports 7M+ downloads | Shared embedded-language infra slashed their maintenance cost; keep tooling in the framework monorepo |
| templ | Generate real Go files; proxy LSP rewrites URIs/positions between `.templ` and generated Go, piggybacking gopls | 1 maintainer (708 vs 69 commits) | 10.4k stars, 40 open issues total, 68 closed LSP-titled issues vs 1 open | The virtual-file blueprint; hard parts are error-tolerant parsing, source-map robustness, Windows, and the HTML half |
| Blade / Laravel | PhpStorm built-in + one-person commercial plugin (Laravel Idea) + official VS Code extension that boots the app to introspect it | IDE vendor + paid plugin, later company-backed | Laravel Idea free for PhpStorm since 2025-07-30; official VS Code extension late 2024 | Runtime introspection (dump the registry) is the cheapest project-aware completion source |
| Phoenix / HEEx | Compiler-verified component interfaces (`attr`/`slot` macros); official LSP (Expert) only consolidating now | Official consolidation of 3 community servers | Expert 2k stars, v0.1.5 2026-06, still early | Compile-time validation gives most of the safety in every editor at once; fragmentation burns years |
| Rails / ERB | Ruby LSP extracts Ruby, delegates HTML to the editor's service; Herb: error-tolerant HTML-aware ERB parser in C feeding LS/formatter/linter | Shopify team; Herb ~1 maintainer | Ruby LSP 2k stars, 123 open issues; Herb 1.3k stars, LS ~1 year after parser | Error-tolerant position-preserving parser first; everything else consumes it |
| htmx | Nothing official; community static attribute lists | Weekend-scale community efforts | Several tiny extensions per editor | Static lists suffice only for closed vocabularies; citry's is open |
| Tailwind IntelliSense | LS loads the real project config and completes classes inside many host languages via per-language patterns | 2 employees | 3.4k stars, 54 open issues, ~monthly releases | Make citry templates discoverable so third-party servers (Tailwind, Emmet) work inside them for free |
| django-components | Pygments lexers for docs; Rust parser groundwork; no editor extension or LS | 1 maintainer (same as citry's) | No marketplace presence found (2026-07-07) | The inherited baseline; citry's `pygments-citry` is already one step past it |

## templ's virtual-file approach mapped onto citry

The templ analogy is unusually direct, because citry already has the
generator half. What citry has today, with citations:

- **Exact source positions on every token.** The parser's `Token` carries
  `start_index`, `end_index`, and `line_col` taken from the Pest span
  (`crates/citry_template_parser/src/ast.rs:32-34` and `:75-98`), plus
  offset-adjustment helpers (`ast.rs:112-118`). This is the raw material a
  source map needs; templ had to build and then harden the same structure.
- **A compiler that already emits Python source.**
  `compile_template(template, lang) -> Result<String, CompileError>`
  (`crates/citry_template_parser/src/compiler.rs:110`) produces a Python
  source string as its contract, with `{{ ... }}` content passed through as
  Python expressions for `safe_eval` (`compiler.rs:172-195`). The
  multi-language `LangImpl` abstraction
  (`crates/citry_template_parser/src/lang/lang.rs`) means the same move
  later generalizes to virtual TS for the planned JS binding.
- **Both authoring modes.** Templates are inline multiline strings
  (`template = """..."""`, `README.md:31`) or standalone files via
  `template_file` (`packages/py/citry/citry/assets.py:58`, resolved at
  `assets.py:223`).

**The analogous move.** Emit the generated Python for each component
template to a shadow location (a `.citry/` cache directory or a sibling
generated file), together with a template-to-generated source map, then:

1. **Step 1, CI-grade (the `svelte-check` / `templ generate` analogue):**
   run mypy or Pyright over the generated files as a batch and map
   diagnostics back to template positions. No LSP, no editor code, works in
   CI and pre-commit on day one. This requires the generated code to be
   *typeable*, i.e. the template context (component inputs, slots) must have
   declared types to check expressions against; that connects directly to
   the component-interface typing work already researched for Events
   ([`../events_research/typing-lab-report.md`](../events_research/typing-lab-report.md)).
2. **Step 2, live (the `templ lsp` analogue):** a proxy language server that
   regenerates on keystroke and forwards requests to a Python language
   server, rewriting URIs and positions both ways.

**Feasibility signals from templ's experience.**

- **It is a small-team-feasible amount of work.** One maintainer built and
  maintains it inside the framework repo, and the whole repo carries only 40
  open issues at 10k stars. The LSP was not a separate product with its own
  release train; it rides the framework's releases.
- **The costs are predictable and front-loaded.** templ's 68 closed
  LSP-titled issues cluster into four buckets (error-tolerant parsing,
  source-map robustness, Windows URI/path handling, and the proxied server's
  quirks), all of which citry can budget for up front rather than discover.
  The single biggest structural demand is on the parser: citry's Pest
  grammar (`crates/citry_template_parser/src/grammar.pest`) is strict, and
  an editor-facing mode must produce a best-effort AST for broken input
  (templ #1155 "allow partial parsing for improved LSP support" is the
  scar).
- **The host checker only covers the expression half.** gopls gave templ
  nothing for HTML tags, attributes, or component references; that
  intelligence was separate work (#498). For citry the same split holds:
  Pyright/mypy would cover `{{ ... }}` expressions and attribute
  expressions, while `<c-*>` component-name completion, attribute/slot
  validation, and go-to-component need citry's own registry-backed layer
  (which the compile-time validation and registry-dump steps below provide
  anyway).

**Where citry's situation differs from templ's, and what that costs.**

- **Inline templates live inside Python files.** templ's `.templ` files are
  standalone documents with their own file extension, which makes the URI
  rewrite clean. Citry's default authoring mode is a string inside a `.py`
  file that Pyright is *already* checking as Python, so the live-editor
  story needs embedded-document extraction (the problem Volar solves for
  Astro, the `~H` sigil poses for Elixir, and Ruby LSP handles via
  delegation). `template_file` components are the easy, templ-shaped case
  and a sensible place to make the proxy work first. Note that the batch
  (CI) checker in step 1 does not have this problem at all: it can extract
  strings from anywhere.
- **Python has no single canonical language server.** templ proxies gopls,
  the one official server. Python's landscape is Pyright (open source, no
  plugin API), Pylance (closed, license restricted to Microsoft products,
  so not proxyable), Jedi, and mypy (has a plugin API, but plugins are
  mypy-only and famously brittle). Generating real `.py` artifacts is the
  move that sidesteps the whole question: any checker, present or future,
  can read files. A live proxy should target Pyright's open server and
  treat others as best-effort.
- **The expression context is dynamic today.** templ expressions are
  ordinary Go in an ordinary function scope, typed for free. Citry
  expressions are evaluated against a runtime context via `safe_eval`
  (`compiler.rs:195`, `:1199`), so the generated Python must synthesize a
  typed scope (parameters typed from the component's declared inputs) for
  the checker to have anything to say. This is the real design work, and it
  is design work on citry's public API (declared component interfaces), not
  on the tooling.

## Lessons for citry

1. **Sequence the investment as a ladder, shipping value at every rung.**
   The field sorts into a cost-ordered progression, and nothing observed
   suggests skipping rungs: (a) syntax highlighting via injection grammar
   for `template`/`js`/`css` strings in editors, the editor-side twin of the
   already-built `pygments-citry`; (b) registry-dump completions, a CLI
   command printing registered components with attributes and slots
   (Laravel's runtime-introspection trick, nearly free given
   `component_registry.py:86`); (c) compile-time validation of component
   usage with precise template positions (HEEx's `attr` lesson; citry
   already compiles at class-definition time and `Token` spans exist);
   (d) generated-Python batch type-checking in CI (`svelte-check` analogue,
   step 1 above); (e) a live proxy LSP (templ analogue, step 2).
2. **Rungs (b) and (c) deliver most of the perceived value.** What users
   notice day to day is "my editor knows my components" and "typos are
   caught before render". Both come from citry's own parser and registry,
   need no type checker and no LSP, and work identically in every editor
   (compiler diagnostics) or with a thin extension (completions).
3. **Declared component interfaces are the gating dependency for typing.**
   Every framework that got real template type-checking (Svelte, Astro,
   templ, HEEx) has statically declared component inputs. The virtual-Python
   checker is only as good as the types on the template context, so the
   component-interface typing design (already in flight for Events) should
   be treated as part of the IDE roadmap, not adjacent to it.
4. **Build the error-tolerant parser mode before any live tooling.** Herb
   was built parser-first for exactly this reason, and templ retrofitted
   partial parsing under issue pressure. A strict grammar that fails on
   incomplete input is fine for rendering and CI, and unusable for
   keystroke-time analysis.
5. **Keep tooling in the monorepo, versioned with the framework.** Astro
   folded its language tools back into the main repo; templ never separated
   them. The parser, generator, and source maps form one contract; separate
   release trains invite drift, the same failure mode CLAUDE.md's Mechanism
   4 guards against for the language bindings.
6. **Plan for the HTML half explicitly.** The host-language checker covers
   expressions only. Tag/attribute completion inside templates, Tailwind and
   Emmet passthrough, and formatting are separate deliverables in every
   surveyed project (templ #498, Ruby LSP delegation, templ's prettier
   handoff), so they belong on the roadmap as their own items, not as
   assumed side effects of the type-checking work.
7. **One or two people can carry this, at a known cost.** templ (one
   maintainer), Herb (one), Tailwind (two), Svelte (two) all sustain
   production editor tooling; the recurring price is a steady trickle of
   platform and editor-quirk issues (Windows URIs, editor-specific LSP
   deviations), roughly weekly-to-monthly patch releases once adopted. What
   a solo maintainer should *not* attempt is several parallel bespoke
   editor plugins; the LSP-first (or CLI-first) shape is what keeps N
   editors from meaning N codebases.
8. **htmx's "no tooling" option is not available to citry.** A closed
   attribute vocabulary can ride static completion lists; an open component
   vocabulary with embedded Python cannot. Doing nothing means citry
   templates present as inert strings in every editor, which is the
   django-components status quo citry exists to improve on.

## Sources

Web sources, accessed 2026-07-07 unless noted:

- Svelte language-tools repo: https://github.com/sveltejs/language-tools
- svelte2tsx package: https://github.com/sveltejs/language-tools/tree/master/packages/svelte2tsx
- Svelte and TypeScript announcement (origin story): https://svelte.dev/blog/svelte-and-typescript
- Astro + Volar announcement: https://astro.build/blog/astro-and-volar/
- Volar: a new beginning: https://blog.vuejs.org/posts/volar-a-new-beginning
- Volar.js site: https://volarjs.dev/
- Astro language-tools (archived repo): https://github.com/withastro/language-tools
- templ IDE support docs: https://templ.guide/developer-tools/ide-support/
- templ CLI docs (lsp flags, gopls-remote, proxy): https://templ.guide/developer-tools/cli/
- Go Time #291 (templ LSP piggybacking on gopls, source remapping): https://changelog.com/gotime/291
- templ repo and issue tracker: https://github.com/a-h/templ (issue numbers cited inline; counts via GitHub search API 2026-07-07)
- PhpStorm Blade support docs: https://www.jetbrains.com/help/phpstorm/blade-templates-support.html
- Laravel Idea free for PhpStorm (2025-07-30): https://laravel.com/blog/laravel-idea-plugin-is-free-for-phpstorm
- Laravel official VS Code extension: https://github.com/laravel/vs-code-extension
- blade-formatter: https://github.com/shufo/blade-formatter
- Phoenix.Component attr/slot compile-time verification: https://hexdocs.pm/phoenix_live_view/Phoenix.Component.html
- LiveView changelog (declarative assigns, v0.18): https://phoenix-live-view.hexdocs.pm/0.20.0/changelog.html
- Expert LSP repo: https://github.com/expert-lsp/expert
- Ruby LSP ERB/code-navigation write-up (2024): https://railsatscale.com/2024-07-18-mastering-ruby-code-navigation-major-enhancements-in-ruby-lsp-2024/
- Ruby LSP ERB delegation issue: https://github.com/Shopify/ruby-lsp/issues/1055
- Introducing Herb (Marco Roth): https://marcoroth.dev/posts/introducing-herb
- Herb language server announcement: https://marcoroth.dev/posts/herb-language-server
- Herb repo: https://github.com/marcoroth/herb
- htmx community extensions: https://github.com/otovo/htmx-tags, https://marketplace.visualstudio.com/items?itemName=sameer-dudeja.htmx-intellisense, https://plugins.jetbrains.com/plugin/20588-htmx-support
- Tailwind CSS IntelliSense repo: https://github.com/tailwindlabs/tailwindcss-intellisense
- Tailwind editor setup docs: https://tailwindcss.com/docs/editor-setup
- pygments-djc (django-components): https://github.com/django-components/pygments-djc
- django-components org repo listing (no editor extension found): https://github.com/django-components (via GitHub API 2026-07-07)

GitHub API statistics (stars, open issues, release dates, contributor
counts) for sveltejs/language-tools, withastro/language-tools, a-h/templ,
tailwindlabs/tailwindcss-intellisense, marcoroth/herb, expert-lsp/expert,
shufo/blade-formatter, and Shopify/ruby-lsp were retrieved 2026-07-07.

Repo citations (read 2026-07-07):

- `crates/citry_template_parser/src/ast.rs:32-34`, `:75-98`, `:112-118`
  (token spans and offset helpers)
- `crates/citry_template_parser/src/compiler.rs:110` (compile_template
  signature), `:172-195` and `:1199` (Python expressions via safe_eval)
- `crates/citry_template_parser/src/lang/lang.rs` (multi-language codegen)
- `crates/citry_template_parser/src/grammar.pest` (strict Pest grammar)
- `packages/py/citry/citry/assets.py:58`, `:223` (template / template_file
  pairs and resolution)
- `packages/py/citry/citry/component_registry.py:86`,
  `packages/py/citry/citry/autodiscovery.py:39` (registry and
  autodiscovery)
- `README.md:31` (inline template authoring)
- `docs/design/pygments_citry.md` (pygments-citry status, 2026-07-03)
