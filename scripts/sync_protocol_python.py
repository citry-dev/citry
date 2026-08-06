"""Update or check the protocol-owned Python packages embedded in ``citry``."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMBEDDED_ROOT = ROOT / "packages" / "py" / "citry" / "citry" / "_protocol"
PACKAGES = {
    "events": ROOT / "packages" / "protocol" / "events" / "v1" / "python" / "citry_events",
    "client_graph": ROOT / "packages" / "protocol" / "client_graph" / "v1" / "python" / "citry_client_graph",
}


def _python_files(directory: Path) -> dict[Path, bytes]:
    if not directory.exists():
        return {}
    return {
        path.relative_to(directory): path.read_bytes()
        for path in sorted(directory.rglob("*.py"))
        if "__pycache__" not in path.parts
    }


def _problems(source: Path, target: Path, label: str) -> list[str]:
    expected = _python_files(source)
    actual = _python_files(target)
    problems: list[str] = []
    for relative in sorted(set(expected) | set(actual)):
        if relative not in actual:
            problems.append(f"{label}: embedded copy is missing {relative}")
        elif relative not in expected:
            problems.append(f"{label}: embedded copy has extra file {relative}")
        elif actual[relative] != expected[relative]:
            problems.append(f"{label}: embedded copy is stale at {relative}")
    return problems


def _sync(source: Path, target: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="citry-protocol-python-") as temporary:
        staged = Path(temporary) / target.name
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report stale copies without changing files.")
    args = parser.parse_args()

    available = {name: source for name, source in PACKAGES.items() if source.exists()}
    if not available:
        sys.stderr.write("No canonical protocol Python packages exist.\n")
        return 1
    if args.check:
        problems = [
            problem for name, source in available.items() for problem in _problems(source, EMBEDDED_ROOT / name, name)
        ]
        if problems:
            sys.stderr.write("\n".join(problems) + "\n")
            return 1
        sys.stdout.write(f"Protocol Python copies are current ({', '.join(available)}).\n")
        return 0
    for name, source in available.items():
        _sync(source, EMBEDDED_ROOT / name)
        sys.stdout.write(f"Updated {EMBEDDED_ROOT / name}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
