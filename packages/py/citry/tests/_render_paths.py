"""
Helpers for tests that compare Citry's native (Rust) render path with its Python one.

``render_both(run)`` calls ``run`` once on each path, in one process, and
checks that both returned the same value (or raised the same error). Every
input that would differ between two renders is pinned first: the component
render ids, the Vue app id, and the Events token clock. ``run`` passes its
own CSP nonce (``NONCE``) and builds its own engine, so nothing else varies.

Byte equality alone cannot show that the Rust path ran, because every part
of it hands an input it cannot handle back to Python silently. So each run
also counts, through spies on two Python functions, the rows Rust read and
the Rust-read rows whose Python leaf an output then rebuilt. Through a
stand-in for the Rust module and a spy on the manifest builder, it counts
the run objects ``_NativeRun.try_new`` built, the call runs it declined,
and the run objects the page manifests held. Through a spy on
``ForNode._walk_call_run``, it records each loop Rust walked and each reason
it gave for leaving a loop to Python's walk. The caller states how many it
expects.
"""

from __future__ import annotations

import itertools
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import pytest

from citry._vue import events, native_render
from citry._vue.leaf_program import LeafProgramNode
from citry.nodes import ForNode

if TYPE_CHECKING:
    from collections.abc import Callable

# Strict CSP needs a nonce; a fixed one keeps both runs the same.
NONCE = "nativerenderfixednonce"
# Events state tokens carry the time they were made.
FIXED_NOW = 1_800_000_000.0


@dataclass(frozen=True, slots=True)
class PathRun:
    """What one path produced, and how much of the Rust path it used."""

    # The value ``run`` returned, or ``describe_error()`` of what it raised.
    result: object
    # Rows Rust read (``LeafProgramNode.read_native_row`` returned a row).
    rows_read: int
    # Rust-read rows whose Python leaf an output built from Rust's copy.
    rows_rebuilt: int
    # Run objects the page manifests held (a run that assembly recorded with
    # one object), and their rows.
    runs_written: int = 0
    run_rows_written: int = 0
    # Run objects ``_NativeRun.try_new`` built, and the call runs it
    # declined. A built run object reaches no manifest when its ``commit``
    # refused it or the assembly failed later.
    runs_built: int = 0
    runs_declined: int = 0
    # Loops Rust walked (``ForNode._walk_call_run`` returned the rows), and
    # the reason of each loop it left to Python's walk, in render order.
    walks: int = 0
    walk_declines: tuple[str, ...] = ()


class _CountingModule:
    """
    Stand in for ``citry_core._rust.native_render`` and count what the run object does.

    Rust classes cannot be patched, so the spy replaces the module Citry
    reads (``native_render.native``) with this proxy. Every name passes
    through except ``_NativeRun``, whose stand-in has only a counting
    ``try_new``. The run objects themselves are the real ones, so every type
    check holds.
    """

    def __init__(self, real: Any, counts: dict[str, int]) -> None:
        self._real = real
        run_class = real._NativeRun

        class _NativeRun:
            @staticmethod
            def try_new(*args: Any) -> Any:
                run = run_class.try_new(*args)
                counts["built" if run is not None else "declined"] += 1
                return run

        self._NativeRun = _NativeRun

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


def describe_error(error: BaseException) -> dict[str, object]:
    """Describe an error by everything a user sees: type, message, the innermost frame, and its causes."""
    chain: list[tuple[str, str]] = []
    current = error.__cause__ or error.__context__
    while current is not None and len(chain) < 5:
        chain.append((type(current).__name__, str(current)))
        current = current.__cause__ or current.__context__
    frames = traceback.extract_tb(error.__traceback__)
    return {
        "error": type(error).__name__,
        "message": str(error),
        # The innermost frame is where user code or Citry raised; both
        # paths must raise from the same function.
        "raised_in": frames[-1].name if frames else None,
        "causes": chain,
    }


