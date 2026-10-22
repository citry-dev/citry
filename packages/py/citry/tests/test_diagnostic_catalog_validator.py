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


def _catalog_with(entry_fields: dict[str, object]) -> dict[str, object]:
    entry = {
        "code": "citry.example.rule",
        "constant": "EXAMPLE_RULE",
        "title": "Example rule",
        "summary": "Something is wrong.",
        "when": "A test writes it.",
        "defaultSeverity": "warning",
        "surfaces": ["check"],
        "parameters": {},
        "messages": {"default": "Something is wrong."},
        "documentationPath": "/ide/diagnostics/#citry.example.rule",
        **entry_fields,
    }
    return {
        "schemaVersion": 1,
        "documentationBaseUrl": "https://citry.dev",
        "externalCodePrefixes": [],
        "diagnostics": [entry],
    }


@pytest.mark.parametrize(
    ("entry_fields", "expected"),
    [
        # A rule that is off by default must be one the application can turn on.
        ({"defaultSeverity": "ignore", "configurableSeverity": True}, []),
        (
            {"defaultSeverity": "ignore"},
            ["diagnostics[0].defaultSeverity may be ignore only when configurableSeverity is true"],
        ),
        (
            {"defaultSeverity": "ignore", "configurableSeverity": False},
            ["diagnostics[0].defaultSeverity may be ignore only when configurableSeverity is true"],
        ),
        ({"defaultSeverity": "off", "configurableSeverity": True}, ["diagnostics[0].defaultSeverity is invalid"]),
    ],
)
def test_an_off_by_default_rule_must_have_a_configurable_severity(entry_fields, expected):
    problems: list[str] = []
    diagnostic_catalog._validate_catalog(_catalog_with(entry_fields), problems)
    assert problems == expected
