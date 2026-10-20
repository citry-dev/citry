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
from .work import _IGNORED_NAMES

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
# them does not rerun every case: the prose notes, and how many cases may
# run at once.
_UNUSED_KEYS = ("notes", "max_jobs")


def _hash_files(digest: hashlib._Hash, root: Path, names: tuple[str, ...]) -> None:
    for name in names:
        digest.update(name.encode() + b"\0")
        digest.update((root / name).read_bytes() + b"\0")


def environment_digest() -> str:
    """
    Hash what every case of a run shares: the runner code that makes raw output, the Node and Python versions.

    Node is not pinned by any lockfile here, and the Next.js and Nuxt tools
    run on whichever Node is first on PATH, so its version is part of the key.
    """
    digest = hashlib.sha256(f"format {FORMAT}\0".encode())
    _hash_files(digest, Path(__file__).parent, _RUNNER_SOURCES)
    _hash_files(digest, BENCH_ROOT / "runner", _RUNNER_PROJECT)
    node = shutil.which("node")
    node_version = (
        subprocess.run([node, "--version"], capture_output=True, text=True, check=False).stdout.strip()
        if node
        else "none"
    )
    digest.update(f"node {node_version}\0python {sys.version}\0{platform.platform()}\0".encode())
    return digest.hexdigest()


def framework_digest(framework: Framework) -> str:
    """
    Hash every file of a framework's folder: the clean app, its lockfiles, helper scripts and framework.toml.

    framework.toml is read and hashed without the keys in `_UNUSED_KEYS`, so
    rewording its notes keeps the stored results. Comments are dropped by
    the same reading.
    """
    digest = hashlib.sha256()
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
    if not marker.is_file() or marker.read_text() != key:
        return None
    stages = [StageOutput(**stage) for stage in json.loads((folder / "stages.json").read_text())]
    runtime = folder / "runtime.json"
    if not runtime.is_file():
        return Entry(stages, None, None)
    return Entry(stages, Observation.from_json(runtime.read_text()), folder / "server.log")


def keeps(stages: list[StageOutput]) -> bool:
    """
    Tell whether a run's stage output is worth storing.

    A stage that timed out, or a command killed by a signal (a negative exit
    code, such as from Ctrl-C or the system running out of memory), says
    more about the machine at that moment than about the case, so the case
    runs again next time.
    """
    return all(stage.exit_code is not None and stage.exit_code >= 0 for stage in stages)


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
    with (cache / "run.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ConfigError(
                f"another run is using {cache}; wait for it to finish, or set CITRY_ERRORS_CACHE to another folder"
            ) from None
        lock.write(str(os.getpid()))
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
