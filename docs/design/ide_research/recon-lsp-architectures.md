# Recon: language server and editor extension architectures for citry

Date: 2026-07-07. Part of the IDE-integration research corpus under
`docs/design/ide_research/`, feeding the eventual `docs/design/ide_integration.md`.
Web claims were verified against current sources on 2026-07-07 (see Sources);
repo claims cite `file:line` in this repository.

Terms used throughout, defined once: **LSP** (Language Server Protocol) is the
JSON-RPC protocol editors use to ask a separate "language server" process for
completion, hover, diagnostics, go-to-definition, and similar features. A
**TextMate grammar** is a regex-based, declarative highlighting grammar (the
format VS Code, Sublime, and JetBrains can all consume). **tree-sitter** is an
incremental parsing library with its own grammar format; several editors run
tree-sitter parsers natively for highlighting and structural editing.
**Semantic tokens** are an LSP feature (spec 3.16+) where the server sends
symbol-aware highlighting that the editor paints on top of the grammar colors.

## 1. What already exists in the repo (ground truth)

The design space is heavily pre-shaped by decisions and assets already in the
tree. Any architecture proposal must account for these.

**The parser is a Rust library, and it is strict.** The template parser is a
Pest grammar (`crates/citry_template_parser/Cargo.toml:14-15`) whose entry
point returns `Result<Template, ParseError>`
(`crates/citry_template_parser/src/parser.rs:63-67`): on invalid input there
is an error, not a partial tree. Section 5 covers why this matters for an LSP.

