"""Validate authored ``<c-live-code>`` directives and their source modules."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files
from docs_site._internal.live_code import LiveCodeValidationError, load_live_source

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_FENCE_OPEN = re.compile(r"^(?P<indent>\s*)(?P<marker>`{3,}|~{3,})")
_DIRECTIVE_RE = re.compile(
    r"<(?P<tag>c-live-code)\b(?P<attrs>[^>]*)>",
    re.DOTALL | re.IGNORECASE,
)
_ATTR_RE = re.compile(r"(?P<name>[A-Za-z_][\w-]*)\s*=\s*(?P<quote>['\"])(?P<value>.*?)(?P=quote)", re.DOTALL)
_BARE_BOOLEAN_RE = re.compile(r"(?<![\w-])(?P<name>full_height|static)(?![\w-])")


def _mask_regions(source: str) -> str:
    chars = list(source)

    def mask(start: int, end: int) -> None:
        for index in range(start, end):
            if chars[index] != "\n":
                chars[index] = " "

    for match in re.finditer(r"<!--.*?-->", source, re.DOTALL):
        mask(match.start(), match.end())

    offset = 0
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        if not in_fence:
            opening = _FENCE_OPEN.match(line.rstrip("\r\n"))
            if opening:
                marker = opening.group("marker")
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
                mask(offset, offset + len(line))
            elif line.startswith(("    ", "\t")):
                mask(offset, offset + len(line))
            else:
                for inline in re.finditer(r"(`+)(.+?)\1", line):
                    mask(offset + inline.start(), offset + inline.end())
        else:
            mask(offset, offset + len(line))
            if stripped.startswith(fence_char * fence_len) and not stripped.startswith(fence_char * (fence_len + 1)):
                in_fence = False
        offset += len(line)
    return "".join(chars)


def _line(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, source in _source_files(ctx):
        masked = _mask_regions(source)
        for match in _DIRECTIVE_RE.finditer(masked):
            line = _line(source, match.start())
            attrs_text = match.group("attrs")
            attrs: dict[str, str] = {}
            spans: list[tuple[int, int]] = []
            duplicate = ""
            unexpected = ""
            problem = ""
            valued_boolean = ""
            if match.group("tag") != "c-live-code":
                problem = "tag name must be lowercase c-live-code"
            elif not attrs_text.rstrip().endswith("/"):
                problem = "directive must be self-closing"
            else:
                attrs_text = attrs_text.rstrip()[:-1]
                attrs = {}
                spans = []
                duplicate = ""
                for attr in _ATTR_RE.finditer(attrs_text):
                    name = attr.group("name")
                    if name in attrs:
                        duplicate = name
                    attrs[name] = attr.group("value")
                    if name in {"full_height", "static"}:
                        valued_boolean = name
                    spans.append(attr.span())
                remainder = list(attrs_text)
                for start, end in spans:
                    remainder[start:end] = " " * (end - start)
                for attr in _BARE_BOOLEAN_RE.finditer("".join(remainder)):
                    name = attr.group("name")
                    if name in attrs:
                        duplicate = name
                    attrs[name] = ""
                    start, end = attr.span()
                    remainder[start:end] = " " * (end - start)
                unexpected = "".join(remainder).strip()
            if not problem and duplicate:
                problem = f"attribute {duplicate!r} is repeated"
            elif not problem and unexpected:
                problem = f"attributes are malformed near {unexpected!r}"
            elif not problem and valued_boolean:
                problem = f"attribute {valued_boolean!r} must be value-less"
            elif not problem and (
                set(attrs) - {"path", "title", "full_height", "static"} or {"path", "title"} - set(attrs)
            ):
                missing = sorted({"path", "title"} - set(attrs))
                extra = sorted(set(attrs) - {"path", "title", "full_height", "static"})
                details = []
                if missing:
                    details.append(f"missing {', '.join(missing)}")
                if extra:
                    details.append(f"unsupported {', '.join(extra)}")
                problem = "; ".join(details)
            if problem:
                yield GuardResult.error(
                    guard="live_code",
                    message=f"Invalid <c-live-code> directive: {problem}.",
                    source=label,
                    line=line,
                )
                continue
            try:
                load_live_source(
                    attrs["path"],
                    repo_root=ctx.repo_root,
                    title=attrs["title"],
                    static="static" in attrs,
                )
            except LiveCodeValidationError as error:
                yield GuardResult.error(
                    guard="live_code",
                    message=f"Invalid <c-live-code> directive: {error}.",
                    source=label,
                    line=line,
                )
