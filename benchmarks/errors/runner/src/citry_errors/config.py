"""Load the mistake catalogue, the framework definitions and the per-framework ports."""

from __future__ import annotations

import os
import re
import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

BENCH_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = BENCH_ROOT.parents[1]
# Installed environments, per-case working copies, raw run evidence and the
# stored output of earlier runs stay out of the repository, next to the other
# benchmarks' caches. CITRY_ERRORS_CACHE moves them, for example to share one
# set of installed frameworks, and the stored output of frameworks whose
# commands name no file in the checkout, between two checkouts that do not
# run at once.
CACHE = Path(os.environ.get("CITRY_ERRORS_CACHE") or REPO_ROOT / ".benchmarks" / "errors").resolve()

# Static stages in the order a developer meets them. The runtime stages and
# the two "not reported" outcomes follow, so a lower index means earlier.
STATIC_STAGES = ("editor", "check", "build")
OUTCOMES = ("editor", "check", "build", "runtime-error", "runtime-warning", "silent", "never")
PARSERS = (
    "citry-json",
    "pyright-json",
    "tsc",
    "eslint-json",
    "ruff-json",
    "djlint",
    "esbuild",
    "python-traceback",
    "exit",
)
PORT_STATUSES = ("ported", "not-applicable", "prevented")
# Each browser step's own keys: the ones it needs, then the ones it may take.
# A key outside these is rejected, so a typo such as `ms` on a click cannot
# silently do nothing. `press` without a selector presses the key on whatever
# has focus, which is how a keyboard flow moves on from the previous step.
STEP_KEYS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "click": (frozenset({"selector"}), frozenset()),
    "fill": (frozenset({"selector", "text"}), frozenset()),
    "press": (frozenset({"key"}), frozenset({"selector"})),
    "wait": (frozenset({"ms"}), frozenset()),
}
# A journey is a named list of browser steps in `framework.toml`. This one is
# the journey the page is recorded around: after the load, after its steps,
# and after a reload. Every framework with a browser check has it.
DEFAULT_JOURNEY = "default"
# A journey name becomes a key in the recorded observation and in messages,
# so it stays lowercase letters, digits and `-`, starting with a letter.
_JOURNEY_NAME = re.compile(r"[a-z][a-z0-9-]*")


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
    """One thing the browser check does on the page: click, fill a field, press a key, or wait."""

    action: str
    selector: str = ""
    ms: int = 0
    # The text `fill` types into the field, replacing what was there.
    text: str = ""
    # The key `press` presses, in Playwright's names such as `Enter` or `Tab`.
    key: str = ""


@dataclass(frozen=True)
class Runtime:
    argv: tuple[str, ...]
    page_path: str
    ready_timeout: int
    # Journey name -> its steps, in the order the file lists them. The
    # default journey is always present; every other one starts from a
    # fresh load of the page and records the page once at its end.
    journeys: dict[str, tuple[Step, ...]]
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
    # How many of this framework's cases may run at once, when fewer than the
    # run's worker count; None means no limit of its own.
    max_jobs: int | None = None

    @property
    def baseline(self) -> Path:
        return self.root / "baseline"


@dataclass(frozen=True)
class Edit:
    """One text replacement a case makes in a baseline file: `old` must appear there exactly once."""

    file: str
    old: str
    new: str


@dataclass(frozen=True)
class Port:
    mistake: str
    framework: str
    status: str
    reason: str
    # Published path inside the baseline -> source file next to port.toml,
    # for a case that replaces the whole file.
    files: dict[str, Path]
    # Replacements in baseline files, for a case that changes a few lines.
    # Written as edits, a case keeps following the baseline when other parts
    # of the same file change.
    edits: tuple[Edit, ...]
    mistake_file: str
    mistake_contains: str
    window: int
    # Why a finding that points away from the change still reports this
    # mistake, and the rule codes of the findings that reason covers.
    indirect: str
    indirect_codes: tuple[str, ...]
    root: Path


def _table(
    data: Any, where: str, required: AbstractSet[str], optional: AbstractSet[str] = frozenset()
) -> dict[str, Any]:
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


# A drive letter such as "C:" makes a path absolute on Windows.
_DRIVE = re.compile(r"^[A-Za-z]:")


