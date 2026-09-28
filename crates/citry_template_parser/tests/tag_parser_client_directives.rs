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

    #[test]
    fn component_tags_keep_bind_on_and_plain_show() {
        let node = parse_first_node(
            r#"<c-child v-show="open" v-bind="props" v-bind:x="a" v-on:y="b()" />"#,
        )
        .unwrap();
        let keys = node
            .attrs()
            .iter()
            .map(|attr| attr.key.content.as_str())
            .collect::<Vec<_>>();
        assert_eq!(keys, ["v-show", "v-bind", "v-bind:x", "v-on:y"]);
        // The dynamic element renders plain HTML, so its directives are not
        // component-tag directives.
        parse_template(r#"<c-element is="div" v-if="open" />"#, None, None).unwrap();
        // `#c-*` stays Citry metadata rather than a slot shorthand.
        parse_template(r#"<c-child #c-key="row" />"#, None, None).unwrap();
    }

    #[test]
    fn component_tags_carry_conditions_models_and_custom_directives() {
        let node = parse_first_node(
            r#"<c-child v-if="a" v-else-if="b" v-else v-model="q" v-model:title.trim="t" v-focus v-tooltip:top.delay="tip" />"#,
        )
        .unwrap();
        let keys = node
            .attrs()
            .iter()
            .map(|attr| attr.key.content.as_str())
            .collect::<Vec<_>>();
        assert_eq!(
            keys,
            [
                "v-if",
                "v-else-if",
                "v-else",
                "v-model",
                "v-model:title.trim",
                "v-focus",
                "v-tooltip:top.delay",
            ]
        );
        // A lone or empty `v-else` and a dynamic component call parse the same way.
        parse_template(r#"<c-child v-else="" />"#, None, None).unwrap();
        parse_template(r#"<c-child v-else />"#, None, None).unwrap();
        parse_template(r#"<c-component is="child" v-if="open" />"#, None, None).unwrap();
    }

    #[test]
    fn component_tags_reject_other_vue_directives_with_a_fix() {
        let cases = [
            (r#"<c-child v-for="row in rows" />"#, "'v-for'", "<c-for>"),
            (r#"<c-child v-html="markup" />"#, "'v-html'", "<c-fill>"),
            (r#"<c-child v-text="label" />"#, "'v-text'", "<c-fill>"),
            (r#"<c-child v-slot="data" />"#, "'v-slot'", "<c-fill name="),
            (
                r##"<c-child #header="data" />"##,
                "'#header'",
                "<c-fill name=",
            ),
            (
                r#"<c-child v-show.lazy="open" />"#,
                "'v-show.lazy'",
                "without an argument",
            ),
            (
                r#"<c-child v-if.once="open" />"#,
                "'v-if.once'",
                "without an argument or modifiers",
            ),
            (
                r#"<c-child v-else:x />"#,
                "'v-else:x'",
                "without an argument or modifiers",
            ),
            (
                r#"<c-child v-once />"#,
                "'v-once'",
                "inside the child's template",
            ),
            (
                r#"<c-child v-citry-control="x" />"#,
                "'v-citry-control'",
                "Citry reserves",
            ),
            (r#"<c-child v-If="open" />"#, "'v-If'", "lowercase"),
            (
                r#"<c-child v-On:click="go()" />"#,
                "'v-On:click'",
                "lowercase",
            ),
            (r#"<c-child v-model:="q" />"#, "'v-model:'", "Name the prop"),
            (r#"<c-child v-on:="go()" />"#, "'v-on:'", "'@event="),
            (
                r#"<c-child v-bind.prop="value" />"#,
                "'v-bind.prop'",
                "':name=",
            ),
            (r#"<c-child .value="text" />"#, "'.value'", "':name="),
            (
                r#"<c-child c-v-for="row in rows" />"#,
                "'c-v-for'",
                "<c-for>",
            ),
        ];
        for (source, name, hint) in cases {
            let message = format!("{}", parse_template(source, None, None).unwrap_err());
            assert!(
                message.contains(&format!(
                    "Vue directive {name} is not supported on the component tag"
                )),
                "{source}: {message}"
            );
            assert!(message.contains(hint), "{source}: {message}");
        }
    }

    #[test]
    fn component_tag_directives_need_an_expression() {
        for (source, name) in [
            (r#"<c-child v-show />"#, "'v-show'"),
            (r#"<c-child v-show=" " />"#, "'v-show'"),
            (r#"<c-child v-if />"#, "'v-if'"),
            (r#"<c-child v-else-if="" />"#, "'v-else-if'"),
            (r#"<c-child v-model />"#, "'v-model'"),
            (r#"<c-child v-model:title />"#, "'v-model:title'"),
        ] {
            let message = format!("{}", parse_template(source, None, None).unwrap_err());
            assert!(
                message.contains(&format!(
                    "{name} on the component tag '<c-child>' needs a Vue expression"
                )),
                "{source}: {message}"
            );
        }
        let message = format!(
            "{}",
            parse_template(r#"<c-child v-else="x" />"#, None, None).unwrap_err()
        );
        assert!(
            message.contains("'v-else' on the component tag '<c-child>' takes no value"),
            "{message}"
        );
    }

    #[test]
    fn slot_tags_reject_every_vue_directive_with_a_fix() {
        // A `<c-slot>` attribute is Python slot data, so no Vue form has a
        // meaning there, including the `:`/`@` shorthands a component keeps.
        let cases = [
            (r#"<c-slot v-if="open" />"#, "'v-if'", "<c-if>"),
            (r#"<c-slot name="body" v-else />"#, "'v-else'", "<c-if>"),
            (r#"<c-slot v-for="row in rows" />"#, "'v-for'", "<c-for>"),
            (
                r#"<c-slot v-show="open" />"#,
                "'v-show'",
                "carries 'v-show'",
            ),
            (r#"<c-slot :item="row" />"#, "':item'", "Vue slot props"),
            (r#"<c-slot v-bind="props" />"#, "'v-bind'", "Vue slot props"),
            (r#"<c-slot @click="go()" />"#, "'@click'", "inside the fill"),
            (r#"<c-slot .value="text" />"#, "'.value'", "Vue slot props"),
            (r##"<c-slot #header />"##, "'#header'", "Name the slot with"),
            (r#"<c-slot v-focus />"#, "'v-focus'", "fallback content"),
            (r#"<c-slot c-v-if="open" />"#, "'c-v-if'", "<c-if>"),
        ];
        for (source, name, hint) in cases {
            let message = format!("{}", parse_template(source, None, None).unwrap_err());
            assert!(
                message.contains(&format!(
                    "Vue directive {name} is not supported on '<c-slot>'"
                )),
                "{source}: {message}"
            );
            assert!(message.contains(hint), "{source}: {message}");
        }
        // Plain and `c-` attributes stay slot data.
        parse_template(
            r#"<c-slot name="row" item="x" c-count="n" required />"#,
            None,
            None,
        )
        .unwrap();
    }
}
