"""
Tests for the events binding rewrite (WP12): the two-stage ``@c-*`` / ``:c-*``
to ``data-cev-*`` rewrite and the design's hard template-load validation
(docs/design/events.md section 5.1, section 7.2).

The rewritten output is exact, so the spec assertions are authored
observe-then-lock: the rewrite ran on representative templates, its real
(decoded) output was read, and that output is locked here. Error assertions
check message content, not just the exception type.
"""

import base64
import json
import re

import pytest

from citry import Citry, Component
from citry.ext.events.bindings import (
    BINDING_SPEC_ENCODING,
    DATA_CEV_ATTRS,
    DATA_CEV_BIND,
    DATA_CEV_ON,
    DATA_CEV_POLL,
    CevAttr,
)

_CID_RE = re.compile(r' data-cid(?:-\w+)?="[^"]*"')
_CEV_RE = re.compile(r'data-cev-(on|poll|bind)="([^"]*)"')

# A State-declaring component mints its state token at render, which needs a
# signing secret on the Citry instance.
SIGNING_KEY = "test-secret-key"


def _events_ext(app):
    return app.extensions.get_extension("events")


def _decode_cev(source):
    """Every ``data-cev-*`` attribute in ``source`` as ``(name, [specs])`` pairs, in order."""
    pairs = []
    for match in _CEV_RE.finditer(source):
        specs = json.loads(base64.b64decode(match.group(2)).decode())
        pairs.append((f"data-cev-{match.group(1)}", specs))
    return pairs


def _rendered(component):
    """Render to HTML with the per-render cid markers (the per-instance and the fixed-name form) stripped."""
    return _CID_RE.sub("", component.render().serialize())


def _noop(self):
    """A handler stub: a binding only needs its handler to exist, not to do anything."""
    return


class TestStageOneEveryForm:
    """Observe-then-lock the rewritten template for a template using every vocabulary form."""

    def _counter(self):
        app = Citry()

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
                "<span :c-name>x</span>"
                '<div @c-poll.30s="refresh">poll</div>'
                '<button @click="$state.count++" :class="{a: true}">plain</button>'
                "</div>"
            )

        return Counter

    def test_locked_specs(self):
        counter = self._counter()
        source = counter.get_template().source
        cid = counter.class_id
        assert _decode_cev(source) == [
            (
                DATA_CEV_ON,
                [
                    {
                        "cid": cid,
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
                    }
                ],
            ),
            (
                DATA_CEV_ON,
                [
                    {
                        "cid": cid,
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
                    }
                ],
            ),
            (
                DATA_CEV_BIND,
                [
                    {
                        "cid": cid,
                        "field": "count",
                        "mode": "two",
                        "handler": "refresh",
                        "lazy": False,
                        "on": None,
                        "key": None,
                        "debounce": 300,
                        "throttle": None,
                    }
                ],
            ),
            (
                DATA_CEV_BIND,
                [
                    {
                        "cid": cid,
                        "field": "name",
                        "mode": "one",
                        "handler": None,
                        "lazy": False,
                        "on": None,
                        "key": None,
                        "debounce": None,
                        "throttle": None,
                    }
                ],
            ),
            (
                DATA_CEV_POLL,
                [{"cid": cid, "handler": "refresh", "args": None, "interval": 30000}],
            ),
        ]

    def test_plain_alpine_attributes_survive(self):
        source = self._counter().get_template().source
        # The authored @c-*/:c-* syntax is gone, but plain Alpine passes through.
        assert "@c-click" not in source
        assert ":c-count" not in source
        assert '@click="$state.count++"' in source
        assert ':class="{a: true}"' in source

    def test_two_way_targets_collected(self):
        counter = self._counter()
        ext = _events_ext(counter.citry)
        counter.get_template()  # loading the template runs the stage-one scan
        assert ext.two_way_binding_targets(counter) == frozenset({"count"})


