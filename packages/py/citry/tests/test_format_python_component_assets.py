"""Tests for atomic Python component-asset formatting."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError

import pytest

from citry import (
    PythonComponentAssetKind,
    PythonTemplateFormatError,
    discover_python_component_assets,
    finish_python_component_assets,
    format_python_component_assets,
    prepare_python_component_assets,
)
from citry_core.template_formatter import EmbeddedFormatResult, EmbeddedLanguage


def _component_source(body: str) -> str:
    return f"from citry import Component\n\nclass Card(Component):\n{body}"


def _format_request(request: object) -> EmbeddedFormatResult:
    plan_id = request.plan_id  # type: ignore[attr-defined]
    region_id = request.id  # type: ignore[attr-defined]
    source = request.source  # type: ignore[attr-defined]
    language = request.language  # type: ignore[attr-defined]
    if language is EmbeddedLanguage.JAVASCRIPT:
        formatted = source.replace("const  ", "const ").replace("=1", " = 1")
    else:
        formatted = source.replace(".card{color:red}", ".card {\n  color: red;\n}")
    return EmbeddedFormatResult.formatted(plan_id, region_id, formatted, "fake@1")


def test_discovers_direct_and_file_assets_with_kind_identity() -> None:
    source = _component_source(
        '    template = """<main></main>"""\n    js = """const answer = 42;"""\n    css_file = "card.css"\n',
    )

    discovery = discover_python_component_assets(source)

    assert [(region.component_name, region.kind) for region in discovery.regions] == [
        ("Card", PythonComponentAssetKind.TEMPLATE),
        ("Card", PythonComponentAssetKind.JS),
    ]
    assert [(asset.component_name, asset.kind, asset.path) for asset in discovery.files] == [
        ("Card", PythonComponentAssetKind.CSS, "card.css"),
    ]
    assert discovery.notices == ()
    assert discovery.valid_python is True


def test_discovery_reports_computed_assets_without_claiming_them() -> None:
    source = _component_source(
        "    js = build_js()\n    css_file = choose_css()\n",
    )

    discovery = discover_python_component_assets(source)

    assert discovery.regions == ()
    assert discovery.files == ()
    assert [(notice.kind, notice.component_name) for notice in discovery.notices] == [
        (PythonComponentAssetKind.JS, "Card"),
        (PythonComponentAssetKind.CSS, "Card"),
    ]
    assert "computed js" in discovery.notices[0].message
    assert "computed css_file" in discovery.notices[1].message


def test_discovery_reports_conditional_and_conflicting_asset_declarations() -> None:
    source = _component_source(
        '    template = """<main></main>"""\n'
        '    template_file = "card.html"\n'
        "    if enabled:\n"
        '        js = """const enabled = true;"""\n'
        "    css = None\n",
    )

    discovery = discover_python_component_assets(source)

    assert discovery.regions == ()
    assert discovery.files == ()
    assert [(notice.kind, notice.message) for notice in discovery.notices] == [
        (
            PythonComponentAssetKind.TEMPLATE,
            "non-None template and template_file declarations conflict",
        ),
        (
            PythonComponentAssetKind.JS,
            "conditional or nested js binding cannot be resolved statically",
        ),
    ]


def test_two_pass_formats_template_embedded_regions_and_direct_assets_atomically() -> None:
    source = _component_source(
        '    template = """<main><script>const  answer=1;</script></main>"""\n'
        '    js = """const  direct=1;"""\n'
        '    css = """.card{color:red}"""\n',
    )

    plan = prepare_python_component_assets(source)

    assert [(request.asset_kind, request.language) for request in plan.requests] == [
        (PythonComponentAssetKind.TEMPLATE, EmbeddedLanguage.JAVASCRIPT),
        (PythonComponentAssetKind.JS, EmbeddedLanguage.JAVASCRIPT),
        (PythonComponentAssetKind.CSS, EmbeddedLanguage.CSS),
    ]
    assert plan.requests[0].source == "const  answer=1;"
    assert plan.requests[1].source == "const  direct=1;"
    with pytest.raises(FrozenInstanceError):
        plan.id = "replacement"  # type: ignore[misc]

    result = finish_python_component_assets(
        plan,
        [_format_request(request) for request in plan.requests],
    )

    assert "const answer = 1;" in result.source
    assert 'js = """const direct = 1;"""' in result.source
    assert 'css = """\n      .card {\n        color: red;\n      }\n    """' in result.source
    assert result.changed_component_assets == (
        ("Card", PythonComponentAssetKind.TEMPLATE),
        ("Card", PythonComponentAssetKind.JS),
        ("Card", PythonComponentAssetKind.CSS),
    )
    assert result.providers == ("fake@1",)
    assert format_python_component_assets(result.source, provider=_format_request).source == result.source


def test_multiline_direct_js_and_css_receive_canonical_host_framing() -> None:
    source = _component_source(
        '    js = """$component(() => {const value=1;run(value);});"""\n'
        '    css = """.card{color:red}.tag--active{color:blue}"""\n',
    )

    def provider(request: object) -> EmbeddedFormatResult:
        text = (
            "$component(() => {\n  const value = 1;\n  run(value);\n});\n"
            if request.language is EmbeddedLanguage.JAVASCRIPT  # type: ignore[attr-defined]
            else ".card {\n  color: red;\n}\n.tag--active {\n  color: blue;\n}\n"
        )
        return EmbeddedFormatResult.formatted(
            request.plan_id,  # type: ignore[attr-defined]
            request.id,  # type: ignore[attr-defined]
            text,
            "prettier@3.7.4",
        )

    result = format_python_component_assets(source, provider=provider)

    assert (
        'js = """\n      $component(() => {\n        const value = 1;\n        run(value);\n      });\n    """'
    ) in result.source
    assert (
        'css = """\n'
        "      .card {\n"
        "        color: red;\n"
        "      }\n"
        "      .tag--active {\n"
        "        color: blue;\n"
        "      }\n"
        '    """'
    ) in result.source
    assert format_python_component_assets(result.source, provider=provider).source == result.source


