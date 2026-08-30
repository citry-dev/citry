"""Cross-family browser evidence from the shared Phase 7.5 scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry_ui.quality.accessibility import AXE_INCOMPLETE_DISPOSITIONS
from citry_ui.quality.routes import build_scenario, render_scenario
from citry_ui.quality.scenarios import SCENARIOS, QualityTool

pytestmark = pytest.mark.e2e

_BROWSER_SCENARIOS = tuple(scenario for scenario in SCENARIOS if QualityTool.BROWSER in scenario.tools)


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the e2e test path."
    raise RuntimeError(msg)


def _axe_findings(
    page: Any,
    *,
    test_embedded_frames: bool = True,
) -> dict[str, list[dict[str, object]]]:
    result = page.evaluate(
        """async testEmbeddedFrames => {
          const options = {
            resultTypes: ['violations', 'incomplete'],
          };
          if (!testEmbeddedFrames) {
            options.rules = {'frame-tested': {enabled: false}};
          }
          const result = await axe.run(document, options);
          return {
            violations: result.violations.filter(
              (finding) => finding.impact === 'serious' || finding.impact === 'critical',
            ),
            incomplete: result.incomplete.map((finding) => ({
              id: finding.id,
              impact: finding.impact,
              nodes: finding.nodes.length,
            })),
          };
        }""",
        test_embedded_frames,
    )
    return result


def _with_external_css(html: str, css: str, *, after_citry: bool) -> str:
    stylesheet = f'<style data-quality-external-css="">{css}</style>'
    if after_citry:
        return html.replace("</head>", stylesheet + "</head>", 1)
    first_citry_style = html.find('<style data-citry-css-class="')
    if first_citry_style < 0:
        msg = "Rendered scenario did not contain a Citry stylesheet."
        raise RuntimeError(msg)
    return html[:first_citry_style] + stylesheet + html[first_citry_style:]


def _install_image_scenario_routes(page: Any) -> None:
    valid = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">'
        '<rect width="1280" height="720" fill="#334155"/></svg>'
    )

    def serve(route: Any) -> None:
        url = route.request.url
        if "missing" in url or "blocked-images" in url:
            route.fulfill(status=200, content_type="image/png", body=b"not-an-image")
            return
        route.fulfill(
            status=200,
            content_type="image/svg+xml",
            body=valid,
            headers={"access-control-allow-origin": "*"},
        )

    page.route("https://images.citry.test/**", serve)
    page.route("https://cross-origin.citry.test/**", serve)
    page.route("https://blocked-images.citry.test/**", serve)


def _activate_representative_state(page: Any, scenario_id: str) -> None:
    if scenario_id == "accordion.states":
        page.get_by_role("button", name="Understory").click()
        return
    if scenario_id == "disclosure.states":
        page.get_by_role("button", name="System requirements").click()
        return
    if scenario_id == "alert.states":
        page.get_by_role("button", name="Mark synchronized").click()
        return
    if scenario_id == "button.states":
        page.get_by_role("button", name="Client-controlled loading").click()
        return
    if scenario_id == "split-button.states":
        page.get_by_role("button", name="Save accession").click()
        return
    if scenario_id == "tags-input.states":
        page.locator('[data-quality-states~="draft"] [data-citry-ui-part="input"]').fill("quality draft")
        return
    if scenario_id == "image.states":
        page.get_by_role("button", name="Broken", exact=True).click()
        page.wait_for_function("document.querySelector('#quality-image-reactive').dataset.status === 'error'")
        return
    if scenario_id == "field-input.states":
        page.get_by_role("textbox", name="Controlled species note").fill("x")
        return
    if scenario_id == "progress.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "spinner.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "radio.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "switch.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "form.states":
        page.get_by_role("button", name="Submit", exact=True).click()
        return
    if scenario_id == "textarea.states":
        page.get_by_role("button", name="Release controlled value").click()
        page.get_by_role("button", name="Reset journal").click()
        return
    if scenario_id == "native-select.states":
        page.get_by_role("button", name="Release controlled value").click()
        page.get_by_role("button", name="Reset survey").click()
        return
    if scenario_id == "checkbox.states":
        page.get_by_role("button", name="Release controlled state").click()
        page.get_by_role("button", name="Reset checklist").click()
        return
    if scenario_id == "tabs.overview":
        page.get_by_role("tab", name="Notifications").click()
        return
    if scenario_id == "dialog.states":
        page.get_by_role("button", name="Open observatory log").click()
        page.wait_for_function("document.querySelector('#quality-dialog').open")
        return
    if scenario_id == "alert-dialog.states":
        page.get_by_role("button", name="Delete project").click()
        page.wait_for_function("document.querySelector('#quality-delete-project').open")
        return
    if scenario_id == "popover.states":
        page.get_by_role("button", name="Inspect Europa").click()
        page.wait_for_function("document.querySelector('#quality-popover').matches(':popover-open')")
        page.locator("#quality-popover").evaluate(
            "element => Promise.all(element.getAnimations({subtree: true}).map(animation => animation.finished))"
        )
        return
    if scenario_id == "drawer.states":
        page.get_by_role("button", name="Edit observatory note").click()
        page.wait_for_function("document.querySelector('#quality-drawer').matches(':modal')")
        return
    if scenario_id == "tooltip.states":
        page.get_by_role("button", name="Europa").focus()
        page.wait_for_function("document.querySelector('#quality-tooltip').matches(':popover-open')")
        page.locator("#quality-tooltip").evaluate(
            "element => Promise.all(element.getAnimations({subtree: true}).map(animation => animation.finished))"
        )
        return
    if scenario_id == "menu.states":
        page.get_by_role("button", name="Open archive index").click()
        page.wait_for_function("document.querySelector('#quality-menu').matches(':popover-open')")
        return
    if scenario_id == "context-menu.states":
        page.locator("#quality-context-menu-basic-target").click(
            button="right",
            position={"x": 24, "y": 24},
        )
        page.wait_for_function("document.querySelector('#quality-context-menu-basic-menu').matches(':popover-open')")
        return
    if scenario_id == "navigation-menu.states":
        page.get_by_role("button", name="المزيد").click()
        page.wait_for_function(
            "document.querySelector('[data-value=rtl-more][data-citry-navigation-menu-trigger]')"
            ".getAttribute('aria-expanded') === 'true'"
        )
        return
    if scenario_id == "carousel.states":
        carousel = page.get_by_role("region", name="Featured stories")
        carousel.get_by_role("button", name="Next slide").click()
        page.wait_for_function("document.querySelector('[aria-label=\"Featured stories\"]').dataset.index === '1'")
        return
    if scenario_id == "toast.states":
        page.get_by_role("button", name="Add notification").click()
        page.get_by_role("button", name="Retry").click()
        return
    if scenario_id == "combobox.states":
        page.get_by_role("combobox", name="Remote catalog").fill("Vega")
        page.wait_for_timeout(50)
        return
    if scenario_id == "select.states":
        trigger = page.locator('.cui-select [role="combobox"]').first
        trigger.click()
        page.wait_for_function("document.querySelector('.cui-select [role=combobox]').ariaExpanded === 'true'")
        page.wait_for_timeout(200)
        return
    if scenario_id == "multi-select.states":
        trigger = page.locator('.cui-multi-select [role="combobox"]').first
        trigger.click()
        page.wait_for_function("document.querySelector('.cui-multi-select [role=combobox]').ariaExpanded === 'true'")
        page.wait_for_timeout(200)
        return
    if scenario_id == "toggle.states":
        page.get_by_role("button", name="Standalone pressed").click()
        return
    if scenario_id == "pagination.states":
        page.locator('[data-citry-ui-part="pagination"]').nth(1).get_by_role("button", name="Next page").click()
        return
    if scenario_id == "slider.states":
        page.locator('[data-quality-states~="single"] [role="slider"]').press("ArrowRight")
        return
    if scenario_id == "rating.states":
        page.locator('[data-quality-states~="required"] input[value="3"]').click(force=True)
        return
    if scenario_id == "pin-input.states":
        page.get_by_role("textbox", name="Required verification code").fill("012345")
        return
    if scenario_id == "date-input.states":
        page.get_by_label("Required arrival date").fill("2026-08-21")
        return
    if scenario_id == "date-picker.states":
        page.get_by_role("button", name="Change date").first.click()
        page.wait_for_function("document.querySelector('.cui-date-picker__popover').matches(':popover-open')")
        page.wait_for_timeout(200)
        return
    if scenario_id == "date-range.states":
        page.get_by_role("button", name="Change date range").first.click()
        page.wait_for_function("document.querySelector('.cui-date-range__popover').matches(':popover-open')")
        page.wait_for_timeout(200)
        return
    if scenario_id == "time.states":
        page.get_by_role("button", name="Change time").first.click()
        page.wait_for_function("document.querySelector('.cui-time-picker__popover').matches(':popover-open')")
        page.wait_for_timeout(200)
        return
    if scenario_id == "workflow.repeatable-contacts":
        page.get_by_role("button", name="Add contact").click()
        return
    if scenario_id == "composition.orbit-access":
        page.get_by_role("textbox", name="Full name").fill("Lin Chen")
        return
    if scenario_id == "composition.ledger-dashboard":
        page.get_by_role("button", name="Create report").click()
        page.wait_for_function("document.querySelector('#ledger-report-dialog').open")


@pytest.mark.parametrize("scenario", _BROWSER_SCENARIOS, ids=lambda scenario: scenario.id)
def test_shared_scenario_semantics_and_active_state_have_no_high_impact_axe_findings(
    page: Any,
    scenario: Any,
) -> None:
    console_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    if scenario.id == "image.states":
        _install_image_scenario_routes(page)
    page.set_content(render_scenario(scenario.id), wait_until="load")
    page.wait_for_selector(scenario.ready_selector, state="attached")
    if scenario.id == "textarea.states":
        assert page.locator(".cui-textarea").count() == 13
        assert page.locator(".cui-textarea[data-citry-textarea-initialized]").count() == 13
    if scenario.id == "native-select.states":
        assert page.locator(".cui-native-select").count() == 11
        assert page.locator(".cui-native-select[data-citry-native-select-initialized]").count() == 11
    if scenario.id == "checkbox.states":
        assert page.locator(".cui-checkbox").count() == 12
        assert page.locator(".cui-checkbox[data-citry-checkbox-initialized]").count() == 12
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    page.add_script_tag(path=str(axe_path))
    embedded_findings = []
    if len(page.frames) > 1:
        assert page.locator("iframe").evaluate_all("frames => frames.every(frame => Boolean(frame.title.trim()))")
    for child_frame in page.frames[1:]:
        child_frame.add_script_tag(path=str(axe_path))
        embedded_findings.append(_axe_findings(child_frame))
    for findings in embedded_findings:
        assert findings["violations"] == []

    # Child documents are checked directly. Disable only axe's redundant
    # frame-tested rule so every other rule still evaluates the iframe element.
    initial = _axe_findings(page, test_embedded_frames=not embedded_findings)
    assert initial["violations"] == []

    _activate_representative_state(page, scenario.id)
    active = _axe_findings(page, test_embedded_frames=not embedded_findings)
    assert active["violations"] == []
    if scenario.id in {
        "accordion.states",
        "disclosure.states",
        "alert.states",
        "split-button.states",
        "tags-input.states",
        "image.states",
        "alert-dialog.states",
        "textarea.states",
        "native-select.states",
        "checkbox.states",
        "toggle.states",
        "pagination.states",
        "menu.states",
        "context-menu.states",
        "navigation-menu.states",
        "carousel.states",
        "drawer.states",
        "toast.states",
    }:
        assert console_errors == []
    incomplete_groups = [initial["incomplete"], active["incomplete"]]
    incomplete_groups.extend(findings["incomplete"] for findings in embedded_findings)
    incomplete_rules = {finding["id"] for group in incomplete_groups for finding in group}
    assert incomplete_rules <= AXE_INCOMPLETE_DISPOSITIONS.keys()

    # The compact record makes axe's manual-review surface visible in test
    # output without pretending automation can resolve it.
    page.evaluate(
        "findings => { window.__citryUiAxeIncomplete = findings; }",
        {"initial": initial["incomplete"], "active": active["incomplete"]},
    )


def test_accordion_quality_form_continuity_and_brand_contrast(page: Any) -> None:
    page.set_content(render_scenario("accordion.states"), wait_until="load")
    page.wait_for_selector('[data-quality-states~="brand-fern"][data-citry-accordion-initialized]')
    form = page.locator("#accordion-quality-form")
    control = form.locator('[name="ridge-note"]')
    assert form.locator('[data-value="upland"] button').get_attribute("aria-expanded") == "false"
    assert page.evaluate("Array.from(new FormData(document.querySelector('#accordion-quality-form')).entries())") == [
        ["ridge-note", "Dry trail"]
    ]
    control.evaluate("element => element.value = 'Changed trail'")
    form.evaluate("element => element.reset()")
    assert control.input_value() == "Dry trail"

    contrast_script = """() => {
      const channels = (value) => {
        const numbers = value.match(/[0-9.]+/g).map(Number);
        return value.startsWith('color(srgb')
          ? numbers.slice(0, 3)
          : numbers.slice(0, 3).map((channel) => channel / 255);
      };
      const luminance = (value) => channels(value)
        .map((channel) => channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4)
        .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
      return ['brand-fern', 'brand-river'].map((brand) => {
        const root = document.querySelector(`[data-quality-states~="${brand}"]`);
        const trigger = root.querySelector('[data-citry-accordion-trigger]');
        const foreground = luminance(getComputedStyle(trigger).color);
        const background = luminance(getComputedStyle(root).backgroundColor);
        return (Math.max(foreground, background) + 0.05)
          / (Math.min(foreground, background) + 0.05);
      });
    }"""
    for color_scheme in ("light", "dark"):
        page.emulate_media(color_scheme=color_scheme)
        assert all(ratio >= 4.5 for ratio in page.evaluate(contrast_script))


def test_disclosure_quality_form_continuity_and_brand_contrast(page: Any) -> None:
    page.set_content(render_scenario("disclosure.states"), wait_until="load")
    page.wait_for_selector('[data-quality-states~="brand-orchard"][data-citry-disclosure-initialized]')
    form = page.locator("#disclosure-quality-form")
    control = form.locator('[name="email"]')
    trigger = form.get_by_role("button", name="Notification settings")
    control.fill("changed@example.com")
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("Array.from(new FormData(document.querySelector('#disclosure-quality-form')).entries())") == [
        ["email", "changed@example.com"]
    ]
    trigger.click()
    assert control.input_value() == "changed@example.com"
    form.evaluate("element => element.reset()")
    assert control.input_value() == "ops@example.com"

    contrast_script = """() => {
      const rgba = (value) => {
        const numbers = value.match(/[0-9.]+/g).map(Number);
        const channels = value.startsWith('color(srgb')
          ? numbers.slice(0, 3)
          : numbers.slice(0, 3).map((channel) => channel / 255);
        return [...channels, numbers[3] ?? 1];
      };
      const composite = (front, back) => [
        ...front.slice(0, 3).map(
          (channel, index) => channel * front[3] + back[index] * (1 - front[3]),
        ),
        1,
      ];
      const luminance = (value) => value.slice(0, 3)
        .map((channel) => channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4)
        .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
      return ['brand-orchard', 'brand-harbor'].map((brand) => {
        const root = document.querySelector(`[data-quality-states~="${brand}"]`);
        const trigger = root.querySelector('[data-citry-ui-part="disclosure-trigger"]');
        const triggerStyle = getComputedStyle(trigger);
        const rootBackground = rgba(getComputedStyle(root).backgroundColor);
        const triggerBackground = composite(rgba(triggerStyle.backgroundColor), rootBackground);
        const foreground = luminance(composite(rgba(triggerStyle.color), triggerBackground));
        const background = luminance(triggerBackground);
        return (Math.max(foreground, background) + 0.05)
          / (Math.min(foreground, background) + 0.05);
      });
    }"""
    for color_scheme in ("light", "dark"):
        page.emulate_media(color_scheme=color_scheme)
        assert all(ratio >= 4.5 for ratio in page.evaluate(contrast_script))


def test_split_button_quality_form_state_and_lifecycle(page: Any, serve_citry_ui_live: Any) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    rendered = build_scenario(
        "split-button.states",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    base_url = serve_citry_ui_live(rendered.app, rendered.html)
    scenario_component = rendered.app.get("CitryUiSplitButtonStates")
    morph_fragments = [
        scenario_component(include_lifecycle=False).render().serialize(deps_strategy="fragment"),
        *(scenario_component().render().serialize(deps_strategy="fragment") for _ in range(3)),
    ]
    page.goto(base_url + "/", wait_until="load")
    page.wait_for_selector(
        '[data-citry-ui-part="split-button"][data-citry-split-button-initialized]',
        state="attached",
    )
    page.wait_for_function(
        """() => document.querySelectorAll('[data-citry-ui-part="split-button"]').length
          === document.querySelectorAll(
            '[data-citry-ui-part="split-button"][data-citry-split-button-initialized]',
          ).length"""
    )
    expected_roots = page.locator('[data-citry-ui-part="split-button"]').count()
    expected_layers = page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length")

    submit_root = page.locator("#quality-split-submit")
    primary = submit_root.get_by_role("button", name="Save accession")
    primary.click()
    assert page.locator("#split-button-quality-log").text_content().startswith("Submits: 1;")
    assert page.evaluate(
        """() => Array.from(new FormData(
          document.querySelector('#split-button-quality-form'),
          document.querySelector('#quality-split-submit-primary'),
        ).entries())"""
    ) == [["accession", "G-104"], ["action", "save"]]

    page.get_by_role("button", name="Reset accession").click()
    assert "resets: 1" in page.locator("#split-button-quality-log").text_content()

    loading_root = page.locator('[data-quality-states~="loading-start"]')
    loading_primary = loading_root.get_by_role("button", name="Save image")
    assert loading_primary.get_attribute("aria-busy") == "true"
    assert loading_primary.evaluate("element => element.matches(':disabled')") is False
    loading_primary.evaluate("element => element.focus()")
    assert loading_primary.evaluate("element => element === document.activeElement") is True
    loading_root.get_by_role("button", name="More loading image actions").click()
    assert loading_root.locator('[data-citry-ui-part="menu"]').evaluate("element => element.matches(':popover-open')")

    controlled = page.locator('[data-quality-states~="controlled"]')
    controlled_trigger = controlled.get_by_role("button", name="More controlled publication actions")
    before = controlled_trigger.get_attribute("aria-expanded")
    page.get_by_role("button", name="Toggle controlled Menu").click()
    assert controlled_trigger.get_attribute("aria-expanded") != before

    lifecycle = page.locator('[data-quality-states~="lifecycle"]')
    assert lifecycle.count() == 1

    morph_snapshots = page.evaluate(
        r"""async (fragments) => {
          const internal = Citry.events._internal;
          const root = document.querySelector('.split-button-quality');
          const componentId = root.getAttribute('data-cid').trim().split(/\s+/).at(-1);
          const anchor = internal.getAnchor(componentId);
          const snapshots = [];
          for (const html of fragments) {
            const epoch = anchor.epoch + 1;
            anchor.epoch = epoch;
            await internal.applyResult(
              {
                ok: true,
                epoch,
                actions: [{
                  action: 'render',
                  target: 'render:' + anchor.componentId,
                  swap: 'morph',
                  html,
                }],
              },
              {anchor, instance: anchor.componentId, event: 'split-button-quality-morph'},
            );
            await new Promise((resolve) => requestAnimationFrame(
              () => requestAnimationFrame(resolve),
            ));
            await new Promise((resolve) => setTimeout(resolve, 200));
            const roots = document.querySelectorAll('[data-citry-ui-part="split-button"]');
            snapshots.push({
              roots: roots.length,
              ready: document.querySelectorAll(
                '[data-citry-ui-part="split-button"][data-citry-split-button-initialized]',
              ).length,
              lifecycle: document.querySelectorAll('[data-quality-states~="lifecycle"]').length,
              layers: globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length,
              submit: {
                ...globalThis[Symbol.for('citry-ui:split-button-submit-runtime')].stats,
              },
            });
          }
          return snapshots;
        }""",
        morph_fragments,
    )
    assert len(morph_snapshots) == 4
    removed, *restored = morph_snapshots
    assert removed["roots"] == expected_roots - 1
    assert removed["lifecycle"] == 0
    assert restored[0] == restored[1] == restored[2]
    assert restored[0]["roots"] == expected_roots
    assert restored[0]["lifecycle"] == 1
    for snapshot in morph_snapshots:
        assert snapshot["ready"] == snapshot["roots"]
        assert snapshot["layers"] == expected_layers
        assert snapshot["submit"] == {"scopes": 1, "registrations": 1}
    assert console_errors == []
    assert page_errors == []


def test_tags_input_quality_form_tokenization_focus_and_morph(page: Any, serve_citry_ui_live: Any) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    rendered = build_scenario(
        "tags-input.states",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    base_url = serve_citry_ui_live(rendered.app, rendered.html)

    page.goto(base_url + "/", wait_until="load")
    page.wait_for_function(
        """() => document.querySelectorAll('[data-citry-ui-part="tags-input"]').length
          === document.querySelectorAll(
            '[data-citry-ui-part="tags-input"][data-citry-tags-input-initialized]',
          ).length"""
    )
    expected_roots = page.locator('[data-citry-ui-part="tags-input"]').count()

    form = page.locator("#tags-input-quality-form")
    required_root = page.locator('[data-quality-states~="form-data"]')
    required_editor = required_root.locator('[data-citry-ui-part="input"]')
    assert page.evaluate(
        "() => new FormData(document.querySelector('#tags-input-quality-form')).getAll('labels')"
    ) == ["alpine", "ordered"]
    required_editor.fill("new-label")
    required_editor.press("Enter")
    assert page.evaluate(
        "() => new FormData(document.querySelector('#tags-input-quality-form')).getAll('labels')"
    ) == ["alpine", "ordered", "new-label"]
    form.evaluate("element => element.reset()")
    page.wait_for_function(
        """() => [...document.querySelector(
          '[data-quality-states~="form-data"] [data-citry-tags-input-native]',
        ).selectedOptions].map(option => option.value).join() === 'alpine,ordered'"""
    )
    assert page.evaluate(
        "() => new FormData(document.querySelector('#tags-input-quality-form')).getAll('readonly-labels')"
    ) == ["readonly-one", "readonly-two"]
    assert page.evaluate(
        "() => new FormData(document.querySelector('#tags-input-quality-form')).getAll('external-labels')"
    ) == ["external-one", "external-two"]
    assert (
        page.evaluate(
            "() => new FormData(document.querySelector('#tags-input-quality-form')).getAll('disabled-labels')"
        )
        == []
    )

    paste_root = page.locator('[data-quality-states~="paste"]')
    paste_editor = paste_root.locator('[data-citry-ui-part="input"]')
    paste_editor.evaluate(
        """input => {
          input.setSelectionRange(0,input.value.length);
          const event=new Event('paste',{bubbles:true,cancelable:true});
          Object.defineProperty(event,'clipboardData',{value:{getData:()=> 'fresh,trail'}});
          input.dispatchEvent(event);
        }"""
    )
    assert paste_root.locator("option:checked").evaluate_all("options => options.map(option => option.value)") == [
        "paste-base",
        "fresh",
    ]
    assert paste_editor.input_value() == "trail"
    paste_editor.evaluate(
        """input => {
          input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));
          input.value='ime,';
          input.dispatchEvent(new InputEvent('input',{bubbles:true,data:'ime,',isComposing:true}));
          input.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:'ime,'}));
          input.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:false}));
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector(
          '[data-quality-states~="paste"] [data-citry-tags-input-native]',
        ).selectedOptions.length === 3"""
    )
    assert paste_editor.input_value() == ""

    controlled = page.locator('[data-quality-states~="controlled-value"]')
    controlled_editor = controlled.locator('[data-citry-ui-part="input"]')
    controlled_editor.press("Enter")
    assert controlled.locator("option:checked").count() == 1
    assert controlled_editor.input_value() == "owner draft"
    page.get_by_role("checkbox", name="Accept controlled value requests").check()
    controlled_editor.press("Enter")
    page.wait_for_function(
        """() => document.querySelector(
          '[data-quality-states~="controlled-value"] [data-citry-tags-input-native]',
        ).selectedOptions.length === 2"""
    )
    assert controlled_editor.input_value() == ""

    invalid_root = page.locator('[data-quality-states~="invalid-focus"]')
    invalid_editor = invalid_root.locator('[data-citry-ui-part="input"]')
    invalid_root.locator("[data-citry-tags-input-native]").evaluate("element => element.reportValidity()")
    page.wait_for_function(
        """() => document.activeElement === document.querySelector(
          '[data-quality-states~="invalid-focus"] [data-citry-ui-part="input"]',
        )"""
    )
    assert invalid_root.get_attribute("data-invalid") == ""
    assert invalid_editor.evaluate("element => element === document.activeElement") is True

    lifecycle = page.locator('[data-quality-states~="lifecycle"]')
    lifecycle_editor = lifecycle.locator('[data-citry-ui-part="input"]')
    lifecycle_editor.fill("typed draft")
    lifecycle_editor.focus()
    lifecycle_editor.evaluate(
        """input => {
          input.setSelectionRange(2,5);
          input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));
          window.__tagsInputCompositionEditor=input;
        }"""
    )
    morph_snapshots = []
    for step in range(1, 6):
        page.evaluate(
            """() => {
              void Citry.events.send(
                document.querySelector('.tags-input-quality'),
                'refresh',
                {},
              );
            }"""
        )
        page.wait_for_function(
            "step => Number(document.querySelector('[data-quality-morph-step]').textContent) === step",
            arg=step,
            timeout=10_000,
        )
        expected_step_roots = expected_roots - 1 if step in {2, 4} else expected_roots
        page.wait_for_function(
            r"""expected => {
              const roots=document.querySelectorAll('[data-citry-ui-part="tags-input"]').length;
              const ready=document.querySelectorAll(
                '[data-citry-ui-part="tags-input"][data-citry-tags-input-initialized]',
              ).length;
              const registry=document[Symbol.for('citry-ui:form-control-reset-registry')];
              return roots===expected && ready===expected && registry?.entries.size===expected;
            }""",
            arg=expected_step_roots,
            timeout=10_000,
        )
        page.evaluate("() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
        page.wait_for_timeout(50)
        snapshot = page.evaluate(
            r"""() => {
              const editor=document.querySelector('#tags-input-quality-lifecycle');
              const roots=document.querySelectorAll('[data-citry-ui-part="tags-input"]');
              const registry=document[Symbol.for('citry-ui:form-control-reset-registry')];
              const snapshot={
                roots:roots.length,
                ready:document.querySelectorAll(
                  '[data-citry-ui-part="tags-input"][data-citry-tags-input-initialized]',
                ).length,
                lifecycle:document.querySelectorAll('[data-quality-states~="lifecycle"]').length,
                registrations:registry?.entries.size??0,
                sameNode:editor===window.__tagsInputCompositionEditor,
                draft:editor?.value??null,
                selection:[editor?.selectionStart??null,editor?.selectionEnd??null],
              };
              if (editor===window.__tagsInputCompositionEditor) {
                editor.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true}));
              }
              return snapshot;
            }"""
        )
        morph_snapshots.append(snapshot)
    same, first_removed, first_restored, second_removed, second_restored = morph_snapshots
    assert same["sameNode"] is True
    assert same["draft"] == "typed draft"
    assert same["selection"] == [2, 5]
    for removed in (first_removed, second_removed):
        assert removed["roots"] == expected_roots - 1
        assert removed["lifecycle"] == 0
    assert first_restored == second_restored
    assert first_restored["roots"] == expected_roots
    assert first_restored["lifecycle"] == 1
    for snapshot in morph_snapshots:
        assert snapshot["ready"] == snapshot["roots"]
        assert snapshot["registrations"] == snapshot["roots"]
    assert console_errors == []
    assert page_errors == []


def test_menu_quality_form_safety_native_disabledness_and_brand_contrast(page: Any) -> None:
    page.set_content(render_scenario("menu.states"), wait_until="load")
    page.wait_for_selector("#quality-menu[data-citry-menu-initialized]", state="attached")

    page.get_by_role("button", name="Open archive index").click()
    page.get_by_role("menuitem", name="Copy citation").click()
    assert page.locator("#quality-menu").evaluate("element => element.matches(':popover-open')")
    assert page.locator("form output").text_content() == "Submits: 0"
    assert page.evaluate("Array.from(new FormData(document.querySelector('.menu-quality form')).entries())") == []

    disabled_trigger = page.get_by_role("button", name="Desk commands")
    assert disabled_trigger.evaluate("element => element.matches(':disabled')") is True
    disabled_trigger.evaluate("element => element.click()")
    assert page.locator("#quality-disabled-menu").evaluate("element => element.matches(':popover-open')") is False

    contrast_script = """() => {
      const channels = (value) => value.match(/[0-9.]+/g).slice(0, 3).map(Number)
        .map((channel) => channel / 255);
      const luminance = (value) => channels(value)
        .map((channel) => channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4)
        .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
      return ['brand-moon', 'brand-ember'].map((brand) => {
        const surface = document.querySelector(`[data-quality-states~="${brand}"]`);
        const foreground = luminance(getComputedStyle(surface).color);
        const background = luminance(getComputedStyle(surface).backgroundColor);
        return (Math.max(foreground, background) + 0.05)
          / (Math.min(foreground, background) + 0.05);
      });
    }"""
    for color_scheme in ("light", "dark"):
        page.emulate_media(color_scheme=color_scheme)
        assert all(ratio >= 4.5 for ratio in page.evaluate(contrast_script))


@pytest.mark.parametrize("scenario_id", ["composition.orbit-access", "composition.ledger-dashboard"])
@pytest.mark.parametrize("framework", ["bootstrap", "tailwind"])
@pytest.mark.parametrize("after_citry", [False, True], ids=("framework-first", "framework-last"))
def test_representative_compositions_coexist_with_pinned_framework_css(
    page: Any,
    scenario_id: str,
    framework: str,
    after_citry: bool,
) -> None:
    root = _repository_root()
    css_path = (
        root / "node_modules" / "bootstrap" / "dist" / "css" / "bootstrap.min.css"
        if framework == "bootstrap"
        else root / "packages" / "py" / "citry_ui" / "citry_ui" / "quality" / "css" / ".generated" / "tailwind.css"
    )
    assert css_path.is_file(), "run `pnpm install` and `pnpm run citry-ui:quality-css` first"
    html = _with_external_css(
        render_scenario(scenario_id),
        css_path.read_text(encoding="utf-8"),
        after_citry=after_citry,
    )
    scenario = next(scenario for scenario in SCENARIOS if scenario.id == scenario_id)
    page.set_content(html, wait_until="load")
    page.wait_for_selector(scenario.ready_selector)

    if scenario_id == "composition.orbit-access":
        control = page.get_by_role("button", name="Request access")
        assert page.get_by_role("textbox", name="Full name").is_visible()
    else:
        control = page.get_by_role("tab", name="Overview")
        assert page.get_by_role("table", name="Active delivery work").is_visible()

    assert control.is_visible()
    assert control.evaluate("element => element.getBoundingClientRect().height >= 24") is True
    assert control.evaluate("element => getComputedStyle(element).boxSizing") == "border-box"
