"""Render the tabs example page and lock stable, example-specific substrings."""

import json

from docs_site._internal.examples import get_example_registry
from lxml import html as lxml_html

from citry import citry as default_citry
from citry._vue.events import definition_bundle


def _prepared_render(page_html: str) -> tuple[dict, str]:
    document = lxml_html.document_fromstring(page_html)
    marker = "CitryStable.startPrepared("
    [bootstrap] = [node for node in document.xpath("//script") if node.text and marker in node.text]
    transport, _ = json.JSONDecoder().raw_decode(bootstrap.text[bootstrap.text.index(marker) + len(marker) :])
    assert transport["manifest"]["protocol"] == "citry-vue-prepared/1"
    definitions = transport["manifest"]["definitions"]
    bundles = []
    for asset in definitions:
        bundle = definition_bundle(default_citry, asset["sha256"])
        assert bundle is not None, asset
        bundles.append(bundle.decode())
    source = "\n".join(bundles)
    definition_ids = {item["id"] for item in definitions}
    assert definition_ids
    assert all(f'window.CitryStableDefinitions["{definition_id}"]' in source for definition_id in definition_ids)
    return transport, source


def test_tabs_example_page_renders() -> None:
    html = str(get_example_registry()["tabs"].page_cls())
    transport, source = _prepared_render(html)
    # Static roles and labels belong to the compiled definition; per-row
    # attributes and text belong to the prepared loop payload.
    assert 'role: "tablist"' in source
    assert '"aria-label": "Example sections"' in source
    assert 'role: "tab"' in source
    assert 'role: "tabpanel"' in source
    tabs = next(item for item in transport["manifest"]["occurrences"] if item["typeKey"].startswith("Tabs_"))
    tab_rows = tabs["preparedData"]["citryLoop0"]
    panel_rows = tabs["preparedData"]["citryLoop1"]
    assert tab_rows[0]["citryAttrs0"]["aria-selected"] == "true"
    assert tab_rows[0]["citryAttrs0"]["data-active"] == "true"
    assert tab_rows[0]["citryAttrs0"]["data-index"] == "0"
    assert tab_rows[0]["citryAttrs0"]["tabindex"] == "0"
    assert tab_rows[0]["citryText0"] == "Overview"
    assert panel_rows[1]["citryAttrs0"]["data-index"] == "1"
    assert panel_rows[1]["citryAttrs0"]["hidden"] is True
    assert panel_rows[1]["citryText0"] == "Clicking a tab toggles the hidden attribute on its panel, all client-side."
    # Tabs and panels are connected for assistive technology, and the shipped
    # script supports the standard horizontal-tab keyboard controls.
    assert panel_rows[0]["citryAttrs0"]["aria-labelledby"] == tab_rows[0]["citryAttrs0"]["id"]
    assert 'event.key === "ArrowRight"' in html
    assert 'event.key === "Home"' in html