@pytest.mark.parametrize(
    ("literal", "provider_text", "host_newline"),
    [
        ('"const  value=1;"', 'const value = "quoted";\n', "\n"),
        ("'const  value=1;'", "const value = 'quoted';\r\n", "\n"),
        ('"""const  value=1;"""', 'const value = "quoted";\r', "\r\n"),
        ("'''const  value=1;'''", "const value = 'quoted';\r\n", "\r"),
        ('r"const  value=1;"', "const value = 1;", "\n"),
        ('r"const  value=1;"', r"const value = \"", "\n"),
        ("r'''const  value=1;'''", r"const value = \'", "\n"),
        ('u"const  value=1;"', "const value = 1;\n", "\n"),
    ],
)
def test_direct_assets_encode_provider_output_in_existing_literal(
    literal: str,
    provider_text: str,
    host_newline: str,
) -> None:
    source = _component_source(f"    js = {literal}\n").replace("\n", host_newline)

    def provider(request: object) -> EmbeddedFormatResult:
        return EmbeddedFormatResult.formatted(
            request.plan_id,  # type: ignore[attr-defined]
            request.id,  # type: ignore[attr-defined]
            provider_text,
            "fake@1",
        )

    result = format_python_component_assets(source, provider=provider)
    expected = provider_text.replace("\r\n", "\n").replace("\r", "\n")
    if literal.lstrip("ruRU").startswith(('"""', "'''")) and "\n" in expected:
        expected = f"\n{expected.rstrip(chr(10))}\n"

    ast.parse(result.source)
    discovery = discover_python_component_assets(result.source)
    assert discovery.regions[0].source_map.template_source == expected
    if host_newline != "\n":
        assert result.source.replace(host_newline, "").find("\n") == -1


