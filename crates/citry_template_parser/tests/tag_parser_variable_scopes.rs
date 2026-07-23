// Scope contract for variables introduced by c-for and c-fill.

mod common;

#[cfg(test)]
mod tests {
    use citry_template_parser::parser::parse_template;

    use super::common::assert_parse_error;

    #[test]
    fn test_binding_is_local_to_its_own_body() {
        for input in [
            r#"<c-for each="x in xs">{{ x }}</c-for>"#,
            r#"<li c-for="x in xs" c-title="x">{{ x }}</li>"#,
            r#"<c-card><c-fill name="default" data="x">{{ x }}</c-fill></c-card>"#,
        ] {
            assert!(
                parse_template(input, None, None).is_ok(),
                "input: {input:?}"
            );
        }
    }

    #[test]
    fn test_sibling_bindings_do_not_shadow_each_other() {
        let input = concat!(
            r#"<c-for each="x in xs">{{ x }}</c-for>"#,
            r#"<c-for each="x in ys">{{ x }}</c-for>"#,
        );
        assert!(parse_template(input, None, None).is_ok());
    }

    #[test]
    fn test_loop_target_cannot_read_same_outer_name() {
        for input in [
            r#"<c-for each="x in x">{{ x }}</c-for>"#,
            r#"<li c-for="x in x">{{ x }}</li>"#,
        ] {
            assert_parse_error(input, "Variable shadowing is not allowed");
        }
    }

    #[test]
    fn test_binding_cannot_reuse_root_or_active_outer_name() {
        for input in [
            r#"{{ x }}<c-for each="x in xs">{{ x }}</c-for>"#,
            r#"<c-for each="x in xs"><c-for each="x in ys">{{ x }}</c-for></c-for>"#,
            r#"<c-for each="x in xs"><c-card><c-fill name="default" data="x">{{ x }}</c-fill></c-card></c-for>"#,
            r#"<div c-if="x" c-for="x in xs">{{ x }}</div>"#,
            r#"<c-card><c-fill name="default" c-bind="x" data="x">{{ x }}</c-fill></c-card>"#,
        ] {
            assert_parse_error(input, "Variable shadowing is not allowed");
        }
    }

    #[test]
    fn test_duplicate_loop_targets_are_rejected_at_the_second_target() {
        for input in [
            r#"<c-for each="x, x in pairs">{{ x }}</c-for>"#,
            r#"<c-for each="x in xs for x in ys">{{ x }}</c-for>"#,
        ] {
            assert_parse_error(input, "Cannot define variable 'x' more than once");
        }
    }

    #[test]
    fn test_nested_template_attribute_binding_sees_writer_scope() {
        for input in [
            r#"<c-for each="x in xs"><c-writer c-body="<c-for each='x in ys'>{{ x }}</c-for>" /></c-for>"#,
            r#"{{ x }}<c-writer c-body="<c-for each='x in ys'>{{ x }}</c-for>" />"#,
        ] {
            assert_parse_error(input, "Variable shadowing is not allowed");
        }
    }

    #[test]
    fn test_nested_template_attribute_internal_binding_remains_local() {
        let input = r#"<c-writer c-body="<c-for each='x in xs'>{{ x }}</c-for>" />"#;
        let template = parse_template(input, None, None).unwrap();
        let names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|token| token.content.as_str())
            .collect();
        assert_eq!(names, vec!["xs"]);
    }

    #[test]
    fn test_nested_template_attribute_sibling_bindings_have_separate_scopes() {
        for input in [
            concat!(
                r#"<c-writer c-body="<section>"#,
                r#"<c-for each='x in xs'>{{ x }}</c-for>"#,
                r#"<c-for each='x in ys'>{{ x }}</c-for>"#,
                r#"</section>" />"#,
            ),
            concat!(
                r#"<c-writer c-body="<>"#,
                r#"<c-child><c-fill name='one' data='x'>{{ x }}</c-fill></c-child>"#,
                r#"<c-child><c-fill name='two' data='x'>{{ x }}</c-fill></c-child>"#,
                r#"</>" />"#,
            ),
        ] {
            assert!(
                parse_template(input, None, None).is_ok(),
                "input: {input:?}"
            );
        }
    }
}
