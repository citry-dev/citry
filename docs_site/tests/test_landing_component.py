"""Focused tests for the purpose-built project landing page."""

from __future__ import annotations

import ast
import base64
import json
import re
from html import unescape
from pathlib import Path

import pytest
from lxml import html as lxml_html

from docs_site._internal.components.landing import (
    _DEPTH_CASES,
    _ERROR_CASES,
    _HOST_CASES,
    _TOUR_PATH,
    _TOUR_STOPS,
    LandingDepth,
    LandingTour,
    _capture,
    _check_depth_docs,
    _check_host_entrypoints,
    _render_diagnostics,
    _tour_code,
)
from docs_site._internal.components.social_links import DISCORD_URL, PYPI_URL, REPO_URL
from docs_site._internal.nav import SCOPE_SITE, NavArea, NavItem, NavTree
from docs_site._internal.pipeline import render_page


def _landing_nav() -> NavTree:
    return NavTree(
        home=NavItem(title="Citry", path="/", scope=SCOPE_SITE),
        areas=[
            NavArea(
                label="Docs",
                items=[NavItem(title="Overview", path="/docs/")],
            ),
        ],
    )


def test_landing_layout_keeps_shared_header_and_omits_document_chrome() -> None:
    result = render_page(
        "---\ntitle: Citry\nlayout: landing\n---\n\n# Build the frontend in Python\n",
        nav_tree=_landing_nav(),
        current_path="",
    )
    document = lxml_html.document_fromstring(result.html)

    assert document.xpath('//body[contains(@class, "citry-landing-page")]')
    assert document.xpath('//header[contains(@class, "djc-header")]')
    assert document.xpath('//main[@id="landing-main"]')
    assert document.xpath('//article[contains(@class, "landing-content")]//*[@id="build-the-frontend-in-python"]')
    assert document.xpath('//nav[@aria-label="Primary navigation"]/a[@href="/docs/"]')
    assert not document.xpath('//nav[@aria-label="Section navigation"]')
    assert not document.xpath('//aside[@id="djc-toc"]')
    assert not document.xpath('//nav[contains(@class, "djc-breadcrumbs")]')
    assert not document.xpath('//div[contains(@class, "djc-layout")]')


def test_reliability_diagnostics_come_from_real_failed_renders() -> None:
    """Each promoted failure is captured from a render, not written by hand."""
    captured = {case["id"]: case for case in json.loads(_render_diagnostics())}

    assert set(captured) == {case["id"] for case in _ERROR_CASES}
    assert captured["input"]["type"] == "TypeError"
    assert "missing 1 required positional argument: 'title'" in captured["input"]["message"]
    assert captured["misspelled"]["type"] == "TypeError"
    assert "Did you mean 'title'?" in captured["misspelled"]["message"]
    # A child reading a parent's variable fails, and the error names the path.
    assert captured["isolation"]["type"] == "KeyError"
    assert "Parent > Child" in captured["isolation"]["message"]
    assert captured["unsafe"]["type"] == "SecurityError"
    # Every message keeps the source excerpt and caret Citry draws.
    for case_id in ("template", "isolation", "unknown", "unsafe"):
        assert "^^^" in captured[case_id]["message"], case_id
    # Neither a build machine's checkout path nor a stand-in module name is
    # something a reader can act on.
    for case in captured.values():
        assert "/Users/" not in case["message"]
        assert "builtins::" not in case["message"]


def test_each_diagnostic_shows_the_code_that_produced_it() -> None:
    """The snippet on the page is the source the build ran, not a retelling."""
    captured = {case["id"]: case for case in json.loads(_render_diagnostics())}

    for case in _ERROR_CASES:
        shown = captured[case["id"]]["code"]
        # The highlighted block is that snippet, so every line of the source
        # has to be present in it once the markup is stripped.
        plain = unescape(re.sub(r"<[^>]+>", "", shown))
        for line in case["code"].splitlines():
            assert line.strip() in plain, (case["id"], line)
        assert len(case["code"].splitlines()) <= 10


def test_a_diagnostic_that_stops_raising_fails_the_build() -> None:
    """The reliability claim cannot outlive the behavior it describes."""
    with pytest.raises(RuntimeError, match="no longer raises"):
        _capture(lambda: "this render succeeded", TypeError, "anything")


def test_a_diagnostic_that_loses_its_detail_fails_the_build() -> None:
    """A still-raising error that dropped its guidance is also stale."""

    def raise_without_the_suggestion() -> object:
        message = "got an unexpected keyword argument 'titel'"
        raise TypeError(message)

    with pytest.raises(RuntimeError, match="lost its detail"):
        _capture(raise_without_the_suggestion, TypeError, "Did you mean 'title'?")


