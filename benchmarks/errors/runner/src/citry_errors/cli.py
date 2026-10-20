"""Command line: validate the cases, install the frameworks, run the matrix and write the report."""

from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from . import parallel, report
from .config import (
    BENCH_ROOT,
    CACHE,
    REPO_ROOT,
    STATIC_STAGES,
    ConfigError,
    Framework,
    Port,
    load_catalogue,
    load_frameworks,
    load_ports,
)
from .parsers import PARSE, Finding, ToolUnavailable
from .runtime import Observation, compare, observe, problems
from .score import StageResult, earliest, score_stage
from .work import changed_files, command_env, env_dir, materialize, mistake_lines, placeholder, prepare

T = TypeVar("T")


def _run_stages(framework: Framework, work: Path, out: Path) -> list[list[Finding] | None]:
    """Run every static stage of one framework on one working copy and keep its raw output.

    A stage that times out gives None: its missing output must neither count
    as catching the mistake nor as missing it.
    """
    env = env_dir(framework)
    results = []
    for index, stage in enumerate(framework.stages):
        argv = [placeholder(part, framework, env, work) for part in stage.argv]
        try:
            completed = subprocess.run(
                argv,
                cwd=work,
                env=command_env(framework, env, work, stage.env),
                capture_output=True,
                text=True,
                timeout=stage.timeout,
                check=False,
            )
            stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired:
            (out / f"stage-{index}.out").write_text(f"$ {' '.join(argv)}\n# timed out after {stage.timeout} s\n")
            results.append(None)
            continue
        (out / f"stage-{index}.out").write_text(f"$ {' '.join(argv)}\n# exit {code}\n{stdout}\n# stderr\n{stderr}")
        try:
            results.append(PARSE[stage.parser](stdout, stderr, code, work))
        except ToolUnavailable as error:
            # Treated like a timeout: a tool that skipped its checks has no verdict.
            (out / f"stage-{index}.unavailable").write_text(str(error))
            results.append(None)
    return results


def validate(frameworks: dict[str, Framework], ports: dict[tuple[str, str], Port]) -> list[str]:
    """List every gap between the catalogue, the frameworks and their ports."""
    problems = []
    mistakes = load_catalogue()
    neutral = sum(mistake.origin == "neutral" for mistake in mistakes)
    if neutral * 2 < len(mistakes):
        problems.append(f"only {neutral} of {len(mistakes)} mistakes are neutral; at least half must be")
    known = {mistake.id for mistake in mistakes}
    for mistake_id, framework_key in ports:
        if mistake_id not in known:
            problems.append(f"cases/{mistake_id} is not in the catalogue")
        if framework_key not in frameworks:
            problems.append(f"cases/{mistake_id}/{framework_key} names an unknown framework")
    for framework_key, framework in frameworks.items():
        for mistake in mistakes:
            port = ports.get((mistake.id, framework_key))
            if port is None:
                problems.append(f"{framework_key} has no port for {mistake.id}")
                continue
            if port.status == "ported":
                problems += port_problems(framework, port)
    return problems


def port_problems(framework: Framework, port: Port) -> list[str]:
    """
    Check one ported case against the current baseline.

    An edit is checked against the baseline as it is now, so when a baseline
    change removes or repeats an edit's old text, `validate` names every case
    that needs a look before a run starts.
    """
    try:
        changed = changed_files(framework, port)
    except ConfigError as error:
        return [str(error)]
    count = len(mistake_lines(changed[port.mistake_file].decode("utf-8"), port.mistake_contains))
    if count != 1:
        return [f"{port.root}: mistake text is on {count} lines, expected 1"]
    return []


