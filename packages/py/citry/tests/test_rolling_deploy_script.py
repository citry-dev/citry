"""
Tests for how the rolling-deploy release check judges what it sees.

The check itself installs two citry releases and runs only in release
qualification. These tests feed its decisions synthetic pages, answers and
PyPI data, so the rules (which deploys are promised, which answers count as
the documented out-of-date answer, and what a success must show) are proved
without a network or a second release.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from scripts.rolling_deploy import check

CONTRACT = "a" * 64
OTHER_CONTRACT = "b" * 64


def _page() -> check.Page:
    return check.Page(
        script_urls=["/citry/citry.0123.js"],
        definitions=[("/citry/ext/events/definitions/0123.js", "c" * 64)],
        helper_contracts={CONTRACT},
        app_id="app",
        revision=0,
        occurrence_id="occurrence",
        component_class_id="Counter_abc",
        render_id="r1",
        state_token="cev1.token",  # noqa: S106 - an opaque test value
    )


def _answer(result: dict[str, Any], *, status: int = 200, request_id: str = "req") -> dict[str, Any]:
    body = {"protocol": "citry-events/1", "requestId": request_id, "results": [result]}
    return {"status": status, "body": json.dumps(body)}


# The pages start at START_COUNT, so the first click shows one more and the
# second two more.
FIRST = check.START_COUNT + 1
SECOND = check.START_COUNT + 2


def _shown(count: int) -> str:
    return f"rolling-count-{count}"


def _render(contract: str, *, shown: str = _shown(FIRST), token: str = "cev1.next") -> dict[str, Any]:  # noqa: S107 - an opaque test value
    # The shape of a Vue render: the shown text sits in the render data under
    # a name the release's compiler chose, beside the protocol's Events record.
    occurrence = {
        "id": "occurrence",
        "preparedData": {"citryText0": shown},
        "eventContext": {"serverRenderId": "r2", "stateToken": token, "componentClassId": "Counter_abc"},
    }
    prepared = {
        "appId": "app",
        "revision": 1,
        "definitions": [{"id": "d", "helperContract": contract}],
        "occurrences": [occurrence],
    }
    return {"action": "render", "renderer": "vue-prepared/1", "prepared": prepared}


def _judge(
    answer: dict[str, Any],
    *,
    page_reports_out_of_date: bool = True,
    expected_count: int = FIRST,
    send_sequence: int = 1,
) -> check.Outcome:
    report = check.Report(previous="1.0.0", candidate="1.1.0", promised=True)
    status = check.judge_event_answer(
        report,
        "call",
        _page(),
        "req",
        answer,
        page_reports_out_of_date=page_reports_out_of_date,
        expected_count=expected_count,
        send_sequence=send_sequence,
    )
    [outcome] = report.outcomes
    assert status == outcome.status
    return outcome


@pytest.mark.parametrize(
    ("previous", "candidate", "promised"),
    [
        ("1.0.0", "1.1.0", True),
        ("1.4.2", "1.4.3", True),
        # A deploy from 0.x starts fresh, and a major release may break pages.
        ("0.9.0", "1.0.0", False),
        ("0.9.0", "0.9.1", False),
        ("1.9.0", "2.0.0", False),
        ("1.0.0", "1.1.0rc1", False),
    ],
)
def test_only_deploys_within_one_major_release_from_1_on_are_promised(
    previous: str, candidate: str, promised: bool
) -> None:
    assert check.deploy_is_promised(previous, candidate) is promised


def test_previous_release_is_the_newest_final_unyanked_release_before_the_candidate() -> None:
    file = [{"yanked": False}]
    releases = {
        "0.9.0": file,
        "1.0.0": file,
        "1.1.0": [{"yanked": True}],
        "1.1.0rc1": file,
        "1.2.0": file,
        "1.0.1": [],
    }
    assert check.pick_previous(releases, "1.2.0") == "1.0.0"
    assert check.pick_previous(releases, "1.3.0") == "1.2.0"
    with pytest.raises(SystemExit, match="no citry release older"):
        check.pick_previous(releases, "0.1.0")


def test_a_success_whose_render_the_old_page_can_apply_is_ok() -> None:
    outcome = _judge(_answer({"ok": True, "sendSequence": 1, "actions": [_render(CONTRACT)]}))
    assert outcome.status == "ok"


def test_stale_state_is_the_documented_out_of_date_answer_whatever_the_http_status() -> None:
    error = {"status": 409, "code": "stale_state", "message": "stale"}
    # The call route answers 200 with a per-call error; a single-call route answers 409.
    for status in (200, 409):
        assert _judge(_answer({"ok": False, "sendSequence": 1, "error": error}, status=status)).status == "stale"


def test_any_other_error_fails() -> None:
    error = {"status": 403, "code": "invalid_state", "message": "invalid"}
    outcome = _judge(_answer({"ok": False, "sendSequence": 1, "error": error}, status=403))
    assert outcome.status == "fail"
    assert "invalid_state" in outcome.detail


@pytest.mark.parametrize(
    "answer",
    [
        {"status": 500, "body": "Internal Server Error"},
        _answer({"ok": True, "sendSequence": 1, "actions": [_render(CONTRACT)]}, request_id="another"),
        _answer({"ok": True, "sendSequence": 2, "actions": [_render(CONTRACT)]}),
    ],
)
def test_an_answer_that_is_not_a_result_for_this_call_fails(answer: dict[str, Any]) -> None:
    assert _judge(answer).status == "fail"


@pytest.mark.parametrize(
    ("shown", "detail"),
    [
        # The handler did not run, or ran on State that was not the page's.
        # 1 is what a fresh default State would show after one click.
        (_shown(1), f"shows 1, not {FIRST}"),
        (_shown(check.START_COUNT), f"shows {check.START_COUNT}, not {FIRST}"),
        (_shown(SECOND), f"shows {SECOND}, not {FIRST}"),
        ("nothing to see", f"shows no count, not {FIRST}"),
    ],
)
def test_a_success_whose_render_shows_the_wrong_count_fails(shown: str, detail: str) -> None:
    outcome = _judge(_answer({"ok": True, "sendSequence": 1, "actions": [_render(CONTRACT, shown=shown)]}))
    assert outcome.status == "fail"
    assert detail in outcome.detail


def test_a_render_that_shows_two_counts_fails() -> None:
    actions = [_render(CONTRACT), _render(CONTRACT, shown=_shown(SECOND))]
    assert _judge(_answer({"ok": True, "sendSequence": 1, "actions": actions})).status == "fail"


def test_the_count_is_found_in_an_html_render_too() -> None:
    html_render = {"action": "render", "renderer": "html-fragment/1", "html": f"<button>{_shown(FIRST)}</button>"}
    outcome = _judge(_answer({"ok": True, "sendSequence": 1, "actions": [html_render]}))
    assert outcome.status == "ok"


def test_a_second_call_must_show_the_count_after_both_calls() -> None:
    # A store that kept the old count would make the second call show 1 again.
    stale_store = _answer({"ok": True, "sendSequence": 2, "actions": [_render(CONTRACT)]})
    assert _judge(stale_store, expected_count=SECOND, send_sequence=2).status == "fail"
    updated = _answer({"ok": True, "sendSequence": 2, "actions": [_render(CONTRACT, shown=_shown(SECOND))]})
    assert _judge(updated, expected_count=SECOND, send_sequence=2).status == "ok"


def test_the_next_click_carries_the_state_and_render_id_the_answer_returned() -> None:
    next_page = check.follow_up_page(_page(), [_render(CONTRACT, token="ces1.new-pointer")])  # noqa: S106
    assert next_page is not None
    assert (next_page.state_token, next_page.render_id, next_page.revision) == ("ces1.new-pointer", "r2", 1)
    # An answer with no Events record for this component class gives the page nothing to send.
    other_class = _render(CONTRACT)
    other_class["prepared"]["occurrences"][0]["eventContext"]["componentClassId"] = "Other_def"
    assert check.follow_up_page(_page(), [other_class]) is None


def test_a_refreshed_token_in_a_state_action_is_used_too() -> None:
    # The protocol lets a release send the new token in a `state` action
    # aimed at the caller instead of in the render's Events record.
    state_action = {"action": "state", "targetRenderId": "r1", "stateToken": "cev1.from-state", "publicState": {}}
    next_page = check.follow_up_page(_page(), [state_action])
    assert next_page is not None
    assert (next_page.state_token, next_page.render_id, next_page.revision) == ("cev1.from-state", "r1", 0)
    aimed_elsewhere = {**state_action, "targetRenderId": "someone-else"}
    assert check.follow_up_page(_page(), [aimed_elsewhere]) is None


def test_a_wrong_count_fails_even_when_the_render_uses_other_helpers() -> None:
    # The count is checked first: a page that would report itself out of date
    # does not excuse a handler that ran on the wrong State.
    answer = _answer({"ok": True, "sendSequence": 1, "actions": [_render(OTHER_CONTRACT, shown=_shown(1))]})
    assert _judge(answer, page_reports_out_of_date=True).status == "fail"


def test_a_second_call_is_skipped_after_stale_state_or_a_failure() -> None:
    report = check.Report(previous="1.0.0", candidate="1.1.0", promised=True)
    pages = {"signed": _page(), "stored": _page(), "other": _page()}
    answers = {
        "event:signed": _answer({"ok": True, "sendSequence": 1, "actions": [_render(CONTRACT)]}),
        "event:stored": {"status": 409, "body": "{}"},
        "event:other": {"status": 500, "body": "boom"},
    }
    next_pages, requests = check.plan_second_calls(
        report, "dir", pages, answers, {"signed": "ok", "stored": "stale", "other": "fail"}
    )
    details = {outcome.name: outcome.detail for outcome in report.outcomes}
    # A render with other helpers also leaves the page out of date, so the
    # reason does not claim stale_state.
    assert "left the page out of date" in details["dir: second event call, stored State"]
    assert "failed" in details["dir: second event call, other State"]
    assert list(next_pages) == ["signed"]
    call = json.loads(requests["event:signed"]["body"])["calls"][0]
    assert (call["stateToken"], call["callerRenderId"], call["sendSequence"]) == ("cev1.next", "r2", 2)
    assert requests["event:signed"]["headers"]["X-Citry-Vue-Revision"] == "1"
    statuses = {outcome.name: outcome.status for outcome in report.outcomes}
    assert statuses == {"dir: second event call, stored State": "skip", "dir: second event call, other State": "skip"}
    assert not report.failed


def test_a_render_with_other_helpers_is_stale_only_where_the_old_page_reports_it() -> None:
    answer = _answer({"ok": True, "sendSequence": 1, "actions": [_render(OTHER_CONTRACT)]})
    assert _judge(answer, page_reports_out_of_date=True).status == "stale"
    assert _judge(answer, page_reports_out_of_date=False).status == "fail"


def test_old_page_records_are_found_in_its_vue_app_data() -> None:
    manifest = {
        "appId": "app-1",
        "revision": 0,
        "definitions": [{"url": "/citry/ext/events/definitions/x.js", "sha256": "d" * 64, "helperContract": CONTRACT}],
        "occurrences": [
            {
                "id": "occ-1",
                "eventContext": {"componentClassId": "C_1", "serverRenderId": "r9", "stateToken": "cev1.t"},
            }
        ],
    }
    block = json.dumps({"manifest": manifest})
    page = (
        '<div id="host"></div><script src="/citry/citry.abc.js"></script>'
        '<script src="https://cdn.example/other.js"></script>'
        f'<script type="application/json" data-citry-vue-document="app-1">{block}</script>'
    )
    old = check.read_page(page)
    assert old.script_urls == ["/citry/citry.abc.js"]
    assert old.definitions == [("/citry/ext/events/definitions/x.js", "d" * 64)]
    assert old.helper_contracts == {CONTRACT}
    assert (old.app_id, old.occurrence_id, old.component_class_id, old.render_id, old.state_token) == (
        "app-1",
        "occ-1",
        "C_1",
        "r9",
        "cev1.t",
    )
    call = json.loads(check.event_call(old, "req")["body"])
    assert call["calls"][0]["stateToken"] == "cev1.t"


def test_a_page_without_events_records_stops_the_check() -> None:
    with pytest.raises(SystemExit, match="update read_page"):
        check.read_page("<p>no app</p>")


def test_cached_renders_are_compared_without_their_render_ids() -> None:
    assert check.same_markup('<p data-cid-abc1="">x</p>', '<p data-cid-zz9="">x</p>')
    assert not check.same_markup('<p data-cid-abc1="">x</p>', '<p data-cid-abc1="">y</p>')


def test_a_served_file_must_be_the_one_the_page_expects() -> None:
    digest = "e" * 64
    report = check.Report(previous="1.0.0", candidate="1.1.0", promised=True)
    check.judge_file(report, "same", {"status": 200, "sha256": digest}, digest)
    check.judge_file(report, "other bytes", {"status": 200, "sha256": "f" * 64}, digest)
    check.judge_file(report, "missing", {"status": 404, "sha256": digest}, digest)
    assert [outcome.status for outcome in report.outcomes] == ["ok", "fail", "fail"]
    assert check.runtime_digest(f"/citry/citry.{digest}.js") == digest
    assert check.runtime_digest("/citry/citry.js") == ""


@pytest.mark.parametrize(("previous", "exit_code"), [("1.0.0", 1), ("0.9.0", 0)])
def test_a_stage_that_cannot_run_fails_only_a_promised_deploy(
    previous: str, exit_code: int, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken(*_args: object) -> None:
        msg = "scenario.py uses a renamed API"
        raise SystemExit(msg)

    monkeypatch.setattr(check, "check", broken)
    wheel = tmp_path / "citry-1.1.0-py3-none-any.whl"
    argv = ["check.py", "--previous", previous, "--candidate", str(wheel), "--keep", str(tmp_path / "work")]
    monkeypatch.setattr("sys.argv", argv)
    assert check.main() == exit_code
    assert "the check could not finish: scenario.py uses a renamed API" in capsys.readouterr().out
