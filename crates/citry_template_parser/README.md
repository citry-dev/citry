# citry_template_parser

A Rust crate that parses [Citry](../../README.md) templates into an AST and
compiles them into host-language source code. Powers the template engine for
every Citry language binding (Python, and planned JS/PHP/Go/Rust).

## What it does

Given a Citry template:

```html
<c-Card title="Welcome" c-class="card_cls">
  <c-fill name="body">
    <c-for each="item in items">
      <p>{{ item.name }}</p>
    </c-for>
  </c-fill>
</c-Card>
```

The crate:

1. **Parses** it (via a [Pest](https://pest.rs/) grammar) into a `Template`
   AST with typed nodes for HTML tags, components (`<c-*>`), expressions
   (`{{ }}`), comments (`{# #}`), control flow (`<c-if>`, `<c-for>`), slots,
   fills, and raw blocks.

2. **Compiles** the AST into host-language source code. For Python (the
   default) this is a `generate_template()` function returning a list of
   runtime node objects:

   ```python
   def generate_template():
       body = [
           ComponentNode(source, (0, 198,), (
               StaticHtmlAttr(source, (8, 23,), """title""", """Welcome""", ()),
               ExprHtmlAttr(source, (24, 41,), """c-class""", """card_cls""", ("card_cls",)),
           ), [
               FillNode(source, (44, 168,), ...),
           ], ("card_cls",), """card""", True),
       ]
       return body
   ```

The host-language runtime provides the node class implementations
(`ExprNode`, `ComponentNode`, `IfNode`, etc.) that this generated code
instantiates. The compiler only produces the source string.

## Template syntax

Citry uses an HTML-compatible syntax with two rules:

- **`<c-*>` tags are components** (or built-in control flow / slot tags)
- **`c-*` attributes are dynamic** (their values are host-language expressions)

```html
<!-- Static attribute -->
<div class="container">

  <!-- Dynamic attribute (expression evaluated at runtime) -->
  <div c-class="dynamic_classes">

    <!-- Component -->
    <c-MyComponent title="Hello" c-data="items" />

    <!-- Control flow -->
    <c-if cond="is_visible">
      <p>Visible</p>
    </c-if>

    <!-- Loop -->
    <c-for each="item in items">
      <li>{{ item.name }}</li>
    </c-for>
    <c-empty>
      <li>No items</li>
    </c-empty>

    <!-- Slot / fill -->
    <c-slot name="footer" />

    <!-- Raw (unparsed) -->
    <c-raw>{{ not evaluated }}</c-raw>

    <!-- Template expression -->
    <p>Hello {{ user.name }}!</p>

    <!-- Template comment (stripped from output) -->
    {# internal note #}
  </div>
</div>
```

Control flow can also be written as attributes on regular tags:

```html
<div c-if="is_visible">...</div>
<li c-for="item in items">{{ item.name }}</li>
```

Dynamic attributes can contain nested templates instead of expressions:

```html
<c-Card c-body="<span>{{ name }}</span>" />
<!-- Or with a fragment for multiple roots: -->
<c-Card c-body="<><p>Line 1</p><p>Line 2</p></>" />
```

See the [root README](../../README.md) for the full syntax reference.

## Public API

### Parsing

```rust
use citry_template_parser::{parse_template, Template, Lang};

// Parse with Python expressions (default)
let template: Template = parse_template("<p>{{ name }}</p>", None, None)?;

// Parse with a different expression language
let template = parse_template("<p>{{ name }}</p>", Some(Lang::Js), None)?;
```

### Compiling

```rust
use citry_template_parser::compiler::compile_template;

let template = parse_template("<p>{{ x + 1 }}</p>", None, None)?;
let python_source: String = compile_template(template, None)?;
// python_source is a `def generate_template(): ...` function body
```

### AST types

The parser produces a `Template` containing `TemplateElement` variants:

- `TemplateElement::Text` - plain text
- `TemplateElement::Expr` - `{{ expression }}` with tracked variables
- `TemplateElement::Node` - an HTML tag or component, either:
  - `Node::SelfClosing` - `<br/>`, `<c-Card />`
  - `Node::WithBody` - `<div>...</div>`, `<c-if cond="x">...</c-if>`

Each node carries `HtmlAttr` entries classified as:

- `HtmlAttrKind::Static` - `class="foo"`
- `HtmlAttrKind::Expression` - `c-class="expr"` (runtime-evaluated)
- `HtmlAttrKind::Template` - `c-body="<div>...</div>"` (nested template)

All nodes track `used_variables` (variables referenced from the surrounding
context) and `introduced_variables` (variables created by `<c-for>` loops or
`<c-fill>` data/default bindings).

### Multi-language support

Expression parsing and code generation are abstracted behind the `LangImpl`
trait. The `Lang` enum selects the implementation:

| Language | Status | Expression parsing |
|----------|--------|--------------------|
| Python   | Complete | Full AST analysis via `python_safe_eval` / ruff |
| JavaScript | Stub | Regex-based variable extraction |
| PHP | Stub | Regex-based variable extraction |
| Go | Stub | Regex-based variable extraction |
| Rust | Stub | Regex-based variable extraction |

To add or extend a language implementation, see `src/lang/lang.rs` for the
`LangImpl` trait and `src/lang/python.rs` for the reference implementation.

### Custom tag validation

Pass user-defined validation rules to enforce allowed/required attributes
and slots on custom component tags:

```rust
use std::collections::HashMap;
use std::rc::Rc;
use citry_template_parser::{parse_template, TagRules};

let mut rules = HashMap::new();
rules.insert("c-my-table".to_string(), TagRules {
    allowed_attrs: Some(vec![
        vec!["title".to_string()],
        vec!["data".to_string(), "c-data".to_string()],
    ]),
    required_attrs: vec![
        vec!["data".to_string(), "c-data".to_string()],
    ],
    allowed_slots: Some(vec!["header".to_string(), "footer".to_string()]),
    required_slots: vec!["header".to_string()],
});

let rules_rc = Rc::new(rules);
let template = parse_template(
    r#"<c-my-table c-data="items"><c-fill name="header">H</c-fill></c-my-table>"#,
    None,
    Some(&rules_rc),
)?;
```

## Compiler output

The compiler converts the AST into host-language source via `LangImpl::compile`.
For the full node taxonomy, signatures, and formatting conventions, see the
module-level documentation at the top of `src/compiler.rs`.

## Architecture

```
template string
  |
  v
grammar.pest (Pest)        -- tokenize into rule tree
  |
  v
parser.rs (parse_template) -- build Template AST (tag stack, c-* classification,
  |                            variable tracking, validation)
  v
compiler.rs                -- walk AST -> Vec<LangSpecArgument> (codegen IR)
  |                            -> control-flow attribute unwrapping
  |                            -> string coalescing
  v
lang/<lang>.rs             -- LangSpecArgument -> host-language source string
```

For deep architectural detail, see
[`docs/agent/INDEX.md`](docs/agent/INDEX.md).

## Development

### Running tests

```bash
# All tests (226 unit tests + 5 ignored doctests)
cargo test -p citry_template_parser

# A specific test file
cargo test -p citry_template_parser --test tag_compiler
```

### Test style

Parser tests assert full AST trees; compiler tests assert exact generated
strings. Both are authored **observe-then-lock**: run the parser/compiler on
representative inputs, observe the real output, then lock it into an assertion.

Test helpers for building expected AST trees are in `tests/common/mod.rs`.

### Dependencies

- [Pest](https://pest.rs/) - PEG parser for the grammar
- [PyO3](https://pyo3.rs/) - AST types are annotated `#[pyclass]` for Python
  binding
- [`python_safe_eval`](../python_safe_eval/) - Python expression parsing and
  variable extraction (via ruff)
