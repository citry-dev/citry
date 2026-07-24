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

from docs_site._internal.paths import md_to_url

if TYPE_CHECKING:
    from pathlib import Path

# The href of an anchor in the rendered HTML. python-markdown / Pygments emit
# double-quoted hrefs; code examples are HTML-escaped (&quot;), so this only
# matches real anchor attributes.
_HREF_RE = re.compile(r'href="([^"]*)"')

# The src attribute of images in the rendered HTML.
_SRC_RE = re.compile(r'src="([^"]*)"')

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


def rewrite_internal_md_links(html: str, *, source_path: Path, content_dir: Path) -> str:
    """
    Rewrite internal ``.md`` links in rendered HTML to clean relative URLs.

    Returns the HTML unchanged when the source file is not under ``content_dir``
    (for example a generated page rendered from outside the content tree).
    """
    content_root = content_dir.resolve()
    try:
        page_rel = source_path.resolve().relative_to(content_root)
    except ValueError:
        return html

    page_url = "/" + md_to_url(page_rel)  # e.g. "/test/pipeline_test/"
    source_dir = source_path.resolve().parent

    def replace_href(match: re.Match[str]) -> str:
        href = match.group(1)
        rewritten = _rewrite_one(href, page_url=page_url, source_dir=source_dir, content_root=content_root)
        return f'href="{rewritten}"'

    def replace_src(match: re.Match[str]) -> str:
        src = match.group(1)
        rewritten = _rewrite_asset(src, page_url=page_url, source_dir=source_dir, content_root=content_root)
        return f'src="{rewritten}"'

    html = _HREF_RE.sub(replace_href, html)
    return _SRC_RE.sub(replace_src, html)


def _rewrite_one(href: str, *, page_url: str, source_dir: Path, content_root: Path) -> str:
    parsed = urlparse(href)

    # Leave external links, schemes, protocol-relative, and anchor-only links alone.
    if parsed.scheme or parsed.netloc or not parsed.path:
        return href

    # Non-`.md` links: clean URLs pass through, but a link that targets a real
    # asset file (e.g. a clickable screenshot) needs the same depth correction
    # as an image src.
    if not parsed.path.endswith(".md"):
        return _rewrite_asset(href, page_url=page_url, source_dir=source_dir, content_root=content_root)

    # Resolve the target's source path (absolute links are content-root-relative).
    if parsed.path.startswith("/"):
        target_abs = (content_root / parsed.path.lstrip("/")).resolve()
    else:
        target_abs = (source_dir / parsed.path).resolve()

    # A link that points outside the content tree is left untouched.
    try:
        target_rel = target_abs.relative_to(content_root)
    except ValueError:
        return href

    target_url = "/" + md_to_url(target_rel)  # e.g. "/test/other/"

    # Relative href from the current page's URL directory to the target.
    rel = posixpath.relpath(target_url, page_url)
    if target_url.endswith("/") and not rel.endswith("/"):
        rel += "/"

    if parsed.fragment:
        rel += "#" + parsed.fragment

    return rel


def _rewrite_asset(ref: str, *, page_url: str, source_dir: Path, content_root: Path) -> str:
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
    rel = posixpath.relpath(target_url, page_url)
    if parsed.fragment:
        rel += "#" + parsed.fragment
    return rel
