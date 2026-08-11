"""Versioned constants and status payloads shared with editor clients."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from citry_core.template_formatter import python_expression_provider

SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = 1
CATALOG_SCHEMA_VERSION = 1
SUPPORTED_CITRY_SERIES = (0, 3)
BROWSER_PROJECTION_METHOD = "citry/browserProjection"
HTML_PROJECTION_METHOD = "citry/htmlProjection"
FORMAT_TEMPLATES_METHOD = "citry/formatTemplates"
FORMAT_COMPONENT_ASSETS_METHOD = "citry/formatComponentAssets"
FORMAT_EMBEDDED_METHOD = "citry/formatEmbedded"
EMBEDDED_FORMATTING_VERSION = 1
PYTHON_EXPRESSION_PROVIDER = python_expression_provider()

AnalysisMode = Literal["registry", "syntax-only", "unavailable"]


@dataclass(frozen=True, slots=True)
class EmbeddedFormattingCapability:
    """Describe the external formatting mechanism a connected client offers."""

    version: int = EMBEDDED_FORMATTING_VERSION
    languages: tuple[str, ...] = ()
    provider_selection: str = "vscode-first-result"
    provider_identity: str | None = None
    provider_version: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectStatus:
    """Report the server's selected project and active confidence level."""

    protocol_version: int = PROTOCOL_VERSION
    server_version: str = SERVER_VERSION
    interpreter: str = ""
    workspace: str = ""
    app: str | None = None
    mode: AnalysisMode = "syntax-only"
    registry_ready: bool = False
    citry_version: str | None = None
    catalog_schema_version: int | None = None
    python_expression_provider: str | None = PYTHON_EXPRESSION_PROVIDER
    embedded_formatting: EmbeddedFormattingCapability | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready status object."""
        return asdict(self)


__all__ = [
    "BROWSER_PROJECTION_METHOD",
    "CATALOG_SCHEMA_VERSION",
    "EMBEDDED_FORMATTING_VERSION",
    "FORMAT_COMPONENT_ASSETS_METHOD",
    "FORMAT_EMBEDDED_METHOD",
    "FORMAT_TEMPLATES_METHOD",
    "HTML_PROJECTION_METHOD",
    "PROTOCOL_VERSION",
    "PYTHON_EXPRESSION_PROVIDER",
    "SERVER_VERSION",
    "SUPPORTED_CITRY_SERIES",
    "AnalysisMode",
    "EmbeddedFormattingCapability",
    "ProjectStatus",
]
