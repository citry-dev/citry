"""
Tests for the events extension's data schemas: schema-class conversion,
validation of the wire args payload with its deliberately small coercion
table, the source-aware string binding of StringArgs payloads, structured
per-field errors, Pydantic wholesale delegation, and the neutral
UploadedFile type (docs/design/events.md sections 3.3 and 6.2).
"""

import io
import subprocess
import sys
import textwrap
from collections.abc import Mapping
from dataclasses import dataclass, is_dataclass
from dataclasses import field as dataclass_field
from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, TypeVar
from uuid import UUID

import pytest

from citry.ext.events import schemas as schemas_module
from citry.ext.events.files import UploadedFile
from citry.ext.events.schemas import (
    StringArgs,
    ValidationResult,
    convert_schema_class,
    declared_field_names,
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

    def test_dict_field_accepts_object_as_is(self):
        # Dicts are not in the coercion table: no per-key coercion happens,
        # even when the annotation is parametrized.
        result = validate_args(TypedDictField, {"blob": {"a": "not-coerced"}})
        assert result.ok
        assert result.value.blob == {"a": "not-coerced"}

    def test_dict_field_rejects_non_object(self):
        result = validate_args(TypedDictField, {"blob": 5})
        assert result.fields == {"blob": "Expected an object, got int."}

    def test_mapping_field_accepts_an_object_without_coercing_values(self):
        blob = MappingProxyType({"a": "not-coerced"})
        result = validate_args(TypedMappingField, {"blob": blob})

        assert result.ok
        assert result.value.blob is blob

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

    def test_unknown_keys_inside_list_rows_count(self):
        lines = [{"sku": "a", "qty": 1, f"x{index:02d}": 1} for index in range(25)]
        result = validate_args(Order, {"lines": lines})
        # List indexes sort in number order, so the first twenty rows are kept.
        assert list(result.fields) == [f"lines.{index}.x{index:02d}" for index in range(20)]
        assert result.unlisted_fields == 5

    @pytest.mark.parametrize(("count", "unlisted"), [(20, 0), (21, 1), (30, 10)])
    def test_bad_list_items_stop_at_twenty_per_field(self, count, unlisted):
        result = validate_args(TagsList, {"tags": ["x"] * count})
        # The earliest items are the ones kept, in number order.
        assert list(result.fields) == [f"tags.{index}" for index in range(min(count, 20))]
        assert set(result.fields.values()) == {"Expected int, got str."}
        assert result.unlisted_fields == unlisted

    def test_each_list_field_has_its_own_limit(self):
        class TwoLists:
            first: list[int]
            second: list[int]

        result = validate_args(TwoLists, {"first": ["x"] * 21, "second": ["x"] * 21})
        assert len([name for name in result.fields if name.startswith("first.")]) == 20
        assert len([name for name in result.fields if name.startswith("second.")]) == 20
        assert result.unlisted_fields == 2

    def test_list_item_errors_and_unknown_keys_are_limited_separately(self):
        result = validate_args(TagsList, {"tags": ["x"] * 30, **_unknown_keys(25)})
        assert [name for name in result.fields if name.startswith("tags.")] == [f"tags.{i}" for i in range(20)]
        assert [name for name in result.fields if name.startswith("u")] == _sorted_unknown(20)
        assert result.unlisted_fields == 15

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


@requires_pydantic
class TestPydanticItemErrorLimit:
    @pytest.mark.parametrize(("count", "unlisted"), [(20, 0), (21, 1)])
    def test_bad_list_items_stop_at_twenty(self, count, unlisted):
        class Tags(pydantic.BaseModel):
            tags: list[int]

        result = validate_args(Tags, {"tags": ["x"] * count})
        assert list(result.fields) == [f"tags.{index}" for index in range(min(count, 20))]
        assert result.unlisted_fields == unlisted

    @pytest.mark.parametrize(("count", "unlisted"), [(20, 0), (21, 1)])
    def test_bad_dict_values_stop_at_twenty(self, count, unlisted):
        class Scores(pydantic.BaseModel):
            scores: dict[str, int]
            name: int

        values = {f"k{index:02d}": "x" for index in range(count)}
        result = validate_args(Scores, {"scores": values, "name": "x"})
        # A scalar field's message is always listed beside the dict's.
        assert result.fields["name"].startswith("Input should be a valid integer")
        assert [name for name in result.fields if name != "name"] == [
            f"scores.k{index:02d}" for index in range(min(count, 20))
        ]
        assert result.unlisted_fields == unlisted

    def test_a_list_inside_a_nested_model_is_limited(self):
        class Inner(pydantic.BaseModel):
            values: list[int]

        class HasInner:
            inner: Inner

        result = validate_args(HasInner, {"inner": {"values": ["x"] * 25}})
        assert list(result.fields) == [f"inner.values.{index}" for index in range(20)]
        assert result.unlisted_fields == 5
