# Design: Citry template formatter

**Status (2026-08-05): accepted; implementation-order steps 1 through 8 are
complete. M1 is release-ready, M2 Python expressions are implemented, and the
initial M3 JavaScript/CSS provider integration is implemented.**
This document defines the formatter for authored Citry templates, issue
[#22](https://github.com/citry-dev/citry/issues/22). It covers the Rust
formatter core, Python source rewriting, the `citry format` command, language
server support, VS Code integration, a minimum useful Citry/HTML pretty-printer,
and later embedded-language formatting. A narrow formatter first proves the
whole integration path, but it is an internal milestone rather than the
finished first release.

Related designs are [`template_grammar.md`](template_grammar.md),
[`source_languages.md`](source_languages.md), and
[`ide_integration.md`](ide_integration.md). The existing Python discovery and
coordinate contracts live in `citry.analysis`; the parser AST lives in
`crates/citry_template_parser`. Operating rules:
[`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Decision

Citry will have one parser-backed, opinionated formatter architecture shared by
every surface:

- a new Rust crate, `crates/citry_template_formatter`, provides the pure
  template-to-template operation;
- `citry_core.template_formatter.format_template()` exposes that operation to
  Python;
- Citry's Python analysis layer safely locates and rewrites authored inline
  template literals;
- `citry format` supports write, check, and diff workflows without importing a
  `Citry` app;
- `citry-lsp` serves standalone-template formatting and a custom request for
  embedded templates in Python documents;
- the VS Code extension contributes standard formatting for `citry-html`, two
  document-oriented commands, an opt-in Citry source action on save, and
  delegation through VS Code's public JavaScript and CSS formatter command.

Implementation is staged by capability:

| Milestone | Capability | Release status |
|---|---|---|
| M0: vertical slice | Opening-tag layout plus Rust, Python, host rewrite, CLI, LSP, and VS Code integration. | Internal only. It proves every boundary but is not called a complete formatter release. |
| M1: minimum useful formatter | Full Citry/HTML structural layout, end tags, nested bodies, comments, and CSS-style whitespace sensitivity. | First releasable formatter. |
| M2: host expressions | Python expressions, `c-for` clauses, and `c-fill data` patterns through validated adapters. | Implemented with the pinned, in-process Ruff provider. |
| M3: embedded assets | JavaScript and CSS blocks and component assets through explicit language-formatter adapters; editor delegation uses immutable standalone virtual documents. | Initial expression-free implementation complete; each surface reports its active providers or selection mechanism. |

M1 is an HTML-aware Citry pretty-printer, not merely an opening-tag wrapper.
It indents ordinary block-oriented structure while preserving whitespace
exactly at inline, mixed-content, custom-component, and uncertain boundaries.
This follows the practical model used by HTML formatters: whitespace is
semantic around inline content, but formatting whitespace around default block
structure may be normalized. It does not change the compiler's whitespace
semantics.

The formatter needs no component registry. It validates syntax with the base
parser, but it does not need to know which component names or schemas are
registered. `--app` and `--static` are checker concepts and are not formatter
modes.

## 2. Goals and non-goals

### 2.1 Goals

The formatter program will:

- produce the same result through Rust, Python, CLI, LSP, and VS Code;
- be idempotent;
- format complete Citry/HTML structure, not only tag interiors;
- preserve non-whitespace text and whitespace-sensitive boundaries exactly;
- normalize only whitespace classified as structural by section 6;
- preserve expression semantic content while allowing M1 to normalize only
  `{{ ... }}` delimiter trivia; after M2 require provider-level syntax and
  comment preservation;
- preserve comments exactly once and attach them deterministically for layout
  decisions;
- preserve source line endings, literal delimiters, quote choices, tag-name
  spelling, attribute order, and self-closing style;
- format valid standalone Citry templates and native template attributes;
- safely rewrite direct literal `template` assignments in Python;
- extend the same safe host-rewrite contract to direct `js` and `css` literals
  at M3;
- discover statically resolvable direct `template_file` declarations during
  directory formatting;
- refuse ambiguous or non-bijective Python rewrites with an actionable reason;
- never format stale last-known-good source after the current source fails to
  parse;
- support CI through `citry format --check` and local review through
  `citry format --diff`;
- grow to Python expression, JavaScript, and CSS formatting without replacing
  the M0/M1 integration architecture.

### 2.2 Non-goals

M1 will not:

- change Citry's compiler or runtime whitespace behavior;
- alter non-whitespace prose, inline boundary whitespace, or uncertain custom
  component boundaries merely to reach a preferred line width;
- claim M2 Python expression formatting or M3 JavaScript/CSS formatting before
  those providers and their preservation tests exist;
- format raw regions, or treat `pre` and `textarea` content as ordinary layout;
- normalize quotation marks, tag case, component spelling, attribute order, or
  line endings;
- import an app, run discovery, initialize a registry, invoke asset hooks, or
  format transformed or compiled output;
- guess that every `.html` file in a directory is a Citry template;
- become the selected Python document formatter in VS Code;
- add `citry check --fix`;
- expose comment attachment by changing the public parser AST;
- add stdin, JSON output, or editor-specific Citry layout rules in M1.

Python expression and JavaScript/CSS formatting are staged goals, not permanent
non-goals. A missing embedded-language provider leaves that region unchanged
and is reported in capability/status output; it does not weaken the Citry/HTML
formatting result.

## 3. Prior art and current repository facts

### 3.1 In this repository

Issue #22 proposed a Rust pretty-printer and a comment-association pass. That
direction remains sound, but its example of a `{# ... #}` comment inside an
expression is no longer valid Citry syntax. Python `#` comments are accepted
inside expressions and stop at the expression delimiter; template comments
remain markup outside expressions.

The parser has three emitted element variants: node, expression, and text.
Template comments are collected as span-bearing metadata but are not emitted
as elements. HTML comments are both comment metadata and rendered `Text`.
Python comments inside expressions are expression metadata. Aggregate comment
lists can repeat a nested comment at more than one AST level, so the root
template's comments, deduplicated by source span, are the formatter's canonical
comment inventory.

The AST retains source tokens, spans, attribute order, attribute kind, inner
values, quote characters, and self-closing structure. This is sufficient for
a source-preserving document model without changing the public AST.

Nested templates in `c-*` attribute values are parsed for bindings, slots, and
comments, but their full nested AST is not retained on `HtmlAttr`. The
formatter reparses such values recursively from their source spans. It does
not expand the public `HtmlAttr` contract merely for printing.

The parser is fail-fast. A syntax error yields no partial AST suitable for a
safe format operation. Editor formatting therefore returns no edit for invalid
current source rather than falling back to an older parse.

Ordinary `TemplateElement::Text` is emitted directly by the compiler. The
compiler tests intentionally preserve whitespace before and between ordinary
HTML elements. Citry already has narrower structural exceptions: whitespace
between adjacent control-flow branches is dropped while those branches are
grouped, and a whitespace-only component body does not create an implicit
slot. The formatter treats these as current language semantics. It neither
labels ordinary preservation a parser bug nor extends the exceptions in the
compiler.

`PythonTemplateSourceMap` maps decoded parser byte ranges into Python UTF-16
coordinates. It handles prefixes, escapes, and implicit literal
concatenation, which is valuable for diagnostics. Formatting additionally
needs a reverse, lossless rewrite contract. A diagnostic map being possible
does not imply that replacing decoded text can be represented safely in the
same authored literal.

### 3.2 External formatter and editor conventions

[Prettier's HTML whitespace work](https://prettier.io/blog/2018/11/07/1.15.0.html#whitespace-sensitive-formatting)
shows why HTML-like whitespace cannot be treated as generic indentation
trivia. Prettier's default `htmlWhitespaceSensitivity="css"` respects default
CSS display behavior, while its strict and ignore modes expose the two useful
extremes in its
[current option contract](https://prettier.io/docs/options.html#html-whitespace-sensitivity).
Citry M1 adopts the CSS-style default as a fixed policy and is more
conservative for custom components and unknown tags. A later configuration
design may expose strict or ignore modes, but M1 has one result across surfaces.

The [HTML Standard's content model](https://html.spec.whatwg.org/multipage/dom.html#content-models)
says that source whitespace between elements becomes DOM `Text` nodes, even
when classified as inter-element whitespace. Its
[suggested rendering rules](https://html.spec.whatwg.org/multipage/rendering.html)
also supply the default block and inline display behavior on which CSS-style
formatting relies. Author CSS can override those defaults, so Citry cannot
promise arbitrary-CSS DOM equivalence.
`fmt: off` is the escape hatch for a known block tag deliberately styled into a
whitespace-sensitive inline context.

[Ruff's formatter CLI](https://docs.astral.sh/ruff/formatter/) establishes the
useful write-by-default plus `--check` and `--diff` command shape. Citry adopts
that workflow, not Ruff's Python layout rules.

VS Code exposes standard document formatting, format-on-save, and code actions
on save. A document can have competing formatters, and users normally select
one formatter for a language. The Citry extension therefore registers a
standard formatter only for the `citry-html` language. It does not compete
with Black, Ruff, or another provider for the whole Python document. Embedded
templates use Citry-specific commands and a source action instead. See the
[VS Code API](https://code.visualstudio.com/api/references/vscode-api),
[formatter guidance](https://code.visualstudio.com/blogs/2016/11/15/formatters-best-practices),
and
[code actions on save](https://code.visualstudio.com/docs/editing/refactoring#_code-actions-on-save).

## 4. Correctness contract

The formatter must satisfy all of these invariants before it may return
changed text:

1. The original source parses with the current Citry parser.
2. The formatted source parses with the same parser and parser options.
3. Formatting the formatted source returns the same bytes.
4. The element tree, tag spellings, attribute names, attribute order,
   self-closing choices, and static attribute values are unchanged.
5. Every `Text` token containing non-whitespace content is byte-identical and
   remains in the same structural position.
6. Every whitespace boundary classified as sensitive or verbatim by section 6
   is byte-identical. Only structural whitespace may be inserted, removed, or
   normalized.
7. In M0 every expression is exact. M1 changes only parser-accepted outer
   trivia of a short, comment-free `{{ ... }}` expression; its semantic content
   and every expression-valued attribute stay exact. M2/M3 may change a region
   only when the responsible language provider reparses it, preserves its
   syntax tree and comments under that provider's equivalence rules, and is
   itself idempotent.
8. The canonical template/HTML comment multiset, keyed by kind and source
   content, is unchanged. Provider-owned comments instead preserve normalized
   content and attachment under item 7. HTML comments are printed from `Text`,
   not a second time from comment metadata.
9. Attribute quote characters remain unchanged unless a later embedded
   provider's explicit contract requires safe re-encoding of its own value.
10. Existing newline sequences inside preserved source stay unchanged. New
   lines inserted by the formatter use the document's detected newline style.
11. A Python rewrite leaves the complete Python module parseable and changes
   only eligible template literal content ranges.

The Rust crate enforces the M0/M1 template invariants. Embedded providers add
their own equivalence checks before their edits enter the final candidate. The
Python host-rewrite layer adds item 11. Tests compare structural projections
rather than AST equality because formatting necessarily changes token
positions.

These are hard correctness conditions, not best-effort tests. If the
formatter cannot prove them for an input, it returns an error or an explicit
ineligible result and makes no edit. The exception is deliberate M1 structural
whitespace: arbitrary author CSS can make a default block element inline, so
the fixed CSS-style classifier is the documented contract rather than a claim
of byte-identical output or arbitrary-CSS DOM identity.

## 5. Core architecture

### 5.1 Rust crate

Add `crates/citry_template_formatter` with a dependency on
`citry_template_parser`. Its first public Rust entry point is intentionally
small:

```rust
pub fn format_template(source: &str) -> Result<String, FormatError>;
```

This is the M1 public contract. M0 may exercise the same signature in local
builds, but no released package promises opening-tag-only behavior.

The crate owns four internal stages:

1. parse the current source;
2. build a source-preserving document model, canonical comment map, and
   whitespace classifications;
3. print the selected M0/M1 layout capability;
4. reparse and verify the invariants before returning.

The printer uses the parser AST plus original source slices. It does not
compile or render the template. The formatter crate introduces no new PyO3
surface; it may use the parser's current dependency shape in M1.
Making the parser's Python bindings optional remains separate work unless a
supported non-Python formatter target actually requires it.

`FormatError` distinguishes at least invalid syntax, invalid UTF-8 span data,
an unsupported safe-printing case, and an internal invariant failure. Parser
diagnostic code and byte range are retained when syntax is invalid. Invariant
failure is treated as a formatter bug and never returns partially formatted
text.

### 5.2 Source-preserving document model

The internal model indexes every structural span without copying semantic
content:

- template root;
- start tag, tag name, attributes, comments, and closing delimiter;
- end tag;
- expression;
- text;
- raw region;
- recursively parsed nested template attribute value.

All leaves point into the original source. Printed content is an exact source
slice, formatter-owned structural whitespace, or a later validated
embedded-provider result. The document records why each whitespace boundary is
verbatim, sensitive, or structural so preservation review is local and
auditable.

The public parser AST remains unchanged. Formatter-only attachment,
whitespace, layout, and embedded-region types live in the formatter crate.

### 5.3 Embedded-language provider boundary

M1's Citry/HTML pass is deterministic. M2 extends `format_template()` by
default with an in-process, vendored Ruff adapter for Python expressions and a
Citry-owned `c-fill data` adapter. M3 adds an orchestration layer for selected
JavaScript and CSS providers rather than teaching the Citry printer to guess
those languages or tools.

An embedded request carries a stable region ID, a source/plan fingerprint,
language, region kind, source, base indentation, preferred width, newline
style, and enclosing delimiter constraints. A provider returns unchanged,
formatted text, unavailable, or a structured error while echoing the plan and
region identity. Citry accepts formatted text only after provider-specific
validation plus its own protected-range, delimiter, source-map, and host-parse
checks pass. A provider adapter may add parser-backed language equivalence
checks when it owns a compatible parser. The generic editor boundary cannot
manufacture such a proof from VS Code's `TextEdit[]` result, so JavaScript/CSS
semantic preservation remains part of the selected formatter provider's
contract. The final Citry template or Python host is always reparsed and
rediscovered before an edit is returned.

Provider identity and version are part of the formatting capability set when
the adapter can prove them. The M1 Citry/HTML pass is byte-identical across
surfaces. Embedded output is required to match only when the same provider,
version, and effective options are selected. The CLI uses only an explicitly
configured, named adapter and reports unavailable embedded providers instead
of searching `PATH`.

VS Code 1.93 exposes no public headless API for invoking the configured
`editor.defaultFormatter` and learning its identity. The public
`vscode.executeFormatDocumentProvider` command returns edits from the first
applicable provider result in registry order and returns no provider metadata.
M3 therefore reports this editor mechanism honestly as `vscode-first-result`,
with provider identity/version unknown. It must not claim default-formatter
parity. A future formatter-specific adapter may provide stronger selection and
identity guarantees without changing the core plan/result boundary.

M2 uses vendored Ruff 0.14.10 at git pin `45bbb4cbff`, reported as
`ruff@0.14.10+45bbb4cbff`. It targets Python 3.10, preserves quote style, uses
two-space embedded continuation indentation, and accounts for the region's
remaining absolute 100-column budget. Original and result expressions must
have equivalent Ruff AST projections and normalized comments anchored to the
same neighboring tokens. Ruff suppression comments leave their expression
region unchanged. Once `{{ ... }}` uses multiline framing, later fixed-point
passes retain that framing while reformatting its Python body; this monotonic
rule prevents column-dependent wrap/unwrap cycles between adjacent
interpolations. M3 editor delegation may be asynchronous, so its embedded
requests and results form a two-pass plan rather than a synchronous Rust
callback. This also lets the server reject stale document versions before
composing edits.

### 5.4 Python binding

Expose the Rust function as:

```python
from citry_core.template_formatter import format_template

formatted: str = format_template(source)
```

The wrapper preserves the structured formatter error categories in Python and
keeps the `.pyi` stub synchronized. This is an additive `citry_core` API. The
Python wrapper performs no app discovery and has no global state.

The binding raises `TemplateFormatError`, a `ValueError` subclass, for an
invalid or unformattable template. It exposes a stable string `code`, message,
and optional parser diagnostic and UTF-8 byte range. Python host-rewrite
eligibility is reported by the higher-level Citry adapter rather than this
pure string API.

## 6. Formatter stages and layout rules

M0 and M1 use fixed rules across every surface. They do not accept line-width,
indentation, quote, or whitespace-sensitivity configuration. A fixed contract
keeps the vertical slice honest and the first useful release reproducible.

The constants are:

- maximum preferred line width: 100 Unicode scalar values;
- indentation per structural nesting level: two spaces;
- indentation characters inserted by Citry: spaces;
- inserted newline: the first newline sequence found in the document, falling
  back to `\n` for a single-line document;
- HTML whitespace sensitivity: CSS-style, with unknown and component tags
  treated conservatively as inline/sensitive.

The width is a preference, not permission to rewrite sensitive content. An
unbreakable token or group longer than the limit remains intact.

### 6.1 M0 vertical slice

M0 formats only opening and self-closing tags. It exists to prove the complete
Rust-to-editor path before the more involved body printer lands. It:

- removes whitespace around `=` while preserving attribute name, order, value,
  quote character, and bare-attribute form;
- separates attributes with one space when the tag fits;
- prints one attribute or direct tag-internal template comment per continuation
  line when the tag does not fit;
- preserves `/>` versus `>`;
- reparses and verifies the result.

The one-line fit calculation covers the resulting physical line through an
immediately adjacent empty-element end tag: the unchanged prefix before the
opening `<`, the canonical opening tag, and an adjacent `</name>` when present.
This means `<div ...></div>` wraps when its complete empty-element spelling
takes the line over the preferred width. Unrelated later source is not counted
because wrapping the current opening tag cannot shorten that source; general
sibling layout belongs to M1. Width is counted in Unicode scalar values, like
the document-wide constant above.

A canonical opening tag stays on one line when it fits, none of its items is
itself multiline, and a tag with multiple items has no individual item longer
than half the preferred line width. The per-item limit keeps a long structured
value readable beside shorter attributes even when their combined line is just
under the outer limit. Direct tag-internal template comments participate in
that decision exactly like attributes, so a short comment may remain inline.
When one item requires multiline layout, every attribute and direct comment
gets one continuation line, indented two spaces beyond the tag's source
column, and the closing `>` or `/>` begins a new line at the tag's source
column.

When a start tag becomes multiline inside a structural parent, M0 also
normalizes the immediate structural gaps needed to put the tag's opening `<`
on its own line and keep a following parent end tag from sharing the child's
line. It never does this at a sensitive, component, root-margin, verbatim, or
suppressed boundary. An empty element's end tag may still follow the start-tag
delimiter directly, as in `></div>`. This narrow surrounding-line rule is part
of opening-tag layout; general body and end-tag layout remains M1 work.

Each block child owns only its leading structural gap. A child owns its trailing
gap only when it is the last significant child and that gap leads directly to
the parent end tag. This prevents adjacent multiline siblings from planning
overlapping edits or assigning the next sibling the parent's indentation.
Shorthand control-flow nodes remain sensitive in this stage because they may
render no outer edge. For a child with an owned leading structural gap, width
is measured at its eventual parent-relative column before edits are planned; a
tag that fits there does not wrap temporarily and leave behind structural
newlines after a later pass. A child that owns only the trailing gap before its
parent end tag remains at its actual source column, so both its width and its
continuation indentation use that column.

Opening tags are planned to a bounded fixed point over reparsed candidates.
This is necessary because changing an earlier tag on a physical line can alter
a later tag's source column or one-line fit. Dependencies run forward in source
order, so the editable-tag count supplies a conservative convergence bound;
exceeding it is an invariant failure and returns no output.

The semantic projection treats classifier-approved structural gaps as
equivalent for both opening-tag and structural-layout verification. Edit scope
is enforced separately: the returned candidate must exactly match a second
deterministic opening-tag plan, and that plan can emit body-gap edits only
through the ownership rules above. Thus an arbitrary structural reindent cannot
pass merely because it is semantically safe under the later M1 model.

For example:

```citry-html
<c-CButton
  class="primary"
  c-disabled="not enabled"
>
```

Apart from the narrowly activated structural gaps above, M0 leaves end tags,
body boundaries, text, and expression contents unchanged.
The CLI and editor commands may expose it in development builds so the
integration can be tested, but packages are not published and issue #22 is not
called complete at M0.

### 6.2 M1 whitespace classification

M1 classifies every gap between body items, including a gap with no authored
whitespace, before choosing line breaks. There are three classes:

| Class | Meaning | Printer permission |
|---|---|---|
| Verbatim | Whitespace belongs to raw or whitespace-preserving content, or to a suppressed range. | Preserve exact bytes. |
| Sensitive | Whitespace presence or spelling may affect inline, mixed, expression-adjacent, or unknown component output. | Preserve exact bytes and never introduce a new text boundary. |
| Structural | The gap is between known block-like structures under the fixed default-CSS model. | Normalize to the required newline and indentation, including inserting a gap that was absent. |

The classifier is deliberately local and conservative:

1. Content inside `c-raw`, `pre`, or `textarea` is verbatim. `script` and
   `style` bodies are verbatim until M3 owns them. A suppression range is
   always verbatim.
2. A gap adjacent to non-whitespace text, a template expression, a known
   phrasing/inline element, an HTML comment in mixed content, an unknown
   standard tag, a custom element, or any component invocation is sensitive.
   Every `c-*` component tag is unknown regardless of registry mode because a
   component may render inline roots, block roots, text, or different shapes
   on different renders.
   If a structural container has any direct sensitive rendered item, its body
   is treated as one mixed-content group: all of that body's gaps stay exact.
   This avoids partially reindenting a body whose local whitespace decisions
   are coupled by inline or uncertain content.
3. A gap is structural only when its parent is a known structural container
   and both rendered neighbors are known block-like HTML structures. Known
   block containers are structural containers; `select` and `optgroup` are the
   contextual exceptions that are structural for their `option`/`optgroup`
   children without becoming block-like at their own outer boundary. A missing
   neighbor at the start or end of a structural container counts as block-like.
   A document-root leading or trailing margin is structural only when authored
   whitespace already exists; the printer never creates a new root margin.
4. `c-if`, `c-elif`, `c-else`, `c-for`, and `c-empty` are transparent for
   classification. Their rendered edge kind is derived from the first or last
   possible descendant of every branch. If branches disagree or an edge can be
   empty, the result is sensitive.
   A non-exhaustive physical control group keeps its containing body and its
   own direct body exact. Exhaustive all-block branch groups may participate
   in structural layout. Shorthand controls on an ordinary HTML element do
   not disable safe recursive layout inside that element.
5. `c-fill`, `c-slot`, `c-component`, `c-element`, and user component tags have
   sensitive outer edges. Formatting may still recurse into their bodies.
   The exact lowercase `c-fill` is a structural body container, so authored
   gaps around known block-like fill content receive normal child indentation;
   the other component-like bodies do not add or remove boundary whitespace.
6. HTML display lookup is ASCII case-insensitive. Citry's reserved control and
   raw tags use the parser and compiler's exact lowercase spellings, so
   `c-IF` is invalid reserved-tag spelling rather than a control tag or a
   component boundary. A normal HTML tag
   carrying exact `c-if` or `c-for` shorthand keeps the underlying HTML tag's
   display classification. `class`, `style`, and project CSS are not
   interpreted.
7. A complete HTML directive such as `<!doctype html>` or processing
   instruction is an exact-content structural pseudo-item at document root.
   The parser represents it as `Text`, so the formatter recognizes only the
   complete token shape and otherwise falls back to sensitive text.

The block-like set is a formatter-owned constant derived from the HTML
Standard's suggested user-agent display rules. Its initial families are
document containers (`html`, `head`, `body`), page and sectioning roots
(`article`, `aside`, headings, `hgroup`, `main`, `nav`, `section`), flow blocks
(`address`, `blockquote`, `dialog`, `div`, `figure`, `figcaption`, `footer`,
`form`, `header`, `hr`, `p`, `pre`, `search`), non-rendered asset containers
(`script`, `style`),
lists (`dir`, `dd`, `dl`, `dt`, `li`, `menu`, `ol`, `ul`), grouping widgets
(`details`, `summary`, `fieldset`), and table structures (`table`, `caption`,
`colgroup`, `thead`, `tbody`, `tfoot`, `tr`, `td`, `th`). `option` and
`optgroup` use their standard structural display inside `select`; `select`
itself remains a sensitive outer edge. Obsolete block elements accepted by the
parser may be listed for stable legacy formatting but are not recommended
syntax.

This set is versioned by tests. Adding or removing a member changes formatter
output and requires a changelog note. A known block styled as inline by author
CSS is outside the fixed model; use `fmt: off` around that region. Unknown tags
remain sensitive instead of guessing.

### 6.3 M1 structural printing

M1 applies M0 opening-tag rules and additionally formats complete structure:

- a block container with structural child gaps prints its opening tag,
  indented children, and closing tag on separate lines;
- nested block structure gains one indentation level at a time;
- an empty element stays on one line when its complete tag fits;
- end-tag spelling and case are preserved, while surrounding structural
  indentation is normalized;
- non-whitespace text is never reflowed or word-wrapped;
- sensitive groups remain flat at their exact boundaries even when they exceed
  the preferred width;
- a block subtree inside a sensitive component body may format internally, but
  the gaps immediately after the component start tag and before its end tag
  remain exact, except for the structural body of exact lowercase `c-fill`;

Thus ordinary block markup becomes conventional:

```citry-html
<main>
  <section>
    <h2>{{ title }}</h2>
  </section>
</main>
```

But inline and mixed content keeps its meaningful spelling:

```citry-html
<p>Hello, <strong>{{ name }}</strong>.</p>
<span>A</span><span>B</span>
<span>A</span> <span>B</span>
```

The last two lines remain observably different. M1 never turns the first into
the second or vice versa.

Python triple-quoted host literals use canonical host framing whenever the
formatted template is multiline. The opening delimiter remains on the
assignment line, template content starts on the next line at two spaces beyond
the assignment indentation, and the closing delimiter occupies its own line
at the assignment indentation. Citry nesting adds two spaces relative to that
template base. A formatted template that remains single-line retains inline
delimiter framing.

This host rule deliberately may introduce or normalize root whitespace in the
decoded template value. It is the Python-source counterpart of M1 structural
whitespace normalization. Authors whose runtime or authored-CSS contract makes
that whitespace significant can protect the template with `fmt: off`. A
literal containing an escaped whitespace character that prevents a physical
line-for-line rewrite retains its existing host framing.

### 6.4 Comments under the whitespace model

An HTML comment keeps its exact token content. It may move with structural
indentation only when both adjacent gaps are structural; in mixed content its
surrounding whitespace is sensitive. A template comment is placed from the
association map in section 7, then the affected gaps are classified again so
moving a non-rendered comment cannot accidentally manufacture inline space.

A direct tag-internal template comment remains inline when the complete
canonical line fits. If it is multiline, exceeds the width with the rest of the
line, or shares a tag with any other item that requires multiline layout, it
occupies its own continuation line together with every attribute and other
direct comment. Comments inside an attribute value belong to that protected,
provider-owned, or recursively parsed value instead.

### 6.5 Expressions and delimiters

M1 owns Citry delimiters but not expression style. For a short single-line
template expression without a Python comment, parser-accepted outer expression
whitespace is delimiter trivia: M1 trims that trivia and prints
`{{ expression }}` while preserving the semantic expression bytes. A multiline
expression, or one containing a Python `#` comment, keeps its complete inner
line structure and is treated as a sensitive group. Python comments end at the
Citry delimiter according to the parser; the formatter must not extend them to
the host line.

"Short" is deterministic: the complete canonical `{{ expression }}` token is
at most the fixed 100-scalar preferred width. A longer expression keeps its
authored delimiter trivia in M1 rather than being partially reformatted.

Expression-valued `c-*`, `c-bind`, and `#c-key` attributes keep their inner
bytes in M1. Plain browser-language attributes such as `@click` and `:class`
are static HTML attribute values to the Citry parser and also remain unchanged.

M2 adds provider-owned formatting for `{{ ... }}`, host expression attributes,
and the special `c-for` clause grammar. It must distinguish those region kinds
rather than passing `item in items` to a parser that expects an ordinary Python
expression. A `c-fill data="{...}"` value is another distinct binding-pattern
grammar with `as` aliases and mapping rest syntax; it must not be sent to an
ordinary Python-expression provider either. Python comment attachment and
AST-equivalence tests are mandatory. Client/browser expressions are not Python
and remain for M3.

A multiline `{{ ... }}` expression ends the opening-delimiter line immediately
and starts its closing delimiter on a new line. Adjacent outer markup remains
at its exact boundary, so an end tag may follow `}}` on that closing line.
Expression content starts two spaces beyond the expression's template column.
When an expression immediately follows its parent opening tag, that template
column is the parent tag's indentation rather than the physical source column
after the opening tag. Ruff's own continuation levels also use two spaces. A
multiline attribute keeps its first Python delimiter attached to the
attribute quote, aligns later Python delimiter lines with the attribute, and
indents Python contents two more spaces. Width is absolute from the containing
template line, not a fresh 100 columns per expression.

M2 owns direct `<c-fill data>` through a separate binding-pattern formatter.
It preserves whole bindings, field order, aliases, and final `**rest`, using a
compact `{field, source as target, **rest}` form when it fits. It never sends
that Citry grammar to Ruff. `c-fill fallback` remains exact.

If formatted text cannot be represented by an unquoted attribute or would
conflict with its enclosing quote delimiter, that region remains unchanged.
Verbatim bodies, alternate languages, and formatter-suppressed ranges likewise
remain exact. The final complete Citry reparse, semantic projection, and
idempotence check are still mandatory.

When that provider expands a Python collection because an item has a trailing
comment, it prints the collection delimiters and every item on separate lines,
including a trailing comma where the provider's stable style requires one. A
multiline expression-valued attribute then makes the containing opening tag
multiline under section 6.1. Until M2 is implemented, this shape is a
provider-target corpus case rather than output produced by the Citry/HTML pass.

### 6.6 Nested templates in attributes

A `c-*` attribute whose parser kind is `Template` is reparsed and formatted
recursively through the same M1 whitespace model. Fragment delimiters remain
where authored. The outer attribute quote and the nested template's existing
quote choices remain unchanged.

If recursive formatting makes a template value multiline, the containing
opening tag becomes multiline under section 6.1. The attribute begins on its
own continuation line, its nested structural content is indented one level
beyond the attribute, the closing fragment or nested end tag aligns with the
value's opening delimiter, and the outer quote remains attached to that close.
The outer tag delimiter then occupies its own line. A fragment is formatted as
a structural container for known block-like children only between margins that
were already authored inside its `<>` and `</>` delimiters. A compact fragment
does not gain new fragment-root margins.

The recursive formatter applies only when edits can be represented without
changing the outer literal's meaning. If inserted whitespace would require
value re-encoding that the current layer cannot prove safe, the nested value is
left unchanged and reported while the containing tag may still be formatted.

### 6.7 JavaScript and CSS

M3 covers both asset locations:

- `script` and `style` bodies inside a Citry template;
- direct literal `js` and `css` component attributes discovered beside
  `template`, plus statically resolvable `js_file` and `css_file` targets.

It also defines provider kinds for browser expressions in attributes where the
owning extension can prove the language. Citry event mini-languages are not
sent to a generic JavaScript formatter unless their extension explicitly
provides that mapping.

A `script` or `style` body may itself contain Citry `{{ ... }}` expressions.
A provider-specific virtual document may replace those protected regions with
same-length, context-safe inert placeholders. Provider edits may not cross a
placeholder; Citry restores each exact expression before final parsing. There
is no universal placeholder that is valid in every JavaScript or CSS lexical
context. An adapter must prove its placeholder strategy for the concrete
region; otherwise that body remains unchanged with a capability notice. The
initial M3 adapter handles expression-free bodies and deliberately reports
interpolated bodies and bodies containing Citry comment syntax unavailable.
Provider output is forbidden from introducing either `{{` or `{#`, in
addition to the enclosing raw-text end tag; the LSP sends the same delimiter
constraints so editor clients can reject the result before returning it.

Whole-body dedent/reindent is not safe inside language tokens whose raw
multiline whitespace is meaningful. The initial adapter therefore also leaves
bodies unchanged when they contain a multiline JavaScript/CSS quoted literal,
template literal, line continuation, or block comment. JavaScript hashbangs,
CSS `@charset`, and an initial CSS BOM are likewise position-sensitive and
remain unchanged. The lexical eligibility scan recognizes common JavaScript
regex-literal positions and ECMAScript U+2028/U+2029 line terminators. It
conservatively preserves ambiguous statement-position regex forms and nested
JavaScript templates rather than risk mistaking their contents for strings.
An unproven slash followed by any quote or backtick before the next line
terminator therefore makes the complete body ineligible for M3 delegation.
Line comments cannot hide an unsafe token. The same checks run on provider
output before composition; an unsafe new result is
rejected atomically. A later language-aware source map may admit these shapes
without changing their raw bytes.

For `script`, an omitted, bare, or empty `type` is classic JavaScript. The
exact HTML JavaScript MIME strings and the exact `module` value are also
delegated. MIME parameters are significant here, so a value such as
`text/javascript; charset=utf-8` remains unsupported. Import maps,
speculation rules, and data-block MIME types are never sent to a JavaScript
formatter. An omitted, bare, empty, or exact `text/css` style type is CSS.

In VS Code, Citry requests formatting through the public standalone
JavaScript/CSS provider command using one stable virtual-document identity per
region. The content provider refreshes that document between immutable pass
snapshots, so both idempotence passes retain the same URI, language, selector,
and configuration scope. Because that API cannot prove the configured default provider or its
identity, capability output names the `vscode-first-result` mechanism rather
than a fabricated provider. When no provider returns a non-empty raw result,
VS Code returns no result; Citry leaves the region unchanged and contributes a
capability notice. If VS Code instead returns an empty edit list after
minimizing a provider's non-empty raw result, Citry classifies the region as
unchanged. Batch formatting uses only an explicitly configured compatible
provider; it never searches `PATH` and
silently chooses a tool. Provider edits are mapped back only after virtual
document version, plan identity, delimiter, protected-range, and host-literal
checks pass.

The Citry/HTML printer always owns the outer `script` or `style` tag and its
indentation. Eligible embedded output is reindented as one block; the lexical
guards above exclude tokens for which that transform could alter meaningful
raw whitespace or start position.

### 6.8 Protected content

M1 preserves these contents exactly:

- raw elements and raw regions;
- `pre` and `textarea` bodies;
- `script` and `style` bodies until M3 has an active provider;
- host and browser expressions until their M2/M3 provider is active;
- JavaScript and CSS component assets until M3;
- any source-language transform other than the native Citry template language;
- every `fmt: off` or `fmt: skip` range.

Their enclosing Citry/HTML syntax may still be formatted when doing so does not
cross a protected boundary.

## 7. Comment association

Comment association is an internal formatter pass, not a parser AST change.
It exists so comment behavior is deterministic now and can support later safe
layout expansion without redesign.

The pass operates as follows:

1. Start with the root template's aggregate comments and deduplicate by exact
   source span and comment kind.
2. Exclude HTML comments from formatter metadata because their authoritative
   printable representation is `Text`.
3. Treat Python comments within expression spans as provider-owned expression
   comments. They are not markup comments and M1 leaves them in place.
4. Find the smallest structural container whose span contains each remaining
   template comment.
5. Within that container, compare the nearest preceding and following
   structural items and intervening source.
6. Attach a same-line comment after an item as trailing, a comment before the
   next item with only whitespace between as leading, and all other comments as
   dangling on the smallest container.
7. Preserve source order for multiple comments with the same attachment.

M0 consumes attachments only inside start tags. M1 may print a body comment on
a normalized line when both surrounding gaps are structural. A comment in a
sensitive or verbatim group retains its exact surrounding source. After moving
a template comment, M1 reruns gap classification before accepting the print.

The corrected issue matrix includes:

- a template comment on its own line;
- stacked template comments;
- leading, trailing, and dangling comments inside a start tag;
- template and HTML comments between block siblings and inside mixed content;
- a Python `#` comment inside `{{ ... }}` ending at `}}`;
- a Python `#` comment inside an expression-valued attribute;
- comments inside recursively parsed nested template values.

## 8. Suppression directives

M0 and every later milestone recognize three exact template-comment directives
after trimming the comment body:

```citry-html
{# fmt: off #}
{# fmt: on #}
{# fmt: skip #}
```

Directives are case-sensitive. They remain unchanged in output.

Formatting starts enabled at document root. `fmt: off` and `fmt: on` are state
transitions after their comment rather than globally paired markers. `off` is
valid only while the inherited state is enabled; another `off` while already
disabled is an error. `on` is valid only while the inherited state is disabled;
an `on` while already enabled is an error. A scope may end while disabled
without an error.

State is linear within one syntactic scope and inherited through the template
tree:

| Scope | Initial state |
|---|---|
| element start tag | the parent body state when the element begins |
| nested template attribute | the start-tag state when that attribute begins |
| element body | the parent body state when the element begins |
| element end tag | the terminal state of that element body |

A child state change does not escape back into its parent. In particular, a
start-tag transition ends at `>` and does not seed the element body; the body
inherits the parent body state independently. The body terminal state seeds
only its end tag. After the complete element, its parent resumes the state it
had when the element began. A nested template likewise restores its containing
start-tag state when the attribute ends.

This inheritance deliberately permits an enabled region inside inherited-off
source. For example, an outer `fmt: off` can keep a component invocation exact
while a nested template or body-local `fmt: on` formats the remainder of that
child scope. Effective protected ranges therefore follow owned source regions
and may contain recursively enabled holes; an outer disabled state is not
represented as one flat range across every descendant.

`fmt: off` and `fmt: on` are valid in template bodies, start tags, nested
templates, and end tags. A tag-local state ends at that tag's `>` delimiter.
End tags currently preserve their internal spelling regardless, but they still
validate inherited state so the contract remains correct when end-tag layout
grows.

Body-level `fmt: skip` protects the next meaningful direct body item: `Node`,
`Expr`, or non-whitespace `Text`. It ignores template comments and
whitespace-only `Text`. A node's protected range includes its full start tag,
body, and end tag, and descendant state changes cannot enable part of a skipped
target. A `fmt: skip` comment directly inside a start tag protects the next
attribute, ignoring intervening comments; it is an error when no attribute
follows. `fmt: skip` inside an end tag is an error because an end tag has no
formatting target. Directive-shaped text inside an expression or raw body is
ordinary content and has no formatter meaning.

Suppression ranges are established before comment reattachment or printing.
No edit may cross a protected range boundary.

`fmt: skip` protects only its target bytes, not the following body gap. A gap is
formatted or preserved according to the surrounding body scope's current
state. Disabled gaps stay exact, while enabled structural gaps around a skipped
node may still receive canonical indentation.

## 9. Formatting component assets embedded in Python

### 9.1 Eligible inline literals

The Python adapter reuses `discover_python_templates()` to find proven direct
literal `template` declarations on `Component` and `LibraryComponent`
subclasses. The first rewrite-capable subset is narrower than the diagnostic
source map:

- one contiguous string literal;
- a complete, valid Python module;
- a native Citry template (`template_lang is None`);
- a direct class-body assignment already accepted by conservative discovery;
- literal content whose decoded-to-authored mapping is one-to-one for every
  changed character and insertion boundary.

Raw and Unicode prefixes are eligible when that proof holds. F-strings,
bytes, computed values, implicit literal concatenation, and literals whose
escapes make the changed range non-bijective are ineligible in M1. The adapter
reports why rather than treating them as already
formatted.

The adapter extends discovery notices where needed so a definite component
with a direct but computed, concatenated, escaped, or alternate-language
template is reported explicitly. It does not turn an unsupported declaration
into a false clean result.

The shared additive API, exported from `citry.analysis` and `citry`, is
host-coordinate based rather than LSP-coordinate based:

```python
def format_python_templates(
    source: str,
    *,
    host_offset: int | None = None,
) -> PythonTemplateFormatResult: ...
```

`host_offset=None` selects the atomic document operation. A zero-based Python
string offset selects only the containing template. The immutable result holds
`source`, `changed_component_names`, and discovery notices. A document-scope
eligibility or template failure raises `PythonTemplateFormatError` with a
stable `code` and the relevant component notices; its candidate source is
never exposed. LSP code converts UTF-16 positions to a host offset before
calling this API. The CLI, server, and tests share this adapter rather than
implementing separate Python-literal rewriting.

The error also carries an optional absolute, half-open Python string-offset
`range`. Its optional nested parser diagnostic remains template-relative, so
consumers use the absolute range for host edits and retain the nested detail
for parser-specific reporting.

The adapter preserves the Python string prefix, delimiter kind, assignment,
and all host text outside the literal body. For multiline triple-quoted
results it canonicalizes delimiter-line placement and body indentation under
section 6.3. It does not reindent the Python class or move the assignment.

### 9.2 Safe rewrite algorithm

For one Python document:

1. parse the host with `ast.parse`;
2. discover definite template regions and notices;
3. prove rewrite eligibility for every definite region selected for this
   operation;
4. format decoded template content through the Rust core and active,
   validated M2/M3 providers;
5. encode changed content back into the existing literal without changing its
   delimiter, accepting only the structural whitespace changes owned by the
   formatter contract;
6. apply non-overlapping replacements from the end of the document backward;
7. parse the complete candidate Python document again;
8. rediscover each changed literal and assert that its decoded value is the
   formatter output;
9. return one atomic document edit only after all checks pass.

If a definite template region is invalid or ineligible, the default document
operation makes no edits to that Python file. This atomicity prevents a file
from looking fully formatted when only its easiest templates changed. An
editor's cursor-scoped command may format one eligible selected region and
report other regions only when the command explicitly targets the current
template.

### 9.3 File templates

Directory discovery may add a file only when static Python analysis proves a
direct, constant `template_file` value on a definite component class and the
path resolves relative to that declaring module. It does not consult
`citry_dirs`, inherited runtime values, registry aliases, asset hooks, or
transforms. Multiple declarations resolving to the same file are deduplicated
by normalized absolute path.

An explicitly named `.html`, `.citry`, or `.citry-html` file is treated as a
standalone Citry template because the user has supplied the scope directly.
Other extensions are a usage error in M1 rather than a language guess; M3 adds
the explicit `.js` and `.css` provider routes. Directory traversal never
assumes that arbitrary `.html` files are Citry templates.

### 9.4 M3 JavaScript and CSS host assets

The M1 `format_python_templates()` API remains template-specific and stable.
M3 adds `format_python_component_assets()` with explicit selected kinds from
`template`, `js`, and `css`. It extends conservative class-body discovery to
direct literal `js`/`css` assignments and direct constant `js_file`/`css_file`
declarations without weakening the proof that the class is a Citry component.

Inline JavaScript and CSS require one complete contiguous literal and use the
same host `ast.parse`, rediscovery, and atomic-file rules as templates. Unlike
the source-preserving template pass, the selected provider owns the complete
decoded asset, so Citry escapes its output back into the existing quote kind.
Provider CRLF and lone-CR output first normalize to logical LF. Single-quoted
hosts encode logical newlines as escapes, while triple-quoted hosts use the
Python file's physical newline. Raw literals are accepted only when the exact
provider result is representable without changing their decoded value. The
decoded asset must equal the accepted provider result after rewriting.
Document scope is atomic across all selected asset kinds; cursor scope targets
only the containing definite asset. An unavailable provider under M3
`available` mode leaves its region unchanged with a notice, while invalid
provider output or `required` mode failure makes no edit to that Python file.

## 10. CLI contract

The command shape is:

```text
citry format [PATH ...]
citry format --check [PATH ...]
citry format --diff [PATH ...]
```

With no path, the target is `.`. Paths are processed in deterministic sorted
order and normalized file paths are deduplicated across overlapping explicit
targets and discovered references. `--check` and `--diff` are mutually
exclusive.

- default mode writes changed files atomically;
- `--check` writes nothing and reports files that would change;
- `--diff` writes nothing and prints a unified diff for each changed file;
- an explicit `.py` path scans eligible inline declarations in that file;
- an explicit `.html`, `.citry`, or `.citry-html` file is parsed as one
  standalone Citry template because the user supplied its scope directly;
- another explicit extension is a usage error instead of being guessed; at M3,
  `.js` and `.css` route only to their configured provider;
- a directory scans Python files with the same rules currently documented by
  `citry.autodiscovery` (stable order, private and non-importable paths
  excluded), then adds only statically proven `template_file` targets.

An explicit directory that cannot be traversed is an error, including when a
permission failure would otherwise make discovery look like an empty clean
scan. Filesystem inspection failures for individual discovered paths remain
file-local errors and do not abort reporting for other targets.

M3 directory discovery additionally adds statically proven `js_file` and
`css_file` targets. It does not recursively claim unrelated JavaScript or CSS
files merely because they are under the requested directory.

Directory-discovered files must resolve to regular, non-symlink files inside
the requested directory after path normalization. A discovered path that
escapes that root, resolves through a symlink, or is not a regular file is an
error and is never written. An explicit file path may be outside the current
directory because the user named it directly, but a symlink is still refused
so atomic replacement cannot unexpectedly replace the link itself.

The formatter is app-independent. `citry --app module:engine format` is a
usage error and must not import the app. `--static` is not accepted. This keeps
formatting deterministic and avoids implying that registry-backed formatting
is stronger than syntax-backed formatting.

M1 has no stdin mode, formatter configuration file, JSON format,
include/exclude glob flags, or cache. Those can be added after real automation
needs establish their contracts.

M2/M3 add a printed capability line in verbose/status output, for example:

```text
citry-html@1, python-expressions:<provider>, javascript:<provider>, css:<provider>
```

M3 also adds `--embedded=off|available|required`:

- `off` runs only the Citry/HTML pass;
- `available` is the default and uses only explicitly configured batch
  providers, with notices for unavailable regions;
- `required` exits with status 2 and writes no affected file when a discovered
  embedded region lacks its configured provider.

Provider flags supplied with `off` are inert: Citry does not resolve or probe
those executables.

The first batch adapter is explicit Biome invocation:

```text
--javascript-provider biome:/absolute/path/to/native/biome
--css-provider biome:/absolute/path/to/native/biome
```

Each option authorizes that executable for the named language. Citry invokes
it without a shell and passes source over stdin. A `.js` or `.css` asset keeps
its real path as the stdin filename; a proven language asset with another
extension gets an asset-local virtual path with the required language suffix.
Citry records the probed Biome version. The adapter streams
stdout and stderr into one 8 MiB cap, applies a 15-second timeout, and
terminates the complete provider process tree on overflow, timeout, or
inherited output pipes (POSIX process groups and Windows Job Objects). Provider
input and output must be UTF-8. Relative executable paths, bare command
names, arbitrary shell strings, and implicit `PATH` lookup are rejected. The
path must identify Biome's self-contained platform-native binary. Every
interpreter script and package-manager or Windows command wrapper is rejected
because its effective dependencies cannot be isolated and fingerprinted. The
adapter uses Biome's stdin `--write` mode and never gives it a target file to
write. Additional named adapters can be added without weakening this
authority boundary.

The adapter reads and hashes the executable bytes before its version probe,
revalidates the authorized path, and runs a secured copy from a private
per-user executable-cache directory. Linux binds execution to the already-open
copy; Windows keeps a replacement-denying handle open and releases a Job-bound
launcher only after containment is established. This avoids requiring write
access beside a system executable and avoids the commonly `noexec` system temp
directory. It resolves the nearest `biome.json` or `biome.jsonc` itself and
passes an isolated copy of those exact bytes through `--config-path`. When no
configuration exists, it passes an isolated empty configuration so an ambient
file cannot appear during the formatter run. The private virtual source keeps
the same config-relative path. Editorconfig and VCS-derived options are
disabled, output is forced to LF, and `BIOME_*` environment overrides are
removed. A configuration with external `extends` or `plugins` dependencies,
including plugins inside overrides, is rejected because the initial adapter
cannot fingerprint those dependencies. Symlinked configuration files are also
rejected so config-relative source identity cannot diverge from the bytes being
hashed. Every
accepted result carries a SHA-256 invocation identity over the executable
bytes, Biome version, virtual source path, fixed arguments, and exact
configuration bytes. Verbose capability output labels Biome's effective
options as per-target rather than claiming that one workspace-wide option set
applies to every asset.

These controls close ordinary project-tree replacement races and substitution
by other OS users. Code already running as the same OS account has the same
authority as Citry itself and is not treated as a hostile sandbox boundary;
such code can interfere with any user-launched formatter process or its private
files on platforms without an executable-FD primitive.

Batch provider configuration is designed with M3 and is not inferred from
whatever executable happens to be first on `PATH`. `--check` and `--diff`
report the same capability set as write mode.

### 10.1 Results and exit status

The summary distinguishes formatted, unchanged, skipped, and errored files.
An unsupported definite template is not reported as clean.

Changed-path announcements in write and check mode go to stdout. Diff mode
keeps stdout as unified-diff output. File errors and the final four-counter
summary go to stderr in every mode. A Python file with no definite inline
template is skipped; a definite template that already matches formatter output
is unchanged.

Python files are decoded and encoded with their declared source encoding.
Standalone template files use UTF-8, with an existing UTF-8 byte-order mark
preserved. A write stages bytes beside the target, preserves its permission
bits, checks that the target identity and contents have not changed since the
read, and atomically replaces that one file. A directory-discovered
target retains its discovery-root and file identities and revalidates its
symlink-free contained route immediately before replacement. A discovered
`template_file` also retains and revalidates the declaring Python source
snapshot so a concurrent declaration change cannot authorize a stale write. If
the formatter itself rewrites that Python source first, it reruns static
discovery on the exact bytes it wrote and refreshes the snapshot only for file
targets that the rewritten declaration still proves.

Portable filesystem APIs do not provide a conditional "replace only if this
path still has snapshot X" operation. Citry therefore validates immediately
before the atomic replacement, but a non-cooperating writer in the final
validation-to-replace instruction window can still be overwritten. Here,
"atomic" means readers see either complete old bytes or complete new bytes; it
does not mean a cross-process compare-and-swap. Editors and automation should
not write the same file concurrently with batch write mode. LSP formatting is
not subject to this filesystem boundary because the versioned workspace edit
is applied by the editor.

| Exit | Meaning |
|---:|---|
| `0` | Write mode completed without errors, or check/diff found no changes. |
| `1` | Check/diff found files that would change. |
| `2` | Usage, read, parse, eligibility, invariant, or write failure occurred. |

Processing may continue after a file-local error so all targets are reported.
Writes are atomic per file, not across the whole invocation. A file with any
error is never partially rewritten. A final exit status of 2 takes precedence
over status 1.

## 11. Language server contract

### 11.1 Standalone templates

`citry-lsp` advertises standard `textDocument/formatting` only for documents
whose language is `citry-html`. Registration is dynamic with that language
selector and a relative pattern rooted at the lexical workspace URI supplied
during initialization. Preserving that URI matters when the workspace was
opened through a symlink. A global static formatting capability would let the
Citry server compete for documents it must not own.

The optional `standardFormatting` initialization option is a boolean and
defaults to `true`. A client that sets it to `false` keeps the standard route
disabled and uses `citry/formatTemplates` instead. The VS Code extension does
this because it runs one language client per workspace folder: it registers
one extension-owned `citry-html` formatter and routes that request to the
client selected by `workspace.getWorkspaceFolder`. Its per-folder middleware
also forwards synchronization and language features only through that selected
folder. This avoids competing same-extension formatter providers and keeps
nested workspace roots on one active route.

When a client does not support or declines dynamic formatting registration,
the server does not advertise a global static formatting capability. Such a
client may call the custom request below for a standalone document, or operate
without formatting; diagnostics, status, and the other existing capabilities
are unaffected.

Formatting uses the current document version and current text. Invalid source
returns no edits plus an actionable error for a manual request. It never uses
the server's `last_good` parse.

The server ignores editor `tabSize` and `insertSpaces` options in M1 because
formatter output is intentionally identical across surfaces.
It returns the smallest safe edit set, with a whole-document edit acceptable
for the first implementation if and only if the text changed.

### 11.2 Custom formatting request

Standard Python document formatting is intentionally not registered. Add a
versioned custom request in protocol v1:

```text
citry/formatTemplates
```

Its request includes the document URI, document version, and exactly one
scope:

- `document`, for every eligible template in the Python document;
- `position`, for the template containing one UTF-16 position.

Protocol v1 uses these JSON shapes:

```json
{
  "textDocument": {"uri": "file:///project/card.py", "version": 7},
  "scope": {"kind": "document"}
}
```

```json
{
  "textDocument": {"uri": "file:///project/card.py", "version": 7},
  "scope": {
    "kind": "position",
    "position": {"line": 12, "character": 18}
  }
}
```

Python documents accept both scopes. A standalone `citry-html` document accepts
only `document`; this is also the fallback for clients without dynamic
formatting registration.

The response contains a versioned `WorkspaceEdit`, an unchanged result, or a
structured refusal with the formatter category and current source range. The
server rejects a version mismatch instead of applying positions computed from
stale text.

```json
{"kind": "unchanged"}
```

```json
{
  "kind": "refused",
  "code": "citry.format.ineligible",
  "message": "the cursor is outside a definite Citry template",
  "range": null
}
```

An edit result uses `kind: "edit"` and an `edit` field containing one
`documentChanges` entry whose `textDocument` carries the requested URI and
version. Malformed request objects are invalid JSON-RPC parameters. A valid
request for a closed document or stale version receives
`citry.format.stale-document` and no edit.

The document scope follows Python file atomicity from section 9. The position
scope may edit just the containing eligible literal. Registry mode may prove
that an HTML-mode document is a Citry `template_file`; it does not change the
formatting behavior or output for selected source text.

The custom request and response schema are part of protocol v1 because the
editor integration had not been released when formatting was added. A future
incompatible change would use the existing protocol-skew status rather than
letting an older client send an unknown request.

M2 adds the active Python expression provider identity to project status but
does not change the request shape. M3 introduces client capability
`citry.embeddedFormatting` and a server-to-client request:

```text
citry/formatEmbedded
```

During a standard or custom Citry formatting request, a capable client receives
immutable virtual JavaScript/CSS pass snapshots under one stable region URI,
stable region and plan IDs, the
original document version, half-open UTF-16 protected ranges, and delimiter
constraints. It returns one explicitly classified result per region and
provider identity/version only when those values are knowable. The server
validates the echoed IDs, rejects missing, extra, duplicate, malformed, or
stale results, composes accepted results with the Citry plan, reparses the final
template and Python host, and returns one edit only if the document version is
still current. Clients without the capability receive M1/M2 formatting and an
embedded-provider notice.

This is an additive, unreleased protocol-v1 capability. Both the LSP and VS
Code extension keep `protocolVersion: 1`; capability negotiation, not a
version bump, determines whether the server may send `citry/formatEmbedded`.
The server cancels the client request after 30 seconds and returns a structured
`citry.format.provider-invalid` refusal. The VS Code client applies the same
30-second bound to each provider pass, cancels Citry's logical invocation,
discards its virtual source, and returns an error result. VS Code exposes no
cancellation token for the underlying public formatter command, so a provider
that ignores disposal may continue internally, but its late result cannot be
composed or applied.

## 12. VS Code integration

### 12.1 Commands

The extension exposes only:

```text
Citry: Format Document
Citry: Format at Cursor
```

Both call `citry/formatComponentAssets`: **Format Document** uses document
scope, while **Format at Cursor** uses position scope in Python. Position scope
selects the one direct `template`, `js`, or `css` literal body containing the
cursor. A `template_file`, `js_file`, or `css_file` path, a component method,
and unrelated Python code are not cursor regions; the command reports a
structured refusal and makes no edit. It deliberately does not turn an editor
command into an implicit cross-file operation. Users open a referenced file or
use `citry format` when they want static file-reference discovery. Standalone
JavaScript and CSS files continue to use their normal language formatter; the
Citry commands do not wrap generic JS/CSS documents.

`citry-html` is one authored template, so both commands use document scope.
The explicit commands also use document scope for an HTML-mode file that the
registry proves is a resolved `template_file`; unrelated HTML remains
ineligible. Standard formatting and format-on-save are registered only for
`citry-html`, so Citry never competes with the selected ordinary HTML
formatter. The narrower `citry/formatTemplates` protocol request remains
available to other clients but is not exposed as a VS Code command.

JavaScript/CSS delegation calls VS Code's public standalone formatting
command. In VS Code 1.93 that means the first applicable non-empty provider
result, which is not guaranteed to be `editor.defaultFormatter`; Citry reports
the `vscode-first-result` mechanism and unknown provider identity. Citry does
not apply fallback style rules. Users who need deterministic bytes use the
explicit batch adapter, and future editor-specific adapters may provide exact
default-provider selection.

The built-in CSS formatter accepts Citry's custom virtual-document scheme, but
the built-in JavaScript/TypeScript formatter does not. JavaScript formatting
therefore currently requires an installed formatter that registers for
non-file virtual documents; Prettier is the recommended compatible option.
This is a temporary editor-compatibility limitation, not a requirement of the
formatter architecture or CLI. Highlighting and editor intelligence use a
separate embedded-language route and do not depend on this formatter selector.

### 12.2 Save behavior

Standalone `citry-html` uses VS Code's standard formatter selection and
`editor.formatOnSave`:

```json
{
  "[citry-html]": {
    "editor.defaultFormatter": "citry-dev.citry",
    "editor.formatOnSave": true
  }
}
```

Python keeps the user's Python formatter and opts into Citry's independent
source action:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.format.citry": "explicit"
    }
  }
}
```

The extension contributes `source.format.citry` as a source action. It calls
the same document-scoped operation as **Citry: Format Document** and applies
the returned versioned edit.
No `citry.formatOnSave` setting duplicates VS Code's native mechanism.

At M3 the same source action advertises embedded-formatting capability, answers
the server's virtual-document requests through VS Code's public provider
command, and still applies one final atomic Python edit. A recursion guard
prevents the Citry provider from satisfying its own JavaScript/CSS request.
The Citry output channel records every region as formatted, unchanged,
unavailable, or failed and names provider identity only when it is actually
known, so format-on-save never silently suggests that all component assets
were formatted.

The server gives each callback an explicit JSON-RPC request ID. Timeout or
caller cancellation sends `$/cancelRequest`; the VS Code handler propagates
its cancellation token into the active virtual document, discards late output,
and starts no later pass or region. Under `vscode-first-result`, a client result
must keep provider identity absent or null because VS Code cannot prove it.

On-save failure does not block saving. It makes no formatter edit and records
the reason in the Citry output channel; repetitive unchanged errors are
coalesced. An explicit command also displays the concise refusal to the user.

### 12.3 File association

A catalog-resolved or statically resolved file template receives diagnostics
without changing its VS Code language mode, but standard formatting is offered
only when the document is associated with `citry-html`. The extension may
provide an association command or documentation, but it must not globally
claim all `.html` files.

## 13. Failure and diagnostic behavior

Failures use stable codes across CLI, LSP, and editor messages:

| Code | Category | Behavior |
|---|---|---|
| `citry.format.syntax` | Invalid Citry syntax | No edit; retain the nested parser diagnostic code and range. |
| `citry.format.host-syntax` | Invalid Python syntax | No Python edit; point to the host syntax failure. |
| `citry.format.ineligible` | Ineligible literal or source language | No file edit; explain the unsupported authored form. |
| `citry.format.unsupported` | Safe source-preserving print unavailable | No edit; identify the source range the current formatter cannot safely rewrite. |
| `citry.format.suppression` | Suppression directive error | No edit; identify the directive range. |
| `citry.format.provider-unavailable` | Requested embedded provider missing | Preserve that region; emit a notice, or fail an M3 `--embedded=required` file. |
| `citry.format.provider-invalid` | Embedded provider returned invalid or non-equivalent text | No affected-file edit; identify the provider and region without accepting its output. |
| `citry.format.stale-document` | Source changed during request | No edit; ask the client to retry on the current version. |
| `citry.format.invariant` | Formatter invariant failed | No edit; report an internal formatter error suitable for a bug report. |
| `citry.format.io` | Read or write failure | No affected-file write; report the path and operation. |

Formatting never repairs invalid syntax in M1. Later language providers also
receive only regions that already parse in their language. Citry never
falls back to registry-loaded, transformed, compiled, or last-known-good text,
because none of those is the current authored source the user asked to edit.

## 14. Test strategy

### 14.1 Shared golden corpus

Add input/output pairs owned by the Rust formatter and consume the same corpus
from Python, CLI, LSP, and VS Code integration tests. Lock each category before
its owning implementation step: step 1 starts with parser-level Citry template
contracts, step 3 adds Python host framing and eligibility cases, and later
provider steps add their language-owned cases. The versioned byte corpus keeps
all of them under one contract without requiring the parser-only crate to
execute host-language policy prematurely.

The VS Code client does not run the formatter a second time. LSP corpus tests
prove the request output, while the client test feeds every shared expected
result through the same versioned validation, conversion, and application
helper used by the registered formatter route and asserts byte identity.

M0/M1 cases include:

- one-line and multiline start tags;
- spaces around `=`, long attributes, and an unbreakable token beyond the
  width;
- bare, static, expression, template, event, binding, and metadata attributes;
- normal, self-closing, void, fragment, and structural Citry tags;
- lowercase and class-name component spellings;
- nested known block elements with absent, one-line, and multiline gaps;
- inline siblings with no gap, one space, and a newline gap, all kept distinct;
- mixed text, expression, inline element, and block element bodies;
- custom elements and Citry components treated as sensitive at their
  boundaries;
- transparent control-flow branches whose rendered edges agree, disagree, or
  may be empty;
- root and Python-triple-string framing indentation;
- default block tags under `fmt: off` to cover author CSS overrides;
- own-line, stacked, leading, trailing, dangling, and tag-internal template
  comments;
- HTML comments printed once in structural and mixed content;
- Python `#` comments inside both expression forms, ending at their Citry
  delimiter;
- nested template attribute values and fragments;
- fills, slots, loops, conditionals, and typed slot-data expressions;
- raw, script, style, pre, and textarea content;
- single quotes, double quotes, both Python triple-quote forms, raw prefixes,
  CRLF, Unicode, and no final newline;
- each suppression directive, inherited scope transition, and invalid or
  redundant state transition;
- invalid Citry and invalid Python source;
- ineligible escapes and implicit string concatenation.

M2 adds Python expression and `c-for` clause goldens with strings, nested
containers, comprehensions, comments, trailing commas, long calls, syntax
errors, and a provider-version pin in the corpus manifest. The shared M3
corpus adds expression-free `script` and `style` bodies, missing and invalid
providers, delimiter conflicts, preservation notices, and virtual-document
mapping. Python and CLI suites separately cover direct `js`/`css` literals and
statically resolved file assets. Context-proven browser-expression adapters
remain a later additive capability.

Each surface loads the shared embedded case list and executes every result it
can produce or consume. Rust, the Python binding, and LSP finishing cover
stale, duplicate, and missing result identities. The CLI's process adapter
constructs those identities itself, and the VS Code producer echoes one result
per input region, so their suites explicitly classify those three cases as
server-side validation rather than fabricating an impossible local state.

The completed corpus uses capability-oriented paths such as
`tests/fixtures/v1/comments`; temporary implementation-stage directory names
do not appear in physical paths, Rust types, tests, case IDs, or schema fields.

### 14.2 Property and invariant tests

For generated and corpus inputs, test:

- `format(format(source)) == format(source)`;
- original and result both parse;
- structural projections match after ignoring positions and tag-internal
  layout trivia;
- non-whitespace `Text` and verbatim/sensitive gaps are byte-identical;
- only gaps classified structural differ;
- M1 expression semantic content is byte-identical after excluding the
  explicitly normalized short-expression delimiter trivia;
- M2/M3 provider results parse, preserve provider-defined AST and comment
  projections, and are idempotent;
- canonical comments have the same kind and content;
- no edit intersects a suppression range;
- Python candidates pass `ast.parse` and rediscovery decodes the exact
  formatter result;
- M1 CLI, Python API, LSP, and VS Code fixtures produce the same bytes;
- embedded output matches whenever provider identity, version, and options
  match, and capability output differs when they do not.

Add regression tests for every formatter bug before fixing it. Fuzz parser
successes, arbitrary whitespace around tag-internal tokens, and generated
block/inline/unknown boundary combinations. Invariant or provider-validation
failure must result in no returned edit.

### 14.3 Browser-semantic probes

The CSS-style classifier is intentionally not byte-preserving for structural
gaps, so it needs browser probes in addition to AST properties. Browser-native
before/after fixtures run under default browser styles and assert:

- inline no-space and one-space cases keep distinct `textContent` and
  `innerText` results;
- unknown/custom-element and component-root boundaries keep their exact text
  nodes;
- block reindentation does not change rendered text under the default display
  model;
- `pre`, `textarea`, raw, mixed-content, and suppressed regions remain exact;
- HTML comments stay in the intended order.

Authored Citry controls and component invocations are not inserted into a
browser as if they were compiled HTML. Their source order and rendered-edge
possibilities are locked by the structural projection and corpus. Browser
fixtures may use unknown and `c-*` elements only to prove that their exact text
boundaries remain untouched; they do not claim to exercise component runtime
rendering.

Fixtures also demonstrate, without claiming to solve it, that author CSS can
make a known block inline. The documented remedy is `fmt: off`; a future
strict whitespace option can be designed from demand.

### 14.4 Stage gates

Each stage has a hard gate:

| Stage | Gate |
|---|---|
| Contract | Block-like set, whitespace classifier, projections, and M0/M1 goldens are reviewed before printing code. |
| M0 Rust | Start-tag goldens, idempotence, reparse, comments, and invariant-failure probes pass. |
| M0 vertical integration | Rust, Python rewrite, CLI, LSP, and VS Code produce the same M0 bytes; write/check/diff, UTF-16 edits, and save behavior pass locally. |
| M1 useful formatter | Full structural goldens, generated boundary properties, browser probes, suppression, and comment association pass across every surface. Only this gate permits the first formatter release. |
| M2 expressions | The selected batch/LSP Python provider passes expression-kind, AST, comment, version, and failure-isolation tests. |
| M3 assets | VS Code public-provider delegation semantics, batch explicit-provider behavior, virtual mappings, capability reports, and atomic composed edits pass. The UI must not claim default-provider parity or identity that VS Code cannot prove. |
| Release | Package-local changelogs describe only their package, compatibility declarations are current, and the shared corpus passes from a clean build. |

## 15. Packaging and release ownership

The Rust formatter crate is internal workspace infrastructure. Public release
notes follow package ownership:

- `citry_core` records the new Python formatter API in
  `packages/py/citry_core/CHANGELOG.md`;
- the Python `citry` package records `citry format` and rewrite discovery in
  the root `CHANGELOG.md`;
- `citry-lsp` records protocol v1 and formatting in its own changelog;
- the VS Code extension records commands, formatting registration, and the
  source action in its own changelog.

The `citry` distribution's exact `citry_core` pin must move with the release
that starts importing `citry_core.template_formatter`. `citry-lsp` protocol v1
carries M0 through M3 formatting because none of these additive capabilities
has been released yet; M3 is negotiated through the client capability in
section 11. Local development tests build the workspace wheel and install it
into the test environment; publishing to PyPI is not required to test the VS
Code extension locally.

Formatter output is an opinionated tooling behavior, not a render API. Minor
releases may improve layout, but they must retain the correctness invariants
and document output-changing classification rules. The M1 Citry/HTML pass is
identical across surfaces. M2/M3 output additionally depends on the reported
provider identity, version, and options; CI must pin those when exact output
matters.

## 16. Accepted implementation order

1. **Lock whitespace and corpus contracts.** Implemented 2026-08-04. The
   contract-only crate contains the block-like constant, boundary classifier
   cases, structural projections, M0/M1 goldens, and invariant helpers before
   printer code.
2. **Build the M0 Rust core.** Implemented 2026-08-04. The crate now has the
   source-preserving model, canonical comment association, suppression ranges,
   opening-tag printer, public entry point, reparse verification, and generated
   and adversarial invariant probes.
3. **Expose M0 through Python.** Implemented 2026-08-04. The PyO3 submodule,
   typed wrapper, and structured formatter error now expose the Rust core. The
   shared host adapter performs reverse-safe direct-template-literal rewrites,
   preserves Python framing and newline style, validates complete candidates,
   and reports explicit ineligibility without exposing partial source.
4. **Add the M0 CLI path.** Implemented 2026-08-04. The development-only
   `citry format` command now provides deterministic explicit and directory
   discovery, static direct `template_file` resolution, normalized
   deduplication, write/check/diff modes, per-file atomic writes, summaries,
   and precedence-correct exit codes without importing an app.
5. **Complete the M0 editor path.** Implemented 2026-08-04. Protocol v1 now
   supports workspace-scoped dynamic `citry-html` formatting for generic
   clients, provides the versioned `citry/formatTemplates` request, and
   connects one routed VS Code formatter plus the commands and
   `source.format.citry` action. The local cross-surface tests exercise the
   opening-tag-only formatter without publishing it.
6. **Expand the same core to M1.** Implemented 2026-08-04. The shared core now
   performs full Citry/HTML structural layout with conservative mixed-content
   boundaries, end-tag placement, body comments, exhaustive control analysis,
   recursive nested templates, exact suppression and verbatim fingerprints,
   and bounded expression-delimiter normalization. Structural goldens run
   through Rust, the Python binding and host rewriter, CLI, and LSP, while the
   VS Code route applies every corpus result byte-for-byte. Generated boundary
   properties, control projections, and browser-native semantic probes pass.
   This is the first formatter capability that may be released.
7. **Add M2 Python expressions.** Implemented 2026-08-04. The bounded spike
   selected vendored Ruff for an in-process provider shared by every surface.
   Ordinary expressions and `c-for` clauses use separate Python adapters with
   Python 3.10 parsing, AST and anchored-comment equivalence, absolute width,
   delimiter-safe fallback, and fixed-point layout. Direct `c-fill data` uses
   a Citry-owned binding-pattern adapter. Project status and verbose CLI output
   report the authoritative provider identity without changing protocol v1.
8. **Add M3 JavaScript/CSS providers.** Implemented 2026-08-05. Citry now
   discovers eligible JavaScript and CSS in template
   `<script>`/`<style>` blocks and in component `js`, `css`, `js_file`, and
   `css_file` assets. The CLI delegates these regions to an explicitly
   configured native Biome binary, while VS Code presents them as temporary
   JavaScript or CSS documents to the editor's registered formatter. The LSP
   coordinates this through protocol v1. After formatting, Citry verifies that
   the document is current, the results belong to the requested regions,
   protected delimiters were preserved, formatting is idempotent, and the
   completed template or Python source still parses before applying an atomic
   edit. Regions containing Citry interpolation, Citry template comments, or
   lexically unsafe constructs remain unchanged until safe adapters are
   available.
9. **Document and release each completed public milestone per package.** Update
   setup, CI examples, package-local changelogs, compatibility declarations,
   and local VS Code development instructions. Do not publish M0 as the
   formatter feature.

### 16.1 Step 9 release-readiness checklist

Step 9 is a release pass, not another formatter capability milestone. Complete
all of these before publishing the formatter surfaces:

1. Manually exercise `citry format` on a representative project before relying
   on the automated corpus alone. Cover write, `--check`, and `--diff`; an
   explicit Python, template, JavaScript, or CSS file; directory discovery;
   statically resolved `template_file`, `js_file`, and `css_file`
   declarations; and each `--embedded` mode with both an available and a
   missing provider. Confirm that refusals and provider failures never leave
   partial file edits.
2. Run the complete clean repository gate with `python scripts/check.py`, then
   build and install the VSIX in a fresh project environment whose selected
   interpreter contains the release-candidate `citry` and `citry-lsp`
   packages. Recheck diagnostics, completion, both formatter commands,
   standalone-template format-on-save, the Python source action, and the
   JavaScript-provider limitation from the installed artifact.
3. Finalize package versions, compatibility declarations, and publication
   order. The release that imports `citry_core.template_formatter` carries the
   matching exact `citry_core` pin. `citry-lsp` and the VS Code extension keep
   protocol version 1 while their owning packages remain below 1.0.0. Publish
   the new `citry-core` first, update Citry's exact pin and `uv.lock`, publish
   `citry`, then publish `citry-lsp`, and publish the editor extension last.
4. Review each public landing surface for a first-time user. The root
   `README.md` introduces framework-level editor support; the extension's
   `packages/editors/vscode/README.md` is its Marketplace and Open VSX listing;
   `docs_site/content/ide/index.md` gives the tooling overview; and
   `docs_site/content/ide/vscode.md` gives the complete setup guide. The public
   `docs_site/content/cli.md` formatter guide belongs in the same review.
   Together they must explain extension installation, `citry-lsp` installation
   in the selected project interpreter, `citry.app`, syntax-only degradation,
   standalone file association, formatting and save configuration, CLI modes
   and providers, and the compatible JavaScript formatter requirement.
5. Add a concise editor-tooling path to the docs-site landing page when the
   public artifacts exist. Before publication, the landing page must describe
   them as upcoming rather than sending users to unavailable registry entries.
   Validate every README link and image from its published host, where
   repository-relative paths may not resolve.
6. Prepare a reproducible publication workflow or documented manual procedure
   for each new channel before invoking it. In particular, `citry-lsp` needs a
   PyPI publishing path, and the extension needs both Visual Studio Marketplace
   and Open VSX procedures. Publish through each owning package's channel and
   smoke-test the installed artifacts. Record user-visible changes exactly
   once in the owning package's changelog.
7. Perform one formatter-code readability pass. Confirm and document the
   intended boundary of `PYTHON_EXPRESSION_PROVIDER`: today it exposes the
   pinned built-in Ruff provider identity to the corpus, Python binding, and LSP
   status contract, but the review should decide whether that identity needs to
   remain a public Rust constant or can have a narrower home. Add concise inline
   comments across the Rust formatter modules that explain the intent behind
   non-obvious state transitions, conservative refusals, source-preservation
   rules, and verification passes. Prefer rationale and invariants over comments
   that merely restate individual operations.

### 16.2 Possible improvements after the first release

These are documented candidates, not commitments or release blockers. Their
order should follow real formatter usage and failure reports:

- Add language-aware mappings for JavaScript and CSS bodies that contain Citry
  interpolation or Citry template comments. Here, a Citry comment means
  `{# ... #}` embedded inside a `<script>` or `<style>` body. Ordinary
  JavaScript `//` and `/* ... */` comments and CSS comments are language
  syntax; they are not what this limitation names. The future adapter must
  shield each Citry-owned region, reject provider edits that cross it, and
  restore the exact authored bytes before reparsing. A context-valid
  placeholder is one possible mechanism, not the required architecture.
- Admit more whitespace-sensitive JavaScript and CSS safely through a
  language-aware source map. Candidates include multiline quoted or template
  literals, block comments, line continuations, nested JavaScript templates,
  ambiguous regular expressions, hashbangs, CSS `@charset`, and initial byte
  order marks. Until the mapping proves raw-token preservation, these regions
  remain unchanged with a capability notice.
- Format browser-language expressions only when their owner can prove the
  language and map edits back to authored source. This includes Alpine
  expressions, browser props, and extension-defined event mini-languages; a
  generic JavaScript formatter must not guess their grammar.
- Give editor clients stronger provider selection when their API permits it.
  The initial VS Code adapter honestly reports `vscode-first-result` because
  the public command neither guarantees the configured default formatter nor
  reveals provider identity. A formatter-specific adapter may later provide a
  stable identity, version, options, and default-provider contract.
- Add further explicit batch providers behind the same executable authority,
  identity, timeout, and validation rules as the Biome adapter. Provider names
  must select a designed adapter rather than an arbitrary command line. A
  language-specific adapter may also add parser-backed semantic-equivalence
  checks that the generic editor boundary cannot prove.
- Support dependency-bearing Biome configurations only after the adapter can
  resolve, isolate, and fingerprint external `extends` and plugin inputs. The
  initial adapter rejects those configurations rather than executing
  untracked code or claiming an incomplete provider identity.
- Add configuration only from demonstrated use cases. Candidate surfaces are
  line width, indentation, a stricter whitespace policy for tags whose CSS
  display differs from browser defaults, stdin or machine-readable output,
  include and exclude patterns, and caching. `fmt: off` remains the immediate
  escape hatch for a local layout where the default structural policy is not
  appropriate.
- Normalize parser-approved end-tag whitespace trivia if real source examples
  show value. End tags already participate in layout and suppression-state
  inheritance, but the first release preserves their interior bytes. Any
  future rule must preserve the exact tag name and case.

The ordering intentionally reaches the real CLI and editor before investing in
the complete pretty-printer, as an integration proof. It then completes M1
before any public formatter release, so users never mistake the vertical slice
for the finished capability.

## 17. Alternatives considered

### 17.1 Use an existing HTML formatter

Rejected. A generic HTML formatter does not understand Citry expressions,
template-valued attributes, transparent structural tags, component
uncertainty, or the classifier in section 6. The Citry core must own outer
markup. Prior art and selected embedded providers are still reused where their
language boundary is real.

### 17.2 Preserve every `Text` token byte-for-byte

Rejected as the end-state formatter contract. It is safe enough for M0 but
limits formatting to tag interiors and does not satisfy issue #22's
pretty-printer goal. M1 instead preserves non-whitespace and sensitive text
exactly while normalizing documented structural gaps.

### 17.3 Change the compiler to discard indentation whitespace

Rejected by this design. The compiler deliberately preserves ordinary
inter-element whitespace, and inline whitespace can be visible or observable.
Changing that behavior would be a separate template-language compatibility
decision. The formatter can become useful with CSS-style classification
without changing runtime semantics.

### 17.4 Register Citry as a Python document formatter

Rejected. VS Code selects competing whole-document formatters. Citry must
coexist with the user's Python formatter and edit only proven embedded regions,
which is what a command and source action provide.

### 17.5 Require an app or accept a component library

Rejected for formatting. The grammar and safe layout rules do not depend on a
runtime registry. App import would make output environment-dependent and add
side effects without improving formatting correctness.

### 17.6 Attach comments in the public parser AST first

Rejected. Comment placement is a printer policy, while the parser already
provides the spans needed to derive it. Keeping the association model internal
avoids a cross-binding public AST change and lets the parser remain neutral.

### 17.7 Format compiled or transformed templates

Rejected. Generated output cannot be mapped back reliably to authored source,
and formatting it would edit the wrong representation. Alternate source
languages need their own authored-source formatting contract.

### 17.8 Build every embedded formatter before integration

Rejected. It would delay proof of the risky Python rewrite, LSP, and editor
boundaries while combining four formatting languages into one debugging
surface. M0 proves integration, M1 supplies the useful Citry/HTML release, and
M2/M3 add language providers behind explicit capability reporting.

### 17.9 Add `citry check --fix`

Rejected. Checking and formatting have different mode and discovery contracts.
A separate `citry format` command makes write behavior obvious and gives CI the
familiar `--check` form without overloading the registry-backed checker.
