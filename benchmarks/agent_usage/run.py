"""Prepare isolated Citry application tasks and record Codex runs with Docker."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = "citry-agent-eval:local"
AUTH_VOLUME = "citry-agent-eval-auth"
ARMS = ("homepage", "llms", "full", "guidance", "skill", "inline", "skill-auto")
CASES = ("cards", "browser", "events")
SKILL = ROOT / "treatments/citry-consumer/SKILL.md"
USER = f"{os.getuid() or 1000}:{os.getgid() or 1000}"
DOCKER = shutil.which("docker") or "docker"


def stamp() -> str:
    """Use UTC timestamps for comparing records from different machines."""
    return datetime.now(timezone.utc).isoformat()


def call(command: list[str], *, capture: bool = False, **kwargs: object) -> subprocess.CompletedProcess:
    """Run argument arrays so paths and prompts never become shell code."""
    return subprocess.run(command, check=True, text=True, capture_output=capture, **kwargs)


def docker(*args: str, capture: bool = False, **kwargs: object) -> subprocess.CompletedProcess:
    return call([DOCKER, *args], capture=capture, **kwargs)


def write_json(path: Path, value: object) -> None:
    # Exclusive creation prevents a submitted symlink from redirecting host writes.
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".record-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(json.dumps(value, indent=2) + "\n")
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_artifact(path: Path) -> str:
    """Read a stopped container's small regular report without following links."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 10_000_000:
        raise ValueError(f"Expected a small regular report: {path.name}")
    return path.read_text()


def tree_hash(path: Path) -> str:
    """Hash inputs by relative name and contents, without machine-specific paths."""
    result = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_symlink():
            raise ValueError(f"Input contains a symlink: {file}")
        if file.is_file() and not any(part in {"__pycache__", ".pytest_cache"} for part in file.parts):
            result.update(file.relative_to(path).as_posix().encode() + b"\0")
            result.update(file.read_bytes())
    return result.hexdigest()


def bind(path: Path, target: str, *, readonly: bool = False) -> list[str]:
    source = str(path.resolve())
    if "," in source:
        raise ValueError("Docker mount paths cannot contain commas")
    return ["--mount", f"type=bind,src={source},dst={target}" + (",readonly" if readonly else "")]


def limits() -> list[str]:
    # Docker owns the execution boundary; no host socket or home is mounted.
    return [
        "--init",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=512",
        "--memory=4g",
        "--cpus=2",
        "--shm-size=256m",
        "--read-only",
        "--tmpfs=/tmp:rw,exec,mode=1777",
        "--tmpfs=/home/agent:rw,exec,mode=1777",
        "--user",
        USER,
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
    ]


def skill_body() -> str:
    return SKILL.read_text().split("---", 2)[2].strip()


def prompt(case: str, arm: str, timeout: int) -> str:
    instructions = {
        "homepage": "Use https://citry.dev/.",
        "llms": "Use https://citry.dev/llms.txt.",
        "full": "Use https://citry.dev/llms-full.txt.",
        "guidance": "Use https://citry.dev/llms.txt to find the relevant documentation. Fetch the linked "
        "Markdown guides and API references for this task, check compatibility with the installed "
        "Citry version, and verify the implementation by running it.",
        "skill": "Use https://citry.dev/llms.txt. Use $citry-consumer for this task.",
        "inline": "Use https://citry.dev/llms.txt.\n\n" + skill_body(),
        "skill-auto": "Use https://citry.dev/llms.txt.",
    }
    return (
        (ROOT / "common.md").read_text().strip()
        + f"\n\nTime limit: {timeout} seconds.\n\n"
        + instructions[arm]
        + "\n\n"
        + (ROOT / "cases" / case / "task.md").read_text()
    )


def image_id(image: str) -> str:
    return docker("image", "inspect", image, "--format", "{{.Id}}", capture=True).stdout.strip()


