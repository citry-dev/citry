"""Command line: validate the cases, install the frameworks, run the matrix and write the report."""

from __future__ import annotations

import argparse
import itertools
import json
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import cache, parallel, report
from .compare import compare, problems
from .config import (
    BENCH_ROOT,
    CACHE,
    REPO_ROOT,
    STATIC_STAGES,
    ConfigError,
    Framework,
    Mistake,
    Port,
    load_catalogue,
    load_frameworks,
    load_ports,
)
from .execute import StageOutput, run_stages
from .parsers import PARSE, Finding, ToolUnavailable
from .runtime import Observation, observe
from .score import StageResult, earliest, score_stage
from .work import changed_files, env_dir, materialize, mistake_lines, prepare


def _record_stages(
    framework: Framework, outputs: list[StageOutput], work: Path, out: Path
) -> list[list[Finding] | None]:
    """
    Write each stage's raw output into the run folder and turn it into findings.

    The output may come from this run or from the cache; parsing it here, on
    every run, lets a parser change take effect without running the tools again.
    A stage that timed out gives None: its missing output must neither count
    as catching the mistake nor as missing it.
    """
    results: list[list[Finding] | None] = []
    for index, (stage, output) in enumerate(zip(framework.stages, outputs, strict=True)):
        command = f"$ {' '.join(output.argv)}\n"
        if output.exit_code is None:
            (out / f"stage-{index}.out").write_text(f"{command}# timed out after {output.timeout} s\n")
            results.append(None)
            continue
        (out / f"stage-{index}.out").write_text(
            f"{command}# exit {output.exit_code}\n{output.stdout}\n# stderr\n{output.stderr}"
        )
        try:
            results.append(PARSE[stage.parser](output.stdout, output.stderr, output.exit_code, work))
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


# The parts of the benchmark folder that decide a run's result: the mistakes,
# each framework's app and cases, and the runner. The published results
# folder is left out, because it changes after the run that wrote it.
INPUT_NAMES = ("cases", "catalogue.toml", "frameworks", "runner")


def _source() -> dict:
    """
    Record what a run starts from, so a published result names the cases it scored.

    A commit's hash changes when the branch is rebased, as GitHub does when it
    merges a stack of pull requests, so the record also names the git tree of
    the benchmark's inputs. That tree id stays the same as long as the inputs
    do, and the README shows how to work it out again for any commit.
    """

    def git(*argv: str, stdin: str | None = None) -> str:
        completed = subprocess.run(
            ["git", *argv], cwd=REPO_ROOT, input=stdin, capture_output=True, text=True, check=False
        )
        return completed.stdout.strip()

    folder = BENCH_ROOT.relative_to(REPO_ROOT).as_posix()
    # Uncommitted changes under the benchmark folder mean the commit alone
    # does not describe the cases that ran.
    changed = git("status", "--porcelain", "--", folder)
    inputs_changed = git("status", "--porcelain", "--", *(f"{folder}/{name}" for name in INPUT_NAMES))
    # `git mktree` turns the listing of the input entries into one tree; the
    # README gives the same two commands for checking a published run.
    listing = git("ls-tree", f"HEAD:{folder}", *INPUT_NAMES)
    inputs_tree = git("mktree", stdin=listing + "\n") if listing else ""
    return {
        "commit": git("rev-parse", "HEAD"),
        "benchmark_files_changed": bool(changed),
        "inputs_tree": inputs_tree,
        "inputs_changed": bool(inputs_changed),
    }


_print_lock = threading.Lock()


@dataclass
class Baseline:
    """The clean app's results for one framework, which every case of that framework is compared with."""

    findings: list[list[Finding] | None]
    runtime: Observation | None
    # What made the clean app's run unusable as the comparison point; empty when it was clean.
    errors: list[str]


@dataclass
class Context:
    """What every case of one run shares."""

    run_dir: Path
    observe_runtime: bool
    # False with --no-cache: run everything, and store the fresh output.
    reuse: bool
    environment: str
    framework_digests: dict[str, str]
    # Set on Ctrl-C. The child processes of running cases may have been
    # killed by the same signal, so nothing finished after it is stored.
    stop: threading.Event


