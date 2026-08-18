"""Browser evidence for the landing-page Citry UI showcase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def _composer_surface_styles(composer: Any) -> dict[str, str]:
    return composer.evaluate(
        """root => {
          const workspace = root.querySelector('.landing-composer__workspace');
          const canvas = root.querySelector('[data-composer-canvas]');
          const probe = document.createElement('span');
          probe.style.cssText = 'position:fixed;pointer-events:none;background:Canvas;color:CanvasText';
          root.append(probe);
          const workspaceStyle = getComputedStyle(workspace);
          const canvasStyle = getComputedStyle(canvas);
          const probeStyle = getComputedStyle(probe);
          const result = {
            stageBackgroundImage: workspaceStyle.backgroundImage,
            stageBoxShadow: workspaceStyle.boxShadow,
            artboardBackgroundColor: canvasStyle.backgroundColor,
            artboardColor: canvasStyle.color,
            artboardBoxShadow: canvasStyle.boxShadow,
            nativeCanvas: probeStyle.backgroundColor,
            nativeCanvasText: probeStyle.color,
          };
          probe.remove();
          return result;
        }"""
    )


def test_landing_showcase_is_simple_nestable_and_visibly_draggable(
    page: Any,
    docs_site_url: str,
) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()

    assert composer.locator(".landing-composer__layout > *").count() == 2
    assert composer.locator("aside").count() == 1
    assert composer.locator('[data-composer-palette-drag="stack"]').count() == 0
    assert composer.locator(".landing-composer__bar h3").text_content().strip() == "Citry UI components"
    assert composer.locator(".landing-composer__palette > h3").count() == 0
    palette = composer.locator(".landing-composer__palette")
    assert palette.evaluate("element => element.scrollHeight <= element.clientHeight + 1")
    workspace = composer.locator(".landing-composer__workspace")
    canvas = composer.locator("[data-composer-canvas]")
    stage_style = workspace.evaluate(
        """element => ({
          backgroundImage: getComputedStyle(element).backgroundImage,
          boxShadow: getComputedStyle(element).boxShadow,
        })"""
    )
    artboard_style = canvas.evaluate(
        """element => ({
          backgroundColor: getComputedStyle(element).backgroundColor,
          boxShadow: getComputedStyle(element).boxShadow,
        })"""
    )
    assert "gradient" in stage_style["backgroundImage"]
    assert stage_style["boxShadow"] != "none"
    assert artboard_style["backgroundColor"] not in {"rgba(0, 0, 0, 0)", "transparent"}
    assert artboard_style["boxShadow"] != "none"
    workspace_box = workspace.bounding_box()
    canvas_box = canvas.bounding_box()
    assert workspace_box
    assert canvas_box
    assert canvas_box["x"] - workspace_box["x"] >= 16
    assert canvas_box["y"] - workspace_box["y"] >= 16
    assert composer.locator("textarea, iframe").count() == 0
    assert (
        composer.locator(
            "[data-composer-announcer], [data-composer-status], .landing-composer__workspace-heading"
        ).count()
        == 0
    )
    assert (
        composer.locator("[data-composer-palette-item] > button").count()
        == composer.locator(
            "[data-composer-palette-item]",
        ).count()
    )
    assert canvas.locator("[data-composer-rendered-recipe]").count() == 0
    assert canvas.locator("[data-composer-drop]").count() == 1
    assert composer.locator("[data-composer-undo], [data-composer-node], [data-composer-slot]").count() == 0

    # The palette row is also the keyboard action. It places a populated,
    # server-rendered Card rather than a structural representation of one.
    card_recipe = composer.locator('[data-composer-palette-drag="card"]')
    card_recipe.focus()
    card_recipe.press("Enter")
    card = canvas.locator('[data-citry-ui-part="card"]')
    card.wait_for()
    assert card.locator('[data-citry-ui-part="header"]', has_text="Observation summary").count() == 1
    assert card.locator('[data-citry-ui-part="body"]', has_text="Three clear nights").count() == 1
    skeleton = card.locator('[data-citry-ui-part="skeleton"]')
    assert skeleton.count() == 1
    assert skeleton.bounding_box()["height"] > 80
    flow_drops = canvas.locator(".landing-composer__drop--flow")
    assert flow_drops.count() == 2
    assert flow_drops.evaluate_all(
        "elements => elements.every(element => element.getBoundingClientRect().height <= 1)"
    )
    assert canvas.locator("[data-composer-drop]").count() == 3
    action_drop = card.locator('[data-citry-ui-part="actions"] [data-composer-drop]')
    assert action_drop.count() == 1

    # Picking up a palette card lifts it, adds a pointer-following card, tints
    # the board, and highlights every compatible destination before release.
    button_recipe = composer.locator('[data-composer-palette-drag="button"]')
    button_recipe.scroll_into_view_if_needed()
    start = button_recipe.bounding_box()
    assert start
    page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
    page.mouse.down()
    page.mouse.move(start["x"] + start["width"] / 2 + 12, start["y"] + start["height"] / 2 + 8)

    assert composer.get_attribute("data-composer-dragging") == "action"
    assert composer.locator(".landing-composer__drag-ghost").count() == 0
    assert page.locator("body > .landing-composer__drag-ghost").count() == 1
    assert canvas.locator("[data-composer-drop].is-drag-available").count() == 3
    assert flow_drops.evaluate_all(
        "elements => elements.every(element => element.getBoundingClientRect().height <= 1)"
    )
    first_gap = flow_drops.first.evaluate(
        """element => {
          const rect = element.getBoundingClientRect();
          return { x: rect.left + rect.width / 2, y: rect.top };
        }"""
    )
    page.mouse.move(first_gap["x"], first_gap["y"])
    page.wait_for_function(
        """() => {
          const gaps = [...document.querySelectorAll(
            '[data-composer-canvas] .landing-composer__drop--flow'
          )];
          return gaps.filter(element => element.classList.contains('is-drag-near')).length === 1
            && gaps.some(element => element.getBoundingClientRect().height >= 40)
            && gaps.some(element => element.getBoundingClientRect().height <= 1);
        }"""
    )
    drag_style = button_recipe.evaluate(
        """element => ({
          transform: getComputedStyle(element).transform,
          boxShadow: getComputedStyle(element).boxShadow,
        })""",
    )
    assert drag_style["transform"] != "none"
    assert drag_style["boxShadow"] != "none"

    action_drop.scroll_into_view_if_needed()
    end = action_drop.bounding_box()
    assert end
    page.mouse.move(end["x"] + end["width"] / 2, end["y"] + end["height"] / 2, steps=8)
    end = action_drop.bounding_box()
    assert end
    page.mouse.move(end["x"] + end["width"] / 2, end["y"] + end["height"] / 2)
    assert action_drop.evaluate("element => element.classList.contains('is-drag-target')")
    page.mouse.up()

    assert composer.get_attribute("data-composer-dragging") is None
    rendered_button = card.locator('[data-citry-ui-part="actions"] [data-citry-ui-part="button"]')
    assert rendered_button.count() == 1
    assert rendered_button.text_content().strip() == "Create observation"
    inline_flow_drops = card.locator(
        '[data-citry-ui-part="actions"] .landing-composer__drop--flow[data-composer-drop-axis="inline"]',
    )
    assert inline_flow_drops.count() == 2
    assert inline_flow_drops.evaluate_all(
        "elements => elements.every(element => element.getBoundingClientRect().width <= 1)"
    )
    assert inline_flow_drops.evaluate_all(
        "elements => elements.map(element => element.dataset.composerFlowPosition)",
    ) == ["start", "end"]
    assert canvas.locator("[data-composer-drop]").count() == 4

    # Horizontal component regions expose logical start/end gaps and grow
    # those gaps along the inline axis for the next drag.
    badge_recipe = composer.locator('[data-composer-palette-drag="badge"]')
    badge_recipe.scroll_into_view_if_needed()
    badge_start = badge_recipe.bounding_box()
    assert badge_start
    page.mouse.move(
        badge_start["x"] + badge_start["width"] / 2,
        badge_start["y"] + badge_start["height"] / 2,
    )
    page.mouse.down()
    page.mouse.move(
        badge_start["x"] + badge_start["width"] / 2 + 12,
        badge_start["y"] + badge_start["height"] / 2 + 8,
    )
    assert inline_flow_drops.evaluate_all(
        "elements => elements.every(element => element.getBoundingClientRect().width <= 1)"
    )
    inline_gap = inline_flow_drops.first.evaluate(
        """element => {
          const rect = element.getBoundingClientRect();
          return { x: rect.left, y: rect.top + rect.height / 2 };
        }"""
    )
    page.mouse.move(inline_gap["x"], inline_gap["y"])
    page.wait_for_function(
        """() => {
          const gaps = [...document.querySelectorAll(
            '[data-citry-ui-part="actions"] .landing-composer__drop--flow[data-composer-drop-axis="inline"]'
          )];
          return gaps.filter(element => element.classList.contains('is-drag-near')).length === 1
            && gaps.some(element => element.getBoundingClientRect().width >= 55)
            && gaps.some(element => element.getBoundingClientRect().width <= 1);
        }"""
    )
    page.mouse.up()

    # The result is a showcase, not an editor. Rendered controls do not become
    # a second interaction model and Reset is the only board operation.
    rendered_button.click()
    assert rendered_button.evaluate("element => document.activeElement !== element")
    assert composer.locator("[data-composer-reset]").count() == 1

    axe_path = Path("node_modules/axe-core/axe.min.js").resolve()
    assert axe_path.is_file(), "run `pnpm install` before landing showcase axe tests"
    page.add_script_tag(path=str(axe_path))
    violations = composer.evaluate(
        """async root => {
          const result = await axe.run(root, { resultTypes: ['violations'] });
          return result.violations.filter(item => ['serious', 'critical'].includes(item.impact));
        }""",
    )
    assert violations == [], json.dumps(violations, indent=2)

    composer.locator("[data-composer-reset]").click()
    assert canvas.locator("[data-composer-rendered-recipe]").count() == 0
    assert canvas.locator("[data-composer-drop]").count() == 1
    page.set_viewport_size({"width": 600, "height": 900})
    assert palette.evaluate("element => element.scrollHeight <= element.clientHeight + 1")
    assert console_errors == []
    assert page_errors == []


def test_cached_restore_keeps_landing_composer_interactive(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    card = composer.locator('[data-composer-palette-drag="card"]')
    card.scroll_into_view_if_needed()
    for _ in range(2):
        start = card.bounding_box()
        assert start
        page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
        page.mouse.down()
        page.mouse.move(start["x"] + start["width"] / 2 + 12, start["y"] + start["height"] / 2 + 8)
        assert composer.get_attribute("data-composer-dragging") == "content"

        page.evaluate("""() => window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true }))""")
        assert composer.get_attribute("data-composer-dragging") is None
        assert page.locator("body > .landing-composer__drag-ghost").count() == 0
        page.mouse.up()
        page.evaluate("""() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))""")

    start = card.bounding_box()
    assert start
    page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
    page.mouse.down()
    page.mouse.move(start["x"] + start["width"] / 2 + 12, start["y"] + start["height"] / 2 + 8)
    assert composer.get_attribute("data-composer-dragging") == "content"
    page.mouse.up()

    canvas = composer.locator("[data-composer-canvas]")
    composer.locator('[data-composer-palette-drag="button"]').click()
    assert canvas.locator('[data-composer-rendered-recipe="button"]').count() == 1
    composer.locator("[data-composer-reset]").click()
    assert canvas.locator("[data-composer-rendered-recipe]").count() == 0


def test_presentation_stage_follows_theme_and_forced_colors(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    theme_styles = {}
    for theme in ("light", "dark"):
        page.evaluate("value => { document.documentElement.dataset.theme = value; }", theme)
        styles = _composer_surface_styles(composer)
        assert "gradient" in styles["stageBackgroundImage"]
        assert styles["stageBoxShadow"] != "none"
        assert styles["artboardBoxShadow"] != "none"
        assert styles["artboardBackgroundColor"] == styles["nativeCanvas"]
        assert styles["artboardColor"] == styles["nativeCanvasText"]
        theme_styles[theme] = styles

    assert theme_styles["light"]["stageBackgroundImage"] != theme_styles["dark"]["stageBackgroundImage"]
    assert theme_styles["light"]["artboardBackgroundColor"] != theme_styles["dark"]["artboardBackgroundColor"]

    page.emulate_media(forced_colors="active")
    forced = _composer_surface_styles(composer)
    assert forced["stageBackgroundImage"] == "none"
    assert forced["stageBoxShadow"] == "none"
    assert forced["artboardBoxShadow"] == "none"
    assert forced["artboardBackgroundColor"] == forced["nativeCanvas"]
    assert forced["artboardColor"] == forced["nativeCanvasText"]


def test_every_landing_recipe_arrives_as_rendered_html(page: Any, docs_site_url: str) -> None:
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    canvas = composer.locator("[data-composer-canvas]")
    reset = composer.locator("[data-composer-reset]")

    recipe_ids = composer.locator("[data-composer-palette-drag]").evaluate_all(
        "elements => elements.map(element => element.dataset.composerPaletteDrag)",
    )
    assert len(recipe_ids) == 15
    for recipe_id in recipe_ids:
        composer.locator(f'[data-composer-palette-drag="{recipe_id}"]').click()
        rendered = canvas.locator(f'[data-composer-rendered-recipe="{recipe_id}"]')
        assert rendered.count() == 1
        assert canvas.locator("[data-citry-ui-part]").count() > 0
        assert canvas.locator(".landing-composer__drop--flow").count() == 2
        assert canvas.locator("[data-composer-drop]").count() <= 4
        if recipe_id == "grid":
            assert canvas.locator("[data-composer-drop]").count() == 4
            badge = composer.locator('[data-composer-palette-drag="badge"]')
            badge.scroll_into_view_if_needed()
            start = badge.bounding_box()
            assert start
            page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
            page.mouse.down()
            page.mouse.move(start["x"] + start["width"] / 2 + 12, start["y"] + start["height"] / 2 + 8)
            assert canvas.locator("[data-composer-drop].is-drag-available").count() == 4
            page.mouse.up()
        reset.click()

    assert page_errors == []


def test_key_recipes_are_finished_compositions_not_flat_defaults(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    canvas = composer.locator("[data-composer-canvas]")
    reset = composer.locator("[data-composer-reset]")

    composer.locator('[data-composer-palette-drag="button"]').click()
    button = canvas.locator('[data-composer-rendered-recipe="button"] [data-citry-ui-part="button"]')
    assert button.get_attribute("data-size") == "lg"
    assert button.get_attribute("data-block") == ""
    button_style = button.evaluate(
        """element => ({
          radius: parseFloat(getComputedStyle(element).borderRadius),
          shadow: getComputedStyle(element).boxShadow,
        })"""
    )
    assert button_style["radius"] > 20
    assert button_style["shadow"] != "none"
    reset.click()

    composer.locator('[data-composer-palette-drag="button-group"]').click()
    button_group = canvas.locator('[data-composer-rendered-recipe="button-group"]')
    assert button_group.locator('[data-citry-ui-part="button-group"][data-grow]').count() == 1
    assert button_group.locator('[data-citry-ui-part="button"]').count() == 3
    assert button_group.locator('[data-citry-ui-part="button-group"]').evaluate(
        "element => getComputedStyle(element).boxShadow !== 'none'"
    )
    reset.click()

    composer.locator('[data-composer-palette-drag="grid"]').click()
    grid = canvas.locator('[data-composer-rendered-recipe="grid"]')
    cards = grid.locator('[data-citry-ui-part="card"]')
    assert cards.count() == 2
    assert grid.locator('[data-citry-ui-part="badge"]').count() == 2
    assert cards.evaluate_all(
        "elements => new Set(elements.map(element => getComputedStyle(element).backgroundColor)).size === 2"
    )
    reset.click()

    composer.locator('[data-composer-palette-drag="list"]').click()
    list_recipe = canvas.locator('[data-composer-rendered-recipe="list"]')
    assert list_recipe.locator('[data-citry-ui-part="list"][data-divided]').count() == 1
    assert list_recipe.locator('[data-citry-ui-part="description"]').count() == 3
    assert list_recipe.locator('[data-citry-ui-part="end"] [data-citry-ui-part="badge"]').count() == 2
    assert list_recipe.locator('[data-citry-ui-part="list"]').evaluate(
        "element => getComputedStyle(element).boxShadow !== 'none'"
    )
    reset.click()

    composer.locator('[data-composer-palette-drag="tabs"]').click()
    tabs = canvas.locator('[data-composer-rendered-recipe="tabs"]')
    assert tabs.locator('[data-citry-ui-part="tabs"][data-variant="pill"][data-grow]').count() == 1
    assert tabs.locator('[data-citry-ui-part="alert"]', has_text="A real component tree").count() == 1
    assert tabs.locator('[data-citry-ui-part="tabs"]').evaluate(
        "element => getComputedStyle(element).boxShadow !== 'none'"
    )
    reset.click()

    composer.locator('[data-composer-palette-drag="progress"]').click()
    progress = canvas.locator('[data-composer-rendered-recipe="progress"]')
    assert progress.locator('[data-citry-ui-part="card"]', has_text="Importing observations").count() == 1
    assert progress.locator('[data-citry-ui-part="badge"]', has_text="68%").count() == 1
    assert progress.locator('[data-citry-ui-part="progress"][data-size="lg"]').count() == 1


def test_nested_sequence_does_not_leak_markdown_paragraphs(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    canvas = composer.locator("[data-composer-canvas]")
    for recipe_id in ("container", "button-group", "field-input", "checkbox", "switch"):
        composer.locator(f'[data-composer-palette-drag="{recipe_id}"]').click()

    container = canvas.locator('[data-citry-ui-part="container"]')
    assert container.count() == 1
    assert container.locator('[data-composer-rendered-recipe="button-group"]').count() == 1
    assert container.locator('[data-composer-rendered-recipe="field-input"]').count() == 1
    assert container.locator('[data-composer-rendered-recipe="checkbox"]').count() == 1
    assert container.locator('[data-composer-rendered-recipe="switch"]').count() == 1
    assert canvas.locator("p").count() == 0


def test_dragging_near_board_edges_scrolls_long_compositions(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    board = composer.locator("[data-composer-board]")
    for _ in range(10):
        composer.locator('[data-composer-palette-drag="field-input"]').click()
    assert board.evaluate("element => element.scrollHeight > element.clientHeight + 200")

    composer.scroll_into_view_if_needed()
    badge = composer.locator('[data-composer-palette-drag="badge"]')
    badge.scroll_into_view_if_needed()
    start = badge.bounding_box()
    assert start
    page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
    page.mouse.down()
    page.mouse.move(start["x"] + start["width"] / 2 + 12, start["y"] + start["height"] / 2 + 8)

    box = board.bounding_box()
    assert box
    x = box["x"] + box["width"] / 2
    middle = box["y"] + box["height"] / 2
    bottom = box["y"] + box["height"]
    page.mouse.move(x, middle)
    page.wait_for_timeout(180)
    assert board.evaluate("element => element.scrollTop") == 0

    page.mouse.move(x, bottom - 70)
    page.wait_for_timeout(320)
    page.mouse.move(x, middle)
    slow_scroll = board.evaluate("element => element.scrollTop")
    assert slow_scroll > 0
    board.evaluate("element => { element.scrollTop = 0; }")

    page.mouse.move(x, bottom - 8)
    page.wait_for_timeout(320)
    page.mouse.move(x, middle)
    fast_scroll = board.evaluate("element => element.scrollTop")
    assert fast_scroll > slow_scroll * 2

    board.evaluate("element => { element.scrollTop = element.scrollHeight; }")
    maximum = board.evaluate("element => element.scrollTop")
    page.mouse.move(x, box["y"] + 8)
    page.wait_for_timeout(320)
    page.mouse.move(x, middle)
    assert board.evaluate("element => element.scrollTop") < maximum
    page.mouse.up()


def test_wheel_scroll_escapes_the_board_after_its_content_ends(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/", wait_until="networkidle")

    composer = page.locator("[data-landing-composer]")
    page.locator("[data-landing-composer][data-composer-ready]").wait_for()
    board = composer.locator("[data-composer-board]")
    for _ in range(10):
        composer.locator('[data-composer-palette-drag="field-input"]').click()
    assert board.evaluate("element => element.scrollHeight > element.clientHeight + 200")

    board.scroll_into_view_if_needed()
    board.evaluate("element => { element.scrollTop = element.scrollHeight; }")
    box = board.bounding_box()
    assert box
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page_scroll = page.evaluate("window.scrollY")
    assert page_scroll < page.evaluate("document.documentElement.scrollHeight - window.innerHeight")

    # A zoomed scroller can consume the first wheel tick while snapping a
    # fractional scrollTop to its physical-pixel boundary. Continued wheel
    # input must then chain to the page instead of trapping there.
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(100)
    page.mouse.wheel(0, 900)
    page.wait_for_function("previous => window.scrollY > previous", arg=page_scroll)
    assert board.evaluate("element => Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) <= 1")
