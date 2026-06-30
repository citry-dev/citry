"""
Dependabot coverage: every Python package under packages/py/ must have a
matching entry in .github/dependabot.yml, and every packages/py/ entry there
must point to a real package.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_DIRECTORY_RE = re.compile(r'directory:\s*["\']?(packages/py/[^"\'\s]+)["\']?')


def _python_packages() -> set[str]:
    packages_dir = REPO_ROOT / "packages" / "py"
    if not packages_dir.exists():
        return set()
    return {
        f"packages/py/{item.name}"
        for item in packages_dir.iterdir()
        if item.is_dir() and ((item / "pyproject.toml").exists() or (item / "__init__.py").exists())
    }


def check() -> list[str]:
    dependabot = REPO_ROOT / ".github" / "dependabot.yml"
    if not dependabot.exists():
        return [f"{dependabot} not found"]

    entries = set(_DIRECTORY_RE.findall(dependabot.read_text()))
    packages = _python_packages()

    problems: list[str] = []
    for pkg in sorted(packages - entries):
        problems.append(f"package '{pkg}' has no Dependabot entry")
    for entry in sorted(entries - packages):
        problems.append(f"Dependabot entry '{entry}' points to a missing package")
    return problems
