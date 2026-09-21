"""
Tests for Events binding capture, validation, and typed prepared metadata.

Binding assertions inspect the prepared owner tables rather than serialized
DOM marker attributes. Error assertions check message content, not just the
exception type.
"""

import re

import pytest

from citry import Citry, Component, InMemoryCache
from citry._vue.capture import render_prepared
from citry._vue.direct_capture import assemble_typed_render
from citry.client_directives import (
    RuntimeComponentEventBinding,
    is_authenticated_runtime_component_event_binding,
)

_CID_RE = re.compile(r' data-cid(?:-\w+)?="[^"]*"')

# A State-declaring component mints its state token at render, which needs a
# signing secret on the Citry instance.
SIGNING_KEY = "test-secret-key"


def _events_ext(app):
    return app.extensions.get_extension("events")


def _rendered(component):
    """Render to HTML with the per-render cid markers (the per-instance and the fixed-name form) stripped."""
    return _CID_RE.sub("", component.render().serialize())


def _compiled_html(comp_cls):
    """Trigger first template compilation and return its rendered HTML."""
    return _rendered(comp_cls())


def _noop(self):
    """A handler stub: a binding only needs its handler to exist, not to do anything."""
    return


def _typed_binding_tables(comp_cls):
    """Return the actual prepared owner and its typed binding tables."""
    assembly = assemble_typed_render(
        render_prepared(comp_cls()),
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )
    owner = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    assert owner.type_key == comp_cls.class_id
    tables = {}
    for name in ("eventBindings", "pollBindings", "controlBindings"):
        records = owner.prepared_data.get(name, {})
        assert all(key == spec["id"] for key, spec in records.items())
        tables[name] = list(records.values())
    return owner, tables, assembly.compile_inputs[owner.definition_id]


class TestStageOneEveryForm:
    """Observe-then-lock the rewritten template for a template using every vocabulary form."""

    def _counter(self):
        app = Citry(secret=SIGNING_KEY)

        class RateIn:
            stars: int = 0

        class Counter(Component):
            citry = app

            class State:
                count: int = 0
                name: str = ""

            class Events:
                def save(self, state):
                    return None

                def rate(self, data: RateIn):
                    return None

                def refresh(self, state):
                    return None

            template = (
                "<div>"
                '<button @c-click="save">Save</button>'
                '<button @c-click.prevent.stop="rate({stars: 5})">Rate</button>'
                '<input :c-count.debounce.300ms="refresh">'
                # A state binding needs a control to bind, so the one-way form
                # rides an <input> too.
                "<input :c-name>"
                '<div @c-poll.30s="refresh">poll</div>'
                '<button @click="$state.count++" :class="{a: true}">plain</button>'
                "</div>"
            )

        return Counter

    def test_locked_specs(self):
        counter = self._counter()
        owner, tables, _ = _typed_binding_tables(counter)
        assert owner.type_key == counter.class_id
        ids_by_channel = {name: [spec["id"] for spec in specs] for name, specs in tables.items()}
        assert all(type(binding_id) is str and binding_id for ids in ids_by_channel.values() for binding_id in ids)
        assert all(len(ids) == len(set(ids)) for ids in ids_by_channel.values())
        semantics = {
            name: [{key: value for key, value in spec.items() if key != "id"} for spec in specs]
            for name, specs in tables.items()
        }
        assert semantics == {
            "eventBindings": [
                {
                    "event": "click",
                    "handler": "save",
                    "args": None,
                    "prevent": False,
                    "stop": False,
                    "self": False,
                    "once": False,
                    "key": None,
                    "debounce": None,
                    "throttle": None,
                },
                {
                    "event": "click",
                    "handler": "rate",
                    "args": "{stars: 5}",
                    "prevent": True,
                    "stop": True,
                    "self": False,
                    "once": False,
                    "key": None,
                    "debounce": None,
                    "throttle": None,
                },
            ],
            "controlBindings": [
                {
                    "field": "count",
                    "binding_mode": "two-way",
                    "handler": "refresh",
                    "lazy": False,
                    "on": None,
                    "key": None,
                    "debounce": 300,
                    "throttle": None,
                },
                {
                    "field": "name",
                    "binding_mode": "one-way",
                    "handler": None,
                    "lazy": False,
                    "on": None,
                    "key": None,
                    "debounce": None,
                    "throttle": None,
                },
            ],
            "pollBindings": [
                {
                    "handler": "refresh",
                    "args": None,
                    "interval": 30000,
                }
            ],
        }

    def test_authored_vue_attributes_survive_typed_capture(self):
        counter = self._counter()
        authored = counter.get_template().source
        _, _, compiled = _typed_binding_tables(counter)
        # Capture does not mutate authored source. Its prepared Vue template
        # consumes Citry bindings while preserving ordinary Vue attributes.
        assert '@c-click="save"' in authored
        assert ":c-count" in authored
        assert "@c-click" not in compiled.template
        assert ":c-count" not in compiled.template
        assert '@click="$state.count++"' in compiled.template
        assert ':class="{a: true}"' in compiled.template

    def test_two_way_targets_collected(self):
        counter = self._counter()
        ext = _events_ext(counter.citry)
        _typed_binding_tables(counter)
        assert ext.two_way_binding_targets(counter) == frozenset({"count"})


