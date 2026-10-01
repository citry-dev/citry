"""`js_data()` values that read attributes through Kwargs classes get JSON wire types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, EnumMeta, Flag
from typing import TYPE_CHECKING, ClassVar, Generic, Literal, NamedTuple, TypeVar

import pydantic
import pytest
from typing_extensions import NotRequired, TypeAliasType, TypedDict

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._json_wire import WireClass
from citry._wire_classes import KwargsWireClasses, kwargs_wire_classes
from citry.analysis import json_wire_type_from_annotation, json_wire_type_from_expression

if TYPE_CHECKING:
    from decimal import Decimal

T = TypeVar("T")


class Lane(Enum):
    TODO = "todo"
    DONE = "done"


class Shape(Enum):
    BOX = (1, 2)


class Limit(Enum):
    NONE = float("inf")


class Perm(Flag):
    READ = 1
    WRITE = 2


class Owner(NamedTuple):
    name: str


class Meta(TypedDict):
    rank: int
    tag: NotRequired[str]


class Audit(pydantic.BaseModel):
    note: str


@dataclass
class Person:
    email: str


@dataclass
class Box(Generic[T]):
    item: T


class Base:
    id: int


@dataclass
class Task(Base):
    lane: str
    owner: Owner
    person: Person
    state: Lane
    shape: Shape
    limit: Limit
    perm: Perm
    meta: Meta
    audit: Audit
    box: Box[int]
    reviewer: Owner | None = None
    _private: int = 0
    kind: ClassVar[str] = "task"


class Unresolved:
    # `Decimal` is imported only for type checkers, so it cannot be resolved here.
    price: Decimal
    label: str


class Card(Component):
    class Kwargs:
        task: Task
        owner: Owner
        meta: Meta
        unresolved: Unresolved
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
        # Attributes of a dataclass with an inherited plain annotation, a
        # NamedTuple, and a Pydantic model.
        ("kwargs.task.lane", "string"),
        ("kwargs.task.id", "number"),
        ("kwargs.task.owner.name", "string"),
        ("kwargs.task.audit.note", "string"),
        ("kwargs.task.person.email", "string"),
        # The wire sends a NamedTuple as an array and a TypedDict as an object.
        ("kwargs.task.owner", "Array<string>"),
        ("kwargs.owner", "Array<string>"),
        ("kwargs.meta", "{rank: number, tag?: string}"),
        # A TypedDict value is a plain dict, so it has no attributes to read.
        ("kwargs.task.meta.rank", "unknown"),
        # An Enum member carries its value and name.
        ("kwargs.task.state.value", '"todo" | "done"'),
        ("kwargs.task.state.name", '"TODO" | "DONE"'),
        # A tuple or infinite value is not a JSON scalar, and a combined flag
        # is not one of the listed members, so none of them is claimed.
        ("kwargs.task.shape.value", "unknown"),
        ("kwargs.task.limit.value", "unknown"),
        ("kwargs.task.perm.value", "unknown"),
        # A type variable or an unresolved annotation names no concrete type.
        ("kwargs.task.box.item", "unknown"),
        ("kwargs.unresolved.price", "unknown"),
        ("kwargs.unresolved.label", "string"),
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


def test_a_whole_dataclass_instance_is_unsupported_on_the_wire():
    classes = kwargs_wire_classes(Card)
    value = json_wire_type_from_expression(
        "kwargs.task.person",
        member_annotations={"kwargs": classes.members},
        classes=classes.classes,
    )

    assert value.kind == "unknown"
    assert value.unsupported == (f"{_PREFIX}Person cannot be proven to cross Citry's strict JSON wire",)


def test_kwargs_wire_classes_records_reachable_classes_by_import_path():
    classes = kwargs_wire_classes(Card)

    assert classes.members["task"] == f"{_PREFIX}Task"
    assert classes.members["count"] == "int"
    assert classes.classes[f"{_PREFIX}Task"].attributes["reviewer"] == f"{_PREFIX}Owner | None"
    assert "_private" not in classes.classes[f"{_PREFIX}Task"].attributes
    assert classes.classes[f"{_PREFIX}Lane"] == WireClass({}, "enum", None, ("todo", "done"), ("TODO", "DONE"))
    assert classes.classes[f"{_PREFIX}Meta"].required == ("rank",)
    assert classes.classes[f"{_PREFIX}Limit"].enum_values is None
    assert f"{_PREFIX}Perm" not in classes.classes
    # The record survives the copy to the language server unchanged.
    assert KwargsWireClasses.from_dict(classes.to_dict()) == classes


def test_kwargs_wire_classes_is_empty_without_a_kwargs_class():
    class Bare(Component):
        template = """
          <p></p>
        """

    assert kwargs_wire_classes(Bare) == KwargsWireClasses()


class _HostileEnumType(EnumMeta):
    def __iter__(cls):
        raise RuntimeError


class Hostile(Enum, metaclass=_HostileEnumType):
    ONE = 1


class Holder(Component):
    # Module level, so the postponed annotations resolve.
    class Kwargs:
        hostile: Hostile
        lane: Lane

    template = """
      <p></p>
    """


def test_kwargs_wire_classes_leaves_out_a_class_whose_metadata_raises():
    # Listing the hostile Enum's members raises, so only that class is left out.
    classes = kwargs_wire_classes(Holder)
    assert classes.members["hostile"] == f"{_PREFIX}Hostile"
    assert f"{_PREFIX}Lane" in classes.classes
    assert f"{_PREFIX}Hostile" not in classes.classes


@pytest.mark.parametrize(
    "payload",
    [
        {"members": {}},
        {"members": {"task": 1}, "classes": {}},
        {
            "members": {},
            "classes": {
                "x": {"attributes": {}, "kind": "enum", "required": None, "enum_values": [[1]], "enum_names": None}
            },
        },
        {
            "members": {},
            "classes": {
                "x": {"attributes": {}, "kind": "mystery", "required": None, "enum_values": None, "enum_names": None}
            },
        },
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
        return {"lane": kwargs.task.lane, "owner": kwargs.task.owner, "person": kwargs.task.person}

    template = """
      <p></p>
    """


def test_check_reports_a_class_instance_reached_through_kwargs(tmp_path):
    report = check_project(CheckAppSelection(spec="app:engine", engine=_ENGINE), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.js-data.unsupported-type"]

    # `lane` is a string and the NamedTuple `owner` is sent as an array,
    # but the dataclass `person` cannot be proven to cross the wire.
    assert len(findings) == 1
    assert "'person'" in findings[0].message
    assert f"{_PREFIX}Person cannot be proven" in findings[0].message


_SIZE_MEMBERS = {
    # The schema names the alias; the resolved annotation spells out its values.
    "member_types": {"kwargs": {"size": json_wire_type_from_annotation("Size")}},
    "member_annotations": {"kwargs": {"size": 'Literal["sm", "md"]'}},
}


def test_a_type_alias_member_types_from_its_resolved_values():
    value = json_wire_type_from_expression("kwargs.size", **_SIZE_MEMBERS)

    assert value.javascript == '"sm" | "md"'
    assert value.unsupported == ()


def test_widened_literals_keep_the_values_an_annotation_declares():
    value = json_wire_type_from_expression(
        "{'flag': False, 'mode': 'a', 'size': kwargs.size, 'either': 'a' if kwargs else kwargs.size}",
        widen_literals=True,
        **_SIZE_MEMBERS,
    )

    # A constant may change in the browser, so it keeps only its kind; an
    # annotated member keeps the values the server declared.
    assert value.javascript == '{flag: boolean, mode: string, size: "sm" | "md", either: string | "sm" | "md"}'


def test_unknown_parts_are_collected_and_filled_by_their_offsets():
    source = "{'rows': self.rows(), 'count': len(items) + 1, 'tags': {1, 2}, 'plain': 1}"
    unproven: list[tuple[int, int]] = []

    value = json_wire_type_from_expression(source, unproven=unproven)

    # Every unknown part is collected, so a caller can ask about the largest
    # ones. A set has a known reason not to fit, so it is not collected.
    assert [source[start:end] for start, end in unproven] == ["self.rows()", "len(items)", "len(items) + 1"]
    assert value.javascript == "{rows: unknown, count: unknown, tags: unknown, plain: 1}"

    rows = source.index("self.rows()")
    count = source.index("len(items) + 1")
    filled = json_wire_type_from_expression(
        source,
        inferred={
            (rows, rows + len("self.rows()")): json_wire_type_from_annotation("list[str]"),
            (count, count + len("len(items) + 1")): json_wire_type_from_annotation("int"),
        },
    )

    assert filled.javascript == "{rows: Array<string>, count: number, tags: unknown, plain: 1}"
    assert filled.unsupported == ("set literals are not JSON-serializable",)


class Outer:
    @dataclass
    class Inner:
        note: str


class NestedCard(Component):
    citry = Citry(autodiscover=False)
    template = """
      <p></p>
    """

    class Kwargs:
        inner: Outer.Inner
        rows: list[Outer.Inner | None]


def test_kwargs_wire_classes_record_the_module_of_a_nested_class():
    classes = kwargs_wire_classes(NestedCard)

    # The import path alone does not say that `Outer` is a class, not a module.
    assert classes.members["inner"] == f"{_PREFIX}Outer.Inner"
    assert classes.class_modules == {f"{_PREFIX}Outer.Inner": __name__}
    assert KwargsWireClasses.from_dict(classes.to_dict()) == classes


# What `type Tone = Literal["a", "b"]` creates on Python 3.12+.
_Tone = TypeAliasType("_Tone", Literal["a", "b"])


class ToneCard(Component):
    citry = Citry(autodiscover=False)
    template = """
      <p></p>
    """

    class Kwargs:
        tone: _Tone


def test_a_type_statement_alias_member_reads_as_its_value():
    assert kwargs_wire_classes(ToneCard).members == {"tone": 'Literal["a", "b"]'}


def test_a_spread_list_element_is_not_collected_as_a_part():
    unproven: list[tuple[int, int]] = []

    value = json_wire_type_from_expression("[*self.rows(), 'x']", unproven=unproven)

    # `*self.rows()` is no expression on its own, so it cannot be asked about.
    assert unproven == []
    assert value.javascript == "Array<unknown>"


def test_unknown_part_offsets_count_only_real_line_breaks():
    # A form feed or U+2028 inside the value is no line break for Python's
    # parser, so the offsets must not treat it as one.
    source = '["a\\u2028b",\n\x0c self.x()]'
    unproven: list[tuple[int, int]] = []

    json_wire_type_from_expression(source, unproven=unproven)

    assert [source[start:end] for start, end in unproven] == ["self.x()"]
