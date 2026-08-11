# I18n source and rich-message spike environment

## Purpose

This is a disposable design probe. It tests selected i18n runtime mechanisms
against the current Citry runtime without choosing a production message or
formatting backend.

## Reproduction

First rebuild the local PyO3 extension from the checked-out Rust sources:

```sh
cd packages/py/citry_core
uv run --frozen maturin develop
cd ../../..
```

Then run the probe from the repository root:

```sh
uv run --isolated --no-project \
  --with-requirements docs/design/i18n_research/source-spike-requirements.txt \
  python docs/design/i18n_research/run_catalog_and_rich_message_spike.py
```

The runner imports Citry and Citry Core from their in-tree package directories.
Its isolated environment contains exactly the four externally installed
versions in
[source-spike-requirements.txt](source-spike-requirements.txt); the fifth
distribution entry is Citry's in-tree package metadata. The runner rejects any
other distribution inventory. The requirements are exact version pins rather
than hash-enforced artifacts.

Every proof gate is an always-on check. The runner parses its own Python AST and
rejects any `assert` statement, then launches an intentional failing check under
`PYTHONOPTIMIZE=1` to show that optimization cannot remove the failure. It also
refuses a PyO3 binary older than the whitelisted native sources.

The deterministic record includes the complete distribution inventory; `uv`,
maturin, Rust, and Cargo versions; optimization level; exact extension identity;
and a path-to-SHA-256 manifest for the harness, requirements, fixtures,
production Python packages, and every local Cargo package in the locked
dependency closure, plus manifests and locks. For the vendored Ruff submodule,
the record also requires a clean checkout and captures its actual HEAD and tree
identity, even when the parent gitlink points elsewhere. It deliberately does
not record the parent repository's Git HEAD: this research is running in a dirty
workspace, and committing the evidence would invalidate a stored pre-commit
HEAD. The manifest verifies an available checkout byte-for-byte but does not
archive those inputs. Long-term replay requires committing or separately
archiving the manifest-matched source state.

Compare both checked evidence modes:

```sh
diff -u docs/design/i18n_research/evidence.json \
  <(uv run --isolated --no-project \
    --with-requirements docs/design/i18n_research/source-spike-requirements.txt \
    python docs/design/i18n_research/run_catalog_and_rich_message_spike.py)

PYTHONOPTIMIZE=1 diff -u docs/design/i18n_research/evidence-optimized.json \
  <(PYTHONOPTIMIZE=1 uv run --isolated --no-project \
    --with-requirements docs/design/i18n_research/source-spike-requirements.txt \
    python docs/design/i18n_research/run_catalog_and_rich_message_spike.py)
```

The two records differ only in the explicitly recorded run optimization level.
Neither command updates the repository lock or adds a production dependency.

## Scope

The probe covers:

- Fluent AST extraction of messages, attributes, variables, selectors,
  comments, and source locations;
- source-only `@param` declarations using a closed, non-evaluating Python type
  syntax;
- inline and file-backed message assets through Citry's existing pair loader;
- nested `Component.I18n.client_messages` configuration through the current
  extension mechanism;
- an ordinary Python `<c-trans>` component whose `<c-fill>` values remain
  structural while catalog and scalar text remains escaped; and
- the current V3 parser's ability to retain the ordinary component/fill shape.

It does not prove Fluent runtime selection and formatting, locale fallback,
CLDR or timezone behavior, production diagnostics, file watching, browser
artifacts, browser locale switching, or rich placeholders inside selectors,
terms, and functions.
