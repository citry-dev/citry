"""Single-path hierarchical selection with a columnar popup."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CCascaderSize = Literal["sm", "md", "lg"]
CCascaderVariant = Literal["outline", "soft", "plain"]
CCascaderChangeSource = Literal["pointer", "keyboard", "reset"]

_CONTEXT = "citry_ui_cascader"
_SIZES = ("sm", "md", "lg")
_VARIANTS = ("outline", "soft", "plain")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-open",
        "data-size",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_OPTION_OWNED = frozenset(
    {
        "aria-level",
        "aria-owns",
        "aria-posinset",
        "aria-setsize",
        "aria-disabled",
        "aria-expanded",
        "aria-hidden",
        "aria-label",
        "aria-selected",
        "contenteditable",
        "data-active",
        "data-citry-cascader-child-group",
        "data-citry-cascader-parent",
        "data-citry-ui-part",
        "data-disabled",
        "data-level",
        "data-selected",
        "data-value",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CCascaderDefaultSlotData:
    pass


class CCascaderOptionDefaultSlotData(TypedDict):
    parent_value: str
    level: int


class CCascaderValueChangeDetail(TypedDict):
    value: list[str]
    labels: list[str]
    previousValue: list[str]
    controlled: bool
    source: CCascaderChangeSource
    option: object
    sourceEvent: object


class CCascaderOpenChangeDetail(TypedDict):
    open: bool
    reason: str
    sourceEvent: object


@dataclass(slots=True)
class _Option:
    value: str
    label: str
    disabled: bool
    attrs: dict[str, object]
    parent: _Option | None
    children: list[_Option] = field(default_factory=list)

    @property
    def path(self) -> tuple[str, ...]:
        values: list[str] = []
        current: _Option | None = self
        while current is not None:
            values.append(current.value)
            current = current.parent
        return tuple(reversed(values))


@dataclass(slots=True)
class _Registry:
    roots: list[_Option] = field(default_factory=list)
    options: list[_Option] = field(default_factory=list)


@dataclass(slots=True)
class _Context:
    registry: _Registry
    parent: _Option | None
    level: int


def _plain(owner: str, name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{owner} {name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{owner} {name} must be nonempty and cannot contain U+0000.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = cast("str", _plain("CCascader", name, value))
    if plain not in allowed:
        raise ValueError(
            f"CCascader {name} must be one of {', '.join(repr(item) for item in allowed)}, got {plain!r}."
        )
    return plain


def _path(value: object) -> tuple[str, ...]:
    raw = const_value(value)
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"CCascader value must be a sequence of strings, got {raw!r}.")
    return tuple(cast("str", _plain("CCascader", "value segment", item)) for item in raw)


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    owner: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
    class_: CClassValue | None,
    style: CStyleValue | None,
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"{owner} attrs must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{owner} attrs")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"{owner} attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{owner} attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{owner} attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{owner} attrs cannot dynamically bind owned attribute {key!r}.")
    return merge_root_attrs(copied, class_, style)


def _token(path: tuple[str, ...]) -> str:
    return sha256("\x1f".join(path).encode()).hexdigest()[:12]


def _item_id(root_id: str, path: tuple[str, ...]) -> str:
    return f"{root_id}-option-{_token(path)}"


def _group_id(root_id: str, path: tuple[str, ...]) -> str:
    return f"{root_id}-group-{_token(path)}"


def _entries(options: Sequence[_Option], *, selected: tuple[str, ...], root: bool) -> list[dict[str, object]]:
    first_enabled = next((option for option in options if not option.disabled), None)
    return [
        {
            "option": option,
            "position": position,
            "set_size": len(options),
            "initial_focus": root and not selected and option is first_enabled,
        }
        for position, option in enumerate(options, 1)
    ]


def _declaration_result(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CCascader content may contain only nested CCascaderOption declarations and formatting whitespace."
        )


class CCascader(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        value: Sequence[str] = ()
        id: str | None = None
        aria_label: str | None = None
        aria_labelledby: str | None = None
        name: str | None = None
        form: str | None = None
        placeholder: str = "Choose an option"
        separator: str = " / "
        change_on_select: bool = False
        open: bool = False
        disabled: bool = False
        size: CCascaderSize = "md"
        variant: CCascaderVariant = "outline"
        empty_label: str = "No options"
        selected_label: str = "Selected {path}"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CCascaderDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_cascader_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_CONTEXT, None) is not None:
            raise ValueError("Nested CCascader must be rendered outside an Option declaration.")
        validate_html_id("CCascader", kwargs.id)
        for name in ("change_on_select", "open", "disabled"):
            validate_boolean("CCascader", name, getattr(kwargs, name))
        catalog = {
            key: uses_catalog_default(self, key if key == "placeholder" else f"{key}_label")
            for key in ("placeholder", "empty", "selected")
        }
        labels = {
            "placeholder": self.i18n.tr("citry-ui-cascader-placeholder")
            if catalog["placeholder"]
            else kwargs.placeholder,
            "empty": self.i18n.tr("citry-ui-cascader-empty") if catalog["empty"] else kwargs.empty_label,
            "selected": self.i18n.tr("citry-ui-cascader-selected", path="{path}")
            if catalog["selected"]
            else kwargs.selected_label,
        }
        labels = {key: cast("str", _plain("CCascader", f"{key}_label", value)) for key, value in labels.items()}
        if "{path}" not in labels["selected"]:
            raise ValueError("CCascader selected_label must contain {path}.")
        registry = _Registry()
        self.provide(_CONTEXT, context=_Context(registry=registry, parent=None, level=1))
        snapshot: dict[str, object] = {
            "root_id": kwargs.id or f"cui-cascader-{self.id}",
            "value": _path(kwargs.value),
            "aria_label": cast("str | None", _plain("CCascader", "aria_label", kwargs.aria_label, optional=True)),
            "aria_labelledby": cast(
                "str | None", _plain("CCascader", "aria_labelledby", kwargs.aria_labelledby, optional=True)
            ),
            "name": cast("str | None", _plain("CCascader", "name", kwargs.name, optional=True)),
            "form": cast("str | None", _plain("CCascader", "form", kwargs.form, optional=True)),
            "separator": cast("str", _plain("CCascader", "separator", kwargs.separator)),
            "change_on_select": bool(kwargs.change_on_select),
            "open": bool(kwargs.open),
            "disabled": bool(kwargs.disabled),
            "size": _choice("size", kwargs.size, _SIZES),
            "variant": _choice("variant", kwargs.variant, _VARIANTS),
            "catalog": catalog,
            "labels": labels,
            "registry": registry,
            "attrs": _attrs("CCascader", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
        }
        self._cui_cascader_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {**snapshot, "snapshot": snapshot}

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "value": list(cast("tuple[str, ...]", snapshot["value"])),
            **{
                key: snapshot[key]
                for key in ("open", "disabled", "change_on_select", "separator", "name", "form", "catalog", "labels")
            },
        }

    template = """
      <c-CInternalCascaderDeclarations><c-slot /></c-CInternalCascaderDeclarations>
      <c-CInternalCascader c-snapshot="snapshot" />
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"

    messages = """
      citry-ui-cascader-placeholder = Choose an option
      citry-ui-cascader-empty = No options
      # @param {str} $path - Application-localized joined Option labels.
      citry-ui-cascader-selected = Selected { $path }
    """


