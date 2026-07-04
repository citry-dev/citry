# Design: `pygments-citry` (Pygments lexer for Citry components) and docs-site item 1.5

**Status (2026-07-03): built (both phases); `pygments-citry` not yet published.**
This document covers a releasable Python package, `pygments-citry`, that teaches
Pygments how to syntax-highlight a Citry component: the Python class plus the
HTML, JS, and CSS embedded in its `template` / `js` / `css` string attributes.
It also covers the docs-site wiring (migration item 1.5) that loads the lexer
and switches Citry component code fences from ` ```python ` to ` ```citry `.
Phase 1 (the package) and Phase 2 (the docs-site wiring) are both implemented
and green locally; the remaining step is to configure the PyPI publisher and
tag `pygments-citry@0.1.0`.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md). For the docs-site port
this feeds into, see [`docs_site.md`](docs_site.md) (Phase 8). The upstream
equivalent is [`pygments-djc`](https://github.com/django-components/pygments-djc),
which the same author (Juro) maintains for django-components.

---

## Goal and why it is a good fit

Citry component code reads best when the reader sees the HTML, JS, and CSS
inside each component highlighted as HTML, JS, and CSS, not as one flat Python
string. A plain ` ```python ` fence renders `template = """..."""` as a dull
string literal; a Citry-aware fence colours the `<c-*>` tags, the `{{ ... }}`
interpolation, and the embedded stylesheet and script the way an editor would.

The mechanism Pygments gives us for this is a custom lexer. Ship it as its own
small package and any Pygments user (our docs, a reader's own mkdocs site, a
`pygmentize` call) gets Citry highlighting, exactly as `pygments-djc` does for
django-components.

## What already exists (prior art)

- **Upstream `pygments-djc` (v1.0.1, MIT).** A tiny setuptools package with one
  lexer, `DjangoComponentsPythonLexer(PythonLexer)`. It prepends three capture
  rules to the Python `root` state that match `template|js|css [: Type] = ("""|''')`
  and hand each triple-quoted body to an embedded sub-lexer via Pygments'
  `using()`: `template` to `HtmlDjangoLexer`, `js` to `JavascriptLexer`, `css`
  to `CssLexer`. It registers itself by writing into `pygments.lexers.LEXERS` at
  import time (aliases `djc_py` / `djc_python`), tests by asserting exact token
  streams, and publishes to PyPI on a tag with a stored API token.
- **How Pygments resolves a lexer name** (read from the installed Pygments
  source). `get_lexer_by_name("citry")` first scans the builtin `LEXERS` table,
  then falls through to `find_plugin_lexers()`, which loads any package that
  declares a `pygments.lexers` entry point. So a proper entry point is enough
  for `get_lexer_by_name` to find the lexer with no explicit import. The comment
  in `pygments-djc` citing [pygments#1096](https://github.com/pygments/pygments/issues/1096)
  is about the *builtin* table only, not the entry-point path.
- **Citry component shape.** A component is a plain Python class with multiline
  `template` / `js` / `css` string attributes (a house rule, see
  [`/CLAUDE.md`](../../CLAUDE.md)). Citry deliberately does not ship
  django-components' typed `Annotated[str, ...]` aliases, so real components use
  a plain `template = """..."""` (see [`source_languages.md`](source_languages.md)).
- **Citry template syntax** (see [`../template-syntax.md`](../template-syntax.md)
  and the grammar in
  [`../../crates/citry_template_parser/src/grammar.pest`](../../crates/citry_template_parser/src/grammar.pest)):
  HTML extended by `<c-*>` tags and `c-*` dynamic attributes, `{{ python }}`
  interpolation, `{# comment #}`, and a verbatim `<c-raw>` element. There are no
  Django `{% %}` block tags, and inside `{{ }}` the body is an ordinary Python
  expression where `|` is bitwise-or, not a template filter. This is why the
  Citry template embed cannot reuse `HtmlDjangoLexer`.
- **Docs-site status of item 1.5.** The feature inventory row
  ([`docs_site_feature_inventory.md`](docs_site_feature_inventory.md) row 1.5)
  is marked done, but that row was inherited from the django-components
  inventory and points at DJC's `import pygments_djc`. The re-verified parity
  audit ([`docs_site_parity_audit.md`](docs_site_parity_audit.md) row 1.5) and
  [`docs_site.md`](docs_site.md) Phase 8 are authoritative: for Citry the lexer
  does not exist yet, so item 1.5 is the tail of building it. A grep confirms
  no `pygments_djc` / `pygments_citry` import or dependency anywhere in
  `docs_site/` or any `pyproject.toml`.

## The two deliverables

The work splits into a package (the substance) and its docs wiring (small,
depends on the package being published).

- **Deliverable A: the `pygments-citry` package.** Buildable and releasable on
  its own, with its own tests, its slot in the repo gate, and its own PyPI
  release workflow. This is Phase 1.
- **Deliverable B: docs-site item 1.5.** Load the lexer at docs-build startup,
  switch Citry component fences to ` ```citry `, and highlight the example-card
  source with the new lexer. This is Phase 2, started only after A is on PyPI.

## Deliverable A: the `pygments-citry` package

### Identity and layout

- Path `packages/py/pygments_citry/`, flat layout to match the repo's existing
  `citry` and `citry_core` packages. PyPI name `pygments-citry`, import name
  `pygments_citry`.
- Pure Python, so it mirrors [`packages/py/citry`](../../packages/py/citry)
  (setuptools backend), not the maturin-backed `citry_core`.
- `requires-python = ">=3.10, <4.0"` (the Citry family floor), MIT license.
- One runtime dependency, `pygments>=2.15`, with no upper bound. The docs
  environment keeps its own `pygments<2.21` ceiling (it guards an unrelated
  pymdownx quirk, see the root `pyproject.toml` `docs` extra); a floor-only
  spec here resolves cleanly against that ceiling.

```
packages/py/pygments_citry/
  pyproject.toml
  README.md
  CHANGELOG.md
  pygments_citry/
    __init__.py        # public re-export + lexer registration
    lexers.py          # CitryPythonLexer (the Python + embedded-string lexer)
    citry_html.py      # CitryHtmlLexer (the template sub-lexer)
    py.typed
  tests/
    test_lexers.py     # token-stream assertions for CitryPythonLexer
    test_citry_html.py # token-stream assertions for the template lexer
    test_registration.py
```

### The lexer: `CitryPythonLexer`

Mirror the `pygments-djc` structure and change exactly one embed. Subclass
`PythonLexer`; prepend three capture rules to `root` that match
`template|js|css [: Type] = ("""|''')` (the optional `: Type` branch is kept for
robustness even though Citry components rarely annotate); and delegate each
string body to a sub-lexer:

- `template` to `CitryHtmlLexer` (below), **not** `HtmlDjangoLexer`.
- `js` to Pygments' `JavascriptLexer` (unchanged; Citry `js` is plain
  JavaScript, `$onComponent(...)` is an ordinary call).
- `css` to Pygments' `CssLexer` (unchanged).

`name = "Citry Python"`, `aliases = ["citry"]`.

### The template sub-lexer: `CitryHtmlLexer`

Subclass Pygments' `HtmlLexer` and extend its states so the reader sees Citry's
own constructs, all mapped to **standard** Pygments token types so the docs
site's existing light and dark Pygments themes need no new CSS classes:

- `{{ python-expression }}` interpolation. The braces are punctuation; the
  inside is delegated to `PythonLexer`. A small callback finds the closing `}}`
  by scanning at brace depth zero and skipping Python string literals, so both
  `{{ "}}" }}` and a nested dict literal like `{{ {"a": {1: 2}} }}` end at the
  right place. This needs the `ExtendedRegexLexer` base (which threads a position
  the callback can advance) rather than a plain regex, which cannot count
  nesting.
- `{# comment #}` as a comment.
- `<c-*>` element tags. The thirteen built-in tags (`c-if`, `c-elif`, `c-else`,
  `c-for`, `c-empty`, `c-slot`, `c-fill`, `c-component`, `c-element`,
  `c-provide`, `c-css`, `c-js`, `c-raw`) are coloured as a builtin name,
  distinct from a user component such as `<c-Card>`, which stays an ordinary
  tag name. The list is a fixed vocabulary defined in
  [`../../crates/citry_template_parser/src/constants.rs`](../../crates/citry_template_parser/src/constants.rs).
- `c-*` dynamic attributes. The attribute name is an attribute; the value is a
  Python expression, delegated to `PythonLexer`. This covers `c-if="cond"`,
  `c-for="item in items"`, `c-data-active="tab['active']"`, `c-bind="{...}"`,
  and the `c-:name` literal-passthrough form.
- A built-in tag's own Python-valued attributes (`cond` on `<c-if>`, `each` on
  `<c-for>`, `is` on `<c-component>`) are delegated to `PythonLexer` too. This is
  scoped to the built-in tags via a separate tag state, so a plain HTML
  `is="..."` on an ordinary element still highlights as a string.
- Framework-style attribute names that plain `HtmlLexer` cannot tokenise
  (`@click`, `:class`, `v-model`, `[style]`, `(click)`) are accepted as ordinary
  attributes with string values, so they highlight instead of erroring.
- `<c-raw>...</c-raw>` content is verbatim: the body is plain text and its
  `{{ }}` / `{# #}` / nested tags are **not** interpreted, matching the engine.

Deferred to a later version (documented, low value in docs): highlighting a
nested-template attribute value (`c-body="<>...</>"`) as HTML rather than as a
Python expression.

### Registration (belt and suspenders)

Two lexers are registered: `citry` (the full component lexer above) and
`citry-html` (the template lexer alone, for a fenced block that shows only a
template, no surrounding Python). `pygments_citry/__init__.py` registers each
two ways, because each covers a gap the other leaves:

- **A `pygments.lexers` entry point** per lexer in `pyproject.toml`
  (`citry = "pygments_citry.lexers:CitryPythonLexer"` and
  `citry-html = "pygments_citry.citry_html:CitryHtmlLexer"`). This is the
  primary, standard plugin mechanism: any environment that has the package
  installed resolves the fence through `get_lexer_by_name` with no explicit
  import.
- **An import-time write into `pygments.lexers.LEXERS`** in `__init__.py`, the
  same hook `pygments-djc` uses. This makes `import pygments_citry` a
  deterministic loader (the item-1.5 "load at startup" hook) that works even
  where entry-point metadata is unavailable, for example an editable checkout
  whose plugin metadata has not been written. `get_lexer_by_name` checks the
  builtin table first, so this path takes precedence once the package is
  imported; the entry point is the fallback for consumers that never import it.

### Tests

Author the token-stream assertions by running the lexer on representative
inputs, observing the real output, then locking it (the observe-then-lock rule
in [`/CLAUDE.md`](../../CLAUDE.md); a throwaway harness captures the output and
is deleted). Cover: each embed alone (template, js, css); a full component
class; `<c-*>` built-in tags versus a user component; `c-*` attributes with
Python values; `{{ }}` interpolation including the `{{ "}}" }}` string case;
`{# #}`; `<c-raw>` verbatim; the triple-single-quote form; and that
`get_lexer_by_name("citry")` resolves after import.

### Repo wiring

The uv workspace picks up `packages/py/*` automatically, but several gate
inputs are explicit lists that must be extended or the gate fails:

- `.github/dependabot.yml`: a `pip` entry for `packages/py/pygments_citry` (the
  `dependabot` validator fails without it).
- Root `pyproject.toml`: add `pygments_citry` to `[tool.ruff.lint.isort]`
  `known-first-party`, to `[tool.coverage.run]` `source`, and its tests dir to
  `[tool.pytest.ini_options]` `testpaths`; add a `[[tool.mypy.overrides]]`
  `module = "pygments_citry.*"` with `disallow_untyped_defs` to hold the public
  package to the strict bar (as `citry_core` is held).
- `scripts/check.py`: add `packages/py/pygments_citry/pygments_citry` to the
  mypy argument list (mypy is not auto-discovering).
- `uv lock`, and commit `uv.lock` (CI syncs with `--locked`).

The combined coverage gate is `fail_under = 92`, measured across every sourced
package, so the lexer's tests must keep its own coverage above that or they drag
the whole gate down.

The changelog is a per-package `CHANGELOG.md`, following the `citry_core`
precedent, which fits a package versioned independently of the root.

### Release

A new `.github/workflows/py--pygments-citry--publish.yml`, cloned from the
pure-Python `py--citry--publish.yml`: it triggers on a `pygments-citry@<version>`
tag, verifies the tag matches the pyproject version, builds the sdist and wheel
with `uv build --package pygments-citry`, smoke-tests the built wheel in a clean
environment (install it, then assert `get_lexer_by_name("citry")` resolves and
highlights a sample), and publishes with PyPI Trusted Publishing (OIDC, the
`pypi` environment) plus a build-provenance attestation and a generated GitHub
release. The first tag is `pygments-citry@0.1.0`.

One-time, off-repo: configure a PyPI pending publisher for project
`pygments-citry`, repo `citry-dev/citry`, workflow file
`py--pygments-citry--publish.yml`, environment `pypi`.

## Deliverable B: docs-site item 1.5 (built)

Built against the workspace member (no publish needed for the in-repo docs
build). What landed:

1. `pygments-citry` is in the root `pyproject.toml` `docs` extra and in
   `[tool.uv.sources]` (`workspace = true`), so in-repo builds use the workspace
   member rather than PyPI.
2. The lexer loads at docs-build startup: `import pygments_citry` at the top of
   [`../../docs_site/pipeline.py`](../../docs_site/pipeline.py), the single
   chokepoint every build, serve, and build-check path funnels through.
3. The 116 Citry component-class code fences across 31 content pages were
   switched from ` ```python ` to ` ```citry ` in one pass (the 77 non-component
   Python fences and the template-only fragments were left alone). A new
   [`../../docs_site/guards/component_fence.py`](../../docs_site/guards/component_fence.py)
   guard warns when a ` ```python ` fence contains a component class, so it is
   not silently reintroduced; the migration and the guard share one detector
   (`fence_defines_component`) built on the shared `scan_fences` scanner (which
   grew a `body` field).
4. The flat `PythonLexer` in
   [`../../docs_site/components/example_card.py`](../../docs_site/components/example_card.py)
   is now `CitryPythonLexer`, keeping `HtmlFormatter(cssclass="highlight")`.
5. The lexer-alias guard's allowlist is unchanged: the entry point makes
   `get_lexer_by_name("citry")` resolve, so the guard accepts the fence with
   real validation rather than an allowlist bypass.
6. The two affected golden snapshots (`your-first-component`, `control-flow`)
   were regenerated; a `component_fence` guard test covers the new guard.
7. The parity audit row 1.5 and the Phase 8 line are updated to done.

The one deferred nicety: a template-only fragment (a bare `template = """..."""`
with no class, as in `error-boundaries.md`) stays ` ```python `, because it is a
fragment, not a component definition; re-tagging those is a judgment call left
for later.

## Sequencing and done criteria

- **Phase 1 (this document's build):** package skeleton, the lexer, the tests,
  the repo wiring, the release workflow. Done when `python scripts/check.py`
  passes and `pip install pygments-citry` then
  `python -c "from pygments.lexers import get_lexer_by_name; get_lexer_by_name('citry')"`
  works from a clean environment. Publish `pygments-citry@0.1.0`.
- **Phase 2 (item 1.5):** the seven steps above. Done when ` ```citry ` fences
  highlight, example cards show embedded markup, the build-check and snapshots
  are green, and the inventory row is corrected.

## What would falsify the design

- **Entry-point discovery in the editable workspace.** If the workspace
  member's entry-point metadata is not written, `get_lexer_by_name("citry")`
  fails in-repo. The import-time `LEXERS` write plus the explicit
  `import pygments_citry` loader are the insurance, and are the first thing to
  verify in Phase 2. Symptom to watch for: the lexer-alias guard reporting
  `Unknown code-fence language: 'citry'` while the dependency is installed.
- **The `{{ }}` boundary.** Handled by a brace-counting, string-aware callback
  (on the `ExtendedRegexLexer` base), so `{{ "}}" }}` and `{{ {"a": {1: 2}} }}`
  both end at the right place. The remaining edge is nesting deeper than the
  scan follows or a genuinely malformed expression; either degrades to lexing
  the rest of the line as the body rather than crashing.
- **Coverage.** A large lexer with thin tests would pull combined coverage under
  92. Thorough token-stream tests are the mitigation.