def _relative_path(value: str, where: str, what: str) -> str:
    """
    Accept only a plain relative path, so a case's path text cannot point outside its folder or the baseline.

    The text is checked here because the working copy a baseline path will
    be joined to does not exist yet when a port is loaded; where the file
    can be resolved, the caller also resolves it. Backslashes and drive
    letters are rejected too: on Windows they would make the path absolute
    or let ".." through as part of one name.
    """
    parts = PurePosixPath(value).parts
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or _DRIVE.match(value)
        or any(part == ".." for part in parts)
        # A doubled or trailing slash, or a "." name, would name the same
        # file a second way.
        or "/".join(parts) != value
        # A control character such as NUL makes the operating system reject
        # the path later with a traceback instead of this message.
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        # Windows drops a trailing dot or space from a name, so "x." would
        # be a second spelling of "x" and ".. " a spelling of "..".
        or any(part.endswith((".", " ")) for part in parts)
    ):
        raise ConfigError(
            f"{where} {what} {value!r}, which must be a plain relative path: no leading '/', no '.' or '..' name,"
            " no backslash, drive letter or control character, and no empty name or name ending in a dot or space"
        )
    return value


def _same_file_key(value: str) -> str:
    """
    Spell a path the way a case-insensitive file system compares it.

    macOS and Windows treat `Templates/INDEX.html` and `templates/index.html`,
    and the composed and decomposed forms of an accented letter, as one file.
    """
    return unicodedata.normalize("NFC", value).casefold()


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
        {"runtime", "notes", "max_jobs"},
    )
    max_jobs = data.get("max_jobs")
    # Python treats `true` as the int 1, so a bool is rejected explicitly.
    if max_jobs is not None and (not isinstance(max_jobs, int) or isinstance(max_jobs, bool) or max_jobs < 1):
        raise ConfigError(f"{path} max_jobs must be a whole number of cases, 1 or more")
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
            {"argv", "page_path", "journeys"},
            {"ready_timeout", "env", "settle_ms"},
        )
        runtime = Runtime(
            argv=tuple(raw["argv"]),
            page_path=raw["page_path"],
            ready_timeout=int(raw.get("ready_timeout", 90)),
            journeys=load_journeys(raw["journeys"], f"{path} [runtime.journeys]"),
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
        max_jobs=max_jobs,
    )


def load_journeys(data: Any, where: str) -> dict[str, tuple[Step, ...]]:
    """
    Read the named journeys of a framework's browser check.

    Every problem is reported here, when the file loads, so a bad journey
    stops `validate` and `run` before any server starts rather than failing
    each case's browser check in the middle of a run.
    """
    if not isinstance(data, dict):
        raise ConfigError(f"{where} must be a table of journey names to lists of steps")
    if DEFAULT_JOURNEY not in data:
        # The three page records every case is compared on are taken around
        # this journey, so without it the browser check would compare nothing.
        raise ConfigError(f"{where} needs a {DEFAULT_JOURNEY!r} journey")
    journeys = {}
    for name, steps in data.items():
        if not _JOURNEY_NAME.fullmatch(name):
            raise ConfigError(f"{where} journey name {name!r} must be lowercase letters, digits and '-'")
        if not isinstance(steps, list) or not steps:
            # A journey with no steps would only record the loaded page again.
            raise ConfigError(f"{where} journey {name!r} must be a non-empty list of steps")
        journeys[name] = tuple(
            _step(step, f"{where} journey {name!r} step {index}") for index, step in enumerate(steps)
        )
    return journeys


def _step(data: Any, where: str) -> Step:
    """Read one step, accepting only the keys its action uses, each with a value of the right kind."""
    if not isinstance(data, dict) or "action" not in data:
        raise ConfigError(f"{where} must be a table with an action")
    action = data["action"]
    # A list or table here is not hashable, so the kind is checked before the lookup.
    if not isinstance(action, str) or action not in STEP_KEYS:
        raise ConfigError(f"{where} has unknown action {action!r}; expected one of {sorted(STEP_KEYS)}")
    required, optional = STEP_KEYS[action]
    row = _table(data, where, {"action"} | required, optional)
    # An empty selector or key would fail only when the browser reaches the
    # step, in the clean app as well, so every cell of that framework would
    # be marked `!` partway through the run.
    for key in ("selector", "key"):
        if key in row and (not isinstance(row[key], str) or not row[key]):
            raise ConfigError(f"{where} {key} must be non-empty text")
    # Filling in empty text is a real action (it clears the field), so only the kind is checked.
    if "text" in row and not isinstance(row["text"], str):
        raise ConfigError(f"{where} text must be text")
    # Python treats `true` as the int 1, so a bool is rejected explicitly.
    if "ms" in row and (not isinstance(row["ms"], int) or isinstance(row["ms"], bool) or row["ms"] <= 0):
        raise ConfigError(f"{where} ms must be a whole number of milliseconds above 0")
    return Step(
        action=action,
        selector=row.get("selector", ""),
        ms=row.get("ms", 0),
        text=row.get("text", ""),
        key=row.get("key", ""),
    )


