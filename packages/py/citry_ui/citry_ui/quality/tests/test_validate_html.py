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
    assert report.css_container_features == ()
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
    source = (
        '<div style="anchor-name: --_cui-menu-anchor-ref-a1;"></div>\n'
        "position-anchor: var(--_cui-menu-anchor);\n"
        "position-area: block-end span-inline-end;\n"
        "position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;\n"
        "position-visibility: anchors-visible;\n"
        "inline-size: min(anchor-size(width), var(--_cui-menu-max-inline-size));"
    )
    report = qualify_nu_result(
        {
            "version": "test",
            "messages": [
                {
                    "type": "error",
                    "lastLine": 1,
                    "message": "CSS: “anchor-name”: Property “anchor-name” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 2,
                    "message": "CSS: “position-anchor”: Property “position-anchor” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 3,
                    "message": "CSS: “position-area”: Property “position-area” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 4,
                    "message": "CSS: “position-try-fallbacks”: Property “position-try-fallbacks” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 5,
                    "message": "CSS: “position-visibility”: Property “position-visibility” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 6,
                    "message": "CSS: “inline-size”: Parse Error.",
                },
            ],
        },
        scenario="split-button.states",
        source=source,
    )

    assert report.css_anchor_features == (
        "anchor-name",
        "anchor-size()",
        "position-anchor",
        "position-area",
        "position-try-fallbacks",
        "position-visibility",
    )


def test_nu_result_uses_columns_to_check_repeated_minified_anchor_declarations():
    source = (
        ":where(.first){position-area:block-end}"
        ":where(.second){position-area:block-start}"
        ":where(.match){min-inline-size:anchor-size(width)}"
    )
    first_end = source.index("block-end") + len("block-end")
    second_end = source.index("block-start") + len("block-start")
    report = qualify_nu_result(
        {
            "version": "test",
            "messages": [
                {
                    "type": "error",
                    "lastLine": 1,
                    "lastColumn": first_end,
                    "message": "CSS: “position-area”: Property “position-area” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 1,
                    "lastColumn": second_end,
                    "message": "CSS: “position-area”: Property “position-area” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 1,
                    "message": ("CSS: “min-inline-size”: “anchor-size(width)” is not a “min-inline-size” value."),
                },
            ],
        },
        scenario="popover.states",
        source=source,
    )

    assert report.css_anchor_features == ("anchor-size()", "position-area")


def test_nu_result_records_checked_css_container_features():
    source = "container-type: inline-size;\n@container (width <= 22rem) {"
    report = qualify_nu_result(
        {
            "version": "test",
            "messages": [
                {
                    "type": "error",
                    "lastLine": 1,
                    "message": "CSS: “container-type”: Property “container-type” doesn't exist.",
                },
                {
                    "type": "error",
                    "lastLine": 2,
                    "message": "CSS: Unrecognized at-rule “@container”",
                },
            ],
        },
        scenario="tour.states",
        source=source,
    )

    assert report.css_container_features == ("@container", "container-type")


@pytest.mark.parametrize(
    ("message", "source"),
    [
        (
            "CSS: “container-type”: Property “container-type” doesn't exist.",
            "container-type: not-a-container-type;",
        ),
        (
            "CSS: Unrecognized at-rule “@container”",
            "@container (unknown-feature: enabled) {",
        ),
    ],
)
def test_nu_result_rejects_unrecognized_css_container_syntax(message: str, source: str):
    with pytest.raises(HtmlQualificationError, match="CSS"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [{"type": "error", "lastLine": 1, "message": message}],
            },
            scenario="tour.states",
            source=source,
        )


@pytest.mark.parametrize(
    "declaration",
    [
        "inline-size: calc(anchor-size(width) + );",
        "inline-size: min(anchor-size(width), calc(100% - ));",
        "inline-size: anchor-size(not-a-real-dimension);",
    ],
)
def test_nu_result_rejects_an_unrelated_inline_size_parse_error(declaration: str):
    with pytest.raises(HtmlQualificationError, match="inline-size"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 1,
                        "message": "CSS: “inline-size”: Parse Error.",
                    }
                ],
            },
            scenario="split-button.states",
            source=declaration,
        )


def test_nu_result_rejects_an_invalid_value_for_a_known_anchor_property():
    with pytest.raises(HtmlQualificationError, match="position-area"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 1,
                        "message": "CSS: “position-area”: Property “position-area” doesn't exist.",
                    }
                ],
            },
            scenario="split-button.states",
            source="position-area: not-a-real-area;",
        )


def test_nu_result_rejects_an_invalid_repeated_minified_anchor_declaration():
    source = ":where(.valid){position-area:block-end}:where(.invalid){position-area:not-a-real-area}"
    invalid_end = source.index("not-a-real-area") + len("not-a-real-area")
    with pytest.raises(HtmlQualificationError, match="position-area"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 1,
                        "lastColumn": invalid_end,
                        "message": "CSS: “position-area”: Property “position-area” doesn't exist.",
                    }
                ],
            },
            scenario="popover.states",
            source=source,
        )


def test_nu_result_rejects_an_invalid_min_inline_anchor_size_value():
    with pytest.raises(HtmlQualificationError, match="min-inline-size"):
        qualify_nu_result(
            {
                "version": "test",
                "messages": [
                    {
                        "type": "error",
                        "lastLine": 1,
                        "message": ("CSS: “min-inline-size”: “anchor-size(width)” is not a “min-inline-size” value."),
                    }
                ],
            },
            scenario="popover.states",
            source="min-inline-size: anchor-size(not-a-real-dimension);",
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
