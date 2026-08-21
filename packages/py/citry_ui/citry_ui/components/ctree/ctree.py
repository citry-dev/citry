"""Accessible application Tree and nested Tree Items."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CTreeSelectionMode = Literal["none", "single", "multiple"]
CTreeVariant = Literal["plain", "soft", "outline"]
CTreeSize = Literal["sm", "md", "lg"]
CTreeChangeSource = Literal["pointer", "keyboard", "structure"]

_CONTEXT = "citry_ui_tree"
_MODES = ("none", "single", "multiple")
_VARIANTS = ("plain", "soft", "outline")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-selection-mode",
        "data-size",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-expanded",
        "aria-hidden",
        "aria-label",
        "aria-selected",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-expanded",
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


class CTreeDefaultSlotData:
    pass


class CTreeItemDefaultSlotData(TypedDict):
    parent_value: str
    level: int


class CTreeExpandedChangeDetail(TypedDict):
    value: str
    expanded: bool
    previousExpanded: list[str]
    controlled: bool
    source: CTreeChangeSource
    item: object
    sourceEvent: object


class CTreeSelectionChangeDetail(TypedDict):
    value: str
    selected: bool
    previousSelected: list[str]
    controlled: bool
    source: CTreeChangeSource
    item: object
    sourceEvent: object


class CTreeActionDetail(TypedDict):
    value: str
    item: object
    sourceEvent: object


@dataclass(slots=True)
class _TreeRegistry:
    values: list[str] = field(default_factory=list)
    branches: set[str] = field(default_factory=set)
    disabled: set[str] = field(default_factory=set)
    roving_assigned: bool = False


@dataclass(slots=True)
class _TreeContext:
    registry: _TreeRegistry
    root_id: str
    expanded: frozenset[str]
    selected: frozenset[str]
    selection_mode: str
    root_disabled: bool
    parent_value: str | None
    level: int


def _plain(owner: str, name: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        raise TypeError(f"{owner} {name} must be a string, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{owner} {name} must be nonempty and cannot contain U+0000.")
    return plain


def _value(owner: str, value: object) -> str:
    plain = _plain(owner, "value", value)
    if any(character in "\t\n\f\r " for character in plain):
        raise ValueError(f"{owner} value cannot contain ASCII whitespace.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain("CTree", name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"CTree {name} must be one of {expected}, got {plain!r}.")
    return plain


def _values(owner: str, name: str, value: object) -> tuple[str, ...]:
    raw = const_value(value)
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"{owner} {name} must be a sequence of strings, got {raw!r}.")
    result = tuple(_value(owner, item) for item in raw)
    if len(result) != len(set(result)):
        raise ValueError(f"{owner} {name} cannot contain duplicate values.")
    return result


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
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{owner} attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{owner} attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{owner} attrs cannot dynamically bind owned attribute {key!r}.")
    return merge_root_attrs(copied, class_, style)


def _token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:12]


class _TreeOutputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str | None] = []
        self.problem: str | None = None
        self.seen_tree = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        part = values.get("data-citry-ui-part")
        parent = self.stack[-1] if self.stack else None
        in_tree = self.seen_tree and bool(self.stack)
        if part == "tree" and not self.seen_tree:
            self.seen_tree = True
        elif in_tree and self.problem is None:
            allowed = {
                "tree": {"item"},
                "item": {"row", "group"},
                "row": {"indicator", "label"},
                "group": {"item"},
                "indicator": set(),
                "label": set(),
            }
            if parent in allowed and part not in allowed[parent]:
                self.problem = f"{parent} contains unsupported element {tag}"
        self.stack.append(part)

    def handle_endtag(self, tag: str) -> None:  # noqa: ARG002
        if self.stack:
            self.stack.pop()


def _validate_tree_output(rendered: object) -> None:
    parser = _TreeOutputParser()
    parser.feed(cast("Any", rendered).serialize(deps_strategy="ignore"))
    if parser.problem is not None:
        raise ValueError(
            f"CTree and CTreeItem content may contain only the documented Tree declaration anatomy: {parser.problem}."
        )


class CTree(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        expanded: Sequence[str] = ()
        selected: Sequence[str] = ()
        selection_mode: CTreeSelectionMode = "single"
        disabled: bool = False
        variant: CTreeVariant = "plain"
        size: CTreeSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTreeDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if self.inject(_CONTEXT, None) is not None:
            raise ValueError("Nested CTree must be rendered outside a CTreeItem declaration collection.")
        label = _plain("CTree", "label", kwargs.label)
        expanded = _values("CTree", "expanded", kwargs.expanded)
        selected = _values("CTree", "selected", kwargs.selected)
        mode = _choice("selection_mode", kwargs.selection_mode, _MODES)
        validate_boolean("CTree", "disabled", kwargs.disabled)
        variant = _choice("variant", kwargs.variant, _VARIANTS)
        size = _choice("size", kwargs.size, _SIZES)
        if mode == "none" and selected:
            raise ValueError("CTree selected must be empty when selection_mode is 'none'.")
        if mode == "single" and len(selected) > 1:
            raise ValueError("CTree single selection accepts at most one selected value.")
        if "default" not in self.raw_slots:
            raise ValueError("CTree requires one or more CTreeItem declarations.")
        registry = _TreeRegistry()
        root_id = f"cui-tree-{self.id}"
        context = _TreeContext(
            registry=registry,
            root_id=root_id,
            expanded=frozenset(expanded),
            selected=frozenset(selected),
            selection_mode=mode,
            root_disabled=bool(kwargs.disabled),
            parent_value=None,
            level=1,
        )
        self.provide(_CONTEXT, context=context)
        self._tree_registry = registry
        self._tree_expanded = expanded
        self._tree_selected = selected
        self._tree_data = {
            "expanded": list(expanded),
            "selected": list(selected),
            "selectionMode": mode,
            "disabled": bool(kwargs.disabled),
            "variant": variant,
            "size": size,
        }
        return {
            **self._tree_data,
            "label": label,
            "root_id": root_id,
            "attrs": _attrs("CTree", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CTree completed without a render result.")
        _validate_tree_output(rendered)
        values = self._tree_registry.values
        if not values:
            raise ValueError("CTree requires one or more CTreeItem declarations.")
        if len(values) != len(set(values)):
            raise ValueError("CTree requires every CTreeItem value to be unique.")
        unknown_expanded = set(self._tree_expanded).difference(self._tree_registry.branches)
        if unknown_expanded:
            raise ValueError(f"CTree expanded contains unknown or leaf Items: {sorted(unknown_expanded)!r}.")
        unknown_selected = set(self._tree_selected).difference(values)
        if unknown_selected:
            raise ValueError(f"CTree selected contains unknown Items: {sorted(unknown_selected)!r}.")

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return self._tree_data

    template = """
      <div
        class="cui-tree"
        c-id="root_id"
        c-bind="attrs"
        role="tree"
        c-aria-label="label"
        c-data-selection-mode="selectionMode"
        c-data-disabled="disabled"
        c-data-variant="variant"
        c-data-size="size"
        data-citry-ui-part="tree"
      ><c-slot required /></div>
    """

    js = r"""
      $component({
        props: {
          expanded: {}, selected: {}, selectionMode: {}, disabled: {}, variant: {}, size: {},
          onExpandedChange: {}, onSelectionChange: {}, onAction: {},
        },
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const invalidEpisodes = new Set();
          const allItems = () => [...root.querySelectorAll('[role="treeitem"]')]
            .filter((item) => item.closest('[role="tree"]') === root);
          const values = () => allItems().map((item) => item.dataset.value);
          const branchItems = () => allItems().filter((item) => item.hasAttribute('aria-expanded'));
          const serverFingerprint = JSON.stringify({expanded:data.expanded, selected:data.selected});
          const prior = root.__citryUiTreeRuntime;
          let committedExpanded = prior?.serverFingerprint === serverFingerprint
            ? [...prior.expanded] : [...data.expanded];
          let committedSelected = prior?.serverFingerprint === serverFingerprint
            ? [...prior.selected] : [...data.selected];
          let currentExpanded = [...committedExpanded];
          let currentSelected = [...committedSelected];
          let expandedControlled = false;
          let selectedControlled = false;
          let activeValue = prior?.activeValue ?? null;
          let callbackExpanded = null;
          let callbackSelected = null;
          let callbackAction = null;
          let configuration = {
            selectionMode: data.selectionMode, disabled: data.disabled,
            variant: data.variant, size: data.size,
          };
          let structureValid = false;
          let task = null;
          let generation = 0;
          let typeBuffer = '';
          let typeTimer = null;

          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CTree ${name} received invalid client value`, value);
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
            report(name, supplied); return fallback;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'string' && allowed.includes(supplied)) {
              invalidEpisodes.delete(name); return supplied;
            }
            report(name, supplied); return fallback;
          };
          const effectivelyDisabled = () => {
            if (configuration.disabled) return true;
            for (let node = root.parentElement; node; node = node.parentElement) {
              if (!(node instanceof HTMLFieldSetElement) || !node.disabled) continue;
              const legend = [...node.children].find((child) => child instanceof HTMLLegendElement);
              if (!(legend instanceof Element) || !legend.contains(root)) return true;
            }
            return false;
          };
          const canonicalVector = (name, supplied, allowed, mode = 'multiple') => {
            if (!Array.isArray(supplied) || !supplied.every((value) => typeof value === 'string'
                && value.length > 0 && !/[\u0000\t\n\f\r ]/.test(value))) return null;
            if (new Set(supplied).size !== supplied.length
                || supplied.some((value) => !allowed.has(value))) return null;
            if (mode === 'none' && supplied.length > 0) return null;
            if (mode === 'single' && supplied.length > 1) return null;
            invalidEpisodes.delete(name);
            return [...supplied];
          };
          const itemFor = (value) => allItems().find((item) => item.dataset.value === value) ?? null;
          const groupFor = (item) => [...item.children]
            .find((child) => child.getAttribute?.('role') === 'group') ?? null;
          const parentItem = (item) => {
            const group = item.parentElement;
            return group?.getAttribute('role') === 'group' ? group.parentElement?.closest('[role="treeitem"]') : null;
          };
          const directChildren = (item) => {
            const group = groupFor(item);
            return group ? [...group.children].filter((child) => child.getAttribute?.('role') === 'treeitem') : [];
          };
          const isItemDisabled = (item) => effectivelyDisabled()
            || item.hasAttribute('data-cui-tree-item-disabled');
          const visibleItems = () => allItems().filter((item) => {
            for (let node = item.parentElement; node && node !== root; node = node.parentElement) {
              if (node.getAttribute?.('role') === 'group' && node.hidden) return false;
            }
            return true;
          });
          const structureProblem = () => {
            const items = allItems();
            if (items.length === 0) return 'requires one or more Items';
            if (new Set(values()).size !== items.length) return 'contains duplicate Item values';
            const roots = [...root.children].filter((child) => child.getAttribute?.('role') === 'treeitem');
            if (roots.length !== root.children.length) return 'contains an unknown direct root child';
            for (const item of items) {
              const children = [...item.children];
              if (!children[0]?.matches?.('[data-citry-ui-part="row"]')) return 'Item row anatomy is invalid';
              const groups = children.filter((child) => child.getAttribute?.('role') === 'group');
              if (groups.length > 1 || children.length !== 1 + groups.length) return 'Item child anatomy is invalid';
              if (groups[0] && [...groups[0].children].some((child) => child.getAttribute?.('role') !== 'treeitem')) {
                return 'Item groups may contain only Tree Items';
              }
            }
            return null;
          };
          const focusItem = (item) => {
            if (!(item instanceof HTMLElement)) return;
            activeValue = item.dataset.value;
            allItems().forEach((entry) => { entry.tabIndex = entry === item ? 0 : -1; });
            item.focus();
          };
          const detail = (value, previous, controlled, source, item, event, stateName, state) => ({
            value, [stateName]: state, [`previous${stateName[0].toUpperCase()}${stateName.slice(1)}`]: [...previous],
            controlled, source, item, sourceEvent: event,
          });
          const requestExpanded = (item, expanded, event, source) => {
            if (isItemDisabled(item) || !groupFor(item)) return;
            const value = item.dataset.value;
            const previous = [...currentExpanded];
            const next = expanded
              ? [...previous.filter((entry) => entry !== value), value]
              : previous.filter((entry) => entry !== value);
            callbackExpanded?.([...next], detail(
              value, previous, expandedControlled, source, item, event, 'expanded', expanded
            ));
            if (!expandedControlled) { committedExpanded = [...next]; currentExpanded = [...next]; sync(); }
            else schedule();
          };
          const requestSelection = (item, event, source) => {
            if (configuration.selectionMode === 'none' || isItemDisabled(item)) return;
            const value = item.dataset.value;
            const previous = [...currentSelected];
            const selected = !previous.includes(value);
            const next = configuration.selectionMode === 'single'
              ? (selected ? [value] : [])
              : (selected ? [...previous, value] : previous.filter((entry) => entry !== value));
            callbackSelected?.([...next], detail(
              value, previous, selectedControlled, source, item, event, 'selected', selected
            ));
            if (!selectedControlled) { committedSelected = [...next]; currentSelected = [...next]; sync(); }
            else schedule();
          };
          const sync = () => {
            const problem = structureProblem();
            if (problem) {
              structureValid = false;
              report('structure', problem);
              root.removeAttribute('data-citry-tree-initialized');
              allItems().forEach((item) => { item.tabIndex = -1; item.setAttribute('aria-disabled', 'true'); });
              return;
            }
            structureValid = true;
            invalidEpisodes.delete('structure');
            const itemValues = new Set(values());
            const branches = new Set(branchItems().map((item) => item.dataset.value));
            let suppliedExpanded = props.expanded;
            if (suppliedExpanded === null) suppliedExpanded = undefined;
            if (suppliedExpanded === undefined) {
              invalidEpisodes.delete('expanded');
              if (expandedControlled) committedExpanded = currentExpanded.filter((value) => branches.has(value));
              expandedControlled = false;
              currentExpanded = committedExpanded.filter((value) => branches.has(value));
            } else {
              const valid = canonicalVector('expanded', suppliedExpanded, branches);
              expandedControlled = true;
              if (valid) currentExpanded = valid;
              else {
                report('expanded', suppliedExpanded);
                currentExpanded = committedExpanded.filter((value) => branches.has(value));
              }
            }
            let suppliedSelected = props.selected;
            if (suppliedSelected === null) suppliedSelected = undefined;
            if (suppliedSelected === undefined) {
              invalidEpisodes.delete('selected');
              if (selectedControlled) committedSelected = currentSelected.filter((value) => itemValues.has(value));
              selectedControlled = false;
              currentSelected = committedSelected.filter((value) => itemValues.has(value));
            } else {
              const valid = canonicalVector('selected', suppliedSelected, itemValues, configuration.selectionMode);
              selectedControlled = true;
              if (valid) currentSelected = valid;
              else {
                report('selected', suppliedSelected);
                currentSelected = committedSelected.filter((value) => itemValues.has(value));
              }
            }
            if (configuration.selectionMode === 'none') currentSelected = [];
            if (configuration.selectionMode === 'single') currentSelected = currentSelected.slice(0, 1);
            const disabled = effectivelyDisabled();
            root.dataset.selectionMode = configuration.selectionMode;
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute('data-disabled', disabled);
            allItems().forEach((item) => {
              const value = item.dataset.value;
              const group = groupFor(item);
              const expanded = Boolean(group && currentExpanded.includes(value));
              const selected = currentSelected.includes(value);
              const itemDisabled = isItemDisabled(item);
              item.setAttribute('aria-disabled', itemDisabled ? 'true' : 'false');
              item.toggleAttribute('data-disabled', itemDisabled);
              if (group) {
                item.setAttribute('aria-expanded', expanded ? 'true' : 'false');
                item.toggleAttribute('data-expanded', expanded);
                group.hidden = !expanded;
                group.inert = !expanded;
              }
              if (configuration.selectionMode === 'none') item.removeAttribute('aria-selected');
              else item.setAttribute('aria-selected', selected ? 'true' : 'false');
              item.toggleAttribute('data-selected', selected);
            });
            const visible = visibleItems();
            let active = itemFor(activeValue);
            if (!(active instanceof HTMLElement) || !visible.includes(active)) {
              active = visible.find((item) => currentSelected.includes(item.dataset.value)) ?? visible[0] ?? null;
            }
            allItems().forEach((item) => { item.tabIndex = item === active && !disabled ? 0 : -1; });
            activeValue = active?.dataset.value ?? null;
            root.__citryUiTreeRuntime = {
              serverFingerprint, expanded:[...committedExpanded], selected:[...committedSelected], activeValue,
            };
            root.setAttribute('data-citry-tree-initialized', '');
          };
          const schedule = () => {
            if (task !== null) return;
            const scheduled = generation;
            task = setTimeout(() => { task = null; if (scheduled === generation) sync(); }, 0);
          };
          const itemFromEvent = (event) => event.composedPath().find(
            (node) => node instanceof HTMLElement && node.getAttribute?.('role') === 'treeitem'
              && node.closest('[role="tree"]') === root
          );
          const onClick = (event) => {
            if (!structureValid) return;
            const item = itemFromEvent(event);
            if (!(item instanceof HTMLElement)) return;
            focusItem(item);
            const indicator = event.composedPath().find(
              (node) => node instanceof Element && node.matches?.('[data-citry-ui-part="indicator"]')
            );
            if (indicator && groupFor(item)) {
              requestExpanded(item, item.getAttribute('aria-expanded') !== 'true', event, 'pointer');
            }
            else requestSelection(item, event, 'pointer');
          };
          const onDoubleClick = (event) => {
            const item = itemFromEvent(event);
            if (!(item instanceof HTMLElement) || isItemDisabled(item)) return;
            callbackAction?.(item.dataset.value, {value:item.dataset.value, item, sourceEvent:event});
          };
          const onKeyDown = (event) => {
            if (!structureValid) return;
            const item = itemFromEvent(event);
            if (!(item instanceof HTMLElement)) return;
            const visible = visibleItems();
            const index = visible.indexOf(item);
            let destination = null;
            if (event.key === 'ArrowDown') destination = visible[index + 1] ?? null;
            else if (event.key === 'ArrowUp') destination = visible[index - 1] ?? null;
            else if (event.key === 'Home') destination = visible[0];
            else if (event.key === 'End') destination = visible.at(-1);
            else if (event.key === 'ArrowRight') {
              const group = groupFor(item);
              if (group && item.getAttribute('aria-expanded') !== 'true') {
                requestExpanded(item, true, event, 'keyboard');
              }
              else if (group) destination = directChildren(item)[0];
            } else if (event.key === 'ArrowLeft') {
              if (groupFor(item) && item.getAttribute('aria-expanded') === 'true') {
                requestExpanded(item, false, event, 'keyboard');
              }
              else destination = parentItem(item);
            } else if (event.key === ' ') {
              requestSelection(item, event, 'keyboard');
            } else if (event.key === 'Enter') {
              requestSelection(item, event, 'keyboard');
              if (!isItemDisabled(item)) callbackAction?.(
                item.dataset.value, {value:item.dataset.value, item, sourceEvent:event}
              );
            } else if (!event.ctrlKey && !event.metaKey && !event.altKey && event.key.length === 1) {
              const key = event.key.toLocaleLowerCase();
              if (typeBuffer.length === 1 && typeBuffer === key) typeBuffer = key;
              else typeBuffer += key;
              if (typeTimer !== null) clearTimeout(typeTimer);
              typeTimer = setTimeout(() => { typeBuffer = ''; typeTimer = null; }, 500);
              const ordered = [...visible.slice(index + 1), ...visible.slice(0, index + 1)];
              destination = ordered.find((entry) => {
                const text = entry.querySelector(':scope > [data-citry-ui-part="row"] > [data-citry-ui-part="label"]')
                  ?.textContent?.trim().replace(/\s+/g, ' ').toLocaleLowerCase() ?? '';
                return text.startsWith(typeBuffer);
              });
            } else return;
            event.preventDefault();
            if (destination instanceof HTMLElement) focusItem(destination);
          };
          const onFocusIn = (event) => {
            const item = itemFromEvent(event);
            if (item instanceof HTMLElement) {
              activeValue = item.dataset.value;
              allItems().forEach((entry) => { entry.tabIndex = entry === item ? 0 : -1; });
            }
          };
          root.addEventListener('click', onClick);
          root.addEventListener('dblclick', onDoubleClick);
          root.addEventListener('keydown', onKeyDown);
          root.addEventListener('focusin', onFocusIn);
          const observer = new MutationObserver(schedule);
          observer.observe(root, {childList:true, subtree:true});
          const fieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const item = new MutationObserver(schedule);
            item.observe(ancestor, {childList:true, attributes:true, attributeFilter:['disabled']});
            fieldsets.push(item);
          }
          const stop = effect(() => {
            callbackExpanded = typeof props.onExpandedChange === 'function' ? props.onExpandedChange : null;
            callbackSelected = typeof props.onSelectionChange === 'function' ? props.onSelectionChange : null;
            callbackAction = typeof props.onAction === 'function' ? props.onAction : null;
            configuration = {
              selectionMode: resolveChoice('selectionMode', data.selectionMode, ['none','single','multiple']),
              disabled: resolveBoolean('disabled', data.disabled),
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
            root.__citryUiTreeRuntime = {
              serverFingerprint, expanded:[...committedExpanded], selected:[...committedSelected], activeValue,
            };
            stop?.(); observer.disconnect(); fieldsets.forEach((item) => item.disconnect());
            root.removeEventListener('click', onClick);
            root.removeEventListener('dblclick', onDoubleClick);
            root.removeEventListener('keydown', onKeyDown);
            root.removeEventListener('focusin', onFocusIn);
            root.removeAttribute('data-citry-tree-initialized');
          };
        },
      })
    """

    css_file = "runtime.min.css"


class CTreeItem(LibraryComponent):
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
        default: SlotInput[CTreeItemDefaultSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        provided = self.inject(_CONTEXT, None)
        if provided is None:
            raise ValueError("CTreeItem must be rendered directly inside CTree or another CTreeItem.")
        context = cast("_TreeContext", provided.context)
        value = _value("CTreeItem", kwargs.value)
        label = _plain("CTreeItem", "label", kwargs.label)
        validate_boolean("CTreeItem", "disabled", kwargs.disabled)
        has_children = "default" in self.raw_slots
        context.registry.values.append(value)
        if has_children:
            context.registry.branches.add(value)
        if kwargs.disabled:
            context.registry.disabled.add(value)
        selected = value in context.selected
        roving = not context.registry.roving_assigned and (
            (context.selected and selected) or (not context.selected and len(context.registry.values) == 1)
        )
        if roving:
            context.registry.roving_assigned = True
        expanded = has_children and value in context.expanded
        attrs = _attrs("CTreeItem", kwargs.attrs, _ITEM_OWNED, kwargs.class_, kwargs.style)
        attrs.update(
            {
                "id": f"{context.root_id}-item-{_token(value)}",
                "role": "treeitem",
                "tabindex": 0 if roving and not context.root_disabled else -1,
                "aria-label": label,
                "aria-disabled": "true" if context.root_disabled or kwargs.disabled else "false",
                "aria-expanded": ("true" if expanded else "false") if has_children else None,
                "aria-selected": ("true" if selected else "false") if context.selection_mode != "none" else None,
                "data-value": value,
                "data-level": context.level,
                "data-expanded": expanded,
                "data-selected": selected,
                "data-disabled": context.root_disabled or bool(kwargs.disabled),
                "data-cui-tree-item-disabled": bool(kwargs.disabled),
            }
        )
        child_context = _TreeContext(
            registry=context.registry,
            root_id=context.root_id,
            expanded=context.expanded,
            selected=context.selected,
            selection_mode=context.selection_mode,
            root_disabled=context.root_disabled,
            parent_value=value,
            level=context.level + 1,
        )
        self.provide(_CONTEXT, context=child_context)
        return {
            "morph_key": value,
            "attrs": attrs,
            "label": label,
            "has_children": has_children,
            "hidden": not expanded,
            "slot_data": {"parent_value": value, "level": context.level + 1},
        }

    template = """
      <div class="cui-tree__item" #c-key="morph_key" c-bind="attrs" data-citry-ui-part="item">
        <span class="cui-tree__row" data-citry-ui-part="row">
          <span class="cui-tree__indicator" aria-hidden="true" data-citry-ui-part="indicator"></span>
          <span class="cui-tree__label" data-citry-ui-part="label">{{ label }}</span>
        </span>
        <c-if cond="has_children">
          <div class="cui-tree__group" role="group" c-hidden="hidden" c-inert="hidden" data-citry-ui-part="group">
            <c-slot c-data="slot_data" />
          </div>
        </c-if>
      </div>
    """


__all__ = [
    "CTree",
    "CTreeActionDetail",
    "CTreeChangeSource",
    "CTreeDefaultSlotData",
    "CTreeExpandedChangeDetail",
    "CTreeItem",
    "CTreeItemDefaultSlotData",
    "CTreeSelectionChangeDetail",
    "CTreeSelectionMode",
    "CTreeSize",
    "CTreeVariant",
]
