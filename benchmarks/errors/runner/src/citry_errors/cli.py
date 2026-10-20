"""Command line: validate the cases, install the frameworks, run the matrix and write the report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from . import report
from .config import (
    BENCH_ROOT,
    CACHE,
    REPO_ROOT,
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
from .work import command_env, env_dir, materialize, placeholder, prepare


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
            if port.status != "ported":
                continue
            for published in port.files:
                if not (framework.baseline / published).is_file():
                    problems.append(f"{port.root}: {published} is not a baseline file")
            source = port.files.get(port.mistake_file)
            if source is not None:
                count = sum(port.mistake_contains in line for line in source.read_text().splitlines())
                if count != 1:
                    problems.append(f"{port.root}: mistake text is on {count} lines, expected 1")
    return problems


def _source() -> dict:
    """Record the commit a run starts from, so a published result names the cases it scored."""

    def git(*argv: str) -> str:
        completed = subprocess.run(["git", *argv], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        return completed.stdout.strip()

    # Uncommitted changes under the benchmark folder mean the commit alone
    # does not describe the cases that ran.
    changed = git("status", "--porcelain", "--", str(BENCH_ROOT.relative_to(REPO_ROOT)))
    return {"commit": git("rev-parse", "HEAD"), "benchmark_files_changed": bool(changed)}


def run(args: argparse.Namespace) -> Path:
    frameworks = load_frameworks()
    ports = load_ports()
    mistakes = load_catalogue()
    selected = [frameworks[key] for key in (args.framework or frameworks)]
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = CACHE / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(json.dumps(_source(), indent=2) + "\n")
    records = []
    for framework in selected:
        prepare(framework)
        env = env_dir(framework)
        base_out = run_dir / framework.key / "baseline"
        base_out.mkdir(parents=True)
        base = materialize(framework, None)
        baseline_findings = _run_stages(framework, base.path, base_out)
        baseline_runtime: Observation | None = None
        if framework.runtime and not args.skip_runtime:
            baseline_runtime = observe(framework, env, base.path, base_out / "server.log")
            (base_out / "runtime.json").write_text(baseline_runtime.to_json())
        # The clean app must pass every stage, or a case's finding could not be
        # told apart from noise that was already there.
        baseline_errors = [
            f"{framework.stages[index].label}: {finding.message}"
            for index, findings in enumerate(baseline_findings)
            for finding in findings or []
            if finding.severity == "error"
        ] + [
            f"{framework.stages[index].label}: timed out"
            for index, findings in enumerate(baseline_findings)
            if findings is None
        ]
        if baseline_runtime:
            baseline_errors += [f"runtime: {problem}" for problem in problems(baseline_runtime)]
        (base_out / "baseline-errors.json").write_text(json.dumps(baseline_errors, indent=2))
        for mistake in mistakes:
            if args.mistake and mistake.id not in args.mistake:
                continue
            port = ports.get((mistake.id, framework.key))
            record: dict = {"framework": framework.key, "mistake": mistake.id}
            if port is None or port.status != "ported":
                record |= {"status": port.status if port else "missing", "reason": port.reason if port else ""}
                records.append(record)
                continue
            out = run_dir / framework.key / mistake.id
            out.mkdir(parents=True)
            copy = materialize(framework, port)
            findings = _run_stages(framework, copy.path, out)
            stages: list[StageResult] = [
                score_stage(
                    stage.stage,
                    stage.label,
                    baseline_findings[index],
                    findings[index],
                    port.mistake_file,
                    copy.mistake_line,
                    port.window,
                    port.indirect_codes,
                )
                for index, stage in enumerate(framework.stages)
            ]
            runtime_result = None
            if baseline_runtime is not None:
                observation = observe(framework, env, copy.path, out / "server.log")
                (out / "runtime.json").write_text(observation.to_json())
                runtime_result = compare(baseline_runtime, observation)
            record |= {
                "status": "ported",
                "baseline_clean": not baseline_errors,
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
            }
            records.append(record)
            print(f"{framework.key:10} {mistake.id:32} {record['strict']:16} {record['lenient']}", flush=True)
    (run_dir / "results.jsonl").write_text("".join(json.dumps(record) + "\n" for record in records))
    return run_dir


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
