"""Typed named formatter profiles accepted by the built-in i18n extension."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class NumberFormat:
    """Use ICU4X's checked locale-default exact-decimal format."""


@dataclass(frozen=True, slots=True)
class CurrencyFormat:
    """Use ICU4X's checked locale-default currency format."""


@dataclass(frozen=True, slots=True)
class DateFormat:
    """Format year, month, and day with one checked display length."""

    length: Literal["short", "medium", "long"] = "medium"

    def __post_init__(self) -> None:
        if self.length not in {"short", "medium", "long"}:
            raise ValueError(f"DateFormat length must be 'short', 'medium', or 'long'; got {self.length!r}.")


@dataclass(frozen=True, slots=True)
class TimeFormat:
    """Format a wall-clock time without time-zone conversion."""

    length: Literal["short", "medium", "long"] = "medium"

    def __post_init__(self) -> None:
        if self.length not in {"short", "medium", "long"}:
            raise ValueError(f"TimeFormat length must be 'short', 'medium', or 'long'; got {self.length!r}.")


@dataclass(frozen=True, slots=True)
class DateTimeFormat:
    """Format an instant after conversion to the context's explicit IANA zone."""

    length: Literal["short", "medium", "long"] = "medium"
    time_zone_name: Literal["none", "short", "long"] = "none"

    def __post_init__(self) -> None:
        if self.length not in {"short", "medium", "long"}:
            raise ValueError(f"DateTimeFormat length must be 'short', 'medium', or 'long'; got {self.length!r}.")
        if self.time_zone_name not in {"none", "short", "long"}:
            raise ValueError(
                f"DateTimeFormat time_zone_name must be 'none', 'short', or 'long'; got {self.time_zone_name!r}."
            )


@dataclass(frozen=True, slots=True)
class RelativeTimeFormat:
    """Format a relative day count. More units need their own parity proof."""

    unit: Literal["day"] = "day"

    def __post_init__(self) -> None:
        if self.unit != "day":
            raise ValueError(f"RelativeTimeFormat currently supports only unit='day'; got {self.unit!r}.")


@dataclass(frozen=True, slots=True)
class ListFormat:
    """Format a conjunction or disjunction list."""

    kind: Literal["and", "or"] = "and"
    length: Literal["wide", "short", "narrow"] = "wide"

    def __post_init__(self) -> None:
        if self.kind not in {"and", "or"}:
            raise ValueError(f"ListFormat kind must be 'and' or 'or'; got {self.kind!r}.")
        if self.length not in {"wide", "short", "narrow"}:
            raise ValueError(f"ListFormat length must be 'wide', 'short', or 'narrow'; got {self.length!r}.")


@dataclass(frozen=True, slots=True)
class FormatRegistry:
    """
    Store the application's named formatter profiles.

    The profile names are application-defined. Each value uses one of Citry's
    checked profile types so the Rust server and browser can share the same
    contract.

    Attributes:
        number: Exact-decimal number profiles.
        currency: Currency profiles.
        date: Calendar-date profiles.
        time: Wall-clock time profiles.
        datetime: Instant and time-zone profiles.
        relative_time: Relative-time profiles.
        list: Conjunction and disjunction list profiles.

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
    currency: Mapping[str, CurrencyFormat] = field(default_factory=dict)
    date: Mapping[str, DateFormat] = field(default_factory=dict)
    time: Mapping[str, TimeFormat] = field(default_factory=dict)
    datetime: Mapping[str, DateTimeFormat] = field(default_factory=dict)
    relative_time: Mapping[str, RelativeTimeFormat] = field(default_factory=dict)
    list: Mapping[str, ListFormat] = field(default_factory=dict)

    def __post_init__(self) -> None:
        fields = (
            ("number", self.number, NumberFormat),
            ("currency", self.currency, CurrencyFormat),
            ("date", self.date, DateFormat),
            ("time", self.time, TimeFormat),
            ("datetime", self.datetime, DateTimeFormat),
            ("relative_time", self.relative_time, RelativeTimeFormat),
            ("list", self.list, ListFormat),
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

    def to_wire(self) -> dict[str, dict[str, dict[str, str]]]:
        return {
            "number": {name: {} for name in sorted(self.number)},
            "currency": {name: {} for name in sorted(self.currency)},
            "date": {name: {"length": profile.length} for name, profile in sorted(self.date.items())},
            "time": {name: {"length": profile.length} for name, profile in sorted(self.time.items())},
            "datetime": {
                name: {"length": profile.length, "time_zone_name": profile.time_zone_name}
                for name, profile in sorted(self.datetime.items())
            },
            "relative_time": {name: {"unit": profile.unit} for name, profile in sorted(self.relative_time.items())},
            "list": {
                name: {"kind": profile.kind, "length": profile.length} for name, profile in sorted(self.list.items())
            },
        }

    @property
    def revision(self) -> str:
        payload = json.dumps(self.to_wire(), ensure_ascii=False, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()


__all__ = [
    "CurrencyFormat",
    "DateFormat",
    "DateTimeFormat",
    "FormatRegistry",
    "ListFormat",
    "NumberFormat",
    "RelativeTimeFormat",
    "TimeFormat",
]
