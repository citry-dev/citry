use ruff_python_ast as ast;
use ruff_python_codegen as codegen;
use ruff_source_file::LineEnding;

/// Generate Python code from a transformed AST expression
pub fn generate_python_code(expr: &ast::Expr) -> String {
    let indentation = codegen::Indentation::default();
    let generator = codegen::Generator::new(&indentation, LineEnding::default());
    generator.expr(expr)
}
