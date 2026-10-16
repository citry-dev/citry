"""Run isolated, locally retained framework comparisons."""

import argparse
import json
import os
import platform
import random
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import Browser, sync_playwright

from citry_bench.browser import record_not_run_session, run_session
from citry_bench.compose import compose
from citry_bench.config import CACHE, ROOT, digest, profile
from citry_bench.lifecycle import application
from citry_bench.memory import ProcessIdentity, SessionMemoryObserver, endpoint_process_memory, pin_process
from citry_bench.prepare import environment, prepare, prepared, write_json
from citry_bench.qualification import qualify_faults
from citry_bench.results import append, report


def run_page_pair(
    browser: Browser,
    base: str,
    settings: dict,
    directory: Path,
    info: dict,
    *,
    adapter: dict | None,
    memory_path: Path | None = None,
    idle_server: dict | None = None,
    server_identity: ProcessIdentity | None = None,
) -> bool:
    """Measure two asset-cold page loads before actions in one server process."""
    first = {**info, "session": uuid4().hex, "page_load": 1}
    first_observer = (
        SessionMemoryObserver(memory_path, first, server_identity, idle_server or {}, browser) if memory_path else None
    )
    first_ok = run_session(
        browser, base, settings, directory, first, adapter=adapter, initial_only=True, memory_observer=first_observer
    )
    second = {**info, "session": uuid4().hex, "page_load": 2}
    if not first_ok:
        record_not_run_session(
            settings,
            directory,
            second,
            reason="first page load did not complete correctly",
        )
        return False
    second_observer = (
        SessionMemoryObserver(memory_path, second, server_identity, idle_server or {}, browser)
        if memory_path
        else None
    )
    return run_session(
        browser,
        base,
        settings,
        directory,
        second,
        adapter=adapter,
        initial_only=False,
        memory_observer=second_observer,
    )


def execute_memory(settings: dict, *, output: Path | None = None) -> Path:
    """Run correctness-qualified memory sessions separately from latency runs."""
    build, evidence = prepared(settings)
    qualification_path = build / "qualification.json"
    if not qualification_path.exists():
        raise ValueError(f"Run qualify --profile {settings['name']} before memory measurement")
    proof = json.loads(qualification_path.read_text())
    if proof.get("status") != "passed" or proof.get("identity") != digest(evidence["inputs"]):
        raise ValueError("Qualification failed or is stale; qualify the current inputs")
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-memory-" + uuid4().hex[:8]
    directory = (output or CACHE / "runs") / run_id
    directory.mkdir(parents=True)
    for name in ("samples.jsonl", "sizes.jsonl", "server-timings.jsonl", "memory.jsonl"):
        (directory / name).touch()
    manifest = {
        "schema": 1,
        "kind": "memory",
        "id": run_id,
        "status": "running",
        "scenario_revision": settings["scenario_revision"],
        "inputs": evidence,
        "command": sys.argv,
        "host": platform.uname()._asdict(),
        "sample_interval_ms": 50,
        "limitations": [
            "memory-only run; values are not latency samples",
            "process-tree RSS can count shared resident pages more than once",
            "sampled peaks can miss spikes between observations",
            "forced V8 garbage collection runs only at each page's last observation, after its response "
            "bodies are read; ordinary heap readings, including the last observation's, can include "
            "uncollected garbage; no heap dumps",
        ],
    }
    write_json(directory / "manifest.json", manifest)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = environment()["PLAYWRIGHT_BROWSERS_PATH"]
    successful = True
    try:
        with sync_playwright() as playwright:
            manifest["browser"] = {
                "executable": playwright.chromium.executable_path,
                "dedicated_instance_per": "page-pair",
            }
            order = settings["apps"][:]
            random.Random(settings["seed"]).shuffle(order)
            for block in range(settings["blocks"]):
                for count in settings["counts"]:
                    for name in order:
                        with application(
                            build / "apps" / name, directory / "logs" / f"{block}-{count}-{name}.log"
                        ) as server:
                            server_identity = pin_process(server["pid"])
                            idle_server = endpoint_process_memory(server_identity)
                            for session_index in range(settings["sessions"]):
                                browser = playwright.chromium.launch()
                                manifest["browser"]["version"] = browser.version
                                info = {
                                    "run": run_id,
                                    "block": block,
                                    "app": name,
                                    "count": count,
                                    "session_index": session_index,
                                    "process": server["pid"],
                                    "server_command": server["command"],
                                }
                                try:
                                    ok = run_page_pair(
                                        browser,
                                        server["url"],
                                        settings,
                                        directory,
                                        info,
                                        adapter=server["adapter"],
                                        memory_path=directory / "memory.jsonl",
                                        idle_server=idle_server,
                                        server_identity=server_identity,
                                    )
                                    successful = ok and successful
                                finally:
                                    browser.close()
            manifest["status"] = "passed" if successful else "failed"
    except BaseException as error:
        manifest["status"] = "incomplete"
        manifest["error"] = repr(error)
        raise
    finally:
        write_json(directory / "manifest.json", manifest)
        report(directory)
    return directory


def qualification_faults_after_page_pairs(
    browser: Browser,
    base: str,
    settings: dict,
    count: int,
    adapter: dict,
    *,
    page_pairs_ok: bool,
) -> list[dict]:
    """Exercise fault cases only after the normal page-load contract passes."""
    return qualify_faults(browser, base, settings, count, adapter) if page_pairs_ok else []