class CCascaderOption(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        label: str
        disabled: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CCascaderOptionDefaultSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        provided = self.inject(_CONTEXT, None)
        if provided is None:
            raise ValueError("CCascaderOption must be rendered directly inside CCascader or another CCascaderOption.")
        context = cast("_Context", provided.context)
        value = cast("str", _plain("CCascaderOption", "value", kwargs.value))
        if any(option.value == value for option in context.registry.options):
            raise ValueError(f"CCascaderOption value {value!r} is duplicated.")
        validate_boolean("CCascaderOption", "disabled", kwargs.disabled)
        option = _Option(
            value=value,
            label=cast("str", _plain("CCascaderOption", "label", kwargs.label)),
            disabled=bool(kwargs.disabled),
            attrs=_attrs("CCascaderOption", kwargs.attrs, _OPTION_OWNED, kwargs.class_, kwargs.style),
            parent=context.parent,
        )
        context.registry.options.append(option)
        (context.registry.roots if context.parent is None else context.parent.children).append(option)
        self.provide(_CONTEXT, context=_Context(context.registry, option, context.level + 1))
        return {"parent_value": value, "level": context.level}

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CCascaderOption declaration completed without a render result.")
        _declaration_result(result)
        return ""

    template = "<c-slot />"


class CInternalCascaderDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CCascaderDefaultSlotData] | None = None

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CCascader declarations completed without a render result.")
        _declaration_result(result)

    template = "<c-slot />"


