use citry_template_parser::analyze_component_members;

#[test]
fn component_members_resolve_aliases_and_captured_references_with_exact_ranges() {
    let source = r#"
const unrelated = data.outside;
$component(({ data: payload, scope, state, props }) => {
    payload.name;
    payload?.optional;
    payload["display-name"];
    payload?.['žluťoučký'];
    queueMicrotask(() => `${payload.captured}`);
    scope.ready = true;
    state.count++;
    props.label;
    payload.nested.deep;
    { const payload = {}; payload.shadowed; }
    function nested(payload) { return payload.shadowedAgain; }
    payload[key];
    payload["escaped\u0041"];
});
"#;
    let analysis = analyze_component_members(source);
    assert!(analysis.valid);
    let records = analysis
        .members
        .iter()
        .map(|member| {
            assert_eq!(
                &source[member.member_start..member.member_end],
                member.member_name
            );
            (
                member.context_name.as_str(),
                &source[member.owner_start..member.owner_end],
                member.member_name.as_str(),
            )
        })
        .collect::<Vec<_>>();
    assert_eq!(
        records,
        [
            ("data", "payload", "name"),
            ("data", "payload", "optional"),
            ("data", "payload", "display-name"),
            ("data", "payload", "žluťoučký"),
            ("data", "payload", "captured"),
            ("scope", "scope", "ready"),
            ("state", "state", "count"),
            ("props", "props", "label"),
            ("data", "payload", "nested"),
        ]
    );
}

#[test]
fn context_reassignment_anywhere_disqualifies_the_binding() {
    for write in [
        "data = other;",
        "data ||= other;",
        "data++;",
        "({ data } = other);",
        "[data] = other;",
        "for (data of others) {}",
        "queueMicrotask(() => { data = other; });",
    ] {
        let source = format!(
            "$component(({{data, props}}) => {{ data.before; {write} data.after; props.label; }});"
        );
        let analysis = analyze_component_members(&source);
        assert!(analysis.valid, "{write}");
        assert_eq!(analysis.members.len(), 1, "{write}");
        assert_eq!(analysis.members[0].context_name, "props", "{write}");
    }
}

#[test]
fn only_static_runtime_initializers_and_direct_context_bindings_are_proven() {
    let source = r#"
$component({ init({ data: payload }) { payload.actual; } });
$component(function ({ state: localState }) { localState.actual; });
$component({ [init]({ data }) { data.dynamicInit; } });
$component(({ [data]: payload }) => { payload.dynamicContext; });
$component(({ data = fallback }) => { data.defaulted; });
$component(({ unknown }) => { unknown.member; });
$component(({ data }) => { function inner(data) { data = {}; data.shadowed; } data.actual; });
function custom($component) { $component(({data}) => { data.fake; }); }
"#;
    let analysis = analyze_component_members(source);
    assert!(analysis.valid);
    assert_eq!(
        analysis
            .members
            .iter()
            .map(|member| member.member_name.as_str())
            .collect::<Vec<_>>(),
        ["actual", "actual", "actual"]
    );
}

#[test]
fn invalid_syntax_discards_all_member_facts() {
    let analysis = analyze_component_members("$component(({data}) => { data.name; data. });");
    assert!(!analysis.valid);
    assert!(analysis.members.is_empty());
}

#[test]
fn overridden_or_dynamically_selected_initializers_do_not_prove_members() {
    for source in [
        "$component({ init({data}) { data.dead; }, init({data}) { data.live; } });",
        "$component({ init({data}) { data.dead; }, ...other });",
        "$component({ ...other, init({data}) { data.live; } });",
        "$component({ init({data}) { data.dead; }, [key]: other });",
        "$component({ get init() { return ({data}) => data.dead; } });",
    ] {
        let analysis = analyze_component_members(source);
        assert!(analysis.valid, "{source}");
        assert!(analysis.members.is_empty(), "{source}");
    }
}
