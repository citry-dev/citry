"""Environment-file handling for isolated Citry app discovery."""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

from dotenv import dotenv_values

if TYPE_CHECKING:
    from collections.abc import Mapping
    from logging import LogRecord

MAX_ENVIRONMENT_FILE_BYTES: Final = 1024 * 1024
_PORTABLE_ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_DOTENV_LOGGER_NAME: Final = "dotenv.main"
_DOTENV_LINE_NUMBER = re.compile(r"\bline\s+(\d+)\b")


class EnvironmentFileError(ValueError):
    """A configured environment file cannot safely seed app discovery."""


class _DotenvWarningCapture(logging.Handler):
    """Collect parser warnings without allowing third-party text into status."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.lines: set[int] = set()
        self.invalid = False

    def emit(self, record: LogRecord) -> None:
        self.invalid = True
        match = _DOTENV_LINE_NUMBER.search(record.getMessage())
        if match is not None:
            self.lines.add(int(match.group(1)))


def resolve_environment_file(workspace: Path, configured: str) -> Path:
    """Resolve one client-provided path against the selected workspace."""
    if not configured.strip():
        raise EnvironmentFileError("must be a non-empty path")
    try:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = workspace / candidate
        return candidate.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise EnvironmentFileError("path is invalid") from exc


def worker_environment(environment_file: Path | None) -> dict[str, str] | None:
    """Return a worker-only environment, or inherit unchanged when unconfigured."""
    if environment_file is None:
        return None
    values = _environment_file_values(environment_file)
    return _merge_environment(os.environ, values, case_insensitive=sys.platform == "win32")


def _environment_file_values(environment_file: Path) -> dict[str, str]:
    try:
        stat = environment_file.stat()
    except OSError as exc:
        raise EnvironmentFileError("file does not exist or cannot be read") from exc
    if not environment_file.is_file():
        raise EnvironmentFileError("path is not a regular file")
    if stat.st_size > MAX_ENVIRONMENT_FILE_BYTES:
        raise EnvironmentFileError(f"file exceeds the {MAX_ENVIRONMENT_FILE_BYTES}-byte limit")

    capture = _DotenvWarningCapture()
    dotenv_logger = logging.getLogger(_DOTENV_LOGGER_NAME)
    previous_propagate = dotenv_logger.propagate
    dotenv_logger.addHandler(capture)
    dotenv_logger.propagate = False
    try:
        try:
            parsed = dotenv_values(environment_file, encoding="utf-8", interpolate=True)
        except (OSError, UnicodeError, ValueError) as exc:
            raise EnvironmentFileError("file is not valid UTF-8 dotenv data") from exc
    finally:
        dotenv_logger.propagate = previous_propagate
        dotenv_logger.removeHandler(capture)
    if capture.invalid:
        location = ""
        if capture.lines:
            joined = ", ".join(str(line) for line in sorted(capture.lines))
            location = f" at line {joined}" if len(capture.lines) == 1 else f" at lines {joined}"
        raise EnvironmentFileError(f"file contains invalid dotenv syntax{location}")

    values: dict[str, str] = {}
    for name, value in parsed.items():
        if _PORTABLE_ENVIRONMENT_NAME.fullmatch(name) is None:
            raise EnvironmentFileError(f"variable name {name!r} is not portable")
        if value is None:
            raise EnvironmentFileError(f"variable {name!r} has no value; use {name}= to set an empty value")
        if "\0" in value:
            raise EnvironmentFileError(f"variable {name!r} contains a NUL character")
        values[name] = value
    return values


def _merge_environment(
    inherited: Mapping[str, str],
    configured: Mapping[str, str],
    *,
    case_insensitive: bool,
) -> dict[str, str]:
    """Overlay configured values, collapsing Windows' case-insensitive keys."""
    result = dict(inherited)
    if not case_insensitive:
        result.update(configured)
        return result

    spelling = {name.casefold(): name for name in result}
    for name, value in configured.items():
        previous = spelling.get(name.casefold())
        if previous is not None and previous != name:
            result.pop(previous, None)
        result[name] = value
        spelling[name.casefold()] = name
    return result


__all__ = [
    "MAX_ENVIRONMENT_FILE_BYTES",
    "EnvironmentFileError",
    "resolve_environment_file",
    "worker_environment",
]
