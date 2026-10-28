"""
Exact reports of the strict-CSP and JavaScript-policy output checks.

Each test pins one validator's whole message for a small page: which
component a finding names, the byte range it points at, the order of the
findings, and whether the validator warns or raises. The rules themselves
run in Rust (`citry/_output_policy.py`).
"""

from __future__ import annotations

import os
import re
import warnings

import pytest

from citry import Citry, Component, _output_html, _output_policy
from citry._csp_validation import _CspRenderValidator
from citry._javascript_policy import _JavascriptPolicy

COMPONENTS = {"c1": "Card"}

# These tests break the Python tag reader or the Rust call on purpose, so
# the opt-in comparison with the frozen Python rules would report that
# break as a difference.
breaks_one_side = pytest.mark.skipif(
    os.environ.get(_output_policy.DIFFERENTIAL_ENVIRONMENT_VARIABLE) == "1",
    reason="the test breaks one side of the comparison on purpose",
)


def _lines(lines: list[str]) -> str:
    return "\n".join(lines)


def _warning(validator: _CspRenderValidator | _JavascriptPolicy) -> str:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validator.report()
    assert [warning.category for warning in caught] == [RuntimeWarning]
    return str(caught[0].message)


def test_strict_csp_reports_handlers_urls_and_raw_elements_in_page_order() -> None:
    validator = _CspRenderValidator("strict")
    validator.validate_settled_html(
        '<main data-cid-c1 onclick="go()"><a href="java&#x73;cript:x">a</a><style>p{}</style></main>',
        marker_prefix="data-t",
        trusted_tag_starts=frozenset(),
        component_classes=COMPONENTS,
    )
    with pytest.raises(ValueError, match=r"^Citry found") as raised:
        validator.report()
    # The `<main>` carries `data-cid-c1`, so every finding on it or inside
    # it names that component.
    assert str(raised.value) == _lines(
        [
            "Citry found 3 strict-CSP incompatibility issue(s):",
            "- Card, attribute 'onclick', settled HTML bytes 18:25: the native inline event attribute 'onclick'; "
            "use a Vue handler or Component.js",
            "- Card, attribute 'href', settled HTML bytes 42:59: a javascript: URL in 'href'; "
            "use a normal URL or a Vue handler",
            "- Card, settled HTML bytes 67:72: a raw <style> element; use Component.css or a "
            "structured Style dependency",
        ]
    )


def test_csp_warning_reports_a_raw_element_once_across_both_checks() -> None:
    validator = _CspRenderValidator("warn")
    validator.validate_pre_extension_html("<p><script>a()</script></p>", component_classes={})
    # The settled page's first script matches the one remembered before the
    # hooks ran, so only the second is reported again.
    validator.validate_settled_html(
        "<p><script>a()</script></p><script>a()</script>",
        marker_prefix="data-t",
        trusted_tag_starts=frozenset(),
        component_classes={},
    )
    validator.add_dependency_findings(("an opaque dependency",))
    assert _warning(validator) == _lines(
        [
            "Citry found 3 strict-CSP incompatibility issue(s):",
            "- settled render output, pre-extension HTML bytes 4:10: a raw <script> element; use Component.js or "
            "a structured Script dependency",
            "- settled render output, settled HTML bytes 28:34: a raw <script> element; use Component.js or a "
            "structured Script dependency",
            "- dependency emission: an opaque dependency",
        ]
    )


@pytest.mark.parametrize("mode", ["warn", "strict"])
def test_csp_reports_a_page_it_cannot_read(mode: str) -> None:
    validator = _CspRenderValidator(mode)
    validator.validate_settled_html(
        "<a>\ud800</a>", marker_prefix="data-t", trusted_tag_starts=frozenset(), component_classes={}
    )
    message = _lines(
        [
            "Citry found 1 strict-CSP incompatibility issue(s):",
            "- settled render output: the settled HTML could not be parsed for CSP validation ('utf-8' codec "
            "can't encode character '\\ud800' in position 3: surrogates not allowed)",
        ]
    )
    if mode == "warn":
        assert _warning(validator) == message
        return
    with pytest.raises(ValueError, match=r"^Citry found") as raised:
        validator.report()
    assert str(raised.value) == message


