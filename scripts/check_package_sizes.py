"""
Check that built package files are within their release size caps.

Each package has a release verifier, a script in `scripts/` that checks that
package's release files and fails a file that is over its size cap. Most of
them run only when a release is qualified, and each stops at the first file it
fails. This script runs on files that are already built. It prints the size of
every file next to its cap and writes a GitHub Actions warning for a file at 90
percent of its cap or more. For each file that is over its cap it prints a
GitHub Actions error and, after the whole report, exits with status 1. The pull
request that grows a file then fails, instead of the release, and one run names
every file that is over.

A file is over its cap when it is larger than the cap, as in the verifiers, so
a file of exactly the cap passes.

The caps are read from the verifier scripts that enforce them, so a cap is
written in one place. A file with no known cap, or one that does not exist, is
also an error: it means `capped_files()` and the build have drifted apart.
"""

from __future__ import annotations

import argparse
import fnmatch
import math
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

try:
    from scripts import (
        verify_citry_core_distribution,
        verify_citry_distribution,
        verify_citry_lsp_distribution,
        verify_citry_ui_distribution,
        verify_pygments_citry_distribution,
    )
except ImportError:  # Run as `python scripts/<name>.py`, where scripts/ itself is on sys.path.
    import verify_citry_core_distribution  # type: ignore[no-redef]
    import verify_citry_distribution  # type: ignore[no-redef]
    import verify_citry_lsp_distribution  # type: ignore[no-redef]
    import verify_citry_ui_distribution  # type: ignore[no-redef]
    import verify_pygments_citry_distribution  # type: ignore[no-redef]

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import ModuleType

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
# A file at or above this share of its cap gets a warning, early enough to
# raise the cap in an ordinary pull request.
WARN_PERCENT: Final = 90


class SizeCheckError(ValueError):
    """A file cannot be measured: it is missing or has no known cap."""


@dataclass(frozen=True, slots=True)
class CappedFile:
    """One kind of built file, the cap its release check enforces, and where that cap is written."""

    pattern: str
    max_bytes: int
    source: str


