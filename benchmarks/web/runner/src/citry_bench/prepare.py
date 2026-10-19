"""Create frozen application installations without touching the root environment."""

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from uuid import uuid4

from citry_bench.config import (
    CACHE,
    ROOT,
    WEB,
    adapter,
    artifact_manifest,
    digest,
    files,
    generated_manifest,
    identity,
)

# A person profiling an unoptimized citry-core build sets this to "1" so
# preparation and measurement accept it; every other run refuses that build.
ALLOW_DEBUG_NATIVE_ENV = "CITRY_BENCH_ALLOW_DEBUG_NATIVE"

# Printed by each prepared Python app: its interpreter, its installed
# distributions, and whether any citry-core extension it imports is a debug build.
# `unrecorded` marks a citry-core wheel built before the extension reported
# its profile.
INSTALLED_PROBE = """import importlib.metadata as m
import importlib.util
import json
import sys
native_build = None
if importlib.util.find_spec('citry_core') is not None:
    from citry_core import _rust
    native_build = getattr(_rust, 'BUILD_PROFILE', 'unrecorded')
print(json.dumps({
    'python': sys.version,
    'packages': sorted((d.metadata['Name'], d.version) for d in m.distributions()),
    'citry_core_build': native_build,
}))"""


def check_native_build(name: str, installed: dict) -> None:
    """Refuse an app whose citry-core extension was compiled without optimizations.

    A debug build runs the Rust paths many times slower, and the run would
    still finish with plausible numbers, so the refusal is the only signal.
    """
    build = installed.get("citry_core_build")
    if build == "unrecorded":
        # Wheels built before the extension reported its profile cannot be
        # checked. Say so instead of passing them as release builds.
        print(f"NOTE: {name} uses a citry-core wheel that does not report its build profile.", file=sys.stderr)
        return
    if build != "debug":
        return
    if os.environ.get(ALLOW_DEBUG_NATIVE_ENV) == "1":
        print(f"WARNING: {name} uses a debug citry-core build because {ALLOW_DEBUG_NATIVE_ENV}=1.", file=sys.stderr)
        return
    raise ValueError(
        f"{name} installed a debug build of citry-core; its Rust paths run many times slower. "
        "Rebuild the wheel in release mode (`maturin build --release` in packages/py/citry_core), "
        "write it to the path in the benchmark profile's `[local_wheels]` table, and prepare again. "
        f"To measure the debug build on purpose, set {ALLOW_DEBUG_NATIVE_ENV}=1."
    )


def unpublished_locked_packages(directory: Path, replaced: list[str]) -> list[str]:
    """Return locked distributions that only a local wheel folder can supply.

    Before a release is published, an app's lockfile may resolve that release
    from wheels built on the maintainer's machine. Such an entry installs only
    when a profile replaces it through `[local_wheels]`; naming it here turns
    uv's missing-file error into an instruction.
    """
    lock = directory / "uv.lock"
    if not lock.is_file():
        return []
    result = []
    for package in tomllib.loads(lock.read_text()).get("package", []):
        registry = package.get("source", {}).get("registry")
        if registry is not None and not registry.startswith(("https://", "http://")):
            if package["name"] not in replaced:
                result.append(f"{package['name']}=={package['version']}")
    return result


