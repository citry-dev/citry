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
