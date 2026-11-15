"""
Tests for how the rolling-deploy release check judges what it sees.

The check itself installs two citry releases and runs only in release
qualification. These tests feed its decisions synthetic pages, answers and
PyPI data, so the rules (which deploys are promised, which answers count as
the documented reload) are proved without a network or a second release.
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


def _render(contract: str) -> dict[str, Any]:
    prepared = {"definitions": [{"id": "d", "helperContract": contract}]}
    return {"action": "render", "renderer": "vue-prepared/1", "prepared": prepared}


def _judge(answer: dict[str, Any], *, page_offers_reload: bool = True) -> check.Outcome:
    report = check.Report(previous="1.0.0", candidate="1.1.0", promised=True)
    check.judge_event_answer(report, "call", _page(), "req", answer, page_offers_reload=page_offers_reload)
    [outcome] = report.outcomes
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


def test_stale_state_is_the_documented_reload_whatever_the_http_status() -> None:
    error = {"status": 409, "code": "stale_state", "message": "stale"}
    # The call route answers 200 with a per-call error; a single-call route answers 409.
    for status in (200, 409):
        assert _judge(_answer({"ok": False, "sendSequence": 1, "error": error}, status=status)).status == "reload"


def test_any_other_error_fails() -> None:
    error = {"status": 403, "code": "invalid_state", "message": "invalid"}
    outcome = _judge(_answer({"ok": False, "sendSequence": 1, "error": error}, status=403))
    assert outcome.status == "fail"
    assert "invalid_state" in outcome.detail


@pytest.mark.parametrize(
    "answer",
    [
        {"status": 500, "body": "Internal Server Error"},
        _answer({"ok": True, "sendSequence": 1, "actions": []}, request_id="another"),
        _answer({"ok": True, "sendSequence": 2, "actions": []}),
    ],
)
def test_an_answer_that_is_not_a_result_for_this_call_fails(answer: dict[str, Any]) -> None:
    assert _judge(answer).status == "fail"


def test_a_render_with_other_helpers_counts_as_a_reload_only_where_the_old_page_offers_one() -> None:
    answer = _answer({"ok": True, "sendSequence": 1, "actions": [_render(OTHER_CONTRACT)]})
    assert _judge(answer, page_offers_reload=True).status == "reload"
    assert _judge(answer, page_offers_reload=False).status == "fail"


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
