from __future__ import annotations

import pytest

from citry._javascript_policy import _JavascriptPolicy
from citry._output_html import OutputTemplate, scan_output_html


def _tags(template: OutputTemplate) -> list[str]:
    found: list[str] = []
    pending = [template]
    while pending:
        current = pending.pop()
        for node in current.elements:
            found.append(node.start_tag.name.content.lower())
            pending.append(node.body)
    return found


@pytest.mark.parametrize("tag", ["title", "textarea"])
def test_html_rcdata_does_not_create_script_elements(tag: str) -> None:
    template = scan_output_html(f"<{tag}><script>active()</script></{tag}>")

    assert _tags(template) == [tag]


@pytest.mark.parametrize(
    "html",
    [
        "<svg><title><script>active()</script></title></svg>",
        "<svg><desc><script>active()</script></desc></svg>",
        "<svg><foreignObject><script>active()</script></foreignObject></svg>",
        "<math><mtext><script>active()</script></mtext></math>",
        '<math><annotation-xml encoding="text/html"><script>active()</script></annotation-xml></math>',
    ],
)
def test_foreign_content_integration_points_create_html_script(html: str) -> None:
    tags = _tags(scan_output_html(html))

    assert "script" in tags


def test_settled_javascript_and_template_delimiters_are_output_data() -> None:
    source = '<main title="{{ literal }}"></main><script>if (a < b) { out = "{{still js}}" }</script>'

    assert _tags(scan_output_html(source)) == ["main", "script"]


def test_attribute_spans_are_utf8_byte_offsets() -> None:
    source = '<p title="žluťoučký" onclick="go()"></p>'
    node = scan_output_html(source).elements[0]
    onclick = node.start_tag.attrs[1]

    assert source.encode()[onclick.key.start_index : onclick.key.end_index] == b"onclick"
    assert source.encode()[onclick.inner_value.start_index : onclick.inner_value.end_index] == b"go()"  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "html",
    [
        "<svg><title><script>active()</script></title></svg>",
        "<math><mtext><script>active()</script></mtext></math>",
    ],
)
def test_javascript_policy_rejects_scripts_reached_through_integration_points(html: str) -> None:
    policy = _JavascriptPolicy("forbid")
    policy.validate_settled_html(
        html,
        marker_prefix="data-citry-trusted-",
        trusted_tag_starts=frozenset(),
        component_classes={},
    )

    with pytest.raises(ValueError, match=r"raw executable <script>"):
        policy.report()


def test_javascript_policy_treats_html_title_script_text_as_inert() -> None:
    policy = _JavascriptPolicy("forbid")
    policy.validate_settled_html(
        "<title><script>active()</script></title>",
        marker_prefix="data-citry-trusted-",
        trusted_tag_starts=frozenset(),
        component_classes={},
    )

    policy.report()