def _pin_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Restart every counter a render draws from, so the next run mints the same values."""
    # Ordinary components and simple='vue' rows draw render ids from two
    # module bindings of the same generator; both share one counter here.
    render_ids = itertools.count(1)
    monkeypatch.setattr("citry.component.gen_render_id", lambda: f"c{next(render_ids)}")
    monkeypatch.setattr("citry.component_render.gen_render_id", lambda: f"c{next(render_ids)}")
    app_ids = itertools.count()
    monkeypatch.setattr("citry._vue.serialization.token_hex", lambda _size: f"{next(app_ids):032x}")
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def run_on_path(run: Callable[[], object], monkeypatch: pytest.MonkeyPatch, *, rust: bool) -> PathRun:
    """Call ``run`` on one render path and count how much of the Rust path it used."""
    counts = {"read": 0, "rebuilt": 0, "walks": 0}
    walk_declines: list[str] = []
    walk_call_run = ForNode._walk_call_run
    run_counts = {"built": 0, "declined": 0, "written": 0, "run_rows": 0}
    read_native_row = LeafProgramNode.read_native_row
    render_native_snapshot = LeafProgramNode.render_native_snapshot
    prepared_manifest = events.prepared_manifest

    def counting_read(self: LeafProgramNode, variables: dict[str, object]) -> Any:
        row = read_native_row(self, variables)
        counts["read"] += row is not None
        return row

    def counting_manifest(**kwargs: Any) -> dict[str, object]:
        # The manifest is built once per assembly that reaches the page; the
        # writer that serializes it can run more than once (the Vue render
        # parity recorder writes it again), so the runs are counted here.
        manifest = prepared_manifest(**kwargs)
        for item in cast("list[object]", manifest["occurrences"]):
            if type(item) is native_render.NativeRun:
                run_counts["written"] += 1
                run_counts["run_rows"] += len(cast("Any", item))
        return manifest

    def counting_walk(self: ForNode, context: Any, run_class: Any) -> Any:
        walked = walk_call_run(self, context, run_class)
        if type(walked) is str:
            walk_declines.append(walked)
        else:
            counts["walks"] += 1
        return walked

    def counting_rebuild(self: LeafProgramNode, variables: dict[str, object], *, component_name: str) -> Any:
        counts["rebuilt"] += 1
        return render_native_snapshot(self, variables, component_name=component_name)

    with monkeypatch.context() as patch:
        patch.setattr(native_render, "ACTIVE", rust)
        patch.setattr(LeafProgramNode, "read_native_row", counting_read)
        patch.setattr(LeafProgramNode, "render_native_snapshot", counting_rebuild)
        patch.setattr(events, "prepared_manifest", counting_manifest)
        patch.setattr(ForNode, "_walk_call_run", counting_walk)
        if native_render.native is not None:
            patch.setattr(native_render, "native", _CountingModule(native_render.native, run_counts))
        _pin_inputs(patch)
        try:
            result = run()
        except Exception as error:  # noqa: BLE001 - compared between the paths
            result = describe_error(error)
    return PathRun(
        result,
        counts["read"],
        counts["rebuilt"],
        runs_written=run_counts["written"],
        run_rows_written=run_counts["run_rows"],
        runs_declined=run_counts["declined"],
        runs_built=run_counts["built"],
        walks=counts["walks"],
        walk_declines=tuple(walk_declines),
    )


def render_both(
    run: Callable[[], object],
    monkeypatch: pytest.MonkeyPatch,
    *,
    rows_read: int | None = None,
    rows_rebuilt: int | None = None,
    runs: tuple[int, int, int] | None = None,
    walks: tuple[int, tuple[str, ...]] | None = None,
) -> tuple[PathRun, PathRun]:
    """
    Run ``run`` on the Rust path and on the Python path, and check they agree.

    ``rows_read`` and ``rows_rebuilt``, when given, are the counts the Rust
    run must show, so a case cannot pass because both runs used Python.
    ``runs``, when given, is ``(run objects built, runs try_new declined,
    run objects the page manifests held)``; a built run object reaches no
    manifest when its ``commit`` refused it or the assembly failed later.
    ``walks``, when given, is ``(loops Rust walked, the reasons of the loops
    it left to Python's walk)``. The Python run must never read a row, make a
    run object or walk a loop in Rust. Returns both runs.
    """
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    rust = run_on_path(run, monkeypatch, rust=True)
    python = run_on_path(run, monkeypatch, rust=False)
    assert rust.result == python.result
    assert python.rows_read == 0
    assert python.rows_rebuilt == 0
    assert (python.runs_built, python.runs_declined, python.runs_written) == (0, 0, 0)
    assert (python.walks, python.walk_declines) == (0, ())
    if rows_read is not None:
        assert rust.rows_read == rows_read
    if rows_rebuilt is not None:
        assert rust.rows_rebuilt == rows_rebuilt
    if runs is not None:
        assert (rust.runs_built, rust.runs_declined, rust.runs_written) == runs
    if walks is not None:
        assert (rust.walks, rust.walk_declines) == walks
    return rust, python
