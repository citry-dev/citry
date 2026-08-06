"""
Tests for the events return channel (WP11): the action constructors
(docs/design/events.md 3.4), return-value coercion with result resolvers
(3.4, 6.2), the wire encoding of actions (4.3), ``EventError`` and the
validation-failure mapping (3.7), and the debug-mode tracking of
constructed-but-unreturned actions.

Exact-output assertions are authored observe-then-lock: the pipeline ran on
representative handler returns, the real encoded output was read, and that
output is locked here. Render ids are pinned by the conftest counter, so the
fragment HTML is byte-stable within a test.
"""

import logging
from types import SimpleNamespace

import pytest

from citry import Citry, Component
from citry.citry_render import CitryRender
from citry.ext.events import actions
from citry.ext.events.errors import EventError, invalid_args_error, wire_error
from citry.ext.events.results import (
    coerce_result,
    encode_actions,
    extract_download_result,
    track_constructed_actions,
    warn_unreturned_actions,
)
from citry.ext.events.schemas import validate_args

SIGNING_KEY = "test-secret-key"


def _mounted_citry():
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")
    return c


def _badge(c):
    """A plain component (no JS/CSS/Events), so its fragment HTML is just markup."""

    class Badge(Component):
        citry = c
        template = """
            <span class="badge">{{ count }}</span>
        """

        def template_data(self, kwargs, slots):
            return {"count": kwargs["count"]}

    return Badge


# What one Badge(count=N) fragment serializes to (observed; the conftest
# counter makes the first render of a test "c1").
def _badge_html(count):
    return f'\n            <span class="badge" data-cid-c1="">{count}</span>\n        '


def _citry_records(caplog):
    return [record for record in caplog.records if record.name == "citry"]


