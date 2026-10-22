"""
Every build backend uv downloads for a workspace package is pinned with a hash.

The root pyproject pins every build backend the workspace packages need to an
exact version with sha256 hashes in `[tool.uv] build-constraint-dependencies`,
and sets `require-build-hashes`. If a package starts asking for a backend the
list does not pin, or for a version range the pin does not satisfy, uv fails
when it builds that package. This check reports the problem first, without
network access.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]

try:
    from scripts import build_constraints
except ImportError:  # validate.py runs with scripts/ itself on sys.path.
    import build_constraints  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parents[2]
PREVIEW_FEATURE = "build-dependency-hashes"
FIX = "run `python scripts/build_constraints.py update && uv lock`"
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}")


def _pinned_version(requirement: Requirement) -> str | None:
    # Only one exact `==` pin lets uv match a download to the listed hashes.
    specifiers = list(requirement.specifier)
    if len(specifiers) == 1 and specifiers[0].operator == "==" and "*" not in specifiers[0].version:
        return specifiers[0].version
    return None


def _constraint_errors(entries: Any) -> tuple[list[str], dict[str, list[str]], set[str]]:
    """
    Check each root entry's shape and return the pins that apply on every Python, by package name.

    The third value names the packages pinned only under an environment marker.
    """
    errors: list[str] = []
    pinned: dict[str, list[str]] = {}
    marked: set[str] = set()
    if not isinstance(entries, list) or not entries:
        return [f"[tool.uv] build-constraint-dependencies is missing or empty; {FIX}"], pinned, marked
    for entry in entries:
        # A bare string constraint carries no hash, so uv would refuse the download.
        if not isinstance(entry, dict) or not isinstance(entry.get("requirement"), str):
            errors.append(f"build constraint {entry!r} must be {{ requirement = ..., hashes = [...] }}; {FIX}")
            continue
        try:
            requirement = Requirement(entry["requirement"])
        except InvalidRequirement as error:
            errors.append(f"build constraint {entry['requirement']!r} is not a valid requirement ({error}); {FIX}")
            continue
        version = _pinned_version(requirement)
        if version is None:
            errors.append(f"build constraint {entry['requirement']!r} must pin one exact version with ==; {FIX}")
            continue
        hashes = entry.get("hashes")
        if not isinstance(hashes, list) or not hashes or not all(_SHA256.fullmatch(str(h)) for h in hashes):
            errors.append(f"build constraint {entry['requirement']!r} needs at least one sha256 hash; {FIX}")
            continue
        name = canonicalize_name(requirement.name)
        # A marked pin (such as tomli for Python 3.10 only) cannot stand in for
        # a backend a package names directly, which every Python needs.
        if requirement.marker is None:
            pinned.setdefault(name, []).append(version)
        else:
            marked.add(name)
    return errors, pinned, marked


def build_pin_errors(root: Path) -> list[str]:
    """Return a problem for each build backend that is not pinned with a hash in `root`."""
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    uv_settings = tomllib.loads(text).get("tool", {}).get("uv", {})
    errors: list[str] = []

    # Without this setting uv checks the listed hashes but still installs an
    # unlisted build dependency, including a transitive one, unchecked.
    if uv_settings.get("require-build-hashes") is not True:
        errors.append(
            "[tool.uv] must set require-build-hashes = true, or uv installs an unlisted build dependency "
            "without checking it; add the line to the root pyproject.toml"
        )
    # uv prints a preview warning on every command unless the feature is named.
    if PREVIEW_FEATURE not in uv_settings.get("preview-features", []):
        errors.append(
            f'[tool.uv] preview-features must include "{PREVIEW_FEATURE}", or uv prints a preview warning '
            "on every command; add it to the root pyproject.toml"
        )

    entries = uv_settings.get("build-constraint-dependencies")
    entry_errors, pinned, marked = _constraint_errors(entries)
    errors.extend(entry_errors)

    # The --no-config builders read the marked block as text, so it must hold
    # exactly the entries uv reads from the table.
    try:
        exported = [(pin.requirement, list(pin.hashes)) for pin in build_constraints.parse_pins(text)]
    except build_constraints.BuildConstraintError as error:
        # `update` needs the markers too, so the fix starts with restoring them.
        errors.append(
            f"{error}; restore the `{build_constraints.BEGIN_MARKER}` and `{build_constraints.END_MARKER}` "
            f"lines, then {FIX}"
        )
    else:
        table = [
            (entry.get("requirement"), entry.get("hashes")) if isinstance(entry, dict) else (entry, None)
            for entry in (entries if isinstance(entries, list) else [])
        ]
        if exported != table:
            # `update` rewrites only the marked lines, so the stray entry has to go by hand.
            errors.append(
                "build-constraint-dependencies has an entry outside the generated block, which --no-config "
                f"builds would not export; delete it, then {FIX}"
            )

    for package in sorted((root / "packages" / "py").glob("*/pyproject.toml")):
        relative = package.relative_to(root)
        requires = tomllib.loads(package.read_text(encoding="utf-8")).get("build-system", {}).get("requires", [])
        for raw in requires:
            requirement = Requirement(raw)
            versions = pinned.get(canonicalize_name(requirement.name), [])
            if not versions and canonicalize_name(requirement.name) in marked:
                errors.append(
                    f"{relative} builds with {raw!r}, but its build constraint applies only under an "
                    f"environment marker; {FIX}"
                )
            elif not versions:
                errors.append(f"{relative} builds with {raw!r}, which has no hashed build constraint; {FIX}")
            elif not any(requirement.specifier.contains(version, prereleases=True) for version in versions):
                errors.append(
                    f"{relative} builds with {raw!r}, but the build constraint pins {', '.join(versions)}; {FIX}"
                )
    return errors


def check() -> list[str]:
    """Check the repository's build-backend pins."""
    return build_pin_errors(REPO_ROOT)
