"""Named ICU4X formatter profiles exposed through ``self.i18n.format`` and ``fmt``."""

# ruff: noqa: RUF001

from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest

from citry import (
    Citry,
    Component,
    CurrencyFormat,
    DateFormat,
    DateInput,
    DateSegments,
    DateTimeFormat,
    DateTimeInput,
    DateTimeSegments,
    FormatRegistry,
    ListFormat,
    NumberFormat,
    NumberInput,
    PercentFormat,
    PercentInput,
    RelativeTimeFormat,
    TimeFormat,
    TimeInput,
    TimeSegments,
    UnitFormat,
)
from citry.ext.i18n import I18nRuntimeUnavailableError


def formats() -> FormatRegistry:
    return FormatRegistry(
        number={
            "measurement": NumberFormat(),
            "scientific-edit": NumberFormat(
                input=NumberInput(notation="decimal_or_scientific"),
            ),
        },
        percent={
            "completion": PercentFormat(input=PercentInput(affix="required")),
            "completion-field": PercentFormat(input=PercentInput(affix="omit")),
        },
        currency={"money": CurrencyFormat()},
        date={
            "short": DateFormat(length="medium"),
            "date-text": DateFormat(
                length="short",
                input=DateInput(mode="strict_text"),
            ),
            "date-text-long": DateFormat(
                length="long",
                input=DateInput(mode="strict_text"),
            ),
            "date-window": DateFormat(
                length="short",
                input=DateInput(
                    mode="strict_text",
                    two_digit_year_start=1950,
                ),
            ),
            "date-segments": DateFormat(
                length="long",
                input=DateInput(mode="segments"),
            ),
        },
        time={
            "clock": TimeFormat(length="medium"),
            "time-text": TimeFormat(
                length="medium",
                input=TimeInput(mode="strict_text"),
            ),
            "time-segments": TimeFormat(
                length="medium",
                input=TimeInput(mode="segments"),
            ),
        },
        datetime={
            "event": DateTimeFormat(length="medium"),
            "event-zone": DateTimeFormat(length="medium", time_zone_name="long"),
            "datetime-text": DateTimeFormat(
                length="medium",
                input=DateTimeInput(mode="strict_text"),
            ),
            "datetime-segments": DateTimeFormat(
                length="medium",
                input=DateTimeInput(mode="segments"),
            ),
        },
        relative_time={"short": RelativeTimeFormat(unit="day")},
        list={"conjunction": ListFormat(kind="and", length="wide")},
        unit={"measurement": UnitFormat(width="long")},
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
                    "ja-JP-u-ca-japanese",
                    "fa-IR-u-ca-persian",
                    "th-TH-u-ca-buddhist",
                    "tr",
                ),
                "formats": formats(),
            }
        }
    )


def test_exact_decimal_and_currency_use_locale_digits_and_symbols() -> None:
    app = configured_app()
    i18n = app.extensions.get_extension("i18n")

    arabic = i18n.for_context(i18n.make_context(locale="ar-EG")).format
    assert arabic.number(Decimal("9007199254740993.25"), format="measurement") == ("٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٣٫٢٥")
    currency = arabic.currency(Decimal("12.5"), "EUR", format="money")
    assert "١٢٫٥" in currency
    assert "€" in currency

    english = i18n.for_context(i18n.make_context(locale="en-US")).format
    assert english.currency(Decimal("12.5"), "EUR", format="money") == "€12.50"
    assert english.currency(Decimal(12), "USD", format="money") == "$12.00"

    japanese = i18n.for_context(i18n.make_context(locale="ja-JP")).format
    assert japanese.currency(Decimal("12.50"), "JPY", format="money") == "￥13"


def test_percent_uses_ratio_values_and_locale_affix_placement() -> None:
    i18n = configured_app().extensions.get_extension("i18n")

    english = i18n.for_context(i18n.make_context(locale="en-US")).format
    assert english.percent(Decimal("0.125"), format="completion") == "12.5%"

    turkish = i18n.for_context(i18n.make_context(locale="tr")).format
    assert turkish.percent(Decimal("0.125"), format="completion") == "%12,5"

    arabic = i18n.for_context(i18n.make_context(locale="ar-EG")).format
    assert "١٢٫٥" in arabic.percent(Decimal("0.125"), format="completion")


