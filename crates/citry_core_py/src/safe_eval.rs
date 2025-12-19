/// Python interface for the python_safe_eval crate.
use pyo3::exceptions::PySyntaxError;
use pyo3::prelude::*;

use python_safe_eval::safe_eval as safe_eval_rust;

/// Transform a Python expression string to make it safe for evaluation.
///
/// This function takes a Python expression string and transforms it into safe code
/// by wrapping potentially unsafe operations (like variable access, function calls,
/// attribute access, etc.) with sandboxed function calls.
///
/// **Args:**
///
/// - source (str): The Python expression string to transform.
///
/// **Returns:**
///
/// - str: The transformed Python expression as a string.
///
/// **Raises:**
///
/// - SyntaxError: If the input is not valid Python syntax or contains forbidden constructs.
///
/// **Examples:**
///
///     >>> safe_eval("my_var + 1")
///     'variable("my_var") + 1'
///
///     >>> safe_eval("lambda x: x + my_var")
///     'lambda x: x + variable("my_var")'
///
/// **Transformations:**
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
#[pyfunction]
#[pyo3(signature = (source))]
pub fn safe_eval(source: &str) -> PyResult<String> {
    let result = safe_eval_rust(source).map_err(|e| PySyntaxError::new_err(e.to_string()))?;
    Ok(result)
}
