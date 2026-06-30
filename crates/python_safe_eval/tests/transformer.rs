#[cfg(test)]
mod tests {
    use python_safe_eval::codegen::generate_python_code;
    use python_safe_eval::transformer::{Comment, Token, transform_expression_string};

    fn _test_transformation(
        input: &str,
        expected: &str,
        expected_used_vars: Vec<(&str, usize, usize, (usize, usize))>, // (content, start_index, end_index, (line, col))
        expected_assigned_vars: Vec<(&str, usize, usize, (usize, usize))>, // (content, start_index, end_index, (line, col))
    ) {
        let result = transform_expression_string(input);
        assert!(result.is_ok());
        let transform_result = result.unwrap();
        let generated = generate_python_code(&transform_result.expression);
        assert_eq!(generated, expected);

        // Assert used variables with full token information
        let actual_used_vars: Vec<(&str, usize, usize, (usize, usize))> = transform_result
            .used_vars
            .iter()
            .map(|token| {
                (
                    token.content.as_str(),
                    token.start_index,
                    token.end_index,
                    token.line_col,
                )
            })
            .collect();
        assert_eq!(
            actual_used_vars, expected_used_vars,
            "Used variables mismatch for input: {}",
            input
        );

        // Assert assigned variables with full token information
        let actual_assigned_vars: Vec<(&str, usize, usize, (usize, usize))> = transform_result
            .assigned_vars
            .iter()
            .map(|token| {
                (
                    token.content.as_str(),
                    token.start_index,
                    token.end_index,
                    token.line_col,
                )
            })
            .collect();
        assert_eq!(
            actual_assigned_vars, expected_assigned_vars,
            "Assigned variables mismatch for input: {}",
            input
        );
    }

    fn _test_forbidden_syntax(input: &str) {
        let result = transform_expression_string(input);
        if let Ok(transform_result) = &result {
            // If transformation succeeded, print the result to help debug
            let generated = generate_python_code(&transform_result.expression);
            panic!(
                "Expected transformation to fail, but it succeeded.\nInput: {}\nGenerated code: {}",
                input, generated
            );
        }
        let error = result.unwrap_err();
        if !error.contains("Parse error")
            && !error.contains("Unexpected token")
            && !error.contains("SyntaxError")
        {
            panic!(
                "Expected error to contain 'Parse error', 'Unexpected token', or 'SyntaxError', but got:\nInput: {}\nError: {}",
                input, error
            );
        }
    }

    #[test]
    fn test_multiple_lines() {
        // NOTE: Altho we could technically handle this, we allow only a single expression,
        //       and this contains 2 statements/expressions, which raises an error.
        //       In this case the actual error message doesn't matter that much, as long as we raise here.
        let result = transform_expression_string("x\n y").unwrap_err();
        assert_eq!(
            result,
            "Parse error: Expected `)`, found name at byte range 3..4: 'y'"
        );
    }

    // Check if it's possible to escape the multiline restriction by closing the first parenthesis.
    // This tries to exploit the fact that we wrap the entire expression in extra parentheses.
    #[test]
    fn test_multiple_lines_escape_1() {
        let result = transform_expression_string("x)\n\nimport os; os.path.join('a', 'b')\n\n(")
            .unwrap_err();
        assert_eq!(
            result,
            "Parse error: Unexpected token at the end of an expression at byte range 4..10: 'import'"
        );
    }

    // This is the most that the logic can be "exploited" - constructing an expression
    // that makes use of the hidden parentheses.
    // So while `lambda x: x + 2)(5` would raise a syntax error in Python, since we wrap it
    // in parentheses, we actually end up with `(lambda x: x + 2)(5)`, which is valid.
    #[test]
    fn test_multiple_lines_escape_2() {
        _test_transformation(
            "lambda x: x + 2)(5",
            "call(context, source, (0, 20), lambda x: x + 2, 5)",
            vec![],
            vec![],
        );
    }

    // However, it's still not possible to construct an expression that contains a statement,
    // as this test shows.
    #[test]
    fn test_multiple_lines_escape_3() {
        let result = transform_expression_string("def fn(x): x + 2)(5").unwrap_err();
        assert_eq!(
            result,
            "Parse error: Expected an identifier, but found a keyword `def` that cannot be used here at byte range 0..3: 'def'"
        );
    }

    #[test]
    fn test_allow_comments() {
        _test_transformation("1 # comment", "1", vec![], vec![]);
    }

    // === LITERAL TESTS ===