def test_unit_keeps_the_domain_unit_explicit_and_uses_locale_plural_data() -> None:
    i18n = configured_app().extensions.get_extension("i18n")

    english = i18n.for_context(i18n.make_context(locale="en-US")).format
    assert english.unit(Decimal("1.5"), "meter", format="measurement") == "1.5 meters"

    arabic = i18n.for_context(i18n.make_context(locale="ar-EG")).format
    assert arabic.unit(Decimal(11), "meter", format="measurement") == "١١ مترًا"
    assert (
        arabic.unit(
            Decimal("9007199254740993.25"),
            "meter",
            format="measurement",
        )
        == "٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٣٫٢٥ متر"
    )


def test_date_relative_time_and_list_use_named_profiles() -> None:
    app = configured_app()
    i18n = app.extensions.get_extension("i18n")

    buddhist = i18n.for_context(i18n.make_context(locale="th-TH-u-ca-buddhist")).format
    assert "2569" in buddhist.date(date(2026, 8, 10), format="short")

    czech = i18n.for_context(i18n.make_context(locale="cs-CZ")).format
    assert czech.relative_time(-3, unit="day", format="short") == "před 3 dny"

    spanish = i18n.for_context(i18n.make_context(locale="es")).format
    assert spanish.list(["España", "Suiza", "Italia"], format="conjunction") == (
        "\u2068España\u2069, \u2068Suiza\u2069 e \u2068Italia\u2069"
    )


def test_time_is_wall_clock_only_and_datetime_converts_an_instant_with_pinned_tzdata() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    formatter = i18n.for_context(context).format

    assert formatter.time(time(14, 5, 9), format="clock") == "2:05:09\u202fPM"
    instant = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert formatter.datetime(instant, format="event") == "Jan 15, 2026, 1:00:00\u202fPM"
    assert "Central European Standard Time" in formatter.datetime(instant, format="event-zone")
    assert context.tzdb_revision.startswith("tzdata:2026.3:sha256:")


def test_temporal_formatters_reject_implicit_or_ambiguous_time_zone_inputs() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    without_zone = i18n.for_context(i18n.make_context(locale="en-US")).format
    with_zone = i18n.for_context(i18n.make_context(locale="en-US", time_zone="Europe/Prague")).format
    naive = datetime(2026, 1, 15, 12, tzinfo=timezone.utc).replace(tzinfo=None)

    with pytest.raises(ValueError, match="wall-clock fields only"):
        with_zone.time(time(12, tzinfo=timezone.utc), format="clock")
    with pytest.raises(ValueError, match="aware datetime"):
        with_zone.datetime(naive, format="event")
    with pytest.raises(ValueError, match="requires time_zone"):
        without_zone.datetime(datetime(2026, 1, 15, 12, tzinfo=timezone.utc), format="event")
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
    rendered = Event(when=datetime(2026, 7, 15, 12, tzinfo=timezone.utc)).render(
        provides={"citry_i18n": context},
    )
    assert str(rendered).strip() == "Jul 15, 2026, 2:00:00\u202fPM"


def test_number_parser_uses_the_same_named_profile_and_locale_data() -> None:
    i18n = configured_app().extensions.get_extension("i18n")

    arabic = i18n.for_context(i18n.make_context(locale="ar-EG")).parse
    parsed = arabic.number("٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٣٫٢٥", format="measurement")
    assert parsed.valid
    assert parsed.value == Decimal("9007199254740993.25")
    assert parsed.error is None

    devanagari = i18n.for_context(i18n.make_context(locale="hi-IN-u-nu-deva")).parse
    assert devanagari.number("९,००,७१,९९,२५,४७,४०,९९३.२५", format="measurement").value == Decimal(
        "9007199254740993.25"
    )


def test_number_parser_preserves_incomplete_and_invalid_edits() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="en-US")).parse

    incomplete = parser.number("1,", format="measurement")
    assert incomplete.state == "incomplete"
    assert incomplete.value is None
    assert incomplete.input == "1,"

    invalid = parser.number("1,2345", format="measurement")
    assert invalid.state == "invalid"
    assert invalid.value is None
    assert invalid.error == "wrong_primary_group"


