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
    _EDITOR_MARKS,
    _EDITOR_NOTES,
    _EDITOR_PATH,
    _ERROR_CASES,
    _HOST_CASES,
    _TOUR_PATH,
    _TOUR_STOPS,
    LandingDepth,
    LandingEditorDemoMarkup,
    LandingTour,
    _capture,
    _check_depth_docs,
    _check_host_entrypoints,
    _editor_code,
    _editor_ranges,
    _inline_code_markup,
    _render_diagnostics,
    _tour_code,
)
from docs_site._internal.components.landing_composer import (
    _RECIPES,
    _initial_state,
    _instantiate,
    _serialize_source,
)
from docs_site._internal.nav import SCOPE_SITE, NavArea, NavItem, NavTree
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import default_docs_project


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
    assert document.xpath('//script[@type="module" and @src="/static/playground/landing_composer.js"]')


def test_landing_composer_catalog_and_fallback_are_generated_together() -> None:
    """The palette and inert recipe bank share one checked catalog."""
    source = Path("docs_site/content/index.md").read_text(encoding="utf-8")
    document = lxml_html.document_fromstring(render_page(source, current_path="").html)
    composer = document.xpath("//*[@data-landing-composer]")[0]
    banks = composer.xpath('.//script[@type="application/json" and @data-composer-recipe-bank]')
    assert len(banks) == 1
    recipe_markup = json.loads(banks[0].text)
    recipe_document = lxml_html.fragment_fromstring(recipe_markup, create_parent="div")
    templates = recipe_document.xpath(".//template[@data-composer-recipe-template]")

    assert {template.get("data-composer-recipe-template") for template in templates} == {
        recipe["id"] for recipe in _RECIPES
    }
    assert len(composer.xpath(".//*[@data-composer-palette-item]")) == len(_RECIPES)
    assert not composer.xpath('.//*[@data-composer-palette-drag="stack"]')
    assert composer.xpath(
        './/div[contains(@class, "landing-composer__bar")]'
        '//h3[@id="landing-composer-palette-title" and normalize-space(.)="Citry UI components"]'
    )
    assert composer.xpath(
        './/aside[contains(@class, "landing-composer__palette")][@aria-labelledby="landing-composer-palette-title"]'
    )
    assert len(composer.xpath('./div[contains(@class, "landing-composer__layout")]/*')) == 2
    assert len(composer.xpath(".//aside")) == 1
    assert not composer.xpath(".//textarea | .//iframe")
    assert not composer.xpath(
        ".//*[@data-composer-announcer or @data-composer-status]"
        " | .//*[contains(@class, 'landing-composer__workspace-heading')]"
    )
    assert composer.xpath('.//section[@aria-label="Component sample page"]')
    assert all(len(item.xpath("./button")) == 1 for item in composer.xpath(".//*[@data-composer-palette-item]"))
    assert len(composer.xpath(".//*[@data-composer-canvas]/*[@data-composer-drop]")) == 1
    assert not composer.xpath(".//*[@data-composer-undo] | .//*[@data-composer-node] | .//*[@data-composer-slot]")
    assert recipe_document.xpath(".//style[not(@data-citry-css-class)]")
    assert recipe_document.xpath(".//style[@data-citry-css-class]")
    assert not composer.xpath('.//script[not(@type="application/json")]')
    assert not recipe_document.xpath(".//p")

    for template in templates:
        assert template.xpath(".//*[@data-citry-ui-part]")
        assert len(template.xpath(".//*[@data-composer-drop]")) <= 2

    card = recipe_document.xpath('.//template[@data-composer-recipe-template="card"]')[0]
    assert card.xpath('.//*[@data-citry-ui-part="card"]')
    assert card.xpath('.//*[@data-citry-ui-part="skeleton"]')
    assert card.xpath('.//*[@data-citry-ui-part="actions"]/*[@data-composer-drop]')
    grid = recipe_document.xpath('.//template[@data-composer-recipe-template="grid"]')[0]
    assert len(grid.xpath(".//*[@data-composer-drop]")) == 2


def test_every_landing_composer_recipe_produces_runnable_citry_source() -> None:
    """A palette entry cannot ship unless the generated source constructs the real family."""
    state = _initial_state()
    state["root"]["slots"]["default"] = []
    for recipe in _RECIPES:
        node, state["nextId"] = _instantiate(recipe["node"], start=state["nextId"])
        state["root"]["slots"]["default"].append(node)

    source = _serialize_source(state)
    namespace: dict[str, object] = {}
    exec(compile(source, "<landing-composer>", "exec"), namespace)  # noqa: S102 - generated trusted fixture
    rendered = str(namespace["preview"])
    document = lxml_html.fragment_fromstring(rendered, create_parent="div")

    assert document.xpath('.//*[@data-citry-ui-part="tabs"]')
    assert document.xpath('.//*[@data-citry-ui-part="card"]')
    assert document.xpath('.//button[@data-citry-ui-part="button"]')
    assert document.xpath('.//*[@data-citry-ui-part="grid"]')


