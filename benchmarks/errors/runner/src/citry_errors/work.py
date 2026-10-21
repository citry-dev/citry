"""Install each framework once and make a fresh working copy of its app for every case."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from .config import CACHE, REPO_ROOT, ConfigError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from .config import Edit, Framework, Port

# Build output and installed dependencies never belong in a working copy: the
# environment is shared, and stale build output would hide the case's change.
_IGNORED_NAMES = ("node_modules", ".venv", ".next", ".nuxt", ".output", "__pycache__", "dist")
_IGNORED = shutil.ignore_patterns(*_IGNORED_NAMES)


def env_dir(framework: Framework) -> Path:
    return CACHE / "envs" / framework.key


def local_sources(framework: Framework) -> dict[str, Path]:
    """
    Give the packages the clean app's pyproject.toml installs from a folder or file on disk, by package name.

    These are uv's `path` sources, such as the Citry app's citry and
    citry-lsp, which come from this repository rather than from PyPI. Their
    files live outside the framework's folder, so neither the lockfile nor
    the framework's own files change when they do.
    """
    manifest = framework.baseline / "pyproject.toml"
    if not manifest.is_file():
        return {}
    sources = tomllib.loads(manifest.read_text(encoding="utf-8")).get("tool", {}).get("uv", {}).get("sources", {})
    found = {}
    # Sorted by name, so the digests below do not depend on the order the
    # table lists them in.
    for name, source in sorted(sources.items()):
        if not isinstance(source, dict) or "path" not in source:
            continue
        if source.get("editable"):
            # An editable install leaves only a pointer to the folder, so the
            # installed files the stored results are keyed by would never change.
            raise ConfigError(f"{manifest} installs {name} as editable; the benchmark needs a built install")
        found[name] = (framework.baseline / source["path"]).resolve()
    return found


def source_files(folder: Path) -> list[str]:
    """
    List the files in `folder` that git tracks, or would track, as paths relative to it.

    Git's ignore rules leave out what a build writes beside the sources,
    such as setuptools' build/ and *.egg-info/ folders, so building the
    package does not count as a change to it.
    """
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=folder,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ConfigError(f"could not list the files of {folder} with git: {completed.stderr.decode()[-2000:]}")
    return sorted({name for name in completed.stdout.decode().split("\0") if name})


def local_source_digest(framework: Framework) -> str:
    """
    Hash the files of every package the clean app installs from disk.

    A change to them can change what the installed package does, so the
    runner installs the package again when this digest changes. It also
    hashes files the package does not install, such as its tests and
    changelog, so editing one rebuilds the package but keeps the stored
    results, which follow `installed_local_digest`.
    """
    digest = hashlib.sha256()
    for name, path in local_sources(framework).items():
        digest.update(f"{name}\0".encode())
        if path.is_file():
            # A built wheel or archive named directly.
            digest.update(path.read_bytes() + b"\0")
            continue
        for relative in source_files(path):
            file = path / relative
            # A tracked file deleted from the working tree is still listed.
            content = file.read_bytes() if file.is_file() else b"<deleted>"
            digest.update(relative.encode() + b"\0" + content + b"\0")
    return digest.hexdigest()


def installed_local_digest(framework: Framework, env: Path) -> str:
    """
    Hash the files that the environment `env` installed for each package the clean app installs from disk.

    Each installed package lists its files with their hashes in its
    `*.dist-info/RECORD`. The stored results depend on those files, not on
    the package's whole folder, so an edit to its tests or changelog keeps
    them. The lines for the `.dist-info` folder itself are left out: its
    metadata holds the package's README, and its `direct_url.json` names
    the checkout the package was built from.
    """
    digest = hashlib.sha256()
    for name in local_sources(framework):
        # Installed folder names use underscores where the package name may
        # use dashes or dots, such as citry_lsp for citry-lsp.
        normalized = re.sub(r"[-_.]+", "_", name).lower()
        records = sorted((env / ".venv" / "lib").glob(f"python*/site-packages/{normalized}-*.dist-info/RECORD"))
        digest.update(f"{name}\0".encode())
        for record in records:
            for line in record.read_text(encoding="utf-8").splitlines():
                if line and ".dist-info/" not in line.split(",", 1)[0]:
                    digest.update(line.encode() + b"\0")
        if not records:
            digest.update(b"<not installed>\0")
    return digest.hexdigest()


def _check_lock(framework: Framework) -> None:
    """
    Stop when the clean app's uv.lock no longer matches the sources of a package it installs from disk.

    `uv sync --frozen` installs whatever the lock says without comparing it
    with those sources, so a dependency they add would be left out
    silently. uv also counts the packages' development dependency groups,
    which are never installed here, so a change to those asks for a new
    lock too. uv runs in the clean app's folder, because it resolves
    `${PROJECT_ROOT}` in the Citry app's overrides against the folder it
    starts in.
    """
    if not local_sources(framework) or not (framework.baseline / "uv.lock").is_file():
        return
    # UV_FROZEN would make `--check` accept any lock that parses.
    environment = {key: value for key, value in os.environ.items() if key not in {"VIRTUAL_ENV", "UV_FROZEN"}}
    try:
        result = subprocess.run(
            ["uv", "lock", "--check", "--directory", str(framework.baseline)],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise ConfigError(f"{framework.key} installs packages from disk, which needs uv on PATH") from None
    if result.returncode != 0:
        raise ConfigError(
            f"{framework.baseline / 'uv.lock'} does not match the sources it installs from disk; "
            f"run `uv lock` in that folder:\n{result.stderr[-2000:]}"
        )


_EXACT_PIN = re.compile(r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*(?P<version>[^\s;,]+)\s*$")


def _exact_pins(requirements: list[str]) -> dict[str, str]:
    """Give the exact versions (`name==1.2.3`) among `requirements`, by normalized package name."""
    return {
        re.sub(r"[-_.]+", "-", match["name"]).lower(): match["version"]
        for requirement in requirements
        if (match := _EXACT_PIN.match(requirement))
    }


def _check_overrides(framework: Framework) -> None:
    """
    Stop when the clean app overrides a version that a package it installs from disk pins differently.

    The Citry app overrides citry-core's version by hand, because this
    repository's own settings would build citry-core from its Rust sources
    instead. The lock records the overridden version only, so `uv lock
    --check` cannot see citry raise its pin, and citry would run against a
    citry-core it was not released with.
    """
    manifest = framework.baseline / "pyproject.toml"
    if not manifest.is_file():
        return
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    overrides = _exact_pins(data.get("tool", {}).get("uv", {}).get("override-dependencies", []))
    for name, path in local_sources(framework).items():
        source_manifest = path / "pyproject.toml"
        if not overrides or not source_manifest.is_file():
            continue
        pins = _exact_pins(
            tomllib.loads(source_manifest.read_text(encoding="utf-8")).get("project", {}).get("dependencies", [])
        )
        for dependency, version in pins.items():
            if dependency in overrides and overrides[dependency] != version:
                raise ConfigError(
                    f"{manifest} overrides {dependency} to {overrides[dependency]}, but {name} pins "
                    f"{dependency}=={version}; change the override and run `uv lock` in that folder"
                )


def _remove_old_builds(framework: Framework) -> None:
    """
    Delete the build/ folder that setuptools leaves in each package folder the clean app installs from.

    setuptools copies the sources into build/lib and builds the wheel from
    there, keeping what an earlier build copied, so a module deleted or
    renamed since would still be installed. The folder is deleted only when
    git ignores it, so nothing a developer keeps there is lost.
    """
    for path in local_sources(framework).values():
        if not (path / "build").is_dir():
            continue
        ignored = subprocess.run(["git", "check-ignore", "-q", "build"], cwd=path, check=False).returncode == 0
        if ignored:
            shutil.rmtree(path / "build")


def _manifest_digest(framework: Framework) -> str:
    digest = hashlib.sha256()
    # The command is part of what the environment holds: a setup step that
    # builds something, such as Tetra's own component library, must run again
    # when the step changes, even if no lockfile did.
    digest.update(json.dumps(framework.setup_command).encode())
    for name in framework.setup_manifests:
        digest.update(name.encode())
        digest.update((framework.baseline / name).read_bytes())
    # A package installed from its sources keeps the same lockfile entry when
    # those sources change, so the sources themselves decide when to install
    # it again.
    digest.update(local_source_digest(framework).encode())
    return digest.hexdigest()


def prepare(framework: Framework) -> Path:
    """Install the framework's locked dependencies into its environment folder, once per lockfile."""
    env = env_dir(framework)
    marker = env / "prepared.json"
    digest = _manifest_digest(framework)
    if marker.is_file() and json.loads(marker.read_text()).get("digest") == digest:
        return env
    _check_overrides(framework)
    _check_lock(framework)
    env.mkdir(parents=True, exist_ok=True)
    marker.unlink(missing_ok=True)
    _remove_old_builds(framework)
    for name in framework.setup_manifests:
        shutil.copy2(framework.baseline / name, env / name)
    result = subprocess.run(
        [placeholder(part, framework, env, env) for part in framework.setup_command],
        cwd=env,
        env=command_env(framework, env, env),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ConfigError(f"setting up {framework.key} failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    # The marker is written only after a successful install, so a failed or
    # interrupted setup is repeated rather than trusted.
    marker.write_text(json.dumps({"digest": digest}))
    return env


def placeholder(value: str, framework: Framework, env: Path, work: Path, port: int = 0, backend_port: int = 0) -> str:
    return value.format_map(
        {
            "env": str(env),
            "venv": str(env / ".venv"),
            "work": str(work),
            "port": str(port),
            # A second port, for a development server that runs its backend
            # apart from the server that answers the page.
            "backend_port": str(backend_port),
            "repo": str(REPO_ROOT),
            "framework": str(framework.root),
        }
    )


def command_env(
    framework: Framework,
    env: Path,
    work: Path,
    extra: dict[str, str] | None = None,
    port: int = 0,
    backend_port: int = 0,
) -> dict[str, str]:
    """Run every tool with the framework's own environment first on PATH and the app importable."""
    base = {key: value for key, value in os.environ.items() if key not in {"VIRTUAL_ENV", "PYTHONPATH"}}
    base["PATH"] = os.pathsep.join([str(env / ".venv" / "bin"), str(env / "node_modules" / ".bin"), base["PATH"]])
    base["PYTHONPATH"] = str(work)
    base["NEXT_TELEMETRY_DISABLED"] = "1"
    base["NUXT_TELEMETRY_DISABLED"] = "1"
    base["PYTHONDONTWRITEBYTECODE"] = "1"
    # A Python server writes what it prints straight to its log, so it is
    # there while the page is checked, not only when the server exits.
    base["PYTHONUNBUFFERED"] = "1"
    for key, value in (extra or {}).items():
        base[key] = placeholder(value, framework, env, work, port, backend_port)
    return base


@dataclass(frozen=True)
class WorkCopy:
    path: Path
    mistake_line: int | None


def apply_edits(text: str, edits: Sequence[Edit], where: str) -> str:
    """
    Replace each edit's old text in the clean file's text.

    Every old text is looked up in the clean text, never in the result of an
    earlier edit, so the order of the edits does not matter and one edit
    cannot create or hide the text another one needs.
    """
    spans = []
    for edit in edits:
        start = text.find(edit.old)
        if start < 0:
            raise ConfigError(f"{where}: edit old text {edit.old!r} is not in {edit.file}")
        # Searching again from the next character also finds an overlapping
        # repeat, such as "aa" in "aaa", which str.count would miss.
        if text.find(edit.old, start + 1) >= 0:
            raise ConfigError(f"{where}: edit old text {edit.old!r} appears more than once in {edit.file}")
        spans.append((start, start + len(edit.old), edit))
    spans.sort(key=lambda span: span[0])
    for (_, end, first), (start, _, second) in itertools.pairwise(spans):
        # Two replacements of the same characters have no single result.
        if start < end:
            raise ConfigError(f"{where}: edits {first.old!r} and {second.old!r} overlap in {first.file}")
    pieces = []
    position = 0
    for start, end, edit in spans:
        pieces += [text[position:start], edit.new]
        position = end
    pieces.append(text[position:])
    return "".join(pieces)


def _inside(baseline: Path, published: str, port: Port) -> Path:
    """
    Join a case's path to the baseline and confirm it still points inside it.

    Loading already rejects "..", absolute paths and drive letters; this also
    catches a symbolic link in the baseline that leads out of it, because the
    case's edits would be applied to a file read through that link.
    """
    path = baseline / published
    if not path.resolve().is_relative_to(baseline.resolve()):
        raise ConfigError(f"{port.root} names {published!r}, which resolves outside the baseline")
    # The working copy leaves these folders out, so a change there would pass
    # validate and then fail in the middle of a run.
    if any(part in _IGNORED_NAMES for part in PurePosixPath(published).parts):
        raise ConfigError(f"{port.root} names {published!r}, inside a folder the working copy leaves out")
    return path


def changed_files(framework: Framework, port: Port) -> dict[str, bytes]:
    """
    Give the new content of every file the case changes, keyed by its path in the baseline.

    Raises ConfigError when the case names a file the baseline does not have,
    or an edit does not match the baseline's text exactly once.
    """
    changed = {}
    for published, source in port.files.items():
        _inside(framework.baseline, published, port)
        if not (framework.baseline / published).is_file():
            # A case may only change files the clean app has, so its
            # difference stays visible next to the baseline.
            raise ConfigError(f"{port.root} replaces {published!r}, which the baseline does not have")
        changed[published] = source.read_bytes()
    by_file: dict[str, list[Edit]] = {}
    for edit in port.edits:
        by_file.setdefault(edit.file, []).append(edit)
    for published, edits in by_file.items():
        path = _inside(framework.baseline, published, port)
        if not path.is_file():
            raise ConfigError(f"{port.root} edits {published!r}, which the baseline does not have")
        # Bytes are decoded by hand, because read_text would turn CRLF line
        # endings into LF and the working copy would no longer match the file.
        text = path.read_bytes().decode("utf-8")
        changed[published] = apply_edits(text, edits, str(port.root)).encode("utf-8")
    return changed


def mistake_lines(text: str, needle: str) -> list[int]:
    """Give the 1-based numbers of the lines that contain the mistake text."""
    return [number for number, line in enumerate(text.splitlines(), start=1) if needle in line]


def materialize(framework: Framework, port: Port | None) -> WorkCopy:
    """
    Copy the clean app and apply the case's changes to it.

    The copy sits inside the environment folder, so Node's module lookup,
    which walks up the parent folders, finds the shared node_modules.
    """
    env = env_dir(framework)
    name = "baseline" if port is None else port.mistake
    work = env / "work" / name
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(framework.baseline, work, ignore=_IGNORED)
    mistake_line = None
    if port is not None:
        changed = changed_files(framework, port)
        for published, content in changed.items():
            # Writing into the copied file keeps its permissions.
            (work / published).write_bytes(content)
        mistake_line = locate(changed[port.mistake_file].decode("utf-8"), port.mistake_contains, port)
    return WorkCopy(work, mistake_line)


def locate(text: str, needle: str, port: Port) -> int:
    lines = mistake_lines(text, needle)
    if len(lines) != 1:
        raise ConfigError(f"{port.root}: mistake text {needle!r} must appear on exactly one line, found {len(lines)}")
    return lines[0]
