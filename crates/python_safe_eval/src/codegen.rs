use ruff_python_ast as ast;
use ruff_python_codegen as codegen;
use ruff_source_file::LineEnding;

use crate::stack::with_enough_stack;

/// Generate Python code from a transformed AST expression
pub fn generate_python_code(expr: &ast::Expr) -> String {
    // Ruff's code generator calls itself once per tree level, so give it
    // enough stack on any thread (see `stack.rs`).
    with_enough_stack(|| {
        let indentation = codegen::Indentation::default();
        let generator = codegen::Generator::new(&indentation, LineEnding::default());
        generator.expr(expr)
    })
}
