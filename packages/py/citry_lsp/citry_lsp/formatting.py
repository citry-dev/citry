"""Current-document formatting for standard and Citry-specific LSP requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypeAlias

from citry import (
    LspPosition,
    PythonComponentAssetNotice,
    PythonComponentAssetPlan,
    PythonComponentAssetRequest,
    PythonTemplateFormatError,
    finish_python_component_assets,
    format_python_templates,
    prepare_python_component_assets,
)
from citry_core.template_formatter import (
    EmbeddedFormatNotice,
    EmbeddedFormatPlan,
    EmbeddedFormatRequest,
    EmbeddedFormatResult,
    TemplateFormatError,
    finish_embedded_format,
    format_template,
    prepare_embedded_format,
)
from citry_lsp.regions import document_offset_at, document_range_for_offsets, standalone_region

if TYPE_CHECKING:
    from lsprotocol import types

    from citry import LspRange
    from citry_lsp.engine import DocumentState

FormatScope = Literal["document", "position"]
FormatTemplatesResponse = dict[str, object]
_UnderlyingAssetPlan: TypeAlias = EmbeddedFormatPlan | PythonComponentAssetPlan


@dataclass(frozen=True, slots=True)
class EmbeddedProviderRequest:
    """One normalized virtual document sent from the server to its client."""

    id: str
    language: str
    kind: str
    source: str
    virtual_source: str
    forbidden_substrings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreparedComponentAssets:
    """Bind an external-provider round trip to one synchronized document."""

    id: str
    document_uri: str
    document_version: int
    document_source: str
    requests: tuple[EmbeddedProviderRequest, ...]
    _plan: _UnderlyingAssetPlan = field(repr=False)


def format_templates(
    document: DocumentState,
    *,
    requested_version: int,
    scope: FormatScope,
    position: types.Position | None = None,
) -> FormatTemplatesResponse:
    """Format current authored text and return one protocol-ready result."""
    if document.version != requested_version:
        return _refused(
            "citry.format.stale-document",
            f"document version {requested_version} is stale; current version is {document.version}",
        )
    if _is_standalone_template_document(document):
        if scope != "document":
            return _refused(
                "citry.format.ineligible",
                "standalone Citry templates support document formatting only",
            )
        return _format_standalone(document)
    if document.language_id != "python":
        return _refused(
            "citry.format.ineligible",
            f"Citry formatting is unavailable for language {document.language_id!r}",
        )
    return _format_python(document, scope=scope, position=position)


def prepare_component_assets(
    document: DocumentState,
    *,
    requested_version: int,
    scope: FormatScope,
    position: types.Position | None = None,
) -> PreparedComponentAssets | FormatTemplatesResponse:
    """Prepare current component assets without running a language provider."""
    if document.version != requested_version:
        return _refused(
            "citry.format.stale-document",
            f"document version {requested_version} is stale; current version is {document.version}",
        )
    plan: _UnderlyingAssetPlan
    if _is_standalone_template_document(document):
        if scope != "document":
            return _refused(
                "citry.format.ineligible",
                "standalone Citry templates support document formatting only",
            )
        try:
            core_plan = prepare_embedded_format(document.source)
        except TemplateFormatError as error:
            return _template_refusal(document, error)
        plan = core_plan
        requests = tuple(_core_provider_request(request) for request in core_plan.requests)
    elif document.language_id == "python":
        host_offset: int | None = None
        if scope == "position":
            if position is None:
                return _refused("citry.format.ineligible", "position scope requires a document position")
            try:
                host_offset = document_offset_at(
                    document.source,
                    LspPosition(position.line, position.character),
                )
            except ValueError as error:
                return _refused("citry.format.ineligible", str(error))
        try:
            python_plan = prepare_python_component_assets(document.source, host_offset=host_offset)
        except PythonTemplateFormatError as error:
            return _python_refusal(document, error)
        plan = python_plan
        requests = tuple(_python_provider_request(request) for request in python_plan.requests)
    else:
        return _refused(
            "citry.format.ineligible",
            f"Citry formatting is unavailable for language {document.language_id!r}",
        )
    if document.version is None:
        return _refused(
            "citry.format.stale-document",
            "document does not have a synchronized version",
        )
    return PreparedComponentAssets(
        id=plan.id,
        document_uri=document.uri,
        document_version=document.version,
        document_source=document.source,
        requests=requests,
        _plan=plan,
    )


def finish_component_assets(
    document: DocumentState,
    prepared: PreparedComponentAssets,
    results: list[EmbeddedFormatResult] | tuple[EmbeddedFormatResult, ...],
) -> FormatTemplatesResponse:
    """Validate provider replies and compose one current atomic document edit."""
    if (
        document.uri != prepared.document_uri
        or document.version != prepared.document_version
        or document.source != prepared.document_source
    ):
        return _refused(
            "citry.format.stale-document",
            "document changed while embedded formatting was in progress",
        )
    try:
        if isinstance(prepared._plan, EmbeddedFormatPlan):
            embedded_outcome = finish_embedded_format(prepared._plan, results)
            candidate = embedded_outcome.source
            notices = [_embedded_notice_dict(notice) for notice in embedded_outcome.notices]
            providers = list(embedded_outcome.providers)
        else:
            python_outcome = finish_python_component_assets(prepared._plan, results)
            candidate = python_outcome.source
            notices = [_python_notice_dict(notice) for notice in python_outcome.notices]
            providers = list(python_outcome.providers)
    except TemplateFormatError as error:
        return _template_refusal(document, error)
    except PythonTemplateFormatError as error:
        return _python_refusal(document, error)
    return _changed_result(
        document,
        candidate,
        notices=notices,
        providers=providers,
    )


def _format_standalone(document: DocumentState) -> FormatTemplatesResponse:
    try:
        candidate = format_template(document.source)
    except TemplateFormatError as error:
        return _template_refusal(document, error)
    return _changed_result(document, candidate)


def _is_standalone_template_document(document: DocumentState) -> bool:
    """Accept explicit Citry mode and registry-owned HTML, but not arbitrary HTML."""
    if document.language_id == "citry-html":
        return True
    return document.language_id == "html" and len(document.regions) == 1 and document.regions[0].key == "standalone"


def _format_python(
    document: DocumentState,
    *,
    scope: FormatScope,
    position: types.Position | None,
) -> FormatTemplatesResponse:
    host_offset: int | None = None
    if scope == "position":
        if position is None:
            return _refused("citry.format.ineligible", "position scope requires a document position")
        try:
            host_offset = document_offset_at(
                document.source,
                LspPosition(position.line, position.character),
            )
        except ValueError as error:
            return _refused("citry.format.ineligible", str(error))
    try:
        result = format_python_templates(document.source, host_offset=host_offset)
    except PythonTemplateFormatError as error:
        return _python_refusal(document, error)
    return _changed_result(document, result.source)


def _changed_result(
    document: DocumentState,
    candidate: str,
    *,
    notices: list[dict[str, object]] | None = None,
    providers: list[str] | None = None,
) -> FormatTemplatesResponse:
    if candidate == document.source:
        response: FormatTemplatesResponse = {"kind": "unchanged"}
    else:
        edit_range = document_range_for_offsets(document.source, 0, len(document.source))
        response = {
            "kind": "edit",
            "edit": {
                "documentChanges": [
                    {
                        "textDocument": {
                            "uri": document.uri,
                            "version": document.version,
                        },
                        "edits": [
                            {
                                "range": _range_dict(edit_range),
                                "newText": candidate,
                            }
                        ],
                    }
                ]
            },
        }
    if notices is not None:
        response["notices"] = notices
    if providers is not None:
        response["providers"] = providers
    return response


def _core_provider_request(request: EmbeddedFormatRequest) -> EmbeddedProviderRequest:
    forbidden = {
        "script-body": ("</script", "{{", "{#"),
        "style-body": ("</style", "{{", "{#"),
    }[request.kind.value]
    return EmbeddedProviderRequest(
        id=request.id,
        language=request.language.value,
        kind=request.kind.value,
        source=request.source,
        virtual_source=request.virtual_source,
        forbidden_substrings=forbidden,
    )


def _python_provider_request(request: PythonComponentAssetRequest) -> EmbeddedProviderRequest:
    forbidden: tuple[str, ...]
    if request.region_kind is not None:
        kind = request.region_kind.value
        forbidden = ("</script", "{{", "{#") if kind == "script-body" else ("</style", "{{", "{#")
    else:
        kind = "component-js" if request.asset_kind.value == "js" else "component-css"
        forbidden = ()
    return EmbeddedProviderRequest(
        id=request.id,
        language=request.language.value,
        kind=kind,
        source=request.source,
        virtual_source=request.virtual_source,
        forbidden_substrings=forbidden,
    )


def _embedded_notice_dict(notice: EmbeddedFormatNotice) -> dict[str, object]:
    return {
        "code": notice.code,
        "message": notice.message,
        "regionId": notice.region_id,
        "language": notice.language.value if notice.language is not None else None,
    }


def _python_notice_dict(notice: PythonComponentAssetNotice) -> dict[str, object]:
    return {
        "code": notice.code,
        "message": notice.message,
        "regionId": notice.request_id,
        "componentName": notice.component_name,
        "assetKind": notice.kind.value,
    }


def _template_refusal(document: DocumentState, error: TemplateFormatError) -> FormatTemplatesResponse:
    mapped: LspRange | None = None
    if error.range is not None and error.code != "citry.format.provider-invalid":
        try:
            mapped = standalone_region(document.source).source_map.map_range(*error.range)
        except ValueError:
            mapped = None
    return _refused(error.code, str(error), mapped)


def _python_refusal(document: DocumentState, error: PythonTemplateFormatError) -> FormatTemplatesResponse:
    mapped: LspRange | None = None
    if error.range is not None:
        try:
            mapped = document_range_for_offsets(document.source, *error.range)
        except ValueError:
            mapped = None
    return _refused(error.code, str(error), mapped)


def _refused(
    code: str,
    message: str,
    error_range: LspRange | None = None,
) -> FormatTemplatesResponse:
    return {
        "kind": "refused",
        "code": code,
        "message": message,
        "range": _range_dict(error_range) if error_range is not None else None,
    }


def _range_dict(value: LspRange) -> dict[str, object]:
    return {
        "start": {"line": value.start.line, "character": value.start.character},
        "end": {"line": value.end.line, "character": value.end.character},
    }


__all__ = [
    "EmbeddedProviderRequest",
    "FormatScope",
    "FormatTemplatesResponse",
    "PreparedComponentAssets",
    "finish_component_assets",
    "format_templates",
    "prepare_component_assets",
]
