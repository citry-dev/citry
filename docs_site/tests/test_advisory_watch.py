"""Tests for the README advisory graphic: the data checks, the SVG files, the README block, and the page part."""

from __future__ import annotations

import copy
import hashlib
import html
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from docs_site._internal.components.advisory_watch import AdvisoryWatch
from docs_site.scripts import advisory_watch

# A name with every character that must be escaped in markup and in an attribute.
NASTY = 'Gam<ma> & "x"'
NASTY_ESCAPED = "Gam&lt;ma&gt; &amp; &quot;x&quot;"


@pytest.fixture(autouse=True)
def _positions(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real table places the real projects; these tests draw made-up ones.
    monkeypatch.setattr(
        advisory_watch,
        "POSITIONS",
        {"Alpha": (110, 128), "Beta": (592, 92), NASTY: (214, 272)},
    )


def _data() -> dict[str, Any]:
    return {
        "as_of": "2026-03",
        "total": 1234,
        "projects": [{"name": "Alpha", "count": 1200}, {"name": "Beta", "count": 34}],
    }


def _nasty_data() -> dict[str, Any]:
    data = _data()
    data["projects"].append({"name": NASTY, "count": 5})
    data["total"] += 5
    return data


def _readme(body: str = "old") -> str:
    return f"top\n{advisory_watch.START_MARKER}\n{body}\n{advisory_watch.END_MARKER}\nbottom\n"


def _without_colours(text: str) -> str:
    return re.sub(r"#[0-9a-fA-F]{6}", "#", text)


def test_check_data_accepts_valid_data() -> None:
    advisory_watch.check_data(_data())
    advisory_watch.check_data(_nasty_data())


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data.update(as_of="2026-13"), "'as_of' must be a month"),
        (lambda data: data.update(as_of="2026-00"), "'as_of' must be a month"),
        (lambda data: data.update(as_of="Nov 2026"), "'as_of' must be a month"),
        (lambda data: data.update(as_of="2026-3"), "'as_of' must be a month"),
        (lambda data: data.update(as_of=202603), "'as_of' must be a month"),
        (lambda data: data.pop("as_of"), "'as_of' must be a month"),
        (lambda data: data.update(projects=[]), "non-empty 'projects'"),
        (lambda data: data.update(projects="Alpha"), "non-empty 'projects'"),
        (lambda data: data.pop("projects"), "non-empty 'projects'"),
        (lambda data: data["projects"].append({"name": "Alpha", "count": 1}), "'Alpha' is listed twice"),
        (lambda data: data["projects"][0].update(name=""), "needs a name"),
        (lambda data: data["projects"][0].update(count=0), "whole count of at least 1"),
        (lambda data: data["projects"][0].update(count=-3), "whole count of at least 1"),
        (lambda data: data["projects"][0].update(count=True), "whole count of at least 1"),
        (lambda data: data["projects"][0].update(count="5"), "whole count of at least 1"),
        (lambda data: data["projects"][0].update(count=2.0), "whole count of at least 1"),
        (lambda data: data["projects"][0].pop("count"), "whole count of at least 1"),
        (lambda data: data["projects"].append({"name": "Omega", "count": 1}), "'Omega' has no place"),
        (lambda data: data.update(total=1235), "'total' is 1235, but the project counts add up to 1234"),
        (lambda data: data.pop("total"), "'total' is None"),
    ],
)
def test_check_data_rejects_data_that_cannot_be_drawn_or_does_not_add_up(
    change: Callable[[dict[str, Any]], object],
    message: str,
) -> None:
    data = copy.deepcopy(_data())
    change(data)
    with pytest.raises(ValueError, match=message):
        advisory_watch.check_data(data)


def test_sentences_use_the_data() -> None:
    data = _data()
    # The total carries a thousands separator, and the month is spelled out.
    assert "1,234" in advisory_watch.intro(data)
    assert "March 2026" in advisory_watch.note(data)
    alt = advisory_watch.alt_text(data)
    assert "Alpha 1,200" in alt
    assert "Beta 34" in alt
    # Another month and total change the sentences, so they are not fixed text.
    data.update(as_of="2027-12", total=7)
    assert "December 2027" in advisory_watch.note(data)
    assert "7" in advisory_watch.intro(data)
    assert "1,234" not in advisory_watch.intro(data)


