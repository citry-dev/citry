"""Install the explicit settlement state without compiling Python modules."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any

from benchmarks.settlement_state_probe.transform import transform

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "packages/py/citry/citry/component_render.py"


def install(changed: bool) -> dict[str, Any]:
    """Replace only the scheduler and add its state class in the live module globals."""
    from citry import component_render as runtime  # noqa: PLC0415

    if hasattr(runtime, "_SettlementState"):
        raise RuntimeError("Settlement candidate was already installed")
    generated, metadata = transform(SOURCE.read_text())
    tree = ast.parse(generated)
    # Retaining the module globals keeps callback-time helper replacement visible.
    selected = [
        node
        for node in tree.body
        if (isinstance(node, ast.ImportFrom) and node.module == "__future__")
        or (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in ("_SettlementState", "_settle_render"))
    ]
    if len([node for node in selected if isinstance(node, (ast.FunctionDef, ast.ClassDef))]) != 2:
        raise RuntimeError("Missing generated settlement definitions")
    if changed:
        code = compile(ast.Module(body=selected, type_ignores=[]), "<python-settlement-probe>", "exec")
        exec(code, vars(runtime))  # noqa: S102 - benchmark-only source transformation
    return {**metadata, "generated_sha256": hashlib.sha256(generated.encode()).hexdigest()}
