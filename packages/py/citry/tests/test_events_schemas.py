"""
Tests for the events extension's data schemas: schema-class conversion,
validation of the wire args payload with its deliberately small coercion
table, the source-aware string binding of StringArgs payloads, structured
per-field errors, Pydantic wholesale delegation, and the neutral
UploadedFile type (docs/design/events.md sections 3.3 and 6.2).
"""

import gc
import io
import json
import subprocess
import sys
import textwrap
import tracemalloc
import typing
import weakref
from collections.abc import Mapping
from dataclasses import dataclass, is_dataclass, make_dataclass
from dataclasses import field as dataclass_field
from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Any, Literal, Protocol, TypedDict, TypeVar
from uuid import UUID

import pytest
import typing_extensions

from citry.ext.events import _pydantic_bounded as bounded
from citry.ext.events import schemas as schemas_module
from citry.ext.events.errors import FieldErrors, PydanticTotal
from citry.ext.events.files import UploadedFile
from citry.ext.events.schemas import (
    PATHS_TOO_LONG_MESSAGE,
    StringArgs,
    ValidationResult,
    convert_schema_class,
    declared_field_names,
    pydantic_can_report,
    validate_args,
)

try:
    import pydantic
except ImportError:
    pydantic = None  # type: ignore[assignment]

requires_pydantic = pytest.mark.skipif(pydantic is None, reason="pydantic is not installed")

# Literal copies of the validation messages, locked independently of the
# module's constants so a wording change shows up as a deliberate test update.
REQUIRED_MESSAGE = "This field is required."
EXTRA_MESSAGE = "Unexpected field: not declared on the schema."
FILE_MESSAGE = "Expected an uploaded file: file fields arrive as multipart form data, not as JSON values."


# Schema classes used across the tests, module-level as the documented style.
class Plain:
    count: int
    name: str = ""


@dataclass
class Decorated:
    count: int


@dataclass(frozen=True)
class Frozen:
    count: int


class TwoRequired:
    alpha: int
    zeta: int


class Numbers:
    count: int
    ratio: float


class Flags:
    on: bool
    label: str


class Ident:
    uid: UUID


class Timestamps:
    at: datetime


class Day:
    day: date


class Tick:
    tick: time


class Money:
    amount: Decimal


class Color(Enum):
    RED = "red"
    BLUE = "blue"


class Priority(IntEnum):
    LOW = 1
    HIGH = 2


class Palette:
    color: Color


class PriorityIn:
    priority: Priority


class PairIn:
    pair: tuple[int, str]


class NumsIn:
    nums: tuple[int, ...]


class TagsSet:
    tags: set[int]


class TagsList:
    tags: list[int]


class ObjectsSet:
    tags: set[object]


class BareList:
    items: list


class BareTuple:
    combo: tuple


class BareSet:
    tags: set


class BareDict:
    blob: dict


class TypedDictField:
    blob: dict[str, int]


class TypedMappingField:
    blob: Mapping[str, int]


class IntKeyedDict:
    blob: dict[int, str]


class AnyValuedDict:
    blob: dict[str, Any]


class Point(TypedDict):
    x: int


class Reader(Protocol):
    # Not @runtime_checkable, so isinstance() refuses it.
    def read(self) -> str: ...


class PointList:
    points: list[Point]


class PointMap:
    by_name: dict[str, Point]


class PointField:
    origin: Point


class ReaderField:
    reader: Reader


class ReaderList:
    readers: list[Reader]


class Named(Protocol):
    # Not @runtime_checkable, and it annotates an attribute, which makes
    # the class look like an ordinary annotated schema class.
    name: str


class NamedField:
    named: Named


class NamedList:
    named: list[Named]


class ExtensionPoint(typing_extensions.TypedDict):
    x: int


class ExtensionPointField:
    origin: ExtensionPoint


class ExtensionPointList:
    points: list[ExtensionPoint]


class TypingListField:
    items: typing.List  # noqa: UP006


class TypingTupleField:
    combo: typing.Tuple  # noqa: UP006


class Box:
    size: int


class BoxUnion:
    v: dict[int, Box] | list[Box]


class DictOfLists:
    blob: dict[str, list[int]]


class TypedDictAndInt:
    scores: dict[str, int]
    name: int


class Address:
    city: str
    zip_code: str = ""


class AddressIn:
    address: Address


class Line:
    sku: str
    qty: int


class Order:
    lines: list[Line]


class MaybeInt:
    v: int | None = None


class IntOrStr:
    v: int | str


class ListOrInt:
    v: list[int] | int


class SetOrInt:
    v: set | int


class MaybeSet:
    v: set | None


class WithFile:
    avatar: UploadedFile


class WithFiles:
    attachments: list[UploadedFile]


# Thirty required fields, to show that missing-field messages are never limited.
Wide = type("Wide", (), {"__annotations__": {f"f{index:02d}": int for index in range(30)}})


def _unknown_keys(count):
    """
    ``count`` payload keys no schema declares.

    Built in reverse so the keys a test sees listed come from the sorted
    order, not from the order the payload happened to send them in.
    """
    return {f"u{index:03d}": 1 for index in reversed(range(count))}


def _sorted_unknown(count, prefix=""):
    """The names ``_unknown_keys(count)`` gets, in the order the errors list them."""
    return [f"{prefix}u{index:03d}" for index in range(count)]


class Pager:
    page: int


class PagedIn:
    pager: Pager


class NullOnly:
    value: None


class Weight(Enum):
    LIGHT = 1
    HEAVY = 2


class EnumLiteral:
    weight: Literal[Weight.HEAVY]


class LiteralChoices:
    level: Literal["low", "high"]
    size: Literal[1, 2] = 1
    forced: Literal[True] | None = None
    color: Literal[Color.RED] | None = None


class UnsupportedContainer:
    value: frozenset[int]


UnsupportedType = TypeVar("UnsupportedType")


class UnsupportedTypeVariable:
    value: UnsupportedType


class TestConvertSchemaClass:
    def test_plain_class_converts_to_a_dataclass(self):
        converted = convert_schema_class(Plain)
        assert converted is not Plain
        assert is_dataclass(converted)
        assert converted.__name__ == "Plain"

    def test_original_class_stays_untouched(self):
        convert_schema_class(Plain)
        assert not is_dataclass(Plain)

    def test_conversion_is_computed_once_per_class(self):
        assert convert_schema_class(Plain) is convert_schema_class(Plain)

    def test_dataclass_passes_through(self):
        assert convert_schema_class(Decorated) is Decorated

    def test_frozen_dataclass_passes_through(self):
        # Schemas are inputs, nothing mutates them, so frozen is fine here.
        assert convert_schema_class(Frozen) is Frozen

    @requires_pydantic
    def test_pydantic_model_passes_through(self):
        class PModel(pydantic.BaseModel):
            x: int

        assert convert_schema_class(PModel) is PModel


class TestValidatePayloadShape:
    def test_valid_payload_builds_the_converted_instance(self):
        result = validate_args(Plain, {"count": 3})
        assert isinstance(result, ValidationResult)
        assert result.ok
        assert result.fields == {}
        converted = convert_schema_class(Plain)
        assert isinstance(result.value, converted)
        # Omitted defaulted fields fill from their defaults.
        assert result.value == converted(count=3, name="")

    def test_non_mapping_payload_is_a_root_error(self):
        # A JSON-decoded body is not guaranteed to be an object.
        payload: Any = [1, 2]
        result = validate_args(Plain, payload)
        assert result.value is None
        assert result.fields == {"": "Expected an object, got list."}

    def test_null_payload_is_a_root_error(self):
        payload: Any = None
        result = validate_args(Plain, payload)
        assert result.fields == {"": "Expected an object, got null."}

    def test_missing_required_field(self):
        result = validate_args(Plain, {})
        assert result.value is None
        assert result.fields == {"count": REQUIRED_MESSAGE}

    def test_extra_key(self):
        result = validate_args(Plain, {"count": 1, "mango": 2})
        assert result.value is None
        assert result.fields == {"mango": EXTRA_MESSAGE}

    def test_errors_are_sorted_by_field_path(self):
        # Extras arrive before the missing-required checks; sorting must not
        # depend on that insertion order.
        result = validate_args(TwoRequired, {"beta": 1, "mango": 2})
        assert list(result.fields) == ["alpha", "beta", "mango", "zeta"]
        assert result.fields == {
            "alpha": REQUIRED_MESSAGE,
            "beta": EXTRA_MESSAGE,
            "mango": EXTRA_MESSAGE,
            "zeta": REQUIRED_MESSAGE,
        }


class TestIntFloatCoercion:
    def test_int_accepts_int(self):
        result = validate_args(Numbers, {"count": 3, "ratio": 1.0})
        assert result.ok
        assert result.value.count == 3

    def test_int_accepts_whole_float(self):
        result = validate_args(Numbers, {"count": 3.0, "ratio": 1.0})
        assert result.ok
        assert result.value.count == 3
        assert type(result.value.count) is int

    def test_int_rejects_fractional_float(self):
        result = validate_args(Numbers, {"count": 3.5, "ratio": 1.0})
        assert result.fields == {"count": "Expected int, got a float with a fractional part."}

    def test_int_rejects_bool(self):
        result = validate_args(Numbers, {"count": True, "ratio": 1.0})
        assert result.fields == {"count": "Expected int, got bool."}

    def test_int_rejects_numeric_string(self):
        # String-to-number parsing is deliberately not in the coercion table.
        result = validate_args(Numbers, {"count": "5", "ratio": 1.0})
        assert result.fields == {"count": "Expected int, got str."}

    def test_float_accepts_float(self):
        result = validate_args(Numbers, {"count": 1, "ratio": 2.5})
        assert result.ok
        assert result.value.ratio == 2.5

    def test_float_accepts_int(self):
        result = validate_args(Numbers, {"count": 1, "ratio": 2})
        assert result.ok
        assert result.value.ratio == 2.0
        assert type(result.value.ratio) is float

    def test_float_rejects_bool(self):
        result = validate_args(Numbers, {"count": 1, "ratio": True})
        assert result.fields == {"ratio": "Expected float, got bool."}

    def test_float_rejects_string(self):
        result = validate_args(Numbers, {"count": 1, "ratio": "x"})
        assert result.fields == {"ratio": "Expected float, got str."}

    def test_float_rejects_int_beyond_float_range(self):
        # JSON ints are unbounded; the overflow is a per-field error, not an
        # exception out of validate_args.
        result = validate_args(Numbers, {"count": 1, "ratio": 10**400})
        assert result.fields == {"ratio": "Expected float, got an int too large for a float."}

    @pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
    def test_float_rejects_non_finite_values(self, value):
        # Unreachable from the JSON codecs (they reject the spellings and
        # the 1e400 overflow at parse); this guards a payload a user codec
        # built directly, so inf / nan never reach a handler.
        result = validate_args(Numbers, {"count": 1, "ratio": value})
        assert result.fields == {"ratio": f"Expected a finite float, got {value!r}."}

    def test_bool_accepts_bool(self):
        result = validate_args(Flags, {"on": True, "label": "s"})
        assert result.ok
        assert result.value.on is True

    def test_bool_rejects_int(self):
        result = validate_args(Flags, {"on": 1, "label": "s"})
        assert result.fields == {"on": "Expected bool, got int."}

    def test_str_rejects_int(self):
        result = validate_args(Flags, {"on": True, "label": 5})
        assert result.fields == {"label": "Expected str, got int."}


