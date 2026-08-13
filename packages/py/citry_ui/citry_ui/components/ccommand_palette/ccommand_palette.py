"""Styled modal Command Palette component family."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any, ClassVar, Literal, TypeAlias, TypedDict, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._active_descendant import ACTIVE_DESCENDANT_RUNTIME_DEPENDENCY
from citry_ui.components._anchored_layer import ANCHORED_LAYER_RUNTIME_DEPENDENCY
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._dialog_controller import DIALOG_CONTROLLER_RUNTIME_DEPENDENCY
from citry_ui.components._i18n import uses_catalog_default

CCommandPaletteIntent = Literal["default", "danger"]
CCommandPaletteSize = Literal["sm", "md", "lg"]
CCommandPaletteActionSource = Literal["keyboard", "click"]
CCommandPaletteOpenReason = Literal[
    "trigger",
    "escape",
    "outside",
    "close-button",
    "action",
    "native",
    "disabled",
    "ancestor",
    "owner",
]
CCommandPaletteQueryReason = Literal["input", "close"]


@dataclass(frozen=True, slots=True)
class CCommandPaletteCommand:
    value: str
    label: str
    description: str | None = None
    keywords: tuple[str, ...] = ()
    shortcut: str | None = None
    disabled: bool = False
    close_on_action: bool | None = None
    intent: CCommandPaletteIntent = "default"


@dataclass(frozen=True, slots=True)
class CCommandPaletteGroup:
    label: str
    commands: tuple[CCommandPaletteCommand, ...]


@dataclass(frozen=True, slots=True)
class CCommandPaletteSeparator:
    pass


CCommandPaletteEntry: TypeAlias = CCommandPaletteCommand | CCommandPaletteGroup | CCommandPaletteSeparator


@dataclass(frozen=True, slots=True)
class CCommandPaletteItemSlotData:
    value: str
    label: str
    description: str | None
    keywords: tuple[str, ...]
    shortcut: str | None
    disabled: bool
    close_on_action: bool
    intent: CCommandPaletteIntent


class CCommandPaletteOpenChangeDetail(TypedDict):
    reason: CCommandPaletteOpenReason
    controlled: bool
    source: object | None


class CCommandPaletteQueryChangeDetail(TypedDict):
    reason: CCommandPaletteQueryReason
    closeReason: CCommandPaletteOpenReason | None
    controlled: bool
    source: object | None


class CCommandPaletteActionDetail(TypedDict):
    query: str
    source: CCommandPaletteActionSource
    item: object
    event: object
    closeOnAction: bool


class _CCommandPaletteActivatorSlotData:
    activator_attrs: dict[str, object]
    activator_disabled: bool


class _CCommandPaletteEmptySlotData:
    pass


@dataclass(frozen=True, slots=True)
class _ResolvedCommand:
    value: str
    label: str
    description: str | None
    keywords: tuple[str, ...]
    shortcut: str | None
    disabled: bool
    close_on_action: bool
    close_on_action_override: bool | None
    intent: CCommandPaletteIntent
    option_id: str
    label_id: str
    description_id: str | None
    slot_data: CCommandPaletteItemSlotData


@dataclass(frozen=True, slots=True)
class _ResolvedEntry:
    kind: Literal["command", "group", "separator"]
    region_index: int
    command: _ResolvedCommand | None = None
    group_label: str | None = None
    group_id: str | None = None
    group_label_id: str | None = None
    commands: tuple[_ResolvedCommand, ...] = ()


_RUNTIME_PREFIXES = (
    "data-citry-",
    "data-cev",
    "data-cid",
    "data-has-alpine-state",
    "x-citry-",
)
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "$c-props",
        "c-bind",
        "c-props",
        "x-bind",
        "x-data",
        "x-effect",
        "x-for",
        "x-html",
        "x-id",
        "x-if",
        "x-ignore",
        "x-init",
        "x-model",
        "x-modelable",
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_DIALOG_OWNED = frozenset(
    {
        "aria-describedby",
        "aria-label",
        "aria-labelledby",
        "aria-modal",
        "closedby",
        "data-citry-command-palette-initialized",
        "data-citry-command-palette-root",
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-open",
        "data-size",
        "hidden",
        "id",
        "inert",
        "open",
        "popover",
        "role",
        "tabindex",
    }
)
_INPUT_OWNED = frozenset(
    {
        "aria-activedescendant",
        "aria-autocomplete",
        "aria-controls",
        "aria-expanded",
        "aria-label",
        "aria-labelledby",
        "autocomplete",
        "autofocus",
        "data-citry-ui-part",
        "disabled",
        "form",
        "formaction",
        "formenctype",
        "formmethod",
        "formnovalidate",
        "formtarget",
        "id",
        "list",
        "name",
        "placeholder",
        "readonly",
        "required",
        "role",
        "tabindex",
        "type",
        "value",
    }
)
_DIALOG_EVENTS = frozenset({"cancel", "click", "close", "keydown", "pointercancel", "pointerdown", "submit"})
_INPUT_EVENTS = frozenset({"beforeinput", "compositionend", "compositionstart", "input", "keydown"})


def _plain_string(
    component: str,
    field: str,
    value: object,
    *,
    optional: bool = False,
    allow_empty: bool = False,
    require_text: bool = False,
) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        raise TypeError(f"{component} {field} must be {expected}.")
    plain = "".join(raw)
    if any(ord(character) < 32 or ord(character) == 127 for character in plain):
        raise ValueError(f"{component} {field} cannot contain ASCII controls.")
    if not allow_empty and not plain:
        raise ValueError(f"{component} {field} must be non-empty.")
    if require_text and not plain.strip():
        raise ValueError(f"{component} {field} must contain non-whitespace text.")
    return plain


def _plain_bool(component: str, field: str, value: object) -> bool:
    raw = const_value(value)
    if not isinstance(raw, bool):
        raise TypeError(f"{component} {field} must be a bool.")
    return bool(raw)


def _plain_choice(component: str, field: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = cast("str", _plain_string(component, field, value))
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"{component} {field} must be one of {expected}.")
    return plain


def _dynamic_target(name: str) -> str | None:
    if name.startswith("x-bind:"):
        return name.removeprefix("x-bind:").split(".", 1)[0]
    if name.startswith((":", ".")):
        return name[1:].split(".", 1)[0]
    return None


def _event_target(name: str) -> str | None:
    if name.startswith("x-on:"):
        return name.removeprefix("x-on:").split(".", 1)[0]
    if name.startswith("@"):
        return name[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    value: Mapping[str, object] | None,
    *,
    destination: str,
    owned: frozenset[str],
    owned_events: frozenset[str],
    reject_all_aria: bool,
) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CCommandPalette {destination} must be a mapping or None.")
    copied = dict(value or {})
    seen: set[str] = set()
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CCommandPalette {destination} requires string attribute names.")
        normalized = key.casefold()
        if normalized in seen:
            raise ValueError(f"CCommandPalette {destination} cannot contain duplicate case variants.")
        seen.add(normalized)
        directive = normalized.split(".", 1)[0]
        target = _dynamic_target(normalized)
        event = _event_target(normalized)
        if (
            normalized in owned
            or normalized.startswith(_RUNTIME_PREFIXES)
            or (reject_all_aria and normalized.startswith("aria-"))
        ):
            raise ValueError(f"CCommandPalette {destination} cannot override owned attributes.")
        if directive in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CCommandPalette {destination} cannot use ownership directives.")
        if normalized.startswith("on"):
            raise ValueError(f"CCommandPalette {destination} cannot use raw event attributes.")
        if event in owned_events:
            raise ValueError(f"CCommandPalette {destination} cannot override owned events.")
        if target is not None and (
            target in owned or target.startswith(_RUNTIME_PREFIXES) or (reject_all_aria and target.startswith("aria-"))
        ):
            raise ValueError(f"CCommandPalette {destination} cannot dynamically bind owned attributes.")
    return copied


class _VisualParser(HTMLParser):
    _VOID: ClassVar[set[str]] = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.html_depth = 0
        self.host_depth: int | None = None
        self.dialog_count = 0
        self.activators: list[dict[str, str | None]] = []
        self.invalid = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if self.host_depth is None and "data-citry-command-palette-host" in values:
            self.host_depth = self.html_depth
        elif self.host_depth is not None and self.html_depth == self.host_depth + 1:
            if tag == "dialog" and "data-citry-command-palette-root" in values:
                self.dialog_count += 1
            else:
                self.activators.append(values)
                if "-" in tag or "is" in values or "data-citry-command-palette-trigger" not in values:
                    self.invalid = True
        if self.depth == 0:
            if "data-citry-command-palette-visual" in values:
                self.depth = 1
        elif tag not in self._VOID:
            self.depth += 1
        if self.depth and (
            "-" in tag
            or "is" in values
            or tag
            in {
                "button",
                "details",
                "embed",
                "iframe",
                "input",
                "label",
                "object",
                "select",
                "textarea",
                "summary",
            }
            or (tag == "a" and "href" in values)
            or (tag == "area" and "href" in values)
            or (tag == "img" and ("alt" not in values or values.get("alt") not in {None, ""}))
            or (tag in {"audio", "video"} and "controls" in values)
            or "tabindex" in values
            or ("contenteditable" in values and (values["contenteditable"] or "").casefold() != "false")
        ):
            self.invalid = True
        if tag not in self._VOID:
            self.html_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        previous = self.depth
        self.handle_starttag(tag, attrs)
        self.depth = previous

    def handle_endtag(self, tag: str) -> None:
        if tag not in self._VOID:
            self.html_depth -= 1
        if self.depth:
            self.depth -= 1


class CCommandPalette(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        entries: Sequence[CCommandPaletteEntry]
        label: str
        id: str | None = None
        open: bool = False
        query: str = ""
        disabled: bool = False
        loop: bool = True
        close_on_action: bool = True
        size: CCommandPaletteSize = "md"
        placeholder: str = "Search commands"
        search_label: str = "Search commands"
        empty_label: str = "No commands found"
        close_label: str = "Close command palette"
        onOpenChange: Any | None = None  # noqa: N815
        onQueryChange: Any | None = None  # noqa: N815
        onAction: Any | None = None  # noqa: N815
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        activator: SlotInput[_CCommandPaletteActivatorSlotData] | None = None
        item_start: SlotInput[CCommandPaletteItemSlotData] | None = None
        item_end: SlotInput[CCommandPaletteItemSlotData] | None = None
        empty: SlotInput[_CCommandPaletteEmptySlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_command_palette_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)

        label = cast("str", _plain_string("CCommandPalette", "label", kwargs.label, require_text=True))
        root_id = (
            f"cui-command-palette-{self.id}"
            if kwargs.id is None
            else cast("str", _plain_string("CCommandPalette", "id", kwargs.id))
        )
        if any(character in "\t\n\f\r " for character in root_id):
            raise ValueError("CCommandPalette id cannot contain ASCII whitespace.")
        query = cast("str", _plain_string("CCommandPalette", "query", kwargs.query, allow_empty=True))
        open_value = _plain_bool("CCommandPalette", "open", kwargs.open)
        disabled = _plain_bool("CCommandPalette", "disabled", kwargs.disabled)
        loop = _plain_bool("CCommandPalette", "loop", kwargs.loop)
        close_on_action = _plain_bool("CCommandPalette", "close_on_action", kwargs.close_on_action)
        size = cast(
            "CCommandPaletteSize",
            _plain_choice("CCommandPalette", "size", kwargs.size, ("sm", "md", "lg")),
        )
        placeholder_value = (
            kwargs.placeholder
            if "placeholder" in self.raw_kwargs
            else self.i18n.tr("citry-ui-command-palette-placeholder")
        )
        placeholder = cast(
            "str",
            _plain_string("CCommandPalette", "placeholder", placeholder_value, allow_empty=True),
        )
        search_label_value = (
            kwargs.search_label
            if "search_label" in self.raw_kwargs
            else self.i18n.tr("citry-ui-command-palette-search-label")
        )
        search_label = cast(
            "str",
            _plain_string("CCommandPalette", "search_label", search_label_value, require_text=True),
        )
        empty_label_value = (
            kwargs.empty_label if "empty_label" in self.raw_kwargs else self.i18n.tr("citry-ui-command-palette-empty")
        )
        empty_label = cast(
            "str",
            _plain_string("CCommandPalette", "empty_label", empty_label_value, require_text=True),
        )
        close_label_value = (
            kwargs.close_label if "close_label" in self.raw_kwargs else self.i18n.tr("citry-ui-command-palette-close")
        )
        close_label = cast(
            "str",
            _plain_string("CCommandPalette", "close_label", close_label_value, require_text=True),
        )
        if isinstance(kwargs.entries, (str, bytes, bytearray)) or not isinstance(kwargs.entries, Sequence):
            raise TypeError("CCommandPalette entries must be a sequence of Command Palette records.")
        entries = tuple(kwargs.entries)
        if entries and isinstance(entries[0], CCommandPaletteSeparator):
            raise ValueError("CCommandPalette separators cannot be first.")
        if entries and isinstance(entries[-1], CCommandPaletteSeparator):
            raise ValueError("CCommandPalette separators cannot be last.")

        seen_values: set[str] = set()
        command_index = 0
        previous_separator = False
        resolved_entries: list[_ResolvedEntry] = []
        browser_regions: list[dict[str, object]] = []

        def resolve_command(command: object) -> _ResolvedCommand:
            nonlocal command_index
            if not isinstance(command, CCommandPaletteCommand):
                raise TypeError("CCommandPalette groups may contain only CCommandPaletteCommand records.")
            value = cast("str", _plain_string("CCommandPaletteCommand", "value", command.value, require_text=True))
            command_label = cast(
                "str",
                _plain_string("CCommandPaletteCommand", "label", command.label, require_text=True),
            )
            description = cast(
                "str | None",
                _plain_string(
                    "CCommandPaletteCommand",
                    "description",
                    command.description,
                    optional=True,
                    require_text=True,
                ),
            )
            shortcut = cast(
                "str | None",
                _plain_string(
                    "CCommandPaletteCommand",
                    "shortcut",
                    command.shortcut,
                    optional=True,
                    require_text=True,
                ),
            )
            if isinstance(command.keywords, (str, bytes, bytearray)) or not isinstance(command.keywords, Sequence):
                raise TypeError("CCommandPaletteCommand keywords must be a sequence of strings.")
            keywords = tuple(
                cast(
                    "str",
                    _plain_string(
                        "CCommandPaletteCommand",
                        f"keywords[{index}]",
                        keyword,
                        require_text=True,
                    ),
                )
                for index, keyword in enumerate(command.keywords)
            )
            command_disabled = _plain_bool("CCommandPaletteCommand", "disabled", command.disabled)
            command_close = (
                close_on_action
                if command.close_on_action is None
                else _plain_bool("CCommandPaletteCommand", "close_on_action", command.close_on_action)
            )
            intent = cast(
                "CCommandPaletteIntent",
                _plain_choice("CCommandPaletteCommand", "intent", command.intent, ("default", "danger")),
            )
            if value in seen_values:
                raise ValueError("CCommandPalette command values must be globally unique.")
            seen_values.add(value)
            digest = sha256(value.encode()).hexdigest()[:12]
            option_id = f"{root_id}-command-{command_index}-{digest}"
            label_id = f"{option_id}-label"
            description_id = f"{option_id}-description" if description is not None else None
            command_index += 1
            slot_data = CCommandPaletteItemSlotData(
                value=value,
                label=command_label,
                description=description,
                keywords=keywords,
                shortcut=shortcut,
                disabled=command_disabled,
                close_on_action=command_close,
                intent=intent,
            )
            return _ResolvedCommand(
                value=value,
                label=command_label,
                description=description,
                keywords=keywords,
                shortcut=shortcut,
                disabled=command_disabled,
                close_on_action=command_close,
                close_on_action_override=command.close_on_action,
                intent=intent,
                option_id=option_id,
                label_id=label_id,
                description_id=description_id,
                slot_data=slot_data,
            )

        for region_index, entry in enumerate(entries):
            if isinstance(entry, CCommandPaletteSeparator):
                if previous_separator:
                    raise ValueError("CCommandPalette separators cannot be consecutive.")
                previous_separator = True
                resolved_entries.append(_ResolvedEntry(kind="separator", region_index=region_index))
                browser_regions.append({"kind": "separator", "index": region_index, "commands": []})
                continue
            previous_separator = False
            if isinstance(entry, CCommandPaletteCommand):
                resolved = resolve_command(entry)
                resolved_entries.append(_ResolvedEntry(kind="command", region_index=region_index, command=resolved))
                browser_regions.append(
                    {"kind": "command", "index": region_index, "commands": [self._browser_command(resolved)]}
                )
                continue
            if not isinstance(entry, CCommandPaletteGroup):
                raise TypeError("CCommandPalette entries must use Command, Group, or Separator records.")
            group_label = cast(
                "str",
                _plain_string("CCommandPaletteGroup", "label", entry.label, require_text=True),
            )
            if isinstance(entry.commands, (str, bytes, bytearray)) or not isinstance(entry.commands, Sequence):
                raise TypeError("CCommandPaletteGroup commands must be a sequence of command records.")
            group_commands = tuple(resolve_command(command) for command in tuple(entry.commands))
            if not group_commands:
                raise ValueError("CCommandPalette groups must contain at least one command.")
            group_id = f"{root_id}-group-{region_index}"
            group_label_id = f"{group_id}-label"
            resolved_entries.append(
                _ResolvedEntry(
                    kind="group",
                    region_index=region_index,
                    group_label=group_label,
                    group_id=group_id,
                    group_label_id=group_label_id,
                    commands=group_commands,
                )
            )
            browser_regions.append(
                {
                    "kind": "group",
                    "index": region_index,
                    "commands": [self._browser_command(command) for command in group_commands],
                }
            )
        if command_index > 500:
            raise ValueError("CCommandPalette accepts at most 500 commands.")

        structural = {
            "label": label,
            "placeholder": placeholder,
            "searchLabel": search_label,
            "emptyLabel": empty_label,
            "closeLabel": close_label,
            "regions": browser_regions,
        }
        fingerprint = sha256(
            json.dumps(structural, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        cached = {
            "label": label,
            "root_id": root_id,
            "dialog_id": root_id,
            "title_id": f"{root_id}-title",
            "input_id": f"{root_id}-input",
            "listbox_id": f"{root_id}-listbox",
            "open": open_value and not disabled,
            "query": query,
            "disabled": disabled,
            "loop": loop,
            "close_on_action": close_on_action,
            "size": size,
            "placeholder": placeholder,
            "search_label": search_label,
            "empty_label": empty_label,
            "close_label": close_label,
            "catalog_placeholder": uses_catalog_default(self, "placeholder"),
            "catalog_search_label": uses_catalog_default(self, "search_label"),
            "catalog_empty_label": uses_catalog_default(self, "empty_label") and "empty" not in self.raw_slots,
            "catalog_close_label": uses_catalog_default(self, "close_label"),
            "entries": tuple(resolved_entries),
            "regions": browser_regions,
            "fingerprint": fingerprint,
        }
        self._cui_command_palette_snapshot = cached
        return cached

    @staticmethod
    def _browser_command(command: _ResolvedCommand) -> dict[str, object]:
        return {
            "value": command.value,
            "label": command.label,
            "description": command.description,
            "keywords": command.keywords,
            "shortcut": command.shortcut,
            "disabled": command.disabled,
            "closeOnAction": command.close_on_action_override,
            "intent": command.intent,
            "id": command.option_id,
        }

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        data = dict(self._snapshot(kwargs))
        attrs = merge_root_attrs(
            _copy_attrs(
                kwargs.attrs,
                destination="attrs",
                owned=_DIALOG_OWNED,
                owned_events=_DIALOG_EVENTS,
                reject_all_aria=True,
            ),
            kwargs.class_,
            kwargs.style,
        )
        input_attrs = _copy_attrs(
            kwargs.input_attrs,
            destination="input_attrs",
            owned=_INPUT_OWNED,
            owned_events=_INPUT_EVENTS,
            reject_all_aria=True,
        )
        data.update(
            {
                "attrs": attrs,
                "input_attrs": input_attrs,
                "has_activator": "activator" in self.raw_slots,
                "has_item_start": "item_start" in self.raw_slots,
                "has_item_end": "item_end" in self.raw_slots,
                "has_empty": "empty" in self.raw_slots,
                "activator_attrs": {
                    "aria-haspopup": "dialog",
                    "aria-controls": data["dialog_id"],
                    "aria-expanded": "true" if data["open"] else "false",
                    "data-citry-command-palette-trigger": "",
                },
                "activator_disabled": data["disabled"],
                "label_attrs": {"for": data["input_id"]},
                "aria_expanded": "true" if data["open"] else "false",
            }
        )
        return data

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        data = self._snapshot(kwargs)
        return {
            "open": data["open"],
            "query": data["query"],
            "disabled": data["disabled"],
            "loop": data["loop"],
            "closeOnAction": data["close_on_action"],
            "size": data["size"],
            "regions": data["regions"],
            "fingerprint": data["fingerprint"],
            "hasActivator": "activator" in self.raw_slots,
            "dialogId": data["dialog_id"],
            "titleId": data["title_id"],
            "inputId": data["input_id"],
            "listboxId": data["listbox_id"],
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CCommandPalette completed without a render result.")
        parser = _VisualParser()
        parser.feed(rendered.serialize(deps_strategy="ignore"))
        parser.close()
        snapshot = cast("dict[str, object]", self._cui_command_palette_snapshot)
        has_activator = "activator" in self.raw_slots
        activator_valid = len(parser.activators) == int(has_activator)
        if has_activator and parser.activators:
            activator = parser.activators[0]
            activator_valid = activator_valid and (
                activator.get("aria-haspopup") == "dialog"
                and activator.get("aria-controls") == snapshot["dialog_id"]
                and activator.get("aria-expanded") == ("true" if snapshot["open"] else "false")
            )
        if parser.invalid or parser.dialog_count != 1 or not activator_valid:
            raise ValueError("CCommandPalette visual slots cannot contain interactive content.")

    template = """
      <span
        class="cui-command-palette-host"
        data-citry-command-palette-host
      >
        <c-if cond="has_activator">
          <c-slot
            name="activator"
            c-activator_attrs="activator_attrs"
            c-activator_disabled="activator_disabled"
          />
        </c-if>
        <dialog
          class="cui-command-palette"
          c-id="dialog_id"
          c-open="open"
          c-aria-labelledby="title_id"
          c-data-open="open"
          c-data-disabled="disabled"
          c-data-size="size"
          c-bind="attrs"
          data-citry-command-palette-root
          data-citry-ui-part="command-palette"
        >
          <section
            class="cui-command-palette__surface"
            data-citry-ui-part="command-palette-surface"
          >
            <header
              class="cui-command-palette__header"
              data-citry-ui-part="command-palette-header"
            >
              <h2
                c-id="title_id"
                data-citry-ui-part="command-palette-title"
              >
                {{ label }}
              </h2>
              <button
                type="button"
                c-aria-label="tr('citry-ui-command-palette-close') if catalog_close_label else close_label"
                c-$c-tr:citry-ui-command-palette-close[aria-label]="True if catalog_close_label else None"
                data-citry-command-palette-close
                data-citry-ui-part="command-palette-close"
              >
                <span aria-hidden="true">&times;</span>
              </button>
            </header>
            <search data-citry-ui-part="command-palette-search">
              <label
                class="cui-command-palette__visually-hidden"
                c-bind="label_attrs"
                data-citry-ui-part="command-palette-search-label"
              >
                <span
                  c-$c-tr:citry-ui-command-palette-search-label="True if catalog_search_label else None"
                >{{ tr('citry-ui-command-palette-search-label') if catalog_search_label else search_label }}</span>
              </label>
              <input
                c-bind="input_attrs"
                c-id="input_id"
                type="text"
                role="combobox"
                autocomplete="off"
                autofocus
                disabled
                c-value="query"
                c-placeholder="tr('citry-ui-command-palette-placeholder') if catalog_placeholder else placeholder"
                c-$c-tr:citry-ui-command-palette-placeholder[placeholder]="True if catalog_placeholder else None"
                c-aria-controls="listbox_id"
                c-aria-expanded="aria_expanded"
                aria-autocomplete="list"
                data-citry-ui-part="command-palette-input"
              />
            </search>
            <div
              c-id="listbox_id"
              role="listbox"
              data-citry-ui-part="command-palette-listbox"
            >
              <c-for each="entry in entries">
                <c-if cond="entry.kind == 'command'">
                  <div
                    c-id="entry.command.option_id"
                    role="option"
                    aria-selected="false"
                    c-aria-labelledby="entry.command.label_id"
                    c-aria-describedby="entry.command.description_id"
                    c-aria-disabled="'true' if entry.command.disabled else None"
                    c-data-value="entry.command.value"
                    c-data-disabled="entry.command.disabled"
                    c-data-intent="entry.command.intent"
                    c-data-region-index="entry.region_index"
                    data-citry-ui-part="command-palette-command"
                  >
                    <c-if cond="has_item_start">
                      <span
                        inert
                        aria-hidden="true"
                        data-citry-command-palette-visual
                        data-citry-ui-part="command-palette-item-start"
                      >
                        <c-slot
                          name="item_start"
                          c-value="entry.command.slot_data.value"
                          c-label="entry.command.slot_data.label"
                          c-description="entry.command.slot_data.description"
                          c-keywords="entry.command.slot_data.keywords"
                          c-shortcut="entry.command.slot_data.shortcut"
                          c-disabled="entry.command.slot_data.disabled"
                          c-close_on_action="entry.command.slot_data.close_on_action"
                          c-intent="entry.command.slot_data.intent"
                        />
                      </span>
                    </c-if>
                    <span c-id="entry.command.label_id">
                      {{ entry.command.label }}
                    </span>
                    <c-if cond="entry.command.description is not None">
                      <span
                        class="cui-command-palette__description"
                        c-id="entry.command.description_id"
                      >
                        {{ entry.command.description }}
                      </span>
                    </c-if>
                    <c-if cond="has_item_end">
                      <span
                        inert
                        aria-hidden="true"
                        data-citry-command-palette-visual
                        data-citry-ui-part="command-palette-item-end"
                      >
                        <c-slot
                          name="item_end"
                          c-value="entry.command.slot_data.value"
                          c-label="entry.command.slot_data.label"
                          c-description="entry.command.slot_data.description"
                          c-keywords="entry.command.slot_data.keywords"
                          c-shortcut="entry.command.slot_data.shortcut"
                          c-disabled="entry.command.slot_data.disabled"
                          c-close_on_action="entry.command.slot_data.close_on_action"
                          c-intent="entry.command.slot_data.intent"
                        />
                      </span>
                    </c-if>
                    <c-elif cond="entry.command.shortcut is not None">
                      <span
                        class="cui-command-palette__shortcut"
                        inert
                        aria-hidden="true"
                        data-citry-ui-part="command-palette-item-end"
                      >
                        {{ entry.command.shortcut }}
                      </span>
                    </c-elif>
                  </div>
                </c-if>
                <c-elif cond="entry.kind == 'group'">
                  <section
                    c-id="entry.group_id"
                    role="group"
                    c-aria-labelledby="entry.group_label_id"
                    c-data-region-index="entry.region_index"
                    data-citry-ui-part="command-palette-group"
                  >
                    <div
                      c-id="entry.group_label_id"
                      data-citry-ui-part="command-palette-group-label"
                    >
                      {{ entry.group_label }}
                    </div>
                    <div
                      c-for="command in entry.commands"
                      c-id="command.option_id"
                      role="option"
                      aria-selected="false"
                      c-aria-labelledby="command.label_id"
                      c-aria-describedby="command.description_id"
                      c-aria-disabled="'true' if command.disabled else None"
                      c-data-value="command.value"
                      c-data-disabled="command.disabled"
                      c-data-intent="command.intent"
                      data-citry-ui-part="command-palette-command"
                    >
                      <c-if cond="has_item_start">
                        <span
                          inert
                          aria-hidden="true"
                          data-citry-command-palette-visual
                          data-citry-ui-part="command-palette-item-start"
                        >
                          <c-slot
                            name="item_start"
                            c-value="command.slot_data.value"
                            c-label="command.slot_data.label"
                            c-description="command.slot_data.description"
                            c-keywords="command.slot_data.keywords"
                            c-shortcut="command.slot_data.shortcut"
                            c-disabled="command.slot_data.disabled"
                            c-close_on_action="command.slot_data.close_on_action"
                            c-intent="command.slot_data.intent"
                          />
                        </span>
                      </c-if>
                      <span c-id="command.label_id">
                        {{ command.label }}
                      </span>
                      <c-if cond="command.description is not None">
                      <span
                        class="cui-command-palette__description"
                        c-id="command.description_id"
                      >
                          {{ command.description }}
                        </span>
                      </c-if>
                      <c-if cond="has_item_end">
                        <span
                          inert
                          aria-hidden="true"
                          data-citry-command-palette-visual
                          data-citry-ui-part="command-palette-item-end"
                        >
                          <c-slot
                            name="item_end"
                            c-value="command.slot_data.value"
                            c-label="command.slot_data.label"
                            c-description="command.slot_data.description"
                            c-keywords="command.slot_data.keywords"
                            c-shortcut="command.slot_data.shortcut"
                            c-disabled="command.slot_data.disabled"
                            c-close_on_action="command.slot_data.close_on_action"
                            c-intent="command.slot_data.intent"
                          />
                        </span>
                      </c-if>
                      <c-elif cond="command.shortcut is not None">
                        <span
                          class="cui-command-palette__shortcut"
                          inert
                          aria-hidden="true"
                          data-citry-ui-part="command-palette-item-end"
                        >
                          {{ command.shortcut }}
                        </span>
                      </c-elif>
                    </div>
                  </section>
                </c-elif>
                <c-else>
                  <hr
                    aria-hidden="true"
                    c-data-region-index="entry.region_index"
                    data-citry-ui-part="command-palette-separator"
                  />
                </c-else>
              </c-for>
            </div>
            <div
              hidden
              role="status"
              data-citry-command-palette-visual
              data-citry-ui-part="command-palette-empty"
            >
              <c-slot name="empty">
                <span
                  c-$c-tr:citry-ui-command-palette-empty="True if catalog_empty_label else None"
                >{{ tr('citry-ui-command-palette-empty') if catalog_empty_label else empty_label }}</span>
              </c-slot>
            </div>
          </section>
        </dialog>
      </span>
    """

    js = r"""
      /* citry-ui:command-palette-attribution:initializer:begin */
      const readyAttribute = "data-citry-command-palette-initialized";
      const ownerKey = Symbol.for("citry-ui:command-palette-owner");
      const handoffKey = Symbol.for("citry-ui:command-palette-handoff");
      const scopeManagers = globalThis[
        Symbol.for("citry-ui:command-palette-mutation-scopes")
      ] ??= new WeakMap();

      const watchPalette = (root, entry) => {
        let scope;
        let manager;
        let active = true;
        const detach = () => {
          if (manager?.entries.get(root) !== entry) return;
          manager.entries.delete(root);
          if (manager.entries.size === 0) {
            manager.observer.disconnect();
            scopeManagers.delete(scope);
          }
        };
        const attach = () => {
          scope = root.getRootNode();
          manager = scopeManagers.get(scope);
          if (!manager) {
            const entries = new Map();
            const observer = new MutationObserver((records) => {
              for (const record of records) {
                for (const node of record.addedNodes) {
                  if (!(node instanceof Element)) continue;
                  const candidates = node.hasAttribute(readyAttribute)
                    ? [node, ...node.querySelectorAll(`[${readyAttribute}]`)]
                    : [...node.querySelectorAll(`[${readyAttribute}]`)];
                  for (const candidate of candidates) {
                    if (!candidate[ownerKey]?.active) {
                      candidate.removeAttribute(readyAttribute);
                      candidate.querySelector(":scope > dialog")?.removeAttribute("data-open");
                    }
                  }
                }
              }
              for (const [candidate, registration] of [...entries]) {
                if (records.some((record) => record.target === candidate
                  || candidate.contains(record.target)
                  || [...record.addedNodes, ...record.removedNodes].some((node) =>
                    node === candidate || node.contains?.(candidate)))) registration.notify();
              }
            });
            observer.observe(scope instanceof Document ? scope.documentElement : scope, {
              subtree: true,
              childList: true,
              attributes: true,
            });
            manager = { entries, observer };
            scopeManagers.set(scope, manager);
          }
          manager.entries.set(root, entry);
        };
        attach();
        return {
          refresh() {
            if (active && root.getRootNode() !== scope) {
              detach();
              attach();
            }
          },
          cleanup() {
            active = false;
            detach();
          },
        };
      };

      $component({
        props: {
          open: {},
          query: {},
          disabled: {},
          loop: {},
          closeOnAction: {},
          size: {},
          onOpenChange: {},
          onQueryChange: {},
          onAction: {},
        },
        init: ({ els, data, props, effect }) => {
          const host = els[0];
          const dialogRuntime = globalThis[Symbol.for("citry-ui:dialog-controller-runtime")];
          const activeRuntime = globalThis[Symbol.for("citry-ui:active-descendant-runtime")];
          if (dialogRuntime?.generation !== 1 || activeRuntime?.generation !== 1) {
            throw new Error("[citry-ui] CCommandPalette private runtime dependency did not load.");
          }
          const dialog = host.querySelector(
            ':scope > dialog[data-citry-command-palette-root]',
          );
          const surface = dialog?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-surface"]',
          );
          const header = surface?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-header"]',
          );
          const title = header?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-title"]',
          );
          const closeButton = header?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-close"]',
          );
          const search = surface?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-search"]',
          );
          const input = search?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-input"]',
          );
          const listbox = surface?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-listbox"]',
          );
          const empty = surface?.querySelector(
            ':scope > [data-citry-ui-part="command-palette-empty"]',
          );
          host?.[ownerKey]?.transfer?.();
          const previous = host?.[handoffKey] ?? null;
          if (previous?.timer !== null && previous?.timer !== undefined) {
            clearTimeout(previous.timer);
          }
          const abortPrevious = () => {
            if (!previous) return;
            if (previous.timer !== null) clearTimeout(previous.timer);
            previous.abort();
            if (host[handoffKey] === previous) delete host[handoffKey];
          };
          if (
            !(host instanceof HTMLSpanElement)
            || !(dialog instanceof HTMLDialogElement)
            || !(surface instanceof HTMLElement)
            || !(header instanceof HTMLElement)
            || !(title instanceof HTMLHeadingElement)
            || !(closeButton instanceof HTMLButtonElement)
            || !(search instanceof HTMLElement)
            || !(input instanceof HTMLInputElement)
            || !(listbox instanceof HTMLElement)
            || !(empty instanceof HTMLElement)
          ) {
            abortPrevious();
            console.error(
              "[citry-ui] CCommandPalette received invalid native anatomy; "
                + "leaving the server fallback unchanged.",
            );
            return () => {};
          }

          const flattened = data.regions.flatMap((region) => region.commands);
          const commandElements = [...listbox.querySelectorAll(
            '[data-citry-ui-part="command-palette-command"]',
          )];
          const optionByValue = new Map(commandElements.map((element) => [
            element.dataset.value,
            element,
          ]));
          const regionElements = [...listbox.children];
          const documentOwner = host.ownerDocument;
          let actualRoot = host.getRootNode();
          const activators = [...host.children].filter((element) => element !== dialog);
          const ownedElements = [
            host, dialog, surface, header, title, closeButton, search, input, listbox, empty,
            ...regionElements, ...commandElements,
          ];
          const frameworkMarker = (attribute) => attribute.name === "data-citry-root"
            || attribute.name === "data-has-alpine-state"
            || attribute.name.startsWith("data-cid")
            || attribute.name.startsWith("data-cev")
            || attribute.name.startsWith("x-citry-");
          const correlationValid = () => {
            const identifiers = (host.getAttribute("data-cid") ?? "").split(/\s+/).filter(Boolean);
            const markers = [...host.attributes]
              .filter((attribute) => attribute.name.startsWith("data-cid-"))
              .map((attribute) => attribute.name.slice(9));
            return host.getAttribute("data-citry-root") === ""
              && (!host.hasAttribute("data-has-alpine-state")
                || host.getAttribute("data-has-alpine-state") === "true")
              && (!host.hasAttribute("x-citry-boundary")
                || host.getAttribute("x-citry-boundary") === "")
              && identifiers.length === 1
              && markers.length === 1
              && markers[0] === identifiers[0]
              && ownedElements.slice(1).every((element) =>
                ![...element.attributes].some(frameworkMarker));
          };
          const frameworkBaseline = ownedElements.map((element) => JSON.stringify(
            [...element.attributes]
              .filter(frameworkMarker)
              .map((attribute) => [attribute.name, attribute.value])
              .sort(([left], [right]) => left.localeCompare(right)),
          ));
          const frameworkMarkersValid = () => ownedElements.every((element, index) => JSON.stringify(
            [...element.attributes]
              .filter(frameworkMarker)
              .map((attribute) => [attribute.name, attribute.value])
              .sort(([left], [right]) => left.localeCompare(right)),
          ) === frameworkBaseline[index]);
          const runtimeAttributesValid = (element, allowed = []) => [...element.attributes].every(
            (attribute) => !attribute.name.startsWith("data-citry-")
              || attribute.name === "data-citry-ui-part"
              || attribute.name === "data-citry-root"
              || allowed.includes(attribute.name),
          );
          const interactiveSelector = [
            "a[href]", "area[href]", "button", "details", "embed", "iframe", "input",
            "label", "object", "select", "summary", "textarea", "audio[controls]",
            "video[controls]", "[contenteditable]:not([contenteditable='false'])", "[tabindex]",
          ].join(",");
          const visualValid = (visual) => {
            if (!(visual instanceof Element)) return true;
            if (visual.querySelector(interactiveSelector)) return false;
            return [...visual.querySelectorAll("*")].every((element) => (
              !element.localName.includes("-")
              && !element.hasAttribute("is")
              && element.shadowRoot === null
              && (
                !(element instanceof HTMLImageElement)
                || (element.hasAttribute("alt") && element.alt === "")
              )
            ));
          };
          const structureValid = (requireReady = false) => {
            if (
              !(surface instanceof HTMLElement)
              || surface.localName !== "section"
              || header.localName !== "header"
              || title.localName !== "h2"
              || closeButton.type !== "button"
              || search.localName !== "search"
              || listbox.localName !== "div"
              || empty.localName !== "div"
              || host.ownerDocument !== documentOwner
              || dialog.ownerDocument !== documentOwner
              || host.getRootNode() !== actualRoot
              || host.getRootNode() !== dialog.getRootNode()
              || !correlationValid()
              || !frameworkMarkersValid()
              || !host.hasAttribute("data-citry-command-palette-host")
              || (requireReady && !host.hasAttribute(readyAttribute))
              || !runtimeAttributesValid(host, [
                "data-citry-command-palette-host",
                readyAttribute,
              ])
              || dialog.id !== data.dialogId
              || dialog.getAttribute("aria-labelledby") !== title.id
              || dialog.dataset.citryUiPart !== "command-palette"
              || !dialog.hasAttribute("data-citry-command-palette-root")
              || ["role", "aria-modal", "tabindex", "inert", "popover", "hidden"]
                .some((name) => dialog.hasAttribute(name))
              || !runtimeAttributesValid(dialog, ["data-citry-command-palette-root"])
              || ![surface, header, title, search, input, listbox]
                .every((element) => runtimeAttributesValid(element))
              || !runtimeAttributesValid(closeButton, ["data-citry-command-palette-close"])
              || !runtimeAttributesValid(empty, ["data-citry-command-palette-visual"])
              || dialog.parentElement !== host
              || surface.parentElement !== dialog
              || header.parentElement !== surface
              || search.parentElement !== surface
              || listbox.parentElement !== surface
              || empty.parentElement !== surface
              || title.id !== data.titleId
              || input.id !== data.inputId
              || listbox.id !== data.listboxId
              || input.type !== "text"
              || input.getAttribute("role") !== "combobox"
              || input.getAttribute("aria-controls") !== listbox.id
              || input.getAttribute("aria-autocomplete") !== "list"
              || input.getAttribute("autocomplete") !== "off"
              || !input.hasAttribute("autofocus")
              || listbox.getAttribute("role") !== "listbox"
              || commandElements.length !== flattened.length
              || regionElements.length !== data.regions.length
              || activators.length !== Number(data.hasActivator)
              || !visualValid(empty)
            ) return false;
            for (const activator of activators) {
              if (
                !(activator instanceof HTMLElement)
                || activator instanceof HTMLUnknownElement
                || activator.localName.includes("-")
                || activator.hasAttribute("is")
                || activator.shadowRoot !== null
                || !activator.hasAttribute("data-citry-command-palette-trigger")
                || activator.getAttribute("aria-haspopup") !== "dialog"
                || activator.getAttribute("aria-controls") !== dialog.id
              ) return false;
            }
            for (let index = 0; index < data.regions.length; index += 1) {
              const region = data.regions[index];
              const element = regionElements[index];
              if (!(element instanceof HTMLElement)) return false;
              if (region.kind === "separator") {
                if (
                  element.localName !== "hr"
                  || element.dataset.citryUiPart !== "command-palette-separator"
                  || element.getAttribute("aria-hidden") !== "true"
                ) return false;
                continue;
              }
              if (region.kind === "group") {
                if (
                  element.localName !== "section"
                  || element.getAttribute("role") !== "group"
                  || element.dataset.citryUiPart !== "command-palette-group"
                ) return false;
              } else if (
                region.kind !== "command"
                || element.getAttribute("role") !== "option"
                || element.dataset.citryUiPart !== "command-palette-command"
              ) return false;
            }
            for (const command of flattened) {
              const element = optionByValue.get(command.value);
              if (
                !(element instanceof HTMLDivElement)
                || element.id !== command.id
                || element.getAttribute("role") !== "option"
                || element.dataset.intent !== command.intent
                || element.hasAttribute("data-disabled") !== command.disabled
                || !runtimeAttributesValid(element)
              ) return false;
              for (const visual of element.querySelectorAll(
                ':scope > [data-citry-command-palette-visual]',
              )) {
                if (
                  visual.getAttribute("aria-hidden") !== "true"
                  || !visual.hasAttribute("inert")
                  || !runtimeAttributesValid(visual, ["data-citry-command-palette-visual"])
                  || !visualValid(visual)
                ) return false;
              }
            }
            return true;
          };
          if (!structureValid()) {
            abortPrevious();
            console.error(
              "[citry-ui] CCommandPalette received invalid owned anatomy; "
                + "leaving the server fallback unchanged.",
            );
            return () => {};
          }

          const retained = Boolean(previous
            && previous.host === host
            && previous.dialog === dialog
            && previous.surface === surface
            && previous.title === title
            && previous.closeButton === closeButton
            && previous.input === input
            && previous.listbox === listbox
            && previous.documentOwner === host.ownerDocument
            && previous.actualRoot === actualRoot);
          if (previous && !retained) abortPrevious();
          if (retained) delete host[handoffKey];

          const owner = { active: true, token: Symbol(), transfer: null };
          host[ownerKey] = owner;
          const invalid = new Set();
          const callbacks = { open: null, query: null, action: null };
          const tasks = new Set();
          const listeners = [];
          let active = true;
          let watcher = null;
          let controller = null;
          let collection = null;
          let configuration = {
            disabled: data.disabled,
            loop: data.loop,
            closeOnAction: data.closeOnAction,
            size: data.size,
          };
          let internalOpen = retained ? previous.internalOpen : data.open;
          let logicalOpen = retained ? previous.logicalOpen : false;
          let openControlled = false;
          let queryControlled = false;
          let fallbackQuery = retained ? previous.fallbackQuery : data.query;
          let query = retained ? previous.query : data.query;
          let suppliedQuery = retained ? previous.suppliedQuery : null;
          let activeValue = retained ? previous.activeValue : null;
          let previousOrder = retained ? previous.previousOrder : flattened.map((item) => item.value);
          let composing = retained ? previous.composing : false;
          let compositionPending = false;
          let compositionGeneration = 0;
          let actionGeneration = 0;
          let closeGeneration = 0;
          let pendingControlledClose = null;
          let formGuard = null;
          let effectStarted = false;
          const queue = (work) => {
            const marker = {};
            tasks.add(marker);
            queueMicrotask(() => {
              if (!tasks.delete(marker) || !active || host[ownerKey] !== owner) return;
              work();
            });
          };
          const report = (name) => {
            if (invalid.has(name)) return;
            invalid.add(name);
            console.error(
              `[citry-ui] CCommandPalette ${name} received an invalid client value; `
                + "retaining the last valid value.",
            );
          };
          const resolveCallback = (name, current) => {
            const value = props[name];
            if (value === undefined) {
              invalid.delete(name);
              return null;
            }
            if (value === null || typeof value === "function") {
              invalid.delete(name);
              return value;
            }
            report(name);
            return current;
          };
          const resolveBoolean = (name, fallback) => {
            const value = props[name] === undefined || props[name] === null
              ? data[name]
              : props[name];
            if (typeof value === "boolean") {
              invalid.delete(name);
              return value;
            }
            report(name);
            return fallback;
          };
          const resolveSize = () => {
            const value = props.size === undefined || props.size === null ? data.size : props.size;
            if (["sm", "md", "lg"].includes(value)) {
              invalid.delete("size");
              return value;
            }
            report("size");
            return configuration.size;
          };
          const add = (target, type, listener, options) => {
            target.addEventListener(type, listener, options);
            listeners.push(() => target.removeEventListener(type, listener, options));
          };
          const commandFor = (value) => flattened.find((command) => command.value === value) ?? null;
          const optionFor = (value) => optionByValue.get(value) ?? null;
          const eligibleItems = () => flattened.map((command) => ({
            value: command.value,
            disabled: command.disabled,
            visible: !optionFor(command.value).hidden,
          }));
          const removeFormGuard = () => {
            if (!formGuard) return;
            clearTimeout(formGuard.timer);
            formGuard.form.removeEventListener("submit", formGuard.listener, true);
            formGuard = null;
          };
          const armFormGuard = () => {
            removeFormGuard();
            const form = input.closest("form");
            if (!(form instanceof HTMLFormElement)) return;
            const generation = compositionGeneration;
            const listener = (event) => {
              if (
                event.target === form
                && generation === compositionGeneration
                && dialogRuntime.deepActive(input.ownerDocument) === input
              ) event.preventDefault();
            };
            form.addEventListener("submit", listener, true);
            const timer = setTimeout(removeFormGuard, 0);
            formGuard = { form, listener, timer };
          };
          const reflect = () => {
            dialog.toggleAttribute("data-open", logicalOpen);
            dialog.toggleAttribute("data-disabled", configuration.disabled);
            dialog.dataset.size = configuration.size;
            input.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
            input.disabled = configuration.disabled;
            closeButton.disabled = configuration.disabled;
            for (const activator of host.querySelectorAll(
              ':scope > [data-citry-command-palette-trigger]',
            )) {
              activator.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
              if ("disabled" in activator) activator.disabled = configuration.disabled;
              activator.toggleAttribute("data-disabled", configuration.disabled);
            }
          };
          const filter = ({ preserveActive = true } = {}) => {
            const needle = activeRuntime.canonicalText(query);
            const visibleValues = new Set();
            for (const command of flattened) {
              const haystacks = [command.label, ...command.keywords]
                .map((value) => activeRuntime.canonicalText(value));
              const visible = needle === "" || haystacks.some((value) => value.includes(needle));
              const option = optionFor(command.value);
              option.hidden = !visible;
              if (visible) visibleValues.add(command.value);
            }
            const contentVisibility = new Map();
            for (let index = 0; index < data.regions.length; index += 1) {
              const region = data.regions[index];
              if (region.kind === "separator") continue;
              const visible = region.commands.some((command) => visibleValues.has(command.value));
              contentVisibility.set(index, visible);
              regionElements[index].hidden = !visible;
            }
            let hasVisibleContent = false;
            let pendingSeparator = null;
            for (let index = 0; index < data.regions.length; index += 1) {
              const region = data.regions[index];
              if (region.kind === "separator") {
                regionElements[index].hidden = true;
                if (hasVisibleContent && pendingSeparator === null) pendingSeparator = index;
                continue;
              }
              if (!contentVisibility.get(index)) continue;
              if (hasVisibleContent && pendingSeparator !== null) {
                regionElements[pendingSeparator].hidden = false;
              }
              hasVisibleContent = true;
              pendingSeparator = null;
            }
            const items = eligibleItems();
            activeValue = logicalOpen
              ? collection.nearest(items, preserveActive ? activeValue : null, previousOrder)
              : null;
            collection.sync({
              items,
              activeValue,
              open: logicalOpen,
              optionFor,
              activeAttribute: "data-active",
            });
            const hasResults = visibleValues.size > 0;
            dialog.toggleAttribute("data-empty", !hasResults);
            listbox.hidden = !hasResults;
            empty.hidden = hasResults;
            previousOrder = flattened.map((command) => command.value);
          };
          const notifyQuery = (next, reason, closeReason, source, controlled) => {
            callbacks.query?.(next, { reason, closeReason, controlled, source });
          };
          const settleCloseQuery = (reason, source) => {
            const generation = ++closeGeneration;
            activeValue = null;
            collection.sync({
              items: eligibleItems(),
              activeValue: null,
              open: false,
              optionFor,
              activeAttribute: "data-active",
            });
            fallbackQuery = "";
            if (queryControlled) {
              if (query !== "") notifyQuery("", "close", reason, source, true);
            } else if (query !== "") {
              query = "";
              input.value = "";
              filter({ preserveActive: false });
              notifyQuery("", "close", reason, source, false);
            }
            if (generation !== closeGeneration) return;
          };
          const commitVisibility = (nextOpen, reason, source, { notify = false } = {}) => {
            const next = Boolean(nextOpen) && !configuration.disabled;
            const wasOpen = logicalOpen;
            controller.setOpen(next, source);
            logicalOpen = controller.isOpen();
            internalOpen = logicalOpen;
            reflect();
            filter({ preserveActive: wasOpen });
            if (notify && wasOpen !== logicalOpen) {
              callbacks.open?.(logicalOpen, { reason, controlled: false, source });
            }
            if (wasOpen && !logicalOpen) settleCloseQuery(reason, source);
            return wasOpen !== logicalOpen;
          };
          const requestVisibility = (nextOpen, reason, source) => {
            if (Boolean(nextOpen) === logicalOpen) return false;
            if (openControlled) {
              const closeRequest = nextOpen ? null : { reason, source };
              pendingControlledClose = closeRequest;
              callbacks.open?.(Boolean(nextOpen), { reason, controlled: true, source });
              if (props.open === Boolean(nextOpen)) {
                const wasOpen = logicalOpen;
                controller.setOpen(Boolean(nextOpen) && !configuration.disabled, source);
                logicalOpen = controller.isOpen();
                reflect();
                filter({ preserveActive: wasOpen });
                if (wasOpen && !logicalOpen) settleCloseQuery(reason, source);
              }
              if (closeRequest) queue(() => {
                if (
                  pendingControlledClose === closeRequest
                  && logicalOpen
                  && props.open === logicalOpen
                ) pendingControlledClose = null;
              });
              return false;
            }
            return commitVisibility(nextOpen, reason, source, { notify: true });
          };
          const commitUserQuery = (requested, source) => {
            if (requested === query) {
              input.value = query;
              return;
            }
            const selectionStart = input.selectionStart;
            const selectionEnd = input.selectionEnd;
            if (queryControlled) {
              notifyQuery(requested, "input", null, input, true);
              const supplied = props.query;
              if (supplied === requested) {
                query = requested;
                fallbackQuery = requested;
                suppliedQuery = requested;
                filter();
                return;
              }
              if (supplied === undefined || supplied === null) queryControlled = false;
              input.value = query;
              if (selectionStart !== null && selectionEnd !== null) {
                input.setSelectionRange(
                  Math.min(selectionStart, query.length),
                  Math.min(selectionEnd, query.length),
                );
              }
              filter();
              return;
            }
            query = requested;
            fallbackQuery = requested;
            input.value = requested;
            filter();
            notifyQuery(requested, "input", null, source, false);
          };
          const act = (command, option, event, source) => {
            if (
              !active
              || configuration.disabled
              || command.disabled
              || option.hidden
              || !logicalOpen
            ) return;
            const generation = ++actionGeneration;
            activeValue = command.value;
            collection.sync({
              items: eligibleItems(),
              activeValue,
              open: true,
              optionFor,
              activeAttribute: "data-active",
            });
            if (source === "click" && dialogRuntime.isFocusable(input)) {
              input.focus({ preventScroll: true });
            }
            const close = command.closeOnAction ?? configuration.closeOnAction;
            callbacks.action?.(command.value, {
              query,
              source,
              item: option,
              event,
              closeOnAction: close,
            });
            if (
              generation !== actionGeneration
              || !active
              || host[ownerKey] !== owner
              || !option.isConnected
            ) return;
            if (close) requestVisibility(false, "action", option);
          };

          collection = activeRuntime.create({
            input,
            listbox,
            idPrefix: `${data.listboxId}-command`,
          });
          collection.retain(flattened.map((command) => command.value));
          input.disabled = configuration.disabled;
          controller = dialogRuntime.create({
            host,
            dialog,
            surface,
            title,
            closeButton,
            signature: "CCommandPalette:command-input",
            policy: () => ({ dismissible: true, closeOnEscape: true, closeOnOutside: true }),
            initialFocus: () => input,
            containmentFallback: () => input,
            escapeBlocked: () => composing,
            interceptDialogSubmit: () => false,
            requestClose: (reason, source) => requestVisibility(false, reason, source),
            nativeClosed: (reason, source) => {
              const wasOpen = logicalOpen;
              logicalOpen = false;
              internalOpen = false;
              reflect();
              filter();
              if (wasOpen) {
                callbacks.open?.(false, { reason, controlled: openControlled, source });
                settleCloseQuery(reason, source);
              }
            },
            forceClose: (reason, source) => {
              const wasOpen = logicalOpen;
              logicalOpen = false;
              internalOpen = false;
              reflect();
              filter();
              if (wasOpen) {
                callbacks.open?.(false, { reason, controlled: openControlled, source });
                settleCloseQuery(reason, source);
              }
            },
            failed: () => {
              logicalOpen = false;
              host.removeAttribute(readyAttribute);
              reflect();
              console.error("[citry-ui] CCommandPalette could not enter modal state.");
            },
            handoffAborted: () => {
              logicalOpen = false;
              host.removeAttribute(readyAttribute);
              reflect();
            },
          });
          if (retained) logicalOpen = controller.isOpen();

          add(host, "click", (event) => {
            const trigger = event.target.closest?.("[data-citry-command-palette-trigger]");
            if (trigger && trigger.parentElement === host && !configuration.disabled) {
              requestVisibility(true, "trigger", trigger);
              return;
            }
            const close = event.target.closest?.("[data-citry-command-palette-close]");
            if (close === closeButton && !configuration.disabled) {
              requestVisibility(false, "close-button", closeButton);
            }
          });
          add(input, "input", (event) => {
            if (composing || event.isComposing || compositionPending) return;
            commitUserQuery(input.value, input);
          });
          add(input, "compositionstart", () => {
            composing = true;
            compositionPending = false;
            compositionGeneration += 1;
          });
          add(input, "compositionend", () => {
            composing = false;
            compositionPending = true;
            const generation = ++compositionGeneration;
            queue(() => {
              if (generation !== compositionGeneration || !compositionPending) return;
              compositionPending = false;
              removeFormGuard();
              commitUserQuery(input.value, input);
            });
          });
          add(input, "keydown", (event) => {
            const isComposition = composing || event.isComposing || event.keyCode === 229;
            if (isComposition) {
              if (event.key === "Enter") armFormGuard();
              return;
            }
            if (configuration.disabled) return;
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
              event.preventDefault();
              activeValue = collection.move(
                eligibleItems(),
                activeValue,
                event.key === "ArrowDown" ? 1 : -1,
                configuration.loop,
              );
              collection.sync({
                items: eligibleItems(),
                activeValue,
                open: logicalOpen,
                optionFor,
                activeAttribute: "data-active",
              });
              return;
            }
            if (event.key === "Enter") {
              event.preventDefault();
              const command = commandFor(activeValue);
              const option = optionFor(activeValue);
              if (command && option) act(command, option, event, "keyboard");
            }
          });
          add(listbox, "pointerdown", (event) => {
            const option = event.target.closest?.(
              '[data-citry-ui-part="command-palette-command"]',
            );
            if (
              optionByValue.get(option?.dataset.value) === option
              && event.button === 0
              && !event.altKey
              && !event.ctrlKey
              && !event.metaKey
              && !event.shiftKey
            ) event.preventDefault();
          });
          add(listbox, "pointermove", (event) => {
            const option = event.target.closest?.(
              '[data-citry-ui-part="command-palette-command"]',
            );
            const command = commandFor(option?.dataset.value);
            if (!command || command.disabled || option.hidden) return;
            activeValue = command.value;
            collection.sync({
              items: eligibleItems(),
              activeValue,
              open: logicalOpen,
              optionFor,
              activeAttribute: "data-active",
            });
          });
          add(listbox, "click", (event) => {
            if (
              event.button !== 0
              || event.altKey
              || event.ctrlKey
              || event.metaKey
              || event.shiftKey
            ) return;
            const option = event.target.closest?.(
              '[data-citry-ui-part="command-palette-command"]',
            );
            const command = commandFor(option?.dataset.value);
            if (command && optionByValue.get(command.value) === option) {
              act(command, option, event, "click");
            }
          });
          add(input, "blur", removeFormGuard);

          const registration = {
            notify() {
              if (!active) return;
              if (!host.isConnected) {
                teardown(false);
                return;
              }
              if (host.ownerDocument !== dialog.ownerDocument) {
                teardown(true);
                return;
              }
              const nextRoot = host.getRootNode();
              if (nextRoot !== actualRoot) {
                const supported = nextRoot === documentOwner
                  || (nextRoot instanceof ShadowRoot
                    && nextRoot.mode === "open"
                    && nextRoot.host.ownerDocument === documentOwner
                    && nextRoot.host.shadowRoot === nextRoot);
                if (!supported || dialog.getRootNode() !== nextRoot || !controller.refreshRoot()) {
                  teardown(true);
                  return;
                }
                actualRoot = nextRoot;
                watcher.refresh();
              }
              if (!structureValid(true)) {
                teardown(true);
                return;
              }
              watcher.refresh();
            },
          };
          watcher = watchPalette(host, registration);

          effect(() => {
            const priorDisabled = configuration.disabled;
            configuration = {
              disabled: resolveBoolean("disabled", configuration.disabled),
              loop: resolveBoolean("loop", configuration.loop),
              closeOnAction: resolveBoolean("closeOnAction", configuration.closeOnAction),
              size: resolveSize(),
            };
            callbacks.open = resolveCallback("onOpenChange", callbacks.open);
            callbacks.query = resolveCallback("onQueryChange", callbacks.query);
            callbacks.action = resolveCallback("onAction", callbacks.action);

            const nextQuery = props.query;
            if (nextQuery === undefined || nextQuery === null) {
              if (queryControlled) query = fallbackQuery;
              queryControlled = false;
              suppliedQuery = null;
              invalid.delete("query");
            } else if (typeof nextQuery === "string") {
              queryControlled = true;
              if (nextQuery !== suppliedQuery) {
                query = nextQuery;
                fallbackQuery = nextQuery;
                suppliedQuery = nextQuery;
              }
              invalid.delete("query");
            } else {
              report("query");
              if (queryControlled) query = fallbackQuery;
              queryControlled = false;
              suppliedQuery = null;
            }
            input.value = query;

            const nextOpen = props.open;
            let ownerOpen = internalOpen;
            if (nextOpen === undefined || nextOpen === null) {
              if (openControlled) internalOpen = logicalOpen;
              openControlled = false;
              ownerOpen = internalOpen;
              pendingControlledClose = null;
              invalid.delete("open");
            } else if (typeof nextOpen === "boolean") {
              openControlled = true;
              ownerOpen = nextOpen;
              invalid.delete("open");
            } else {
              report("open");
              if (openControlled) internalOpen = logicalOpen;
              openControlled = false;
              ownerOpen = internalOpen;
              pendingControlledClose = null;
            }
            if (configuration.disabled && logicalOpen) {
              const wasControlled = openControlled;
              controller.setOpen(false, dialog);
              logicalOpen = false;
              internalOpen = false;
              callbacks.open?.(false, {
                reason: "disabled",
                controlled: wasControlled,
                source: dialog,
              });
              settleCloseQuery("disabled", dialog);
            } else if (!configuration.disabled) {
              const expected = Boolean(ownerOpen);
              if (expected !== logicalOpen) {
                const wasOpen = logicalOpen;
                controller.setOpen(expected, null);
                logicalOpen = controller.isOpen();
                internalOpen = logicalOpen;
                if (wasOpen && !logicalOpen) {
                  const close = pendingControlledClose ?? { reason: "owner", source: null };
                  settleCloseQuery(close.reason, close.source);
                }
              }
            }
            if (!configuration.disabled && priorDisabled && openControlled && props.open === true) {
              controller.setOpen(true, null);
              logicalOpen = controller.isOpen();
            }
            pendingControlledClose = logicalOpen ? pendingControlledClose : null;
            reflect();
            filter({ preserveActive: effectStarted });
            effectStarted = true;
          });

          const teardown = (diagnose = false) => {
            if (!active) return;
            active = false;
            owner.active = false;
            actionGeneration += 1;
            compositionGeneration += 1;
            closeGeneration += 1;
            removeFormGuard();
            tasks.clear();
            watcher?.cleanup();
            listeners.splice(0).forEach((remove) => remove());
            const canHandoff = host.isConnected
              && host.ownerDocument === documentOwner
              && host.getRootNode() === actualRoot
              && dialog.isConnected
              && dialog.parentElement === host
              && surface.parentElement === dialog
              && title.isConnected
              && closeButton.isConnected
              && input.isConnected
              && listbox.isConnected;
            const handedOff = controller.cleanup({ handoff: canHandoff });
            if (host[ownerKey] === owner) delete host[ownerKey];
            if (handedOff) {
              const record = {
                host,
                dialog,
                surface,
                title,
                closeButton,
                input,
                listbox,
                documentOwner: host.ownerDocument,
                actualRoot: host.getRootNode(),
                internalOpen,
                logicalOpen,
                query,
                fallbackQuery,
                suppliedQuery,
                activeValue,
                previousOrder,
                composing,
                collection,
                timer: null,
                abort() {
                  dialogRuntime.abortHandoff(dialog);
                  collection.cleanup();
                  host.removeAttribute(readyAttribute);
                  dialog.removeAttribute("data-open");
                  input.removeAttribute("aria-activedescendant");
                },
              };
              host[handoffKey] = record;
              record.timer = setTimeout(() => {
                if (host[handoffKey] !== record || host[ownerKey]?.active) return;
                record.abort();
                delete host[handoffKey];
              }, 1000);
            } else {
              collection.cleanup();
              host.removeAttribute(readyAttribute);
              dialog.removeAttribute("data-open");
            }
            if (diagnose) {
              console.error(
                "[citry-ui] CCommandPalette lost its owned anatomy; component behavior was removed.",
              );
            }
          };

          owner.transfer = () => teardown(false);

          reflect();
          filter({ preserveActive: retained });
          input.disabled = configuration.disabled;
          host.setAttribute(readyAttribute, "");

          return () => teardown(false);
        },
      });
      /* citry-ui:command-palette-attribution:initializer:end */
    """

    css = """
      /* citry-ui:command-palette-attribution:css:begin */
      @layer citry-ui.theme {
        :where(.cui-command-palette-host) {
          display: contents;
        }

        :where(.cui-command-palette [hidden]) {
          display: none !important;
        }

        :where(.cui-command-palette) {
          --_cui-command-palette-backdrop: var(
            --cui-command-palette-backdrop,
            color-mix(in srgb, CanvasText 48%, transparent)
          );
          --_cui-command-palette-background: var(--cui-command-palette-background, Canvas);
          --_cui-command-palette-foreground: var(--cui-command-palette-foreground, CanvasText);
          --_cui-command-palette-muted: var(
            --cui-command-palette-muted,
            color-mix(in srgb, CanvasText 68%, transparent)
          );
          --_cui-command-palette-border-color: var(
            --cui-command-palette-border-color,
            color-mix(in srgb, CanvasText 22%, transparent)
          );
          --_cui-command-palette-active-background: var(
            --cui-command-palette-active-background,
            color-mix(in srgb, Highlight 15%, Canvas)
          );
          --_cui-command-palette-active-foreground: var(
            --cui-command-palette-active-foreground,
            CanvasText
          );
          --_cui-command-palette-danger: var(
            --cui-command-palette-danger,
            light-dark(#b42318, #f97066)
          );
          --_cui-command-palette-radius: var(--cui-command-palette-radius, 0.875rem);
          --_cui-command-palette-shadow: var(
            --cui-command-palette-shadow,
            0 1.5rem 4rem color-mix(in srgb, CanvasText 28%, transparent)
          );
          --_cui-command-palette-inline-size: var(
            --cui-command-palette-inline-size,
            36rem
          );
          --_cui-command-palette-max-block-size: var(
            --cui-command-palette-max-block-size,
            calc(100dvb - 2rem)
          );
          --_cui-command-palette-padding: var(--cui-command-palette-padding, 0.75rem);
          --_cui-command-palette-gap: var(--cui-command-palette-gap, 0.5rem);
          --_cui-command-palette-input-block-size: var(
            --cui-command-palette-input-block-size,
            2.75rem
          );
          --_cui-command-palette-row-min-block-size: var(
            --cui-command-palette-row-min-block-size,
            2.75rem
          );
          --_cui-command-palette-row-padding-inline: var(
            --cui-command-palette-row-padding-inline,
            0.75rem
          );
          --_cui-command-palette-group-gap: var(--cui-command-palette-group-gap, 0.5rem);
          --_cui-command-palette-focus-ring: var(--cui-command-palette-focus-ring, Highlight);
          background: transparent;
          border: 0;
          color: var(--_cui-command-palette-foreground);
          inline-size: min(var(--_cui-command-palette-inline-size), calc(100vi - 2rem));
          margin: auto;
          max-block-size: var(--_cui-command-palette-max-block-size);
          max-inline-size: calc(100vi - 2rem);
          padding: 0;
        }

        :where(.cui-command-palette[data-size="sm"]) {
          --_cui-command-palette-inline-size: var(--cui-command-palette-inline-size, 28rem);
          --_cui-command-palette-input-block-size: var(
            --cui-command-palette-input-block-size,
            2.5rem
          );
        }

        :where(.cui-command-palette[data-size="lg"]) {
          --_cui-command-palette-inline-size: var(--cui-command-palette-inline-size, 44rem);
          --_cui-command-palette-input-block-size: var(
            --cui-command-palette-input-block-size,
            3rem
          );
          --_cui-command-palette-row-min-block-size: var(
            --cui-command-palette-row-min-block-size,
            3rem
          );
        }

        :where(.cui-command-palette)::backdrop {
          background: var(--_cui-command-palette-backdrop);
        }

        :where(.cui-command-palette__surface) {
          background: var(--_cui-command-palette-background);
          border: 1px solid var(--_cui-command-palette-border-color);
          border-radius: var(--_cui-command-palette-radius);
          box-shadow: var(--_cui-command-palette-shadow);
          display: grid;
          gap: var(--_cui-command-palette-gap);
          max-block-size: inherit;
          min-inline-size: 0;
          overflow: hidden;
          padding: var(--_cui-command-palette-padding);
        }

        :where(.cui-command-palette__header) {
          align-items: center;
          display: flex;
          gap: 0.75rem;
          justify-content: space-between;
        }

        :where([data-citry-ui-part="command-palette-title"]) {
          font: inherit;
          font-size: 1rem;
          font-weight: 650;
          margin: 0;
          min-inline-size: 0;
        }

        :where([data-citry-ui-part="command-palette-close"]) {
          align-items: center;
          appearance: none;
          background: transparent;
          border: 1px solid transparent;
          border-radius: 0.5rem;
          color: inherit;
          cursor: pointer;
          display: inline-flex;
          flex: none;
          font: inherit;
          inline-size: 2.75rem;
          justify-content: center;
          min-block-size: 2.75rem;
          padding: 0;
        }

        :where([data-citry-ui-part="command-palette-close"]:hover) {
          background: var(--_cui-command-palette-active-background);
        }

        :where([data-citry-ui-part="command-palette-close"]:focus-visible) {
          outline: 2px solid var(--_cui-command-palette-focus-ring);
          outline-offset: 2px;
        }

        :where([data-citry-ui-part="command-palette-search"]) {
          display: block;
        }

        :where([data-citry-ui-part="command-palette-input"]) {
          appearance: none;
          background: var(--_cui-command-palette-background);
          block-size: var(--_cui-command-palette-input-block-size);
          border: 1px solid var(--_cui-command-palette-border-color);
          border-radius: 0.625rem;
          color: inherit;
          font: inherit;
          inline-size: 100%;
          min-inline-size: 0;
          padding-inline: 0.75rem;
        }

        :where([data-citry-ui-part="command-palette-input"]:focus-visible) {
          border-color: var(--_cui-command-palette-focus-ring);
          outline: 2px solid var(--_cui-command-palette-focus-ring);
          outline-offset: 1px;
        }

        :where([data-citry-ui-part="command-palette-listbox"]) {
          display: grid;
          gap: 0.25rem;
          max-block-size: min(26rem, calc(100dvb - 10rem));
          min-block-size: 0;
          overflow: auto;
          overscroll-behavior: contain;
          scrollbar-gutter: stable;
        }

        :where([data-citry-ui-part="command-palette-command"]) {
          align-items: center;
          border-radius: 0.625rem;
          color: inherit;
          cursor: default;
          display: grid;
          gap: 0.125rem var(--_cui-command-palette-gap);
          grid-template-columns: auto minmax(0, 1fr) auto;
          min-block-size: var(--_cui-command-palette-row-min-block-size);
          padding-block: 0.375rem;
          padding-inline: var(--_cui-command-palette-row-padding-inline);
        }

        :where([data-citry-ui-part="command-palette-command"][data-active]) {
          background: var(--_cui-command-palette-active-background);
          color: var(--_cui-command-palette-active-foreground);
          outline: 1px solid color-mix(in srgb, var(--_cui-command-palette-focus-ring) 55%, transparent);
        }

        :where([data-citry-ui-part="command-palette-command"][data-disabled]) {
          cursor: not-allowed;
          opacity: 0.52;
        }

        :where([data-citry-ui-part="command-palette-command"][data-intent="danger"]:not([data-disabled])) {
          color: var(--_cui-command-palette-danger);
        }

        :where(.cui-command-palette__description) {
          color: var(--_cui-command-palette-muted);
          font-size: 0.875em;
          grid-column: 2;
        }

        :where(.cui-command-palette__shortcut) {
          color: var(--_cui-command-palette-muted);
          font: inherit;
          font-size: 0.8125em;
          grid-column: 3;
          grid-row: 1 / span 2;
          margin-inline-start: auto;
          white-space: nowrap;
        }

        :where([data-citry-ui-part="command-palette-item-start"]) {
          grid-column: 1;
          grid-row: 1 / span 2;
        }

        :where([data-citry-ui-part="command-palette-item-end"]) {
          grid-column: 3;
          grid-row: 1 / span 2;
        }

        :where([data-citry-ui-part="command-palette-group"]) {
          display: grid;
          gap: 0.25rem;
        }

        :where([data-citry-ui-part="command-palette-group"] + [data-citry-ui-part="command-palette-group"]) {
          margin-block-start: var(--_cui-command-palette-group-gap);
        }

        :where([data-citry-ui-part="command-palette-group-label"]) {
          color: var(--_cui-command-palette-muted);
          font-size: 0.75rem;
          font-weight: 650;
          letter-spacing: 0.04em;
          padding-block: 0.375rem 0.125rem;
          padding-inline: var(--_cui-command-palette-row-padding-inline);
          text-transform: uppercase;
        }

        :where([data-citry-ui-part="command-palette-separator"]) {
          border: 0;
          border-block-start: 1px solid var(--_cui-command-palette-border-color);
          margin: 0.25rem var(--_cui-command-palette-row-padding-inline);
        }

        :where([data-citry-ui-part="command-palette-empty"]) {
          color: var(--_cui-command-palette-muted);
          padding: 1.5rem var(--_cui-command-palette-row-padding-inline);
          text-align: center;
        }

        :where(.cui-command-palette__visually-hidden) {
          block-size: 1px;
          clip-path: inset(50%);
          inline-size: 1px;
          overflow: hidden;
          position: absolute;
          white-space: nowrap;
        }

        :where(.cui-command-palette[data-disabled]) {
          opacity: 0.65;
        }
      }

      @media (pointer: coarse) {
        :where(.cui-command-palette) {
          --_cui-command-palette-row-min-block-size: max(
            var(--cui-command-palette-row-min-block-size, 2.75rem),
            44px
          );
        }
      }

      @media (prefers-reduced-motion: no-preference) {
        :where([data-citry-ui-part="command-palette-command"]) {
          transition: background-color 100ms ease, color 100ms ease;
        }
      }

      @media (forced-colors: active) {
        :where(.cui-command-palette__surface),
        :where([data-citry-ui-part="command-palette-input"]) {
          border-color: CanvasText;
        }

        :where([data-citry-ui-part="command-palette-command"][data-active]) {
          outline: 2px solid Highlight;
        }

        :where([data-citry-ui-part="command-palette-command"][data-disabled]) {
          color: GrayText;
          opacity: 1;
        }
      }

      @media print {
        :where(.cui-command-palette) {
          display: none !important;
        }
      }
      /* citry-ui:command-palette-attribution:css:end */
    """

    messages = """
      citry-ui-command-palette-placeholder = Search commands
      citry-ui-command-palette-search-label = Search commands
      citry-ui-command-palette-empty = No commands found
      citry-ui-command-palette-close = Close command palette
    """


class _CCommandPaletteDependencies:
    js: ClassVar = [
        ANCHORED_LAYER_RUNTIME_DEPENDENCY,
        DIALOG_CONTROLLER_RUNTIME_DEPENDENCY,
        ACTIVE_DESCENDANT_RUNTIME_DEPENDENCY,
    ]


CCommandPalette.Dependencies = _CCommandPaletteDependencies


__all__ = [  # noqa: RUF022 - ratified public order
    "CCommandPalette",
    "CCommandPaletteCommand",
    "CCommandPaletteGroup",
    "CCommandPaletteSeparator",
    "CCommandPaletteEntry",
    "CCommandPaletteIntent",
    "CCommandPaletteSize",
    "CCommandPaletteActionSource",
    "CCommandPaletteActionDetail",
    "CCommandPaletteOpenReason",
    "CCommandPaletteOpenChangeDetail",
    "CCommandPaletteQueryReason",
    "CCommandPaletteQueryChangeDetail",
    "CCommandPaletteItemSlotData",
]
