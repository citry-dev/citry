# Agent knowledge - citry_template_parser

Deep architecture for the V3 template parser and compiler. For repo-wide rules
see [`/CLAUDE.md`](../../../../CLAUDE.md). For cross-crate facts (the V1/V2/V3
version model, the binding architecture, repo-wide anti-patterns) see
[`/docs/agent/INDEX.md`](../../../../docs/agent/INDEX.md).
For quick pointers and gotchas see [`../../AGENTS.md`](../../AGENTS.md).

When you discover a non-obvious fact while working in this crate, propose a new
entry here. Keep each one to a paragraph; link to source with `file:line`.

---

## The pipeline

```
template string
  -> Pest grammar (grammar.pest)        : tokens / rule tree
  -> parser.rs (parse_template)         : Template AST (tree of Node / TemplateElement)
  -> compiler.rs (compile_template)     : Vec<LangSpecArgument> (codegen IR)
  -> lang/<lang>.rs (LangImpl::compile)  : host-language source string
```

For Python the final string is a `generate_template()` function that returns a
`body` list of runtime node objects. Those node classes live on the Python
side (not yet implemented; see the cross-crate INDEX "Open project plans").

---

## Grammar (`grammar.pest`)

Pest rule atomicity markers matter a lot here:

- `{ }` non-atomic: Pest inserts implicit whitespace between sequence elements
  and repetitions (because a `WHITESPACE` rule is defined).
- `@{ }` atomic: no implicit whitespace, and inner rules are silenced (no
  tokens). Cascades to called rules.
- `${ }` compound-atomic: no implicit whitespace, but inner rules still produce
  tokens. The no-whitespace property cascades to called rules.

**`template` is compound-atomic (`${ }`) on purpose.** A `WHITESPACE = _{ ... }`
rule is defined, so a non-atomic `template` would let Pest silently skip
whitespace between `template_element` repetitions, dropping (for example) the
space right after a closing tag. Making `template` compound-atomic stops that.
Because atomicity cascades, `html_comment` and `html_raw` (reached from
`template_element`) are also matched without implicit whitespace; this is why
HTML-comment values include their surrounding spaces symmetrically, and why
`<c-raw attr>` matches the raw rule (the parser then rejects the attribute, see
Validation). The tag rules (`html_start_tag`, `html_end_tag`,
`html_self_closing_tag`) are already `${ }` and use explicit `spacing` /
`spacing_with_whitespace` rules, so they are unaffected.

