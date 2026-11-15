r"""
Check that citry-lsp and citry keep working together across 1.x releases.

Every citry-lsp 1.x release must work with every citry 1.x release, so a
user can upgrade either package first. Release qualification checks the two
pairs furthest apart:

- ``old-lsp``: the oldest citry-lsp release with the candidate's major
  version, installed from PyPI next to the candidate citry wheel. It runs
  the tests of that citry-lsp release, taken from its git tag.
- ``old-citry``: the oldest citry release with the candidate's major
  version (1.0.0 for 1.x), installed from PyPI next to the candidate
  citry-lsp wheel. It runs this checkout's citry-lsp tests.

citry-lsp and citry share their major version (citry-lsp 1.0.0 ships with
citry 1.0.0), so "the same major version" pairs the right releases. When
PyPI has no release of the other package with the candidate's major
version yet, no published release promises to work with the candidate,
so the script says so and skips the pair without failing. A candidate
below 1.0.0 is skipped the same way, because 0.x releases make no such
promise.

Run it from the repository root, with the wheels the release built:

    python scripts/lsp_citry_pairs.py old-lsp \\
        --citry-wheel dist/citry-1.1.0-py3-none-any.whl \\
        [--core-wheel core-dist/citry_core-....whl]

    python scripts/lsp_citry_pairs.py old-citry \\
        --lsp-wheel dist/citry_lsp-1.1.0-py3-none-any.whl

``--version`` picks the other package's release by hand instead of the
oldest one, for example to try the check against a 0.x release.

A test may fail for a reason that is not a break. In the old-lsp pair, an
old test may assert the exact text of a Citry diagnostic that a later
citry reworded on purpose. In the old-citry pair, a test may need a fix
that only a later citry has. List such a test in ``KNOWN_DIFFERENCES``
with a comment that says why, so the pair runs the rest. A test of a
feature that citry-lsp turns off on an older citry should skip itself
instead. Anything else that fails is a real incompatibility: in the
old-lsp pair, fix it in citry (see ``citry/_lsp_support.py`` and
docs/codebase.md, "Breaking changes"); in the old-citry pair, make
citry-lsp handle the older citry. A deprecation warning is shown but
does not fail either pair, because a 1.x minor release may deprecate a
name that an older citry-lsp still uses.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
LSP_TESTS = Path("packages") / "py" / "citry_lsp" / "tests"
LSP_PYPROJECT = Path("packages") / "py" / "citry_lsp" / "pyproject.toml"
TAG_PREFIX = {"citry-lsp": "citry-lsp@"}
# The test runner distributes test files over the CPU cores, as the
# repository check does, so the pair takes about as long as one CI test job.
RUNNER_REQUIREMENTS = ("pytest-xdist>=3.8.0",)

# Tests that may fail on purpose, by pair and by the version of the
# published release in that pair (citry-lsp for old-lsp, citry for
# old-citry). Each entry is a pytest node ID relative to the checkout
# root, such as "packages/py/citry_lsp/tests/test_engine.py::test_name",
# and needs a comment saying which change it follows and why it is not a
# break.
KNOWN_DIFFERENCES: dict[str, dict[str, tuple[str, ...]]] = {"old-lsp": {}, "old-citry": {}}
# How often to ask PyPI before giving up, since one dropped connection
# should not fail a release.
PYPI_ATTEMPTS = 3


def say(message: str) -> None:
    """Print one line now, before a later command's output, so the job log reads in order."""
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def version_tuple(version: str) -> tuple[int, ...] | None:
    """Read a final release number such as 1.2.3; anything else (a pre-release) is None."""
    if re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        return None
    return tuple(int(part) for part in version.split("."))


def wheel_version(wheel: Path) -> str:
    """Read a wheel's version from its file name, `{name}-{version}-{tags}.whl`."""
    parts = wheel.name.split("-")
    if wheel.suffix != ".whl" or len(parts) < 3:
        msg = f"{wheel} is not a wheel file name"
        raise SystemExit(msg)
    return parts[1]