class TestSourceAwareStringBinding:
    """
    The source-aware binding rule of design 3.3: an args payload the form or
    query codec built as StringArgs additionally binds strings to declared
    ``int`` / ``float`` / ``bool`` fields (those transports carry every
    value as a string). A plain mapping keeps the strict JSON behavior. The
    number grammar is Python's own ``int()`` / ``float()`` (signs,
    surrounding whitespace, digit-grouping underscores, exponents), minus
    the non-finite float spellings, and the bool vocabulary is exactly the
    HTML form one.
    """

    @pytest.mark.parametrize(
        ("spelling", "expected"),
        [("true", True), ("false", False), ("1", True), ("0", False), ("on", True)],
    )
    def test_bool_binds_each_accepted_spelling(self, spelling, expected):
        result = validate_args(Flags, StringArgs({"on": spelling, "label": "x"}))
        assert result.ok
        assert result.value.on is expected

    @pytest.mark.parametrize("spelling", ["off", "True", "FALSE", "ON", "yes", ""])
    def test_bool_rejects_anything_outside_the_vocabulary(self, spelling):
        # "off" is never what an unchecked checkbox submits (it submits
        # nothing), and casing variants are not in the vocabulary.
        result = validate_args(Flags, StringArgs({"on": spelling, "label": "x"}))
        assert result.fields == {"on": f"Not a valid bool: {spelling!r}; accepted spellings: true, false, 1, 0, on."}

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("5", 5), (" 5 ", 5), ("1_000", 1000), ("+7", 7), ("-3", -3)],
    )
    def test_int_binds_pythons_own_grammar(self, value, expected):
        # Python's int() latitude (whitespace, underscores, signs) is the
        # contract: the lenient shapes a typed-into-an-input value takes.
        result = validate_args(Numbers, StringArgs({"count": value, "ratio": "1.0"}))
        assert result.ok
        assert result.value.count == expected
        assert type(result.value.count) is int

    @pytest.mark.parametrize("value", ["", "5.5", "1e3", "abc"])
    def test_int_rejects_what_the_grammar_cannot_read(self, value):
        result = validate_args(Numbers, StringArgs({"count": value, "ratio": "1.0"}))
        assert result.fields == {"count": f"Not a valid int: {value!r}."}

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("2.5", 2.5), (" 2.5 ", 2.5), ("1e3", 1000.0), ("1_000.5", 1000.5), ("-0.5", -0.5)],
    )
    def test_float_binds_pythons_own_grammar(self, value, expected):
        result = validate_args(Numbers, StringArgs({"count": "1", "ratio": value}))
        assert result.ok
        assert result.value.ratio == expected
        assert type(result.value.ratio) is float

    @pytest.mark.parametrize("value", ["", "abc"])
    def test_float_rejects_what_the_grammar_cannot_read(self, value):
        result = validate_args(Numbers, StringArgs({"count": "1", "ratio": value}))
        assert result.fields == {"ratio": f"Not a valid float: {value!r}."}

    @pytest.mark.parametrize("value", ["inf", "nan", "-inf", "+inf", "Infinity", "NAN"])
    def test_float_rejects_the_non_finite_spellings(self, value):
        # float() would parse these, but they would bind a value the JSON
        # result envelope cannot carry (and one strict JSON binding could
        # never produce), so they answer the same per-field error.
        result = validate_args(Numbers, StringArgs({"count": "1", "ratio": value}))
        assert result.fields == {"ratio": f"Not a valid float: {value!r}."}

    def test_repeated_fields_bind_through_list_annotations(self):
        # A repeated form field arrives as a list of strings; the binding
        # threads into container elements.
        result = validate_args(TagsList, StringArgs({"tags": ["1", "2", "3"]}))
        assert result.ok
        assert result.value.tags == [1, 2, 3]

    def test_repeated_field_failure_names_the_index(self):
        result = validate_args(TagsList, StringArgs({"tags": ["1", "x"]}))
        assert result.fields == {"tags.1": "Not a valid int: 'x'."}

    def test_binding_threads_into_nested_schemas(self):
        # The marking is read off the top-level payload once and threads
        # through the whole subtree, nested schema objects included.
        result = validate_args(PagedIn, StringArgs({"pager": {"page": "3"}}))
        assert result.ok
        assert result.value.pager.page == 3

    def test_binding_threads_through_unions(self):
        # With binding on, the int member of int | str fits a numeric
        # string first (union members are tried in order).
        assert validate_args(IntOrStr, StringArgs({"v": "5"})).value.v == 5
        assert validate_args(IntOrStr, StringArgs({"v": "x"})).value.v == "x"
        # Optional fields bind their member type the same way.
        assert validate_args(MaybeInt, StringArgs({"v": "7"})).value.v == 7

    def test_plain_mapping_keeps_the_strict_json_behavior(self):
        # The same payload, marked vs plain: the marking is the whole
        # difference, so nothing a JSON body carries can turn binding on.
        payload = {"count": "5", "ratio": "2.5"}
        assert validate_args(Numbers, StringArgs(payload)).ok
        result = validate_args(Numbers, dict(payload))
        assert result.fields == {
            "count": "Expected int, got str.",
            "ratio": "Expected float, got str.",
        }

    def test_bind_strings_true_overrides_a_plain_mapping(self):
        # A custom codec for another string transport can opt in explicitly.
        result = validate_args(Numbers, {"count": "5", "ratio": "2.5"}, bind_strings=True)
        assert result.ok
        assert (result.value.count, result.value.ratio) == (5, 2.5)

    def test_bind_strings_false_overrides_string_args(self):
        result = validate_args(Numbers, StringArgs({"count": "5", "ratio": "2.5"}), bind_strings=False)
        assert result.fields == {
            "count": "Expected int, got str.",
            "ratio": "Expected float, got str.",
        }

    def test_nested_plain_payload_stays_strict(self):
        # The strict contrast for the nested case: without the marking the
        # nested string is the usual per-field mismatch.
        result = validate_args(PagedIn, {"pager": {"page": "3"}})
        assert result.fields == {"pager.page": "Expected int, got str."}


class TestStringCoercions:
    def test_uuid_from_string(self):
        result = validate_args(Ident, {"uid": "12345678-1234-5678-1234-567812345678"})
        assert result.ok
        assert result.value.uid == UUID("12345678-1234-5678-1234-567812345678")

    def test_uuid_rejects_malformed_string(self):
        result = validate_args(Ident, {"uid": "nope"})
        assert result.fields == {"uid": "Not a valid UUID: 'nope'."}

    def test_uuid_rejects_non_string(self):
        result = validate_args(Ident, {"uid": 7})
        assert result.fields == {"uid": "Expected UUID, got int."}

    def test_uuid_instance_passes_through(self):
        uid = UUID("12345678-1234-5678-1234-567812345678")
        result = validate_args(Ident, {"uid": uid})
        assert result.ok
        assert result.value.uid is uid

    def test_datetime_from_iso_string(self):
        result = validate_args(Timestamps, {"at": "2024-05-01T12:30:00+00:00"})
        assert result.ok
        assert type(result.value.at) is datetime
        assert result.value.at == datetime(2024, 5, 1, 12, 30, tzinfo=timezone.utc)

    def test_datetime_rejects_malformed_string(self):
        result = validate_args(Timestamps, {"at": "not-a-date"})
        assert result.fields == {"at": "Not a valid datetime: 'not-a-date'."}

    def test_datetime_rejects_non_string(self):
        result = validate_args(Timestamps, {"at": 7})
        assert result.fields == {"at": "Expected datetime, got int."}

    def test_date_from_iso_string(self):
        result = validate_args(Day, {"day": "2024-05-01"})
        assert result.ok
        assert type(result.value.day) is date
        assert result.value.day == date(2024, 5, 1)

    def test_date_rejects_malformed_string(self):
        result = validate_args(Day, {"day": "2024-13-01"})
        assert result.fields == {"day": "Not a valid date: '2024-13-01'."}

    def test_time_from_iso_string(self):
        result = validate_args(Tick, {"tick": "12:30:15"})
        assert result.ok
        assert type(result.value.tick) is time
        assert result.value.tick == time(12, 30, 15)

    def test_time_rejects_malformed_string(self):
        result = validate_args(Tick, {"tick": "99:99"})
        assert result.fields == {"tick": "Not a valid time: '99:99'."}

    def test_datetime_date_and_time_instances_pass_through(self):
        class TemporalValues:
            at: datetime
            day: date
            tick: time

        at = datetime(2024, 5, 1, 12, 30, tzinfo=timezone.utc)
        day = date(2024, 5, 1)
        tick = time(12, 30)
        result = validate_args(TemporalValues, {"at": at, "day": day, "tick": tick})

        assert result.ok
        assert result.value.at is at
        assert result.value.day is day
        assert result.value.tick is tick

    def test_decimal_from_string(self):
        result = validate_args(Money, {"amount": "1.50"})
        assert result.ok
        assert type(result.value.amount) is Decimal
        assert result.value.amount == Decimal("1.50")

    def test_finite_decimal_instance_passes_through(self):
        amount = Decimal("1.50")
        result = validate_args(Money, {"amount": amount})
        assert result.ok
        assert result.value.amount is amount

    def test_decimal_rejects_malformed_string(self):
        result = validate_args(Money, {"amount": "abc"})
        assert result.fields == {"amount": "Not a valid Decimal: 'abc'."}

    @pytest.mark.parametrize("spelling", ["Infinity", "-Infinity", "inf", "NaN", "snan"])
    def test_decimal_rejects_the_non_finite_spellings(self, spelling):
        # Decimal's own grammar reads these, but they would bind a value
        # the JSON result envelope cannot carry.
        result = validate_args(Money, {"amount": spelling})
        assert result.fields == {"amount": f"Not a valid Decimal: {spelling!r}."}

    @pytest.mark.parametrize("amount", [Decimal("Infinity"), Decimal("-Infinity"), Decimal("NaN")])
    def test_decimal_rejects_non_finite_instances(self, amount):
        result = validate_args(Money, {"amount": amount})
        assert result.fields == {"amount": f"Not a valid Decimal: {amount!r}."}

    def test_decimal_rejects_json_float(self):
        # A JSON float already lost the precision Decimal exists to keep.
        result = validate_args(Money, {"amount": 1.5})
        assert result.fields == {"amount": "Expected Decimal, got float."}

    def test_enum_from_value_string(self):
        result = validate_args(Palette, {"color": "red"})
        assert result.ok
        assert result.value.color is Color.RED

    def test_enum_rejects_unknown_value(self):
        result = validate_args(Palette, {"color": "green"})
        assert result.fields == {"color": "Not a valid Color: 'green'."}

    def test_enum_rejects_non_string(self):
        result = validate_args(Palette, {"color": 3})
        assert result.fields == {"color": "Expected Color, got int."}

    def test_int_enum_rejects_raw_int(self):
        # Enum coercion is from strings by value; a raw int is not coerced
        # even when the enum's values are ints.
        result = validate_args(PriorityIn, {"priority": 1})
        assert result.fields == {"priority": "Expected Priority, got int."}

    def test_enum_instance_passes_through(self):
        result = validate_args(Palette, {"color": Color.BLUE})
        assert result.ok
        assert result.value.color is Color.BLUE