def execute(settings: dict, *, qualification: bool, output: Path | None = None) -> Path:
    build, evidence = prepared(settings)
    qualification_path = build / "qualification.json"
    if qualification:
        qualification_path.unlink(missing_ok=True)
    if not qualification:
        if not qualification_path.exists():
            raise ValueError(f"Run qualify --profile {settings['name']} before measurement")
        proof = json.loads(qualification_path.read_text())
        if proof.get("status") != "passed" or proof.get("identity") != digest(evidence["inputs"]):
            raise ValueError("Qualification failed or is stale; qualify the current inputs")
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = (output or CACHE / "runs") / run_id
    directory.mkdir(parents=True)
    for name in ("samples.jsonl", "sizes.jsonl", "server-timings.jsonl"):
        (directory / name).touch()
    manifest = {
        "schema": 1,
        "id": run_id,
        "status": "running",
        "qualification": qualification,
        "scenario_revision": settings["scenario_revision"],
        "build": str(build),
        "inputs": evidence,
        "command": sys.argv,
        "host": platform.uname()._asdict(),
        "cpu_count": os.cpu_count(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "limitations": [
            "native loopback HTTP and single WebSocket; identity encoding",
            evidence["source_policy"],
            "diagnostic descriptive summaries, no publication ranking",
            "two asset-cold browser contexts and distinct logical sessions share one application process",
            "only session index zero starts with the process's first measured page request",
        ],
    }
    write_json(directory / "manifest.json", manifest)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = environment()["PLAYWRIGHT_BROWSERS_PATH"]
    successful = True
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            manifest["browser"] = {"version": browser.version, "executable": playwright.chromium.executable_path}
            order = settings["apps"][:]
            random.Random(settings["seed"]).shuffle(order)
            for block in range(settings["blocks"]):
                rotated = order[block % len(order) :] + order[: block % len(order)]
                if (block // len(order)) % 2:
                    rotated.reverse()
                for count in settings["counts"]:
                    for name in rotated:
                        with application(
                            build / "apps" / name, directory / "logs" / f"{block}-{count}-{name}.log"
                        ) as server:
                            page_pairs_ok = True
                            for session_index in range(settings["sessions"]):
                                info = {
                                    "run": run_id,
                                    "block": block,
                                    "app": name,
                                    "count": count,
                                    "session_index": session_index,
                                    "process": server["pid"],
                                    "server_command": server["command"],
                                }
                                pair_ok = run_page_pair(
                                    browser,
                                    server["url"],
                                    settings,
                                    directory,
                                    info,
                                    adapter=server["adapter"],
                                )
                                page_pairs_ok = pair_ok and page_pairs_ok
                                successful = pair_ok and successful
                            if qualification and block == 0:
                                try:
                                    faults = qualification_faults_after_page_pairs(
                                        browser,
                                        server["url"],
                                        settings,
                                        count,
                                        server["adapter"],
                                        page_pairs_ok=page_pairs_ok,
                                    )
                                    for fault in faults:
                                        append(
                                            directory / "qualification.jsonl", {"app": name, "count": count, **fault}
                                        )
                                except Exception as error:
                                    append(
                                        directory / "qualification.jsonl",
                                        {
                                            "app": name,
                                            "count": count,
                                            "status": "failed",
                                            "error": repr(error),
                                        },
                                    )
                                    successful = False
            browser.close()
        # Editing inputs during a run cannot qualify a different executable state.
        prepared(settings)
        manifest["status"] = "passed" if successful else "failed"
    except BaseException as error:
        manifest["status"] = "incomplete"
        manifest["error"] = repr(error)
        raise
    finally:
        write_json(directory / "manifest.json", manifest)
        report(directory)
    if qualification:
        write_json(
            qualification_path,
            {
                "identity": digest(evidence["inputs"]),
                "status": manifest["status"],
                "run": str(directory),
                "browser": manifest["browser"],
            },
        )
    return directory


def run_directory(value: str) -> Path:
    """Accept a run folder path or the id of a run under `.benchmarks/runs/`."""
    # Absolute, so a composed manifest's run paths work from any folder.
    path = Path(value)
    return (path if path.is_dir() else CACHE / "runs" / value).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "qualify", "run", "memory"):
        command = commands.add_parser(name)
        command.add_argument("--profile", default="smoke")
        if name != "prepare":
            command.add_argument("--output-dir", type=Path)
    report_command = commands.add_parser("report")
    report_command.add_argument("run")
    report_command.add_argument("--memory-run")
    compose_command = commands.add_parser("compose")
    compose_command.add_argument("--output", type=Path, required=True)
    # One qualification run and the measurement run made from the same build,
    # repeated for each run whose apps the combined report takes.
    compose_command.add_argument(
        "--runs", nargs=2, action="append", required=True, metavar=("QUALIFY_RUN", "MEASUREMENT_RUN")
    )
    args = parser.parse_args()
    try:
        if args.command == "compose":
            pairs = [(run_directory(qualification), run_directory(run)) for qualification, run in args.runs]
            path = compose(args.output, pairs, command=sys.argv)
        elif args.command == "report":
            path = run_directory(args.run)
            memory_path = run_directory(args.memory_run) if args.memory_run else None
            report(path, memory_directory=memory_path)
        else:
            settings = profile(args.profile)
            path = (
                prepare(settings)
                if args.command == "prepare"
                else (
                    execute_memory(settings, output=args.output_dir)
                    if args.command == "memory"
                    else execute(settings, qualification=args.command == "qualify", output=args.output_dir)
                )
            )
        print(path)
        if args.command in ("qualify", "run", "memory"):
            return 0 if json.loads((path / "manifest.json").read_text())["status"] == "passed" else 1
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"citry-bench: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
