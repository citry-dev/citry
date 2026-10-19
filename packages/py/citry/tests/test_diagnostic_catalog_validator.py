"""The diagnostic catalog validator finds code literals that the catalog does not own."""

from pathlib import Path

import pytest
from scripts.validators import diagnostic_catalog


@pytest.fixture
def roots(tmp_path, monkeypatch):
    bound = tmp_path / "bound"
    unbound = tmp_path / "unbound"
    bound.mkdir()
    unbound.mkdir()
    # Point the scan at two synthetic source folders: one whose language has a
    # generated binding and one, like the i18n crate, that must spell codes.
    monkeypatch.setattr(diagnostic_catalog, "ROOT", tmp_path)
    monkeypatch.setattr(diagnostic_catalog, "IMPLEMENTATION_ROOTS", (bound, unbound))
    monkeypatch.setattr(diagnostic_catalog, "UNBOUND_ROOTS", (unbound,))
    return bound, unbound


def _problems(bound: Path, unbound: Path, bound_source: str, unbound_source: str) -> list[str]:
    (bound / "emit.py").write_text(bound_source, encoding="utf-8")
    (unbound / "emit.rs").write_text(unbound_source, encoding="utf-8")
    codes = {"citry.i18n.catalog-invalid", "citry.vue.unknown-variable"}
    return diagnostic_catalog._code_literal_problems(codes, ("citry.python.",))


def test_uncataloged_code_in_a_known_family_is_reported_everywhere(roots):
    bound, unbound = roots
    problems = _problems(bound, unbound, 'CODE = "citry.vue.made-up"\n', 'let code = "citry.i18n.made-up";\n')
    assert problems == [
        "bound/emit.py uses uncataloged diagnostic code 'citry.vue.made-up'",
        "unbound/emit.rs uses uncataloged diagnostic code 'citry.i18n.made-up'",
    ]


def test_catalogued_literal_is_allowed_only_where_no_binding_exists(roots):
    bound, unbound = roots
    problems = _problems(
        bound,
        unbound,
        'CODE = "citry.i18n.catalog-invalid"\n',
        'let code = "citry.i18n.catalog-invalid";\n',
    )
    assert problems == [
        "bound/emit.py duplicates catalog code 'citry.i18n.catalog-invalid'; use the generated binding",
    ]


def test_module_paths_and_external_prefixes_are_not_codes(roots):
    bound, unbound = roots
    problems = _problems(
        bound,
        unbound,
        'MODULES = ("citry.contrib.asgi", "citry.python.unresolved-reference")\n',
        "",
    )
    assert problems == []