def _entry_folder(framework: Framework, name: str) -> Path:
    return CACHE / "results" / framework.key / name


def _stages_for(
    context: Context, framework: Framework, port: Port | None, work: Path
) -> tuple[str, cache.Entry | None, list[StageOutput]]:
    """Give a working copy's raw stage output: stored when its inputs are unchanged, else from running the tools."""
    key = cache.case_key(context.environment, context.framework_digests[framework.key], port, work)
    folder = _entry_folder(framework, "baseline" if port is None else port.mistake)
    entry = cache.load(folder, key) if context.reuse else None
    return key, entry, entry.stages if entry else run_stages(framework, work, context.stop)


def _observe(framework: Framework, entry: cache.Entry | None, work: Path, out: Path) -> tuple[Observation, bool]:
    """Give the browser check for a working copy, reusing a stored one, and say whether it was reused."""
    log = out / "server.log"
    if entry is not None and entry.observation is not None and entry.server_log is not None:
        shutil.copyfile(entry.server_log, log)
        observation, reused = entry.observation, True
    else:
        observation, reused = observe(framework, env_dir(framework), work, log), False
    (out / "runtime.json").write_text(observation.to_json())
    return observation, reused


def _store(
    context: Context,
    folder: Path,
    key: str,
    stages: list[StageOutput],
    observation: Observation | None,
    log: bytes | None,
) -> None:
    """Store a case's fresh raw output for the next run, leaving out what says more about the machine than the case."""
    if context.stop.is_set() or not cache.keeps(stages):
        return
    # A server that never answered, or a journey that ran out of time, may
    # only have been slow under load, so the browser check runs again next
    # time; the stage output is still kept.
    kept = observation if observation is not None and cache.keeps_observation(observation) else None
    cache.store(folder, key, stages, kept, log if kept else None)


def _run_baseline(context: Context, framework: Framework) -> tuple[Baseline, bool]:
    """Run the clean app, or reuse its stored output, and say whether everything was reused."""
    base_out = context.run_dir / framework.key / "baseline"
    base_out.mkdir(parents=True)
    base = materialize(framework, None)
    key, entry, outputs = _stages_for(context, framework, None, base.path)
    findings = _record_stages(framework, outputs, base.path, base_out)
    runtime: Observation | None = None
    reused = entry is not None
    if framework.runtime and context.observe_runtime:
        # A fresh copy, as for every case's browser check.
        base = materialize(framework, None)
        runtime, runtime_reused = _observe(framework, entry, base.path, base_out)
        reused = reused and runtime_reused
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
    # A clean app with problems is never stored: the problem may come from
    # the machine, and every case of the framework is compared with it.
    if not reused and not errors:
        log = (base_out / "server.log").read_bytes() if runtime is not None else None
        _store(context, _entry_folder(framework, "baseline"), key, outputs, runtime, log)
    return Baseline(findings, runtime, errors), reused


