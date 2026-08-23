import pytest

from citry_ui.quality.validate_html import HtmlQualificationError, qualify_nu_result


def test_nu_result_records_alpine_directives_without_hiding_other_information():
    report = qualify_nu_result(
        {
            "version": "test",
            "messages": [
                {
                    "type": "error",
                    "message": "Attribute “x-data” not allowed on element “section” at this point.",
                },
                {
                    "type": "error",
                    "message": "Attribute “x-text” not allowed on element “output” at this point.",
                },
                {"type": "info", "message": "A non-gating recommendation."},
            ],
        },
        scenario="tabs.overview",
    )

    assert report.errors == 0
    assert report.alpine_directives == ("x-data", "x-text")
    assert report.css_anchor_features == ()
    assert report.information == 1


def test_nu_result_records_alpines_shorthand_spellings():
    # `@event` and `:attr` are Alpine's shorthands for `x-on:` and `x-bind:`, so
    # Nu rejects them for the same reason it rejects the `x-` forms.
    report = qualify_nu_result(
        {
            "version": "test",
            "messages": [
                {
                    "type": "error",
                    "message": "Attribute “@submit.prevent” not allowed on element “form” at this point.",
                },
                {
                    "type": "error",
                    "message": "Attribute “@reset” not allowed on element “form” at this point.",
                },
                {
                    "type": "error",
                    "message": "Attribute “:style” not allowed on element “div” at this point.",
                },
            ],
        },
        scenario="button.states",
    )

    assert report.errors == 0
    assert report.alpine_directives == (":style", "@reset", "@submit.prevent")


def test_nu_result_records_css_anchor_features_without_hiding_other_css_errors():
    report = qualify_nu_result(
        {
            "version": "test",
            "messages": [
                {
                    "type": "error",
                    "message": "CSS: “anchor-name”: Property “anchor-name” doesn't exist.",
                },
                {
                    "type": "error",
                    "message": "CSS: “position-anchor”: Property “position-anchor” doesn't exist.",
                },
                {
                    "type": "error",
                    "message": "CSS: “position-area”: Property “position-area” doesn't exist.",
                },
                {
                    "type": "error",
                    "message": "CSS: “position-try-fallbacks”: Property “position-try-fallbacks” doesn't exist.",
                },
                {
                    "type": "error",
                    "message": "CSS: “position-visibility”: Property “position-visibility” doesn't exist.",
                },
                {
                    "type": "error",
                    "message": "CSS: “inline-size”: Parse Error.",
                    "extract": "inline-size: min(anchor-size(width), 20rem)",
                },
            ],
        },
        scenario="split-button.states",
    )

    assert report.css_anchor_features == (
        "anchor-name",
        "anchor-size()",
        "position-anchor",
        "position-area",
        "position-try-fallbacks",
        "position-visibility",
    )


def test_nu_result_rejects_an_unrelated_inline_size_parse_error():
    with pytest.raises(HtmlQualificationError, match="inline-size"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 9,
                        "message": "CSS: “inline-size”: Parse Error.",
                        "extract": "inline-size: calc(100% - );",
                    }
                ],
            },
            scenario="split-button.states",
        )


def test_nu_result_still_rejects_citrys_own_event_syntax():
    # `@c-*` is Citry's event syntax, which the server consumes and never
    # renders. Meeting one in output means it leaked, so it stays an error even
    # though it looks like an Alpine shorthand.
    with pytest.raises(HtmlQualificationError, match="@c-click"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 7,
                        "message": "Attribute “@c-click” not allowed on element “button” at this point.",
                    }
                ],
            },
            scenario="button.states",
        )


def test_nu_result_rejects_an_unexpected_html_error():
    with pytest.raises(HtmlQualificationError, match="line 12: End tag"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 12,
                        "message": "End tag for body seen, but there were unclosed elements.",
                    }
                ],
            },
            scenario="tabs.overview",
        )
