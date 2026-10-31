"""Contracts for cancelling stale CI runs and for focused Python diagnostics."""

from __future__ import annotations

import fnmatch
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import tomllib
import yaml  # type: ignore[import-untyped]

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"


def _load_workflow(name: str) -> dict[str, Any]:
    content = yaml.safe_load((_WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(content, dict)
    # PyYAML applies YAML 1.1 booleans, where the Actions key `on` becomes True.
    if True in content:
        content["on"] = content.pop(True)
    return content


# The concurrency the check workflows use, apart from
# `_CANCELS_ONLY_PULL_REQUEST_RUNS` below. A run joins the group of its pull
# request, or of its branch when it comes from a push, so a newer run cancels
# the older one. A scheduled or manual run is alone in a group named after its
# own run ID, so nothing cancels it.
_CHECK_CONCURRENCY = {
    "group": (
        "${{ github.workflow }}-${{ github.event.pull_request.number"
        " || (github.event_name == 'push' && github.ref) || github.run_id }}"
    ),
    "cancel-in-progress": (
        "${{ github.event_name == 'pull_request' || github.event_name == 'pull_request_target'"
        " || github.event_name == 'push' }}"
    ),
}

# The concurrency of a workflow where a newer run cancels an older one only for
# the same pull request.
_PULL_REQUEST_ONLY_CONCURRENCY = {
    "group": "${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}",
    "cancel-in-progress": "${{ github.event_name == 'pull_request' || github.event_name == 'pull_request_target' }}",
}

# Workflows that run checks on a push to main but let no newer push cancel that
# run, so every commit on main keeps a complete result. Release step 5 in
# docs/codebase.md requires the repository Check to pass for the release
# commit itself.
_CANCELS_ONLY_PULL_REQUEST_RUNS = {"repo--check.yml"}

# Workflows that run on a push to main but must finish once started, each
# with the reason.
_PUSH_WORKFLOWS_NEVER_CANCELLED = {
    # Deploys the docs site. A cancelled deploy publishes nothing, so if the
    # newer run then fails, the site stays on a deploy older than both.
    "repo--docs-deploy.yml",
    # Starts the publish workflows that qualify a release and waits for them;
    # stopping it would leave those runs going with no candidate to collect.
    "repo--release-candidate.yml",
}


def _workflows() -> list[tuple[str, dict[str, Any]]]:
    paths = sorted([*_WORKFLOWS.glob("*.yml"), *_WORKFLOWS.glob("*.yaml")])
    return [(path.name, _load_workflow(path.name)) for path in paths]


def test_pull_request_workflows_cancel_only_stale_runs() -> None:
    checked: set[str] = set()
    for name, workflow in _workflows():
        events = workflow.get("on", {})
        if not isinstance(events, dict) or not {"pull_request", "pull_request_target"}.intersection(events):
            continue

        expected = _PULL_REQUEST_ONLY_CONCURRENCY if name in _CANCELS_ONLY_PULL_REQUEST_RUNS else _CHECK_CONCURRENCY
        assert workflow.get("concurrency") == expected, name
        checked.add(name)

    assert checked == {
        "py--examples--tests.yml",
        "py--tests.yml",
        "repo--check.yml",
        "repo--codeql.yml",
        "repo--dependabot-relock.yml",
        "repo--discord-pr.yml",
        "repo--docs-check.yml",
        "repo--docs-lighthouse.yml",
        "repo--dom-members.yml",
        "repo--generated.yml",
        "repo--security.yml",
        "rust--tests.yml",
    }


def _runs_on_push_to_main(events: object) -> bool:
    """Whether these `on:` events start a run when someone pushes to main."""
    if isinstance(events, str):
        return events == "push"
    if isinstance(events, list):
        return "push" in events
    if not isinstance(events, dict) or "push" not in events:
        return False
    push = events["push"] or {}
    # A filter on tags alone leaves branch pushes out; no filter at all
    # takes every branch.
    if "branches" not in push and "branches-ignore" not in push and ("tags" in push or "tags-ignore" in push):
        return False
    # GitHub accepts one pattern written as a plain string. `!` patterns are
    # not modelled, so a filter that uses them errs toward checking the
    # workflow.
    if "branches-ignore" in push:
        ignored = push["branches-ignore"]
        ignored = [ignored] if isinstance(ignored, str) else ignored
        return not any(fnmatch.fnmatchcase("main", pattern) for pattern in ignored)
    branches = push.get("branches", ["**"])
    branches = [branches] if isinstance(branches, str) else branches
    return any(fnmatch.fnmatchcase("main", pattern) for pattern in branches)


def _never_cancels(concurrency: Any) -> bool:
    # A bare string group, or one without `cancel-in-progress`, never cancels
    # a started run; it only replaces a waiting one.
    return concurrency is None or isinstance(concurrency, str) or concurrency.get("cancel-in-progress", False) is False


def test_a_newer_push_to_main_cancels_the_older_run_except_check_docs_deploy_and_release_candidate() -> None:
    cancelled: set[str] = set()
    never_cancelled: set[str] = set()
    for name, workflow in _workflows():
        # Every workflow a push to main can start is checked, so a new one
        # must either use the shared concurrency or join the exceptions above.
        if not _runs_on_push_to_main(workflow.get("on")):
            continue
        concurrency = workflow.get("concurrency")
        if name in _PUSH_WORKFLOWS_NEVER_CANCELLED:
            assert isinstance(concurrency, dict), name
            assert concurrency.get("cancel-in-progress") is False, name
            never_cancelled.add(name)
        elif name in _CANCELS_ONLY_PULL_REQUEST_RUNS:
            assert concurrency == _PULL_REQUEST_ONLY_CONCURRENCY, name
            never_cancelled.add(name)
        else:
            assert concurrency == _CHECK_CONCURRENCY, name
            cancelled.add(name)

    assert never_cancelled == _PUSH_WORKFLOWS_NEVER_CANCELLED | _CANCELS_ONLY_PULL_REQUEST_RUNS
    # Guards against the loop finding nothing because the trigger shape changed.
    assert {"py--tests.yml", "rust--tests.yml"} <= cancelled


def test_publish_and_release_workflows_are_never_cancelled_by_a_newer_run() -> None:
    checked: set[str] = set()
    for name, workflow in _workflows():
        if not (name.endswith("--publish.yml") or "release" in name):
            continue
        checked.add(name)
        # A run that stops halfway can leave a package or tag half published,
        # so a group here may queue a newer run but never cancel a started one.
        assert _never_cancels(workflow.get("concurrency")), name
        for job_name, job in workflow["jobs"].items():
            assert _never_cancels(job.get("concurrency")), f"{name}: {job_name}"
    assert {
        "py--citry--publish.yml",
        "repo--docs-release.yml",
        "repo--release.yml",
        "repo--release-candidate.yml",
        "vscode--citry--publish.yml",
    } <= checked


# Workflows that run on pull requests but run no checks, so a closed PR has
# nothing of theirs worth cancelling: a notification and a lockfile refresh.
_PR_WORKFLOWS_WITHOUT_CHECKS = {"repo--discord-pr.yml", "repo--dependabot-relock.yml"}


def test_check_workflows_cancel_a_pull_requests_runs_when_it_closes() -> None:
    checked: set[str] = set()
    for name, workflow in _workflows():
        events = workflow.get("on", {})
        # Every check workflow that runs on pull requests is covered, so a new
        # one cannot leave its runs going after the PR merges.
        if not isinstance(events, dict) or "pull_request" not in events:
            continue
        if name in _PR_WORKFLOWS_WITHOUT_CHECKS:
            continue
        checked.add(name)
        # A `closed` run joins the PR's concurrency group, and the group's
        # cancel-in-progress (checked above) cancels the PR's earlier runs.
        assert workflow["on"]["pull_request"]["types"] == ["opened", "synchronize", "reopened", "closed"], name
        for job_name, job in workflow["jobs"].items():
            # A job with `needs` is skipped with the job it needs, so only the
            # jobs that start a run need the condition. Without it, the
            # cancelling run would itself queue for runners. Jobs that need
            # the Python tests' `changes` job check `closed` themselves; the
            # next test covers them.
            if "needs" not in job:
                # The Python tests' `changes` job also skips outside pull requests.
                expected = _CHANGES_IF if (name, job_name) == ("py--tests.yml", "changes") else _SKIPS_ON_CLOSE
                assert job.get("if") == expected, f"{name}: {job_name}"
    # Guards against the loop finding nothing because the trigger shape changed.
    assert {"repo--check.yml", "py--tests.yml"} <= checked


_SKIPS_ON_CLOSE = "github.event.action != 'closed'"

# When the Python tests' `changes` job runs: on a pull request, except the
# `closed` event, which must start no runner.
_CHANGES_IF = "github.event_name == 'pull_request' && github.event.action != 'closed'"

# The condition on each job that needs `changes`: it skips only on an
# explicit "false", so a failed `changes` runs everything rather than leaving
# a required check skipped, which GitHub counts as passing.
_RUNS_UNLESS_NOTHING_CHANGED = (
    "${{ !cancelled() && github.event.action != 'closed' && needs.changes.outputs.python != 'false' }}"
)

# The condition on a job below the wheel build. GitHub's default condition
# would skip it on every push, because `changes` is skipped there.
_RUNS_AFTER_THE_WHEEL_BUILD = "${{ !cancelled() && needs.citry-ui-wheel-build.result == 'success' }}"


def test_python_tests_start_on_every_pull_request_and_skip_without_python_changes() -> None:
    workflow = _load_workflow("py--tests.yml")
    # A required check in a workflow that never starts waits forever, so the
    # pull-request trigger has no path list and the `changes` job decides.
    assert "paths" not in workflow["on"]["pull_request"]
    changes = workflow["jobs"]["changes"]
    assert changes["if"] == _CHANGES_IF
    # The gated jobs read this output. If the step id or output name changed,
    # the output would be empty and every job would run on every pull request.
    step = changes["steps"][0]
    assert changes["outputs"]["python"] == f"${{{{ steps.{step['id']}.outputs.python }}}}"
    # The shell matcher compares each line as it is, so a stray space would
    # make a path never match.
    inputs = [line for line in step["env"]["PYTHON_INPUTS"].splitlines() if line]
    assert all(line == line.strip() for line in inputs), inputs
    # Both lists must name the same paths, or a push and a pull request
    # would disagree about which changes the Python jobs test.
    assert inputs == workflow["on"]["push"]["paths"]
    # The job's shell matcher understands only `folder/**` and an exact file
    # path, so no other glob character may appear.
    for pattern in inputs:
        body = pattern.removesuffix("/**")
        assert not any(char in body for char in "*?[]!+{}"), pattern

    jobs = workflow["jobs"]
    for name, job in jobs.items():
        if name == "changes":
            continue
        needs = job.get("needs")
        needs = needs if isinstance(needs, list) else [needs]
        assert needs != [None], f"{name} must need `changes` or a job that does"
        if "changes" in needs:
            assert job["if"] == _RUNS_UNLESS_NOTHING_CHANGED, name
        else:
            # A job below a gated one must check its parent's result itself.
            # GitHub's default check skips it whenever any job further up was
            # skipped, and `changes` is skipped on every push.
            assert needs == ["citry-ui-wheel-build"], name
            assert job["if"] == _RUNS_AFTER_THE_WHEEL_BUILD, name
    assert "citry-ui-wheel-build" in jobs


_BASH = shutil.which("bash")
_JQ = shutil.which("jq")


def _files(*names: str) -> list[dict[str, str]]:
    return [{"filename": name} for name in names]


@pytest.mark.skipif(_BASH is None or _JQ is None, reason="the changes job runs in bash and reads JSON with jq")
@pytest.mark.parametrize(
    ("files", "changed_files", "head", "expected"),
    [
        (_files("docs_site/content/a.md", "CHANGELOG.md"), 2, "abc", "false"),
        (_files("docs/notes.md", "packages/py/citry/x.py"), 2, "abc", "true"),
        # Only the root README goes into the citry wheel's metadata.
        (_files("README.md"), 1, "abc", "true"),
        (_files("docs/README.md"), 1, "abc", "false"),
        # A folder pattern does not match a longer folder name.
        (_files("packages/pyx/a.py"), 1, "abc", "false"),
        (_files("crates/a b/c.rs"), 1, "abc", "true"),
        ([], 0, "abc", "false"),
        # Moving a file out of a Python folder counts under its old path.
        ([{"filename": "docs/x.md", "previous_filename": "packages/py/x.md"}], 1, "abc", "true"),
        # A match on a later page of the listing still counts.
        (_files("a.md", "b.md", "c.md", "d.md", "crates/x.rs"), 5, "abc", "true"),
        # A list shorter than the pull request (more than 3,000 files, or a
        # listing that lags a push), or a pull request that got a newer
        # commit, runs everything.
        (_files("docs/a.md"), 3001, "abc", "true"),
        (_files("docs/a.md"), 1, "newer", "true"),
    ],
)
def test_the_changes_job_matches_files_like_the_push_path_filter(
    tmp_path: Path, files: list[dict[str, str]], changed_files: int, head: str, expected: str
) -> None:
    step = _load_workflow("py--tests.yml")["jobs"]["changes"]["steps"][0]
    # A stand-in for `gh api` that returns the JSON GitHub would: the pull
    # request itself, or its file list as pages of two, the way
    # `gh api --paginate` prints them. The job's own jq then reads it.
    pull = tmp_path / "pull.json"
    pull.write_text(json.dumps({"changed_files": changed_files, "head": {"sha": head}}), encoding="utf-8")
    pages = tmp_path / "pages.json"
    pages.write_text("".join(json.dumps(files[i : i + 2]) for i in range(0, max(len(files), 1), 2)), encoding="utf-8")
    fake_gh = tmp_path / "bin" / "gh"
    fake_gh.parent.mkdir()
    fake_gh.write_text(
        "#!/usr/bin/env bash\n"
        'case "$*" in\n'
        f"  */files*) cat {shlex.quote(str(pages))} ;;\n"
        f"  *) cat {shlex.quote(str(pull))} ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    output = tmp_path / "output"
    output.write_text("", encoding="utf-8")
    assert _BASH is not None
    assert _JQ is not None
    env = {
        "PATH": f"{fake_gh.parent}:{Path(_JQ).parent}:/usr/bin:/bin",
        "PYTHON_INPUTS": step["env"]["PYTHON_INPUTS"],
        "REPOSITORY": "owner/repo",
        "PR_NUMBER": "1",
        "HEAD_SHA": "abc",
        "GITHUB_OUTPUT": str(output),
    }

    subprocess.run([_BASH, "-c", step["run"]], env=env, check=True, capture_output=True)

    assert output.read_text(encoding="utf-8").strip().splitlines() == [f"python={expected}"]


_SUPPORTED_PYTHONS = ["3.11", "3.12", "3.13", "3.14", "3.15"]


def _python_test_cells() -> dict[str, set[tuple[str, str]]]:
    """Return the (OS, Python) cells py--tests.yml runs on a pull request and on every other event."""
    expression = _load_workflow("py--tests.yml")["jobs"]["test"]["strategy"]["matrix"]["include"]
    # The matrix is one expression that picks a JSON list by event, so the
    # two lists are read out of its two quoted strings.
    match = re.fullmatch(
        r"\$\{\{ fromJSON\(github\.event_name == 'pull_request' && '(?P<pr>\[.*?\])' \|\| '(?P<full>\[.*?\])'\) \}\}",
        expression.strip(),
    )
    assert match is not None, expression
    return {
        name: {(cell["os"], cell["python-version"]) for cell in json.loads(match.group(name))}
        for name in ("pr", "full")
    }


def test_the_full_python_matrix_runs_every_supported_python_on_every_os() -> None:
    cells = _python_test_cells()
    check_job = _load_workflow("repo--check.yml")["jobs"]["check"]
    check_python = next(
        step["with"]["python-version"]
        for step in check_job["steps"]
        if step.get("uses", "").startswith("actions/setup-python")
    )

    # Pushes to main run the full set, so a failure that a pull request's
    # trimmed set skips still shows up right after the merge. Linux leaves out
    # only the Python that the Check workflow already runs on every pull
    # request; Windows runs every supported Python; macOS keeps the oldest and
    # newest. If Check moves to another Python, this fails until the matrix
    # moves with it.
    assert check_job["runs-on"] == "ubuntu-latest"
    assert check_python in _SUPPORTED_PYTHONS
    assert cells["full"] == {
        *(("ubuntu-latest", version) for version in _SUPPORTED_PYTHONS if version != check_python),
        *(("windows-latest", version) for version in _SUPPORTED_PYTHONS),
        ("macos-latest", _SUPPORTED_PYTHONS[0]),
        ("macos-latest", _SUPPORTED_PYTHONS[-1]),
    }
    # That only holds while Check runs on every pull request: no path filter on
    # its trigger and no condition on the step that runs check.py.
    check_events = _load_workflow("repo--check.yml")["on"]
    assert not (check_events.get("pull_request") or {}).get("paths")
    gate = next(step for step in check_job["steps"] if "scripts/check.py --profile full" in step.get("run", ""))
    assert "if" not in gate
    # And while both select the same tests: the matrix runs every non-browser
    # test except the reload file, which check.py runs in its own phase.
    tests_steps = {step.get("name"): step for step in _load_workflow("py--tests.yml")["jobs"]["test"]["steps"]}
    matrix_run = tests_steps["Run Python tests"]["run"]
    assert '-m "not e2e"' in matrix_run
    assert matrix_run.count("--ignore") == 1


def test_a_pull_request_runs_a_trimmed_python_matrix() -> None:
    cells = _python_test_cells()

    # A pull request keeps every Linux cell, and Windows and macOS only at the
    # edges, to save runner slots. Every cell it runs is in the full set, so
    # the trimmed set can never test something main does not.
    linux = {cell for cell in cells["full"] if cell[0] == "ubuntu-latest"}
    assert cells["pr"] == {
        *linux,
        ("windows-latest", _SUPPORTED_PYTHONS[0]),
        ("windows-latest", _SUPPORTED_PYTHONS[-1]),
        ("macos-latest", _SUPPORTED_PYTHONS[-1]),
    }
    assert cells["pr"] < cells["full"]


def test_python_diagnostic_constrains_setup_and_passes_one_literal_target() -> None:
    workflow = _load_workflow("py--diagnostic.yml")
    dispatch = workflow["on"]["workflow_dispatch"]
    inputs = dispatch["inputs"]

    runner = inputs["runner_os"]
    assert runner["type"] == "choice"
    assert runner["required"] is True
    assert runner["default"] == "ubuntu-latest"
    assert runner["options"] == ["ubuntu-latest", "macos-latest", "windows-latest"]

    python = inputs["python_version"]
    assert python["type"] == "choice"
    assert python["required"] is True
    assert python["default"] == "3.14"
    assert python["options"] == ["3.11", "3.12", "3.13", "3.14", "3.15"]

    profile = inputs["install_profile"]
    assert profile["type"] == "choice"
    assert profile["required"] is True
    assert profile["default"] == "citry"
    assert profile["options"] == [
        "citry",
        "citry-core",
        "citry-lsp",
        "citry-ui",
        "pygments-citry",
        "full-workspace",
    ]

    wheel_mode = inputs["core_wheel_mode"]
    assert wheel_mode["type"] == "choice"
    assert wheel_mode["required"] is True
    assert wheel_mode["default"] == "reuse"
    assert wheel_mode["options"] == ["reuse", "rebuild"]

    target = inputs["pytest_target"]
    assert target == {
        "description": "One ordinary non-browser Python test file or node ID",
        "required": True,
        "default": "packages/py/citry/tests/test_server_reload.py",
        "type": "string",
    }

    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["jobs"]) == {"test"}
    job = workflow["jobs"]["test"]
    assert job["runs-on"] == "${{ inputs.runner_os }}"
    assert job["timeout-minutes"] == 45
    steps = {step.get("name", step.get("uses")): step for step in job["steps"]}
    assert "with" not in steps["actions/checkout@v7"]
    assert steps["Set up Python"]["with"]["python-version"] == "${{ inputs.python_version }}"

    validate_step = steps["Validate the selected pytest target"]
    assert validate_step["shell"] == "bash"
    assert validate_step["env"] == {
        "INSTALL_PROFILE": "${{ inputs.install_profile }}",
        "PYTEST_TARGET": "${{ inputs.pytest_target }}",
    }
    assert "inputs.pytest_target" not in validate_step["run"]
    assert 'validate-target --profile "$INSTALL_PROFILE" --target "$PYTEST_TARGET"' in validate_step["run"]

    restore = steps["Restore exact Citry Core wheel"]
    assert restore["uses"] == "actions/cache/restore@v6"
    assert restore["with"] == {
        "path": ".diagnostic-cache/citry-core",
        "key": "${{ steps.core-identity.outputs.cache_key }}",
    }
    assert "restore-keys" not in restore["with"]
    identity = steps["Resolve Citry Core wheel identity"]
    runner_image_argument = (
        'runner-image "${ImageOS:?missing hosted image OS}/${ImageVersion:?missing hosted image version}"'
    )
    assert runner_image_argument in identity["run"]

    build = steps["Build Citry Core wheel"]
    assert build["env"] == {
        "CARGO_INCREMENTAL": "0",
        "RUSTC_WRAPPER": "sccache",
        "SCCACHE_GHA_ENABLED": "true",
    }
    assert build["run"].splitlines() == [
        "uv lock --check",
        "uv build --package citry-core --wheel \\",
        "  --out-dir .diagnostic-cache/citry-core",
    ]
    assert steps["Set up sccache for a Core wheel cache miss"]["uses"] == (
        "mozilla-actions/sccache-action@fc920bf0ec8de6ee65d409111f7ec508035751ba"
    )
    assert steps["Enable GitHub Actions-backed sccache"]["run"].splitlines() == [
        'echo "RUSTC_WRAPPER=sccache" >> "$GITHUB_ENV"',
        'echo "SCCACHE_GHA_ENABLED=true" >> "$GITHUB_ENV"',
    ]
    assert steps["Initialize native submodules"]["run"] == "git submodule update --init --recursive"

    uv = shutil.which("uv")
    assert uv is not None
    uv_build_help = subprocess.run([uv, "build", "--help"], check=True, capture_output=True, text=True).stdout
    supported_build_options = set(re.findall(r"(?m)^\s+(?:-[A-Za-z],\s+)?(--[a-z][a-z-]*)\b", uv_build_help))
    build_command = " ".join(build["run"].splitlines()[1:]).replace("\\", "")
    requested_build_options = {token for token in shlex.split(build_command) if token.startswith("--")}
    assert requested_build_options <= supported_build_options

    core_pyproject = tomllib.loads(
        (_REPO_ROOT / "packages" / "py" / "citry_core" / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert core_pyproject["tool"]["maturin"]["locked"] is True

    save = steps["Save exact Citry Core wheel"]
    assert save["uses"] == "actions/cache/save@v6"
    assert save["with"] == restore["with"]
    assert "core_wheel_mode == 'reuse'" in save["if"]
    assert "cache-hit != 'true'" in save["if"]
    step_names = [step.get("name", step.get("uses")) for step in job["steps"]]
    assert step_names.index("Install selected diagnostic profile") < step_names.index("Save exact Citry Core wheel")
    assert step_names.index("Save exact Citry Core wheel") < step_names.index("Run selected pytest target serially")

    install = steps["Install selected diagnostic profile"]
    assert install["env"] == {
        "CORE_WHEEL_CACHE_KEY": "${{ steps.core-identity.outputs.cache_key }}",
        "INSTALL_PROFILE": "${{ inputs.install_profile }}",
    }
    assert "inputs.install_profile" not in install["run"]
    assert 'install-profile --profile "$INSTALL_PROFILE"' in install["run"]

    run_step = steps["Run selected pytest target serially"]
    assert run_step["shell"] == "bash"
    assert run_step["env"] == {"PYTEST_TARGET": "${{ inputs.pytest_target }}"}
    assert "inputs.pytest_target" not in run_step["run"]
    assert run_step["run"] == 'uv run --no-sync python -m pytest -m "not e2e" --durations 30 -- "$PYTEST_TARGET"'
    assert "-n" not in run_step["run"].split()


def test_docs_check_keeps_the_playground_on_the_published_pins() -> None:
    # Docs check runs the playground against runtime.json's published pins and
    # lets branch-only tests skip; a workspace Core wheel would opt it back in.
    docs_workflow = _load_workflow("repo--docs-check.yml")
    steps = docs_workflow["jobs"]["docs-e2e"]["steps"]
    assert all("CITRY_PLAYGROUND_CORE_WHEEL" not in step.get("run", "") for step in steps)
    assert all("CITRY_PLAYGROUND_CORE_WHEEL" not in step.get("env", {}) for step in steps)
    assert "CITRY_PLAYGROUND_CORE_WHEEL" not in docs_workflow["jobs"]["docs-e2e"].get("env", {})


def test_workspace_core_wheel_consumers_reject_ambiguous_cached_outputs() -> None:
    publish_workflow = _load_workflow("py--citry--publish.yml")
    core_consumers = [
        step
        for job in publish_workflow["jobs"].values()
        for step in job.get("steps", [])
        if "--core-wheel" in step.get("run", "")
    ]
    assert len(core_consumers) == 2
    for step in core_consumers:
        assert step["shell"] == "bash"
        assert "${#core_wheels[@]} -ne 1" in step["run"]
        assert "-print -quit" not in step["run"]


def test_generated_files_workflow_runs_on_every_change() -> None:
    # A required check on a path-filtered workflow waits forever when the
    # filter skips it, so this early check must never have a path filter.
    workflow = _load_workflow("repo--generated.yml")
    events = workflow["on"]
    assert set(events) == {"push", "pull_request", "workflow_dispatch"}
    for event in ("push", "pull_request"):
        assert "paths" not in (events[event] or {})
        assert "paths-ignore" not in (events[event] or {})