class TestContainerCoercion:
    def test_fixed_tuple_from_list(self):
        result = validate_args(PairIn, {"pair": [1, "a"]})
        assert result.ok
        assert type(result.value.pair) is tuple
        assert result.value.pair == (1, "a")

    def test_fixed_tuple_rejects_wrong_length(self):
        result = validate_args(PairIn, {"pair": [1, "a", 2]})
        assert result.fields == {"pair": "Expected a list of 2 items, got 3."}

    def test_fixed_tuple_rejects_non_list(self):
        result = validate_args(PairIn, {"pair": "x"})
        assert result.fields == {"pair": "Expected a list, got str."}

    def test_variadic_tuple_from_list(self):
        result = validate_args(NumsIn, {"nums": [1, 2.0, 3]})
        assert result.ok
        assert result.value.nums == (1, 2, 3)
        assert [type(n) for n in result.value.nums] == [int, int, int]

    def test_variadic_tuple_element_failure_names_the_index(self):
        result = validate_args(NumsIn, {"nums": [1, "x"]})
        assert result.fields == {"nums.1": "Expected int, got str."}

    def test_set_from_list_collapses_duplicates(self):
        result = validate_args(TagsSet, {"tags": [1, 2, 2]})
        assert result.ok
        assert type(result.value.tags) is set
        assert result.value.tags == {1, 2}

    def test_set_element_failure_names_the_index(self):
        result = validate_args(TagsSet, {"tags": ["x"]})
        assert result.fields == {"tags.0": "Expected int, got str."}

    def test_list_elements_coerce(self):
        result = validate_args(TagsList, {"tags": [1, 2.0]})
        assert result.ok
        assert result.value.tags == [1, 2]
        assert [type(n) for n in result.value.tags] == [int, int]

    def test_list_element_failure_names_the_index(self):
        result = validate_args(TagsList, {"tags": [1, "x", 3]})
        assert result.fields == {"tags.1": "Expected int, got str."}

    def test_bare_list_accepts_any_elements(self):
        result = validate_args(BareList, {"items": [1, {"a": 1}]})
        assert result.ok
        assert result.value.items == [1, {"a": 1}]

    def test_bare_list_rejects_non_list(self):
        result = validate_args(BareList, {"items": 5})
        assert result.fields == {"items": "Expected a list, got int."}

    def test_bare_tuple_from_list(self):
        result = validate_args(BareTuple, {"combo": [1, 2]})
        assert result.ok
        assert result.value.combo == (1, 2)

    def test_bare_tuple_rejects_non_list(self):
        result = validate_args(BareTuple, {"combo": 5})
        assert result.fields == {"combo": "Expected a list, got int."}

    def test_bare_set_from_list(self):
        result = validate_args(BareSet, {"tags": [1, 2, 2]})
        assert result.ok
        assert type(result.value.tags) is set
        assert result.value.tags == {1, 2}

    def test_bare_set_rejects_non_list(self):
        result = validate_args(BareSet, {"tags": 5})
        assert result.fields == {"tags": "Expected a list, got int."}

    def test_dict_field_checks_each_value(self):
        # A parametrized dict's values are checked, and a bad one is named by its key.
        result = validate_args(TypedDictField, {"blob": {"a": 1, "b": "not-an-int"}})
        assert result.fields == {"blob.b": "Expected int, got str."}

    def test_dict_field_accepts_a_valid_object(self):
        result = validate_args(TypedDictField, {"blob": {"a": 1, "b": 2.0}})
        assert result.ok
        assert result.value.blob == {"a": 1, "b": 2}
        assert [type(item) for item in result.value.blob.values()] == [int, int]

    def test_dict_field_rejects_non_object(self):
        result = validate_args(TypedDictField, {"blob": 5})
        assert result.fields == {"blob": "Expected an object, got int."}

    def test_mapping_field_checks_each_value_and_returns_a_plain_dict(self):
        # A read-only mapping is accepted, and its checked content comes back
        # as a plain dict rather than the object that was passed in.
        blob = MappingProxyType({"a": 1})
        result = validate_args(TypedMappingField, {"blob": blob})

        assert result.ok
        assert type(result.value.blob) is dict
        assert result.value.blob == {"a": 1}

        bad = validate_args(TypedMappingField, {"blob": MappingProxyType({"a": "x"})})
        assert bad.fields == {"blob.a": "Expected int, got str."}

    def test_int_keyed_dict_binds_keys_by_the_string_rule(self):
        # A JSON object key is always a string, so "3" has to fill an int key.
        result = validate_args(IntKeyedDict, {"blob": {"3": "c", "10": "d"}})
        assert result.ok
        assert result.value.blob == {3: "c", 10: "d"}

    def test_bad_dict_key_is_named_with_the_key_prefix(self):
        result = validate_args(IntKeyedDict, {"blob": {"x": "c"}})
        assert result.fields == {"blob.x": "Invalid key: Not a valid int: 'x'."}

    def test_dict_with_any_values_passes_the_same_object_through(self):
        # Nothing to coerce, so the caller's object is handed over as it is.
        blob = {"a": 1, "b": [2]}
        result = validate_args(AnyValuedDict, {"blob": blob})
        assert result.ok
        assert result.value.blob is blob

    def test_nested_dict_values_name_the_whole_path(self):
        result = validate_args(DictOfLists, {"blob": {"a": [1, 2], "b": [3, "x"]}})
        assert result.fields == {"blob.b.1": "Expected int, got str."}

    @pytest.mark.parametrize("count", [1, 2, 21])
    def test_a_dict_stops_at_its_first_bad_value(self, count):
        # The same early stop the Pydantic path has, for a plain class.
        values = {f"k{index:02d}": "x" for index in range(count)}
        result = validate_args(TypedDictAndInt, {"scores": values, "name": "x"})
        # A scalar field's message is always listed beside the dict's.
        assert result.fields == {
            "name": "Expected int, got str.",
            "scores.k00": "Expected int, got str.",
        }
        assert result.unlisted_fields == 0

    def test_a_dict_names_the_first_bad_value_in_the_order_sent(self):
        result = validate_args(TypedDictAndInt, {"scores": {"a": 1, "b": "x", "c": "y"}, "name": 1})
        # `c` is bad too, but the dict stopped at `b`.
        assert result.fields == {"scores.b": "Expected int, got str."}

    def test_a_bad_dict_key_stops_the_dict(self):
        result = validate_args(IntKeyedDict, {"blob": {"x": "c", "y": "d", "3": "e"}})
        assert result.fields == {"blob.x": "Invalid key: Not a valid int: 'x'."}
        assert result.unlisted_fields == 0

    def test_mapping_field_rejects_non_object(self):
        result = validate_args(TypedMappingField, {"blob": 5})
        assert result.fields == {"blob": "Expected an object, got int."}

    def test_bare_dict_accepts_object(self):
        result = validate_args(BareDict, {"blob": {"a": 1}})
        assert result.ok
        assert result.value.blob == {"a": 1}

    def test_bare_dict_rejects_non_object(self):
        result = validate_args(BareDict, {"blob": [1]})
        assert result.fields == {"blob": "Expected an object, got list."}

    def test_typed_dict_items_pass_as_they_came(self):
        # isinstance() refuses a TypedDict, so an object passes unchanged.
        points = [{"x": 1}, {"unrelated": "kept"}]
        result = validate_args(PointList, {"points": points})
        assert result.ok
        assert result.value.points == points

    def test_a_typed_dict_item_that_is_not_an_object_is_named_by_its_index(self):
        result = validate_args(PointList, {"points": [{"x": 1}, 3]})
        assert result.fields == {"points.1": "Expected an object, got int."}

    def test_typed_dict_values_of_a_dict_pass_and_a_bad_one_is_named_by_its_key(self):
        by_name = {"a": {"x": 1}}
        result = validate_args(PointMap, {"by_name": by_name})
        assert result.ok
        assert result.value.by_name == by_name
        bad = validate_args(PointMap, {"by_name": {"a": {"x": 1}, "b": "text"}})
        assert bad.fields == {"by_name.b": "Expected an object, got str."}

    @pytest.mark.parametrize(("value", "message"), [(3, "got int"), ([1], "got list"), ("x", "got str")])
    def test_a_typed_dict_field_rejects_a_non_object(self, value, message):
        result = validate_args(PointField, {"origin": value})
        assert result.fields == {"origin": f"Expected an object, {message}."}

    def test_a_typed_dict_field_accepts_an_object(self):
        result = validate_args(PointField, {"origin": {"x": 1}})
        assert result.ok
        assert result.value.origin == {"x": 1}

    def test_a_protocol_field_without_runtime_checkable_is_unsupported(self):
        result = validate_args(ReaderField, {"reader": {"read": "x"}})
        assert result.fields == {"reader": "Unsupported annotation for event data: Reader."}

    def test_a_protocol_list_item_is_named_by_its_index(self):
        result = validate_args(ReaderList, {"readers": [1]})
        assert result.fields == {"readers.0": "Unsupported annotation for event data: Reader."}

    def test_a_protocol_with_an_annotated_attribute_is_unsupported(self):
        # The annotated attribute must not make it a schema class to build from the object.
        result = validate_args(NamedField, {"named": {"name": "x"}})
        assert result.fields == {"named": "Unsupported annotation for event data: Named."}

    def test_a_protocol_with_an_annotated_attribute_in_a_list_is_named_by_its_index(self):
        result = validate_args(NamedList, {"named": [{"name": "x"}]})
        assert result.fields == {"named.0": "Unsupported annotation for event data: Named."}

    def test_a_typing_extensions_typed_dict_field_accepts_an_object(self):
        result = validate_args(ExtensionPointField, {"origin": {"x": 1}})
        assert result.ok
        assert result.value.origin == {"x": 1}

    def test_a_typing_extensions_typed_dict_field_rejects_a_non_object(self):
        result = validate_args(ExtensionPointField, {"origin": 5})
        assert result.fields == {"origin": "Expected an object, got int."}

    def test_a_list_of_typing_extensions_typed_dicts_names_the_bad_item(self):
        result = validate_args(ExtensionPointList, {"points": [{"x": 1}, 3]})
        assert result.fields == {"points.1": "Expected an object, got int."}
        assert validate_args(ExtensionPointList, {"points": [{"x": 1}]}).ok

    def test_a_bare_typing_list_accepts_any_items(self):
        result = validate_args(TypingListField, {"items": [1, "a"]})
        assert result.ok
        assert result.value.items == [1, "a"]

    def test_a_bare_typing_list_rejects_a_non_list(self):
        result = validate_args(TypingListField, {"items": 5})
        assert result.fields == {"items": "Expected a list, got int."}

    def test_a_bare_typing_tuple_accepts_any_items(self):
        # The builtin `tuple[()]` declares an empty tuple, but the bare typing alias does not.
        result = validate_args(TypingTupleField, {"combo": [1, "a"]})
        assert result.ok
        assert result.value.combo == (1, "a")

    def test_a_bare_typing_tuple_rejects_a_non_list(self):
        result = validate_args(TypingTupleField, {"combo": 5})
        assert result.fields == {"combo": "Expected a list, got int."}

    def test_a_message_names_a_class_inside_a_generic_without_its_module(self):
        result = validate_args(BoxUnion, {"v": "s"})
        assert result.fields == {"v": "Expected dict[int, Box] or list[Box], got str."}


