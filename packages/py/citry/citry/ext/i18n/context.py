"""Immutable locale context values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LocaleContext:
    """All explicit render inputs that can change localized output."""

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
    """Resolved text plus the locale metadata needed by semantic wrappers."""

    text: str
    locale: str
    direction: Literal["ltr", "rtl"]
    used_fallback: bool


@dataclass(frozen=True, slots=True)
class NumberParseResult:
    """One strict localized number edit without losing invalid or incomplete text."""

    input: str
    state: Literal["valid", "incomplete", "invalid"]
    value: Decimal | None
    error: str | None

    @property
    def valid(self) -> bool:
        """Return whether the edit contains one complete canonical number."""
        return self.state == "valid"
