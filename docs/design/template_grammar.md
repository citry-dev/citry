# Design: the V3 template grammar

**Status (2026-07-01): current.** This describes the Pest grammar and the
parse-time validation contract for citry's V3 `<c-*>` template syntax. The
grammar itself lives in
[`grammar.pest`](../../crates/citry_template_parser/src/grammar.pest); the
validation rules are enforced in
[`parser.rs`](../../crates/citry_template_parser/src/parser.rs) and configured
from [`constants.rs`](../../crates/citry_template_parser/src/constants.rs).

Related reading: the user-facing syntax guide is
[`../template-syntax.md`](../template-syntax.md); the V1/V2/V3 version model is in
[`../agent/INDEX.md`](../agent/INDEX.md); the dynamic-attribute rendering
semantics (class/style merging, `c-bind` spread) are in
[`template_html_attrs.md`](template_html_attrs.md); how the parse tree becomes an AST and then
generated code is in the parser crate's
[`AGENTS.md`](../../crates/citry_template_parser/AGENTS.md) and its
[agent INDEX](../../crates/citry_template_parser/docs/agent/INDEX.md).

## What the grammar is for

A citry template *is* HTML. The grammar's whole job is to recognize, inside
otherwise ordinary HTML, the few citry-specific pieces and pass everything else
through unchanged. Those pieces are: `{{ expr }}` expressions, `{# comment #}`
comments, `<c-*>` tags (components and the built-in control-flow tags), `c-*`
dynamic attributes, `#c-*` template flags, and `<c-raw>` verbatim blocks.

Two rules cover the whole syntax:

- A **tag** whose name starts with `c-` is a component (or a built-in
  control-flow tag).
- An **attribute** whose name starts with `c-` is dynamic: its value is a Python
  expression, or a nested template. The rendered attribute drops the `c-`
  prefix, so `c-class="..."` becomes `class="..."`.

On top of those, the template body may use:

- `{{ expr }}` in text (a Python expression, evaluated and escaped).
- `{# comment #}` anywhere (in text and inside tags); it is dropped from output.
- `c-bind="mapping"` to spread a dict of attributes onto a tag or component.
- `#c-key="expr"` and bare `#c-ignore` to describe node identity and morphing.
- A nested template as a `c-*` value, if the value starts with an HTML tag or a
  `<>` fragment, e.g. `c-body="<span>Hello {{ name }}</span>"`.

