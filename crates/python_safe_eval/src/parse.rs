//! Shared expression validation for evaluation, template analysis and formatting.

use std::collections::HashSet;

use ruff_python_ast::visitor::source_order::{SourceOrderVisitor, walk_expr};
use ruff_python_ast::{Expr, ModExpression};
use ruff_python_parser::{ParseError, ParseErrorType, Parsed};

/// Parse an expression and reject duplicate named arguments before consumers
/// transform or format it. Ruff's parser leaves this check to its semantic pass.
pub fn parse_expression(source: &str) -> Result<Parsed<ModExpression>, ParseError> {
    let parsed = ruff_python_parser::parse_expression(source)?;
    let mut checker = KeywordChecker { error: None };
    checker.visit_expr(&parsed.syntax().body);
    if let Some(error) = checker.error {
        return Err(error);
    }
    Ok(parsed)
}

struct KeywordChecker {
    error: Option<ParseError>,
}

impl<'a> SourceOrderVisitor<'a> for KeywordChecker {
    fn visit_expr(&mut self, expression: &'a Expr) {
        if self.error.is_some() {
            return;
        }
        walk_expr(self, expression);
        if self.error.is_some() {
            return;
        }
        if let Expr::Call(call) = expression {
            let mut names = HashSet::new();
            for keyword in &call.arguments.keywords {
                // Expanded mappings are checked at call time; repeated authored
                // names are a syntax error, using Ruff's normalized identifiers.
                if let Some(name) = &keyword.arg
                    && !names.insert(name.as_str())
                {
                    let name = name.as_str();
                    self.error = Some(ParseError {
                        error: ParseErrorType::OtherError(format!(
                            "Duplicate keyword argument {name:?}"
                        )),
                        location: keyword.range,
                    });
                    return;
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::parse_expression;

    #[test]
    fn rejects_nested_and_normalized_duplicate_names() {
        for source in ["f(x=1, x=2)", "outer(f(x=1, x=2))", "f(K=1, K=2)"] {
            assert!(
                parse_expression(source)
                    .unwrap_err()
                    .to_string()
                    .contains("Duplicate keyword")
            );
        }
    }

    #[test]
    fn preserves_source_order_and_wrapped_unicode_ranges() {
        let error = parse_expression("f(a=g(x=1,x=2), *(h(y=1,y=2)))").unwrap_err();
        assert!(
            error
                .to_string()
                .starts_with("Duplicate keyword argument \"x\"")
        );
        let source = "f('é', x=1, x=2)";
        let wrapped = format!("(\n{source}\n)");
        let error =
            crate::parse_expression_with_adjusted_error_ranges(&wrapped, source, 2).unwrap_err();
        assert!(error.contains("byte range 13..16: 'x=2'"), "{error}");
        assert!(parse_expression("f(x=1, **values, x=2)").is_err());
    }

    #[test]
    fn allows_independent_calls_and_expanded_mappings() {
        for source in ["f(x=1) + f(x=2)", "f(x=1, **values)", "f(**left, **right)"] {
            assert!(parse_expression(source).is_ok());
        }
    }
}
