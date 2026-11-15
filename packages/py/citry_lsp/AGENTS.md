# AGENTS.md - packages/py/citry_lsp

The pure-Python Citry language server. It owns its dependencies, release
version, and changelog separately from the `citry` runtime package.

Read [`/CLAUDE.md`](../../../CLAUDE.md) and
[`/docs/design/ide_integration.md`](../../../docs/design/ide_integration.md)
before changing protocol or capability behavior.
Before adding a component source body, embedded language, or language island,
also follow the complete vertical checklist in
[`/docs/design/embedded_language_ide.md`](../../../docs/design/embedded_language_ide.md).

Project code must never be imported in the LSP stdio process. Keep app loading
in `citry_lsp.app_worker`, preserve the registry/static confidence boundary,
and bump the declared protocol version for incompatible client changes.

TypeScript diagnostics: `engine.type_check_projections` builds the checked
files, `citry_lsp/typescript.py` runs `tsc` and maps and filters findings,
and the server asks a client that offers it (`typeCheckClient`) through
`citry/typeCheck`. Fix a false positive in the projection types or
`citry_lsp/citry-dom.d.ts`, never by matching TypeScript's message text, which
VS Code may show in another language.

`citry check --types` reuses the editor's code through
`citry_lsp/project_check.py`: `project_documents` reads the component files
once, `typescript.check_project_types` runs `tsc`, and
`check_project_python_types` runs the editor's `semantic.semantic_diagnostics`
with one ty child. Change the shared functions, not a CLI-only copy.

When the rules in `citry/_json_wire.py` cannot type part of a `js_data()`
value, ty types it: `semantic.infer_js_data_value_types` wraps each unknown
part in `reveal_type()` in a copy of the module and stores the answers on
the `ProjectState` for that exact source. The server runs it before each
document's checks, and `check_project_python_types` runs it before the
CLI's TypeScript check, so the TypeScript projections read the answers. A
project reload copies the answers as stale ones, used until ty answers
again (`adopt_js_data_inferred_types`).

The Vue type declarations under `citry_lsp/types/` are generated and shipped
in the wheel; [`citry_lsp/types/README.md`](citry_lsp/types/README.md) says
how to regenerate them.

## Updating ty

The server runs only the exact `ty` version in `TY_VERSION`
(`citry_lsp/type_analysis.py`) and turns Python analysis off for any other
version. A `ty` update must change these together:

- the `ty==` pin in this package's `pyproject.toml`;
- `TY_VERSION` in `citry_lsp/type_analysis.py`;
- the `analysis-ty` extra in `packages/py/citry/pyproject.toml`, because the
  workspace lock holds one `ty` version;
- the expected versions in `scripts/verify_citry_lsp_distribution.py` and
  `scripts/verify_citry_distribution.py`;
- `uv.lock`, by running `uv lock`.

`test_runtime_ty_version_matches_every_declared_ty_pin` fails when
`TY_VERSION` and the two package pins disagree. Dependabot changes only the
`pyproject.toml` pins, so its `ty` pull requests need the other updates by
hand.

The part of a `citry.python.` code after the dot is ty's own rule name, so a
ty release that renames a rule changes the code users see. After raising the
pin, run the whole `citry_lsp` test suite and search the tests and the docs
for each rule name the ty release notes rename or split (for example
`git grep -n -E 'unresolved-|citry\.python\.'`), then record the rename in
`CHANGELOG.md`. Result files that record an earlier benchmark run keep the
names they recorded.

## Raising the required Citry version

The editor refuses to analyze a project whose installed Citry is older than
`MINIMUM_CITRY_VERSION` (`citry_lsp/protocol.py`), and that includes this
repository's own workspace Citry. So the floor moves only in the change
that also sets `version` in `packages/py/citry/pyproject.toml` to that
release, usually the release pull request, and these change together:

- the `citry>=` floor in this package's `pyproject.toml` (keep the `<2`
  cap beside it for all of 1.x);
- `MINIMUM_CITRY_VERSION` in `citry_lsp/protocol.py`;
- the expected `citry` entry in `scripts/verify_citry_lsp_distribution.py`,
  written as the built metadata writes it (`citry<2,>=1.0.0`).

`test_runtime_compatibility_matches_the_declared_dependency_floor` fails when
the constant and the installed requirement disagree.

The floor moves to 1.0.0 in the citry 1.0.0 release pull request, because
`citry._lsp_support` first ships in 1.0.0. After that it stays at 1.0.0 for
all of 1.x, since every citry-lsp 1.x must work with every citry 1.x. The
same pull request releases citry-lsp 1.0.0 (citry-lsp keeps the same major
version as citry, which `scripts/lsp_citry_pairs.py` relies on) and records
`packages/py/citry/tests/lsp_support_names.json` again from scratch, so it
lists what citry 1.0.0 exports.

## Importing from Citry

Import Citry's internals, and its experimental template analysis names,
from `citry._lsp_support` only. Import from `citry` itself only the covered
public names listed in `tests/test_citry_imports.py`, which fails on any
other Citry import in the package or its tests. citry's own
`test_lsp_support_module.py` keeps each name in `citry._lsp_support`
working the same way for all of 1.x.

When citry-lsp needs a Citry internal that `citry._lsp_support` does not
export yet, add it there in the same change (see `docs/codebase.md`,
"Breaking changes"). That name is missing from older citry 1.x releases,
so import it in a `try` block, set it to `None` on `ImportError`, and turn
off the feature that needs it, the way the editor stays quiet about what
it cannot check. Do not raise the `citry>=` floor for it. A test of that
feature skips itself when the name is `None`, because the release check
runs this package's tests against citry 1.0.0.

The same holds for a private class attribute or settings key that
citry-lsp reads by name: read it through a constant in
`citry._lsp_support`, such as `DEFINITION_ID_ATTRIBUTE`, not a string
literal.

Release qualification runs `scripts/lsp_citry_pairs.py`: the oldest
published citry-lsp of the major version runs its own tests against the
candidate citry, and this package's tests run against the oldest citry of
the major version.
