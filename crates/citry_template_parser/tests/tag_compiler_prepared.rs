//! Contract tests for the private prepared-view compiler target.

use citry_template_parser::compiler::{compile_prepared_template, compile_template};
use citry_template_parser::lang::lang::Lang;
use citry_template_parser::parser::parse_template;
use citry_template_parser::{parse_template_with_options, ForeignSpan, ParseOptions};

fn compile(source: &str) -> String {
    let template = parse_template(source, None, None).expect("template should parse");
    compile_prepared_template(template, None).expect("prepared template should compile")
}

#[test]
fn emits_typed_html_text_expression_and_metadata_parts() {
    let source = "<main class=\"card\" #c-key=\"item.id\">ž {{ value }}</main>";
    let output = compile(source);

    assert!(
        output.contains("PreparedElementOpenNode(source, (0, 36,)"),
        "{output}"
    );
    assert!(output.contains("StaticHtmlAttr(source"));
    assert!(output.contains("\"\"\"class\"\"\", \"\"\"card\"\"\""));
    assert!(output.contains("PreparedSourceTextNode(source, (36, 39,), \"\"\"ž \"\"\")"));
    assert!(
        output.contains("PreparedExprNode(source, (39, 50,), \"\"\"value \"\"\", (\"value\",))")
    );
    assert!(output.contains("(\"key\", ExprHtmlAttr(source"));
    assert!(output.contains("PreparedElementCloseNode(source, (50, 57,), \"\"\"main\"\"\")"));
}

#[test]
fn propagates_prepared_mode_through_control_components_slots_and_fills() {
    let output = compile(
        "<c-if cond=\"show\"><c-Card><c-fill name=\"title\"><span>T</span></c-fill></c-Card></c-if>",
    );

    assert!(output.contains("IfNode("));
    assert!(output.contains("ComponentNode("));
    assert!(output.contains("FillNode("));
    assert!(output.contains("PreparedElementOpenNode("));
    assert!(output.contains("PreparedSourceTextNode("));
    assert!(output.contains("PreparedElementCloseNode("));
    assert!(!output.contains("\"\"\"<span>T</span>\"\"\""));
}

#[test]
fn distinguishes_void_and_nonvoid_self_closing_elements() {
    let output = compile("<br><img/><section/>");

    assert_eq!(output.matches("PreparedElementOpenNode(").count(), 3);
    assert_eq!(output.matches("PreparedElementCloseNode(").count(), 1);
    assert!(output.contains("\"\"\"br\"\"\", (), (), True, False"));
    assert!(output.contains("\"\"\"img\"\"\", (), (), True, True"));
    assert!(output.contains("\"\"\"section\"\"\", (), (), False, True"));
}

#[test]
fn propagates_mode_through_shorthand_control_and_dynamic_element() {
    let output = compile(
        "<article c-if=\"show\"><c-element c-is=\"'aside'\"><b c-class=\"kind\">x</b></c-element></article>",
    );

    assert!(output.contains("IfNode("));
    assert!(output.contains("ComponentNode("));
    assert!(output.contains("\"\"\"element\"\"\""));
    assert_eq!(output.matches("PreparedElementOpenNode(").count(), 2);
    assert!(output.contains("ExprHtmlAttr("));
    assert!(output.contains("PreparedSourceTextNode("));
    assert_eq!(output.matches("PreparedElementCloseNode(").count(), 2);
}

#[test]
fn ordinary_compilation_stays_byte_identical_and_prepared_is_deterministic() {
    let source = "<p>Hello {{ name }}</p>";
    let ordinary_template = parse_template(source, None, None).unwrap();
    let ordinary = compile_template(ordinary_template, None).unwrap();
    assert_eq!(
        ordinary,
        "def generate_template():\n    body = [\"\"\"<p>Hello \"\"\", ExprNode(source, (9, 19,), \"\"\"name \"\"\", (\"name\",)), \"\"\"</p>\"\"\",]\n    return body\n"
    );

    assert_eq!(compile(source), compile(source));
}

#[test]
fn rejects_targets_and_sources_without_a_prepared_contract() {
    for lang in [Lang::Php, Lang::Js, Lang::Go, Lang::Rust] {
        let template = parse_template("<p>x</p>", None, None).unwrap();
        let error = compile_prepared_template(template, Some(lang)).unwrap_err();
        assert!(error
            .to_string()
            .contains("prepared template compilation currently supports only Python"));
    }

    let source = "before {% host %} after";
    let start = source.find("{% host %}").unwrap();
    let options = ParseOptions::with_foreign_spans(vec![ForeignSpan::from_parts(
        start,
        start + "{% host %}".len(),
        "host",
        0,
        false,
    )]);
    let foreign = parse_template_with_options(source, None, None, &options).unwrap();
    assert!(compile_prepared_template(foreign, None)
        .unwrap_err()
        .to_string()
        .contains("does not yet support foreign source"));
}

#[test]
fn raw_compiles_to_distinct_opaque_html_data() {
    let raw = parse_template("<c-raw><b>{{ x }}</b></c-raw>", None, None).unwrap();
    let output = compile_prepared_template(raw, None).unwrap();
    assert!(output.contains(r#"PreparedVerbatimHtmlNode(source, (7, 21,), """<b>{{ x }}</b>""")"#));
    assert!(!output.contains("PreparedSourceTextNode"));

    let empty = parse_template("<c-raw></c-raw>", None, None).unwrap();
    assert!(compile_prepared_template(empty, None)
        .unwrap()
        .contains(r#"PreparedVerbatimHtmlNode(source, (7, 7,), """""")"#));
}
