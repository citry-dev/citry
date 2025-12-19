use python_safe_eval::{Comment, Token, extract_comments};

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
    let result = extract_comments("1 # comment").unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("# comment", 2, 1, 3),
            value: _token(" comment", 3, 1, 4),
        }],
    );
}

#[test]
fn test_comment_at_end_of_input() {
    let result = extract_comments("42#end").unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("#end", 2, 1, 3),
            value: _token("end", 3, 1, 4),
        }],
    );
}

#[test]
fn test_multiple_comments() {
    let result = extract_comments("x # first\n y # second").unwrap();
    assert_eq!(
        result,
        vec![
            Comment {
                token: _token("# first", 2, 1, 3),
                value: _token(" first", 3, 1, 4),
            },
            Comment {
                token: _token("# second", 13, 2, 4),
                value: _token(" second", 14, 2, 5),
            },
        ],
    );
}

#[test]
fn test_comment_inside_string_not_extracted() {
    let result = extract_comments(r#""text # not a comment""#).unwrap();
    assert_eq!(result, vec![],);
}

#[test]
fn test_comment_after_string_extracted() {
    let result = extract_comments(r#""t#xt" # this is a comment"#).unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("# this is a comment", 7, 1, 8),
            value: _token(" this is a comment", 8, 1, 9),
        }],
    );
}

#[test]
fn test_multiline_string() {
    // Newlines in triple-quoted strings are preserved
    let result = extract_comments("1 \n 2 \"\"\"my\n#tring\"\"\" 3 \n 4").unwrap();
    assert_eq!(result, vec![]);

    let result = extract_comments("1 \n 2 '''my\n#tring''' 3 \n 4").unwrap();
    assert_eq!(result, vec![]);
}

#[test]
fn test_raw_string_preserves_newlines() {
    // In this case `\n` in string is a newline
    let result = extract_comments("1 \n 2 r\"\"\"my\n#tring\"\"\" 3 \n 4").unwrap();
    assert_eq!(result, vec![],);

    // In this case `\#` in raw string is two characters `\` and `#` (not an escape)
    let result = extract_comments(r#"1 \n 2 r"""my\#string""" 3 \n 4"#).unwrap();
    assert_eq!(result, vec![],);
}

#[test]
fn test_fstring_newline_replacement() {
    // Newlines in triple-quoted strings are preserved
    let result = extract_comments("f\"\"\"my#\n{#name}\"\"\"").unwrap();
    assert_eq!(result, vec![],);
}

#[test]
fn test_regular_string_no_newline() {
    let result = extract_comments("\"he#lo\"").unwrap();
    assert_eq!(result, vec![]);
}

#[test]
fn test_single_quoted_string_with_literal_newline() {
    // Single-quoted strings cannot contain literal newlines in Python
    // The preprocessing preserves the newline, but parsing will catch this as a syntax error.
    let result = extract_comments("'ab#\n'").unwrap();
    assert_eq!(result, vec![]);

    let result = extract_comments("\"ab#\n\"").unwrap();
    assert_eq!(result, vec![]);
}

#[test]
fn test_multiline_string_with_comment() {
    // Newlines in triple-quoted strings are preserved (will work with exec())
    let result = extract_comments("\"\"\"my\n#tring\"\"\" # comment").unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("# comment", 16, 2, 11),
            value: _token(" comment", 17, 2, 12),
        }],
    );
}

#[test]
fn test_string_with_escape_sequence() {
    let result = extract_comments(r##""t#xt \"qu#te\"#" # after"##).unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("# after", 18, 1, 19),
            value: _token(" after", 19, 1, 20),
        }],
    );
}

#[test]
fn test_raw_string_with_escape_sequence() {
    let result = extract_comments(r##"r"t#xt \"qu#te\"#" # after"##).unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("# after", 19, 1, 20),
            value: _token(" after", 20, 1, 21),
        }],
    );
}

#[test]
fn test_string_prefixes() {
    // Test various string prefixes
    assert_eq!(extract_comments(r#"r"raw""#).unwrap(), vec![],);
    assert_eq!(extract_comments(r#"f"formatted""#).unwrap(), vec![],);
    assert_eq!(extract_comments(r#"b"bytes""#).unwrap(), vec![],);
    assert_eq!(extract_comments(r#"rf"raw formatted""#).unwrap(), vec![],);
}

#[test]
fn test_comment_before_string() {
    let source = r#"# comment before"text""#;
    let result = extract_comments(source).unwrap();
    // When there's no newline, the comment extends to the end of input
    // So the comment includes " comment before"text""
    assert_eq!(
        result,
        vec![Comment {
            token: _token(source, 0, 1, 1),
            value: _token(&source[1..], 1, 1, 2),
        }],
    );
}

#[test]
fn test_nested_strings() {
    // String containing quote characters
    let result = extract_comments(r#""ou#ter 'in#ner' ou#ter""#).unwrap();
    assert_eq!(result, vec![],);
}

#[test]
fn test_triple_quotes_in_single_quote_string() {
    // Triple quotes inside a single-quote string should not close it
    let result = extract_comments(r#"'''te#xt \"\"\" ins#ide\"\"\te#xt2'''"#).unwrap();
    assert_eq!(result, vec![],);
}

#[test]
fn test_empty_comment() {
    let result = extract_comments("x #").unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("#", 2, 1, 3),
            value: _token("", 3, 1, 4),
        }],
    );
}

#[test]
fn test_comment_with_carriage_return() {
    let result = extract_comments("x # comment\r\nnext").unwrap();
    assert_eq!(
        result,
        vec![Comment {
            token: _token("# comment", 2, 1, 3),
            value: _token(" comment", 3, 1, 4),
        }],
    );
}

#[test]
fn test_multiline_string_with_escaped_newline() {
    // Escaped newline in non-raw string should not be replaced
    let result = extract_comments(r#""line1\\nline2""#).unwrap();
    assert_eq!(result, vec![]);
}

#[test]
fn test_complex_expression_with_comments() {
    let result = extract_comments(
        "[      # comment 1\n  1,   # comment 2\n  2,   # comment 3\n]       # comment 4",
    )
    .unwrap();
    assert_eq!(
        result,
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
