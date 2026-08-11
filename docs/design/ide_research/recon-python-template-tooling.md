# Recon: IDE tooling in Python template land

**Date: 2026-07-07.** Ground-truth sweep of existing editor tooling for
Python-adjacent template languages, feeding the IDE integration design
([`../ide_integration.md`](../ide_integration.md)). It covers the Django
template language servers, the template linters and formatters, how PyCharm
and the VS Code Python stack handle templates, how editors highlight foreign
languages inside Python strings today, and what django-components (the
project citry was forked from) ships or recommends. It closes with lessons
for citry, centered on the one problem citry cannot avoid: its templates
live inside Python string literals.

All web claims were verified against live sources on 2026-07-07 (access
dates in the Sources section). Repo claims cite `file:line`.

Related repo context, read before this sweep:

- [`../source_languages.md`](../source_languages.md) already records the
  standing decisions on editor experience: no interim highlight-only
  stopgap, and the real investment is a citry language server plus grammar
  (`docs/design/source_languages.md:367-377`).
- The extensions roadmap files the language server / linter (#23), formatter
  (#22), and syntax highlighting (#24) as standalone tooling that benefits
  from the Rust parser (`docs/design/extensions_roadmap.md:110`).
- The migration review carried over django-components' own language-server
  wish, noting citry's variable tracking in the AST already supports it
  (`docs/design/migration_djc.md:148`).

---

## 1. The problem citry has that Django tools do not

A citry component holds its template, script, and style as multiline Python
strings on a class (example in `docs/design/source_languages.md:32-37`). The
template is citry's own language: `<c-*>` tags, `{{ ... }}` Python
expressions, `{# ... #}` comments
(`docs/design/source_languages.md:350-352`). The Rust parser already records
what a language service needs, per-node `used_variables` and
`introduced_variables` tokens with source positions
(`crates/citry_template_parser/src/ast.rs:274`,
`crates/citry_template_parser/src/ast.rs:520`).

Every Django-world tool surveyed below assumes the template is a **file**
with its own extension. citry's default is a **string inside a `.py` file**
that the editor has already assigned to the Python language and to the
Python language server. So citry needs two things the Django tools never
built: a way to attach template intelligence to regions of Python files,
and (the easier, well-trodden part) intelligence for template files
themselves. Section 7 covers who has attached anything to Python strings
and how; the short answer is that highlighting is solved, semantics is not,
and the solutions that exist for semantics come from owning a separate
language server or a JetBrains plugin, never from extending the Python
language server.

---

## 2. Django template language servers

Two real language servers exist for Django templates. Both are active in
2025-2026, both target template files only, and neither touches templates
embedded in Python strings.

### 2.1 django-template-lsp (djlsp, Four Digits)

A Python-implemented language server (LSP), v1.2.2 released 2025-11-14,
with a VS Code extension (`FourDigits.djlsp`) plus Helix and Neovim
configs.

- **Features:** completion for custom tags and filters, `{% load %}`,
  `{% static %}` paths, `{% url %}` names, and template paths in
  `{% extends %}` / `{% include %}`; go-to-definition for templates, the
  views behind `{% url %}`, and tag/filter implementations; hover docs for
  urls, tags, and filters. Context variables get only "partial support for
  jumping to context definitions".
- **Project introspection runs the user's project.** djlsp collects project
  data (installed tags, urls, templates, static files) by executing a
  collection script with the project's own Python, tried in order: a local
  virtualenv (`env`, `.env`, `venv`, `.venv`), a Docker Compose service
  (default name `django`), or global `python3`. Collection fails if the
  project has syntax errors or missing imports, a real operational
  weakness.
- **Context typing is a manual workaround.** Because Django gives no static
  way to know what a view passes to a template, djlsp reads type comments
  written into the template itself, `{# type blog: blogs.models.Blog #}`,
  currently limited to Django models. This is the clearest evidence in the
  ecosystem that "what variables exist here, and what are their types" is
  the unsolved hard part for Django templates.

### 2.2 django-language-server (djls, Josh Thomas)

A newer language server with a **Rust core** (~81% Rust), distributed as
PyPI wheels and standalone binaries, runnable with
`uvx --from django-language-server djls serve`, with a VS Code marketplace
extension and documented Neovim, Sublime Text, and Zed setups. Latest
release v6.0.3, 2026-05-16, still flagged by its author as early stage
("most features are incomplete").

- **Features (as listed):** tag and filter completion with snippets,
  diagnostics, go-to-definition for templates, blocks, and variables, find
  references across templates, document links for
  `{% extends %}` / `{% include %}` / `{% load %}`, folding, hover docs,
  code actions, rename across files, document and workspace symbols,
  signature help, and optional whole-document formatting delegated to
  `djangofmt`.
- **Relevance to citry:** djls is the existence proof for citry's exact
  architecture bet, a Rust-core language server for a Python-framework
  template language, shipped through PyPI so Python users install it with
  their normal tools. Its docs do not detail how it introspects the Django
  project, so no lesson could be verified there.

### 2.3 What both punt on

Neither server attempts type-aware context resolution (djlsp's type
comments are opt-in manual labels), and neither handles templates inside
Python strings. Their value concentrates in project-level cross-references
(urls, template paths, tag libraries), which Django scatters across the
project and citry mostly does not.

---

## 3. Template linters and formatters

These are batch tools, not editor services, but they define user
expectations and show where parsing approaches hit their ceiling.

- **djLint** (v1.40.3, released 2026-07-04): the de facto linter and
  formatter for HTML templates, with profiles for django, jinja, nunjucks,
  twig, handlebars, mustache, golang, and angular. Configurable lint rules
  plus a `--reformat` / `--check` formatter, a VS Code extension
  (`monosans.djlint`), and pre-commit hooks. Implementation is **regex
  pattern matching**, and the project openly maintains a 2.0 rewrite branch
  to address performance and edge cases. Lesson: regex-based template
  tooling ships fast, gets popular, then accumulates an edge-case tail that
  forces a rewrite.
- **djade** (Adam Johnson, introduced 2024-09-26): a Django template
  formatter written in Rust as "a translation of the relevant parts of
  Django's template parser". Deliberately Black-like (opinionated, no
  configuration) and deliberately scoped: it formats only the template
  syntax and leaves the surrounding HTML untouched for safety. Fast
  (~20ms for 377 templates).
- **djangofmt** (UnknownPlatypus): a Rust, HTML-aware Django template
  formatter, the one djls delegates to.
- Directory of the niche: Django Packages keeps a "template linters" grid
  (djLint, djhtml the indenter, curlylint, etc.), most of which are
  single-purpose file-level tools.

The trend across all three actively developed tools is the same: the
serious implementations moved to Rust and to real parsers, and the scope
that works is "format the template language, do not try to own the HTML".
citry already has the real parser these tools had to build.

---

## 4. jinja-lsp

A Rust language server for Jinja templates (uros-5/jinja-lsp, v0.2.3,
released 2026-07-01), built on **tree-sitter** queries, with Helix and
Neovim configs and a VS Code extension.

- Features: completion, hover, go-to-definition, code actions, diagnostics,
  document symbols.
- Its distinctive move: it **reads the backend source** (Rust or Python
  directories, configured by the user) to learn which variables and filters
  the backend defines and passes to templates, then offers them in template
  completion. This is the closest open-source analogue to "resolve into
  context", achieved by static analysis of the host code rather than by
  running it (contrast djlsp, section 2.1).
- Its docs do not claim support for templates embedded in backend string
  literals; the analysis pairs template files with backend code.

---

## 5. PyCharm: the ceiling of what an IDE does for Python templates

### 5.1 What PyCharm Professional's Django support delivers

PyCharm's Django template support (a paid-tier feature, historically
PyCharm Professional) is the richest Python-template experience shipping
anywhere: syntax and error highlighting, code completion, completion for
block names, resolve and completion for custom tags and filters, quick
documentation for tags and filters, navigation between views and templates,
live preview, a Django Structure tool window, and a template debugger
(breakpoints inside templates). Configuration is project-level: directories
in `TEMPLATES['DIRS']` are auto-marked as template roots on first open, and
the project's template language (Django, Jinja2) is chosen in settings; the
chosen language is then applied to the configured template file types.

