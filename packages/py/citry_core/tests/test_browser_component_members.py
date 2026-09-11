"""Check that component member facts preserve lexical identity and byte ranges."""

from citry_core.template_parser import analyze_component_members


def test_members_keep_context_names_and_exact_utf8_ranges() -> None:
    """Aliases retain their context name while ranges select authored text."""
    source = """
$component(({ data: payload, state }) => {
    payload.name;
    queueMicrotask(() => `${payload?.["žluťoučký"]}`);
    state.count;
    { const payload = {}; payload.unrelated; }
});
"""
    valid, members = analyze_component_members(source)
    assert valid
    encoded = source.encode()
    assert [
        (
            context,
            name,
            encoded[owner_start:owner_end].decode(),
            encoded[member_start:member_end].decode(),
        )
        for context, name, owner_start, owner_end, member_start, member_end in members
    ] == [
        ("data", "name", "payload", "name"),
        ("data", "žluťoučký", "payload", "žluťoučký"),
        ("state", "count", "state", "count"),
    ]


def test_members_omit_rebound_dynamic_and_defaulted_objects() -> None:
    """Uncertain objects and keys must not produce schema diagnostics."""
    source = """
$component(({ data, props = fallback }) => {
    data.before;
    data = other;
    data.after;
    props.defaulted;
});
$component(({ data }) => {
    data[key];
    const unrelated = {};
    unrelated.field;
});
"""
    assert analyze_component_members(source) == (True, [])


def test_invalid_component_members_are_not_partially_returned() -> None:
    """A parse failure cannot prove an earlier member access."""
    assert analyze_component_members("$component(({data}) => { data.name; data. });") == (False, [])
