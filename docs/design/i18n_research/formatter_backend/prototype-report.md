# Formatter backend comparison

## Outcome

No backend is ratified yet, but the choice is now much clearer:

- Babel is a good small server API for a deliberately limited profile set. It
  matched plural behavior and ordinary Latin-digit formatting in this matrix,
  accepts exact Python `Decimal` values, and provides strict decimal parsing.
  It did not shape Arabic-Indic or Devanagari digits, did not parse those
  shaped inputs in the tested strict path, rejected Unicode locale extensions,
  and rendered the Thai date with Gregorian year 2026 rather than Buddhist
  year 2569. It cannot satisfy the proposed full matrix by itself.
- PyICU exposes the capabilities needed for the full matrix. It shaped and
  parsed Arabic-Indic and Devanagari digits, honored the Buddhist calendar,
  preserved an exact decimal string beyond JavaScript's safe-integer range,
  and matched browser plural categories for all ten locales and nine operands.
  Its cost is operational: it is a native source build tied to an ICU install.
- Browser `Intl` is a strong formatter but is not a localized-input parser.
  The checked runtime has no public number-parse operation. Citry must own a
  parsing contract and implementation for editable number/date controls even
  if every display formatter delegates to `Intl`.

The likely architecture is therefore either a PyICU-backed optional/full
profile with an intentionally normalized adapter, or a Babel-backed core
subset with unsupported digit/calendar profiles rejected at configuration
time. Adding an ad hoc digit-shaping step to Babel is not justified by this
spike because parsing, calendars, bidi, and parity would still need separate
solutions.

## What the spike proved

The checked `evidence.json` records `PASS_BOUNDED` for:

1. Identical plural categories across Babel, PyICU, and Node `Intl` for the ten
   fixed locales, including Czech fractional `many`.
2. Exact PyICU/`Intl` output for seven format kinds in the five reference
   profiles `en-US`, `cs-CZ`, `ar-EG`, `hi-IN-u-nu-deva`, and
   `th-TH-u-ca-buddhist` when both use ICU 78.3.
3. Arabic-Indic and Devanagari digit shaping in PyICU and `Intl`, and the lack
   of such shaping in Babel 2.18.0.
4. Buddhist-calendar output in PyICU and `Intl`, and Babel's Gregorian-only
   result through the tested API.
5. Full-consumption PyICU number parsing for Latin, Arabic-Indic, and
   Devanagari cases. Babel's strict parser passed the English and Czech cases
   and rejected the two shaped-digit cases.
6. Exact decimal-string formatting of `9007199254740993`, signed negative
   zero, and `1.2300` through PyICU and modern `Intl` without first converting
   the input to binary64.
7. Package-only `zoneinfo` classification of both declared Prague and New York
   gaps and folds, including the two explicit fold instants.

The test uses ICU's modern `NumberFormatter` family for display. ICU recommends
that API for modern formatting; the legacy `NumberFormat` remains useful for
parsing.

## The important mismatch

The same ICU version does not guarantee byte-identical behavior through two
different APIs. Seven raw PyICU/`Intl` differences remained:

- Russian medium date used a narrow no-break space through PyICU and a regular
  space through Node.
- Raw PyICU service lookup for `az-Arab` fell back to root data, including a
  Persian calendar, while `Intl` used Azerbaijani formatting and a Gregorian
  calendar.

Projecting `az-Arab` to Azerbaijani base-language service data reproduced the
browser output for every tested kind. That is evidence for a Citry-owned locale
service projection and explicit calendar/numbering profiles, not permission to
silently strip scripts in general. The adapter must use versioned, tested
locale matching rules and record the actual service locale. Exact output
equality remains a per-profile claim; the general contract compares semantic
fields and permits bounded presentational variation.

## Packaging observation

On this host, the installed Babel package tree was about 31 MB and the PyICU
Python package tree about 1.7 MB. The latter is misleading alone: its extension
linked three external ICU dylibs totaling about 37 MB, in addition to the
roughly 1.6 MB extension. Babel is pure Python and wheel-friendly; PyICU needs
headers, a compiler, correct runtime library discovery, and an ICU revision
that remains present after deployment. Package size alone does not select a
winner, but PyICU is not suitable as an invisible mandatory dependency without
wheel and deployment work.

## What remains open

- Define Citry's normalized locale-to-service-locale algorithm instead of
  inheriting Babel, ICU, or ECMA-402 fallback accidentally.
- Turn the design's named profiles into explicit Babel, ICU skeleton, and
  ECMA-402 option mappings, then compare semantic fields across the full
  matrix.
- Specify strict parsing states, grouping validation, signs, exponents,
  whitespace, incomplete edits, and error spans. A successful `NumberFormat`
  parse alone is not a UI input contract.
- Test date/time parsing, all calendar profiles, time-zone display names, and
  browser tzdb divergence. The current gap/fold proof belongs to Citry's
  `zoneinfo` boundary, not to Babel or PyICU parsing.
- Measure cold import, first format, repeated format, formatter-cache behavior,
  concurrency, and production wheel coverage.
- Run Chromium, Firefox, and WebKit, not only Node.

The evidence does not approve Babel plus a shaping layer, make PyICU mandatory,
or promise universal server/browser string equality.
