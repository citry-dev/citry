# citry_template_formatter

A Rust crate that formats authored [Citry](../../README.md) templates. It takes
template text in and gives template text back, with the layout tidied and
everything that carries meaning left exactly as written.

It is the one formatting engine behind every Citry surface: the `citry format`
command, the Python API, the language server, and the VS Code extension all
call into this crate, so a template formats identically wherever you format it.

## What it does

```citry-html
<c-CButton  class = "primary"  disabled ></c-CButton>
```

becomes

```citry-html
<c-CButton class="primary" disabled></c-CButton>
```

It normalizes the spacing inside start tags, indents block structure, wraps
attributes that run past the preferred width, and tidies the Python inside
`{{ ... }}`:

```citry-html
<main>{{foo( 1,bar= [1,2])}}</main>
```

becomes

```citry-html
<main>{{ foo(1, bar=[1, 2]) }}</main>
```

What it will not touch: text you wrote, the bodies of `<c-raw>` blocks,
anything between suppression directives, comment text, tag spelling, your
choice of quote character, and your file's line-ending style. Whitespace stays
byte-exact wherever it could change what the page renders, which is why an
attribute value spanning several lines keeps its own line breaks even as the
tag around it is re-laid out:

```citry-html
<div
  title="first
second"
></div>
```

## Why it works off the parser

Formatting Citry with regular expressions would be guesswork, because the same
characters mean different things in different places. `{# fmt: on #}` is a real
directive in one position and ordinary text inside an attribute value, a
`<c-raw>` body, or a Python string. So this crate parses the template with
[`citry_template_parser`](../citry_template_parser/) first and edits only spans
the parse proved are safe to touch.

It needs no component registry and no application. It checks that the syntax
parses, but it never asks which component names exist, so it can format a file
on its own in an editor with nothing else loaded.

## The correctness contract

The part worth understanding before changing anything here: the formatter does
not trust its own output. Every call formats the template, then tries to prove
the result is sound, and returns an error rather than text it cannot vouch for.

`format` in [`src/formatter.rs`](src/formatter.rs) checks all of these:

1. **The edit plan is deterministic.** It formats a second time from the
   original source and requires the identical result.
2. **The structural contract is unchanged.** It compares a projection of the
   template before and after, so re-laying out the markup cannot alter what the
   markup means.
3. **The result reparses.** Output that no longer parses is a bug, never a
   result.
4. **Comments survive.** It fingerprints the comment inventory on both sides
   and requires a match.
5. **Protected bytes survive.** Suppressed ranges and verbatim bodies get their
   own fingerprints, compared the same way.
6. **Formatting is idempotent.** It formats its own output and requires no
   further change, so running the formatter twice can never drift.

A failure in any of these raises a `FormatError` describing which invariant
broke. When you change formatting behavior, expect these checks to be what
catches the mistake, and treat a triggered invariant as a real defect rather
than a check to relax.

## Public API

```rust
use citry_template_formatter::{format_template, FormatError};

let tidy: String = format_template("<div  class = \"x\" ></div>")?;
```

`format_template` is the whole structural operation. On invalid syntax, a
malformed directive, or a failed invariant it returns a `FormatError`, whose
`kind` distinguishes the cases and whose range points at the offending bytes.

Python expressions are formatted in-process by a pinned Ruff, whose exact
identity is published as `PYTHON_EXPRESSION_PROVIDER` so callers can record
which provider produced a result.

JavaScript and CSS work differently, because this crate does not format either
language itself. `prepare_embedded_format` reports the regions it found and
what it needs, the caller formats those with whatever provider it has, and
`finish_embedded_format` validates the returned text and composes it back in.
Results that are stale, duplicated, missing, or otherwise unsafe are rejected
rather than pasted in.

## Suppression directives

Three comment directives control the formatter, matched on exact text:

```citry-html
{# fmt: off #}   keep everything as written from here
{# fmt: on #}    resume formatting
{# fmt: skip #}  leave just the next node, expression, or text alone
```

`fmt: off` and `fmt: on` nest according to the scope they appear in, and
mismatched pairs are an error rather than a silently ignored comment. The
directive text only counts where a comment is a comment, so the same characters
inside an attribute value, a `<c-raw>` body, or a Python string stay content.

