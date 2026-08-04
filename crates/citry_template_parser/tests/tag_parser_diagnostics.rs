use citry_template_parser::{parse_template, ParseError};

#[test]
fn grammar_failure_exposes_its_root_source_position() {
    let source = "Hello {{ name";
    let error = parse_template(source, None, None).unwrap_err();
    let diagnostic = error.diagnostic();

    assert_eq!(diagnostic.code, "citry.parse.syntax");
    assert_eq!(diagnostic.message, error.to_string());
    assert_eq!(diagnostic.start_index, Some(13));
    assert_eq!(diagnostic.end_index, Some(13));
    assert_eq!(diagnostic.start_line, Some(1));
    assert_eq!(diagnostic.start_column, Some(14));
    assert_eq!(diagnostic.end_line, Some(1));
    assert_eq!(diagnostic.end_column, Some(14));
}

#[test]
fn semantic_failure_exposes_a_half_open_byte_range() {
    let source = "<div></span>";
    let error = parse_template(source, None, None).unwrap_err();
    let diagnostic = error.diagnostic();

    assert_eq!(diagnostic.code, "citry.parse.syntax");
    assert_eq!(diagnostic.start_index, Some(5));
    assert_eq!(diagnostic.end_index, Some(12));
    assert_eq!(diagnostic.start_line, Some(1));
    assert_eq!(diagnostic.start_column, Some(6));
    assert_eq!(diagnostic.end_line, Some(1));
    assert_eq!(diagnostic.end_column, Some(13));
}

#[test]
fn unpositioned_value_failure_has_no_source_range() {
    let error = ParseError::Value("cannot map internal source position".to_string());
    let diagnostic = error.diagnostic();

    assert_eq!(diagnostic.code, "citry.parse.value");
    assert_eq!(diagnostic.message, error.to_string());
    assert_eq!(diagnostic.start_index, None);
    assert_eq!(diagnostic.end_index, None);
    assert_eq!(diagnostic.start_line, None);
    assert_eq!(diagnostic.start_column, None);
    assert_eq!(diagnostic.end_line, None);
    assert_eq!(diagnostic.end_column, None);
}
