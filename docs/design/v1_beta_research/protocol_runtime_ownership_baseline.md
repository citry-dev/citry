# Protocol runtime ownership baseline

**Closed 2026-08-04 after the Stage 0 review.** This is the opening evidence for
[`protocol_runtime_ownership.md`](../protocol_runtime_ownership.md). It records
only files in the protocol/runtime/build scope. It is not a repository freeze;
each implementation stage refreshes the affected entries before editing.

Reproduce the structural baseline with:

```bash
python scripts/protocol_runtime_baseline.py --details
```

Add the bounded seven-sample timing comparison with:

```bash
python scripts/protocol_runtime_baseline.py --details --timings
```

The script owns the explicit scope list. It sorts every tracked or untracked
in-scope path, records its worktree SHA-256 plus Git index and HEAD blob
identities, and hashes the compact JSON records separated by a zero byte. The
status digest hashes Git's zero-delimited porcelain output. Test-tree digests
hash each sorted relative name and its content SHA-256. Normalized schema
hashes use compact JSON with sorted object names.

## Repository identity

| Item | Value |
|---|---|
| Commit | `5a8f589c8a14d812f968e7a1fda3490d456773ab` |
| Branch | `review` |
| Scoped path count | 270 |
| Scoped status digest | `8600f29bc2eb2bfaf62c9ba0a128dbd1e1e8102eaef1ef005e5b89d0f9f5d317` |
| Scoped content-identity digest | `d785668fba43f51e1a9790de5fb95b2ef7a0181021e079bbdeae494104501bf1` |
| Client-graph test-tree digest | `3376b615245d971e0f6934fb686008b1d08cd04c2f63041c87f400dc21b051f3` |
| Events test-tree digest | `2f07c1966305d798f68ff05b80f2d800a95f3beddf5e633a01faf7a862d862b4` |

The scoped HEAD moved from `4126c6ed89971d676bb3ff78e1b63f006b61b0d1` to
the commit above while Stage 0 was running. That movement is expected. The
Events Python extension, Events TypeScript package, ownership-manifest producer,
and generated Events browser file remain untracked; the Events browser file is
not ignored. Git history alone cannot reconstruct their chronology, so each
stage compares the live scoped identities before editing.

The closing environment was Python 3.13.12, Node 26.5.0, pnpm 10.32.1, and
macOS 26.6 on arm64. CI uses Node 22; the protocol JavaScript checks target
Node 22 and ES2020 rather than relying on Node 26 behavior.

## Normalized schema hashes

The hashes below use compact, sorted JSON so formatting changes do not look like
contract changes.

| Schema | SHA-256 |
|---|---|
| Client graph manifest | `4e15aa0999d7942778f44d33e641f7b315a8a6eb978be664382d4494be2f57a2` |
| Events call | `e1f91d62f7e2dbaf81de4a1884d8378947814a2a3b419b9a4af61d7a93ea2da2` |
| Events descriptor | `bb92dab7cbdf43552b50a3bfaad233eab9cdcabe5164d00394e9fe0011c5769a` |
| Events manifest | `a437d110b0eb3f38e11406a71ab9e1b1d3dc734b9df97790f8962d949b683d7d` |
| Events result | `671a203a1f9078eadefba692b6861b8d2549a5fc0eb6c058caa569378f2413f8` |

## Browser artifacts

| Artifact | SHA-256 | Raw bytes |
|---|---:|---:|
| `citry.js` | `72f905828e19de2aaec657989bbb1b7f4689e27e38cfbd51e7af331cd0c8b3bf` | 278,851 |
| `citry-events.js` | `55ace6de78c13accfe8d196b924439404504de7a3572ec61d901702d6ce5ce7c` | 294,410 |
| Combined | | 573,261 |

The combined payload is 123,032 bytes with the repository test's deterministic
single gzip stream. The hard guards are 574,000 raw and 123,500 gzip bytes.

A checked-in Stage 0 esbuild prototype generates a private helper inside the
core IIFE and bundles the same comment parser source into Events. Run it with:

```bash
pnpm --dir packages/protocol/client_graph/v1/js run prototype
```

After removing the corresponding duplicate declarations and parser code in
memory, the projected combined change is 729 raw and 275 gzip bytes. That
projects 573,990 raw and 123,307 gzip bytes, leaving 10 raw and 193 gzip bytes
under the guards. This proves the composition and load-order design, but it is
too close to integrate before the larger handwritten validators are removed in
the same migration stage.

## Focused timing comparison points

These local medians only detect a material regression during this refactor.
They are not the project's broader benchmarking work.

| Path | Median |
|---|---:|
| One Events `data` call through `EventsDispatcher` | 17.580 microseconds |
| Sixteen Events `data` calls through `EventsDispatcher` | 244.181 microseconds |
| Render and serialize the 25-instance client scenario | 7.504 milliseconds |
| Render and serialize the 325-instance client scenario | 146.413 milliseconds |

The 25-instance graph is 37,843 raw and 1,994 gzip bytes. Its whole document is
630,448 raw and 127,567 gzip bytes. The 325-instance graph is 489,757 raw and
17,142 gzip bytes. Its whole document is 1,274,946 raw and 153,435 gzip bytes.

## Opening verification

- `python -S packages/protocol/client_graph/v1/validate.py`: 47 cases passed.
- `python -S packages/protocol/events/v1/validate.py`: 19 exchanges, 9
  descriptors, and 8 manifests passed.
- `pnpm --dir packages/js/citry-client run check`: type checking, lint, and 10
  Node canaries passed.
- Focused protocol and runtime pytest selection: 79 tests passed.
- `python -S packages/protocol/client_graph/v1/tests/check_canonicalization.py`
  and the matching Node command passed all 13 shared vectors.
- `pnpm --dir packages/protocol/client_graph/v1/js run check`: type checking,
  formatting, four unit tests, and the composition prototype passed.

The complete repository gate and full browser matrix were deliberately not run
for this opening snapshot. They are completion gates after the code migration.
