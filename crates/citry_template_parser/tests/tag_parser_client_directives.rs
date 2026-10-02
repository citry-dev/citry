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
            // Vue reads an uppercase `V-` as a plain attribute, so these
            // would reach the child as Python kwargs without a trace.
            (
                r#"<c-child V-SHOW="open" />"#,
                "'V-SHOW'",
                "'v-' prefix is lowercase",
            ),
            (
                r#"<c-child V-focus />"#,
                "'V-focus'",
                "'v-' prefix is lowercase",
            ),
            (
                r#"<c-child c-V-IF="open" />"#,
                "'c-V-IF'",
                "'v-' prefix is lowercase",
            ),
            (r#"<c-child ^title="x" />"#, "'^title'", "':name="),
            (r#"<c-child c-^title="x" />"#, "'c-^title'", "':name="),
            (
                r#"<c-component is="child" V-SHOW="open" />"#,
                "'V-SHOW'",
                "'v-' prefix is lowercase",
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
            // HTML names are case-insensitive and `^title` sets an attribute
            // in Vue, so neither may become slot data.
            (r#"<c-slot V-IF="open" />"#, "'V-IF'", "<c-if>"),
            (r#"<c-slot ^title="x" />"#, "'^title'", "Vue slot props"),
            (r#"<c-slot c-V-FOR="rows" />"#, "'c-V-FOR'", "<c-for>"),
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
            // Vue's short forms of `.prop` and `.attr` bindings.
            (r#"<p c-title="a" .title="b">x</p>"#, "'.title' on <p>"),
            (r#"<p c-title="a" ^title="b">x</p>"#, "'^title' on <p>"),
            (r#"<p c-class="a" .class="b">x</p>"#, "Remove the modifier"),
            // Vue treats `Class` as a key of its own, which it does not merge.
            (
                r#"<p c-class="a" v-bind:Class="b">x</p>"#,
                "'v-bind:Class' on <p>",
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
            (r#"<p v-bind.prop="o" c-title="t">x</p>"#, "'v-bind.prop' on <p>"),
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
            // Control flow sets no attribute of its own name.
            r#"<label c-for="f in fields" :for="f">x</label>"#,
            r#"<p c-if="ok" :if="x">x</p>"#,
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
            "'@click.outside' (line 1, column 6) uses '.outside', which is not a Vue event modifier. Vue would read '.outside' as a key name, so the listener would never run. Add a 'click' listener to document in mounted(), check whether this.$el contains event.target, and remove the listener in unmounted().",
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
            assert_parse_error(
                input,
                &format!("uses '.{modifier}', which is not a Vue event modifier"),
            );
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
    fn key_names_on_a_non_keyboard_event_are_rejected() {
        assert_parse_error(
            r#"<button @click.enter="go();"></button>"#,
            "'@click.enter' (line 1, column 9) uses '.enter' on the 'click' event. Vue reads a modifier it does not know as a key name, and only keyboard events ('keydown', 'keyup', 'keypress') have a key, so the listener would never run. On other events Vue accepts '.stop', '.prevent', '.self', '.capture', '.once', '.passive', '.ctrl', '.shift', '.alt', '.meta', '.exact', and the mouse buttons '.left', '.right', and '.middle'. To react to a key, listen to 'keydown' or 'keyup' instead.",
        );
        for (input, modifier, event) in [
            (r#"<button @click.foo="go();"></button>"#, "foo", "click"),
            (
                r#"<button v-on:click.prevent.esc="go();"></button>"#,
                "esc",
                "click",
            ),
            (r#"<input @input.trim="go();" />"#, "trim", "input"),
            (
                r#"<form @submit.Prevent="go();"></form>"#,
                "Prevent",
                "submit",
            ),
            (r#"<c-child @select.enter="go();" />"#, "enter", "select"),
        ] {
            assert_parse_error(
                input,
                &format!("uses '.{modifier}' on the '{event}' event."),
            );
        }
    }

    #[test]
    fn key_names_on_keyboard_and_dynamic_events_still_parse() {
        for input in [
            r#"<input @keydown.enter="go();" @keyup.page-down="go();" @keypress.a="go();" />"#,
            r#"<input @KeyDown.my-key="go();" />"#,
            r#"<div @[name].enter="go();"></div>"#,
            r#"<button @click.ctrl.shift.alt.meta.exact.left.right.middle="go();"></button>"#,
            r#"<div @scroll.passive.capture.once.self.stop.prevent="go();"></div>"#,
            r#"<button @c-click.enter="save"></button>"#,
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

    #[test]
    fn vue_builtin_components_are_rejected_in_both_spellings() {
        assert_parse_error(
            r#"<div><Transition><p>x</p></Transition></div>"#,
            "'<Transition>' (line 1, column 7) is Vue's built-in 'Transition' component, which Citry templates do not support. To animate an element, give it a CSS transition or animation and change its class with ':class'.",
        );
        for (input, component) in [
            ("<transition><p>x</p></transition>", "Transition"),
            ("<TransitionGroup></TransitionGroup>", "TransitionGroup"),
            ("<transition-group></transition-group>", "TransitionGroup"),
            ("<KeepAlive></KeepAlive>", "KeepAlive"),
            ("<keep-alive></keep-alive>", "KeepAlive"),
            (r##"<Teleport to="#x"></Teleport>"##, "Teleport"),
            ("<teleport />", "Teleport"),
            ("<Suspense></Suspense>", "Suspense"),
            ("<suspense></suspense>", "Suspense"),
        ] {
            assert_parse_error(
                input,
                &format!("is Vue's built-in '{component}' component, which Citry templates do not support."),
            );
        }
        assert_parse_error(
            "<KeepAlive></KeepAlive>",
            "leave it rendered and hide it with 'v-show'",
        );
        assert_parse_error(
            "<Teleport></Teleport>",
            "use the HTML '<dialog>' element or the 'popover' attribute",
        );
        assert_parse_error(
            "<Suspense></Suspense>",
            "keep a loading flag in the component's data",
        );
    }

    #[test]
    fn names_that_only_resemble_vue_builtin_components_still_parse() {
        for input in [
            "<transition-panel></transition-panel>",
            "<c-Transition />",
            "<my-teleport></my-teleport>",
        ] {
            parse_template(input, None, None).unwrap();
        }
    }
}
