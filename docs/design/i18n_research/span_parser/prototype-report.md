# Fluent semantic-span Phase 0 exploration

## Outcome

Semantic source positions are not a blocker for the Citry i18n compiler, and
Citry does not need to fork `fluent-syntax` or maintain a second Fluent parser.

The crate's successful AST has no span fields, but its public parser is generic
over a `Slice` value. The probe supplies an owned `SpannedSlice` containing one
shared source string plus a half-open UTF-8 byte range. Every identifier, text
run, literal, comment line, and other source slice returned by the existing
parser then retains its exact authored range.

A small AST-aware index derives composite ranges from those positioned leaves:
the complete variable or reference including its sigil, a function call and
its arguments, nested and outer placeables, selectors, variants, attributes,
messages, and terms. This is not opportunistic global string matching. The
parser-provided leaves anchor each occurrence first, so identical text at
different positions remains distinct.

The chosen production direction is therefore:

1. parse with an owned positioned `Slice` in the Rust compiler;
2. walk the returned Fluent AST once to produce Citry's typed compiler IR and
   source-map table;
3. cache that owned IR, including its byte ranges and source revision; and
4. keep source positions out of the server and browser runtime bundles except
   where development diagnostics explicitly need them.

An upstream contribution might later make the adapter smaller or cover new
tooling use cases, but it is not required to continue Citry's implementation.
No upstream action was taken.

## What a semantic span means here

A semantic span is the half-open byte range `start..end` of one meaningful
piece of authored FTL. It is more precise than the start of the surrounding
message. For example, these are separate spans:

- `$count` as a variable reference;
- `minimumFractionDigits: 2` as one named argument;
- `NUMBER($count, minimumFractionDigits: 2)` as the complete function call;
- the selector from `$count ->` through its final variant; and
- each nested `{ ... }` placeable.

Citry stores UTF-8 byte offsets because Rust parsers and existing Citry source
spans use byte positions. Human line and column values are derived from the
same source only when a diagnostic is displayed. The range always points into
the exact catalog revision whose digest appears in the compiled artifact.

The production compiler fails closed when it cannot derive a range for a
supported node. A syntax failure keeps using upstream `ParserError` positions
and recovered `Junk` ranges. A successful parse followed by an invalid,
out-of-bounds, overlapping, or revision-mismatched source map is an internal
compile error; Citry emits no artifact from that catalog. New upstream enum
variants also force the exhaustive Rust walker to be updated before it builds.

## Prior art and upstream state

The audit covered the released 0.12.0 parser and the current upstream main
revision pinned in the [environment](prototype-environment.md):

