"""Load the mistake catalogue, the framework definitions and the per-framework ports."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BENCH_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = BENCH_ROOT.parents[1]
# Installed environments, per-case working copies and raw run evidence stay
# out of the repository, next to the other benchmarks' caches.
CACHE = REPO_ROOT / ".benchmarks" / "errors"

# Static stages in the order a developer meets them. The runtime stages and
# the two "not reported" outcomes follow, so a lower index means earlier.
STATIC_STAGES = ("editor", "check", "build")
OUTCOMES = ("editor", "check", "build", "runtime-error", "runtime-warning", "silent", "never")
PARSERS = ("citry-json", "pyright-json", "tsc", "eslint-json", "ruff-json", "djlint", "exit")
PORT_STATUSES = ("ported", "not-applicable", "prevented")
STEP_ACTIONS = ("click", "wait")


class ConfigError(ValueError):
    """A catalogue, framework or port file does not match the expected shape."""


@dataclass(frozen=True)
class Mistake:
    id: str
    title: str
    category: str
    origin: str
    description: str
    correct: str


@dataclass(frozen=True)
class Stage:
    stage: str
    label: str
    argv: tuple[str, ...]
    parser: str
    timeout: int = 300
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    action: str
    selector: str = ""
    ms: int = 0


@dataclass(frozen=True)
class Runtime:
    argv: tuple[str, ...]
    page_path: str
    ready_timeout: int
    steps: tuple[Step, ...]
    env: dict[str, str] = field(default_factory=dict)
    settle_ms: int = 800


@dataclass(frozen=True)
class Framework:
    key: str
    name: str
    setup_manifests: tuple[str, ...]
    setup_command: tuple[str, ...]
    stages: tuple[Stage, ...]
    runtime: Runtime | None
    notes: str
    root: Path

    @property
    def baseline(self) -> Path:
        return self.root / "baseline"


@dataclass(frozen=True)
class Port:
    mistake: str
    framework: str
    status: str
    reason: str
    # Published path inside the baseline -> source file next to port.toml.
    files: dict[str, Path]
    mistake_file: str
    mistake_contains: str
    window: int
    # Why a finding that points away from the change still reports this
    # mistake, and the rule codes of the findings that reason covers.
    indirect: str
    indirect_codes: tuple[str, ...]
    root: Path


def _table(data: Any, where: str, required: set[str], optional: set[str] = frozenset()) -> dict[str, Any]:
    """Reject a missing or unknown key, so a typo in a definition cannot silently change a result."""
    if not isinstance(data, dict):
        raise ConfigError(f"{where} must be a table")
    missing = required - data.keys()
    unknown = data.keys() - required - optional
    if missing:
        raise ConfigError(f"{where} is missing {sorted(missing)}")
    if unknown:
        raise ConfigError(f"{where} has unknown keys {sorted(unknown)}")
    return data


def load_catalogue(path: Path = BENCH_ROOT / "catalogue.toml") -> list[Mistake]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    _table(data, str(path), {"mistake"})
    mistakes = []
    for index, raw in enumerate(data["mistake"]):
        where = f"{path.name} mistake {index}"
        row = _table(raw, where, {"id", "title", "category", "origin", "description", "correct"})
        if row["origin"] not in {"neutral", "citry-inventory"}:
            raise ConfigError(f"{where} has unknown origin {row['origin']!r}")
        mistakes.append(Mistake(**row))
    ids = [mistake.id for mistake in mistakes]
    if len(ids) != len(set(ids)):
        raise ConfigError("catalogue mistake ids are not unique")
    return mistakes


def load_framework(root: Path) -> Framework:
    path = root / "framework.toml"
    data = _table(
        tomllib.loads(path.read_text(encoding="utf-8")),
        str(path),
        {"key", "name", "setup", "stages"},
        {"runtime", "notes"},
    )
    if data["key"] != root.name:
        raise ConfigError(f"{path} key {data['key']!r} must match its folder name {root.name!r}")
    setup = _table(data["setup"], f"{path} [setup]", {"manifests", "command"})
    stages = []
    for index, raw in enumerate(data["stages"]):
        where = f"{path} stage {index}"
        row = _table(raw, where, {"stage", "label", "argv", "parser"}, {"timeout", "env"})
        if row["stage"] not in STATIC_STAGES:
            raise ConfigError(f"{where} has unknown stage {row['stage']!r}")
        if row["parser"] not in PARSERS:
            raise ConfigError(f"{where} has unknown parser {row['parser']!r}")
        stages.append(
            Stage(
                stage=row["stage"],
                label=row["label"],
                argv=tuple(row["argv"]),
                parser=row["parser"],
                timeout=int(row.get("timeout", 300)),
                env=dict(row.get("env", {})),
            )
        )
    runtime = None
    if "runtime" in data:
        raw = _table(
            data["runtime"],
            f"{path} [runtime]",
            {"argv", "page_path", "steps"},
            {"ready_timeout", "env", "settle_ms"},
        )
        steps = []
        for index, step in enumerate(raw["steps"]):
            row = _table(step, f"{path} runtime step {index}", {"action"}, {"selector", "ms"})
            if row["action"] not in STEP_ACTIONS:
                raise ConfigError(f"{path} runtime step {index} has unknown action {row['action']!r}")
            steps.append(Step(action=row["action"], selector=row.get("selector", ""), ms=int(row.get("ms", 0))))
        runtime = Runtime(
            argv=tuple(raw["argv"]),
            page_path=raw["page_path"],
            ready_timeout=int(raw.get("ready_timeout", 90)),
            steps=tuple(steps),
            env=dict(raw.get("env", {})),
            settle_ms=int(raw.get("settle_ms", 800)),
        )
    return Framework(
        key=data["key"],
        name=data["name"],
        setup_manifests=tuple(setup["manifests"]),
        setup_command=tuple(setup["command"]),
        stages=tuple(stages),
        runtime=runtime,
        notes=data.get("notes", ""),
        root=root,
    )


def load_frameworks(root: Path = BENCH_ROOT / "frameworks") -> dict[str, Framework]:
    return {path.name: load_framework(path) for path in sorted(root.iterdir()) if (path / "framework.toml").is_file()}


def load_port(path: Path) -> Port:
    where = str(path)
    data = _table(
        tomllib.loads(path.read_text(encoding="utf-8")),
        where,
        {"status"},
        {"reason", "files", "mistake", "window", "indirect"},
    )
    status = data["status"]
    if status not in PORT_STATUSES:
        raise ConfigError(f"{where} has unknown status {status!r}")
    root = path.parent
    files: dict[str, Path] = {}
    mistake_file = mistake_contains = ""
    if status == "ported":
        _table(data, where, {"status", "files", "mistake"}, {"reason", "window", "indirect"})
        for published, source in data["files"].items():
            source_path = root / source
            if not source_path.is_file():
                raise ConfigError(f"{where} names a missing file {source!r}")
            files[published] = source_path
        mistake = _table(data["mistake"], f"{where} [mistake]", {"file", "contains"})
        mistake_file, mistake_contains = mistake["file"], mistake["contains"]
        if mistake_file not in files:
            raise ConfigError(f"{where} mistake file {mistake_file!r} is not one of the replaced files")
    elif not data.get("reason"):
        # A case a framework cannot express is recorded with its reason, never dropped.
        raise ConfigError(f"{where} with status {status!r} needs a reason")
    # A note names the codes it accepts, so it cannot also let through an
    # unrelated finding, such as a variable the change left unused.
    indirect = _table(data.get("indirect", {"reason": "", "codes": []}), f"{where} [indirect]", {"reason", "codes"})
    if bool(indirect["reason"]) != bool(indirect["codes"]):
        raise ConfigError(f"{where} [indirect] needs both a reason and at least one code")
    return Port(
        mistake=root.parent.name,
        framework=root.name,
        status=status,
        reason=data.get("reason", ""),
        files=files,
        mistake_file=mistake_file,
        mistake_contains=mistake_contains,
        window=int(data.get("window", 3)),
        indirect=indirect["reason"],
        indirect_codes=tuple(indirect["codes"]),
        root=root,
    )


def load_ports(root: Path = BENCH_ROOT / "cases") -> dict[tuple[str, str], Port]:
    ports = {}
    for path in sorted(root.glob("*/*/port.toml")):
        port = load_port(path)
        ports[(port.mistake, port.framework)] = port
    return ports