Two implementation facts matter for citry:

- Template files are handled by a dedicated template-language machinery
  (the file is parsed as template syntax layered over a data language such
  as HTML), not by generic string injection. That machinery is the IDE's
  own, closed-source Django plugin.
- Even PyCharm's flagship implementation documents completion and resolve
  for **tags, filters, and block names**; deep context-variable resolution
  from views is at best partial and not documented as a headline feature.
  The same hard part everyone else punts on (sections 2.1, 4).

### 5.2 What the IntelliJ platform offers third parties

For a citry plugin, the IntelliJ Platform provides real, documented
injection APIs, and this is the one ecosystem where a third party can get
**semantic** features inside a Python string literal:

- **User-level injections (IntelliLang):** users inject a language into a
  string via a `# language=HTML` comment or IDE settings, with optional
  `prefix` / `suffix` text to make fragments parse as valid documents.
  Injection configurations are shareable XML with `<place>` element
  patterns, so a project can ship injection rules without writing a plugin.
- **Plugin APIs:** `LanguageInjectionContributor` (declare *what* language
  to inject for a given PSI context, e.g. "the string assigned to
  `template` on a `Component` subclass is citry-HTML"),
  `LanguageInjectionPerformer` (control *how*, including string
  concatenation and interpolation), and the low-level `MultiHostInjector`
  (inject across multiple string fragments). An injected fragment gets its
  own PSI tree, so the injected language's completion, navigation, and
  inspections run inside the string. PSI is the platform's parsed program
  model; a plugin with PSI access can implement any semantic feature the
  IDE itself could.
- **LSP as an alternative to a native plugin:** JetBrains added an LSP API
  for plugin developers in 2023.2, then restricted to paid IDEs. As of
  IntelliJ IDEA Ultimate 2025.2 the LSP API remains usable without an
  active subscription (the LSP implementation stays closed but free for
  third-party plugins), while the 2025.2 Community Edition still lacks it;
  JetBrains is moving to a unified distribution where LSP support is
  available to all users. Independently, Red Hat's **LSP4IJ** is a free,
  open-source LSP client plugin that works across all IntelliJ-based IDEs,
  including community flavors. So a citry language server can reach
  JetBrains users two ways (official LSP API, LSP4IJ) before any native
  plugin is written, at the cost of shallower integration than PSI
  injection.

---

## 6. VS Code: Pylance is closed, and the ecosystem routes around it

### 6.1 No extension points inside Pylance

Pylance, the language server behind the Microsoft Python extension, is
closed-source and free; its typing engine is the open-source pyright, and
Microsoft directs all code contributions there. Pyright deliberately does
not support plugins (unlike mypy's plugin system); this has been its
maintainer's documented position since 2020 (pyright issue #607). The
sanctioned ways to influence what Pylance shows are all typing-standards
shaped: PEP 561 stub packages, bundled stubs, and typing-spec features like
`dataclass_transform`, which is exactly how pydantic got first-class
completion without a plugin. None of these can express "this string literal
is a citry template", so **there is no Pylance integration point for
citry's problem**.

Open alternatives exist and are growing: **basedpyright** (an open-source
pyright fork that reimplements Pylance-only features) and Astral's **ty**
(an open-source type checker and language server). Both are contributable,
neither has a template-injection concept today. They matter mainly as a
hedge: the Python-LSP layer may not stay a closed monoculture.

### 6.2 What third parties actually do: run a second language server

VS Code merges language features from every provider registered for a
document. The working pattern, proven at scale, is to ship your own
extension with your own language server registered for `python` documents
alongside Pylance: Ruff does this for lint/format, and
tailwindcss-intellisense does it for class completion (section 8). The two
servers do not coordinate; each answers the requests it understands. The
Python extension additionally exposes a public API
(`@vscode/python-extension` npm package) for discovering the selected
interpreter and environments, which a companion server needs to resolve the
user's project (the same problem djlsp solves with its venv/Docker probing,
section 2.1).

### 6.3 Embedded-language machinery for the server itself

For the "CSS and JS inside a citry template" layer, VS Code documents two
patterns for a language server that owns a mixed-language document:
**language services** (embed e.g. `vscode-css-languageservice` in your
server and compute a virtual document per region, blanking non-CSS text
with whitespace so positions survive) and **request forwarding** (the
extension client registers a virtual `embedded-content://` document per
region and forwards requests to whatever extension handles that language).
The guide recommends language services for control and editor portability;
request forwarding cannot produce diagnostics and ties the behavior to VS
Code. This matches the delegation plan already recorded in
`docs/design/source_languages.md:448-455`.

---

## 7. Highlighting foreign languages inside Python strings today

This is the current state of the art for citry's core problem, and it is
highlighting only.

### 7.1 VS Code: injection grammars keyed on annotation text

VS Code's TextMate grammar system allows an extension to contribute an
**injection grammar** that splices new rules into another language's
scopes. The `python-inline-source` extension (samwillis) is the canonical
Python example, and the mechanism is instructive:

- The extension contributes **one** injection grammar with
  `"injectTo": ["source.python"]`, whose rules mark string regions with
  scopes like `meta.embedded.inline.html`, and an `embeddedLanguages` map
  that tells VS Code which language each `meta.embedded.inline.*` scope is
  (18+ languages: html, django_html, jinja, css/scss/less, js/ts, sql,
  graphql, ...). The `embeddedLanguages` mapping only affects basic editor
  behaviors in the region (bracket matching, comment toggling, snippets
  context); it grants no intelligence.
- Detection is **textual**: the grammar's regexes key off the annotation
  name written before the string (`my_str: html = """..."""`). It is not a
  real Python parse and does not resolve the `Annotated` metadata; any
  annotation spelled `html` triggers it, which is also why the companion
  `sourcetypes` package (PEP 593 `Annotated[str, ...]` aliases) is
  convenient but not required. (Note: `docs/design/source_languages.md:293`
  describes this extension as parsing the Python AST; the verified
  mechanism is TextMate regex matching on the annotation text.)
- The upstream extension is barely maintained (7 commits); the ecosystem
  runs on forks. The citry maintainer publishes one,
  `jurooravec.python-inline-source-2` (v0.0.4, last updated 2024-10-17,
  adds django-html and friends), and another fork (`chrx.python-inline-3`)
  also circulates. Fragile, fork-driven maintenance is part of the lesson.

### 7.2 PyCharm: comment-driven injections

PyCharm's equivalent is native language injection (section 5.2): a
`# language=HTML` comment before the string, or persistent
settings/XML-pattern rules, with `prefix` / `suffix` to make fragments
valid. Unlike the VS Code grammar trick, PyCharm's injection produces a
real parsed fragment, so the injected language's own completion and
inspections work inside the string (e.g. CSS completion in an injected CSS
string). What no stock injection can provide is *citry* semantics, because
citry-HTML is not a language PyCharm knows; that requires a citry plugin
defining the language or an LSP hookup.

### 7.3 The markers do not agree

The two ecosystems chose incompatible markers (type-annotation text vs a
`# language=` comment), so there is no portable way to label a string's
language today. This was already a deciding argument against the typed
string alias route (`docs/design/source_languages.md:128-133`), and this
sweep confirms it: a marker convention buys one editor at a time, and only
for coloring. citry's `template` / `js` / `css` class attributes are
themselves the marker; a citry-aware tool needs no extra labeling
convention at all.

---

## 8. tailwindcss-intellisense: prior art for completion inside arbitrary strings

Tailwind's editor tooling is the strongest existing proof that a
**separate, attach-to-the-host-language language server** can deliver
useful completion inside strings the host language server knows nothing
about.

- It ships `tailwindcss-language-server` inside the VS Code extension (and
  the same server is reused by Neovim and other LSP clients). It activates
  on many host languages and completes utility classes inside `class`-like
  attributes by default.
- Two settings extend where it looks: `tailwindCSS.includeLanguages` maps
  extra language ids onto ones it understands (users map `python` to
  `html` to get completions in Python files), and
  `tailwindCSS.experimental.classRegex` accepts custom regexes that mark
  arbitrary string contexts as class lists (needed for `clsx`, `cva`,
  etc.; a community repo curates patterns per library).
- The costs are documented in its own tracker: `classRegex` has a long bug
  tail (e.g. issues #716, #946: patterns that complete but do not hover,
  regex edge cases), and JetBrains had to reimplement the same
  functionality separately with its own parity gaps (YouTrack WEB-48505).

Lessons: (a) the attach-a-second-LSP pattern works, ships to millions of
users, and coexists with Pylance without any integration between them;
(b) regex-configured extraction of "which string is mine" is exactly the
approximation citry can avoid, because citry's strings sit on known class
attributes that a real Python parse (or citry's own component discovery)
identifies precisely.

---

## 9. django-components editor tooling in the wild

citry was forked from django-components, so its users' current experience
is the baseline citry improves on.

- The official django-components docs recommend, for VS Code: annotate
  inline strings with `types.django_html` / `types.js` / `types.css` and
  install the "Python Inline Source Syntax Highlighting" extension
  (section 7.1). For JetBrains IDEs: `# language=HTML` / `CSS` / `JS`
  comments, no annotation aliases needed.
- The docs state the limitation outright: "Autocompletion / intellisense
  does not work in the inlined code", with an open call for community help
  to implement it.
- **No dedicated django-components editor extension or language server
  exists.** Marketplace searches surface only generic Django template
  extensions (e.g. `batisteo.vscode-django` for snippets and template
  highlighting, `monosans.djlint` for djLint). django-components' `{%
  component %}` tags, slots, and inline strings have no tool-aware support
  anywhere.
- The adjacent tooling that does exist is docs-side, not editor-side:
  Pygments lexers for pretty code blocks. citry already has the same
  in-repo (`packages/py/pygments_citry`, the citry-HTML Pygments lexer
  used by the docs site).

The gap is total: the framework citry forked from, with a large user base,
offers highlighting-by-convention and nothing else. A citry language
server would not be catching up to django-components; it would be the
first of its kind in this family.

---

## 10. Lessons for citry

### 10.1 The embedded-in-Python-strings problem: who solved it, how

Nobody in the Python ecosystem ships semantic template intelligence inside
Python string literals today. The full solution space observed:

| Approach | Who | What it buys | Ceiling |
|---|---|---|---|
| TextMate injection grammar keyed on annotation text | python-inline-source and forks (VS Code) | Coloring only | No semantics; textual detection; fork-maintained |
| `# language=` comment injection | PyCharm IntelliLang | Coloring plus the injected language's own completion/inspections | No citry semantics; per-string manual comments; JetBrains only |
| Second language server attached to the host language | tailwindcss-intellisense, Ruff | Real completion/hover/diagnostics inside strings, coexists with Pylance | Must find its own strings; tailwind's regex config shows the brittleness of doing that textually |
| PSI injection via plugin (`LanguageInjectionContributor`) | JetBrains plugin authors | Full semantic features inside the string | JetBrains-only, separate codebase from an LSP |
| Extend the Python language server | nobody | n/a | Pylance closed, pyright refuses plugins; only typing-spec-shaped influence exists |

The composite answer for citry: **VS Code via a citry extension that ships
an injection grammar (color now) and a citry language server registered
for Python documents (semantics), and JetBrains via the LSP route first
(official LSP API or LSP4IJ) with an optional native injection plugin
later.** Every piece of that path is individually proven in the wild; no
one has assembled it for a Python component framework yet.

### 10.2 citry's structural advantages, confirmed by others' pain

- **Context resolution is the ecosystem's unsolved hard part**, and citry
  mostly does not have the problem. Django tools cannot statically know a
  template's variables, so djlsp asks users to write
  `{# type ... #}` comments, jinja-lsp scans backend directories, and
  PyCharm's resolution stays partial. In citry, the template string and
  the Python that feeds it live on the same class, and the parser already
  emits `used_variables` / `introduced_variables` with positions
  (`crates/citry_template_parser/src/ast.rs:274`,
  `crates/citry_template_parser/src/ast.rs:520`). "What exists here" is
  local static analysis, not whole-project archaeology. This is the
  feature to lead with, because no competitor can match it structurally.
- **Finding the strings is exact, not regex.** Tailwind's `classRegex`
  bug tail is the cost of textual extraction. citry's templates sit on
  known attributes (`template`, `js`, `css`) of `Component` subclasses; a
  Python-AST scan (or the component registry itself) identifies them
  precisely, including the `*_lang` dialect declaration that
  `docs/design/source_languages.md:488-496` already plans as the single
  declaration read by all tools.
- **The Rust core is the right substrate.** The actively developed tools
  in this niche (djls, jinja-lsp, djade, djangofmt) all moved to Rust,
  and djLint's regex approach is being rewritten. citry starts with the
  real parser they each had to build. djls also proves the distribution
  story: a Rust language server shipped as PyPI wheels, runnable with
  `uvx`, plus a thin VS Code extension.

### 10.3 Constraints to design around

- **Plan for two integration surfaces, not one.** An LSP covers VS Code,
  Neovim, Helix, Zed, Sublime, and (via the LSP API or LSP4IJ) JetBrains;
  but the first-class JetBrains experience (injection into strings with
  full PSI features) requires a separate native plugin eventually.
  Sequence LSP first; the JetBrains-native plugin is a later, deliberate
  second codebase, and PyCharm's paid-tier Django support shows JetBrains
  will not build it for citry.
- **Do not wait for, or design against, Pylance.** There is no plugin
  surface and none is coming; coexistence as a second server is the
  pattern. Use the Python extension's environments API to find the
  interpreter instead of reinventing djlsp's venv/Docker probing.
- **Keep "run the user's project" optional.** djlsp's introspection
  breaks when the project does not import cleanly. citry's component
  discovery can start from static analysis of component classes and treat
  executing user code (for registries, dynamic components) as an
  enhancement with a graceful fallback.
- **Formatter and linter are separate deliverables with proven demand**
  (djLint's adoption, djade, djangofmt), already filed as #22 and #23
  (`docs/design/extensions_roadmap.md:110`). djade's scoping rule is
  worth copying: format the template language conservatively, do not try
  to own the user's HTML style on day one.
- **The no-stopgap decision holds up.** This sweep independently confirms
  what `docs/design/source_languages.md:367-377` decided: highlight-only
  marker conventions are editor-specific dead ends, and the ones in the
  wild are maintained by forks (including the citry maintainer's own).
  The one cheap earlier win consistent with that decision is a
  tree-sitter grammar for citry-HTML, which buys correct highlighting in
  tree-sitter editors and is reusable by the language server later
  (`docs/design/source_languages.md:402-417`).

---

## Sources

All URLs accessed 2026-07-07.

Django template language servers:

- django-template-lsp repository: <https://github.com/fourdigits/django-template-lsp>
- django-template-lsp VS Code extension: <https://marketplace.visualstudio.com/items?itemName=FourDigits.djlsp>
- PyGrunn 2025 talk notes on django-template-lsp (Kees Hink, via Reinout van Rees): <https://reinout.vanrees.org/weblog/2025/05/16/3-django-template-lsp.html>
- django-language-server repository: <https://github.com/joshuadavidthomas/django-language-server>
- django-language-server docs: <https://djls.joshthomas.dev/>
- django-language-server on PyPI: <https://pypi.org/project/django-language-server/>

Linters and formatters:

- djLint repository: <https://github.com/djlint/djLint>
- djLint on PyPI (v1.40.3, 2026-07-04): <https://pypi.org/project/djlint/>
- djLint VS Code extension: <https://github.com/djlint/djlint-vscode>
- djade announcement (Adam Johnson, 2024-09-26): <https://adamj.eu/tech/2024/09/26/django-introducing-djade/>
- djade repository: <https://github.com/adamchainz/djade>
- djangofmt repository: <https://github.com/UnknownPlatypus/djangofmt>
- Django Packages template-linters grid: <https://djangopackages.org/grids/g/template-linters/>

jinja-lsp:

- jinja-lsp repository: <https://github.com/uros-5/jinja-lsp>
- jinja-lsp on crates.io: <https://crates.io/crates/jinja-lsp>

PyCharm and the IntelliJ platform:

- PyCharm Django support: <https://www.jetbrains.com/help/pycharm/django-support7.html>
- PyCharm template languages configuration: <https://www.jetbrains.com/help/pycharm/template-languages.html>
- PyCharm Django templates: <https://www.jetbrains.com/help/pycharm/templates.html>
- PyCharm language injections (user-level): <https://www.jetbrains.com/help/pycharm/using-language-injections.html>
- IntelliJ Platform SDK, language injection (contributor/performer/MultiHostInjector, IntelliLang XML): <https://plugins.jetbrains.com/docs/intellij/language-injection.html>
- JetBrains LSP API for plugin developers (2023.2, paid IDEs): <https://blog.jetbrains.com/platform/2023/07/lsp-for-plugin-developers/>
- JetBrains LSP API available to all IntelliJ IDEA users (2025.2/2025.3): <https://blog.jetbrains.com/platform/2025/09/the-lsp-api-is-now-available-to-all-intellij-idea-users-and-plugin-developers/>
- LSP4IJ plugin (Red Hat): <https://plugins.jetbrains.com/plugin/23257-lsp4ij>

VS Code, Pylance, pyright:

- Pylance release repo (closed source; contribute via pyright): <https://github.com/microsoft/pylance-release>
- pyright "Plugins?" issue #607 (no plugin support): <https://github.com/microsoft/pyright/issues/607>
- pydantic's VS Code support via typing spec (`dataclass_transform`): <https://docs.pydantic.dev/latest/integrations/visual_studio_code/>
- basedpyright (open fork with Pylance features): <https://docs.basedpyright.com/>
- ty, Astral's type checker and language server: <https://astral.sh/blog/ty>
- VS Code embedded languages guide (language services vs request forwarding): <https://code.visualstudio.com/api/language-extensions/embedded-languages>
- VS Code syntax highlight guide (injection grammars, embeddedLanguages): <https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide>

Highlighting inside Python strings:

- python-inline-source repository (sourcetypes + VS Code extension): <https://github.com/samwillis/python-inline-source>
- python-inline-source extension manifest (injectTo source.python, embeddedLanguages map): <https://raw.githubusercontent.com/samwillis/python-inline-source/main/vscode-python-inline-source/package.json>
- Maintainer's fork on the marketplace (v0.0.4, 2024-10-17): <https://marketplace.visualstudio.com/items?itemName=jurooravec.python-inline-source-2>
- Another fork ("Python Inline Source Syntax Highlighting 3"): <https://marketplace.visualstudio.com/items?itemName=chrx.python-inline-3>

tailwindcss-intellisense:

- classRegex discussion (custom class name completion contexts): <https://github.com/tailwindlabs/tailwindcss/discussions/7554>
- classRegex bug reports: <https://github.com/tailwindlabs/tailwindcss-intellisense/issues/716>, <https://github.com/tailwindlabs/tailwindcss-intellisense/issues/946>
- Community regex pattern list: <https://github.com/paolotiu/tailwind-intellisense-regex-list>
- JetBrains parity request for classRegex: <https://youtrack.jetbrains.com/issue/WEB-48505/Tailwind-CSS-regex-support-custom-class-name-completion-contexts>

django-components:

- Single-file components docs (highlighting recommendations, intellisense limitation): <https://django-components.github.io/django-components/latest/concepts/fundamentals/single_file_components/>
- Generic Django VS Code extension (baseline, not component-aware): <https://marketplace.visualstudio.com/items?itemName=batisteo.vscode-django>
