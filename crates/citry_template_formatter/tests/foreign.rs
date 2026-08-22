use citry_template_formatter::{ParseOptions, format_template_with_options};
use citry_template_parser::ForeignSpan;

fn options_for(source: &str, needles: &[(&str, bool)]) -> ParseOptions {
    let mut spans = Vec::new();
    let mut cursor = 0;
    for (ordinal, (needle, may_control_body)) in needles.iter().enumerate() {
        let relative = source[cursor..]
            .find(needle)
            .unwrap_or_else(|| panic!("missing foreign source {needle:?}"));
        let start = cursor + relative;
        let end = start + needle.len();
        spans.push(ForeignSpan::from_parts(
            start,
            end,
            "test-host",
            ordinal,
            *may_control_body,
        ));
        cursor = end;
    }
    ParseOptions::with_foreign_spans(spans)
}

#[test]
fn preserves_body_foreign_spans_while_formatting_citry_markup() {
    let source = "é<main><section  class = 'x' ></section>{% if active %}<footer></footer>{% endif %}</main>";
    let options = options_for(source, &[("{% if active %}", true), ("{% endif %}", true)]);

    let formatted = format_template_with_options(source, &options).unwrap();

    assert!(formatted.contains("{% if active %}"));
    assert!(formatted.contains("{% endif %}"));
    assert!(formatted.contains("<section class='x'></section>"));
    let reparsed_options = options_for(
        &formatted,
        &[("{% if active %}", true), ("{% endif %}", true)],
    );
    assert_eq!(
        format_template_with_options(&formatted, &reparsed_options).unwrap(),
        formatted,
    );
}

#[test]
fn treats_attribute_and_start_tag_foreign_spans_as_unknown_source() {
    let attribute = r#"<div class="{% if active %}on{% endif %}"  title = "x"></div>"#;
    let attribute_options = options_for(
        attribute,
        &[("{% if active %}", true), ("{% endif %}", true)],
    );
    let formatted = format_template_with_options(attribute, &attribute_options).unwrap();
    assert_eq!(
        formatted,
        r#"<div class="{% if active %}on{% endif %}" title="x"></div>"#,
    );

    let start_tag = r#"<div  class="x" {% html_attrs attrs %} id = "y"></div>"#;
    let start_tag_options = options_for(start_tag, &[("{% html_attrs attrs %}", false)]);
    assert_eq!(
        format_template_with_options(start_tag, &start_tag_options).unwrap(),
        start_tag,
    );
}

#[test]
fn accepts_root_absolute_options_for_a_projected_source() {
    let source = r#"<div class="{% host %}"  title = "x"></div>"#;
    let root = format!("before:{source}:after");
    let source_offset = "before:".len();
    let local_start = source.find("{% host %}").unwrap();
    let options = ParseOptions::with_projection(
        vec![ForeignSpan::from_parts(
            source_offset + local_start,
            source_offset + local_start + "{% host %}".len(),
            "test-host",
            0,
            false,
        )],
        source_offset,
        root,
    );

    assert_eq!(
        format_template_with_options(source, &options).unwrap(),
        r#"<div class="{% host %}" title="x"></div>"#,
    );
}
