"""
Discover, validate, and project authored documentation Blog posts.

The Blog keeps dated Markdown source files while publishing stable slug URLs.
This module owns the strict authored metadata contract and derives every
catalog-level projection from one immutable model. Rendering, output writes,
and request routing remain with the docs build and development server.
"""

from __future__ import annotations

import math
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import MappingProxyType
from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

import markdown
import yaml
from lxml import html as lxml_html

from docs_site._internal.nav import NavItem

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import Path


BLOG_INDEX_PATH = "/blog/"
BLOG_FEED_PATH = "/blog/feed.xml"
BLOG_LIST_START = "<!-- docs-blog-list:start -->"
BLOG_LIST_END = "<!-- docs-blog-list:end -->"

_POST_NAME_RE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md")
_KEY_RE = re.compile(r"[a-z][a-z0-9_]*")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})")
_ATX_H1_RE = re.compile(r"^ {0,3}#(?:\s+|$)")
_SETEXT_H1_RE = re.compile(r"^ {0,3}=+\s*$")
_RAW_H1_RE = re.compile(r"<h1(?:\s|>)", re.IGNORECASE)
_BLOG_LIST_TAG_RE = re.compile(r"<c-blog-list\b[^>]*>", re.DOTALL)
_PARAMETERLESS_BLOG_LIST_RE = re.compile(r"<c-blog-list\s*/>", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_WORD_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
_BLOG_LIST_BLOCK_RE = re.compile(
    rf"{re.escape(BLOG_LIST_START)}.*?{re.escape(BLOG_LIST_END)}",
    re.DOTALL,
)

_REQUIRED_KEYS = frozenset({"title", "description", "date", "author"})
_OPTIONAL_KEYS = frozenset(
    {
        "updated",
        "author_url",
        "tags",
        "og_image",
        "noindex",
        "searchable",
        "boost",
    }
)
_ALLOWED_KEYS = _REQUIRED_KEYS | _OPTIONAL_KEYS
_TRUTHY = frozenset({"true", "1", "yes", "on"})
_FALSY = frozenset({"false", "0", "no", "off"})
_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
_ATOM_NS = "http://www.w3.org/2005/Atom"
_FEED_LIMIT = 20
_WORDS_PER_MINUTE = 200


class BlogCatalogError(ValueError):
    """One invalid Blog source value, with its authored location when known."""

    def __init__(self, source: Path, message: str, *, line: int | None = None) -> None:
        self.source = source
        self.line = line
        self.message = message
        location = f"{source}:{line}" if line is not None else str(source)
        super().__init__(f"{location}: {message}")


@dataclass(frozen=True)
class BlogPost:
    """One validated dated post and its stable public identity."""

    source_path: Path
    source_rel: Path
    source: str
    body: str
    slug: str
    public_path: str
    title: str
    description: str
    published: datetime
    updated: datetime | None
    author: str
    author_url: str
    tags: tuple[str, ...]
    og_image: str
    noindex: bool
    searchable: bool
    boost: float
    reading_minutes: int

    @property
    def effective_updated(self) -> datetime:
        """The timestamp consumers use for the post's latest editorial state."""
        return self.updated or self.published

    @property
    def date_iso(self) -> str:
        """The publication timestamp for machine-readable markup."""
        return self.published.isoformat()

    @property
    def date_label(self) -> str:
        """A compact, locale-independent publication label."""
        return f"{self.published.day} {_MONTHS[self.published.month - 1]} {self.published.year}"


@dataclass(frozen=True)
class BlogCatalog:
    """The immutable accepted Blog source tree, newest posts first."""

    blog_dir: Path
    index_path: Path | None
    posts: tuple[BlogPost, ...] = ()
    source_to_public_path: Mapping[Path, str] = field(default_factory=lambda: MappingProxyType({}))
    _by_public_path: Mapping[str, BlogPost] = field(default_factory=lambda: MappingProxyType({}), repr=False)
    _by_source: Mapping[Path, BlogPost] = field(default_factory=lambda: MappingProxyType({}), repr=False)

    @property
    def exists(self) -> bool:
        """Whether the content tree contains an authored Blog directory."""
        return self.index_path is not None

    def post_for_public_path(self, path: str) -> BlogPost | None:
        """Return the post published at ``path``, accepting either slash style."""
        return self._by_public_path.get(_normalize_public_path(path))

    def post_for_source(self, path: Path) -> BlogPost | None:
        """Return the post authored at ``path``, or ``None`` for an ordinary page."""
        return self._by_source.get(path.resolve())

    def public_path_for_source(self, path: Path) -> str | None:
        """Return the stable public path for a dated source file."""
        return self.source_to_public_path.get(path.resolve())

    def neighbors(self, post: BlogPost) -> tuple[BlogPost | None, BlogPost | None]:
        """Return ``(newer, older)`` posts around ``post`` in catalog order."""
        for index, candidate in enumerate(self.posts):
            if candidate.public_path != post.public_path:
                continue
            newer = self.posts[index - 1] if index > 0 else None
            older = self.posts[index + 1] if index + 1 < len(self.posts) else None
            return newer, older
        msg = f"Post {post.public_path!r} does not belong to this catalog"
        raise ValueError(msg)

    def nav_items(self, *, include_posts: bool = True) -> list[NavItem]:
        """Build the generated Blog area's sidebar items."""
        if not self.exists:
            return []
        items = [_nav_item("All posts", BLOG_INDEX_PATH)]
        if include_posts:
            items.extend(
                _nav_item(
                    post.title,
                    post.public_path,
                    date_iso=post.date_iso,
                    date_label=post.date_label,
                )
                for post in self.posts
            )
        return items


@dataclass(frozen=True)
class _FrontMatter:
    values: Mapping[str, str]
    lines: Mapping[str, int]
    body: str
    body_line: int


_current_catalog: ContextVar[BlogCatalog | None] = ContextVar("docs_blog_catalog", default=None)


def load_blog_catalog(content_dir: Path, *, now: datetime | None = None) -> BlogCatalog:
    """Discover and strictly validate ``content/blog`` into one immutable catalog."""
    blog_dir = (content_dir / "blog").resolve()
    if not blog_dir.exists():
        return BlogCatalog(blog_dir=blog_dir, index_path=None)
    if not blog_dir.is_dir():
        raise BlogCatalogError(blog_dir, "Blog path must be a directory")

    index_path = blog_dir / "index.md"
    if not index_path.is_file():
        raise BlogCatalogError(blog_dir, "Blog directory must contain index.md")
    _validate_index(index_path)

    clock = now or datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("Blog catalog clock must include an explicit timezone")

    posts: list[BlogPost] = []
    for source_path in sorted(blog_dir.rglob("*.md")):
        if source_path == index_path:
            continue
        if source_path.parent != blog_dir:
            raise BlogCatalogError(source_path, "Blog posts must be direct children of the Blog directory")
        posts.append(_load_post(source_path, content_dir=content_dir.resolve(), now=clock))

    # A stable second sort preserves ascending filenames for equal timestamps.
    posts.sort(key=lambda post: post.source_path.name)
    posts.sort(key=lambda post: post.published, reverse=True)

    by_public: dict[str, BlogPost] = {}
    by_source: dict[Path, BlogPost] = {}
    source_to_public: dict[Path, str] = {}
    for post in posts:
        if post.public_path in by_public:
            other = by_public[post.public_path]
            raise BlogCatalogError(
                post.source_path,
                f"Public path {post.public_path!r} is already owned by {other.source_path.name}",
            )
        source = post.source_path.resolve()
        by_public[post.public_path] = post
        by_source[source] = post
        source_to_public[source] = post.public_path

    return BlogCatalog(
        blog_dir=blog_dir,
        index_path=index_path,
        posts=tuple(posts),
        source_to_public_path=MappingProxyType(source_to_public),
        _by_public_path=MappingProxyType(by_public),
        _by_source=MappingProxyType(by_source),
    )


def blog_source_routes(content_dir: Path) -> Mapping[Path, str]:
    """
    Derive stable Blog routes from filenames without reading post content.

    Snapshot builds use this lightweight map to project links from versioned
    documentation to root-site Blog URLs without validating current editorial
    metadata. The root build still uses ``load_blog_catalog`` as authority.
    """
    blog_dir = (content_dir / "blog").resolve()
    routes: dict[Path, str] = {}
    if not blog_dir.is_dir():
        return MappingProxyType(routes)
    for source_path in blog_dir.glob("*.md"):
        match = _POST_NAME_RE.fullmatch(source_path.name)
        if match is not None:
            routes[source_path.resolve()] = f"/blog/{match.group('slug')}/"
    return MappingProxyType(routes)


@contextmanager
def use_blog_catalog(catalog: BlogCatalog) -> Iterator[BlogCatalog]:
    """Make ``catalog`` available to Blog components during one render."""
    token = _current_catalog.set(catalog)
    try:
        yield catalog
    finally:
        _current_catalog.reset(token)


def current_blog_catalog() -> BlogCatalog:
    """Return the catalog provided for the current render."""
    catalog = _current_catalog.get()
    if catalog is None:
        raise RuntimeError("No Blog catalog is active for this render")
    return catalog


def blog_list_markdown(catalog: BlogCatalog) -> str:
    """Render the concise text projection of the Blog index list."""
    if not catalog.posts:
        return "No Blog posts have been published yet."
    return "\n".join(
        f"- [{post.title}]({post.public_path}) ({post.date_label}, {post.author}): {post.description}"
        for post in catalog.posts
    )


def project_blog_list_for_text(source: str, catalog: BlogCatalog) -> str:
    """Replace a rendered Blog-list marker block with its Markdown projection."""
    return _BLOG_LIST_BLOCK_RE.sub(blog_list_markdown(catalog), source)


def serialize_atom_feed(catalog: BlogCatalog, *, site_url: str, base_path: str = "") -> str:
    """Serialize the newest Blog posts as an Atom 1.0 summary feed."""
    if not catalog.posts:
        return ""

    public_root = _feed_public_root(site_url, base_path)
    feed_url = f"{public_root}{BLOG_FEED_PATH}"
    index_url = f"{public_root}{BLOG_INDEX_PATH}"
    entries = catalog.posts[:_FEED_LIMIT]

    ET.register_namespace("", _ATOM_NS)
    root = ET.Element(_atom("feed"))
    ET.SubElement(root, _atom("title")).text = "Citry blog"
    ET.SubElement(root, _atom("id")).text = feed_url
    ET.SubElement(root, _atom("link"), {"rel": "self", "href": feed_url})
    ET.SubElement(root, _atom("link"), {"rel": "alternate", "href": index_url})
    ET.SubElement(root, _atom("updated")).text = max(post.effective_updated for post in entries).isoformat()

    for post in entries:
        post_url = f"{public_root}{post.public_path}"
        entry = ET.SubElement(root, _atom("entry"))
        ET.SubElement(entry, _atom("title")).text = post.title
        ET.SubElement(entry, _atom("id")).text = post_url
        ET.SubElement(entry, _atom("link"), {"rel": "alternate", "href": post_url})
        ET.SubElement(entry, _atom("published")).text = post.published.isoformat()
        ET.SubElement(entry, _atom("updated")).text = post.effective_updated.isoformat()
        ET.SubElement(entry, _atom("summary"), {"type": "text"}).text = post.description
        author = ET.SubElement(entry, _atom("author"))
        ET.SubElement(author, _atom("name")).text = post.author
        if post.author_url:
            uri = post.author_url if post.author_url.startswith("https://") else f"{public_root}{post.author_url}"
            ET.SubElement(author, _atom("uri")).text = uri
        for tag in post.tags:
            ET.SubElement(entry, _atom("category"), {"term": tag})

    ET.indent(root, space="  ")
    rendered = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return rendered.decode("utf-8") + "\n"


def _load_post(source_path: Path, *, content_dir: Path, now: datetime) -> BlogPost:
    name_match = _POST_NAME_RE.fullmatch(source_path.name)
    if name_match is None:
        raise BlogCatalogError(
            source_path,
            "Post filename must match YYYY-MM-DD-lowercase-kebab-slug.md",
        )
    filename_date = name_match.group("date")
    try:
        date.fromisoformat(filename_date)
    except ValueError as exc:
        raise BlogCatalogError(source_path, f"Filename date is invalid: {filename_date}") from exc

    source = source_path.read_text(encoding="utf-8")
    front = _parse_strict_front_matter(source, source_path)
    _validate_keys(front, source_path)

    title = _required_text(front, source_path, "title")
    description = _required_text(front, source_path, "description")
    author = _required_text(front, source_path, "author")
    published = _parse_timestamp(_required_text(front, source_path, "date"), source_path, front.lines["date"])
    if published.date().isoformat() != filename_date:
        raise BlogCatalogError(
            source_path,
            f"Filename date {filename_date} does not match publication date {published.date().isoformat()}",
            line=front.lines["date"],
        )
    if published > now:
        raise BlogCatalogError(source_path, "Publication date may not be in the future", line=front.lines["date"])

    updated = _optional_timestamp(front, source_path, "updated")
    if updated is not None and updated < published:
        raise BlogCatalogError(
            source_path, "Updated date may not be earlier than publication date", line=front.lines["updated"]
        )
    if updated is not None and updated > now:
        raise BlogCatalogError(source_path, "Updated date may not be in the future", line=front.lines["updated"])

    author_url = front.values.get("author_url", "").strip()
    if author_url and not _valid_author_url(author_url):
        raise BlogCatalogError(
            source_path,
            "author_url must be HTTPS or root-relative",
            line=front.lines["author_url"],
        )

    tags = _parse_tags(front, source_path)
    noindex = _parse_bool(front, source_path, "noindex", default=False)
    searchable = _parse_bool(front, source_path, "searchable", default=True)
    boost = _parse_boost(front, source_path)

    if not front.body.strip():
        raise BlogCatalogError(source_path, "Post body may not be empty", line=front.body_line)
    h1_line = _body_h1_line(front.body)
    if h1_line is not None:
        raise BlogCatalogError(
            source_path,
            "Post body may not contain an h1; the Blog layout supplies the page title",
            line=front.body_line + h1_line - 1,
        )

    slug = name_match.group("slug")
    return BlogPost(
        source_path=source_path.resolve(),
        source_rel=source_path.resolve().relative_to(content_dir),
        source=source,
        body=front.body,
        slug=slug,
        public_path=f"/blog/{slug}/",
        title=title,
        description=description,
        published=published,
        updated=updated,
        author=author,
        author_url=author_url,
        tags=tags,
        og_image=front.values.get("og_image", "").strip(),
        noindex=noindex,
        searchable=searchable,
        boost=boost,
        reading_minutes=_reading_minutes(front.body),
    )


def _parse_strict_front_matter(source: str, source_path: Path) -> _FrontMatter:
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise BlogCatalogError(source_path, "Post must begin with a front-matter block", line=1)

    values: dict[str, str] = {}
    key_lines: dict[str, int] = {}
    for offset, raw_line in enumerate(lines[1:], start=2):
        line = raw_line.rstrip("\r\n")
        if line.strip() == "---":
            body = "".join(lines[offset:])
            return _FrontMatter(
                values=MappingProxyType(values),
                lines=MappingProxyType(key_lines),
                body=body,
                body_line=offset + 1,
            )
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, raw_value = line.partition(":")
        key = key.strip()
        if not separator or _KEY_RE.fullmatch(key) is None:
            raise BlogCatalogError(source_path, "Malformed front-matter line; expected key: value", line=offset)
        if key in values:
            raise BlogCatalogError(source_path, f"Duplicate front-matter key {key!r}", line=offset)
        try:
            parsed = yaml.load(raw_value.strip(), Loader=yaml.BaseLoader)  # noqa: S506 - BaseLoader constructs scalars only
        except yaml.YAMLError as exc:
            raise BlogCatalogError(source_path, f"Malformed scalar value for {key!r}", line=offset) from exc
        if parsed is None:
            value = ""
        elif isinstance(parsed, str):
            value = parsed
        else:
            raise BlogCatalogError(source_path, f"Front-matter value for {key!r} must be scalar", line=offset)
        values[key] = value
        key_lines[key] = offset

    raise BlogCatalogError(source_path, "Front-matter block is not closed", line=1)


def _validate_keys(front: _FrontMatter, source_path: Path) -> None:
    for key in front.values:
        if key == "canonical":
            raise BlogCatalogError(
                source_path,
                "Blog posts may not override their canonical URL",
                line=front.lines[key],
            )
        if key not in _ALLOWED_KEYS:
            raise BlogCatalogError(source_path, f"Unknown Blog front-matter key {key!r}", line=front.lines[key])
    for key in sorted(_REQUIRED_KEYS):
        if key not in front.values:
            raise BlogCatalogError(source_path, f"Missing required front-matter key {key!r}", line=1)


def _required_text(front: _FrontMatter, source_path: Path, key: str) -> str:
    value = front.values[key].strip()
    if not value:
        raise BlogCatalogError(
            source_path, f"Required front-matter key {key!r} may not be blank", line=front.lines[key]
        )
    return value


def _parse_timestamp(value: str, source_path: Path, line: int) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BlogCatalogError(source_path, f"Invalid ISO 8601 timestamp {value!r}", line=line) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BlogCatalogError(source_path, "Timestamp must include an explicit timezone", line=line)
    return parsed


def _optional_timestamp(front: _FrontMatter, source_path: Path, key: str) -> datetime | None:
    value = front.values.get(key, "").strip()
    if not value:
        return None
    return _parse_timestamp(value, source_path, front.lines[key])


def _parse_bool(front: _FrontMatter, source_path: Path, key: str, *, default: bool) -> bool:
    value = front.values.get(key, "").strip().casefold()
    if not value:
        return default
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    expected = ", ".join(sorted(_TRUTHY | _FALSY))
    raise BlogCatalogError(
        source_path,
        f"{key}: {front.values[key]!r} is not a boolean (expected one of: {expected})",
        line=front.lines[key],
    )


def _parse_boost(front: _FrontMatter, source_path: Path) -> float:
    value = front.values.get("boost", "").strip()
    if not value:
        return 1.0
    try:
        boost = float(value)
    except ValueError as exc:
        raise BlogCatalogError(source_path, f"boost: {value!r} is not a number", line=front.lines["boost"]) from exc
    if not math.isfinite(boost):
        raise BlogCatalogError(source_path, "boost must be a finite number", line=front.lines["boost"])
    return boost


def _parse_tags(front: _FrontMatter, source_path: Path) -> tuple[str, ...]:
    if "tags" not in front.values:
        return ()
    raw_tags = front.values["tags"].split(",")
    display_tags = tuple(" ".join(tag.split()) for tag in raw_tags)
    if any(not tag for tag in display_tags):
        raise BlogCatalogError(source_path, "Tags may not be empty", line=front.lines["tags"])
    seen: set[str] = set()
    for tag in display_tags:
        normalized = tag.casefold()
        if normalized in seen:
            raise BlogCatalogError(source_path, f"Duplicate tag {tag!r}", line=front.lines["tags"])
        seen.add(normalized)
    return display_tags


def _valid_author_url(value: str) -> bool:
    if "\\" in value or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        return False
    if value.startswith("/") and not value.startswith("//"):
        parsed = urlsplit(value)
        return not parsed.scheme and not parsed.netloc
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _validate_index(index_path: Path) -> None:
    source = index_path.read_text(encoding="utf-8")
    rendered = _validation_markdown(source)
    prose = _HTML_COMMENT_RE.sub("", rendered)
    tags = _BLOG_LIST_TAG_RE.findall(prose)
    document = lxml_html.fragment_fromstring(rendered, create_parent="div")
    elements = document.xpath(".//c-blog-list")
    if len(elements) != 1 or len(tags) != 1 or _PARAMETERLESS_BLOG_LIST_RE.fullmatch(tags[0]) is None:
        raise BlogCatalogError(
            index_path,
            "Blog index must contain exactly one parameterless <c-blog-list /> directive",
        )


def _fence_marker(line: str) -> str:
    """Return a valid Markdown fence opener marker, or an empty string."""
    match = _FENCE_OPEN_RE.match(line)
    if match is None:
        return ""
    marker = match.group("marker")
    # CommonMark forbids backticks in a backtick fence's info string. Without
    # this check an inline code span such as `````inline````` would hide every
    # later heading from the catalog even though Markdown never opens a fence.
    if marker[0] == "`" and "`" in line[match.end() :]:
        return ""
    return marker


def _is_fence_closer(line: str, marker: str) -> bool:
    indentation = len(line) - len(line.lstrip(" "))
    if indentation > 3:
        return False
    stripped = line[indentation:]
    if not stripped.startswith(marker[0] * len(marker)):
        return False
    run_length = len(stripped) - len(stripped.lstrip(marker[0]))
    # pymdownx.superfences, used by the site pipeline, requires the closing run
    # to match the opener length exactly.
    return run_length == len(marker) and not stripped[run_length:].strip()


def _fenced_line_numbers(lines: list[str]) -> set[int]:
    """Return one-based lines belonging to complete Markdown fenced blocks."""
    fenced: set[int] = set()
    index = 0
    while index < len(lines):
        marker = _fence_marker(lines[index])
        if not marker:
            index += 1
            continue
        close = next(
            (candidate for candidate in range(index + 1, len(lines)) if _is_fence_closer(lines[candidate], marker)),
            None,
        )
        # Python-Markdown treats an opener with no valid closer as ordinary
        # prose, so it must not suppress later headings or reading-time words.
        if close is None:
            index += 1
            continue
        fenced.update(range(index + 1, close + 2))
        index = close + 1
    return fenced


def _without_markdown_code(source: str) -> str:
    """Mask Markdown code and HTML comments while preserving source lines."""
    source_lines = source.splitlines(keepends=True)
    logical_lines = [line.rstrip("\r\n") for line in source_lines]
    fenced = _fenced_line_numbers(logical_lines)
    masked_lines: list[str] = []
    for line_number, line in enumerate(source_lines, start=1):
        if line_number in fenced or line.startswith(("    ", "\t")):
            masked_lines.append("".join(character if character in "\r\n" else " " for character in line))
        else:
            masked_lines.append(line)
    without_comments = _without_html_comments("".join(masked_lines))
    return _without_inline_code_spans(without_comments)


def _without_html_comments(source: str) -> str:
    """Mask HTML comments through their closer or EOF, preserving newlines."""
    masked = list(source)
    position = 0
    while (start := source.find("<!--", position)) >= 0:
        close = source.find("-->", start + 4)
        end = len(source) if close < 0 else close + 3
        for index in range(start, end):
            if masked[index] not in "\r\n":
                masked[index] = " "
        position = end
    return "".join(masked)


def _without_inline_code_spans(source: str) -> str:
    """Mask paired backtick spans, including spans that cross a line break."""
    masked = list(source)
    position = 0
    while opener := re.search(r"`+", source[position:]):
        start = position + opener.start()
        end = position + opener.end()
        if _is_backslash_escaped(source, start):
            position = end
            continue
        marker_length = end - start
        closer_end = -1
        for closer in re.finditer(r"`+", source[end:]):
            # Backslash escaping is not active inside a code span, so a
            # same-length run closes even when a backslash precedes it.
            if closer.end() - closer.start() == marker_length:
                closer_end = end + closer.end()
                break
        if closer_end < 0:
            position = end
            continue
        for index in range(start, closer_end):
            if masked[index] not in "\r\n":
                masked[index] = " "
        position = closer_end
    return "".join(masked)


def _is_backslash_escaped(source: str, position: int) -> bool:
    backslashes = 0
    position -= 1
    while position >= 0 and source[position] == "\\":
        backslashes += 1
        position -= 1
    return backslashes % 2 == 1


def _body_h1_line(body: str) -> int | None:
    rendered = _validation_markdown(body)
    document = lxml_html.fragment_fromstring(rendered, create_parent="div")
    if not document.xpath(".//h1"):
        return None
    # The rendered DOM is authoritative. The source scan supplies a precise
    # line for ordinary Markdown and raw-HTML headings; exotic delimiter
    # interactions fall back to the first body line rather than bypassing the
    # one-H1 contract.
    return _source_h1_line(body) or 1


def _source_h1_line(body: str) -> int | None:
    lines = _without_markdown_code(body).splitlines()
    previous_prose = False
    in_comment = False
    for line_number, line in enumerate(lines, start=1):
        visible = line
        if in_comment:
            if "-->" in visible:
                visible = visible.split("-->", 1)[1]
                in_comment = False
            else:
                continue
        while "<!--" in visible:
            before, after = visible.split("<!--", 1)
            if "-->" in after:
                visible = before + after.split("-->", 1)[1]
            else:
                visible = before
                in_comment = True
                break

        if _ATX_H1_RE.match(visible) or _RAW_H1_RE.search(visible):
            return line_number
        if previous_prose and _SETEXT_H1_RE.match(visible):
            return line_number
        previous_prose = bool(visible.strip())
    return None


def _validation_markdown(source: str) -> str:
    """Render the Markdown constructs that determine code, comments, and H1s."""
    return markdown.markdown(
        source,
        extensions=["md_in_html", "pymdownx.superfences"],
    )


def _reading_minutes(body: str) -> int:
    rendered = _validation_markdown(body)
    document = lxml_html.fragment_fromstring(rendered, create_parent="div")
    # Fenced and indented code render beneath <pre>. Script/style bodies are
    # likewise not reading prose. Inline code remains visible and contributes
    # its words just like other inline phrasing.
    for hidden in document.xpath(".//pre | .//script | .//style"):
        hidden.drop_tree()
    prose = document.text_content()
    words = _WORD_RE.findall(prose)
    return max(1, math.ceil(len(words) / _WORDS_PER_MINUTE))


def _nav_item(title: str, path: str, *, date_iso: str = "", date_label: str = "") -> NavItem:
    return NavItem(
        title=title,
        path=path,
        date_iso=date_iso,
        date_label=date_label,
    )


def _normalize_public_path(path: str) -> str:
    clean = path.strip("/")
    return f"/{clean}/" if clean else "/"


def _feed_public_root(site_url: str, base_path: str) -> str:
    parsed = urlsplit(site_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("Atom feed site_url must be an absolute HTTP(S) URL without a query or fragment")
    base_path = base_path.rstrip("/")
    if base_path:
        if not base_path.startswith("/") or base_path.startswith("//"):
            raise ValueError("Atom feed base_path must be root-relative")
        if any(part in {".", ".."} for part in base_path.split("/")):
            raise ValueError("Atom feed base_path may not contain dot segments")
    root = site_url.rstrip("/")
    if not base_path:
        return root
    # DOCS_SITE_URL is documented as the complete public site URL, including
    # a project-Pages path. DOCS_BASE_PATH separately drives root-relative HTML
    # rewriting. Accept an origin-only site URL by appending the base path, but
    # never duplicate a path that the complete site URL already carries.
    site_path = parsed.path.rstrip("/")
    if site_path == base_path or site_path.endswith(base_path):
        return root
    return root + base_path


def _atom(tag: str) -> str:
    return f"{{{_ATOM_NS}}}{tag}"