class TestUnhashableSetItems:
    # Wire arrays may nest arrays or objects; turning those into a set must be
    # a per-field error, never a TypeError out of validate_args.

    def test_bare_set_reports_unhashable_array_items(self):
        result = validate_args(BareSet, {"tags": [[1, 2]]})
        assert result.value is None
        assert result.fields == {"tags": "Set items must be hashable."}

    def test_bare_set_reports_unhashable_object_items(self):
        result = validate_args(BareSet, {"tags": [{"a": 1}]})
        assert result.fields == {"tags": "Set items must be hashable."}

    def test_parametrized_set_reports_unhashable_items(self):
        result = validate_args(ObjectsSet, {"tags": [[1, 2]]})
        assert result.fields == {"tags": "Set items must be hashable."}

    def test_set_union_member_does_not_raise(self):
        # The failed set attempt stays scratch work; the union reports its
        # combined message.
        result = validate_args(SetOrInt, {"v": [[1, 2]]})
        assert result.value is None
        assert result.fields == {"v": "Expected set or int, got list."}

    def test_optional_set_reports_unhashable_items(self):
        result = validate_args(MaybeSet, {"v": [[1, 2]]})
        assert result.fields == {"v": "Set items must be hashable."}


class TestNestedSchemas:
    def test_nested_object_builds_the_nested_instance(self):
        result = validate_args(AddressIn, {"address": {"city": "Brno"}})
        assert result.ok
        address = result.value.address
        assert address.city == "Brno"
        assert address.zip_code == ""
        assert isinstance(address, convert_schema_class(Address))

    def test_nested_schema_instance_passes_through(self):
        @dataclass
        class ReadyAddress:
            city: str

        class ReadyAddressIn:
            address: ReadyAddress

        address = ReadyAddress(city="Brno")
        result = validate_args(ReadyAddressIn, {"address": address})

        assert result.ok
        assert result.value.address is address

    def test_nested_field_error_uses_a_dotted_path(self):
        result = validate_args(AddressIn, {"address": {"city": 5}})
        assert result.fields == {"address.city": "Expected str, got int."}

    def test_nested_non_object_is_an_error_on_the_field(self):
        result = validate_args(AddressIn, {"address": "x"})
        assert result.fields == {"address": "Expected an object, got str."}

    def test_nested_extra_key_uses_a_dotted_path(self):
        result = validate_args(AddressIn, {"address": {"city": "B", "mango": 1}})
        assert result.fields == {"address.mango": EXTRA_MESSAGE}

    def test_nested_missing_required_uses_a_dotted_path(self):
        result = validate_args(AddressIn, {"address": {}})
        assert result.fields == {"address.city": REQUIRED_MESSAGE}

    def test_list_of_schemas_builds_instances(self):
        result = validate_args(Order, {"lines": [{"sku": "a", "qty": 1}, {"sku": "b", "qty": 2}]})
        assert result.ok
        line_cls = convert_schema_class(Line)
        assert result.value.lines == [line_cls(sku="a", qty=1), line_cls(sku="b", qty=2)]

    def test_list_of_schemas_error_paths_include_the_index(self):
        result = validate_args(Order, {"lines": [{"sku": "a", "qty": 1}, {"qty": "x"}]})
        assert list(result.fields) == ["lines.1.qty", "lines.1.sku"]
        assert result.fields == {
            "lines.1.qty": "Expected int, got str.",
            "lines.1.sku": REQUIRED_MESSAGE,
        }


class TestUnexpectedFieldLimit:
    @pytest.mark.parametrize("count", [21, 100])
    def test_a_declared_error_is_kept_and_unknown_keys_stop_at_twenty(self, count):
        result = validate_args(Plain, {"count": "x", **_unknown_keys(count)})
        assert result.value is None
        # `count` sorts before the `u...` names, so it comes first; the
        # unknown keys listed are the first twenty in sorted order.
        assert list(result.fields) == ["count", *_sorted_unknown(20)]
        assert result.fields["count"] == "Expected int, got str."
        assert all(result.fields[name] == EXTRA_MESSAGE for name in _sorted_unknown(20))
        assert result.unlisted_fields == count - 20

    def test_exactly_twenty_unknown_keys_are_all_listed(self):
        result = validate_args(Plain, {"count": 1, **_unknown_keys(20)})
        assert list(result.fields) == _sorted_unknown(20)
        assert result.unlisted_fields == 0

    def test_one_past_twenty_unknown_keys_leaves_one_out(self):
        result = validate_args(Plain, {"count": 1, **_unknown_keys(21)})
        assert list(result.fields) == _sorted_unknown(20)
        assert result.unlisted_fields == 1

    def test_a_form_payload_is_limited_like_a_json_payload(self):
        result = validate_args(Plain, StringArgs({"count": "x", **_unknown_keys(30)}))
        assert list(result.fields) == ["count", *_sorted_unknown(20)]
        assert result.unlisted_fields == 10

    def test_nothing_is_unlisted_when_validation_succeeds(self):
        result = validate_args(Plain, {"count": 1})
        assert result.ok
        assert result.unlisted_fields == 0

    @pytest.mark.parametrize("payload", [{}, {"count": "x"}, [1, 2]])
    def test_nothing_is_unlisted_when_no_unknown_key_was_sent(self, payload):
        result = validate_args(Plain, payload)
        assert not result.ok
        assert result.unlisted_fields == 0

    def test_unknown_keys_inside_a_nested_object_count(self):
        result = validate_args(AddressIn, {"address": {"city": 5, **_unknown_keys(25)}})
        assert result.fields["address.city"] == "Expected str, got int."
        assert [name for name in result.fields if name != "address.city"] == _sorted_unknown(20, "address.")
        assert result.unlisted_fields == 5

    def test_nested_and_top_level_unknown_keys_share_one_limit(self):
        nested = {f"n{index:02d}": 1 for index in range(12)}
        top = {f"t{index:02d}": 1 for index in range(12)}
        result = validate_args(AddressIn, {"address": {"city": "Brno", **nested}, **top})
        # 24 unknown keys in all. `address.n..` sorts before `t..`, so the
        # twelve nested names and the first eight top-level names are listed.
        assert list(result.fields) == [
            *(f"address.n{index:02d}" for index in range(12)),
            *(f"t{index:02d}" for index in range(8)),
        ]
        assert result.unlisted_fields == 4

    def test_unknown_keys_inside_an_optional_nested_object_count(self):
        class MaybeAddressIn:
            address: Address | None = None

        result = validate_args(MaybeAddressIn, {"address": {"city": "Brno", **_unknown_keys(22)}})
        assert list(result.fields) == _sorted_unknown(20, "address.")
        assert result.unlisted_fields == 2

    def test_unknown_keys_inside_a_list_row_count(self):
        row = {"sku": "a", "qty": 1, **_unknown_keys(25)}
        result = validate_args(Order, {"lines": [row]})
        assert list(result.fields) == _sorted_unknown(20, "lines.0.")
        assert result.unlisted_fields == 5

    def test_a_list_of_rows_stops_at_the_first_row_with_an_error(self):
        lines = [{"sku": "a", "qty": 1, f"x{index:02d}": 1} for index in range(25)]
        result = validate_args(Order, {"lines": lines})
        # Row 0 has an unknown key, so the later rows are not checked.
        assert result.fields == {"lines.0.x00": EXTRA_MESSAGE}
        assert result.unlisted_fields == 0

    @pytest.mark.parametrize("count", [1, 20, 21, 30])
    def test_a_list_stops_at_its_first_bad_item(self, count):
        result = validate_args(TagsList, {"tags": ["x"] * count})
        assert result.fields == {"tags.0": "Expected int, got str."}
        assert result.unlisted_fields == 0

    def test_a_list_names_the_first_bad_item_in_the_order_sent(self):
        result = validate_args(TagsList, {"tags": [1, 2, "x", 4, "y"]})
        # Item 4 is bad too, but the list stopped at item 2.
        assert result.fields == {"tags.2": "Expected int, got str."}

    def test_each_list_field_stops_at_its_own_first_bad_item(self):
        class TwoLists:
            first: list[int]
            second: list[int]

        result = validate_args(TwoLists, {"first": ["x"] * 21, "second": [1, "x", "x"]})
        assert result.fields == {"first.0": "Expected int, got str.", "second.1": "Expected int, got str."}
        assert result.unlisted_fields == 0

    def test_a_stopped_list_and_unknown_keys_are_limited_separately(self):
        result = validate_args(TagsList, {"tags": ["x"] * 30, **_unknown_keys(25)})
        # The list's early stop leaves the unknown-key limit untouched.
        assert result.fields["tags.0"] == "Expected int, got str."
        assert [name for name in result.fields if name.startswith("tags.")] == ["tags.0"]
        assert [name for name in result.fields if name.startswith("u")] == _sorted_unknown(20)
        assert result.unlisted_fields == 5

    def test_every_missing_required_field_is_listed(self):
        result = validate_args(Wide, {})
        assert len(result.fields) == 30
        assert set(result.fields.values()) == {REQUIRED_MESSAGE}
        assert result.unlisted_fields == 0

    def test_missing_required_fields_are_kept_beside_limited_unknown_keys(self):
        result = validate_args(Wide, _unknown_keys(25))
        required = [name for name in result.fields if name.startswith("f")]
        assert required == [f"f{index:02d}" for index in range(30)]
        assert [name for name in result.fields if name.startswith("u")] == _sorted_unknown(20)
        assert result.unlisted_fields == 5


