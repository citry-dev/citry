"""Persistent single- and multiple-selection Listbox components."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any, ClassVar, Literal, TypedDict, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CListboxVariant = Literal["plain", "soft", "outline"]
CListboxSize = Literal["sm", "md", "lg"]
CListboxChangeSource = Literal["pointer", "keyboard", "structure"]
CListboxValue = str | None | Sequence[str]

_CONTEXT = "citry_ui_listbox"
_VARIANTS = ("plain", "soft", "outline")
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
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-mandatory",
        "data-multiple",
        "data-size",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_SURFACE_OWNED = frozenset(
    {
        "aria-activedescendant",
        "aria-disabled",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-multiselectable",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_OPTION_OWNED = frozenset(
    {
        "aria-describedby",
        "aria-disabled",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-selected",
        "contenteditable",
        "data-active",
        "data-citry-ui-part",
        "data-disabled",
        "data-selected",
        "data-value",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_GROUP_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


class CListboxDefaultSlotData:
    pass


class CListboxOptionDefaultSlotData(TypedDict):
    value: str


class CListboxOptionStateSlotData(TypedDict):
    value: str
    selected: bool
    disabled: bool


class CListboxOptionDescriptionSlotData(TypedDict):
    value: str


class CListboxGroupDefaultSlotData:
    pass


class CListboxValueChangeDetail(TypedDict):
    value: str | list[str] | None
    previousValue: str | list[str] | None
    option: object | None
    selected: bool
    controlled: bool
    source: CListboxChangeSource
    sourceEvent: object | None


@dataclass(slots=True)
class _ListboxRegistry:
    values: list[str] = field(default_factory=list)
    disabled: set[str] = field(default_factory=set)
    roving_assigned: bool = False


@dataclass(frozen=True, slots=True)
class _ListboxContext:
    registry: _ListboxRegistry
    root_id: str
    selected: frozenset[str]
    root_disabled: bool
    parent_kind: Literal["root", "group"]


def _plain_optional(owner: str, name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"{owner} {name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"{owner} could not convert {name} to a plain string."
        raise TypeError(msg)
    return plain.replace("\r\n", "\n").replace("\r", "\n")


def _plain(owner: str, name: str, value: object) -> str:
    plain = _plain_optional(owner, name, value)
    if plain is None:
        msg = f"{owner} {name} must be a string."
        raise TypeError(msg)
    if not plain.strip():
        msg = f"{owner} {name} must be nonempty."
        raise ValueError(msg)
    if "\0" in plain:
        msg = f"{owner} {name} cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _identity(owner: str, value: object) -> str:
    plain = _plain_optional(owner, "value", value)
    if plain is None:
        msg = f"{owner} value must be a string."
        raise TypeError(msg)
    if not plain:
        msg = f"{owner} value must be nonempty."
        raise ValueError(msg)
    if "\0" in plain:
        msg = f"{owner} value cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _choice(owner: str, name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(owner, name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{owner} {name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _initial_values(value: object, *, multiple: bool) -> tuple[str, ...]:
    raw = const_value(value)
    if multiple:
        if raw is None:
            return ()
        if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
            msg = f"CListbox value must be a sequence of strings in multiple mode, got {raw!r}."
            raise TypeError(msg)
        result = tuple(_identity("CListbox", item) for item in raw)
    else:
        if raw is None:
            return ()
        if not isinstance(raw, str):
            msg = f"CListbox value must be a string or None in single mode, got {raw!r}."
            raise TypeError(msg)
        result = (_identity("CListbox", raw),)
    if len(result) != len(set(result)):
        raise ValueError("CListbox value cannot contain duplicate values.")
    return result


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    owner: str,
    input_name: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
    class_: CClassValue | None = None,
    style: CStyleValue | None = None,
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{owner} {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{owner} {input_name}")
    for key in copied:
        if not isinstance(key, str):
            msg = f"{owner} {input_name} requires string keys, got {key!r}."
            raise TypeError(msg)
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{owner} {input_name} cannot contain Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{owner} {input_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if _dynamic_target(normalized) in owned:
            msg = f"{owner} {input_name} cannot dynamically bind owned attribute {key!r}."
            raise ValueError(msg)
    return merge_root_attrs(copied, class_, style)


def _token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:12]


class _ListboxOutputParser(HTMLParser):
    _OWNED_PARTS: ClassVar[set[str]] = {
        "listbox-root",
        "listbox-label",
        "listbox",
        "listbox-option",
        "listbox-indicator",
        "listbox-option-start",
        "listbox-option-copy",
        "listbox-option-label",
        "listbox-option-description",
        "listbox-option-end",
        "listbox-group",
        "listbox-group-label",
    }
    _ALLOWED: ClassVar[dict[str | None, set[str]]] = {
        None: {"listbox-root"},
        "listbox-root": {"listbox-label", "listbox"},
        "listbox": {"listbox-option", "listbox-group"},
        "listbox-group": {"listbox-group-label", "listbox-option"},
        "listbox-option": {
            "listbox-indicator",
            "listbox-option-start",
            "listbox-option-copy",
            "listbox-option-end",
        },
        "listbox-option-copy": {"listbox-option-label", "listbox-option-description"},
        "listbox-label": set(),
        "listbox-indicator": set(),
        "listbox-option-start": set(),
        "listbox-option-label": set(),
        "listbox-option-description": set(),
        "listbox-option-end": set(),
        "listbox-group-label": set(),
    }
    _INTERACTIVE_TAGS: ClassVar[set[str]] = {
        "button",
        "input",
        "select",
        "textarea",
        "summary",
        "label",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str | None, bool]] = []
        self.problem: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        raw_part = values.get("data-citry-ui-part")
        part = raw_part if raw_part in self._OWNED_PARTS else None
        in_slot = any(slot for _, slot in self.stack)
        starts_slot = "data-cui-listbox-slot-region" in values
        option_region = in_slot or starts_slot
        if option_region and self.problem is None:
            role = (values.get("role") or "").casefold()
            contenteditable = (values.get("contenteditable") or "").casefold()
            tabindex = values.get("tabindex")
            if (
                tag in self._INTERACTIVE_TAGS
                or (tag == "a" and "href" in values)
                or role in {"listbox", "option"}
                or (contenteditable and contenteditable != "false")
                or (tabindex is not None and tabindex != "-1")
            ):
                self.problem = f"Option content contains interactive {tag}"
        if not in_slot and self.problem is None:
            parent = self.stack[-1][0] if self.stack else None
            if part is None and parent in self._ALLOWED and not starts_slot:
                self.problem = f"{parent or 'document'} contains unsupported {tag}"
            elif part is not None and part not in self._ALLOWED.get(parent, set()):
                self.problem = f"{parent or 'document'} contains unsupported {part}"
        self.stack.append((part, option_region))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:  # noqa: ARG002
        if self.stack:
            self.stack.pop()


def _validate_output(rendered: object) -> None:
    parser = _ListboxOutputParser()
    parser.feed(cast("Any", rendered).serialize(deps_strategy="ignore"))
    if parser.problem is not None:
        msg = f"CListbox content must follow the documented noninteractive Listbox anatomy: {parser.problem}."
        raise ValueError(msg)


class CListbox(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        value: CListboxValue = None
        multiple: bool = False
        mandatory: bool = False
        disabled: bool = False
        loop: bool = False
        variant: CListboxVariant = "outline"
        size: CListboxSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        listbox_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CListboxDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if self.inject(_CONTEXT, None) is not None:
            raise ValueError("CListbox cannot be nested inside a CListbox declaration collection.")
        label = _plain("CListbox", "label", kwargs.label)
        validate_boolean("CListbox", "multiple", kwargs.multiple)
        validate_boolean("CListbox", "mandatory", kwargs.mandatory)
        validate_boolean("CListbox", "disabled", kwargs.disabled)
        validate_boolean("CListbox", "loop", kwargs.loop)
        values = _initial_values(kwargs.value, multiple=bool(kwargs.multiple))
        if kwargs.mandatory and not values:
            raise ValueError("CListbox mandatory requires an initial selected value.")
        variant = _choice("CListbox", "variant", kwargs.variant, _VARIANTS)
        size = _choice("CListbox", "size", kwargs.size, _SIZES)
        registry = _ListboxRegistry()
        root_id = f"cui-listbox-{self.id}"
        self.provide(
            _CONTEXT,
            context=_ListboxContext(
                registry=registry,
                root_id=root_id,
                selected=frozenset(values),
                root_disabled=bool(kwargs.disabled),
                parent_kind="root",
            ),
        )
        self._listbox_registry = registry
        self._listbox_values = values
        self._listbox_data = {
            "value": list(values),
            "multiple": bool(kwargs.multiple),
            "mandatory": bool(kwargs.mandatory),
            "disabled": bool(kwargs.disabled),
            "loop": bool(kwargs.loop),
            "variant": variant,
            "size": size,
        }
        return {
            **self._listbox_data,
            "label": label,
            "root_id": root_id,
            "label_id": f"{root_id}-label",
            "surface_id": f"{root_id}-surface",
            "attrs": _attrs("CListbox", "attrs", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "listbox_attrs": _attrs(
                "CListbox",
                "listbox_attrs",
                kwargs.listbox_attrs,
                _SURFACE_OWNED,
            ),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CListbox completed without a render result.")
        _validate_output(rendered)
        values = self._listbox_registry.values
        if not values:
            raise ValueError("CListbox requires one or more CListboxOption declarations.")
        if len(values) != len(set(values)):
            raise ValueError("CListbox requires every CListboxOption value to be unique.")
        unknown = set(self._listbox_values).difference(values)
        if unknown:
            raise ValueError(f"CListbox value contains unknown Options: {sorted(unknown)!r}.")

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return self._listbox_data

    template = """
      <div
        class="cui-listbox"
        c-id="root_id"
        c-data-multiple="multiple"
        c-data-mandatory="mandatory"
        c-data-disabled="disabled"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="listbox-root"
      >
        <span
          class="cui-listbox__label"
          c-id="label_id"
          data-citry-ui-part="listbox-label"
        >{{ label }}</span>
        <div
          class="cui-listbox__surface"
          c-id="surface_id"
          role="listbox"
          c-aria-labelledby="label_id"
          c-aria-multiselectable="'true' if multiple else None"
          c-aria-disabled="'true' if disabled else None"
          c-bind="listbox_attrs"
          data-citry-ui-part="listbox"
        ><c-slot required /></div>
      </div>
    """

    js = r"""
      $component({
        props: {
          value: {}, mandatory: {}, disabled: {}, loop: {}, variant: {}, size: {}, onValueChange: {},
        },
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const surface = root.querySelector(':scope > [data-citry-ui-part="listbox"]');
          const invalidEpisodes = new Set();
          const prior = root.__citryUiListboxRuntime;
          const serverFingerprint = JSON.stringify(data.value);
          let committed = prior?.serverFingerprint === serverFingerprint
            ? [...prior.committed]
            : [...data.value];
          let current = [...committed];
          let controlled = false;
          let activeValue = prior?.activeValue ?? null;
          let previousOrder = Array.isArray(prior?.order) ? [...prior.order] : [];
          let pendingStructural = prior?.pendingStructural ?? null;
          let configuration = {
            mandatory: data.mandatory,
            disabled: data.disabled,
            loop: data.loop,
            variant: data.variant,
            size: data.size,
          };
          let onValueChange = null;
          let clientValue;
          let structureValid = false;
          let task = null;
          let generation = 0;
          let typeBuffer = '';
          let typeTimer = null;

          const options = () => [...surface.querySelectorAll('[role="option"]')]
            .filter((option) => option.closest('[role="listbox"]') === surface);
          const canonicalString = (value) => (
            typeof value === 'string' && value.length > 0 && !value.includes('\0')
              ? value.replace(/\r\n?/g, '\n')
              : null
          );
          const report = (name, value, suffix = '') => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CListbox ${name} received invalid client value${suffix}`, value);
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
            report(name, supplied, '; using the server fallback');
            return fallback;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'string' && allowed.includes(supplied)) {
              invalidEpisodes.delete(name);
              return supplied;
            }
            report(name, supplied, '; using the server fallback');
            return fallback;
          };
          const deepActiveElement = (documentRoot) => {
            let active = documentRoot.activeElement;
            while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
            return active;
          };
          const composedContains = (ancestor, node) => {
            for (let currentNode = node; currentNode;) {
              if (currentNode === ancestor) return true;
              currentNode = currentNode.parentNode ?? currentNode.getRootNode?.().host ?? null;
            }
            return false;
          };
          const focusBody = () => {
            const body = root.ownerDocument.body;
            if (!(body instanceof HTMLElement)) return;
            const hadTabIndex = body.hasAttribute('tabindex');
            if (!hadTabIndex) body.tabIndex = -1;
            body.focus({preventScroll:true});
            if (!hadTabIndex) queueMicrotask(() => body.removeAttribute('tabindex'));
          };
          const fieldsetDisabled = () => {
            for (let node = root.parentElement; node; node = node.parentElement) {
              if (!(node instanceof HTMLFieldSetElement) || !node.disabled) continue;
              const legend = [...node.children].find((child) => child instanceof HTMLLegendElement);
              if (!(legend instanceof Element) || !legend.contains(root)) return true;
            }
            return false;
          };
          const rootDisabled = () => configuration.disabled || fieldsetDisabled();
          const ownDisabled = (option) => option.hasAttribute('data-cui-listbox-option-disabled');
          const optionDisabled = (option) => rootDisabled() || ownDisabled(option);
          const enabledOptions = () => options().filter((option) => !optionDisabled(option));
          const valueOf = (option) => option.dataset.value;
          const optionFor = (value) => options().find((option) => valueOf(option) === value) ?? null;
          const values = () => options().map(valueOf);
          const isOption = (node) => node instanceof HTMLElement
            && node.getAttribute('role') === 'option'
            && node.closest('[role="listbox"]') === surface;
          const optionFromEvent = (event) => event.composedPath().find(isOption) ?? null;
          const formatValue = (vector) => data.multiple ? [...vector] : (vector[0] ?? null);
          const normalizeSupplied = (supplied) => {
            if (supplied === null) return {valid:true, values:[]};
            if (data.multiple) {
              if (!Array.isArray(supplied)) return {valid:false, values:[]};
              const normalized = supplied.map(canonicalString);
              if (normalized.some((value) => value === null) || new Set(normalized).size !== normalized.length) {
                return {valid:false, values:[]};
              }
              return {valid:true, values:normalized};
            }
            const normalized = canonicalString(supplied);
            return normalized === null ? {valid:false, values:[]} : {valid:true, values:[normalized]};
          };
          const nearestSurvivor = (removedValue) => {
            const enabled = new Set(enabledOptions().map(valueOf));
            const oldIndex = previousOrder.indexOf(removedValue);
            if (oldIndex >= 0) {
              for (let distance = 1; distance < previousOrder.length; distance += 1) {
                const following = previousOrder[oldIndex + distance];
                if (enabled.has(following)) return optionFor(following);
                const preceding = previousOrder[oldIndex - distance];
                if (enabled.has(preceding)) return optionFor(preceding);
              }
            }
            return enabledOptions()[0] ?? null;
          };
          const structureProblem = () => {
            const entries = options();
            if (entries.length === 0) return 'requires one or more Options';
            if (new Set(values()).size !== entries.length) return 'contains duplicate Option values';
            for (const child of surface.children) {
              if (isOption(child)) continue;
              if (child.getAttribute?.('role') !== 'group') return 'contains an unknown direct child';
              const groupChildren = [...child.children];
              if (!groupChildren[0]?.matches?.('[data-citry-ui-part="listbox-group-label"]')) {
                return 'Group label anatomy is invalid';
              }
              const grouped = groupChildren.slice(1);
              if (grouped.length === 0 || grouped.some((option) => !isOption(option))) {
                return 'Group must contain direct Options';
              }
            }
            const forbidden = [
              'a[href]', 'button', 'input', 'select', 'textarea', 'summary', 'label',
              '[contenteditable]:not([contenteditable="false"])',
              '[tabindex]:not([tabindex="-1"])', '[role="listbox"]', '[role="option"]',
            ].join(',');
            for (const option of entries) {
              const regions = option.querySelectorAll('[data-cui-listbox-slot-region]');
              if ([...regions].some((region) => region.querySelector(forbidden))) {
                return 'Option content must remain noninteractive';
              }
            }
            return null;
          };
          const saveRuntime = () => {
            root.__citryUiListboxRuntime = {
              serverFingerprint,
              committed:[...committed],
              activeValue,
              order:[...previousOrder],
              pendingStructural,
            };
          };
          const focusOption = (option, {moveFocus = true} = {}) => {
            if (!(option instanceof HTMLElement) || optionDisabled(option)) return;
            activeValue = valueOf(option);
            options().forEach((entry) => {
              const active = entry === option;
              entry.tabIndex = active && !rootDisabled() ? 0 : -1;
              entry.toggleAttribute('data-active', active);
            });
            if (moveFocus) option.focus({preventScroll:false});
          };
          const callbackDetail = (next, previous, option, selected, source, sourceEvent) => ({
            value:formatValue(next),
            previousValue:formatValue(previous),
            option,
            selected,
            controlled,
            source,
            sourceEvent,
          });
          const emitChange = (next, previous, option, selected, source, sourceEvent) => {
            onValueChange?.(
              formatValue(next),
              callbackDetail(next, previous, option, selected, source, sourceEvent),
            );
          };
          const applyState = () => {
            const disabled = rootDisabled();
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute('data-multiple', data.multiple);
            root.toggleAttribute('data-mandatory', configuration.mandatory);
            root.toggleAttribute('data-disabled', disabled);
            surface.setAttribute('aria-disabled', disabled ? 'true' : 'false');
            if (data.multiple) surface.setAttribute('aria-multiselectable', 'true');
            else surface.removeAttribute('aria-multiselectable');
            options().forEach((option) => {
              const selected = current.includes(valueOf(option));
              const itemDisabled = optionDisabled(option);
              option.setAttribute('aria-selected', selected ? 'true' : 'false');
              option.setAttribute('aria-disabled', itemDisabled ? 'true' : 'false');
              option.toggleAttribute('data-selected', selected);
              option.toggleAttribute('data-disabled', itemDisabled);
            });
            let active = optionFor(activeValue);
            if (!(active instanceof HTMLElement) || optionDisabled(active)) {
              active = options().find((option) => current.includes(valueOf(option)) && !optionDisabled(option))
                ?? enabledOptions()[0]
                ?? null;
            }
            options().forEach((option) => {
              const isActive = option === active;
              option.tabIndex = isActive && !disabled ? 0 : -1;
              option.toggleAttribute('data-active', isActive);
            });
            activeValue = active ? valueOf(active) : null;
            previousOrder = values();
            saveRuntime();
          };
          const failClosed = (problem) => {
            const active = deepActiveElement(root.ownerDocument);
            if (composedContains(surface, active)) focusBody();
            structureValid = false;
            report('structure', problem);
            root.removeAttribute('data-citry-listbox-initialized');
            surface.inert = true;
            surface.setAttribute('aria-disabled', 'true');
            options().forEach((option) => { option.tabIndex = -1; });
          };
          const reconcileValue = () => {
            const allowed = new Set(values());
            const supplied = clientValue;
            if (supplied === undefined) {
              invalidEpisodes.delete('value');
              if (controlled) committed = [...current];
              controlled = false;
              current = committed.filter((value) => allowed.has(value));
            } else {
              const normalized = normalizeSupplied(supplied);
              if (!normalized.valid) {
                report('value', supplied, '; releasing control from the committed selection');
                if (controlled) committed = [...current];
                controlled = false;
                current = committed.filter((value) => allowed.has(value));
              } else {
                controlled = true;
                const missing = normalized.values.filter((value) => !allowed.has(value));
                current = normalized.values.filter((value) => allowed.has(value));
                if (missing.length === 0) {
                  invalidEpisodes.delete('value');
                  pendingStructural = null;
                } else {
                  report('value', supplied, '; filtering values missing from the settled collection');
                  const fingerprint = JSON.stringify([missing, current]);
                  if (pendingStructural !== fingerprint) {
                    const previous = [...normalized.values];
                    const next = [...current];
                    const scheduled = generation;
                    pendingStructural = fingerprint;
                    queueMicrotask(() => {
                      if (generation === scheduled && pendingStructural === fingerprint) {
                        emitChange(next, previous, null, false, 'structure', null);
                      }
                    });
                  }
                }
              }
            }
            const removedCommitted = committed.filter((value) => !allowed.has(value));
            if (!controlled && removedCommitted.length > 0) {
              const previous = [...committed];
              committed = committed.filter((value) => allowed.has(value));
              current = [...committed];
              emitChange(current, previous, null, false, 'structure', null);
            }
            if (!controlled && configuration.mandatory && current.length === 0) {
              const first = enabledOptions()[0];
              if (first) {
                const previous = [...current];
                current = [valueOf(first)];
                if (!controlled) committed = [...current];
                if (previousOrder.length > 0) {
                  emitChange(current, previous, first, true, 'structure', null);
                }
              }
            }
          };
          const sync = () => {
            const focusBefore = deepActiveElement(root.ownerDocument);
            const focusRoot = root.getRootNode();
            const focusWasOwned = composedContains(surface, focusBefore);
            const focusWasLost = focusBefore === root.ownerDocument.body
              || (focusRoot instanceof ShadowRoot && focusBefore === focusRoot.host);
            const priorActive = activeValue;
            const disabled = rootDisabled();
            if (!wasDisabled && disabled) {
              const active = deepActiveElement(root.ownerDocument);
              if (composedContains(root, active)) focusBody();
            }
            wasDisabled = disabled;
            const problem = structureProblem();
            if (problem) { failClosed(problem); return; }
            structureValid = true;
            invalidEpisodes.delete('structure');
            surface.inert = false;
            reconcileValue();
            const activeOption = optionFor(activeValue);
            const activeUnavailable = activeValue !== null
              && (!(activeOption instanceof HTMLElement) || optionDisabled(activeOption));
            if (activeUnavailable) {
              const replacement = nearestSurvivor(activeValue);
              activeValue = replacement ? valueOf(replacement) : null;
            }
            applyState();
            if (activeUnavailable && (focusWasOwned || focusWasLost)) {
              const replacement = optionFor(activeValue);
              if (replacement instanceof HTMLElement) replacement.focus({preventScroll:true});
              else focusBody();
            } else if (priorActive !== null && activeValue === null && focusWasOwned) {
              focusBody();
            }
            root.setAttribute('data-citry-listbox-initialized', '');
          };
          const schedule = () => {
            if (task !== null) return;
            const scheduled = generation;
            task = setTimeout(() => {
              task = null;
              if (scheduled === generation) sync();
            }, 0);
          };
          const requestSelection = (option, event, source) => {
            if (!structureValid || !isOption(option) || optionDisabled(option)) return;
            const value = valueOf(option);
            const previous = [...current];
            const wasSelected = previous.includes(value);
            let next;
            if (data.multiple) {
              if (wasSelected && configuration.mandatory && previous.length === 1) return;
              next = wasSelected
                ? previous.filter((entry) => entry !== value)
                : [...previous, value];
            } else {
              if (wasSelected) return;
              next = [value];
            }
            if (!controlled) {
              committed = [...next];
              current = [...next];
              applyState();
            }
            emitChange(next, previous, option, !wasSelected, source, event);
            if (controlled) schedule();
          };
          const clearSelection = (event) => {
            if (configuration.mandatory || current.length === 0 || rootDisabled()) return false;
            const previous = [...current];
            const next = [];
            if (!controlled) {
              committed = [];
              current = [];
              applyState();
            }
            emitChange(next, previous, optionFor(activeValue), false, 'keyboard', event);
            if (controlled) schedule();
            return true;
          };
          const localeLower = (value) => {
            const lang = root.closest('[lang]')?.getAttribute('lang')
              ?? root.ownerDocument.documentElement.lang
              ?? '';
            try { return lang ? value.toLocaleLowerCase(lang) : value.toLocaleLowerCase(); }
            catch { return value.toLowerCase(); }
          };
          const typeaheadText = (option) => {
            const explicit = option.getAttribute('data-cui-listbox-text-value');
            const label = option.querySelector('[data-citry-ui-part="listbox-option-label"]');
            const raw = explicit ?? label?.textContent ?? '';
            return localeLower(raw.trim().replace(/\s+/g, ' '));
          };
          const onClick = (event) => {
            const option = optionFromEvent(event);
            if (!isOption(option) || optionDisabled(option)) return;
            focusOption(option);
            requestSelection(option, event, 'pointer');
          };
          const onKeyDown = (event) => {
            const option = optionFromEvent(event);
            if (!isOption(option) || optionDisabled(option) || rootDisabled()) return;
            const enabled = enabledOptions();
            const index = enabled.indexOf(option);
            let destination = null;
            if (event.key === 'ArrowDown') {
              destination = enabled[index + 1] ?? (configuration.loop ? enabled[0] : null);
            } else if (event.key === 'ArrowUp') {
              destination = enabled[index - 1] ?? (configuration.loop ? enabled.at(-1) : null);
            } else if (event.key === 'Home') destination = enabled[0] ?? null;
            else if (event.key === 'End') destination = enabled.at(-1) ?? null;
            else if (event.key === ' ' || event.key === 'Enter') {
              event.preventDefault();
              requestSelection(option, event, 'keyboard');
              return;
            } else if (event.key === 'Escape') {
              if (clearSelection(event)) event.preventDefault();
              return;
            } else {
              const altGraph = event.getModifierState?.('AltGraph') ?? false;
              if (
                event.isComposing
                || event.ctrlKey
                || event.metaKey
                || (event.altKey && !altGraph)
                || event.key.length !== 1
              ) return;
              const key = localeLower(event.key);
              typeBuffer = typeBuffer.length === 1 && typeBuffer === key ? key : typeBuffer + key;
              if (typeTimer !== null) clearTimeout(typeTimer);
              typeTimer = setTimeout(() => { typeBuffer = ''; typeTimer = null; }, 500);
              const ordered = [...enabled.slice(index + 1), ...enabled.slice(0, index + 1)];
              destination = ordered.find((entry) => typeaheadText(entry).startsWith(typeBuffer)) ?? null;
            }
            if (destination instanceof HTMLElement) {
              event.preventDefault();
              focusOption(destination);
            }
          };
          const onFocusIn = (event) => {
            const option = optionFromEvent(event);
            if (isOption(option) && !optionDisabled(option)) focusOption(option, {moveFocus:false});
          };
          const observeStructure = (records) => {
            const relevant = records.some((record) => {
              if (record.type === 'childList') return true;
              if (record.attributeName === 'tabindex' && isOption(record.target)) return false;
              return true;
            });
            if (relevant) schedule();
          };
          root.addEventListener('click', onClick, true);
          root.addEventListener('keydown', onKeyDown, true);
          root.addEventListener('focusin', onFocusIn, true);
          const observer = new MutationObserver(observeStructure);
          observer.observe(surface, {
            childList:true,
            subtree:true,
            attributes:true,
            attributeFilter:[
              'data-cui-listbox-option-disabled', 'data-cui-listbox-text-value',
              'href', 'tabindex', 'contenteditable', 'role',
            ],
          });
          const fieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const fieldsetObserver = new MutationObserver(schedule);
            fieldsetObserver.observe(ancestor, {
              attributes:true,
              childList:true,
              attributeFilter:['disabled'],
            });
            fieldsets.push(fieldsetObserver);
          }
          let wasDisabled = rootDisabled();
          const stop = effect(() => {
            clientValue = props.value;
            onValueChange = typeof props.onValueChange === 'function' ? props.onValueChange : null;
            if (props.onValueChange !== undefined && props.onValueChange !== null && onValueChange === null) {
              report('onValueChange', props.onValueChange, '; ignoring the callback');
            } else invalidEpisodes.delete('onValueChange');
            configuration = {
              mandatory: resolveBoolean('mandatory', data.mandatory),
              disabled: resolveBoolean('disabled', data.disabled),
              loop: resolveBoolean('loop', data.loop),
              variant: resolveChoice('variant', data.variant, ['plain','soft','outline']),
              size: resolveChoice('size', data.size, ['sm','md','lg']),
            };
            schedule();
          });
          schedule();
          return () => {
            generation += 1;
            if (task !== null) clearTimeout(task);
            if (typeTimer !== null) clearTimeout(typeTimer);
            saveRuntime();
            stop?.();
            observer.disconnect();
            fieldsets.forEach((item) => item.disconnect());
            root.removeEventListener('click', onClick, true);
            root.removeEventListener('keydown', onKeyDown, true);
            root.removeEventListener('focusin', onFocusIn, true);
            root.removeAttribute('data-citry-listbox-initialized');
          };
        },
      })
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-listbox) {
          --_cui-listbox-gap: var(--cui-listbox-gap, 0.375rem);
          --_cui-listbox-max-block-size: var(--cui-listbox-max-block-size, 18rem);
          --_cui-listbox-background: var(--cui-listbox-background, Canvas);
          --_cui-listbox-foreground: var(--cui-listbox-foreground, CanvasText);
          --_cui-listbox-muted-color: var(--cui-listbox-muted-color, light-dark(#667085, #a4a7ae));
          --_cui-listbox-border-color: var(--cui-listbox-border-color, light-dark(#d0d5dd, #535862));
          --_cui-listbox-hover-background: var(
            --cui-listbox-hover-background,
            color-mix(in srgb, CanvasText 7%, transparent)
          );
          --_cui-listbox-selected-background: var(
            --cui-listbox-selected-background,
            light-dark(#dbeafe, #1e3a5f)
          );
          --_cui-listbox-selected-foreground: var(
            --cui-listbox-selected-foreground,
            light-dark(#1849a9, #d1e9ff)
          );
          --_cui-listbox-focus-color: var(--cui-listbox-focus-color, Highlight);
          --_cui-listbox-radius: var(--cui-listbox-radius, 0.625rem);
          --_cui-listbox-option-padding: var(--cui-listbox-option-padding, 0.5rem 0.625rem);
          box-sizing: border-box;
          display: grid;
          gap: var(--_cui-listbox-gap);
          min-inline-size: 0;
          color: var(--_cui-listbox-foreground);
          font-family: ui-sans-serif, system-ui, sans-serif;
        }
        :where(.cui-listbox[data-size="sm"]) {
          --_cui-listbox-option-padding: var(--cui-listbox-option-padding, 0.375rem 0.5rem);
          font-size: 0.875rem;
        }
        :where(.cui-listbox[data-size="lg"]) {
          --_cui-listbox-option-padding: var(--cui-listbox-option-padding, 0.625rem 0.75rem);
          font-size: 1.0625rem;
        }
        :where(.cui-listbox__label) {
          font-size: 0.9375em;
          font-weight: 650;
          line-height: 1.35;
          overflow-wrap: anywhere;
        }
        :where(.cui-listbox__surface) {
          box-sizing: border-box;
          display: grid;
          align-content: start;
          gap: 0.125rem;
          min-inline-size: 0;
          max-block-size: var(--_cui-listbox-max-block-size);
          margin: 0;
          padding: 0.25rem;
          overflow: auto;
          border: 1px solid transparent;
          border-radius: var(--_cui-listbox-radius);
          background: var(--_cui-listbox-background);
          color: var(--_cui-listbox-foreground);
          overscroll-behavior: contain;
        }
        :where(.cui-listbox[data-variant="soft"] .cui-listbox__surface) {
          --_cui-listbox-background: var(
            --cui-listbox-background,
            color-mix(in srgb, CanvasText 5%, Canvas)
          );
        }
        :where(.cui-listbox[data-variant="outline"] .cui-listbox__surface) {
          border-color: var(--_cui-listbox-border-color);
        }
        :where(.cui-listbox__option) {
          box-sizing: border-box;
          display: grid;
          grid-template-columns: 1rem auto minmax(0, 1fr) auto;
          grid-template-areas: "indicator start copy end";
          align-items: center;
          gap: 0.5rem;
          min-inline-size: 0;
          padding: var(--_cui-listbox-option-padding);
          border-radius: calc(var(--_cui-listbox-radius) - 0.125rem);
          outline: none;
          cursor: default;
        }
        :where(.cui-listbox__option:not([data-disabled]):hover) {
          background: var(--_cui-listbox-hover-background);
        }
        :where(.cui-listbox__option[data-selected]) {
          background: var(--_cui-listbox-selected-background);
          color: var(--_cui-listbox-selected-foreground);
        }
        :where(.cui-listbox__option:focus-visible) {
          outline: 2px solid var(--_cui-listbox-focus-color);
          outline-offset: -2px;
        }
        :where(.cui-listbox__option[data-disabled]) {
          color: var(--_cui-listbox-muted-color);
          cursor: not-allowed;
          opacity: 0.7;
        }
        :where(.cui-listbox__indicator) {
          grid-area: indicator;
          display: grid;
          inline-size: 1rem;
          block-size: 1rem;
          place-items: center;
          font-weight: 800;
          opacity: 0;
          transform: scale(0.75);
          transition: opacity 100ms ease-out, transform 100ms ease-out;
        }
        :where(.cui-listbox__indicator::before) { content: "✓"; }
        :where(.cui-listbox__option[data-selected] > .cui-listbox__indicator) {
          opacity: 1;
          transform: none;
        }
        :where(.cui-listbox__option-start) { grid-area: start; min-inline-size: 0; }
        :where(.cui-listbox__option-copy) {
          grid-area: copy;
          display: grid;
          gap: 0.125rem;
          min-inline-size: 0;
        }
        :where(.cui-listbox__option-label) {
          min-inline-size: 0;
          line-height: 1.35;
          overflow-wrap: anywhere;
        }
        :where(.cui-listbox__option-description) {
          min-inline-size: 0;
          color: var(--_cui-listbox-muted-color);
          font-size: 0.875em;
          line-height: 1.35;
          overflow-wrap: anywhere;
        }
        :where(.cui-listbox__option[data-selected] .cui-listbox__option-description) {
          color: currentColor;
          opacity: 0.82;
        }
        :where(.cui-listbox__option-end) {
          grid-area: end;
          min-inline-size: 0;
          color: var(--_cui-listbox-muted-color);
          font-size: 0.875em;
        }
        :where(.cui-listbox__option[data-selected] .cui-listbox__option-end) {
          color: currentColor;
          opacity: 0.82;
        }
        :where(.cui-listbox__group) {
          display: grid;
          gap: 0.125rem;
          min-inline-size: 0;
        }
        :where(.cui-listbox__group-label) {
          padding: 0.5rem 0.625rem 0.25rem;
          color: var(--_cui-listbox-muted-color);
          font-size: 0.8125em;
          font-weight: 700;
          letter-spacing: 0.025em;
          line-height: 1.3;
          overflow-wrap: anywhere;
          text-transform: uppercase;
        }
        :where(.cui-listbox[data-disabled] .cui-listbox__label) { color: var(--_cui-listbox-muted-color); }
        @media (prefers-reduced-motion: reduce) {
          :where(.cui-listbox__indicator) { transition: none; }
        }
        @media (forced-colors: active) {
          :where(.cui-listbox__surface) { border-color: CanvasText; }
          :where(.cui-listbox__option[data-selected]) {
            background: Highlight;
            color: HighlightText;
            forced-color-adjust: none;
          }
          :where(.cui-listbox__option:focus-visible) { outline-color: Highlight; }
        }
        @media print {
          :where(.cui-listbox__surface) {
            max-block-size: none;
            overflow: visible;
            border-color: CanvasText;
            background: transparent;
          }
          :where(.cui-listbox__option:focus-visible) { outline: none; }
        }
      }
    """


class CListboxOption(LibraryComponent):
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
        default: SlotInput[CListboxOptionDefaultSlotData]
        start: SlotInput[CListboxOptionStateSlotData] | None = None
        description: SlotInput[CListboxOptionDescriptionSlotData] | None = None
        end: SlotInput[CListboxOptionStateSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_listbox_option_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)
        provided = self.inject(_CONTEXT, None)
        if provided is None:
            raise ValueError("CListboxOption must be rendered directly inside CListbox or CListboxGroup.")
        context = cast("_ListboxContext", provided.context)
        if context.parent_kind not in {"root", "group"}:
            raise ValueError("CListboxOption has an invalid enclosing Listbox context.")
        value = _identity("CListboxOption", kwargs.value)
        validate_boolean("CListboxOption", "disabled", kwargs.disabled)
        text_value = _plain_optional("CListboxOption", "text_value", kwargs.text_value)
        if text_value is not None and not text_value.strip():
            raise ValueError("CListboxOption text_value must be nonempty when supplied.")
        if text_value is not None and "\0" in text_value:
            raise ValueError("CListboxOption text_value cannot contain U+0000.")
        context.registry.values.append(value)
        if kwargs.disabled:
            context.registry.disabled.add(value)
        selected = value in context.selected
        active = not context.registry.roving_assigned and not context.root_disabled and not kwargs.disabled
        if active:
            context.registry.roving_assigned = True
        option_id = f"{context.root_id}-option-{_token(value)}"
        label_id = f"{option_id}-label"
        description_id = f"{option_id}-description"
        snapshot = {
            "morph_key": value,
            "value": value,
            "disabled": bool(kwargs.disabled),
            "selected": selected,
            "active": active,
            "text_value": text_value,
            "option_id": option_id,
            "label_id": label_id,
            "description_id": description_id,
            "described_by": description_id if "description" in self.raw_slots else None,
            "has_start": "start" in self.raw_slots,
            "has_description": "description" in self.raw_slots,
            "has_end": "end" in self.raw_slots,
            "attrs": _attrs(
                "CListboxOption",
                "attrs",
                kwargs.attrs,
                _OPTION_OWNED,
                kwargs.class_,
                kwargs.style,
            ),
            "default_slot_data": {"value": value},
            "state_slot_data": {"value": value, "selected": selected, "disabled": bool(kwargs.disabled)},
            "description_slot_data": {"value": value},
        }
        self.unprovide(_CONTEXT)
        self._listbox_option_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {"disabled": snapshot["disabled"], "textValue": snapshot["text_value"]}

    template = """
      <div
        class="cui-listbox__option"
        #c-key="morph_key"
        c-id="option_id"
        role="option"
        c-tabindex="0 if active else -1"
        c-aria-labelledby="label_id"
        c-aria-describedby="described_by"
        c-aria-selected="'true' if selected else 'false'"
        c-aria-disabled="'true' if disabled else 'false'"
        c-data-value="value"
        c-data-selected="selected"
        c-data-active="active"
        c-data-disabled="disabled"
        c-data-cui-listbox-option-disabled="disabled"
        c-data-cui-listbox-text-value="text_value"
        c-bind="attrs"
        data-citry-ui-part="listbox-option"
      >
        <span
          class="cui-listbox__indicator"
          aria-hidden="true"
          data-citry-ui-part="listbox-indicator"
        ></span>
        <c-if cond="has_start">
          <span
            class="cui-listbox__option-start"
            aria-hidden="true"
            data-cui-listbox-slot-region
            data-citry-ui-part="listbox-option-start"
          >
            <c-slot name="start" c-data="state_slot_data" />
          </span>
        </c-if>
        <span
          class="cui-listbox__option-copy"
          data-citry-ui-part="listbox-option-copy"
        >
          <span
            class="cui-listbox__option-label"
            c-id="label_id"
            data-cui-listbox-slot-region
            data-citry-ui-part="listbox-option-label"
          >
            <c-slot required c-data="default_slot_data" />
          </span>
          <c-if cond="has_description">
            <span
              class="cui-listbox__option-description"
              c-id="description_id"
              data-cui-listbox-slot-region
              data-citry-ui-part="listbox-option-description"
            >
              <c-slot name="description" c-data="description_slot_data" />
            </span>
          </c-if>
        </span>
        <c-if cond="has_end">
          <span
            class="cui-listbox__option-end"
            aria-hidden="true"
            data-cui-listbox-slot-region
            data-citry-ui-part="listbox-option-end"
          >
            <c-slot name="end" c-data="state_slot_data" />
          </span>
        </c-if>
      </div>
    """

    js = r"""
      $component({
        props: {disabled: {}, textValue: {}},
        init: ({els, data, props, effect}) => {
          const option = els[0];
          const invalidEpisodes = new Set();
          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CListboxOption ${name} received invalid client value`, value);
          };
          const stop = effect(() => {
            const suppliedDisabled = props.disabled;
            const disabled = suppliedDisabled === undefined
              ? data.disabled
              : typeof suppliedDisabled === 'boolean'
                ? suppliedDisabled
                : data.disabled;
            if (suppliedDisabled !== undefined && typeof suppliedDisabled !== 'boolean') {
              report('disabled', suppliedDisabled);
            } else invalidEpisodes.delete('disabled');
            option.toggleAttribute('data-cui-listbox-option-disabled', disabled);
            const suppliedText = props.textValue;
            let textValue = data.textValue;
            if (suppliedText === null || suppliedText === undefined) {
              invalidEpisodes.delete('textValue');
            } else if (typeof suppliedText === 'string' && suppliedText.trim() && !suppliedText.includes('\0')) {
              textValue = suppliedText.replace(/\r\n?/g, '\n');
              invalidEpisodes.delete('textValue');
            } else report('textValue', suppliedText);
            if (textValue === null) option.removeAttribute('data-cui-listbox-text-value');
            else option.setAttribute('data-cui-listbox-text-value', textValue);
          });
          return () => stop?.();
        },
      })
    """


class CListboxGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CListboxGroupDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        provided = self.inject(_CONTEXT, None)
        if provided is None:
            raise ValueError("CListboxGroup must be rendered directly inside CListbox.")
        context = cast("_ListboxContext", provided.context)
        if context.parent_kind != "root":
            raise ValueError("CListboxGroup cannot be nested inside another CListboxGroup.")
        label = _plain("CListboxGroup", "label", kwargs.label)
        group_id = f"{context.root_id}-group-{self.id}"
        self._listbox_group_start = len(context.registry.values)
        self._listbox_group_registry = context.registry
        self.provide(
            _CONTEXT,
            context=_ListboxContext(
                registry=context.registry,
                root_id=context.root_id,
                selected=context.selected,
                root_disabled=context.root_disabled,
                parent_kind="group",
            ),
        )
        return {
            "morph_key": self.id,
            "group_id": group_id,
            "label_id": f"{group_id}-label",
            "label": label,
            "attrs": _attrs(
                "CListboxGroup",
                "attrs",
                kwargs.attrs,
                _GROUP_OWNED,
                kwargs.class_,
                kwargs.style,
            ),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CListboxGroup completed without a render result.")
        if len(self._listbox_group_registry.values) == self._listbox_group_start:
            raise ValueError("CListboxGroup requires one or more direct CListboxOption declarations.")

    template = """
      <div
        class="cui-listbox__group"
        #c-key="morph_key"
        c-id="group_id"
        role="group"
        c-aria-labelledby="label_id"
        c-bind="attrs"
        data-citry-ui-part="listbox-group"
      >
        <span
          class="cui-listbox__group-label"
          c-id="label_id"
          data-citry-ui-part="listbox-group-label"
        >{{ label }}</span>
        <c-slot required />
      </div>
    """


__all__ = [
    "CListbox",
    "CListboxChangeSource",
    "CListboxDefaultSlotData",
    "CListboxGroup",
    "CListboxGroupDefaultSlotData",
    "CListboxOption",
    "CListboxOptionDefaultSlotData",
    "CListboxOptionDescriptionSlotData",
    "CListboxOptionStateSlotData",
    "CListboxSize",
    "CListboxValue",
    "CListboxValueChangeDetail",
    "CListboxVariant",
]