def test_the_landing_page_publishes_no_unrendered_markdown() -> None:
    """Nested grids must stay markdown contexts, or headings ship as literal text."""
    source = (Path("docs_site/content/index.md")).read_text(encoding="utf-8")
    document = lxml_html.document_fromstring(render_page(source, current_path="").html)
    content = document.xpath('//article[contains(@class, "landing-content")]')[0]
    text = "\n".join(content.itertext())

    assert not [line for line in text.split("\n") if line.startswith(("### ", "- "))]
    # The trust cards carry real headings and links, not markdown source.
    assert content.xpath('//div[@class="landing-trust-card"]/h3')
    assert content.xpath('//a[@href="/about/compatibility/"]')

    # Component markup that lands in a markdown block must be flushed left.
    # Indented HTML there is read as an indented code block, which printed the
    # diagnostic panel as source and broke every section under it.
    assert "<div class=" not in text
    assert content.xpath('.//div[contains(@class, "landing-diagnostic")]/pre')
    # The proof section shows exactly one sample; the reliability panels each
    # carry the snippet that produced their error.
    proof = content.xpath('.//section[@id="proof"]')[0]
    assert len(proof.xpath('.//div[contains(@class, "highlight")]')) == 1
    reliability = content.xpath('.//section[@id="reliability"]')[0]
    panels = reliability.xpath(".//div[@data-picker-panel]")
    assert len(panels) == len(_ERROR_CASES)
    for panel in panels:
        assert len(panel.xpath('.//div[contains(@class, "landing-picker__code")]//pre')) == 1


def test_contributor_grid_can_drop_the_per_person_counts() -> None:
    """The landing page acknowledges people without turning them into a scoreboard."""
    plain = render_page('---\ntitle: T\n---\n\n<c-people group="contributors" plain />\n', current_path="x")
    counted = render_page('---\ntitle: T\n---\n\n<c-people group="contributors" />\n', current_path="x")

    assert "Contributions:" not in plain.html
    assert "Contributions:" in counted.html
    assert plain.html.count("avatar-wrapper") == counted.html.count("avatar-wrapper")


def test_walkthrough_stops_point_at_the_right_lines() -> None:
    """Line numbers drift as the example is edited; each stop must still land on it."""
    source = (Path(_TOUR_PATH)).read_text(encoding="utf-8").splitlines()

    for stop in _TOUR_STOPS:
        first, last = stop["lines"]
        assert 1 <= first <= last <= len(source), stop["id"]
        region = "\n".join(source[first - 1 : last])
        # The anchor is the text the note claims to explain.
        assert stop["anchor"] in region, (stop["id"], stop["anchor"], region)


def test_walkthrough_marks_every_stop_in_the_highlighted_source() -> None:
    """Each stop reaches the page as hoverable lines with one marker."""
    source = (Path(_TOUR_PATH)).read_text(encoding="utf-8")
    html = _tour_code(source, _TOUR_STOPS)

    for stop in _TOUR_STOPS:
        assert f'data-tour="{stop["id"]}"' in html, stop["id"]
    # One dot per stop, at the first line of its range.
    assert html.count("data-tour-start") == len(_TOUR_STOPS)


def test_the_walkthrough_example_is_valid_python() -> None:
    """
    The page shows this file as source, so it must at least parse.

    It is deliberately not runnable: it leaves out the engine setup and the
    child component's definition so the reader sees the concepts rather than
    the scaffolding. Parsing is the guarantee that still applies.
    """
    source = Path(_TOUR_PATH).read_text(encoding="utf-8")

    ast.parse(source)
    # The concepts the notes promise have to be present in the source.
    for needle in ("class Kwargs", "class Slots", "class State", "class Events", "class Dependencies"):
        assert needle in source, needle


def test_host_examples_name_adapters_that_exist() -> None:
    """A renamed adapter must fail the build, not publish a dead instruction."""
    _check_host_entrypoints()

    for case in _HOST_CASES:
        module_name, attribute = case["entrypoint"]
        # The snippet has to actually call the entry point it is checked against.
        assert attribute in case["code"], case["id"]
        assert module_name in case["code"], case["id"]


def test_a_moved_adapter_fails_the_host_section(monkeypatch: pytest.MonkeyPatch) -> None:
    """The check is real: point one case at a name that is gone."""
    broken = ({**_HOST_CASES[0], "entrypoint": ("citry.contrib.fastapi", "mount_somewhere_else")},)
    monkeypatch.setattr("docs_site._internal.components.landing._HOST_CASES", broken)

    with pytest.raises(RuntimeError, match="no longer exists"):
        _check_host_entrypoints()


def test_walkthrough_offers_the_original_source_for_copying() -> None:
    """Block-per-line markup carries no newlines, so copy must not read the DOM."""
    source = (Path(_TOUR_PATH)).read_text(encoding="utf-8")
    document = lxml_html.document_fromstring(str(LandingTour()))
    tour = document.xpath("//div[@data-landing-tour]")[0]

    assert base64.b64decode(tour.get("data-tour-source")).decode() == source
    # The rendered lines really do lack newlines, which is why the above matters.
    rendered = "".join(tour.xpath('.//span[contains(@class, "landing-tour__line")]/text()'))
    assert "\n" not in rendered