class CInternalCascader(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        snapshot: dict[str, object]

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        data = kwargs.snapshot
        registry = cast("_Registry", data["registry"])
        value = cast("tuple[str, ...]", data["value"])
        match = next((option for option in registry.options if option.path == value), None) if value else None
        if value and match is None:
            raise ValueError(f"CCascader value {list(value)!r} is not one continuous Option path.")
        if match is not None and any(
            option.disabled for option in registry.options if option.path == value[: len(option.path)]
        ):
            raise ValueError("CCascader value cannot pass through or select a disabled Option.")
        if match is not None and match.children and not data["change_on_select"]:
            raise ValueError("CCascader value must end at a leaf unless change_on_select is true.")
        labels = [
            option.label for option in registry.options if option.path and option.path == value[: len(option.path)]
        ]
        joined = cast("str", data["separator"]).join(labels)
        catalog = cast("dict[str, bool]", data["catalog"])
        texts = cast("dict[str, str]", data["labels"])
        root_id = cast("str", data["root_id"])
        self.unprovide(_CONTEXT)
        return {
            **data,
            "roots": registry.roots,
            "root_entries": _entries(registry.roots, selected=value, root=True),
            "groups": [option for option in registry.options if option.children],
            "joined": joined,
            "display": joined or texts["placeholder"],
            "trigger_id": f"{root_id}-trigger",
            "popup_id": f"{root_id}-popup",
            "root_attrs": {
                **cast("dict[str, object]", data["attrs"]),
                "data-disabled": True if data["disabled"] else None,
                "data-open": True if data["open"] else None,
                "data-size": data["size"],
                "data-variant": data["variant"],
            },
            "catalog_placeholder": catalog["placeholder"],
            "catalog_empty": catalog["empty"],
            "status": texts["selected"].format(path=joined) if joined else "",
        }

    template = """
      <div class="cui-cascader" c-id="root_id" c-bind="root_attrs" data-citry-ui-part="cascader">
        <button type="button" c-id="trigger_id" c-disabled="disabled" c-aria-label="aria_label" c-aria-labelledby="aria_labelledby" aria-haspopup="tree" c-aria-controls="popup_id" c-aria-expanded="'true' if open else 'false'" data-citry-ui-part="trigger">
          <span data-citry-ui-part="value">{{ tr('citry-ui-cascader-placeholder') if catalog_placeholder and not joined else display }}</span>
          <span aria-hidden="true" data-citry-ui-part="indicator">⌄</span>
        </button>
        <div c-id="popup_id" c-hidden="not open" data-citry-ui-part="popup">
          <ul role="tree" c-aria-labelledby="trigger_id" c-hidden="not roots" data-citry-cascader-column data-level="1" data-citry-ui-part="tree">
            <c-for each="entry in root_entries"><c-CInternalCascaderOption c-bind="entry" c-root_id="root_id" c-selected="value" c-level="1" /></c-for>
          </ul>
          <c-for each="parent in groups"><c-CInternalCascaderGroup c-parent="parent" c-root_id="root_id" c-selected="value" /></c-for>
          <p c-if="not roots" data-citry-ui-part="empty" c-$c-tr:citry-ui-cascader-empty="True if catalog_empty else None">{{ tr('citry-ui-cascader-empty') if catalog_empty else labels['empty'] }}</p>
        </div>
        <span data-citry-ui-part="inputs" hidden>
          <c-for each="segment in value"><input type="hidden" c-name="name" c-value="segment" c-form="form" c-disabled="disabled or name is None" /></c-for>
        </span>
        <span data-citry-ui-part="status" role="status" aria-live="polite" aria-atomic="true">{{ status }}</span>
      </div>
    """


class CInternalCascaderOption(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        option: _Option
        root_id: str
        selected: tuple[str, ...]
        level: int
        position: int
        set_size: int
        initial_focus: bool

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        option = kwargs.option
        path = option.path
        active = bool(option.children and kwargs.selected[: len(path)] == path)
        selected = kwargs.selected == path
        attrs = {
            **option.attrs,
            "id": _item_id(kwargs.root_id, path),
            "role": "treeitem",
            "tabindex": 0 if selected or kwargs.initial_focus else -1,
            "aria-label": option.label,
            "aria-level": kwargs.level,
            "aria-owns": _group_id(kwargs.root_id, path) if option.children else None,
            "aria-posinset": kwargs.position,
            "aria-setsize": kwargs.set_size,
            "aria-disabled": "true" if option.disabled else "false",
            "aria-expanded": ("true" if active else "false") if option.children else None,
            "aria-selected": "true" if selected else "false",
            "data-active": True if active else None,
            "data-citry-cascader-child-group": _group_id(kwargs.root_id, path) if option.children else None,
            "data-citry-cascader-parent": _item_id(kwargs.root_id, option.parent.path) if option.parent else None,
            "data-disabled": True if option.disabled else None,
            "data-level": kwargs.level,
            "data-selected": True if selected else None,
            "data-value": option.value,
        }
        return {
            "option": option,
            "attrs": attrs,
            "has_children": bool(option.children),
        }

    template = """
      <li c-bind="attrs" #c-key="option.value" data-citry-ui-part="option">
        <div data-citry-ui-part="option-row"><span data-citry-ui-part="option-label">{{ option.label }}</span><span c-if="has_children" aria-hidden="true" data-citry-ui-part="option-indicator">&#8250;</span></div>
      </li>
    """


class CInternalCascaderGroup(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        parent: _Option
        root_id: str
        selected: tuple[str, ...]

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        parent = kwargs.parent
        level = len(parent.path) + 1
        return {
            "group_id": _group_id(kwargs.root_id, parent.path),
            "level": level,
            "active": kwargs.selected[: len(parent.path)] == parent.path,
            "entries": _entries(parent.children, selected=kwargs.selected, root=False),
            "root_id": kwargs.root_id,
            "selected": kwargs.selected,
        }

    template = """
      <ul c-id="group_id" role="group" c-hidden="not active" data-citry-cascader-column c-data-level="level" data-citry-ui-part="group">
        <c-for each="entry in entries"><c-CInternalCascaderOption c-bind="entry" c-root_id="root_id" c-selected="selected" c-level="level" /></c-for>
      </ul>
    """


__all__ = [
    "CCascader",
    "CCascaderChangeSource",
    "CCascaderDefaultSlotData",
    "CCascaderOpenChangeDetail",
    "CCascaderOption",
    "CCascaderOptionDefaultSlotData",
    "CCascaderSize",
    "CCascaderValueChangeDetail",
    "CCascaderVariant",
]