def load_frameworks(root: Path = BENCH_ROOT / "frameworks") -> dict[str, Framework]:
    return {path.name: load_framework(path) for path in sorted(root.iterdir()) if (path / "framework.toml").is_file()}


def load_port(path: Path) -> Port:
    where = str(path)
    data = _table(
        tomllib.loads(path.read_text(encoding="utf-8")),
        where,
        {"status"},
        {"reason", "files", "edits", "mistake", "window", "indirect"},
    )
    status = data["status"]
    if status not in PORT_STATUSES:
        raise ConfigError(f"{where} has unknown status {status!r}")
    root = path.parent
    files: dict[str, Path] = {}
    edits: list[Edit] = []
    mistake_file = mistake_contains = ""
    if status == "ported":
        _table(data, where, {"status", "mistake"}, {"files", "edits", "reason", "window", "indirect"})
        raw_files = data.get("files", {})
        # A wrong shape would otherwise fail later as a traceback instead of
        # an error that names the port file.
        if not isinstance(raw_files, dict) or not all(isinstance(value, str) for value in raw_files.values()):
            raise ConfigError(f"{where} files must be a table of baseline paths to copy file names")
        # Each changed file once, by the spelling that file systems compare,
        # so one file cannot be changed twice under two spellings.
        spellings: dict[str, str] = {}
        for published, source in raw_files.items():
            _relative_path(published, where, "replaces")
            spellings[_same_file_key(published)] = published
            source_path = root / _relative_path(source, where, "copies from")
            if not source_path.is_file():
                raise ConfigError(f"{where} names a missing file {source!r}")
            # A symbolic link next to port.toml would copy a file from
            # anywhere into the working copy; the case folder exists now, so
            # the link is followed and checked here.
            if not source_path.resolve().is_relative_to(root.resolve()):
                raise ConfigError(f"{where} copies from {source!r}, which resolves outside the case folder")
            files[published] = source_path
        if not isinstance(data.get("edits", []), list):
            raise ConfigError(f"{where} edits must be a list of tables")
        for index, raw in enumerate(data.get("edits", [])):
            row = _table(raw, f"{where} edit {index}", {"file", "old", "new"})
            if not all(isinstance(row[key], str) for key in ("file", "old", "new")):
                raise ConfigError(f"{where} edit {index} needs text for file, old and new")
            _relative_path(row["file"], f"{where} edit {index}", "edits")
            # Empty text is found everywhere, and an edit that keeps the text
            # would leave the clean app unchanged, so both point at a typo.
            if not row["old"]:
                raise ConfigError(f"{where} edit {index} has an empty old text")
            if row["old"] == row["new"]:
                raise ConfigError(f"{where} edit {index} changes nothing")
            if row["file"] in files:
                # Edits to a file the case also replaces whole have no single
                # meaning: they could apply to the clean file or to the copy.
                raise ConfigError(f"{where} both replaces and edits {row['file']!r}")
            known = spellings.setdefault(_same_file_key(row["file"]), row["file"])
            if known != row["file"]:
                raise ConfigError(f"{where} edit {index} names {row['file']!r}, the same file as {known!r}")
            edits.append(Edit(**row))
        # A ported case that changes nothing would score the clean app.
        if not files and not edits:
            raise ConfigError(f"{where} with status 'ported' needs files or edits")
        mistake = _table(data["mistake"], f"{where} [mistake]", {"file", "contains"})
        mistake_file, mistake_contains = mistake["file"], mistake["contains"]
        if mistake_file not in files and all(edit.file != mistake_file for edit in edits):
            raise ConfigError(f"{where} mistake file {mistake_file!r} is not one of the changed files")
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
        edits=tuple(edits),
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