class TestStageOneVocabulary:
    """One form per test, so a regression points at the exact vocabulary item."""

    def _one(self, template, *, state=None, events):
        app = Citry(secret=SIGNING_KEY)
        ns = {"citry": app, "template": template}
        if state is not None:
            ns["State"] = type("State", (), state)
        ns["Events"] = type("Events", (), events)
        comp = type("Comp", (Component,), ns)
        return _compiled_html(comp)

    def _one_typed(self, template, *, state=None, events):
        app = Citry(secret=SIGNING_KEY)
        ns = {"citry": app, "template": template, "Events": type("Events", (), events)}
        if state is not None:
            ns["State"] = type("State", (), state)
        comp = type("Comp", (Component,), ns)
        owner, tables, compiled = _typed_binding_tables(comp)
        assert owner.type_key == comp.class_id
        return tables, compiled

    def test_bare_event(self):
        tables, _ = self._one_typed('<button @c-click="save">x</button>', events={"save": _noop})
        [spec] = tables["eventBindings"]
        assert (spec["event"], spec["handler"], spec["args"]) == ("click", "save", None)

    def test_event_modifiers(self):
        tables, _ = self._one_typed('<button @c-keyup.enter.prevent.once="go">x</button>', events={"go": _noop})
        [spec] = tables["eventBindings"]
        assert (spec["event"], spec["key"], spec["prevent"], spec["once"], spec["stop"]) == (
            "keyup",
            "enter",
            True,
            True,
            False,
        )

    def test_debounce_bare_default_and_throttle(self):
        tables, _ = self._one_typed('<button @c-click.debounce.throttle.1s="go">x</button>', events={"go": _noop})
        [spec] = tables["eventBindings"]
        assert spec["debounce"] == 250  # bare .debounce default
        assert spec["throttle"] == 1000  # .throttle.1s

    def test_bare_throttle_default(self):
        # Design 5.1 pins bare `.throttle` (no time segment) at 250 ms, the same
        # default as bare `.debounce`.
        tables, _ = self._one_typed('<button @c-click.throttle="go">x</button>', events={"go": _noop})
        [spec] = tables["eventBindings"]
        assert spec["throttle"] == 250
        assert spec["debounce"] is None

    def test_bare_throttle_default_on_state_binding(self):
        # The same 250 ms default applies on the :c-* state channel (shared builder).
        tables, _ = self._one_typed(
            '<input :c-q.throttle="go">',
            state={"__annotations__": {"q": str}, "q": ""},
            events={"go": _noop},
        )
        [spec] = tables["controlBindings"]
        assert spec["throttle"] == 250
        assert spec["debounce"] is None

    def test_handler_debounce_config_merges_when_binding_has_none(self):
        from citry.ext.events import event

        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class Events:
                @event(debounce=500)
                def go(self):
                    return None

            template = '<button @c-click="go">x</button>'

        _, tables, _ = _typed_binding_tables(Comp)
        [spec] = tables["eventBindings"]
        # The handler's configured debounce fills in when the binding sets none.
        assert spec["debounce"] == 500

    def test_binding_debounce_overrides_handler_config(self):
        from citry.ext.events import event

        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                @event(debounce=500)
                def go(self):
                    return None

            template = '<button @c-click.debounce.50ms="go">x</button>'

        _, tables, _ = _typed_binding_tables(Comp)
        [spec] = tables["eventBindings"]
        assert spec["debounce"] == 50

    def test_poll_interval_in_ms(self):
        tables, _ = self._one_typed('<div @c-poll.5s="go">x</div>', events={"go": _noop})
        assert tables["pollBindings"][0]["interval"] == 5000

    def test_poll_interval_must_fit_javascript_safe_integer_milliseconds(self):
        with pytest.raises(ValueError, match="@c-poll interval exceeds the JavaScript safe-integer limit"):
            self._one('<div @c-poll.9007199254741s="go">x</div>', events={"go": _noop})

    def test_poll_interval_must_be_positive(self):
        with pytest.raises(
            ValueError,
            match=r"'@c-poll\.0s': @c-poll interval must be positive \(in Comp template, line 1\)",
        ):
            self._one('<div @c-poll.0s="go">x</div>', events={"go": _noop})

    def test_one_way_binding(self):
        tables, _ = self._one_typed(
            "<input :c-title>",
            state={"__annotations__": {"title": str}, "title": ""},
            events={"h": _noop},
        )
        [spec] = tables["controlBindings"]
        assert (spec["binding_mode"], spec["field"], spec["handler"]) == ("one-way", "title", None)

    def test_two_way_on_override_and_key_filter(self):
        tables, _ = self._one_typed(
            '<input :c-q.on:keyup.enter="go">',
            state={"__annotations__": {"q": str}, "q": ""},
            events={"go": _noop},
        )
        [spec] = tables["controlBindings"]
        assert (spec["binding_mode"], spec["on"], spec["key"]) == ("two-way", "keyup", "enter")

    def test_field_case_preserved(self):
        # The rewrite is server-side, so a mixed-case State field name survives.
        tables, _ = self._one_typed(
            "<input :c-docId>",
            state={"__annotations__": {"docId": int}, "docId": 0},
            events={"h": _noop},
        )
        assert tables["controlBindings"][0]["field"] == "docId"

    def test_multiple_event_bindings_on_one_element(self):
        tables, compiled = self._one_typed(
            '<input @c-focus="a" @c-blur="b">',
            events={"a": _noop, "b": _noop},
        )
        assert [spec["event"] for spec in tables["eventBindings"]] == ["focus", "blur"]
        opening = compiled.template[compiled.template.index("<input") : compiled.template.index(">")]
        assert opening.index("v-on:focus") < opening.index("v-on:blur")


