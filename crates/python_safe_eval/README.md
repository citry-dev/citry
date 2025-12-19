# Python safe eval

_Sandbox unsafe Python expressions_

Citry templates support dynamic expressions, similar to Vue, React, Django, and Jinja templates. For example:

```html
<div>{{ 2 + 2 }}</div>
```

Historically, Python web dev ecosystem (Django and Jinja) were designed around the idea that the templates (e.g. HTML, reports, etc) could be written by non-coders. E.g. imagine a WordPress blog post whose content is stored in a database.

This is reflected in their design:

- Django limits what operations are available inside expressions `{{ ... }}`
- Jinja allows for rich expressions, and sandboxes the expressions to keep it safe.

Citry follows the same design pattern as Jinja - Code inside `{{ ... }}` is treated as Python expressions. And these Python expressions are sandboxed to prevent unsafe operations.

This package is a re-implementation of Jinja2's sandboxed evaluation logic, built in Rust using the Ruff Python parser.

It works by:

1. Parsing the Python expression into an AST using `ruff_python_parser`
2. Validating the AST against a set of allowed nodes -> Unsupported syntax raises error.
3. Transforming specific nodes so we can intercept them:

   - Variables → `variable("name")`
   - Function calls → `call(func, *args, **kwargs)`
   - Attributes → `attribute(obj, "attr")`
   - Subscripts → `subscript(obj, key)`
   - Walrus operator → `assign("var", value)`
   - F-strings → `format("...")` calls with transformed arguments
   - T-strings → `template(...)` calls with interpolation objects

   **Example conversions:**

   ```python
   # Before: Simple variable access
   x
   # After:
   variable(context, source, (0, 1), 'x')

   # Before: Function call
   foo(x, 2)
   # After:
   call(context, source, (0, 10), variable(context, source, (0, 3), 'foo'), variable(context, source, (4, 5), 'x'), 2)

   # Before: Attribute access
   obj.attr
   # After:
   attribute(context, source, (0, 8), variable(context, source, (0, 3), 'obj'), 'attr')

   # Before: Complex nested access
   obj.items[key].value
   # After:
   attribute(context, source, (0, 20), subscript(context, source, (0, 14), attribute(context, source, (0, 9), variable(context, source, (0, 3), 'obj'), 'items'), variable(context, source, (10, 13), 'key')), 'value')
   ```

4. Re-generating Python code from the modified AST using `ruff_python_codegen`
5. On the Python side we define `call()`, `variable()`, etc.
   - This is the logic that runs when the target expression uses e.g. function calls.
     Here we implement similar safety measures as Jinja.
6. User receives back a function to evaluate the compiled code.

7. **Runtime**: The generated code is evaluated with sandboxed interceptors that enforce security policies

This package is split in 2 parts:

- The Rust code defined here
- Python code defined in [`packages/py/citry_core/safe_eval`](../../packages/py/citry_core/safe_eval/)

This package serves dual role:

- Transform an expression into a "sandboxed" version
- Support linters by extracting metadata about comments and variables found in the expression

This is why the expression parsing is done in Rust - The linter can be also defined in Rust. No need to run Python.

The collected metadata for the linter includes:

1. What variables were used in the expression
2. What variables were introduced in the expression using walrus operator `x := 1`
3. What comments were found in the expression (including their positions and text)

## Usage

### Basic usage

```python
from citry_core.safe_eval import safe_eval

# Compile an expression into function
expr_func = safe_eval("my_var + 1")

# Evaluate with a context
result = expr_func({"my_var": 5})
print(result)  # 6
```

### More examples

```python
from citry_core.safe_eval import safe_eval

# Conditionals
expr_func = safe_eval(
    "'Login' if not user.authenticated else 'Logout'"
)
result = expr_func({"user": anon_user})
print(result)  # "Login"

# Comprehension
expr_func = safe_eval(
    "[x * 2 for x in items if x > 0]"
)
result = expr_func({"items": [1, 2, -3, 4, 5]})
print(result)  # [2, 4, 8, 10]

# Lambda
expr_func = safe_eval(
    "max(users, key=lambda u: u.last_login)"
)
result = expr_func({
    "users": [User(), ...],
    "max": max,
})
print(result)  # 2025-11-02T15:54:36Z
```

### Assignments

You can use the walrus operator `x := val` to assign a value to the context object. Assigned variable is then accessible to the rest of the expression:

```py
expr_func = safe_eval("(y := x * 2)")
context = {"x": 4}
result = expr_func(context)
print(result)  # 8
print(context)  # {"x": 4, "y": 8}
```

Walrus operator can be used also inside comprehensions or lambdas:

