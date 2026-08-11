# Formatter backend spike environment

This is a bounded comparison, not a production dependency choice. It runs
Babel 2.18.0, PyICU 2.16.2 linked to Homebrew ICU 78.3, Python `zoneinfo`
forced to `tzdata` 2026.3, and the `Intl` implementation embedded in Node
26.5.0. The checked evidence was produced on macOS 26.6 arm64 with Python
3.13.12 and uv 0.12.0.

The exact Python package pins are in `python-requirements.txt`. PyICU publishes
a source distribution, so this macOS run deliberately rebuilds it without the
uv cache. PyICU expects its list-valued environment variables to use the
platform path separator, which is `:` on this host:

```bash
ICU_VERSION=78.3 \
PYICU_INCLUDES=/opt/homebrew/opt/icu4c@78/include \
PYICU_CFLAGS=-std=c++17 \
PYICU_LFLAGS=-L/opt/homebrew/opt/icu4c@78/lib:-Wl,-rpath,/opt/homebrew/opt/icu4c@78/lib \
PYICU_LIBRARIES=icui18n:icuuc:icudata \
PYTHONTZPATH='' \
uv run --isolated --no-project --no-cache \
  --with-requirements docs/design/i18n_research/formatter_backend/python-requirements.txt \
  python docs/design/i18n_research/formatter_backend/run_formatter_backend_spike.py
```

`PYTHONTZPATH=''` must be present before Python imports `zoneinfo`; the harness
rejects a non-empty `TZPATH`. `--no-cache` is load-bearing here because a PyICU
wheel built against different ICU linker settings is not a valid substitute.
The build requires ICU headers and libraries at the recorded path and takes
about 15 seconds on this machine.

To reproduce the checked artifact, direct stdout to a temporary file and
compare it with `evidence.json`. Machine identity, uv, Node, ICU, CLDR, Unicode,
tzdb, all source hashes, and all package versions are embedded in the result.
The package pins do not contain artifact hashes, so this is an exact-version
research environment rather than a supply-chain lock.

The browser side has no package dependency: `browser/runner.mjs` exercises the
built-in ECMA-402 implementation in the recorded Node binary. A real browser
matrix remains necessary because browsers can carry different ICU, CLDR, and
tzdb revisions.
