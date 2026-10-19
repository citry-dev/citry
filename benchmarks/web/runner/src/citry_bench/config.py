"""Validate profiles and identify the exact source inputs of a run."""

import hashlib
import json
import os
import platform
import sys
import tomllib
from pathlib import Path

WEB = Path(__file__).resolve().parents[3]
ROOT = WEB.parents[1]
CACHE = ROOT / ".benchmarks"
SCHEMA = 1
IGNORED = {".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", ".DS_Store"}
FIELDS = {
    "name",
    "mode",
    "apps",
    "scenario",
    "scenario_revision",
    "counts",
    "browser",
    "python",
    "blocks",
    "sessions",
    "warmups",
    "cycles",
    "initial_timeout_ms",
    "action_timeout_ms",
    "cache",
    "network",
    "compression",
    "seed",
    "publication",
}


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def files(directory: Path, exclude: tuple[str, ...] = ()) -> list[Path]:
    result = []
    for parent, directories, filenames in os.walk(directory, followlinks=False):
        for name in list(directories) + filenames:
            path = Path(parent) / name
            relative = path.relative_to(directory)
            if set(relative.parts) & IGNORED or any(relative.is_relative_to(item) for item in exclude):
                if name in directories:
                    directories.remove(name)
                continue
            # Check links before file type, including broken and directory links.
            if path.is_symlink():
                raise ValueError(f"Source symlinks are unsupported: {path}")
            if path.is_file():
                result.append(path)
    return sorted(result)


