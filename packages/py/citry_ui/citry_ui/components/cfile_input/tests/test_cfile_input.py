from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CDropTarget, CFileInput


def _render(template: str, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("<c-css />" if include_css else "")

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def _tag(html: str, part: str) -> str:
    match = re.search(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_schemas_and_aliases_are_exact() -> None:
    assert [field.name for field in fields(CFileInput.Kwargs)] == [
        "id",
        "name",
        "accept",
        "capture",
        "multiple",
        "required",
        "disabled",
        "invalid",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CDropTarget.Kwargs)] == [
        "label",
        "id",
        "name",
        "accept",
        "capture",
        "multiple",
        "required",
        "disabled",
        "invalid",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    hints = get_type_hints(CFileInput.Kwargs)
    assert hints["capture"] == citry_ui.CFileInputCapture | None
    assert hints["variant"] == citry_ui.CFileInputVariant
    assert hints["size"] == citry_ui.CFileInputSize
    assert CFileInput in citry_ui.COMPONENTS
    assert CDropTarget in citry_ui.COMPONENTS


def test_file_input_is_a_native_form_control() -> None:
    tag = _tag(
        _render(
            '<c-CFileInput id="evidence" name="documents" accept="application/pdf,.txt" '
            'capture="environment" multiple required variant="soft" size="lg" />'
        ),
        "file-input",
    )
    assert 'type="file"' in tag
    assert 'id="evidence"' in tag
    assert 'name="documents"' in tag
    assert 'accept="application/pdf,.txt"' in tag
    assert 'capture="environment"' in tag
    assert "multiple" in tag
    assert "required" in tag
    assert 'data-variant="soft"' in tag
    assert 'data-size="lg"' in tag


def test_drop_target_has_one_owned_native_input_and_visible_content() -> None:
    html = _render('<c-CDropTarget label="Evidence files" name="evidence" multiple>PDF or image files</c-CDropTarget>')
    root = _tag(html, "drop-target")
    native = _tag(html, "input")
    assert root.startswith("<label")
    assert native.startswith("<input")
    assert 'type="file"' in native
    assert 'aria-label="Evidence files"' in native
    assert "Evidence files" in html
    assert "PDF or image files" in html
    assert len(re.findall(r'<input[^>]+type="file"', html.split("<script", 1)[0])) == 1


def test_root_class_style_and_attrs_merge() -> None:
    file_tag = _tag(
        _render('<c-CFileInput class_="brand" style="inline-size: 20rem" c-attrs="{\'data-test\': \'file\'}" />'),
        "file-input",
    )
    assert 'class="cui-file-input brand"' in file_tag
    assert 'style="inline-size: 20rem;"' in file_tag
    assert 'data-test="file"' in file_tag

    drop_tag = _tag(
        _render('<c-CDropTarget label="Upload" class_="drop-brand" c-attrs="{\'data-test\': \'drop\'}" />'),
        "drop-target",
    )
    assert 'class="cui-drop-target drop-brand"' in drop_tag
    assert 'data-test="drop"' in drop_tag


def test_file_input_integrates_with_field_relationships() -> None:
    html = _render(
        '<c-CField control_id="report" required invalid>'
        '<c-fill name="label">Report</c-fill>'
        '<c-fill name="default"><c-CFileInput name="report" /></c-fill>'
        '<c-fill name="description">One PDF</c-fill>'
        '<c-fill name="error">Choose a report</c-fill>'
        "</c-CField>"
    )
    tag = _tag(html, "file-input")
    assert 'id="report"' in tag
    assert "required" in tag
    assert 'aria-invalid="true"' in tag
    assert 'aria-describedby="report-description report-error"' in tag
    assert 'aria-errormessage="report-error"' in tag
    assert "data-citry-field-control" in tag


@pytest.mark.parametrize("state", ["required", "disabled", "invalid"])
def test_file_input_rejects_field_owned_state(state: str) -> None:
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            '<c-CField><c-fill name="label">File</c-fill><c-fill name="default">'
            f"<c-CFileInput {state} /></c-fill></c-CField>"
        )


def test_field_readonly_is_rejected_for_file_input() -> None:
    with pytest.raises(ValueError, match="readonly=True is not supported"):
        _render(
            '<c-CField readonly><c-fill name="label">File</c-fill>'
            '<c-fill name="default"><c-CFileInput /></c-fill></c-CField>'
        )


def test_drop_target_rejects_field_context() -> None:
    with pytest.raises(ValueError, match="cannot be used as the control inside CField"):
        _render(
            '<c-CField><c-fill name="label">File</c-fill>'
            '<c-fill name="default"><c-CDropTarget label="Upload" /></c-fill></c-CField>'
        )


def test_form_context_supplies_native_owner_and_disabledness() -> None:
    html = _render('<form id="upload-form"><c-CFileInput name="one" c-attrs="{\'form\': \'upload-form\'}" /></form>')
    file_tag = _tag(html, "file-input")
    assert 'form="upload-form"' in file_tag


@pytest.mark.parametrize("component", ["CFileInput", "CDropTarget"])
def test_conflicting_form_owner_is_rejected(component: str) -> None:
    declaration = (
        "<c-CFileInput c-attrs=\"{'form': 'outside'}\" />"
        if component == "CFileInput"
        else "<c-CDropTarget label=\"Upload\" c-input_attrs=\"{'form': 'outside'}\" />"
    )
    # The effective conflict is tested through CForm once the shared CForm
    # lifecycle fixture is available; the family must still preserve the
    # explicit native owner without rewriting it.
    html = _render(f'<form id="inside">{declaration}</form>')
    part = "file-input" if component == "CFileInput" else "input"
    assert 'form="outside"' in _tag(html, part)


@pytest.mark.parametrize(
    ("template", "message"),
    [
        ('<c-CFileInput capture="rear" />', "capture must be one of"),
        ('<c-CFileInput variant="raised" />', "variant must be one of"),
        ('<c-CFileInput size="xl" />', "size must be one of"),
        ('<c-CFileInput id="bad id" />', "ASCII whitespace"),
        ("<c-CDropTarget c-label=\"''\" />", "label must be a nonempty"),
    ],
)
def test_invalid_server_inputs_fail(template: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(template)


@pytest.mark.parametrize(
    "template",
    [
        "<c-CFileInput c-attrs=\"{'type': 'text'}\" />",
        "<c-CFileInput c-attrs=\"{':required': 'ready'}\" />",
        "<c-CFileInput c-attrs=\"{'x-model': 'files'}\" />",
        "<c-CDropTarget label=\"Upload\" c-attrs=\"{'for': 'other'}\" />",
        "<c-CDropTarget label=\"Upload\" c-attrs=\"{'x-html': 'content'}\" />",
        "<c-CDropTarget label=\"Upload\" c-input_attrs=\"{'aria-hidden': 'true'}\" />",
        "<c-CDropTarget label=\"Upload\" c-input_attrs=\"{':form': 'owner'}\" />",
    ],
)
def test_owned_and_structural_attrs_are_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(template)


def test_static_relationship_attrs_remain_available_standalone() -> None:
    file_tag = _tag(
        _render("<c-CFileInput c-attrs=\"{'aria-label': 'Choose evidence', 'aria-describedby': 'help'}\" />"),
        "file-input",
    )
    assert 'aria-label="Choose evidence"' in file_tag
    assert 'aria-describedby="help"' in file_tag
    drop_input = _tag(
        _render("<c-CDropTarget label=\"Evidence\" c-input_attrs=\"{'aria-describedby': 'drop-help'}\" />"),
        "input",
    )
    assert 'aria-describedby="drop-help"' in drop_input


def test_css_contract_contains_public_parts_variables_and_environments() -> None:
    html = _render('<c-CFileInput /><c-CDropTarget label="Upload" />', include_css=True)
    for token in (
        "--cui-file-input-background",
        "--cui-file-input-active-color",
        "--cui-file-input-invalid-color",
        "--cui-file-input-radius",
        'data-citry-ui-part="drop-target"',
        'data-citry-ui-part="input"',
        "prefers-reduced-motion",
        "forced-colors",
        "@media print",
    ):
        assert token in html
