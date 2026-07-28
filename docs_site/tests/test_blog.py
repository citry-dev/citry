"""Tests for strict Blog discovery and catalog-derived projections."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from docs_site._internal.blog import (
    BLOG_LIST_END,
    BLOG_LIST_START,
    BlogCatalogError,
    blog_list_markdown,
    current_blog_catalog,
    load_blog_catalog,
    project_blog_list_for_text,
    serialize_atom_feed,
    use_blog_catalog,
)
from docs_site._internal.pipeline import render_page

NOW = datetime.fromisoformat("2026-08-10T12:00:00+00:00")
ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def _blog(tmp_path: Path, *, index: str = "# Blog\n\n<c-blog-list />\n") -> Path:
    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)
    (blog / "index.md").write_text(index, encoding="utf-8")
    return content


def _post_source(
    *,
    title: str = "A useful post",
    description: str = "What this post explains.",
    date: str = "2026-07-28T09:00:00+02:00",
    author: str = "Juro Oravec",
    extra: str = "",
    body: str = "Opening context.\n\n## Evidence\n\nThe result.\n",
) -> str:
    return f"---\ntitle: {title}\ndescription: {description}\ndate: {date}\nauthor: {author}\n{extra}---\n\n{body}"


def _write_post(content: Path, name: str = "2026-07-28-useful-post.md", **kwargs: str) -> Path:
    path = content / "blog" / name
    path.write_text(_post_source(**kwargs), encoding="utf-8")
    return path


def test_absent_blog_directory_is_an_empty_optional_catalog(tmp_path: Path) -> None:
    catalog = load_blog_catalog(tmp_path / "content", now=NOW)

    assert not catalog.exists
    assert catalog.index_path is None
    assert catalog.posts == ()
    assert catalog.nav_items() == []
    assert serialize_atom_feed(catalog, site_url="not needed for an empty feed") == ""


def test_existing_blog_requires_an_index(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "blog").mkdir(parents=True)

    with pytest.raises(BlogCatalogError, match=r"must contain index\.md"):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize(
    "index",
    [
        "# Blog\n",
        "<c-blog-list /><c-blog-list />\n",
        '<c-blog-list class="wrong" />\n',
        "```html\n<c-blog-list />\n```\n",
    ],
)
def test_index_requires_one_parameterless_blog_list(tmp_path: Path, index: str) -> None:
    content = _blog(tmp_path, index=index)

    with pytest.raises(BlogCatalogError, match="exactly one parameterless"):
        load_blog_catalog(content, now=NOW)


def test_index_ignores_a_directive_shown_in_a_fence_or_comment(tmp_path: Path) -> None:
    content = _blog(
        tmp_path,
        index=("```html\n<c-blog-list />\n```\n\n<!-- <c-blog-list /> -->\n\n<c-blog-list />\n"),
    )

    assert load_blog_catalog(content, now=NOW).exists


def test_index_ignores_directives_shown_in_inline_or_indented_code(tmp_path: Path) -> None:
    content = _blog(
        tmp_path,
        index=("The `<c-blog-list />` directive renders the cards below.\n\n    <c-blog-list />\n\n<c-blog-list />\n"),
    )

    assert load_blog_catalog(content, now=NOW).exists


def test_index_comment_backticks_cannot_hide_a_duplicate_directive(tmp_path: Path) -> None:
    content = _blog(
        tmp_path,
        index="<!-- `\n-->\n<c-blog-list />\n`\n<c-blog-list />\n",
    )

    with pytest.raises(BlogCatalogError, match="exactly one parameterless"):
        load_blog_catalog(content, now=NOW)


def test_valid_post_populates_immutable_metadata_lookup_and_nav(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    source_path = _write_post(
        content,
        extra=(
            "updated: 2026-08-02T16:30:00+02:00\n"
            "author_url: https://github.com/jurooravec\n"
            "tags: Project updates, Architecture\n"
            "og_image: /static/img/blog/post.png\n"
            "noindex: false\n"
            "searchable: yes\n"
            "boost: 1.5\n"
        ),
    )

    catalog = load_blog_catalog(content, now=NOW)
    post = catalog.posts[0]

    assert catalog.exists
    assert post.public_path == "/blog/useful-post/"
    assert post.source_rel == Path("blog/2026-07-28-useful-post.md")
    assert post.updated == datetime.fromisoformat("2026-08-02T16:30:00+02:00")
    assert post.author_url == "https://github.com/jurooravec"
    assert post.tags == ("Project updates", "Architecture")
    assert post.og_image == "/static/img/blog/post.png"
    assert not post.noindex
    assert post.searchable
    assert post.boost == 1.5
    assert post.reading_minutes == 1
    assert catalog.post_for_source(source_path) is post
    assert catalog.public_path_for_source(source_path) == post.public_path
    assert catalog.post_for_public_path("blog/useful-post") is post

    nav = catalog.nav_items()
    assert [(item.title, item.path) for item in nav] == [
        ("All posts", "/blog/"),
        ("A useful post", "/blog/useful-post/"),
    ]
    assert nav[1].date_iso == "2026-07-28T09:00:00+02:00"
    assert nav[1].date_label == "28 Jul 2026"
    with pytest.raises(FrozenInstanceError):
        post.slug = "changed"  # type: ignore[misc]


def test_posts_sort_newest_first_with_ascending_filename_tiebreaker_and_neighbors(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    shared = "2026-07-29T10:00:00+00:00"
    _write_post(content, "2026-07-29-beta.md", title="Beta", date=shared)
    _write_post(content, "2026-07-29-alpha.md", title="Alpha", date=shared)
    _write_post(
        content,
        "2026-07-30-newest.md",
        title="Newest",
        date="2026-07-30T08:00:00+00:00",
    )

    catalog = load_blog_catalog(content, now=NOW)

    assert [post.title for post in catalog.posts] == ["Newest", "Alpha", "Beta"]
    assert catalog.neighbors(catalog.posts[0]) == (None, catalog.posts[1])
    assert catalog.neighbors(catalog.posts[1]) == (catalog.posts[0], catalog.posts[2])
    assert catalog.neighbors(catalog.posts[2]) == (catalog.posts[1], None)


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("post.md", "filename must match"),
        ("2026-07-28-Upper.md", "filename must match"),
        ("2026-07-28-two--hyphens.md", "filename must match"),
        ("2026-02-30-bad-date.md", "Filename date is invalid"),
    ],
)
def test_post_filename_contract(tmp_path: Path, name: str, message: str) -> None:
    content = _blog(tmp_path)
    _write_post(content, name)

    with pytest.raises(BlogCatalogError, match=message):
        load_blog_catalog(content, now=NOW)


def test_nested_post_is_rejected(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    nested = content / "blog" / "year"
    nested.mkdir()
    (nested / "2026-07-28-post.md").write_text(_post_source(), encoding="utf-8")

    with pytest.raises(BlogCatalogError, match="direct children"):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize(
    ("source", "message", "line"),
    [
        ("No front matter.\n", "must begin", 1),
        ("---\ntitle: T\nbroken\n---\nBody\n", "Malformed front-matter line", 3),
        ("---\ntitle: T\ntitle: Again\n---\nBody\n", "Duplicate front-matter key", 3),
        ("---\ntitle: T\n", "not closed", 1),
        ("---\ntitle: [nested]\n---\nBody\n", "must be scalar", 2),
    ],
)
def test_strict_front_matter_reports_source_lines(
    tmp_path: Path,
    source: str,
    message: str,
    line: int,
) -> None:
    content = _blog(tmp_path)
    post = content / "blog" / "2026-07-28-post.md"
    post.write_text(source, encoding="utf-8")

    with pytest.raises(BlogCatalogError, match=message) as caught:
        load_blog_catalog(content, now=NOW)
    assert caught.value.source == post
    assert caught.value.line == line


@pytest.mark.parametrize("key", ["title", "description", "date", "author"])
def test_required_front_matter_key_may_not_be_missing(tmp_path: Path, key: str) -> None:
    content = _blog(tmp_path)
    source = _post_source()
    source = "\n".join(line for line in source.splitlines() if not line.startswith(f"{key}:")) + "\n"
    (content / "blog" / "2026-07-28-post.md").write_text(source, encoding="utf-8")

    with pytest.raises(BlogCatalogError, match=f"Missing required front-matter key '{key}'"):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize("key", ["title", "description", "date", "author"])
def test_required_front_matter_key_may_not_be_blank(tmp_path: Path, key: str) -> None:
    content = _blog(tmp_path)
    kwargs = {key: "   "}
    _write_post(content, **kwargs)

    with pytest.raises(BlogCatalogError, match="may not be blank"):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ("unknown: value\n", "Unknown Blog front-matter key"),
        ("canonical: https://example.com/post\n", "may not override"),
        ("noindex: maybe\n", "is not a boolean"),
        ("searchable: perhaps\n", "is not a boolean"),
        ("boost: fast\n", "is not a number"),
        ("boost: nan\n", "finite number"),
    ],
)
def test_unknown_or_invalid_optional_metadata_is_rejected(tmp_path: Path, extra: str, message: str) -> None:
    content = _blog(tmp_path)
    _write_post(content, extra=extra)

    with pytest.raises(BlogCatalogError, match=message):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize(
    ("date", "extra", "message"),
    [
        ("2026-07-28T09:00:00", "", "explicit timezone"),
        ("not-a-time", "", "Invalid ISO 8601"),
        ("2026-07-29T09:00:00+02:00", "", "does not match publication date"),
        (
            "2026-07-28T09:00:00+02:00",
            "updated: 2026-07-27T09:00:00+02:00\n",
            "may not be earlier",
        ),
        (
            "2026-07-28T09:00:00+02:00",
            "updated: 2026-08-11T09:00:00+00:00\n",
            "may not be in the future",
        ),
    ],
)
def test_timestamp_contract(tmp_path: Path, date: str, extra: str, message: str) -> None:
    content = _blog(tmp_path)
    _write_post(content, date=date, extra=extra)

    with pytest.raises(BlogCatalogError, match=message):
        load_blog_catalog(content, now=NOW)


def test_future_publication_is_rejected_with_a_matching_filename_date(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(
        content,
        "2026-08-11-future.md",
        date="2026-08-11T09:00:00+00:00",
    )

    with pytest.raises(BlogCatalogError, match="may not be in the future"):
        load_blog_catalog(content, now=NOW)


def test_catalog_clock_must_be_aware(tmp_path: Path) -> None:
    content = _blog(tmp_path)

    with pytest.raises(ValueError, match="clock must include"):
        load_blog_catalog(content, now=datetime.fromisoformat("2026-08-10T12:00:00"))


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/author",
        "//example.com/author",
        r"/\evil.test/path",
        "authors/juro",
        "mailto:juro@example.com",
    ],
)
def test_author_url_rejects_non_https_or_non_root_relative_values(tmp_path: Path, url: str) -> None:
    content = _blog(tmp_path)
    _write_post(content, extra=f"author_url: {url}\n")

    with pytest.raises(BlogCatalogError, match="HTTPS or root-relative"):
        load_blog_catalog(content, now=NOW)


def test_root_relative_author_url_is_valid(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(content, extra="author_url: /community/people/\n")

    assert load_blog_catalog(content, now=NOW).posts[0].author_url == "/community/people/"


@pytest.mark.parametrize("tags", ["Architecture, architecture", "Architecture,   ", ""])
def test_tags_reject_empty_or_normalized_duplicates(tmp_path: Path, tags: str) -> None:
    content = _blog(tmp_path)
    _write_post(content, extra=f"tags: {tags}\n")

    with pytest.raises(BlogCatalogError, match=r"Tags may not be empty|Duplicate tag"):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("   \n", "may not be empty"),
        ("# Duplicate title\n", "may not contain an h1"),
        ("Duplicate title\n===\n", "may not contain an h1"),
        ("<h1>Duplicate title</h1>\n", "may not contain an h1"),
        ("```inline```\n\n# Duplicate title\n", "may not contain an h1"),
        ("```text\n\n# Duplicate title\n", "may not contain an h1"),
        ("~~~text\n\n# Duplicate title\n", "may not contain an h1"),
        (r"\`<h1>Duplicate title</h1>\` visible", "may not contain an h1"),
        ("`\n# Duplicate title\n`\n", "may not contain an h1"),
        ("~~~\n# Duplicate title\n~~~~\n", "may not contain an h1"),
    ],
)
def test_post_body_contract(tmp_path: Path, body: str, message: str) -> None:
    content = _blog(tmp_path)
    _write_post(content, body=body)

    with pytest.raises(BlogCatalogError, match=message):
        load_blog_catalog(content, now=NOW)


@pytest.mark.parametrize(
    "body",
    [
        "<!-- `\n-->\n<h1>Duplicate title</h1>\n`\n",
        "<!-- `\n-->\n# Duplicate title\n`\n",
        "`<!--`\n<h1>Duplicate title</h1>\n",
        "`<!--`\n# Duplicate title\n",
        "`\n# Duplicate title\n`\n",
        "~~~\n# Duplicate title\n~~~~\n",
    ],
)
def test_comment_backticks_cannot_hide_a_rendered_h1(tmp_path: Path, body: str) -> None:
    assert "<h1" in render_page(body, wrap_in_layout=False).html
    content = _blog(tmp_path)
    _write_post(content, body=body)

    with pytest.raises(BlogCatalogError, match="may not contain an h1"):
        load_blog_catalog(content, now=NOW)


def test_h1_inside_code_or_comment_is_not_a_body_heading(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(
        content,
        body=(
            "```markdown\n# Example\n```\n\n"
            "    <h1>Indented example</h1>\n\n"
            "Use `<h1>Inline example</h1>` in an HTML document.\n\n"
            "Use \\\\`<h1>Even escape example</h1>` as inline code.\n\n"
            "Use `<h1>Backslash closer</h1>\\` as inline code.\n\n"
            "<!-- # Hidden -->\n\nVisible prose.\n"
        ),
    )

    assert load_blog_catalog(content, now=NOW).posts[0].reading_minutes == 1


def test_reading_time_keeps_visible_words_when_fence_lengths_do_not_match(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    code = " ".join(["ignored"] * 500)
    _write_post(content, body=f"One visible sentence.\n\n```text\n{code}\n````\n")

    assert load_blog_catalog(content, now=NOW).posts[0].reading_minutes == 3


def test_reading_time_keeps_prose_after_an_unclosed_fence_opener(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    prose = " ".join(["visible"] * 201)
    _write_post(content, body=f"```text\n\n{prose}\n")

    assert load_blog_catalog(content, now=NOW).posts[0].reading_minutes == 2


@pytest.mark.parametrize(
    "body",
    [
        "`\n\n{prose}\n\n`\n",
        "`<!--`\n\n{prose}\n",
    ],
)
def test_reading_time_counts_visible_prose_across_block_delimiters(tmp_path: Path, body: str) -> None:
    content = _blog(tmp_path)
    prose = " ".join(["visible"] * 401)
    _write_post(content, body=body.format(prose=prose))

    assert load_blog_catalog(content, now=NOW).posts[0].reading_minutes == 3


def test_duplicate_stable_slug_is_rejected(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(content)
    _write_post(
        content,
        "2026-07-29-useful-post.md",
        date="2026-07-29T09:00:00+02:00",
    )

    with pytest.raises(BlogCatalogError, match=r"Public path.*already owned"):
        load_blog_catalog(content, now=NOW)


def test_reading_time_excludes_fenced_code_and_raw_markup(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    prose = " ".join(["word"] * 201)
    code = " ".join(["ignored"] * 500)
    _write_post(
        content,
        body=f'{prose}\n\n```text\n{code}\n```\n\n<c-example name="card" />\n',
    )

    assert load_blog_catalog(content, now=NOW).posts[0].reading_minutes == 2


def test_catalog_context_is_nested_and_restored(tmp_path: Path) -> None:
    first = load_blog_catalog(_blog(tmp_path / "first"), now=NOW)
    second = load_blog_catalog(_blog(tmp_path / "second"), now=NOW)

    with pytest.raises(RuntimeError, match="No Blog catalog"):
        current_blog_catalog()
    with use_blog_catalog(first):
        assert current_blog_catalog() is first
        with use_blog_catalog(second):
            assert current_blog_catalog() is second
        assert current_blog_catalog() is first
    with pytest.raises(RuntimeError, match="No Blog catalog"):
        current_blog_catalog()


def test_blog_list_text_projection_uses_catalog_order(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(content)
    catalog = load_blog_catalog(content, now=NOW)
    block = f"before\n{BLOG_LIST_START}\n<div>browser cards</div>\n{BLOG_LIST_END}\nafter"

    projected = project_blog_list_for_text(block, catalog)

    assert "browser cards" not in projected
    assert "[A useful post](/blog/useful-post/)" in projected
    assert blog_list_markdown(catalog) in projected


def test_atom_feed_contains_summary_metadata_escaping_and_base_path(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(
        content,
        title="A quoted & useful post",
        description="What <works> & why.",
        extra=(
            "updated: 2026-08-02T16:30:00+02:00\nauthor_url: /community/people/\ntags: Project updates, Architecture\n"
        ),
    )
    catalog = load_blog_catalog(content, now=NOW)

    feed = serialize_atom_feed(catalog, site_url="https://example.com", base_path="/preview")
    root = ET.fromstring(feed)  # noqa: S314 - parses the serializer output under test
    entry = root.find("atom:entry", ATOM)

    assert root.findtext("atom:id", namespaces=ATOM) == "https://example.com/preview/blog/feed.xml"
    assert root.find("atom:link[@rel='alternate']", ATOM).attrib["href"] == "https://example.com/preview/blog/"
    assert root.findtext("atom:updated", namespaces=ATOM) == "2026-08-02T16:30:00+02:00"
    assert entry is not None
    assert entry.findtext("atom:title", namespaces=ATOM) == "A quoted & useful post"
    assert entry.findtext("atom:summary", namespaces=ATOM) == "What <works> & why."
    assert entry.findtext("atom:author/atom:uri", namespaces=ATOM) == ("https://example.com/preview/community/people/")
    assert [node.attrib["term"] for node in entry.findall("atom:category", ATOM)] == [
        "Project updates",
        "Architecture",
    ]
    assert "<content" not in feed


def test_atom_feed_does_not_duplicate_base_path_already_in_site_url(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    _write_post(content)

    feed = serialize_atom_feed(
        load_blog_catalog(content, now=NOW),
        site_url="https://owner.github.io/citry/",
        base_path="/citry",
    )
    root = ET.fromstring(feed)  # noqa: S314 - parses the serializer output under test

    assert root.findtext("atom:id", namespaces=ATOM) == "https://owner.github.io/citry/blog/feed.xml"
    assert "/citry/citry/" not in feed


def test_atom_feed_limits_entries_to_twenty_newest_posts(tmp_path: Path) -> None:
    content = _blog(tmp_path)
    for day in range(1, 22):
        _write_post(
            content,
            f"2026-07-{day:02d}-post-{day}.md",
            title=f"Post {day}",
            date=f"2026-07-{day:02d}T09:00:00+00:00",
        )

    root = ET.fromstring(  # noqa: S314 - parses the serializer output under test
        serialize_atom_feed(load_blog_catalog(content, now=NOW), site_url="https://x.test")
    )
    entries = root.findall("atom:entry", ATOM)

    assert len(entries) == 20
    assert entries[0].findtext("atom:title", namespaces=ATOM) == "Post 21"
    assert entries[-1].findtext("atom:title", namespaces=ATOM) == "Post 2"


@pytest.mark.parametrize(
    ("site_url", "base_path"),
    [
        ("relative", ""),
        ("https://x.test/?query=1", ""),
        ("https://x.test", "preview"),
        ("https://x.test", "//preview"),
        ("https://x.test", "/preview/../escape"),
    ],
)
def test_atom_feed_rejects_invalid_public_roots(tmp_path: Path, site_url: str, base_path: str) -> None:
    content = _blog(tmp_path)
    _write_post(content)

    with pytest.raises(ValueError, match="Atom feed"):
        serialize_atom_feed(load_blog_catalog(content, now=NOW), site_url=site_url, base_path=base_path)
