"""Render the tabs example page and lock stable, example-specific substrings."""

import json

from docs_site._internal.examples import get_example_registry
from lxml import html as lxml_html


def _prepared_render(page_html: str) -> tuple[dict, str]:
    document = lxml_html.document_fromstring(page_html)
    # The page carries its start configuration as one JSON data block.
    [block] = document.xpath('//script[@type="application/json"][@data-citry-vue-document]')
    transport = json.loads(block.text)
    assert transport["manifest"]["protocol"] == "citry-vue-prepared/1"
    source = "\n".join(
        node.text for node in document.xpath("//script") if node.text and "function render(_ctx, _cache" in node.text
    )
    definition_ids = {item["id"] for item in transport["manifest"]["definitions"]}
    assert definition_ids
    assert all(f'window.__citryRuntimeDefinitions["{definition_id}"]' in source for definition_id in definition_ids)
    return transport, source


def test_tabs_example_page_renders() -> None:
    html = str(get_example_registry()["tabs"].page_cls())
    transport, source = _prepared_render(html)
    # Static roles and labels belong to the compiled definition; js_data()
    # sends the tab list and the open index to the browser.
    assert 'role: "tablist"' in source
    assert '"aria-label": "Example sections"' in source
    assert 'role: "tab"' in source
    assert 'role: "tabpanel"' in source
    tabs = next(item for item in transport["manifest"]["occurrences"] if item["typeKey"].startswith("Tabs_"))
    # Python seeds the browser state; Vue renders the tabs and panels from it.
    server_data = tabs["serverData"]
    assert server_data["activeIndex"] == 0
    assert server_data["idPrefix"] == f"demo-tabs-{tabs['renderId']}"
    assert [tab["label"] for tab in server_data["tabs"]] == ["Overview", "Details", "Notes"]
    # Tabs and panels are bound for assistive technology, and the shipped script
    # supports the standard horizontal-tab keyboard controls.
    assert "aria-selected" in source
    assert "aria-controls" in source
    assert "aria-labelledby" in source
    assert "ArrowRight:" in html
    assert "Home:" in html
