from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from importlib import metadata
from pathlib import Path
from typing import Any
from zoneinfo import TZPATH, ZoneInfo

import babel
import icu
import icu._icu_ as icu_extension
import tzdata
from babel import Locale, dates, lists, numbers, units
from babel.core import get_cldr_version

LOCALES = (
    "en-US",
    "cs-CZ",
    "ar-EG",
    "ru-RU",
    "pl-PL",
    "ja-JP",
    "az-Latn",
    "az-Arab",
    "hi-IN-u-nu-deva",
    "th-TH-u-ca-buddhist",
)
PLURAL_INPUTS = (0, 1, 2, Decimal("1.5"), Decimal("2.5"), 5, 11, 21, 101)
INSTANT = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)


def _babel_locale(tag: str) -> Locale:
    return Locale.parse(tag.split("-u-")[0], sep="-")


def _numbering_system(tag: str) -> str:
    if tag == "ar-EG":
        return "default"
    if tag == "hi-IN-u-nu-deva":
        return "deva"
    return "latn"


def _babel_result(tag: str) -> dict[str, Any]:
    locale = _babel_locale(tag)
    numbering_system = _numbering_system(tag)
    prague = ZoneInfo("Europe/Prague")
    local_instant = INSTANT.astimezone(prague)
    return {
        "resolved": {
            "calendar": "gregory",
            "locale": str(locale).replace("_", "-"),
            "numbering_system": numbering_system,
        },
        "decimal": numbers.format_decimal(Decimal("1234.5"), locale=locale, numbering_system=numbering_system),
        "currency": numbers.format_currency(
            Decimal("1234.5"), "EUR", locale=locale, numbering_system=numbering_system
        ),
        "percent": numbers.format_percent(Decimal("0.56"), locale=locale, numbering_system=numbering_system),
        "unit": units.format_unit(Decimal("1234.5"), "kilometer", length="short", locale=locale),
        "list": lists.format_list(["A", "B", "C"], locale=locale),
        "relative_day": dates.format_timedelta(timedelta(days=-3), add_direction=True, locale=locale),
        "date": dates.format_date(local_instant.date(), format="medium", locale=locale),
        "plurals": {str(value): str(locale.plural_form(value)) for value in PLURAL_INPUTS},
    }


def _icu_result(tag: str) -> dict[str, Any]:
    locale = icu.Locale.forLanguageTag(tag)
    decimal = icu.NumberFormatter.with_().precision(icu.Precision.maxFraction(3)).locale(locale)
    currency = icu.NumberFormatter.with_().unit(icu.CurrencyUnit("EUR")).locale(locale)
    percent = icu.NumberFormatter.with_().unit(icu.NoUnit.percent()).scale(icu.Scale.powerOfTen(2)).locale(locale)
    unit = (
        icu.NumberFormatter.with_()
        .unit(icu.MeasureUnit.createKilometer())
        .unitWidth(icu.UNumberUnitWidth.SHORT)
        .precision(icu.Precision.maxFraction(1))
        .locale(locale)
    )
    date = icu.DateFormat.createDateInstance(icu.DateFormat.MEDIUM, locale)
    date.setTimeZone(icu.TimeZone.createTimeZone("Europe/Prague"))
    plural = icu.PluralRules.forLocale(locale)
    calendar = date.getCalendar().getType()
    return {
        "resolved": {
            "calendar": calendar,
            "locale": locale.toLanguageTag(),
            "numbering_system": _icu_numbering_system(locale),
        },
        "decimal": decimal.formatDouble(1234.5),
        "currency": currency.formatDouble(1234.5),
        "percent": percent.formatDouble(0.56),
        "unit": unit.formatDouble(1234.5),
        "list": icu.ListFormatter.createInstance(locale).format(("A", "B", "C")),
        "relative_day": icu.RelativeDateTimeFormatter(locale).formatNumeric(-3, icu.URelativeDateTimeUnit.DAY),
        "date": date.format(INSTANT.timestamp()),
        "plurals": {str(value): plural.select(float(value)) for value in PLURAL_INPUTS},
    }


def _icu_numbering_system(locale: icu.Locale) -> str:
    formatted = icu.NumberFormatter.withLocale(locale)
    rendered = formatted.formatInt(123)
    if "١٢٣" in rendered:
        return "arab"
    if "१२३" in rendered:
        return "deva"
    return "latn"


def _babel_parse(text: str, tag: str, numbering_system: str) -> dict[str, Any]:
    try:
        value = numbers.parse_decimal(
            text,
            locale=_babel_locale(tag),
            strict=True,
            numbering_system=numbering_system,
        )
        return {"accepted": True, "value": str(value)}
    except numbers.NumberFormatError as error:
        return {"accepted": False, "error": type(error).__name__}


def _icu_parse(text: str, tag: str) -> dict[str, Any]:
    formatter = icu.NumberFormat.createInstance(icu.Locale.forLanguageTag(tag))
    formatter.setLenient(False)
    position = icu.ParsePosition(0)
    value = formatter.parse(text, position)
    accepted = position.getIndex() == len(text) and position.getErrorIndex() == -1
    return {
        "accepted": accepted,
        "consumed": position.getIndex(),
        "value": str(value) if accepted else None,
    }