def _source() -> dict:
    """Record the commit a run starts from, so a published result names the cases it scored."""

    def git(*argv: str) -> str:
        completed = subprocess.run(["git", *argv], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        return completed.stdout.strip()

    # Uncommitted changes under the benchmark folder mean the commit alone
    # does not describe the cases that ran.
    changed = git("status", "--porcelain", "--", str(BENCH_ROOT.relative_to(REPO_ROOT)))
    return {"commit": git("rev-parse", "HEAD"), "benchmark_files_changed": bool(changed)}


@dataclass
class Baseline:
    """The clean app's results for one framework, which every case of that framework is compared with."""

    findings: list[list[Finding] | None]
    runtime: Observation | None
    # What made the clean app's run unusable as the comparison point; empty when it was clean.
    errors: list[str]


def _run_baseline(framework: Framework, run_dir: Path, *, observe_runtime: bool) -> Baseline:
    env = env_dir(framework)
    base_out = run_dir / framework.key / "baseline"
    base_out.mkdir(parents=True)
    base = materialize(framework, None)
    findings = _run_stages(framework, base.path, base_out)
    runtime: Observation | None = None
    if framework.runtime and observe_runtime:
        runtime = observe(framework, env, base.path, base_out / "server.log")
        (base_out / "runtime.json").write_text(runtime.to_json())
    # The clean app must pass every stage, or a case's finding could not be
    # told apart from noise that was already there.
    errors = [
        f"{framework.stages[index].label}: {finding.message}"
        for index, stage_findings in enumerate(findings)
        for finding in stage_findings or []
        if finding.severity == "error"
    ] + [
        f"{framework.stages[index].label}: timed out"
        for index, stage_findings in enumerate(findings)
        if stage_findings is None
    ]
    if runtime:
        errors += [f"runtime: {problem}" for problem in problems(runtime)]
    (base_out / "baseline-errors.json").write_text(json.dumps(errors, indent=2))
    return Baseline(findings, runtime, errors)


def _run_case(framework: Framework, port: Port, baseline: Baseline, run_dir: Path) -> dict:
    """Run one case's stages and browser check and score them against the clean app; runs on a worker thread."""
    out = run_dir / framework.key / port.mistake
    out.mkdir(parents=True)
    copy = materialize(framework, port)
    findings = _run_stages(framework, copy.path, out)
    stages: list[StageResult] = [
        score_stage(
            stage.stage,
            stage.label,
            baseline.findings[index],
            findings[index],
            port.mistake_file,
            copy.mistake_line,
            port.window,
            port.indirect_codes,
        )
        for index, stage in enumerate(framework.stages)
    ]
    runtime_result = None
    caught_by = _static_catch(stages)
    # The benchmark scores only where a mistake is first reported. A static
    # error decides both columns, because the lenient one counts errors too,
    # so the browser check could not change the cell and is skipped. A static
    # warning alone leaves the strict column to the browser check, which runs.
    if baseline.runtime is not None and not caught_by:
        observation = observe(framework, env_dir(framework), copy.path, out / "server.log")
        (out / "runtime.json").write_text(observation.to_json())
        runtime_result = compare(baseline.runtime, observation)
    record = {
        "status": "ported",
        "baseline_clean": not baseline.errors,
        "timed_out": [stage.label for stage in stages if stage.timed_out],
        "mistake_line": copy.mistake_line,
        "strict": earliest(stages, runtime_result, count_warnings=False, accept_indirect=True),
        "lenient": earliest(stages, runtime_result, count_warnings=True, accept_indirect=True),
        # Shown with a mark, so a reader sees which cells rest on a confirmed indirect finding.
        "indirect": port.indirect
        if any(
            earliest(stages, runtime_result, count_warnings=lenient, accept_indirect=True)
            != earliest(stages, runtime_result, count_warnings=lenient)
            for lenient in (False, True)
        )
        else "",
        # Both lists are kept, so a reader can check what a note let
        # through and what was left out.
        "accepted_indirect": [
            f"{stage.label}: {finding.file}:{finding.line} {finding.code} {finding.message[:160]}"
            for stage in stages
            for finding in stage.indirect
        ],
        "unconfirmed_indirect": [
            f"{stage.label}: {finding.file}:{finding.line} {finding.code} {finding.message[:160]}"
            for stage in stages
            for finding in stage.unconfirmed
        ],
        "stages": [asdict(stage) for stage in stages],
        "runtime": asdict(runtime_result) if runtime_result else None,
        # Says why `runtime` is empty for a case a static stage already
        # reported, so it is not read as a run with the browser check off.
        "runtime_skipped": f"caught by {caught_by}" if caught_by and baseline.runtime is not None else "",
    }
    print(f"{framework.key:10} {port.mistake:32} {record['strict']:16} {record['lenient']}", flush=True)
    return record


def _static_catch(stages: list[StageResult]) -> str:
    """
    Name the first static stage whose error reports the mistake, or give "" when none does.

    It counts the findings the strict column counts: errors at the change and
    errors a case's note accepts, in the order a developer meets the stages.
    """
    if earliest(stages, None, count_warnings=False, accept_indirect=True) not in STATIC_STAGES:
        return ""
    return next(
        stage.label
        for name in STATIC_STAGES
        for stage in stages
        if stage.stage == name and (stage.error or stage.indirect_error)
    )


def default_jobs() -> int:
    """Use half the CPUs, at most 8: each case runs tools and a browser that use several cores at once."""
    return max(1, min(8, (os.cpu_count() or 2) // 2))


def _interleave(groups: list[list[T]]) -> list[T]:
    """Take one item from each group in turn, so the workers run several frameworks' cases side by side."""
    return [item for row in itertools.zip_longest(*groups) for item in row if item is not None]


def _new_run_dir(run_id: str) -> Path:
    """Create the run's folder, adding a number when a run that started in the same second already has the name."""
    (CACHE / "runs").mkdir(parents=True, exist_ok=True)
    for attempt in itertools.count(1):
        run_dir = CACHE / "runs" / (run_id if attempt == 1 else f"{run_id}-{attempt}")
        try:
            run_dir.mkdir()
        except FileExistsError:
            continue
        return run_dir
    raise AssertionError("unreachable")


def run(args: argparse.Namespace) -> Path:
    frameworks = load_frameworks()
    ports = load_ports()
    mistakes = load_catalogue()
    selected = [frameworks[key] for key in (args.framework or frameworks)]
    # A broken case would otherwise stop the run when it is reached, perhaps
    # tens of minutes in, and leave no results.
    problems_found = validate(frameworks, ports)
    if problems_found:
        raise ConfigError("the cases do not validate:\n" + "\n".join(problems_found))
    run_dir = _new_run_dir(datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    (run_dir / "run.json").write_text(json.dumps(_source() | {"jobs": args.jobs}, indent=2) + "\n")
    for framework in selected:
        prepare(framework)
    # Each clean app runs alone, before any case: every case of its framework
    # is compared with it, so its timings must not suffer from other work
    # competing for the machine.
    baselines = {
        framework.key: _run_baseline(framework, run_dir, observe_runtime=not args.skip_runtime)
        for framework in selected
    }
    chosen = [mistake for mistake in mistakes if not args.mistake or mistake.id in args.mistake]
    tasks = _interleave(
        [
            [
                (framework, port)
                for mistake in chosen
                if (port := ports.get((mistake.id, framework.key))) is not None and port.status == "ported"
            ]
            for framework in selected
        ]
    )
    scored = parallel.run_all(
        tasks,
        lambda task: _run_case(task[0], task[1], baselines[task[0].key], run_dir),
        jobs=args.jobs,
        group=lambda task: task[0].key,
        limits={framework.key: framework.max_jobs for framework in selected if framework.max_jobs},
        stop=threading.Event(),
    )
    by_case = {(framework.key, port.mistake): record for (framework, port), record in zip(tasks, scored, strict=True)}
    # Records keep the framework and catalogue order, whatever order the cases finished in.
    records = []
    for framework in selected:
        for mistake in chosen:
            port = ports.get((mistake.id, framework.key))
            record: dict = {"framework": framework.key, "mistake": mistake.id}
            if port is None or port.status != "ported":
                record |= {"status": port.status if port else "missing", "reason": port.reason if port else ""}
            else:
                record |= by_case[(framework.key, mistake.id)]
            records.append(record)
    (run_dir / "results.jsonl").write_text("".join(json.dumps(record) + "\n" for record in records))
    return run_dir


def _positive(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="citry-errors", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="check that every mistake has a port in every framework")
    prep = commands.add_parser("prepare", help="install each framework's locked dependencies")
    prep.add_argument("--framework", action="append")
    run_cmd = commands.add_parser("run", help="run the static stages and the browser check for each case")
    run_cmd.add_argument("--framework", action="append")
    run_cmd.add_argument("--mistake", action="append")
    run_cmd.add_argument("--skip-runtime", action="store_true")
    run_cmd.add_argument(
        "--jobs",
        type=_positive,
        default=default_jobs(),
        help=f"how many cases run at once (default: {default_jobs()}, half the CPUs, at most 8)",
    )
    rep = commands.add_parser("report", help="write the matrix for one run")
    rep.add_argument("run_dir", type=Path)
    rep.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            problems = validate(load_frameworks(), load_ports())
            for problem in problems:
                print(problem)
            return 1 if problems else 0
        if args.command == "prepare":
            for key, framework in load_frameworks().items():
                if not args.framework or key in args.framework:
                    print(f"{key}: {prepare(framework)}")
            return 0
        if args.command == "run":
            print(run(args))
            return 0
        report.write(args.run_dir, args.output)
        return 0
    except ConfigError as error:
        print(f"citry-errors: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
