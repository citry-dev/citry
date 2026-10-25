"""The build-backend pins stay hashed, readable as text, and in step with each package's build requirements."""

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
    assert "python scripts/build_constraints.py update && uv lock" in errors[0]


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
    build_constraints.update(pyproject=root / "pyproject.toml", packages_dir=root / "packages" / "py")
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