def _classify_wall_time(value: datetime, zone_name: str) -> dict[str, Any]:
    zone = ZoneInfo(zone_name)
    candidates: list[dict[str, str | int]] = []
    for fold in (0, 1):
        aware = value.replace(tzinfo=zone, fold=fold)
        instant = aware.astimezone(timezone.utc)
        round_trip = instant.astimezone(zone).replace(tzinfo=None)
        if round_trip == value:
            candidates.append(
                {
                    "fold": fold,
                    "instant": instant.isoformat(),
                    "offset": str(aware.utcoffset()),
                }
            )
    unique = {(candidate["instant"], candidate["offset"]) for candidate in candidates}
    if not unique:
        kind = "gap"
    elif len(unique) == 2:
        kind = "fold"
    else:
        kind = "valid"
    return {"kind": kind, "candidates": candidates}


def _tree_bytes(package: str) -> int:
    root = Path(metadata.distribution(package).locate_file(""))
    package_root = root / ("icu" if package == "PyICU" else package.lower())
    return sum(
        path.stat().st_size
        for path in package_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    )


def _linked_icu_artifacts() -> dict[str, int]:
    extension = Path(icu_extension.__file__)
    otool = shutil.which("otool")
    if otool is None:
        raise RuntimeError("otool is required for the recorded macOS artifact audit")
    process = subprocess.run(
        [otool, "-L", str(extension)],
        check=True,
        capture_output=True,
        text=True,
    )
    artifacts = {extension.name: extension.stat().st_size}
    for line in process.stdout.splitlines()[1:]:
        linked_path = Path(line.strip().split(" ", 1)[0])
        if linked_path.name.startswith("libicu") and linked_path.exists():
            artifacts[linked_path.name] = linked_path.stat().st_size
    return artifacts


def collect() -> dict[str, Any]:
    parse_cases = {
        "en-US": ("1,234.5", "latn"),
        "cs-CZ": ("1\u00a0234,5", "latn"),
        "ar-EG": ("\u0661\u066c\u0662\u0663\u0664\u066b\u0665", "default"),
        "hi-IN-u-nu-deva": ("\u0967,\u0968\u0969\u096a.\u096b", "deva"),
    }
    return {
        "runtime": {
            "python": platform_python_version(),
            "babel": babel.__version__,
            "babel_cldr": get_cldr_version(),
            "pyicu": icu.VERSION,
            "icu": icu.ICU_VERSION,
            "unicode": icu.UNICODE_VERSION,
            "tzdata": tzdata.__version__,
            "zoneinfo_tzpath": list(TZPATH),
        },
        "babel": {tag: _babel_result(tag) for tag in LOCALES},
        "pyicu": {tag: _icu_result(tag) for tag in LOCALES},
        "exact_decimal": {
            "babel": {
                value: numbers.format_decimal(Decimal(value), locale="en_US", decimal_quantization=False)
                for value in ("9007199254740993", "-0", "1.2300")
            },
            "pyicu": {
                value: icu.NumberFormatter.withLocale(icu.Locale("en-US")).formatDecimal(value.encode("ascii"))
                for value in ("9007199254740993", "-0", "1.2300")
            },
        },
        "parsing": {
            tag: {
                "babel": _babel_parse(text, tag, numbering_system),
                "pyicu": _icu_parse(text, tag),
            }
            for tag, (text, numbering_system) in parse_cases.items()
        },
        "locale_extensions": {
            "babel_accepts_unicode_extension": _babel_accepts_extension(),
            "pyicu_devanagari_numbering": _icu_result("hi-IN-u-nu-deva")["resolved"]["numbering_system"],
            "pyicu_thai_calendar": _icu_result("th-TH-u-ca-buddhist")["resolved"]["calendar"],
        },
        "locale_data_fallback_probe": {
            "az-Arab_raw": _icu_result("az-Arab"),
            "az_base_language": _icu_result("az"),
        },
        "wall_times": {
            "prague_gap": _classify_wall_time(
                datetime(2026, 3, 29, 2, 30),  # noqa: DTZ001 - local wall input
                "Europe/Prague",
            ),
            "prague_fold": _classify_wall_time(
                datetime(2026, 10, 25, 2, 30),  # noqa: DTZ001 - local wall input
                "Europe/Prague",
            ),
            "new_york_gap": _classify_wall_time(
                datetime(2026, 3, 8, 2, 30),  # noqa: DTZ001 - local wall input
                "America/New_York",
            ),
            "new_york_fold": _classify_wall_time(
                datetime(2026, 11, 1, 1, 30),  # noqa: DTZ001 - local wall input
                "America/New_York",
            ),
        },
        "installed_tree_bytes": {
            "babel": _tree_bytes("Babel"),
            "pyicu_wrapper": _tree_bytes("PyICU"),
            "tzdata": _tree_bytes("tzdata"),
        },
        "pyicu_runtime_artifact_bytes": _linked_icu_artifacts(),
    }


def _babel_accepts_extension() -> bool:
    try:
        Locale.parse("hi-IN-u-nu-deva", sep="-")
    except (ValueError, TypeError):
        return False
    return True


def platform_python_version() -> str:
    return ".".join(str(part) for part in sys.version_info[:3])
