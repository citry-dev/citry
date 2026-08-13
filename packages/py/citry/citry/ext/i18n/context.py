"""Immutable locale context values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import date, datetime, time
    from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LocaleContext:
    """
    All explicit render inputs that can change localized output.

    Attributes:
        locale: The selected canonical locale.
        fallback_locales: The ordered configured fallback chain.
        direction: The writing direction used by the render subtree.
        time_zone: The explicit IANA time zone, or ``None`` for zone-free work.
        tzdb_revision: The exact time-zone data revision.
        catalog_revision: The exact checked message graph revision.
        formats_revision: The exact named-profile registry revision.

    """

    locale: str
    fallback_locales: tuple[str, ...]
    direction: Literal["ltr", "rtl"]
    time_zone: str | None
    tzdb_revision: str
    catalog_revision: str
    formats_revision: str

    @property
    def identity(self) -> tuple[object, ...]:
        """Plain immutable data that identifies every input to localized output."""
        return (
            "citry-i18n-context",
            1,
            self.locale,
            self.fallback_locales,
            self.direction,
            self.time_zone,
            self.tzdb_revision,
            self.catalog_revision,
            self.formats_revision,
        )


@dataclass(frozen=True, slots=True)
class LocalizedText:
    """
    Resolved text plus the locale metadata needed by semantic wrappers.

    Attributes:
        text: The formatted message text.
        locale: The locale that supplied the selected pattern.
        direction: The selected pattern's writing direction.
        used_fallback: Whether resolution used a locale other than the request.

    """

    text: str
    locale: str
    direction: Literal["ltr", "rtl"]
    used_fallback: bool


@dataclass(frozen=True, slots=True)
class NumberParseResult:
    """
    One strict localized number edit without losing unfinished text.

    Attributes:
        input: The exact user edit.
        state: ``valid``, ``incomplete``, or ``invalid``.
        value: The canonical exact decimal when valid.
        error: A stable explanation for an invalid result, otherwise ``None``.

    """

    input: str
    state: Literal["valid", "incomplete", "invalid"]
    value: Decimal | None
    error: str | None

    @property
    def valid(self) -> bool:
        """Return whether the edit contains one complete canonical number."""
        return self.state == "valid"


@dataclass(frozen=True, slots=True)
class PercentParseResult:
    """
    Keep one localized percent edit and its canonical ratio separate.

    Attributes:
        input: The exact user edit.
        state: ``valid``, ``incomplete``, or ``invalid``.
        value: The canonical ratio when valid; ``0.125`` means 12.5 percent.
        error: A stable explanation for an invalid result, otherwise ``None``.

    """

    input: str
    state: Literal["valid", "incomplete", "invalid"]
    value: Decimal | None
    error: str | None

    @property
    def valid(self) -> bool:
        """Return whether the edit contains one complete percent value."""
        return self.state == "valid"


@dataclass(frozen=True, slots=True)
class DateSegments:
    """
    Hold the three editable fields from a segmented date control.

    Attributes:
        year: The localized calendar-year edit.
        month: The localized numeric month edit.
        day: The localized day-of-month edit.

    """

    year: str
    month: str
    day: str

    def __post_init__(self) -> None:
        for name in ("year", "month", "day"):
            value = getattr(self, name)
            if type(value) is not str:
                raise TypeError(f"DateSegments {name} must be an exact string, got {type(value).__name__}.")


@dataclass(frozen=True, slots=True)
class DateParseResult:
    """
    Keep one localized date edit and its canonical Python date separate.

    ``ambiguous`` reports an input that needs an explicit calendar decision.
    ``valid`` is the only state with a canonical `value`.
    """

    input: str | DateSegments
    state: Literal["valid", "incomplete", "invalid", "ambiguous"]
    value: date | None
    error: str | None

    @property
    def valid(self) -> bool:
        """Return whether the edit contains one complete calendar date."""
        return self.state == "valid"


@dataclass(frozen=True, slots=True)
class TimeSegments:
    """
    Hold editable fields from a segmented wall-clock time control.

    `second` and `day_period` are optional because the named profile decides
    whether those fields are present.
    """

    hour: str
    minute: str
    second: str | None = None
    day_period: str | None = None

    def __post_init__(self) -> None:
        for name in ("hour", "minute"):
            value = getattr(self, name)
            if type(value) is not str:
                raise TypeError(f"TimeSegments {name} must be an exact string, got {type(value).__name__}.")
        for name in ("second", "day_period"):
            value = getattr(self, name)
            if value is not None and type(value) is not str:
                raise TypeError(f"TimeSegments {name} must be an exact string or None, got {type(value).__name__}.")


@dataclass(frozen=True, slots=True)
class TimeParseResult:
    """
    Keep one localized time edit and its canonical wall-clock value separate.

    The result is a zone-free [`datetime.time`][datetime.time]. Converting it
    to an instant requires a date and time zone.
    """

    input: str | TimeSegments
    state: Literal["valid", "incomplete", "invalid"]
    value: time | None
    error: str | None

    @property
    def valid(self) -> bool:
        """Return whether the edit contains one complete wall-clock time."""
        return self.state == "valid"


@dataclass(frozen=True, slots=True)
class DateTimeSegments:
    """Combine named date and time fields from one local datetime control."""

    date: DateSegments
    time: TimeSegments

    def __post_init__(self) -> None:
        if type(self.date) is not DateSegments:
            raise TypeError(f"DateTimeSegments date must be an exact DateSegments, got {type(self.date).__name__}.")
        if type(self.time) is not TimeSegments:
            raise TypeError(f"DateTimeSegments time must be an exact TimeSegments, got {type(self.time).__name__}.")


@dataclass(frozen=True, slots=True)
class DateTimeParseResult:
    """
    Keep a local datetime edit separate from its resolved aware instant.

    An ``ambiguous`` daylight-saving fold returns both aware instants in
    `alternatives`. Pass ``fold="earlier"`` or ``fold="later"`` to the parser
    to resolve that choice explicitly.
    """

    input: str | DateTimeSegments
    state: Literal["valid", "incomplete", "invalid", "ambiguous"]
    value: datetime | None
    error: str | None
    alternatives: tuple[datetime, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether the edit resolved to one complete aware instant."""
        return self.state == "valid"
