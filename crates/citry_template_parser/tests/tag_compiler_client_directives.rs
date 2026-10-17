//! Migration locks for removed `$c-props` aliases and native Vue call syntax.

#[cfg(test)]
mod tests {
    use citry_template_parser::parser::parse_template;

    #[test]
    fn retired_client_props_aliases_name_native_vue_replacement() {
        for source in [
            r#"<c-child $c-props="{ count: localCount }" />"#,
            r#"<c-child c-$c-props="props_source" />"#,
        ] {
            let error = parse_template(source, None, None).unwrap_err();
            let message = format!("{error}");
            assert!(message.contains("was removed"), "{message}");
            assert!(
                message.contains(":prop") && message.contains("v-bind"),
                "{message}"
            );
        }
    }

    #[test]
    fn native_vue_component_bindings_remain_structured_for_python_capture() {
        assert!(parse_template(
            r#"<c-child :disabled="blocked" @change="changed($event)" ref="root" />"#,
            None,
            None,
        )
        .is_ok());
    }
}
