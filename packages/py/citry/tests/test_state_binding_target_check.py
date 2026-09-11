"""Static checking reports unsupported State binding targets without an app."""

import pytest

from citry._checker import _check_template, _TemplateSource


@pytest.mark.parametrize(
    "source",
    [
        "<head :c-query></head>",
        '<input type="file" :c-query>',
        '<input type="hidden" :c-query="refresh">',
        '<my-control :c-query="refresh"></my-control>',
    ],
)
def test_static_check_reports_invalid_state_targets_at_the_attribute_key(source):
    findings = _check_template(_TemplateSource(origin="card.html", content=source, consumers=[]))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.code == "citry.browser.invalid-state-binding-target"
    assert finding.severity == "error"
    assert source[finding.start_index : finding.end_index] == ":c-query"


def test_static_check_accepts_supported_and_unresolved_targets():
    source = '<input :c-query><c-element c-is="target" :c-query></c-element>'
    assert _check_template(_TemplateSource(origin="card.html", content=source, consumers=[])) == []
