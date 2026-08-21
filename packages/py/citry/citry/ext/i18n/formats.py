"""Typed named formatter profiles accepted by the built-in i18n extension."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Literal, cast

DateFormatFields = Literal[
    "year",
    "month",
    "day",
    "weekday",
    "year_month",
    "month_day",
    "day_weekday",
    "month_day_weekday",
    "year_month_day",
    "year_month_day_weekday",
]

_DATE_FORMAT_FIELDS = {
    "year",
    "month",
    "day",
    "weekday",
    "year_month",
    "month_day",
    "day_weekday",
    "month_day_weekday",
    "year_month_day",
    "year_month_day_weekday",
}


@dataclass(frozen=True, slots=True)
class NumberInput:
    """Declare the strict notation accepted by a named number profile."""

    notation: Literal["decimal", "decimal_or_scientific"] = "decimal"

    def __post_init__(self) -> None:
        if self.notation not in {"decimal", "decimal_or_scientific"}:
            raise ValueError(
                f"NumberInput notation must be 'decimal' or 'decimal_or_scientific'; got {self.notation!r}."
            )


@dataclass(frozen=True, slots=True)
class NumberFormat:
    """Use ICU4X's locale-default exact-decimal format and input grammar."""

    input: NumberInput = field(default_factory=NumberInput)

    def __post_init__(self) -> None:
        if type(self.input) is not NumberInput:
            raise TypeError(f"NumberFormat input must be NumberInput, got {type(self.input).__name__}.")


@dataclass(frozen=True, slots=True)
class PercentInput:
    """
    Choose whether a percent edit includes the locale's percent affix.

    Attributes:
        affix: ``"required"`` accepts the same affix that formatting emits.
            ``"omit"`` accepts only the localized number, which is useful when
            a control renders the affix outside its editable field.

    """

    affix: Literal["required", "omit"] = "required"

    def __post_init__(self) -> None:
        if self.affix not in {"required", "omit"}:
            raise ValueError(f"PercentInput affix must be 'required' or 'omit'; got {self.affix!r}.")


@dataclass(frozen=True, slots=True)
class PercentFormat:
    """
    Format a canonical ratio and optionally accept localized percent edits.

    A value of ``Decimal("0.125")`` represents 12.5 percent. Parsing returns
    the same ratio domain value.

    Attributes:
        input: The strict editing rule used by ``i18n.parse.percent()``.

    """

    input: PercentInput = field(default_factory=PercentInput)

    def __post_init__(self) -> None:
        if type(self.input) is not PercentInput:
            raise TypeError(f"PercentFormat input must be PercentInput, got {type(self.input).__name__}.")


@dataclass(frozen=True, slots=True)
class CurrencyFormat:
    """Use ICU4X's checked locale-default currency format."""


@dataclass(frozen=True, slots=True)
class DateInput:
    """
    Declare how a named date profile accepts editable input.

    Attributes:
        mode: ``"strict_text"`` accepts one localized date string.
            ``"segments"`` accepts named year, month, and day edit segments.
        two_digit_year_start: The first year in the selected calendar's
            explicit 100-year window. ``None`` requires a full year.

    """

    mode: Literal["strict_text", "segments"]
    two_digit_year_start: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"strict_text", "segments"}:
            raise ValueError(f"DateInput mode must be 'strict_text' or 'segments'; got {self.mode!r}.")
        if self.two_digit_year_start is not None and (
            type(self.two_digit_year_start) is not int or not 1 <= self.two_digit_year_start <= 9_900
        ):
            raise ValueError("DateInput two_digit_year_start must be an exact integer from 1 through 9900 or None.")


@dataclass(frozen=True, slots=True)
class DateFormat:
    """
    Format a date and optionally accept input through the same profile.

    Attributes:
        fields: The exact calendar fields included in display output.
        length: The locale-sensitive display length.
        input: The strict editing rule. ``None`` keeps the profile display-only.

    """

    fields: DateFormatFields = "year_month_day"
    length: Literal["short", "medium", "long"] = "medium"
    input: DateInput | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.fields, str) or self.fields not in _DATE_FORMAT_FIELDS:
            raise ValueError(f"DateFormat fields has an unsupported value {self.fields!r}.")
        if self.length not in {"short", "medium", "long"}:
            raise ValueError(f"DateFormat length must be 'short', 'medium', or 'long'; got {self.length!r}.")
        if self.input is not None and type(self.input) is not DateInput:
            raise TypeError(f"DateFormat input must be DateInput or None, got {type(self.input).__name__}.")
        if self.input is not None and self.fields != "year_month_day":
            raise ValueError("DateFormat input requires fields='year_month_day'.")