def prepare(args: argparse.Namespace) -> Path:
    """Copy only declared starter files into the directory visible to the agent."""
    if args.timeout <= 0:
        raise ValueError("timeout must be positive")
    identifier = f"{args.case}-{args.arm}-{uuid.uuid4().hex[:10]}"
    directory = args.out.resolve() / identifier
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    workspace = directory / "workspace"
    shutil.copytree(ROOT / "cases" / args.case / "starter", workspace)
    if args.arm in {"skill", "skill-auto"}:
        target = workspace / ".agents/skills/citry-consumer"
        target.mkdir(parents=True)
        shutil.copy2(SKILL, target / "SKILL.md")
    text = prompt(args.case, args.arm, args.timeout)
    (directory / "prompt.md").write_text(text)
    manifest = {
        "id": identifier,
        "case": args.case,
        "arm": args.arm,
        "model": args.model,
        "effort": args.effort,
        "timeout_seconds": args.timeout,
        "image": image_id(args.image),
        "image_tag": args.image,
        "created_at": stamp(),
        "status": "prepared",
        "docs_mode": "live-public",
        "prompt_sha256": digest(directory / "prompt.md"),
        "starter_sha256": tree_hash(workspace),
        "case_sha256": tree_hash(ROOT / "cases" / args.case),
        "grader_sha256": tree_hash(ROOT / "grading"),
        "skill_sha256": digest(SKILL),
        "runner_sha256": digest(Path(__file__)),
        "resources": {"cpus": 2, "memory": "4g"},
    }
    write_json(directory / "run.json", manifest)
    print(directory)
    return directory


def load_run(directory: Path) -> tuple[Path, dict]:
    directory = directory.resolve()
    manifest = json.loads((directory / "run.json").read_text())
    if manifest["case"] not in CASES or manifest["arm"] not in ARMS:
        raise ValueError("Unknown case or condition in run.json")
    if not re.fullmatch(r"[a-z0-9-]+", manifest["id"]):
        raise ValueError("Invalid run identifier")
    return directory, manifest


def auth_helper(image: str, volume: str, code: str, *, extra: list[str] | None = None) -> None:
    # Helpers see credential volumes only. Credentials never cross stdout.
    docker(
        "run",
        "--rm",
        "--network=none",
        "--user=0",
        "--mount",
        f"type=volume,src={volume},dst=/auth",
        *(extra or []),
        image,
        "python",
        "-c",
        code,
    )


def login(args: argparse.Namespace) -> None:
    docker("volume", "create", AUTH_VOLUME, capture=True)
    auth_helper(
        args.image,
        AUTH_VOLUME,
        f"import os; os.chown('/auth', {USER.split(':')[0]}, {USER.split(':')[1]}); os.chmod('/auth', 0o700)",
    )
    if args.auth_file:
        source = args.auth_file.resolve(strict=True)
        if not source.is_file():
            raise ValueError("auth-file must be a regular file")
        auth_helper(
            args.image,
            AUTH_VOLUME,
            "import os,shutil; shutil.copyfile('/input-auth','/auth/auth.json'); "
            f"os.chown('/auth/auth.json',{USER.split(':')[0]},{USER.split(':')[1]}); "
            "os.chmod('/auth/auth.json',0o600)",
            extra=bind(source, "/input-auth", readonly=True),
        )
        return
    command = ["run", "--rm", "-i"]
    if args.method in {"device", "shell"} and sys.stdin.isatty():
        command += ["-t"]
    command += [*limits(), "--mount", f"type=volume,src={AUTH_VOLUME},dst=/auth", "-e", "CODEX_HOME=/auth", args.image]
    if args.method == "shell":
        command += ["bash"]
    else:
        command += [
            "codex",
            "-c",
            'cli_auth_credentials_store="file"',
            "login",
            "--device-auth" if args.method == "device" else "--with-api-key",
        ]
    docker(*command)


def copy_auth(image: str, home_volume: str, auth_volume: str, *, restore: bool = False) -> None:
    source, target = ("/home/auth.json", "/auth/auth.json") if restore else ("/auth/auth.json", "/home/auth.json")
    auth_helper(
        image,
        auth_volume,
        "import os,shutil; "
        f"shutil.copyfile({source!r},{target!r}); os.chmod({target!r},0o600); "
        f"os.chown({target!r},{USER.split(':')[0]},{USER.split(':')[1]}); "
        f"os.chown('/home',{USER.split(':')[0]},{USER.split(':')[1]})",
        extra=["--mount", f"type=volume,src={home_volume},dst=/home"],
    )


def event_summary(path: Path) -> dict:
    """Summarize emitted events without treating an agent's claims as grades."""
    usage: dict[str, int] = {}
    tools: dict[str, int] = {}
    messages = []
    completed = False
    errors = []
    malformed = 0
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(event, dict):
            malformed += 1
            continue
        if event.get("type") == "turn.completed":
            completed = True
            for key, value in event.get("usage", {}).items():
                if isinstance(value, int):
                    usage[key] = usage.get(key, 0) + value
        if event.get("type") in {"error", "turn.failed"}:
            errors.append(event)
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            kind = item.get("type", "unknown")
            if kind == "agent_message":
                messages.append(item.get("text", ""))
            else:
                tools[kind] = tools.get(kind, 0) + 1
    return {
        "usage": usage,
        "completed_items": tools,
        "turn_completed": completed,
        "errors": errors,
        "malformed_lines": malformed,
        "final_message": messages[-1] if messages else "",
    }