def test_number_parser_accepts_exponents_only_when_the_profile_opts_in() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    english = i18n.for_context(i18n.make_context(locale="en-US")).parse
    arabic = i18n.for_context(i18n.make_context(locale="ar-EG")).parse

    assert english.number("1.25e3", format="scientific-edit").value == Decimal(1250)
    assert arabic.number("١٫٢٥e٣", format="scientific-edit").value == Decimal(1250)
    assert english.number("1e", format="scientific-edit").state == "incomplete"
    assert english.number("1e+", format="scientific-edit").state == "incomplete"
    assert english.number("1e3", format="measurement").state == "invalid"


def test_percent_parser_uses_the_profiles_declared_input_affix() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    english = i18n.for_context(i18n.make_context(locale="en-US")).parse

    required = english.percent("12.5%", format="completion")
    assert required.valid
    assert required.value == Decimal("0.125")

    unfinished = english.percent("12.5", format="completion")
    assert unfinished.state == "incomplete"
    assert unfinished.error == "missing_percent_affix"

    omitted = english.percent("12.5", format="completion-field")
    assert omitted.valid
    assert omitted.value == Decimal("0.125")
    assert english.percent("12.5%", format="completion-field").state == "invalid"


def test_percent_parser_round_trips_the_locale_affix_and_digits() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    context = i18n.make_context(locale="ar-EG")
    formatter = i18n.for_context(context).format
    parser = i18n.for_context(context).parse

    rendered = formatter.percent(Decimal("-0.125"), format="completion")
    parsed = parser.percent(rendered, format="completion")
    assert parsed.valid
    assert parsed.value == Decimal("-0.125")


@pytest.mark.parametrize(
    ("locale", "input_text"),
    [
        ("en-US", "8/10/2026"),
        ("cs-CZ", "10. 08. 2026"),
        ("ar-EG", "١٠/٨/٢٠٢٦"),
        ("hi-IN-u-nu-deva", "१०/८/२०२६"),
        ("th-TH-u-ca-buddhist", "10/8/2569"),
    ],
)
def test_strict_date_parser_uses_locale_order_digits_and_calendar(locale: str, input_text: str) -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale=locale)).parse

    parsed = parser.date(input_text, format="date-text")
    assert parsed.valid
    assert parsed.value == date(2026, 8, 10)
    assert parsed.input == input_text


def test_strict_date_parser_keeps_partial_and_invalid_edits_separate() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="en-US")).parse

    partial = parser.date("8/10/20", format="date-text")
    assert partial.state == "incomplete"
    assert partial.value is None

    impossible = parser.date("2/29/2025", format="date-text")
    assert impossible.state == "invalid"
    assert impossible.error == "invalid_date"


def test_segmented_date_parser_accepts_named_fields_without_guessing_their_order() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="th-TH-u-ca-buddhist")).parse
    segments = DateSegments(year="2569", month="8", day="10")

    parsed = parser.date_segments(segments, format="date-segments")
    assert parsed.valid
    assert parsed.value == date(2026, 8, 10)
    assert parsed.input is segments

    partial = parser.date_segments(
        DateSegments(year="", month="8", day="10"),
        format="date-segments",
    )
    assert partial.state == "incomplete"


@pytest.mark.parametrize(
    "locale",
    ["en-US", "cs-CZ", "fa-IR-u-ca-persian"],
)
def test_long_date_parser_round_trips_locale_month_names(locale: str) -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    context = i18n.make_context(locale=locale)
    rendered = i18n.for_context(context).format.date(
        date(2026, 8, 10),
        format="date-text-long",
    )

    parsed = i18n.for_context(context).parse.date(rendered, format="date-text-long")
    assert parsed.valid
    assert parsed.value == date(2026, 8, 10)


def test_two_digit_year_uses_the_profiles_explicit_calendar_year_window() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="en-US")).parse

    assert parser.date("8/10/49", format="date-window").value == date(2049, 8, 10)
    assert parser.date("8/10/50", format="date-window").value == date(1950, 8, 10)