@dataclass(frozen=True, slots=True)
class TimeInput:
    """
    Declare how a named wall-clock time profile accepts editable input.

    `strict_text` accepts one locale-shaped string. `segments` accepts a
    [`TimeSegments`][citry.TimeSegments] value from a segmented control.
    """

    mode: Literal["strict_text", "segments"]

    def __post_init__(self) -> None:
        if self.mode not in {"strict_text", "segments"}:
            raise ValueError(f"TimeInput mode must be 'strict_text' or 'segments'; got {self.mode!r}.")


@dataclass(frozen=True, slots=True)
class TimeFormat:
    """
    Format a wall-clock time and optionally accept localized edits.

    Attributes:
        length: The locale-sensitive display length.
        input: The strict editing rule. ``None`` keeps the profile display-only.

    """

    length: Literal["short", "medium", "long"] = "medium"
    input: TimeInput | None = None

    def __post_init__(self) -> None:
        if self.length not in {"short", "medium", "long"}:
            raise ValueError(f"TimeFormat length must be 'short', 'medium', or 'long'; got {self.length!r}.")
        if self.input is not None and type(self.input) is not TimeInput:
            raise TypeError(f"TimeFormat input must be TimeInput or None, got {type(self.input).__name__}.")


@dataclass(frozen=True, slots=True)
class DateTimeInput:
    """
    Declare how a named local datetime profile accepts editable input.

    Attributes:
        mode: ``strict_text`` for one string or ``segments`` for named fields.
        two_digit_year_start: First year in an explicit 100-year window, or
            ``None`` to require a full year.

    """

    mode: Literal["strict_text", "segments"]
    two_digit_year_start: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"strict_text", "segments"}:
            raise ValueError(f"DateTimeInput mode must be 'strict_text' or 'segments'; got {self.mode!r}.")
        if self.two_digit_year_start is not None and (
            type(self.two_digit_year_start) is not int or not 1 <= self.two_digit_year_start <= 9_900
        ):
            raise ValueError(
                "DateTimeInput two_digit_year_start must be an exact integer from 1 through 9900 or None."
            )


@dataclass(frozen=True, slots=True)
class DateTimeFormat:
    """
    Format an instant after conversion to the context's explicit IANA zone.

    Attributes:
        length: The locale-sensitive date and time display length.
        time_zone_name: Whether and how to display the resolved zone name.
        input: The strict local-edit rule. ``None`` keeps the profile display-only.

    """

    length: Literal["short", "medium", "long"] = "medium"
    time_zone_name: Literal["none", "short", "long"] = "none"
    input: DateTimeInput | None = None

    def __post_init__(self) -> None:
        if self.length not in {"short", "medium", "long"}:
            raise ValueError(f"DateTimeFormat length must be 'short', 'medium', or 'long'; got {self.length!r}.")
        if self.time_zone_name not in {"none", "short", "long"}:
            raise ValueError(
                f"DateTimeFormat time_zone_name must be 'none', 'short', or 'long'; got {self.time_zone_name!r}."
            )
        if self.input is not None and type(self.input) is not DateTimeInput:
            raise TypeError(f"DateTimeFormat input must be DateTimeInput or None, got {type(self.input).__name__}.")


@dataclass(frozen=True, slots=True)
class RelativeTimeFormat:
    """Format a relative day count; the current checked unit is ``day``."""

    unit: Literal["day"] = "day"

    def __post_init__(self) -> None:
        if self.unit != "day":
            raise ValueError(f"RelativeTimeFormat currently supports only unit='day'; got {self.unit!r}.")


@dataclass(frozen=True, slots=True)
class ListFormat:
    """
    Format a conjunction or disjunction list.

    `kind` chooses “and” or “or”. `length` chooses the locale's wide, short,
    or narrow pattern.
    """

    kind: Literal["and", "or"] = "and"
    length: Literal["wide", "short", "narrow"] = "wide"

    def __post_init__(self) -> None:
        if self.kind not in {"and", "or"}:
            raise ValueError(f"ListFormat kind must be 'and' or 'or'; got {self.kind!r}.")
        if self.length not in {"wide", "short", "narrow"}:
            raise ValueError(f"ListFormat length must be 'wide', 'short', or 'narrow'; got {self.length!r}.")