class TestUnionsAndOptional:
    def test_optional_defaults_to_none(self):
        result = validate_args(MaybeInt, {})
        assert result.ok
        assert result.value.v is None

    def test_optional_accepts_null(self):
        result = validate_args(MaybeInt, {"v": None})
        assert result.ok
        assert result.value.v is None

    def test_optional_accepts_the_member_type(self):
        result = validate_args(MaybeInt, {"v": 3})
        assert result.ok
        assert result.value.v == 3

    def test_optional_failure_uses_the_member_message(self):
        result = validate_args(MaybeInt, {"v": "x"})
        assert result.fields == {"v": "Expected int, got str."}

    def test_union_picks_the_fitting_member(self):
        assert validate_args(IntOrStr, {"v": 3}).value.v == 3
        assert validate_args(IntOrStr, {"v": "x"}).value.v == "x"

    def test_union_failure_names_all_members(self):
        result = validate_args(IntOrStr, {"v": [1]})
        assert result.fields == {"v": "Expected int or str, got list."}

    def test_union_failure_formats_a_parameterized_member_readably(self):
        result = validate_args(ListOrInt, {"v": "x"})
        assert result.fields == {"v": "Expected list[int] or int, got str."}


class TestLiteralFields:
    def test_a_listed_value_validates(self):
        result = validate_args(LiteralChoices, {"level": "high", "size": 2, "forced": True, "color": "red"})
        assert result.ok
        assert (result.value.level, result.value.size, result.value.forced, result.value.color) == (
            "high",
            2,
            True,
            Color.RED,
        )

    def test_an_unlisted_value_names_the_choices(self):
        result = validate_args(LiteralChoices, {"level": "mid"})
        assert result.fields == {"level": "Expected one of 'low', 'high', got 'mid'."}

    def test_a_value_of_another_type_is_rejected(self):
        result = validate_args(LiteralChoices, {"level": 1})
        assert result.fields == {"level": "Expected one of 'low', 'high', got 1."}

    def test_true_and_one_stay_apart(self):
        # Python counts True == 1, but JSON keeps them apart, and so does the field.
        assert validate_args(LiteralChoices, {"level": "low", "size": True}).fields == {
            "size": "Expected one of 1, 2, got true.",
        }
        assert validate_args(LiteralChoices, {"level": "low", "forced": 1}).fields == {
            "forced": "Expected one of true, got 1.",
        }

    def test_a_whole_float_binds_to_an_int_choice(self):
        # The int/float cross-coercion of a plain int field applies to each choice.
        result = validate_args(LiteralChoices, {"level": "low", "size": 2.0})
        assert result.ok
        assert result.value.size == 2

    def test_an_enum_choice_binds_from_its_value(self):
        assert validate_args(LiteralChoices, {"level": "low", "color": "blue"}).fields == {
            "color": "Expected one of 'red', got 'blue'.",
        }

    def test_an_enum_choice_with_a_number_value_matches_that_number(self):
        # The wire carries an Enum member as its value, whatever its type.
        assert validate_args(EnumLiteral, {"weight": 2}).value.weight is Weight.HEAVY
        assert validate_args(EnumLiteral, {"weight": 1}).fields == {"weight": "Expected one of 2, got 1."}

    def test_a_string_transport_binds_each_choice_by_its_type(self):
        result = validate_args(LiteralChoices, StringArgs({"level": "low", "size": "2", "forced": "true"}))
        assert result.ok
        assert (result.value.size, result.value.forced) == (2, True)

    def test_json_keeps_a_numeric_string_apart_from_an_int_choice(self):
        result = validate_args(LiteralChoices, {"level": "low", "size": "2"})
        assert result.fields == {"size": "Expected one of 1, 2, got '2'."}


class TestUnsupportedAnnotations:
    def test_exact_none_accepts_null_and_rejects_other_values(self):
        result = validate_args(NullOnly, {"value": None})
        assert result.ok
        assert result.value.value is None

        rejected = validate_args(NullOnly, {"value": "none"})
        assert rejected.fields == {"value": "Expected null, got str."}

    def test_unsupported_parameterized_annotation_is_a_field_error(self):
        result = validate_args(UnsupportedContainer, {"value": []})
        assert result.fields == {
            "value": "Unsupported annotation for event data: frozenset[int].",
        }

    def test_unsupported_type_variable_is_a_field_error(self):
        result = validate_args(UnsupportedTypeVariable, {"value": 1})
        assert result.fields == {
            "value": "Unsupported annotation for event data: ~UnsupportedType.",
        }


class TestUploadedFile:
    def test_attributes(self):
        uploaded = UploadedFile(
            io.BytesIO(b"hello world"),
            filename="a.txt",
            content_type="text/plain",
            native="HOST",
        )
        assert uploaded.filename == "a.txt"
        assert uploaded.size == 11
        assert uploaded.content_type == "text/plain"
        assert uploaded.native == "HOST"

    def test_explicit_size_and_defaults(self):
        uploaded = UploadedFile(io.BytesIO(b"abc"), filename="b.bin", size=3)
        assert uploaded.size == 3
        assert uploaded.content_type is None
        assert uploaded.native is None

    def test_full_read_rewinds_and_repeats(self):
        uploaded = UploadedFile(io.BytesIO(b"hello world"), filename="a.txt")
        assert uploaded.read() == b"hello world"
        assert uploaded.read() == b"hello world"

    def test_partial_reads_advance(self):
        uploaded = UploadedFile(io.BytesIO(b"hello world"), filename="a.txt")
        assert uploaded.read(5) == b"hello"
        assert uploaded.read(6) == b" world"
        # A full read still returns everything afterwards.
        assert uploaded.read() == b"hello world"

    def test_save_writes_full_content_and_returns_the_path(self, tmp_path):
        uploaded = UploadedFile(io.BytesIO(b"hello world"), filename="a.txt")
        destination = uploaded.save(str(tmp_path / "out.bin"))
        assert isinstance(destination, Path)
        assert destination == tmp_path / "out.bin"
        assert destination.read_bytes() == b"hello world"

    def test_save_after_read_writes_full_content(self, tmp_path):
        uploaded = UploadedFile(io.BytesIO(b"hello world"), filename="a.txt")
        uploaded.read()
        destination = uploaded.save(tmp_path / "out.bin")
        assert destination.read_bytes() == b"hello world"

    def test_file_field_rejects_wire_json_object(self):
        result = validate_args(WithFile, {"avatar": {"name": "x.png"}})
        assert result.value is None
        assert result.fields == {"avatar": FILE_MESSAGE}

    def test_file_field_rejects_wire_json_string(self):
        result = validate_args(WithFile, {"avatar": "abc"})
        assert result.fields == {"avatar": FILE_MESSAGE}

    def test_file_list_rejects_wire_json_naming_the_index(self):
        result = validate_args(WithFiles, {"attachments": ["x"]})
        assert result.fields == {"attachments.0": FILE_MESSAGE}

    def test_file_field_accepts_a_real_instance(self):
        # The multipart payload codec (v1.x) will construct the instances;
        # validation accepts them as-is.
        uploaded = UploadedFile(io.BytesIO(b"png"), filename="c.png")
        result = validate_args(WithFile, {"avatar": uploaded})
        assert result.ok
        assert result.value.avatar is uploaded

    def test_file_list_accepts_real_instances(self):
        uploaded = UploadedFile(io.BytesIO(b"png"), filename="c.png")
        result = validate_args(WithFiles, {"attachments": [uploaded]})
        assert result.ok
        assert result.value.attachments == [uploaded]


@requires_pydantic
class TestPydanticDelegation:
    def test_validation_delegates_wholesale(self):
        class PModel(pydantic.BaseModel):
            x: int

        # Pydantic's lax mode parses numeric strings; our own table rejects
        # them. Accepting "5" proves the payload went to Pydantic, not us.
        result = validate_args(PModel, {"x": "5"})
        assert result.ok
        assert result.value == PModel(x=5)

    def test_missing_field_maps_per_field(self):
        class PModel(pydantic.BaseModel):
            x: int

        result = validate_args(PModel, {})
        assert result.value is None
        assert result.fields == {"x": "Field required"}

    def test_extra_keys_follow_pydantic_rules(self):
        class PModel(pydantic.BaseModel):
            x: int

        # Pydantic ignores extras by default; our extra-key rule must not
        # apply to a delegated model.
        result = validate_args(PModel, {"x": 1, "mango": 2})
        assert result.ok
        assert result.value == PModel(x=1)

    def test_error_locations_join_with_dots(self):
        class PList(pydantic.BaseModel):
            items: list[int]

        result = validate_args(PList, {"items": [1, "abc"]})
        assert list(result.fields) == ["items.1"]
        # The message is Pydantic's own wording; lock only its stable start.
        assert result.fields["items.1"].startswith("Input should be a valid integer")

    def test_nested_model_inside_a_plain_schema(self):
        class PModel(pydantic.BaseModel):
            x: int

        class HasInner:
            inner: PModel

        result = validate_args(HasInner, {"inner": {"x": "5"}})
        assert result.ok
        assert result.value.inner == PModel(x=5)

    def test_nested_model_error_path_is_prefixed(self):
        class PModel(pydantic.BaseModel):
            x: int

        class HasInner:
            inner: PModel

        result = validate_args(HasInner, {"inner": {"x": "abc"}})
        assert list(result.fields) == ["inner.x"]
        assert result.fields["inner.x"].startswith("Input should be a valid integer")


