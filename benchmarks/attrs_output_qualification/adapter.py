"""Compare ordinary compact keys with the archived nested-key formatter."""

from __future__ import annotations
import __future__

import os
import textwrap
from pathlib import Path

from citry import attrs, nodes
from citry_core import _rust

ROOT = Path(__file__).resolve().parent
ARTIFACT = Path(_rust.__file__)
CANDIDATE = nodes.ElementAttrsNode._format
source = (ROOT / "reference_format.py.txt").read_text()
line = int((ROOT / "reference_line.txt").read_text())
# Retain the original filename and line positions while sharing live module globals.
exec(  # noqa: S102 - archived reference method used only by this comparison
    compile(
        "\n" * (line - 1) + textwrap.dedent(source),
        CANDIDATE.__code__.co_filename,
        "exec",
        flags=__future__.annotations.compiler_flag,
    ),
    nodes.__dict__,
)
ORIGINAL = nodes.__dict__.pop("_format")
FALLBACK = os.environ.get("CITRY_ATTRS_OUTPUT_PYTHON") == "1"
BUILDER = attrs._python_attrs_output_key if FALLBACK else _rust.attrs.output_cache_key


def install(changed: bool) -> None:
    """Use one builder and empty cache consistently throughout each variant."""
    nodes._attrs_output_cache.clear()
    nodes._build_attrs_output_key = BUILDER
    nodes.ElementAttrsNode._format = CANDIDATE if changed else ORIGINAL