The grammar parses the source it receives without changing whitespace. The
component asset loader removes common indentation from inline Python
`template` declarations before parsing, while `template_file` content remains
exact. Direct parser calls and standalone Citry files are also exact. See
[`asset_loading.md`](asset_loading.md#34-inline-source-normalization).

Three naming constraints hold for every tag and attribute:

1. A tag or component name must start with an ASCII letter (`a-zA-Z`).
2. The rest of a tag name may be anything except whitespace, `/`, `>`, or `{#`.
3. An attribute name may be anything except whitespace, `=`, `/`, `>`, `<`, or
   `{#`.

## Template elements

The `template` rule matches a sequence of template elements. They are tried in
precedence order (most specific first), because some prefixes overlap (an HTML
comment `<!--` also starts with `<!`, so it must be tried before the generic
`<!...>` directive):

1. HTML comments, `<!-- ... -->`
2. HTML directives, `<!...>` (DOCTYPE, CDATA, and anything else in `<!...>`)
3. Processing instructions, `<?...?>`
4. Raw blocks, `<c-raw>...</c-raw>`
5. HTML tags (start, end, self-closing)
6. Template expressions, `{{ ... }}`
7. Template comments, `{# ... #}`
8. Plain text

### HTML comments, directives, and processing instructions

citry recognizes `<!-- ... -->`, `<!...>` (DOCTYPE and CDATA included), and
`<?...?>`, and preserves them in the output rather than parsing their insides.
The reason to treat them uniformly is what browsers do. In Chrome v142 (and
Firefox v145, Safari v18.6), everything in `<!...>` that is not a real comment,
plus every `<?...?>`, is turned into a comment, and DOCTYPE is moved to the top
or dropped. So this input:

```html
<span>
  <!-- keep -->
  <!LOL>
  <![CDATA[lol]]>
  <?lol?>
  <!DOCTYPE html>
</span>
```

renders (in the browser) as:

```html
<span>
  <!-- keep -->
  <!--LOL-->
  <!--[CDATA[lol]]-->
  <!--?lol?-->
</span>
```

Because the browser will treat them as inert comments anyway, citry does the
same: it matches each shape and keeps the text verbatim. Processing
instructions are matched as `<?` up to the first `>` (not the strict `?>`),
because browsers end them at the first `>` too.

## HTML tags

There are three kinds of tag, matched flat:

- Start tag, `<div ...>`
- End tag, `</div>`
- Self-closing tag, `<img ... />`

### Tag names

A tag name must start with an ASCII letter and may then contain almost anything.
This is stricter than the HTML5 tokenizer (which allows `<1a>`, `<:a>`, `<.a>`),
and it is deliberately stricter to match real browsers: Chrome v142 treats
`<1a>`, `<_a>`, `<:a>`, `<;a>` as text, not tags, because the name does not start
with a letter. After the first letter the browser is permissive, so `<a1_-:.,>`
is a valid tag, and citry matches that. citry additionally stops a tag name at
`{#`, since that begins a template comment.

This "starts with a letter" rule is what lets text like `3 < 4` stay text: the
`<` is only the start of a tag when a letter, `/`, `!`, or `?` follows it.

### Attributes

An attribute is a name with an optional value (no value means a boolean
attribute, e.g. `<input disabled>`). The name may contain anything except the
characters that would naturally end it: whitespace, `=`, `/`, `>`, `<`, and
`{#`. This is intentionally permissive so framework attributes parse as written:
`@change`, `v-model`, `:class`, `[style]`, `(click)`, `_('hello')` are all valid
attribute names. (Browsers are stricter about the first character, rejecting a
leading digit, `$`, `-`, `;`, or `,`; citry does not, because being permissive
here costs nothing and supports more tooling.)

A value, when present, is `=` (with optional whitespace on either side) followed
by one of:

- a double-quoted string, `"..."`
- a single-quoted string, `'...'`
- an unquoted run with no whitespace, quotes, `=`, `<`, `>`, or `{#`

The grammar does not look inside the value; it only finds the value's
boundaries. What the value *means* (a static string, a Python expression, or a
nested template) is decided afterwards in Rust. One consequence worth knowing:
an unquoted value cannot contain a space, so an expression that needs one (for
example `- .123e-5`) must be quoted: `key="- .123e-5"`.

### Why nesting is built in Rust, not in the grammar

Pest rules cannot refer back to text they already matched, so the grammar
cannot say "the closing tag must repeat this start tag's name". It therefore
matches start and end tags *flat*, as a stream, and the parser builds the tree
afterwards with a tag stack: each start tag is pushed, each end tag pops and is
checked against the tag on top using HTML's ASCII-case-insensitive tag identity
(a different name is a parse error), and text,
expressions, and self-closing tags are appended to the current open tag's body.
The AST and renderer preserve the opening and closing spellings the author
wrote. HTML void-element recognition uses the same case-insensitive identity,
so `<BR>` and `<br>` are equally void.

Citry syntax has a narrower casing contract. The framework prefix is exactly
lowercase `c-`; a Citry-looking `<C-Card>` is an error. After that prefix, a
component name is ASCII-case-insensitive (`<c-Card>` and `<c-card>` select the
same component). Reserved structural tags are different: they execute only in
their canonical lowercase spelling. A spelling such as `<c-If>` receives a
pointed “write `<c-if>`” parse error rather than being treated as either the
control tag or a user component. The dynamic built-ins follow component-name
identity, so `<c-Element>` and `<c-Component>` are equivalent to their
lowercase spellings. Attribute identity still follows the selected boundary:
`<c-element>` accepts ASCII-case variants of its HTML-style `is` / `c-is`
selector, while `<c-component>` keeps those component-input names exact.
Only HTML identities use ASCII case folding. Component kwargs, slot and fill
names, State fields, handler names, and custom event names remain
case-sensitive.

## Raw blocks (`<c-raw>`)

`<c-raw>...</c-raw>` is defined at the grammar level rather than as a normal
tag, for two reasons: its contents may not be valid template syntax, and there
is no reason to spend time parsing text that will be emitted verbatim. Inside
`<c-raw>`, everything up to the matching `</c-raw>` becomes a single text run;
`{{ }}`, `{# #}`, and nested tags are not interpreted. When rendered, the
`<c-raw>` wrapper itself is dropped and only its body is emitted.

The grammar recognizes attributes on `<c-raw>` (so `<c-raw foo>` parses), but
Rust then rejects them, which is how it produces a clear error message instead
of a confusing grammar failure. The same "recognize in the grammar, reject in
Rust for a good error" approach is used for attributes on end tags.

## Native text containers

`<script>`, `<style>`, `<textarea>`, and `<title>` follow HTML's text-container
shape: tag-looking body text does not become nested template nodes. The grammar
uses a tag-specific rule for each one so an opening `<script>` can close only
with `</script>` (ASCII-case-insensitively), not with another container's end
tag.

Citry interpolation remains intentionally active in these bodies. `{{ expr }}`
still compiles to an expression and `{# comment #}` is still removed, while
everything else, including `<button @c-click="save">`-shaped text, stays text.
This differs from `<c-raw>`, which disables expressions and template comments
as well. Keeping the distinction in the grammar means extensions that inspect
compiled nodes cannot mistake text inside a native container for a real HTML
element or attribute.

## Expression boundaries

Inside `{{ ... }}`, only whitespace is allowed around the expression, not
`{# #}` comments, because the contents are a Python expression, not template
syntax. The hard part is knowing where the expression *ends*, since `}}` can
also appear inside the expression (as in `{{ {"a": {1: 2}} }}`). The grammar
handles this by understanding just enough Python to find the real end:

- string literals (`'...'`, `"..."`, `'''...'''`, `"""..."""`) are skipped
  whole, so a `}}` inside a string does not end the expression;
- Python `#` comments are skipped to a newline or the host `}}` delimiter, so
  quotes and braces in comment text do not change the expression boundary;
- curly braces are counted, so the expression ends only when every `{` opened
  inside it has been closed.

Parentheses are not counted, only curly braces. The same boundary logic applies
to a `c-*` attribute value that holds a Python expression.

There are no template filters. A `|` inside `{{ }}` is just Python's bitwise-or
operator, so `{{ a | b }}` evaluates `a | b`; it is not a Django-style filter.

## Dynamic attributes and nested templates

A `c-*` attribute value is classified in Rust after the grammar has found its
bounds:

- A trimmed value exactly enclosed by `<>` and `</>` is a **fragment-valued
  nested template**. The delimiters must enclose the whole non-whitespace value;
  Rust strips them before parsing the payload. They are not template nodes and
  cannot be mixed with sibling roots (`<>a</><div>b</div>` is invalid).
- Otherwise, a value that starts with an HTML tag (`<tag...`) and whose last
  grammar element is a closing tag (including a native text container),
  self-closing tag, `<c-raw>` block, or HTML void element is a **nested
  template**. It may contain one or more adjacent
  root tags, with text, expressions, or comments between them. After trimming
  outer whitespace, leading or trailing non-tag content requires the
  whole-value fragment form.
- Otherwise it is a **Python expression**, e.g. `c-class="'vip' if user.vip else ''"`.

Nested templates render against the same writer-component context, e.g.
`c-body="<span>{{ name }}</span>"`. A static `<c-slot>` inside one therefore
belongs to the component whose template contains the attribute; its slot
metadata is propagated to that component's `Template.slots` just like a slot in
the ordinary body.

`c-bind="mapping"` is special: it spreads a dict of attributes onto the tag. It
does not become a `bind="..."` attribute, and a tag may carry several `c-bind`
attributes. The rendering-time details (how dynamic `class`/`style` merge with
static ones) live in [`template_html_attrs.md`](template_html_attrs.md).

Because a spread itself must evaluate to a mapping, `c-bind` is always an
expression and never a nested-template value. It is valid on elements and
components, including a normal tag carrying a control-flow shortcut, but not
directly on `<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`, or
`<c-raw>`: those structural runtime nodes do not consume spread attributes.
The selection/metadata expressions `c-is` on `<c-component>`/`<c-element>`,
`c-name` on `<c-slot>`/`<c-fill>`, and `c-required` on `<c-slot>` likewise
reject nested-template values on those special tags. The same spellings remain
ordinary template-capable kwargs on a user component.

## Template flags

An attribute name beginning with `#c-` enters the framework-metadata channel.
The grammar uses `html_meta_attribute_name` before the ordinary attribute-name
rule so Rust can distinguish that channel without inspecting string prefixes
later. The parser accepts exactly two members:

- `#c-key="expr"` evaluates a non-empty host-language expression and identifies
  an HTML element or component invocation across updates. If the expression
  evaluates to Python `None`, Citry emits no key for that render. `False`, `0`,
  and the empty string remain key values.
- bare `#c-ignore` leaves an ordinary element subtree or a logical component
  range out of morph updates. On runtime `<c-element>` it retains ordinary
  element semantics; structural tags still reject it.

The parser rejects unknown members, a valueless `#c-key`, a valued `#c-ignore`,
and placements on `<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`,
`<c-raw>`, `<c-fill>`, or `<c-slot>`. This placement check uses the same
reserved-tag identity described above. HTML void elements remain ordinary
identity nodes and may carry `#c-key`. Template flags must be written
explicitly on the tag. A `#c-*` mapping key arriving through `c-bind` is a
render-time error, even when its value is `None`; callers pass an ordinary
component input and the component writes `#c-key` on the markup it owns.

## Parse-time validation

The grammar accepts a broad shape; the parser then enforces the semantic rules
below and reports precise errors. These are compile-time guarantees, so a
malformed component usage fails when the *parent* template is parsed, not at
render time.

### 1. Control-flow tags must form groups

HTML wants every element balanced (`<a>...</a>`), but Django's
`{% if %}/{% else %}/{% endif %}` uses one shared tag for several branches,
which is not balanced HTML. citry instead gives each branch its own balanced
tag and validates that they sit together as a group:

- `<c-if>` / `<c-elif>` / `<c-else>` (in that order)
- `<c-for>` / `<c-empty>`

So `<c-elif>` and `<c-else>` may only follow a `<c-if>` or `<c-elif>`, and
`<c-empty>` may only follow a `<c-for>`. Anything wedged between the branches
(a stray `<div>`, for instance) breaks the group and is an error. The same rule
applies to the attribute form (`c-elif` / `c-else` may only follow `c-if` /
`c-elif`, and so on).

### 2. One control-flow attribute per group, per tag

A single tag may not carry two attributes from the same group. `c-if` with
`c-elif`, or `c-for` with `c-empty`, on one tag is an error. Attributes from
*different* groups may coexist (see rule 3).

### 3. Control-flow attributes across groups

A tag may combine one attribute from the IF group with one from the FOR group.
When it does, only the higher-priority group (IF) may use a non-leader member of
its group; the lower-priority group (FOR) must use its leader, `c-for`. This is
because the desugaring nests the FOR wrapper inside the IF wrapper (rule 3 of
"control-flow shortcuts" below), and a `<c-empty>` nested inside a `<c-if>` would
be cut off from its `<c-for>`.

Remember `c-else` and `c-empty` are boolean (they take no value):

```html
<!-- valid -->
<div c-if="x"   c-for="y in z">...</div>
<div c-elif="x" c-for="y in z">...</div>
<div c-else     c-for="y in z">...</div>

<!-- invalid: c-empty is the FOR group's non-leader -->
<div c-if="x"   c-empty>...</div>
<div c-elif="x" c-empty>...</div>
<div c-else     c-empty>...</div>
```

### 4. `<c-fill>` must eventually be inside a component

A `<c-fill>` fills a slot, so it has to resolve to some component. It may sit
inside control-flow tags on the way up (that is how you fill slots
conditionally or in a loop), but the nearest non-control-flow ancestor must be a
component:

```html
<!-- valid: fill is inside a component -->
<c-my-comp>
  <c-fill name="footer">...</c-fill>
</c-my-comp>

<!-- invalid: fill is inside a plain element, never reaches a component -->
<div>
  <c-fill name="footer">...</c-fill>
</div>
```

Concretely: a `<c-fill>` inside `<c-if>`/`<c-elif>`/`<c-else>` or
`<c-for>`/`<c-empty>` keeps looking up the stack; inside a plain tag (`<div>`)
or one of `<c-raw>`, `<c-fill>`, `<c-slot>` it is an error; inside a component
(`<c-component>`, `<c-element>`, or any user `<c-*>`) it is fine.

### 5. Cannot mix `<c-fill>` with non-fill siblings

A component body either passes its content as the single default slot, or names
its slots explicitly with `<c-fill>`; it cannot do both. So sibling `<c-fill>`
tags are fine, but a `<c-fill>` next to a non-fill element is an error. The
parser checks that a `<c-fill>`'s previous sibling is also a `<c-fill>`, and
vice versa.

### 6. Unique `<c-fill>` names

Within one component there is at most one fill per name. Names may be static
(`name="header"`) or dynamic (`c-name="prefix + '_x'"`). The parser catches
duplicate *static* names directly. Dynamic expressions are evaluated once per
fill and may be stateful, so identical expression source is not evidence of an
equal result. The runtime fill collector rejects duplicate resolved names.

### 7. Allowed and required fill names

A component may declare which slots it accepts (from its `Component.Slots`).
When `parse_template()` is given that information, a `<c-fill name="...">` whose
name is not one of the component's slots is an error, and a missing required
fill is an error, both caught in the parent template. A dynamic
`<c-fill c-name="...">` is deferred to runtime.

### 8. Allowed and required attributes

The built-in tags have fixed attribute rules, and user components get rules
derived from their declared inputs. The built-in rules are:

| Tag | Allowed attributes | Required |
|---|---|---|
| `c-if`, `c-elif` | `cond` | `cond` |
| `c-else` | (none) | (none) |
| `c-for` | `each` | `each` |
| `c-empty` | (none) | (none) |
| `c-raw` | (none) | (none) |
| `c-fill` | `name`; `c-name`; `data`; `fallback`; `c-bind` | one of `name` / `c-name` / `c-bind` |
| `c-slot` | any (no name means the `default` slot) | (none) |
| `c-component` | any | one of `is` / `c-is` / `c-bind` |
| `c-element` | any (only the `default` slot) | one of `is` / `c-is` / `c-bind` |

For a user component, its `Component.Kwargs` become the allowed and required
attributes, so `<c-Table bogus="1">` (unknown input) or `<c-Table>` (missing a
required input) fails at parse time. An input may always be supplied statically
(`title="x"`), dynamically (`c-title="expr"`), or via `c-bind`. The two
explicit spellings are mutually exclusive, while either spelling satisfies the
parser's required-input check. A `c-bind` spread may coexist with either one
because whether the mapping contributes that input is known only at render.

### 9. One explicit provider per logical attribute

A tag may not set the exact same attribute twice, or set both the static and
dynamic spelling of one logical attribute (`x` together with `c-x`). Both
spellings are visible when the template is written, and one would always make
the other dead configuration. The accumulating `class` / `c-class` and `style`
/ `c-style` pairs are the exception on HTML elements because both contributions
are preserved and merged.

`c-bind` is repeatable and may coexist with an explicit provider. A spread may
or may not contain the logical key at render time, so its contributions resolve
in source order. The directive does not clash with a literal `bind` attribute
because it never becomes `bind="..."`. Structural directives such as `c-for`
likewise do not clash with ordinary HTML attributes such as `for`.

### 10. No variable shadowing

Two constructs introduce new names into a local scope: `<c-for each="x in y">`
introduces the loop variables, and `<c-fill data="d" fallback="f">` may
introduce `d` and `f`. A destructured fill data binding such as
`data="{x, source as target, **rest}"` introduces `x`, `target`, and `rest`.
A newly introduced loop/fill binding may not reuse a name already in scope.
This no-shadow rule keeps the binding metadata below sound; it does not ban
assignment expressions inside ordinary Python expressions, nor imply that
repeated calls or other stateful expressions return equal values.

Using the new name inside its own loop or fill body is the purpose of the
binding, not shadowing. The parser rejects collisions visible from template
syntax. At render time the resolved loop targets and fill binding names are
also checked against the actual template context, which covers component data,
template globals, enclosing loop variables, and names supplied through
`c-bind`.

### 11. Fill-data binding language

A direct `<c-fill data="...">` value is parsed as a small language layered on
top of the general HTML attribute-value grammar. It has two forms:

```text
identifier
{ source, source as target, **rest }
```

The destructuring form is exactly one level. Items require comma separators,
an optional trailing comma is accepted, and whitespace or newlines may appear
between tokens. `**rest` is optional, must be last, and may be the only item.
Every source and target is a valid Python identifier. Source names are unique
by their literal mapping-key spelling. Target names are unique after Python's
NFKC identifier normalization, and overlap across those two categories is
allowed.

The parser stores the result as `FillDataPattern` on the direct `HtmlAttr` and
records every target as an introduced variable. A later `c-bind` clears the
known targets just as it clears a whole-data binding; a later direct `data`
restores them. The compiler emits destructuring as `FillDataBinding` inside the
static attribute value so normal rightmost attribute resolution chooses the
effective provider. Dynamic `c-bind` values cannot contain a destructuring
pattern because their targets would not be available to static scope analysis.

The isolated Pest rules are `fill_data_pattern` through
`fill_data_ws_required`. They are compound atomic so the accepted whitespace
positions are explicit and cannot change with the general grammar's implicit
whitespace behavior.

## Control-flow shortcuts

Control flow can be written two ways: as dedicated tags
(`<c-if cond="...">`, `<c-for each="...">`) or as attributes on ordinary tags
(`<div c-if="...">`, `<div c-for="...">`). The attribute form is the concise
one, in the spirit of Vue's `v-if` / `v-for`. At compile time, a tag carrying a
control-flow attribute is wrapped in the matching control-flow tag:

The valued shortcuts are semantic expressions, even though generic `c-*`
attributes may carry nested templates: `c-if`/`c-elif` require condition
expressions and `c-for` requires a loop clause. `c-else`/`c-empty` are bare
markers; any authored value, including an empty string, is rejected.

1. the control-flow attribute is removed from the original tag,
2. a wrapper tag is created around it,
3. the attribute name is translated to the wrapper's attribute: `c-if` / `c-elif`
   become `cond`, `c-for` becomes `each`, and `c-else` / `c-empty` become the
   boolean (attribute-less) wrapper.

So `<div c-if="ok" class="box">...</div>` becomes
`<c-if cond="ok"><div class="box">...</div></c-if>`.

When a tag has attributes from both groups, they are applied one at a time in
priority order (IF group first, then FOR group), which nests the FOR wrapper
inside the IF wrapper:

```html
<!-- input -->
<div c-if="ok" c-for="item in items">{{ item }}</div>

<!-- result -->
<c-if cond="ok">
  <c-for each="item in items">
    <div>{{ item }}</div>
  </c-for>
</c-if>
```

## For loops

`<c-for>` is parsed as an ordinary tag; its `each` value is handed to the
language layer to parse, not to the Pest grammar. For Python that layer is
Ruff's parser: the `each` value is wrapped in parentheses and parsed as a
comprehension, from which the loop targets and the iterable are extracted (with
their source positions). Anything that is not a comprehension target is an
error. Doing it this way, rather than with a dedicated grammar rule, means the
loop expression is language-specific by construction, which is what the
multi-language design needs (see below).

This buys two features for free from the comprehension form: multiple
generators and `if` filters in one `each`:

```html
<c-for each="user in users if user.active for post in user.posts if post.live">
  <article>{{ post.title }} by {{ user.name }}</article>
</c-for>
```

One deliberate choice: there is no `index` attribute. With multiple generators
an index is ambiguous, so `c-for` accepts only `each`; if you need an index,
build it into the data on the Python side and destructure it into the targets.

The loop's targets are recorded as *introduced* variables and subtracted from
the body's *used* variables, so a template that only reads a loop variable does
not report that variable as an input the caller must supply. This used-vs-
introduced tracking is the same machinery that powers rule 10 and the render
optimizations. Both sets are kept on the node (the introduced names are not
simply discarded), so tooling such as a linter or language server can still link
a use of a loop variable back to the `each` that defines it.

## Multi-language support

The grammar is shared across host languages, but stays Python-native in one
respect: it recognizes Python string literals (`'''`, `"""`, `'`, `"`) and
counts `{ }` so it can find where a `{{ ... }}` expression ends without scanning
the template character by character. Everything *inside* an expression, and the
whole `each` value of a `<c-for>`, is treated as a language-specific black box.

Parsing those black boxes is injected from outside through the `LangImpl` trait,
so a template can be parsed as Python, JS, PHP, or Go by swapping the
implementation. Python is fully implemented (via Ruff); the others are
structural stubs. The trait contract, and which languages are live, are recorded
in the parser crate's
[agent INDEX](../../crates/citry_template_parser/docs/agent/INDEX.md); the
host-binding work is tracked in
[#27](https://github.com/citry-dev/citry/issues/27).

## Deferred: HTML inside expressions (PYX)

A `c-*` attribute can already hold a nested template, which is close to JSX. The
natural generalization is to allow HTML fragments anywhere a Python expression
is expected, including inside `{{ }}`. This is deferred, not planned. The
disambiguation is actually clean (in Python a bare expression never starts with
`<`, so a leading `<` is unambiguously a fragment, unlike JSX in JavaScript),
but the implementation is hard: knowing where an inlined fragment *ends* would
need either a fork of Ruff's Python parser (to hook where it expects an
expression) or a streaming HTML parser to find the fragment's end and hand that
range back to the template parser. The full feasibility analysis is kept as
historical notes; the direction is superseded in practice by the `<c-*>` syntax.
