"""
Static-typing contract of extending a parent component's nested data class.

A subclass extends its parent's ``Kwargs`` (or ``Slots``, ``State``,
``TemplateData``, ``JsData``, ``CssData``) by naming the parent's class as a
base. That spelling must stay clean under both mypy and pyright, and the
fields from both classes must be visible to both checkers, because it is the
form the documentation teaches. The check gate runs both over this file:
scripts/check.py targets it in the mypy phase and in the pinned pyright phase.
To re-check just this file by hand, from the repo root:

    .venv/bin/python -m mypy <this file>
    node_modules/.bin/pyright --pythonversion 3.13 --pythonpath .venv/bin/python <this file>

pytest runs the runtime half, proving that what the checkers see matches the
class Citry builds.
"""

from __future__ import annotations

import warnings
from dataclasses import fields
from typing import Any

from typing_extensions import assert_type

from citry import Citry, Component, NestedSchemaReplacedWarning

app = Citry()


class Message(Component):
    citry = app

    class Kwargs:
        text: str
        author: str = ""

    class State:
        draft: str = ""
        _public = ("draft",)


class SignedMessage(Message):
    class Kwargs(Message.Kwargs):
        signature: str = ""

    class State(Message.State):
        signed: bool = False


class InheritedMessage(Message):
    pass


def _assert_extended_field_types(kwargs: SignedMessage.Kwargs, state: SignedMessage.State) -> None:
    # Fields from the parent's class and the subclass's own fields are both
    # typed through ordinary class inheritance.
    assert_type(kwargs.text, str)
    assert_type(kwargs.author, str)
    assert_type(kwargs.signature, str)
    assert_type(state.draft, str)
    assert_type(state.signed, bool)


def _assert_inherited_class_is_the_parent_class(kwargs: InheritedMessage.Kwargs) -> None:
    # A subclass that declares nothing uses the parent's class.
    assert_type(kwargs, Message.Kwargs)


def test_runtime_matches_the_static_view() -> None:
    assert issubclass(SignedMessage.Kwargs, Message.Kwargs)
    # Checkers see the authored plain class; at runtime Citry has made it a
    # dataclass, so read its generated fields and constructor through Any.
    signed: Any = SignedMessage.Kwargs
    assert [field.name for field in fields(signed)] == ["text", "author", "signature"]
    assert signed(text="hi") == signed(text="hi", author="", signature="")
    state: Any = SignedMessage.State
    assert [field.name for field in fields(state)] == ["draft", "signed"]
    assert InheritedMessage.Kwargs is Message.Kwargs


def test_extension_does_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", NestedSchemaReplacedWarning)

        class CountedMessage(Message):
            class Kwargs(Message.Kwargs):
                count: int = 0

    counted: Any = CountedMessage.Kwargs
    assert [field.name for field in fields(counted)] == ["text", "author", "count"]