    #[test]
    fn test_allow_literal_string() {
        _test_transformation("\"hello world\"", "\"hello world\"", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_bytes() {
        _test_transformation("b'hello'", "b'hello'", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_integer() {
        _test_transformation("42", "42", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_integer_negative() {
        _test_transformation("-42", "-42", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_float() {
        _test_transformation("3.14", "3.14", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_float_negative() {
        _test_transformation("-3.14", "-3.14", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_float_scientific() {
        _test_transformation("-1e10", "-10000000000.0", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_boolean_true() {
        _test_transformation("True", "True", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_boolean_false() {
        _test_transformation("False", "False", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_none() {
        _test_transformation("None", "None", vec![], vec![]);
    }

    #[test]
    fn test_allow_literal_ellipsis() {
        _test_transformation("...", "...", vec![], vec![]);
    }

    // === DATA STRUCTURE TESTS ===

    #[test]
    fn test_allow_list_empty() {
        _test_transformation("[]", "[]", vec![], vec![]);
    }

    #[test]
    fn test_allow_list_with_literals() {
        _test_transformation("[1, 2, 3]", "[1, 2, 3]", vec![], vec![]);
    }

    #[test]
    fn test_allow_multiline_expr() {
        // Note: The code generator doesn't preserve formatting, so output is on one line
        _test_transformation("[\n  1,\n  2,\n  3\n]", "[1, 2, 3]", vec![], vec![]);
    }

    #[test]
    fn test_allow_multiline_with_variables() {
        // Note: The code generator doesn't preserve formatting, so output is on one line
        _test_transformation(
            "[\n  x,\n  y,\n  z\n]",
            "[variable(context, source, (4, 5), 'x'), variable(context, source, (9, 10), 'y'), variable(context, source, (14, 15), 'z')]",
            vec![
                ("x", 4, 5, (2, 3)),
                ("y", 9, 10, (3, 3)),
                ("z", 14, 15, (4, 3)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_allow_tuple_empty() {
        _test_transformation("()", "()", vec![], vec![]);
    }

    #[test]
    fn test_allow_tuple_with_literals() {
        _test_transformation("(1, 2, 3)", "1, 2, 3", vec![], vec![]);
    }

    // NOTE: As can be seen below, it's not possible to construct empty
    // sets, because `set` will be interpreted as a variable and replaced
    // with `variable('set', context)`.
    #[test]
    fn test_allow_set_empty() {
        _test_transformation(
            "set()",
            "call(context, source, (0, 5), variable(context, source, (0, 3), 'set'))",
            vec![("set", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_allow_set_literal() {
        _test_transformation("{1, 2, 3}", "{1, 2, 3}", vec![], vec![]);
    }

    #[test]
    fn test_allow_dict_empty() {
        _test_transformation("{}", "{}", vec![], vec![]);
    }

    #[test]
    fn test_allow_dict_with_literals() {
        _test_transformation("{'a': 1, 'b': 2}", "{'a': 1, 'b': 2}", vec![], vec![]);
    }

    #[test]
    fn test_allow_nested_data_structures() {
        _test_transformation(
            "[1, [2, 3], {'a': 4}]",
            "[1, [2, 3], {'a': 4}]",
            vec![],
            vec![],
        );
    }

    // === UNARY OPERATOR TESTS ===

    #[test]
    fn test_allow_unary_plus() {
        _test_transformation("+42", "+42", vec![], vec![]);
    }

    #[test]
    fn test_allow_unary_minus() {
        _test_transformation("-42", "-42", vec![], vec![]);
    }

    #[test]
    fn test_allow_unary_not() {
        _test_transformation("not True", "not True", vec![], vec![]);
    }

    #[test]
    fn test_allow_unary_invert() {
        _test_transformation("~42", "~42", vec![], vec![]);
    }

    #[test]
    fn test_allow_nested_unary_operators() {
        _test_transformation("--42", "--42", vec![], vec![]);
    }

    // === BINARY OPERATOR TESTS ===

    #[test]
    fn test_allow_binary_add() {
        _test_transformation("1 + 2", "1 + 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_subtract() {
        _test_transformation("5 - 3", "5 - 3", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_multiply() {
        _test_transformation("4 * 5", "4 * 5", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_divide() {
        _test_transformation("10 / 2", "10 / 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_modulo() {
        _test_transformation("10 % 3", "10 % 3", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_power() {
        _test_transformation("2 ** 3", "2 ** 3", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_equality() {
        _test_transformation("1 == 1", "1 == 1", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_inequality() {
        _test_transformation("1 != 2", "1 != 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_less_than() {
        _test_transformation("1 < 2", "1 < 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_greater_than() {
        _test_transformation("3 > 2", "3 > 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_less_equal() {
        _test_transformation("2 <= 3", "2 <= 3", vec![], vec![]);
    }

    #[test]
    fn test_allow_binary_greater_equal() {
        _test_transformation("3 >= 2", "3 >= 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_nested_binary_operations() {
        _test_transformation("1 + 2 * 3", "1 + 2 * 3", vec![], vec![]);
    }

    // Boolean operator tests
    #[test]
    fn test_allow_boolean_and() {
        _test_transformation("True and False", "True and False", vec![], vec![]);
    }

    #[test]
    fn test_allow_boolean_or() {
        _test_transformation("True or False", "True or False", vec![], vec![]);
    }

    #[test]
    fn test_allow_boolean_chained_and() {
        _test_transformation(
            "True and False and True",
            "True and False and True",
            vec![],
            vec![],
        );
    }

    #[test]
    fn test_allow_boolean_chained_or() {
        _test_transformation(
            "False or True or False",
            "False or True or False",
            vec![],
            vec![],
        );
    }

    #[test]
    fn test_allow_boolean_mixed_operators() {
        _test_transformation(
            "True and False or True",
            "True and False or True",
            vec![],
            vec![],
        );
    }

    #[test]
    fn test_allow_boolean_with_comparisons() {
        _test_transformation("1 < 2 and 3 > 4", "1 < 2 and 3 > 4", vec![], vec![]);
    }

    // Comparison operator tests

    #[test]
    fn test_allow_comparison_less_than() {
        _test_transformation("1 < 2", "1 < 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_less_equal() {
        _test_transformation("1 <= 2", "1 <= 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_greater_than() {
        _test_transformation("3 > 2", "3 > 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_greater_equal() {
        _test_transformation("3 >= 2", "3 >= 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_equality() {
        _test_transformation("1 == 1", "1 == 1", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_inequality() {
        _test_transformation("1 != 2", "1 != 2", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_in() {
        _test_transformation("1 in [1, 2, 3]", "1 in [1, 2, 3]", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_not_in() {
        _test_transformation("4 not in [1, 2, 3]", "4 not in [1, 2, 3]", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_is() {
        _test_transformation(
            "x is None",
            "variable(context, source, (0, 1), 'x') is None",
            vec![("x", 0, 1, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_allow_comparison_is_not() {
        _test_transformation(
            "x is not None",
            "variable(context, source, (0, 1), 'x') is not None",
            vec![("x", 0, 1, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_allow_comparison_chained() {
        _test_transformation("1 < 2 < 3", "1 < 2 < 3", vec![], vec![]);
    }

    #[test]
    fn test_allow_comparison_mixed_types() {
        _test_transformation("'hello' == 'world'", "'hello' == 'world'", vec![], vec![]);
    }

    // === COMPREHENSION TESTS ===

    #[test]
    fn test_allow_list_comprehension() {
        _test_transformation(
            "[x for x in items]",
            "[x for x in variable(context, source, (12, 17), 'items')]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_allow_list_comprehension_with_condition() {
        _test_transformation(
            "[x for x in items if x > 0]",
            "[x for x in variable(context, source, (12, 17), 'items') if x > 0]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_allow_list_comprehension_complex() {
        // Test list comprehension with:
        // - Multiple 'for' clauses
        // - Multiple 'if' conditions
        // - Mix of local variables (x, y) and external variables (items, multiplier, min_val, max_val)
        _test_transformation(
            "[x * y * multiplier for x in items for y in x.values if x > min_val if y < max_val]",
            "[x * y * variable(context, source, (9, 19), 'multiplier') for x in variable(context, source, (29, 34), 'items') for y in attribute(context, source, (44, 52), x, 'values') if x > variable(context, source, (60, 67), 'min_val') if y < variable(context, source, (75, 82), 'max_val')]",
            vec![
                ("multiplier", 9, 19, (1, 10)),
                ("items", 29, 34, (1, 30)),
                ("min_val", 60, 67, (1, 61)),
                ("max_val", 75, 82, (1, 76)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_forbid_async_list_comprehension() {
        let result = transform_expression_string("[x async for x in items]");
        assert!(result.is_err());
        let error = result.unwrap_err();
        assert!(error.contains("Async comprehensions are not allowed"));
    }

    #[test]
    fn test_allow_set_comprehension() {
        _test_transformation(
            "{x for x in items}",
            "{x for x in variable(context, source, (12, 17), 'items')}",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_forbid_async_set_comprehension() {
        let result = transform_expression_string("{x async for x in items}");
        assert!(result.is_err());
        let error = result.unwrap_err();
        assert!(error.contains("Async comprehensions are not allowed"));
    }

    #[test]
    fn test_allow_dict_comprehension() {
        _test_transformation(
            "{x: x*2 for x in items}",
            "{x: x * 2 for x in variable(context, source, (17, 22), 'items')}",
            vec![("items", 17, 22, (1, 18))],
            vec![],
        );
    }

    #[test]
    fn test_forbid_async_dict_comprehension() {
        let result = transform_expression_string("{x: x*2 async for x in items}");
        assert!(result.is_err());
        let error = result.unwrap_err();
        assert!(error.contains("Async comprehensions are not allowed"));
    }

    #[test]
    fn test_allow_generator_expression() {
        _test_transformation(
            "(x for x in items)",
            "(x for x in variable(context, source, (12, 17), 'items'))",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_forbid_async_generator_expression() {
        let result = transform_expression_string("(x async for x in items)");
        assert!(result.is_err());
        let error = result.unwrap_err();
        assert!(error.contains("Async comprehensions are not allowed"));
    }

    #[test]
    fn test_allow_multiple_comprehensions() {
        _test_transformation(
            "[x for x in items for y in x.children]",
            "[x for x in variable(context, source, (12, 17), 'items') for y in attribute(context, source, (27, 37), x, 'children')]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_allow_comprehension_with_multiple_conditions() {
        _test_transformation(
            "[x for x in items if x > 0 if x < 10]",
            "[x for x in variable(context, source, (12, 17), 'items') if x > 0 if x < 10]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_allow_nested_comprehension() {
        _test_transformation(
            "[[x for x in row] for row in matrix]",
            "[[x for x in row] for row in variable(context, source, (29, 35), 'matrix')]",
            vec![("matrix", 29, 35, (1, 30))],
            vec![],
        );
    }

    // === FUNCTION CALL TESTS ===

    #[test]
    fn test_transform_function_call_simple() {
        _test_transformation(
            "foo()",
            "call(context, source, (0, 5), variable(context, source, (0, 3), 'foo'))",
            vec![("foo", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_positional_args() {
        _test_transformation(
            "foo(x, 2, 3)",
            "call(context, source, (0, 12), variable(context, source, (0, 3), 'foo'), variable(context, source, (4, 5), 'x'), 2, 3)",
            vec![("foo", 0, 3, (1, 1)), ("x", 4, 5, (1, 5))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_keyword_args() {
        _test_transformation(
            "foo(a=1, b=x)",
            "call(context, source, (0, 13), variable(context, source, (0, 3), 'foo'), a=1, b=variable(context, source, (11, 12), 'x'))",
            vec![("foo", 0, 3, (1, 1)), ("x", 11, 12, (1, 12))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_mixed_args() {
        _test_transformation(
            "foo(1, x, a=y, b=4)",
            "call(context, source, (0, 19), variable(context, source, (0, 3), 'foo'), 1, variable(context, source, (7, 8), 'x'), a=variable(context, source, (12, 13), 'y'), b=4)",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("x", 7, 8, (1, 8)),
                ("y", 12, 13, (1, 13)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_nested_function_calls() {
        _test_transformation(
            "foo(bar(1, x))",
            "call(context, source, (0, 14), variable(context, source, (0, 3), 'foo'), call(context, source, (4, 13), variable(context, source, (4, 7), 'bar'), 1, variable(context, source, (11, 12), 'x')))",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("bar", 4, 7, (1, 5)),
                ("x", 11, 12, (1, 12)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_method_call() {
        _test_transformation(
            "obj.method()",
            "call(context, source, (0, 12), attribute(context, source, (0, 10), variable(context, source, (0, 3), 'obj'), 'method'))",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_variable_args() {
        _test_transformation(
            "foo(x, y, z)",
            "call(context, source, (0, 12), variable(context, source, (0, 3), 'foo'), variable(context, source, (4, 5), 'x'), variable(context, source, (7, 8), 'y'), variable(context, source, (10, 11), 'z'))",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("x", 4, 5, (1, 5)),
                ("y", 7, 8, (1, 8)),
                ("z", 10, 11, (1, 11)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_variable_kwargs() {
        _test_transformation(
            "foo(a=x, b=y)",
            "call(context, source, (0, 13), variable(context, source, (0, 3), 'foo'), a=variable(context, source, (6, 7), 'x'), b=variable(context, source, (11, 12), 'y'))",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("x", 6, 7, (1, 7)),
                ("y", 11, 12, (1, 12)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_spread_args() {
        _test_transformation(
            "foo(*args)",
            "call(context, source, (0, 10), variable(context, source, (0, 3), 'foo'), *variable(context, source, (5, 9), 'args'))",
            vec![("foo", 0, 3, (1, 1)), ("args", 5, 9, (1, 6))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_spread_kwargs() {
        _test_transformation(
            "foo(**kwargs)",
            "call(context, source, (0, 13), variable(context, source, (0, 3), 'foo'), **variable(context, source, (6, 12), 'kwargs'))",
            vec![("foo", 0, 3, (1, 1)), ("kwargs", 6, 12, (1, 7))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_mixed_spreads() {
        _test_transformation(
            "foo(1, *args, a=2, **kwargs)",
            "call(context, source, (0, 28), variable(context, source, (0, 3), 'foo'), 1, *variable(context, source, (8, 12), 'args'), a=2, **variable(context, source, (21, 27), 'kwargs'))",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("args", 8, 12, (1, 9)),
                ("kwargs", 21, 27, (1, 22)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_with_nested_call_as_arg() {
        _test_transformation(
            "foo(a=get_item())",
            "call(context, source, (0, 17), variable(context, source, (0, 3), 'foo'), a=call(context, source, (6, 16), variable(context, source, (6, 14), 'get_item')))",
            vec![("foo", 0, 3, (1, 1)), ("get_item", 6, 14, (1, 7))],
            vec![],
        );
    }

    #[test]
    fn test_transform_function_call_complex_signature() {
        _test_transformation(
            "foo(x, y, 3, *args, a=get_item(), b=5, **kwargs)",
            "call(context, source, (0, 48), variable(context, source, (0, 3), 'foo'), variable(context, source, (4, 5), 'x'), variable(context, source, (7, 8), 'y'), 3, *variable(context, source, (14, 18), 'args'), a=call(context, source, (22, 32), variable(context, source, (22, 30), 'get_item')), b=5, **variable(context, source, (41, 47), 'kwargs'))",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("x", 4, 5, (1, 5)),
                ("y", 7, 8, (1, 8)),
                ("args", 14, 18, (1, 15)),
                ("get_item", 22, 30, (1, 23)),
                ("kwargs", 41, 47, (1, 42)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_as_callable() {
        _test_transformation(
            "my_func(1, 2)",
            "call(context, source, (0, 13), variable(context, source, (0, 7), 'my_func'), 1, 2)",
            vec![("my_func", 0, 7, (1, 1))],
            vec![],
        );
    }

    // === ATTRIBUTE ACCESS TESTS ===

    #[test]
    fn test_transform_attribute_access_simple() {
        _test_transformation(
            "obj.attr",
            "attribute(context, source, (0, 8), variable(context, source, (0, 3), 'obj'), 'attr')",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_attribute_access_chained() {
        _test_transformation(
            "obj.foo.bar",
            "attribute(context, source, (0, 11), attribute(context, source, (0, 7), variable(context, source, (0, 3), 'obj'), 'foo'), 'bar')",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_attribute_access_with_method_call() {
        _test_transformation(
            "obj.method()",
            "call(context, source, (0, 12), attribute(context, source, (0, 10), variable(context, source, (0, 3), 'obj'), 'method'))",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_attribute_access_with_args() {
        _test_transformation(
            "obj.method(1, x)",
            "call(context, source, (0, 16), attribute(context, source, (0, 10), variable(context, source, (0, 3), 'obj'), 'method'), 1, variable(context, source, (14, 15), 'x'))",
            vec![("obj", 0, 3, (1, 1)), ("x", 14, 15, (1, 15))],
            vec![],
        );
    }

    #[test]
    fn test_transform_nested_attribute_method_call() {
        _test_transformation(
            "obj.foo.bar.baz()",
            "call(context, source, (0, 17), attribute(context, source, (0, 15), attribute(context, source, (0, 11), attribute(context, source, (0, 7), variable(context, source, (0, 3), 'obj'), 'foo'), 'bar'), 'baz'))",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_attribute_in_expression() {
        _test_transformation(
            "obj.value + 10",
            "attribute(context, source, (0, 9), variable(context, source, (0, 3), 'obj'), 'value') + 10",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_attribute_in_comprehension() {
        _test_transformation(
            "[item.name for item in items]",
            "[attribute(context, source, (1, 10), item, 'name') for item in variable(context, source, (23, 28), 'items')]",
            vec![("items", 23, 28, (1, 24))],
            vec![],
        );
    }

    // NOTE: The transformation happens, but the runtime `attribute()` function
    // will be responsible for blocking access to _private attributes
    #[test]
    fn test_transform_attribute_with_underscore() {
        _test_transformation(
            "obj._private",
            "attribute(context, source, (0, 12), variable(context, source, (0, 3), 'obj'), '_private')",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    // NOTE: The transformation happens, but the runtime `attribute()` function
    // will be responsible for blocking access to __dunder__ attributes
    #[test]
    fn test_transform_attribute_with_dunder() {
        _test_transformation(
            "obj.__class__",
            "attribute(context, source, (0, 13), variable(context, source, (0, 3), 'obj'), '__class__')",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    // === SUBSCRIPT ACCESS TESTS ===

    #[test]
    fn test_transform_subscript_access_simple() {
        _test_transformation(
            "obj[0]",
            "subscript(context, source, (0, 6), variable(context, source, (0, 3), 'obj'), 0)",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_access_with_variable_key() {
        _test_transformation(
            "obj[key]",
            "subscript(context, source, (0, 8), variable(context, source, (0, 3), 'obj'), variable(context, source, (4, 7), 'key'))",
            vec![("obj", 0, 3, (1, 1)), ("key", 4, 7, (1, 5))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_access_with_string_key() {
        _test_transformation(
            "obj['name']",
            "subscript(context, source, (0, 11), variable(context, source, (0, 3), 'obj'), 'name')",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_access_chained() {
        _test_transformation(
            "obj[0][1]",
            "subscript(context, source, (0, 9), subscript(context, source, (0, 6), variable(context, source, (0, 3), 'obj'), 0), 1)",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_access_with_expression_key() {
        _test_transformation(
            "obj[x + 1]",
            "subscript(context, source, (0, 10), variable(context, source, (0, 3), 'obj'), variable(context, source, (4, 5), 'x') + 1)",
            vec![("obj", 0, 3, (1, 1)), ("x", 4, 5, (1, 5))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_access_in_expression() {
        _test_transformation(
            "obj[0] + 10",
            "subscript(context, source, (0, 6), variable(context, source, (0, 3), 'obj'), 0) + 10",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_access_in_comprehension() {
        _test_transformation(
            "[item[0] for item in items]",
            "[subscript(context, source, (1, 8), item, 0) for item in variable(context, source, (21, 26), 'items')]",
            vec![("items", 21, 26, (1, 22))],
            vec![],
        );
    }

    #[test]
    fn test_transform_mixed_attribute_and_subscript() {
        _test_transformation(
            "obj.items[0]",
            "subscript(context, source, (0, 12), attribute(context, source, (0, 9), variable(context, source, (0, 3), 'obj'), 'items'), 0)",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_then_attribute() {
        _test_transformation(
            "obj[0].name",
            "attribute(context, source, (0, 11), subscript(context, source, (0, 6), variable(context, source, (0, 3), 'obj'), 0), 'name')",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_subscript_with_method_call() {
        _test_transformation(
            "obj[0].method()",
            "call(context, source, (0, 15), attribute(context, source, (0, 13), subscript(context, source, (0, 6), variable(context, source, (0, 3), 'obj'), 0), 'method'))",
            vec![("obj", 0, 3, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_complex_nested_access() {
        _test_transformation(
            "obj.items[key].value",
            "attribute(context, source, (0, 20), subscript(context, source, (0, 14), attribute(context, source, (0, 9), variable(context, source, (0, 3), 'obj'), 'items'), variable(context, source, (10, 13), 'key')), 'value')",
            vec![("obj", 0, 3, (1, 1)), ("key", 10, 13, (1, 11))],
            vec![],
        );
    }

    // === SLICE TESTS ===

    #[test]
    fn test_transform_slice_start_stop() {
        _test_transformation(
            "list[1:x]",
            "subscript(context, source, (0, 9), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 8), 1, variable(context, source, (7, 8), 'x'), None))",
            vec![("list", 0, 4, (1, 1)), ("x", 7, 8, (1, 8))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_stop_only() {
        _test_transformation(
            "list[:x]",
            "subscript(context, source, (0, 8), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 7), None, variable(context, source, (6, 7), 'x'), None))",
            vec![("list", 0, 4, (1, 1)), ("x", 6, 7, (1, 7))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_start_only() {
        _test_transformation(
            "list[1:]",
            "subscript(context, source, (0, 8), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 7), 1, None, None))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_all() {
        _test_transformation(
            "list[:]",
            "subscript(context, source, (0, 7), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 6), None, None, None))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_with_step() {
        _test_transformation(
            "list[::]",
            "subscript(context, source, (0, 8), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 7), None, None, None))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_reverse() {
        _test_transformation(
            "list[::-1]",
            "subscript(context, source, (0, 10), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 9), None, None, -1))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_full() {
        _test_transformation(
            "list[1:-2:1]",
            "subscript(context, source, (0, 12), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 11), 1, -2, 1))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_start_with_step() {
        _test_transformation(
            "list[1::]",
            "subscript(context, source, (0, 9), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 8), 1, None, None))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_start_stop_with_step() {
        _test_transformation(
            "list[1:2:]",
            "subscript(context, source, (0, 10), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 9), 1, 2, None))",
            vec![("list", 0, 4, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_with_variables() {
        _test_transformation(
            "list[start:end:step]",
            "subscript(context, source, (0, 20), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 19), variable(context, source, (5, 10), 'start'), variable(context, source, (11, 14), 'end'), variable(context, source, (15, 19), 'step')))",
            vec![
                ("list", 0, 4, (1, 1)),
                ("start", 5, 10, (1, 6)),
                ("end", 11, 14, (1, 12)),
                ("step", 15, 19, (1, 16)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_with_expressions() {
        _test_transformation(
            "list[x + 1:y - 1]",
            "subscript(context, source, (0, 17), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 16), variable(context, source, (5, 6), 'x') + 1, variable(context, source, (11, 12), 'y') - 1, None))",
            vec![
                ("list", 0, 4, (1, 1)),
                ("x", 5, 6, (1, 6)),
                ("y", 11, 12, (1, 12)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_with_function_call() {
        _test_transformation(
            "list[get_start():get_end()]",
            "subscript(context, source, (0, 27), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 26), call(context, source, (5, 16), variable(context, source, (5, 14), 'get_start')), call(context, source, (17, 26), variable(context, source, (17, 24), 'get_end')), None))",
            vec![
                ("list", 0, 4, (1, 1)),
                ("get_start", 5, 14, (1, 6)),
                ("get_end", 17, 24, (1, 18)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_slice_with_attribute_access() {
        _test_transformation(
            "list[obj.start:obj.end]",
            "subscript(context, source, (0, 23), variable(context, source, (0, 4), 'list'), slice(context, source, (5, 22), attribute(context, source, (5, 14), variable(context, source, (5, 8), 'obj'), 'start'), attribute(context, source, (15, 22), variable(context, source, (15, 18), 'obj'), 'end'), None))",
            vec![
                ("list", 0, 4, (1, 1)),
                ("obj", 5, 8, (1, 6)),
                ("obj", 15, 18, (1, 16)),
            ],
            vec![],
        );
    }

    // === WALRUS OPERATOR (NAMED EXPRESSION) TESTS ===

    #[test]
    fn test_transform_walrus_simple() {
        _test_transformation(
            "(x := 5)",
            "assign(context, source, (1, 7), 'x', 5)",
            vec![],
            vec![("x", 1, 2, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_with_variable() {
        _test_transformation(
            "(x := y)",
            "assign(context, source, (1, 7), 'x', variable(context, source, (6, 7), 'y'))",
            vec![("y", 6, 7, (1, 7))],
            vec![("x", 1, 2, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_with_expression() {
        _test_transformation(
            "(x := y + 1)",
            "assign(context, source, (1, 11), 'x', variable(context, source, (6, 7), 'y') + 1)",
            vec![("y", 6, 7, (1, 7))],
            vec![("x", 1, 2, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_with_function_call() {
        _test_transformation(
            "(result := get_value())",
            "assign(context, source, (1, 22), 'result', call(context, source, (11, 22), variable(context, source, (11, 20), 'get_value')))",
            vec![("get_value", 11, 20, (1, 12))],
            vec![("result", 1, 7, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_with_attribute_access() {
        _test_transformation(
            "(x := obj.value)",
            "assign(context, source, (1, 15), 'x', attribute(context, source, (6, 15), variable(context, source, (6, 9), 'obj'), 'value'))",
            vec![("obj", 6, 9, (1, 7))],
            vec![("x", 1, 2, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_in_if_expression() {
        _test_transformation(
            "(x := get_value()) if (x := get_value()) else 0",
            "assign(context, source, (1, 17), 'x', call(context, source, (6, 17), variable(context, source, (6, 15), 'get_value'))) if assign(context, source, (23, 39), 'x', call(context, source, (28, 39), variable(context, source, (28, 37), 'get_value'))) else 0",
            vec![("get_value", 6, 15, (1, 7)), ("get_value", 28, 37, (1, 29))],
            vec![("x", 1, 2, (1, 2)), ("x", 23, 24, (1, 24))],
        );
    }

    #[test]
    fn test_transform_walrus_in_comprehension() {
        _test_transformation(
            "[y for x in items if (y := x.value)]",
            "[variable(context, source, (1, 2), 'y') for x in variable(context, source, (12, 17), 'items') if assign(context, source, (22, 34), 'y', attribute(context, source, (27, 34), x, 'value'))]",
            vec![("y", 1, 2, (1, 2)), ("items", 12, 17, (1, 13))],
            vec![("y", 22, 23, (1, 23))],
        );
    }

    #[test]
    fn test_transform_walrus_chained() {
        _test_transformation(
            "(x := (y := 5))",
            "assign(context, source, (1, 14), 'x', assign(context, source, (7, 13), 'y', 5))",
            vec![],
            vec![("x", 1, 2, (1, 2)), ("y", 7, 8, (1, 8))],
        );
    }

    #[test]
    fn test_transform_walrus_in_function_call() {
        _test_transformation(
            "foo(x := get_value())",
            "call(context, source, (0, 21), variable(context, source, (0, 3), 'foo'), assign(context, source, (4, 20), 'x', call(context, source, (9, 20), variable(context, source, (9, 18), 'get_value'))))",
            vec![("foo", 0, 3, (1, 1)), ("get_value", 9, 18, (1, 10))],
            vec![("x", 4, 5, (1, 5))],
        );
    }

    #[test]
    fn test_transform_walrus_remains_accessible_after_scope() {
        // NOTE: Previously, when a variable was assigned with walrus op,
        // then we didn't have to call `variable(...)` to access it later.
        // But that was not the right approach, because the assignment doesn't happen
        // in the expression's scope, but inside `assign(...)` call.
        // So even after `assign()`, we now expect to see `variable(...)`.
        _test_transformation(
            "foo([(a := i) for i in items], a)",
            "call(context, source, (0, 33), variable(context, source, (0, 3), 'foo'), [assign(context, source, (6, 12), 'a', i) for i in variable(context, source, (23, 28), 'items')], variable(context, source, (31, 32), 'a'))",
            vec![
                ("foo", 0, 3, (1, 1)),
                ("items", 23, 28, (1, 24)),
                ("a", 31, 32, (1, 32)),
            ],
            vec![("a", 6, 7, (1, 7))],
        );
    }

    #[test]
    fn test_transform_walrus_multiple_assignments() {
        // NOTE: Previously, when a variable was assigned with walrus op,
        // then we didn't have to call `variable(...)` to access it later.
        // But that was not the right approach, because the assignment doesn't happen
        // in the expression's scope, but inside `assign(...)` call.
        // So even after `assign()`, we now expect to see `variable(...)`.
        _test_transformation(
            "[(x := i, y := i*2) for i in items] and x + y",
            "[(assign(context, source, (2, 8), 'x', i), assign(context, source, (10, 18), 'y', i * 2)) for i in variable(context, source, (29, 34), 'items')] and variable(context, source, (40, 41), 'x') + variable(context, source, (44, 45), 'y')",
            vec![
                ("items", 29, 34, (1, 30)),
                ("x", 40, 41, (1, 41)),
                ("y", 44, 45, (1, 45)),
            ],
            vec![("x", 2, 3, (1, 3)), ("y", 10, 11, (1, 11))],
        );
    }

    #[test]
    fn test_transform_walrus_sequential_usage() {
        _test_transformation(
            "(x := 5) + x",
            "assign(context, source, (1, 7), 'x', 5) + variable(context, source, (11, 12), 'x')",
            vec![("x", 11, 12, (1, 12))],
            vec![("x", 1, 2, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_before_comprehension() {
        _test_transformation(
            "(limit := 10) and [x for x in items if x < limit]",
            "assign(context, source, (1, 12), 'limit', 10) and [x for x in variable(context, source, (30, 35), 'items') if x < variable(context, source, (43, 48), 'limit')]",
            vec![("items", 30, 35, (1, 31)), ("limit", 43, 48, (1, 44))],
            vec![("limit", 1, 6, (1, 2))],
        );
    }

    #[test]
    fn test_transform_walrus_nested_scopes() {
        // 'a' is assigned in inner comprehension, should be accessible in outer comprehension and after
        // 'b' is assigned in outer comprehension, should be accessible after
        // Both 'a' and 'b' at the end should NOT be transformed
        // Breakdown in order of execution:
        // - `(a := i)`
        //   - `i` known from comp
        //   - defines `a`
        // - `(b := a + 1)`
        //   - `a` known from walrus
        //   - defines `b`
        // - Left side `y + x + a + b + i`
        //   - `a`, `b` known from walrus
        //   - `x` known from comp
        //   - `y` unknown
        //   - `i` unknown (NOT in this scope). If `i` was defined then inner comp would be leaky.
        // - Right side `y + x + a + b + i`
        //   - `a`, `b` known from walrus
        //   - `y` unknown
        //   - `i`, `x` unknown (NOT in this scope). If `i`, `x` were defined then inner comps would be leaky.
        _test_transformation(
            "[y + x + a + b + i for x in [(a := i) for i in items] if (b := a + 1)] and y + x + a + b + i",
            "[variable(context, source, (1, 2), 'y') + x + variable(context, source, (9, 10), 'a') + variable(context, source, (13, 14), 'b') + variable(context, source, (17, 18), 'i') for x in [assign(context, source, (30, 36), 'a', i) for i in variable(context, source, (47, 52), 'items')] if assign(context, source, (58, 68), 'b', variable(context, source, (63, 64), 'a') + 1)] and variable(context, source, (75, 76), 'y') + variable(context, source, (79, 80), 'x') + variable(context, source, (83, 84), 'a') + variable(context, source, (87, 88), 'b') + variable(context, source, (91, 92), 'i')",
            vec![
                ("y", 1, 2, (1, 2)),
                ("a", 9, 10, (1, 10)),
                ("b", 13, 14, (1, 14)),
                ("i", 17, 18, (1, 18)),
                ("items", 47, 52, (1, 48)),
                ("a", 63, 64, (1, 64)),
                ("y", 75, 76, (1, 76)),
                ("x", 79, 80, (1, 80)),
                ("a", 83, 84, (1, 84)),
                ("b", 87, 88, (1, 88)),
                ("i", 91, 92, (1, 92)),
            ],
            vec![("a", 30, 31, (1, 31)), ("b", 58, 59, (1, 59))],
        );
    }

    #[test]
    fn test_transform_walrus_overwriting_loop_argument_syntax_error() {
        // Attempting to rebind comprehension iteration variable should raise SyntaxError
        // [(n := n + 1) + n for n in [1, 2, 3]]  # raises SyntaxError: assignment expression cannot rebind comprehension iteration variable 'n'
        _test_forbidden_syntax("[(n := n + 1) + n for n in items]");
    }

    #[test]
    fn test_tranform_walrus_overwriting_function_argument_allowed() {
        // Overwriting function argument IS allowed in Python.
        // (lambda x: (x := 3) and x**2)(0)  # returns 9
        // However, for consistency with comprehensions, we disallow it here.
        _test_forbidden_syntax("(lambda x: (x := 3) and x**2)");
    }

    #[test]
    fn test_transform_walrus_in_lambda_leaks() {
        // In Python, the walrus assignment inside lambda is scoped to that function,
        // and will NOT be available to outer scope.
        // However, we allow that so that in templates one can assign variables to the context
        // even from inside callbacks, e.g.
        // `fn_with_callback(on_done=lambda res: (data := res)) }}`
        _test_transformation(
            "(lambda: (y := 42) and y)",
            r#"lambda: assign(context, source, (10, 17), 'y', 42) and variable(context, source, (23, 24), 'y')"#,
            vec![("y", 23, 24, (1, 24))],
            vec![("y", 10, 11, (1, 11))],
        );
    }

    #[test]
    fn test_transform_walrus_in_lambda_in_comprehension() {
        // In Python, the walrus assignment inside lambda is scoped to that function,
        // and will NOT be available to outer scope.
        // However, we allow that so that in templates one can assign variables to the context
        // even from inside callbacks, e.g.
        // `fn_with_callback(on_done=lambda res: (data := res)) }}`
        _test_transformation(
            "[lambda: (temp := item * 2) for item in items] and temp + item",
            r#"[lambda: assign(context, source, (10, 26), 'temp', item * 2) for item in variable(context, source, (40, 45), 'items')] and variable(context, source, (51, 55), 'temp') + variable(context, source, (58, 62), 'item')"#,
            vec![
                ("items", 40, 45, (1, 41)),
                ("temp", 51, 55, (1, 52)),
                ("item", 58, 62, (1, 59)),
            ],
            vec![("temp", 10, 14, (1, 11))],
        );
    }

    #[test]
    fn test_transform_walrus_in_comprehension_condition_in_lambda() {
        // In Python, the walrus assignment inside lambda is scoped to that function,
        // and will NOT be available to outer scope.
        // However, we allow that so that in templates one can assign variables to the context
        // even from inside callbacks, e.g.
        // `fn_with_callback(on_done=lambda res: (data := res)) }}`
        // Note that the `+ [y]` at the end is STILL part of lambda and should NOT be transformed.
        _test_transformation(
            "lambda: [y for x in items if (y := x * 2)] + [y]",
            r#"lambda: [variable(context, source, (9, 10), 'y') for x in variable(context, source, (20, 25), 'items') if assign(context, source, (30, 40), 'y', x * 2)] + [variable(context, source, (46, 47), 'y')]"#,
            vec![
                ("y", 9, 10, (1, 10)),
                ("items", 20, 25, (1, 21)),
                ("y", 46, 47, (1, 47)),
            ],
            vec![("y", 30, 31, (1, 31))],
        );
    }

    #[test]
    fn test_transform_walrus_in_comprehension_condition_in_lambda_2() {
        // In Python, the walrus assignment inside lambda is scoped to that function,
        // and will NOT be available to outer scope.
        // However, we allow that so that in templates one can assign variables to the context
        // even from inside callbacks, e.g.
        // `fn_with_callback(on_done=lambda res: (data := res)) }}`
        // Note that the `+ [y]` at the end is STILL part of lambda and should NOT be transformed.
        _test_transformation(
            "(lambda: [y for x in items if (y := x * 2)] + [y])",
            r#"lambda: [variable(context, source, (10, 11), 'y') for x in variable(context, source, (21, 26), 'items') if assign(context, source, (31, 41), 'y', x * 2)] + [variable(context, source, (47, 48), 'y')]"#,
            vec![
                ("y", 10, 11, (1, 11)),
                ("items", 21, 26, (1, 22)),
                ("y", 47, 48, (1, 48)),
            ],
            vec![("y", 31, 32, (1, 32))],
        );
    }

    #[test]
    fn test_transform_walrus_in_comprehension_condition_in_lambda_3() {
        // In Python, the walrus assignment inside lambda is scoped to that function,
        // and will NOT be available to outer scope.
        // However, we allow that so that in templates one can assign variables to the context
        // even from inside callbacks, e.g.
        // `fn_with_callback(on_done=lambda res: (data := res)) }}`
        _test_transformation(
            "(lambda: [y for x in items if (y := x * 2)]) + y",
            r#"(lambda: [variable(context, source, (10, 11), 'y') for x in variable(context, source, (21, 26), 'items') if assign(context, source, (31, 41), 'y', x * 2)]) + variable(context, source, (47, 48), 'y')"#,
            vec![
                ("y", 10, 11, (1, 11)),
                ("items", 21, 26, (1, 22)),
                ("y", 47, 48, (1, 48)),
            ],
            vec![("y", 31, 32, (1, 32))],
        );
    }

    #[test]
    fn test_walrus_conflict_with_comprehension_variable() {
        // [(n := n + 1) + n for n in [1, 2, 3]]
        // Raises `SyntaxError: assignment expression cannot rebind comprehension iteration variable 'n'`
        _test_forbidden_syntax("[(n := n + 1) + n for n in items]");
    }

    #[test]
    fn test_walrus_conflict_with_nested_comprehension_variable() {
        // Test that even outer comprehension variables cannot be rebound
        // [[(x := x + 1) for y in inner] for x in outer]  # should raise SyntaxError
        _test_forbidden_syntax("[[(x := x + 1) for y in inner] for x in outer]");
    }

    #[test]
    fn test_walrus_conflict_with_lambda_parameter() {
        // (lambda x: (x := 3) and x**2)(0)
        // Raises `SyntaxError: assignment expression cannot rebind lambda parameter 'x'`
        _test_forbidden_syntax("(lambda x: (x := 3) and x**2)");
    }

    #[test]
    fn test_walrus_conflict_with_nested_lambda_outer_parameter() {
        // Test that outer lambda parameters cannot be rebound
        // (lambda x: lambda y: (x := 3))(0)  # should raise SyntaxError for x
        _test_forbidden_syntax("(lambda x: lambda y: (x := 3))");
    }

    #[test]
    fn test_walrus_conflict_with_nested_lambda_inner_parameter() {
        // Test that inner lambda parameters cannot be rebound
        // (lambda x: lambda y: (y := 3))(0)  # should raise SyntaxError for y
        _test_forbidden_syntax("(lambda x: lambda y: (y := 3))");
    }

    // === F-STRING AND T-STRING TESTS ===

    #[test]
    fn test_transform_fstring_simple() {
        // f-strings are transformed to format() function calls
        // The format() call itself is NOT transformed (it's a safe built-in)
        // Only the arguments (interpolated expressions) are transformed
        _test_transformation(
            "f'Hello {name}'",
            "format(context, source, (0, 15), 'Hello {}', (variable(context, source, (9, 13), 'name'), None, ''))",
            vec![("name", 9, 13, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_expression() {
        _test_transformation(
            "f'Result: {x + 1}'",
            "format(context, source, (0, 18), 'Result: {}', (variable(context, source, (11, 12), 'x') + 1, None, ''))",
            vec![("x", 11, 12, (1, 12))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_function_call() {
        _test_transformation(
            "f'Value: {get_value()}'",
            "format(context, source, (0, 23), 'Value: {}', (call(context, source, (10, 21), variable(context, source, (10, 19), 'get_value')), None, ''))",
            vec![("get_value", 10, 19, (1, 11))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_attribute() {
        _test_transformation(
            "f'Name: {obj.name}'",
            "format(context, source, (0, 19), 'Name: {}', (attribute(context, source, (9, 17), variable(context, source, (9, 12), 'obj'), 'name'), None, ''))",
            vec![("obj", 9, 12, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_multiple_interpolations() {
        _test_transformation(
            "f'{x} and {y}'",
            "format(context, source, (0, 14), '{} and {}', (variable(context, source, (3, 4), 'x'), None, ''), (variable(context, source, (11, 12), 'y'), None, ''))",
            vec![("x", 3, 4, (1, 4)), ("y", 11, 12, (1, 12))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_nested_expression() {
        _test_transformation(
            "f'start {obj.method(x, y)} end'",
            "format(context, source, (0, 31), 'start {} end', (call(context, source, (9, 25), attribute(context, source, (9, 19), variable(context, source, (9, 12), 'obj'), 'method'), variable(context, source, (20, 21), 'x'), variable(context, source, (23, 24), 'y')), None, ''))",
            vec![
                ("obj", 9, 12, (1, 10)),
                ("x", 20, 21, (1, 21)),
                ("y", 23, 24, (1, 24)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_format_spec() {
        // Format spec is applied using format(value, ".2f")
        _test_transformation(
            "f'start {value:.2f} end'",
            "format(context, source, (0, 24), 'start {} end', (variable(context, source, (9, 14), 'value'), None, '.2f'))",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_format_spec_alignment() {
        _test_transformation(
            "f'start {name:>10} end'",
            "format(context, source, (0, 23), 'start {} end', (variable(context, source, (9, 13), 'name'), None, '>10'))",
            vec![("name", 9, 13, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_conversion() {
        // Conversion !r is applied using repr()
        _test_transformation(
            "f'start {value!r} end'",
            "format(context, source, (0, 22), 'start {} end', (variable(context, source, (9, 14), 'value'), 'r', ''))",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_conversion_str() {
        _test_transformation(
            "f'start {value!s} end'",
            "format(context, source, (0, 22), 'start {} end', (variable(context, source, (9, 14), 'value'), 's', ''))",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_conversion_and_format() {
        // Both conversion and format spec are applied
        _test_transformation(
            "f'start {value!r:>20} end'",
            "format(context, source, (0, 26), 'start {} end', (variable(context, source, (9, 14), 'value'), 'r', '>20'))",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_fstring_with_dynamic_format_spec() {
        // Dynamic format spec: the format spec itself is built using .format()
        _test_transformation(
            "f'start {value:{width}.{precision}f} end'",
            "format(context, source, (0, 41), 'start {} end', (variable(context, source, (9, 14), 'value'), None, ('{}.{}f', variable(context, source, (16, 21), 'width'), variable(context, source, (24, 33), 'precision'))))",
            vec![
                ("value", 9, 14, (1, 10)),
                ("width", 16, 21, (1, 17)),
                ("precision", 24, 33, (1, 25)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_percent_formatting() {
        _test_transformation(
            "'text %s' % var",
            "'text %s' % variable(context, source, (12, 15), 'var')",
            vec![("var", 12, 15, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_transform_percent_formatting_tuple() {
        _test_transformation(
            "'%s and %s' % (x, y)",
            "'%s and %s' % (variable(context, source, (15, 16), 'x'), variable(context, source, (18, 19), 'y'))",
            vec![("x", 15, 16, (1, 16)), ("y", 18, 19, (1, 19))],
            vec![],
        );
    }

    // === T-STRING TESTS ===

    #[test]
    fn test_transform_tstring_simple() {
        // t-strings become template() function calls
        _test_transformation(
            "t'Hello {name}'",
            "template(context, source, (0, 15), 'Hello ', interpolation(context, source, (8, 14), variable(context, source, (9, 13), 'name'), '', None, ''))",
            vec![("name", 9, 13, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_tstring_with_expression() {
        _test_transformation(
            "t'Result: {x + 1}'",
            "template(context, source, (0, 18), 'Result: ', interpolation(context, source, (10, 17), variable(context, source, (11, 12), 'x') + 1, '', None, ''))",
            vec![("x", 11, 12, (1, 12))],
            vec![],
        );
    }

    #[test]
    fn test_transform_tstring_multiple_interpolations() {
        _test_transformation(
            "t'{x} and {y}'",
            "template(context, source, (0, 14), interpolation(context, source, (2, 5), variable(context, source, (3, 4), 'x'), '', None, ''), ' and ', interpolation(context, source, (10, 13), variable(context, source, (11, 12), 'y'), '', None, ''))",
            vec![("x", 3, 4, (1, 4)), ("y", 11, 12, (1, 12))],
            vec![],
        );
    }

    #[test]
    fn test_transform_tstring_with_format_spec() {
        // Format spec is stored in the interpolation object
        _test_transformation(
            "t'start {value:.2f} end'",
            "template(context, source, (0, 24), 'start ', interpolation(context, source, (8, 19), variable(context, source, (9, 14), 'value'), '', None, '.2f'), ' end')",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_tstring_with_conversion() {
        // Conversion flag is stored in the interpolation object
        _test_transformation(
            "t'start {value!r} end'",
            "template(context, source, (0, 22), 'start ', interpolation(context, source, (8, 17), variable(context, source, (9, 14), 'value'), '', 'r', ''), ' end')",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_tstring_with_conversion_and_format() {
        // Both conversion and format spec are stored in the interpolation object
        _test_transformation(
            "t'start {value!r:>20} end'",
            "template(context, source, (0, 26), 'start ', interpolation(context, source, (8, 21), variable(context, source, (9, 14), 'value'), '', 'r', '>20'), ' end')",
            vec![("value", 9, 14, (1, 10))],
            vec![],
        );
    }

    #[test]
    fn test_transform_tstring_with_dynamic_format_spec() {
        // Dynamic format spec: the format spec itself is built using .format()
        _test_transformation(
            "t'start {value:{width}.{precision}f} end'",
            "template(context, source, (0, 41), 'start ', interpolation(context, source, (8, 36), variable(context, source, (9, 14), 'value'), '', None, '{}.{}f'.format(variable(context, source, (16, 21), 'width'), variable(context, source, (24, 33), 'precision'))), ' end')",
            vec![
                ("value", 9, 14, (1, 10)),
                ("width", 16, 21, (1, 17)),
                ("precision", 24, 33, (1, 25)),
            ],
            vec![],
        );
    }

    // === VARIABLE/IDENTIFIER TESTS ===

    #[test]
    fn test_allow_simple_variable() {
        _test_transformation(
            "x",
            "variable(context, source, (0, 1), 'x')",
            vec![("x", 0, 1, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_binary_operation() {
        _test_transformation(
            "x + y",
            "variable(context, source, (0, 1), 'x') + variable(context, source, (4, 5), 'y')",
            vec![("x", 0, 1, (1, 1)), ("y", 4, 5, (1, 5))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_comparison() {
        _test_transformation(
            "x > 5",
            "variable(context, source, (0, 1), 'x') > 5",
            vec![("x", 0, 1, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_boolean_operation() {
        _test_transformation(
            "x and y",
            "variable(context, source, (0, 1), 'x') and variable(context, source, (6, 7), 'y')",
            vec![("x", 0, 1, (1, 1)), ("y", 6, 7, (1, 7))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_list() {
        _test_transformation(
            "[x, y, z]",
            "[variable(context, source, (1, 2), 'x'), variable(context, source, (4, 5), 'y'), variable(context, source, (7, 8), 'z')]",
            vec![
                ("x", 1, 2, (1, 2)),
                ("y", 4, 5, (1, 5)),
                ("z", 7, 8, (1, 8)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_dict() {
        _test_transformation(
            "{'key': x}",
            "{'key': variable(context, source, (8, 9), 'x')}",
            vec![("x", 8, 9, (1, 9))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_unary_operation() {
        _test_transformation(
            "-x",
            "-variable(context, source, (1, 2), 'x')",
            vec![("x", 1, 2, (1, 2))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_in_complex_expression() {
        _test_transformation(
            "x + y * z > 10",
            "variable(context, source, (0, 1), 'x') + variable(context, source, (4, 5), 'y') * variable(context, source, (8, 9), 'z') > 10",
            vec![
                ("x", 0, 1, (1, 1)),
                ("y", 4, 5, (1, 5)),
                ("z", 8, 9, (1, 9)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_names_with_underscores() {
        _test_transformation(
            "my_variable",
            "variable(context, source, (0, 11), 'my_variable')",
            vec![("my_variable", 0, 11, (1, 1))],
            vec![],
        );
    }

    #[test]
    fn test_transform_variable_names_with_numbers() {
        _test_transformation(
            "var123",
            "variable(context, source, (0, 6), 'var123')",
            vec![("var123", 0, 6, (1, 1))],
            vec![],
        );
    }

    // === LAMBDA TESTS ===

    #[test]
    fn test_lambda_simple() {
        _test_transformation(
            "lambda x: x + 1 + y",
            "lambda x: x + 1 + variable(context, source, (18, 19), 'y')",
            vec![("y", 18, 19, (1, 19))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_no_params() {
        _test_transformation(
            "lambda: 42 + y",
            "lambda: 42 + variable(context, source, (13, 14), 'y')",
            vec![("y", 13, 14, (1, 14))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_multiple_params() {
        _test_transformation(
            "lambda x, y: x + y + z",
            "lambda x, y: x + y + variable(context, source, (21, 22), 'z')",
            vec![("z", 21, 22, (1, 22))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_defaults() {
        _test_transformation(
            "lambda x=1, y=c: x + y + c",
            r#"lambda x=1, y=variable(context, source, (14, 15), 'c'): x + y + variable(context, source, (25, 26), 'c')"#,
            vec![("c", 14, 15, (1, 15)), ("c", 25, 26, (1, 26))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_posonly_defaults() {
        // Positional-only parameters with defaults (Python 3.8+)
        // The '/' separator marks parameters before it as positional-only
        _test_transformation(
            "lambda x=a, y=b, /: x + y + a + b",
            r#"lambda x=variable(context, source, (9, 10), 'a'), y=variable(context, source, (14, 15), 'b'), /: x + y + variable(context, source, (28, 29), 'a') + variable(context, source, (32, 33), 'b')"#,
            vec![
                ("a", 9, 10, (1, 10)),
                ("b", 14, 15, (1, 15)),
                ("a", 28, 29, (1, 29)),
                ("b", 32, 33, (1, 33)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_kwonly_defaults() {
        // Keyword-only parameters with defaults
        // The '*' separator marks parameters after it as keyword-only
        _test_transformation(
            "lambda *, x=a, y=b: x + y + a + b",
            r#"lambda *, x=variable(context, source, (12, 13), 'a'), y=variable(context, source, (17, 18), 'b'): x + y + variable(context, source, (28, 29), 'a') + variable(context, source, (32, 33), 'b')"#,
            vec![
                ("a", 12, 13, (1, 13)),
                ("b", 17, 18, (1, 18)),
                ("a", 28, 29, (1, 29)),
                ("b", 32, 33, (1, 33)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_mixed_params_and_defaults() {
        // Mix of positional-only, regular, and keyword-only with various defaults
        // Note: After a parameter with a default, all following positional params must have defaults too
        _test_transformation(
            "lambda a, /, b, c=y, *args, d, e=z, **kwargs: a + b + c + d + e + args + kwargs + y + z",
            r#"lambda a, /, b, c=variable(context, source, (18, 19), 'y'), *args, d, e=variable(context, source, (33, 34), 'z'), **kwargs: a + b + c + d + e + args + kwargs + variable(context, source, (82, 83), 'y') + variable(context, source, (86, 87), 'z')"#,
            vec![
                ("y", 18, 19, (1, 19)),
                ("z", 33, 34, (1, 34)),
                ("y", 82, 83, (1, 83)),
                ("z", 86, 87, (1, 87)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_varargs() {
        _test_transformation(
            "lambda *args: len(args)",
            "lambda *args: call(context, source, (14, 23), variable(context, source, (14, 17), 'len'), args)",
            vec![("len", 14, 17, (1, 15))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_kwargs() {
        _test_transformation(
            "lambda **kwargs: len(kwargs)",
            "lambda **kwargs: call(context, source, (17, 28), variable(context, source, (17, 20), 'len'), kwargs)",
            vec![("len", 17, 20, (1, 18))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_with_external_variable() {
        // Lambda parameter 'x' should NOT be transformed
        // but external variable 'items' SHOULD be transformed
        _test_transformation(
            "lambda x: x in items",
            r#"lambda x: x in variable(context, source, (15, 20), 'items')"#,
            vec![("items", 15, 20, (1, 16))],
            vec![],
        );
    }

    #[test]
    fn test_nested_lambda() {
        // Both 'x' and 'y' should NOT be transformed as they are lambda parameters
        // but 'z' SHOULD be transformed as it's an external variable
        _test_transformation(
            "lambda x: lambda y: x + y + z",
            r#"lambda x: lambda y: x + y + variable(context, source, (28, 29), 'z')"#,
            vec![("z", 28, 29, (1, 29))],
            vec![],
        );
    }

    #[test]
    fn test_lambda_in_comprehension() {
        // Lambda used within a list comprehension
        // The comprehension variable 'item' should not be transformed
        // The lambda parameter 'x' should not be transformed
        // External variable 'n' should be transformed in both contexts
        _test_transformation(
            "[lambda x: x * item * n for item in items]",
            r#"[lambda x: x * item * variable(context, source, (22, 23), 'n') for item in variable(context, source, (36, 41), 'items')]"#,
            vec![("n", 22, 23, (1, 23)), ("items", 36, 41, (1, 37))],
            vec![],
        );
    }

    #[test]
    fn test_comprehension_in_lambda() {
        // List comprehension used within a lambda body
        // Lambda parameter 'n' should not be transformed
        // Comprehension variable 'i' should not be transformed
        // Both should be accessible in their respective scopes
        _test_transformation(
            "lambda n: [i * n * c for i in items]",
            r#"lambda n: [i * n * variable(context, source, (19, 20), 'c') for i in variable(context, source, (30, 35), 'items')]"#,
            vec![("c", 19, 20, (1, 20)), ("items", 30, 35, (1, 31))],
            vec![],
        );
    }

    #[test]
    fn test_nested_lambda_and_comprehension() {
        // Complex nesting: lambda -> comprehension -> lambda
        // 'x' (outer lambda param) should not be transformed
        // 'item' (comprehension var) should not be transformed
        // 'y' (inner lambda param) should not be transformed
        // 'c' (external var) should be transformed
        _test_transformation(
            "lambda x: [lambda y: x + y + item + c for item in items]",
            r#"lambda x: [lambda y: x + y + item + variable(context, source, (36, 37), 'c') for item in variable(context, source, (50, 55), 'items')]"#,
            vec![("c", 36, 37, (1, 37)), ("items", 50, 55, (1, 51))],
            vec![],
        );
    }

    #[test]
    fn test_comprehension_with_lambda_filter() {
        // Comprehension using a lambda in the filter condition
        _test_transformation(
            "lambda: [item for item in items if (lambda x: x > threshold)(item)]",
            r#"lambda: [item for item in variable(context, source, (26, 31), 'items') if call(context, source, (35, 66), lambda x: x > variable(context, source, (50, 59), 'threshold'), item)]"#,
            vec![("items", 26, 31, (1, 27)), ("threshold", 50, 59, (1, 51))],
            vec![],
        );
    }

    // === TERNARY IF EXPRESSION TESTS ===

    #[test]
    fn test_ternary_if_simple() {
        _test_transformation(
            "x + 1 if condition else y + 2",
            r#"variable(context, source, (0, 1), 'x') + 1 if variable(context, source, (9, 18), 'condition') else variable(context, source, (24, 25), 'y') + 2"#,
            vec![
                ("x", 0, 1, (1, 1)),
                ("condition", 9, 18, (1, 10)),
                ("y", 24, 25, (1, 25)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_nested() {
        // Nested ternary expressions
        _test_transformation(
            "a if x else b if y else c",
            r#"variable(context, source, (0, 1), 'a') if variable(context, source, (5, 6), 'x') else variable(context, source, (12, 13), 'b') if variable(context, source, (17, 18), 'y') else variable(context, source, (24, 25), 'c')"#,
            vec![
                ("a", 0, 1, (1, 1)),
                ("x", 5, 6, (1, 6)),
                ("b", 12, 13, (1, 13)),
                ("y", 17, 18, (1, 18)),
                ("c", 24, 25, (1, 25)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_in_expression() {
        // Ternary used within a larger expression
        _test_transformation(
            "result + (x if flag else y) * 2",
            r#"variable(context, source, (0, 6), 'result') + (variable(context, source, (10, 11), 'x') if variable(context, source, (15, 19), 'flag') else variable(context, source, (25, 26), 'y')) * 2"#,
            vec![
                ("result", 0, 6, (1, 1)),
                ("x", 10, 11, (1, 11)),
                ("flag", 15, 19, (1, 16)),
                ("y", 25, 26, (1, 26)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_with_function_calls() {
        // Ternary with function calls
        _test_transformation(
            "max(a, b) if a > 0 else min(a, b)",
            r#"call(context, source, (0, 9), variable(context, source, (0, 3), 'max'), variable(context, source, (4, 5), 'a'), variable(context, source, (7, 8), 'b')) if variable(context, source, (13, 14), 'a') > 0 else call(context, source, (24, 33), variable(context, source, (24, 27), 'min'), variable(context, source, (28, 29), 'a'), variable(context, source, (31, 32), 'b'))"#,
            vec![
                ("max", 0, 3, (1, 1)),
                ("a", 4, 5, (1, 5)),
                ("b", 7, 8, (1, 8)),
                ("a", 13, 14, (1, 14)),
                ("min", 24, 27, (1, 25)),
                ("a", 28, 29, (1, 29)),
                ("b", 31, 32, (1, 32)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_in_comprehension() {
        // Ternary used in list comprehension
        _test_transformation(
            "[x if x > 0 else 0 for x in items]",
            r#"[x if x > 0 else 0 for x in variable(context, source, (28, 33), 'items')]"#,
            vec![("items", 28, 33, (1, 29))],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_in_lambda() {
        // Ternary in lambda body
        _test_transformation(
            "lambda x: x if x > threshold else 0",
            r#"lambda x: x if x > variable(context, source, (19, 28), 'threshold') else 0"#,
            vec![("threshold", 19, 28, (1, 20))],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_with_walrus() {
        // Ternary with walrus operator in condition
        _test_transformation(
            "x if (y := compute()) else default",
            r#"variable(context, source, (0, 1), 'x') if assign(context, source, (6, 20), 'y', call(context, source, (11, 20), variable(context, source, (11, 18), 'compute'))) else variable(context, source, (27, 34), 'default')"#,
            vec![
                ("x", 0, 1, (1, 1)),
                ("compute", 11, 18, (1, 12)),
                ("default", 27, 34, (1, 28)),
            ],
            vec![("y", 6, 7, (1, 7))],
        );
    }

    #[test]
    fn test_ternary_if_with_walrus_order() {
        // condition branch runs first, so y in either branch should be already known
        _test_transformation(
            "y if (y := compute()) else y",
            r#"variable(context, source, (0, 1), 'y') if assign(context, source, (6, 20), 'y', call(context, source, (11, 20), variable(context, source, (11, 18), 'compute'))) else variable(context, source, (27, 28), 'y')"#,
            vec![
                ("y", 0, 1, (1, 1)),
                ("compute", 11, 18, (1, 12)),
                ("y", 27, 28, (1, 28)),
            ],
            vec![("y", 6, 7, (1, 7))],
        );
    }

    #[test]
    fn test_ternary_if_with_attribute_access() {
        // Ternary with attribute access
        _test_transformation(
            "obj.value if obj.is_valid else obj.default",
            r#"attribute(context, source, (0, 9), variable(context, source, (0, 3), 'obj'), 'value') if attribute(context, source, (13, 25), variable(context, source, (13, 16), 'obj'), 'is_valid') else attribute(context, source, (31, 42), variable(context, source, (31, 34), 'obj'), 'default')"#,
            vec![
                ("obj", 0, 3, (1, 1)),
                ("obj", 13, 16, (1, 14)),
                ("obj", 31, 34, (1, 32)),
            ],
            vec![],
        );
    }

    #[test]
    fn test_ternary_if_with_subscript() {
        // Ternary with subscript access
        _test_transformation(
            "data[key] if key in data else None",
            r#"subscript(context, source, (0, 9), variable(context, source, (0, 4), 'data'), variable(context, source, (5, 8), 'key')) if variable(context, source, (13, 16), 'key') in variable(context, source, (20, 24), 'data') else None"#,
            vec![
                ("data", 0, 4, (1, 1)),
                ("key", 5, 8, (1, 6)),
                ("key", 13, 16, (1, 14)),
                ("data", 20, 24, (1, 21)),
            ],
            vec![],
        );
    }

    // === FORBIDDEN SYNTAX TESTS ===

    #[test]
    fn test_forbid_assignment() {
        // NOTE: Use walrus operator := instead
        _test_forbidden_syntax("x = 1");
    }

    #[test]
    fn test_forbid_augmented_assignment() {
        _test_forbidden_syntax("x += 1");
    }

    #[test]
    fn test_forbid_annotated_assignment() {
        _test_forbidden_syntax("x: int = 1");
    }

    #[test]
    fn test_forbid_delete() {
        _test_forbidden_syntax("del x");
    }

    #[test]
    fn test_forbid_multiple_delete() {
        _test_forbidden_syntax("del x, y, z");
    }

    #[test]
    fn test_forbid_raise() {
        _test_forbidden_syntax("raise ValueError('error')");
    }

    #[test]
    fn test_forbid_raise_bare() {
        _test_forbidden_syntax("raise 'Oops'");
    }

    #[test]
    fn test_forbid_assert() {
        _test_forbidden_syntax("assert x > 0");
    }

    #[test]
    fn test_forbid_assert_with_message() {
        _test_forbidden_syntax("assert x > 0, 'x must be positive'");
    }

    #[test]
    fn test_forbid_pass() {
        _test_forbidden_syntax("pass");
    }

    #[test]
    fn test_forbid_type_alias() {
        _test_forbidden_syntax("type Point = tuple[float, float]");
    }

    #[test]
    fn test_forbid_for() {
        _test_forbidden_syntax("for i in range(10): print(i");
    }

    #[test]
    fn test_forbid_while() {
        _test_forbidden_syntax("while i < 10: print(i)");
    }

    #[test]
    fn test_forbid_break() {
        _test_forbidden_syntax("for i in range(10): break");
    }

    #[test]
    fn test_forbid_continue() {
        _test_forbidden_syntax("for i in range(10): continue");
    }

    #[test]
    fn test_forbid_if() {
        _test_forbidden_syntax("if x > 0: print(1)");
    }

    #[test]
    fn test_forbid_if_else() {
        _test_forbidden_syntax("if x > 0: print(1)\nelif 2: print(2)\nelse: print(3)");
    }

    #[test]
    fn test_forbid_try_except() {
        _test_forbidden_syntax("try: x\nexcept: pass");
    }

    #[test]
    fn test_forbid_try_except_specific() {
        _test_forbidden_syntax("try: x\nexcept ValueError: pass");
    }

    #[test]
    fn test_forbid_try_except_finally() {
        _test_forbidden_syntax("try: x\nexcept: pass\nfinally: pass");
    }

    #[test]
    fn test_forbid_except_star() {
        _test_forbidden_syntax("try: x\nexcept* ValueError: pass");
    }

    #[test]
    fn test_forbid_with() {
        _test_forbidden_syntax("with open('f') as f: pass");
    }

    #[test]
    fn test_forbid_with_multiple() {
        _test_forbidden_syntax("with open('f1') as f1, open('f2') as f2: pass");
    }

    #[test]
    fn test_forbid_async_with_in_async_fn() {
        _test_forbidden_syntax("async def fn():\n    async with x as y: pass");
    }

    #[test]
    fn test_forbid_import() {
        _test_forbidden_syntax("import os");
    }

    #[test]
    fn test_forbid_import_from() {
        _test_forbidden_syntax("from os import path");
    }

    #[test]
    fn test_forbid_import_from_as() {
        _test_forbidden_syntax("from os import path as p");
    }

    #[test]
    fn test_forbid_class() {
        _test_forbidden_syntax("class MyClass: pass");
    }

    #[test]
    fn test_forbid_fn() {
        _test_forbidden_syntax("def fn(): 1");
    }

    #[test]
    fn test_forbid_return() {
        _test_forbidden_syntax("def fn(): return 42");
    }

    #[test]
    fn test_forbid_global() {
        _test_forbidden_syntax("def fn(): global x");
    }

    #[test]
    fn test_forbid_nonlocal() {
        _test_forbidden_syntax("def fn(): nonlocal x");
    }

    #[test]
    fn test_forbid_yield() {
        _test_forbidden_syntax("def fn(): yield x");
    }

    #[test]
    fn test_forbid_yield_from() {
        _test_forbidden_syntax("def fn(): yield from x");
    }

    #[test]
    fn test_forbid_decorator() {
        _test_forbidden_syntax("@decorator\ndef fn(): pass");
    }

    #[test]
    fn test_forbid_async_fn() {
        _test_forbidden_syntax("async def fn(): await x");
    }

    #[test]
    fn test_forbid_async_for() {
        _test_forbidden_syntax("async for x in y");
    }

    #[test]
    fn test_forbid_async_with() {
        _test_forbidden_syntax("async with x as y: pass");
    }

    #[test]
    fn test_forbid_match() {
        _test_forbidden_syntax("match x:\n    case 1: pass");
    }

    #[test]
    fn test_forbid_match_singleton() {
        _test_forbidden_syntax("match x:\n    case None: pass\n    case True: pass");
    }

    #[test]
    fn test_forbid_match_sequence() {
        _test_forbidden_syntax("match x:\n    case [1, 2, 3]: pass");
    }

    #[test]
    fn test_forbid_match_star() {
        _test_forbidden_syntax("match x:\n    case [1, *rest]: pass");
    }

    #[test]
    fn test_forbid_match_mapping() {
        _test_forbidden_syntax("match x:\n    case {'key': value}: pass");
    }

    #[test]
    fn test_forbid_match_class() {
        _test_forbidden_syntax("match x:\n    case Point(x=0, y=0): pass");
    }

    #[test]
    fn test_forbid_match_as() {
        _test_forbidden_syntax("match x:\n    case [1, 2] as pair: pass");
    }

    #[test]
    fn test_forbid_match_or() {
        _test_forbidden_syntax("match x:\n    case 1 | 2 | 3: pass");
    }

    #[test]
    fn test_forbid_match_wildcard() {
        _test_forbidden_syntax("match x:\n    case _: pass");
    }

    #[test]
    fn test_forbid_match_guard() {
        _test_forbidden_syntax("match x:\n    case n if n > 0: pass");
    }

    #[test]
    fn test_forbid_typevar() {
        _test_forbidden_syntax("type T = int");
    }

    #[test]
    fn test_forbid_typevar_union() {
        _test_forbidden_syntax("type StringOrInt = str | int");
    }

    #[test]
    fn test_forbid_generic_function() {
        _test_forbidden_syntax("def func[T](x: T) -> T: return x");
    }

    #[test]
    fn test_forbid_paramspec() {
        _test_forbidden_syntax(
            "def decorator[**P, T](func: Callable[P, T]) -> Callable[P, T]: return func",
        );
    }

    #[test]
    fn test_forbid_typevartuple() {
        _test_forbidden_syntax("def func[*Ts](*args: *Ts) -> tuple[*Ts]: return args");
    }

    // === VARIABLE IN COMPREHENSION ===

    #[test]
    fn test_local_variable_tracking_in_comprehensions() {
        _test_transformation(
            "[x for x in items]",
            "[x for x in variable(context, source, (12, 17), 'items')]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_local_variable_tracking_in_nested_comprehensions() {
        _test_transformation(
            "[[x for x in row] for row in matrix]",
            "[[x for x in row] for row in variable(context, source, (29, 35), 'matrix')]",
            vec![("matrix", 29, 35, (1, 30))],
            vec![],
        );
    }

    #[test]
    fn test_local_variable_tracking_in_multiple_comprehensions() {
        _test_transformation(
            "[x for x in items for y in x.children]",
            "[x for x in variable(context, source, (12, 17), 'items') for y in attribute(context, source, (27, 37), x, 'children')]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_local_variable_tracking_in_comprehension_conditions() {
        _test_transformation(
            "[x for x in items if x > 0]",
            "[x for x in variable(context, source, (12, 17), 'items') if x > 0]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    #[test]
    fn test_local_variable_tracking_in_multiple_comprehension_conditions() {
        _test_transformation(
            "[x for x in items for y in x.children if y > 0]",
            "[x for x in variable(context, source, (12, 17), 'items') for y in attribute(context, source, (27, 37), x, 'children') if y > 0]",
            vec![("items", 12, 17, (1, 13))],
            vec![],
        );
    }

    // === COMMENT EXTRACTION TESTS ===

    fn _token(content: &str, start_index: usize, line: usize, col: usize) -> Token {
        Token {
            content: content.to_string(),
            start_index,
            end_index: start_index + content.len(),
            line_col: (line, col),
        }
    }

    #[test]
    fn test_simple_comment_extraction() {
        let result = transform_expression_string("1 # comment").unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("# comment", 2, 1, 3),
                value: _token(" comment", 3, 1, 4),
            }],
        );
    }

    #[test]
    fn test_comment_at_end_of_input() {
        let result = transform_expression_string("42#end").unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("#end", 2, 1, 3),
                value: _token("end", 3, 1, 4),
            }],
        );
    }

    #[test]
    fn test_comment_inside_string_not_extracted() {
        let result = transform_expression_string(r#""text # not a comment""#).unwrap();
        assert_eq!(result.comments, vec![]);
    }

    #[test]
    fn test_comment_after_string_extracted() {
        let result = transform_expression_string(r#""t#xt" # this is a comment"#).unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("# this is a comment", 7, 1, 8),
                value: _token(" this is a comment", 8, 1, 9),
            }],
        );
    }

    #[test]
    fn test_multiline_string_with_comment() {
        // Newlines in triple-quoted strings are preserved (will work with exec())
        let result = transform_expression_string("\"\"\"my\n#tring\"\"\" # comment").unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("# comment", 16, 2, 11),
                value: _token(" comment", 17, 2, 12),
            }],
        );
    }

    #[test]
    fn test_string_with_escape_sequence() {
        let result = transform_expression_string(r##""t#xt \"qu#te\"#" # after"##).unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("# after", 18, 1, 19),
                value: _token(" after", 19, 1, 20),
            }],
        );
    }

    #[test]
    fn test_raw_string_with_escape_sequence() {
        let result = transform_expression_string(r##"r"t#xt \"qu#te\"#" # after"##).unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("# after", 19, 1, 20),
                value: _token(" after", 20, 1, 21),
            }],
        );
    }

    #[test]
    fn test_comment_before_string() {
        let source = r#"1# comment before"text""#;
        let result = transform_expression_string(source).unwrap();
        // When there's no newline, the comment extends to the end of input
        // So the comment includes " comment before"text""
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token(&source[1..], 1, 1, 2),
                value: _token(&source[2..], 2, 1, 3),
            }],
        );
    }

    #[test]
    fn test_nested_strings() {
        // String containing quote characters
        let result = transform_expression_string(r#""ou#ter 'in#ner' ou#ter""#).unwrap();
        assert_eq!(result.comments, vec![]);
    }

    #[test]
    fn test_triple_quotes_in_single_quote_string() {
        // Triple quotes inside a single-quote string should not close it
        let result =
            transform_expression_string(r#"'''te#xt \"\"\" ins#ide\"\"\te#xt2'''"#).unwrap();
        assert_eq!(result.comments, vec![]);
    }

    #[test]
    fn test_empty_comment() {
        let result = transform_expression_string("x #").unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("#", 2, 1, 3),
                value: _token("", 3, 1, 4),
            }],
        );
    }

    #[test]
    fn test_comment_with_carriage_return() {
        let result = transform_expression_string("[x, # comment\r\nnext]").unwrap();
        assert_eq!(
            result.comments,
            vec![Comment {
                token: _token("# comment", 4, 1, 5),
                value: _token(" comment", 5, 1, 6),
            }],
        );
    }

    #[test]
    fn test_multiline_string_with_escaped_newline() {
        // Escaped newline in non-raw string should not be replaced
        let result = transform_expression_string(r#""line1\\nline2""#).unwrap();
        assert_eq!(result.comments, vec![]);
    }

    #[test]
    fn test_complex_expression_with_comments() {
        let result = transform_expression_string(
            "[      # comment 1\n  1,   # comment 2\n  2,   # comment 3\n]       # comment 4",
        )
        .unwrap();
        assert_eq!(
            result.comments,
            vec![
                Comment {
                    token: _token("# comment 1", 7, 1, 8),
                    value: _token(" comment 1", 8, 1, 9),
                },
                Comment {
                    token: _token("# comment 2", 26, 2, 8),
                    value: _token(" comment 2", 27, 2, 9),
                },
                Comment {
                    token: _token("# comment 3", 45, 3, 8),
                    value: _token(" comment 3", 46, 3, 9),
                },
                Comment {
                    token: _token("# comment 4", 65, 4, 9),
                    value: _token(" comment 4", 66, 4, 10),
                },
            ],
        );
    }
}