def test_forbid_reports_every_settled_rule_in_page_order() -> None:
    policy = _JavascriptPolicy("forbid")
    policy.validate_settled_html(
        '<div data-cid-c1 @click="go" onclick="x"><a href="javascript:x">a</a>'
        '<iframe srcdoc="&lt;script&gt;"></iframe><script>run()</script>'
        '<script type="application/json" data-citry>{}</script></div>',
        marker_prefix="data-t",
        trusted_tag_starts=frozenset(),
        component_classes=COMPONENTS,
    )
    with pytest.raises(ValueError, match=r"^security_javascript=") as raised:
        policy.report()
    assert str(raised.value) == _lines(
        [
            "security_javascript='forbid' found 6 client behavior requirement(s):",
            "- Card, attribute '@click', settled HTML bytes 17:23: the browser activation attribute '@click' "
            "requires JavaScript",
            "- Card, attribute 'onclick', settled HTML bytes 29:36: the native inline event attribute 'onclick' "
            "remains executable browser code",
            "- Card, attribute 'href', settled HTML bytes 50:62: a javascript: URL in 'href' "
            "remains executable browser code",
            "- Card, attribute 'srcdoc', settled HTML bytes 85:99: 'srcdoc' contains an embedded "
            "HTML document with executable browser code",
            "- Card, dependency bytes 111:117: a raw executable <script> remains outside Citry's dependency policy",
            "- Card, dependency bytes 133:139: a raw Citry browser manifest requires the client manager",
        ]
    )


def test_omit_removes_its_markers_and_reports_unusable_fallbacks() -> None:
    policy = _JavascriptPolicy("omit")
    cleaned = policy.validate_settled_html(
        '<div data-cid-c1 data-citry-omit-handler-ab v-if="x">a</div><button @click="go">b</button>',
        marker_prefix="data-t",
        trusted_tag_starts=frozenset(),
        component_classes=COMPONENTS,
        omit_handler_marker="data-citry-omit-handler-ab",
    )
    assert cleaned == '<div data-cid-c1 v-if="x">a</div><button @click="go">b</button>'
    assert _warning(policy) == _lines(
        [
            "security_javascript='omit' found 3 client behavior requirement(s):",
            "- Card, attribute 'v-if', settled HTML bytes 44:48: 'v-if' is inert after Citry-managed JavaScript "
            "is omitted and may leave an unusable static fallback",
            "- Card, settled HTML bytes 1:4: this control has a browser handler but no native navigation or "
            "submission fallback",
            "- settled render output, settled HTML bytes 61:67: this control has a browser handler but no native "
            "navigation or submission fallback",
        ]
    )


@pytest.mark.parametrize(
    ("html", "message"),
    [
        # A marker in text survives the removal of marker attributes.
        (
            "<p data-citry-omit-handler-ab>data-citry-omit-handler-ab</p>",
            "Citry omission handler metadata escaped settled HTML cleanup",
        ),
        (
            "<p data-citry-omit-handler-ab>\ud800</p>",
            "Citry omission handler metadata remained in unparseable settled HTML",
        ),
    ],
)
def test_omit_rejects_a_marker_it_cannot_remove(html: str, message: str) -> None:
    policy = _JavascriptPolicy("omit")
    with pytest.raises(ValueError, match=f"^{message}$"):
        policy.validate_settled_html(
            html,
            marker_prefix="data-t",
            trusted_tag_starts=frozenset(),
            component_classes={},
            omit_handler_marker="data-citry-omit-handler-ab",
        )


def test_javascript_warning_reports_a_raw_script_once_across_both_checks() -> None:
    policy = _JavascriptPolicy("warn")
    policy.validate_pre_extension_html("<script>a()</script>", component_classes={})
    policy.validate_settled_html(
        "<script>a()</script><script>a()</script>",
        marker_prefix="data-t",
        trusted_tag_starts=frozenset(),
        component_classes={},
    )
    assert _warning(policy) == _lines(
        [
            "security_javascript='warn' found 2 client behavior requirement(s):",
            "- settled render output, pre-extension HTML bytes 1:7: a raw executable <script> remains outside "
            "Citry's dependency policy",
            "- settled render output, dependency bytes 21:27: a raw executable <script> remains outside Citry's "
            "dependency policy",
        ]
    )


def test_javascript_policy_reports_a_page_it_cannot_read() -> None:
    policy = _JavascriptPolicy("warn")
    html = "<a>\ud800</a>"
    assert (
        policy.validate_settled_html(html, marker_prefix="", trusted_tag_starts=frozenset(), component_classes={})
        is html
    )
    assert _warning(policy) == _lines(
        [
            "security_javascript='warn' found 1 client behavior requirement(s):",
            "- settled render output: settled HTML could not be parsed for JavaScript policy validation ('utf-8' "
            "codec can't encode character '\\ud800' in position 3: surrogates not allowed)",
        ]
    )