def published_releases(package: str) -> dict[str, list[dict[str, Any]]]:
    """Return PyPI's `releases` map for one package."""
    url = f"https://pypi.org/pypi/{package}/json"
    for attempt in range(1, PYPI_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - a fixed https URL
                releases: dict[str, list[dict[str, Any]]] = json.load(response)["releases"]
        except OSError:
            if attempt == PYPI_ATTEMPTS:
                raise
            time.sleep(5 * attempt)
        else:
            return releases
    raise AssertionError  # the loop either returns or raises


def oldest_in_major(releases: dict[str, list[dict[str, Any]]], major: int) -> str | None:
    """Pick the oldest final release with this major version, skipping yanked ones and pre-releases."""
    usable = [
        version
        for version, files in releases.items()
        if (number := version_tuple(version)) is not None
        and number[0] == major
        and files
        and not all(item.get("yanked") for item in files)
    ]
    if not usable:
        return None
    return min(usable, key=lambda version: version_tuple(version) or ())


def pick_other_release(package: str, candidate: str, chosen: str | None) -> str | None:
    """Return the release of `package` to pair with the candidate, or None (with a message) to skip."""
    if chosen is not None:
        return chosen
    number = version_tuple(candidate)
    if number is None or number[0] < 1:
        say(f"skipped: candidate {candidate} is not a 1.x or later final release, so no pair is promised")
        return None
    oldest = oldest_in_major(published_releases(package), number[0])
    if oldest is None:
        say(
            f"skipped: PyPI has no {package} {number[0]}.x release yet, so no published release "
            "promises to work with the candidate"
        )
    return oldest


def run(command: list[str], *, cwd: Path | None = None) -> None:
    """Run a command and stop with its output when it fails."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        msg = f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        raise SystemExit(msg)


def probe(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git query in the repository and return its result, failed or not."""
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def test_requirements(checkout: Path) -> list[str]:
    """Read citry-lsp's test-only dependencies from the checkout whose tests run."""
    project = tomllib.loads((checkout / LSP_PYPROJECT).read_text(encoding="utf-8"))
    return [str(item) for item in project.get("dependency-groups", {}).get("dev", []) if isinstance(item, str)]


def make_environment(path: Path, requirements: list[str]) -> Path:
    """Create a virtual environment with uv and install the requirements; return its Python."""
    run(["uv", "venv", "--quiet", "--python", sys.executable, str(path)])
    python = path / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    # `--no-sources` resolves citry and citry-core from PyPI or the given
    # wheels, never from this checkout's workspace members.
    run(["uv", "pip", "install", "--quiet", "--no-sources", "--python", str(python), *requirements])
    return python


def tag_checkout(package: str, version: str, destination: Path) -> Path:
    """Check out the git tag of a published release, so its own tests run against the installed wheel."""
    tag = f"{TAG_PREFIX[package]}{version}"
    has_tag = probe(["git", "rev-parse", "--quiet", "--verify", f"refs/tags/{tag}"]).returncode == 0
    # A release job checks out one commit without tags, so fetch just this
    # one. `--depth 1` only in a clone that is already shallow: in a full
    # clone it would make the whole repository shallow.
    if not has_tag:
        shallow = probe(["git", "rev-parse", "--is-shallow-repository"])
        depth = ["--depth", "1"] if shallow.stdout.strip() == "true" else []
        run(["git", "fetch", "--quiet", *depth, "origin", f"refs/tags/{tag}:refs/tags/{tag}"], cwd=REPO_ROOT)
    run(["git", "worktree", "add", "--quiet", "--detach", str(destination), tag], cwd=REPO_ROOT)
    return destination


def run_tests(python: Path, checkout: Path, deselect: tuple[str, ...]) -> int:
    """Run the checkout's citry-lsp tests with the installed packages and return pytest's exit code."""
    command = [
        str(python),
        # `-I` keeps the working folder off the import path, so the tests
        # import the installed wheels. pytest's `pythonpath` setting adds
        # the checkout root, which holds no package source.
        "-I",
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "-n",
        "auto",
        "--dist",
        "loadfile",
        "--rootdir",
        str(checkout),
        "-c",
        str(checkout / "pyproject.toml"),
        # A command-line filter wins over the configuration's, which turns
        # every deprecation warning into an error.
        "-W",
        "default::DeprecationWarning",
        *(f"--deselect={item}" for item in deselect),
        str(checkout / LSP_TESTS),
    ]
    started = time.monotonic()
    code = subprocess.run(command, cwd=checkout, check=False).returncode
    say(f"tests took {time.monotonic() - started:.0f} s")
    return code


def check_old_lsp(citry_wheel: Path, core_wheel: Path | None, chosen: str | None) -> int:
    """Run the oldest citry-lsp release of the candidate's major version against the candidate citry."""
    candidate = wheel_version(citry_wheel)
    lsp_version = pick_other_release("citry-lsp", candidate, chosen)
    if lsp_version is None:
        return 0
    say(f"pair: citry-lsp {lsp_version} (PyPI) with candidate citry {candidate}")
    with tempfile.TemporaryDirectory(prefix="lsp-citry-pairs-") as temporary:
        root = Path(temporary)
        checkout = tag_checkout("citry-lsp", lsp_version, root / "checkout")
        try:
            wheels = [str(citry_wheel.resolve()), *([str(core_wheel.resolve())] if core_wheel else [])]
            python = make_environment(
                root / "venv",
                [*wheels, f"citry-lsp=={lsp_version}", *test_requirements(checkout), *RUNNER_REQUIREMENTS],
            )
            return run_tests(python, checkout, KNOWN_DIFFERENCES["old-lsp"].get(lsp_version, ()))
        finally:
            run(["git", "worktree", "remove", "--force", str(checkout)], cwd=REPO_ROOT)


def check_old_citry(lsp_wheel: Path, chosen: str | None) -> int:
    """Run the candidate citry-lsp, with this checkout's tests, against the oldest citry of its major version."""
    candidate = wheel_version(lsp_wheel)
    citry_version = pick_other_release("citry", candidate, chosen)
    if citry_version is None:
        return 0
    say(f"pair: candidate citry-lsp {candidate} with citry {citry_version} (PyPI)")
    with tempfile.TemporaryDirectory(prefix="lsp-citry-pairs-") as temporary:
        python = make_environment(
            Path(temporary) / "venv",
            [
                str(lsp_wheel.resolve()),
                f"citry=={citry_version}",
                *test_requirements(REPO_ROOT),
                *RUNNER_REQUIREMENTS,
            ],
        )
        return run_tests(python, REPO_ROOT, KNOWN_DIFFERENCES["old-citry"].get(citry_version, ()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pairs = parser.add_subparsers(dest="pair", required=True)
    old_lsp = pairs.add_parser("old-lsp", help="the oldest citry-lsp of this major version with the candidate citry")
    old_lsp.add_argument("--citry-wheel", type=Path, required=True)
    old_lsp.add_argument("--core-wheel", type=Path, help="the candidate citry-core wheel, when it ships too")
    old_lsp.add_argument("--version", help="pair with this citry-lsp release instead of the oldest")
    old_citry = pairs.add_parser("old-citry", help="the candidate citry-lsp with the oldest citry of this major")
    old_citry.add_argument("--lsp-wheel", type=Path, required=True)
    old_citry.add_argument("--version", help="pair with this citry release instead of the oldest")
    args = parser.parse_args(argv)
    if args.pair == "old-lsp":
        return check_old_lsp(args.citry_wheel, args.core_wheel, args.version)
    return check_old_citry(args.lsp_wheel, args.version)


if __name__ == "__main__":
    sys.exit(main())
