# Percent, unit, and date-editing exploration

**Status:** Design exploration completed on 2026-08-11. The later production
slice implemented the selected percent, unit, and numeric-date contracts. This
report keeps the evidence and tradeoffs that led to that API.

## Plain-language result

The three open areas do not have the same problem.

- **Percent has a clear standard contract.** A stored value of `0.125` formats
  as `12.5%`. Parsing `12.5%` returns `0.125`. Browser `Intl`, CLDR, Vue I18n,
  Babel, and React Aria all use this fraction-of-one convention. ICU4X's current
  experimental formatter does not: it printed `0.125%`, used the wrong Arabic
  percent sign, and remains tracked as unfinished ECMA-402 work. Citry should
  define the standard convention itself and must not expose that experimental
  API directly.
- **Ordinary unit formatting already agrees.** ICU4X 2.2 and all three tested
  browsers produced the same Arabic long-unit forms for `11`, `11.25`, and
  `12345.67` metres. The earlier apparent general mismatch was a bad diagnosis.
  The real difference appears only for an exact decimal larger than JavaScript's
  safe integer range. ICU4X follows CLDR; the tested browsers choose the wrong
  plural form because their ICU4C path loses precision during plural selection.
  This limitation is already discussed by TC39 and ICU maintainers.
- **Date editing is not a formatter-backend mismatch.** ECMA-402 and ICU4X
  format dates but do not define a general user-input parser. Libraries that do
  date entry either use structured fields or require an explicit locale and
  expected pattern. Citry should do the same and should never guess what an
  isolated value such as `04/05/2026` means.

This made percent ready for an adapter design, unit ready for a deliberately
small server profile, and date editing ready for an input-policy design. The
production follow-up has since implemented those three server contracts.

## The visible examples

### Percent

The canonical application value is a ratio:

```text
stored Decimal("0.125")
        |
        | format as percent
        v
      12.5%
        |
        | parse as percent
        v
stored Decimal("0.125")
```

Storing `12.5` and then applying percent formatting means `1,250%`. The profile
must say how many digits to display and how to round, but it must not change the
meaning of the value.

For Arabic Egypt, the browser result also demonstrates that the percent sign
and invisible direction mark are locale data, not ASCII punctuation that Citry
can append itself:

```text
Intl:                  ١٢٫٥٪؜
ICU4X experimental:   ٠٫١٢٥‎%‎
```

The second result has three independent problems for Citry: no multiplication
by 100, an ASCII `%`, and different bidi controls.

### Date entry

The same visible edit can name two dates:

| Edit | Expected field order | Result |
|---|---|---|
| `04/05/2026` in `en-US` | month/day/year | 5 April 2026 |
| `04/05/2026` in `cs-CZ` | day/month/year | 4 May 2026 |
| `04/05/2026` without a locale and input policy | unknown | ambiguous; do not guess |

A segmented control avoids that ambiguity while still presenting fields in the
locale's order:

```text
cs-CZ UI:  [day 04] [month 05] [year 2026]
                         |
                         v
              Python date(2026, 5, 4)
```

The submitted or stored value is typed and canonical. The displayed order,
digits, separators, month names, calendar, and first day of week remain
localized.

### Units

CLDR unit forms depend on the plural category of the **rounded displayed
number**, not merely on the unit name:

| Exact input | CLDR category in Arabic | ICU4X 2.2 | Chromium, Firefox, WebKit |
|---|---|---|---|
| `11` | `many` | `١١ مترًا` | `١١ مترًا` |
| `11.25` | `other` | `١١٫٢٥ متر` | `١١٫٢٥ متر` |
| `12345.67` | `other` | `١٢٬٣٤٥٫٦٧ متر` | `١٢٬٣٤٥٫٦٧ متر` |
| `9007199254740993.25` | `other` | `…٩٩٣٫٢٥ متر` | `…٩٩٣٫٢٥ مترًا` (`many`) |

The final browser result is not a second acceptable Arabic form for that
number. CLDR's `=` relation only matches integers in a listed range. Arabic
`many` uses `n % 100 = 11..99`; a value with a non-zero fraction therefore
selects `other`. ICU4X preserves the exact decimal operands and gets this case
right.

## Why ICU4X and browser `Intl` differ

