"""Small, dependency-free helpers shared across the docs site."""

from __future__ import annotations


def lstrip_outside_pre(html: str) -> str:
    """
    Strip leading whitespace from each line, but keep it inside ``<pre>`` blocks.

    A ``<c-*>`` tag that renders a component injects the component's HTML into the
    markdown body. Flushing each line left (except inside ``<pre>``, where
    whitespace is significant) stops the markdown pass from mistaking the indented
    HTML for a code block.
    """
    lines = html.splitlines()
    result: list[str] = []
    in_pre = False
    for line in lines:
        if not in_pre and ("<pre>" in line or "<pre " in line):
            in_pre = True
        result.append(line if in_pre else line.lstrip())
        if in_pre and "</pre>" in line:
            in_pre = False
    return "\n".join(result)
