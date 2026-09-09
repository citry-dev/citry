"""Keep eligible serialization frames in an isolated Rust session until assembly."""

from __future__ import annotations

import ast
import copy
import importlib.machinery
import importlib.util
import inspect
import textwrap
from pathlib import Path
from typing import Any

import citry.serialize as ser

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "target/release/libcitry_serializer_session_probe.dylib"
spec = importlib.util.spec_from_file_location(
    "citry_serializer_session_probe",
    ARTIFACT,
    loader=importlib.machinery.ExtensionFileLoader("citry_serializer_session_probe", str(ARTIFACT)),
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the serializer session probe")
NATIVE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(NATIVE)
ORIGINAL = ser.serialize_render_result
MARK = ser.mark_html
VALUED = ser._apply_valued_markers
COUNTS: dict[str, int] | None = None


def make_session(artifact: Any) -> Any:
    """Keep artifact serialization and changed marker helpers on the ordinary path."""
    if artifact is not None or ser.mark_html is not MARK or ser._apply_valued_markers is not VALUED:
        return None
    return NATIVE.Session(ser._RENDER_ID_ATTR)


def finish_session(session: Any) -> str:
    """Observe activation only after the native frame program is complete."""
    if COUNTS is not None:
        COUNTS["sessions"] = COUNTS.get("sessions", 0) + 1
        COUNTS["frames"] = COUNTS.get("frames", 0) + session.frame_count()
    return session.finish()


def assigned(statement: ast.AST, name: str) -> bool:
    """Locate exact phase boundaries in the current production function."""
    targets = statement.targets if isinstance(statement, ast.Assign) else []
    return any(isinstance(target, ast.Name) and target.id == name for target in targets)


def transformed() -> Any:
    """Change the two serializer passes while retaining surrounding policy and hooks."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(ORIGINAL)))
    function = tree.body[0]
    function.decorator_list = []
    start = next(
        index
        for index, node in enumerate(function.body)
        if isinstance(node, ast.While) and isinstance(node.test, ast.Name) and node.test.id == "stack"
    )
    end = next(index for index, node in enumerate(function.body) if assigned(node, "html"))
    original_loop = function.body[start]
    cut = next(index for index, node in enumerate(original_loop.body) if assigned(node, "root_markers"))
    native_loop = copy.deepcopy(original_loop)
    native_loop.body = (
        native_loop.body[:cut]
        + ast.parse(
            """
_serializer_session.add_frame(
    key, inherited, frame,
    [marker for marker in own_markers if "=" not in marker],
    [marker for marker in own_markers if "=" in marker],
    bool(children), placeholder_map,
)
for child_render, child_id in children:
    stack.append((child_render, key, None, child_id))
"""
        ).body
    )
    replacement = ast.parse(
        """
_serializer_session = _make_serializer_session(artifact)
if _serializer_session is None:
    pass
else:
    stack = [(root, None, None, root_key)]
"""
    ).body
    branch = replacement[-1]
    branch.body = function.body[start : end + 1]
    branch.orelse.append(native_loop)
    branch.orelse.extend(ast.parse("html = _finish_serializer_session(_serializer_session)").body)
    function.body[start : end + 1] = replacement
    tree = ast.fix_missing_locations(tree)
    ser.__dict__["_make_serializer_session"] = make_session
    ser.__dict__["_finish_serializer_session"] = finish_session
    namespace = {}
    exec(compile(tree, "<serializer-session-probe>", "exec"), ser.__dict__, namespace)  # noqa: S102
    return namespace["serialize_render_result"]


CANDIDATE = transformed()


def install(changed: bool) -> None:
    """Select a serializer before constructing the benchmark fixture."""
    ser.serialize_render_result = CANDIDATE if changed else ORIGINAL
