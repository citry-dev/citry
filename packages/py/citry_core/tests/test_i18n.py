"""Tests for the locale primitives exposed through the Rust extension."""

import json

import pytest

from citry_core.i18n import (
    CatalogCompiler,
    I18nCompileError,
    TextCatalog,
    canonicalize_locale,
    locale_direction,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("EN-us", "en-US"),
        ("iw-IL", "he-IL"),
        ("hi-IN-u-nu-deva", "hi-IN-u-nu-deva"),
    ],
)
def test_canonicalize_locale(value: str, expected: str) -> None:
    assert canonicalize_locale(value) == expected


@pytest.mark.parametrize("value", ["", "en_US", "not a locale", "en--US"])
def test_canonicalize_locale_rejects_invalid_input(value: str) -> None:
    with pytest.raises(ValueError, match="locale"):
        canonicalize_locale(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("en-US", "ltr"), ("ar-EG", "rtl"), ("en-Arab", "rtl")],
)
def test_locale_direction(value: str, expected: str) -> None:
    assert locale_direction(value) == expected


def test_text_catalog_formats_values_and_attributes() -> None:
    catalog = TextCatalog(
        "en-US",
        "my-app-title = Account\n    .aria-label = Account summary",
        "account.ftl",
    )
    assert catalog.origin == "account.ftl"
    assert catalog.entries() == [("my-app-title", True, ["aria-label"])]
    assert catalog.format("my-app-title") == "Account"
    assert catalog.format("my-app-title", "aria-label") == "Account summary"


def test_text_catalog_accepts_locale_extensions() -> None:
    catalog = TextCatalog("hi-IN-u-nu-deva", "hello = Namaste", "account.ftl")
    assert catalog.format("hello") == "Namaste"


@pytest.mark.parametrize(
    "source",
    [
        "my-app-title = Hello, { $name }.",
        "-brand = Citry\nmy-app-title = { -brand }",
        "my-app-title = Unsafe \u202e text",
    ],
)
def test_text_catalog_rejects_unpromoted_or_unsafe_source(source: str) -> None:
    with pytest.raises(ValueError, match=r"unsupported|bidi-control"):
        TextCatalog("en-US", source, "account.ftl")


def _compile_request(*, source: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "active_locales": ["en-US"],
        "fallbacks": {},
        "packages": [{"name": "app", "source_locale": "en-US", "exports": ["hello"]}],
        "catalogs": [
            {
                "path": "app/en-US.ftl",
                "package": "app",
                "layer": "app",
                "precedence": 0,
                "locale": "en-US",
                "source": source,
            }
        ],
    }


def test_catalog_compiler_returns_checked_runtime_and_resolution_metadata() -> None:
    catalog = CatalogCompiler().compile(
        json.dumps(_compile_request(source="# @param {str} $name\nhello = Hello { $name }\n"))
    )
    args = json.dumps({"name": {"type": "str", "value": "Ada"}})
    assert catalog.schema_version == 1
    assert catalog.format("en-US", "hello", args) == "Hello \u2068Ada\u2069"
    resolved = json.loads(catalog.resolve_json("en-US", "hello", args))
    assert resolved == {
        "text": "Hello \u2068Ada\u2069",
        "requested_locale": "en-US",
        "selected_locale": "en-US",
        "owner": "app",
        "owner_source_locale": "en-US",
        "selected_layer": "app",
        "selected_path": "app/en-US.ftl",
        "used_fallback": False,
    }


def test_compiled_catalog_exposes_exact_browser_message_partitions() -> None:
    request = _compile_request(source="hello = Hello\nunused = Unused\n")
    request["packages"] = [{"name": "app", "source_locale": "en-US", "exports": []}]
    catalog = CatalogCompiler().compile(json.dumps(request))

    artifact = json.loads(
        catalog.browser_artifact_json(
            "en-US",
            json.dumps({"outputs": ["hello"], "messages": []}),
        )
    )

    assert artifact["runtime"] == "@fluent/bundle@0.19.1"
    assert artifact["requested_locale"] == "en-US"
    assert list(artifact["messages"]) == ["hello"]
    assert "Unused" not in artifact["bundles"]["en-US"]
    assert artifact["catalog_revision"] == catalog.revision


