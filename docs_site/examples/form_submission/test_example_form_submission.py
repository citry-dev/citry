"""Render the form-submission example page and lock stable, example-specific substrings."""

import json

from docs_site._internal.examples import get_example_registry
from lxml import html as lxml_html


def _prepared_definition_source(page_html: str) -> str:
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
    return source


def test_form_submission_example_page_renders() -> None:
    html = str(get_example_registry()["form_submission"].page_cls())
    # The page's script carries the compiled Vue template, and the server
    # also renders the form for the first paint.
    source = _prepared_definition_source(html)
    assert 'placeholder: "Ada Lovelace"' in source
    assert 'class: "contact-form__button"' in source
    assert 'role: "status"' in source
    assert '"aria-live": "polite"' in source
    # Python seeds an empty message, so the first paint has no thank-you
    # box; Vue adds it only after a submit.
    document = lxml_html.document_fromstring(html)
    [status] = document.xpath('//div[@role="status"]')
    assert not status.xpath(".//*[contains(@class, 'contact-form__thanks')]")