def test_note_refuses_a_month_it_cannot_read() -> None:
    with pytest.raises(ValueError, match="'as_of' must be a month"):
        advisory_watch.note({"as_of": "soon"})


def test_light_and_dark_files_differ_only_by_colour() -> None:
    data = _data()
    light = advisory_watch.file_svg(data, "light")
    dark = advisory_watch.file_svg(data, "dark")
    assert light != dark
    assert _without_colours(light) == _without_colours(dark)
    # Each file is drawn with its own theme's colours.
    for theme, text in (("light", light), ("dark", dark)):
        for colour in advisory_watch.FILE_COLORS[theme].values():
            assert colour in text


def test_file_svg_is_a_labelled_image_with_a_size() -> None:
    data = _nasty_data()
    text = advisory_watch.file_svg(data, "light")
    # Parsing proves the markup is well-formed XML, so a viewer will draw it.
    root = ET.fromstring(text)  # noqa: S314 - parses text this test generated
    attrs = root.attrib
    assert attrs["width"] == str(advisory_watch.IMAGE_WIDTH)
    assert attrs["height"] == str(advisory_watch.IMAGE_HEIGHT)
    assert attrs["role"] == "img"
    # The label is the alt text, with every project's count.
    assert attrs["aria-label"] == advisory_watch.alt_text(data)
    assert "aria-hidden" not in attrs
    assert text.endswith("</svg>\n")
    # The file draws its own card.
    assert "<rect" in text


def test_inline_svg_is_labelled_and_takes_the_page_colours() -> None:
    data = _nasty_data()
    text = advisory_watch.inline_svg(data)
    root = ET.fromstring(text)  # noqa: S314 - parses text this test generated
    # Only the alt text lists every count in words, so screen readers get it inline too.
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-label"] == advisory_watch.alt_text(data)
    # The page sizes it, so the root tag has no fixed width or height.
    assert "width" not in root.attrib
    assert "height" not in root.attrib
    assert "viewBox" in root.attrib
    # The card belongs to the page, and every colour is a CSS variable.
    assert "<rect" not in text
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", text)
    for colour in advisory_watch.INLINE_COLORS.values():
        if colour != "none":
            assert colour.startswith("var(--")
            assert colour in text
    assert "font-family:inherit" in text


