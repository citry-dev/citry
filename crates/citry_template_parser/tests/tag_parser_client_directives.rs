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
    fn slot_tags_reject_every_vue_directive_but_a_slot_prop_with_a_fix() {
        // A `<c-slot>` attribute other than a static `:name` slot prop is
        // Python slot data, so no other Vue form has a meaning there.
        let cases = [
            (r#"<c-slot v-if="open" />"#, "'v-if'", "<c-if>"),
            (r#"<c-slot name="body" v-else />"#, "'v-else'", "<c-if>"),
            (r#"<c-slot v-for="row in rows" />"#, "'v-for'", "<c-for>"),
            (
                r#"<c-slot v-show="open" />"#,
                "'v-show'",
                "carries 'v-show'",
            ),
            (r#"<c-slot v-bind="props" />"#, "'v-bind'", "fixed name"),
            (r#"<c-slot :[key]="row" />"#, "':[key]'", "fixed name"),
            (
                r#"<c-slot :item.prop="row" />"#,
                "':item.prop'",
                "no modifiers",
            ),
            (r#"<c-slot c-:item="row" />"#, "'c-:item'", "fixed name"),
            (
                r#"<c-slot V-BIND:item="row" />"#,
                "'V-BIND:item'",
                "fixed name",
            ),
            (r#"<c-slot @click="go()" />"#, "'@click'", "inside the fill"),
            (r#"<c-slot .value="text" />"#, "'.value'", "fixed name"),
            (r##"<c-slot #header />"##, "'#header'", "Name the slot with"),
            (r#"<c-slot v-focus />"#, "'v-focus'", "fallback content"),
            (r#"<c-slot c-v-if="open" />"#, "'c-v-if'", "<c-if>"),
            // HTML names are case-insensitive and `^title` sets an attribute
            // in Vue, so neither may become slot data.
            (r#"<c-slot V-IF="open" />"#, "'V-IF'", "<c-if>"),
            (r#"<c-slot ^title="x" />"#, "'^title'", "fixed name"),
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
        // Plain and `c-` attributes stay slot data, beside Vue slot props.
        parse_template(
            r#"<c-slot name="row" item="x" c-count="n" :row="row" v-bind:row-index="i" required />"#,
            None,
            None,
        )
        .unwrap();
    }

    #[test]
    fn slot_props_reject_names_and_values_the_fill_could_not_read() {
        let cases = [
            (
                r#"<c-slot :name="n" />"#,
                "Vue reads ':name' on a slot as the slot's own name",
            ),
            (r#"<c-slot :key="k" />"#, "Citry sets the slot's own 'key'"),
            (
                r#"<c-slot :$i18n="x" />"#,
                "reserved for the props Citry passes to every fill",
            ),
            (
                r#"<c-slot :_row="x" />"#,
                "reserved for the props Citry passes to every fill",
            ),
            (
                r#"<c-slot :citry-props="x" />"#,
                "reserved for the props Citry passes to every fill",
            ),
            (r#"<c-slot :row />"#, "needs a Vue expression"),
            (r#"<c-slot :row="  " />"#, "needs a Vue expression"),
            (
                r#"<c-slot :row-data="a" :rowData="b" />"#,
                "pass the same slot prop 'rowData'",
            ),
            (
                r#"<c-slot :row="a" c-row="b" />"#,
                "both pass 'row' to the fill, once as Vue data and once as Python slot data",
            ),
            (
                r#"<c-slot row-data="a" :rowData="b" />"#,
                "both pass 'rowData' to the fill",
            ),
            // `bind="1"` is ordinary Python slot data; only `c-bind` spreads.
            (
                r#"<c-slot :bind="x" bind="1" />"#,
                "both pass 'bind' to the fill",
            ),
            (
                r#"<c-slot :c-value="x" />"#,
                "names that start with 'c-' are Citry attributes",
            ),
            (r#"<c-slot :row="{{ x }}" />"#, "holds '{{'"),
            (
                r#"<c-slot c-:row="x" />"#,
                "A 'c-' attribute takes a Python value",
            ),
        ];
        for (source, expected) in cases {
            let message = format!("{}", parse_template(source, None, None).unwrap_err());
            assert!(message.contains(expected), "{source}: {message}");
        }
    }

    #[test]
    fn fill_tags_accept_one_slot_props_pattern() {
        for source in [
            r#"<c-child><c-fill name="row" v-slot="{ row }">x</c-fill></c-child>"#,
            r#"<c-child><c-fill name="row" v-slot="{ row: item, index = 0, ...rest }">x</c-fill></c-child>"#,
            r#"<c-child><c-fill name="row" v-slot="props" data="{ label }">x</c-fill></c-child>"#,
            // A trailing comma inside the braces and a literal default merge safely.
            r#"<c-child><c-fill name="row" v-slot="{ row, }">x</c-fill></c-child>"#,
            r#"<c-child><c-fill name="row" v-slot="{ row = null, label = 'x' }">x</c-fill></c-child>"#,
            r#"<c-child><c-fill name="row" v-slot="{ n = -1, v = void 0, list = [1, 'a'], o = { a: `t` } }">x</c-fill></c-child>"#,
            "<c-child><c-fill name=\"row\" v-slot=\"{\n  row,\n  index\n}\">x</c-fill></c-child>",
        ] {
            parse_template(source, None, None).unwrap_or_else(|error| panic!("{source}: {error}"));
        }
    }

    #[test]
    fn fill_tags_reject_slot_props_they_could_not_merge_or_name() {
        let wrap = |fill: &str| format!("<c-child>{fill}</c-child>");
        let cases = [
            (r#"<c-fill name="row" v-slot>x</c-fill>"#, "needs a pattern"),
            (
                r#"<c-fill name="row" v-slot="">x</c-fill>"#,
                "needs a pattern",
            ),
            (
                r#"<c-fill name="row" v-slot="a, b">x</c-fill>"#,
                "lists several parameters",
            ),
            (
                r#"<c-fill name="row" v-slot="[a]">x</c-fill>"#,
                "is an array pattern",
            ),
            (
                r#"<c-fill name="row" v-slot="...p">x</c-fill>"#,
                "starts with '...'",
            ),
            (
                r#"<c-fill name="row" v-slot="p = {}">x</c-fill>"#,
                "has a default value",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row ">x</c-fill>"#,
                "is not a valid JavaScript parameter",
            ),
            (
                r#"<c-fill name="row" v-slot="a) => (b">x</c-fill>"#,
                "is not a valid JavaScript parameter",
            ),
            (
                r#"<c-fill name="row" v-slot="{ $i18n }">x</c-fill>"#,
                "uses a reserved name",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row: citryRow }">x</c-fill>"#,
                "uses a reserved name",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row }" data="{ row }">x</c-fill>"#,
                "'row' is named by both 'v-slot' and the Python 'data' or 'fallback'",
            ),
            (
                r#"<c-fill name="row" v-slot="{ fb }" fallback="fb">x</c-fill>"#,
                "'fb' is named by both 'v-slot'",
            ),
            (
                r##"<c-fill name="row" #row="{ row }">x</c-fill>"##,
                "Choose the slot with 'name=",
            ),
            (
                r#"<c-fill name="row" v-slot:row="{ row }">x</c-fill>"#,
                "Choose the slot with 'name=",
            ),
            (
                r#"<c-fill name="row" V-SLOT="{ row }">x</c-fill>"#,
                "written in lowercase",
            ),
            (
                r#"<c-fill name="row" c-v-slot="p">x</c-fill>"#,
                "A 'c-' attribute takes a Python value",
            ),
            (
                r#"<c-fill name="row" v-slot.mod="p">x</c-fill>"#,
                "without an argument or modifier",
            ),
            // Citry writes the pattern into a larger parameter, where any of
            // these would change what the rest of it means.
            (
                r#"<c-fill name="row" v-slot="{ row },">x</c-fill>"#,
                "has text around its one parameter",
            ),
            (
                r#"<c-fill name="row" v-slot="p,">x</c-fill>"#,
                "has text around its one parameter",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row } /* c */">x</c-fill>"#,
                "holds a comment",
            ),
            (
                "<c-fill name=\"row\" v-slot=\"p // the props\n\">x</c-fill>",
                "holds a comment",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row = &quot;x&quot; }">x</c-fill>"#,
                "holds an '&' character",
            ),
            // Vue's compiler would read these names from the wrong scope.
            (
                r#"<c-fill name="row" v-slot="{ [k]: row }">x</c-fill>"#,
                "has a computed key",
            ),
            (
                r#"<c-fill name="row" v-slot="{ ['k' + 'ey']: k }">x</c-fill>"#,
                "has a computed key",
            ),
            (
                r#"<c-fill name="row" v-slot="{ cell, id = row.id }">x</c-fill>"#,
                "has a default value that is not a literal",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row = function f() { return f } }">x</c-fill>"#,
                "has a default value that is not a literal",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row: { cell = make() } }">x</c-fill>"#,
                "has a default value that is not a literal",
            ),
            (
                r#"<c-fill name="row" v-slot="{ row = '{{' }">x</c-fill>"#,
                "holds '{{'",
            ),
            (
                r#"<c-fill name="row" v-slot="{ key }">x</c-fill>"#,
                "reads 'key', which is not a slot prop",
            ),
            (
                r#"<c-fill name="row" :title="t">x</c-fill>"#,
                "inside the fill",
            ),
            (
                r#"<c-fill name="row" v-if="ok">x</c-fill>"#,
                "inside the fill",
            ),
        ];
        for (fill, expected) in cases {
            let source = wrap(fill);
            let message = format!("{}", parse_template(&source, None, None).unwrap_err());
            assert!(message.contains(expected), "{source}: {message}");
        }
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
        // `.away` is Alpine's name for what Citry spells `.outside`, so the
        // hint points at Citry's modifier.
        assert_parse_error(
            r#"<div @click.away="open = false;">x</div>"#,
            "'@click.away' (line 1, column 6) uses '.away', which is not a Vue event modifier. Vue would read '.away' as a key name, so the listener would not do what '.away' asks. Use Citry's '.outside' modifier instead.",
        );
        for (input, modifier, hint) in [
            (
                r#"<div @click.AWAY="x = 1;"></div>"#,
                "AWAY",
                "Use Citry's '.outside' modifier instead.",
            ),
            (
                r#"<div @[name].away="x = 1;"></div>"#,
                "away",
                "Use Citry's '.outside' modifier instead.",
            ),
            (
                r#"<c-Card @close.away="x = 1;" />"#,
                "away",
                "Use Citry's '.outside' modifier instead.",
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
                r#"<input @keydown.super.enter="x = 1;" />"#,
                "super",
                "'.meta'",
            ),
            (
                r#"<input @keydown.period="x = 1;" />"#,
                "period",
                "$event.key === '.'",
            ),
            // Alpine's names for these keys match no key in Vue, so the
            // listener would load and never run.
            (
                r#"<input @keydown.minus="x = 1;" />"#,
                "minus",
                "$event.key === '.'",
            ),
            (
                r#"<input @keydown.underscore="x = 1;" />"#,
                "underscore",
                "$event.key === '.'",
            ),
            (
                r#"<input @keydown.spacebar="x = 1;" />"#,
                "spacebar",
                "'.space'",
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
    fn citry_listener_modifiers_parse_alone_and_with_vue_modifiers() {
        for input in [
            // Each modifier alone, in both spellings of a listener.
            r#"<div @click.outside="open = false;"></div>"#,
            r#"<div v-on:click.outside="open = false;"></div>"#,
            r#"<div @resize.window="go();"></div>"#,
            r#"<div v-on:keyup.document="go();"></div>"#,
            r#"<input @input.debounce="go();" />"#,
            r#"<input @input.throttle="go();" />"#,
            // A time after `.debounce` or `.throttle`, in ms and in s, up to
            // the largest integer JavaScript holds exactly.
            r#"<input @input.debounce.300ms="go();" />"#,
            r#"<input @scroll.throttle.2s="go();" />"#,
            r#"<input @input.debounce.0ms="go();" />"#,
            r#"<input @input.debounce.9007199254740991ms="go();" />"#,
            r#"<input @input.debounce.9007199254740s="go();" />"#,
            // With Vue's own modifiers.
            r#"<div @click.outside.stop.prevent="go();"></div>"#,
            r#"<div @click.stop.prevent.window="go();"></div>"#,
            r#"<div @keydown.escape.window="go();"></div>"#,
            r#"<div @keydown.enter.exact.outside="go();"></div>"#,
            r#"<div @keyup.ctrl.shift.a.document="go();"></div>"#,
            r#"<div @click.right.document.throttle="go();"></div>"#,
            r#"<div @click.capture.window="go();"></div>"#,
            r#"<div @click.passive.window="go();"></div>"#,
            // `.once` with a timing modifier or a non-outside place.
            r#"<input @input.once.debounce.300ms="go();" />"#,
            r#"<input @input.debounce.300ms.once="go();" />"#,
            r#"<div @click.once.window="go();"></div>"#,
            // `.self` has a meaning for `.window` and `.document`: the event
            // target is the window or document itself.
            r#"<div @selectionchange.self.document="go();"></div>"#,
            r#"<div @click.self.window="go();"></div>"#,
            // Both timing modifiers, each with its own time, and both
            // together with a place.
            r#"<input @input.debounce.1s.throttle.2s="go();" />"#,
            r#"<input @input.throttle.debounce.1s="go();" />"#,
            r#"<div @keydown.escape.window.debounce.300ms.stop.prevent="go();"></div>"#,
        ] {
            parse_template(input, None, None).unwrap_or_else(|error| {
                panic!("expected {input} to parse, got: {error}");
            });
        }
    }

    #[test]
    fn citry_listener_modifiers_parse_on_dynamic_elements() {
        // `<c-element>` writes a plain HTML element, so it is not a
        // component tag here.
        for input in [
            r#"<c-element is="div" @click.outside="go();" />"#,
            r#"<c-element is="div" @keydown.escape.window="go();"></c-element>"#,
            r#"<c-element is="input" @input.debounce.300ms="go();" />"#,
            r#"<c-element is="div" @scroll.throttle.1s.document="go();" />"#,
        ] {
            parse_template(input, None, None).unwrap_or_else(|error| {
                panic!("expected {input} to parse, got: {error}");
            });
        }
        // The rules about combinations still apply to it.
        assert_parse_error(
            r#"<c-element is="div" @click.outside.once="go();" />"#,
            "'@click.outside.once' on <c-element> (line 1, column 21) combines '.outside' with '.once'",
        );
    }

    #[test]
    fn citry_listener_modifiers_are_rejected_off_html_elements() {
        // On a component tag the listener receives emitted values, not DOM
        // events, so a window, document, outside, or timed listener has no
        // meaning there. The same holds for the Vue built-ins that write no
        // element of their own.
        let message = "uses a Citry listener modifier, which works only on HTML elements. Put the listener on an element inside the component, or handle the timing in the method.";
        for (input, tag) in [
            (r#"<c-Card @close.window="x = 1;" />"#, "c-Card"),
            (r#"<c-card @close.outside="x = 1;"></c-card>"#, "c-card"),
            (r#"<c-card v-on:close.document="x = 1;" />"#, "c-card"),
            (r#"<c-card @close.debounce="x = 1;" />"#, "c-card"),
            (r#"<c-card @close.throttle.1s="x = 1;" />"#, "c-card"),
            // A Vue modifier next to the Citry one does not change that.
            (r#"<c-card @close.stop.window="x = 1;" />"#, "c-card"),
            (
                r#"<template @click.outside="x = 1;"></template>"#,
                "template",
            ),
            (r#"<slot @click.throttle="x = 1;"></slot>"#, "slot"),
            (
                r#"<component @click.document="x = 1;"></component>"#,
                "component",
            ),
            // `<c-element>` counts as the tag its static `is` names.
            (
                r#"<c-element is="component" @click.outside="x = 1;" />"#,
                "c-element",
            ),
            (
                r#"<c-element is="MyThing" @click.outside="x = 1;" />"#,
                "c-element",
            ),
        ] {
            assert_parse_error(input, &format!("on <{tag}> (line 1, column"));
            assert_parse_error(input, message);
        }
        assert_parse_error(
            r#"<c-Card @close.window="x = 1;" />"#,
            "'@close.window' on <c-Card> (line 1, column 9) uses a Citry listener modifier",
        );
        // A component tag still takes the listeners it took before.
        for input in [
            r#"<c-card @close="x = 1;" />"#,
            r#"<c-card @close.once="x = 1;" />"#,
            r#"<template @click.stop="x = 1;"></template>"#,
        ] {
            parse_template(input, None, None).unwrap();
        }
    }

    #[test]
    fn conflicting_citry_listener_modifiers_are_rejected_with_their_reason() {
        for (input, message) in [
            // Two places to listen.
            (
                r#"<div @click.outside.window="x = 1;"></div>"#,
                "'@click.outside.window' on <div> (line 1, column 6) combines '.outside' and '.window'. A listener listens in one place: the element, the window or the document.",
            ),
            (
                r#"<div @click.window.document="x = 1;"></div>"#,
                "combines '.window' and '.document'. A listener listens in one place",
            ),
            (
                r#"<div @click.document.outside="x = 1;"></div>"#,
                "combines '.outside' and '.document'. A listener listens in one place",
            ),
            // Rules about the event itself.
            (
                r#"<div @click.outside.self="x = 1;"></div>"#,
                "combines '.outside' with '.self': the element can never be the target of an event that starts outside it.",
            ),
            (
                r#"<div @click.capture.outside="x = 1;"></div>"#,
                "combines '.outside' with '.capture': '.outside' listens on the document after the event's own handlers have run, and the capture phase would run it first.",
            ),
            (
                r#"<div @click.outside.once="x = 1;"></div>"#,
                "combines '.outside' with '.once': '.once' removes the listener after its first event, and a document listener sees every click, so a click inside the element would use it up.",
            ),
            (
                r#"<div @click.passive.prevent.window="x = 1;"></div>"#,
                "combines '.passive' with '.prevent'. A passive listener cannot cancel the event.",
            ),
            (
                r#"<input @input.prevent.debounce.passive="x = 1;" />"#,
                "combines '.passive' with '.prevent'.",
            ),
            // Counts and order.
            (
                r#"<input @input.debounce.100ms.debounce.200ms="x = 1;" />"#,
                "'@input.debounce.100ms.debounce.200ms' on <input> (line 1, column 8) repeats '.debounce'. Give each modifier once.",
            ),
            (
                r#"<input @input.throttle.throttle="x = 1;" />"#,
                "repeats '.throttle'. Give each modifier once.",
            ),
            (
                r#"<div @click.window.stop.window="x = 1;"></div>"#,
                "repeats '.window'. Give each modifier once.",
            ),
            (
                r#"<div @click.stop.outside.stop="x = 1;"></div>"#,
                "repeats '.stop'. Give each modifier once.",
            ),
            (
                r#"<input @input.300ms.window="x = 1;" />"#,
                "'@input.300ms.window' on <input> (line 1, column 8) has the time '.300ms' without '.debounce' or '.throttle' right before it.",
            ),
            (
                r#"<input @input.window.300ms="x = 1;" />"#,
                "has the time '.300ms' without '.debounce' or '.throttle' right before it.",
            ),
            // A time belongs to one timing modifier only.
            (
                r#"<input @input.debounce.1s.1s="x = 1;" />"#,
                "has the time '.1s' without '.debounce' or '.throttle' right before it.",
            ),
            (
                r#"<div @click.debounce.1.5s="x = 1;"></div>"#,
                "gives '.1' as a time. Write the time in milliseconds or seconds, such as '.300ms' or '.2s'. To name a key, put it before '.debounce'.",
            ),
            (
                r#"<div @keydown.debounce.1m="x = 1;"></div>"#,
                "gives '.1m' as a time. Write the time in milliseconds or seconds, such as '.300ms' or '.2s'. To name a key, put it before '.debounce'.",
            ),
            (
                r#"<div @click.throttle.200="x = 1;"></div>"#,
                "gives '.200' as a time. Write the time in milliseconds or seconds, such as '.300ms' or '.2s'. To name a key, put it before '.throttle'.",
            ),
            (
                r#"<input @keydown.window.300ms="x = 1;" />"#,
                "has the time '.300ms' without '.debounce' or '.throttle' right before it.",
            ),
            // A time past the largest integer JavaScript holds exactly.
            (
                r#"<input @input.debounce.9007199254740992ms="x = 1;" />"#,
                "gives '.9007199254740992ms', which is longer than JavaScript can hold exactly.",
            ),
            (
                r#"<input @input.throttle.9007199254741s="x = 1;" />"#,
                "gives '.9007199254741s', which is longer than JavaScript can hold exactly.",
            ),
            // Too many digits for any integer type.
            (
                r#"<input @input.debounce.99999999999999999999999999999999999999999999999999ms="x = 1;" />"#,
                "which is longer than JavaScript can hold exactly.",
            ),
        ] {
            assert_parse_error(input, message);
        }
    }

    #[test]
    fn citry_listener_modifiers_must_be_lowercase() {
        for (input, written, lowercase) in [
            (
                r#"<div @click.Outside="x = 1;"></div>"#,
                "Outside",
                "outside",
            ),
            (
                r#"<div @click.OUTSIDE="x = 1;"></div>"#,
                "OUTSIDE",
                "outside",
            ),
            (r#"<div @resize.WINDOW="x = 1;"></div>"#, "WINDOW", "window"),
            (
                r#"<div @click.Document="x = 1;"></div>"#,
                "Document",
                "document",
            ),
            (
                r#"<input @input.Debounce.1s="x = 1;" />"#,
                "Debounce",
                "debounce",
            ),
            (
                r#"<input @input.THROTTLE="x = 1;" />"#,
                "THROTTLE",
                "throttle",
            ),
            (r#"<div @[name].Window="x = 1;"></div>"#, "Window", "window"),
        ] {
            assert_parse_error(
                input,
                &format!("uses '.{written}'. Write it in lowercase, '.{lowercase}'."),
            );
        }
        assert_parse_error(
            r#"<div @click.Outside="x = 1;"></div>"#,
            "'@click.Outside' (line 1, column 6) uses '.Outside'. Write it in lowercase, '.outside'.",
        );
    }

    #[test]
    fn citry_listener_modifiers_need_the_event_name_written_out() {
        // A name in brackets comes from a value at run time, which would let
        // data decide what a window or document listener hears.
        let message = "gives the event name in brackets. Citry's listener modifiers need the event name written out, as in '@click.outside'.";
        for input in [
            r#"<div @[name].window="go();"></div>"#,
            r#"<div @[name].outside.stop="go();"></div>"#,
            r#"<div v-on:[name].debounce.1s="go();"></div>"#,
        ] {
            assert_parse_error(input, message);
        }
    }

    #[test]
    fn citry_listener_modifiers_are_rejected_on_capitalized_tags() {
        // Vue reads a tag that starts with a capital letter as a component,
        // `<Div>` included.
        let message = "on a tag that starts with a capital letter, which Vue reads as a component";
        for input in [
            r#"<MyThing @click.outside="x = 1;"></MyThing>"#,
            r#"<Card v-on:close.window="x = 1;" />"#,
            r#"<Div @click.outside="x = 1;"></Div>"#,
        ] {
            assert_parse_error(input, message);
        }
    }

    #[test]
    fn names_the_compiler_writes_for_a_rewritten_listener_are_reserved() {
        // Vue's `camelize` turns `-0` into `0`, so these all give the props
        // key `onCitryOn0`, which the compiler writes for a listener.
        let message =
            "uses a name Citry's compiler writes for itself. Rename the attribute or event.";
        for (input, name, tag) in [
            (r#"<div @citry-on-0="go();"></div>"#, "@citry-on-0", "div"),
            (r#"<div @citry-on0="go();"></div>"#, "@citry-on0", "div"),
            (
                r#"<div v-on:citry-on-0="go();"></div>"#,
                "v-on:citry-on-0",
                "div",
            ),
            (r#"<div :onCitryOn0="go();"></div>"#, ":onCitryOn0", "div"),
            (
                r#"<div v-bind:onCitryOn0="go();"></div>"#,
                "v-bind:onCitryOn0",
                "div",
            ),
            (r#"<div onCitryOn0="go();"></div>"#, "onCitryOn0", "div"),
            // `.camel` makes Vue camelize the bound name.
            (
                r#"<div :on-citry-on-0.camel="go"></div>"#,
                ":on-citry-on-0.camel",
                "div",
            ),
            // More digits, a Vue modifier, and a component tag.
            (r#"<div @citry-on-12="go();"></div>"#, "@citry-on-12", "div"),
            (
                r#"<div @citry-on-12.stop="go();"></div>"#,
                "@citry-on-12.stop",
                "div",
            ),
            (
                r#"<div v-bind:onCitryOn12.prop="go();"></div>"#,
                "v-bind:onCitryOn12.prop",
                "div",
            ),
            (r#"<c-card @citry-on-0="go();" />"#, "@citry-on-0", "c-card"),
            // An Events binding `@c-<event>` becomes a listener for `<event>`.
            (
                r#"<div @c-citry-on-0="save"></div>"#,
                "@c-citry-on-0",
                "div",
            ),
            (r#"<div @c-citryOn0="save"></div>"#, "@c-citryOn0", "div"),
            (
                r#"<div @c-citry-on-0.prevent="save"></div>"#,
                "@c-citry-on-0.prevent",
                "div",
            ),
            (
                r#"<c-element is="div" @citry-on-0="go();" />"#,
                "@citry-on-0",
                "c-element",
            ),
            // The reserved name still counts when a Citry modifier follows.
            (
                r#"<div @citry-on-0.outside="go();"></div>"#,
                "@citry-on-0.outside",
                "div",
            ),
        ] {
            assert_parse_error(input, &format!("'{name}' on <{tag}> (line 1, column"));
            assert_parse_error(input, message);
        }
        // The key is `onCitryOnline`, not `onCitryOn` plus digits.
        for input in [
            r#"<div @citry-online="go();"></div>"#,
            r#"<div @citry-on="go();"></div>"#,
            r#"<div @citry-on-x="go();"></div>"#,
            r#"<div :onCitryOnline="go();"></div>"#,
            // A dynamic name is known only in the browser.
            r#"<div @[citry-on-0]="go();"></div>"#,
        ] {
            parse_template(input, None, None).unwrap_or_else(|error| {
                panic!("expected {input} to parse, got: {error}");
            });
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
            "'@click.enter' (line 1, column 9) uses '.enter' on the 'click' event. Vue reads a modifier it does not know as a key name, and only keyboard events ('keydown', 'keyup', 'keypress') have a key, so Vue would ignore '.enter' and run the listener on every 'click' event. On other events Vue accepts '.stop', '.prevent', '.self', '.capture', '.once', '.passive', '.ctrl', '.shift', '.alt', '.meta', '.exact', and the mouse buttons '.left', '.right', and '.middle'. Remove '.enter', or listen to 'keydown' or 'keyup' to react to a key.",
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
            // Citry's Vue compiler listens for `KeyDown` as written, which
            // the browser never sends, so it is not a keyboard event.
            (r#"<input @KeyDown.enter="go();" />"#, "enter", "KeyDown"),
        ] {
            assert_parse_error(
                input,
                &format!("uses '.{modifier}' on the '{event}' event."),
            );
        }
    }

    #[test]
    fn model_and_native_modifiers_on_a_listener_name_their_own_fix() {
        assert_parse_error(
            r#"<input @input.trim="go();" />"#,
            "'.trim' is a 'v-model' modifier. Put it on 'v-model', or remove it from the listener.",
        );
        assert_parse_error(
            r#"<c-child @click.native="go();" />"#,
            "Vue 3 has no '.native' modifier",
        );
    }

    #[test]
    fn key_names_on_keyboard_and_dynamic_events_still_parse() {
        for input in [
            r#"<input @keydown.enter="go();" @keyup.page-down="go();" @keypress.a="go();" />"#,
            r#"<div @[name].enter="go();"></div>"#,
            r#"<button @click.ctrl.shift.alt.meta.exact.left.right.middle="go();"></button>"#,
            r#"<div @scroll.passive.capture.once.self.stop.prevent="go();"></div>"#,
            r#"<button @c-click.enter="save"></button>"#,
        ] {
            parse_template(input, None, None).unwrap();
        }
    }

    #[test]
    fn element_directives_in_the_wrong_case_are_rejected() {
        assert_parse_error(
            r#"<div V-IF="open">x</div>"#,
            "'V-IF' on <div> (line 1, column 6) is not a Vue directive, because Vue reads a directive only when its 'v-' prefix is lowercase. Vue would write it as a plain attribute. Write 'v-if'.",
        );
        assert_parse_error(r#"<div V-focus:x.y="a">x</div>"#, "Write 'v-focus:x.y'.");
        assert_parse_error(
            r#"<div v-If="open">x</div>"#,
            "'v-If' on <div> (line 1, column 6) uses a Vue directive name in the wrong case. Vue's own directives are lowercase, and Vue would look up 'v-If' as a custom directive named 'If'. Write 'v-if'.",
        );
        assert_parse_error(r#"<input v-MODEL.trim="q" />"#, "Write 'v-model.trim'.");
    }

    #[test]
    fn element_directives_with_reserved_names_are_rejected() {
        for input in [
            r#"<div v-citry-control="a">x</div>"#,
            // The directive the Vue compiler writes for a listener with a
            // Citry modifier.
            r#"<div v-citry-on:click="go();">x</div>"#,
            r#"<div v-c-tr="a">x</div>"#,
            r#"<c-element c-is="tag" v-Citry-x="a">x</c-element>"#,
        ] {
            assert_parse_error(
                input,
                "uses a name Citry reserves: 'v-c-*' and 'v-citry-*' belong to Citry's own browser runtime. Give the directive another name.",
            );
        }
    }

    #[test]
    fn element_directives_without_an_expression_are_rejected() {
        assert_parse_error(
            r#"<div v-show>x</div>"#,
            "'v-show' on <div> (line 1, column 6) needs a Vue expression, for example 'v-show=\"open\"'.",
        );
        for (input, example) in [
            (r#"<div v-show="  ">x</div>"#, r#"v-show="open""#),
            (r#"<div v-if>x</div>"#, r#"v-if="open""#),
            (
                r#"<div v-if="a">x</div><div v-else-if>y</div>"#,
                r#"v-else-if="open""#,
            ),
            (r#"<li v-for>x</li>"#, r#"v-for="item in items""#),
            (r#"<input v-model.lazy />"#, r#"v-model.lazy="query""#),
            (r#"<div v-html></div>"#, r#"v-html="html""#),
            (r#"<p v-text=""></p>"#, r#"v-text="label""#),
        ] {
            assert_parse_error(
                input,
                &format!("needs a Vue expression, for example '{example}'."),
            );
        }
        assert_parse_error(
            r#"<div v-show.lazy="open">x</div>"#,
            "'v-show.lazy' on <div> (line 1, column 6) takes no argument or modifiers.",
        );
    }

    #[test]
    fn element_model_argument_and_v_is_are_rejected() {
        assert_parse_error(
            r#"<input v-model:title="q" />"#,
            "'v-model:title' on <input> (line 1, column 8) names an argument, which only a component tag's 'v-model' takes.",
        );
        assert_parse_error(
            r#"<div v-is="'x'"></div>"#,
            "'v-is' on <div> (line 1, column 6) is not supported: Vue 3 reads 'v-is' only in its compatibility build.",
        );
    }

    #[test]
    fn element_directives_spelled_as_vue_reads_them_still_parse() {
        for input in [
            r#"<div v-show="open" v-Tooltip="tip" v-my-dir:Arg.Mod="x">x</div>"#,
            r#"<template v-if="a"><p>x</p></template><p v-else>y</p>"#,
            r#"<li v-for="item in items" :key="item">x</li>"#,
            r#"<p v-html="html" v-text="text"></p>"#,
            r#"<div data-V-flag="x">x</div>"#,
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
