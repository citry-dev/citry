"""
Workspace membership: every crate under crates/ must be listed in
[workspace].members in the root Cargo.toml, and every members entry must point
to a real crate.
"""

from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]

REPO_ROOT = Path(__file__).resolve().parents[2]


def _crates_on_disk() -> set[str]:
    crates_dir = REPO_ROOT / "crates"
    if not crates_dir.exists():
        return set()
    return {f"crates/{item.name}" for item in crates_dir.iterdir() if item.is_dir() and (item / "Cargo.toml").exists()}


def check() -> list[str]:
    cargo = REPO_ROOT / "Cargo.toml"
    if not cargo.exists():
        return [f"{cargo} not found"]

    declared = tomllib.loads(cargo.read_text()).get("workspace", {}).get("members", [])
    members = {member.strip("/") for member in declared}
    crates = _crates_on_disk()

    problems: list[str] = []
    for crate in sorted(crates - members):
        problems.append(f"crate '{crate}' is not listed in [workspace].members")
    for member in sorted(members - crates):
        problems.append(f"[workspace].members entry '{member}' points to a missing crate")
    return problems
