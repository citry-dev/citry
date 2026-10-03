---
title: Parse localized input
description: Convert strict locale-sensitive form edits into canonical numbers, dates, times, and instants without guessing free-form prose.
---

# Parse localized input

Users type numbers and dates the way their language writes them. A Czech
user enters `1234,5`, an American user `1234.5`. Your code needs the
same `Decimal("1234.5")` from both.

Citry reads this input with the same [format profile](/i18n/formatting/)
you use to display the value. A profile can say which input it accepts,
and the parser accepts only that: the locale's own digits, separators,
and field order. It does not guess.

## Read a number

Call `self.i18n.parse.number()` with the text and a profile name:

```python
result = self.i18n.parse.number(
    raw_amount,
    format="measurement",
)

if result.valid:
    save_amount(result.value)
else:
    show_edit_again(result.input, result.error)
```

A number result keeps the user's exact text in `input` and reports one
of three states:

- `valid`: `value` holds the number as a `Decimal`;
- `incomplete`: more typing could make it valid, as with a trailing
  decimal separator; and
- `invalid`: the text does not match the profile.

While the user is still typing, leave their text in the field. Do not
replace it with `value`; use `value` in your own logic once the result
is valid.

Outside a component, use `parse` on a service for an explicit locale
context, as in the datetime example below.

## Accept number formats

Every `NumberFormat` accepts plain decimal numbers by default. To also
accept scientific notation, set `NumberInput`:

```python
from citry import FormatRegistry, NumberFormat, NumberInput

formats = FormatRegistry(
    number={
        "measurement": NumberFormat(),
        "scientific-measurement": NumberFormat(
            input=NumberInput(
                notation="decimal_or_scientific",
            ),
        ),
    },
)
```

The parser checks the locale's digits, decimal separator, grouping
separator and group sizes, and signs. A separator or digit from another
locale is invalid.

With `decimal_or_scientific`, the exponent marker is ASCII `e` or `E`.
The exponent digits still use the locale's digits.

## Read percentages

`PercentInput` says whether the user types the percent sign:

```python
from citry import FormatRegistry, PercentFormat, PercentInput

formats = FormatRegistry(
    percent={
        "completion": PercentFormat(
            input=PercentInput(affix="required"),
        ),
        "completion-field": PercentFormat(
            input=PercentInput(affix="omit"),
        ),
    },
)
```

Use `required` when the percent sign is part of the typed text. Use
`omit` when the form shows the sign outside the input field.

Both return a ratio: 12.5 percent comes back as `Decimal("0.125")`.

## Read dates

A date profile only reads input when you give it a `DateInput`. Choose
one of two modes:

```python
from citry import DateFormat, DateInput, FormatRegistry

formats = FormatRegistry(
    date={
        "invoice-date": DateFormat(
            length="short",
            input=DateInput(mode="strict_text"),
        ),
        "birthday-fields": DateFormat(
            length="long",
            input=DateInput(mode="segments"),
        ),
    },
)
```

- `strict_text` reads one text field. It accepts the field order,
  separators, digits, and month names this profile displays in the
  locale, and nothing from other locales.
- `segments` reads a form that already has separate year, month, and
  day fields.

For `segments`, pass each field by name, whatever order the form shows
them in:

```python
from citry import DateSegments

result = self.i18n.parse.date_segments(
    DateSegments(
        year=year_edit,
        month=month_edit,
        day=day_edit,
    ),
    format="birthday-fields",
)
```

A valid result holds a Python `date`. Citry reads the fields in the
locale's calendar and reports an error for unclear or unsupported input
instead of guessing.

## Read times

Time profiles use the same two modes, with `TimeInput`:

```python
from citry import (
    FormatRegistry,
    TimeFormat,
    TimeInput,
    TimeSegments,
)

formats = FormatRegistry(
    time={
        "appointment-time": TimeFormat(
            length="medium",
            input=TimeInput(mode="segments"),
        ),
    },
)

result = self.i18n.parse.time_segments(
    TimeSegments(
        hour="2",
        minute="30",
        second="00",
        day_period="PM",
    ),
    format="appointment-time",
)
```

A valid result holds a Python `time` without a time zone. To get an
exact moment, you also need a date and a zone; read both together as a
datetime.

## Read a date and time

A datetime profile combines date and time fields. Reading it needs a
locale context with a time zone:

```python
from citry import (
    Citry,
    DateSegments,
    DateTimeFormat,
    DateTimeInput,
    DateTimeSegments,
    FormatRegistry,
    TimeSegments,
)
from citry.ext.i18n import make_context

formats = FormatRegistry(
    datetime={
        "appointment": DateTimeFormat(
            length="medium",
            input=DateTimeInput(mode="segments"),
        ),
    },
)

app = Citry(
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "formats": formats,
        },
    },
)

context = make_context(
    app,
    locale="en-US",
    time_zone="Europe/Prague",
)
i18n = app.extensions.get_extension("i18n")
parser = i18n.for_context(context).parse

edit = DateTimeSegments(
    date=DateSegments(year="2026", month="10", day="25"),
    time=TimeSegments(
        hour="2",
        minute="30",
        second="00",
        day_period="AM",
    ),
)
result = parser.datetime_segments(edit, format="appointment")
```

Daylight saving time makes some local times special:

- A time that the clocks skip when daylight saving starts is `invalid`.
- A time that happens twice when the clocks go back is `ambiguous`. The
  result lists both possible moments in `alternatives`.

The example above is ambiguous: 2:30 AM happens twice in Prague on
25 October 2026. Ask the user which one they mean, then pass it as
`fold`:

```python
result = parser.datetime_segments(
    edit,
    format="appointment",
    fold="earlier",  # or "later"
)
```

## Parse in the browser { #parse-numbers-and-percentages-in-the-browser }

Inside a [browser i18n provider](/i18n/browser/), `$i18n.parse` reads
numbers and percentages:

```javascript
const result = $i18n.parse.number(
  "12,345.50",
  { format: "measurement" },
);
```

It returns a frozen object with `input`, `state`, `value`, `error`, and
`valid`. `value` is a string, so JavaScript does not lose decimal
digits.

Dates, times, and datetimes are parsed only on the server; the browser
has no methods for them. Reading them exactly like the server needs the
server's calendar and daylight saving data, and Citry does not try to
rebuild that data in the browser.

## Less common cases

### Accept two-digit years

By default, a year must have enough digits to identify it. To accept
two-digit years, choose the first year of a 100-year window:

```python
DateInput(
    mode="strict_text",
    two_digit_year_start=1950,
)
```

Two-digit years then map to 1950 through 2049. Citry does not move the
window with the current date.

### Read money and units

Parse the amount with `parse.number()` and keep the currency code or
unit as separate data. Citry does not read a currency or unit from the
typed text.

### No relative dates

Citry does not read phrases such as "next Tuesday evening". Each profile
accepts one strict format.

### Time-zone data

Citry reads time-zone rules from the `tzdata` Python package it depends
on, not from the operating system. A context with a time zone records
the `tzdata` version it used.
