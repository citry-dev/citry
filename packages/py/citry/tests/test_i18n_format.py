"""Named ICU4X formatter profiles exposed through ``self.i18n.format`` and ``fmt``."""

# ruff: noqa: RUF001

from datetime import UTC, date, datetime, time
from decimal import Decimal

import pytest

from citry import (
    Citry,
    Component,
    CurrencyFormat,
    DateFormat,
    DateTimeFormat,
    FormatRegistry,
    ListFormat,
    NumberFormat,
    RelativeTimeFormat,
    TimeFormat,
)
from citry.ext.i18n import I18nRuntimeUnavailableError


def formats() -> FormatRegistry:
    return FormatRegistry(
        number={"measurement": NumberFormat()},
        currency={"money": CurrencyFormat()},
        date={"short": DateFormat(length="medium")},
        time={"clock": TimeFormat(length="medium")},
        datetime={
            "event": DateTimeFormat(length="medium"),
            "event-zone": DateTimeFormat(length="medium", time_zone_name="long"),
        },
        relative_time={"short": RelativeTimeFormat(unit="day")},
        list={"conjunction": ListFormat(kind="and", length="wide")},
    )


def configured_app() -> Citry:
    return Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": (
                    "en-US",
                    "ar-EG",
                    "cs-CZ",
                    "es",
                    "hi-IN-u-nu-deva",
                    "ja-JP",
                    "th-TH-u-ca-buddhist",
                ),
                "formats": formats(),
            }
        }
    )


def test_exact_decimal_and_currency_use_locale_digits_and_symbols() -> None:
    app = configured_app()
    i18n = app.extensions.get_extension("i18n")

    arabic = i18n.format_for(i18n.make_context(locale="ar-EG"))
    assert arabic.number(Decimal("9007199254740993.25"), format="measurement") == ("٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٣٫٢٥")
    currency = arabic.currency(Decimal("12.5"), "EUR", format="money")
    assert "١٢٫٥" in currency
    assert "€" in currency

    english = i18n.format_for(i18n.make_context(locale="en-US"))
    assert english.currency(Decimal("12.5"), "EUR", format="money") == "€12.50"
    assert english.currency(Decimal(12), "USD", format="money") == "$12.00"

    japanese = i18n.format_for(i18n.make_context(locale="ja-JP"))
    assert japanese.currency(Decimal("12.50"), "JPY", format="money") == "￥13"


def test_date_relative_time_and_list_use_named_profiles() -> None:
    app = configured_app()
    i18n = app.extensions.get_extension("i18n")

    buddhist = i18n.format_for(i18n.make_context(locale="th-TH-u-ca-buddhist"))
    assert "2569" in buddhist.date(date(2026, 8, 10), format="short")

    czech = i18n.format_for(i18n.make_context(locale="cs-CZ"))
    assert czech.relative_time(-3, unit="day", format="short") == "před 3 dny"

    spanish = i18n.format_for(i18n.make_context(locale="es"))
    assert spanish.list(["España", "Suiza", "Italia"], format="conjunction") == (
        "\u2068España\u2069, \u2068Suiza\u2069 e \u2068Italia\u2069"
    )


def test_time_is_wall_clock_only_and_datetime_converts_an_instant_with_pinned_tzdata() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    formatter = i18n.format_for(context)

    assert formatter.time(time(14, 5, 9), format="clock") == "2:05:09\u202fPM"
    instant = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    assert formatter.datetime(instant, format="event") == "Jan 15, 2026, 1:00:00\u202fPM"
    assert "Central European Standard Time" in formatter.datetime(instant, format="event-zone")
    assert context.tzdb_revision.startswith("tzdata:2026.3:sha256:")


def test_temporal_formatters_reject_implicit_or_ambiguous_time_zone_inputs() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    without_zone = i18n.format_for(i18n.make_context(locale="en-US"))
    with_zone = i18n.format_for(i18n.make_context(locale="en-US", time_zone="Europe/Prague"))
    naive = datetime(2026, 1, 15, 12, tzinfo=UTC).replace(tzinfo=None)

    with pytest.raises(ValueError, match="wall-clock fields only"):
        with_zone.time(time(12, tzinfo=UTC), format="clock")
    with pytest.raises(ValueError, match="aware datetime"):
        with_zone.datetime(naive, format="event")
    with pytest.raises(ValueError, match="requires time_zone"):
        without_zone.datetime(datetime(2026, 1, 15, 12, tzinfo=UTC), format="event")
    with pytest.raises(ValueError, match="Unknown IANA"):
        i18n.make_context(locale="en-US", time_zone="Europe/Definitely-Missing")


def test_template_datetime_reads_only_the_explicit_root_locale_context() -> None:
    app = configured_app()

    class Event(Component):
        citry = app

        class Kwargs:
            when: datetime

        template = """
            {{ fmt.datetime(when, format="event") }}
        """

    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    rendered = Event(when=datetime(2026, 7, 15, 12, tzinfo=UTC)).render(
        provides={"citry_i18n": context},
    )
    assert str(rendered).strip() == "Jul 15, 2026, 2:00:00\u202fPM"