def container_present(name: str) -> bool:
    """Distinguish a missing container from an unavailable Docker daemon."""
    return bool(docker("ps", "-aq", "--filter", f"name=^/{name}$", capture=True).stdout.strip())


def remove_container(name: str) -> None:
    if container_present(name):
        docker("rm", "-f", name, capture=True)
    if container_present(name):
        raise ValueError(f"Container is still present: {name}")


def run(args: argparse.Namespace) -> None:
    directory, manifest = load_run(args.directory)
    if manifest["status"] != "prepared":
        raise ValueError("A run can start only once. Prepare a fresh run to retry.")
    if digest(Path(__file__)) != manifest["runner_sha256"]:
        raise ValueError("Runner changed since preparation; prepare a fresh run")
    if digest(directory / "prompt.md") != manifest["prompt_sha256"]:
        raise ValueError("The prepared prompt changed; prepare a fresh run")
    if tree_hash(directory / "workspace") != manifest["starter_sha256"]:
        raise ValueError("The prepared workspace changed; prepare a fresh run")
    # The exclusive host lock also protects refresh-token writes across runs.
    lock = ROOT / "runs/.active"
    lock.parent.mkdir(exist_ok=True)
    lock.mkdir()
    (lock / "owner").write_text(manifest["id"])
    name = "citry-eval-" + manifest["id"]
    home = name + "-home"
    image = manifest["image"]
    created = False
    timer_started = False
    try:
        docker("volume", "create", home, capture=True)
        copy_auth(image, home, args.auth_volume)
        docker(
            "run",
            "-d",
            "--name",
            name,
            *limits(),
            *bind(directory / "workspace", "/workspace"),
            "--mount",
            f"type=volume,src={home},dst=/home/agent/.codex",
            "-w",
            "/workspace",
            image,
            "sleep",
            "infinity",
            capture=True,
        )
        created = True
        docker("exec", name, "codex", "-c", 'cli_auth_credentials_store="file"', "login", "status", capture=True)
        # Git setup and image inspection are preparation, excluded from timing.
        docker("exec", name, "git", "init", "-q", "/workspace", capture=True)
        # Docker Desktop reports bind-mount ownership differently from the host UID.
        docker("exec", name, "git", "config", "--global", "--add", "safe.directory", "/workspace", capture=True)
        docker("exec", name, "git", "-C", "/workspace", "add", ".", capture=True)
        docker(
            "exec",
            name,
            "git",
            "-C",
            "/workspace",
            "-c",
            "user.name=Evaluation",
            "-c",
            "user.email=eval@localhost",
            "commit",
            "-qm",
            "Starter",
            capture=True,
        )
        audit = docker("inspect", name, capture=True).stdout
        write_json(directory / "container.json", json.loads(audit))
        versions = docker("exec", name, "cat", "/opt/agent-eval/versions.json", capture=True).stdout
        (directory / "versions.json").write_text(versions)
        command = [
            DOCKER,
            "exec",
            "-i",
            name,
            "codex",
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--dangerously-bypass-approvals-and-sandbox",
            "--color",
            "never",
            "-c",
            'cli_auth_credentials_store="file"',
            "-c",
            'web_search="live"',
            "-c",
            "features.multi_agent=false",
            "-c",
            f'model_reasoning_effort="{manifest["effort"]}"',
            "--model",
            manifest["model"],
            "-",
        ]
        manifest.update(status="running", started_at=stamp(), command=command)
        write_json(directory / "run.json", manifest)
        print(f"Starting {manifest['id']} ({manifest['timeout_seconds']}s limit)", flush=True)
        with (directory / "events.jsonl").open("w") as stdout, (directory / "stderr.log").open("w") as stderr:
            started = time.monotonic()
            timer_started = True
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True)
            try:
                process.communicate((directory / "prompt.md").read_text(), timeout=manifest["timeout_seconds"])
                manifest["status"] = "completed" if process.returncode == 0 else "agent_error"
            except subprocess.TimeoutExpired:
                docker("kill", name, capture=True)
                process.communicate(timeout=30)
                manifest["status"] = "timeout"
            except KeyboardInterrupt:
                docker("kill", name, capture=True)
                process.communicate(timeout=30)
                manifest["status"] = "interrupted"
            # Stop background children before ending the stopwatch or reading logs.
            remove_container(name)
            manifest["container_stopped"] = True
            manifest.update(
                elapsed_seconds=round(time.monotonic() - started, 3), finished_at=stamp(), exit_code=process.returncode
            )
        summary = event_summary(directory / "events.jsonl")
        (directory / "final.md").write_text(summary.pop("final_message") + "\n")
        manifest.update(summary)
        if manifest["status"] == "completed" and not manifest["turn_completed"]:
            manifest["status"] = "incomplete"
    except (subprocess.CalledProcessError, OSError) as error:
        manifest["status"] = "harness_error" if timer_started else "preflight_error"
        # Do not serialize exception output: authentication diagnostics can be sensitive.
        manifest["error"] = f"{type(error).__name__}: inspect local Docker/login state"
        raise
    finally:
        try:
            remove_container(name)
            manifest["container_stopped"] = True
            if created:
                try:
                    copy_auth(image, home, args.auth_volume, restore=True)
                except subprocess.CalledProcessError:
                    manifest["auth_refresh_saved"] = False
                else:
                    manifest["auth_refresh_saved"] = True
            docker("volume", "rm", home, capture=True)
        except (subprocess.CalledProcessError, ValueError):
            manifest["status"] = "cleanup_error"
            manifest["cleanup_required"] = True
            raise
        else:
            (lock / "owner").unlink()
            lock.rmdir()
        finally:
            write_json(directory / "run.json", manifest)
    print(f"{manifest['status']}: {directory}")


