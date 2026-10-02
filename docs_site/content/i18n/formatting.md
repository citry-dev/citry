---
title: Format values
description: Define named locale-sensitive formats once and use them from Python, Citry templates, and browser code.
---

# Format values

The same number or date is written differently in each language. One
amount may be `€1,234.50` in American English and `1 234,50 €` in
Czech, with different digits, separators, currency placement, or date
order elsewhere.

Citry formats values for the current locale through format profiles. A
format profile is a named set of formatting options, such as
`account-balance` for currency amounts. You define each profile once,
then refer to it by name in Python, templates, and browser code.

## Define named formats

Create a `FormatRegistry` with your profiles, grouped by kind, and pass
it in the i18n settings:

```python
from citry import (
    Citry,
    CurrencyFormat,
    DateFormat,
    DateTimeFormat,
    FormatRegistry,
    NumberFormat,
    PercentFormat,
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
    datetime={
        "appointment": DateTimeFormat(
            length="medium",
            time_zone_name="short",
        ),
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

Each kind has its own profile class:

| Kind | Profile class | Options |
|---|---|---|
| `number` | `NumberFormat` | `input` |
| `percent` | `PercentFormat` | `input` |
| `currency` | `CurrencyFormat` | none |
| `date` | `DateFormat` | `fields`, `length`, `input` |
| `time` | `TimeFormat` | `length`, `input` |
| `datetime` | `DateTimeFormat` | `length`, `time_zone_name`, `input` |
| `relative_time` | `RelativeTimeFormat` | `unit` |
| `list` | `ListFormat` | `kind`, `length` |
| `unit` | `UnitFormat` | `width` |

All of these classes are importable from `citry`. The `input` option
says how to read what users type; see
[Parse localized input](/i18n/parsing/).

## Format a value

In component Python code, use `self.i18n.format`:

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

In a template, use `fmt`:

```citry-html
<data>{{ fmt.number(total, format="measurement") }}</data>
```

Outside a component, use a service for an explicit
[locale context](/i18n/locale-context/):

```python
i18n = app.extensions.get_extension("i18n")
formatted = i18n.for_context(context).format.number(
    Decimal("1234.50"),
    format="measurement",
)
```

## Pass the right kind of value

Each kind accepts a specific Python value:

| Operation | Value | Rule |
|---|---|---|
| `number` | `int` or finite `Decimal` | Keeps every decimal digit |
| `percent` | `int` or finite `Decimal` | A ratio: `0.125` means 12.5% |
| `currency` | `int` or `Decimal`, plus a currency code | A code of three uppercase letters, such as `EUR` |
| `date` | `date` | Uses the locale's calendar |
| `time` | `time` without a time zone | A time on the clock, not a moment |
| `datetime` | `datetime` with a time zone | Shown in the context's time zone |
| `relative_time` | `int` or `Decimal`, plus `unit="day"` | Days are the only unit |
| `list` | list or tuple of non-empty strings | Joins items with "and" or "or" |
| `unit` | `int` or `Decimal`, plus a unit name | You always pass the unit |

Floats are rejected with `TypeError`, because they cannot hold every
decimal amount exactly. Convert amounts to `Decimal` first.

## Pass percentages as ratios

A percent profile takes the ratio, not the number of percent:

```python
from decimal import Decimal

label = self.i18n.format.percent(
    Decimal("0.125"),
    format="completion",
)
```

`Decimal("0.125")` means 12.5% in every locale. The locale decides the
digits, the decimal separator, the spacing, and the percent sign.
Reading the value back with the same profile returns the ratio again.

## Format dates, times, and moments in time

Citry keeps three kinds apart:

- a `date` is a calendar day, with no clock time;
- a `time` is a clock time, with no date or time zone;
- a `datetime` is an exact moment, which Citry shows in the context's
  time zone.

Formatting a `datetime` therefore needs a context with a time zone:

```python
from citry.ext.i18n import make_context

i18n = app.extensions.get_extension("i18n")
context = make_context(
    app,
    locale="cs-CZ",
    time_zone="Europe/Prague",
)
formatter = i18n.for_context(context).format

text = formatter.datetime(
    aware_instant,
    format="appointment",
)
```

`datetime()` raises `ValueError` when the context has no time zone.
`time()` raises `ValueError` for a `time` that carries a time zone,
because the offset of a zone can depend on the date, which a `time`
does not have.

## Show only some parts of a date

By default a date profile shows year, month, and day. Set `fields` for
a calendar heading, a weekday name, or another partial date:

```python
calendar_formats = FormatRegistry(
    date={
        "calendar-heading": DateFormat(
            fields="year_month",
            length="long",
        ),
        "calendar-weekday": DateFormat(
            fields="weekday",
            length="medium",
        ),
        "calendar-day": DateFormat(fields="day", length="short"),
        "calendar-date-label": DateFormat(
            fields="year_month_day_weekday",
            length="long",
        ),
    },
)
```

The values are `year`, `month`, `day`, `weekday`, `year_month`,
`month_day`, `day_weekday`, `month_day_weekday`, `year_month_day`, and
`year_month_day_weekday`. They choose which parts appear, not their
order; the locale still decides the order, names, digits, and
punctuation.

A profile that also reads user input (`input=DateInput(...)`) must keep
the default `fields="year_month_day"`, because Citry only reads complete
dates.

## Format values in the browser

Inside a [browser i18n provider](/i18n/browser/), `$i18n.format` uses
the same profile names:

```citry-html
<output
  v-text="$i18n.format.currency(
    '1234.50',
    'EUR',
    { format: 'account-balance' },
  )"
></output>
```

In the browser, pass exact decimals as strings, or as integers small
enough for JavaScript to hold exactly. Pass a date as
`{ year, month, day }`, a time as its clock fields, and a moment as a
JavaScript `Date`, which is shown in the context's time zone.

## Rules for less common cases

### Errors from profile names and kinds

A profile name may contain ASCII letters, digits, `-`, and `_`. Any
other name raises `ValueError` when you create the registry. A profile
of the wrong class for its kind, such as a `PercentFormat` under
`number`, raises `TypeError` there too. Calling a profile name that does
not exist raises `ValueError`.

### Only the built-in kinds are supported

You can add any number of profiles under the kinds above, but you cannot
add a new kind or plug in your own formatter. The server and the browser
must apply the same rules, and that is only possible for the built-in
kinds.

### Browser output can differ slightly from server output

The server formats with ICU4X, the locale library Citry uses, and the
browser with its built-in `Intl`
API. Both apply the same profile, but a browser may have newer or older
locale data, so small details such as spacing can differ. Do not compare
formatted text to identify a value.
