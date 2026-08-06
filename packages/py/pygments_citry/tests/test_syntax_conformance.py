"""Run the shared editor syntax corpus through the Pygments lexers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pygments.lexers import get_lexer_by_name
from pygments.token import Comment, Error, Keyword, Name, Text, Token

FIXTURE_PATH = Path(__file__).parents[3] / "editors" / "syntax-fixtures" / "template.json"


def _load_cases() -> list[dict[str, object]]:
    fixture = json.loads(FIXTURE_PATH.read_text())
    assert fixture["schema_version"] == 1
    return fixture["cases"]


def _nth_start(source: str, text: str, occurrence: int) -> int:
    start = -1
    for _ in range(occurrence):
        start = source.find(text, start + 1)
        assert start >= 0, f"{text!r} occurrence {occurrence} is absent from fixture source"
    return start


def _has_role(token: Token, role: str) -> bool:
    if role == "tag":
        return token in Name.Tag
    if role == "attribute":
        return token in Name.Attribute
    if role == "python":
        return token is Name or token in Keyword
    if role == "javascript":
        return token in Name.Other or token in Keyword
    if role == "handler":
        return token in Name.Function
    if role == "css":
        return token in Keyword.Constant
    if role == "comment":
        return token in Comment
    if role == "text":
        return token in Text
    msg = f"unknown portable syntax role: {role!r}"
    raise AssertionError(msg)


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: str(case["name"]))
def test_shared_syntax_case(case: dict[str, object]) -> None:
    source = str(case["source"])
    lexer = get_lexer_by_name(str(case["language"]))
    tokens = list(lexer.get_tokens_unprocessed(source))

    if not case["allow_errors"]:
        errors = [(offset, value) for offset, token, value in tokens if token in Error]
        assert not errors

    assertions = case["assertions"]
    assert isinstance(assertions, list)
    for assertion in assertions:
        assert isinstance(assertion, dict)
        text = str(assertion["text"])
        role = str(assertion["role"])
        occurrence = int(assertion.get("occurrence", 1))
        start = _nth_start(source, text, occurrence)
        end = start + len(text)
        overlapping = [
            (offset, token, value) for offset, token, value in tokens if offset < end and offset + len(value) > start
        ]

        assert overlapping, f"{case['name']}: no token covers {text!r}"
        assert all(_has_role(token, role) for _, token, _ in overlapping), (
            f"{case['name']}: expected {text!r} to have role {role!r}, got {overlapping!r}"
        )
