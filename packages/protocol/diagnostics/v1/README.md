# Citry diagnostic catalog v1

`catalog.json` is the source of truth for Citry-owned diagnostic codes,
human-facing message templates, trigger conditions, examples, default
severities, and documentation links. The catalog schema version is independent
from the LSP protocol version.

Each entry's `constant` is generator metadata. It names the Python, Rust, and
TypeScript constant that stores the diagnostic code, so product code imports a
generated symbol instead of repeating a raw string. It is not shown in the
public diagnostic reference.

The public reference at `/ide/diagnostics/` renders each entry for a reader
who has the diagnostic on screen. Write `summary` as the mistake and what the
reader sees, the optional `fix` as what they change, and `when` as the exact
conditions under which Citry reports it.

Run `python scripts/generate_diagnostic_catalog.py` after changing the catalog.
Repository validation rejects stale generated language bindings, duplicate or
invalid entries, and Citry-owned diagnostic codes that are absent from the
catalog.

`citry.python.*` codes are intentionally different. Citry maps those from the
pinned Python analyzer, so their suffixes and messages remain provider-owned.
`citry.typescript.*` codes work the same way for TypeScript's errors in
component JavaScript and templates: the suffix is TypeScript's error number,
such as `ts2322`, and the message is TypeScript's.
