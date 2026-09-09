"""Configure native tables to export their known NamedTuple classes directly."""

from __future__ import annotations

from typing import Any

from benchmarks.ownership_journal_probe.storage_probe import TABLES, install_storage

import citry.ownership as own

TUPLE_NEW = tuple.__new__


def configure(graph: Any, constructor: Any) -> None:
    """Set the constructor for four row tables and their shared invocation journal."""
    for name in TABLES:
        getattr(graph, name).set_tuple_constructor(constructor)
    graph._component_invocations.journal.set_tuple_constructor(constructor)


def install_export(native: Any, stats: dict[str, int]) -> tuple[Any, Any, Any]:
    """Return candidate, existing-native and production installation functions."""
    graph = own.OwnershipGraph
    base_enable, base_disable = install_storage(native, stats)
    base_enable()
    base_initialize = graph.__init__
    base_disable()

    def initialize(self: Any) -> None:
        base_initialize(self)
        configure(self, TUPLE_NEW)

    def candidate() -> None:
        base_enable()
        graph.__init__ = initialize

    return candidate, base_enable, base_disable
