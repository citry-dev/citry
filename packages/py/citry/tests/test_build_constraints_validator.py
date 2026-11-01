"""The build-backend pins stay hashed, readable as text, and in step with each project's build requirements."""

from pathlib import Path

import pytest
from scripts import build_constraints
from scripts.build_constraints import BEGIN_MARKER, END_MARKER, Pin
from scripts.validators.build_backend_pins import build_pin_errors

_HASH_A = "sha256:" + "a" * 64
_HASH_B = "sha256:" + "b" * 64
_PINS = [Pin("backend==2.1.0", (_HASH_A, _HASH_B)), Pin("helper==1.0.0 ; python_full_version < '3.11'", (_HASH_A,))]


_SETTINGS = 'require-build-hashes = true\npreview-features = ["build-dependency-hashes"]\n'


def _root_pyproject(pins=_PINS, *, settings=_SETTINGS, after_block=""):
    return (
        "[project]\nname = 'monorepo'\nversion = '0.0.0'\n\n"
        f"[tool.uv]\n{settings}build-constraint-dependencies = [\n"
        f"    {BEGIN_MARKER}\n{build_constraints.render_block(pins)}    {END_MARKER}\n{after_block}]\n"
    )


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(_root_pyproject(), encoding="utf-8")
    _package(tmp_path, "first", '["backend>=2.0.0"]')
    _package(tmp_path, "second", '["backend==2.1.0"]')
    return tmp_path


def _package(root: Path, name: str, requires: str) -> None:
    package = root / "packages" / "py" / name
    package.mkdir(parents=True, exist_ok=True)
    (package / "pyproject.toml").write_text(
        f"[build-system]\nrequires = {requires}\nbuild-backend = 'backend.api'\n", encoding="utf-8"
    )


def _set_root(root: Path, text: str) -> None:
    (root / "pyproject.toml").write_text(text, encoding="utf-8")


_RUNNER = "benchmarks/web/runner"
_RUNNER_PINS = [Pin("hatchling==1.27.0", (_HASH_A,)), Pin("editables==0.6", (_HASH_B,))]


def _lock_text(pins: list[Pin]) -> str:
    """The `[manifest]` table `uv lock` writes for the project's build constraints."""
    entries = ""
    for pin in pins:
        name, version = pin.requirement.split("==")
        hashes = ", ".join(f'"{digest}"' for digest in pin.hashes)
        entries += f'    {{ name = "{name}", specifier = "=={version}", hashes = [{hashes}] }},\n'
    return f"version = 1\n\n[manifest]\nbuild-constraints = [\n{entries}]\n"


def _standalone(root: Path, pins: list[Pin] = _RUNNER_PINS, *, locked: list[Pin] | None = None) -> Path:
    """Write a standalone project that builds with hatchling, with its own pin table and lock."""
    project = root / _RUNNER
    project.mkdir(parents=True, exist_ok=True)
    (project / "pyproject.toml").write_text(
        "[build-system]\nrequires = ['hatchling==1.27.0']\nbuild-backend = 'hatchling.build'\n\n"
        f"[tool.uv]\n{_SETTINGS}build-constraint-dependencies = [\n"
        f"    {BEGIN_MARKER}\n{build_constraints.render_block(pins)}    {END_MARKER}\n]\n",
        encoding="utf-8",
    )
    (project / "uv.lock").write_text(_lock_text(pins if locked is None else locked), encoding="utf-8")
    return project


def test_matching_pins_pass(root: Path) -> None:
    assert build_pin_errors(root) == []


@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        # Without require-build-hashes, uv installs an unlisted transitive build dependency unchecked.
        ('preview-features = ["build-dependency-hashes"]\n', "require-build-hashes = true"),
        # uv would print the preview warning on every command.
        ("require-build-hashes = true\n", '"build-dependency-hashes"'),
    ],
)
def test_root_settings_are_required(root: Path, settings: str, expected: str) -> None:
    _set_root(root, _root_pyproject(settings=settings))
    errors = build_pin_errors(root)
    assert len(errors) == 1
    assert expected in errors[0]


def test_a_new_backend_without_a_pin_is_reported(root: Path) -> None:
    _package(root, "third", '["other-backend>=1.0.0"]')
    errors = build_pin_errors(root)
    assert len(errors) == 1
    assert "packages/py/third/pyproject.toml" in errors[0]
    # Every pin error tells the reader how to repair it.
    assert "python scripts/build_constraints.py update`, then the `uv lock` commands it prints" in errors[0]


def test_a_requirement_the_pin_no_longer_satisfies_is_reported(root: Path) -> None:
    _package(root, "first", '["backend>=3.0.0"]')
    errors = build_pin_errors(root)
    assert len(errors) == 1
    assert "pins 2.1.0" in errors[0]


