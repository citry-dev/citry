"""Probe a shared parts buffer while retaining deferred simple component calls."""

from __future__ import annotations

# ruff: noqa: S101 - presentation refuses optimized Python.
import hashlib
import itertools
import json
from typing import Any

from benchmarks.performance_followups.presentation import baseline, callback_counts, load

from citry import component_render as runtime
from citry.citry_render import CitryRender, unwrap_physical_region
from citry.nodes import ForNode, IfNode

ORIGINAL_BODY = runtime._render_body


def buffered_body(body: Any, context: Any) -> list[Any]:
    """Join simple control-flow text while retaining structured child renders."""
    if context._simple_scope is None or type(context.component).transparent or runtime.is_tracing():
        return ORIGINAL_BODY(body, context)
    output: list[Any] = []
    text: list[str] = []

    def emit(items: Any, current: Any) -> None:
        token = runtime._VALUE_CONTEXT.set(current)
        try:
            for item in items:
                if isinstance(item, str):
                    text.append(item)
                    continue
                try:
                    if type(item) is IfNode:
                        branch = item.active_branch_body(current)
                        if branch is not None:
                            emit(branch, current)
                        continue
                    if type(item) is ForNode and item._precomputed_text is None:
                        for branch, child in item.iter_bodies(current):
                            emit(branch, child)
                        continue
                    part = item.render(current)
                    if isinstance(part, str):
                        text.append(part)
                        continue
                    unwrapped = unwrap_physical_region(part)
                    if (
                        isinstance(unwrapped, CitryRender)
                        and unwrapped.context is not current
                        and not runtime._contains_deferred(unwrapped)
                    ):
                        runtime._merge_dependencies(current, unwrapped.context)
                    if text:
                        output.append("".join(text))
                        text.clear()
                    output.append(part)
                except Exception as error:
                    runtime._attach_template_position(error, item, current)
                    raise
        finally:
            runtime._VALUE_CONTEXT.reset(token)

    emit(body, context)
    if text:
        output.append("".join(text))
    return output


def install() -> None:
    """Replace only the process-local body walker for this research candidate."""
    runtime._render_body = buffered_body


def _qualify() -> dict[str, Any]:
    """Require identical full output and captures under the deferred public API."""
    runtime._render_body = ORIGINAL_BODY
    baseline.ids._id_base = 123456
    control, tree_hash = load()
    before, _ = baseline.observe(control, control.gen_render_data())
    callbacks = callback_counts(control)
    baseline.ids._id_counter = itertools.count()
    raw_control = control.render(control.gen_render_data())
    install()
    candidate, _ = load()
    after, _ = baseline.observe(candidate, candidate.gen_render_data())
    assert before == after
    assert callback_counts(candidate) == callbacks
    baseline.ids._id_counter = itertools.count()
    raw_candidate = candidate.render(candidate.gen_render_data())
    assert raw_candidate == raw_control
    return {
        "control": before,
        "candidate": after,
        "callbacks": callbacks,
        "scenario_sha256": tree_hash,
        "raw_sha256": hashlib.sha256(raw_control.encode()).hexdigest(),
    }


def qualify() -> dict[str, Any]:
    """Restore the caller's walker after the isolated qualification."""
    previous = runtime._render_body
    try:
        return _qualify()
    finally:
        runtime._render_body = previous


if __name__ == "__main__":
    print(json.dumps(qualify()))