def test_segmented_date_parser_supports_an_unambiguous_persian_calendar() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="fa-IR-u-ca-persian")).parse

    parsed = parser.date_segments(
        DateSegments(year="۱۴۰۵", month="۵", day="۱۹"),
        format="date-segments",
    )
    assert parsed.valid
    assert parsed.value == date(2026, 8, 10)


def test_date_parser_rejects_era_based_calendars_until_era_is_explicit() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="ja-JP-u-ca-japanese")).parse

    with pytest.raises(ValueError, match="era or leap-month fields"):
        parser.date_segments(
            DateSegments(year="8", month="8", day="10"),
            format="date-segments",
        )


@pytest.mark.parametrize("locale", ["en-US", "cs-CZ", "ar-EG"])
def test_time_parser_round_trips_the_named_profiles_locale_shape(locale: str) -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    context = i18n.make_context(locale=locale)
    rendered = i18n.for_context(context).format.time(time(14, 5, 9), format="time-text")

    parsed = i18n.for_context(context).parse.time(rendered, format="time-text")
    assert parsed.valid
    assert parsed.value == time(14, 5, 9)


def test_segmented_time_parser_keeps_day_period_explicit() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    english = i18n.for_context(i18n.make_context(locale="en-US")).parse
    czech = i18n.for_context(i18n.make_context(locale="cs-CZ")).parse

    english_result = english.time_segments(
        TimeSegments(hour="2", minute="05", second="09", day_period="PM"),
        format="time-segments",
    )
    assert english_result.value == time(14, 5, 9)
    czech_result = czech.time_segments(
        TimeSegments(hour="14", minute="05", second="09"),
        format="time-segments",
    )
    assert czech_result.value == time(14, 5, 9)


def test_datetime_parser_resolves_normal_times_and_requires_a_fold_choice() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    parser = i18n.for_context(context).parse
    formatter = i18n.for_context(context).format
    instant = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    rendered = formatter.datetime(instant, format="datetime-text")

    assert parser.datetime(rendered, format="datetime-text").value == instant

    fold_input = DateTimeSegments(
        date=DateSegments(year="2026", month="10", day="25"),
        time=TimeSegments(hour="2", minute="30", second="00", day_period="AM"),
    )
    ambiguous = parser.datetime_segments(fold_input, format="datetime-segments")
    assert ambiguous.state == "ambiguous"
    assert len(ambiguous.alternatives) == 2
    earlier = parser.datetime_segments(
        fold_input,
        format="datetime-segments",
        fold="earlier",
    )
    later = parser.datetime_segments(
        fold_input,
        format="datetime-segments",
        fold="later",
    )
    assert earlier.valid
    assert later.valid
    assert earlier.value is not None
    assert later.value is not None
    assert earlier.value < later.value


def test_datetime_parser_rejects_dst_gaps_and_missing_time_zones() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    gap_input = DateTimeSegments(
        date=DateSegments(year="2026", month="3", day="29"),
        time=TimeSegments(hour="2", minute="30", second="00", day_period="AM"),
    )
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    gap = i18n.for_context(context).parse.datetime_segments(
        gap_input,
        format="datetime-segments",
    )
    assert gap.state == "invalid"
    assert gap.error == "nonexistent_local_time"

    without_zone = i18n.for_context(i18n.make_context(locale="en-US")).parse
    with pytest.raises(ValueError, match="requires time_zone"):
        without_zone.datetime_segments(gap_input, format="datetime-segments")
    with pytest.raises(ValueError, match="fold must be"):
        i18n.for_context(context).parse.datetime_segments(
            gap_input,
            format="datetime-segments",
            fold="closest",
        )


def test_date_parser_rejects_the_wrong_operation_for_the_profile() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    parser = i18n.for_context(i18n.make_context(locale="en-US")).parse

    with pytest.raises(ValueError, match="strict_text"):
        parser.date("8/10/2026", format="date-segments")
    with pytest.raises(ValueError, match="segments"):
        parser.date_segments(
            DateSegments(year="2026", month="8", day="10"),
            format="date-text",
        )
    with pytest.raises(ValueError, match="does not declare an input mode"):
        parser.date("8/10/2026", format="short")
    with pytest.raises(ValueError, match="does not declare an input mode"):
        parser.time("2:05:09 PM", format="clock")
    with pytest.raises(ValueError, match="segments"):
        parser.time_segments(
            TimeSegments(hour="2", minute="05", second="09", day_period="PM"),
            format="time-text",
        )


