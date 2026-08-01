"""
AI-readable index files written after the build: ``/llms.txt`` and ``/llms-full.txt``.

``llms.txt`` follows the [llmstxt.org](https://llmstxt.org/) convention: a short,
navigation-ordered table of contents that an AI agent can fetch in one request.
``llms-full.txt`` concatenates every page's text so a model can read the whole
site at once.

Both are built from what the page build already produced: the navigation tree
for ordering, and the per-page records (title, description, and the expanded
markdown body) for the text. Nothing here re-reads the written HTML.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from docs_site._internal.build import PageRecord
    from docs_site._internal.nav import NavTree


def generate_llms_files(
    records: list[PageRecord],
    output_dir: Path,
    nav_tree: NavTree,
    *,
    site_url: str,
    site_name: str,
) -> tuple[int, int]:
    """Write llms.txt and llms-full.txt. Returns (llms_txt_links, llms_full_pages)."""
    base = site_url.rstrip("/")
    by_url = {record.url.strip("/"): record for record in records}
    links = write_llms_txt(output_dir, nav_tree, by_url, site_url=base, site_name=site_name)
    pages = write_llms_full_txt(output_dir, nav_tree, by_url, site_url=base)
    return links, pages


def _description(by_url: dict[str, PageRecord], path: str) -> str:
    """The page's front-matter description, or empty when there is no record for it."""
    record = by_url.get(path.strip("/"))
    return record.description if record else ""


def _bullet(title: str, path: str, by_url: dict[str, PageRecord], site_url: str) -> str:
    """One llms.txt list entry: ``- [Title](url): description`` (description optional)."""
    entry = f"- [{title}]({site_url}/{path.strip('/')}/)" if path.strip("/") else f"- [{title}]({site_url}/)"
    desc = _description(by_url, path)
    return f"{entry}: {desc}" if desc else entry


def write_llms_txt(
    output_dir: Path,
    nav_tree: NavTree,
    by_url: dict[str, PageRecord],
    *,
    site_url: str,
    site_name: str,
) -> int:
    """Write the llms.txt navigation index. Returns the number of link entries."""
    home = by_url.get("")
    title = (home.title if home and home.title else site_name).strip()
    summary = home.description if home and home.description else ""

    lines = [f"# {title}", ""]
    if summary:
        lines += [f"> {summary}", ""]

    count = 0
    for area in nav_tree.areas:
        area_lines: list[str] = []
        for item in area.items:
            # The root page already supplies the file title and summary.
            if not item.path.strip("/"):
                continue
            area_lines.append(_bullet(item.title, item.path, by_url, site_url))
            count += 1

        for group in area.groups:
            group_lines = [_bullet(item.title, item.path, by_url, site_url) for item in group.items]
            if not group_lines:
                continue
            if area_lines:
                area_lines.append("")
            area_lines += [f"### {group.label}", "", *group_lines]
            count += len(group_lines)

        if area_lines:
            lines += [f"## {area.label}", "", *area_lines, ""]

    (output_dir / "llms.txt").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return count


def write_llms_full_txt(
    output_dir: Path,
    nav_tree: NavTree,
    by_url: dict[str, PageRecord],
    *,
    site_url: str,
) -> int:
    """Write the full-text llms-full.txt. Returns the number of pages concatenated."""
    blocks: list[str] = []
    for item in nav_tree.flat_pages():
        record = by_url.get(item.path.strip("/"))
        if record is None or not record.markdown_body.strip():
            continue
        heading = item.title or record.title or item.path
        path = item.path.strip("/")
        url = f"{site_url}/{path}/" if path else f"{site_url}/"
        blocks.append(f"# {heading}\n\nSource: {url}\n\n{record.markdown_body.strip()}")

    if not blocks:
        return 0
    # A horizontal rule between pages keeps the boundaries clear for a reader.
    (output_dir / "llms-full.txt").write_text("\n\n---\n\n".join(blocks) + "\n", encoding="utf-8")
    return len(blocks)
