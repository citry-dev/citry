"""
Keep each case's raw tool output and browser check between runs, so a run repeats only what changed.

The runner stores what the tools printed and what the browser recorded,
never the scores, so a change to how results are scored or reported takes
effect on the next run without repeating any case. Each stored entry is
filed under a key: a hash of everything that can change that raw output.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tomllib
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .config import BENCH_ROOT, ConfigError
from .execute import StageOutput
from .runtime import Observation
from .work import _IGNORED_NAMES, installed_local_digest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .config import Framework, Port

# Raised by hand when the stored files change shape, so an older entry is
# read as a miss rather than misread.
FORMAT = 1
# The runner code that decides what a tool or the browser check prints: the
# commands and their environment, the working copy, the browser steps and
# what the page record holds. Parsing, comparing and scoring happen after
# the raw output is read back, so they are left out on purpose.
_RUNNER_SOURCES = ("cache.py", "config.py", "execute.py", "runtime.py", "work.py")
# Pins the Playwright version, which pins the Chromium build.
_RUNNER_PROJECT = ("pyproject.toml", "uv.lock")
# Keys of framework.toml that do not change what a tool prints, so editing
# them does not rerun every case: the prose notes, and how many development
# servers may run at once.
_UNUSED_KEYS = ("notes", "max_servers")
# Environment variables known to change what these tools print, such as
# colors or Node's own options. The rest of the environment is not hashed:
# it differs between shells, and these are the ones known to matter.
_TOOL_VARIABLES = ("CI", "FORCE_COLOR", "NO_COLOR", "NODE_ENV", "NODE_OPTIONS", "PYTHONWARNINGS", "TERM")
# Files an install writes into a framework's environment that name what was
# installed: the Python the virtual environment uses, and npm's record of
# every installed package. A reinstall from the same lockfile can still pick
# a different Python patch release.
_INSTALL_RECORDS = (".venv/pyvenv.cfg", "node_modules/.package-lock.json")


def _hash_files(digest: hashlib._Hash, root: Path, names: tuple[str, ...]) -> None:
    for name in names:
        digest.update(name.encode() + b"\0")
        digest.update((root / name).read_bytes() + b"\0")


def environment_digest() -> str:
    """
    Hash what every case of a run shares: the runner code, Playwright, Node, Python, the system and some variables.

    Node is not pinned by any lockfile here, and the Next.js and Nuxt tools
    run on whichever Node is first on PATH, so its version is part of the key.
    """
    digest = hashlib.sha256(f"format {FORMAT}\0".encode())
    _hash_files(digest, Path(__file__).parent, _RUNNER_SOURCES)
    _hash_files(digest, BENCH_ROOT / "runner", _RUNNER_PROJECT)
    # The Playwright actually installed, which picks the Chromium build; the
    # lockfile above may belong to another checkout's environment.
    digest.update(f"playwright {importlib.metadata.version('playwright')}\0".encode())
    for name in _TOOL_VARIABLES:
        digest.update(f"{name}={os.environ.get(name, '<unset>')}\0".encode())
    node = shutil.which("node")
    node_version = (
        subprocess.run([node, "--version"], capture_output=True, text=True, check=False).stdout.strip()
        if node
        else "none"
    )
    digest.update(f"node {node_version}\0python {sys.version}\0{platform.platform()}\0".encode())
    return digest.hexdigest()


def framework_digest(framework: Framework, env: Path) -> str:
    """
    Hash every file of a framework's folder, and what its environment `env` has installed.

    The folder holds the clean app, its lockfiles, helper scripts and
    framework.toml. For a package the app installs from disk, such as Citry
    from this repository, the files the environment installed are hashed
    too. framework.toml is read and hashed without the keys in
    `_UNUSED_KEYS`, so rewording its notes keeps the stored results;
    comments are dropped by the same reading. When a stage or server
    command names a file by its absolute path in the checkout (`{framework}`
    or `{repo}`), that path is printed in the output, so the folder's
    location is hashed too; otherwise two checkouts sharing one cache
    folder can reuse each other's output.
    """
    definition = tomllib.loads((framework.root / "framework.toml").read_text(encoding="utf-8"))
    # The setup step's output is never stored, so a path it names, such as
    # the Citry app's folder that uv runs in, does not tie the results to
    # this checkout.
    commands = json.dumps({key: value for key, value in definition.items() if key != "setup"})
    names_checkout = "{framework}" in commands or "{repo}" in commands
    digest = hashlib.sha256(f"{framework.root if names_checkout else ''}\0".encode())
    for name in _INSTALL_RECORDS:
        record = env / name
        digest.update(name.encode() + b"\0" + (record.read_bytes() if record.is_file() else b"<none>") + b"\0")
    # A package installed from its sources in this repository, such as the
    # Citry app's citry, changes what the tools print without changing any
    # file of the framework's folder or the install records above.
    digest.update(f"installed from disk {installed_local_digest(framework, env)}\0".encode())
    for path in sorted(framework.root.rglob("*")):
        relative = path.relative_to(framework.root)
        # Build output and installed packages never reach a working copy.
        if not path.is_file() or any(part in _IGNORED_NAMES for part in relative.parts):
            continue
        digest.update(relative.as_posix().encode() + b"\0")
        if relative.as_posix() == "framework.toml":
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            for key in _UNUSED_KEYS:
                data.pop(key, None)
            digest.update(json.dumps(data, sort_keys=True).encode() + b"\0")
        else:
            digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def case_key(environment: str, framework: str, port: Port | None, work: Path) -> str:
    """
    Hash one case's inputs, or the clean app's when `port` is None.

    The case's port.toml holds its edits; the copies it replaces whole files
    with are read too. The working copy's folder is included because tools
    print absolute paths into their output.
    """
    digest = hashlib.sha256(f"{environment}\0{framework}\0{work}\0".encode())
    if port is not None:
        digest.update((port.root / "port.toml").read_bytes() + b"\0")
        for published, source in sorted(port.files.items()):
            digest.update(published.encode() + b"\0" + source.read_bytes() + b"\0")
    return digest.hexdigest()


@dataclass
class Entry:
    """The raw output one earlier run stored for a case."""

    stages: list[StageOutput]
    # None when that run skipped the browser check or did not keep it.
    observation: Observation | None
    server_log: Path | None


def load(folder: Path, key: str) -> Entry | None:
    """
    Read the entry stored in `folder` when it was made from the same inputs, or give None.

    The key file is written last, so an entry a run stopped writing has none
    and is not used.
    """
    marker = folder / "key"
    try:
        if not marker.is_file() or marker.read_text() != key:
            return None
        stages = [StageOutput(**stage) for stage in json.loads((folder / "stages.json").read_text())]
        runtime, log = folder / "runtime.json", folder / "server.log"
        if not runtime.is_file() or not log.is_file():
            return Entry(stages, None, None)
        return Entry(stages, Observation.from_json(runtime.read_text()), log)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        # A damaged entry is a miss: the case runs again and its entry is
        # replaced, rather than the whole run stopping. It is named, so a
        # format change that makes every entry unreadable does not go unseen.
        print(f"citry-errors: ignoring the stored output in {folder}: {error!r}", file=sys.stderr)
        return None


def keeps(stages: list[StageOutput]) -> bool:
    """
    Tell whether a run's stage output is worth storing.

    A stage that timed out, or a command killed by a signal (a negative exit
    code, such as from Ctrl-C or the system running out of memory), says
    more about the machine at that moment than about the case, so the case
    runs again next time.
    """
    return all(stage.exit_code is not None and stage.exit_code >= 0 for stage in stages)


def keeps_observation(observation: Observation) -> bool:
    """
    Tell whether a browser check is worth storing.

    A server that never answered, or a journey that stopped (an element not
    found in time, a page that did not load or go quiet), can come from the
    mistake or from a busy machine. The two cannot be told apart here, so
    such a check runs again on the next run.
    """
    return (
        observation.started
        and not observation.failure
        and not any(record.failure for record in observation.journeys.values())
    )


def store(
    folder: Path, key: str, stages: list[StageOutput], observation: Observation | None, log: bytes | None
) -> None:
    """
    Replace the entry in `folder` with this run's raw output.

    The key file is removed first and written last, so a run stopped halfway
    leaves an entry that the next run ignores rather than one that mixes
    two runs' files.
    """
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "key").unlink(missing_ok=True)
    for name in ("runtime.json", "server.log"):
        (folder / name).unlink(missing_ok=True)
    (folder / "stages.json").write_text(json.dumps([asdict(stage) for stage in stages], indent=2))
    if observation is not None and log is not None:
        # The log first: a stored runtime.json promises its log is complete.
        (folder / "server.log").write_bytes(log)
        (folder / "runtime.json").write_text(observation.to_json())
    (folder / "key").write_text(key)


@contextmanager
def exclusive(cache: Path) -> Iterator[None]:
    """
    Hold the cache folder for one run at a time.

    Two runs on one folder would write the same working copies and stored
    entries at once. The operating system releases the lock when the process
    ends, so a run that crashed leaves nothing to clean up.
    """
    cache.mkdir(parents=True, exist_ok=True)
    # Opened for appending, so a second run that fails to get the lock does
    # not wipe the first run's process id from the file.
    with (cache / "run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ConfigError(
                f"another run is using {cache}; wait for it to finish, or set CITRY_ERRORS_CACHE to another folder"
            ) from None
        lock.truncate(0)
        lock.write(str(os.getpid()))
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
