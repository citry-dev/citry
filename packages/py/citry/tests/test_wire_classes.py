"""`js_data()` values that read attributes through Kwargs classes get JSON wire types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, NamedTuple, TypedDict

import pydantic
import pytest

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._json_wire import WireClass
from citry._wire_classes import KwargsWireClasses, kwargs_wire_classes
from citry.analysis import json_wire_type_from_expression


class Lane(Enum):
    TODO = "todo"
    DONE = "done"


class Shape(Enum):
    BOX = (1, 2)


class Owner(NamedTuple):
    name: str


class Meta(TypedDict):
    rank: int


class Audit(pydantic.BaseModel):
    note: str


class Base:
    id: int


@dataclass
class Task(Base):
    lane: str
    owner: Owner
    state: Lane
    shape: Shape
    meta: Meta
    audit: Audit
    reviewer: Owner | None = None
    _private: int = 0
    kind: ClassVar[str] = "task"


class Card(Component):
    class Kwargs:
        task: Task
        count: int = 0

    template = """
      <p></p>
    """


_PREFIX = f"{__name__}."


def _type(expression: str) -> str:
    classes = kwargs_wire_classes(Card)
    return json_wire_type_from_expression(
        expression,
        member_types={"kwargs": {}},
        member_annotations={"kwargs": classes.members},
        classes=classes.classes,
    ).javascript


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        # Each supported kind of class: dataclass with an inherited plain
        # annotation, NamedTuple, TypedDict, and a Pydantic model.
        ("kwargs.task.lane", "string"),
        ("kwargs.task.id", "number"),
        ("kwargs.task.owner.name", "string"),
        ("kwargs.task.meta.rank", "number"),
        ("kwargs.task.audit.note", "string"),
        # An Enum member carries its value and name.
        ("kwargs.task.state.value", '"todo" | "done"'),
        ("kwargs.task.state.name", '"TODO" | "DONE"'),
        # A tuple value is not a JSON scalar, so it is not claimed.
        ("kwargs.task.shape.value", "unknown"),
        # An optional value may be None, and private or unknown names prove nothing.
        ("kwargs.task.reviewer.name", "unknown"),
        ("kwargs.task._private", "unknown"),
        ("kwargs.task.missing", "unknown"),
        ("kwargs.task.kind", "unknown"),
        ("kwargs.count.real", "unknown"),
    ],
)
def test_attribute_chains_follow_class_annotations(expression, expected):
    assert _type(expression) == expected


def test_a_whole_class_instance_is_unsupported_on_the_wire():
    classes = kwargs_wire_classes(Card)
    value = json_wire_type_from_expression(
        "kwargs.task.owner",
        member_annotations={"kwargs": classes.members},
        classes=classes.classes,
    )

    assert value.kind == "unknown"
    assert value.unsupported == (f"{_PREFIX}Owner cannot be proven to cross Citry's strict JSON wire",)


def test_kwargs_wire_classes_records_reachable_classes_by_import_path():
    classes = kwargs_wire_classes(Card)

    assert classes.members == {"task": f"{_PREFIX}Task", "count": "int"}
    assert classes.classes[f"{_PREFIX}Task"].attributes["reviewer"] == f"{_PREFIX}Owner | None"
    assert "_private" not in classes.classes[f"{_PREFIX}Task"].attributes
    assert classes.classes[f"{_PREFIX}Lane"] == WireClass({}, ("todo", "done"), ("TODO", "DONE"))
    assert classes.classes[f"{_PREFIX}Shape"].enum_values is None
    # The record survives the copy to the language server unchanged.
    assert KwargsWireClasses.from_dict(classes.to_dict()) == classes


def test_kwargs_wire_classes_is_empty_without_a_kwargs_class():
    class Bare(Component):
        template = """
          <p></p>
        """

    assert kwargs_wire_classes(Bare) == KwargsWireClasses()


@pytest.mark.parametrize(
    "payload",
    [
        {"members": {}},
        {"members": {"task": 1}, "classes": {}},
        {"members": {}, "classes": {"x": {"attributes": {}, "enum_values": [[1]], "enum_names": None}}},
    ],
)
def test_kwargs_wire_classes_rejects_a_malformed_copy(payload):
    with pytest.raises(ValueError, match="wire class"):
        KwargsWireClasses.from_dict(payload)


# `citry check` reads an inferred js_data() from its source file, which needs
# a class defined at module level.
_ENGINE = Citry(autodiscover=False)


class Board(Component):
    citry = _ENGINE

    class Kwargs:
        task: Task

    def js_data(self, kwargs, slots):
        return {"lane": kwargs.task.lane, "owner": kwargs.task.owner}

    template = """
      <p></p>
    """


def test_check_reports_a_class_instance_reached_through_kwargs(tmp_path):
    report = check_project(CheckAppSelection(spec="app:engine", engine=_ENGINE), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.js-data.unsupported-type"]

    # `lane` is a string; `owner` is a NamedTuple instance the wire rejects.
    assert len(findings) == 1
    assert "'owner'" in findings[0].message
    assert f"{_PREFIX}Owner cannot be proven" in findings[0].message
