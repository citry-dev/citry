from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FIXTURE = HERE / "fixtures" / "adversarial.ftl"
RUST_SOURCE = HERE / "src" / "main.rs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=REPO,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def source_manifest() -> dict[str, str]:
    paths = [
        HERE / "Cargo.lock",
        HERE / "Cargo.toml",
        FIXTURE,
        Path(__file__),
        RUST_SOURCE,
    ]
    return {path.relative_to(REPO).as_posix(): sha256(path) for path in sorted(paths)}


def no_python_asserts() -> bool:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    return not any(isinstance(node, ast.Assert) for node in ast.walk(tree))


def build_evidence() -> dict[str, Any]:
    raw = run(
        [
            "cargo",
            "run",
            "--quiet",
            "--locked",
            "--manifest-path",
            str(HERE / "Cargo.toml"),
            "--",
            str(FIXTURE),
        ]
    )
    probe = json.loads(raw)
    require(probe["result"] == "PASS_BOUNDED", f"unexpected probe result: {probe!r}")
    require(all(probe["gates"].values()), f"one or more Rust gates failed: {probe['gates']!r}")
    require(no_python_asserts(), "runner contains a load-bearing Python assert")

    lock = (HERE / "Cargo.lock").read_text(encoding="utf-8")
    require(
        'name = "fluent-syntax"\nversion = "0.12.0"' in lock,
        "Cargo.lock does not pin fluent-syntax 0.12.0",
    )

    return {
        "schema_version": 1,
        "result": "PASS_BOUNDED",
        "probe": probe,
        "upstream": {
            "repository": "https://github.com/projectfluent/fluent-rs",
            "inspected_main_commit": "b822cfe0ac5f35099ee71d3cf6f43b7c01d5fc6d",
            "existing_span_issue": "https://github.com/projectfluent/fluent-rs/issues/270",
            "duplicate_span_issue": "https://github.com/projectfluent/fluent-rs/issues/346",
            "main_ast_still_spanless": True,
            "slice_trait_public_on_main": True,
        },
        "environment": {
            "cargo": run(["cargo", "--version"]),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "python_optimize": int(os.environ.get("PYTHONOPTIMIZE", "0") or "0"),
            "rustc": run(["rustc", "--version"]),
        },
        "input_manifest": source_manifest(),
        "runner_has_no_assert_statements": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    evidence = build_evidence()
    rendered = json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if arguments.output is None:
        sys.stdout.write(rendered)
    else:
        arguments.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