class TestStageOneVocabulary:
    """One form per test, so a regression points at the exact vocabulary item."""

    def _one(self, template, *, state=None, events):
        app = Citry()
        ns = {"citry": app, "template": template}
        if state is not None:
            ns["State"] = type("State", (), state)
        ns["Events"] = type("Events", (), events)
        comp = type("Comp", (Component,), ns)
        return comp.get_template().source

    def test_bare_event(self):
        source = self._one('<button @c-click="save">x</button>', events={"save": _noop})
        ((name, specs),) = _decode_cev(source)
        assert name == DATA_CEV_ON
        assert specs[0]["event"] == "click"
        assert specs[0]["handler"] == "save"
        assert specs[0]["args"] is None

    def test_event_modifiers(self):
        source = self._one('<button @c-keyup.enter.prevent.once="go">x</button>', events={"go": _noop})
        specs = _decode_cev(source)[0][1]
        assert specs[0]["event"] == "keyup"
        assert specs[0]["key"] == "enter"
        assert specs[0]["prevent"] is True
        assert specs[0]["once"] is True
        assert specs[0]["stop"] is False

    def test_debounce_bare_default_and_throttle(self):
        source = self._one('<button @c-click.debounce.throttle.1s="go">x</button>', events={"go": _noop})
        specs = _decode_cev(source)[0][1]
        assert specs[0]["debounce"] == 250  # bare .debounce default
        assert specs[0]["throttle"] == 1000  # .throttle.1s

    def test_bare_throttle_default(self):
        # Design 5.1 pins bare `.throttle` (no time segment) at 250 ms, the same
        # default as bare `.debounce`.
        source = self._one('<button @c-click.throttle="go">x</button>', events={"go": _noop})
        specs = _decode_cev(source)[0][1]
        assert specs[0]["throttle"] == 250
        assert specs[0]["debounce"] is None

    def test_bare_throttle_default_on_state_binding(self):
        # The same 250 ms default applies on the :c-* state channel (shared builder).
        source = self._one(
            '<input :c-q.throttle="go">',
            state={"__annotations__": {"q": str}, "q": ""},
            events={"go": _noop},
        )
        specs = _decode_cev(source)[0][1]
        assert specs[0]["throttle"] == 250
        assert specs[0]["debounce"] is None

    def test_handler_debounce_config_merges_when_binding_has_none(self):
        from citry.ext.events import event

        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                @event(debounce=500)
                def go(self):
                    return None

            template = '<button @c-click="go">x</button>'

        specs = _decode_cev(Comp.get_template().source)[0][1]
        # The handler's configured debounce fills in when the binding sets none.
        assert specs[0]["debounce"] == 500

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

        specs = _decode_cev(Comp.get_template().source)[0][1]
        assert specs[0]["debounce"] == 50

    def test_poll_interval_in_ms(self):
        source = self._one('<div @c-poll.5s="go">x</div>', events={"go": _noop})
        ((name, specs),) = _decode_cev(source)
        assert name == DATA_CEV_POLL
        assert specs[0]["interval"] == 5000

    def test_one_way_binding(self):
        source = self._one(
            "<span :c-title>x</span>",
            state={"__annotations__": {"title": str}, "title": ""},
            events={"h": _noop},
        )
        specs = _decode_cev(source)[0][1]
        assert specs[0]["mode"] == "one"
        assert specs[0]["field"] == "title"
        assert specs[0]["handler"] is None

    def test_two_way_on_override_and_key_filter(self):
        source = self._one(
            '<input :c-q.on:keyup.enter="go">',
            state={"__annotations__": {"q": str}, "q": ""},
            events={"go": _noop},
        )
        specs = _decode_cev(source)[0][1]
        assert specs[0]["mode"] == "two"
        assert specs[0]["on"] == "keyup"
        assert specs[0]["key"] == "enter"

    def test_field_case_preserved(self):
        # The rewrite is server-side, so a mixed-case State field name survives.
        source = self._one(
            "<span :c-docId>x</span>",
            state={"__annotations__": {"docId": int}, "docId": 0},
            events={"h": _noop},
        )
        assert _decode_cev(source)[0][1][0]["field"] == "docId"

    def test_multiple_event_bindings_on_one_element(self):
        source = self._one(
            '<input @c-focus="a" @c-blur="b">',
            events={"a": _noop, "b": _noop},
        )
        pairs = _decode_cev(source)
        assert len(pairs) == 1  # one data-cev-on attribute...
        assert [s["event"] for s in pairs[0][1]] == ["focus", "blur"]  # ...holding both specs


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

        specs = _decode_cev(Comp.get_template().source)[0][1]
        assert specs[0]["handler"] == "remove"
        assert specs[0]["args"] == "{id: $el.dataset.id}"

    def test_arg_expression_preserves_authored_inner_whitespace(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

            template = '<button @c-click="save(  {value: 1}  )">x</button>'

        specs = _decode_cev(Comp.get_template().source)[0][1]
        assert specs[0]["args"] == "  {value: 1}  "

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

        assert _decode_cev(Comp.get_template().source)[0][1][0]["args"] == expression

    def test_trailing_javascript_is_rejected_instead_of_truncated(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

            template = '<button @c-click="save({ok: true}); selected = false">x</button>'

        with pytest.raises(ValueError, match=r"must end at its final '\)' with no trailing text"):
            Comp.get_template()


class TestScannerRobustness:
    """The textual stage-one scanner handles awkward but valid tag shapes."""

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

        source = Comp.get_template().source
        # The `>` inside the quoted value must not be read as the tag's end.
        assert 'title="t"' in source
        assert _decode_cev(source)[0][1][0]["args"] == "{ok: a > b}"

    def test_nested_parens_in_arg_expression(self):
        app = Citry()

        class CmpIn:
            v: int = 0

        class Comp(Component):
            citry = app

            class Events:
                def f(self, data: CmpIn):
                    return None

            template = '<button @c-click="f({v: (1 + 2)})">x</button>'

        assert _decode_cev(Comp.get_template().source)[0][1][0]["args"] == "{v: (1 + 2)}"

    def test_self_closing_element_slash_preserved(self):
        app = Citry()

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            template = '<input :c-q="go" class="a"/>'

        source = Comp.get_template().source
        assert source.startswith("<input ")
        assert source.rstrip().endswith("/>")  # the self-closing slash survives
        assert 'class="a"' in source
        assert _decode_cev(source)[0][1][0]["field"] == "q"


class TestValidationErrors:
    """
    Each load error, with message content (design 5.1's error list). Every test
    also asserts the ``(in Comp template, line N)`` location suffix, so no
    error path can lose the template location.
    """

    def _load(self, template, *, state=None, events, child=False):
        app = Citry()
        if child:
            type("Child", (Component,), {"citry": app, "template": "x"})
        ns = {"citry": app, "template": template}
        if state is not None:
            ns["State"] = type("State", (), state)
        ns["Events"] = type("Events", (), events)
        comp = type("Comp", (Component,), ns)
        comp.get_template()
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
        comp = self._load('<c-Child @c-click="go" />', events={"go": _noop}, child=True)

        assert '@c-click="go"' in comp.get_template().source

    def test_component_state_binding_remains_invalid(self):
        with pytest.raises(
            ValueError, match=r"binds State on it.*\$c-props or Python kwargs.*\(in Comp template, line 1\)"
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
            self._load("<span :c-q>x</span>", events={"go": _noop})

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
                "<span :c-q.debounce.300ms>x</span>",
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

    def test_key_filter_on_non_keyboard_event(self):
        with pytest.raises(
            ValueError,
            match=r"key filter '\.enter' only applies to keyboard events, not 'click'.*\(in Comp template, line 1\)",
        ):
            self._load('<button @c-click.enter="go">x</button>', events={"go": _noop})

    def test_file_input_two_way(self):
        with pytest.raises(
            ValueError, match=r'<input type="file"> cannot be two-way bound.*\(in Comp template, line 1\)'
        ):
            self._load(
                '<input type="file" :c-q="go">',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )

    def test_custom_control_needs_on(self):
        with pytest.raises(
            ValueError,
            match=r"is not a known form control.*explicit update event via '\.on:.*\(in Comp template, line 1\)",
        ):
            self._load(
                '<my-widget :c-q="go"></my-widget>',
                state={"__annotations__": {"q": str}, "q": ""},
                events={"go": _noop},
            )


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

        out = _rendered(Comp())
        pairs = _decode_cev(out)
        assert "@c-click" not in out
        assert ":c-q" not in out
        on = next(specs for name, specs in pairs if name == DATA_CEV_ON)
        assert on[0]["event"] == "click"
        assert on[0]["prevent"] is True
        bind = next(specs for name, specs in pairs if name == DATA_CEV_BIND)
        assert bind[0]["mode"] == "two"
        assert bind[0]["field"] == "q"
        assert bind[0]["debounce"] == 250

    def test_spread_merges_with_literal_binding_on_same_element(self):
        app = Citry()

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

        out = _rendered(Comp())
        ((name, specs),) = _decode_cev(out)
        assert name == DATA_CEV_ON
        # The literal @c-click (stage one) and the spread @c-mouseover (stage
        # two) both survive in one merged attribute.
        assert [s["event"] for s in specs] == ["click", "mouseover"]
        assert [s["handler"] for s in specs] == ["a", "b"]

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

        with pytest.raises(ValueError, match=r"names event handler 'ghost'.*render-time attribute spread"):
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

        with pytest.raises(ValueError, match=r"'\.on:' needs an event name.*render-time attribute spread"):
            _rendered(Comp())


class TestCRawCaveat:
    def test_textual_rewrite_reaches_inside_c_raw(self):
        # Documented v1 caveat (design 5.1): the load-time rewrite is textual,
        # so it also matches binding-shaped text inside <c-raw>. This test pins
        # the current (imperfect) behavior as such: the binding IS rewritten.
        app = Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

            template = '<c-raw><button @c-click="save">x</button></c-raw>'

        source = Comp.get_template().source
        assert "@c-click" not in source  # the caveat: rewritten even inside c-raw
        ((name, specs),) = _decode_cev(source)
        assert name == DATA_CEV_ON
        assert specs[0]["handler"] == "save"


class TestComponentTagSpreadBoundary:
    """
    Component-boundary entries from a render-time spread follow A1's split.

    ``@c-*`` is captured as a component-tag client binding and remains absent from emitted
    HTML until the client work lands. ``:c-*`` is element-only and therefore
    fails at input resolution, just as its directly authored form fails while
    the template loads.
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

        render = Parent().render()
        graph = render.context.ownership
        assert graph is not None
        call = next(call for call in graph.snapshot().component_invocations if call.authored_tag == "child")
        client_binding = call.client_bindings[0]

        assert client_binding.source.value == "spread"
        assert client_binding.payload.type == "citry-dom-event"
        assert client_binding.payload.event == "click"
        assert client_binding.payload.handler == "go"
        assert "data-cev" not in render.serialize(deps_strategy="ignore")

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


class TestDynamicControlTypeCaveat:
    """
    Documented v1 caveat (design 5.1 "where the type is statically known"): the
    control-type load checks (a two-way ``<input type="file">``, ``.lazy`` on a
    control whose value already commits on ``change``) run only for a
    statically-known control type. When the type is contributed dynamically
    (``c-type`` / ``:type`` / ``c-bind``) it is unknown at load, so the checks
    are skipped, and a literal binding stage one already rewrote is not
    re-validated at render time. These tests pin that gap explicitly: the
    binding renders with no server-side error. (The statically-typed forms are
    still load errors; see ``TestValidationErrors.test_file_input_two_way`` and
    ``test_lazy_on_committed_input_type``.)
    """

    def _dynamic_type_component(self, resolved_type, binding):
        # The secret: a State-declaring component mints its token at render.
        app = Citry(secret=SIGNING_KEY)

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            def template_data(self, kwargs, slots):
                return {"t": resolved_type}

            template = f'<input c-type="t" {binding}>'

        return Comp

    def test_dynamic_type_file_two_way_not_caught(self):
        # A statically-written <input type="file"> two-way binding is a load
        # error; contributed via a dynamic c-type it is not caught server-side.
        comp = self._dynamic_type_component("file", ':c-q="go"')
        out = _rendered(comp())
        assert 'type="file"' in out  # the type resolved to file at render...
        ((name, specs),) = _decode_cev(out)  # ...and no server-side error was raised
        assert name == DATA_CEV_BIND
        assert specs[0]["mode"] == "two"
        assert specs[0]["field"] == "q"

    def test_dynamic_type_lazy_on_committed_control_not_caught(self):
        # `.lazy` on a statically-known checkbox is a load error; via a dynamic
        # c-type it passes with lazy recorded in the emitted spec.
        comp = self._dynamic_type_component("checkbox", ':c-q.lazy="go"')
        out = _rendered(comp())
        assert 'type="checkbox"' in out
        ((name, specs),) = _decode_cev(out)
        assert name == DATA_CEV_BIND
        assert specs[0]["lazy"] is True


class TestPassthrough:
    def test_plain_alpine_untouched(self):
        app = Citry()

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


class TestPublishedContract:
    """The compiled data-cev-* contract WP17 reads (a frozen constant + encoding)."""

    def test_enumerates_the_three_attributes(self):
        assert set(DATA_CEV_ATTRS) == {DATA_CEV_ON, DATA_CEV_POLL, DATA_CEV_BIND}

    def test_each_entry_describes_its_payload_keys(self):
        for name, entry in DATA_CEV_ATTRS.items():
            assert isinstance(entry, CevAttr)
            assert entry.name == name
            assert entry.payload_keys  # non-empty
            assert "cid" in entry.payload_keys

    def test_contract_matches_emitted_keys(self):
        # The constant must stay in step with what the builders emit.
        app = Citry()

        class Comp(Component):
            citry = app

            class State:
                q: str = ""

            class Events:
                def go(self, state):
                    return None

            template = '<input @c-keyup.enter="go" :c-q.debounce.300ms="go"><div @c-poll.5s="go">p</div>'

        emitted = dict(_decode_cev(Comp.get_template().source))
        for name, specs in emitted.items():
            assert set(specs[0]) == set(DATA_CEV_ATTRS[name].payload_keys)

    def test_encoding_is_documented_as_base64(self):
        assert "base64" in BINDING_SPEC_ENCODING.lower()

    def test_contract_is_frozen(self):
        with pytest.raises(TypeError):
            DATA_CEV_ATTRS["data-cev-new"] = None  # type: ignore[index]
