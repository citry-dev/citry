"""Portable syntax for Citry's declarative browser translation binding."""

from __future__ import annotations

from dataclasses import dataclass

I18N_BINDING_ROOT = "$c-tr"
I18N_BINDING_PREFIX = f"{I18N_BINDING_ROOT}:"
I18N_BINDING_ATTRIBUTE_TARGETS = frozenset(
    {
        "alt",
        "aria-description",
        "aria-label",
        "aria-placeholder",
        "aria-roledescription",
        "aria-valuetext",
        "placeholder",
        "title",
    }
)


@dataclass(frozen=True, slots=True)
class I18nBindingName:
    """One fully validated ``$c-tr`` attribute name and its exact spans."""

    message: str
    output: str | None
    target: str | None
    message_start: int
    message_end: int
    output_start: int | None
    output_end: int | None
    target_start: int | None
    target_end: int | None


class I18nBindingNameError(ValueError):
    """A malformed Citry-owned translation-binding attribute name."""

    def __init__(self, message: str, *, start: int, end: int) -> None:
        super().__init__(message)
        self.start = start
        self.end = end


def looks_like_i18n_binding(name: str) -> bool:
    """Return whether ``name`` belongs to the reserved ``$c-tr`` family."""
    folded = name.lower()
    return folded == I18N_BINDING_ROOT or (
        folded.startswith(I18N_BINDING_ROOT)
        and len(folded) > len(I18N_BINDING_ROOT)
        and folded[len(I18N_BINDING_ROOT)] in {":", ".", "["}
    )


def parse_i18n_binding_name(name: str) -> I18nBindingName:
    """Parse the public ``$c-tr:message.output[target]`` spelling."""
    if not looks_like_i18n_binding(name):
        raise I18nBindingNameError(
            f"{name!r} is not a $c-tr directive.",
            start=0,
            end=max(1, len(name)),
        )
    if not name.startswith(I18N_BINDING_ROOT):
        raise I18nBindingNameError(
            f"Citry client directive names are lowercase; write {I18N_BINDING_ROOT!r}.",
            start=0,
            end=min(len(name), len(I18N_BINDING_ROOT)),
        )

    cursor = len(I18N_BINDING_ROOT)
    if cursor >= len(name) or name[cursor] != ":":
        raise I18nBindingNameError(
            "$c-tr requires ':' followed by a message ID.",
            start=cursor,
            end=min(len(name), cursor + 1),
        )
    cursor += 1
    message_start = cursor
    cursor = _identifier_end(name, cursor)
    if cursor == message_start:
        raise I18nBindingNameError(
            "$c-tr requires a non-empty message ID after ':'.",
            start=message_start,
            end=min(len(name), message_start + 1),
        )
    message = name[message_start:cursor]

    output: str | None = None
    output_start: int | None = None
    output_end: int | None = None
    if cursor < len(name) and name[cursor] == ".":
        cursor += 1
        output_start = cursor
        cursor = _identifier_end(name, cursor)
        if cursor == output_start:
            raise I18nBindingNameError(
                "$c-tr requires a non-empty Fluent attribute name after '.'.",
                start=output_start,
                end=min(len(name), output_start + 1),
            )
        output_end = cursor
        output = name[output_start:output_end]

    target: str | None = None
    target_start: int | None = None
    target_end: int | None = None
    if cursor < len(name) and name[cursor] == "[":
        cursor += 1
        target_start = cursor
        closing = name.find("]", cursor)
        if closing < 0:
            raise I18nBindingNameError(
                "$c-tr HTML target is missing its closing ']'.",
                start=max(0, cursor - 1),
                end=len(name),
            )
        target_end = closing
        target = name[target_start:target_end]
        if not target:
            raise I18nBindingNameError(
                "$c-tr requires a non-empty HTML attribute name inside '[' and ']'.",
                start=target_start,
                end=min(len(name), target_start + 1),
            )
        if not _identifier(target):
            raise I18nBindingNameError(
                f"Malformed $c-tr HTML target {target!r}.",
                start=target_start,
                end=target_end,
            )
        if target != target.lower() or target not in I18N_BINDING_ATTRIBUTE_TARGETS:
            allowed = ", ".join(sorted(I18N_BINDING_ATTRIBUTE_TARGETS))
            raise I18nBindingNameError(
                f"$c-tr HTML target {target!r} is not allowed; choose one of: {allowed}.",
                start=target_start,
                end=target_end,
            )
        cursor = closing + 1

    if cursor != len(name):
        raise I18nBindingNameError(
            f"Malformed $c-tr directive {name!r}.",
            start=cursor,
            end=len(name),
        )
    return I18nBindingName(
        message,
        output,
        target,
        message_start,
        message_start + len(message),
        output_start,
        output_end,
        target_start,
        target_end,
    )


def _identifier_end(value: str, start: int) -> int:
    if start >= len(value) or not _identifier_start(value[start]):
        return start
    cursor = start + 1
    while cursor < len(value) and _identifier_continue(value[cursor]):
        cursor += 1
    return cursor


def _identifier(value: str) -> bool:
    return bool(value) and _identifier_end(value, 0) == len(value)


def _identifier_start(char: str) -> bool:
    return char.isascii() and char.isalpha()


def _identifier_continue(char: str) -> bool:
    return _identifier_start(char) or char.isdigit() or char in {"-", "_"}


__all__ = [
    "I18N_BINDING_ATTRIBUTE_TARGETS",
    "I18N_BINDING_PREFIX",
    "I18N_BINDING_ROOT",
    "I18nBindingName",
    "I18nBindingNameError",
    "looks_like_i18n_binding",
    "parse_i18n_binding_name",
]
