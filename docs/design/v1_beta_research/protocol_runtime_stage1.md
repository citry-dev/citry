# Protocol runtime ownership: Stage 1 evidence

**Status (2026-08-04): complete; independent review passed.**

This is the focused Stage 1 record for
[`protocol_runtime_ownership.md`](../protocol_runtime_ownership.md). It records
what was built, the deliberate limit on schema tooling, and the remaining
coverage that the runtime stages must close.

## Outcome

Stage 1 added three small pieces:

1. `packages/protocol/_tooling/` audits the Draft 2020-12 vocabulary used by
   the five schemas, inventories runtime constraints with stable JSON Pointer
   IDs, strictly reads conformance case files, and applies explicit `add`,
   `remove`, and `replace` mutations.
2. Each protocol now has `tests/conformance-cases.json`. Every case points to
   an existing valid example, names the schema constraint it tests, records
   the mutation, and records the expected issue path and category. A case may
   name a handwritten rule when protocol validation is intentionally clearer
   than the schema's enclosing error, such as an action discriminator.
3. Both private JavaScript packages read and replay the same cases. Python
   proves that each seed is valid and each mutation reaches the named schema
   constraint. A handwritten rule ties the expected runtime path to the
   changed field when the schema reports only its enclosing object. Runtime
   validators will assert the exact `ValidationIssue` during Stages 2 through
   5.

The tooling does not generate mutations. An early prototype grew to roughly
one thousand lines before it could cover the current schema vocabulary. That
crossed the design's stop condition for a general-purpose schema compiler, so
it was replaced with explicit cases and an uncovered-constraint report.

## Commands

```bash
uv run pytest -q packages/protocol/_tooling/tests
uv run python -m packages.protocol._tooling.check \
  packages/protocol/events/v1 packages/protocol/client_graph/v1
pnpm --dir packages/protocol/events/v1/js run check
pnpm --dir packages/protocol/client_graph/v1/js run check
```

The same commands are part of `python scripts/check.py` and the repository
check workflow.

## Opening coverage

The first case set is intentionally small. It establishes every boundary and
the issue categories needed for the first runtime migrations without creating
hundreds of speculative cases.

| Schema | Constraints | Covered in Stage 1 | Remaining |
|---|---:|---:|---:|
| Events call | 37 | 6 | 31 |
| Events descriptor | 24 | 3 | 21 |
| Events manifest | 49 | 2 | 47 |
| Events result | 147 | 5 | 142 |
| Client graph manifest | 213 | 11 | 202 |

`required` is counted per required member. The report excludes annotations and
schema-routing keywords such as `$ref`, `items`, and `properties`; it includes
assertions, closed-object checks, `oneOf`, and `not`. Assertions inside `if`
selectors and `not` bodies are not counted as independent rejection cases.

The Events runtime stages add cases when they migrate a field family. The
client-graph stages run and assert the six browser type cases already recorded
here, then add cases for other migrated field families. Existing invalid
corpora remain the relationship-rule coverage; they are not duplicated into
structural mutations.
