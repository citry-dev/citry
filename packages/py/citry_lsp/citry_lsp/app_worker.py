"""One-shot, transport-isolated Citry app discovery worker."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from citry import Citry


def _load_app(spec: str) -> Any:
    module_name, separator, attribute = spec.partition(":")
    if not separator or not module_name or not attribute:
        msg = "app must be 'module:attribute', e.g. 'myproject.app:engine'"
        raise ValueError(msg)
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _error_message(exc: BaseException) -> str:
    detail = str(exc)
    kind = type(exc).__name__
    return f"{kind}: {detail}" if detail else kind


def _run(app: str, workspace: Path) -> dict[str, object]:
    os.chdir(workspace)
    workspace_text = str(workspace)
    if workspace_text not in sys.path:
        sys.path.insert(0, workspace_text)
    engine = _load_app(app)
    if not isinstance(engine, Citry):
        msg = f"app target {app!r} is a {type(engine).__name__}, not a Citry instance"
        raise TypeError(msg)
    analysis = engine.template_analysis()
    catalog = engine.inspect_components(include_builtins=True, resolve_assets=True)
    return {
        "ok": True,
        "analysis": analysis.to_dict(),
        "catalog": catalog.to_dict(),
    }


def _captured_worker(app: str, workspace: Path) -> dict[str, object]:
    """Capture Python and file-descriptor output while project code runs."""
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with tempfile.TemporaryFile(mode="w+b") as output:
            os.dup2(output.fileno(), 1)
            os.dup2(output.fileno(), 2)
            try:
                payload = _run(app, workspace)
            except (BaseException, SystemExit) as exc:  # noqa: BLE001 - worker serializes all project failures
                payload = {"ok": False, "error": _error_message(exc)}
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
            output.seek(0)
            captured = output.read(16384).decode("utf-8", errors="replace").strip()
            if captured:
                payload["project_output"] = captured
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stderr_fd)
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True).encode("utf-8")
    os.write(stdout_fd, encoded)
    os.write(stdout_fd, b"\n")
    os.close(stdout_fd)
    return payload


def main(argv: list[str] | None = None) -> int:
    """Load one app and emit one JSON envelope to the parent server."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--app", required=True)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = _captured_worker(args.app, args.workspace.resolve())
    return 0 if payload.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__: list[str] = []
