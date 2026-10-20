"""The scoring logic is the part most likely to go wrong quietly, so it is tested on made-up tool output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from citry_errors import html_report, report
from citry_errors.config import ConfigError, load_port
from citry_errors.parsers import (
    Finding,
    ToolUnavailable,
    citry_json,
    djlint,
    eslint_json,
    exit_status,
    pyright_json,
    ruff_json,
    tsc,
)
from citry_errors.runtime import Observation, _normal, compare, problems
from citry_errors.score import RuntimeResult, StageResult, earliest, new_findings, score_stage

WORK = Path("/cache/envs/next/work/m02-input-name")


def test_tsc_reads_both_layouts_and_next_build_errors() -> None:
    out = "\n".join(
        [
            "app/page.tsx(12,5): error TS2322: Type 'string' is not assignable to type 'number'.",
            f"{WORK}/app/card.tsx:3:1 - error TS2304: Cannot find name 'titel'.",
            "./app/page.tsx:20:7",
            "Type error: Property 'nmae' does not exist on type 'Owner'.",
        ]
    )
    findings = tsc(out, "", 1, WORK)
    assert [(f.file, f.line, f.code) for f in findings] == [
        ("app/page.tsx", 12, "TS2322"),
        ("app/card.tsx", 3, "TS2304"),
        ("app/page.tsx", 20, "build"),
    ]


def test_a_failing_command_without_diagnostics_is_one_unlocated_error() -> None:
    assert tsc("", "Build failed", 1, WORK) == [Finding(None, None, "error", "exit-1", "Build failed")]
    assert exit_status("ok", "", 0, WORK) == []


def test_citry_json_keeps_location_severity_and_import_failures() -> None:
    payload = {
        "app_failure": None,
        "findings": [
            {
                "origin": f"{WORK}/app.py:30:9",
                "code": "citry.template.unknown-variable",
                "severity": "error",
                "message": "Unknown variable 'ownr'",
                "range": {"start": {"line": 30, "column": 9}},
            },
            {
                "origin": "app.py",
                "code": "citry.template.invalid-attribute-value",
                "severity": "warning",
                "message": "x",
                "range": None,
            },
        ],
    }
    findings = citry_json(json.dumps(payload), "", 1, WORK)
    assert [(f.file, f.line, f.severity) for f in findings] == [("app.py", 30, "error"), ("app.py", None, "warning")]
    failed = citry_json(json.dumps({"app_failure": "ImportError: boom", "findings": []}), "", 2, WORK)
    assert failed == [Finding(None, None, "error", "citry.app-failure", "ImportError: boom")]


def test_pyright_lines_are_made_one_based() -> None:
    payload = {
        "generalDiagnostics": [
            {
                "file": f"{WORK}/main.py",
                "severity": "warning",
                "rule": "reportUndefinedVariable",
                "message": '"Crad" is not defined',
                "range": {"start": {"line": 4}},
            }
        ]
    }
    assert pyright_json(json.dumps(payload), "", 0, WORK) == [
        Finding("main.py", 5, "warning", "reportUndefinedVariable", '"Crad" is not defined')
    ]


def test_only_findings_at_the_change_count_unless_the_case_confirms_an_indirect_one() -> None:
    known = Finding("app.py", 3, "warning", "x", "already there")
    moved = Finding("app.py", 9, "warning", "x", "already there")
    near = Finding("app.py", 21, "error", "y", "new and near")
    far = Finding("app.py", 80, "error", "y", "new, end of file")
    other_file = Finding("page.vue", 20, "error", "z", "new, where the value is used")
    assert new_findings([known], [moved, near]) == [near]
    result = score_stage("editor", "pyright", [known], [moved, near, far, other_file], "app.py", 20, 3)
    assert (result.error, result.evidence, result.indirect) == (True, [near], [])
    assert result.unconfirmed == [far, other_file]
    # A note accepts only the codes it names: `z` counts, `y` stays unconfirmed.
    elsewhere = score_stage("editor", "vue-tsc", [], [far, other_file], "app.py", 20, 3, ("z",))
    assert not elsewhere.error
    assert (elsewhere.indirect_error, elsewhere.indirect, elsewhere.unconfirmed) == (True, [other_file], [far])
    assert earliest([elsewhere], RuntimeResult(), count_warnings=False) == "never"
    assert earliest([elsewhere], RuntimeResult(), count_warnings=False, accept_indirect=True) == "editor"


def test_a_failure_without_a_location_counts_only_when_it_names_the_changed_file() -> None:
    named = Finding(None, None, "error", "exit-1", "SyntaxError in app/card.tsx")
    unrelated = Finding(None, None, "error", "exit-1", "fetch failed: ENOTFOUND registry.npmjs.org")
    result = score_stage("build", "next build", [], [named, unrelated], "app/card.tsx", 4, 3)
    assert (result.evidence, result.unconfirmed) == ([named], [unrelated])


def test_an_indirect_note_needs_a_reason_and_codes(tmp_path: Path) -> None:
    (tmp_path / "page.tsx").write_text("titel=\n")
    port = tmp_path / "port.toml"
    head = (
        'status = "ported"\nfiles = { "page.tsx" = "page.tsx" }\n'
        'mistake = { file = "page.tsx", contains = "titel=" }\n'
    )
    port.write_text(head + '[indirect]\nreason = "why"\ncodes = []\n')
    with pytest.raises(ConfigError, match="needs both a reason and at least one code"):
        load_port(port)
    port.write_text(head + '[indirect]\nreason = "why"\ncodes = ["TS2322"]\n')
    assert load_port(port).indirect_codes == ("TS2322",)


def test_a_case_lands_in_the_first_of_the_five_buckets_it_reaches() -> None:
    def record(strict: str, lenient: str) -> dict:
        return {"status": "ported", "strict": strict, "lenient": lenient, "stages": []}

    assert report.bucket(record("editor", "editor")) == "static-error"
    # A warning before running beats an error at runtime: it came earlier.
    assert report.bucket(record("runtime-error", "check")) == "static-warning"
    assert report.bucket(record("runtime-error", "runtime-error")) == "runtime-error"
    assert report.bucket(record("never", "runtime-warning")) == "runtime-warning"
    # A miss is a miss, whether or not the page changed.
    assert report.bucket(record("silent", "silent")) == "missed"
    assert report.bucket(record("never", "never")) == "missed"
    assert report.bucket(record("not-run", "not-run")) is None
    assert report.bucket({"status": "not-applicable"}) is None
    assert report.cell(record("never", "editor")) == "Ew, M"
    assert report.cell(record("check", "check") | {"indirect": "why"}) == "C°"


def test_published_evidence_drops_local_folders_and_long_tails() -> None:
    text = report._public(f"build: {report.REPO_ROOT}/.benchmarks/errors/x.vue " + "y" * 400)
    assert str(report.REPO_ROOT) not in text
    assert text.startswith("build: .benchmarks/errors/x.vue")
    assert len(text) == 300


def test_paths_relative_to_a_parent_folder_are_mapped_to_the_working_copy() -> None:
    findings = tsc("./work/m02-input-name/app/card.tsx:22:1\nParsing ecmascript source code failed", "", 1, WORK)
    assert [(f.file, f.line) for f in findings] == [("app/card.tsx", 22)]


def test_earliest_stage_follows_the_developer_order_and_the_warning_policy() -> None:
    warn_in_editor = StageResult("editor", "e", warning=True)
    error_in_build = StageResult("build", "b", error=True)
    assert earliest([warn_in_editor, error_in_build], None, count_warnings=False) == "build"
    assert earliest([warn_in_editor, error_in_build], None, count_warnings=True) == "editor"
    quiet = [StageResult("editor", "e")]
    assert earliest(quiet, RuntimeResult(warning=True, output_differs=True), count_warnings=True) == "runtime-warning"
    assert earliest(quiet, RuntimeResult(warning=True, output_differs=True), count_warnings=False) == "silent"
    assert earliest(quiet, RuntimeResult(), count_warnings=False) == "never"
    assert earliest(quiet, RuntimeResult(started=False), count_warnings=False) == "runtime-error"


def test_runtime_comparison_ignores_noise_already_in_the_clean_app() -> None:
    snapshot = {"text": "Saved: 1", "elements": []}
    clean = Observation(snapshot=snapshot, console_warnings=["devtools hint 123"], server_log=["GET / 200 4ms"])
    same = Observation(snapshot=snapshot, console_warnings=["devtools hint 456"], server_log=["GET / 200 9ms"])
    assert compare(clean, same) == RuntimeResult()
    broken = Observation(
        snapshot={"text": "Saved: 0", "elements": []},
        server_log=["GET / 200 4ms", "POST /sav 404"],
        bad_responses=["404 http://127.0.0.1:1/sav"],
    )
    result = compare(clean, broken)
    assert result.error
    assert result.output_differs


def test_a_port_must_say_why_it_is_not_ported(tmp_path: Path) -> None:
    path = tmp_path / "m01-component-name" / "jinja" / "port.toml"
    path.parent.mkdir(parents=True)
    path.write_text('status = "not-applicable"\n')
    with pytest.raises(ConfigError, match="needs a reason"):
        load_port(path)
    path.write_text(
        'status = "ported"\nfiles = { "app.py" = "app.py" }\nmistake = { file = "app.py", contains = "x" }\n'
    )
    with pytest.raises(ConfigError, match="missing file"):
        load_port(path)
    path.write_text('status = "ported"\nunknown = 1\n')
    with pytest.raises(ConfigError, match="unknown keys"):
        load_port(path)


def test_a_timed_out_stage_neither_catches_nor_misses() -> None:
    result = score_stage("build", "next build", [], None, "app/page.tsx", 3, 3)
    assert result.timed_out
    assert not result.error


def test_a_difference_visible_only_before_the_clicks_still_counts() -> None:
    after = {"text": "Details are visible", "elements": []}
    clean = Observation(snapshot_loaded={"text": "", "elements": []}, snapshot=after)
    shown_too_early = Observation(snapshot_loaded=after, snapshot=after)
    assert compare(clean, shown_too_early).output_differs


def test_inline_template_findings_map_to_their_python_file_line(tmp_path: Path) -> None:
    work = tmp_path / "work" / "m07-undefined-variable"
    module = work / "app" / "components"
    module.mkdir(parents=True)
    (module / "board_page.py").write_text(
        'class Other:\n    template = """x"""\n\n\n'
        'class BoardPage:\n    template = """\n      <p>{{ ownr.name }}</p>\n    """\n'
    )
    payload = {
        "findings": [
            {
                "origin": "app.components.board_page.BoardPage.template",
                "code": "citry.template.unknown-variable",
                "severity": "error",
                "message": "Template variable 'ownr' is not available in this template.",
                "range": {"start": {"line": 2, "column": 10}},
            }
        ]
    }
    [finding] = citry_json(json.dumps(payload), "", 1, work)
    assert (finding.file, finding.line) == ("app/components/board_page.py", 7)


def test_a_type_check_that_did_not_run_has_no_verdict() -> None:
    payload = {"findings": [], "notes": ["--types did not run TypeScript or ty; it needs an app"], "exit_code": 0}
    with pytest.raises(ToolUnavailable):
        citry_json(json.dumps(payload), "", 0, WORK)


def test_a_server_error_status_is_not_mistaken_for_the_clean_apps_success() -> None:
    clean = Observation(server_log=['"GET / HTTP/1.1" 200 4512'])
    failing = Observation(server_log=['"GET / HTTP/1.1" 500 145'])
    assert compare(clean, failing).error
    assert not compare(clean, Observation(server_log=['"GET / HTTP/1.1" 200 4498'])).error


def test_a_response_size_is_not_read_as_a_server_error() -> None:
    clean = Observation(server_log=['"GET /static/a.js HTTP/1.1" 200 1024'])
    assert not compare(clean, Observation(server_log=['"GET /static/a.js HTTP/1.1" 200 512'])).error
    assert compare(clean, Observation(server_log=["POST /save 500 in 12ms"])).error


def test_eslint_reads_paths_lines_and_severity() -> None:
    payload = [
        {
            "filePath": f"{WORK}/app/page.tsx",
            "messages": [
                {"line": 4, "severity": 2, "ruleId": "react/jsx-key", "message": "Missing key"},
                {"line": 9, "severity": 1, "ruleId": None, "message": "Unused"},
            ],
        }
    ]
    assert eslint_json(json.dumps(payload), "", 1, WORK) == [
        Finding("app/page.tsx", 4, "error", "react/jsx-key", "Missing key"),
        Finding("app/page.tsx", 9, "warning", "eslint", "Unused"),
    ]


def test_a_finding_is_new_when_only_its_severity_or_a_number_differs() -> None:
    clean = [Finding("a.ts", 3, "warning", "TS1", "Expected 1 arguments")]
    assert new_findings(clean, [Finding("a.ts", 3, "error", "TS1", "Expected 1 arguments")])
    both = [
        Finding("a.ts", 3, "warning", "TS1", "Expected 1 arguments"),
        Finding("a.ts", 4, "warning", "TS1", "Expected 2 arguments"),
    ]
    assert new_findings(clean, both) == [both[1]]
    # A known finding that only quotes a moved line is still the clean app's.
    moved = [Finding("a.ts", 9, "warning", "TS1", "Expected 1 arguments, see line 12")]
    assert not new_findings([Finding("a.ts", 8, "warning", "TS1", "Expected 1 arguments, see line 11")], moved)


def test_relative_working_copy_paths_in_messages_are_blanked() -> None:
    clean = [Finding(None, None, "warning", "x", "in ./work/baseline/app/card.tsx")]
    assert not new_findings(clean, [Finding(None, None, "warning", "x", "in ./work/m02-input-name/app/card.tsx")])


def test_timings_in_the_server_log_are_not_read_as_status_codes() -> None:
    clean = Observation(server_log=["Warning: slow page 456ms", "Error: retrying in 310ms"])
    same = Observation(server_log=["Warning: slow page 123ms", "Error: retrying in 250ms"])
    assert compare(clean, same) == RuntimeResult()


def test_named_errors_and_bracketed_statuses_are_server_errors() -> None:
    assert compare(Observation(), Observation(server_log=["TypeError: x is undefined"])).error
    assert compare(Observation(), Observation(server_log=["[500] GET /"])).error


def test_a_new_status_on_a_known_failing_url_counts() -> None:
    clean = Observation(bad_responses=["404 http://127.0.0.1:1/a"])
    assert not compare(clean, Observation(bad_responses=["404 http://127.0.0.1:2/a"])).error
    assert compare(clean, Observation(bad_responses=["500 http://127.0.0.1:2/a"])).error


def test_the_clean_app_is_unusable_with_error_responses_or_server_errors() -> None:
    assert problems(Observation()) == []
    assert problems(Observation(bad_responses=["500 http://x/"]))
    assert problems(Observation(server_log=["Traceback (most recent call last):"]))


def test_a_timeout_marks_only_cells_it_could_have_changed() -> None:
    def record(outcome: str, timed_out_stage: str) -> dict:
        stages = [{"stage": timed_out_stage, "timed_out": True}]
        return {"status": "ported", "strict": outcome, "stages": stages}

    assert report._cell(record("check", "editor"), "strict") == "C~"
    assert report._cell(record("editor", "build"), "strict") == "E"
    assert report._cell(record("not-run", "build"), "strict") == "?~"


def test_ruff_findings_are_errors_with_their_rule() -> None:
    payload = [
        {
            "filename": f"{WORK}/main.py",
            "location": {"row": 7, "column": 1},
            "code": "F821",
            "message": "Undefined name",
        },
        {"filename": f"{WORK}/main.py", "location": {"row": 9, "column": 1}, "code": None, "message": "Expected ')'"},
    ]
    assert ruff_json(json.dumps(payload), "", 1, WORK) == [
        Finding("main.py", 7, "error", "F821", "Undefined name"),
        Finding("main.py", 9, "error", "invalid-syntax", "Expected ')'"),
    ]


def test_djlint_findings_take_the_file_printed_above_them() -> None:
    out = (
        "\nLinting 3/3 files\n\n\nboard/templates/board/card.html\n"
        + "─" * 20
        + '\nH025 1:0 Tag seems to be an orphan. <div class="card">\n\nLinted 3 files, found 1 error.\n'
    )
    assert djlint(out, "", 1, WORK) == [
        Finding("board/templates/board/card.html", 1, "error", "H025", 'Tag seems to be an orphan. <div class="card">')
    ]
    assert djlint("Linted 3 files, found 0 errors.\n", "", 0, WORK) == []


def test_the_html_report_draws_every_framework_and_escapes_tool_output() -> None:
    summary = {
        "run": "r1",
        "source": {"commit": "abc", "benchmark_files_changed": False},
        "frameworks": [{"key": "citry", "name": "Citry"}, {"key": "next", "name": "Next.js"}],
        "categories": [{"id": "naming", "heading": "Names"}],
        "buckets": [{"id": key, "label": key} for key in html_report.BUCKET_COLORS],
        "codes": [{"code": "E", "meaning": "reported in the editor"}],
        "mistakes": [{"id": "m1", "title": "Misspelled name", "category": "naming"}],
        "results": [
            {
                "framework": "citry",
                "mistake": "m1",
                "status": "ported",
                "bucket": "static-error",
                "cell": "E",
                "evidence": ["editor: <c-Crad> is not registered"],
            },
            {
                "framework": "next",
                "mistake": "m1",
                "status": "not-applicable",
                "bucket": None,
                "cell": "n/a",
                "reason": "No equivalent",
                "evidence": [],
            },
        ],
    }
    page = html_report.render(summary)
    assert page.startswith("<!doctype html>")
    assert "&lt;c-Crad&gt;" in page
    assert "<c-Crad>" not in page
    # A mistake that does not apply is drawn as its own part of the bar.
    assert 'aria-label="Next.js, N/A or prevented: 1"' in page
    # Citry reported its one mistake; Next.js has none that apply.
    assert "<td>(1/1)</td>" in page
    assert "<td>(0/0)</td>" in page
    # Both bars start at the axis, and each covers every mistake.
    assert page.count('<rect x="180.00" y="') == 2
    assert 'download="error-outcomes.svg"' in page
    assert "<script" not in page


def test_a_failing_build_takes_the_first_file_its_output_names() -> None:
    out = f"[plugin vite:vue] {WORK}/app/components/Card.vue:15:5\nElement is missing end tag.\n" + "frame\n" * 20
    [finding] = exit_status(out, "", 1, WORK)
    assert (finding.file, finding.line) == ("app/components/Card.vue", 15)


def test_an_import_failure_counts_and_a_file_name_must_match_whole() -> None:
    crash = Finding(None, None, "error", "citry.app-failure", "NameError: name 'x' is not defined")
    assert score_stage("check", "citry check", [], [crash], "app/data.py", 3, 3).error
    other = Finding(None, None, "error", "exit-1", "failed in app/board_card.py")
    assert score_stage("build", "build", [], [other], "app/card.py", 3, 3).unconfirmed == [other]


def test_the_working_folder_name_in_a_server_log_is_not_a_new_line() -> None:
    clean = _normal("Will watch for changes in /x/work/baseline", keep_status=True)
    assert _normal("Will watch for changes in /x/work/m01-component-name", keep_status=True) == clean


def test_published_evidence_blanks_dev_server_ports() -> None:
    assert report._public("404 http://127.0.0.1:51234/sav") == "404 http://127.0.0.1:<port>/sav"


def test_chart_ticks_count_in_fives_from_ten_up() -> None:
    assert html_report._ticks(24) == [0, 5, 10, 15, 20, 25]
    assert html_report._ticks(10) == [0, 5, 10]
    assert html_report._ticks(7) == [0, 2, 4, 6, 8]
    assert html_report._ticks(60) == [0, 20, 40, 60]
