"""Install each framework once and make a fresh working copy of its app for every case."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import CACHE, REPO_ROOT, ConfigError

if TYPE_CHECKING:
    from pathlib import Path

    from .config import Framework, Port

# Build output and installed dependencies never belong in a working copy: the
# environment is shared, and stale build output would hide the case's change.
_IGNORED = shutil.ignore_patterns("node_modules", ".venv", ".next", ".nuxt", ".output", "__pycache__", "dist")


def env_dir(framework: Framework) -> Path:
    return CACHE / "envs" / framework.key


def _manifest_digest(framework: Framework) -> str:
    digest = hashlib.sha256()
    for name in framework.setup_manifests:
        digest.update(name.encode())
        digest.update((framework.baseline / name).read_bytes())
    return digest.hexdigest()


def prepare(framework: Framework) -> Path:
    """Install the framework's locked dependencies into its environment folder, once per lockfile."""
    env = env_dir(framework)
    marker = env / "prepared.json"
    digest = _manifest_digest(framework)
    if marker.is_file() and json.loads(marker.read_text()).get("digest") == digest:
        return env
    env.mkdir(parents=True, exist_ok=True)
    marker.unlink(missing_ok=True)
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


def placeholder(value: str, framework: Framework, env: Path, work: Path, port: int = 0) -> str:
    return value.format_map(
        {
            "env": str(env),
            "venv": str(env / ".venv"),
            "work": str(work),
            "port": str(port),
            "repo": str(REPO_ROOT),
            "framework": str(framework.root),
        }
    )


def command_env(
    framework: Framework, env: Path, work: Path, extra: dict[str, str] | None = None, port: int = 0
) -> dict[str, str]:
    """Run every tool with the framework's own environment first on PATH and the app importable."""
    base = {key: value for key, value in os.environ.items() if key not in {"VIRTUAL_ENV", "PYTHONPATH"}}
    base["PATH"] = os.pathsep.join([str(env / ".venv" / "bin"), str(env / "node_modules" / ".bin"), base["PATH"]])
    base["PYTHONPATH"] = str(work)
    base["NEXT_TELEMETRY_DISABLED"] = "1"
    base["NUXT_TELEMETRY_DISABLED"] = "1"
    base["PYTHONDONTWRITEBYTECODE"] = "1"
    for key, value in (extra or {}).items():
        base[key] = placeholder(value, framework, env, work, port)
    return base


@dataclass(frozen=True)
class WorkCopy:
    path: Path
    mistake_line: int | None


def materialize(framework: Framework, port: Port | None) -> WorkCopy:
    """
    Copy the clean app and lay the case's files over it.

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
        for published, source in port.files.items():
            target = work / published
            if not (framework.baseline / published).is_file():
                # A case may only change files the clean app has, so its
                # difference stays visible next to the baseline.
                raise ConfigError(f"{port.root} replaces {published!r}, which the baseline does not have")
            shutil.copy2(source, target)
        mistake_line = locate(work / port.mistake_file, port.mistake_contains, port)
    return WorkCopy(work, mistake_line)


def locate(path: Path, needle: str, port: Port) -> int:
    lines = [number for number, line in enumerate(path.read_text().splitlines(), start=1) if needle in line]
    if len(lines) != 1:
        raise ConfigError(f"{port.root}: mistake text {needle!r} must appear on exactly one line, found {len(lines)}")
    return lines[0]