@requires_pydantic
class TestPydanticUnexpectedFieldLimit:
    @staticmethod
    def _forbidding_model():
        class PModel(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(extra="forbid")
            x: int

        return PModel

    def test_forbidden_extra_keys_stop_at_twenty_and_other_errors_stay(self):
        result = validate_args(self._forbidding_model(), {"x": "nope", **_unknown_keys(25)})
        assert result.value is None
        # `x` sorts after the `u...` names.
        assert list(result.fields) == [*_sorted_unknown(20), "x"]
        assert result.fields["x"].startswith("Input should be a valid integer")
        # The extras carry Pydantic's own wording.
        assert result.fields["u000"].startswith("Extra inputs are not permitted")
        assert result.unlisted_fields == 5

    def test_exactly_twenty_forbidden_extra_keys_are_all_listed(self):
        result = validate_args(self._forbidding_model(), {"x": 1, **_unknown_keys(20)})
        assert list(result.fields) == _sorted_unknown(20)
        assert result.unlisted_fields == 0

    def test_forbidden_extra_keys_inside_a_nested_model_count(self):
        forbidding = self._forbidding_model()

        class HasInner:
            inner: forbidding

        result = validate_args(HasInner, {"inner": {"x": 1, **_unknown_keys(23)}})
        assert list(result.fields) == _sorted_unknown(20, "inner.")
        assert result.unlisted_fields == 3

    def test_every_missing_model_field_is_listed(self):
        wide = pydantic.create_model("Wide", **{f"f{index:02d}": (int, ...) for index in range(30)})
        result = validate_args(wide, {})
        assert len(result.fields) == 30
        assert result.unlisted_fields == 0

    def test_missing_model_fields_are_kept_beside_limited_extras(self):
        wide = pydantic.create_model(
            "Wide",
            __config__=pydantic.ConfigDict(extra="forbid"),
            **{f"f{index:02d}": (int, ...) for index in range(30)},
        )
        result = validate_args(wide, _unknown_keys(25))
        assert [name for name in result.fields if name.startswith("f")] == [f"f{index:02d}" for index in range(30)]
        assert [name for name in result.fields if name.startswith("u")] == _sorted_unknown(20)
        assert result.unlisted_fields == 5

    def test_ignored_extra_keys_are_not_errors_at_all(self):
        class PModel(pydantic.BaseModel):
            x: int

        result = validate_args(PModel, {"x": 1, **_unknown_keys(50)})
        assert result.ok
        assert result.unlisted_fields == 0


class TestWithoutPydantic:
    def test_plain_schemas_validate_with_pydantic_hidden(self, monkeypatch):
        monkeypatch.setattr(schemas_module, "pydantic", None)

        class SearchIn:
            query: str
            limit: int = 10

        result = validate_args(SearchIn, {"query": "abc"})
        assert result.ok
        assert (result.value.query, result.value.limit) == ("abc", 10)
        missing = validate_args(SearchIn, {})
        assert missing.fields == {"query": REQUIRED_MESSAGE}

    def test_module_imports_and_validates_without_pydantic(self):
        # A subprocess with pydantic blocked at the import machinery proves
        # the soft import: the module loads and plain schemas validate.
        script = textwrap.dedent(
            """
            import importlib.abc
            import sys

            class BlockPydantic(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname == "pydantic" or fullname.startswith("pydantic."):
                        raise ImportError("pydantic is blocked in this test")
                    return None

            sys.meta_path.insert(0, BlockPydantic())

            from citry.ext.events.schemas import validate_args

            class SearchIn:
                query: str
                limit: int = 10

            ok = validate_args(SearchIn, {"query": "abc"})
            assert ok.ok, ok.fields
            assert (ok.value.query, ok.value.limit) == ("abc", 10)
            bad = validate_args(SearchIn, {})
            assert bad.fields == {"query": "This field is required."}, bad.fields
            assert "pydantic" not in sys.modules
            print("OK-WITHOUT-PYDANTIC")
            """
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert "OK-WITHOUT-PYDANTIC" in completed.stdout


def test_declared_field_names_reads_init_fields_without_resolving_annotations():
    @dataclass
    class WithInitFalse:
        q: str
        computed: int = dataclass_field(default=0, init=False)

    class Plain:
        q: "NotDefinedAnywhere"  # noqa: F821 - never resolved
        page: int = 1

    assert declared_field_names(WithInitFalse) == frozenset({"q"})
    assert declared_field_names(Plain) == frozenset({"q", "page"})


@requires_pydantic
def test_declared_field_names_counts_a_pydantic_alias():
    class Model(pydantic.BaseModel):
        token: str = pydantic.Field(alias="csrfmiddlewaretoken")

    assert declared_field_names(Model) == frozenset({"token", "csrfmiddlewaretoken"})


@requires_pydantic
def test_declared_field_names_counts_pydantic_validation_aliases():
    class Single(pydantic.BaseModel):
        token: str = pydantic.Field(validation_alias="csrfmiddlewaretoken")

    class Choices(pydantic.BaseModel):
        token: str = pydantic.Field(validation_alias=pydantic.AliasChoices("csrfmiddlewaretoken", "tok"))

    class Nested(pydantic.BaseModel):
        token: str = pydantic.Field(validation_alias=pydantic.AliasPath("csrf", 0))

    assert "csrfmiddlewaretoken" in declared_field_names(Single)
    assert {"csrfmiddlewaretoken", "tok"} <= declared_field_names(Choices)
    assert "csrf" in declared_field_names(Nested)


INTEGER_MESSAGE = "Input should be a valid integer, unable to parse string as an integer"


@requires_pydantic
class TestPydanticItemErrorLimit:
    """
    A Pydantic list, set, tuple or dict stops at its first bad item, so a 422 lists one item per collection.

    Citry's own validator for a plain dataclass stops at the first bad item
    of each collection too (see ``TestContainerCoercion`` and
    ``TestUnexpectedFieldLimit``).
    """

    @pytest.mark.parametrize("count", [1, 20, 21])
    def test_a_pydantic_list_lists_only_its_first_bad_item(self, count):
        class Tags(pydantic.BaseModel):
            tags: list[int]

        result = validate_args(Tags, {"tags": ["x"] * count})
        assert result.fields == {"tags.0": INTEGER_MESSAGE}
        assert result.unlisted_fields == 0

    def test_a_pydantic_list_lists_the_first_bad_item_in_the_order_sent(self):
        class Tags(pydantic.BaseModel):
            tags: list[int]

        result = validate_args(Tags, {"tags": [1, 2, "x", 4, "y"]})
        assert result.fields == {"tags.2": INTEGER_MESSAGE}

    @pytest.mark.parametrize("count", [1, 20, 21])
    def test_a_pydantic_dict_lists_only_its_first_bad_value(self, count):
        class Scores(pydantic.BaseModel):
            scores: dict[str, int]
            name: int

        values = {f"k{index:02d}": "x" for index in range(count)}
        result = validate_args(Scores, {"scores": values, "name": "x"})
        # A scalar field's message is always listed beside the dict's.
        assert result.fields == {"name": INTEGER_MESSAGE, "scores.k00": INTEGER_MESSAGE}
        assert result.unlisted_fields == 0

    @pytest.mark.parametrize("count", [1, 21])
    def test_a_plain_dataclass_dict_lists_only_its_first_bad_value(self, count):
        class Scores:
            scores: dict[str, int]

        values = {f"k{index:02d}": "x" for index in range(count)}
        result = validate_args(Scores, {"scores": values})
        assert result.fields == {"scores.k00": "Expected int, got str."}
        assert result.unlisted_fields == 0

    def test_a_list_inside_a_nested_model_lists_its_first_bad_item(self):
        class Inner(pydantic.BaseModel):
            values: list[int]

        class HasInner:
            inner: Inner

        result = validate_args(HasInner, {"inner": {"values": ["x"] * 25}})
        assert result.fields == {"inner.values.0": INTEGER_MESSAGE}
        assert result.unlisted_fields == 0

    def test_a_list_or_dict_inside_a_union_lists_its_first_bad_item(self):
        class Shapes(pydantic.BaseModel):
            items: list[int] | str
            scores: dict[str, int] | int

        result = validate_args(Shapes, {"items": ["x"] * 25, "scores": {f"k{index:02d}": "x" for index in range(25)}})
        # Pydantic also reports the other union member once; that message stays.
        assert result.fields == {
            "items.list[int].0": INTEGER_MESSAGE,
            "items.str": "Input should be a valid string",
            "scores.dict[str,int].k00": INTEGER_MESSAGE,
            "scores.int": "Input should be a valid integer",
        }
        assert result.unlisted_fields == 0

    def test_an_aliased_list_or_dict_lists_its_first_bad_item(self):
        class Aliased(pydantic.BaseModel):
            tags: list[int] = pydantic.Field(default=[], alias="tagList")
            scores: dict[str, int] = pydantic.Field(default={}, alias="scoreMap")

        result = validate_args(
            Aliased, {"tagList": ["x"] * 21, "scoreMap": {f"k{index:02d}": "x" for index in range(21)}}
        )
        assert result.fields == {"scoreMap.k00": INTEGER_MESSAGE, "tagList.0": INTEGER_MESSAGE}
        assert result.unlisted_fields == 0

    def test_a_very_long_digit_key_in_a_dict_is_an_ordinary_error(self):
        class Scores(pydantic.BaseModel):
            scores: dict[str, int]

        # Sorting must not turn the key into a number: Python refuses a
        # number this long.
        result = validate_args(Scores, {"scores": {"1" * 5000: "x"}})
        assert list(result.fields) == ["scores." + "1" * 5000]

    def test_marking_the_lists_of_deep_errors_takes_time_in_step_with_their_depth(self):
        # Every level holds a list of nodes, and the innermost node also has
        # thirty bad scalar fields. Each scalar field has its own error, so
        # thirty errors pass through `depth` lists, and the list of 3,000 bad
        # items beside them adds only its first.
        fields: dict[str, Any] = {f"v{index:02d}": (int, 0) for index in range(30)}
        Node = pydantic.create_model("Node", c=("list[Node]", []), **fields)
        Node.model_rebuild(_types_namespace={"Node": Node})

        def best_time(depth: int) -> float:
            # The best of three runs keeps one slow run of a busy machine out
            # of the ratio.
            best = float("inf")
            for _run in range(3):
                value: dict[str, Any] = {"c": [1] * 3_000, **{f"v{index:02d}": "x" for index in range(30)}}
                for _level in range(depth - 1):
                    value = {"c": [value]}
                started = perf_counter()
                result = validate_args(Node, value)
                best = min(best, perf_counter() - started)
                # The 31 errors are inside the outer lists, which keep twenty.
                assert len(result.fields) == 20
                assert result.unlisted_fields == 11
            return best

        # Writing the text of each list for each error made the time grow
        # with the square of the depth: five times the depth took about 19
        # times as long. Reading each error once takes about 5 times as long,
        # and the bound leaves room for a slow machine.
        assert best_time(200) < 10 * best_time(40)

    @pytest.mark.parametrize("data_class", ["top", "nested"])
    def test_a_list_field_with_an_empty_alias_lists_its_first_bad_item(self, data_class):
        class Empty(pydantic.BaseModel):
            v: list[int] = pydantic.Field(alias="")

        @dataclass
        class Outer:
            o: Empty

        if data_class == "top":
            result = validate_args(Empty, {"": ["x"] * 500})
            assert result.fields == {".0": INTEGER_MESSAGE}
        else:
            result = validate_args(Outer, {"o": {"": ["x"] * 500}})
            assert result.fields == {"o..0": INTEGER_MESSAGE}
        assert result.unlisted_fields == 0


def test_a_very_long_digit_key_is_an_ordinary_unexpected_field():
    result = validate_args(TagsList, {"tags": [], "1" * 5000: 1})
    assert list(result.fields) == ["1" * 5000]


def test_digit_segments_sort_in_number_order_with_leading_zeros_apart():
    result = validate_args(TagsList, {"tags": [], "10": 1, "9": 1, "09": 1, "x": 1})
    assert list(result.fields) == ["09", "9", "10", "x"]


@requires_pydantic
class TestPydanticPathText:
    """
    Pydantic writes each field's path into its errors, so Citry can add up the paths before calling it.

    ``pydantic_can_report`` is that sum. A Pydantic v2 class that Citry checks
    with its copy of the validator does not need it, because the copy keeps one
    error per collection. The sum still runs for a class whose copy had to be
    built without its counting wrappers (``Checker.needs_path_limit``), which
    the ``without_wrappers`` fixture forces, and for a Pydantic v1 model.
    """

    class Model(pydantic.BaseModel if pydantic else object):  # type: ignore[misc]
        pass

    @pytest.fixture
    def without_wrappers(self, monkeypatch):
        """Make Citry's copy of the validator fail to build with wrappers, so Citry falls back to the path limit."""
        build = bounded._build

        def refuse_wrappers(schema, *, wrapped):
            if wrapped:
                msg = "no wrappers"
                raise RuntimeError(msg)
            return build(schema, wrapped=wrapped)

        monkeypatch.setattr(bounded, "_build", refuse_wrappers)

    def _passes(self, payload, model=None):
        return pydantic_can_report(payload, model or self.Model, FieldErrors())

    def test_short_paths_pass(self):
        assert self._passes({"tags": ["x"] * 100_000})

    def test_a_long_key_over_many_items_does_not_pass(self):
        assert not self._passes({"tags": {"a" * 56_000: ["x"] * 14_000}})

    def test_the_total_runs_across_a_validation(self):
        # One object is under the limit; four of them together are not.
        errors = FieldErrors()

        # Held in a list, as a request's payload is held: the total reads ids.
        payloads = [{"tags": {"a" * 40_000: ["x"] * 120}} for _ in range(4)]
        assert [pydantic_can_report(payload, self.Model, errors) for payload in payloads] == [True, True, True, False]

    def test_each_union_attempt_counts_the_same_payload_again(self):
        class First(pydantic.BaseModel):
            pass

        class Second(pydantic.BaseModel):
            pass

        errors = FieldErrors()
        scratch = FieldErrors(shares_total_with=errors)
        # One payload object, as Citry's own union hands to each of its members.
        payload = {"tags": {"a" * 40_000: ["x"] * 400}}
        assert pydantic_can_report(payload, First, scratch)
        size = errors.pydantic_total.size
        assert not pydantic_can_report(payload, Second, errors)
        # Reading it twice adds paths, and does not make the payload larger.
        assert errors.pydantic_total.size == size

    @pytest.mark.parametrize(
        ("rows", "limited", "reaches_costly"),
        [
            # Citry's copy of the validator keeps one error per collection, so every
            # member runs and answers cheaply.
            (1, False, True),
            (1_000, False, True),
            (1, True, True),
            (10, True, True),
            (100, True, True),
            (1_000, True, False),
        ],
        ids=["copy-1", "copy-1000", "limit-1", "limit-10", "limit-100", "limit-1000"],
    )
    def test_a_citry_union_of_pydantic_models_is_held_to_the_limit(self, rows, limited, reaches_costly, request):
        if limited:
            request.getfixturevalue("without_wrappers")

        class Cheap(pydantic.BaseModel):
            other: int

        row = pydantic.create_model("Row", **{f"f{index:02d}": (int, ...) for index in range(40)})
        checked: list[object] = []

        class Costly(pydantic.BaseModel):
            rows: dict[str, list[row]]  # type: ignore[valid-type]

            # Runs only when Pydantic checks this member.
            @pydantic.model_validator(mode="before")
            @classmethod
            def note(cls, value: object) -> object:
                checked.append(value)
                return value

        @dataclass
        class Data:
            value: Cheap | Costly

        # Each empty row lacks 40 fields under Costly and one under Cheap,
        # so only Costly's count is over the limit. Citry tries Cheap first,
        # and must still count the same object again for Costly. With fewer
        # rows the count stays under the limit, so Costly runs: that shows
        # `checked` is empty at 1,000 rows because of the limit.
        payload = {"rows": {"a" * 500: [{} for _ in range(rows)]}}
        result = validate_args(Data, {"value": payload})
        assert not result.ok
        assert bool(checked) is reaches_costly
        # The limit refuses the member before it runs, so only the union's
        # own message is left either way.
        assert result.fields == {"value": "Expected Cheap or Costly, got dict."}

    def test_the_limit_follows_the_size_of_a_large_payload(self):
        # The same paths pass when the payload holds enough other text, so
        # an app that raises its body limit is not caught by the fixed amount.
        tight = {"tags": {"a" * 20_000: ["x"] * 1_000}}
        assert not self._passes(tight)
        assert self._passes({**tight, "note": "n" * 1_000_000})

    def test_a_large_grid_of_short_numbers_passes(self):
        # Long lists of short numbers under one field are the valid shape
        # nearest the limit. Through JSON, as a request's data is, so no
        # list is shared.
        grid = json.loads(json.dumps({"measurement_grid_values_x": [[1] * 700] * 700}))
        assert self._passes(grid)

    def test_a_value_that_holds_itself_ends_the_walk(self):
        cycle: dict[str, Any] = {}
        cycle["self"] = cycle
        assert self._passes(cycle)

    @pytest.mark.parametrize(
        "shape",
        [
            pytest.param('{"K": [ITEMS]}', id="plain"),
            # A parser that keeps the last repeated key would see nothing here.
            pytest.param('{"K": [ITEMS], "K": []}', id="repeated-key"),
            # Python's parser and Pydantic's stop at different depths.
            pytest.param('{"K": [ITEMS], "x": ' + "[" * 201 + "]" * 201 + "}", id="deep-sibling"),
            pytest.param('{"K": [NaN, ITEMS]}', id="not-strict-json"),
            pytest.param('{"K": [ITEMS]', id="unclosed"),
        ],
    )
    def test_the_paths_inside_a_json_field_count(self, shape):
        class WithJson(pydantic.BaseModel):
            data: pydantic.Json[dict[str, list[int]]]

        text = shape.replace("K", "a" * 56_000).replace("ITEMS", ",".join(['"x"'] * 14_000))
        assert self._passes({"data": text})
        assert not self._passes({"data": text}, WithJson)

    def test_many_short_json_strings_add_up(self):
        class WithJson(pydantic.BaseModel):
            data: dict[str, list[pydantic.Json[list[str]]]]

        text = "[" + ",".join(['"x"'] * 100) + "]"
        payload = {"data": {"a" * 200_000: [text] * 1_000}}
        assert not self._passes(json.loads(json.dumps(payload)), WithJson)

    def test_text_that_ends_in_a_backslash_is_read_in_one_pass(self):
        class WithJson(pydantic.BaseModel):
            data: pydantic.Json[list[str]]

        started = perf_counter()
        self._passes({"data": '\\"' * 100_000 + "\\"}, WithJson)
        assert perf_counter() - started < 0.5

    def test_json_text_inside_json_text_counts(self):
        class Twice(pydantic.BaseModel):
            data: dict[str, pydantic.Json[pydantic.Json[list[int]]]]

        inner = json.dumps(json.dumps(["x"] * 14_000))
        assert not self._passes({"data": {"a" * 56_000: inner}}, Twice)

    def test_json_text_under_a_long_key_in_json_text_counts_the_key(self):
        class Nested(pydantic.BaseModel):
            data: pydantic.Json[dict[str, pydantic.Json[list[int]]]]

        text = json.dumps({"a" * 56_000: json.dumps(["x"] * 14_000)})
        assert not self._passes({"data": text}, Nested)

    def test_a_string_of_nested_quotes_is_read_in_a_few_passes(self):
        class WithJson(pydantic.BaseModel):
            data: pydantic.Json[list[str]]

        started = perf_counter()
        self._passes({"data": '"[\\"' * 40_000}, WithJson)
        assert perf_counter() - started < 1

    def test_json_text_that_opens_a_bracket_at_every_character_is_read_in_little_memory(self):
        class WithJson(pydantic.BaseModel):
            data: pydantic.Json[list[Any]]

        # The count keeps the path length at each open bracket, so a megabyte
        # of brackets must not cost an object per bracket.
        tracemalloc.start()
        try:
            self._passes({"data": "[" * 1_000_000}, WithJson)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        assert peak < 16_000_000

    @pytest.mark.parametrize(
        "quote",
        ["\\u0022", '\\"'],
        ids=["unicode-escape", "backslash-escape"],
    )
    def test_a_long_key_written_with_escaped_quotes_counts(self, quote):
        class Nested(pydantic.BaseModel):
            data: pydantic.Json[pydantic.Json[dict[str, list[int]]]]

        items = ",".join(["[]"] * 17_000)
        text = f'"{{{quote}{"a" * 48_000}{quote}:[{items}]}}"'
        assert not self._passes({"data": text}, Nested)

    def test_a_key_that_holds_a_quote_hides_nothing(self):
        class Nested(pydantic.BaseModel):
            data: pydantic.Json[pydantic.Json[dict[str, list[int]]]]

        # Reading the text without decoding it would turn this key's quote
        # into the start of a string that swallows everything after it.
        inner = json.dumps({'z"': [], "a" * 48_000: [[]] * 17_000}, separators=(",", ":"))
        assert not self._passes({"data": json.dumps(inner)}, Nested)

    def test_json_text_nested_five_levels_counts(self):
        class Deep(pydantic.BaseModel):
            data: pydantic.Json[pydantic.Json[pydantic.Json[pydantic.Json[pydantic.Json[dict[str, list[int]]]]]]]

        text = json.dumps({"a" * 48_000: [[]] * 17_000}, separators=(",", ":"))
        for _ in range(4):
            text = json.dumps(text)
        assert not self._passes({"data": text}, Deep)

    def test_a_bracket_written_as_an_escape_is_still_read(self):
        class Deep(pydantic.BaseModel):
            data: pydantic.Json[pydantic.Json[pydantic.Json[dict[str, list[int]]]]]

        # After one decoding the text holds a quote and no bracket, because
        # the bracket is still escaped.
        inner = '{"' + "a" * 48_000 + '":[' + ",".join(["[]"] * 17_000) + "]}"
        hidden = json.dumps(inner).replace("{", "\\u007b").replace("[", "\\u005b")
        assert not self._passes({"data": json.dumps(hidden)}, Deep)

    def test_an_empty_object_counts_the_fields_it_may_lack(self):
        class Row(pydantic.BaseModel):
            a0: int
            a1: int
            a2: int
            a3: int
            a4: int
            a5: int
            a6: int
            a7: int

        class Rows(pydantic.BaseModel):
            rows: dict[str, list[Row]]

        payload = json.loads(json.dumps({"rows": {"a" * 25_000: [{}] * 100}}))
        assert self._passes(payload)
        payload = json.loads(json.dumps({"rows": {"a" * 25_000: [{}] * 200}}))
        assert not self._passes(payload, Rows)

    def test_required_positions_of_a_fixed_tuple_count_for_lists(self):
        class Shapes(pydantic.BaseModel):
            fixed: tuple[int, int, int, int]

        assert schemas_module._model_costs(Shapes).list_items == 4

    def test_required_positions_of_a_named_tuple_count_for_lists_and_objects(self):
        class Point(typing.NamedTuple):
            x: int
            y: int
            z: int

        class Shapes(pydantic.BaseModel):
            named: Point

        costs = schemas_module._model_costs(Shapes)
        assert costs.list_items == 3
        assert costs.object_fields == 3

    def test_a_list_of_one_type_counts_no_positions(self):
        class Row(pydantic.BaseModel):
            a: int
            b: int

        class Rows(pydantic.BaseModel):
            rows: list[Row]

        assert schemas_module._model_costs(Rows).list_items == 0

    def test_nested_pydantic_dataclasses_count_each_object_once(self):
        @pydantic.dataclasses.dataclass
        class Inner:
            note: str

        @pydantic.dataclasses.dataclass
        class Outer:
            inner: Inner

        errors = FieldErrors()
        result = validate_args(Outer, {"inner": {"note": "n" * 1_000}})
        assert result.ok
        assert pydantic_can_report({"note": "x"}, Inner, errors)
        payload = {"inner": {"note": "n" * 1_000}}
        pydantic_can_report(payload["inner"], Inner, errors)
        size_after_inner = errors.pydantic_total.size
        pydantic_can_report(payload["inner"], Outer, errors)
        assert errors.pydantic_total.size == size_after_inner

    def test_optional_fields_do_not_count(self):
        class Row(pydantic.BaseModel):
            a: int
            b: int = 0
            c: int | None = None

        assert schemas_module._model_costs(Row).object_fields == 1

    def test_ordinary_rows_of_a_wide_model_pass(self):
        class Row(pydantic.BaseModel):
            field_a: int = 0
            field_b: int = 0
            field_c: int = 0
            field_d: int = 0
            field_e: int = 0
            field_f: int = 0
            field_g: int = 0
            field_h: int = 0
            field_i: int = 0
            field_j: int = 0

        class Rows(pydantic.BaseModel):
            rows: list[Row]

        row = {f"field_{letter}": 1 for letter in "abcdefghij"}
        assert self._passes(json.loads(json.dumps({"rows": [row] * 8_000})), Rows)

    def test_an_unfinished_model_is_rebuilt_before_it_is_measured(self):
        class Later(pydantic.BaseModel):
            text: pydantic.Json[list[int]] = []

        rebuilt = []

        def rebuild(**kwargs):
            rebuilt.append(kwargs)
            Later.__pydantic_complete__ = True

        Later.__pydantic_complete__ = False
        Later.model_rebuild = rebuild
        assert schemas_module._model_costs(Later).parses_json
        assert rebuilt == [{"raise_errors": False}]

    def test_required_object_fields_are_not_counted_for_lists(self):
        class Form(pydantic.BaseModel):
            pairs: list[tuple[float, float]]
            name: str
            mail: str
            city: str
            zip_code: str

        costs = schemas_module._model_costs(Form)
        assert (costs.object_fields, costs.list_items) == (5, 2)
        pairs = json.loads(json.dumps({"pairs": [[1.25, 2.25]] * 80_000}))
        assert self._passes(pairs, Form)

    def test_a_float_counts_a_flat_size(self):
        class Filled(pydantic.BaseModel):
            values: list[float]

        costs = schemas_module._model_costs(Filled)
        _, size = schemas_module._measure_paths({"values": [1e15] * 1_000}, costs, Filled, PydanticTotal())
        assert size < 6_500

    def test_a_schema_of_many_nested_models_can_be_read(self):
        inner: Any = int
        for _ in range(300):
            inner = pydantic.create_model("Level", value=(inner, ...))
        assert schemas_module._model_costs(inner).reports_per_value == 1

    def test_a_list_of_long_numbers_counts_their_real_size(self):
        class Filled(pydantic.BaseModel):
            values: list[int]

        costs = schemas_module._model_costs(Filled)
        _, size = schemas_module._measure_paths({"values": [123_456_789] * 1_000}, costs, Filled, PydanticTotal())
        assert 9_000 < size < 11_000

    def test_a_union_counts_once_per_member(self):
        class Plain(pydantic.BaseModel):
            value: dict[str, list[int] | list[bool] | list[float] | list[date]]

        class Tagged(pydantic.BaseModel):
            value: int

        assert schemas_module._model_costs(Plain).reports_per_value == 4
        assert schemas_module._model_costs(Tagged).reports_per_value == 1
        payload = {"value": {"a" * 16_000: ["x"] * 500}}
        assert self._passes(payload, Tagged)
        assert not self._passes(payload, Plain)

    def test_nested_unions_add_up_and_a_tagged_union_reports_one_member(self):
        class Cat(pydantic.BaseModel):
            kind: Literal["cat"]

        class Dog(pydantic.BaseModel):
            kind: Literal["dog"]

        class Nested(pydantic.BaseModel):
            value: list[int | str] | dict[str, int | str] | None

        class Tagged(pydantic.BaseModel):
            pet: Cat | Dog = pydantic.Field(discriminator="kind")

        assert schemas_module._model_costs(Nested).reports_per_value == 4
        assert schemas_module._model_costs(Tagged).reports_per_value == 1

    def test_a_recursive_model_has_an_answer(self):
        class Tree(pydantic.BaseModel):
            kids: "list[Tree | int]" = []

        Tree.model_rebuild(_types_namespace={"Tree": Tree})
        assert schemas_module._model_costs(Tree).reports_per_value >= 1

    def test_a_class_made_at_run_time_can_be_freed(self):
        made = pydantic.create_model("Made", value=(int, 0))
        schemas_module._model_costs(made)
        assert made in schemas_module._MODEL_COSTS
        reference = weakref.ref(made)
        del made
        gc.collect()
        assert reference() is None

    def test_a_json_field_in_a_tagged_union_counts(self):
        class Tagged(pydantic.BaseModel):
            value: typing.Annotated[
                typing.Annotated[pydantic.Json[list[int]], pydantic.Tag("text")]
                | typing.Annotated[int, pydantic.Tag("number")],
                pydantic.Discriminator(lambda value: "text" if isinstance(value, str) else "number"),
            ]

        assert schemas_module._model_costs(Tagged).parses_json

    def test_a_pydantic_dataclass_reports_field_messages(self):
        @pydantic.dataclasses.dataclass
        class Limits:
            size: int = pydantic.Field(gt=0)

        result = validate_args(Limits, {"size": -1})
        assert result.fields == {"size": "Input should be greater than 0"}

    def test_a_bug_in_a_pydantic_dataclass_validator_stays_in_its_call(self):
        @pydantic.dataclasses.dataclass
        class Broken:
            size: int

            @pydantic.field_validator("size")
            @classmethod
            def check(cls, _value):
                raise RuntimeError

        result = validate_args(Broken, {"size": 1})
        assert result.fields == {"_args": "The value could not be checked."}

    @pytest.mark.parametrize("limited", [False, True], ids=["copy", "limit"])
    def test_a_pydantic_dataclass_is_held_to_the_limit(self, limited, request):
        if limited:
            request.getfixturevalue("without_wrappers")

        # A class that forbids extra keys has no fixed bound on its errors,
        # so its copy is built with wrappers, which the fixture then refuses.
        @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(extra="forbid"))
        class Scores:
            scores: dict[str, list[typing.Annotated[int, pydantic.Field(gt=0)]]]

        result = validate_args(Scores, {"scores": {"a" * 56_000: [-1] * 14_000}})
        if limited:
            assert result.fields == {"_args": PATHS_TOO_LONG_MESSAGE}
        else:
            # The copy stops at the first bad item, and that one error is cheap.
            assert result.fields == {"scores." + "a" * 56_000 + ".0": "Input should be greater than 0"}

    @pytest.mark.parametrize("limited", [False, True], ids=["copy", "limit"])
    def test_a_nested_model_over_the_limit_is_reported_on_its_own_path(self, limited, request):
        if limited:
            request.getfixturevalue("without_wrappers")

        class Row(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(extra="forbid")
            tags: list[int]

        @dataclass
        class Data:
            rows: dict[str, Row]

        result = validate_args(Data, {"rows": {"a": {"tags": {"b" * 56_000: ["x"] * 14_000}}}})
        if limited:
            assert result.fields == {"rows.a": PATHS_TOO_LONG_MESSAGE}
        else:
            assert result.fields == {"rows.a.tags": "Input should be a valid list"}

    @pytest.mark.parametrize("limited", [False, True], ids=["copy", "limit"])
    def test_many_nested_models_share_the_limit(self, limited, request):
        if limited:
            request.getfixturevalue("without_wrappers")

        class Row(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(extra="forbid")
            scores: dict[str, list[int]]

        # A list of rows would stop at its first bad row, so the rows sit in
        # separate fields, each of which is checked.
        Data = make_dataclass("Data", [(f"row{index:03d}", Row) for index in range(100)])

        payload = {f"row{index:03d}": {"scores": {"." * 1_000: ["x"] * 2_000}} for index in range(100)}
        started = perf_counter()
        result = validate_args(Data, payload)
        assert perf_counter() - started < 1
        # Each row keeps one error, and the field messages are cut off at their own text limit.
        assert len(result.fields) + result.unlisted_fields == 100
        messages = [result.fields[name] for name in result.fields]
        if limited:
            # Rows past the running total get one refusal each, not 2,000 messages.
            refused = [message == PATHS_TOO_LONG_MESSAGE for message in messages]
            assert refused == [False] * 8 + [True] * 92
        else:
            assert all(message.startswith("Input should be a valid integer") for message in messages)