## Where it is used

| Surface | Entry point |
|---|---|
| Python | `citry_core.template_formatter.format_template()` |
| Command line | `citry format` (write, check, and diff, with no app to load) |
| Language server | `citry-lsp`, for standalone templates and for templates written inside Python files |
| VS Code | formatting for `citry-html`, two commands, and an opt-in action on save |

Citry's Python analysis layer locates inline `template` / `js` / `css`
literals in component source and rewrites them in place, which is how a
component file gets formatted without disturbing the Python around it.

## Navigating the code

Start at [`src/lib.rs`](src/lib.rs) for the public surface, then
[`src/formatter.rs`](src/formatter.rs) for the pipeline and the invariant
checks above. From there:

| Module | What lives there |
|---|---|
| `source.rs` | The document model. Spans, and the fingerprints the invariants compare. |
| `printer.rs` | Turns the model into an `EditPlan` of byte edits and applies it. Formatting is expressed as edits to the original text, never as a re-render from the AST, which is how untouched bytes stay untouched. |
| `html.rs` | Which elements are block or inline, and where whitespace is meaningful. |
| `layout.rs` | Analyzes the rendered edges of each element so the printer knows which gaps are safe to change. |
| `projection.rs` | Builds the structural projection that invariant 2 compares. |
| `suppression.rs` | Parses the directives and marks protected ranges. |
| `comments.rs` | Decides which node a comment belongs to, so it moves with it. |
| `python.rs` | The Ruff adapters for expressions, `c-for` clauses, and the provider identity. |
| `embedded.rs` | The two-pass JavaScript and CSS handoff. |
| `newline.rs` | Detects the file's line-ending style and restores it. |
| `error.rs` | `FormatError` and `FormatErrorKind`. |
| `corpus.rs` | Test-only. Loads and validates the shared fixture corpus. |

## Development

```bash
cargo test -p citry_template_formatter
cargo clippy --no-deps -p citry_template_formatter --all-targets -- -D warnings
```

### The fixture corpus

Behavior is pinned by a shared corpus under
[`tests/fixtures/v1/`](tests/fixtures/v1/), driven by
[`index.json`](tests/fixtures/v1/index.json). Each case names an input file, the
expected output, the capability and category it belongs to, and the features it
covers. Files are compared byte for byte, so a stray trailing newline is a
failure.

To add a case, write the `.input.citry-html` and `.expected.citry-html` pair in
the category directory that fits, then register it in `index.json`. Author the
expected file by running the formatter and reading the real output rather than
hand-writing what it ought to be; the corpus is a record of behavior, so an
expected file written from imagination pins a fiction.

`index.json` also records `python_expression_provider`. Because Ruff's output
is part of the expected bytes, changing the pin means the expressions in the
corpus change with it: update the pin, re-observe the affected expected files,
and check the diff is only what the new Ruff does differently.

Note that the fixtures are excluded from `ruff` in the root
[`pyproject.toml`](../../pyproject.toml), because several of them deliberately
contain invalid or noncanonical Python.

### Things that are easy to get wrong

- **`c-fill data` is Citry's own grammar, not Python.** It looks like a Python
  expression and is not one. Sending it to Ruff produces confidently wrong
  output, so it is formatted by Citry's own code.
- **Display and whitespace classification belongs here, not in the parser.**
  The parser describes what the template says; which elements are inline and
  where whitespace matters is a formatting question, and adding it to the
  parser would put a formatting decision in everyone else's contract.
- **Whitespace changes cascade.** Editing one gap can change the column of
  everything after it, and so whether the next element still fits on one line.
  The printer runs a pass per editable item and then checks for a fixed point,
  which is also why idempotence is one of the invariants rather than an
  assumption.

## Further reading

- [`docs/design/template_formatter.md`](../../docs/design/template_formatter.md)
  is the accepted design: the correctness contract in full, the whitespace
  model, comment association, the suppression rules, the embedded-language
  boundary, and how component assets inside Python files are rewritten.
- [`AGENTS.md`](AGENTS.md) is the short orientation for agents working here.
- [`citry_template_parser`](../citry_template_parser/) is the parser this crate
  is built on; its README covers the template syntax and the AST.
