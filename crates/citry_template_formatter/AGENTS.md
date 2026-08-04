# AGENTS.md - crates/citry_template_formatter

The parser-backed formatter for authored Citry templates. Read the repository
rules in [`/CLAUDE.md`](../../CLAUDE.md) and the accepted formatter design in
[`docs/design/template_formatter.md`](../../docs/design/template_formatter.md)
before changing this crate. Parser contracts and gotchas are documented in
[`../citry_template_parser/AGENTS.md`](../citry_template_parser/AGENTS.md).

The crate has the formatter
contracts, classifiers, invariant projections, shared golden corpus,
source-preserving opening-tag printer, suppression handling, and public
`format_template()` API. The opening-tag capability is exposed through Python.
Keep formatter-owned display classification here rather than adding it to the parser.

Verify changes with:

```bash
cargo test -p citry_template_formatter
cargo clippy --no-deps -p citry_template_formatter --all-targets -- -D warnings
```
