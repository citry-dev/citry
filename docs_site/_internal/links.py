"""
Rewrite internal ``.md`` links in rendered HTML to clean relative URLs.

Pages are authored with internal links written the way the source tree looks,
``[X](foo/bar.md)``. The build serves clean URLs (``foo.md`` becomes ``/foo/``),
so every page lives one directory deeper than its source file and a raw ``.md``
href would not resolve in the browser. This pass rewrites each internal ``.md``
link to a relative URL that resolves correctly under that clean-URL scheme.

Links that are already clean URLs (``../other/``), external
(``https://example.com/...``), anchor-only (``#section``), or non-``.md`` are
left untouched, so it is safe to run over every page's content HTML.

Example, in a page built from ``content/test/pipeline_test.md`` (served at
``/test/pipeline_test/``):

    [another page](./other.md)   ->  [another page](../other/)
    [another page](../other/)    ->  unchanged (already a clean URL)
"""

from __future__ import annotations

import posixpath
import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from docs_site._internal.html_rewrite import StartTag, rewrite_attribute_values, rewrite_start_tags
from docs_site._internal.paths import md_to_url
from docs_site._internal.project import current_docs_project

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from docs_site._internal.nav import NavTree

_ROOT_OWNED_PREFIXES = ("/static/", "/citry/", "/v/")
_ROOT_OWNED_PATHS = frozenset({"/robots.txt", "/sitemap.xml", "/llms.txt", "/llms-full.txt"})

# The href of an anchor in the rendered HTML. python-markdown / Pygments emit
# double-quoted hrefs; code examples are HTML-escaped (&quot;), so this only
# matches real anchor attributes.
_HREF_RE = re.compile(r'href="([^"]*)"')

# The src attribute of images in the rendered HTML.
_SRC_RE = re.compile(r'src="([^"]*)"')

# Inline Markdown links and images. The destination is kept separate from an
# optional title so source companions can reuse the same clean-route resolver
# as rendered HTML without touching prose or fenced code.
_MD_LINK_RE = re.compile(
    r"(?P<prefix>!?\[[^\]\n]*\]\()"
    r"(?P<destination><[^>\n]+>|[^)\s\n]+)"
    r'(?P<suffix>(?:\s+["\'][^)\n]*["\'])?\))'
)
_MD_REFERENCE_DESTINATION_RE = re.compile(
    r"(?m)^(?P<prefix>[ \t]{0,3}\[[^\]\n]+\]:[ \t]*)(?P<destination><[^>\n]+>|[^\s\n]+)"
)
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_RAW_HTML_URL_ATTRS = frozenset(
    {"href", "src", "action", "formaction", "poster", "data-pagefind-path", "data-fragment-url"}
)

# Any heading that carries an id. Markdown headings and the raw-HTML
# API-reference symbol headings both emit the id first (the minifier reorders
# attributes later, but this runs before it). `.*?` captures just that heading's
# content, up to its own closing tag.
_HEADING_RE = re.compile(r'<h([1-6]) id="([^"]+)"([^>]*)>(.*?)</h\1>', re.DOTALL)

# The trailing ¤ permalink glyph that python-markdown adds to a markdown heading.
_PERMALINK_GLYPH_RE = re.compile(r'\s*<a class="headerlink"[^>]*>\xa4</a>\s*$')


def linkify_headings(html: str) -> str:
    """
    Make the whole heading its own permalink.

    A markdown heading renders as ``<h2 id="x">Title<a class="headerlink">¤</a></h2>``
    and an API-reference symbol heading as
    ``<h2 id="x" class="doc-heading"><span>...</span></h2>`` (no ¤). Both get their
    content wrapped in a link to their own anchor - ``<a class="heading-anchor"
    href="#x">...</a>`` - so the whole heading is clickable and underlines on hover
    (see ``.heading-anchor`` in site.css). The trailing ¤ glyph, when present, is
    dropped in favour of the whole-heading link. A heading whose content already
    holds a link is left untouched (an ``<a>`` must not nest inside another).
    """
    if "<h" not in html:
        return html

    def replace(match: re.Match[str]) -> str:
        level, hid, attrs, content = match.groups()
        body = _PERMALINK_GLYPH_RE.sub("", content)  # drop the ¤ glyph, if any
        if "<a " in body:  # content already links somewhere -> do not nest anchors
            return match.group(0)
        return f'<h{level} id="{hid}"{attrs}><a class="heading-anchor" href="#{hid}">{body}</a></h{level}>'

    return _HEADING_RE.sub(replace, html)