def test_component_number_parser_reads_the_explicit_root_context() -> None:
    app = configured_app()

    class Amount(Component):
        citry = app

        class Kwargs:
            text: str

        def template_data(self, kwargs, slots):
            parsed = self.i18n.parse.number(kwargs.text, format="measurement")
            return {"value": parsed.value}

        template = """
            {{ value }}
        """

    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="ar-EG")
    rendered = Amount(text="١٢٣٤٫٥").render(provides={"citry_i18n": context})
    assert str(rendered).strip() == "1234.5"


@pytest.mark.parametrize("hostile", ["unsafe\u202e", "first\nsecond", "first\u2029second"])
def test_list_formatter_rejects_values_that_can_escape_text_isolation(hostile: str) -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    service = i18n.for_context(i18n.make_context())
    with pytest.raises(ValueError, match=r"bidi controls|paragraph boundaries"):
        service.format.list([hostile, "safe"], format="conjunction")


def test_list_formatter_isolates_repeated_items_without_changing_locale_grammar() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    spanish = i18n.for_context(i18n.make_context(locale="es")).format
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

        class Kwargs:
            amount: Decimal

        template = """
            {{ tr("amount", amount=amount) }}|{{ fmt.number(amount, format="measurement") }}
        """

        messages = """
            # @param {Decimal} $amount
            amount = { NUMBER($amount, profile: "measurement") }
        """

    context = app.extensions.get_extension("i18n").make_context(locale="ar-EG")
    rendered = str(
        Amount(amount=Decimal("1234.5")).render(
            provides={"citry_i18n": context},
        )
    )
    assert rendered.strip() == "\u2068١٬٢٣٤٫٥\u2069|١٬٢٣٤٫٥"


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

        class Kwargs:
            amount: Decimal

        template = """
            {{ tr("amount", amount=amount) }}|{{ fmt.number(amount, format="measurement") }}
        """

        messages = """
            # @param {Decimal} $amount
            amount = { NUMBER($amount, profile: "measurement") }
        """

    assert str(Amount(amount=Decimal("-0.00"))).strip() == "\u20680\u2069|0"


def test_unknown_profile_fails_before_message_runtime_is_published() -> None:
    app = configured_app()

    class Broken(Component):
        citry = app

        messages = """
            # @param {Decimal} $amount
            amount = { NUMBER($amount, profile: "missing") }
        """

    with pytest.raises(ValueError, match="unknown number format profile"):
        Broken.get_messages()


def test_free_form_unit_parser_remains_outside_the_public_contract() -> None:
    i18n = configured_app().extensions.get_extension("i18n")
    service = i18n.for_context(i18n.make_context())
    with pytest.raises(I18nRuntimeUnavailableError, match="not available"):
        service.parse.unit("1.5 meters", format="measurement")


def test_registry_defensively_copies_and_validates_profiles() -> None:
    source = {"default": NumberFormat()}
    registry = FormatRegistry(number=source)
    source["later"] = NumberFormat()

    assert tuple(registry.number) == ("default",)
    with pytest.raises(TypeError, match="must be NumberFormat"):
        FormatRegistry(number={"bad": object()})
    with pytest.raises(ValueError, match="ASCII letters"):
        FormatRegistry(number={"bad name": NumberFormat()})
    with pytest.raises(ValueError, match="affix"):
        PercentInput(affix="optional")
    with pytest.raises(ValueError, match="notation"):
        NumberInput(notation="engineering")
    with pytest.raises(ValueError, match="mode"):
        DateInput(mode="natural_language")
    with pytest.raises(ValueError, match="two_digit_year_start"):
        DateInput(mode="strict_text", two_digit_year_start=True)
    with pytest.raises(ValueError, match="mode"):
        TimeInput(mode="natural_language")
    with pytest.raises(ValueError, match="two_digit_year_start"):
        DateTimeInput(mode="segments", two_digit_year_start=9_901)
    with pytest.raises(ValueError, match="width"):
        UnitFormat(width="verbose")
