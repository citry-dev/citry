"""
Shared post-build HTML walker for the docs-site guards.

The ``SiteIndex`` parses every built HTML file exactly once and exposes a typed
view of each page: its links, anchors, assets, images, headings, and redirect
info. Every post-build guard reads from this index instead of re-parsing the
site, so the whole suite pays the parse cost a single time.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

import lxml.html  # type: ignore[import-untyped]
from lxml.etree import LxmlError  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from pathlib import Path

# URL schemes / prefixes that mark a link or asset as external (not a local path
# the link/asset guards should resolve against the build output).
_EXTERNAL_SCHEMES = ("http://", "https://", "//", "mailto:", "tel:", "javascript:", "data:")

# The generator meta tag DocPage emits; pages that carry it are full doc pages
# (content + reference), as opposed to standalone example demo pages.
_DOC_PAGE_MARKER = "citry docs builder"

# Markdown that should never survive into visible page text. Both signals are
# chosen to be effectively impossible in ordinary prose: an ATX heading opening
# a line, and inline link syntax. Bullet dashes are deliberately not listed,
# because a wrapped sentence can legitimately begin with one.
# A var() reference butted straight against the value that should follow it, as
# in `var(--bg)0%`. CSS requires the space; without it the declaration is void.
_GLUED_VAR_RE = re.compile(r"var\(--[a-zA-Z0-9_-]+\)(?=[0-9a-zA-Z.#])")

_MARKDOWN_LEAK_PATTERNS = (
    re.compile(r"^#{1,6}\s+\S"),
    re.compile(r"^\[[^\]]+\]\([^)\s]+\)"),
)

# A page that Vue builds in the browser ships its static HTML inside the JSON
# data block that configures the Citry app, not in <body>. The guards read that
# HTML too, or they would pass a page whose visible content they never saw.
_PREPARED_CONFIGURATION_XPATH = '//script[@type="application/json"][@data-citry-vue-document]'

# Markup the markdown pass leaves behind when it wraps raw HTML in paragraphs:
# an empty paragraph, or a paragraph opened right before a block element's
# opening or closing tag.
# A browser renders each as a visible gap or moves the content that follows.
_STRAY_MARKUP_PATTERNS = (
    re.compile(r"<p>\s*</p>"),
    re.compile(r"<p>\s*<(?:div|section|template)\b"),
    re.compile(r"<p>\s*</(?:div|section|template)>"),
)
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class LinkRef:
    """A single ``<a href>`` on a page, pre-parsed into path + fragment."""

    href: str  # the raw href attribute value
    target: str  # path portion only (no fragment); may be relative or absolute
    anchor: str  # the #fragment, or "" if none

    @property
    def is_external(self) -> bool:
        return self.href.startswith(_EXTERNAL_SCHEMES)

    @property
    def is_anchor_only(self) -> bool:
        return self.href.startswith("#")


@dataclass(frozen=True)
class AssetRef:
    """A local asset reference (``<img src>``, ``<script src>``, ``<link href>``)."""

    tag: str  # "img" | "script" | "link"
    src: str

    @property
    def is_external(self) -> bool:
        return self.src.startswith(_EXTERNAL_SCHEMES)


@dataclass(frozen=True)
class ImageRef:
    """An ``<img>`` with its alt text (None = attribute absent, "" = empty)."""

    src: str
    alt: str | None


@dataclass(frozen=True)
class Heading:
    """A rendered heading: its level (1-6), id (may be ""), and text."""

    level: int
    id: str
    text: str


@dataclass
class PageRecord:
    """Everything the guards need to know about one built HTML page."""

    rel_path: PurePosixPath  # path relative to the build dir, e.g. "concepts/foo/index.html"
    url: str  # clean URL form, e.g. "/concepts/foo/"
    parse_error: str | None = None
    is_doc_page: bool = False  # rendered through DocPage (vs an example demo)
    is_redirect_stub: bool = False
    redirect_target: str | None = None
    robots: str = ""  # <meta name="robots"> content, e.g. "index,follow"
    canonical: str = ""  # <link rel="canonical"> href
    anchors: set[str] = field(default_factory=set)  # id= values
    name_aliases: set[str] = field(default_factory=set)  # legacy <a name="..."> values
    links: list[LinkRef] = field(default_factory=list)
    assets: list[AssetRef] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    # Raw text of every <script type="application/ld+json"> block.
    jsonld_blocks: list[str] = field(default_factory=list)
    # Lines of visible text that still look like Markdown source, meaning the
    # markdown pass skipped a block that was meant to be rendered.
    markdown_leaks: list[str] = field(default_factory=list)
    # Inline CSS where a custom property lost the space before the next value,
    # which makes the browser discard the whole declaration.
    glued_css_vars: list[str] = field(default_factory=list)
    # Markup that the markdown pass wrapped in paragraphs or left unconsumed.
    stray_markup: list[str] = field(default_factory=list)
    # Static HTML fragments shipped inside a prepared Vue app's start script.
    prepared_html: list[str] = field(default_factory=list)

    @property
    def h1_count(self) -> int:
        return sum(1 for h in self.headings if h.level == 1)

    @property
    def label(self) -> str:
        """A human-friendly identifier for guard messages."""
        return str(self.rel_path)


def is_isolated_preview_page(page: PageRecord) -> bool:
    """Return whether a page is a UI preview with deliberately fictional navigation."""
    return "_previews" in page.rel_path.parts


class SiteIndex:
    """Parses a built docs site once and indexes every page for the guards."""

    def __init__(self, build_dir: Path) -> None:
        self.build_dir = build_dir
        self.pages: list[PageRecord] = []
        self._by_rel: dict[PurePosixPath, PageRecord] = {}
        self.built_page_paths: set[PurePosixPath] = set()

        for html_path in sorted(build_dir.rglob("*.html")):
            rel = PurePosixPath(html_path.relative_to(build_dir).as_posix())
            record = self._parse(html_path, rel)
            self.pages.append(record)
            self._by_rel[rel] = record
            self.built_page_paths.add(rel)

    def get_page(self, rel: PurePosixPath | None) -> PageRecord | None:
        return self._by_rel.get(rel) if rel is not None else None

    def _parse(self, path: Path, rel: PurePosixPath) -> PageRecord:
        text = path.read_text(encoding="utf-8")
        record = PageRecord(rel_path=rel, url=_rel_to_url(rel))

        # Parse leniently. We deliberately do NOT use recover=False: libxml2's
        # strict HTML parser treats `<a id="X" name="X">` as defining ID "X"
        # twice (HTML4 shares the id/name namespace for <a>), which the code-line
        # anchors emit on every page - a false positive almost everywhere. Real
        # duplicate `id=` attributes are detected precisely by the counter below.
        try:
            dom = lxml.html.fromstring(text)
        except LxmlError as e:
            record.parse_error = str(e)
            return record  # unparseable; nothing more to extract

        self._extract(dom, record)
        self._find_markdown_leaks(dom.xpath("//body"), record)
        self._find_glued_css_vars(dom, record)
        # A shell holds Citry's HTML for a part Vue builds in the browser,
        # written from component templates rather than Markdown, so an empty
        # element there is not a stray paragraph. Markdown inside it is raw
        # HTML the page also ships for Vue, which is checked below.
        served = _SCRIPT_RE.sub("", text)
        outside_shells = _without_shell_contents(served)
        self._find_stray_markup(outside_shells, record)
        # Raw HTML a page ships for Vue is checked like its body. The server
        # usually also writes it into the body, which the checks above
        # already read; checking it twice would count its headings twice.
        for fragment_html in _prepared_html(dom):
            record.prepared_html.append(fragment_html)
            if fragment_html in outside_shells:
                continue
            if fragment_html not in served:
                fragment = lxml.html.fragment_fromstring(fragment_html, create_parent="div")
                self._extract(fragment, record, seen_ids={})
                self._find_markdown_leaks([fragment], record)
            self._find_stray_markup(fragment_html, record)
        return record

    @staticmethod
    def _find_stray_markup(html: str, record: PageRecord) -> None:
        """Collect markup that the markdown pass wrapped in stray paragraphs."""
        for pattern in _STRAY_MARKUP_PATTERNS:
            record.stray_markup.extend(match.group().strip() for match in pattern.finditer(html))

    @staticmethod
    def _find_glued_css_vars(dom: lxml.html.HtmlElement, record: PageRecord) -> None:
        """Collect ``var(--x)`` references that lost the space before the next value."""
        for style in dom.xpath("//style"):
            css = style.text or ""
            for match in _GLUED_VAR_RE.finditer(css):
                record.glued_css_vars.append(css[match.start() : match.end() + 12])

    @staticmethod
    def _find_markdown_leaks(roots: list[lxml.html.HtmlElement], record: PageRecord) -> None:
        """
        Collect visible text that is still Markdown source rather than HTML.

        A raw-HTML wrapper without ``markdown="1"`` makes python-markdown skip
        everything nested inside it, so headings, bullets, and links reach the
        reader as literal ``###``, ``-``, and ``[text](url)``. The page still
        builds and every other guard still passes, so nothing else catches it.

        Only text a reader actually sees counts: anything inside code, script,
        style, or a text area is quoted on purpose.
        """
        nodes = [
            node
            for root in roots
            for node in root.xpath(
                ".//text()[not(ancestor::pre) and not(ancestor::code)"
                " and not(ancestor::script) and not(ancestor::style)"
                " and not(ancestor::textarea)]",
            )
        ]
        for node in nodes:
            for raw in str(node).split("\n"):
                line = raw.strip()
                if any(pattern.match(line) for pattern in _MARKDOWN_LEAK_PATTERNS):
                    record.markdown_leaks.append(line)

    def _extract(
        self, dom: lxml.html.HtmlElement, record: PageRecord, *, seen_ids: dict[str, int] | None = None
    ) -> None:
        seen_ids = {} if seen_ids is None else seen_ids
        for el in dom.iter():
            tag = el.tag
            if not isinstance(tag, str):
                continue  # comments / processing instructions

            el_id = el.get("id")
            if el_id:
                record.anchors.add(el_id)
                seen_ids[el_id] = seen_ids.get(el_id, 0) + 1

            if tag == "a":
                name = el.get("name")
                if name:
                    record.name_aliases.add(name)
                href = el.get("href")
                if href is not None:
                    record.links.append(_parse_link(href))
            elif tag == "img":
                src = el.get("src") or ""
                record.assets.append(AssetRef(tag="img", src=src))
                record.images.append(ImageRef(src=src, alt=el.get("alt")))
            elif tag == "script":
                src = el.get("src")
                if src:
                    record.assets.append(AssetRef(tag="script", src=src))
                elif (el.get("type") or "").lower() == "application/ld+json":
                    record.jsonld_blocks.append(el.text_content() or "")
            elif tag == "link":
                href = el.get("href")
                if href:
                    record.assets.append(AssetRef(tag="link", src=href))
                    if (el.get("rel") or "").lower() == "canonical":
                        record.canonical = href
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                record.headings.append(
                    Heading(level=int(tag[1]), id=el.get("id") or "", text=(el.text_content() or "").strip())
                )
            elif tag == "meta":
                self._read_meta(el, record)

        record.duplicate_ids.extend(i for i, n in seen_ids.items() if n > 1 and i not in record.duplicate_ids)

    @staticmethod
    def _read_meta(el: lxml.html.HtmlElement, record: PageRecord) -> None:
        # Pages rendered through DocPage carry this generator meta; example demo
        # pages do not. The content guards (single-h1, headings, alt-text) only
        # apply to real doc pages.
        if el.get("name") == "generator" and _DOC_PAGE_MARKER in (el.get("content") or ""):
            record.is_doc_page = True
        if el.get("name") == "robots":
            record.robots = el.get("content") or ""
        if (el.get("http-equiv") or "").lower() == "refresh":
            content = el.get("content") or ""
            _, _, url_part = content.partition("url=")
            if url_part:
                record.is_redirect_stub = True
                record.redirect_target = url_part.strip()

    def resolve_link(self, page_rel: PurePosixPath, target: str) -> PurePosixPath | None:
        """
        Resolve a link target (path only, no fragment) to a built page path.

        Handles clean URLs (``/foo/`` -> ``foo/index.html``) and relative links
        resolved against the source page's directory. Returns None if the target
        does not match any built page.
        """
        target = unquote(target)
        base = PurePosixPath(target.lstrip("/")) if target.startswith("/") else PurePosixPath(page_rel).parent / target
        # Normalize away "." and ".." segments.
        parts: list[str] = []
        for seg in base.parts:
            if seg == ".":
                continue
            if seg == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(seg)
        normalized = "/".join(parts)

        for candidate in _candidate_paths(normalized):
            cp = PurePosixPath(candidate)
            if cp in self.built_page_paths:
                return cp
        return None


def _candidate_paths(normalized: str) -> list[str]:
    """Clean-URL candidates for a normalized link target."""
    normalized = normalized.strip("/")
    if not normalized:
        return ["index.html"]
    candidates = [normalized]
    if normalized.endswith(".html"):
        return candidates
    candidates.append(f"{normalized}/index.html")
    candidates.append(f"{normalized}.html")
    return candidates


def strip_base_path(target: str, base_path: str) -> str:
    """Remove a deployment prefix from a local URL without changing its suffix."""
    base = "/" + base_path.strip("/") if base_path.strip("/") else ""
    if not base or not target.startswith("/"):
        return target
    suffix_index = len(target)
    for separator in ("?", "#"):
        index = target.find(separator)
        if index >= 0:
            suffix_index = min(suffix_index, index)
    path = target[:suffix_index]
    if path != base and not path.startswith(f"{base}/"):
        return target
    stripped = path[len(base) :] or "/"
    return stripped + target[suffix_index:]


def _parse_link(href: str) -> LinkRef:
    if href.startswith("#"):
        return LinkRef(href=href, target="", anchor=href[1:])
    parsed = urlparse(href)
    return LinkRef(href=href, target=parsed.path, anchor=parsed.fragment)


def _rel_to_url(rel: PurePosixPath) -> str:
    """Convert a built file path to its clean URL (foo/index.html -> /foo/)."""
    s = rel.as_posix()
    if s == "index.html":
        return "/"
    if s.endswith("/index.html"):
        return "/" + s[: -len("index.html")]
    if s.endswith(".html"):
        return "/" + s[: -len(".html")] + "/"
    return "/" + s


_VOID_TAGS = frozenset(
    ("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr")
)


class _ShellContents(HTMLParser):
    """Find the contents of each element marked ``data-allow-mismatch="children"``, as offsets."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self.line_starts = [0, *(match.end() for match in re.finditer("\n", html))]
        self.ranges: list[tuple[int, int]] = []
        self.depth = 0
        self.start = 0

    def _offset(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _VOID_TAGS:
            return
        if self.depth:
            self.depth += 1
        elif ("data-allow-mismatch", "children") in attrs:
            self.depth = 1
            self.start = self._offset() + len(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if self.depth and tag not in _VOID_TAGS:
            self.depth -= 1
            if not self.depth:
                self.ranges.append((self.start, self._offset()))


def _without_shell_contents(html: str) -> str:
    """Return the page HTML with the contents of each Vue shell element removed."""
    if 'data-allow-mismatch="children"' not in html:
        return html
    finder = _ShellContents(html)
    finder.feed(html)
    finder.close()
    output, position = [], 0
    for start, end in finder.ranges:
        output.append(html[position:start])
        position = end
    output.append(html[position:])
    return "".join(output)


def _prepared_html(dom: lxml.html.HtmlElement) -> list[str]:
    """Return the static HTML fragments a prepared Vue app carries, in page order."""
    fragments: list[str] = []
    for script in dom.xpath(_PREPARED_CONFIGURATION_XPATH):
        try:
            transport = json.loads(script.text or "")
        except ValueError:
            # Not a configuration this reader understands; it contributes no HTML.
            continue
        manifest = transport.get("manifest") if isinstance(transport, dict) else None
        occurrences = manifest.get("occurrences") if isinstance(manifest, dict) else None
        for occurrence in occurrences if isinstance(occurrences, list) else ():
            prepared = occurrence.get("preparedData") if isinstance(occurrence, dict) else None
            opaque = prepared.get("opaqueHtml") if isinstance(prepared, dict) else None
            for record in opaque.values() if isinstance(opaque, dict) else ():
                html = record.get("html") if isinstance(record, dict) else None
                if isinstance(html, str) and html.strip():
                    fragments.append(html)
    return fragments


def source_markdown(page: PageRecord, content_dir: Path) -> Path | None:
    """Return the Markdown file a built page came from, when one exists."""
    parts = page.rel_path.parts
    if not parts or not parts[-1].endswith(".html"):
        return None
    if parts[-1] == "index.html":
        stem = parts[:-1]
        candidates = [content_dir.joinpath(*stem, "index.md")]
        if stem:
            candidates.append(content_dir.joinpath(*stem[:-1], f"{stem[-1]}.md"))
    else:
        candidates = [content_dir.joinpath(*parts[:-1], parts[-1].removesuffix(".html") + ".md")]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def source_line(path: Path, text: str) -> int | None:
    """Return the 1-based line of the first source line that contains ``text``."""
    needle = text.strip()
    if not needle:
        return None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return number
    return None
