# Phase 0 payload and performance result

This is the final bounded Phase 0 exploration. It measures the production-shaped
Rust/PyO3 message slice, a browser bundle that combines the Fluent runtime,
provider, rich-Slot relocation, strict value decoder, and 100 messages, and 30
loaded locale changes in each supported browser.

The checked [evidence](evidence.json), host-specific
[measurements](performance.json), [runner](run_phase0_completion.py), and
[environment](prototype-environment.md) record the result.

## Plain-language result

The bounded runtime is small enough and fast enough for the limits in the
design.

- A fixed-locale server page loaded no i18n browser code.
- The dynamic browser bundle plus 100 English messages was 11,344 bytes gzip.
  The limit is 35,840 bytes.
- A second 100-message locale partition was 511 bytes gzip. The limit is
  15,360 bytes.
- The production-shaped server tree resolved 100 messages and made 20 named
  formatter calls with 1.49 ms added median render time and 1.51 ms added p95
  time on this machine. The limits were 2 ms and 3 ms.
- Thirty loaded locale changes passed in Chromium, Firefox, and WebKit. The
  measured p95 was 0.4 ms in Chromium and 1 ms in Firefox and WebKit, below the
  50 ms limit. No sampled frame contained a partly changed locale.

These numbers do not remove the formatter blocker. The server benchmark uses
the production-shaped Fluent runtime and the slice's deterministic formatter
stand-in. The selected ICU4X adapter still needs its percent, unit, editing,
and date/time work, followed by the same benchmark through the final adapter.

## What the browser bundle contains

The measured bundle is more than the upstream Fluent baseline. It contains:

- `@fluent/bundle` 0.19.1 and its source parser;
- the provider service and atomic switch transaction;
- source-aware rich-Slot relocation;
- strict decoding for the first tagged browser value set;
- artifact and public-message checks; and
- 100 simple English messages.

The canary imports and runs the minified result. It checks a value larger than
JavaScript's safe integer range, signed float zero, one formatted message, and
the provider and rich-relocation schema versions. The additional locale is a
separate minified module, so it measures lazy locale data rather than counting
the runtime twice.

## What the browser timing means

The page already has both locale artifacts in memory. Each sample measures
validation, nested provider recomputation, message sink updates, `lang` and
`dir` updates, and the atomic DOM commit. It does not measure a network fetch.
Network time belongs to loading status and does not change the 50 ms commit
budget.

The benchmark alternates English and Arabic 30 times. Czech explicit children,
the Japanese provider below a server-only barrier, and the blocked subtree stay
fixed. Animation-frame sampling accepts either the complete old state or the
complete new state and rejects every mixed state.

## What the server timing means

The two Citry trees produce the same visible HTML. One has literal Czech text.
The other performs 100 warm attribute-message resolutions and 20 named decimal
format calls through the compiled Rust/PyO3 artifact. The run uses five warmups,
30 samples per tree, and rotates literal, localized, and unconfigured order.

On this arm64 macOS host:

- literal median was 0.24 ms and p95 was 0.26 ms;
- localized median was 1.73 ms and p95 was 1.77 ms; and
- unconfigured median was 0.24 ms and stayed inside the literal tree's 95%
  mean confidence interval.

The process peak increased by 128 KiB during the measured loop. The four-
catalog compiler smoke test remained about 4 to 5 ms. These are host-specific
numbers, so the checked semantic evidence stores pass/fail gates separately
from the timing file.

## What still needs production proof

This slice does not claim that the whole feature is ready to ship.

- The final ICU4X named-profile adapter and localized editing contract are not
  implemented.
- The complete tagged wire still needs local date-time fold/gap records and
  every production formatter wrapper.
- The browser bundle uses research candidates, not code promoted into Citry's
  shipped extension and client runtime.
- The locale partitions use simple messages. Large real catalogs and feature-
  split package graphs need release benchmarks.
- The loaded switch benchmark excludes network transfer by design.
- Linux and supported wheel targets need the same server and size matrix.
- Rich messages still limit in-page switching to the same Slot occurrence count
  in every selectable locale. A count change uses navigation in the first
  release.

## Decision

Keep the payload and performance limits. The proved architecture has enough
headroom for the first release. Do not reopen the choice of Fluent or the Rust
boundary because of size or warm runtime cost.

Phase 0 is complete as an exploration. Implementation can begin with the
bounded surface, but the complete formatter remains a named implementation
gate: finish or reject each unsupported profile before claiming the full i18n
API.