@pytest.mark.parametrize(
    "pin",
    [
        # A range lets uv pick a version whose hashes are not listed.
        Pin("backend>=2.0.0", (_HASH_A,)),
        # A pin with no hash cannot be checked.
        Pin("backend==2.1.0", ()),
        # The refresh writes only sha256 hashes, so another algorithm means a hand edit.
        Pin("backend==2.1.0", ("md5:" + "a" * 32,)),
    ],
)
def test_an_unchecked_pin_is_reported(root: Path, pin: Pin) -> None:
    _set_root(root, _root_pyproject([pin]))
    errors = build_pin_errors(root)
    # The broken entry is reported, and because uv cannot use it, the packages also show as unpinned.
    assert any(repr(pin.requirement) in error for error in errors)


def test_an_entry_outside_the_generated_block_is_reported(root: Path) -> None:
    # uv reads this hand-added entry, but the --no-config builders would not export it.
    _set_root(root, _root_pyproject(after_block=f'    {{ requirement = "extra==1.0.0", hashes = ["{_HASH_A}"] }},\n'))
    errors = build_pin_errors(root)
    assert any("outside the generated block" in error for error in errors)


def test_missing_markers_are_reported(root: Path) -> None:
    _set_root(root, _root_pyproject().replace(BEGIN_MARKER, "# hand-written"))
    assert any(BEGIN_MARKER in error for error in build_pin_errors(root))


def test_export_writes_every_pin_with_its_hashes(root: Path, tmp_path: Path) -> None:
    exported = build_constraints.export(tmp_path / "constraints.txt", pyproject=root / "pyproject.toml")
    assert exported.read_text(encoding="utf-8") == (
        f"backend==2.1.0 \\\n    --hash={_HASH_A} \\\n    --hash={_HASH_B}\n"
        f"helper==1.0.0 ; python_full_version < '3.11' \\\n    --hash={_HASH_A}\n"
    )
    # uv build receives the file and refuses any build dependency it does not hash.
    assert build_constraints.constraint_args(exported) == ["--build-constraints", str(exported), "--require-hashes"]


def test_export_refuses_an_empty_block(root: Path, tmp_path: Path) -> None:
    _set_root(root, _root_pyproject([]))
    with pytest.raises(build_constraints.BuildConstraintError):
        build_constraints.export(tmp_path / "constraints.txt", pyproject=root / "pyproject.toml")


def test_compiled_output_becomes_sorted_pins() -> None:
    # The shape `uv pip compile --generate-hashes --no-header --no-annotate` prints.
    output = (
        f"zeta==1.0.0 ; python_full_version < '3.11' \\\n    --hash={_HASH_B} \\\n    --hash={_HASH_A}\n"
        f"alpha==2.0.0 \\\n    --hash={_HASH_A}\n"
    )
    assert build_constraints.parse_compiled(output) == [
        Pin("alpha==2.0.0", (_HASH_A,)),
        Pin("zeta==1.0.0 ; python_full_version < '3.11'", (_HASH_A, _HASH_B)),
    ]


