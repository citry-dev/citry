//! Parser migration contract for native Vue component-call bindings.

mod common;

#[cfg(test)]
mod tests {
    use citry_template_parser::parser::parse_template;

    use super::common::parse_first_node;

    #[test]
    fn native_vue_bindings_preserve_authored_order_and_spans() {
        let node = parse_first_node(
            r#"<c-child :disabled="blocked" @change="changed($event)" ref="root" />"#,
        )
        .unwrap();
        let keys = node
            .attrs()
            .iter()
            .map(|attr| attr.key.content.as_str())
            .collect::<Vec<_>>();
        assert_eq!(keys, [":disabled", "@change", "ref"]);
        assert!(node
            .attrs()
            .windows(2)
            .all(|pair| pair[0].token.end_index < pair[1].token.start_index));
    }

    #[test]
    fn retired_aliases_are_rejected_everywhere() {
        for source in [
            r#"<c-child $c-props="value" />"#,
            r#"<div c-$c-props="value"></div>"#,
        ] {
            assert!(
                format!("{}", parse_template(source, None, None).unwrap_err())
                    .contains("was removed")
            );
        }
    }
}
