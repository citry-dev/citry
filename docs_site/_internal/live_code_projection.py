"""Plain-text projection for rich inline live-code blocks."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.live_code import decode_live_projection, load_live_source

if TYPE_CHECKING:
    from pathlib import Path

_BLOCK_RE = re.compile(
    r"<!-- docs-live-code:(?P<payload>[A-Za-z0-9_-]+):start -->.*?"
    r"<!-- docs-live-code:(?P=payload):end -->",
    re.DOTALL,
)


def project_live_code_for_text(source: str, *, repo_root: Path, allow_citry_ui: bool = False) -> str:
    """Replace rich live-code HTML with its canonical source-first Markdown."""

    def replace(match: re.Match[str]) -> str:
        path, title, static = decode_live_projection(match.group("payload"))
        code = load_live_source(
            path,
            repo_root=repo_root,
            title=title,
            static=static,
            allow_citry_ui=allow_citry_ui,
        ).rstrip()
        longest_run = max((len(run) for run in re.findall(r"`+", code)), default=0)
        fence = "`" * max(4, longest_run + 1)
        return f"### {title}\n\n{fence}citry\n{code}\n{fence}"

    return _BLOCK_RE.sub(replace, source)