def test_non_landing_pages_do_not_load_the_composer_controller() -> None:
    result = render_page("---\ntitle: Guide\n---\n\n# Guide\n", current_path="guide/")

    assert "/static/playground/landing_composer.js" not in result.html


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


def test_people_section_identifies_the_maintainer_and_keeps_the_people_route() -> None:
    source = Path("docs_site/content/index.md").read_text(encoding="utf-8")
    document = lxml_html.document_fromstring(render_page(source, current_path="").html)
    section = document.xpath('//section[@id="people"]')[0]
    maintainer = section.xpath('.//div[contains(@class, "landing-maintainer")]')[0]

    assert len(maintainer.xpath('.//div[contains(@class, "landing-maintainer__portrait")]//img')) == 1
    assert maintainer.xpath('.//p[contains(@class, "landing-maintainer__name")]/a[@href="/community/people/"]')
    assert maintainer.xpath('.//p[contains(@class, "landing-maintainer__role")]')
    assert section.xpath('.//div[contains(@class, "landing-human-links")]/a[@href="/community/people/"]')


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


def test_editor_demo_marks_exact_symbols_without_changing_the_source() -> None:
    """Interactive wrappers add behavior, but must not repaint or rewrite the sample."""
    source = Path(_EDITOR_PATH).read_text(encoding="utf-8")
    rendered = _editor_code(source, _EDITOR_MARKS)
    document = lxml_html.fragment_fromstring(rendered, create_parent="div")
    annotations = document.xpath(".//*[@data-editor-annotation]")
    symbols = document.xpath(".//button[@data-editor-symbol]")
    definitions = document.xpath(".//span[@data-editor-definition]")

    assert len(annotations) == len(_EDITOR_MARKS)
    assert document.xpath(".//pre")[0].text_content() == source
    assert {item.get("data-editor-annotation") for item in annotations} == {mark["id"] for mark in _EDITOR_MARKS}
    assert {item.get("data-editor-definition") for item in definitions} == {
        mark["definition"] for mark in _EDITOR_MARKS if mark.get("definition")
    }
    assert {item.get("data-editor-symbol") for item in symbols} == {
        mark["id"] for mark in _EDITOR_MARKS if not mark.get("definition")
    }
    # The Pygments token span remains inside the button, so the dotted target
    # keeps exactly the syntax colour it had before becoming interactive.
    assert all(item.xpath(".//span[@class]") for item in annotations)


def test_editor_demo_annotations_fail_closed_when_the_source_drifts() -> None:
    """A stale or ambiguous annotation must fail the page instead of marking the wrong name."""
    stale = ({**_EDITOR_MARKS[0], "needle": "text that is not in the source"},)
    ambiguous = ({**_EDITOR_MARKS[0], "needle": "title", "symbol": "title"},)
    source = Path(_EDITOR_PATH).read_text(encoding="utf-8")

    with pytest.raises(RuntimeError, match="needs one occurrence"):
        _editor_ranges(source, stale)
    with pytest.raises(RuntimeError, match="needs one occurrence"):
        _editor_ranges(source, ambiguous)


def test_editor_note_inline_code_escapes_prose_and_code() -> None:
    rendered = _inline_code_markup("Use <unsafe> & `call(<value>)`, then `result`.")
    document = lxml_html.fragment_fromstring(str(rendered), create_parent="p")

    assert not document.xpath(".//unsafe | .//value")
    assert [node.text for node in document.xpath("./code")] == ["call(<value>)", "result"]
    assert document.text_content() == "Use <unsafe> & call(<value>), then result."


@pytest.mark.parametrize("text", ["An `unfinished span", "An empty `` span"])
def test_editor_note_inline_code_rejects_malformed_spans(text: str) -> None:
    with pytest.raises(ValueError, match="Editor note inline code"):
        _inline_code_markup(text)


