use citry_template_formatter::{FormatErrorKind, format_template};

#[test]
fn public_api_formats_and_is_idempotent() {
    let source = r#"<c-CButton  class = "primary"  disabled ></c-CButton>"#;
    let expected = r#"<c-CButton class="primary" disabled></c-CButton>"#;

    let formatted = format_template(source).expect("format valid template");
    assert_eq!(formatted, expected);
    assert_eq!(format_template(&formatted).unwrap(), formatted);
}

#[test]
fn syntax_errors_retain_the_parser_diagnostic() {
    let error = format_template("<c-raw />").expect_err("invalid template");

    assert_eq!(error.kind(), FormatErrorKind::Syntax);
    assert_eq!(error.code(), "citry.format.syntax");
    let diagnostic = error
        .parse_diagnostic()
        .expect("syntax error retains parser diagnostic");
    assert!(diagnostic.code.starts_with("citry.parse."));
    assert!(error.range().is_some());
}

#[test]
fn generated_valid_tags_preserve_contract_and_converge() {
    let spacings = [" ", "  ", "\t", "\n  ", "\r\n  "];
    let attributes = [
        r#"class = "x""#,
        "disabled",
        "data-key = value",
        r#"c-active = "is_active""#,
        r#"#c-key = "item.id""#,
    ];

    for spacing in spacings {
        for first in attributes {
            for second in attributes {
                if first == second {
                    continue;
                }
                let source = format!("<div{spacing}{first}{spacing}{second} ></div>");
                let formatted = format_template(&source)
                    .unwrap_or_else(|error| panic!("failed for {source:?}: {error}"));
                assert_eq!(
                    format_template(&formatted).unwrap(),
                    formatted,
                    "input: {source:?}",
                );
            }
        }
    }
}

#[test]
fn earlier_same_line_edits_do_not_stale_later_tag_layout() {
    let nested = r#"<main  id = "x" ><div {# note #}></div></main>"#;
    let nested_expected = "<main id=\"x\">\n  <div {# note #}></div>\n</main>";
    let siblings = r#"<div  id = "x" ></div><div {# note #}></div>"#;
    let siblings_expected = "<div id=\"x\"></div>\n<div {# note #}></div>";

    assert_eq!(format_template(nested).unwrap(), nested_expected);
    assert_eq!(format_template(siblings).unwrap(), siblings_expected);

    let title = "x".repeat(60);
    let boundary = format!(r#"<div  id = "x" ></div><span title="{title}"></span>"#);
    let boundary_expected = format!(r#"<div id="x"></div><span title="{title}"></span>"#);
    assert_eq!(format_template(&boundary).unwrap(), boundary_expected);

    let title = "x".repeat(61);
    let over_boundary = format!(r#"<div  id = "x" ></div><span title="{title}"></span>"#);
    let over_boundary_expected = format!(
        "<div id=\"x\"></div><span\n{}title=\"{title}\"\n{}></span>",
        " ".repeat(20),
        " ".repeat(18),
    );
    assert_eq!(
        format_template(&over_boundary).unwrap(),
        over_boundary_expected,
    );

    let dependency_chain = "<div {# note #}></div>".repeat(12);
    let formatted_chain = format_template(&dependency_chain).unwrap();
    assert_eq!(format_template(&formatted_chain).unwrap(), formatted_chain);
}

#[test]
fn width_boundary_counts_unicode_scalars() {
    let exact = format!(r#"<div title="{}"></div>"#, "é".repeat(80));
    let over = format!(r#"<div title="{}"></div>"#, "é".repeat(81));

    assert!(!format_template(&exact).unwrap().contains('\n'));
    assert!(format_template(&over).unwrap().starts_with("<div\n"));
}

#[test]
fn long_item_boundary_uses_unicode_scalars() {
    let exact = format!(r#"<div id="x" data="{}"></div>"#, "é".repeat(43));
    let over = format!(r#"<div id="x" data="{}"></div>"#, "é".repeat(44));

    assert!(!format_template(&exact).unwrap().contains('\n'));
    assert!(format_template(&over).unwrap().starts_with("<div\n"));
}

#[test]
fn multiline_tags_move_only_across_unprotected_structural_gaps() {
    let title = "x".repeat(100);
    let component = format!(r#"<c-Card><div title="{title}"></div></c-Card>"#);
    let formatted_component = format_template(&component).unwrap();
    assert!(formatted_component.starts_with("<c-Card><div\n"));
    assert!(formatted_component.ends_with("></div></c-Card>"));

    let skipped = format!(r#"<main>{{# fmt: skip #}}<div title="{title}"></div></main>"#,);
    assert_eq!(format_template(&skipped).unwrap(), skipped);

    let shorthand = format!(r#"<main><div c-if="show" title="{title}"></div></main>"#,);
    let formatted_shorthand = format_template(&shorthand).unwrap();
    assert!(formatted_shorthand.starts_with("<main><div\n"));
    assert!(formatted_shorthand.ends_with("></div></main>"));
}

#[test]
fn structural_siblings_have_single_gap_owners() {
    let title = "x".repeat(100);
    let source =
        format!(r#"<main><div title="{title}"></div><section title="{title}"></section></main>"#,);
    let expected = format!(
        "<main>\n  <div\n    title=\"{title}\"\n  ></div>\n  <section\n    title=\"{title}\"\n  ></section>\n</main>",
    );

    assert_eq!(format_template(&source).unwrap(), expected);
}

#[test]
fn structural_target_column_prevents_wrap_then_unwrap_residue() {
    let title = "x".repeat(75);
    let source = format!(r#"<main><div title="{title}"></div></main>"#);

    let expected = format!("<main>\n  <div title=\"{title}\"></div>\n</main>",);
    assert_eq!(format_template(&source).unwrap(), expected);
}

#[test]
fn trailing_only_placement_uses_the_actual_tag_column() {
    let title = "x".repeat(69);
    let source = format!(r#"<main>prefix<div title="{title}"></div></main>"#);
    let expected = format!(
        "<main>prefix<div\n{}title=\"{title}\"\n{}></div></main>",
        " ".repeat(14),
        " ".repeat(12),
    );

    assert_eq!(format_template(&source).unwrap(), expected);
}

#[test]
fn inserted_lines_follow_lone_cr_and_scalar_source_column() {
    let comment = format!("{{# {} #}}", "x".repeat(100));
    let source = format!("head\ré<div {comment}></div>");
    let expected = format!("head\ré<div\r   {comment}\r ></div>");

    assert_eq!(format_template(&source).unwrap(), expected);
}

#[test]
fn empty_and_text_only_templates_are_stable() {
    for source in ["", "plain text", "nonbreaking\u{00a0}space"] {
        assert_eq!(format_template(source).unwrap(), source);
    }
}

#[test]
fn directives_inside_end_tags_are_rejected() {
    let error = format_template("<div></div {# fmt: skip #}>").unwrap_err();

    assert_eq!(error.kind(), FormatErrorKind::Suppression);
    assert_eq!(error.code(), "citry.format.suppression");
    assert!(error.to_string().contains("end tag"));
}
