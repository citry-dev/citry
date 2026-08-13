# Server runtime and formatter decision

**Status:** The message runtime is ready to ratify. The complete formatter is
not. This Phase 0 exploration selected the direction and found the remaining
blockers.

## Decision

Use Rust `fluent-bundle` 0.16.0 for server message execution through Citry's
existing Rust/PyO3 boundary. The earlier runtime, compiler/linker, and
production-shaped slices already prove the checked generated operations,
errors, exact typed values, source maps, and real component calls. The Python
`fluent.runtime` package remains a test oracle, not a production dependency.

Use ICU4X as the Rust foundation for locale data, plural rules, formatters, and
strict parser metadata. It fits the same compiled extension, produces a self-
contained binary, accepts exact decimal strings, and does not need a system ICU
installation.

Do not yet call the complete Citry formatter contract ratified. ICU4X 2.2.0's
stable surface is a strong fit, but several APIs Citry needs are still in
`icu_experimental` 0.5.0, and two direct outputs failed the browser contract.
Citry needs a checked adapter or an upstream fix before implementation may
claim the full profile.

PyICU stays a comparison oracle. It covers the broad matrix, but PyICU 2.16.2
publishes only a source archive on PyPI. It requires system ICU headers and
libraries, and its result depends on the linked ICU build. Making it Citry's
default would turn a normal Python install into a native toolchain and runtime-
library requirement.

Babel remains useful for comparison and possibly build tooling. It cannot be
the full server formatter because the earlier matrix showed missing digit
shaping, alternate-calendar, Unicode-locale-extension, and shaped-number parse
behavior.

## What ICU4X proved

The release Rust binary used ICU4X 2.2.0 with compiled data and the `sync`
feature. It passed concurrent use from 16 threads and covered:

- exact Arabic and Devanagari decimal formatting for
  `9007199254740993.25`;
- Arabic currency formatting;
- a Thai Buddhist-calendar date;
- Czech fractional plural category `many`;
- Czech relative day formatting;
- a Spanish conjunction list;
- Arabic unit formatting;
- non-Latin strict decimal round trips, including a localized negative sign;
  and
- rejection of bad grouping and mixed digit systems.

The exact Arabic currency and decimal, Devanagari decimal, Buddhist date,
Czech relative day, and Spanish list outputs matched Node's ICU 78.3 `Intl`
output in this fixed matrix. Czech fractional plural semantics also matched.

The strict parser did not hard-code Arabic or Devanagari characters. It wrapped
ICU4X's data provider while creating the formatter and captured the exact
resolved digits, decimal separator, grouping separator, grouping sizes, and
sign affixes. The immutable parser specification then accepted only those
values and returned an exact ASCII decimal string. This is a practical route
for NumberInput, but incomplete edit states and every configured locale still
need production tests.

The `sync` feature is required. Without it, the compiled-data payload uses
`Rc` and formatter values are not `Send + Sync`.

## What failed

The direct experimental percent formatter and browser `Intl` do not have the
same contract. ICU4X treated `12.5` as 12.5 percent, while `Intl` takes a
fraction and formats `0.125` as 12.5 percent. More importantly, ICU4X emitted
the ASCII percent sign with left-to-right marks for Arabic, while `Intl`
emitted the Arabic percent sign.

The direct experimental Arabic long-unit formatter and `Intl` selected
different forms for `9007199254740993.25`. The later
[`formatting_followup`](../formatting_followup/prototype-report.md) added ordinary
integer and fractional controls and corrected the diagnosis: ICU4X and all
three browsers agree for those values. For this one exact decimal, ICU4X follows
the CLDR `other` rule while the tested browsers lose precision in their ICU4C
plural path and select `many`. The checked evidence key calls this a grammar
difference because that was the earlier interpretation; it should be read as a
historical raw-output difference, not as evidence that ICU4X generally misses
Arabic unit grammar.

ICU4X does not ship IANA time-zone offset transitions. It formats a zone once
the application supplies the resolved identity, offset, and time. Citry should
keep the already proved package-only Python `zoneinfo` boundary, then pass the
resolved instant and zone data into Rust. That also keeps the chosen tzdb
revision explicit.

ICU4X does not provide Citry's localized editing parser. The small strict
decimal parser proved that the resolved locale data is available, but Citry
must own the editing-state and diagnostic rules. Date and time editing remain
unproved.

## Cost

The research binary that links the broad checked ICU4X surface was 4,089,008
bytes. A binary in the same package that did not use ICU4X formatting was
431,152 bytes, for a 3,657,856-byte research delta. The complete candidate
compressed to 1,158,913 bytes with gzip. This is a rough native-wheel cost, not
a final Citry extension measurement: release LTO, selected data markers, and
the existing extension code will change it.

On this machine, the first decimal formatter construction stayed below 5 ms
and repeated exact decimal formatting stayed below 10 microseconds per call.
The deterministic evidence stores only the passed budgets, not unstable timing
samples.

## Required follow-up before the full formatter is ratified

1. Define Citry's percent input convention and prove one ICU4X adapter that
   matches the named browser profile, including the correct locale percent
   sign and bidi marks.
2. Prove unit profiles whose grammatical output matches or is semantically
   equivalent to the three browser engines. Reject unsupported units and
   profiles at build time.
3. Finish strict number editing states and add bounded date/time parsing.
4. Connect Python `zoneinfo` resolution to the Rust date/time formatter and
   include the chosen tzdb revision in formatter and cache identities.
5. Build the real extension with only the selected ICU4X markers, then measure
   wheel size and all supported platform targets.

Until those pass, server messages without these formatter operations can use
the ratified Fluent runtime, but Phase 1 must not claim the complete formatter
surface or unblock locale-sensitive UI inputs.

## Limits

- The proof uses one macOS arm64 build and Node's embedded ICU for its browser
  comparison. The final matrix still needs Chromium, Firefox, and WebKit.
- The binary is a Rust executable, not the final PyO3 wheel.
- Exact equality was checked only for the listed profiles. The general contract
  remains semantic equality plus explicitly approved presentation differences.
- This session did not have an independent agent reviewer. The evidence is
  executable and adversarial, but not independently reviewed.

The frozen results are in [`evidence.json`](evidence.json). Reproduction steps
are in [`prototype-environment.md`](prototype-environment.md).