@dataclass(frozen=True, slots=True)
class UnitFormat:
    """
    Format an exact value with an explicit CLDR unit identifier.

    Attributes:
        width: How fully ICU4X writes the unit name.

    """

    width: Literal["long", "short", "narrow"] = "long"

    def __post_init__(self) -> None:
        if self.width not in {"long", "short", "narrow"}:
            raise ValueError(f"UnitFormat width must be 'long', 'short', or 'narrow'; got {self.width!r}.")


@dataclass(frozen=True, slots=True)
class FormatRegistry:
    """
    Store the application's named formatter profiles.

    The profile names are application-defined. Each value uses one of Citry's
    checked profile types so the Rust server and browser can share the same
    contract.

    Attributes:
        number: Exact-decimal number profiles.
        percent: Ratio-based percent profiles and their input rules.
        currency: Currency profiles.
        date: Calendar-date profiles.
        time: Wall-clock time profiles.
        datetime: Instant and time-zone profiles.
        relative_time: Relative-time profiles.
        list: Conjunction and disjunction list profiles.
        unit: Standalone measurement-unit profiles.

    Example:
        Give call sites names that describe why they format a value::

            formats = FormatRegistry(
                number={
                    "measurement": NumberFormat(),
                },
                date={
                    "invoice-date": DateFormat(
                        length="long",
                    ),
                },
            )

            # Inside a component:
            text = self.i18n.format.number(
                meters,
                format="measurement",
            )

    """

    number: Mapping[str, NumberFormat] = field(default_factory=dict)
    percent: Mapping[str, PercentFormat] = field(default_factory=dict)
    currency: Mapping[str, CurrencyFormat] = field(default_factory=dict)
    date: Mapping[str, DateFormat] = field(default_factory=dict)
    time: Mapping[str, TimeFormat] = field(default_factory=dict)
    datetime: Mapping[str, DateTimeFormat] = field(default_factory=dict)
    relative_time: Mapping[str, RelativeTimeFormat] = field(default_factory=dict)
    list: Mapping[str, ListFormat] = field(default_factory=dict)
    unit: Mapping[str, UnitFormat] = field(default_factory=dict)

    def __post_init__(self) -> None:
        fields = (
            ("number", self.number, NumberFormat),
            ("percent", self.percent, PercentFormat),
            ("currency", self.currency, CurrencyFormat),
            ("date", self.date, DateFormat),
            ("time", self.time, TimeFormat),
            ("datetime", self.datetime, DateTimeFormat),
            ("relative_time", self.relative_time, RelativeTimeFormat),
            ("list", self.list, ListFormat),
            ("unit", self.unit, UnitFormat),
        )
        for kind, profiles, expected in fields:
            if type(profiles) is not dict:
                raise TypeError(f"FormatRegistry {kind} profiles must be an exact dict.")
            copied: dict[str, object] = {}
            for name, profile in profiles.items():
                if (
                    type(name) is not str
                    or not name
                    or not all(
                        character.isascii() and (character.isalnum() or character in "-_") for character in name
                    )
                ):
                    raise ValueError(
                        f"FormatRegistry {kind} profile names must be non-empty and use only "
                        "ASCII letters, digits, '-' and '_'."
                    )
                if type(profile) is not expected:
                    raise TypeError(
                        f"FormatRegistry {kind}[{name!r}] must be {expected.__name__}, got {type(profile).__name__}."
                    )
                copied[name] = profile
            object.__setattr__(self, kind, MappingProxyType(copied))

    def to_wire(self) -> dict[str, dict[str, dict[str, object]]]:
        return {
            "number": {
                name: {"input": {"notation": profile.input.notation}} for name, profile in sorted(self.number.items())
            },
            "percent": {
                name: {"input": {"affix": profile.input.affix}} for name, profile in sorted(self.percent.items())
            },
            "currency": {name: {} for name in sorted(self.currency)},
            "date": {
                name: {
                    "fields": profile.fields,
                    "length": profile.length,
                    "input": (
                        None
                        if profile.input is None
                        else {
                            "mode": profile.input.mode,
                            "two_digit_year_start": profile.input.two_digit_year_start,
                        }
                    ),
                }
                for name, profile in sorted(self.date.items())
            },
            "time": {
                name: {
                    "length": profile.length,
                    "input": None if profile.input is None else {"mode": profile.input.mode},
                }
                for name, profile in sorted(self.time.items())
            },
            "datetime": {
                name: {
                    "length": profile.length,
                    "time_zone_name": profile.time_zone_name,
                    "input": (
                        None
                        if profile.input is None
                        else {
                            "mode": profile.input.mode,
                            "two_digit_year_start": profile.input.two_digit_year_start,
                        }
                    ),
                }
                for name, profile in sorted(self.datetime.items())
            },
            "relative_time": {name: {"unit": profile.unit} for name, profile in sorted(self.relative_time.items())},
            "list": {
                name: {"kind": profile.kind, "length": profile.length} for name, profile in sorted(self.list.items())
            },
            "unit": {name: {"width": profile.width} for name, profile in sorted(self.unit.items())},
        }

    @property
    def revision(self) -> str:
        payload = json.dumps(self.to_wire(), ensure_ascii=False, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()


def format_registry_from_wire(value: object, *, source: str) -> FormatRegistry:
    """Build one checked registry from Citry's closed JSON profile shape."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must contain one JSON object.")  # noqa: TRY004 - malformed resource
    expected_kinds = {
        "number",
        "percent",
        "currency",
        "date",
        "time",
        "datetime",
        "relative_time",
        "list",
        "unit",
    }
    unknown = set(value) - expected_kinds
    if unknown:
        names = ", ".join(repr(name) for name in sorted(unknown, key=repr))
        raise ValueError(f"{source} contains unknown format profile categories: {names}.")

    def profiles(kind: str) -> Mapping[object, object]:
        raw = value.get(kind, {})
        if not isinstance(raw, Mapping):
            raise ValueError(f"{source}.{kind} must contain one JSON object.")  # noqa: TRY004 - malformed resource
        return raw

    def record(kind: str, name: object, raw: object, fields: set[str]) -> tuple[str, Mapping[object, object]]:
        if type(name) is not str:
            raise ValueError(f"{source}.{kind} profile names must be strings.")
        if not isinstance(raw, Mapping):
            raise ValueError(  # noqa: TRY004 - malformed resource
                f"{source}.{kind}.{name} must contain one JSON object."
            )
        extra = set(raw) - fields
        if extra:
            names = ", ".join(repr(field) for field in sorted(extra, key=repr))
            raise ValueError(f"{source}.{kind}.{name} contains unknown fields: {names}.")
        return name, raw

    def optional_input(raw: object, *, kind: str, name: str, datetime_input: bool = False) -> object:
        if raw is None:
            return None
        if not isinstance(raw, Mapping):
            raise ValueError(  # noqa: TRY004 - malformed resource
                f"{source}.{kind}.{name}.input must be an object or null."
            )
        allowed = {"mode", "two_digit_year_start"} if datetime_input else {"mode"}
        extra = set(raw) - allowed
        if extra:
            raise ValueError(f"{source}.{kind}.{name}.input contains unknown fields: {sorted(extra)!r}.")
        mode = raw.get("mode")
        if datetime_input:
            return DateTimeInput(
                mode=cast("Literal['strict_text', 'segments']", mode),
                two_digit_year_start=raw.get("two_digit_year_start"),
            )
        return TimeInput(mode=cast("Literal['strict_text', 'segments']", mode))

    number: dict[str, NumberFormat] = {}
    for raw_name, raw_profile in profiles("number").items():
        name, profile = record("number", raw_name, raw_profile, {"input"})
        raw_input = profile.get("input", {})
        if not isinstance(raw_input, Mapping) or set(raw_input) - {"notation"}:
            raise ValueError(f"{source}.number.{name}.input has an unsupported shape.")
        number[name] = NumberFormat(input=NumberInput(notation=raw_input.get("notation", "decimal")))

    percent: dict[str, PercentFormat] = {}
    for raw_name, raw_profile in profiles("percent").items():
        name, profile = record("percent", raw_name, raw_profile, {"input"})
        raw_input = profile.get("input", {})
        if not isinstance(raw_input, Mapping) or set(raw_input) - {"affix"}:
            raise ValueError(f"{source}.percent.{name}.input has an unsupported shape.")
        percent[name] = PercentFormat(input=PercentInput(affix=raw_input.get("affix", "required")))

    currency = {
        name: CurrencyFormat()
        for raw_name, raw_profile in profiles("currency").items()
        for name, _profile in (record("currency", raw_name, raw_profile, set()),)
    }

    date: dict[str, DateFormat] = {}
    for raw_name, raw_profile in profiles("date").items():
        name, profile = record("date", raw_name, raw_profile, {"fields", "length", "input"})
        raw_input = profile.get("input")
        if raw_input is None:
            parsed_input = None
        elif isinstance(raw_input, Mapping) and not set(raw_input) - {"mode", "two_digit_year_start"}:
            parsed_input = DateInput(
                mode=cast("Literal['strict_text', 'segments']", raw_input.get("mode")),
                two_digit_year_start=raw_input.get("two_digit_year_start"),
            )
        else:
            raise ValueError(f"{source}.date.{name}.input has an unsupported shape.")
        date[name] = DateFormat(
            fields=cast("DateFormatFields", profile.get("fields", "year_month_day")),
            length=cast("Literal['short', 'medium', 'long']", profile.get("length", "medium")),
            input=parsed_input,
        )

    time: dict[str, TimeFormat] = {}
    for raw_name, raw_profile in profiles("time").items():
        name, profile = record("time", raw_name, raw_profile, {"length", "input"})
        time[name] = TimeFormat(
            length=cast("Literal['short', 'medium', 'long']", profile.get("length", "medium")),
            input=cast(
                "TimeInput | None",
                optional_input(profile.get("input"), kind="time", name=name),
            ),
        )

    datetime_profiles: dict[str, DateTimeFormat] = {}
    for raw_name, raw_profile in profiles("datetime").items():
        name, profile = record("datetime", raw_name, raw_profile, {"length", "time_zone_name", "input"})
        datetime_profiles[name] = DateTimeFormat(
            length=cast("Literal['short', 'medium', 'long']", profile.get("length", "medium")),
            time_zone_name=cast(
                "Literal['none', 'short', 'long']",
                profile.get("time_zone_name", "none"),
            ),
            input=cast(
                "DateTimeInput | None",
                optional_input(
                    profile.get("input"),
                    kind="datetime",
                    name=name,
                    datetime_input=True,
                ),
            ),
        )

    relative_time = {
        name: RelativeTimeFormat(unit=cast("Literal['day']", profile.get("unit", "day")))
        for raw_name, raw_profile in profiles("relative_time").items()
        for name, profile in (record("relative_time", raw_name, raw_profile, {"unit"}),)
    }
    list_profiles = {
        name: ListFormat(
            kind=cast("Literal['and', 'or']", profile.get("kind", "and")),
            length=cast("Literal['wide', 'short', 'narrow']", profile.get("length", "wide")),
        )
        for raw_name, raw_profile in profiles("list").items()
        for name, profile in (record("list", raw_name, raw_profile, {"kind", "length"}),)
    }
    unit = {
        name: UnitFormat(width=cast("Literal['long', 'short', 'narrow']", profile.get("width", "long")))
        for raw_name, raw_profile in profiles("unit").items()
        for name, profile in (record("unit", raw_name, raw_profile, {"width"}),)
    }
    return FormatRegistry(
        number=number,
        percent=percent,
        currency=currency,
        date=date,
        time=time,
        datetime=datetime_profiles,
        relative_time=relative_time,
        list=list_profiles,
        unit=unit,
    )


def merge_format_registries(
    base: FormatRegistry,
    contributions: tuple[tuple[str, FormatRegistry], ...],
) -> FormatRegistry:
    """Merge immutable package profiles, rejecting every replacement."""
    merged = {kind: dict(getattr(base, kind)) for kind in base.to_wire()}
    owners = {kind: {name: "application" for name in values} for kind, values in merged.items()}
    for owner, registry in contributions:
        for kind, merged_profiles in merged.items():
            for name, profile in getattr(registry, kind).items():
                previous = owners[kind].get(name)
                if previous is not None:
                    raise ValueError(
                        f"i18n {kind} format profile {name!r} from catalog package {owner!r} collides with {previous}."
                    )
                merged_profiles[name] = profile
                owners[kind][name] = f"catalog package {owner!r}"
    return FormatRegistry(**merged)


__all__ = [
    "CurrencyFormat",
    "DateFormat",
    "DateInput",
    "DateTimeFormat",
    "DateTimeInput",
    "FormatRegistry",
    "ListFormat",
    "NumberFormat",
    "NumberInput",
    "PercentFormat",
    "PercentInput",
    "RelativeTimeFormat",
    "TimeFormat",
    "TimeInput",
    "UnitFormat",
    "format_registry_from_wire",
    "merge_format_registries",
]