def test_multiline_triple_double_asset_keeps_ordinary_javascript_quotes_plain() -> None:
    source = _component_source('    js = """const  label="value";"""\n')

    def provider(request: object) -> EmbeddedFormatResult:
        return EmbeddedFormatResult.formatted(
            request.plan_id,  # type: ignore[attr-defined]
            request.id,  # type: ignore[attr-defined]
            'const label = "value";\n',
            "prettier@3.7.4",
        )

    result = format_python_component_assets(source, provider=provider)

    assert 'const label = "value";' in result.source
    assert '\\"value\\"' not in result.source


@pytest.mark.parametrize("delimiter", ['"""', "'''"])
@pytest.mark.parametrize("quote_count", [1, 2, 3, 4])
@pytest.mark.parametrize("backslash_count", [0, 1, 2, 3, 4])
def test_direct_triple_quoted_assets_encode_matching_quote_and_backslash_runs(
    delimiter: str,
    quote_count: int,
    backslash_count: int,
) -> None:
    source = _component_source(f"    js = {delimiter}const value=1;{delimiter}\n")
    provider_text = "const value = " + ("\\" * backslash_count) + (delimiter[0] * quote_count)

    def provider(request: object) -> EmbeddedFormatResult:
        return EmbeddedFormatResult.formatted(
            request.plan_id,  # type: ignore[attr-defined]
            request.id,  # type: ignore[attr-defined]
            provider_text,
            "fake@1",
        )

    result = format_python_component_assets(source, provider=provider)

    ast.parse(result.source)
    discovery = discover_python_component_assets(result.source)
    assert discovery.regions[0].source_map.template_source == provider_text


def test_raw_single_quoted_asset_rejects_new_provider_lines_atomically() -> None:
    source = _component_source('    js = r"const value = 1;"\n')

    def provider(request: object) -> EmbeddedFormatResult:
        return EmbeddedFormatResult.formatted(
            request.plan_id,  # type: ignore[attr-defined]
            request.id,  # type: ignore[attr-defined]
            "const value = 1;\n",
            "fake@1",
        )

    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_component_assets(source, provider=provider)

    assert raised.value.code == "citry.format.ineligible"


def test_no_provider_keeps_js_css_and_still_formats_template_structure() -> None:
    source = _component_source(
        '    template = """<main  ><script>const  answer=1;</script></main>"""\n    js = """const  direct=1;"""\n',
    )

    result = format_python_component_assets(source)

    assert "<main>" in result.source
    assert "const  answer=1;" in result.source
    assert 'js = """const  direct=1;"""' in result.source
    assert [notice.kind for notice in result.notices] == [
        PythonComponentAssetKind.TEMPLATE,
        PythonComponentAssetKind.JS,
    ]
    assert all(notice.code == "citry.format.provider-unavailable" for notice in result.notices)


def test_template_capability_notice_is_not_duplicated_when_finishing() -> None:
    source = _component_source(
        '    template = """<script>const value = {{ value }};</script>"""\n',
    )

    plan = prepare_python_component_assets(source)
    result = finish_python_component_assets(plan, [])

    assert len(plan.notices) == 1
    assert result.notices == plan.notices


def test_required_provider_failure_rejects_the_complete_python_file() -> None:
    source = _component_source(
        '    template = """<main  ></main>"""\n    js = """const  value=1;"""\n',
    )
    plan = prepare_python_component_assets(source)
    request = plan.requests[0]

    with pytest.raises(PythonTemplateFormatError) as raised:
        finish_python_component_assets(
            plan,
            [EmbeddedFormatResult.unavailable(plan.id, request.id, "missing")],
            require_providers=True,
        )

    assert raised.value.code == "citry.format.provider-unavailable"
    assert not hasattr(raised.value, "source")


def test_required_providers_respect_explicit_suppression() -> None:
    source = _component_source(
        '    template = """{# fmt: off #}<script>const  value=1;</script>"""\n',
    )

    result = format_python_component_assets(source, require_providers=True)

    assert "const  value=1;" in result.source
    assert [notice.code for notice in result.notices] == [
        "citry.format.embedded-suppressed",
    ]