def _run_case(context: Context, framework: Framework, port: Port, baseline: Baseline) -> tuple[dict, bool]:
    """
    Run one case's stages and browser check, or reuse their stored output, and score them against the clean app.

    Runs on a worker thread. Also says whether everything the case needed came from the cache.
    """
    out = context.run_dir / framework.key / port.mistake
    out.mkdir(parents=True)
    copy = materialize(framework, port)
    key, entry, outputs = _stages_for(context, framework, port, copy.path)
    findings = _record_stages(framework, outputs, copy.path, out)
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
    observation = None
    reused = entry is not None
    caught_by = _static_catch(stages)
    # The benchmark scores only where a mistake is first reported. A static
    # error decides both columns, because the lenient one counts errors too,
    # so the browser check could not change the cell and is skipped. A static
    # warning alone leaves the strict column to the browser check, which runs.
    # The decision is made again on every run, from the current scoring, so
    # a stored case whose static catch no longer counts gets its browser check.
    if baseline.runtime is not None and not caught_by:
        if context.stop.is_set():
            raise parallel.Stopped
        # The server starts from a fresh copy, without what the tools wrote
        # (such as a production build), so the browser check sees the same
        # files whether the tools ran in this run or an earlier one.
        copy = materialize(framework, port)
        observation, runtime_reused = _observe(framework, entry, copy.path, out)
        runtime_result = compare(baseline.runtime, observation)
        reused = reused and runtime_reused
    # A case compared with a clean app that had problems is not stored: the
    # problem may come from the machine, such as a broken environment, and
    # would then be reused after the machine is fixed.
    if not reused and not baseline.errors:
        log = (out / "server.log").read_bytes() if observation is not None else None
        _store(context, _entry_folder(framework, port.mistake), key, outputs, observation, log)
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
    source = "(stored)" if reused else ""
    # One write per line under a lock: workers finishing together would
    # otherwise interleave their lines and newlines.
    with _print_lock:
        print(
            f"{framework.key:10} {port.mistake:32} {record['strict']:16} {record['lenient']:16} {source}", flush=True
        )
    return record, reused


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


def _interleave[T](groups: list[list[T]]) -> list[T]:
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
    with cache.exclusive(CACHE):
        return _run_locked(args, selected, ports, mistakes)


def _run_locked(
    args: argparse.Namespace, selected: list[Framework], ports: dict[tuple[str, str], Port], mistakes: list[Mistake]
) -> Path:
    run_dir = _new_run_dir(datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    source = _source() | {"jobs": args.jobs}
    (run_dir / "run.json").write_text(json.dumps(source, indent=2) + "\n")
    for framework in selected:
        prepare(framework)
    context = Context(
        run_dir=run_dir,
        observe_runtime=not args.skip_runtime,
        reuse=not args.no_cache,
        environment=cache.environment_digest(),
        framework_digests={
            framework.key: cache.framework_digest(framework, env_dir(framework)) for framework in selected
        },
        stop=threading.Event(),
    )
    reused_baselines: list[str] = []
    # Each clean app runs alone, before any case: every case of its framework
    # is compared with it, so its page and logs are recorded without other
    # work competing for the machine.
    baselines = {}
    for framework in selected:
        baselines[framework.key], from_cache = _run_baseline(context, framework)
        reused_baselines += [f"{framework.key}/baseline"] if from_cache else []
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
        lambda task: _run_case(context, task[0], task[1], baselines[task[0].key]),
        jobs=args.jobs,
        group=lambda task: task[0].key,
        limits={framework.key: framework.max_jobs for framework in selected if framework.max_jobs},
        stop=context.stop,
    )
    by_case = {(framework.key, port.mistake): result for (framework, port), result in zip(tasks, scored, strict=True)}
    # Records keep the framework and catalogue order, whatever order the cases finished in.
    records = []
    reused_cases = []
    for framework in selected:
        for mistake in chosen:
            port = ports.get((mistake.id, framework.key))
            record: dict = {"framework": framework.key, "mistake": mistake.id}
            if port is None or port.status != "ported":
                record |= {"status": port.status if port else "missing", "reason": port.reason if port else ""}
            else:
                scored_record, from_cache = by_case[(framework.key, mistake.id)]
                record |= scored_record
                reused_cases += [f"{framework.key}/{mistake.id}"] if from_cache else []
            records.append(record)
    (run_dir / "results.jsonl").write_text("".join(json.dumps(record) + "\n" for record in records))
    # Names the clean apps and cases whose every output came from an earlier
    # run's stored output, so a reader can tell what this run ran itself.
    (run_dir / "run.json").write_text(
        json.dumps(source | {"reused": reused_baselines + reused_cases}, indent=2) + "\n"
    )
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
        "--no-cache", action="store_true", help="run every case again instead of reusing stored output"
    )
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
            # Installing into an environment a run is using would change its tools mid-run.
            with cache.exclusive(CACHE):
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