**The AST already carries what an LSP needs for variables.** Scope-introducing
nodes record `used_variables` and `introduced_variables` as tokens with source
positions; `docs/design/source_languages.md:361-365` records this explicitly as
the seed of the language server (tracked in issue
[#23](https://github.com/citry-dev/citry/issues/23), alongside the formatter
[#22](https://github.com/citry-dev/citry/issues/22) and syntax highlighting
[#24](https://github.com/citry-dev/citry/issues/24); see
`docs/design/extensions_roadmap.md:110-116`).

**A prior design decision constrains the plan.** The source-languages design
already decided: no interim highlight-only stopgap; when citry invests in the
editor, it builds the full language server and VS Code extension directly
(`docs/design/source_languages.md:367-377`). It also already sketches the
three-layer model (TextMate grammar, semantic tokens, language server) and the
Volar-style virtual-document approach for embedded languages
(`docs/design/source_languages.md:379-400`), plus a concrete TextMate
limitation: a naive `{{ ... }}` regex rule mis-detects boundaries on values
containing braces (`docs/design/source_languages.md:402-409`).

**Two host contexts for templates.** Components declare templates either as
inline Python strings or as separate files via the `template` / `template_file`
pair (`packages/py/citry/citry/assets.py:58`, resolved at
`packages/py/citry/citry/assets.py:223`). Editor support therefore has two
distinct problems: highlighting/serving a citry region *inside a `.py` file*,
and handling a standalone template file. Most template-language LSPs (Django,
Jinja) only face the second; the first is the harder, Svelte/Vue-like half.

**Reference LSP implementations are vendored in-tree.** The ruff submodule is
already a workspace path dependency (`Cargo.toml:29-38`), and it contains
`ruff_server` and `ty_server`, both built on the `lsp-server` and `lsp-types`
crates (`third_party/rust/ruff/crates/ruff_server/Cargo.toml:34-35`,
`third_party/rust/ruff/crates/ty_server/Cargo.toml:31-32`), plus `ruff_wasm`
and `ty_wasm` as working examples of compiling this kind of Rust tooling to
WebAssembly. A citry Rust server can crib structure (document store, scheduler,
handler dispatch) from code that is already checked out.

**A Python parser for Rust is also already vendored.** `ruff_python_parser` is
a workspace dependency (`Cargo.toml:35`). This matters because finding inline
templates means parsing Python source; a Rust server does not need a Python
runtime to locate `class Card(Component): template = "..."` statically.

**Bindings status.** Python bindings are live via PyO3; JS bindings are planned
via wasm-bindgen (issue [#27](https://github.com/citry-dev/citry/issues/27)).
A wasm build of the parser is therefore already on the roadmap independent of
editor tooling.

**Highlighting prior art in-tree.** Two Pygments lexers exist: `citry` (Python
with embedded template/js/css) and `citry-html` (template only), registered in
`packages/py/pygments_citry/pygments_citry/__init__.py:29-43`. The builtin-tag
list there is a hand-kept mirror of `RESERVED_TAG_NAMES`
(`crates/citry_template_parser/src/constants.rs:56`,
`packages/py/pygments_citry/pygments_citry/citry_html.py:31-33`). These lexers
cover docs-site and Sphinx/PyPI rendering, not editors, but they are a tested
statement of what citry highlighting must distinguish, and every new grammar
artifact (TextMate, tree-sitter) adds another mirror of the same token
taxonomy to keep in step.

## 2. The layers of editor support

One editor integration is really four artifacts, and different editors consume
different subsets:

1. **A declarative grammar for base highlighting.** TextMate format for
   VS Code, Sublime, and JetBrains; tree-sitter format for Neovim, Zed, and
   Helix. No current editor consumes both from one source; these are two
   hand-maintained artifacts.
2. **A language server** for completion, diagnostics, hover, go-to-definition.
   Written once, consumed by every editor with an LSP client (all six targets).
3. **Semantic tokens** from that same server, upgrading highlighting where the
   grammar cannot reach (e.g. coloring a `{{ user.name }}` expression by what
   `user` resolves to). Supported by VS Code, Neovim, Sublime (opt-in),
   JetBrains (2024.2+), and Zed (recent, off by default); not by Helix.
4. **Per-editor glue**: a VS Code extension, a JetBrains plugin, a Zed
   extension, a Neovim config entry, a Sublime helper package, a Helix
   `languages.toml` entry. Thin wrappers, but each is a separate artifact with
   its own distribution channel.

## 3. Language server implementation options

The central question: what runtime hosts the server, and how does it reach the
Rust parser? Four realistic options.

### 3.1 Option A: Rust server binary on `lsp-server` (the rust-analyzer scaffold)

`lsp-server` is the synchronous, crossbeam-channel-based scaffold published by
the rust-analyzer project (v0.8.0, released 2026-06-24, actively maintained).
It handles the protocol handshake and message framing; the server owns its own
dispatch loop and threading. This is what both `ruff_server` and `ty_server`
use, vendored in-tree as noted above.

- **Parser reuse:** direct crate linkage; `citry_template_parser` is a library
  dependency, no FFI, no serialization boundary. The richest possible access
  to the AST (spans, variable tracking, future incremental APIs).
- **Python-side knowledge:** static analysis via the vendored
  `ruff_python_parser` (find `Component` subclasses, extract `template`
  strings and `Kwargs` dataclass fields with offsets). Runtime introspection
  (what the registry actually contains after autodiscovery) would need a
  Python sidecar; see section 6.
- **Cost:** most new code among the options (a document store, position
  mapping UTF-8/UTF-16, scheduling), but with two vendored reference
  implementations to copy structure from. Per-platform binary builds are
  mandatory (the same matrix maturin already implies for `citry_core`).
- **Prior art:** rust-analyzer, ruff, ty; among template/framework servers,
  django-language-server (Rust, ships as PyPI wheels).

### 3.2 Option A': Rust server on `tower-lsp-server` (async)

`tower-lsp-server` is the maintained community fork of the dormant `tower-lsp`
(original last released ~2022; the fork is at v0.23.0, 2025-12-07, LSP 3.18).
It gives a `LanguageServer` trait with async handlers on Tokio. Used by Biome,
Oxc, Harper, ast-grep, and django-language-server.

- Same parser reuse and distribution story as option A.
- Trade: less boilerplate than `lsp-server` and a friendlier trait-based API,
  at the cost of an async runtime and less control over request scheduling
  (rust-analyzer-style cancellation and prioritized queues are easier to
  express over the synchronous channel API). For a template-scale language,
  either scaffold is comfortably fast; this is an ergonomics choice, not a
  capability one.

### 3.3 Option B: Node server consuming a wasm build of the parser

A TypeScript server on `vscode-languageserver` (the most mature LSP server
library), calling the Rust parser through a wasm-bindgen build, which issue
[#27](https://github.com/citry-dev/citry/issues/27) plans anyway for JS
bindings.

- **Parser reuse:** real but narrower; only what the wasm API surface exposes,
  with a JS/wasm serialization boundary for AST access.
- **Ecosystem advantage:** the embedded-languages tooling is JS-native.
  `vscode-html-languageservice` (the HTML/CSS smarts behind VS Code itself)
  and the Volar.js framework can be linked in directly, which is exactly the
  machinery a `<c-*>`-in-HTML-in-Python language needs. This is how Svelte,
  Astro, and Vue servers are built.
- **Runtime burden:** inside VS Code the extension host ships Node, so the
  server costs users nothing extra. Every other editor (Neovim, Zed, Helix,
  Sublime, JetBrains) must find a Node runtime on the user's machine, which
  is a real friction for a Python-first audience.
- **Prior art:** svelte-language-server (with svelte2tsx), Astro, Tailwind CSS
  IntelliSense, Prisma.

A variant, **option B': the whole server in Rust compiled to
wasm32-wasip1-threads**, running inside VS Code via `@vscode/wasm-wasi-lsp`
and the WebAssembly core extension (WASI preview 1). Proven by Microsoft's
2024 blog series; also powers VS Code for Web. But it is VS Code-specific
(other editors expect a stdio process), single-digit-factor slower, and adds a
wasm packaging pipeline. Best kept as a later add-on for vscode.dev, not the
primary architecture.

### 3.4 Option C: Python server via pygls reusing `citry_core`

pygls (v2.0.0, released 2025-10-17, LSP 3.18 via lsprotocol 2025.x) is the
standard Python server library. The server would `import citry_core` and reuse
the existing PyO3 bindings unchanged.

- **Parser reuse:** free; the bindings exist today and are the Python
  contract already maintained (`packages/py/citry_core/citry_core/_rust.pyi`).
- **Unique capability:** running inside the user's environment, it can import
  the user's project and ask the real component registry what exists,
  including dynamically registered components that static analysis cannot
  see. No other option gets this without a sidecar.
- **Weaknesses:** interpreter discovery is the classic failure mode (the
  server must run in the *project's* venv to see the project's components,
  and every editor integration must solve "which Python?"); performance
  ceiling for always-on analysis; asyncio server plumbing in Python is more
  fragile under load than the Rust scaffolds. Non-Python editors still need
  the package installed per-project.
- **Prior art:** django-template-lsp (djlsp), jedi-language-server, esbonio.
  Notably, the Django ecosystem's second-generation server
  (django-language-server) moved to Rust and kept only a thin Python agent,
  which is evidence about where option C tops out.

### 3.5 Decision table

Effort grades are relative to each other, not absolute estimates.

| | A: Rust + `lsp-server` | A': Rust + `tower-lsp-server` | B: Node + wasm parser | C: Python + pygls |
|---|---|---|---|---|
| Rust parser reuse | Direct crate link (full AST) | Direct crate link (full AST) | Via wasm API surface only | Via existing PyO3 bindings |
| New binding work | None | None | wasm-bindgen surface (planned anyway, #27) | None |
| Sees user's live component registry | Needs Python sidecar | Needs Python sidecar | Needs Python sidecar | Native (imports project) |
| Static Python analysis (find components/templates) | Vendored `ruff_python_parser` | Vendored `ruff_python_parser` | Needs a JS-side Python parser or wasm export | Python `ast` module |
| Embedded HTML/CSS smarts | Reimplement or shell out | Reimplement or shell out | `vscode-html-languageservice`, Volar.js direct | Reimplement or shell out |
| Runtime users need | None (native binary) | None (native binary) | Node (free inside VS Code only) | Python + citry install per project |
| Performance headroom | Highest | Highest | Medium | Lowest |
| Error-tolerant parsing path | tree-sitter crate in-process (see 5) | Same | web-tree-sitter or last-good-tree | Last-good-tree |
| Distribution | Per-platform binaries (wheels, vsix, Mason, Zed, brew) | Same | npm + bundled into vsix | PyPI (`citry[lsp]` extra) |
| Build/release cost | Highest (platform matrix, but same matrix as `citry_core` wheels) | Same | Lowest (one wasm blob + JS) | Lowest (pure Python + existing wheels) |
| In-tree reference code | `ruff_server`, `ty_server` vendored | django-language-server (external) | Svelte/Astro/Tailwind (external) | djlsp (external) |
| Main risk | Most code to write | Fork longevity (community-maintained) | Node requirement outside VS Code; JS<->wasm AST boundary | Interpreter discovery; perf ceiling; rewrite risk later |

**Reading of the table.** The Rust options maximize reuse of what makes citry
distinctive (the parser and its variable tracking) and match the project's
"Rust is the single source of truth" doctrine (CLAUDE.md, "What this project
is"). Option C maximizes time-to-first-demo and is the only one that sees the
live registry, but the Django precedent suggests it becomes the thing you
rewrite. Option B's real pull is the JS-native embedded-language tooling; that
pull weakens if the server delegates embedded regions to other servers rather
than embedding language services (section 6). A hybrid is available and has
precedent (django-language-server): a Rust server as the product, with a tiny
optional Python introspection helper for registry-accurate answers.

## 4. Syntax highlighting artifacts

### 4.1 TextMate grammar: still mandatory for VS Code

VS Code has no native tree-sitter highlighting; the 2018 feature request
(microsoft/vscode#50140) remains unimplemented and de-prioritized, so a
TextMate grammar contributed by the extension is still the base highlighting
mechanism in 2026. The same `.tmLanguage`/`.tmBundle` artifact is consumable
by Sublime Text (which prefers its own `.sublime-syntax` but reads TextMate)
and by JetBrains IDEs through the bundled TextMate Bundles plugin, which
highlights file types with no native plugin support.

Two citry-specific notes:

- **Injection grammars** are how the inline case works in VS Code: a grammar
  with `injectTo: source.python` can match `template = """` regions and hand
  the string body to the citry-HTML grammar, and inside it hand `{{ ... }}` to
  Python, `<style>` to CSS, `<script>` to JS. This is the established pattern
  for SQL-in-strings and styled-components extensions.
- The already-recorded limitation stands: TextMate cannot count braces, so
  `{{ {'a': {}} }}` mis-highlights under a naive rule
  (`docs/design/source_languages.md:402-409`). The grammar should be treated
  as best-effort coloring, with correctness delegated to semantic tokens.

### 4.2 tree-sitter grammar: three editors and a server-side bonus

Neovim (built-in `vim.treesitter`), Helix, and Zed all do their highlighting,
indentation, and structural editing exclusively through tree-sitter grammars
plus per-editor query files (`highlights.scm` etc.; capture conventions are
not fully standardized across the three, so queries need per-editor variants).
GitHub's code-view highlighting service is also tree-sitter-based where a
grammar exists, falling back to TextMate-based PrettyLights (linguist does
detection only). Registering the language with linguist is a longer-term,
traction-gated play; note that inline citry templates live in `.py` files that
GitHub will keep highlighting as Python regardless, so the linguist question
only affects standalone template files and ```` ```citry ```` fences.

Cost side: a tree-sitter grammar is a second full grammar (grammar.js, and
likely an external scanner in C for raw-text elements like `<c-raw>`),
maintained by hand in parallel with the Pest grammar. There is no
Pest-to-tree-sitter conversion; the token taxonomy becomes a third mirror
(after the Pygments lexers) of `RESERVED_TAG_NAMES`. tree-sitter's
**injections** mechanism covers both embedding directions: a citry grammar can
inject Python into `{{ ... }}`, and the *Python* grammar can inject citry into
`template = """..."""` strings via an `injections.scm` shipped for the Python
grammar (the same mechanism Neovim uses for SQL-in-string highlighting).

The bonus: tree-sitter is also a Rust library. A Rust server (options A/A')
can embed the same grammar in-process as its error-tolerant parser for
broken-mid-keystroke documents, while the strict Pest parser provides the
authoritative AST when the document parses. htmx-lsp2 and jinja-lsp are
existing Rust template servers built exactly this way. This turns the grammar
from a pure maintenance cost into a shared asset across three editors, GitHub,
and the server itself.

### 4.3 Semantic tokens: the upgrade channel, not the baseline

Semantic-token support across the targets, verified 2026-07-07:

- VS Code: full support, themable, the reference implementation.
- Neovim: built-in since 0.9, on by default when the server provides them.
- JetBrains: "semantic highlighting" listed in the native LSP API feature set
  (2024.2-2025.1 wave).
- Sublime: supported by the LSP package, opt-in (`semantic_highlighting`
  setting), custom token types mappable to scopes.
- Zed: added in v0.224 (2026), off by default, with `off`/`combined`/`full`
  modes; tree-sitter remains the default highlighter.
- Helix: not supported (issue #814, converted to discussion #5589); grammar
  queries are the only highlighting channel.

Implication: semantic tokens cannot be the only highlighting story anywhere,
and on Helix/Zed defaults they do not fire at all. The grammars carry the
baseline; the server's semantic tokens add symbol-aware color for editors that
paint them. Custom token types (e.g. a `citryComponent` token for `<c-Card>`)
degrade to nothing in stricter clients unless mapped, so the server should
stick close to standard token types and use modifiers for citry-ness.

## 5. Error tolerance: the strict-parser gap

`parse_template` returns `Result<Template, ParseError>`
(`crates/citry_template_parser/src/parser.rs:63-67`): one error, no partial
tree, and Pest reports the first failure point rather than a set of
diagnostics. An LSP lives in permanently broken documents (the user is
mid-keystroke most of the time). Consequences and the standard mitigations:

- **Diagnostics** work fine from day one: a failed parse becomes one squiggle.
  Multiple simultaneous diagnostics need either parser-side recovery work or a
  second tolerant pass.
- **Completion/hover during typing** cannot depend on a clean parse. The
  cheap, universal mitigation is the last-good-tree pattern (answer from the
  most recent successful parse, adjusted by text deltas). The stronger one is
  the embedded tree-sitter parse from section 4.2, which always yields a tree
  with explicit `ERROR` nodes.
- Whatever the choice, it should be recorded as an explicit architectural
  decision in the design doc, because it shapes whether the tree-sitter
  grammar is optional (editor reach only) or load-bearing (server internals).

## 6. Embedded languages: the hard quarter of the problem

citry is embedded twice over: templates inside Python files, and Python/CSS/JS
inside templates. Three architectures exist in the wild:

1. **Request forwarding with virtual documents** (VS Code's documented
   pattern): the client extension mirrors embedded regions into hidden
   documents (`embedded-content://css/...`) where non-CSS text is blanked to
   whitespace, then forwards completion requests to whatever extension handles
   that language. Cheap, but it is a *client-side* trick: it works in VS Code
   and must be re-invented (or dropped) per editor.
2. **Language services in the server**: link the target language's analyzer
   into the server itself. `vscode-html-languageservice` (HTML/CSS) makes this
   nearly free in a Node server; Volar.js generalizes it into a framework of
   virtual-code mappings. The repo's own analysis of this model is at
   `docs/design/source_languages.md:334-346`: the mapping is authored per
   language and is never free.
3. **Shadow files**: compile the component to a real file of the host
   language and let the existing ecosystem server analyze it, mapping
   positions back. svelte2tsx is the canonical example (Svelte template ->
   TSX -> tsserver). The citry analog would generate a shadow `.py` per
   component (template expressions as real Python code referencing the
   component's `Kwargs`/state types) and let Pyright/ty/Jedi produce
   type-aware completion, with the citry server mapping ranges. This is the
   only realistic route to *typed* `{{ user.name }}` completion, because
   Pyright has no plugin API to teach it citry directly.

The pragmatic recon conclusion: HTML/CSS assistance inside templates is
table stakes and cheap in a Node server, moderate in Rust (either re-expose a
minimal HTML data set or delegate). Typed Python expression support is the
premium feature and points at shadow files regardless of server language.
Speculative but worth flagging: `ty_server` and its analysis crates are
already vendored (`third_party/rust/ruff/crates/`), so a Rust citry server
embedding ty's analysis for expression-level checks is at least conceivable,
though it is unvalidated and would be a major dependency decision.

## 7. Editor coverage matrix

What one language server plus two grammars (TextMate + tree-sitter with
queries) buys, per editor, as of 2026-07:

| Editor | Base highlighting artifact | LSP client | Semantic tokens | Citry must ship | Channel |
|---|---|---|---|---|---|
| VS Code + forks (Cursor, Windsurf, VSCodium) | TextMate grammar (required; no native tree-sitter) | Extension-provided client | Yes | Extension: grammar + client + server binary (or wasm) | Marketplace and Open VSX (forks default to Open VSX) |
| JetBrains (PyCharm, IntelliJ, ...) | TextMate bundle (bundled plugin) or full custom plugin | Native LSP API (2023.2+; free for all IDEA users since 2025.2/2025.3 unified installer; open-sourced for 2026.2, reaching Android Studio); or LSP4IJ | Yes (2024.2+) | Thin plugin: `LspServerDescriptor` + bundled server + TextMate bundle | JetBrains Marketplace |
| Neovim 0.11+ | tree-sitter grammar + queries | Built-in (`vim.lsp.enable`; `vim.lsp.config` standard by 0.12) | Yes (0.9+) | Grammar registration + lspconfig/native config entry; server via Mason registry | nvim-treesitter/user config + mason-registry |
| Zed | tree-sitter grammar (compiled to wasm by the extension toolchain) + queries | Extension declares `language_server_command`; extension can auto-download the binary | Yes since v0.224, off by default | Rust wasm extension (`zed_extension_api`) bundling grammar + queries | zed-industries/extensions registry PR |
| Sublime Text | `.sublime-syntax` (or reuse the TextMate grammar) | LSP package (Package Control) | Opt-in | Syntax package + an `LSP-citry` helper package pointing at the binary | Package Control |
| Helix | tree-sitter grammar + queries | Built-in | No | `languages.toml` entry (user-side, or PR into helix for out-of-box) + grammar fetch/build | helix repo PR or user config |
| GitHub.com (read-only bonus) | tree-sitter-based highlighting service (TextMate/PrettyLights fallback); linguist for detection | n/a | n/a | linguist registration once usage justifies it; `.py` files stay Python-highlighted either way | github-linguist PR |

Two structural takeaways. First, the language server is the only
write-once-run-everywhere artifact; every editor's glue is thin once the
server exists. Second, the grammar work splits the world in half: TextMate
covers VS Code/JetBrains/Sublime, tree-sitter covers Neovim/Zed/Helix (plus
GitHub and possibly the server's own error tolerance). Skipping tree-sitter
forfeits three editors' highlighting entirely (their users would get LSP
features over plain-text files); skipping TextMate forfeits VS Code, the
majority target.

## 8. Distribution and packaging

### 8.1 The server binary (assuming a native-binary option)

- **PyPI wheels, rides the existing pipeline.** The strongest fit for citry's
  audience: publish the server as a binary inside a wheel (own package like
  `citry-lsp`, or an extra of `citry`), giving `uv tool install` / `pipx`
  installs and a console-script entry point. django-language-server and ruff
  both ship Rust binaries this way, and citry already runs a maturin wheel
  matrix for `citry_core`, so the platform matrix is not new cost. This also
  neutralizes option C's "already in your venv" advantage for every editor
  whose users have Python (all of them, for citry's audience).
- **GitHub Releases artifacts** as the canonical URL source that Zed
  extensions, Mason, and Homebrew formulas download from. Zed's
  `zed_extension_api` and Mason's registry both expect per-platform archive
  URLs; cargo-dist-style automation generates them from tags.
- **Bundled per editor** where the channel supports it (see 8.2 for VS Code,
  JetBrains plugins can bundle the binary as a plugin resource).
- Version skew policy is needed early: the server's understanding of the
  grammar must track the `citry` package version the project uses. The djls
  and ruff pattern (server versioned and released in lockstep with the main
  package, from the same monorepo) is the natural fit here.

### 8.2 VS Code specifically

- **Platform-specific extensions**: `vsce publish --target win32-x64 ...`
  publishes one vsix per platform, each embedding the right server binary, so
  installs work offline and behind proxies (the pattern Microsoft documents
  and the platform-specific-sample demonstrates). This is preferred over
  download-on-activation (the older hashicorp/terraform-style approach), which
  breaks in restricted networks.
- **Publish to both registries.** The Microsoft Marketplace terms restrict
  its use to Visual Studio-family products, so Cursor, Windsurf, and VSCodium
  default to Open VSX (Eclipse Foundation; 300M+ monthly downloads, AWS and
  Cursor sponsorship as of 2026-03). Not publishing to Open VSX leaves the
  fast-growing fork audience with nothing, and unclaimed names on Open VSX
  have been an active supply-chain attack surface (January 2026 reports), so
  claiming `citry` there early is also defensive.
- A wasm-wasip1 server build via `@vscode/wasm-wasi-lsp` additionally unlocks
  vscode.dev/github.dev; treat as a later increment, not the base plan.

### 8.3 npm (only if option B, or for the JS bindings anyway)

The established pattern is one wrapper package plus per-platform binary
packages under `optionalDependencies` with `os`/`cpu` fields (esbuild
pioneered it, PR evanw/esbuild#1621; Biome, Turbo, and Bun use it). If citry
ships JS bindings per issue #27, the wasm package for Node makes a per-platform
matrix unnecessary for the *parser*; the pattern only becomes relevant if a
native Node server binary is ever distributed through npm.

### 8.4 JetBrains specifically

The native LSP API removes the old blocker: since 2025.2 it is available
beyond paid IDEs, the 2025.3 unified IntelliJ IDEA installer keeps LSP
available to everyone, and the client API is open-sourced in the 2026.2 cycle
(landing in 2026.1.4), extending to Android Studio and IntelliJ-platform
forks. A citry plugin is then: a `plugin.xml` with the
`com.intellij.modules.lsp` optional dependency, an `LspServerDescriptor`
(or the renamed `LspClient`-era API), the bundled server binary, and a
TextMate bundle for base highlighting, distributed via JetBrains Marketplace.
LSP4IJ (Red Hat's third-party client) remains the fallback for older IDE
versions; JetBrains' own guidance is not to migrate between the two without
reason. PyCharm is the single most important citry target after VS Code, and
this path no longer requires writing a full PSI-based custom-language plugin;
the trade-off (less deep integration than PSI, e.g. no full refactoring
parity) is acceptable for a template language.

### 8.5 The long tail

- **Neovim**: Mason registry entry (points at GitHub release archives) plus an
  lspconfig/`vim.lsp.config` server definition upstreamed; tree-sitter parser
  registered for install. Note nvim-treesitter's master branch is frozen with
  the plugin reorganized around its main branch and Neovim 0.12's built-in
  workflows; new grammar registrations should target the current mechanism.
- **Zed**: one small Rust wasm extension in the zed-industries/extensions
  registry; it carries the grammar by git revision reference and downloads the
  server from releases.
- **Helix**: PR to helix's `languages.toml` for out-of-the-box support (grammar
  fetched from the citry grammar repo and built locally); until then a
  documented user-config snippet suffices.
- **Sublime**: syntax package plus `LSP-citry` helper on Package Control.

## 9. Prior-art shortlist for the design phase

- **In-tree**: `ruff_server` / `ty_server` (Rust, `lsp-server`, document
  store and scheduling patterns), `ruff_wasm` / `ty_wasm` (wasm packaging),
  `ruff_python_parser` (static Python analysis from Rust).
- **django-language-server** (Rust, `tower-lsp-server`, PyPI wheels, Python
  agent for project introspection): the closest analog to citry's whole
  problem, one ecosystem over.
- **django-template-lsp** (pure Python): what option C looks like matured,
  including its ceiling.
- **svelte-language-tools / svelte2tsx**: the shadow-file architecture for
  typed template expressions.
- **Volar.js / Vue**: the virtual-code mapping framework; already analyzed in
  `docs/design/source_languages.md:334-346`.
- **htmx-lsp2 / jinja-lsp**: Rust template servers using tree-sitter
  in-process for error-tolerant parsing.
- **Tailwind CSS IntelliSense**: Node server; the reference for
  attribute-level completion UX inside markup.

## 10. Implications (recon-level, not the decision)

1. The repo's own doctrine (Rust as single source of truth, CLAUDE.md) plus
   the vendored `ruff_server`/`ty_server` reference code plus the wheel
   pipeline already in place make **a Rust server distributed as PyPI wheels
   and platform-specific vsix** the default candidate; the honest competitor
   is **Node + wasm** on embedded-language tooling strength, not on parser
   reuse or distribution.
2. A **Python pygls server is the cheapest first demo** but the Django
   ecosystem already ran that experiment and moved to Rust; if speed-to-demo
   matters, scope it as a throwaway prototype, not the architecture.
3. The **tree-sitter grammar should be evaluated as server infrastructure,
   not just editor reach**: it is the plausible answer to Pest's all-or-nothing
   parsing, and it unlocks Neovim/Zed/Helix and GitHub as side effects. The
   design doc should decide grammar-maintenance policy (a third mirror of the
   token taxonomy) explicitly.
4. **TextMate + injection grammar for `.py` inline templates** is unavoidable
   for VS Code baseline highlighting and reusable in JetBrains and Sublime.
5. **Typed `{{ ... }}` completion** is the differentiating feature and needs a
   shadow-file design (svelte2tsx-style) regardless of server language; it
   deserves its own design section, possibly its own research pass.
6. Registry-accurate component knowledge (dynamic registration, autodiscovery)
   eventually wants a **small Python introspection sidecar** even under a Rust
   server; djls proves the shape. Static analysis via `ruff_python_parser`
   covers the common case without it.

## Sources

Repo files are cited inline as `file:line`. Web sources, all accessed
2026-07-07:

- tower-lsp (original, dormant): https://github.com/ebkalderon/tower-lsp
- tower-lsp-server community fork (v0.23.0, 2025-12-07, LSP 3.18; users incl. Biome, Oxc, django-language-server): https://github.com/tower-lsp-community/tower-lsp-server
- lsp-server crate (rust-analyzer project; v0.8.0, 2026-06-24; synchronous crossbeam design): https://lib.rs/crates/lsp-server
- VS Code wasm extensions part 2 (2024-06-07; `@vscode/wasm-wasi-lsp`, wasm32-wasip1-threads, WASI preview 1): https://code.visualstudio.com/blogs/2024/06/07/wasm-part2
- microsoft/vscode-wasm (WASI on the extension host): https://github.com/microsoft/vscode-wasm
- Oso's Rust+wasm VS Code extension write-up: https://www.osohq.com/post/building-vs-code-extension-with-rust-wasm-typescript
- pygls releases (v2.0.0, 2025-10-17; lsprotocol 2025.x, LSP 3.18): https://github.com/openlawlibrary/pygls/releases
- VS Code tree-sitter feature request (open since 2018): https://github.com/microsoft/vscode/issues/50140
- tree-sitter syntax highlighting docs: https://tree-sitter.github.io/tree-sitter/3-syntax-highlighting.html
- Zed language extensions docs (grammar by git rev, queries): https://zed.dev/docs/extensions/languages
- Zed extensions internals (Rust, WIT, wasm32-wasip1): https://zed.dev/blog/zed-decoded-extensions
- Zed syntax-aware editing (tree-sitter rationale): https://zed.dev/blog/syntax-aware-editing
- Zed semantic tokens docs (off/combined/full, off by default): https://zed.dev/docs/semantic-tokens
- Zed semantic tokens issue and rollout (added v0.224): https://github.com/zed-industries/zed/issues/7450
- Helix languages docs: https://docs.helix-editor.com/languages.html
- Helix semantic-tokens status (not supported; #814 converted to discussion): https://github.com/helix-editor/helix/discussions/5589
- Neovim treesitter docs: https://neovim.io/doc/user/treesitter/
- Neovim LSP docs (native client, `vim.lsp.enable`/`vim.lsp.config`): https://neovim.io/doc/user/lsp/
- nvim-treesitter (branch/architecture transition): https://github.com/nvim-treesitter/nvim-treesitter
- mason.nvim and registry (server binary distribution for Neovim): https://github.com/mason-org/mason.nvim, https://mason-registry.dev/registry/list
- Sublime LSP package (semantic highlighting opt-in, custom token scopes): https://github.com/sublimelsp/LSP, https://sublimelsp.github.io/LSP/features/
- VS Code embedded languages guide (virtual documents, request forwarding): https://code.visualstudio.com/api/language-extensions/embedded-languages
- vscode-html-languageservice: https://github.com/microsoft/vscode-html-languageservice
- VS Code publishing docs (platform-specific targets): https://code.visualstudio.com/api/working-with-extensions/publishing-extension
- Open VSX registry: https://open-vsx.org/
- Open VSX growth and AWS backing (2026-03-03): https://www.theregister.com/2026/03/03/open_vsx_aws/
- VS Code fork extension supply-chain reports (2026-01): https://thehackernews.com/2026/01/vs-code-forks-recommend-missing.html
- esbuild optionalDependencies install strategy (PR #1621): https://github.com/evanw/esbuild/pull/1621
- Sentry on publishing binaries to npm: https://sentry.engineering/blog/publishing-binaries-on-npm
- IntelliJ Platform LSP docs (feature matrix by version, server bundling): https://plugins.jetbrains.com/docs/intellij/language-server-protocol.html
- JetBrains blog, LSP API for all IDEA users (2025-09; 2025.2/2025.3 licensing change): https://blog.jetbrains.com/platform/2025/09/the-lsp-api-is-now-available-to-all-intellij-idea-users-and-plugin-developers/
- JetBrains blog, open-sourcing the LSP client API (2026-06; 2026.1.4/2026.2, Android Studio): https://blog.jetbrains.com/platform/2026/06/open-sourcing-the-lsp-client-api-in-intellij-idea-2026-2/
- LSP4IJ (Red Hat third-party LSP client for JetBrains): https://plugins.jetbrains.com/plugin/23257-lsp4ij
- JetBrains TextMate bundles: https://www.jetbrains.com/help/idea/textmate.html
- GitHub linguist: highlighting vs detection (tree-sitter service, PrettyLights fallback): https://github.com/github-linguist/linguist/discussions/5572
- django-language-server (Rust, PyPI wheels, Python agent): https://github.com/joshuadavidthomas/django-language-server
- django-template-lsp (Python, fourdigits): https://github.com/fourdigits/django-template-lsp
- htmx-lsp2 (Rust, tree-sitter-based template server): https://github.com/uros-5/htmx-lsp2
- svelte language-tools (svelte2tsx shadow-file architecture): https://github.com/sveltejs/language-tools
