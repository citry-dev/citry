"""The generated-copies validator reports a copy or a recorded Vue version that drifted from its source."""

from pathlib import Path

from scripts.validators import generated_copies

_HEADER = '"""\nGenerated; do not edit.\n- @vue/runtime-dom {version} types, path/to/runtime-dom.d.ts\n"""\n'


def _repository(tmp_path: Path, *, module_vue: str = "3.5.44", vendored_vue: str = "3.5.44") -> Path:
    # Lay out every file the validator reads, all matching, so each test
    # changes exactly one of them.
    for copy, original in generated_copies.EXACT_COPIES:
        for relative in (copy, original):
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"<svg/>")
    module = tmp_path / generated_copies.HTML_ATTRIBUTE_VALUES
    module.parent.mkdir(parents=True, exist_ok=True)
    module.write_text(_HEADER.format(version=module_vue), encoding="utf-8")
    inventory = tmp_path / generated_copies.VUE_TYPES_INVENTORY
    inventory.parent.mkdir(parents=True, exist_ok=True)
    inventory.write_text(f'{{"vue": "{vendored_vue}"}}', encoding="utf-8")
    return tmp_path


def test_matching_copies_and_versions_pass(tmp_path: Path) -> None:
    assert generated_copies.check(_repository(tmp_path)) == []


def test_a_copy_with_different_bytes_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    copy, original = generated_copies.EXACT_COPIES[0]
    (root / original).write_bytes(b"<svg>new</svg>")

    assert generated_copies.check(root) == [f"{copy} differs from {original}; copy {original} over it"]


def test_a_missing_copy_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    copy, _original = generated_copies.EXACT_COPIES[1]
    (root / copy).unlink()

    assert generated_copies.check(root) == [f"{copy} is missing"]


def test_a_vue_bump_without_regenerating_the_attribute_module_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path, module_vue="3.5.44", vendored_vue="3.5.45")

    [problem] = generated_copies.check(root)
    assert "@vue/runtime-dom 3.5.44" in problem
    assert "Vue 3.5.45" in problem


def test_a_module_header_without_the_vue_line_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / generated_copies.HTML_ATTRIBUTE_VALUES).write_text('"""Generated."""\n', encoding="utf-8")

    [problem] = generated_copies.check(root)
    assert "does not name the @vue/runtime-dom version" in problem


def test_a_missing_vue_types_inventory_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / generated_copies.VUE_TYPES_INVENTORY).unlink()

    assert generated_copies.check(root) == [f"{generated_copies.VUE_TYPES_INVENTORY} is missing"]
