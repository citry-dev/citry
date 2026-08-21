---
title: Format values
url: https://citry.dev/v/0.4.2/i18n/formatting/
description: "Define named locale-sensitive formats once and use them from Python, Citry templates, and browser code."
---
# Format values

A formatter turns a canonical application value into text for one locale. The
same amount may use different digits, decimal separators, currency placement,
or date order in different locales.

Citry keeps those choices in named profiles. Application code asks for a name
such as `account-balance`; it does not repeat low-level formatter options at
every call site.

## Define a format registry

Pass one `FormatRegistry` in the i18n engine settings:


```python
from citry import (
    Citry,
    CurrencyFormat,
    DateFormat,
    DateTimeFormat,
    FormatRegistry,
    ListFormat,
    NumberFormat,
    PercentFormat,
    RelativeTimeFormat,
    TimeFormat,
    UnitFormat,
)

formats = FormatRegistry(
    number={
        "measurement": NumberFormat(),
    },
    percent={
        "completion": PercentFormat(),
    },
    currency={
        "account-balance": CurrencyFormat(),
    },
    date={
        "invoice-date": DateFormat(length="long"),
    },
    time={
        "appointment-time": TimeFormat(length="short"),
    },
    datetime={
        "appointment": DateTimeFormat(
            length="medium",
            time_zone_name="short",
        ),
    },
    relative_time={
        "activity-age": RelativeTimeFormat(unit="day"),
    },
    list={
        "people": ListFormat(kind="and", length="wide"),
    },
    unit={
        "distance": UnitFormat(width="long"),
    },
)

app = Citry(
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US", "cs-CZ", "ar-EG"),
            "formats": formats,
        },
    },
)
```


Profile names are application-defined. They must use ASCII letters, digits,
`-`, or `_`. An unknown profile or a profile stored under the wrong category
raises an error.

The registry accepts new names under the supported categories. It is not a
plugin registry for arbitrary formatter implementations. The profile types
are closed so the Rust server and browser can apply the same semantic rule.

## Choose the date fields a profile displays

`DateFormat.fields` defaults to `"year_month_day"`. Use a narrower closed field
set when an interface needs a calendar heading, weekday, day number, or another
partial display without copying browser-specific formatter options:


```python
calendar_formats = FormatRegistry(
    date={
        "calendar-heading": DateFormat(fields="year_month", length="long"),
        "calendar-weekday": DateFormat(fields="weekday", length="medium"),
        "calendar-day": DateFormat(fields="day", length="short"),
        "calendar-date-label": DateFormat(
            fields="year_month_day_weekday",
            length="long",
        ),
    },
)
```


The supported values are `year`, `month`, `day`, `weekday`, `year_month`,
`month_day`, `day_weekday`, `month_day_weekday`, `year_month_day`, and
`year_month_day_weekday`. They describe calendar fields, not a fixed word order;
ICU4X and the browser still choose locale-appropriate order, names, digits, and
punctuation.

Parsing remains a complete date job. A profile with `input=DateInput(...)` must
keep `fields="year_month_day"`; display-only partial profiles do not claim that
Citry can parse a partial date.

## Use profiles from a component

Use `self.i18n.format` in Python:


```citry
from decimal import Decimal


class AccountBalance(Component):
    citry = app

    def template_data(self, kwargs, slots):
        return {
            "balance": self.i18n.format.currency(
                Decimal("1234.50"),
                "EUR",
                format="account-balance",
            ),
        }

    template = """
      <data>{{ balance }}</data>
    """
```


Templates receive the shorter `fmt` facade:


```citry-html
<data>{{ fmt.number(total, format="measurement") }}</data>
```


Outside a component, use the service bound to an explicit locale context:


```python
formatted = i18n.for_context(context).format.number(
    Decimal("1234.50"),
    format="measurement",
)
```


## Choose the correct value type

| Operation | Application value | Important rule |
|---|---|---|
| `number` | exact `int` or finite `Decimal` | Preserves exact decimal digits |
| `percent` | exact `int` or finite `Decimal` | The value is a ratio; `0.125` means 12.5% |
| `currency` | exact number plus a currency code | The code is three uppercase ASCII letters such as `EUR` |
| `date` | exact Python `date` | Uses the locale's selected calendar and profile length |
| `time` | zone-free Python `time` | Represents wall-clock fields, not an instant |
| `datetime` | aware Python `datetime` | Converts the instant into the context's explicit time zone |
| `relative_time` | exact number plus `unit="day"` | The current checked profile supports relative days |
| `list` | list or tuple of non-empty strings | Formats a conjunction or disjunction and isolates every item |
| `unit` | exact number plus a unit identifier | The unit stays explicit application data |

Citry rejects floats for exact numeric profiles. Convert application amounts to
`Decimal` before formatting when decimal precision matters.

## Keep percent values in one domain

Percent formatting uses ratio values:


```python
from decimal import Decimal

label = self.i18n.format.percent(
    Decimal("0.125"),
    format="completion",
)
```


The same `Decimal("0.125")` means 12.5 percent in every locale. The formatter
chooses the digits, decimal separator, spacing, and percent sign.

Parsing with the same profile returns the ratio again. See
[Parse localized input](/v/0.4.2/i18n/parsing/).

## Keep date, time, and datetime distinct

A date has calendar fields but no clock. A time has wall-clock fields but no
date or zone. A datetime formatter receives an aware instant and converts it
to the time zone in the context:


```python
context = i18n.make_context(
    locale="cs-CZ",
    time_zone="Europe/Prague",
)
formatter = i18n.for_context(context).format

text = formatter.datetime(
    aware_instant,
    format="appointment",
)
```


Calling `datetime()` without a context time zone is an error. Calling `time()`
with a zone-aware Python `time` is also an error, because a zone offset can
depend on the missing date.

## Use the same names in the browser

A client-enabled provider exposes the registry through `$i18n.format`:


```citry-html
<output
  x-text="$i18n.format.currency(
    '1234.50',
    'EUR',
    { format: 'account-balance' },
  )"
></output>
```


Browser exact decimal values use strings or safe exact integers. Date
formatting takes `{ year, month, day }`; time formatting takes wall-clock
fields; datetime formatting takes a JavaScript `Date` instant and the context's
time zone.

The server uses ICU4X and the browser uses `Intl`. Both consume the same named
profile and semantic input. Browser implementations may use different current
locale data for presentational details, so do not compare localized output as
an application identifier.