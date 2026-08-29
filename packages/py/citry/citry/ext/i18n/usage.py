"""
Render-scoped i18n operation metadata.

The records in this module describe which message outputs and named profiles a
render used. They never contain call arguments, input text, or resolved output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .bindings import I18nBindingCollector
    from .context import LocaleContext

EXTRA_KEY = "i18n"
CLIENT_CONTEXT_KEY = "citry_i18n_client"
AMBIENT_CLIENT_OWNER = "\0ambient"


@dataclass(frozen=True, slots=True)
class MessageOutputUse:
    """One public message value or attribute used by a render."""

    message: str
    attr: str | None


@dataclass(frozen=True, slots=True)
class ProfileUse:
    """One named formatter or parser profile used by a render."""

    operation: str
    profile: str


class I18nUsageCollector:
    """Insertion-ordered, render-local i18n operation set."""

    __slots__ = ("_formats", "_messages", "_parsers")

    def __init__(self) -> None:
        self._messages: dict[tuple[str, str | None], None] = {}
        self._formats: dict[tuple[str, str], None] = {}
        self._parsers: dict[tuple[str, str], None] = {}

    @property
    def messages(self) -> tuple[MessageOutputUse, ...]:
        return tuple(MessageOutputUse(message=message, attr=attr) for message, attr in self._messages)

    @property
    def formats(self) -> tuple[ProfileUse, ...]:
        return tuple(ProfileUse(operation=operation, profile=profile) for operation, profile in self._formats)

    @property
    def parsers(self) -> tuple[ProfileUse, ...]:
        return tuple(ProfileUse(operation=operation, profile=profile) for operation, profile in self._parsers)

    @property
    def empty(self) -> bool:
        return not (self._messages or self._formats or self._parsers)

    def record_message(self, message: str, attr: str | None) -> None:
        # A render records many repeated translation calls, so retain the
        # lightweight key and build public records only when metadata is read.
        self._messages[(message, attr)] = None

    def record_profile(
        self,
        kind: Literal["format", "parse"],
        operation: str,
        profile: str,
    ) -> None:
        target = self._formats if kind == "format" else self._parsers
        target[(operation, profile)] = None


@dataclass(frozen=True, slots=True)
class ProviderFieldPolicy:
    """How one nested browser-provider field follows its parent."""

    mode: Literal["clear", "explicit", "inherit"]
    value: str | None = None


@dataclass(frozen=True, slots=True)
class ClientProviderUse:
    """One client-enabled ``<c-i18n>`` boundary emitted by a render."""

    context: LocaleContext
    parent: str | None
    locale: ProviderFieldPolicy
    direction: ProviderFieldPolicy
    time_zone: ProviderFieldPolicy


@dataclass(frozen=True, slots=True)
class I18nRenderRecord:
    """The i18n metadata owned by one rendered component instance."""

    render_id: str
    class_id: str
    server_usage: I18nUsageCollector
    client_outputs: tuple[MessageOutputUse, ...]
    client_messages: tuple[str, ...]
    bindings: I18nBindingCollector
    client_owner: str | None = None
    provider: ClientProviderUse | None = None
    client_barrier: bool = False


__all__ = [
    "AMBIENT_CLIENT_OWNER",
    "CLIENT_CONTEXT_KEY",
    "EXTRA_KEY",
    "ClientProviderUse",
    "I18nRenderRecord",
    "I18nUsageCollector",
    "MessageOutputUse",
    "ProfileUse",
    "ProviderFieldPolicy",
]
