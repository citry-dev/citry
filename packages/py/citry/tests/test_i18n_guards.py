"""Formatter calls that run only when i18n is configured are recognized."""

from __future__ import annotations

import ast

import pytest

from citry._i18n_guards import i18n_configured_guarded_calls


def _guarded_call_sources(source: str) -> list[str]:
    tree = ast.parse(source)
    guarded = i18n_configured_guarded_calls(tree)
    return [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Call) and id(node) in guarded]


@pytest.mark.parametrize(
    "source",
    [
        "x = f() if self.i18n.configured else 1",
        "if self.i18n.configured:\n    f()",
        "if value is not None and component.i18n.configured:\n    f()",
        "x = i18n.configured and f()",
        "x = 1 if not self.i18n.configured else f()",
        "def g():\n    if not self.i18n.configured:\n        return 1\n    return f()",
        "def g():\n    if not self.i18n.configured:\n        raise ValueError\n    f()",
    ],
)
def test_guarded_calls_are_recognized(source):
    assert _guarded_call_sources(source) == ["f()"]


@pytest.mark.parametrize(
    "source",
    [
        "f()",
        "x = f() if self.i18n.available else 1",
        "x = 1 if self.i18n.configured else f()",
        "x = f() or self.i18n.configured",
        "if self.i18n.configured or other:\n    f()",
        "if not self.i18n.configured:\n    pass\nf()",
        "enabled = self.i18n.configured\nif enabled:\n    f()",
    ],
)
def test_other_calls_are_not_guarded(source):
    assert _guarded_call_sources(source) == []
