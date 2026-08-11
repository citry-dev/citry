"""Labelled descriptive and interactive Tag collections."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CTagSelectionMode = Literal["none", "single", "multiple"]
CTagVariant = Literal["soft", "solid", "outline"]
CTagSize = Literal["sm", "md", "lg"]
CTagValue = str | None | Sequence[str]

_TAG_CONTEXT_KEY = "citry_ui_tag_group"
_SELECTION_MODES = ("none", "single", "multiple")
_VARIANTS = ("soft", "solid", "outline")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "x-bind",
        "x-for",
        "x-html",
        "x-if",
        "x-ignore",
        "x-model",
        "x-modelable",
        "x-teleport",
        "x-text",
    }
)
_COMMON_OWNED = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_GROUP_OWNED = _COMMON_OWNED | frozenset(
    {
        "aria-describedby",
        "aria-label",
        "aria-labelledby",
        "data-actionable",
        "data-citry-ui-part",
        "data-disabled",
        "data-removable",
        "data-selection-mode",
        "data-size",
        "data-variant",
        "id",
    }
)
_TAG_OWNED = _COMMON_OWNED | frozenset(
    {
        "aria-disabled",
        "aria-selected",
        "data-citry-ui-part",
        "data-disabled",
        "data-removable",
        "data-selected",
        "data-size",
        "data-value",
        "data-variant",
        "id",
    }
)


class CTagGroupDefaultSlotData:
    pass


class CTagGroupLabelSlotData:
    pass


class CTagGroupDescriptionSlotData:
    pass


class CTagDefaultSlotData:
    pass


class CTagStartSlotData:
    pass


class CTagValueChangeDetail(TypedDict):
    value: str | list[str] | None
    previousValue: str | list[str] | None
    tagValue: str
    source: Literal["activation"]
    controlled: bool
    nativeEvent: object


class CTagActionDetail(TypedDict):
    value: str
    source: Literal["activation"]
    nativeEvent: object


class CTagRemoveDetail(TypedDict):
    values: list[str]
    tagValue: str
    source: Literal["remove-button", "delete-key"]
    nativeEvent: object


def _plain(input_name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        suffix = " or None" if optional else ""
        msg = f"{input_name} must be a string{suffix}, got {raw!r}."
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


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    component: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
) -> dict[str, object]:
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
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{component} attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if _dynamic_target(normalized) in owned:
            msg = f"{component} attrs cannot dynamically bind owned attribute {key!r}."
            raise ValueError(msg)
    return copied


def _normalize_server_value(value: object, mode: str) -> str | tuple[str, ...] | None:
    raw = const_value(value)
    if mode == "none":
        if raw not in (None, (), []):
            raise ValueError("CTagGroup value must be empty when selection_mode='none'.")
        return None
    if mode == "multiple":
        if raw is None:
            return ()
        if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
            raise TypeError("CTagGroup value must be a sequence of strings in multiple mode.")
        normalized = tuple(str(_plain("CTagGroup value item", item)) for item in raw)
        if len(normalized) != len(set(normalized)):
            raise ValueError("CTagGroup value cannot contain duplicates.")
        return normalized
    if isinstance(raw, Sequence) and not isinstance(raw, str):
        raise TypeError("CTagGroup value must be one string or None in single mode.")
    return _plain("CTagGroup value", raw, optional=True)


@dataclass(slots=True)
class _TagEntry:
    value: str
    disabled: bool


@dataclass(slots=True)
class _TagContext:
    group_id: str
    mode: str
    selected: set[str]
    disabled: bool
    actionable: bool
    removable: bool
    remove_label: str
    variant: str
    size: str
    entries: list[_TagEntry] = field(default_factory=list)
    roving_assigned: bool = False


class CTagGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        id: str | None = None
        value: CTagValue = None
        selection_mode: CTagSelectionMode = "none"
        mandatory: bool = False
        actionable: bool = False
        removable: bool = False
        remove_label: str = "Remove"
        disabled: bool = False
        variant: CTagVariant = "soft"
        size: CTagSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTagGroupDefaultSlotData]
        label: SlotInput[CTagGroupLabelSlotData] | None = None
        description: SlotInput[CTagGroupDescriptionSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        label = _plain("CTagGroup label", kwargs.label)
        group_id = _plain("CTagGroup id", kwargs.id, optional=True)
        validate_html_id("CTagGroup", group_id)
        if group_id is not None and "\x00" in group_id:
            raise ValueError("CTagGroup id cannot contain U+0000.")
        group_id = group_id or f"cui-tag-group-{self.id}"
        mode = _choice("CTagGroup", "selection_mode", kwargs.selection_mode, _SELECTION_MODES)
        variant = _choice("CTagGroup", "variant", kwargs.variant, _VARIANTS)
        size = _choice("CTagGroup", "size", kwargs.size, _SIZES)
        for name in ("mandatory", "actionable", "removable", "disabled"):
            validate_boolean("CTagGroup", name, getattr(kwargs, name))
        if kwargs.mandatory and mode == "none":
            raise ValueError("CTagGroup mandatory requires a selectable mode.")
        remove_label = _plain("CTagGroup remove_label", kwargs.remove_label)
        value = _normalize_server_value(kwargs.value, mode)
        selected = set(value if isinstance(value, tuple) else (() if value is None else (value,)))
        if kwargs.mandatory and not selected:
            raise ValueError("CTagGroup mandatory=True requires an initial value.")
        form = self.inject(FORM_CONTEXT_KEY, None)
        effective_disabled = bool(kwargs.disabled) or bool(form.disabled if form is not None else False)
        context = _TagContext(
            group_id=group_id,
            mode=mode,
            selected=selected,
            disabled=effective_disabled,
            actionable=bool(kwargs.actionable),
            removable=bool(kwargs.removable),
            remove_label=str(remove_label),
            variant=variant,
            size=size,
        )
        self.provide(_TAG_CONTEXT_KEY, context=context)
        self._tag_context = context
        self._tag_value = value
        interactive = mode != "none" or bool(kwargs.actionable) or bool(kwargs.removable)
        label_id = f"{group_id}-label"
        description_id = f"{group_id}-description"
        return {
            "group_id": group_id,
            "label": label,
            "label_id": label_id,
            "description_id": description_id,
            "has_label_slot": "label" in self.raw_slots,
            "has_description": "description" in self.raw_slots,
            "mode": mode,
            "mandatory": bool(kwargs.mandatory),
            "actionable": bool(kwargs.actionable),
            "removable": bool(kwargs.removable),
            "disabled": effective_disabled,
            "variant": variant,
            "size": size,
            "interactive": interactive,
            "list_role": "grid" if interactive else "list",
            "attrs": merge_root_attrs(
                _copy_attrs("CTagGroup", kwargs.attrs, _GROUP_OWNED),
                kwargs.class_,
                kwargs.style,
            ),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CTagGroup completed without a render result.")
        entries = self._tag_context.entries
        values = [entry.value for entry in entries]
        if len(values) != len(set(values)):
            raise ValueError("CTagGroup requires unique CTag values.")
        unknown = self._tag_context.selected.difference(values)
        if unknown:
            raise ValueError(f"CTagGroup value contains unknown Tags: {sorted(unknown)!r}.")

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        value = self._tag_value
        return {
            "value": list(value) if isinstance(value, tuple) else value,
            "serverValueFingerprint": repr(value),
            "selectionMode": _choice("CTagGroup", "selection_mode", kwargs.selection_mode, _SELECTION_MODES),
            "mandatory": bool(kwargs.mandatory),
            "actionable": bool(kwargs.actionable),
            "removable": bool(kwargs.removable),
            "disabled": bool(kwargs.disabled),
            "variant": _choice("CTagGroup", "variant", kwargs.variant, _VARIANTS),
            "size": _choice("CTagGroup", "size", kwargs.size, _SIZES),
        }

    template = """
      <div
        class="cui-tag-group"
        c-id="group_id"
        c-bind="attrs"
        data-citry-ui-part="tag-group"
        c-data-selection-mode="mode"
        c-data-actionable="actionable"
        c-data-removable="removable"
        c-data-disabled="disabled"
        c-data-variant="variant"
        c-data-size="size"
      >
        <div class="cui-tag-group__label" c-id="label_id" data-citry-ui-part="group-label">
          <c-if cond="has_label_slot"><c-slot name="label" /></c-if>
          <c-else>{{ label }}</c-else>
        </div>
        <div
          class="cui-tag-group__list"
          data-citry-ui-part="list"
          c-role="list_role"
          c-aria-labelledby="label_id"
          c-aria-describedby="description_id if has_description else None"
          c-tabindex="-1 if interactive else None"
        >
          <c-slot required />
        </div>
        <c-if cond="has_description">
          <div
            class="cui-tag-group__description"
            c-id="description_id"
            data-citry-ui-part="description"
          ><c-slot name="description" /></div>
        </c-if>
      </div>
    """

    js = r"""
      $component({
        props: {
          value: {}, disabled: {}, variant: {}, size: {},
          onValueChange: {}, onAction: {}, onRemove: {},
        },
        init: ({els, data, props, effect, inject}) => {
          const root = els[0];
          const list = root.querySelector(':scope > [data-citry-ui-part="list"]');
          const form = inject(Symbol.for("citry-ui:form"), null);
          const invalidEpisodes = new Set();
          const registrations = new Map();
          const runtime = root.__citryUiTagRuntime ?? {
            selection: data.selectionMode === "multiple" ? [] : null,
            serverValueFingerprint: null,
            focusedValue: null,
            order: [],
          };
          root.__citryUiTagRuntime = runtime;
          if (runtime.serverValueFingerprint !== data.serverValueFingerprint) {
            runtime.selection = data.selectionMode === "multiple" ? [...(data.value ?? [])] : data.value;
            runtime.serverValueFingerprint = data.serverValueFingerprint;
          }
          let committed = data.selectionMode === "multiple"
            ? new Set(runtime.selection ?? [])
            : runtime.selection;
          let controlled = false;
          let reconcileTimer = null;
          let typeaheadTimer = null;
          let typeaheadBuffer = "";
          let focusWithin = false;
          let structureInvalid = false;
          let generation = 1;
          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CTagGroup ${name} received invalid client value`, value);
          };
          const clearEpisode = (name) => invalidEpisodes.delete(name);
          const directTags = () => [...list.querySelectorAll(':scope > [data-citry-ui-part="tag"]')];
          const entries = () => directTags().map((tag) => registrations.get(tag)).filter(Boolean);
          const canonical = (value) => typeof value === "string" && !value.includes("\0")
            ? value.replace(/\r\n?/g, "\n") : null;
          const known = () => new Set(entries().map((entry) => entry.value));
          const publicValue = (value) => data.selectionMode === "multiple" ? [...value] : value;
          const selectedSet = (value) => data.selectionMode === "multiple"
            ? value : new Set(value === null ? [] : [value]);
          const validCallback = (name) => {
            const supplied = props[name];
            if (supplied === undefined || supplied === null) { clearEpisode(name); return null; }
            if (typeof supplied === "function") { clearEpisode(name); return supplied; }
            report(name, supplied);
            return null;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { clearEpisode(name); return fallback; }
            if (typeof supplied === "string" && allowed.includes(supplied)) {
              clearEpisode(name); return supplied;
            }
            report(name, supplied);
            return fallback;
          };
          const inDisabledFieldset = () => {
            let node = root.parentElement;
            while (node) {
              if (node instanceof HTMLFieldSetElement && node.disabled) {
                const firstLegend = [...node.children].find((child) => child instanceof HTMLLegendElement);
                if (!firstLegend || !firstLegend.contains(root)) return true;
              }
              node = node.parentElement;
            }
            return false;
          };
          const localDisabled = () => {
            if (props.disabled === undefined) { clearEpisode("disabled"); return data.disabled; }
            if (typeof props.disabled === "boolean") { clearEpisode("disabled"); return props.disabled; }
            report("disabled", props.disabled);
            return data.disabled;
          };
          const effectiveGroupDisabled = () => Boolean(form?.disabled) || inDisabledFieldset() || localDisabled();
          const validStructure = () => {
            const children = [...list.children];
            if (children.some((child) => !child.matches('[data-citry-ui-part="tag"]'))) return false;
            if (children.some((child) => !registrations.has(child))) return false;
            const values = children.map((child) => child.dataset.value);
            if (values.length !== new Set(values).size) return false;
            const interactiveSelector = [
              "a[href]", "button", "input", "select", "textarea", "label",
              "[contenteditable]:not([contenteditable='false'])", "[tabindex]",
            ].join(",");
            return !children.some((tag) => [...tag.querySelectorAll(
              '[data-citry-ui-part="tag-label"], [data-citry-ui-part="start"]'
            )].some((region) => region.matches(interactiveSelector) || region.querySelector(interactiveSelector)));
          };
          const nearest = (priorOrder, missingValue, candidates) => {
            const priorIndex = priorOrder.indexOf(missingValue);
            if (priorIndex < 0) return candidates[0] ?? null;
            for (let distance = 1; distance <= priorOrder.length; distance += 1) {
              const following = priorOrder[priorIndex + distance];
              const preceding = priorOrder[priorIndex - distance];
              const foundFollowing = candidates.find((entry) => entry.value === following);
              if (foundFollowing) return foundFollowing;
              const foundPreceding = candidates.find((entry) => entry.value === preceding);
              if (foundPreceding) return foundPreceding;
            }
            return candidates[0] ?? null;
          };
          const normalizeClientValue = (supplied) => {
            const values = known();
            if (data.selectionMode === "multiple") {
              if (!Array.isArray(supplied)) return null;
              const normalized = supplied.map(canonical);
              if (normalized.includes(null) || new Set(normalized).size !== normalized.length) return null;
              const knownValues = normalized.filter((value) => values.has(value));
              return {value: new Set(knownValues), invalid: knownValues.length !== normalized.length};
            }
            if (supplied === null) return {value: null, invalid: false};
            const normalized = canonical(supplied);
            if (normalized === null) return null;
            return {value: values.has(normalized) ? normalized : null, invalid: !values.has(normalized)};
          };
          const applySelection = (value) => {
            committed = value;
            runtime.selection = publicValue(value);
            const selected = selectedSet(value);
            entries().forEach((entry) => {
              const isSelected = selected.has(entry.value);
              entry.root.toggleAttribute("data-selected", isSelected);
              if (data.selectionMode !== "none") entry.root.setAttribute("aria-selected", String(isSelected));
              else entry.root.removeAttribute("aria-selected");
              entry.indicator.hidden = !isSelected;
            });
          };
          const applyRoving = (groupDisabled) => {
            const enabled = entries().filter((entry) => !groupDisabled && !entry.disabled);
            let current = enabled.find((entry) => entry.value === runtime.focusedValue) ?? enabled[0] ?? null;
            if (runtime.focusedValue && !entries().some((entry) => entry.value === runtime.focusedValue)) {
              current = nearest(runtime.order, runtime.focusedValue, enabled);
              if (focusWithin && current) queueMicrotask(() => current.root.focus());
              else if (focusWithin && !current) queueMicrotask(() => list.focus());
            }
            runtime.focusedValue = current?.value ?? null;
            entries().forEach((entry) => { entry.root.tabIndex = entry === current ? 0 : -1; });
          };
          const reconcile = () => {
            reconcileTimer = null;
            if (!validStructure()) {
              structureInvalid = true;
              report("structure", "Tag content must remain direct and noninteractive");
              list.inert = true;
              entries().forEach((entry) => { entry.root.tabIndex = -1; });
              root.removeAttribute("data-citry-tag-group-initialized");
              return;
            }
            structureInvalid = false;
            clearEpisode("structure");
            list.inert = false;
            const currentEntries = entries();
            const currentOrder = currentEntries.map((entry) => entry.value);
            const groupDisabled = effectiveGroupDisabled();
            const variant = resolveChoice("variant", data.variant, ["soft", "solid", "outline"]);
            const size = resolveChoice("size", data.size, ["sm", "md", "lg"]);
            root.toggleAttribute("data-disabled", groupDisabled);
            root.dataset.variant = variant;
            root.dataset.size = size;
            currentEntries.forEach((entry) => {
              entry.disabled = groupDisabled || entry.localDisabled;
              entry.root.toggleAttribute("data-disabled", entry.disabled);
              entry.root.setAttribute("aria-disabled", String(entry.disabled));
              entry.root.dataset.variant = variant;
              entry.root.dataset.size = size;
              if (entry.remove) entry.remove.disabled = entry.disabled;
            });
            controlled = props.value !== undefined;
            if (controlled && data.selectionMode !== "none") {
              const normalized = normalizeClientValue(props.value);
              if (normalized === null) report("value", props.value);
              else {
                if (normalized.invalid) report("value", props.value); else clearEpisode("value");
                applySelection(normalized.value);
              }
            } else if (!controlled) {
              clearEpisode("value");
              if (data.selectionMode === "multiple") {
                const surviving = new Set([...committed].filter((value) => known().has(value)));
                applySelection(surviving);
              } else if (committed !== null && !known().has(committed)) applySelection(null);
              else applySelection(committed);
            }
            applyRoving(groupDisabled);
            runtime.order = currentOrder;
            if (groupDisabled && focusWithin) queueMicrotask(() => list.focus());
            root.setAttribute("data-citry-tag-group-initialized", "");
          };
          const schedule = () => {
            if (reconcileTimer !== null) return;
            reconcileTimer = setTimeout(reconcile, 0);
          };
          root.__citryTagRegister = (entry) => {
            registrations.set(entry.root, entry);
            schedule();
            return () => { registrations.delete(entry.root); schedule(); };
          };
          const ownedEntry = (target) => {
            const tag = target.closest?.('[data-citry-ui-part="tag"]');
            return tag?.closest('[data-citry-ui-part="tag-group"]') === root ? registrations.get(tag) : null;
          };
          const focusEntry = (entry) => {
            if (!entry || entry.disabled) return;
            runtime.focusedValue = entry.value;
            entries().forEach((candidate) => { candidate.root.tabIndex = candidate === entry ? 0 : -1; });
            entry.root.focus();
          };
          const requestRemove = (entry, source, nativeEvent) => {
            if (structureInvalid || !data.removable || entry.disabled) return;
            const callback = validCallback("onRemove");
            const selected = selectedSet(committed);
            const values = data.selectionMode === "multiple" && selected.has(entry.value)
              ? entries().filter((item) => selected.has(item.value) && !item.disabled).map((item) => item.value)
              : [entry.value];
            callback?.([...values], {
              values: [...values], tagValue: entry.value, source, nativeEvent,
            });
          };
          const activate = (entry, nativeEvent) => {
            if (structureInvalid || !entry || entry.disabled) return;
            const beforeGeneration = generation;
            if (data.selectionMode !== "none") {
              const previous = publicValue(committed);
              let next;
              if (data.selectionMode === "multiple") {
                next = new Set(committed);
                if (next.has(entry.value)) {
                  if (!data.mandatory || next.size > 1) next.delete(entry.value);
                } else next.add(entry.value);
              } else {
                next = committed === entry.value && !data.mandatory ? null : entry.value;
              }
              const changed = JSON.stringify(publicValue(next)) !== JSON.stringify(previous);
              if (changed) {
                validCallback("onValueChange")?.(publicValue(next), {
                  value: publicValue(next), previousValue: previous, tagValue: entry.value,
                  source: "activation", controlled, nativeEvent,
                });
                if (!controlled) applySelection(next);
                else schedule();
              }
            }
            if (generation === beforeGeneration && data.actionable) {
              validCallback("onAction")?.(entry.value, {
                value: entry.value, source: "activation", nativeEvent,
              });
            }
          };
          const onClick = (event) => {
            const entry = ownedEntry(event.target);
            if (!entry) return;
            if (event.target.closest?.('[data-citry-ui-part="remove"]')) {
              event.preventDefault();
              event.stopPropagation();
              requestRemove(entry, "remove-button", event);
              return;
            }
            focusEntry(entry);
            activate(entry, event);
          };
          const normalizedText = (entry) => {
            const raw = entry.textValue || entry.label.textContent || "";
            return raw.replace(/\s+/g, " ").trim();
          };
          const lower = (value) => {
            const lang = root.closest("[lang]")?.getAttribute("lang") || document.documentElement.lang;
            try { return lang ? value.toLocaleLowerCase(lang) : value.toLocaleLowerCase(); }
            catch { return value.toLowerCase(); }
          };
          const move = (entry, direction) => {
            const enabled = entries().filter((candidate) => !candidate.disabled);
            const index = enabled.indexOf(entry);
            if (index < 0 || !enabled.length) return;
            focusEntry(enabled[(index + direction + enabled.length) % enabled.length]);
          };
          const onKeyDown = (event) => {
            const entry = ownedEntry(event.target);
            if (!entry) return;
            if (event.target.closest?.('[data-citry-ui-part="remove"]')) {
              if (event.key === "Tab" && event.shiftKey) {
                event.preventDefault(); focusEntry(entry);
              }
              return;
            }
            const rtl = getComputedStyle(root).direction === "rtl";
            if (["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(event.key)) {
              event.preventDefault();
              const forward = event.key === "ArrowDown" || event.key === (rtl ? "ArrowLeft" : "ArrowRight");
              move(entry, forward ? 1 : -1); return;
            }
            if (event.key === "Home" || event.key === "End") {
              event.preventDefault();
              const enabled = entries().filter((candidate) => !candidate.disabled);
              focusEntry(event.key === "Home" ? enabled[0] : enabled.at(-1)); return;
            }
            if ((event.key === "Delete" || event.key === "Backspace") && data.removable) {
              event.preventDefault(); requestRemove(entry, "delete-key", event); return;
            }
            if (event.key === "Tab" && !event.shiftKey && data.removable && entry.remove && !entry.disabled) {
              event.preventDefault(); entry.remove.focus(); return;
            }
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault(); activate(entry, event); return;
            }
            if (!event.isComposing && !event.ctrlKey && !event.metaKey && !event.altKey
                && event.key.length === 1) {
              event.preventDefault();
              const char = lower(event.key);
              typeaheadBuffer = typeaheadBuffer && [...typeaheadBuffer].every((item) => item === char)
                ? char : typeaheadBuffer + char;
              clearTimeout(typeaheadTimer);
              typeaheadTimer = setTimeout(() => { typeaheadBuffer = ""; }, 500);
              const enabled = entries().filter((candidate) => !candidate.disabled);
              const start = enabled.indexOf(entry);
              for (let offset = 1; offset <= enabled.length; offset += 1) {
                const candidate = enabled[(start + offset) % enabled.length];
                if (lower(normalizedText(candidate)).startsWith(typeaheadBuffer)) {
                  focusEntry(candidate); break;
                }
              }
            }
          };
          const onFocusIn = (event) => {
            focusWithin = true;
            const entry = ownedEntry(event.target);
            if (entry) runtime.focusedValue = entry.value;
          };
          const onFocusOut = () => setTimeout(() => {
            focusWithin = root.contains(root.ownerDocument.activeElement);
          }, 0);
          root.addEventListener("click", onClick, true);
          root.addEventListener("keydown", onKeyDown, true);
          root.addEventListener("focusin", onFocusIn, true);
          root.addEventListener("focusout", onFocusOut);
          const fieldsets = [];
          let ancestor = root.parentElement;
          while (ancestor) {
            if (ancestor instanceof HTMLFieldSetElement) fieldsets.push(ancestor);
            ancestor = ancestor.parentElement;
          }
          const fieldsetObserver = fieldsets.length ? new MutationObserver(schedule) : null;
          fieldsets.forEach((fieldset) => fieldsetObserver.observe(fieldset, {
            attributes: true, attributeFilter: ["disabled"], childList: true,
          }));
          const structureObserver = new MutationObserver((records) => {
            if (records.some((record) => record.type === "childList"
              || record.target.closest?.('[data-citry-ui-part="tag-label"], [data-citry-ui-part="start"]'))) {
              schedule();
            }
          });
          structureObserver.observe(list, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ["contenteditable", "href", "tabindex"],
          });
          const stop = effect(() => {
            void props.value;
            void props.disabled;
            void props.variant;
            void props.size;
            void props.onValueChange;
            void props.onAction;
            void props.onRemove;
            void form?.disabled;
            schedule();
          });
          schedule();
          return () => {
            generation += 1;
            stop?.();
            fieldsetObserver?.disconnect();
            structureObserver.disconnect();
            clearTimeout(reconcileTimer);
            clearTimeout(typeaheadTimer);
            root.removeEventListener("click", onClick, true);
            root.removeEventListener("keydown", onKeyDown, true);
            root.removeEventListener("focusin", onFocusIn, true);
            root.removeEventListener("focusout", onFocusOut);
            root.removeAttribute("data-citry-tag-group-initialized");
            delete root.__citryTagRegister;
          };
        },
      })
    """


class CTag(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        text_value: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTagDefaultSlotData]
        start: SlotInput[CTagStartSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        provided = self.inject(_TAG_CONTEXT_KEY, None)
        if provided is None:
            raise ValueError("CTag must be declared directly inside CTagGroup.")
        context: _TagContext = provided.context
        value = _plain("CTag value", kwargs.value)
        text_value = _plain("CTag text_value", kwargs.text_value, optional=True)
        validate_boolean("CTag", "disabled", kwargs.disabled)
        disabled = context.disabled or bool(kwargs.disabled)
        selected = str(value) in context.selected
        interactive = context.mode != "none" or context.actionable or context.removable
        roving = interactive and not disabled and not context.roving_assigned
        if roving:
            context.roving_assigned = True
        index = len(context.entries)
        context.entries.append(_TagEntry(str(value), bool(kwargs.disabled)))
        label_id = f"{context.group_id}-tag-{index}-label"
        remove_text_id = f"{context.group_id}-tag-{index}-remove"
        self.unprovide(_TAG_CONTEXT_KEY)
        return {
            "value": value,
            "text_value": text_value,
            "disabled": disabled,
            "item_disabled": bool(kwargs.disabled),
            "selected": selected,
            "interactive": interactive,
            "selectable": context.mode != "none",
            "row_role": "row" if interactive else "listitem",
            "cell_role": "gridcell" if interactive else None,
            "tabindex": 0 if roving else -1 if interactive else None,
            "removable": context.removable,
            "remove_label": context.remove_label,
            "label_id": label_id,
            "remove_text_id": remove_text_id,
            "variant": context.variant,
            "size": context.size,
            "has_start": "start" in self.raw_slots,
            "attrs": merge_root_attrs(_copy_attrs("CTag", kwargs.attrs, _TAG_OWNED), kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "disabled": bool(kwargs.disabled),
            "textValue": _plain("CTag text_value", kwargs.text_value, optional=True),
        }

    template = """
      <div
        class="cui-tag"
        c-bind="attrs"
        data-citry-ui-part="tag"
        c-data-value="value"
        c-data-selected="selected"
        c-data-disabled="disabled"
        c-data-removable="removable"
        c-data-item-disabled="item_disabled"
        c-data-text-value="text_value"
        c-data-variant="variant"
        c-data-size="size"
        c-role="row_role"
        c-tabindex="tabindex"
        c-aria-labelledby="label_id if interactive else None"
        c-aria-selected="'true' if selected and selectable else 'false' if selectable else None"
        c-aria-disabled="'true' if disabled and interactive else 'false' if interactive else None"
      >
        <span class="cui-tag__cell" c-role="cell_role">
          <span
            class="cui-tag__indicator"
            data-citry-ui-part="indicator"
            c-hidden="not selected"
            aria-hidden="true"
          >&#10003;</span>
          <c-if cond="has_start">
            <span class="cui-tag__start" data-citry-ui-part="start" aria-hidden="true"><c-slot name="start" /></span>
          </c-if>
          <span class="cui-tag__label" c-id="label_id" data-citry-ui-part="tag-label"><c-slot required /></span>
          <c-if cond="removable">
            <button
              class="cui-tag__remove"
              data-citry-ui-part="remove"
              type="button"
              tabindex="-1"
              c-disabled="disabled"
              c-aria-labelledby="remove_text_id + ' ' + label_id"
            >
              <span class="cui-tag__remove-text" c-id="remove_text_id">{{ remove_label }}</span>
              <span aria-hidden="true">&#215;</span>
            </button>
          </c-if>
        </span>
      </div>
    """

    js = r"""
      $component({
        props: {disabled: {}, textValue: {}},
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const group = root.closest('[data-citry-ui-part="tag-group"]');
          if (!group || root.parentElement !== group.querySelector(':scope > [data-citry-ui-part="list"]')) {
            console.error("[citry-ui] CTag must be a direct child of CTagGroup collection output.");
            root.setAttribute("inert", "");
            return () => {};
          }
          const label = root.querySelector(':scope > .cui-tag__cell > [data-citry-ui-part="tag-label"]');
          const indicator = root.querySelector(':scope > .cui-tag__cell > [data-citry-ui-part="indicator"]');
          const remove = root.querySelector(':scope > .cui-tag__cell > [data-citry-ui-part="remove"]');
          const invalid = new Set();
          let localDisabled = data.disabled;
          let textValue = data.textValue;
          let unregister = null;
          const report = (name, value) => {
            if (invalid.has(name)) return;
            invalid.add(name);
            console.error(`[citry-ui] CTag ${name} received invalid client value`, value);
          };
          const entry = {
            root, label, indicator, remove, value: root.dataset.value,
            localDisabled, disabled: localDisabled, textValue,
          };
          unregister = group.__citryTagRegister?.(entry) ?? null;
          const apply = () => {
            if (props.disabled === undefined) { invalid.delete("disabled"); localDisabled = data.disabled; }
            else if (typeof props.disabled === "boolean") {
              invalid.delete("disabled"); localDisabled = props.disabled;
            }
            else report("disabled", props.disabled);
            if (props.textValue === undefined || props.textValue === null) {
              invalid.delete("textValue"); textValue = data.textValue;
            } else if (typeof props.textValue === "string"
              && props.textValue.length && !props.textValue.includes("\0")) {
              invalid.delete("textValue"); textValue = props.textValue.replace(/\r\n?/g, "\n");
            } else report("textValue", props.textValue);
            entry.localDisabled = localDisabled;
            entry.textValue = textValue;
            group.__citryTagRegister?.(entry);
          };
          const stop = effect(apply);
          root.setAttribute("data-citry-tag-initialized", "");
          return () => {
            stop?.(); unregister?.();
            root.removeAttribute("data-citry-tag-initialized");
          };
        },
      })
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="tag-group"]) {
          --_cui-tag-gap: var(--cui-tag-gap, 0.5rem);
          --_cui-tag-row-gap: var(--cui-tag-row-gap, 0.5rem);
          --_cui-tag-label-color: var(--cui-tag-label-color, CanvasText);
          --_cui-tag-description-color: var(--cui-tag-description-color, light-dark(#57534e, #d6d3d1));
          display: grid;
          gap: 0.4rem;
          min-inline-size: 0;
          max-inline-size: 100%;
        }
        :where([data-citry-ui-part="group-label"]) {
          color: var(--_cui-tag-label-color);
          font-weight: 650;
          line-height: 1.3;
          overflow-wrap: anywhere;
        }
        :where([data-citry-ui-part="description"]) {
          color: var(--_cui-tag-description-color);
          font-size: 0.925em;
          line-height: 1.45;
          overflow-wrap: anywhere;
        }
        :where([data-citry-ui-part="list"]) {
          display: flex;
          flex-wrap: wrap;
          gap: var(--_cui-tag-row-gap) var(--_cui-tag-gap);
          min-inline-size: 0;
          max-inline-size: 100%;
          outline: none;
        }
        :where([data-citry-ui-part="tag"]) {
          --_cui-tag-background: var(--cui-tag-background, light-dark(#f5f5f4, #292524));
          --_cui-tag-foreground: var(--cui-tag-foreground, light-dark(#292524, #fafaf9));
          --_cui-tag-border-color: var(--cui-tag-border-color, light-dark(#d6d3d1, #57534e));
          --_cui-tag-selected-background: var(--cui-tag-selected-background, light-dark(#175cd3, #2563eb));
          --_cui-tag-selected-foreground: var(--cui-tag-selected-foreground, #ffffff);
          --_cui-tag-selected-border-color: var(--cui-tag-selected-border-color, var(--_cui-tag-selected-background));
          --_cui-tag-focus-color: var(--cui-tag-focus-color, Highlight);
          --_cui-tag-radius: var(--cui-tag-radius, 999px);
          --_cui-tag-min-height: var(--cui-tag-min-height, 2rem);
          --_cui-tag-padding-inline: var(--cui-tag-padding-inline, 0.7rem);
          --_cui-tag-internal-gap: var(--cui-tag-internal-gap, 0.35rem);
          --_cui-tag-font-size: var(--cui-tag-font-size, 0.875rem);
          box-sizing: border-box;
          display: inline-flex;
          min-block-size: var(--_cui-tag-min-height);
          min-inline-size: 0;
          max-inline-size: 100%;
          border: 1px solid var(--_cui-tag-border-color);
          border-radius: var(--_cui-tag-radius);
          color: var(--_cui-tag-foreground);
          background: var(--_cui-tag-background);
          font: inherit;
          font-size: var(--_cui-tag-font-size);
          line-height: 1.2;
          cursor: default;
          user-select: none;
        }
        :where([data-citry-ui-part="tag"][role="row"]) { cursor: pointer; }
        :where([data-citry-ui-part="tag"]:focus-visible),
        :where([data-citry-ui-part="remove"]:focus-visible) {
          outline: 2px solid var(--_cui-tag-focus-color);
          outline-offset: 2px;
        }
        :where([data-citry-ui-part="tag"][data-selected]) {
          border-color: var(--_cui-tag-selected-border-color);
          color: var(--_cui-tag-selected-foreground);
          background: var(--_cui-tag-selected-background);
        }
        :where([data-citry-ui-part="tag"][data-variant="solid"]:not([data-selected])) {
          --_cui-tag-background: var(--cui-tag-background, light-dark(#44403c, #d6d3d1));
          --_cui-tag-foreground: var(--cui-tag-foreground, light-dark(#ffffff, #1c1917));
          --_cui-tag-border-color: var(--cui-tag-border-color, var(--_cui-tag-background));
        }
        :where([data-citry-ui-part="tag"][data-variant="outline"]:not([data-selected])) {
          --_cui-tag-background: var(--cui-tag-background, transparent);
        }
        :where([data-citry-ui-part="tag"][data-size="sm"]) {
          --_cui-tag-min-height: var(--cui-tag-min-height, 1.75rem);
          --_cui-tag-padding-inline: var(--cui-tag-padding-inline, 0.55rem);
          --_cui-tag-font-size: var(--cui-tag-font-size, 0.8125rem);
        }
        :where([data-citry-ui-part="tag"][data-size="lg"]) {
          --_cui-tag-min-height: var(--cui-tag-min-height, 2.5rem);
          --_cui-tag-padding-inline: var(--cui-tag-padding-inline, 0.9rem);
          --_cui-tag-font-size: var(--cui-tag-font-size, 1rem);
        }
        :where([data-citry-ui-part="tag"][data-disabled]) {
          cursor: not-allowed;
        }
        :where(.cui-tag__cell) {
          display: inline-grid;
          grid-template-columns: auto auto minmax(0, auto) auto;
          align-items: center;
          gap: var(--_cui-tag-internal-gap);
          min-inline-size: 0;
          padding-inline: var(--_cui-tag-padding-inline);
        }
        :where([data-citry-ui-part="indicator"]),
        :where([data-citry-ui-part="start"]) {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex: none;
        }
        :where([data-citry-ui-part="indicator"][hidden]) { display: none !important; }
        :where([data-citry-ui-part="tag-label"]) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }
        :where([data-citry-ui-part="remove"]) {
          box-sizing: border-box;
          display: inline-grid;
          place-items: center;
          inline-size: 1.5rem;
          block-size: 1.5rem;
          margin-inline-end: -0.35rem;
          padding: 0;
          border: 0;
          border-radius: 999px;
          color: inherit;
          background: transparent;
          font: inherit;
          cursor: pointer;
        }
        :where([data-citry-ui-part="remove"]:hover) { background: color-mix(in srgb, currentColor 14%, transparent); }
        :where([data-citry-ui-part="remove"]:disabled) { cursor: not-allowed; }
        :where(.cui-tag__remove-text) {
          position: absolute;
          inline-size: 1px;
          block-size: 1px;
          overflow: hidden;
          clip-path: inset(50%);
          white-space: nowrap;
        }
      }
      @media (forced-colors: active) {
        @layer citry-ui.theme {
          :where([data-citry-ui-part="tag"]) {
            border-color: ButtonText;
            color: ButtonText;
            background: Canvas;
            forced-color-adjust: auto;
          }
          :where([data-citry-ui-part="tag"][data-selected]) {
            border-color: Highlight;
            color: HighlightText;
            background: Highlight;
          }
          :where([data-citry-ui-part="tag"][data-disabled]) { color: GrayText; }
        }
      }
      @media print {
        @layer citry-ui.theme {
          :where([data-citry-ui-part="tag"]) {
            border-color: currentColor;
            color: CanvasText;
            background: transparent;
          }
          :where([data-citry-ui-part="tag"][data-selected]) { border-width: 2px; }
        }
      }
    """


__all__ = [
    "CTag",
    "CTagActionDetail",
    "CTagDefaultSlotData",
    "CTagGroup",
    "CTagGroupDefaultSlotData",
    "CTagGroupDescriptionSlotData",
    "CTagGroupLabelSlotData",
    "CTagRemoveDetail",
    "CTagSelectionMode",
    "CTagSize",
    "CTagStartSlotData",
    "CTagValue",
    "CTagValueChangeDetail",
    "CTagVariant",
]