def write_json(path: Path, data: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def copy_sources(source: Path, destination: Path, exclude: tuple[str, ...] = ()) -> None:
    for path in files(source, exclude):
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("VIRTUAL_ENV", "PYTHONPATH", "UV_PROJECT_ENVIRONMENT"):
        env.pop(key, None)
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(CACHE / "browsers")
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    return env


def build_sources(directory: Path, settings: dict) -> dict:
    return {name: generated_manifest(directory / "apps" / name) for name in settings["apps"]}


def expected_sources(inputs: dict) -> dict:
    return {
        name: {**manifest, **{f"scenario/{path}": value for path, value in inputs["scenario"].items()}}
        for name, manifest in inputs["apps"].items()
    }


def runtime_root(target: Path, declaration: dict) -> Path:
    """Return the frozen dependency tree for the adapter's declared runtime."""
    return target / (".toolchain" if declaration["runtime"] == "node" else ".venv")


def runtime_python(target: Path, declaration: dict) -> Path:
    """Return the Python used by a build helper, not necessarily the app runtime."""
    if declaration["runtime"] == "node":
        return Path(sys.executable)
    return target / ".venv/bin/python"


def prepared(settings: dict) -> tuple[Path, dict]:
    inputs = identity(settings)
    directory = CACHE / "builds" / digest(inputs)
    marker = directory / "prepared.json"
    if not marker.exists():
        raise ValueError(f"No current prepared build. Run prepare --profile {settings['name']}")
    data = json.loads(marker.read_text())
    if data["inputs"] != inputs:
        raise ValueError("Prepared inputs differ from current source")
    for name in settings["apps"]:
        declaration = adapter(WEB / "apps" / name)
        if declaration["runtime"] == "node":
            expected = directory / "apps" / name / declaration["node"]
            if not expected.exists():
                raise ValueError(f"Prepared Node runtime missing for {name}; prepare again")
        elif not (directory / "apps" / name / ".venv/bin/python").exists():
            raise ValueError(f"Prepared environment missing for {name}; prepare again")
    if build_sources(directory, settings) != data["build_sources"]:
        raise ValueError("Prepared application snapshot changed; remove that build and prepare again")
    for name in settings["apps"]:
        declaration = adapter(WEB / "apps" / name)
        if artifact_manifest(runtime_root(directory / "apps" / name, declaration)) != data["artifacts"][name]:
            raise ValueError(f"Installed artifacts changed for {name}; prepare a clean build")
        # A debug build prepared with the override stays refused for a later
        # qualify, run or memory command that does not set it again.
        check_native_build(name, data.get("installed", {}).get(name, {}))
    if artifact_manifest(CACHE / "browsers") != data["browser_artifacts"]:
        raise ValueError("Browser installation changed; prepare and qualify again")
    return directory, data


def check_installable(settings: dict) -> None:
    """Stop before any work when an app's lockfile needs wheels the profile does not supply."""
    configured = settings.get("local_wheels", {})
    for name in settings["apps"]:
        declaration = adapter(WEB / "apps" / name)
        if declaration["runtime"] != "python":
            continue
        replaced = [item for item in declaration["local_wheels"] if item in configured]
        unpublished = unpublished_locked_packages(WEB / "apps" / name, replaced)
        if unpublished:
            raise ValueError(
                f"{name} locks {', '.join(unpublished)} from local wheels, not from PyPI. "
                "Build those wheels and select them in the profile's `[local_wheels]` table; "
                f"apps/{name}/README.md explains how."
            )


def prepare(settings: dict) -> Path:
    check_installable(settings)
    inputs = identity(settings)
    directory = CACHE / "builds" / digest(inputs)
    marker = directory / "prepared.json"
    if directory.exists() and not marker.exists():
        # Preserve failed work for diagnosis, but never bless its leftover files.
        directory.rename(directory.with_name(directory.name + ".incomplete-" + uuid4().hex[:8]))
    directory.mkdir(parents=True, exist_ok=True)
    if marker.exists():
        prepared(settings)
        return directory
    env = environment()
    copy_sources(WEB / "runner", directory / "sources" / "runner")
    installed = {}
    artifacts = {}
    for name in settings["apps"]:
        target = directory / "apps" / name
        declaration = adapter(WEB / "apps" / name)
        copy_sources(WEB / "apps" / name, target, tuple(declaration["source_exclude"]))
        copy_sources(WEB / "scenarios" / settings["scenario"], target / "scenario")
        # An app may name distributions that a profile can replace with
        # locally built wheels, to test a release before it is published.
        # Without a `[local_wheels]` table the app installs only its lockfile.
        configured = settings.get("local_wheels", {})
        selected_wheels = [item for item in declaration["local_wheels"] if item in configured]
        if declaration["runtime"] == "python":
            sync = ["uv", "sync", "--frozen", "--no-dev", "--python", settings["python"]]
            if not declaration["allow_dependency_build"]:
                sync.insert(3, "--no-build")
            # The lockfile's copy of a replaced distribution is never
            # installed, so its recorded source need not exist on this machine.
            for item in selected_wheels:
                sync.extend(["--no-install-package", item])
            subprocess.run(
                sync,
                cwd=target,
                env=env,
                check=True,
            )
        python = runtime_python(target, declaration)
        if selected_wheels:
            wheel_paths = [Path(configured[item]) for item in selected_wheels]
            wheel_paths = [path if path.is_absolute() else ROOT / path for path in wheel_paths]
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python), "--no-deps", "--reinstall", *map(str, wheel_paths)],
                cwd=target,
                env=env,
                check=True,
            )
        for command in declaration["build"]:
            argv = [part.format(python=str(python)) for part in command]
            subprocess.run(argv, cwd=target, env=env, check=True)
        if declaration["runtime"] == "node":
            node = target / declaration["node"]
            output = subprocess.check_output([str(node), "--version"], cwd=target, env=env, text=True).strip()
            installed[name] = {"runtime": "node", "node": output}
        else:
            output = subprocess.check_output([str(python), "-c", INSTALLED_PROBE], cwd=target, env=env, text=True)
            installed[name] = json.loads(output)
            # Refuse before the marker is written, so a debug build never
            # becomes a prepared build.
            check_native_build(name, installed[name])
        artifacts[name] = artifact_manifest(runtime_root(target, declaration))
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], env=env, check=True)
    outputs = build_sources(directory, settings)
    for name, expected in expected_sources(inputs).items():
        generated = adapter(WEB / "apps" / name)["source_exclude"]
        for extra in set(outputs[name]) - set(expected):
            if outputs[name][extra] == {"type": "directory"} and any(
                Path(path).is_relative_to(extra) for path in [*expected, *generated]
            ):
                continue
            if not any(Path(extra).is_relative_to(root) for root in generated):
                raise ValueError(f"Build created an undeclared output: {name}/{extra}")
    if (
        any(
            any(outputs[name].get(path) != value for path, value in expected.items())
            for name, expected in expected_sources(inputs).items()
        )
        or identity(settings) != inputs
    ):
        raise ValueError("Sources changed during preparation; rerun prepare on stable inputs")
    write_json(
        marker,
        {
            "inputs": inputs,
            "installed": installed,
            "artifacts": artifacts,
            "build_sources": outputs,
            "browser_artifacts": artifact_manifest(CACHE / "browsers"),
            "source_policy": "captured application sources; frozen installed framework artifacts",
        },
    )
    return directory