@dataclass(frozen=True, slots=True)
class SizeRecord:
    """One measured file."""

    name: str
    size: int
    cap: CappedFile

    @property
    def percent(self) -> int:
        """Return the share of the cap in use as a whole percent, rounded down, or up for a file over its cap."""
        # Rounding an over-cap file up keeps one byte over a large cap from
        # reading "100 percent", which is also what a file of exactly the cap
        # reads, and that file passes.
        if self.is_over_cap:
            return -(-self.size * 100 // self.cap.max_bytes)
        return self.size * 100 // self.cap.max_bytes

    @property
    def is_near_cap(self) -> bool:
        """Return whether the file is at 90 percent of its cap or more, which includes a file over its cap."""
        # Integer arithmetic keeps a file at exactly 90 percent from being
        # lost to float rounding.
        return self.size * 100 >= self.cap.max_bytes * WARN_PERCENT

    @property
    def is_over_cap(self) -> bool:
        """Return whether the file is larger than its cap."""
        # The release verifiers reject a file with `size > cap`, so a file of
        # exactly the cap passes here too; a stricter test would fail a pull
        # request that the release would accept.
        return self.size > self.cap.max_bytes


def _cap_in_bytes(value: object, *, source: str) -> int:
    """Return a cap read from a verifier as a whole number of bytes, refusing a value that is not a size."""
    # A verifier only compares file sizes with its cap, so a fractional cap such
    # as 1.5 * 1024 * 1024 works there and must work here. bool is a subclass of
    # int: a cap of True is really 1 byte and would warn about every file.
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 1:
        raise SizeCheckError(f"{source} must be a size of at least 1 byte, found {value!r}")
    return int(value)


def _module_cap(pattern: str, module: ModuleType, constant: str) -> CappedFile:
    """Read one cap from the verifier module that enforces it."""
    path = Path(str(module.__file__)).resolve().relative_to(REPO_ROOT).as_posix()
    source = f"{constant} in {path}"
    return CappedFile(pattern, _cap_in_bytes(getattr(module, constant, None), source=source), source)


def _citry_ui_wheel_cap() -> CappedFile:
    """Read the citry-ui wheel cap from its wheel check."""
    # The wheel check lives inside the citry_ui source tree, which is not
    # importable before the wheel is built, so the citry-ui verifier runs it by
    # path too.
    qualifier = verify_citry_ui_distribution.QUALIFIER
    source = f"MAX_WHEEL_BYTES in {qualifier.relative_to(REPO_ROOT).as_posix()}"
    try:
        value = runpy.run_path(str(qualifier))["MAX_WHEEL_BYTES"]
    except (OSError, KeyError) as error:
        # Running the file walks the citry_ui source tree, so a checkout
        # without it fails here, and a renamed constant fails on the lookup.
        raise SizeCheckError(f"could not read {source}: {error!r}") from error
    return CappedFile("citry_ui-[0-9]*.whl", _cap_in_bytes(value, source=source), source)


def capped_files() -> tuple[CappedFile, ...]:
    """
    Return every kind of built file that has a release cap.

    A file name matches the first pattern that fits. The citry and citry-core
    source distributions and the VS Code extension are not here: the first two
    have no cap, and the extension is not built by the pull request build.
    """
    return (
        _module_cap("citry-[0-9]*.whl", verify_citry_distribution, "MAX_WHEEL_BYTES"),
        _module_cap("citry_core-[0-9]*.whl", verify_citry_core_distribution, "MAX_WHEEL_BYTES"),
        _citry_ui_wheel_cap(),
        _module_cap("citry_ui-[0-9]*.tar.gz", verify_citry_ui_distribution, "MAX_SDIST_BYTES"),
        _module_cap("citry_lsp-[0-9]*.whl", verify_citry_lsp_distribution, "MAX_WHEEL_BYTES"),
        _module_cap("citry_lsp-[0-9]*.tar.gz", verify_citry_lsp_distribution, "MAX_SDIST_BYTES"),
        _module_cap("pygments_citry-[0-9]*.whl", verify_pygments_citry_distribution, "MAX_WHEEL_BYTES"),
        _module_cap("pygments_citry-[0-9]*.tar.gz", verify_pygments_citry_distribution, "MAX_SDIST_BYTES"),
    )


def measure(files: Sequence[Path], *, caps: Sequence[CappedFile] | None = None) -> list[SizeRecord]:
    """
    Return the size of each file next to its cap.

    Args:
        files: Built package files.
        caps: The known caps. The default reads them from the release verifiers.

    Raises:
        SizeCheckError: A path is not a file, or no cap matches its name.

    """
    known = capped_files() if caps is None else caps
    records: list[SizeRecord] = []
    for path in files:
        if not path.is_file():
            raise SizeCheckError(f"{path} is not a file; the build did not produce it")
        # Matching the name case-sensitively keeps the match the same on every operating system.
        cap = next((candidate for candidate in known if fnmatch.fnmatchcase(path.name, candidate.pattern)), None)
        if cap is None:
            raise SizeCheckError(f"{path.name} has no known size cap; add it to capped_files() in this script")
        records.append(SizeRecord(path.name, path.stat().st_size, cap))
    return records


def _escape_log_line(text: str) -> str:
    """Escape the three characters GitHub reads as workflow command syntax in a line of output."""
    # A file name with a newline and `::error::` in it would otherwise start a
    # second command on a line of its own, so every line that carries a name
    # goes through here. A listed name always starts with a package prefix, so
    # it cannot begin a command on its own line without a newline in it.
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def report_lines(records: Sequence[SizeRecord]) -> list[str]:
    """
    Return the log line for every file, then a GitHub Actions annotation for each file near or over its cap.

    A file over its cap gets an error, and a file at 90 percent of its cap or
    more but not over it gets a warning. No file gets both.
    """
    lines = [
        _escape_log_line(
            f"{record.name}: {record.size:,} of {record.cap.max_bytes:,} bytes ({record.percent} percent of its cap)"
        )
        for record in records
    ]
    # Every file is listed before any annotation, so one run reads as a table
    # of all the sizes and the annotations follow it.
    for record in records:
        # Each annotation names where the cap is written, because raising it
        # is the fix and the cap lives in a different file for each package.
        if record.is_over_cap:
            message = (
                f"{record.name} is {record.size:,} bytes, over its {record.cap.max_bytes:,}-byte release cap, "
                f"and the release would fail on it. If the growth is expected, raise {record.cap.source}; "
                "otherwise make the file smaller."
            )
            lines.append(f"::error title=Package over its release cap::{_escape_log_line(message)}")
        elif record.is_near_cap:
            message = (
                f"{record.name} is at {record.percent} percent of its {record.cap.max_bytes:,}-byte release cap "
                f"({record.size:,} bytes). If the growth is expected, raise {record.cap.source} before the release."
            )
            lines.append(f"::warning title=Package size at or near its release cap::{_escape_log_line(message)}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    """
    Print every file's size, warn about files near their cap, and fail on files over it.

    Returns:
        0 when every file is within its cap, and 1 when any file is over it.

    Raises:
        SystemExit: A file is missing or has no known cap, with status 1.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="built wheels and source distributions")
    args = parser.parse_args(argv)
    try:
        records = measure(args.files)
    except SizeCheckError as error:
        # The error text holds a path, which can hold a newline.
        parser.exit(1, _escape_log_line(f"package size check failed: {error}") + "\n")
    # The whole report prints before the verdict, so a failing run still shows
    # the size of every file and not only the one that failed.
    sys.stdout.write("\n".join(report_lines(records)) + "\n")
    over = sum(record.is_over_cap for record in records)
    if over:
        # CI merges the two streams, and a piped stdout is held back until exit
        # while stderr appears at once. Flush so the summary does not print
        # above the report it points to.
        sys.stdout.flush()
        # Counts only: each file's name is already in its error line above, so
        # no unescaped name is printed here.
        sys.stderr.write(
            f"package size check failed, files over their release cap: {over} of {len(records)} "
            "(see the errors above)\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