def rewrite_internal_md_links(
    html: str,
    *,
    source_path: Path,
    content_dir: Path,
    current_public_path: str = "",
    source_to_public_path: Mapping[Path, str] | None = None,
    nav_tree: NavTree | None = None,
    version_prefix: str = "",
) -> str:
    """
    Rewrite internal ``.md`` links in rendered HTML to clean relative URLs.

    A catalog-backed source may live outside ``content_dir`` when
    ``source_to_public_path`` or ``current_public_path`` gives it a public route.
    """
    content_root = content_dir.resolve()
    try:
        page_rel = source_path.resolve().relative_to(content_root)
    except ValueError:
        page_rel = None

    page_url = current_public_path or _public_url_for_source(
        source_path,
        source_to_public_path=source_to_public_path,
    )
    if not page_url:
        if page_rel is None:
            return html
        page_url = "/" + md_to_url(page_rel)  # e.g. "/test/pipeline_test/"
    elif not page_url.startswith("/"):
        page_url = "/" + page_url
    source_dir = source_path.resolve().parent

    def replace_href(match: re.Match[str]) -> str:
        href = match.group(1)
        rewritten = _rewrite_one(
            href,
            page_url=page_url,
            source_dir=source_dir,
            content_root=content_root,
            source_to_public_path=source_to_public_path,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
        return f'href="{rewritten}"'

    def replace_src(match: re.Match[str]) -> str:
        src = match.group(1)
        rewritten = _rewrite_asset(
            src,
            page_url=page_url,
            source_dir=source_dir,
            content_root=content_root,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
        if rewritten == src:
            rewritten = _project_clean_route(
                src,
                page_url=page_url,
                nav_tree=nav_tree,
                version_prefix=version_prefix,
            )
        return f'src="{rewritten}"'

    html = _HREF_RE.sub(replace_href, html)
    return _SRC_RE.sub(replace_src, html)


def rewrite_internal_md_links_in_markdown(
    source: str,
    *,
    source_path: Path,
    content_dir: Path,
    current_public_path: str = "",
    source_to_public_path: Mapping[Path, str] | None = None,
    nav_tree: NavTree | None = None,
    version_prefix: str = "",
) -> str:
    """Rewrite Markdown destinations while leaving fenced examples untouched."""
    content_root = content_dir.resolve()
    try:
        page_rel = source_path.resolve().relative_to(content_root)
    except ValueError:
        page_rel = None

    page_url = current_public_path or _public_url_for_source(
        source_path,
        source_to_public_path=source_to_public_path,
    )
    if not page_url:
        if page_rel is None:
            return source
        page_url = "/" + md_to_url(page_rel)
    elif not page_url.startswith("/"):
        page_url = "/" + page_url
    source_dir = source_path.resolve().parent

    in_fence = False
    fence_marker = ""
    lines: list[str] = []
    for line in source.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            destination = match.group("destination")
            wrapped = destination.startswith("<") and destination.endswith(">")
            raw = destination[1:-1] if wrapped else destination
            rewritten = _rewrite_one(
                raw,
                page_url=page_url,
                source_dir=source_dir,
                content_root=content_root,
                source_to_public_path=source_to_public_path,
                nav_tree=nav_tree,
                version_prefix=version_prefix,
            )
            if wrapped:
                rewritten = f"<{rewritten}>"
            return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

        lines.append(_MD_LINK_RE.sub(replace, line))
    return "".join(lines)


def project_internal_html_urls(
    html: str,
    *,
    current_public_path: str,
    nav_tree: NavTree | None,
    version_prefix: str,
) -> str:
    """Project clean links in generated HTML that has no authored source path."""
    if not version_prefix or nav_tree is None:
        return html
    page_url = current_public_path if current_public_path.startswith("/") else f"/{current_public_path}"

    def project(value: str) -> str:
        return _project_clean_route(
            value,
            page_url=page_url,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )

    def replace_href(match: re.Match[str]) -> str:
        return f'href="{project(match.group(1))}"'

    def replace_src(match: re.Match[str]) -> str:
        return f'src="{project(match.group(1))}"'

    return _SRC_RE.sub(replace_src, _HREF_RE.sub(replace_href, html))


def project_internal_markdown_urls(
    source: str,
    *,
    current_public_path: str,
    nav_tree: NavTree | None,
    version_prefix: str,
) -> str:
    """Project clean destinations in generated Markdown without a source path."""
    if not version_prefix or nav_tree is None:
        return source
    page_url = current_public_path if current_public_path.startswith("/") else f"/{current_public_path}"
    in_fence = False
    fence_marker = ""
    lines: list[str] = []
    for line in source.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            destination = match.group("destination")
            wrapped = destination.startswith("<") and destination.endswith(">")
            raw = destination[1:-1] if wrapped else destination
            projected = _project_clean_route(
                raw,
                page_url=page_url,
                nav_tree=nav_tree,
                version_prefix=version_prefix,
            )
            if wrapped:
                projected = f"<{projected}>"
            return f"{match.group('prefix')}{projected}{match.group('suffix')}"

        lines.append(_MD_LINK_RE.sub(replace, line))
    return "".join(lines)


def project_markdown_base_path(source: str, base_path: str) -> str:
    """Prefix root-relative Markdown destinations for a subpath deployment."""
    base = "/" + base_path.strip("/") if base_path.strip("/") else ""
    if not base:
        return source

    def project(destination: str) -> str:
        parsed = urlparse(destination)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
            return destination
        return _join_url_parts(f"{base}{parsed.path}", parsed.query, parsed.fragment)

    def project_destination(match: re.Match[str]) -> str:
        destination = match.group("destination")
        wrapped = destination.startswith("<") and destination.endswith(">")
        raw = destination[1:-1] if wrapped else destination
        projected = project(raw)
        if wrapped:
            projected = f"<{projected}>"
        return f"{match.group('prefix')}{projected}{match.groupdict().get('suffix', '')}"

    def project_html_tag(tag: StartTag) -> str:
        return rewrite_attribute_values(
            tag.source,
            lambda name, value: project(value) if name in _RAW_HTML_URL_ATTRS else value,
        )

    def project_chunk(chunk: str) -> str:
        chunk = _MD_LINK_RE.sub(project_destination, chunk)
        chunk = _MD_REFERENCE_DESTINATION_RE.sub(project_destination, chunk)
        return rewrite_start_tags(chunk, project_html_tag)

    in_fence = False
    fence_marker = ""
    lines: list[str] = []
    prose: list[str] = []

    def flush_prose() -> None:
        if prose:
            lines.append(project_chunk("".join(prose)))
            prose.clear()

    for line in source.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if fence:
            flush_prose()
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue
        prose.append(line)
    flush_prose()
    return "".join(lines)


def _rewrite_one(
    href: str,
    *,
    page_url: str,
    source_dir: Path,
    content_root: Path,
    source_to_public_path: Mapping[Path, str] | None = None,
    nav_tree: NavTree | None = None,
    version_prefix: str = "",
) -> str:
    parsed = urlparse(href)

    # Leave external links, schemes, protocol-relative, and anchor-only links alone.
    if parsed.scheme or parsed.netloc or not parsed.path:
        return href

    # Non-`.md` links: clean URLs pass through, but a link that targets a real
    # asset file (e.g. a clickable screenshot) needs the same depth correction
    # as an image src.
    if not parsed.path.endswith(".md"):
        rewritten_asset = _rewrite_asset(
            href,
            page_url=page_url,
            source_dir=source_dir,
            content_root=content_root,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
        if rewritten_asset != href:
            return rewritten_asset
        return _project_clean_route(
            href,
            page_url=page_url,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )

    # Resolve the target's source path (absolute links are content-root-relative).
    if parsed.path.startswith("/"):
        target_abs = (content_root / parsed.path.lstrip("/")).resolve()
    else:
        target_abs = (source_dir / parsed.path).resolve()

    target_url = _public_url_for_source(
        target_abs,
        source_to_public_path=source_to_public_path,
    )

    # A link outside the content tree needs an explicit catalog route.
    try:
        target_rel = target_abs.relative_to(content_root)
    except ValueError:
        if not target_url:
            return href
        target_rel = None

    if not target_url:
        if target_rel is None:  # pragma: no cover - guarded above
            return href
        target_url = "/" + md_to_url(target_rel)  # e.g. "/test/other/"

    # A cross-scope link from a snapshot must escape to the site root. Links to
    # another versioned page stay relative so they remain in the same snapshot.
    if version_prefix and nav_tree is not None and nav_tree.scope_for_url(target_url) == "site":
        return _join_url_parts(target_url, parsed.query, parsed.fragment)

    # Relative href from the current page's URL directory to the target.
    rel = posixpath.relpath(target_url, page_url)
    if target_url.endswith("/") and not rel.endswith("/"):
        rel += "/"

    if parsed.query:
        rel += "?" + parsed.query
    if parsed.fragment:
        rel += "#" + parsed.fragment

    return rel


def _public_url_for_source(
    source_path: Path,
    *,
    source_to_public_path: Mapping[Path, str] | None,
) -> str:
    """Return a catalog override for ``source_path``, or an empty string."""
    if not source_to_public_path:
        return ""
    resolved = source_path.resolve()
    mapped = source_to_public_path.get(resolved)
    if mapped is None:
        # Accept callers that built the mapping from unresolved content paths,
        # while keeping resolved keys as the preferred catalog contract.
        mapped = source_to_public_path.get(source_path)
    if not mapped:
        return ""
    clean = mapped.strip("/")
    return f"/{clean}/" if clean else "/"


def _rewrite_asset(
    ref: str,
    *,
    page_url: str,
    source_dir: Path,
    content_root: Path,
    nav_tree: NavTree | None = None,
    version_prefix: str = "",
) -> str:
    """
    Rewrite a relative asset reference (image etc.) authored against the source
    tree into a URL relative to the page's clean URL.

    Pages live one directory deeper in the URL space than in the source tree
    (``foo.md`` becomes ``/foo/``), so a source-relative ``../images/x.png`` needs
    one more ``../`` in the built page. Only refs that resolve to a real file
    inside the content tree are touched; clean URLs, external refs, and absolute
    paths pass through.
    """
    parsed = urlparse(ref)
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
        return ref

    target_abs = (source_dir / parsed.path).resolve()
    if not target_abs.is_file():
        return ref
    try:
        target_rel = target_abs.relative_to(content_root)
    except ValueError:
        return ref

    target_url = "/" + target_rel.as_posix()
    if version_prefix and nav_tree is not None and nav_tree.scope_for_url(target_url) == "site":
        return _join_url_parts(target_url, parsed.query, parsed.fragment)
    rel = posixpath.relpath(target_url, page_url)
    if parsed.query:
        rel += "?" + parsed.query
    if parsed.fragment:
        rel += "#" + parsed.fragment
    return rel


def _project_clean_route(
    href: str,
    *,
    page_url: str,
    nav_tree: NavTree | None,
    version_prefix: str,
) -> str:
    """Project a clean page/asset URL according to its declared scope."""
    if not version_prefix or nav_tree is None:
        return href
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return href
    pagefind_dir = current_docs_project().settings.pagefind_path.rsplit("/", 1)[0]
    root_owned_prefixes = (*_ROOT_OWNED_PREFIXES, f"{pagefind_dir}/")
    if parsed.path in _ROOT_OWNED_PATHS or parsed.path.startswith(root_owned_prefixes):
        return href

    if parsed.path.startswith("/"):
        target_url = parsed.path
        projected = nav_tree.project_path(target_url, version_prefix)
        return _join_url_parts(projected, parsed.query, parsed.fragment)

    target_url = posixpath.normpath(posixpath.join(page_url, parsed.path))
    if not target_url.startswith("/"):
        target_url = "/" + target_url
    if parsed.path.endswith("/") and not target_url.endswith("/"):
        target_url += "/"
    if nav_tree.scope_for_url(target_url) == "site":
        return _join_url_parts(target_url, parsed.query, parsed.fragment)
    return href


def _join_url_parts(path: str, query: str, fragment: str) -> str:
    result = path
    if query:
        result += "?" + query
    if fragment:
        result += "#" + fragment
    return result
