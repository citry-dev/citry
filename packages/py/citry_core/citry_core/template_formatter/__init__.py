"""Rust-backed formatting for authored Citry template text."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from citry_core import _rust

TemplateFormatError: TypeAlias = _rust.template_formatter.TemplateFormatError


class EmbeddedLanguage(str, Enum):
    """A standalone language delegated to an embedded formatter provider."""

    JAVASCRIPT = "javascript"
    CSS = "css"


class EmbeddedRegionKind(str, Enum):
    """A Citry template location owned by an embedded formatter request."""

    SCRIPT_BODY = "script-body"
    STYLE_BODY = "style-body"


class EmbeddedResultStatus(str, Enum):
    """The outcome reported by an external embedded formatter provider."""

    FORMATTED = "formatted"
    UNCHANGED = "unchanged"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class EmbeddedFormatRequest:
    """One immutable standalone document offered to a provider."""

    id: str
    language: EmbeddedLanguage
    kind: EmbeddedRegionKind
    source: str
    virtual_source: str
    byte_range: tuple[int, int]
    base_indent: int
    newline: str


@dataclass(frozen=True, slots=True)
class EmbeddedFormatNotice:
    """A non-fatal reason why an embedded region was skipped or unchanged."""

    code: str
    message: str
    region_id: str | None
    language: EmbeddedLanguage | None


@dataclass(frozen=True, slots=True)
class EmbeddedFormatPlan:
    """A source-bound plan prepared before external provider delegation."""

    id: str
    formatted_source: str
    requests: tuple[EmbeddedFormatRequest, ...]
    notices: tuple[EmbeddedFormatNotice, ...]
    _handle: _rust.template_formatter._EmbeddedFormatPlan = field(
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, slots=True)
class EmbeddedFormatResult:
    """One provider response, echoing its plan and region identities."""

    status: EmbeddedResultStatus
    plan_id: str
    region_id: str
    text: str | None = None
    provider: str | None = None
    message: str | None = None

    @classmethod
    def formatted(
        cls,
        plan_id: str,
        region_id: str,
        text: str,
        provider: str | None = None,
    ) -> "EmbeddedFormatResult":
        """Report formatted provider output for a region."""
        return cls(
            status=EmbeddedResultStatus.FORMATTED,
            plan_id=plan_id,
            region_id=region_id,
            text=text,
            provider=provider,
        )

    @classmethod
    def unchanged(cls, plan_id: str, region_id: str) -> "EmbeddedFormatResult":
        """Report that the provider accepted but did not change a region."""
        return cls(
            status=EmbeddedResultStatus.UNCHANGED,
            plan_id=plan_id,
            region_id=region_id,
        )

    @classmethod
    def unavailable(
        cls,
        plan_id: str,
        region_id: str,
        message: str,
    ) -> "EmbeddedFormatResult":
        """Report that no compatible provider was available for a region."""
        return cls(
            status=EmbeddedResultStatus.UNAVAILABLE,
            plan_id=plan_id,
            region_id=region_id,
            message=message,
        )

    @classmethod
    def error(
        cls,
        plan_id: str,
        region_id: str,
        message: str,
    ) -> "EmbeddedFormatResult":
        """Report a provider failure that must reject the complete plan."""
        return cls(
            status=EmbeddedResultStatus.ERROR,
            plan_id=plan_id,
            region_id=region_id,
            message=message,
        )


@dataclass(frozen=True, slots=True)
class EmbeddedFormatOutcome:
    """Atomically composed source plus provider notices and identities."""

    source: str
    notices: tuple[EmbeddedFormatNotice, ...]
    providers: tuple[str, ...]


def format_template(
    source: str,
    *,
    options: _rust.template_parser.ParseOptions | None = None,
) -> str:
    """
    Format authored Citry template text without loading an application.

    Args:
        source: Complete Citry template text.
        options: Low-level parser options. Host-template adapters use this to
            identify foreign source spans. The formatter preserves those bytes
            as unknown syntax and does not format inside them.

    Returns:
        The formatted template.

    Raises:
        TemplateFormatError: If the template is invalid or cannot be formatted
            while preserving the formatter invariants.

    """
    return _rust.template_formatter.format_template(source, options=options)


def python_expression_provider() -> str:
    """Return the pinned identity of the built-in Python expression formatter."""
    return _rust.template_formatter.python_expression_provider()


def _notice_from_rust(
    raw: tuple[str, str, str | None, str | None],
) -> EmbeddedFormatNotice:
    code, message, region_id, language = raw
    return EmbeddedFormatNotice(
        code=code,
        message=message,
        region_id=region_id,
        language=EmbeddedLanguage(language) if language is not None else None,
    )


def prepare_embedded_format(source: str) -> EmbeddedFormatPlan:
    """
    Format Citry structure and discover safe JavaScript and CSS regions.

    The returned plan is bound to its exact ``formatted_source``. Provider
    work may happen asynchronously, but replies must be finished against this
    same plan.
    """
    handle = _rust.template_formatter.prepare_embedded_format(source)
    requests = tuple(
        EmbeddedFormatRequest(
            id=region_id,
            language=EmbeddedLanguage(language),
            kind=EmbeddedRegionKind(kind),
            source=region_source,
            virtual_source=virtual_source,
            byte_range=byte_range,
            base_indent=base_indent,
            newline=newline,
        )
        for (
            region_id,
            language,
            kind,
            region_source,
            virtual_source,
            byte_range,
            base_indent,
            newline,
        ) in handle.requests
    )
    return EmbeddedFormatPlan(
        id=handle.id,
        formatted_source=handle.formatted_source,
        requests=requests,
        notices=tuple(_notice_from_rust(notice) for notice in handle.notices),
        _handle=handle,
    )


def finish_embedded_format(
    plan: EmbeddedFormatPlan,
    results: Sequence[EmbeddedFormatResult],
) -> EmbeddedFormatOutcome:
    """
    Validate provider replies and atomically compose a prepared plan.

    Raises:
        TemplateFormatError: If results are missing, duplicated, stale, or
            contain output that is unsafe to place back in the Citry template.

    """
    raw_results = [
        (
            result.status.value,
            result.plan_id,
            result.region_id,
            result.text,
            result.provider,
            result.message,
        )
        for result in results
    ]
    source, notices, providers = _rust.template_formatter.finish_embedded_format(
        plan._handle,
        raw_results,
    )
    return EmbeddedFormatOutcome(
        source=source,
        notices=tuple(_notice_from_rust(notice) for notice in notices),
        providers=tuple(providers),
    )


__all__ = [
    "EmbeddedFormatNotice",
    "EmbeddedFormatOutcome",
    "EmbeddedFormatPlan",
    "EmbeddedFormatRequest",
    "EmbeddedFormatResult",
    "EmbeddedLanguage",
    "EmbeddedRegionKind",
    "EmbeddedResultStatus",
    "TemplateFormatError",
    "finish_embedded_format",
    "format_template",
    "prepare_embedded_format",
    "python_expression_provider",
]
