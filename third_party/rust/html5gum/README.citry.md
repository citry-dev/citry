# Citry's patched copy of `html5gum`

This directory is a locally patched copy of the upstream `html5gum` 0.8.4
crate (MIT, by Markus Unterwaditzer). It is not Citry-authored and is not a
separate hosted fork. The source came from the crates.io archive
`html5gum-0.8.4.crate`, whose SHA-256 is
`428502d3ec1742c35e015871aef742bc4722a9acfcb616b8ff79b519922e1c36`; the
upstream repository is <https://github.com/untitaker/html5gum> at commit
`d182efa7a6e315a4f38518697ba9addf3e8fc266`. Citry identifies the patched
package as `0.8.4+citry.1`.

The registry archive's `Cargo.toml.orig` is kept byte for byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when it
builds a source package. `LICENSE` is the upstream MIT license text.

## What changed and why

Relative to that archive, the Citry change is:

- `src/machine.rs`, line 1007, in the `AfterAttributeValueQuoted` state:
  `reconsume_in!(slf, c, BeforeAttributeName)?.inline_next_state(slf)`
  becomes `reconsume_in!(slf, c, BeforeAttributeName)`.
- `Cargo.toml` (and the copy's own `Cargo.lock`): the package version is `0.8.4+citry.1`, and the `include`
  list is left out, so a source package of `citry_core` carries every file
  here, this one included.

Upstream, a double-quoted attribute value followed by white space calls
the next state directly instead of returning to the tokenizer's main loop.
So a tag whose attributes are all written `name="value"` nests a few calls
per attribute, with no limit. One tag with about 50,000 of them overflows
the 8 MiB main-thread stack in a release build (about 3,000 on a 512 KiB
thread, and far fewer in a debug build), and a stack overflow aborts the
whole process. Citry reads HTML that can hold request data with html5gum,
so a page with such a tag could end the server process.

With the change, the state machine returns to its main loop after every
such attribute, as it already does after single-quoted and unquoted
values, and after a value followed directly by the next name. The tokens
and errors it produces are the same; only how deeply the calls nest
changes. `crates/citry_html_transform/tests/attribute_runs.rs` reads a tag
with 100,000 attributes on a 128 KiB stack and fails if the change is
lost.

## Keeping it up to date

The copy is updated by hand. Because it is a path dependency, cargo-deny
does not check it against the RustSec advisory database, so watch
html5gum's advisories by hand.

When upgrading html5gum, check whether the new release still nests in
that state. If it does, carry the one-line change over and bump the
`+citry.N` suffix (in `Cargo.toml` and in the version list of
`scripts/verify_citry_core_distribution.py`). If it does not, delete this
directory and its entries in the root `Cargo.toml`, `third_party/README.md`,
`packages/py/citry_core/pyproject.toml` (the uv cache keys),
`scripts/verify_citry_core_distribution.py` and
`packages/py/citry_core/tests/test_distribution_artifacts.py`, and update
the html5gum notes in `crates/citry_html_transform/AGENTS.md` and
`src/tokenizer.rs`.
