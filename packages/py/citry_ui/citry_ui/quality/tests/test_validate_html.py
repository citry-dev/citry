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
