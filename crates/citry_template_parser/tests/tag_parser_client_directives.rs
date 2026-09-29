//! Parser migration contract for native Vue component-call bindings.

mod common;

#[cfg(test)]
mod tests {
    use citry_template_parser::parser::parse_template;

    use super::common::{assert_parse_error, parse_first_node};

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
            (r#"<c-child v-once />"#, "'v-once'", "Remove the directive"),
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

    #[test]
    fn a_vue_binding_and_a_python_value_for_one_attribute_are_rejected() {
        assert_parse_error(
            r#"<p c-title="label" :title="hint">x</p>"#,
            "':title' on <p> (line 1, column 20) sets the same attribute as 'c-title'. Set the attribute in one place: keep 'c-title' when Python decides the value, or keep ':title' and send the value to the browser with js_data().",
        );
        for (input, expected) in [
            (
                r#"<p v-bind:TITLE="hint" c-title="label">x</p>"#,
                "'v-bind:TITLE' on <p>",
            ),
            (
                r#"<c-element c-is="'p'" c-id="a" :id="b" />"#,
                "':id' on <c-element>",
            ),
            (
                r#"<li v-for="item in items" #c-key="k" :key="item.id">x</li>"#,
                "Keep '#c-key' to key the element from Python, or remove it and keep ':key'.",
            ),
            (
                r#"<p c-class="a" :class.prop="b">x</p>"#,
                "Remove the modifier and write ':class', which Vue joins with 'c-class'.",
            ),
        ] {
            assert_parse_error(input, expected);
        }
        // An object `v-bind` or a dynamic name may set any attribute.
        for (input, expected) in [
            (
                r#"<p v-bind="attrs" c-title="t">x</p>"#,
                "'v-bind' on <p> (line 1, column 4) may set any attribute, so it cannot be combined with 'c-title', which Python sets.",
            ),
            (r#"<p c-bind="d" :[name]="v">x</p>"#, "':[name]' on <p>"),
            (r#"<p #c-key="k" v-bind:[name]="v">x</p>"#, "'#c-key'"),
            (
                r#"<c-element c-is="'p'" v-bind="attrs" c-id="i" />"#,
                "cannot be combined with 'c-id'",
            ),
        ] {
            assert_parse_error(input, expected);
        }
        // Vue joins a bound class or style with the Python one, a component
        // tag's `c-*` attributes are Python inputs rather than attributes,
        // and a structural `c-if` or `c-is` sets no attribute.
        for input in [
            r#"<p c-class="a" :class="b" c-style="c" v-bind:style="d">x</p>"#,
            r#"<c-Card c-title="a" :title="b" />"#,
            r#"<p title="a" :title="b">x</p>"#,
            r#"<p v-bind="attrs" class="a" c-if="ok">x</p>"#,
            r#"<c-element c-is="'p'" v-bind="attrs" />"#,
            r#"<c-Card v-bind="props" c-title="a" />"#,
        ] {
            parse_template(input, None, None).unwrap();
        }
    }

    #[test]
    fn alpine_only_listener_modifiers_are_rejected_with_the_vue_form() {
        assert_parse_error(
            r#"<div @click.outside="open = false;">x</div>"#,
            "'@click.outside' (line 1, column 6) uses the Alpine modifier '.outside', which Vue does not have. Vue would read '.outside' as a key name, so the listener would never run. Add a 'click' listener to document in mounted(), check whether this.$el contains event.target, and remove the listener in unmounted().",
        );
        for (input, modifier, hint) in [
            (
                r#"<div @click.away="x = 1;"></div>"#,
                "away",
                "this.$el contains event.target",
            ),
            (
                r#"<div @resize.window="x = 1;"></div>"#,
                "window",
                "window.addEventListener",
            ),
            (
                r#"<div v-on:keyup.document="x = 1;"></div>"#,
                "document",
                "document.addEventListener",
            ),
            (
                r#"<input @input.debounce.500ms="x = 1;" />"#,
                "debounce",
                "'@c-input.debounce'",
            ),
            (
                r#"<input @input.throttle="x = 1;" />"#,
                "throttle",
                "setTimeout",
            ),
            (
                r#"<div @custom-event.camel="x = 1;"></div>"#,
                "camel",
                "exact event name",
            ),
            (
                r#"<div @custom-event.dot="x = 1;"></div>"#,
                "dot",
                "exact event name",
            ),
            (r#"<input @keydown.cmd.enter="x = 1;" />"#, "cmd", "'.meta'"),
            (
                r#"<input @keydown.period="x = 1;" />"#,
                "period",
                "$event.key === '.'",
            ),
            (
                r#"<div @[name].outside="x = 1;"></div>"#,
                "outside",
                "this.$el",
            ),
            (
                r#"<c-Card @close.window="x = 1;" />"#,
                "window",
                "window.addEventListener",
            ),
            (
                r#"<div @click.OUTSIDE="x = 1;"></div>"#,
                "OUTSIDE",
                "this.$el contains",
            ),
        ] {
            assert_parse_error(input, &format!("the Alpine modifier '.{modifier}'"));
            assert_parse_error(input, hint);
        }
    }

    #[test]
    fn vue_listener_modifiers_and_citry_event_modifiers_still_parse() {
        for input in [
            r#"<form @submit.prevent.stop="go();"></form>"#,
            r#"<div @click.self.once.capture.passive="go();"></div>"#,
            r#"<input @keyup.enter.exact="go();" @keydown.ctrl.shift.alt.meta.a="go();" />"#,
            r#"<input @keydown.caps-lock.page-down.esc.space.tab.delete="go();" />"#,
            r#"<div @click.left.right.middle="go();"></div>"#,
            r#"<input @c-input.debounce.300ms="search" @c-scroll.throttle.1s="more" />"#,
            r#"<div @[name.window]="go();"></div>"#,
        ] {
            parse_template(input, None, None).unwrap();
        }
    }

    #[test]
    fn once_and_memo_on_an_element_name_the_directive() {
        assert_parse_error(
            r#"<p v-once>hi</p>"#,
            "'v-once' on <p> (line 1, column 4): Citry does not support 'v-once' or 'v-memo' in component templates, on elements or component tags. Remove the directive. To keep an element's contents as the server first rendered them, put '#c-ignore' on the element.",
        );
        assert_parse_error(
            r#"<li v-memo="[a]">x</li>"#,
            "'v-memo' on <li> (line 1, column 5)",
        );
    }
}