def test_update_rewrites_only_the_generated_block(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before = (root / "pyproject.toml").read_text(encoding="utf-8")
    fresh = [Pin("backend==2.2.0", (_HASH_B,))]
    requested: list[list[str]] = []

    def fake_compile(requirements: list[str], *, uv: str) -> list[Pin]:
        del uv
        requested.append(requirements)
        return fresh

    monkeypatch.setattr(build_constraints, "compile_pins", fake_compile)
    build_constraints.update(root=root)
    # Each distinct package requirement reaches the resolver once, in package order.
    # The third-party sdist backends follow the workspace packages' own.
    assert requested == [["backend>=2.0.0", "backend==2.1.0", *build_constraints.THIRD_PARTY_BUILD_REQUIREMENTS]]
    assert (root / "pyproject.toml").read_text(encoding="utf-8") == before.replace(
        build_constraints.render_block(_PINS), build_constraints.render_block(fresh)
    )


def test_a_backend_pinned_only_under_a_marker_is_reported(root: Path) -> None:
    # Every Python needs a backend a package names, so a pin for Python 3.10 only leaves the rest unchecked.
    _set_root(root, _root_pyproject([Pin("backend==2.1.0 ; python_full_version < '3.11'", (_HASH_A,))]))
    errors = build_pin_errors(root)
    assert len(errors) == 2
    assert all("environment marker" in error for error in errors)


def test_a_standalone_project_with_its_own_pins_and_lock_passes(root: Path) -> None:
    _standalone(root)
    assert build_pin_errors(root) == []


def test_a_standalone_project_gets_no_pins_from_the_root(root: Path) -> None:
    # uv reads pins from the project's own workspace root, so the root's table does not cover it.
    project = _standalone(root)
    (project / "pyproject.toml").write_text(
        "[build-system]\nrequires = ['hatchling==1.27.0']\nbuild-backend = 'hatchling.build'\n", encoding="utf-8"
    )
    errors = build_pin_errors(root)
    assert any(f"{_RUNNER}/pyproject.toml builds with 'hatchling==1.27.0'" in error for error in errors)
    # The unpinned-backend error names `update`, which prints the lock commands for the root and each runner.
    assert any("builds with" in error and "then the `uv lock` commands it prints" in error for error in errors)
    assert any("require-build-hashes = true" in error and f"add the line to {_RUNNER}" in error for error in errors)


def test_the_extra_requirements_of_hatchling_need_a_pin(root: Path) -> None:
    # Hatchling asks for editables only for an editable install, which is how `uv sync` installs the project.
    _standalone(root, [Pin("hatchling==1.27.0", (_HASH_A,))])
    errors = build_pin_errors(root)
    assert len(errors) == 1
    assert "'editables~=0.3'" in errors[0]


def test_a_standalone_lock_that_lags_behind_its_pins_is_reported(root: Path) -> None:
    # `uv sync --frozen` reads the pins from uv.lock, so a stale lock fails the sync even when the table is right.
    _standalone(root, locked=[])
    errors = build_pin_errors(root)
    assert len(errors) == 1
    assert f"{_RUNNER}/uv.lock does not record" in errors[0]
    # Only the lock is stale, so relocking that folder repairs it; refreshing the pins would not be needed.
    assert errors[0].endswith(f"run `uv lock --directory {_RUNNER}`")


def test_a_standalone_lock_with_other_hashes_is_reported(root: Path) -> None:
    _standalone(root, locked=[Pin("hatchling==1.27.0", (_HASH_B,)), Pin("editables==0.6", (_HASH_B,))])
    assert any("does not record" in error for error in build_pin_errors(root))


def test_update_pins_each_standalone_project_from_its_own_requirements(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _standalone(root)
    requested: list[list[str]] = []

    def fake_compile(requirements: list[str], *, uv: str) -> list[Pin]:
        del uv
        requested.append(requirements)
        return [Pin("backend==2.2.0", (_HASH_B,))]

    monkeypatch.setattr(build_constraints, "compile_pins", fake_compile)
    updated = build_constraints.update(root=root)
    # The root block comes from the workspace packages only; the project's own block from its backend and extras.
    assert requested == [
        ["backend>=2.0.0", "backend==2.1.0", *build_constraints.THIRD_PARTY_BUILD_REQUIREMENTS],
        ["hatchling==1.27.0", "editables~=0.3"],
    ]
    assert list(updated) == [root / "pyproject.toml", project / "pyproject.toml"]
    assert build_constraints.render_block(updated[project / "pyproject.toml"]) in (
        project / "pyproject.toml"
    ).read_text(encoding="utf-8")


def test_only_hatchling_gets_extra_build_requirements(tmp_path: Path) -> None:
    for name, requires, expected in [
        ("hatch", '["Hatchling>=1.0"]', ["Hatchling>=1.0", "editables~=0.3"]),
        ("other", '["setuptools>=61"]', ["setuptools>=61"]),
    ]:
        project = tmp_path / name / "pyproject.toml"
        project.parent.mkdir()
        project.write_text(f"[build-system]\nrequires = {requires}\nbuild-backend = 'x'\n", encoding="utf-8")
        assert build_constraints.project_requirements(project) == expected


def test_a_standalone_lock_without_a_manifest_is_reported(root: Path) -> None:
    # A lock written before the pins existed has no [manifest] table at all.
    project = _standalone(root)
    (project / "uv.lock").write_text("version = 1\nrevision = 3\n", encoding="utf-8")
    assert any("does not record" in error for error in build_pin_errors(root))


def test_a_standalone_project_without_a_lock_is_left_to_uv(root: Path) -> None:
    # A missing lock fails `uv sync --frozen` with its own message, so the pin check has nothing to compare.
    project = _standalone(root)
    (project / "uv.lock").unlink()
    assert build_pin_errors(root) == []


def test_the_root_lock_is_not_compared_here(root: Path) -> None:
    # `uv lock --check` covers the root lock; a root lock with no manifest must not be reported by this check.
    (root / "uv.lock").write_text("version = 1\nrevision = 3\n", encoding="utf-8")
    assert build_pin_errors(root) == []