def test_walkthrough_notes_render_markup_rather_than_escaping_it() -> None:
    """
    A note names attributes and methods, which read better as code.

    The wording is content and belongs to the page, so this checks the
    mechanism: markup in a note becomes real elements, and an angle bracket in
    a tag name survives as text instead of being parsed into an element.
    """
    document = lxml_html.document_fromstring(str(LandingTour()))
    notes = {n.get("data-tour-note"): n for n in document.xpath("//div[@data-tour-note]")}

    control = notes["control"]
    code_tags = control.xpath(".//code")
    assert code_tags, "the control note is written with inline code"
    text = "".join(control.itertext())
    for tag in code_tags:
        rendered = "".join(tag.itertext())
        assert rendered in text
        # An escaped tag name stays text; it must not become an element.
        if rendered.startswith("<"):
            assert not control.xpath(f".//{rendered.strip('<>').split()[0]}")


def test_injected_component_markup_survives_the_markdown_pass() -> None:
    """
    Generated markup must reach the page as written, not as paragraphs.

    The markdown pass looks for markdown inside raw HTML and gives up around
    preformatted code and around a <button> that wraps block content, wrapping
    everything after it in stray paragraph tags.
    """
    source = (Path("docs_site/content/index.md")).read_text(encoding="utf-8")
    html = render_page(source, current_path="").html

    for stray in ("<p><div", "<p></div>", "<p></p>"):
        assert stray not in html, stray
    # The attribute that asks for this is consumed, not published.
    assert 'markdown="0"' not in html

    document = lxml_html.document_fromstring(html)
    # Indentation and newlines inside a code block survive the round trip.
    code = document.xpath('//div[@data-picker-panel="input"]//div[contains(@class, "highlight")]//pre')[0]
    text = code.text_content()
    assert len(text.split("\n")) > 1
    assert "    complete" in text


def test_advanced_capabilities_link_to_pages_that_exist() -> None:
    """A promoted capability must keep the page that explains it."""
    _check_depth_docs()

    for case in _DEPTH_CASES:
        assert (Path("docs_site/content") / case["doc"]).is_file(), case["id"]


def test_a_removed_capability_page_fails_the_build(monkeypatch: pytest.MonkeyPatch) -> None:
    """The check is real: point one case at a page that is not there."""
    broken = ({**_DEPTH_CASES[0], "doc": "advanced/gone-away.md"},)
    monkeypatch.setattr("docs_site._internal.components.landing._DEPTH_CASES", broken)

    with pytest.raises(RuntimeError, match="is gone"):
        _check_depth_docs()


def test_every_picker_shares_one_mechanism() -> None:
    """Three sections use the picker; each must ship rows, panels, and carets."""
    source = (Path("docs_site/content/index.md")).read_text(encoding="utf-8")
    document = lxml_html.document_fromstring(render_page(source, current_path="").html)
    pickers = document.xpath("//div[@data-landing-picker]")

    assert len(pickers) == 3
    for picker in pickers:
        rows = picker.xpath(".//button[@data-picker-case]")
        panels = picker.xpath(".//div[@data-picker-panel]")
        carets = picker.xpath('.//svg[contains(@class, "landing-picker__caret")]')
        assert len(rows) == len(panels) == len(carets)
        # A row and its panel are paired by id, so the list cannot point at
        # something the section does not show.
        assert [r.get("data-picker-case") for r in rows] == [p.get("data-picker-panel") for p in panels]


def test_each_advanced_capability_explains_itself_above_its_code() -> None:
    """A snippet alone does not say what the capability is or what it costs."""
    document = lxml_html.document_fromstring(str(LandingDepth()))
    panels = document.xpath("//div[@data-picker-panel]")

    assert len(panels) == len(_DEPTH_CASES)
    for panel in panels:
        note = panel.xpath('./div[contains(@class, "landing-picker__note")]')
        assert note, panel.get("data-picker-panel")
        assert len(note[0].xpath("./p")) >= 1
        # The note comes before the code it introduces.
        assert "landing-picker__code" in (note[0].getnext().get("class") or "")


def test_social_links_point_at_one_set_of_urls() -> None:
    """The header, hero, and footer must not drift to different destinations."""
    source = (Path("docs_site/content/index.md")).read_text(encoding="utf-8")
    document = lxml_html.document_fromstring(render_page(source, current_path="").html)

    rows = document.xpath('//div[contains(@class, "social-links")]')
    assert len(rows) == 2  # the hero and the footer
    for row in rows:
        links = row.xpath('.//a[contains(@class, "social-links__link")]')
        assert [a.get("aria-label") for a in links] == ["GitHub", "PyPI", "Discord"]
        assert [a.get("href") for a in links] == [REPO_URL, PYPI_URL, DISCORD_URL]
        # An icon-only link needs its name from somewhere.
        assert all(a.get("rel") == "noopener" for a in links)