def test_number_parser_uses_the_same_named_profile_and_locale_data() -> None:
    i18n = configured_app().extensions.get_extension("i18n")

    arabic = i18n.parse_for(i18n.make_context(locale="ar-EG"))
    parsed = arabic.number("٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٣٫٢٥", format="measurement")
    assert parsed.valid
    assert parsed.value == Decimal("9007199254740993.25")
    assert parsed.error is None

    devanagari = i18n.parse_for(i18n.make_context(locale="hi-IN-u-nu-deva"))
    assert devanagari.number("९,००,७१,९९,२५,४७,४०,९९३.२५", format="measurement").value == Decimal(
        "9007199254740993.25"
    )


def test_number_parser_preserves_incomplete_and_invalid_edits() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.parse_for(i18n.make_context(locale="en-US"))

    incomplete = parser.number("1,", format="measurement")
    assert incomplete.state == "incomplete"
    assert incomplete.value is None
    assert incomplete.input == "1,"

    invalid = parser.number("1,2345", format="measurement")
    assert invalid.state == "invalid"
    assert invalid.value is None
    assert invalid.error == "wrong_primary_group"


def test_component_number_parser_reads_the_explicit_root_context() -> None:
    app = configured_app()

    class Amount(Component):
        citry = app

        def template_data(self, kwargs, slots):
            parsed = self.i18n.parse.number(kwargs.text, format="measurement")
            return {"value": parsed.value}

        template = """
            {{ value }}
        """

        class Kwargs:
            text: str

    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="ar-EG")
    rendered = Amount(text="١٢٣٤٫٥").render(provides={"citry_i18n": context})
    assert str(rendered).strip() == "1234.5"


@pytest.mark.parametrize("hostile", ["unsafe\u202e", "first\nsecond", "first\u2029second"])
def test_list_formatter_rejects_values_that_can_escape_text_isolation(hostile: str) -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    with pytest.raises(ValueError, match=r"bidi controls|paragraph boundaries"):
        i18n.format.list([hostile, "safe"], format="conjunction")


def test_list_formatter_isolates_repeated_items_without_changing_locale_grammar() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    spanish = i18n.format_for(i18n.make_context(locale="es"))
    assert spanish.list(["Italia", "Italia"], format="conjunction") == ("\u2068Italia\u2069 e \u2068Italia\u2069")


def test_template_fmt_and_fluent_number_share_the_same_profile() -> None:
    app = Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "ar-EG",
                "locales": ("ar-EG",),
                "formats": formats(),
            }
        }
    )

    class Amount(Component):
        citry = app
        messages = '# @param {Decimal} $amount\namount = { NUMBER($amount, profile: "measurement") }'
        template = '{{ tr("amount", amount=amount) }}|{{ fmt.number(amount, format="measurement") }}'

        class Kwargs:
            amount: Decimal

    context = app.extensions.get_extension("i18n").make_context(locale="ar-EG")
    rendered = str(
        Amount(amount=Decimal("1234.5")).render(
            provides={"citry_i18n": context},
        )
    )
    assert rendered == "\u2068١٬٢٣٤٫٥\u2069|١٬٢٣٤٫٥"


def test_template_fmt_and_fluent_number_normalize_decimal_negative_zero_the_same_way() -> None:
    app = Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "formats": formats(),
            }
        }
    )

    class Amount(Component):
        citry = app
        messages = '# @param {Decimal} $amount\namount = { NUMBER($amount, profile: "measurement") }'
        template = '{{ tr("amount", amount=amount) }}|{{ fmt.number(amount, format="measurement") }}'

        class Kwargs:
            amount: Decimal

    assert str(Amount(amount=Decimal("-0.00"))) == "\u20680\u2069|0"


def test_unknown_profile_fails_before_message_runtime_is_published() -> None:
    app = configured_app()

    class Broken(Component):
        citry = app
        messages = '# @param {Decimal} $amount\namount = { NUMBER($amount, profile: "missing") }'

    with pytest.raises(ValueError, match="unknown number format profile"):
        Broken.get_messages()


def test_unratified_percent_and_unit_profiles_fail_plainly() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    with pytest.raises(I18nRuntimeUnavailableError, match="not checked yet"):
        i18n.format.percent(Decimal("0.5"), format="completion")
    with pytest.raises(I18nRuntimeUnavailableError, match="not checked yet"):
        i18n.format.unit(Decimal("1.5"), "meter", format="measurement")


def test_registry_defensively_copies_and_validates_profiles() -> None:
    source = {"default": NumberFormat()}
    registry = FormatRegistry(number=source)
    source["later"] = NumberFormat()

    assert tuple(registry.number) == ("default",)
    with pytest.raises(TypeError, match="must be NumberFormat"):
        FormatRegistry(number={"bad": object()})
    with pytest.raises(ValueError, match="ASCII letters"):
        FormatRegistry(number={"bad name": NumberFormat()})
