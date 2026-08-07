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