def grade(args: argparse.Namespace) -> None:
    directory, manifest = load_run(args.directory)
    if manifest["status"] in {"prepared", "running", "preflight_error", "cleanup_error"}:
        raise ValueError("Grade only a stopped submission")
    if container_present("citry-eval-" + manifest["id"]):
        raise ValueError("The agent container still exists; clean it up before grading")
    if tree_hash(ROOT / "grading") != manifest["grader_sha256"]:
        raise ValueError("Grader changed since preparation; preserve the original grader before grading")
    results = directory / "grade"
    results.mkdir(exist_ok=False)
    name = "citry-grade-" + manifest["id"]
    command = [
        DOCKER,
        "run",
        "--name",
        name,
        "--rm",
        "--network=none",
        *limits(),
        *bind(directory / "workspace", "/workspace", readonly=True),
        *bind(ROOT / "grading", "/grader", readonly=True),
        *bind(results, "/results"),
        "-e",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "-w",
        "/grader",
        manifest["image"],
        "python",
        "-I",
        "-m",
        "pytest",
        "-q",
        "-c",
        "/dev/null",
        "--rootdir=/grader",
        "--confcutdir=/grader",
        "-p",
        "no:cacheprovider",
        f"/grader/test_{manifest['case']}.py",
        "--junitxml=/results/junit.xml",
    ]
    started = time.monotonic()
    try:
        with (results / "output.log").open("w") as output:
            result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=180, check=False)
        record = {"exit_code": result.returncode, "passed": result.returncode == 0, "status": "graded"}
    except subprocess.TimeoutExpired:
        record = {"exit_code": None, "passed": False, "status": "timeout"}
    finally:
        remove_container(name)
    record.update(elapsed_seconds=round(time.monotonic() - started, 3), graded_at=stamp())
    try:
        xml = read_artifact(results / "junit.xml")
        # JUnit has no DTD; reject declarations before parsing generated reports.
        if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
            raise ValueError("JUnit output contains an unexpected XML declaration")
        suites = ET.fromstring(xml)  # noqa: S314 - declarations rejected above
        records = list(suites.iter("testsuite"))
        for key in ("tests", "failures", "errors", "skipped"):
            record[key] = sum(int(suite.get(key, "0")) for suite in records)
    except (OSError, ValueError, ET.ParseError):
        record.update(passed=False, report_status="invalid_or_missing")
    expected = json.loads((ROOT / "grading/cases.json").read_text())[manifest["case"]]["expected_tests"]
    record["expected_tests"] = expected
    record["runner_sha256"] = digest(Path(__file__))
    record["passed"] = (
        record["passed"]
        and record.get("tests") == expected
        and all(record.get(key) == 0 for key in ("failures", "errors", "skipped"))
    )
    write_json(results / "result.json", record)
    print(json.dumps(record, indent=2))


