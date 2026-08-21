"""Standalone and grouped pressed Toggle Buttons."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CToggleVariant = Literal["soft", "outline", "plain"]
CToggleSize = Literal["sm", "md", "lg"]
CToggleOrientation = Literal["horizontal", "vertical"]
CToggleValue = str | None | Sequence[str]

_TOGGLE_CONTEXT_KEY = "citry_ui_toggle_group"
_VARIANTS = ("soft", "outline", "plain")
_SIZES = ("sm", "md", "lg")
_ORIENTATIONS = ("horizontal", "vertical")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_GROUP_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-orientation",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-grow",
        "data-mandatory",
        "data-multiple",
        "data-orientation",
        "data-size",
        "data-variant",
        "role",
        "tabindex",
    }
)
_TOGGLE_OWNED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-hidden",
        "aria-pressed",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-pressed",
        "data-size",
        "data-value",
        "data-variant",
        "disabled",
        "form",
        "role",
        "tabindex",
        "type",
        "value",
    }
)


class CToggleDefaultSlotData:
    pass


class CToggleGroupDefaultSlotData:
    pass


class CToggleValueChangeDetail(TypedDict):
    value: str | list[str] | None
    previousValue: str | list[str] | None
    source: Literal["activation"]


def _plain(input_name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        msg = f"{input_name} must be a string{' or None' if optional else ''}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain or "\x00" in plain:
        msg = f"{input_name} must be nonempty and cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _choice(component: str, name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(f"{component} {name}", value)
    if plain not in allowed:
        msg = f"{component} {name} must be one of {allowed!r}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(component: str, attrs: Mapping[str, object] | None, owned: frozenset[str]) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{component} attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{component} attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component} attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _DIRECTIVES:
            msg = f"{component} attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if _dynamic_target(normalized) in owned:
            msg = f"{component} attrs cannot dynamically bind owned attribute {key!r}."
            raise ValueError(msg)
    return copied


def _normalize_value(value: object, multiple: bool) -> str | tuple[str, ...] | None:
    raw = const_value(value)
    if multiple:
        if raw is None:
            return ()
        if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
            msg = "CToggleGroup value must be a sequence of strings in multiple mode."
            raise TypeError(msg)
        result = tuple(str(_plain("CToggleGroup value item", item)) for item in raw)
        if len(result) != len(set(result)):
            msg = "CToggleGroup value cannot contain duplicates."
            raise ValueError(msg)
        return result
    if isinstance(raw, Sequence) and not isinstance(raw, str):
        msg = "CToggleGroup value must be one string or None in single mode."
        raise TypeError(msg)
    return _plain("CToggleGroup value", raw, optional=True)


@dataclass(slots=True)
class _ToggleEntry:
    value: str
    disabled: bool


@dataclass(slots=True)
class _ToggleContext:
    selected: set[str]
    disabled: bool
    variant: str
    size: str
    entries: list[_ToggleEntry] = field(default_factory=list)


class CToggleGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        value: CToggleValue = None
        multiple: bool = False
        mandatory: bool = False
        disabled: bool = False
        orientation: CToggleOrientation = "horizontal"
        variant: CToggleVariant = "outline"
        size: CToggleSize = "md"
        grow: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CToggleGroupDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        label = _plain("CToggleGroup label", kwargs.label)
        validate_boolean("CToggleGroup", "multiple", kwargs.multiple)
        validate_boolean("CToggleGroup", "mandatory", kwargs.mandatory)
        validate_boolean("CToggleGroup", "disabled", kwargs.disabled)
        validate_boolean("CToggleGroup", "grow", kwargs.grow)
        multiple = bool(kwargs.multiple)
        normalized = _normalize_value(kwargs.value, multiple)
        selected = set(normalized if isinstance(normalized, tuple) else (() if normalized is None else (normalized,)))
        orientation = _choice("CToggleGroup", "orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _choice("CToggleGroup", "variant", kwargs.variant, _VARIANTS)
        size = _choice("CToggleGroup", "size", kwargs.size, _SIZES)
        if kwargs.mandatory and not selected:
            msg = "CToggleGroup mandatory=True requires an initial value."
            raise ValueError(msg)
        context = _ToggleContext(selected, bool(kwargs.disabled), variant, size)
        self.provide(_TOGGLE_CONTEXT_KEY, context=context)
        self._toggle_context = context
        self._toggle_value = normalized
        form = self.inject(FORM_CONTEXT_KEY, None)
        form_disabled = bool(form.disabled if form is not None else False)
        disabled = bool(kwargs.disabled) or form_disabled
        context.disabled = disabled
        return {
            "label": label,
            "value": list(normalized) if isinstance(normalized, tuple) else normalized,
            "multiple": multiple,
            "mandatory": bool(kwargs.mandatory),
            "disabled": disabled,
            "orientation": orientation,
            "variant": variant,
            "size": size,
            "grow": bool(kwargs.grow),
            "attrs": merge_root_attrs(_attrs("CToggleGroup", kwargs.attrs, _GROUP_OWNED), kwargs.class_, kwargs.style),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CToggleGroup completed without a render result.")
        entries = self._toggle_context.entries
        if not entries:
            raise ValueError("CToggleGroup requires at least one descendant CToggle.")
        values = [entry.value for entry in entries]
        if len(values) != len(set(values)):
            raise ValueError("CToggleGroup requires unique CToggle values.")
        unknown = self._toggle_context.selected.difference(values)
        if unknown:
            raise ValueError(f"CToggleGroup value contains unknown Toggles: {sorted(unknown)!r}.")

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "value": list(self._toggle_value) if isinstance(self._toggle_value, tuple) else self._toggle_value,
            "multiple": bool(kwargs.multiple),
            "mandatory": bool(kwargs.mandatory),
            "disabled": bool(kwargs.disabled),
            "orientation": _choice("CToggleGroup", "orientation", kwargs.orientation, _ORIENTATIONS),
            "variant": _choice("CToggleGroup", "variant", kwargs.variant, _VARIANTS),
            "size": _choice("CToggleGroup", "size", kwargs.size, _SIZES),
        }

    template = """
      <div
        class="cui-toggle-group"
        c-bind="attrs"
        data-citry-ui-part="toggle-group"
        c-data-multiple="multiple"
        c-data-mandatory="mandatory"
        c-data-disabled="disabled"
        c-data-orientation="orientation"
        c-data-variant="variant"
        c-data-size="size"
        c-data-grow="grow"
        role="group"
        c-aria-label="label"
      >
        <c-slot required />
      </div>
    """

    js = r"""
      $component({
        props: {value: {}, disabled: {}, orientation: {}, variant: {}, size: {}, onValueChange: {}},
        init: ({els, data, props, effect, inject}) => {
          const root = els[0];
          const form = inject(Symbol.for("citry-ui:form"), null);
          const owned = () => [...root.querySelectorAll('[data-citry-ui-part="toggle"]')]
            .filter((item) => item.closest('[data-citry-ui-part="toggle-group"]') === root);
          const known = () => new Set(owned().map((item) => item.dataset.value));
          const invalid = new Set();
          let current = data.multiple ? new Set(data.value ?? []) : data.value;
          let callback = null;
          const report = (name, value) => {
            if (invalid.has(name)) return;
            invalid.add(name);
            console.error(`[citry-ui] CToggleGroup ${name} received invalid client value`, value);
          };
          const normalize = (value) => {
            const values = known();
            if (data.multiple) {
              if (!Array.isArray(value)) return undefined;
              const next = value.map((item) => typeof item === "string" ? item.replace(/\r\n?/g, "\n") : null);
              if (next.includes(null) || new Set(next).size !== next.length
                  || next.some((item) => !values.has(item))) return undefined;
              return new Set(next);
            }
            if (value === null) return null;
            if (typeof value !== "string") return undefined;
            const next = value.replace(/\r\n?/g, "\n");
            return values.has(next) ? next : undefined;
          };
          const snapshot = (value) => data.multiple ? [...value] : value;
          const apply = (value) => {
            current = value;
            const selected = data.multiple ? value : new Set(value === null ? [] : [value]);
            owned().forEach((item) => {
              const pressed = selected.has(item.dataset.value);
              item.setAttribute("aria-pressed", String(pressed));
              item.toggleAttribute("data-pressed", pressed);
            });
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalid.delete(name); return fallback; }
            if (typeof supplied === "string" && allowed.includes(supplied)) { invalid.delete(name); return supplied; }
            report(name, supplied);
            return fallback;
          };
          const reconcile = () => {
            callback = typeof props.onValueChange === "function" ? props.onValueChange : null;
            const disabled = props.disabled === undefined ? data.disabled : props.disabled;
            if (typeof disabled !== "boolean") report("disabled", disabled);
            else invalid.delete("disabled");
            const localDisabled = typeof disabled === "boolean" ? disabled : data.disabled;
            const effectiveDisabled = Boolean(form?.disabled) || localDisabled;
            root.toggleAttribute("data-disabled", effectiveDisabled);
            root.dataset.orientation = resolveChoice("orientation", data.orientation, ["horizontal", "vertical"]);
            const variant = resolveChoice("variant", data.variant, ["soft", "outline", "plain"]);
            const size = resolveChoice("size", data.size, ["sm", "md", "lg"]);
            root.dataset.variant = variant;
            root.dataset.size = size;
            owned().forEach((item) => {
              item.disabled = effectiveDisabled || item.hasAttribute("data-item-disabled");
              item.dataset.variant = variant;
              item.dataset.size = size;
            });
            if (props.value !== undefined) {
              const next = normalize(props.value);
              if (next === undefined) report("value", props.value);
              else { invalid.delete("value"); apply(next); }
            }
          };
          const onClick = (event) => {
            const item = event.target.closest?.('[data-citry-ui-part="toggle"]');
            if (!item || item.closest('[data-citry-ui-part="toggle-group"]') !== root || item.disabled) return;
            const previous = snapshot(current);
            let next;
            if (data.multiple) {
              next = new Set(current);
              if (next.has(item.dataset.value)) {
                if (data.mandatory && next.size === 1) return;
                next.delete(item.dataset.value);
              } else next.add(item.dataset.value);
            } else {
              next = current === item.dataset.value ? (data.mandatory ? current : null) : item.dataset.value;
              if (next === current) return;
            }
            const publicValue = snapshot(next);
            callback?.(publicValue, {value: publicValue, previousValue: previous, source: "activation"});
            if (props.value === undefined) apply(next);
            else setTimeout(reconcile, 0);
          };
          root.addEventListener("click", onClick, true);
          const stop = effect(reconcile);
          root.setAttribute("data-citry-toggle-group-initialized", "");
          return () => {
            stop?.();
            root.removeEventListener("click", onClick, true);
            root.removeAttribute("data-citry-toggle-group-initialized");
          };
        },
      })
    """


class CToggle(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str | None = None
        pressed: bool = False
        disabled: bool = False
        variant: CToggleVariant | None = None
        size: CToggleSize | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CToggleDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        context_value = self.inject(_TOGGLE_CONTEXT_KEY, None)
        context: _ToggleContext | None = context_value.context if context_value is not None else None
        value = _plain("CToggle value", kwargs.value, optional=True)
        if context is not None and value is None:
            raise ValueError("CToggle inside CToggleGroup requires value.")
        if context is None and value is not None:
            value = str(value)
        validate_boolean("CToggle", "pressed", kwargs.pressed)
        validate_boolean("CToggle", "disabled", kwargs.disabled)
        raw_variant = const_value(kwargs.variant)
        raw_size = const_value(kwargs.size)
        if context is not None and (raw_variant is not None or raw_size is not None):
            raise ValueError("CToggleGroup owns variant and size for grouped CToggle children.")
        variant = (
            context.variant
            if context is not None
            else _choice("CToggle", "variant", "outline" if raw_variant is None else raw_variant, _VARIANTS)
        )
        size = (
            context.size
            if context is not None
            else _choice("CToggle", "size", "md" if raw_size is None else raw_size, _SIZES)
        )
        form = self.inject(FORM_CONTEXT_KEY, None)
        form_disabled = bool(form.disabled if form is not None else False)
        group_disabled = context.disabled if context is not None else False
        effective_disabled = bool(kwargs.disabled) or group_disabled or form_disabled
        pressed = (context is not None and str(value) in context.selected) or (
            context is None and bool(kwargs.pressed)
        )
        if context is not None:
            context.entries.append(_ToggleEntry(str(value), bool(kwargs.disabled)))
        self._toggle_variant = variant
        self._toggle_size = size
        return {
            "value": value,
            "pressed": pressed,
            "disabled": effective_disabled,
            "item_disabled": bool(kwargs.disabled),
            "variant": variant,
            "size": size,
            "grouped": context is not None,
            "attrs": merge_root_attrs(_attrs("CToggle", kwargs.attrs, _TOGGLE_OWNED), kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "pressed": bool(kwargs.pressed),
            "disabled": bool(kwargs.disabled),
            "variant": self._toggle_variant,
            "size": self._toggle_size,
        }

    template = """
      <button
        class="cui-toggle"
        c-bind="attrs"
        data-citry-ui-part="toggle"
        c-data-value="value"
        c-data-pressed="pressed"
        c-data-disabled="disabled"
        c-data-item-disabled="item_disabled"
        c-data-variant="variant"
        c-data-size="size"
        c-data-grouped="grouped"
        type="button"
        c-disabled="disabled"
        c-aria-pressed="'true' if pressed else 'false'"
      >
        <c-slot required />
      </button>
    """

    js = r"""
      $component({
        props: {pressed: {}, disabled: {}, variant: {}, size: {}, onPressedChange: {}},
        init: ({els, data, props, effect, inject}) => {
          const root = els[0];
          const groupRoot = root.closest('[data-citry-ui-part="toggle-group"]');
          const form = inject(Symbol.for("citry-ui:form"), null);
          const grouped = groupRoot !== null;
          let pressed = data.pressed;
          let localDisabled = data.disabled;
          let localVariant = data.variant;
          let localSize = data.size;
          let callback = null;
          const invalid = new Set();
          const report = (name, value) => {
            if (invalid.has(name)) return;
            invalid.add(name);
            console.error(`[citry-ui] CToggle ${name} received invalid client value`, value);
          };
          const apply = () => {
            if (props.disabled === undefined) {
              invalid.delete("disabled");
              localDisabled = data.disabled;
            } else if (typeof props.disabled === "boolean") {
              invalid.delete("disabled");
              localDisabled = props.disabled;
            } else report("disabled", props.disabled);
            root.toggleAttribute("data-item-disabled", localDisabled);
            if (grouped) {
              const effectiveDisabled = grouped
                ? groupRoot.hasAttribute("data-disabled") || localDisabled
                : localDisabled;
              root.disabled = effectiveDisabled;
              root.toggleAttribute("data-disabled", effectiveDisabled);
              for (const name of ["pressed", "variant", "size"]) {
                if (props[name] === undefined) invalid.delete(name);
                else report(name, props[name]);
              }
            } else {
              const effectiveDisabled = Boolean(form?.disabled) || localDisabled;
              root.disabled = effectiveDisabled;
              root.toggleAttribute("data-disabled", effectiveDisabled);
              const choices = {variant: ["soft", "outline", "plain"], size: ["sm", "md", "lg"]};
              for (const [name, allowed] of Object.entries(choices)) {
                if (props[name] === undefined) {
                  invalid.delete(name);
                  if (name === "variant") localVariant = data.variant;
                  else localSize = data.size;
                } else if (allowed.includes(props[name])) {
                  invalid.delete(name);
                  if (name === "variant") localVariant = props[name];
                  else localSize = props[name];
                } else report(name, props[name]);
              }
              root.dataset.variant = localVariant;
              root.dataset.size = localSize;
            }
            callback = typeof props.onPressedChange === "function" ? props.onPressedChange : null;
            if (!grouped && props.pressed === undefined) invalid.delete("pressed");
            else if (!grouped && typeof props.pressed === "boolean") {
              invalid.delete("pressed");
              pressed = props.pressed;
              root.setAttribute("aria-pressed", String(pressed));
              root.toggleAttribute("data-pressed", pressed);
            } else if (!grouped) report("pressed", props.pressed);
          };
          const onClick = () => {
            if (grouped || root.disabled) return;
            const previousValue = pressed;
            const value = !pressed;
            callback?.(value, {value, previousValue, source: "activation"});
            if (props.pressed === undefined) {
              pressed = value;
              root.setAttribute("aria-pressed", String(value));
              root.toggleAttribute("data-pressed", value);
            } else setTimeout(apply, 0);
          };
          root.addEventListener("click", onClick);
          const stop = effect(apply);
          root.setAttribute("data-citry-toggle-initialized", "");
          return () => {
            stop?.();
            root.removeEventListener("click", onClick);
            root.removeAttribute("data-citry-toggle-initialized");
          };
        },
      })
    """

    css_file = "runtime.min.css"


__all__ = [
    "CToggle",
    "CToggleDefaultSlotData",
    "CToggleGroup",
    "CToggleGroupDefaultSlotData",
    "CToggleOrientation",
    "CToggleSize",
    "CToggleValue",
    "CToggleValueChangeDetail",
    "CToggleVariant",
]
