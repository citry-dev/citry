"""Small, dependency-free helpers shared across the docs site."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def lstrip_outside_pre(html: str) -> str:
    """
    Strip leading whitespace from each line, but keep it inside ``<pre>`` blocks.

    A ``<c-*>`` tag that renders a component injects the component's HTML into the
    markdown body. Flushing each line left (except inside ``<pre>``, where
    whitespace is significant) stops the markdown pass from mistaking the indented
    HTML for a code block.
    """
    return "\n".join(_walk_outside_pre(html, lambda line: line.lstrip()))


def flatten_for_markdown(html: str) -> str:
    """
    Wrap generated markup so the markdown pass leaves it exactly as it is.

    Markup injected into a page meets a pass that looks for markdown inside raw
    HTML, and it mangles this markup in two separate ways. It gives up part way
    through a subtree containing preformatted code, wrapping the remainder in
    stray paragraph tags; ``markdown="0"`` is that pass's own way of being told a
    subtree is finished HTML, and the attribute is consumed rather than reaching
    the page. It also judges the markup line by line, where a blank line ends the
    block and a four-space indent reads as a code block, so everything goes onto
    one line. Newlines inside ``<pre>`` are written as ``&#10;`` entities, which
    parse back to real newlines, leaving the rendered text and anything a reader
    copies unchanged.
    """
    joined = ""
    in_pre = False
    for raw in html.splitlines():
        opens_pre = not in_pre and ("<pre>" in raw or "<pre " in raw)
        if in_pre:
            # Indentation here is content, so the line survives whole.
            joined += "&#10;" + raw
        elif line := raw.strip():
            if not joined:
                joined = line
            elif joined.endswith(">") and line.startswith("<"):
                joined += line
            else:
                # A boundary next to text keeps one space so words do not run
                # together; tag against tag closes up.
                joined += " " + line
        if opens_pre:
            in_pre = True
        if in_pre and "</pre>" in raw:
            in_pre = False
    return f'<div markdown="0">{joined}</div>'


def _walk_outside_pre(html: str, transform: Callable[[str], str | None]) -> Iterator[str]:
    """
    Apply ``transform`` to every line outside a ``<pre>`` block, dropping ``None``.

    Lines inside ``<pre>`` are yielded untouched. The opening ``<pre>`` line is
    treated as outside the block, because whitespace before the tag sits outside
    the preformatted text and is what makes the markdown pass read the tag as an
    indented code block.
    """
    in_pre = False
    for line in html.splitlines():
        opens_pre = not in_pre and ("<pre>" in line or "<pre " in line)
        if in_pre:
            yield line
        else:
            replaced = transform(line)
            if replaced is not None:
                yield replaced
        if opens_pre:
            in_pre = True
        if in_pre and "</pre>" in line:
            in_pre = False