def plan(args: argparse.Namespace) -> None:
    if args.repetitions <= 0:
        raise ValueError("repetitions must be positive")
    cells = [
        (case, arm, repetition)
        for case in args.cases
        for arm in args.arms
        for repetition in range(1, args.repetitions + 1)
    ]
    random.Random(args.seed).shuffle(cells)  # noqa: S311 - reproducible order, not a secret
    directories = []
    for case, arm, repetition in cells:
        values = vars(args) | {"case": case, "arm": arm}
        directory = prepare(argparse.Namespace(**values))
        path, manifest = load_run(directory)
        manifest.update(repetition=repetition, order=len(directories) + 1, seed=args.seed)
        write_json(path / "run.json", manifest)
        directories.append(str(directory))
    target = args.out.resolve() / f"plan-{uuid.uuid4().hex[:10]}.json"
    write_json(target, {"created_at": stamp(), "seed": args.seed, "runs": directories})
    print(f"Plan saved to {target}. No model calls started.")


def report(args: argparse.Namespace) -> None:
    rows = []
    for path in sorted(args.out.resolve().glob("*/run.json")):
        manifest = json.loads(path.read_text())
        grading = path.parent / "grade/result.json"
        try:
            result = json.loads(read_artifact(grading)) if grading.exists() or grading.is_symlink() else {}
        except (OSError, ValueError):
            result = {"passed": False, "status": "invalid_report"}
        rows.append(
            {
                key: manifest.get(key)
                for key in ("id", "case", "arm", "model", "effort", "image", "status", "elapsed_seconds", "usage")
            }
            | {"grade": result}
        )
    print(json.dumps(rows, indent=2))


def execute(args: argparse.Namespace) -> None:
    """Run a prepared order sequentially so trials do not compete for resources."""
    batch = json.loads(args.plan.read_text())
    for directory in batch["runs"]:
        options = argparse.Namespace(directory=Path(directory), auth_volume=args.auth_volume)
        run(options)
        _, manifest = load_run(options.directory)
        if manifest["status"] not in {"completed", "timeout"}:
            raise ValueError(f"Batch stopped after {manifest['id']}: {manifest['status']}")
        grade(options)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Build the image from its isolated context")
    build.add_argument("--image", default=IMAGE)
    auth = sub.add_parser("login", help="Authenticate before any timed runs")
    auth.add_argument("--image", default=IMAGE)
    auth.add_argument("--method", choices=("device", "api-key", "shell"), default="device")
    auth.add_argument("--auth-file", type=Path)
    verification = sub.add_parser("verify", help="Test the harness and reference solutions without model calls")
    verification.add_argument("--image", default=IMAGE)
    execution = sub.add_parser("execute", help="Run and grade every prepared trial in plan order")
    execution.add_argument("plan", type=Path)
    execution.add_argument("--auth-volume", default=AUTH_VOLUME)
    for name in ("prepare", "plan"):
        command = sub.add_parser(name)
        command.add_argument("--image", default=IMAGE)
        command.add_argument("--model", required=True)
        command.add_argument("--effort", choices=("low", "medium", "high", "xhigh"), default="high")
        command.add_argument("--timeout", type=int, default=900)
        command.add_argument("--out", type=Path, default=ROOT / "runs")
        if name == "prepare":
            command.add_argument("--case", choices=CASES, required=True)
            command.add_argument("--arm", choices=ARMS, required=True)
        else:
            command.add_argument("--cases", choices=CASES, nargs="+", default=["cards", "browser"])
            command.add_argument("--arms", choices=ARMS, nargs="+", default=["homepage", "llms"])
            command.add_argument("--repetitions", type=int, default=2)
            command.add_argument("--seed", type=int, default=17)
    for name in ("run", "grade"):
        command = sub.add_parser(name)
        command.add_argument("directory", type=Path)
        if name == "run":
            command.add_argument("--auth-volume", default=AUTH_VOLUME)
    command = sub.add_parser("report")
    command.add_argument("--out", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    actions = {
        "login": login,
        "prepare": prepare,
        "run": run,
        "grade": grade,
        "plan": plan,
        "report": report,
        "execute": execute,
    }
    if args.command == "build":
        docker("build", "-t", args.image, str(ROOT / "image"))
    elif args.command == "verify":
        call(
            [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"],
            env=os.environ | {"CITRY_AGENT_EVAL_DOCKER": "1", "CITRY_AGENT_EVAL_IMAGE": args.image},
        )
    else:
        actions[args.command](args)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, FileExistsError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