```py
# Comprehension
expr_func = safe_eval("[(x := y) for y in [1, 2, 3]]")
context = {}
result = expr_func(context)
print(context)  # {"x": 3}

# Lambda
expr_func = safe_eval("fn_with_callback(on_done=lambda res: (data := res))")
context = {"fn_with_callback": fn_with_callback}
result = expr_func(context)
print(context)  # {"data": {...}, "fn_with_callback": fn_with_callback},  }
```

> **NOTE: This differs from regular Python, where walrus operator inside a function
> will NOT leak out.**

If you try to assign a variable to the same value as an existing comprehension or
lambda arguments, you will get a SyntaxError:

```py
safe_eval("[(y := y) for y in [1, 2, 3]]")  # SyntaxError
safe_eval("lambda x: (x := 123))")  # SyntaxError
```

### Unsafe operations

Unsafe operations raise `SecurityError`. See all unsafe scenarios in [What is unsafe?](#what-is-unsafe)

```python
# Unsafe functions
expr_func = safe_eval("eval('1+1')")
result = expr_func({"eval": eval})
# SecurityError: unsafe builtin 'eval'
#
#     1 | eval('1+1')
#         ^^^^^^^^^^^

# Private attributes
expr_func = safe_eval("obj._private")
result = expr_func({"obj": MyObject()})
# SecurityError: unsafe attribute '_private'
#
#     1 | obj._private
#         ^^^^^^^^^^^^
```

### Mark functions as unsafe

Use the `@unsafe` decorator to mark functions as unsafe in expressions.

When an unsafe funtion is to be called, `safe_eval()` will raise a `SecurityError`.

This is compatible with Jinja's `@unsafe` decorator.

```py
from citry_core.safe_eval import safe_eval, unsafe

@unsafe
def dump_all_passwords():
    return UserPasswords.objects.all()

expr_func = safe_eval("evil()")
result = expr_func({"evil": dump_all_passwords})
# SecurityError: unsafe function 'dump_all_passwords'
#
#     1 | evil()
#         ^^^^^^
```

### Custom validators

`safe_eval()` has a hard-coded set of scenarios it considers unsafe.

You can extend the validation by providing custom validators.

Return a falsy value from the validator to mark the value as UNSAFE.

Custom validators are run **in addition to** the rules defined in [What is unsafe?](#what-is-unsafe)

| Function             | Signature                             |
| -------------------- | ------------------------------------- |
| `validate_variable`  | `(var_name: str) -> bool`             |
| `validate_attribute` | `(obj: Any, attr: str) -> bool`       |
| `validate_subscript` | `(obj: Any, key: str) -> bool`        |
| `validate_callable`  | `(obj: Any) -> bool`                  |
| `validate_assign`    | `(var_name: str, value: Any) -> bool` |

```python
from citry_core.safe_eval import safe_eval, SecurityError

# Example 1: Custom variable validator
def validate_var(name: str) -> bool:
    return not name.startswith("secret")

expr_func = safe_eval(
    "public_var + secret_var",
    validate_variable=validate_var,
)
result = expr_func({
    "public_var": 1,
    "secret_var": 42,
})
# SecurityError: unsafe variable 'secret_var'
#
#     1 | public_var + secret_var
#                      ^^^^^^^^^^

# Example 2: Custom attribute validator
allowed = {"name", "value", "items"}
def validate_attr(obj: Any, attr: str) -> bool:
    return attr in allowed

expr_func = safe_eval(
    "f'Owner: {obj.owner}'",
    validate_attribute=validate_attr
)
result = expr_func({"obj": MyObject()})
# SecurityError: unsafe attribute 'owner'
#
#     1 | f'Owner: {obj.owner}'
#                   ^^^^^^^^^
```

### Error reporting

When an expression raises an error, the error message includes the position in the expression where the error happened:

```python
from citry_core.safe_eval import safe_eval

expr_func = safe_eval("my_var + undefined_var")
result = expr_func({"my_var": 5})
# NameError: name 'undefined_var' is not defined
#
#     1 | my_var + undefined_var
#                  ^^^^^^^^^^^^^
```

### What is unsafe?

Here's a list of all unsafe scenarios that will trigger `SecurityError`:

- **Unsafe builtins**: `eval`, `exec`, `compile`, `open`, `input`, etc., even if passed under different names.
- **Private attributes**: Starting with `_`
- **Dunder attributes**: Internal Python attributes like `__class__`, `__dict__`, `mro`, etc.
- **Unsafe methods**:
  - Functions decorated with `@unsafe`
  - Django methods marked with `alters_data = True`
  - `str.format` and `str.format_map` (use f-strings instead)
- **Internal attributes**: Prevents access to frame, code, and other internal Python object attributes

## Security and safety considerations

While `safe_eval()` prevents the execution of unsafe code and goes further than Jinja2 or Django's template engine in terms of security (blocking unsafe builtins, private attributes, etc.).

However, it CANNOT protect against all forms of misuse.

### Denial of service (DoS) attacks

Even with all security checks in place, bad actors can still bring a server to a halt by submitting templates with computationally expensive operations. For example, nested loops can force the server to iterate millions of times:

```django
{% comment %}
Sample of how a bad actor could halt the server
if they have access to the template.

This renders 100 entries. It would be extremely simple to wrap this
in extra 4-5 additional loops, forcing the template to iterate 1M times.
{% endcomment %}

{% for i in "abcdefghij" %}
  {% for j in "0123456789" %}
    {{ i }}{{ j }}
  {% endfor %}
{% endfor %}
```

This example renders 100 entries (10 × 10), but adding just 4-5 more nested loops would force the template to iterate over 1 million times, potentially causing the server to become unresponsive.

### Security best practices

**Do not allow end users to write their own Django/Jinja/Citry templates. NEVER.** There is no safe way to allow arbitrary template code from untrusted sources, as even "safe" operations can be used to perform denial of service attacks.

Instead, if you need to allow user customization:

1. **Use pre-defined template blocks**: Provide a set of pre-defined, validated template blocks that users can combine
2. **Validate all inputs**: Ensure that any user-provided data that goes into templates is validated and sanitized
3. **Limit complexity**: Restrict the depth of nesting, number of iterations, or computational complexity allowed

## Syntax features

_This section describes the features enforced on the compiler (Rust) level._

[Statements](https://docs.python.org/3/library/ast.html#statements) are NOT supported (AKA anything that spans multiple lines and uses identation, like `for`, `match`, `with`, etc).

The entire python code must be a SINGLE [expression](https://docs.python.org/3/library/ast.html#expressions). As a rule of thumb, anything that can be assigned to a variable is an expression. So even, `a and b` or `c + d` are both still just a single expression.

For simplicity we don't allow async features like async comprehensions.

### Comments

Python comments (`# ...`) are supported and are captured during parsing. Comments are preserved with their positions and text content, allowing linters and other tools to analyze them.

```python
expr_func = safe_eval("x + 1  # Add one to x")
```

### Multiline expressions

Multiline expressions are supported. When an expression spans multiple lines, it is automatically wrapped in parentheses with newlines: `(\n{}\n)`. This wrapping serves two purposes:

1. **Enables multiline syntax**: In Python, when you're inside parentheses `(...)`, square brackets `[...]`, or curly braces `{...}`, Python ignores indentation and allows expressions to span multiple lines. This means you can write:

   ```python
   [
     1,
       2,
         3,
   ]
   ```

   Without the wrapping, Python would require proper indentation.

2. **Allows trailing comments**: So we wrap the original expression in `(...)`. If used decided to add a comment after the expression, the comment would consume the closing `)`. Hence, we also add newlines so that `(` and `)` are on separate lines:

   ```
   (2 + 2  # comment)      ❌ Comment consumes the ')'
   (\n2 + 2  # comment\n)  ✅ Comment is on separate line
   ```

The wrapping is transparent to users - all token positions (variables, comments, etc.) are automatically adjusted to reference the original unwrapped source positions.

### Supported syntax

Almost anything that is a valid Python expression is allowed:

- **Literals**: strings, numbers (integers, floats, scientific notation), bytes, booleans, `None`, `Ellipsis`
- **Data structures**: lists, tuples, sets, dictionaries
- **String formatting**: f-strings (`f"Hello {name}"`), t-strings (template strings), `%` formatting
- **Operators**:
  - Unary: `+`, `-`, `not`, `~`
  - Binary: `+`, `-`, `*`, `/`, `%`, `**`, `//`, `<<`, `>>`, `&`, `^`, `|`
  - Comparison: `<`, `<=`, `>`, `>=`, `==`, `!=`, `in`, `not in`, `is`, `is not`
  - Boolean: `and`, `or`
- **Comprehensions**: list (`[...]`), set (`{...}`), dict (`{k: v ...}`), generator (`(...)`)
  - Note: Async comprehensions are **not** allowed
- **Conditional expressions**: ternary operator (`x if condition else y`)
- **Variables**: `obj` with security checks
- **Function calls**: with positional, keyword, `*args`, and `**kwargs` arguments
- **Spread operators**: `*args`, `**kwargs` in function calls
- **Attribute access**: `obj.attr` with security checks
- **Subscript access**: `obj[key]` and slice notation `obj[start:end:step]`
- **Lambda functions**: anonymous functions with proper parameter scoping
- **Walrus operator**: `(x := value)` for inline assignments

### Unsupported syntax

- **Statements**: assignments (`=`), augmented assignments (`+=`, `-=`), `del`, `import`, class/function definitions, `return`, `yield`, etc.
- **Async/Await**: async comprehensions, `await` expressions
- **Control Flow**: `if`/`elif`/`else` statements, `for`, `while`, `break`, `continue`, `try`/`except`/`finally`, `with`
- **Builtins**: No built-in functions are available by default (pass them as variables if needed)
- **Type annotations:** `x: int`
- **Class and functions:** `def fn()` or `class Cls`
- **Function-only keywords:** return, yield, global, nonlocal

### Variable scoping

The transformer matches Python's scoping rules for comprehensions and lambdas, but diverges for walrus assignments:

- **Comprehensions**: Variables introduced in comprehensions are local to the comprehension (e.g., `x` in `[x for x in items]`)
- **Lambda parameters**: Lambda parameters are local to the lambda and not transformed
- **Walrus operator**: Walrus assignments remain available outside of comprehensions or lambdas.(diverges from Python)

## Performance

Python expressions with `safe_eval` are 5-8x slower than if the expression was called outside of the template:

```py
fn = safe_eval("a + b * c")
fn({"a": 1, "b": 2, "c": 3})

# vs

fn = lambda ctx: ctx["a"] + ctx["b"] * ctx["c"]
fn({"a": 1, "b": 2, "c": 3})
```

This is the tradeoff for all the security checks that we do, as we have to check safety of each attribute or variable access, or function call.

### Caching performance

I tried to see what would happen if I cached the results, and got about 30-50% improvement. LLM estimated that at 10,000 entries, the cache could take up ~3-5 MB. This would be relevant only to large projects, say with 500 templates, each having total of 20 tags or expressions (`{% ...%}`, `{{ }}`).

- For comparison, my last work project had about ~100 templates, and that was a mid-sized app that I worked on for ~1.5 years.

However, I removed this caching from this final PR. In citry/django-components I think that it will be more meaningful to cache on the level of entire tags and expressions (`{% ...%}`, `{{ }}`), which will make the caching in `safe_eval` irrelevant.

## Development

### Dependencies

This crate depends on several internal crates from the `ruff` project, included as a git submodule:

- [`ruff_python_parser`](https://github.com/astral-sh/ruff/crates/ruff_python_parser) - Python parser
- [`ruff_python_ast`](https://github.com/astral-sh/ruff/crates/ruff_python_ast) - AST types
- [`ruff_python_codegen`](https://github.com/astral-sh/ruff/crates/ruff_python_codegen) - Code generation
- [`ruff_source_file`](https://github.com/astral-sh/ruff/crates/ruff_source_file) - Source file handling
- [`ruff_text_size`](https://github.com/astral-sh/ruff/crates/ruff_text_size) - Text size utilities

These crates are essential for parsing Python code into an AST and manipulating it.

However, there's an issue with using these as upstream dependencies:

1. These crates are not available on [crates.io](https://crates.io/). Their `Cargo.toml` files are marked with `publish = false`.

2. `cargo` allows to specify dependencies as git links ([see docs](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#specifying-dependencies-from-git-repositories)). However, I (Juro) wasn't able to get it working.

   - It seems that `cargo` may be ignoring nested crates if there is `Cargo.toml` at the root. And `ruff`'s codebase does have a root `Cargo.toml`. So we're unable to target the internal crates like `ruff_python_ast`.

So as a workaround solution, we use a **Git submodule** to have access to the `ruff` source code directly in our project.

The `ruff` repository is included as a submodule in `third_party/rust/ruff`. Our `Cargo.toml` uses `path` dependencies to refer to the crates within this submodule.

### Initial setup

When you first clone this repository, the submodule directory will be empty. You must initialize it:

```bash
git submodule update --init --recursive
```

### Updating the ruff dependency

The version of `ruff` is locked to a specific commit or tag, documented in `.gitmodules`. To update:

1. Navigate into the submodule directory:

   ```bash
   cd third_party/rust/ruff
   ```

2. Fetch the latest tags:

   ```bash
   git fetch origin --tags
   ```

3. Check out the new tag (e.g., `0.15.0`):

   ```bash
   git checkout 0.15.0
   ```

4. Navigate back and commit the change:

   ```bash
   cd ../../..
   git add .gitmodules third_party/rust/ruff
   git commit -m "Update Ruff submodule to 0.15.0"
   ```

5. To keep track of the current version, update the comment in the `.gitmodules` file.