Pest grammars cannot match nested structure dynamically (a closing tag cannot
be required to match its opener's name in the grammar), so the grammar only
recognizes individual start / end / self-closing tags; the tree is assembled in
the parser with a stack.

`<c-raw>` content is grabbed as raw text by the grammar (`html_raw_content`)
because it may not be valid template syntax.

## AST (`ast.rs`)

Top type is `Template { elements, comments, used_variables, slots }`. A
`TemplateElement` is one of `Text`, `Expr` (a `{{ }}` expression), `Node` (a
tag), or it is a comment (collected into `comments`, not kept as an element,
except HTML comments which are also kept as `Text`). A `Node` is either
`SelfClosing { start_tag, .. }` or `WithBody { start_tag, end_tag, body, .. }`,
and carries `used_variables`, `introduced_variables`, `comments`, and
`contains_fills`. `HtmlAttr` carries `key`, `value`, `inner_value`,
`quote_char`, `kind` (`Static` / `Expression` / `Template` / `Meta`),
`used_variables`, and `comments`. `Meta` is the `#c-*` framework-metadata
channel (`#c-key` / `#c-ignore`): routed by its own grammar rule
(`html_meta_attribute_name`), exempt from tag attribute rules, with its own
placement validation (`validate_meta_attr_placement`) and its own compiler
emission (never an ordinary attribute node). `Token` is the shared span type
(`content`, `start_index`, `end_index`, `line_col`).

Types annotated `#[pyclass]` are the Python contract. Changing their shape is a
high-risk change: update the PyO3 registration, the `_rust.pyi` stub, and the
Python wrapper together (CLAUDE.md Mechanism 4).

The child lists and the per-node lists of variables and comments are
`Shared<Vec<...>>` (`ast.rs`), an `Arc` that copies of the tree share. PyO3
copies a field when Python reads it, so this keeps a read to one node instead
of the whole subtree below it (#384). Python sees plain lists. `Shared` has no
`DerefMut`, so every possible copy is visible in the code: change a list with
`Shared::make_mut`, which copies only when the list is shared, and move one
out with `Shared::into_inner`.

## Parser (`parser.rs`)

`parse_template(input, lang, user_rules)` builds the tree:

- The grammar's `template` rule always runs through `parse_grammar`, which sizes the stack
  from how many `{` the source holds (see "Expressions and braces that nest too
  deeply" in `docs/design/template_grammar.md`). Call it rather than
  `GrammarParser::parse` for `Rule::template`.
- An HTML tag stack assembles `WithBody` nodes; a closing tag pops and must
  match the open tag's name under ASCII-case-insensitive HTML identity, else a
  mismatched-tags error. Authored spelling stays in the AST.
- Void elements (`constants::HTML_VOID_ELEMENTS`) are treated as self-closing
  through the same ASCII-case-insensitive identity.
- Citry's `c-` prefix is exact lowercase. Component suffix identity is
  ASCII-case-insensitive, including the dynamic built-ins, while structural
  tags require their exact lowercase spelling. The shared helpers in
  `constants.rs` keep parser and compiler dispatch aligned.
- `c-*` attributes are classified: a value whose trimmed content starts with a
  real tag and whose last grammar element is a closing, self-closing, raw, or
  HTML void tag becomes `Template`, as does a value wholly enclosed by
  `<>...</>`. Adjacent real-tag roots are valid; fragment delimiters must wrap
  the entire non-whitespace value and cannot be sibling roots. They are stripped
  at the attribute level (not in the grammar). Other dynamic values become
  `Expression`. Plain attributes are `Static`.
  Control-flow shortcuts are the semantic exception: `c-if`/`c-elif` must be
  expressions, `c-for` must be a loop clause, and the `c-else`/`c-empty`
  markers must be valueless.
- Token positions come from `utils/line_index.rs`, built once from the whole
  template string the caller passed and shared with the parses of nested
  `Template` attribute values. It returns the same line and column as
  `pest::Position::line_col`, which scans from the start of the source and
  would make parsing grow with the square of its length.
- Variable tracking: each node's `used_variables` lists the variables its
  body reads, then those its attributes read, and a template lists its
  elements' variables in source order (a `Vec`, not a set, so order is
  stable). `recompute_template_used_variables` builds these lists once the
  whole tree exists, so they are complete only after parsing finishes;
  `introduced_variables` come from `<c-for>` loop targets and `<c-fill>`
  `data` / `fallback`. Python variable extraction delegates to
  `python_safe_eval` via the `LangImpl`.
- Control-flow grouping (`<c-if>/<c-elif>/<c-else>`, `<c-for>/<c-empty>`) is
  validated for adjacency and ordering (`constants::TAG_ORDERING_RULES`) in
  both explicit-tag and shorthand-attribute forms, using the same IF-before-FOR
  precedence as compiler lowering.

Some parse costs still grow faster than the template, because the AST
contract requires them: every node holds its subtree's comments and used
variables, and every body holds its subtree's comments and slots, so these
lists cost depth times count. The nesting limits bound them: a template nests
at most 512 tags and 256 logic levels (`nesting.rs`; see "13. Nesting limits"
in `docs/design/template_grammar.md`). The parse loop checks each tag's depth
as it builds the tag stack, and a template in an attribute continues from the
depth of the tag that holds it (`ParserContext::depth_base`).

Validation runs through `validate_node` (fill placement, attributes present,
attribute conflicts, `c-bind`, fill names, variable shadowing). **`<c-raw>` is
the exception:** `process_html_raw` builds the node directly and bypasses
`validate_node`, so it calls `validate_attributes_present` itself to reject
attributes on raw tags. Attribute and slot rules per tag are data-driven in
`constants::TAG_ATTR_RULES_DATA` / `TAG_SLOT_RULES_DATA`. User `TagRules` also
carry optional per-slot data-field names. A direct destructuring source is
checked only when the effective fill name and data provider are both static;
dynamic providers keep the runtime check.
Ordinary HTML elements and `<c-element>` compare explicit attribute identities
with ASCII folding (`ID`/`id` duplicate, `ID`/`c-id` logical conflict,
`CLASS`/`c-class` accumulation). Component kwargs remain exact-case.

## Compiler (`compiler.rs`) and the output-format contract

The compiler checks a tree's depth with `check_template_depth` before it walks
it, using the parser's `nesting::tag_levels`, so a tree built by hand cannot
go past the limits either.

The **module-level docstring** at the top of `compiler.rs` is the definitive
reference for the node types emitted, their signatures, and the formatting
conventions (trailing commas, triple-quoted strings, coalescing, name
normalization, void-element rendering, determinism). Read it first; this
section covers only the high-level flow and agent-relevant non-obvious facts.

`compile_template(template, lang)` first calls
`wrap_nodes_with_control_flow_attrs` (turning `c-if`/`c-for` attributes on a
regular tag into wrapping `<c-if>`/`<c-for>` nodes; IF has higher priority than
FOR, so IF wraps FOR), then walks elements into a `Vec<LangSpecArgument>`, then
hands that to `LangImpl::compile`. Consecutive static strings are coalesced.

`LangSpecArgument` (in `lang/lang.rs`) is the language-agnostic codegen IR:
`Variable`, `UnsafeString` (any text, written as an escaped multiline literal),
`SafeString` (a short name, written as a one-line literal that is escaped
too), `Int`, `Bool`, `Tuple`, `List`, `Struct { name, arguments }`.

Non-obvious facts to keep in mind (the module doc carries the full output
contract):

- On a regular HTML tag (not a component), any dynamic `c-*` attribute makes
  the whole attribute set compile to one `ElementAttrsNode` covering every
  ordinary attribute (static ones included), because spreads and class/style
  merging resolve as one unit at render time (`compile_html_node`). A purely
  static tag flattens to literal strings instead.
- `#c-*` framework metadata never joins that attribute set: on an element it
  compiles after the ordinary attributes (`#c-key` as an `ElementKeyNode`
  wrapping its `ExprHtmlAttr`, `#c-ignore` as the literal morph marker). The
  key node emits the complete `data-citry-key` attribute for every evaluated
  value except `None`, which emits nothing. On a component tag `#c-key` rides
  as the `ComponentNode`'s trailing key argument, emitted only when authored;
  the Python runtime likewise treats an evaluated `None` as no key.
- Expression content retains its trailing whitespace from `{{ expr }}`.
- The Python printer (`lang/python.rs`) keeps each generated statement within
  100 nested brackets, because CPython rejects more than 200. For a deeper
  template it moves some subtrees into earlier `_nN = ...` statements, chosen
  so Python still builds the nodes in the same order. Its tests are in `src/lang/python_printer_tests.rs`.
- `<c-raw>` compiles its body to a single literal text part (an `UnsafeString`
  that `coalesce_strings` may merge with adjacent static text); the inner
  content is emitted verbatim, with no template processing.

Compiler tests are in `tests/tag_compiler.rs`, `tests/tag_compiler_dynamic.rs`,
and `tests/tag_compiler_meta_attrs.rs` and assert exact generated strings (the
observe-then-lock style).

## Lang trait (`lang/lang.rs`)

`LangImpl` has `parse_expression` (returns used / assigned vars and comments),
`parse_forloop_expression` (extracts loop target variables), and `compile`
(turns the codegen IR into a source string). `Lang` is the enum
(`Python`/`Php`/`Js`/`Go`/`Rust`); `Lang::to_lang_impl` maps to the static
impl. **Only `python.rs` is complete** (it uses `python_safe_eval` and Ruff's
Python AST); the other four are structural stubs that extract variables with
regex heuristics and do not do real parsing. Adding or changing a trait method
is a cross-language change.

## Tests

One file per feature area under `tests/` (structure, html, kwargs,
boolean_attrs, dynamic_attrs, meta_attrs, expressions, comments,
nested_templates, spreads, control_flow_if, control_flow_for, fills,
composition, raw, user_rules), plus `tag_compiler.rs`,
`tag_compiler_dynamic.rs`, and `tag_compiler_meta_attrs.rs` for compiler
output. Shared AST builders are in
`tests/common/mod.rs`. Parser tests assert the full AST via `assert_eq!`;
compiler tests assert the exact generated string. Both are authored
observe-then-lock. Illustrative code blocks in doc comments (in `lang/rust.rs`
and `parser_context.rs`) are marked ```` ```ignore ```` so the doctest runner
skips them.