def test_editor_demo_pairs_symbols_hovers_notes_and_definitions() -> None:
    """Every interactive affordance names a server-rendered target that exists."""
    document = lxml_html.document_fromstring(str(LandingEditorDemoMarkup()))
    showcase = document.xpath("//*[@data-editor-showcase]")[0]
    symbols = {item.get("data-editor-symbol"): item for item in document.xpath("//*[@data-editor-symbol]")}
    hover = document.xpath("//*[@data-editor-hover]")[0]
    definitions = {item.get("data-editor-definition") for item in document.xpath("//*[@data-editor-definition]")}

    assert "landing-editor__code" in showcase[0].classes
    assert "landing-editor__notes" in showcase[1].classes
    assert hover.get("role") == "dialog"
    assert hover.get("hidden") == ""
    assert hover.xpath(".//*[@data-editor-hover-signature]")
    docs_link = hover.xpath(".//a[@data-editor-hover-docs]")[0]
    assert docs_link.get("target") == "_blank"
    assert docs_link.get("rel") == "noopener"
    assert hover.xpath(".//a[@data-editor-jump]")
    for symbol in symbols.values():
        assert symbol.get("aria-controls") == hover.get("id")
        assert symbol.get("aria-expanded") == "false"
        assert symbol.get("aria-label")
        assert symbol.get("data-editor-signature")
        assert '<span class="' in symbol.get("data-editor-signature-html")
        assert symbol.get("data-editor-provenance")
        assert symbol.get("data-editor-description")
        assert symbol.get("data-editor-docs").startswith("/")
        if target := symbol.get("data-editor-target"):
            assert target in definitions

    # Destination declarations remain visually inert until a jump flashes them.
    assert not document.xpath("//*[@data-editor-definition and @data-editor-symbol]")

    assert symbols["title-use"].get("data-editor-placement") == "below"
    assert all(
        symbol.get("data-editor-placement") is None for mark_id, symbol in symbols.items() if mark_id != "title-use"
    )

    expected_targets = {
        "title-use": "template-title",
        "member-type-use": "member-type",
        "invite-type-use": "invite-type",
        "kwargs-title-use": "kwarg-title",
        "kwargs-members-use": "kwarg-members",
        "member-chip-use": "member-chip",
        "member-chip-name-use": "member-chip-name",
        "member-chip-status-use": "member-chip-status",
        "member-name-use": "member-name",
        "nested-title-use": "template-title",
        "member-chip-online-use": "member-chip-online",
        "member-online-use": "member-online",
        "event-name": "event-invite",
        "email-use": "scope-email",
        "inviting-use": "js-inviting",
        "visible-members-use": "visible-members",
        "data-members-slice-use": "js-members",
        "data-members-fallback-use": "js-members",
    }
    assert {mark_id: symbols[mark_id].get("data-editor-target") for mark_id in expected_targets} == expected_targets

    expected_diagnostics = {
        "unknown-template-variable": "citry.template.unknown-variable",
        "unknown-alpine-variable": "citry.alpine.unknown-variable",
        "unknown-event": "citry.browser.unknown-server-event",
    }
    for mark_id, code in expected_diagnostics.items():
        symbol = symbols[mark_id]
        assert "landing-editor__symbol--error" in symbol.classes
        assert symbol.get("data-editor-severity") == "error"
        assert symbol.get("data-editor-diagnostic") == code

    note_targets = {note.get("data-editor-note") for note in document.xpath("//*[@data-editor-note]")}
    assert note_targets == {note["mark"] for note in _EDITOR_NOTES}
    assert note_targets <= symbols.keys()


def test_the_editor_demo_source_is_valid_python() -> None:
    """The interactive surface is generated from code a reader can copy and edit."""
    source = Path(_EDITOR_PATH).read_text(encoding="utf-8")

    ast.parse(source)
    assert source.index("class InvitePanel(Component):") < source.index("class MemberChip(Component):")
    assert 'c-status="<>\n' in source
    assert "<small c-title='title'>" in source


def test_injected_component_markup_survives_the_markdown_pass() -> None:
    """
    Generated markup must reach the page as written, not as paragraphs.

    The markdown pass looks for markdown inside raw HTML and gives up around
    preformatted code and around a <button> that wraps block content, wrapping
    everything after it in stray paragraph tags.
    """
    source = (Path("docs_site/content/index.md")).read_text(encoding="utf-8")
    html = render_page(source, current_path="").html

    for stray in ("<p><div", "<p></div>", "<p></p>", "<p></template>"):
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


def test_i18n_is_the_third_depth_case_before_fragments() -> None:
    """The landing progression introduces i18n before fragment transport."""
    case_ids = [case["id"] for case in _DEPTH_CASES]

    assert case_ids[2] == "i18n"
    assert case_ids.index("i18n") < case_ids.index("fragments")


def test_security_depth_moves_from_csrf_rollout_to_strict_csp() -> None:
    """The security progression names both request and browser-code policy."""
    case_ids = [case["id"] for case in _DEPTH_CASES]
    csp = next(case for case in _DEPTH_CASES if case["id"] == "csp")

    assert case_ids.index("csrf") < case_ids.index("csp") < case_ids.index("fragments")
    assert "CSP nonce" in str(csp["note"])
    assert 'security_csp="strict"' in csp["code"]
    assert "serialize_result(csp_nonce=nonce)" in csp["code"]


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
        settings = default_docs_project().settings
        assert [a.get("href") for a in links] == [
            settings.repository.url,
            settings.pypi_url,
            settings.discord_url,
        ]
        # An icon-only link needs its name from somewhere.
        assert all(a.get("rel") == "noopener" for a in links)