def test_compiled_catalog_exposes_localized_format_and_input_bindings() -> None:
    request = _compile_request(source="hello = Hello\n")
    request["formats"] = {
        "number": {
            "scientific-edit": {
                "input": {"notation": "decimal_or_scientific"},
            },
        },
        "percent": {
            "completion": {"input": {"affix": "required"}},
        },
        "unit": {
            "measurement": {"width": "long"},
        },
        "date": {
            "date-text": {
                "length": "short",
                "input": {"mode": "strict_text"},
            },
            "date-segments": {
                "length": "long",
                "input": {"mode": "segments"},
            },
        },
        "time": {
            "time-text": {
                "length": "medium",
                "input": {"mode": "strict_text"},
            },
            "time-segments": {
                "length": "medium",
                "input": {"mode": "segments"},
            },
        },
        "datetime": {
            "datetime-text": {
                "length": "medium",
                "time_zone_name": "none",
                "input": {"mode": "strict_text"},
            },
            "datetime-segments": {
                "length": "medium",
                "time_zone_name": "none",
                "input": {"mode": "segments"},
            },
        },
    }
    catalog = CatalogCompiler().compile(json.dumps(request))
    parser_artifact = json.loads(catalog.browser_parser_artifact_json("en-US"))

    assert parser_artifact["formats_revision"] == catalog.formats_revision
    assert parser_artifact["number"]["scientific-edit"]["notation"] == "decimal_or_scientific"
    assert parser_artifact["percent"]["completion"]["affix"] == "required"
    assert json.loads(catalog.parse_number_json("en-US", "scientific-edit", "1.25e3"))["value"] == "1250"
    assert catalog.format_percent("en-US", "completion", "0.125") == "12.5%"
    assert json.loads(catalog.parse_percent_json("en-US", "completion", "12.5%"))["value"] == "0.125"
    assert catalog.format_unit("en-US", "measurement", "1.5", "meter") == "1.5 meters"
    assert json.loads(catalog.parse_date_json("en-US", "date-text", "8/10/2026"))["value"] == {
        "year": 2026,
        "month": 8,
        "day": 10,
    }
    assert json.loads(
        catalog.parse_date_segments_json(
            "en-US",
            "date-segments",
            "2026",
            "8",
            "10",
        )
    )["value"] == {"year": 2026, "month": 8, "day": 10}
    time_text = catalog.format_time("en-US", "time-text", 14, 5, 9, 0)
    assert json.loads(catalog.parse_time_json("en-US", "time-text", time_text))["value"] == {
        "hour": 14,
        "minute": 5,
        "second": 9,
        "nanosecond": 0,
    }
    assert json.loads(
        catalog.parse_time_segments_json(
            "en-US",
            "time-segments",
            "2",
            "05",
            "09",
            "PM",
        )
    )["value"] == {"hour": 14, "minute": 5, "second": 9, "nanosecond": 0}
    assert json.loads(
        catalog.parse_datetime_segments_json(
            "en-US",
            "datetime-segments",
            "2026",
            "8",
            "10",
            "2",
            "05",
            "09",
            "PM",
        )
    )["value"] == {
        "year": 2026,
        "month": 8,
        "day": 10,
        "hour": 14,
        "minute": 5,
        "second": 9,
        "nanosecond": 0,
    }


def test_catalog_compiler_exposes_structured_diagnostic() -> None:
    request = _compile_request(source="hello = One\n")
    request["catalogs"].append(
        {
            "path": "app/duplicate.ftl",
            "package": "app",
            "layer": "app",
            "precedence": 0,
            "locale": "en-US",
            "source": "hello = Two\n",
        }
    )
    with pytest.raises(I18nCompileError) as caught:
        CatalogCompiler().compile(json.dumps(request))
    assert caught.value.code == "I18N_DUPLICATE_LAYER_OUTPUT"
    diagnostic = json.loads(caught.value.diagnostic_json)
    assert {diagnostic["path"], diagnostic["related"][0]["path"]} == {
        "app/duplicate.ftl",
        "app/en-US.ftl",
    }


def test_catalog_compiler_analyzes_one_editor_source_unit() -> None:
    compiler = CatalogCompiler()
    source = "hello = { -product }\n-product = Citry\n"
    analysis = json.loads(compiler.analyze_source("card.ftl", source))
    assert analysis["schema_version"] == 1
    assert [(item["kind"], item["token"]) for item in analysis["definitions"]] == [
        ("message", "hello"),
        ("term", "-product"),
    ]
    assert [(item["kind"], item["token"]) for item in analysis["references"]] == [
        ("term", "-product"),
    ]
    for item in (*analysis["definitions"], *analysis["references"]):
        expected = item["token"].removeprefix("-").split(".", maxsplit=1)[-1]
        assert source[item["start"] : item["end"]] == expected

    with pytest.raises(I18nCompileError) as caught:
        compiler.analyze_source(
            "card.ftl",
            "# @param {Slot1} $link\nhello = { $link }\n",
        )
    assert caught.value.code == "I18N_PARAM_TYPE_UNSUPPORTED"