def test_one_read_of_a_page_serves_both_validators() -> None:
    html = '<a onclick="x()" href="javascript:y">a</a>'
    check = _output_policy.check_output_html(html, csp=True, javascript="warn", marker_prefix="data-t")
    csp = _CspRenderValidator("warn")
    policy = _JavascriptPolicy("warn")
    policy.validate_settled_html(
        html, marker_prefix="data-t", trusted_tag_starts=frozenset(), component_classes={}, check=check
    )
    csp.validate_settled_html(
        html, marker_prefix="data-t", trusted_tag_starts=frozenset(), component_classes={}, check=check
    )
    assert [finding.attribute for finding in csp._findings] == ["onclick", "href"]
    assert [finding.rule for finding in policy._findings] == ["native-handler", "javascript-url"]
    # A check made for other rules is refused rather than read wrongly.
    with pytest.raises(AssertionError, match="was not made for"):
        _CspRenderValidator("warn").validate_settled_html(
            html,
            marker_prefix="data-t",
            trusted_tag_starts=frozenset(),
            component_classes={},
            check=_output_policy.check_output_html(html, javascript="warn"),
        )


@breaks_one_side
def test_strict_serialize_of_a_large_page_builds_no_python_tag_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = Citry(autodiscover=False, security_csp="strict")

    class Rows(Component):
        citry = engine

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"rows": [{"id": index, "name": f"Row {index}"} for index in range(500)]}

        template = """
<table>
  <tbody>
    <c-for each="row in rows">
      <tr id="row-{{ row['id'] }}" class="row"><td><a href="/rows/{{ row['id'] }}">{{ row['name'] }}</a></td></tr>
    </c-for>
  </tbody>
</table>
"""

    def refuse(source: str) -> list[dict[str, object]]:
        msg = "the output checks must not turn every tag into Python objects"
        raise AssertionError(msg)

    rendered = Rows().render()
    monkeypatch.setattr(_output_html, "_scan_output_html", refuse)
    html = rendered.serialize(deps_strategy="simple", csp_nonce="cmVxdWVzdE5vbmNl")
    assert html.count("<tr ") == 500
    # Rust returns only the page's script and style elements, never one
    # entry per row.
    check = _output_policy.check_output_html(html, csp=True, marker_prefix="data-t")
    assert check.error is None
    assert all(event[0] == "element" and event[1] in {"script", "style"} for event in check.events)