- [`parser::Slice`](https://github.com/projectfluent/fluent-rs/blob/b822cfe0ac5f35099ee71d3cf6f43b7c01d5fc6d/fluent-syntax/src/parser/slice.rs#L7-L10)
  is public, requires `AsRef<str> + Clone + PartialEq`, and controls every
  source slice placed in the generic AST;
- [`parser::Parser`](https://github.com/projectfluent/fluent-rs/blob/b822cfe0ac5f35099ee71d3cf6f43b7c01d5fc6d/fluent-syntax/src/parser/core.rs#L8-L15)
  tracks one byte pointer and already emits exact ranges for syntax failures;
- the [AST definitions](https://github.com/projectfluent/fluent-rs/blob/b822cfe0ac5f35099ee71d3cf6f43b7c01d5fc6d/fluent-syntax/src/ast/mod.rs#L116-L118)
  remain generic over the slice value but have no explicit span field; and
- [Python's official Fluent parser](https://projectfluent.org/python-fluent/fluent.syntax/stable/_modules/fluent/syntax/parser.html)
  has a separate `with_spans=True` mode, but
  adopting that only for positions would introduce a second parser and a new
  Python build dependency.

Upstream already tracks the exact request in
[issue 270](https://github.com/projectfluent/fluent-rs/issues/270). A maintainer
said a prototype is welcome if it does not degrade runtime performance, and
suggested a separate AST/parser or a generic design. Later
[issue 346](https://github.com/projectfluent/fluent-rs/issues/346) discussed a
feature-gated position field or parser callback and was closed as a duplicate.

If Citry later finds a real gap in the public `Slice` route, the appropriate
next step is for the maintainer of Citry to discuss or submit a design on issue
270. Codex must not open or submit that contribution autonomously.

## Probe shape

The [Rust probe](src/main.rs) implements an owned source slice with these
properties:

- every clone shares one immutable `Arc<String>`;
- each value carries its own absolute byte range;
- trimming shortens the range as well as the visible value; and
- equality compares text, not position, because `fluent-syntax` uses slice
  equality to reject duplicate named arguments.

That last rule is load-bearing. If equality included the range, two authored
arguments both named `foo` would appear unequal and the upstream duplicate
check would silently stop working.

The AST walker indexes the constructs needed by the current Citry compiler
design. Its fixture includes:

- repeated identical variables and repeated rich `Slot` variables;
- a message reference and message-attribute reference;
- a term call with a named string argument;
- `NUMBER` with a named numeric argument;
- a multiline selector and variants;
- nested placeables and an escaped Unicode spelling;
- non-ASCII source before later operations;
- attached `@param` comments;
- authored trailing spaces;
- an equivalent CRLF resource; and
- parser recovery from a duplicate named argument.

## Results

The checked [evidence](evidence.json) is `PASS_BOUNDED`.

| Gate | Result |
|---|---|
| Positioned input preserves normal AST semantics and canonical serialization | Pass |
| Repeated `$name` and `$terms_link` occurrences have distinct ranges | Pass |
| Complete function, named-argument, term-call, message-attribute, selector, and variant ranges | Pass |
| Nested and outer placeable ranges are properly nested | Pass |
| `@param` comment line and annotation ranges | Pass |
| UTF-8 byte offsets remain valid after non-ASCII text | Pass |
| Equivalent CRLF source retains correct operation ranges | Pass |
| Final text trimming stops before authored trailing whitespace | Pass |
| Duplicate named-argument behavior remains intact | Pass |
| Recovered `Junk` range equals `ParserError.slice` | Pass |

The probe indexed 23 identifiers, 11 placeables, 7 variable references, 2
message references, 2 variants, one selector, one formatter call, one term
call, and all three `@param` annotations in the fixture.

## Alternatives considered

### Add spans directly to every upstream AST node

Not selected for Citry. It would change a broad public AST and its serde and
equality surface, while the upstream maintainers have explicitly called out
runtime, memory, and maintenance costs. Citry can get the required information
without that change.

### Parse with Python `fluent.syntax` only for spans

Not selected. Its span mode is useful as an oracle, but production would have
two parsers whose accepted syntax, recovery, and releases could diverge. It
would also move part of the Rust compiler's source-of-truth work back to
Python.

### Search the raw catalog after parsing

Rejected. Repeated identifiers, nested placeables, escaped literals, comments,
and multiline selectors make global searching ambiguous. The chosen adapter
uses exact parser-produced leaf positions and only expands adjacent grammar
punctuation around a known node.

### Submit an upstream parser callback or concrete-syntax-tree API now

Deferred. Such an API may be useful to the ecosystem and issue 270 is the
right place for it, but the local proof removes it from Citry's critical path.
The current Phase 0 work should continue first and reveal whether any actual
unsupported construct remains.

## Bounded limits

This probe does not claim that its walker covers every legal Fluent AST shape.
Before production, the index must cover the complete Citry-supported Fluent
subset and reject any unindexed node. In particular, full operation generation still needs
tests for all reference/argument combinations, selector modes, source-map
composition through linking, and decoded-text transformations.

The probe also does not measure large-catalog memory, compilation latency, or
concurrency. The positioned AST is build-time/compiler state, so it adds no
browser or request-render payload by design, but compiler cost still belongs in
the full Phase 0 performance matrix.

## Decision and next work

Adopt the owned positioned `Slice` plus AST-aware index as the Phase 0
source-map route. Keep the existing open upstream issue as a possible future
collaboration point owned by the Citry maintainer.

The next production-shaped compiler extension can now port the full generated-operation
subset already proved by the compiler/linker spike, using these exact authored
ranges for emitted operations and diagnostics. Semantic spans no longer need
to precede that work as an open design choice.