def test_provider_error_after_a_valid_result_is_atomic() -> None:
    source = _component_source(
        '    js = """const  value=1;"""\n    css = """.card{color:red}"""\n',
    )
    plan = prepare_python_component_assets(source)
    first, second = plan.requests

    with pytest.raises(PythonTemplateFormatError) as raised:
        finish_python_component_assets(
            plan,
            [
                _format_request(first),
                EmbeddedFormatResult.error(plan.id, second.id, "provider crashed"),
            ],
        )

    assert raised.value.code == "citry.format.provider-invalid"
    assert not hasattr(raised.value, "source")


def test_provider_exception_becomes_a_structured_atomic_error() -> None:
    source = _component_source('    js = """const value = 1;"""\n')

    def failing_provider(_request: object) -> EmbeddedFormatResult:
        msg = "provider crashed"
        raise RuntimeError(msg)

    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_component_assets(source, provider=failing_provider)

    assert raised.value.code == "citry.format.provider-invalid"
    assert "RuntimeError: provider crashed" in str(raised.value)
    assert not hasattr(raised.value, "source")


def test_cursor_scope_formats_only_the_containing_selected_asset() -> None:
    source = _component_source(
        '    template = """<main  ></main>"""\n    js = """const  value=1;"""\n    css = """.card{color:red}"""\n',
    )

    result = format_python_component_assets(
        source,
        kinds=(PythonComponentAssetKind.JS, PythonComponentAssetKind.CSS),
        host_offset=source.index("const"),
        provider=_format_request,
    )

    assert "<main  ></main>" in result.source
    assert "const value = 1;" in result.source
    assert ".card{color:red}" in result.source
    assert result.changed_component_assets == (("Card", PythonComponentAssetKind.JS),)


def test_invalid_provider_output_never_exposes_a_partial_candidate() -> None:
    source = _component_source("    js = r'''const value = 1;'''\n")

    def invalid(request: object) -> EmbeddedFormatResult:
        return EmbeddedFormatResult.formatted(
            request.plan_id,  # type: ignore[attr-defined]
            request.id,  # type: ignore[attr-defined]
            "const value = `'''`;",
            "fake@1",
        )

    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_component_assets(source, provider=invalid)

    assert raised.value.code == "citry.format.ineligible"
    assert not hasattr(raised.value, "source")


@pytest.mark.parametrize(
    "result",
    [
        EmbeddedFormatResult(
            status=EmbeddedFormatResult.formatted("p", "r", "x").status,
            plan_id="p",
            region_id="r",
            text="x",
            message="contradiction",
        ),
        EmbeddedFormatResult(
            status=EmbeddedFormatResult.unchanged("p", "r").status,
            plan_id="p",
            region_id="r",
            text="unexpected",
        ),
        EmbeddedFormatResult(
            status=EmbeddedFormatResult.unavailable("p", "r", "missing").status,
            plan_id="p",
            region_id="r",
            text="unexpected",
            message="missing",
        ),
    ],
)
def test_contradictory_direct_provider_payload_is_rejected(result: EmbeddedFormatResult) -> None:
    source = _component_source('    js = "const value = 1;"\n')
    plan = prepare_python_component_assets(source)
    request = plan.requests[0]
    contradictory = EmbeddedFormatResult(
        status=result.status,
        plan_id=plan.id,
        region_id=request.id,
        text=result.text,
        provider=result.provider,
        message=result.message,
    )

    with pytest.raises(PythonTemplateFormatError, match="provider result") as raised:
        finish_python_component_assets(plan, [contradictory])

    assert raised.value.code == "citry.format.provider-invalid"


def test_public_asset_api_is_exported_from_citry() -> None:
    import citry

    assert citry.PythonComponentAssetKind.JS.value == "js"
    assert citry.prepare_python_component_assets is prepare_python_component_assets
    assert citry.finish_python_component_assets is finish_python_component_assets
    assert citry.format_python_component_assets is format_python_component_assets