@breaks_one_side
@pytest.mark.parametrize("mode", ["warn", "strict"])
def test_an_internal_error_in_the_output_check_reports_the_page_as_unreadable(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = Citry(autodiscover=False, security_csp=mode)  # type: ignore[arg-type]

    class Card(Component):
        citry = engine
        template = """
<p>kept</p>
"""

    def broken(html: str, **options: object) -> object:
        # What the Rust binding raises when the check panics.
        msg = "citry output check failed: boom"
        raise ValueError(msg)

    rendered = Card().render()
    monkeypatch.setattr(_output_policy, "_check_output_html", broken)
    message = "the settled HTML could not be parsed for CSP validation (citry output check failed: boom)"
    if mode == "strict":
        with pytest.raises(ValueError, match=re.escape(message)):
            rendered.serialize(deps_strategy="simple", csp_nonce="cmVxdWVzdE5vbmNl")
        return
    # A warn mode still serves the page.
    with pytest.warns(RuntimeWarning, match=re.escape(message)):
        html = rendered.serialize(deps_strategy="simple", csp_nonce="cmVxdWVzdE5vbmNl")
    assert "<p" in html
    assert "kept</p>" in html


def test_a_caller_error_is_raised_not_reported_as_an_unreadable_page() -> None:
    with pytest.raises(ValueError, match="unknown security_javascript mode"):
        _output_policy.check_output_html("<p>x</p>", javascript="sometimes")  # type: ignore[arg-type]
    # Any collection of trusted starts works.
    check = _output_policy.check_output_html(
        "<style>a{}</style>",
        csp=True,
        marker_prefix=None,
        trusted_tag_starts=[0],  # type: ignore[arg-type]
    )
    assert check.error is None
    assert [event[6] for event in check.events] == [True]


def _serialize_warnings(page: type[Component]) -> list[str]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        page().render().serialize(deps_strategy="ignore")
    # The byte offsets move with the generated component ids, so the
    # helper writes them as `s:e`; these tests check the component a
    # finding names.
    return [re.sub(r"bytes \d+:\d+", "bytes s:e", str(warning.message)) for warning in caught]


def test_a_finding_inside_a_component_names_that_component() -> None:
    app = Citry(autodiscover=False, security_javascript="warn")

    class Card(Component):
        citry = app
        template = """
<div>
  <a href="javascript:void(0)">x</a>
</div>
"""

    assert _serialize_warnings(Card) == [
        _lines(
            [
                "security_javascript='warn' found 1 client behavior requirement(s):",
                "- Card, attribute 'href', settled HTML bytes s:e: a javascript: URL in 'href' remains "
                "executable browser code",
            ]
        )
    ]


def test_a_finding_inside_a_nested_component_names_the_innermost_one() -> None:
    app = Citry(autodiscover=False, security_javascript="warn")

    class Inner(Component):
        citry = app
        template = """
<div>
  <a href="javascript:void(0)">in</a>
</div>
"""

    class Outer(Component):
        citry = app
        template = """
<section>
  <c-Inner />
</section>
"""

    assert _serialize_warnings(Outer) == [
        _lines(
            [
                "security_javascript='warn' found 1 client behavior requirement(s):",
                "- Inner, attribute 'href', settled HTML bytes s:e: a javascript: URL in 'href' remains "
                "executable browser code",
            ]
        )
    ]


def test_a_finding_in_slot_content_names_the_component_that_renders_the_slot() -> None:
    app = Citry(autodiscover=False, security_javascript="warn")

    class Card(Component):
        citry = app
        template = """
<div>
  <c-slot />
</div>
"""

    class Page(Component):
        citry = app
        template = """
<section>
  <c-Card>
    <a href="javascript:void(0)">x</a>
  </c-Card>
</section>
"""

    # The browser puts the link inside the Card's `<div>`, so the report
    # names Card, not Page, which wrote the link.
    assert _serialize_warnings(Page) == [
        _lines(
            [
                "security_javascript='warn' found 1 client behavior requirement(s):",
                "- Card, attribute 'href', settled HTML bytes s:e: a javascript: URL in 'href' remains "
                "executable browser code",
            ]
        )
    ]


def test_an_element_the_browser_moves_out_of_every_root_is_not_named_after_a_component() -> None:
    app = Citry(autodiscover=False, security_javascript="warn")

    class Inner(Component):
        citry = app
        template = """
<div>y</div>
"""

    class Outer(Component):
        citry = app
        # Inner's `<div>` closes Outer's open `<p>`, so the browser puts the
        # link after both components' roots. Each component's roots are
        # marked on their own, so the link sits inside Outer's `<p>` in the
        # source, and the report must follow the browser's tree instead.
        template = """
<p><c-Inner /><a href="javascript:void(0)">x</a></p>
"""

    assert _serialize_warnings(Outer) == [
        _lines(
            [
                "security_javascript='warn' found 1 client behavior requirement(s):",
                "- settled render output, attribute 'href', settled HTML bytes s:e: a javascript: URL in "
                "'href' remains executable browser code",
            ]
        )
    ]


def test_an_element_after_a_paragraph_the_browser_closes_is_named_after_the_component() -> None:
    app = Citry(autodiscover=False, security_javascript="warn")

    class Paragraph(Component):
        citry = app
        # The `<div>` closes the open `<p>`, so the browser makes the
        # `<div>` a second top-level element of the component. It carries
        # the component's marker too, so the link inside it is named after
        # the component.
        template = """
<p>text<div><a href="javascript:void(0)">x</a></div></p>
"""

    assert _serialize_warnings(Paragraph) == [
        _lines(
            [
                "security_javascript='warn' found 1 client behavior requirement(s):",
                "- Paragraph, attribute 'href', settled HTML bytes s:e: a javascript: URL in "
                "'href' remains executable browser code",
            ]
        )
    ]


def test_omit_passes_a_submit_button_inside_a_form() -> None:
    app = Citry(autodiscover=False, security_javascript="omit")

    class SaveForm(Component):
        citry = app
        template = """
<form action="/save" method="post">
  <button @click="track()">Save</button>
</form>
"""

    # The form submits without JavaScript, so the button has a fallback.
    assert _serialize_warnings(SaveForm) == []


def test_omit_reports_a_button_after_its_form_closed() -> None:
    app = Citry(autodiscover=False, security_javascript="omit")

    class LateButton(Component):
        citry = app
        template = """
<div>
  <form action="/save"></form>
  <button @click="track()">Save</button>
</div>
"""

    assert _serialize_warnings(LateButton) == [
        _lines(
            [
                "security_javascript='omit' found 1 client behavior requirement(s):",
                "- LateButton, settled HTML bytes s:e: this control has a browser handler but no native "
                "navigation or submission fallback",
            ]
        )
    ]
