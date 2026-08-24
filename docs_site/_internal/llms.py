"""
Write AI-readable navigation and bulk text files after the docs build.

The output follows the [llmstxt.org](https://llmstxt.org/) v2 proposal. It stays
small enough to scan first, uses H2-delimited file lists, and points each entry
at the page's generated Markdown companion. Agents can then fetch only the
pages they need.

The navigation tree supplies ordering and section names. Per-page build records
supply descriptions and prove that the linked Markdown companion was written.
Nothing here re-reads the output HTML.

``llms-full.txt`` remains a nonstandard bulk convenience for existing users.
Agents should start with ``llms.txt`` and fetch individual Markdown companions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.paths import clean_url_to_companion_url

if TYPE_CHECKING:
    from pathlib import Path

    from docs_site._internal.build import PageRecord
    from docs_site._internal.nav import NavItem, NavTree


def generate_llms_files(
    records: list[PageRecord],
    output_dir: Path,
    nav_tree: NavTree,
    *,
    site_url: str,
    site_name: str,
) -> tuple[int, int]:
    """Write the navigation and bulk files, returning their entry counts."""
    base = site_url.rstrip("/")
    by_url = {record.url.strip("/"): record for record in records}
    links = write_llms_txt(output_dir, nav_tree, by_url, site_url=base, site_name=site_name)
    pages = write_llms_full_txt(output_dir, nav_tree, by_url, site_url=base)
    return links, pages


def _markdown_url(site_url: str, path: str) -> str:
    """Return the deployed Markdown companion URL for one clean page path."""
    return f"{site_url}{clean_url_to_companion_url(path)}"


def _one_line(value: str) -> str:
    """Collapse prose so every machine-parsed file-list entry stays on one line."""
    return " ".join(value.split())


def _link_label(value: str) -> str:
    """Return one parser-safe Markdown link label."""
    return _one_line(value).replace("[", "&#91;").replace("]", "&#93;")


def _bullet(title: str, path: str, by_url: dict[str, PageRecord], site_url: str) -> str | None:
    """One llms.txt list entry: ``- [Title](url): description`` (description optional)."""
    record = by_url.get(path.strip("/"))
    if record is None or record.noindex:
        return None
    entry = f"- [{_link_label(title)}]({_markdown_url(site_url, path)})"
    description = _one_line(record.description)
    return f"{entry}: {description}" if description else entry


def _bullets(items: list[NavItem], by_url: dict[str, PageRecord], site_url: str) -> list[str]:
    """Return entries only for pages whose Markdown companions were built."""
    lines = [_bullet(item.title, item.path, by_url, site_url) for item in items if item.path.strip("/")]
    return [line for line in lines if line is not None]


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
    title = _one_line(home.title if home and home.title else site_name)
    summary = _one_line(home.description) if home else ""

    lines = [f"# {title}", ""]
    if summary:
        lines += [f"> {summary}", ""]

    count = 0
    for area in nav_tree.areas:
        area_lines = _bullets(area.items, by_url, site_url)
        if area_lines:
            lines += [f"## {_one_line(area.label)}", "", *area_lines, ""]
            count += len(area_lines)

        for group in area.groups:
            group_lines = _bullets(group.items, by_url, site_url)
            if not group_lines:
                continue
            # H2 is the proposal's file-list boundary. Prefixing the group keeps
            # repeated names such as "Components" distinct across site areas.
            lines += [f"## {_one_line(area.label)}: {_one_line(group.label)}", "", *group_lines, ""]
            count += len(group_lines)

    (output_dir / "llms.txt").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return count


def write_llms_full_txt(
    output_dir: Path,
    nav_tree: NavTree,
    by_url: dict[str, PageRecord],
    *,
    site_url: str,
) -> int:
    """Write the nonstandard bulk text export and return its page count."""
    items = ([nav_tree.home] if nav_tree.home is not None else []) + nav_tree.flat_pages()
    blocks: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.path.strip("/")
        record = by_url.get(key)
        if key in seen or record is None or record.noindex or not record.markdown_body.strip():
            continue
        seen.add(key)
        heading = item.title or record.title or item.path
        source_url = record.canonical or (f"{site_url}/{key}/" if key else f"{site_url}/")
        blocks.append(f"# {heading}\n\nSource: {source_url}\n\n{record.markdown_body.strip()}")

    if blocks:
        # A horizontal rule keeps page boundaries visible in the bulk export.
        (output_dir / "llms-full.txt").write_text("\n\n---\n\n".join(blocks) + "\n", encoding="utf-8")
    return len(blocks)