def source_manifest(directory: Path, exclude: tuple[str, ...] = ()) -> dict[str, str]:
    result = {}
    for path in files(directory, exclude):
        result[str(path.relative_to(directory))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def generated_manifest(directory: Path) -> dict:
    """Record prepared files and confined links, including build dependencies.

    Installed Python packages have their own inventory. Interpreter and test
    caches are mutable runtime output. Every other generated path, including
    empty directories and node_modules, participates in the frozen inventory.
    Directory links are recorded without traversing them; their real targets
    must be inside this inventory, so target bytes are checked independently.
    """
    root = directory.resolve()
    result = {}
    links = []
    for parent, directories, filenames in os.walk(root, followlinks=False):
        for name in list(directories) + filenames:
            path = Path(parent) / name
            relative = path.relative_to(root)
            if (
                relative.parts[0] == ".venv"
                or set(relative.parts) & {"__pycache__", ".pytest_cache", ".ruff_cache"}
                or path.suffix == ".pyc"
            ):
                if name in directories:
                    directories.remove(name)
                continue
            key = str(relative)
            if path.is_symlink():
                try:
                    target = path.resolve(strict=True)
                except (OSError, RuntimeError) as error:
                    raise ValueError(f"Broken or cyclic generated symlink: {path}") from error
                if not target.is_relative_to(root):
                    raise ValueError(f"Generated symlink escapes the application: {path}")
                if target.is_dir() and path.parent.is_relative_to(target):
                    raise ValueError(f"Cyclic generated directory symlink: {path}")
                result[key] = {"type": "symlink", "target": os.readlink(path)}
                links.append((key, str(target.relative_to(root))))
            elif path.is_dir():
                result[key] = {"type": "directory"}
            elif path.is_file():
                result[key] = hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                raise ValueError(f"Unsupported generated file type: {path}")
    for key, target in links:
        if target not in result:
            raise ValueError(f"Generated symlink target is outside the inventory: {key}")
    # Directory links can form cycles through siblings even when each individual
    # link resolves successfully. Check the directory graph without following it.
    children = {key: [] for key, value in result.items() if value == {"type": "directory"}}
    children["."] = []
    for key in children:
        if key != ".":
            children[str(Path(key).parent)].append(key)
    for key, target in links:
        if target in children:
            children[str(Path(key).parent)].append(target)
    active = set()
    complete = set()
    pending = [(".", False)]
    while pending:
        key, leaving = pending.pop()
        if leaving:
            active.remove(key)
            complete.add(key)
        elif key in active:
            raise ValueError(f"Cyclic generated directory links: {key}")
        elif key not in complete:
            active.add(key)
            pending.append((key, True))
            pending.extend((child, False) for child in children[key])
    return dict(sorted(result.items()))


def profile(name: str) -> dict:
    path = WEB / "profiles" / f"{name}.toml"
    if Path(name).name != name:
        raise ValueError("Select a profile name, not a path")
    data = tomllib.loads(path.read_text())
    optional = {"local_wheels"}
    if FIELDS - set(data) or set(data) - FIELDS - optional:
        raise ValueError(f"Profile fields: missing={FIELDS - set(data)}, unknown={set(data) - FIELDS - optional}")
    wheels = data.get("local_wheels", {})
    if not isinstance(wheels, dict) or any(
        not isinstance(name, str) or not isinstance(path, str) or not path for name, path in wheels.items()
    ):
        raise ValueError("local_wheels must map distribution names to wheel paths")
    for name, value in wheels.items():
        path = Path(value)
        resolved = path if path.is_absolute() else ROOT / path
        if name not in {"citry", "citry-core"} or resolved.suffix != ".whl" or not resolved.is_file():
            raise ValueError(f"Invalid local wheel for {name!r}: {value!r}")
    for key in ("blocks", "sessions", "cycles", "initial_timeout_ms", "action_timeout_ms"):
        if type(data[key]) is not int or data[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if type(data["warmups"]) is not int or data["warmups"] < 0:
        raise ValueError("warmups must be a nonnegative integer")
    if type(data["seed"]) is not int or type(data["publication"]) is not bool:
        raise ValueError("seed must be an integer and publication a boolean")
    if (
        not isinstance(data["apps"], list)
        or not data["apps"]
        or any(not isinstance(app, str) for app in data["apps"])
        or len(set(data["apps"])) != len(data["apps"])
    ):
        raise ValueError("apps must be a nonempty unique list")
    for app in data["apps"]:
        if not isinstance(app, str) or Path(app).name != app or not (WEB / "apps" / app).is_dir():
            raise ValueError(f"Unknown application: {app}")
    if (
        not isinstance(data["counts"], list)
        or not data["counts"]
        or any(type(n) is not int or n not in (14, 140, 1400) for n in data["counts"])
    ):
        raise ValueError("counts must select 14, 140 or 1400 outputs")
    supported = {
        "mode": "native",
        "scenario": "project_board",
        "scenario_revision": "canonical-project-v1",
        "browser": "chromium",
        "cache": "cold-context",
        "network": "loopback",
        "compression": "identity",
    }
    for key, expected in supported.items():
        if data[key] != expected:
            raise ValueError(f"Unsupported {key}: {data[key]!r}; implemented: {expected}")
    if data["publication"]:
        raise ValueError(
            "Publication requires container, network and statistical qualification; native runs are diagnostic"
        )
    return data


def adapter(directory: Path) -> dict:
    data = tomllib.loads((directory / "adapter.toml").read_text())
    if set(data) != {"app"}:
        raise ValueError("Adapter must contain only an app table")
    app = data["app"]
    allowed = {
        "name",
        "runtime",
        "launch",
        "node",
        "health",
        "transport",
        "audit",
        "build",
        "allow_dependency_build",
        "source_exclude",
        "port",
        "rendering",
        "update_payload",
        "hydration_min_count",
        "timing_boundary",
        "local_wheels",
    }
    if set(app) - allowed or not {"name", "launch", "health"} <= set(app):
        raise ValueError(f"Invalid adapter fields: {directory}")
    app.setdefault("runtime", "python")
    if app["runtime"] not in ("python", "node"):
        raise ValueError("Adapter runtime must be python or node")
    if "port" in app and (type(app["port"]) is not int or not 1024 <= app["port"] <= 65535):
        raise ValueError("Adapter port must be an integer from 1024 to 65535")
    if "node" in app:
        node = Path(app["node"]) if isinstance(app["node"], str) else None
        if (
            not isinstance(app["node"], str)
            or not app["node"]
            or node is None
            or node.is_absolute()
            or ".." in node.parts
        ):
            raise ValueError("Adapter node must be a relative executable path")
    if app["runtime"] == "node" and "node" not in app:
        raise ValueError("Node adapters must declare a pinned node executable")
    if app["runtime"] == "python" and "node" in app:
        raise ValueError("Python adapters must not declare a node executable")
    app.setdefault("rendering", "server")
    if app["rendering"] not in ("server", "browser", "hybrid"):
        raise ValueError("Adapter rendering must be server, browser or hybrid")
    if "update_payload" in app and app["update_payload"] not in ("html", "json", "delta"):
        raise ValueError("Adapter update_payload must be html, json or delta")
    if app["rendering"] == "hybrid" and app.get("update_payload") not in ("json", "delta"):
        raise ValueError("Hybrid adapters must declare update_payload as json or delta")
    if app["rendering"] != "hybrid" and "update_payload" in app:
        raise ValueError("update_payload is only valid for hybrid adapters")
    # A framework may decide per page whether to write server HTML for
    # hydration. The runner needs that decision per board size to label the
    # initial output and to know whether the board exists before scripts run.
    if "hydration_min_count" in app:
        if app["rendering"] != "hybrid":
            raise ValueError("hydration_min_count is only valid for hybrid adapters")
        if type(app["hydration_min_count"]) is not int or app["hydration_min_count"] < 1:
            raise ValueError("hydration_min_count must be a positive integer")
    app.setdefault("timing_boundary", "complete")
    if app["timing_boundary"] not in ("complete", "first-chunk"):
        raise ValueError("Adapter timing_boundary must be complete or first-chunk")
    app.setdefault("transport", "http")
    app.setdefault("build", [])
    app.setdefault("allow_dependency_build", False)
    app.setdefault("source_exclude", [])
    app.setdefault("local_wheels", [])
    if app["transport"] not in ("http", "websocket"):
        raise ValueError("Unsupported adapter transport")
    for command in [app["launch"], *app["build"]]:
        if not isinstance(command, list) or not command or any(not isinstance(part, str) for part in command):
            raise ValueError("Adapter commands must be nonempty argument lists")
    if not isinstance(app["allow_dependency_build"], bool):
        raise ValueError("allow_dependency_build must be a boolean")
    if any("{node}" in part for part in app["launch"]) and "node" not in app:
        raise ValueError("Node launch commands require an adapter node path")
    for field in ("health", "audit"):
        if field in app and (
            not isinstance(app[field], str) or not app[field].startswith("/") or app[field].startswith("//")
        ):
            raise ValueError(f"{field} must be a same-origin absolute path")
    if not isinstance(app["source_exclude"], list) or any(not isinstance(item, str) for item in app["source_exclude"]):
        raise ValueError("source_exclude must be a list of relative paths")
    if (
        not isinstance(app["local_wheels"], list)
        or len(set(app["local_wheels"])) != len(app["local_wheels"])
        or any(item not in {"citry", "citry-core"} for item in app["local_wheels"])
    ):
        raise ValueError("local_wheels must be a unique list of supported distribution names")
    if app["runtime"] == "node" and app["local_wheels"]:
        raise ValueError("Node adapters cannot install Python local wheels")
    for item in app["source_exclude"]:
        if (
            not isinstance(item, str)
            or not item
            or Path(item).is_absolute()
            or ".." in Path(item).parts
            or item == "."
        ):
            raise ValueError("Source exclusions must be relative input paths")
    if app["transport"] == "websocket" and "audit" not in app:
        raise ValueError("WebSocket adapter requires an audit endpoint")
    return app


def initial_rendering(adapter: dict, count: int) -> str:
    """Return where the initial page of this board size is rendered.

    A hybrid adapter with ``hydration_min_count`` mounts smaller boards in the
    browser, so their initial page behaves like a browser-rendered adapter's:
    its output is labelled by transport (JSON over HTTP, deltas over a
    WebSocket), not by ``update_payload``. Updates keep the hybrid adapter's
    declared ``update_payload``.
    """
    rendering = adapter.get("rendering", "server")
    if rendering == "hybrid" and count < adapter.get("hydration_min_count", 0):
        return "browser"
    return rendering


def artifact_manifest(directory: Path) -> dict[str, str]:
    """Hash installed bytes, excluding interpreter-generated caches."""
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def identity(settings: dict) -> dict:
    return {
        "schema": SCHEMA,
        "profile": settings,
        "runner": source_manifest(WEB / "runner"),
        "scenario": source_manifest(WEB / "scenarios" / settings["scenario"]),
        "apps": {
            name: source_manifest(WEB / "apps" / name, tuple(adapter(WEB / "apps" / name)["source_exclude"]))
            for name in settings["apps"]
        },
        "platform": platform.platform(),
        "machine": platform.machine(),
        "runner_python": sys.version,
        "runner_environment": artifact_manifest(Path(sys.prefix)),
        "local_wheels": {
            name: {
                "path": value,
                "size": (path if path.is_absolute() else ROOT / path).stat().st_size,
                "sha256": hashlib.sha256((path if path.is_absolute() else ROOT / path).read_bytes()).hexdigest(),
            }
            for name, value in settings.get("local_wheels", {}).items()
            for path in (Path(value),)
        },
    }