@pytest.mark.parametrize("inline", [False, True])
def test_every_name_in_the_style_is_prefixed_so_an_inline_svg_cannot_leak(inline: bool) -> None:
    colors = advisory_watch.INLINE_COLORS if inline else advisory_watch.FILE_COLORS["light"]
    text = advisory_watch.svg(_nasty_data(), colors, inline=inline)

    classes = [name for value in re.findall(r'class="([^"]+)"', text) for name in value.split()]
    assert classes
    assert all(name.startswith("aw-") for name in classes)
    ids = re.findall(r'\bid="([^"]+)"', text)
    assert all(name.startswith("aw-") for name in ids)

    style = re.search(r"<style>(.*?)</style>", text, re.DOTALL)
    assert style
    css = style.group(1)
    keyframes = re.findall(r"@keyframes\s+([^\s{]+)", css)
    assert keyframes
    assert all(name.startswith("aw-") for name in keyframes)
    # An animation may only name a keyframes rule defined here.
    used = [name for name in re.findall(r"animation:([\w-]+)", css) if name != "none"]
    assert used
    assert set(used) <= set(keyframes)

    # Inline, the stylesheet applies to the whole page, so every selector must
    # start from the SVG's own root class. A bare `text{...}` would restyle
    # every <text> element on the page.
    rules = re.sub(r"@keyframes[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    rules = re.sub(r"@media[^{]+\{", "", rules)
    selectors = [part.strip() for part in re.findall(r"([^{}]+)\{", rules)]
    assert selectors
    assert all(selector.startswith(".aw-root") for selector in selectors), selectors
    assert 'class="aw-root"' in text


def test_a_reduced_motion_rule_stops_the_animation() -> None:
    text = advisory_watch.file_svg(_data(), "light")
    assert "animation:aw-flow" in text
    rule = re.search(r"@media \(prefers-reduced-motion:reduce\)\{(.*?)\}\}", text)
    assert rule
    assert "animation:none" in rule.group(1)
    # The rule must reach the same element that carries the animation.
    assert ".aw-line" in rule.group(1)


def test_a_project_name_is_escaped_in_the_svg_and_the_alt_text() -> None:
    data = _nasty_data()
    for text in (advisory_watch.file_svg(data, "dark"), advisory_watch.inline_svg(data)):
        assert NASTY_ESCAPED in text
        assert NASTY not in text
        assert "<ma>" not in text
    # The file's label holds the escaped alt text, which parses back to the raw name.
    label = ET.fromstring(advisory_watch.file_svg(data, "dark")).attrib["aria-label"]  # noqa: S314
    assert NASTY in label
    assert f"{html.escape(NASTY)} 5" in html.escape(advisory_watch.alt_text(data))


def test_the_logo_comes_from_the_artwork_file() -> None:
    paths = advisory_watch.mark_paths()
    assert len(paths) == 2
    text = advisory_watch.inline_svg(_data())
    for path_data, stroke_width in paths:
        assert f'<path d="{path_data}" stroke-width="{stroke_width}"' in text


def test_mark_paths_reads_the_two_paths_of_a_file(tmp_path: Path) -> None:
    mark = tmp_path / "mark.svg"
    mark.write_text(
        '<svg><path d="M 1 2" stroke-width="3"/><path d="M 4 5" stroke-width="6"/></svg>',
        encoding="utf-8",
    )
    assert advisory_watch.mark_paths(mark) == [("M 1 2", "3"), ("M 4 5", "6")]


@pytest.mark.parametrize(
    "body",
    [
        "<svg></svg>",
        '<svg><path d="M 1 2" stroke-width="3"/></svg>',
        '<svg><path d="M 1" stroke-width="1"/><path d="M 2" stroke-width="2"/><path d="M 3" stroke-width="3"/></svg>',
    ],
)
def test_mark_paths_refuses_a_file_without_exactly_two_paths(tmp_path: Path, body: str) -> None:
    mark = tmp_path / "mark.svg"
    mark.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match="should hold the mark's two paths"):
        advisory_watch.mark_paths(mark)


def test_file_svg_refuses_an_unknown_theme() -> None:
    with pytest.raises(ValueError, match="Unknown image theme 'sepia'"):
        advisory_watch.file_svg(_data(), "sepia")


def test_drawing_is_deterministic() -> None:
    first, second = _nasty_data(), copy.deepcopy(_nasty_data())
    for theme in advisory_watch.THEMES:
        assert advisory_watch.file_svg(first, theme).encode() == advisory_watch.file_svg(second, theme).encode()
    assert advisory_watch.inline_svg(first) == advisory_watch.inline_svg(second)
    # The data's own order decides the drawing order, so a reordered list is a different file.
    swapped = copy.deepcopy(first)
    swapped["projects"].reverse()
    assert advisory_watch.inline_svg(swapped) != advisory_watch.inline_svg(first)


def test_image_name_holds_the_month_a_hash_of_the_content_and_the_theme() -> None:
    data = _data()
    name = advisory_watch.image_name(data, "svg text", "dark")
    digest = hashlib.sha256(b"svg text").hexdigest()[: advisory_watch.HASH_LENGTH]
    assert len(digest) == 12
    assert name == f"advisories-2026-03-{digest}-dark.svg"
    assert advisory_watch.parse_image_name(name) == {"as_of": "2026-03", "hash": digest, "theme": "dark"}
    # Other content under the same month and theme gets another name, never the same file.
    assert advisory_watch.image_name(data, "other text", "dark") != name
    assert advisory_watch.image_name(data, "svg text", "light") == name.replace("-dark.svg", "-light.svg")


@pytest.mark.parametrize(
    "name",
    [
        "advisories-2026-03-0123456789ab-sepia.svg",
        "advisories-2026-03-0123456789a-dark.svg",
        "advisories-2026-03-0123456789abc-dark.svg",
        "advisories-2026-03-0123456789AB-dark.svg",
        "advisories-2026-3-0123456789ab-dark.svg",
        "advisories-2026-03-0123456789ab-dark.png",
        "errors-20990101T000000Z-0123456789ab-dark.png",
        "../advisories-2026-03-0123456789ab-dark.svg",
        "x/advisories-2026-03-0123456789ab-dark.svg",
        "",
    ],
)
def test_parse_image_name_rejects_other_names(name: str) -> None:
    assert advisory_watch.parse_image_name(name) is None


def test_readme_block_links_both_images_and_escapes_the_alt_text() -> None:
    data = _nasty_data()
    block = advisory_watch.readme_block(data, "light.svg", "dark.svg")

    assert block.startswith(advisory_watch.START_MARKER)
    assert block.endswith(advisory_watch.END_MARKER)
    assert block.count(advisory_watch.START_MARKER) == 1
    assert block.count(advisory_watch.END_MARKER) == 1
    assert f"## {advisory_watch.HEADING}" in block
    assert f'srcset="{advisory_watch.ASSET_URL}/dark.svg"' in block
    assert f'src="{advisory_watch.ASSET_URL}/light.svg"' in block
    # A quote or angle bracket in a name is escaped rather than ending the attribute.
    assert f'alt="{html.escape(advisory_watch.alt_text(data))}"' in block
    assert NASTY not in block
    assert f'width="{advisory_watch.IMAGE_WIDTH}"' in block
    assert f"]({advisory_watch.DETAILS_URL})" in block
    # The sentences are wrapped, so compare them with the whitespace collapsed.
    flat = " ".join(block.split())
    assert advisory_watch.intro(data) in flat
    assert advisory_watch.note(data) in flat


def test_image_names_in_lists_the_dark_file_first_then_the_light_one() -> None:
    data = _data()
    names = {
        theme: advisory_watch.image_name(data, advisory_watch.file_svg(data, theme), theme)
        for theme in advisory_watch.THEMES
    }
    block = advisory_watch.readme_block(data, names["light"], names["dark"])
    assert advisory_watch.image_names_in(block) == [names["dark"], names["light"]]
    assert advisory_watch.image_names_in("no images here") == []


def test_find_block_gives_the_marked_range() -> None:
    readme = _readme()
    start, end = advisory_watch.find_block(readme)
    assert readme[start:end] == f"{advisory_watch.START_MARKER}\nold\n{advisory_watch.END_MARKER}"


def test_replace_block_swaps_only_the_marked_text() -> None:
    assert advisory_watch.replace_block(_readme(), "NEW") == "top\nNEW\nbottom\n"


@pytest.mark.parametrize(
    ("readme", "message"),
    [
        ("no markers here\n", "exactly one"),
        (f"{advisory_watch.START_MARKER}\nonly a start\n", "exactly one"),
        (f"only an end\n{advisory_watch.END_MARKER}\n", "exactly one"),
        (_readme() + _readme(), "exactly one"),
        (f"{advisory_watch.END_MARKER}\n{advisory_watch.START_MARKER}\n", "end marker before its start marker"),
    ],
)
def test_replace_block_refuses_missing_doubled_or_reversed_markers(readme: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        advisory_watch.replace_block(readme, "NEW")


def test_save_never_overwrites_an_existing_file(tmp_path: Path) -> None:
    asset_dir = tmp_path / "nested" / "assets"
    # A missing folder is made, and the first write reports that it wrote.
    assert advisory_watch.save("a.svg", "first", asset_dir) is True
    path = asset_dir / "a.svg"
    assert path.read_text(encoding="utf-8") == "first"
    # A published file is left exactly as it was.
    path.write_text("published", encoding="utf-8")
    assert advisory_watch.save("a.svg", "first", asset_dir) is False
    assert advisory_watch.save("a.svg", "different", asset_dir) is False
    assert path.read_text(encoding="utf-8") == "published"


class _Run:
    """A run of ``main()`` on files in a temporary folder, never the repository's."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: dict[str, Any], readme: str) -> None:
        self.readme_path = tmp_path / "README.md"
        self.asset_dir = tmp_path / "assets"
        self.readme_path.write_text(readme, encoding="utf-8")
        monkeypatch.setattr(advisory_watch, "README_PATH", self.readme_path)
        monkeypatch.setattr(advisory_watch, "ASSET_DIR", self.asset_dir)
        # main() calls load_data() with no argument, so the data must come from here.
        monkeypatch.setattr(advisory_watch, "load_data", lambda: data)
        # save() binds its default folder when the module loads, so the
        # ASSET_DIR above does not reach it; pass the folder explicitly.
        real_save = advisory_watch.save
        monkeypatch.setattr(
            advisory_watch,
            "save",
            lambda name, content: real_save(name, content, self.asset_dir),
        )

    def files(self) -> list[str]:
        return sorted(path.name for path in self.asset_dir.glob("*")) if self.asset_dir.exists() else []


def test_main_writes_both_files_and_rewrites_the_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    data = _data()
    run = _Run(tmp_path, monkeypatch, data, _readme())

    assert advisory_watch.main() == 0

    # Both themes' SVGs are written under names that match their content.
    files = run.files()
    assert len(files) == 2
    for theme in advisory_watch.THEMES:
        content = advisory_watch.file_svg(data, theme)
        name = advisory_watch.image_name(data, content, theme)
        assert name in files
        assert (run.asset_dir / name).read_text(encoding="utf-8") == content
    # The README holds the block for those files, and the text around it is untouched.
    readme = run.readme_path.read_text(encoding="utf-8")
    assert readme.startswith("top\n")
    assert readme.endswith("\nbottom\n")
    block = readme[slice(*advisory_watch.find_block(readme))]
    assert sorted(advisory_watch.image_names_in(block)) == files
    assert "wrote" in capsys.readouterr().out

    # A second run changes nothing and says so.
    assert advisory_watch.main() == 0
    assert run.readme_path.read_text(encoding="utf-8") == readme
    assert run.files() == files
    out = capsys.readouterr().out
    assert "kept" in out
    assert "already up to date" in out


@pytest.mark.parametrize("problem", ["data", "readme"])
def test_main_returns_one_and_writes_nothing_when_a_check_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    problem: str,
) -> None:
    data = _data()
    readme = _readme()
    if problem == "data":
        data["total"] = 1
    else:
        readme = "a README with no advisory block\n"
    run = _Run(tmp_path, monkeypatch, data, readme)

    assert advisory_watch.main() == 1

    # Bad data or a missing block stops the script before any file is written.
    assert run.files() == []
    assert run.readme_path.read_text(encoding="utf-8") == readme
    assert capsys.readouterr().err.startswith("error: ")


@pytest.mark.parametrize("part", ["intro", "note"])
def test_the_component_prints_the_readme_sentence(part: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # The landing page prints each shared sentence through this tag, so it
    # must print exactly what the README block holds.
    data = _data()
    monkeypatch.setattr(advisory_watch, "load_data", lambda: data)
    block = advisory_watch.readme_block(data, "light.svg", "dark.svg")
    text = str(AdvisoryWatch(part=part)).strip()
    assert text == getattr(advisory_watch, part)(data)
    assert text in " ".join(block.split())


def test_the_component_prints_the_inline_graphic_as_markup(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _nasty_data()
    monkeypatch.setattr(advisory_watch, "load_data", lambda: data)
    text = str(AdvisoryWatch(part="chart"))
    # The SVG arrives as markup, not as escaped text, wrapped for the landing page.
    assert f'<div class="landing-advisories">{advisory_watch.inline_svg(data)}</div>' in text
    assert "&lt;svg" not in text
    assert NASTY_ESCAPED in text
    # Blank lines keep a Markdown pass from joining it to the next paragraph.
    assert text.startswith("\n\n")
    assert text.endswith("\n\n")


@pytest.mark.parametrize("part", ["intro", "chart", "note"])
def test_the_component_refuses_data_that_does_not_add_up(part: str, monkeypatch: pytest.MonkeyPatch) -> None:
    data = _data()
    data["total"] = 1
    monkeypatch.setattr(advisory_watch, "load_data", lambda: data)
    with pytest.raises(Exception, match="project counts add up to 1234"):
        str(AdvisoryWatch(part=part))
