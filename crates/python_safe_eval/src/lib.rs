pub mod codegen;
pub mod comments;
pub mod transformer;
mod utils {
    pub mod python_ast;
}

// Re-export public API
pub use codegen::generate_python_code;
pub use comments::extract_comments;
pub use transformer::{
    Comment, Token, TransformResult, parse_expression_with_adjusted_error_ranges,
    transform_expression_string,
};

/// Transform potentially unsafe Python expression into a safe one.
///
/// This function:
/// 1. Parses the Python expression into an AST
/// 2. Validates that the AST contains only a set of allowed nodes
/// 3. Transforms unsafe syntax patterns / nodes into safe ones so we can intercept them.
///    E.g. `foo(1)` -> `call(foo, 1)`
/// 4. Re-generates the now-modified Python code from the modified AST
/// 5. Returns the generated code
///
/// If the expression is invalid, returns an error.
///
/// ### Examples
///
/// ```rust
/// let result = safe_eval("1 + my_var.foo");
/// assert_eq!(result, Ok("1 + variable(attribute(my_var, 'foo'))".to_string()));
/// ```
///
/// ### Transformations
///
/// The following transformations are applied to make expressions safe for evaluation:
///
/// 1. **Variable access** - `my_var` → `variable("my_var")`
/// 2. **Function calls** - `foo(1, 2, a=3, *args, **kwargs)` → `call(foo, 1, 2, a=x, *args, **kwargs)`
/// 3. **Attribute access** - `obj.attr` → `attribute(obj, "attr")`
/// 4. **Subscript access** - `obj[key]` → `subscript(obj, key)`
/// 5. **Walrus operator** - `(x := value)` → `assign("x", value)`
///
/// Because of the changes above, we also need to transform:
///
/// 6. **Slice notation** - `obj[1:10:2]` → `subscript(obj, slice(1, 10, 2))`
///    - Because slice syntax is valid only inside square brackets.
/// 7. **F-strings** - `f"Hello {price!r:.2f}"` → `format("Hello {}", (variable("price"), "r", ".2f"))`
///    - To avoid issues with quote escaping and enable error reporting
/// 8. **T-strings** - `t"Hello {name!r:>10}"` → `template("Hello ", interpolation(variable("name"), "expr", "r", ">10"))`
///    - To avoid issues with quote escaping
pub fn safe_eval(source: &str) -> Result<String, String> {
    let result = transform_expression_string(source)?;
    let generated_code = codegen::generate_python_code(&result.expression);
    Ok(generated_code)
}
