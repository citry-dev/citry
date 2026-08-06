# Citry editor syntax fixtures

`template.json` is the shared behavior corpus for syntax highlighters. It
describes source text and the language role expected at selected substrings,
without naming Pygments tokens or TextMate scopes. Each editor package maps
the portable roles to its own token or scope vocabulary.

The schema has four fields:

- `schema_version`: incremented when the fixture shape changes.
- `cases`: the ordered list of examples.
- `cases[].language`: `citry-html` for a template or `citry` for a complete
  Python component.
- `cases[].assertions`: a source substring, its one-based occurrence when the
  substring repeats, and its expected role.

Every assertion substring must occur in its case. A consumer should fail when
the selected substring is missing or has no token or scope with the stated
role. `allow_errors` marks deliberately unfinished input where best-effort
coloring is expected but error tokens are acceptable. All other cases should
highlight without error tokens.

The portable roles are `tag`, `attribute`, `python`, `javascript`, `handler`,
`css`, `comment`, and `text`. A `handler` is a Citry server-handler reference,
not a browser expression. The corpus tests behavior, not parser validation.
Parser-invalid placement is covered by parser and extension tests rather than
syntax-coloring fixtures.
