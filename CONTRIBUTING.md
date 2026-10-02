# Contributing to Citry

Thanks for your interest in improving Citry. This file is the short version.
The full guide is the
[Development page](https://citry.dev/community/development/) on the docs
site (source:
[`docs_site/content/community/development.md`](docs_site/content/community/development.md)).
It covers the tools to install, every check, the docs preview, and how CI
and releases work. How the codebase fits together lives in
[`docs/codebase.md`](docs/codebase.md), and the rules for contributors and
AI agents are in [`CLAUDE.md`](CLAUDE.md).

## Getting set up

Install [uv](https://docs.astral.sh/uv/), Rust through
[rustup](https://rustup.rs/), Node.js (current LTS), and
[pnpm](https://pnpm.io/). Then clone with submodules and install the
packages from the repository root:

```sh
git clone --recurse-submodules https://github.com/citry-dev/citry
cd citry
uv sync --all-packages
pnpm install
```

## Running the checks

`scripts/check.py` runs the same checks as the main CI job and reports every
failure together. It only checks; it never edits your files.

```sh
# While you work: no coverage threshold, skips the slow stress tests
python scripts/check.py --profile fast

# Before a pull request: the default profile, and what CI runs
python scripts/check.py
```

Add `--reporter agent` for one JSON object you can parse. The Development
page lists the phases and shows how to run a single tool on its own.

## Making a change and opening a pull request

Add tests for new or changed behavior, add a changelog entry only when users
of the package will notice the change, and read [`CLAUDE.md`](CLAUDE.md)
before you change the template grammar, the parsed template structures, or
the compiler output. Then fill in the pull request template, make sure
`python scripts/check.py` passes, and link any related issue.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating
you agree to uphold it.
