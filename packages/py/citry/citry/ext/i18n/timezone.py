"""Load IANA time zones from Citry's pinned Python tzdata package."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib import metadata, resources
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@lru_cache(maxsize=1)
def tzdb_revision() -> str:
    """Identify the exact package-owned time-zone database used by Citry."""
    version = metadata.version("tzdata")
    source = resources.files("tzdata.zoneinfo").joinpath("tzdata.zi").read_bytes()
    return f"tzdata:{version}:sha256:{sha256(source).hexdigest()}"


@lru_cache(maxsize=256)
def load_time_zone(key: str) -> ZoneInfo:
    """Open one checked IANA zone without consulting the host's zoneinfo path."""
    if type(key) is not str or not key:
        raise ValueError("i18n time_zone must be an exact non-empty string.")
    if "\\" in key or key.startswith("/"):
        raise ValueError(f"Invalid IANA time-zone ID {key!r}.")
    parts = key.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValueError(f"Invalid IANA time-zone ID {key!r}.")

    target = resources.files("tzdata.zoneinfo").joinpath(*parts)
    if not target.is_file():
        raise ValueError(f"Unknown IANA time-zone ID {key!r}.")
    try:
        with target.open("rb") as handle:
            return ZoneInfo.from_file(handle, key=key)
    except (OSError, ValueError, ZoneInfoNotFoundError) as error:
        raise ValueError(f"Could not load IANA time-zone ID {key!r} from Citry's tzdata package.") from error


__all__ = ["load_time_zone", "tzdb_revision"]