class TestActionConstructors:
    def test_field_defaults(self):
        c = _mounted_citry()
        render = actions.Render(_badge(c)(count=1))
        assert render.target is None
        assert render.swap == "morph"
        assert render.delay == 0
        assert render.wait is True
        dispatch = actions.Dispatch("saved")
        assert dispatch.detail is None
        redirect = actions.Redirect("/next", delay=5, wait=False)
        assert (redirect.url, redirect.delay, redirect.wait) == ("/next", 5, False)
        push = actions.PushUrl("?page=2", delay=0.25, wait=False)
        replace = actions.ReplaceUrl("#results")
        assert (push.url, push.delay, push.wait) == ("?page=2", 0.25, False)
        assert (replace.url, replace.delay, replace.wait) == ("#results", 0, True)

    def test_delay_and_wait_are_validated(self):
        with pytest.raises(ValueError, match="delay must be a finite, non-negative number of seconds"):
            actions.Data(1, delay=-1)
        with pytest.raises(ValueError, match="delay must be a finite, non-negative number of seconds"):
            actions.Data(1, delay="soon")
        with pytest.raises(ValueError, match="delay must be a finite, non-negative number of seconds"):
            actions.Data(1, delay=True)
        with pytest.raises(ValueError, match="delay must be a finite, non-negative number of seconds"):
            actions.Data(1, delay=float("nan"))
        with pytest.raises(ValueError, match="delay must be a finite, non-negative number of seconds"):
            actions.Data(1, delay=float("inf"))
        with pytest.raises(ValueError, match="delay must be a finite, non-negative number of seconds"):
            actions.Data(1, delay=10**400)
        with pytest.raises(ValueError, match="wait must be True or False"):
            actions.Data(1, wait="yes")

    def test_data_must_wait_to_resolve_the_caller(self):
        data = actions.Data(1, delay=0.25, wait=True)
        assert (data.delay, data.wait) == (0.25, True)
        with pytest.raises(
            ValueError,
            match=r"^actions\.Data: wait must be True because Data resolves the caller's promise; got False\.$",
        ):
            actions.Data(1, wait=False)

    def test_render_rejects_a_component_class(self):
        c = _mounted_citry()
        badge = _badge(c)
        # The natural first mistake: passing the class instead of calling it.
        with pytest.raises(ValueError, match=r"call it to build the element first: Badge\(\.\.\.\)"):
            actions.Render(badge)

    def test_render_rejects_non_elements(self):
        with pytest.raises(ValueError, match=r"component element .* or an already-rendered CitryRender"):
            actions.Render("<div>html</div>")

    def test_render_validates_target_and_swap(self):
        c = _mounted_citry()
        element = _badge(c)(count=1)
        with pytest.raises(ValueError, match="target must be a CSS selector string"):
            actions.Render(element, target="")
        with pytest.raises(ValueError, match="target must be a CSS selector string"):
            actions.Render(element, target=123)
        with pytest.raises(ValueError, match="HTML-case-safe render ID"):
            actions.Render(element, target="render:MixedCase")
        with pytest.raises(ValueError, match="swap must be one of"):
            actions.Render(element, swap="innerHTML")

    def test_dispatch_validates_the_name(self):
        with pytest.raises(ValueError, match="name must be a non-empty string"):
            actions.Dispatch("")
        with pytest.raises(ValueError, match="name must be a non-empty string"):
            actions.Dispatch(None)
        # citry:* is the runtime's own namespace (events.md 4.3).
        with pytest.raises(ValueError, match="reserved for the citry runtime"):
            actions.Dispatch("citry:boom")

    def test_redirect_validates_the_url(self):
        with pytest.raises(ValueError, match="url must be a non-empty string"):
            actions.Redirect("")

    def test_history_actions_validate_the_url(self):
        with pytest.raises(ValueError, match="url must be a non-empty string"):
            actions.PushUrl("")
        with pytest.raises(ValueError, match="url must be a non-empty string"):
            actions.ReplaceUrl(None)

    def test_download_defaults_and_is_frozen(self):
        download = actions.Download(b"csv,data", "report.csv")
        assert download.content == b"csv,data"
        assert download.filename == "report.csv"
        assert download.content_type == "application/octet-stream"
        with pytest.raises(AttributeError):
            download.filename = "other.csv"

    @pytest.mark.parametrize("content", [None, 1, bytearray(b"x")])
    def test_download_validates_content(self, content):
        with pytest.raises(ValueError, match="content must be str or bytes"):
            actions.Download(content, "report.csv")

    @pytest.mark.parametrize(
        ("filename", "message"),
        [
            ("", "non-empty string"),
            (" report.csv", "start or end with whitespace"),
            ("..", "must name a file"),
            ("reports/july.csv", "path separators"),
            ("reports\\july.csv", "path separators"),
            ("report\n.csv", "control or bidirectional"),
            ("report\u202e.csv", "control or bidirectional"),
            ("report\ud800.csv", "surrogate code points"),
        ],
    )
    def test_download_validates_filename(self, filename, message):
        with pytest.raises(ValueError, match=message):
            actions.Download(b"x", filename)

    @pytest.mark.parametrize("content_type", ["", "text/csv\nX-Injected: yes", "text/čsv"])
    def test_download_validates_content_type(self, content_type):
        with pytest.raises(ValueError, match="content_type"):
            actions.Download(b"x", "report.csv", content_type)

    @pytest.mark.parametrize(
        ("filename", "ascii_fallback"),
        [
            ("报告.csv", "download.csv"),
            ("报告", "download"),
            (".env", ".env"),
            (".报告.csv", ".download.csv"),
            ("报告.", "download"),
            (".报告.", ".download"),
            ("report.", "report"),
            ("report .", "report"),
            ("报告 .", "download"),
            (".报告 .", ".download"),
            (".报告 .csv", ".download.csv"),
            ("..报告 .csv", "..download.csv"),
        ],
    )
    def test_download_content_disposition_has_a_usable_ascii_fallback(self, filename, ascii_fallback):
        disposition = actions._download_content_disposition(filename)
        assert disposition.startswith(f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''")


class TestReturnCoercion:
    def test_download_is_a_response_result_not_an_action(self):
        download = actions.Download(b"x", "report.csv")
        assert extract_download_result(download, handler="export") is download
        assert extract_download_result([download], handler="export") is download
        assert extract_download_result((download,), handler="export") is download

    @pytest.mark.parametrize(
        "value",
        [
            [actions.Download(b"x", "one.csv"), actions.Data(None)],
            [actions.Download(b"x", "one.csv"), None],
            [actions.Download(b"x", "one.csv"), actions.Download(b"y", "two.csv")],
            [[actions.Download(b"x", "one.csv")]],
            {"file": actions.Download(b"x", "one.csv")},
        ],
    )
    def test_download_cannot_be_combined_or_nested(self, value):
        with pytest.raises(ValueError, match="only top-level list or tuple item"):
            extract_download_result(value, handler="export")

    def test_none_acknowledges_with_no_actions(self):
        assert coerce_result(None, handler="save") == []

    def test_an_action_passes_through_as_itself(self):
        action = actions.Data({"id": 17})
        coerced = coerce_result(action, handler="save")
        assert len(coerced) == 1
        assert coerced[0] is action

    def test_an_element_becomes_a_render_of_the_calling_instance(self):
        c = _mounted_citry()
        element = _badge(c)(count=1)
        coerced = coerce_result(element, handler="refresh")
        assert len(coerced) == 1
        render = coerced[0]
        assert isinstance(render, actions.Render)
        assert render.element is element
        assert render.target is None  # the calling instance
        assert render.swap == "morph"

    def test_a_citry_render_becomes_a_render_action(self):
        c = _mounted_citry()
        rendered = _badge(c)(count=1).render()
        assert isinstance(rendered, CitryRender)
        coerced = coerce_result(rendered, handler="refresh")
        assert isinstance(coerced[0], actions.Render)
        assert coerced[0].element is rendered

    def test_a_dict_becomes_a_data_action(self):
        value = {"count": 3}
        coerced = coerce_result(value, handler="add")
        assert isinstance(coerced[0], actions.Data)
        assert coerced[0].value is value

    def test_lists_and_tuples_coerce_each_element_in_order(self):
        c = _mounted_citry()
        element = _badge(c)(count=1)
        dispatch = actions.Dispatch("saved")
        coerced = coerce_result([{"a": 1}, dispatch, element], handler="save")
        assert [type(action) for action in coerced] == [actions.Data, actions.Dispatch, actions.Render]
        assert coerced[1] is dispatch
        # A tuple follows the same rules.
        assert [type(a) for a in coerce_result(({"a": 1},), handler="save")] == [actions.Data]

    def test_nested_lists_flatten_in_order(self):
        coerced = coerce_result(
            [actions.Dispatch("one"), [{"a": 1}, actions.Redirect("/two")]],
            handler="save",
        )
        assert [type(action) for action in coerced] == [actions.Dispatch, actions.Data, actions.Redirect]

    def test_none_inside_a_list_contributes_nothing(self):
        coerced = coerce_result([None, {"a": 1}, None], handler="save")
        assert [type(action) for action in coerced] == [actions.Data]

    def test_an_empty_list_acknowledges(self):
        assert coerce_result([], handler="save") == []

    def test_a_string_is_refused_never_guessed(self):
        with pytest.raises(ValueError, match=r"never guessed .*HTML or JSON.*actions\.Data\(\.\.\.\)") as err:
            coerce_result("<p>done</p>", handler="save")
        assert "'save'" in str(err.value)

    def test_other_values_are_refused_naming_data_and_resolvers(self):
        with pytest.raises(ValueError, match=r"actions\.Data\(\.\.\.\)"):
            coerce_result(42, handler="save")

        class Receipt:
            pass

        with pytest.raises(ValueError, match="register a result resolver for Receipt"):
            coerce_result(Receipt(), handler="save")


class _Model:
    """A stand-in for a user's own return type (say a Pydantic model)."""

    def __init__(self, payload):
        self.payload = payload


class _ModelResolver:
    """The design's resolver shape (events.md 6.2): claim _Model, decline the rest."""

    def __init__(self):
        self.seen = []

    def resolve(self, value, events):
        self.seen.append(value)
        if isinstance(value, _Model):
            return [actions.Data(value.payload)]
        return None


class TestResultResolvers:
    def test_a_resolver_claims_its_type(self):
        resolver = _ModelResolver()
        model = _Model({"id": 1})
        coerced = coerce_result(model, resolvers=[resolver], events=SimpleNamespace(), handler="save")
        assert isinstance(coerced[0], actions.Data)
        assert coerced[0].value == {"id": 1}
        assert resolver.seen == [model]

    def test_resolver_receives_the_events_instance(self):
        received = []

        class Recorder:
            def resolve(self, value, events):
                received.append(events)
                return [actions.Data(1)]

        events = SimpleNamespace()
        coerce_result(_Model(1), resolvers=[Recorder()], events=events, handler="save")
        assert received == [events]

    def test_builtins_run_before_resolvers(self):
        greedy_claims = []

        class Greedy:
            def resolve(self, value, events):
                greedy_claims.append(value)
                return [actions.Data("claimed")]

        c = _mounted_citry()
        element = _badge(c)(count=1)
        coerced = coerce_result(
            [{"a": 1}, element, None, actions.Dispatch("x")],
            resolvers=[Greedy()],
            handler="save",
        )
        # A greedy resolver never sees what the built-ins already mean:
        # the dict stayed Data, the element stayed Render, None stayed silent.
        assert greedy_claims == []
        assert [type(action) for action in coerced] == [actions.Data, actions.Render, actions.Dispatch]

    def test_the_first_claiming_resolver_wins(self):
        class Declines:
            def resolve(self, value, events):
                return None

        class ClaimsAsDispatch:
            def resolve(self, value, events):
                return [actions.Dispatch("model-note")]

        coerced = coerce_result(
            _Model(1),
            resolvers=[Declines(), _ModelResolver(), ClaimsAsDispatch()],
            handler="save",
        )
        # Declines passed; _ModelResolver claimed; ClaimsAsDispatch never ran.
        assert [type(action) for action in coerced] == [actions.Data]

    def test_an_empty_answer_still_claims(self):
        class Swallows:
            def resolve(self, value, events):
                return []

        assert coerce_result(_Model(1), resolvers=[Swallows()], handler="save") == []

    def test_resolvers_claim_elements_of_a_list(self):
        coerced = coerce_result(
            [{"n": 1}, _Model({"id": 2})],
            resolvers=[_ModelResolver()],
            handler="save",
        )
        assert [type(action) for action in coerced] == [actions.Data, actions.Data]
        assert coerced[1].value == {"id": 2}

    def test_an_unclaimed_value_still_errors(self):
        with pytest.raises(ValueError, match="cannot become an action"):
            coerce_result(42, resolvers=[_ModelResolver()], handler="save")

    def test_a_malformed_resolver_answer_is_refused(self):
        class AnswersBare:
            def resolve(self, value, events):
                return actions.Data(1)  # not wrapped in a list

        with pytest.raises(ValueError, match="Result resolver AnswersBare answered"):
            coerce_result(_Model(1), resolvers=[AnswersBare()], handler="save")

        class AnswersJunk:
            def resolve(self, value, events):
                return ["not-an-action"]

        with pytest.raises(ValueError, match="Result resolver AnswersJunk answered"):
            coerce_result(_Model(1), resolvers=[AnswersJunk()], handler="save")

    def test_a_resolver_cannot_synthesize_a_download(self):
        class AnswersDownload:
            def resolve(self, value, events):
                return [actions.Download(b"x", "report.csv")]

        with pytest.raises(ValueError, match="a resolver answers a list of actions"):
            coerce_result(_Model(1), resolvers=[AnswersDownload()], handler="save")


class TestEncodeActions:
    def test_locks_the_full_two_action_result(self):
        # The design's add_to_cart shape (events.md 3.4): a targeted render
        # plus a dict that resolves the caller's promise. Observed, then
        # locked byte for byte.
        c = _mounted_citry()
        badge = _badge(c)
        coerced = coerce_result(
            [
                actions.Render(badge(count=3), target="#cart-badge"),
                {"count": 3},
            ],
            handler="add_to_cart",
        )
        assert encode_actions(coerced, instance_id="c9zk1q00", handler="add_to_cart") == [
            {
                "action": "render",
                "target": "#cart-badge",
                "swap": "morph",
                "html": _badge_html(3),
            },
            {
                "action": "data",
                "value": {"count": 3},
            },
        ]

    def test_a_render_defaults_to_the_calling_instance(self):
        c = _mounted_citry()
        [encoded] = encode_actions(
            coerce_result(_badge(c)(count=1), handler="refresh"),
            instance_id="c0abc000",
            handler="refresh",
        )
        assert encoded["target"] == "render:c0abc000"
        assert encoded["html"] == _badge_html(1)

    def test_a_render_without_instance_or_target_is_refused(self):
        c = _mounted_citry()
        with pytest.raises(ValueError, match=r"no target.*Pass target=\.\.\."):
            encode_actions([actions.Render(_badge(c)(count=1))], instance_id=None, handler="poll")

    def test_a_render_of_an_events_component_carries_the_events_manifest(self):
        # The fragment serialize includes the fresh events manifest (WP10),
        # so a morphed-in component arrives with its state token.
        c = _mounted_citry()

        class LiveState:
            n: int = 0

        class Live(Component):
            citry = c
            State = LiveState

            class Events:
                def bump(self, state):
                    return None

            template = """
                <b>live</b>
            """

        [encoded] = encode_actions(
            [actions.Render(Live(n=1), target="#panel")],
            instance_id=None,
            handler="bump",
        )
        assert "data-citry-events" in encoded["html"]
        assert 'data-cid="c1"' in encoded["html"]

    def test_an_already_rendered_citry_render_is_serialized_as_is(self):
        c = _mounted_citry()
        rendered = _badge(c)(count=7).render()
        [encoded] = encode_actions(
            [actions.Render(rendered, target="#spot")],
            instance_id=None,
            handler="refresh",
        )
        assert encoded["html"] == _badge_html(7)

    def test_a_dispatch_is_self_addressed_at_encode_time(self):
        [encoded] = encode_actions(
            [actions.Dispatch("todo:added", {"id": 17})],
            instance_id="c9zk1q00",
            handler="add",
        )
        assert encoded == {
            "action": "event",
            "eventName": "todo:added",
            "detail": {"id": 17},
            "target": "render:c9zk1q00",
        }

    def test_an_instance_less_dispatch_targets_the_document(self):
        # No target field means the document (events.md 4.3: only
        # instance-less calls produce a document-targeted dispatch).
        [encoded] = encode_actions([actions.Dispatch("ping")], instance_id=None, handler="ping")
        assert encoded == {"action": "event", "eventName": "ping"}

    def test_delay_and_wait_ride_only_when_set(self):
        encoded = encode_actions(
            [
                actions.Data({"ok": True}, delay=0.125),
                actions.Dispatch("bye", delay=0.5),
                actions.Redirect("/next", delay=5, wait=False),
                actions.PushUrl("?page=2", delay=0.25, wait=False),
                actions.ReplaceUrl("#results"),
            ],
            instance_id=None,
            handler="save",
        )
        assert encoded == [
            {"action": "data", "value": {"ok": True}, "delay": 0.125},
            {"action": "event", "eventName": "bye", "delay": 0.5},
            {"action": "redirect", "url": "/next", "delay": 5, "wait": False},
            {"action": "url", "url": "?page=2", "mode": "push", "delay": 0.25, "wait": False},
            {"action": "url", "url": "#results", "mode": "replace"},
        ]

    def test_two_data_actions_are_an_encode_time_error(self):
        with pytest.raises(ValueError, match="at most one is allowed"):
            encode_actions(
                [actions.Data({"a": 1}), actions.Data({"b": 2})],
                instance_id=None,
                handler="save",
            )

    def test_two_bare_dicts_in_one_list_hit_the_same_error(self):
        # The coercion happily makes two Data actions; the encode step is
        # where the contradiction (which promise value wins?) is refused.
        coerced = coerce_result([{"a": 1}, {"b": 2}], handler="save")
        with pytest.raises(ValueError, match="which value would win"):
            encode_actions(coerced, instance_id=None, handler="save")

    def test_an_unknown_action_kind_is_refused(self):
        class Custom(actions.Action):
            pass

        with pytest.raises(ValueError, match="the action set is closed"):
            encode_actions([Custom()], instance_id=None, handler="save")


class TestRedirectWarnings:
    def test_actions_after_a_redirect_warn_and_keep_their_order(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        encoded = encode_actions(
            [
                actions.Redirect("/gone"),
                actions.Dispatch("bye"),
                actions.Data({"ok": True}),
            ],
            instance_id=None,
            handler="save",
        )
        # Never reordered, never dropped: the redirect stays first and both
        # trailing actions are encoded after it.
        assert [entry["action"] for entry in encoded] == ["redirect", "event", "data"]
        [record] = [record for record in _citry_records(caplog) if "action(s) after a redirect" in record.message]
        assert record.levelno == logging.DEBUG
        assert "'save'" in record.message
        assert "2 action(s) after a redirect" in record.message
        assert "race the navigation" in record.message

    def test_a_render_alongside_a_redirect_warns(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        c = _mounted_citry()
        encoded = encode_actions(
            [
                actions.Render(_badge(c)(count=1), target="#x"),
                actions.Redirect("/gone"),
            ],
            instance_id=None,
            handler="save",
        )
        assert [entry["action"] for entry in encoded] == ["render", "redirect"]
        [record] = [record for record in _citry_records(caplog) if "render together with a redirect" in record.message]
        assert "render together with a redirect" in record.message
        assert "never seen" in record.message

    def test_a_final_redirect_without_a_render_is_silent(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        encode_actions(
            [actions.Dispatch("bye"), actions.Redirect("/gone")],
            instance_id=None,
            handler="save",
        )
        assert not any("action(s) after a redirect" in record.message for record in _citry_records(caplog))

    def test_warnings_are_silent_without_debug_logging(self, caplog):
        caplog.set_level(logging.INFO, logger="citry")
        encode_actions(
            [actions.Redirect("/gone"), actions.Dispatch("bye")],
            instance_id=None,
            handler="save",
        )
        assert _citry_records(caplog) == []


class TestSelectorRenderContinuityWarning:
    def test_self_addressed_action_after_selector_render_warns_without_reordering(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        c = _mounted_citry()
        badge = _badge(c)
        encoded = encode_actions(
            [
                actions.Render(badge(count=1), target="#panel"),
                actions.Dispatch("saved"),
                actions.Render(badge(count=2)),
            ],
            instance_id="c9zk1q00",
            handler="save",
        )
        assert [entry["target"] for entry in encoded] == ["#panel", "render:c9zk1q00", "render:c9zk1q00"]
        [record] = [record for record in _citry_records(caplog) if "self-addressed action" in record.message]
        assert "2 self-addressed action(s) after a selector-targeted render" in record.message
        assert "retire or replace the calling instance" in record.message

    def test_non_risky_orderings_do_not_warn(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        c = _mounted_citry()
        badge = _badge(c)
        orderings = [
            [actions.Dispatch("saved"), actions.Render(badge(count=1), target="#panel")],
            [actions.Render(badge(count=2), target="#panel"), actions.Data({"ok": True})],
            [actions.Render(badge(count=3), target="render:other"), actions.Dispatch("saved")],
        ]
        for ordered_actions in orderings:
            encode_actions(ordered_actions, instance_id="c9zk1q00", handler="save")
        assert not any("self-addressed action" in record.message for record in _citry_records(caplog))


class TestEventError:
    def test_defaults_to_a_422_with_no_fields(self):
        error = EventError("Please fix the errors below.")
        assert error.message == "Please fix the errors below."
        assert error.fields == {}
        assert error.status == 422
        assert str(error) == "Please fix the errors below."

    def test_the_code_follows_the_status(self):
        assert EventError("x").code == "invalid_args"
        assert EventError("x", status=403).code == "forbidden"
        assert EventError("x", status=404).code == "not_found"
        assert EventError("x", status=409).code == "conflict"
        # Statuses without a dedicated code carry the generic one; the
        # status itself stays authoritative.
        assert EventError("x", status=418).code == "error"
        assert EventError("x", status=500).code == "error"

    def test_constructor_validation(self):
        with pytest.raises(ValueError, match="message must be a non-empty string"):
            EventError("")
        with pytest.raises(ValueError, match="status must be an HTTP error status"):
            EventError("x", status=200)
        with pytest.raises(ValueError, match="status must be an HTTP error status"):
            EventError("x", status=True)
        with pytest.raises(ValueError, match="fields must map field names to messages"):
            EventError("x", fields={"email": 5})
        with pytest.raises(ValueError, match="fields must map field names to messages"):
            EventError("x", fields="broken")

    def test_fields_are_copied(self):
        fields = {"email": "Enter a valid email address."}
        error = EventError("x", fields=fields)
        fields["email"] = "mutated"
        assert error.fields == {"email": "Enter a valid email address."}

    def test_wire_error_omits_empty_fields(self):
        assert wire_error(EventError("You cannot edit this document.", status=403)) == {
            "status": 403,
            "code": "forbidden",
            "message": "You cannot edit this document.",
        }

    def test_a_failed_validation_maps_to_the_422_object(self):
        # The WP9 validator's structured result becomes the same wire shape a
        # hand-raised EventError produces (observed, then locked).
        class CartIn:
            product_id: int

        result = validate_args(CartIn, {"product_id": "nope", "extra": 1})
        assert not result.ok
        assert wire_error(invalid_args_error(result)) == {
            "status": 422,
            "code": "invalid_args",
            "message": "Invalid event arguments.",
            "fieldErrors": {
                "extra": "Unexpected field: not declared on the schema.",
                "product_id": "Expected int, got str.",
            },
        }

    def test_invalid_args_error_refuses_a_successful_result(self):
        class CartIn:
            product_id: int

        result = validate_args(CartIn, {"product_id": 1})
        with pytest.raises(ValueError, match="this one succeeded"):
            invalid_args_error(result)


class TestDebugTracking:
    def test_an_unreturned_action_warns_naming_the_handler(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            kept = actions.Dispatch("saved")
            actions.Redirect("/never-returned")
            returned = coerce_result(kept, handler="save")
        warn_unreturned_actions(events, returned, "save")
        [record] = [r for r in _citry_records(caplog) if r.levelno == logging.WARNING]
        assert "'save'" in record.message
        assert "1 return value(s) that were never returned: Redirect" in record.message

    def test_returning_every_constructed_action_is_silent(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            returned = coerce_result(
                [actions.Dispatch("saved"), actions.Redirect("/next")],
                handler="save",
            )
        warn_unreturned_actions(events, returned, "save")
        assert [r for r in _citry_records(caplog) if r.levelno == logging.WARNING] == []

    def test_a_returned_download_is_tracked_without_a_warning(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            download = actions.Download(b"x", "report.csv")
        warn_unreturned_actions(events, [download], "export")
        assert [r for r in _citry_records(caplog) if r.levelno == logging.WARNING] == []

    def test_coercion_built_wrappers_are_counted_as_returned(self, caplog):
        # A returned dict constructs its Data action inside the tracked
        # block (during coercion); that wrapper must not read as dropped.
        caplog.set_level(logging.DEBUG, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            returned = coerce_result({"count": 3}, handler="add")
        warn_unreturned_actions(events, returned, "add")
        assert [r for r in _citry_records(caplog) if r.levelno == logging.WARNING] == []

    def test_an_identical_but_distinct_action_still_counts_as_unreturned(self, caplog):
        # Two equal Dispatch values are two constructed actions; returning
        # one must not mask dropping the other (the comparison is by
        # identity, not equality).
        caplog.set_level(logging.DEBUG, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            kept = actions.Dispatch("saved")
            actions.Dispatch("saved")
            returned = coerce_result(kept, handler="save")
        warn_unreturned_actions(events, returned, "save")
        [record] = [r for r in _citry_records(caplog) if r.levelno == logging.WARNING]
        assert "1 return value(s) that were never returned: Dispatch" in record.message

    def test_tracking_is_off_without_debug_logging(self, caplog):
        caplog.set_level(logging.INFO, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            actions.Redirect("/never-returned")
        assert not hasattr(events, "_constructed_actions")
        warn_unreturned_actions(events, [], "save")
        assert _citry_records(caplog) == []

    def test_construction_outside_the_block_is_not_tracked(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        events = SimpleNamespace()
        with track_constructed_actions(events):
            pass
        actions.Dispatch("after-the-call")
        assert events._constructed_actions == []

    def test_a_none_events_instance_disables_tracking(self, caplog):
        caplog.set_level(logging.DEBUG, logger="citry")
        with track_constructed_actions(None):
            actions.Dispatch("unowned")
        warn_unreturned_actions(None, [], "save")
        assert _citry_records(caplog) == []