`Intl` is an API standard, not one formatter implementation. Chromium,
Firefox, WebKit, and Node normally delegate much of their locale work to ICU4C.
Citry's server uses ICU4X. They can use the same CLDR rules yet differ because
they have different APIs, data versions, maturity, and numeric representations.

There are two unrelated differences in this exploration:

1. **Percent is unfinished ICU4X API work.** The tested type lives in
   `icu_experimental`. Its direct value convention and Arabic sign output do
   not claim the ECMA-402 contract that Citry needs. ICU4X issue
   [#4483](https://github.com/unicode-org/icu4x/issues/4483) explicitly tracks a
   percent formatter for ECMA-402 compatibility.
2. **The huge unit value exposes ICU4C precision loss.** Current
   [ECMA-402](https://tc39.es/ecma402/#sec-intl.pluralrules.prototype.select)
   uses an exact “Intl mathematical value” for string input to both NumberFormat
   and PluralRules. The normative TC39 change
   [#1026](https://github.com/tc39/ecma402/pull/1026) says this aligns plural
   selection with NumberFormat and permits exact decimals. The associated
   [Test262 discussion](https://github.com/tc39/test262/pull/4912) records the
   remaining limitation plainly: ICU4C converts plural operands to `double`,
   which makes some large values select the wrong category. Firefox tracked the
   standards change in
   [bug 1991475](https://bugzilla.mozilla.org/show_bug.cgi?id=1991475), but the
   tested Firefox 153 still reproduced the large exact-decimal unit result.

ICU4X had its own large-magnitude operand issue
[#2588](https://github.com/unicode-org/icu4x/issues/2588). The merged fix
[#7502](https://github.com/unicode-org/icu4x/pull/7502) preserves the modulo
digits that CLDR plural rules need. The checked ICU4X 2.2 path therefore returns
the CLDR category for the exact value.

I did not find a dedicated browser issue for this exact NumberFormat unit
example. The underlying precision problem and lack of strong large-value
conformance tests are, however, already documented in the Test262 thread. Citry
does not need to rediscover or normalize away that problem.

ICU4X unit formatting is also not yet a stable surface. Its open
[#6900](https://github.com/unicode-org/icu4x/issues/6900) tracks replacing the
legacy unit formatter, while the broader
[#8157 graduation epic](https://github.com/unicode-org/icu4x/issues/8157)
requires correct all-locale behavior and consistency with ECMA-402 and UTS 35.
Citry may use a pinned experimental primitive behind its own checked adapter;
it should not expose that primitive as Citry's public contract.

## What the standards say

### Percent

[ECMA-402 NumberFormat](https://tc39.es/ecma402/#sec-partitionnumberpattern)
multiplies the input by 100 when the style is `percent`, rounds that value, and
uses a locale-provided percent sign. [Unicode TR35
Numbers](https://unicode.org/reports/tr35/tr35-numbers.html) defines percent as
one part in one hundred and gives the same `1.23 -> 123%` behavior.

Citry should therefore use this contract:

- canonical value: exact ratio, preferably `Decimal`;
- display: multiply by 100, then apply the profile's exact rounding;
- input: parse locale digits, separators, sign, and percent affixes, then divide
  by 100;
- editing: retain distinct complete, incomplete, and invalid states;
- bidi: use locale data for the sign and surrounding controls.

### Units

[Unicode TR35 unit
formatting](https://unicode.org/reports/tr35/tr35-general.html#Unit_Elements)
defines unit widths, plural-sensitive patterns, grammatical case, compound
units, and locale preferences. [ECMA-402](https://tc39.es/ecma402/#sec-partitionnumberpattern)
selects the unit string after number rounding and allows it to depend on that
rounded value.

The first Citry profile should stay smaller than the full CLDR model:

- one explicit sanctioned unit ID supplied by the call;
- one width: `long`, `short`, or `narrow`;
- exact decimal input and profile-owned rounding;
- plural selection from the rounded display value;
- standalone/default grammatical case;
- no automatic conversion to a preferred regional unit;
- no parsing of free-form strings such as `5 m`.

Grammatical case inside running prose, compound units, and automatic unit
conversion need separate profiles and tests. They must not appear silently as
side effects of a simple `format.unit()` call.

### Date editing

[Unicode TR35 date
parsing](https://unicode.org/reports/tr35/tr35-dates.html#Parsing_Dates_Times)
describes why lenient parsing is difficult: the expected pattern is tried first,
field order matters, names and narrow forms may be ambiguous, and not every
formatted date round-trips. ECMA-402 exposes `Intl.DateTimeFormat` but no date
parser.

The [HTML date input
standard](https://html.spec.whatwg.org/multipage/input.html#date-state-(type=date))
uses a useful separation: the browser may show a localized editor, while the
control's value is a canonical date string. Citry should use the same idea with
typed Python values.

The recommended Citry rule is:

- a `DateFormat` profile may opt into an explicit editing policy;
- `self.i18n.parse.date(..., format="invoice-date")` uses that named profile,
  just like number parsing does;
- the editing policy declares the fields, calendar, two-digit-year rule,
  accepted separators, and whether the UI is segmented or strict free text;
- parsing returns complete, incomplete, invalid, or ambiguous without changing
  the last canonical value;
- arbitrary natural-language date parsing is out of scope.

This uses the same profile name for display and input policy without pretending
that parsing is the formatter run backwards.

## How other libraries handle it

| Library | Percent and units | Date input lesson |
|---|---|---|
| [Vue I18n](https://vue-i18n.intlify.dev/guide/essentials/number) | Named number formats are ECMA-402 options. Its percent example maps `0.99123` to `99%`. It delegates browser behavior rather than inventing another numeric standard. | Date formatting also delegates to `Intl.DateTimeFormat`; Vue I18n does not provide a general date parser. |
| [FormatJS](https://formatjs.github.io/docs/intl/) | Wraps and caches the `Intl` formatter family, including numbers and units. | Formatting and messages are in scope; arbitrary localized input parsing is not. |
| [Babel](https://babel.pocoo.org/en/latest/api/numbers.html) | `format_percent(0.34)` produces `34%`; [unit formatting](https://babel.pocoo.org/en/latest/api/units.html) applies locale plural forms. Number parsing is a separate API. | Its date parser needs a locale and expected format; it is not a natural-language date interpreter. |
| [React Aria NumberParser](https://react-aria.adobe.com/internationalized/number/NumberParser) | The parser takes the same options as `Intl.NumberFormat`; `45%` becomes `0.45`, and unit parsing requires the expected unit. It also understands partial edits and numbering systems. | [DateField](https://react-aria.adobe.com/DateField) uses locale-ordered editable segments and typed immutable date values. Form submission can remain ISO-shaped. |
| [Globalize](https://github.com/globalizejs/globalize/blob/master/doc/api/date/date-parser.md) | Number parsing and formatting are separate CLDR-backed operations. | The date parser is created from explicit formatter options. `1/2/2013` means January 2 in English and February 1 in Spanish, which makes locale and profile part of the input contract. |

The common pattern is strong: formatting follows CLDR/Intl; parsing is an
explicit, separate operation; and robust date controls edit structured values
instead of trying to understand arbitrary prose.

## Decisions carried into the production slice

These design outcomes now have a server implementation:

1. Add a named `PercentFormat` category whose canonical value is a ratio. The
   same profile name governs strict percent editing. Do not expose ICU4X's
   experimental direct semantics.
2. Add a named `UnitFormat` category with an explicit unit, width, and exact
   decimal value. Keep v1 to standalone unit formatting and exclude free-form
   unit parsing, grammatical-case selection, automatic conversion, and custom
   rounding options.
3. Extend `DateFormat` with an optional, explicit editing policy. Segmented
   editing is the recommended default. Strict free text is allowed only with a
   declared pattern/field contract.
4. Keep exact decimal values through the server. Do not change a correct CLDR
   result to match browser precision loss. Before browser switching ships,
   either add a Citry exact-plural path for unit selection or reject affected
   values on that client path.
5. Expand the formatter conformance matrix with percent round trips, unit
   rounding-before-plural cases, large exact decimals, grammatical-case
   fixtures, and ambiguous/incomplete date edits.

## What remains deliberately open

- browser-side formatting and input parity for these new profiles;
- the browser workaround for exact unit plural selection;
- calendar-specific date editing beyond Gregorian, ISO, and Buddhist numeric
  fields;
- free-form unit parsing, automatic unit conversion, and running-text
  grammatical case;
- localized time and datetime editing; and
- accessibility and keyboard behavior for the future Citry UI controls.

Those questions belong in the implementation design and conformance fixtures,
not in ad hoc formatter calls.
