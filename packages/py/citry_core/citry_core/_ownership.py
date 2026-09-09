"""Internal storage for ownership records supplied by the Citry runtime."""

from citry_core import _rust

Journal = _rust.ownership.Journal
RecordTable = _rust.ownership.RecordTable
UnsupportedRetirement = _rust.ownership.UnsupportedRetirement

__all__ = ["Journal", "RecordTable", "UnsupportedRetirement"]