class TestArgExpressionVerbatim:
    def test_arg_expression_carried_verbatim(self):
        app = Citry()

        class RemoveIn:
            id: str = ""

        class Comp(Component):
            citry = app

            class Events:
                def remove(self, data: RemoveIn):
                    return None

            template = '<button @c-click="remove({id: $el.dataset.id})">x</button>'

        _, tables, _ = _typed_binding_tables(Comp)
        [spec] = tables["eventBindings"]
        assert spec["handler"] == "remove"
        assert spec["args"] == "{id: $el.dataset.id}"

    def test_arg_expression_preserves_authored_inner_whitespace(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

            template = '<button @c-click="save(  {value: 1}  )">x</button>'

        _, tables, _ = _typed_binding_tables(Comp)
        assert tables["eventBindings"][0]["args"] == "  {value: 1}  "

    @pytest.mark.parametrize(
        "expression",
        [
            "{value: ')'}",
            "{value: `closed ) and ${nested(1)}`}",
            r"{value: /\)/.test(text)}",
            "{value: outer(inner(1), () => (2))}",
        ],
    )
    def test_opaque_javascript_interior_is_consumed_whole(self, expression):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

            template = f'<button @c-click="save({expression})">x</button>'

        _, tables, _ = _typed_binding_tables(Comp)
        assert tables["eventBindings"][0]["args"] == expression

    def test_trailing_javascript_is_rejected_instead_of_truncated(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

            template = '<button @c-click="save({ok: true}); selected = false">x</button>'

        with pytest.raises(ValueError, match=r"must end at its final '\)' with no trailing text"):
            _compiled_html(Comp)


class TestCompiledAttributeRobustness:
    """The compiled-node transform handles awkward but valid attributes."""

    def test_gt_inside_binding_value_does_not_end_the_tag(self):
        app = Citry()

        class CmpIn:
            ok: bool = False

        class Comp(Component):
            citry = app

            class Events:
                def save(self, data: CmpIn):
                    return None

            template = '<button @c-click="save({ok: a > b})" title="t">x</button>'

        _, tables, compiled = _typed_binding_tables(Comp)
        # The `>` inside the quoted value must not be read as the tag's end.
        assert 'title="t"' in compiled.template
        assert tables["eventBindings"][0]["args"] == "{ok: a > b}"

    def test_nested_parens_in_arg_expression(self):
        app = Citry(secret=SIGNING_KEY)

        class CmpIn:
            v: int = 0

        class Comp(Component):
            citry = app

            class Events:
                def f(self, data: CmpIn):
                    return None

            template = '<button @c-click="f({v: (1 + 2)})">x</button>'

        _, tables, _ = _typed_binding_tables(Comp)
        assert tables["eventBindings"][0]["args"] == "{v: (1 + 2)}"

    def test_self_closing_element_slash_preserved(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            template = '<input :c-q="go" class="a"/>'

        _, tables, compiled = _typed_binding_tables(Comp)
        assert "<input " in compiled.template
        assert "/>" in compiled.template  # the self-closing slash survives
        assert 'class="a"' in compiled.template
        [spec] = tables["controlBindings"]
        assert spec["field"] == "q"

    def test_static_collapse_uses_parser_byte_offsets_for_unicode_source(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def go(self):
                    return None

            template = '<button title="Příliš žluťoučký" @c-click="go">x</button>'

        _, tables, compiled = _typed_binding_tables(Comp)
        assert 'title="Příliš žluťoučký"' in compiled.template
        assert tables["eventBindings"][0]["handler"] == "go"


class TestValidationErrors:
    """
    Each load error, with message content (design 5.1's error list). Every test
    also asserts the ``(in Comp template, line N)`` location suffix, so no
    error path can lose the template location.
    """

    def _component(self, template, *, state=None, events, child=False):
        app = Citry(secret=SIGNING_KEY)
        if child:
            type("Child", (Component,), {"citry": app, "template": "x"})
        ns = {"citry": app, "template": template}
        if state is not None:
            ns["State"] = type("State", (), state)
        ns["Events"] = type("Events", (), events)
        return type("Comp", (Component,), ns)

    def _load(self, template, *, state=None, events, child=False):
        comp = self._component(template, state=state, events=events, child=child)
        _compiled_html(comp)
        return comp

    def test_undeclared_handler(self):
        with pytest.raises(
            ValueError,
            match=r"names event handler 'ghost', which is not a declared handler.*\(in Comp template, line 1\)",
        ):
            self._load('<button @c-click="ghost">x</button>', events={"real": _noop})

    def test_undeclared_handler_lists_declared(self):
        with pytest.raises(ValueError, match=r"Declared handlers: real \(in Comp template, line 1\)"):
            self._load('<button @c-click="ghost">x</button>', events={"real": _noop})

    def test_empty_event_name(self):
        # `@c-="save"` names no DOM event, so there is nothing to listen for; it
        # must not ship event="" to the client. It fails at load, with location.
        with pytest.raises(
            ValueError, match=r"'@c-' needs a DOM event name, e\.g\. '@c-click'.*\(in Comp template, line 1\)"
        ):
            self._load('<button @c-="save">x</button>', events={"save": _noop})

    def test_empty_event_name_with_modifier(self):
        # The same holds when a modifier follows the empty base (`@c-.prevent`).
        with pytest.raises(ValueError, match=r"'@c-\.prevent' needs a DOM event name.*\(in Comp template, line 1\)"):
            self._load('<button @c-.prevent="save">x</button>', events={"save": _noop})

    def test_error_carries_template_location(self):
        with pytest.raises(ValueError, match=r"\(in Comp template, line 3\)"):
            self._load(
                '<div>\n  <p>hi</p>\n  <button @c-click="ghost">x</button>\n</div>',
                events={"real": _noop},
            )

    def test_event_handler_on_component_tag_stays_for_boundary_capture(self):
        comp = self._component('<c-Child @c-click="go" />', events={"go": _noop}, child=True)
        owner, tables, compiled = _typed_binding_tables(comp)
        [event] = tables["eventBindings"]
        [call] = compiled.local_calls
        [binding] = call["bindings"]

        assert owner.type_key == comp.class_id
        assert '@c-click="go"' in comp.get_template().source
        assert (event["event"], event["handler"]) == ("click", "go")
        assert (binding["kind"], binding["name"]) == ("event", "v-on:click")

    def test_component_handler_is_validated_during_compilation(self):
        comp = self._component('<c-Child @c-click="ghost" />', events={"go": _noop}, child=True)
        with pytest.raises(ValueError, match=r"names event handler 'ghost'.*component boundary"):
            _typed_binding_tables(comp)

    def test_invalid_literal_does_not_mutate_or_fail_template_loading(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def real(self):
                    return None

            template = '<button @c-click="ghost">x</button>'

        assert Comp.get_template().source == Comp.template
        with pytest.raises(ValueError, match=r"names event handler 'ghost'.*\(in Comp template, line 1\)"):
            _compiled_html(Comp)

    def test_component_state_binding_remains_invalid(self):
        with pytest.raises(
            ValueError,
            match=r"binds State on it.*native Vue prop binding.*Python kwargs.*\(in Comp template, line 1\)",
        ):
            self._load('<c-Child :c-x="go" />', events={"go": _noop}, child=True)

    def test_field_not_public(self):
        with pytest.raises(
            ValueError,
            match=r"'secret', which is not a public State field \(not in _public\).*\(in Comp template, line 1\)",
        ):
            self._load(
                "<span :c-secret>x</span>",
                state={"__annotations__": {"secret": int}, "secret": 0, "_public": ()},
                events={"h": _noop},
            )

    def test_field_not_a_state_field(self):
        with pytest.raises(
            ValueError, match=r"binds 'ghost', which is not a State field.*\(in Comp template, line 1\)"
        ):
            self._load(
                "<span :c-ghost>x</span>",
                state={"__annotations__": {"real": int}, "real": 0},
                events={"h": _noop},
            )

    def test_two_way_field_not_writable(self):
        with pytest.raises(
            ValueError, match=r"public but not writable \(not in _model\).*\(in Comp template, line 1\)"
        ):
            self._load(
                '<input :c-shown="h">',
                state={"__annotations__": {"shown": int}, "shown": 0, "_model": ()},
                events={"h": _noop},
            )

    def test_binding_without_state_class(self):
        with pytest.raises(
            ValueError,
            match=r"binds State field 'q', but Comp declares no State class.*\(in Comp template, line 1\)",
        ):
            self._load("<input :c-q>", events={"go": _noop})

    def test_unknown_modifier(self):
        with pytest.raises(ValueError, match=r"has an unknown modifier '\.wat'.*\(in Comp template, line 1\)"):
            self._load('<button @c-click.wat="go">x</button>', events={"go": _noop})

    def test_unclosed_call_shell(self):
        # The strict outer-shell error names the binding and carries the
        # template location, like every other load error.
        with pytest.raises(
            ValueError,
            match=r"'@c-click': a server-handler call must end at its final '\)' with no trailing text"
            r" \(in Comp template, line 1\)",
        ):
            self._load('<button @c-click="save({stars: 5">x</button>', events={"save": _noop})

    def test_poll_second_time_segment(self):
        with pytest.raises(
            ValueError,
            match=r"@c-poll takes exactly one interval; found a second time segment.*\(in Comp template, line 1\)",
        ):
            self._load('<div @c-poll.30s.5s="go">x</div>', events={"go": _noop})

    def test_poll_interval_rejects_milliseconds(self):
        # The @c-poll interval is seconds, one segment exactly (design 5.1); a
        # millisecond unit is a load error, not a silent 500 ms poll.
        with pytest.raises(
            ValueError,
            match=r"the @c-poll interval is in seconds, e\.g\. '\.30s', not '\.500ms'.*\(in Comp template, line 1\)",
        ):
            self._load('<div @c-poll.500ms="go">x</div>', events={"go": _noop})

    def test_poll_needs_interval(self):
        with pytest.raises(ValueError, match=r"@c-poll needs an interval.*\(in Comp template, line 1\)"):
            self._load('<div @c-poll="go">x</div>', events={"go": _noop})

    def test_lazy_with_on_conflict(self):
        with pytest.raises(ValueError, match=r"'\.lazy' and '\.on:' cannot be combined.*\(in Comp template, line 1\)"):
            self._load(
                '<input :c-q.lazy.on:keyup="go">',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    def test_empty_on_event_override(self):
        # `.on:` with no event name (`.on:=`) is a malformed shape; it must not
        # ship on="" to the client.
        with pytest.raises(
            ValueError, match=r"'\.on:' needs an event name, e\.g\. '\.on:keyup'.*\(in Comp template, line 1\)"
        ):
            self._load(
                '<input :c-q.on:="go">',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    def test_lazy_on_event_binding(self):
        with pytest.raises(
            ValueError, match=r"'\.lazy' only applies to a two-way state binding.*\(in Comp template, line 1\)"
        ):
            self._load('<button @c-click.lazy="go">x</button>', events={"go": _noop})

    def test_update_timing_on_one_way_binding(self):
        with pytest.raises(
            ValueError,
            match=r"is a one-way binding.*cannot carry an update-timing modifier.*\(in Comp template, line 1\)",
        ):
            self._load(
                "<input :c-q.debounce.300ms>",
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    def test_lazy_on_committed_control(self):
        with pytest.raises(ValueError, match=r"'\.lazy' has no effect on <select>.*\(in Comp template, line 1\)"):
            self._load(
                '<select :c-q.lazy="go"></select>',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    def test_lazy_on_committed_input_type(self):
        with pytest.raises(
            ValueError, match=r'\.lazy\' has no effect on <input type="checkbox">.*\(in Comp template, line 1\)'
        ):
            self._load(
                '<input type="checkbox" :c-q.lazy="go">',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    @pytest.mark.parametrize("event_name", ["click", "lol"])
    def test_event_key_filter_accepts_any_event_name(self, event_name):
        comp = self._component(f'<button @c-{event_name}.enter="go">x</button>', events={"go": _noop})
        _, tables, compiled = _typed_binding_tables(comp)
        [spec] = tables["eventBindings"]
        assert f"@c-{event_name}" not in compiled.template
        assert spec["event"] == event_name
        assert spec["key"] == "enter"

    def test_state_key_filter_accepts_any_update_event_name(self):
        comp = self._component(
            '<input :c-q.on:lol.escape="go">',
            state={"__annotations__": {"q": str}, "q": ""},
            events={"go": _noop},
        )
        _, tables, compiled = _typed_binding_tables(comp)
        [spec] = tables["controlBindings"]
        assert ":c-q" not in compiled.template
        assert spec["on"] == "lol"
        assert spec["key"] == "escape"

    def test_file_input_two_way(self):
        with pytest.raises(
            ValueError, match=r'<input type="file"> cannot be bound to State.*\(in Comp template, line 1\)'
        ):
            self._load(
                '<input type="file" :c-q="go">',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    def test_custom_control_needs_on(self):
        with pytest.raises(
            ValueError,
            match=r"is a custom element, so it has no default update event.*'\.on:.*\(in Comp template, line 1\)",
        ):
            self._load(
                '<my-widget :c-q="go"></my-widget>',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )


class TestBindingTarget:
    """
    Which elements a ``:c-*`` binding may sit on.

    The client reads a control's value and writes it back, so a binding needs an
    element that holds one: ``<input>``, ``<textarea>``, ``<select>``, or a
    custom element that exposes a value. On any other plain element the binding
    would apply nothing on the way down and write an undefined value on the way
    up, so it is rejected while the template loads.
    """

    _STATE = {"__annotations__": {"q": str}, "q": ""}

    def _component(self, template):
        app = Citry(secret=SIGNING_KEY)
        state_cls = type("State", (), dict(self._STATE))
        events_cls = type("Events", (), {"go": _noop})
        comp = type(
            "Comp",
            (Component,),
            {
                "citry": app,
                "State": state_cls,
                "Events": events_cls,
                "template": template,
                "template_data": lambda _self, _kwargs, _slots: {
                    "tag": "input",
                    "attrs": {"is": "input"},
                },
            },
        )
        return comp

    def _load(self, template):
        return _compiled_html(self._component(template))

    def _typed_control(self, template):
        comp = self._component(template)
        owner, tables, compiled = _typed_binding_tables(comp)
        assert owner.type_key == comp.class_id
        [spec] = tables["controlBindings"]
        tag = template.lstrip()[1:].split(None, 1)[0].rstrip("/>").casefold()
        if tag == "c-element":
            static_target = re.search(
                r"""\bis\s*=\s*(["'])([^"']+)\1""",
                template,
                flags=re.IGNORECASE,
            )
            assert static_target is not None
            tag = static_target.group(2).casefold()
        assert f"<{tag}" in compiled.template.casefold()
        assert "v-citry-control=" in compiled.template
        return spec

    _NO_VALUE = r"holds no value, so a State binding has nothing to bind.*use an '@c-\*' event binding instead"

    @pytest.mark.parametrize(
        "template",
        [
            '<input :c-q="go">',
            "<input :c-q>",
            '<textarea :c-q="go"></textarea>',
            "<textarea :c-q></textarea>",
            '<select :c-q="go"></select>',
            "<select :c-q></select>",
            '<select multiple :c-q="go"></select>',
            "<select multiple :c-q></select>",
        ],
    )
    def test_form_controls_are_accepted(self, template):
        spec = self._typed_control(template)
        assert spec["field"] == "q"

    @pytest.mark.parametrize(
        "template",
        [
            # A `.on:` event does not make a <div> bindable: naming when to read
            # a value does not give the element a value to read.
            '<div :c-q.on:click="go"></div>',
            '<div :c-q="go"></div>',
            "<div :c-q></div>",
            "<span :c-q>x</span>",
            '<p :c-q="go"></p>',
            "<a :c-q>link</a>",
        ],
    )
    def test_elements_without_a_value_are_rejected(self, template):
        with pytest.raises(ValueError, match=self._NO_VALUE):
            self._load(template)

    def test_custom_element_one_way_is_accepted(self):
        spec = self._typed_control("<my-picker :c-q></my-picker>")
        assert spec["binding_mode"] == "one-way"
        assert spec["field"] == "q"

    def test_custom_element_two_way_is_accepted_with_an_event(self):
        spec = self._typed_control('<my-picker :c-q.on:pick="go"></my-picker>')
        assert spec["binding_mode"] == "two-way"
        assert spec["on"] == "pick"

    def test_c_element_binds_the_element_its_is_names(self):
        # `<c-element is="input">` renders an <input>, so the binding is valid
        # and needs no explicit update event.
        spec = self._typed_control('<c-element is="input" :c-q="go" />')
        assert (spec["binding_mode"], spec["field"], spec["handler"]) == ("two-way", "q", "go")

    def test_c_element_input_uses_the_same_type_matrix(self):
        with pytest.raises(ValueError, match=r'<input type="submit"> cannot be bound to State'):
            self._load('<c-element is="input" type="submit" :c-q="go" />')

    def test_c_element_naming_a_valueless_element_is_rejected(self):
        with pytest.raises(ValueError, match=self._NO_VALUE):
            self._load('<c-element is="div" :c-q="go" />')

    def test_c_element_with_a_computed_name_defers_target_validation(self):
        comp = self._component('<c-element c-is="tag" :c-q="go" />')
        owner, tables, _ = _typed_binding_tables(comp)
        [spec] = tables["controlBindings"]
        assert owner.type_key == comp.class_id
        assert (spec["binding_mode"], spec["field"]) == ("two-way", "q")

    def test_c_element_with_a_spread_name_defers_target_validation(self):
        comp = self._component('<c-element c-bind="attrs" :c-q="go" />')
        owner, tables, _ = _typed_binding_tables(comp)
        [spec] = tables["controlBindings"]
        assert owner.type_key == comp.class_id
        assert (spec["binding_mode"], spec["field"]) == ("two-way", "q")

    @pytest.mark.parametrize(
        "template",
        [
            # HTML attribute names are case insensitive, so an uppercase
            # spelling must reach the same check as the lowercase one.
            '<input type="file" :c-q="go">',
            '<input TYPE="file" :c-q="go">',
            '<input Type="file" :c-q="go">',
            # Neither direction can work, so the one-way form is rejected too.
            '<input type="file" :c-q>',
            '<input TYPE="file" :c-q>',
        ],
    )
    def test_file_inputs_are_rejected_in_both_directions(self, template):
        with pytest.raises(ValueError, match=r'<input type="file"> cannot be bound to State'):
            self._load(template)

    @pytest.mark.parametrize(
        "input_type",
        [
            "text",
            "search",
            "tel",
            "url",
            "email",
            "password",
            "date",
            "month",
            "week",
            "time",
            "datetime-local",
            "number",
            "range",
            "color",
            "checkbox",
            "radio",
        ],
    )
    @pytest.mark.parametrize(("binding", "mode"), [(':c-q="go"', "two-way"), (":c-q", "one-way")])
    def test_editable_input_types_support_both_directions(self, input_type, binding, mode):
        spec = self._typed_control(f'<input type="{input_type}" {binding}>')
        assert spec["binding_mode"] == mode

    def test_hidden_supports_one_way_only(self):
        spec = self._typed_control('<input type="hidden" :c-q>')
        assert spec["binding_mode"] == "one-way"
        with pytest.raises(ValueError, match=r"supports one-way State bindings only"):
            self._load('<input type="hidden" :c-q="go">')

    @pytest.mark.parametrize("input_type", ["submit", "image", "reset", "button"])
    @pytest.mark.parametrize("binding", [':c-q="go"', ":c-q"])
    def test_action_input_types_support_neither_direction(self, input_type, binding):
        with pytest.raises(ValueError, match=rf'<input type="{input_type}"> cannot be bound to State'):
            self._load(f'<input type="{input_type}" {binding}>')

    @pytest.mark.parametrize("type_attr", ["", ' type=""', " type"])
    @pytest.mark.parametrize("binding", [':c-q="go"', ":c-q"])
    def test_missing_empty_and_bare_type_are_text(self, type_attr, binding):
        spec = self._typed_control(f"<input{type_attr} {binding}>")
        assert spec["field"] == "q"

    def test_input_type_is_case_insensitive_but_not_whitespace_trimmed(self):
        spec = self._typed_control('<input type="TEXT" :c-q="go">')
        assert spec["field"] == "q"
        with pytest.raises(ValueError, match=r"not a recognized input type"):
            self._load('<input type=" text " :c-q="go">')

    def test_unknown_input_type_has_a_distinct_error(self):
        with pytest.raises(ValueError, match=r"not a recognized input type in this Citry version"):
            self._load('<input type="future-widget" :c-q>')

    @pytest.mark.parametrize("input_type", ["hidden", "submit", "image", "reset", "button", "file", "wat"])
    def test_on_override_does_not_upgrade_an_unsupported_native_type(self, input_type):
        with pytest.raises(
            ValueError, match=r"cannot be bound|one-way State bindings only|not a recognized input type"
        ):
            self._load(f'<input type="{input_type}" :c-q.on:change="go">')

    @pytest.mark.parametrize(
        "template",
        [
            # A hyphen alone does not make a custom element: HTML reserves
            # these names for SVG and MathML elements that hold no value.
            "<font-face :c-q></font-face>",
            "<missing-glyph :c-q></missing-glyph>",
            "<color-profile :c-q></color-profile>",
            "<annotation-xml :c-q></annotation-xml>",
            # Citry's own tags are components, reachable here through the
            # element the `is` attribute names.
            '<c-element is="c-foo" :c-q.on:x="go" />',
        ],
    )
    def test_hyphenated_names_that_are_not_custom_elements_are_rejected(self, template):
        with pytest.raises(ValueError, match=self._NO_VALUE):
            self._load(template)

    def test_uppercase_tag_names_are_classified_the_same(self):
        # HTML tag names are case insensitive, so the spelling must not change
        # the verdict, for a control or for a custom element.
        assert self._typed_control("<INPUT :c-q>")["field"] == "q"
        assert self._typed_control("<My-Widget :c-q></My-Widget>")["field"] == "q"
        with pytest.raises(ValueError, match=self._NO_VALUE):
            self._load("<DIV :c-q></DIV>")


class TestStageTwoSpread:
    """Bindings that arrive through a render-time spread (attrs kwarg + c-bind)."""

    def test_event_and_two_way_through_spread(self):
        # A State-declaring component mints its state token at render, which
        # needs a signing secret.
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"btn": {"@c-click.prevent": "go"}, "inp": {":c-q.debounce": "go"}}

            template = '<button c-bind="btn">go</button><input c-bind="inp">'

        owner, tables, compiled = _typed_binding_tables(Comp)
        [event] = tables["eventBindings"]
        [control] = tables["controlBindings"]
        assert owner.type_key == Comp.class_id
        assert (event["event"], event["handler"], event["prevent"]) == ("click", "go", True)
        assert (control["binding_mode"], control["field"], control["debounce"]) == ("two-way", "q", 250)
        assert "data-cev-" not in compiled.template

    def test_multiple_select_and_binding_are_accepted_through_spread(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                tags: list[str] = ()

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"attrs": {"multiple": True, ":c-tags": "go"}}

            template = '<select c-bind="attrs"><option value="a">A</option></select>'

        owner, tables, compiled = _typed_binding_tables(Comp)
        [control] = tables["controlBindings"]
        attrs = [value for key, value in owner.prepared_data.items() if key.startswith("citryAttrs")]
        assert (control["binding_mode"], control["field"]) == ("two-way", "tags")
        assert any(attrs_for_element.get("multiple") is True for attrs_for_element in attrs)
        assert "v-citry-control=" in compiled.template
        assert "data-cev-" not in compiled.template

    def test_binding_spread_onto_an_element_without_a_value_is_rejected(self):
        # The target check runs in the shared spec builder, so a binding that
        # only appears at render time is rejected there too, naming the spread.
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"attrs": {":c-q": "go"}}

            template = '<div c-bind="attrs"></div>'

        with pytest.raises(
            ValueError,
            match=r"holds no value.*after dynamic attributes resolved",
        ):
            _rendered(Comp())

    def test_spread_merges_with_literal_binding_on_same_element(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class Events:
                def a(self):
                    return None

                def b(self):
                    return None

            def template_data(self, kwargs, slots):
                return {"extra": {"@c-mouseover": "b"}}

            template = '<button @c-click="a" c-bind="extra">go</button>'

        owner, tables, compiled = _typed_binding_tables(Comp)
        specs = tables["eventBindings"]
        # The literal listener stays in the Vue template while the spread
        # listener is represented by a typed runtime event site.
        assert [s["event"] for s in specs] == ["click", "mouseover"]
        assert [s["handler"] for s in specs] == ["a", "b"]
        runtime_event = specs[1]
        [site] = compiled.runtime_event_sites
        start, end = site["sourceStart"], site["sourceEnd"]
        opening = compiled.template.encode()[start:end].decode()

        assert "v-on:click" in compiled.template
        assert "v-citry-runtime-events=" in opening
        assert site["bindingKey"] in opening
        assert owner.prepared_data[site["bindingKey"]] == runtime_event["id"]
        assert "v-on:mouseover" not in compiled.template
        assert "data-cev-" not in compiled.template

    def test_spread_validation_error_is_render_time_with_same_wording(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def real(self):
                    return None

            def template_data(self, kwargs, slots):
                return {"a": {"@c-click": "ghost"}}

            template = '<button c-bind="a">x</button>'

        with pytest.raises(ValueError, match=r"names event handler 'ghost'.*after dynamic attributes resolved"):
            _rendered(Comp())

    def test_empty_on_override_through_spread_is_render_time(self):
        # The empty-`.on:` rejection also fires for a spread-contributed binding,
        # at render time, with the same wording (stage two shares the builder).
        # The secret keeps the render-time token mint (which runs first) out of
        # the way, so the error under test is the one that surfaces.
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"a": {":c-q.on:": "go"}}

            template = '<input c-bind="a">'

        with pytest.raises(ValueError, match=r"'\.on:' needs an event name.*after dynamic attributes resolved"):
            _rendered(Comp())


class TestBindingShapedText:
    def test_c_raw_content_is_literal(self):
        app = Citry()

        class Comp(Component):
            citry = app

            template = '<c-raw><button @c-click="ghost">x</button></c-raw>'

        owner, tables, compiled = _typed_binding_tables(Comp)
        assert not any(tables.values())
        assert "citry-opaque-html" in compiled.template
        assert any('@c-click="ghost"' in item["html"] for item in owner.prepared_data["opaqueHtml"].values())

    @pytest.mark.parametrize(
        "template",
        [
            '<div><!-- <button @c-click="ghost"> --></div>',
            '<script>const markup = `<button @c-click="ghost">`;</script>',
            '<style>/* <button @c-click="ghost"> */</style>',
            '<textarea><button @c-click="ghost"></textarea>',
            '<title><button @c-click="ghost"></title>',
        ],
    )
    def test_comments_and_native_text_containers_are_literal(self, template):
        app = Citry()
        comp = type("Comp", (Component,), {"citry": app, "template": template})
        _, tables, compiled = _typed_binding_tables(comp)
        assert not any(tables.values())
        assert '@c-click="ghost"' in compiled.template


class TestNestedTemplateBindings:
    """Nested string-template bindings remain attached to their lexical owner."""

    def test_nested_template_attr_uses_its_owner_events_scope(self):
        app = Citry(secret=SIGNING_KEY)

        class Card(Component):
            citry = app
            template = "<section>{{ body }}</section>"

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

        class Page(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            template = "<c-card c-body=\"<input @c-focus='go' :c-q='go'>\" />"

        owner, tables, compiled = _typed_binding_tables(Page)
        assert owner.type_key == Page.class_id
        assert tables["eventBindings"][0]["handler"] == "go"
        assert tables["controlBindings"][0]["field"] == "q"
        assert "data-cev-" not in compiled.template
        assert _events_ext(app).two_way_binding_targets(Page) == frozenset({"q"})

    def test_invalid_nested_template_binding_fails_when_fragment_compiles(self):
        app = Citry()

        class Card(Component):
            citry = app
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

        class Page(Component):
            citry = app

            class Events:
                def real(self):
                    return None

            template = "<c-card c-body=\"<button @c-click='ghost'>x</button>\" />"

        with pytest.raises(ValueError, match=r"names event handler 'ghost'.*\(in Page template, line 1\)"):
            _compiled_html(Page)


class TestComponentTagSpreadBoundary:
    """
    Component-boundary entries from a render-time spread follow A1's split.

    ``@c-*`` is captured as a component-call browser binding, separate from
    the child's Python kwargs. ``:c-*`` is element-only and therefore fails
    at input resolution, just as its directly authored form fails while the
    template loads.
    """

    def test_event_binding_via_spread_is_compiled_for_the_boundary_manifest(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = "<span>child</span>"

        class Parent(Component):
            citry = app

            class Events:
                def go(self):
                    return None

            def template_data(self, kwargs, slots):
                return {"a": {"@c-click": "go"}}

            template = '<c-Child c-bind="a"></c-Child>'

        owner, tables, compiled = _typed_binding_tables(Parent)
        [event] = tables["eventBindings"]
        [call] = compiled.local_calls
        [binding] = call["bindings"]

        assert owner.type_key == Parent.class_id
        assert (event["event"], event["handler"]) == ("click", "go")
        assert call["typeKey"] == Child.class_id
        assert binding["kind"] == "event"
        assert binding["name"] == "v-on:click"
        assert f"dispatchComponent('{event['id']}', $event)" in binding["value"]

    def test_runtime_component_event_carrier_cannot_be_forged(self):
        forged = RuntimeComponentEventBinding("@c-click", "go", "<c-Child c-bind='a'>", (9, 19))

        assert not is_authenticated_runtime_component_event_binding(forged)

    def test_event_binding_via_spread_accepts_only_a_handler_name(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = "<span>child</span>"

        class Payload:
            value: int

        class Parent(Component):
            citry = app

            class Events:
                def go(self, data: Payload):
                    return None

            def template_data(self, kwargs, slots):
                return {"a": {"@c-click": "go(1)"}}

            template = '<c-Child c-bind="a"></c-Child>'

        with pytest.raises(TypeError, match="accept a handler name without arguments"):
            _typed_binding_tables(Parent)

    def test_runtime_and_authored_listener_collision_is_rejected(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = "<span>child</span>"

        class Parent(Component):
            citry = app

            class Events:
                def go(self):
                    return None

            def template_data(self, kwargs, slots):
                return {"a": {"@c-click": "go"}}

            template = '<c-Child v-on:click="noop" c-bind="a"></c-Child>'

        with pytest.raises(TypeError, match="more than one listener named 'v-on:click'"):
            _typed_binding_tables(Parent)

    def test_cached_runtime_component_listener_replays(self):
        app = Citry(cache=InMemoryCache())
        renders = 0

        class Child(Component):
            citry = app
            template = "<span>child</span>"

        class Parent(Component):
            citry = app

            class Cache:
                enabled = True

            class Events:
                def go(self):
                    return None

            def template_data(self, kwargs, slots):
                nonlocal renders
                renders += 1
                return {"a": {"@c-click": "go"}}

            template = '<c-Child c-bind="a"></c-Child>'

        first = _typed_binding_tables(Parent)
        second = _typed_binding_tables(Parent)

        assert renders == 1
        assert first[1]["eventBindings"] == second[1]["eventBindings"]
        assert first[2].local_calls == second[2].local_calls

    def test_state_binding_via_spread_is_rejected(self):
        # The secret: a State-declaring component mints its token at render.
        app = Citry(secret=SIGNING_KEY)

        class Child(Component):
            citry = app
            template = "<span>child</span>"

        class Parent(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"a": {":c-q": "go"}}

            template = '<c-Child c-bind="a"></c-Child>'

        with pytest.raises(RuntimeError, match=r"State binding ':c-q'.*component boundary"):
            _rendered(Parent())


class TestResolvedControlTypeValidation:
    """Final server-rendered attributes are checked after c-type/c-bind resolution."""

    def _component(self, template, data):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return data

        Comp.template = template
        return Comp

    @pytest.mark.parametrize("resolved_type", ["hidden", "file", "submit", "image", "reset", "button", "wat"])
    def test_literal_binding_plus_c_type_is_revalidated(self, resolved_type):
        comp = self._component('<input c-type="t" :c-q="go">', {"t": resolved_type})
        with pytest.raises(ValueError, match=r"after all attribute hooks resolved"):
            _rendered(comp())

    def test_literal_binding_plus_c_type_accepts_valid_case_insensitive_type(self):
        comp = self._component('<input c-type="t" :c-q="go">', {"t": "TEXT"})
        owner, tables, compiled = _typed_binding_tables(comp)
        [spec] = tables["controlBindings"]
        assert compiled.template.startswith("<input ")
        assert "v-citry-control=" in compiled.template
        assert any(
            attrs.get("type") == "TEXT" for key, attrs in owner.prepared_data.items() if key.startswith("citryAttrs")
        )
        assert spec["binding_mode"] == "two-way"

    def test_literal_binding_plus_spread_type_is_revalidated(self):
        comp = self._component('<input :c-q="go" c-bind="attrs">', {"attrs": {"type": "file"}})
        with pytest.raises(ValueError, match=r'<input type="file"> cannot be bound to State'):
            _rendered(comp())

    def test_spread_supplying_type_and_binding_is_revalidated(self):
        comp = self._component('<input c-bind="attrs">', {"attrs": {"type": "submit", ":c-q": "go"}})
        with pytest.raises(ValueError, match=r'<input type="submit"> cannot be bound to State'):
            _rendered(comp())

    def test_case_variant_type_is_recognized_and_later_spread_wins(self):
        accepted = self._component('<input :c-q="go" c-bind="attrs">', {"attrs": {"TYPE": "TEXT"}})
        accepted_owner, accepted_tables, _ = _typed_binding_tables(accepted)
        assert accepted_owner.type_key == accepted.class_id
        assert accepted_tables["controlBindings"][0]["binding_mode"] == "two-way"
        overridden = self._component(
            '<input type="submit" :c-q="go" c-bind="attrs">',
            {"attrs": {"TYPE": "TEXT"}},
        )
        owner, tables, _ = _typed_binding_tables(overridden)
        attrs = [value for key, value in owner.prepared_data.items() if key.startswith("citryAttrs")]
        assert any(name.casefold() == "type" and value == "TEXT" for item in attrs for name, value in item.items())
        assert tables["controlBindings"][0]["binding_mode"] == "two-way"

    def test_bare_resolved_type_is_default_text(self):
        comp = self._component('<input :c-q="go" c-bind="attrs">', {"attrs": {"type": True}})
        _, tables, _ = _typed_binding_tables(comp)
        assert tables["controlBindings"][0]["binding_mode"] == "two-way"

    def test_existing_compiled_binding_is_revalidated_without_raw_binding_key(self):
        comp = self._component('<input c-type="t" :c-q="go">', {"t": "file"})
        # Compilation preserves authored source while the compiled node passed
        # to the final-attrs hook no longer contains the raw binding key.
        assert ":c-q" in comp.get_template().source
        with pytest.raises(ValueError, match=r'<input type="file"> cannot be bound to State'):
            _rendered(comp())

    def test_lazy_is_revalidated_against_final_type(self):
        comp = self._component('<input c-type="t" :c-q.lazy="go">', {"t": "checkbox"})
        with pytest.raises(ValueError, match=r"'\.lazy' has no effect"):
            _rendered(comp())

    @pytest.mark.parametrize(
        ("binding", "binding_mode"),
        [
            (":c-q", "one-way"),
            (':c-q="go"', "two-way"),
        ],
    )
    def test_computed_c_element_binding_uses_owner_and_final_tag(self, binding, binding_mode):
        comp = self._component(f'<c-element c-is="tag" {binding} />', {"tag": "input"})
        owner, tables, _ = _typed_binding_tables(comp)
        [spec] = tables["controlBindings"]
        assert owner.type_key == comp.class_id
        assert spec["field"] == "q"
        assert spec["binding_mode"] == binding_mode

    def test_computed_c_element_binding_rejects_final_valueless_tag(self):
        comp = self._component('<c-element c-is="tag" :c-q="go" />', {"tag": "div"})
        with pytest.raises(
            ValueError,
            match=r"':c-q': <div> holds no value.*\(in Comp template, <div> after all attribute hooks resolved\)",
        ):
            _rendered(comp())

    def test_computed_c_element_binding_rejects_final_input_type(self):
        comp = self._component(
            '<c-element c-is="tag" type="submit" :c-q="go" />',
            {"tag": "input"},
        )
        with pytest.raises(ValueError, match=r'<input type="submit"> cannot be bound to State'):
            _rendered(comp())

    def test_computed_c_element_custom_target_still_needs_update_event(self):
        comp = self._component('<c-element c-is="tag" :c-q="go" />', {"tag": "my-picker"})
        with pytest.raises(ValueError, match=r"custom element.*\.on:<event>"):
            _rendered(comp())

    def test_computed_c_element_modifiers_validate_against_final_tag(self):
        comp = self._component('<c-element c-is="tag" :c-q.lazy="go" />', {"tag": "select"})
        with pytest.raises(ValueError, match=r"'\.lazy' has no effect on <select>"):
            _rendered(comp())

    def test_c_element_spread_bindings_use_lexical_owner(self):
        comp = self._component(
            '<c-element c-is="tag" c-bind="attrs" />',
            {
                "tag": "input",
                "attrs": {
                    "@c-click": "go",
                    "@c-poll.10s": "go",
                    ":c-q": "go",
                },
            },
        )
        owner, tables, _ = _typed_binding_tables(comp)
        [event] = tables["eventBindings"]
        [poll] = tables["pollBindings"]
        [control] = tables["controlBindings"]
        assert owner.type_key == comp.class_id
        assert event["handler"] == "go"
        assert poll["handler"] == "go"
        assert control["field"] == "q"

    @pytest.mark.parametrize(
        ("attrs", "error"),
        [
            ({"@c-click": "missing"}, r"declared handler of Comp"),
            ({":c-missing": "go"}, r"Declared State fields: q \(in Comp template"),
        ],
    )
    def test_c_element_spread_binding_errors_name_lexical_owner(self, attrs, error):
        comp = self._component(
            '<c-element c-is="tag" c-bind="attrs" />',
            {"tag": "input", "attrs": attrs},
        )
        with pytest.raises(ValueError, match=error):
            _rendered(comp())


class TestReservedEventsMetadataAttributes:
    """Authored HTML cannot impersonate internal Events metadata."""

    def _render_attrs(self, attrs):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"attrs": attrs}

            template = '<input c-bind="attrs">'

        return _rendered(Comp())

    @pytest.mark.parametrize(
        "name",
        [
            "data-cev-on",
            "data-cev-poll",
            "data-cev-bind",
            "data-cev-future",
            "DATA-CEV-ON",
            "Data-Cev-Future",
        ],
    )
    def test_static_compiler_owned_attributes_are_rejected(self, name):
        app = Citry()
        comp = type(
            "Comp",
            (Component,),
            {"citry": app, "template": f'<input {name}="manual">'},
        )
        with pytest.raises(RuntimeError, match=rf"{name!r}.*reserved internal Events namespace"):
            _compiled_html(comp)

    def test_static_compiler_owned_attribute_cannot_duplicate_a_raw_binding(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            template = '<input :c-q data-cev-bind="manual">'

        with pytest.raises(RuntimeError, match=r"data-cev-bind.*reserved internal Events namespace"):
            _compiled_html(Comp)

    @pytest.mark.parametrize("name", ["data-cev-on", "data-cev-poll", "data-cev-bind", "data-cev-future"])
    def test_spread_cannot_author_compiler_owned_attributes(self, name):
        with pytest.raises(RuntimeError, match=rf"{name!r}.*reserved internal Events namespace"):
            self._render_attrs({name: "manual"})

    def test_dynamic_attribute_cannot_author_compiler_owned_attributes(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"manual": "forged"}

            template = '<input c-data-cev-on="manual">'

        with pytest.raises(RuntimeError, match=r"data-cev-on.*reserved internal Events namespace"):
            _rendered(Comp())

    def test_c_element_spread_cannot_author_compiler_owned_attributes(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"attrs": {"data-cev-bind": "forged"}}

            template = '<c-element is="input" c-bind="attrs" />'

        with pytest.raises(RuntimeError, match=r"data-cev-bind.*reserved internal Events namespace"):
            _rendered(Comp())


class TestPassthrough:
    def test_plain_alpine_untouched(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app
            template = '<button @click="x++" :class="{a: 1}" :disabled="loading">y</button>'

        # No @c-*/:c-* anywhere, so the template is returned byte-for-byte.
        assert Comp.get_template().source == '<button @click="x++" :class="{a: 1}" :disabled="loading">y</button>'

    def test_bare_c_expression_channel_untouched(self):
        # A bare c-* dynamic-expression attribute is a different channel and is
        # never a binding; it must survive untouched.
        app = Citry()

        class Comp(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"cls": "btn"}

            template = '<button c-class="cls">y</button>'

        assert _rendered(Comp()) == '<button class="btn">y</button>'

    def test_template_without_bindings_is_unchanged(self):
        app = Citry()

        class Comp(Component):
            citry = app
            template = "<div><p>hello</p></div>"

        assert Comp.get_template().source == "<div><p>hello</p></div>"


class TestTypedPreparedBindingContract:
    """Event, poll, and control metadata is carried in typed prepared tables."""

    def test_typed_specs_are_self_identifying_and_match_compiled_directives(self):
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            template = '<input @c-keyup.enter="go" :c-q.debounce.300ms="go"><div @c-poll.5s="go">p</div>'

        owner, tables, compiled = _typed_binding_tables(Comp)
        [event] = tables["eventBindings"]
        [poll] = tables["pollBindings"]
        [control] = tables["controlBindings"]

        assert owner.type_key == Comp.class_id
        assert set(event) == {
            "id",
            "event",
            "handler",
            "args",
            "prevent",
            "stop",
            "self",
            "once",
            "key",
            "debounce",
            "throttle",
        }
        assert set(poll) == {"id", "handler", "args", "interval"}
        assert set(control) == {
            "id",
            "field",
            "binding_mode",
            "handler",
            "lazy",
            "on",
            "key",
            "debounce",
            "throttle",
        }
        assert all("cid" not in spec for specs in tables.values() for spec in specs)
        assert (event["event"], event["handler"], event["key"]) == ("keyup", "go", "enter")
        assert (poll["handler"], poll["interval"]) == ("go", 5000)
        assert (control["field"], control["handler"], control["debounce"]) == ("q", "go", 300)
        assert "v-on:keyup.enter" in compiled.template
        assert "v-citry-event-timing" in compiled.template
        assert "v-citry-control" in compiled.template
        assert "data-cev-" not in compiled.template
