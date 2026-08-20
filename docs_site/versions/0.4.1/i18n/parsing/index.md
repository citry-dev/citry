---
title: Parse localized input
url: https://citry.dev/v/0.4.1/i18n/parsing/
description: "Convert strict locale-sensitive form edits into canonical numbers, dates, times, and instants without guessing free-form prose."
---
# Parse localized input

Formatting and parsing solve opposite problems, but they share the same named
profile. A profile says how a value is displayed and, when configured, which
strict editing grammar the matching parser accepts.

Citry does not parse free-form requests such as "next Tuesday evening" or
guess a currency or measurement unit from text.

## Keep the user's edit separate from its value

A parse result preserves the exact input and reports its state:


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


Numeric results have three states:

- `valid`: `value` contains a canonical `Decimal`;
- `incomplete`: the input may become valid with more typing, such as a trailing
  decimal separator; and
- `invalid`: the input breaks the profile's grammar.

Do not replace the edit field with `value` while the user is still typing. Keep
the localized string in the control and use the canonical value for domain
logic after the result becomes valid.

## Parse numbers with locale digits and separators

Every `NumberFormat` includes a `NumberInput` policy:


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


The default accepts strict decimal notation. It checks the locale's digits,
decimal separator, grouping separator, grouping sizes, and signs. It does not
silently accept a digit or separator from another locale.

`decimal_or_scientific` also accepts ASCII `e` or `E`; the exponent digits
still use the selected locale's digit set.

## Parse percentages as ratios

`PercentInput` chooses whether the user edits the locale's percent affix:


```python
from citry import PercentFormat, PercentInput

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


Use `required` when the percent sign belongs inside the editable text. Use
`omit` when the control renders the affix outside its input field.

Both modes return a ratio. Parsing localized 12.5 percent returns
`Decimal("0.125")`.

## Choose strict text or segmented dates

A date profile may be display-only or may declare one input mode:


```python
from citry import DateFormat, DateInput

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


`strict_text` accepts the locale-specific field order, separators, digits, and
month names produced by that profile. It does not accept another locale's date
shape.

`segments` is for a control that already owns separate fields. Pass the fields
by meaning, regardless of their visual order:


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


The valid result is a canonical Python `date`. Citry uses the selected locale's
calendar when reading the fields and reports ambiguous or unsupported calendar
input rather than guessing.

## Make two-digit years explicit

By default, a year requires enough digits to identify it. If a product truly
accepts two-digit years, define the first year of one explicit 100-year window:


```python
DateInput(
    mode="strict_text",
    two_digit_year_start=1950,
)
```


The profile now maps two-digit years into 1950 through 2049. Another product
can choose another window. Citry does not derive the window from the current
date.

## Parse wall-clock time without a zone

Time parsing follows the same two input modes:


```python
from citry import TimeFormat, TimeInput, TimeSegments

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


A valid result is a zone-free Python `time`. Converting it to an instant needs
a date and a time zone, so it belongs to datetime parsing instead.

## Resolve local datetimes through an explicit zone

Datetime parsing combines date and time fields and requires a context with an
IANA time zone:


```python
from citry import (
    DateSegments,
    DateTimeFormat,
    DateTimeInput,
    DateTimeSegments,
    TimeSegments,
)

formats = FormatRegistry(
    datetime={
        "appointment": DateTimeFormat(
            length="medium",
            input=DateTimeInput(mode="segments"),
        ),
    },
)

context = i18n.make_context(
    locale="en-US",
    time_zone="Europe/Prague",
)
parser = i18n.for_context(context).parse

edit = DateTimeSegments(
    date=DateSegments(year="2026", month="10", day="25"),
    time=TimeSegments(hour="2", minute="30", second="00"),
)
result = parser.datetime_segments(edit, format="appointment")
```


A local time in a daylight-saving gap is `invalid`. A local time in a fold is
`ambiguous` and contains both possible aware instants in `alternatives`.
Resolve the user's choice explicitly:


```python
result = parser.datetime_segments(
    edit,
    format="appointment",
    fold="earlier",  # or "later"
)
```


Citry reads time-zone transitions from its pinned `tzdata` package rather than
the host machine's unversioned zone database.

## Know the browser boundary

The browser service currently provides synchronous strict parsing for numbers
and percentages:


```javascript
const result = $i18n.parse.number(
  "12,345.50",
  { format: "measurement" },
);
```


It returns a frozen object with `input`, `state`, `value`, `error`, and
`valid`. The canonical numeric `value` is a string so JavaScript does not lose
decimal precision.

Date, time, and datetime parsing currently runs on the server. Those browser
methods are absent because safe parity requires generated calendar-conversion
and daylight-saving records; Citry does not reverse-engineer arbitrary
`Intl.DateTimeFormat` output.

Unit controls parse their numeric field with `parse.number()` and keep the
unit as separate domain data. Currency controls likewise keep the currency
code explicit.
